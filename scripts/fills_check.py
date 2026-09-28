#!/usr/bin/env python3
"""
REAL FILLS CHECK -- are real trades as cheap as the backtest assumes?

Every backtest assumes Trading 212 charges 0.15% currency exchange on US
shares and no dealing charge, and that you trade close to the price the plan
was worked out from. This reads your REAL filled orders from Trading 212
(needs the key's "History - Orders" permission) and measures:

  * charges    what Trading 212 actually took, as % of each trade
               (assumed: 0.15% on US shares, 0% on the London tracker/bond fund)
  * price gap  fill price against the previous day's close -- the price the
               plan used. Positive = worse for you (paid more / got less)

Your amounts are sent ONLY by email. The repository gets only percentages
(docs/FILLS.md), which say nothing about the size of your account.
"""
from __future__ import annotations

import importlib.util
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ASSUMED_FX = 0.0015


def load_t212():
    spec = importlib.util.spec_from_file_location("t212_orders", HERE / "t212_orders.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def fetch_history(api) -> list[dict]:
    items, path = [], "/equity/history/orders?limit=50"
    for _ in range(40):                                   # up to 2,000 orders
        page = api.get(path, wait=11)                     # 6 requests a minute
        items += page.get("items", []) if isinstance(page, dict) else (page or [])
        nxt = page.get("nextPagePath") if isinstance(page, dict) else None
        if not nxt:
            break
        path = nxt.split("/api/v0", 1)[-1] if "/api/v0" in nxt else nxt
    return items


def tax_total(taxes) -> float:
    tot = 0.0
    for t in taxes or []:
        for key in ("quantity", "amount", "value"):
            if isinstance(t, dict) and t.get(key) is not None:
                try:
                    tot += abs(float(t[key]))
                except (TypeError, ValueError):
                    pass
                break
    return tot


def rows_from(items: list[dict]) -> pd.DataFrame:
    rows = []
    for it in items:
        o, f = it.get("order") or {}, it.get("fill") or {}
        if not f or not f.get("price"):
            continue
        wi = f.get("walletImpact") or {}
        qty = abs(float(f.get("quantity") or o.get("filledQuantity") or 0))
        net = abs(float(wi.get("netValue") or 0))
        ticker = o.get("ticker") or (o.get("instrument") or {}).get("ticker", "")
        side = str(o.get("side") or ("BUY" if float(f.get("quantity") or 0) > 0 else "SELL")).upper()
        rows.append({"date": str(f.get("filledAt", ""))[:10], "ticker": ticker, "side": side, "qty": qty,
                     "price": float(f["price"]), "gbp": net, "fees": tax_total(wi.get("taxes")),
                     "fx_rate": wi.get("fxRate"), "us": str(ticker).endswith("_US_EQ")})
    return pd.DataFrame(rows)


def add_price_gap(df: pd.DataFrame) -> pd.DataFrame:
    """Fill price vs the previous close in data/live_prices.csv (US$). US shares only."""
    try:
        P = pd.read_csv("data/live_prices.csv", index_col=0, parse_dates=True)
    except Exception:                                              # noqa: BLE001
        df["gap"] = np.nan
        return df
    gaps = []
    for _, r in df.iterrows():
        sym = str(r["ticker"]).replace("_US_EQ", "").replace("_", "-")
        if not r["us"] or sym not in P.columns:
            gaps.append(np.nan)
            continue
        s = P[sym].dropna()
        prev = s[s.index < pd.Timestamp(r["date"])]
        if prev.empty:
            gaps.append(np.nan)
            continue
        pc = float(prev.iloc[-1])
        g = r["price"] / pc - 1
        gaps.append(g if r["side"] == "BUY" else -g)   # positive = worse for you
    df["gap"] = gaps
    return df


def main() -> int:
    key, sec = os.environ.get("T212_API_KEY", ""), os.environ.get("T212_API_SECRET", "")
    out_md, email = Path("docs/FILLS.md"), Path("docs/FILLS_EMAIL.md")
    email.unlink(missing_ok=True)
    if not (key and sec):
        out_md.write_text("# Real fills check\n\nNo Trading 212 key -- nothing to check.\n")
        return 0
    t2 = load_t212()
    try:
        items = fetch_history(t2.T212(key, sec))
    except PermissionError:
        out_md.write_text("# Real fills check\n\nThe Trading 212 key is not allowed to read order history. "
                          "Turn on **History - Orders** for the key.\n")
        return 0
    df = rows_from(items)
    now = pd.Timestamp.now("Europe/London").strftime("%a %d %b %Y")
    if df.empty:
        out_md.write_text(f"# Real fills check\n\n_{now}_\n\nNo filled orders yet.\n")
        return 0
    df = add_price_gap(df)
    df["fee_pct"] = np.where(df["gbp"] > 0, df["fees"] / df["gbp"], np.nan)
    us, uk = df[df["us"]], df[~df["us"]]
    fee_us = float(us["fees"].sum() / us["gbp"].sum()) if len(us) and us["gbp"].sum() else np.nan
    fee_uk = float(uk["fees"].sum() / uk["gbp"].sum()) if len(uk) and uk["gbp"].sum() else np.nan
    gap = float(np.nanmean(df["gap"])) if df["gap"].notna().any() else np.nan
    extra = (fee_us - ASSUMED_FX) if np.isfinite(fee_us) else np.nan
    verdict = ("✅ Real costs match the backtest." if np.isfinite(extra) and extra <= 0.0005 else
               "⚠️ Real charges are higher than the backtest assumes -- tell Claude so the tests can be re-run "
               "with the real figure." if np.isfinite(extra) else "Not enough US trades yet.")
    L = ["# Real fills check\n", f"_{now}. {len(df)} filled orders from your Trading 212 account._\n",
         "| | Backtest assumes | Real |", "|---|---|---|",
         f"| Charges on US shares | 0.15% | {fee_us:.3%} |" if np.isfinite(fee_us) else "| Charges on US shares | 0.15% | — |",
         f"| Charges on London funds | 0% | {fee_uk:.3%} |" if np.isfinite(fee_uk) else "| Charges on London funds | 0% | — |",
         (f"| Price gap vs the plan's price (previous close) | about 0% on average | {gap:+.2%} |"
          if np.isfinite(gap) else "| Price gap vs the plan's price | — | — |"),
         "", verdict, "",
         "_Price gap: positive means you paid more (buys) or got less (sells) than the previous close. "
         "Day-to-day moves make single trades noisy; the average over many trades is what matters._"]
    out_md.write_text("\n".join(L) + "\n")          # percentages only: safe to publish
    # the email adds each trade
    E = L + ["", "## Each trade", "", "| Date | Order | Shares | Price | Value | Charges | Gap |", "|---|---|---|---|---|---|---|"]
    for _, r in df.sort_values("date").iterrows():
        E.append(f"| {r['date']} | {r['side']} {str(r['ticker']).split('_')[0]} | {r['qty']:.3f} | {r['price']:,.2f} | "
                 f"£{r['gbp']:,.2f} | £{r['fees']:,.2f} ({r['fee_pct']:.2%}) | "
                 + (f"{r['gap']:+.2%}" if np.isfinite(r['gap']) else "—") + " |")
    email.write_text("\n".join(E) + "\n")
    Path("data/fills_summary.json").write_text(json.dumps(
        {"run": now, "orders": int(len(df)), "fee_us": fee_us, "fee_uk": fee_uk, "avg_gap": gap}, default=str))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
