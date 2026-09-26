#!/usr/bin/env python3
"""
TRADING 212 ORDER BOT -- DRY RUN.

Every weekday shortly after the US market opens it:
  1. reads last night's plan (docs/plan.json -- what the strategy holds)
  2. reads your REAL Trading 212 account through the API: cash, positions,
     pending orders (only if the T212_API_KEY / T212_API_SECRET secrets exist;
     otherwise it pretends the account is new, holding just the set-up deposit)
  3. works out the exact orders that would bring the account in line with the
     strategy: which stock, how many shares, about how many pounds, and why
  4. runs safety checks on them
  5. writes docs/ORDERS.md, logs to data/orders_log.jsonl, and emails you
     when there is anything to do

It NEVER sends an order: there is no order-placing code in this file. The API
key it needs only has to be allowed to READ the account.

How the orders are worked out (no rebalancing, just the strategy's own moves):
  * market switch OFF   -> sell every stock and the tracker, buy the bond fund
  * a stock you hold that the strategy no longer holds -> SELL all of it
  * a stock the strategy holds that you don't            -> BUY one slot
        new account : the same split as the plan's "Starting from scratch" list
        otherwise   : one tenth of the account, paid for by selling tracker
  * bond fund held while the switch is ON -> sell it, buy the tracker
  * spare cash (sale proceeds, dividends, a deposit) -> into the tracker
"""
from __future__ import annotations

import base64
import json
import math
import os
import sys
import time
from pathlib import Path

import pandas as pd

LIVE = "https://live.trading212.com/api/v0"
DOCS = Path("docs")
LOG = Path("data/orders_log.jsonl")
CFG = Path("config/t212.yml")


# ---------------------------------------------------------------------------
# Trading 212 API -- read only
# ---------------------------------------------------------------------------

class T212:
    def __init__(self, key: str, secret: str, base: str = LIVE):
        import requests
        self.s = requests.Session()
        tok = base64.b64encode(f"{key}:{secret}".encode()).decode()
        self.s.headers["Authorization"] = f"Basic {tok}"
        self.base = base

    def get(self, path: str, wait: float = 1.2):
        for attempt in range(4):
            r = self.s.get(self.base + path, timeout=60)
            if r.status_code == 429:                      # rate limit: wait and retry
                time.sleep(int(r.headers.get("x-ratelimit-reset-in", 0) or 0) or 10 * (attempt + 1))
                continue
            if r.status_code in (401, 403):
                raise PermissionError(f"Trading 212 refused {path} ({r.status_code}): check the API key "
                                      "and that it is allowed to read the account")
            r.raise_for_status()
            time.sleep(wait)
            return r.json()
        raise RuntimeError(f"Trading 212 rate limit on {path}")


def floor_to(x: float, d: int = 2) -> float:
    return math.floor(x * 10 ** d) / 10 ** d


def ceil_to(x: float, d: int = 2) -> float:
    return math.ceil(x * 10 ** d - 1e-9) / 10 ** d


def yahoo_price_gbp(symbol: str) -> float | None:
    """Last close of a London-listed fund in pounds (Yahoo quotes some in pence)."""
    if not symbol:
        return None
    try:
        import yfinance as yf
        s = yf.download(symbol, period="10d", auto_adjust=True, progress=False)["Close"]
        s = (s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s).dropna()
        p = float(s.iloc[-1])
        return p / 100 if p > 1000 else p                 # pence -> pounds
    except Exception:                                      # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# the account
# ---------------------------------------------------------------------------

def read_account(api: T212 | None, plan: dict) -> dict:
    """Cash, positions and pending orders. Without an API key: a new account holding the deposit."""
    if api is None:
        su = (plan.get("strategy") or {}).get("setup") or {}
        dep = float(su.get("deposit") or (plan.get("strategy") or {}).get("pot") or 10_000)
        return {"real": False, "currency": "GBP", "cash": dep, "total": dep, "positions": {},
                "pending": [], "instruments": None}
    summ = api.get("/equity/account/summary", wait=5.5)
    pos = api.get("/equity/positions")
    try:                                   # needs the "orders" read permission; fine without it
        pend = api.get("/equity/orders", wait=5.5)
    except PermissionError:
        pend = None
    inst = api.get("/equity/metadata/instruments", wait=1)
    P = {}
    for p in pos:
        tk = p["instrument"]["ticker"]
        q = float(p.get("quantity") or 0)
        v = float((p.get("walletImpact") or {}).get("currentValue") or 0)
        P[tk] = {"qty": q, "avail": float(p.get("quantityAvailableForTrading", q) or 0), "value": v,
                 "price_gbp": v / q if q else None, "name": p["instrument"].get("name", tk),
                 "price": float(p.get("currentPrice") or 0), "currency": p["instrument"].get("currency")}
    return {"real": True, "currency": summ.get("currency"), "id": summ.get("id"),
            "cash": float((summ.get("cash") or {}).get("availableToTrade") or 0),
            "total": float(summ.get("totalValue") or 0), "positions": P, "pending": pend,
            "instruments": inst}


def resolver(instruments):
    """Plan symbol (Yahoo style, e.g. BRK-B) -> Trading 212 ticker. Unverified without the API."""
    by_short = {}
    for i in instruments or []:
        by_short.setdefault(str(i.get("shortName", "")).upper(), []).append(i)

    def us(sym: str) -> tuple[str, bool]:
        s = sym.upper()
        guess = s.replace("-", "_").replace(".", "_") + "_US_EQ"
        if instruments is None:
            return guess, False
        for cand in (s, s.replace("-", "."), s.replace("-", "/"), s.replace("-", "")):
            hits = [i for i in by_short.get(cand, []) if i.get("currencyCode") == "USD"
                    and i.get("type") in ("STOCK", "ETF")]
            hits.sort(key=lambda i: not str(i["ticker"]).endswith("_US_EQ"))
            if hits:
                return hits[0]["ticker"], True
        return guess, False

    def london(short: str) -> tuple[str, bool]:
        guess = f"{short}l_EQ"
        if instruments is None or not short:
            return guess, False
        hits = [i for i in by_short.get(short.upper(), []) if i.get("currencyCode") in ("GBP", "GBX")]
        return (hits[0]["ticker"], True) if hits else (guess, False)
    return us, london


# ---------------------------------------------------------------------------
# the orders
# ---------------------------------------------------------------------------

def work_out(plan: dict, acct: dict, cfg: dict) -> dict:
    res = plan["strategy"]
    rate = float(res.get("usd_per_gbp") or 1.0)
    fxf = float(cfg.get("fx_fee", 0.0015))
    buf = float(cfg.get("price_buffer", 0.015))
    minimum = float(cfg.get("min_order_gbp", 25))
    us, london = resolver(acct["instruments"])
    tr_tk, tr_ok = london(cfg.get("tracker", "VUAG"))
    bd_tk, bd_ok = london(cfg.get("bond", "")) if cfg.get("bond") else ("", False)
    ignore = {str(x) for x in cfg.get("ignore") or []}
    P = {k: v for k, v in acct["positions"].items() if k not in ignore}

    tr_px = (P.get(tr_tk) or {}).get("price_gbp") or yahoo_price_gbp(cfg.get("tracker_yahoo", ""))
    bd_px = (P.get(bd_tk) or {}).get("price_gbp") or yahoo_price_gbp(cfg.get("bond_yahoo", ""))

    want = {}                                   # T212 ticker -> plan holding
    unverified = []
    for h in res.get("holdings", []):
        tk, ok = us(h["ticker"])
        want[tk] = h
        if not ok:
            unverified.append(f"{h['ticker']} → {tk}")
    if not tr_ok:
        unverified.append(f"tracker {cfg.get('tracker')} → {tr_tk}")

    stocks_held = {k: v for k, v in P.items() if k not in (tr_tk, bd_tk)}
    left_alone = {k: v for k, v in stocks_held.items() if not k.endswith("_US_EQ")}
    stocks_held = {k: v for k, v in stocks_held.items() if k.endswith("_US_EQ")}
    tr_val = (P.get(tr_tk) or {}).get("value", 0.0)
    bd_val = (P.get(bd_tk) or {}).get("value", 0.0)
    cash = acct["cash"]
    total = cash + tr_val + bd_val + sum(v["value"] for v in stocks_held.values())

    sells, buys, notes = [], [], []

    def sell_all(tk, pos, why, name=None):
        sells.append({"side": "SELL", "ticker": tk, "name": name or pos.get("name", tk),
                      "qty": -round(pos["avail"], 6), "gbp": pos["value"], "why": why})
        return pos["value"] * (1 - (fxf if tk.endswith("_US_EQ") else 0))

    def buy_stock(tk, h, gbp, why):
        p = h.get("price_usd")
        if not p:
            notes.append(f"No price for {h['ticker']} -- order skipped")
            return 0.0
        q = floor_to(gbp * (1 - buf / 3) * (1 - fxf) * rate / p, 2)
        if q <= 0:
            notes.append(f"{h['ticker']}: £{gbp:,.0f} buys less than 0.01 shares -- skipped")
            return 0.0
        buys.append({"side": "BUY", "ticker": tk, "name": h["ticker"], "qty": q,
                     "gbp": q * p / rate * (1 + fxf), "usd_price": p, "why": why})
        return q * p / rate * (1 + fxf)

    def buy_fund(tk, px, gbp, label, why):
        if not tk or not px:
            notes.append(f"Can't buy the {label}: " + ("no fund chosen in config/t212.yml" if not tk
                                                        else "no price found") + f" (£{gbp:,.0f})")
            return 0.0
        q = floor_to(gbp * (1 - buf) / px, 2)
        if q * px >= minimum:
            buys.append({"side": "BUY", "ticker": tk, "name": label, "qty": q, "gbp": q * px,
                         "gbp_price": px, "why": why})
            return q * px
        return 0.0

    if not res.get("market_on", True):
        # everything into the bond fund
        for tk, pos in stocks_held.items():
            cash += sell_all(tk, pos, "Market switch OFF: the S&P 500 closed below its 200-day average 3 days running")
        if tr_val > minimum:
            cash += sell_all(tr_tk, P[tr_tk], "Market switch OFF", "S&P 500 tracker")
        if cash > minimum:
            buy_fund(bd_tk, bd_px, cash, "Bond fund", "Market switch OFF: money waits in bonds")
    else:
        if bd_val > minimum:
            cash += sell_all(bd_tk, P[bd_tk], "Market switch back ON: leave bonds", "Bond fund")
        for tk, pos in stocks_held.items():
            if tk not in want:
                cash += sell_all(tk, pos, "The strategy has sold it (3 weekly checks in the bottom half)")
        missing = [tk for tk in want if tk not in stocks_held]
        # how much each missing stock should get:
        #   bought by the strategy at its latest weekly check -> one slot, a tenth of the account
        #   held by the strategy for longer (new account, or a buy that never happened)
        #                                                     -> the strategy's current share of the pot
        pot = float(res.get("total_value") or res.get("pot") or 1)
        new_buys = {t for _, a, t, _ in res.get("this_week", []) if a == "BUY"}
        target = {}
        for tk in missing:
            h = want[tk]
            target[tk] = total / 10 if h["ticker"] in new_buys else total * h["value"] / pot
        need = sum(target.values()) - cash
        if need > minimum and tr_val > minimum and tr_px:
            q = min(ceil_to(min(need, tr_val) / tr_px, 2), (P.get(tr_tk) or {}).get("avail", 0))
            sells.append({"side": "SELL", "ticker": tr_tk, "name": "S&P 500 tracker", "qty": -q,
                          "gbp": q * tr_px, "why": "To pay for " + ", ".join(want[t]["ticker"] for t in missing)})
            tr_val -= q * tr_px
            cash += q * tr_px
        wanted = sum(target.values())
        scale = min(1.0, cash / wanted) if wanted else 1.0
        if scale < 0.99:
            notes.append(f"Not enough money for every buy in full (£{cash:,.0f} for £{wanted:,.0f}) "
                         f"-- each buy cut to {scale:.0%}")
        for tk in missing:
            h = want[tk]
            why = ("The strategy bought it: 3 weekly checks in a row in the top 5% of the S&P 500"
                   if h["ticker"] in new_buys else
                   f"The strategy holds it ({h['value'] / pot:.0%} of the pot) and this account doesn't yet")
            if target[tk] * scale >= minimum:
                cash -= buy_stock(tk, h, target[tk] * scale, why)
        if cash > minimum:
            cash -= buy_fund(tr_tk, tr_px, cash, "S&P 500 tracker",
                             "The rest waits in the tracker" if not stocks_held else "Spare cash goes into the tracker")

    # never sell and buy the tracker in the same run: keep only the difference
    trs = [o for o in sells if o["ticker"] == tr_tk]
    trb = [o for o in buys if o["ticker"] == tr_tk]
    if trs and trb:
        q = sum(o["qty"] for o in trs + trb)
        sells = [o for o in sells if o["ticker"] != tr_tk]
        buys = [o for o in buys if o["ticker"] != tr_tk]
        px = tr_px or 1
        if abs(q) * px >= minimum:
            o = dict(trs[0] if q < 0 else trb[0], qty=round(q, 2), gbp=abs(q) * px)
            (sells if q < 0 else buys).append(o)
    orders = sells + buys
    # ---- safety checks ------------------------------------------------------
    as_of = pd.Timestamp(plan.get("as_of", "1970-01-01"))
    age = (pd.Timestamp.now("UTC").tz_localize(None).normalize() - as_of).days
    mx = float(cfg.get("max_order_share", 0.30)) * max(total, 1)
    spend = sum(o["gbp"] for o in buys)
    raise_ = acct["cash"] + sum(o["gbp"] for o in sells)
    checks = [
        ("Plan is up to date", age <= 4, f"plan of {as_of.date()} ({age} days old)"),
        ("Strategy ran without errors", not plan.get("strategy_error"), ""),
        ("Account is in pounds", acct["currency"] == "GBP", str(acct["currency"])),
        ("No orders already waiting", None if acct["pending"] is None else not acct["pending"],
         "the key isn't allowed to see orders" if acct["pending"] is None else f"{len(acct['pending'])} pending"),
        ("Every ticker found on Trading 212", (not unverified) if acct["real"] else None,
         ("; ".join(unverified) if unverified else "all verified") if acct["real"]
         else "not checked yet -- needs the API key"),
        (f"No stock order above {cfg.get('max_order_share', 0.30):.0%} of the account",
         all(o["gbp"] <= mx + 1 for o in orders if o["ticker"].endswith("_US_EQ")),
         "applies to single stocks; whole-account moves into the tracker or bonds are allowed"),
        ("Buys covered by cash + sales", spend <= raise_ + 1, f"buys £{spend:,.0f} vs £{raise_:,.0f}"),
        ("Reading the real account", True if acct["real"] else None,
         "yes" if acct["real"] else "no API key yet -- shown as a new account holding the set-up deposit"),
    ]
    return {"orders": orders, "notes": notes, "checks": checks, "total": total, "cash_after": cash,
            "tracker": tr_tk, "tracker_price": tr_px, "rate": rate, "as_of": str(as_of.date())}


# ---------------------------------------------------------------------------
# report + email
# ---------------------------------------------------------------------------

def report(plan: dict, acct: dict, W: dict) -> tuple[str, str, str]:
    now = pd.Timestamp.now("Europe/London").strftime("%a %d %b %Y %H:%M")
    n = len(W["orders"])
    ok = all(c[1] is not False for c in W["checks"])
    subj = (f"T212 dry run: {n} order{'s' if n != 1 else ''} worked out - nothing sent"
            if n else "T212 dry run: no orders")
    L = [f"# Trading 212 orders — DRY RUN\n",
         f"_{now} UK time. Plan of {W['as_of']}. Exchange rate £1 = ${W['rate']:.4f}. "
         "**Nothing has been sent to Trading 212.**_\n",
         f"**Account:** {'your real account' if acct['real'] else 'pretend new account (no API key yet)'} — "
         f"worth £{W['total']:,.0f}, £{acct['cash']:,.0f} cash.\n"]
    if n:
        L += ["| # | Order | Trading 212 ticker | Shares | ≈ £ | Why |", "|---|---|---|---|---|---|"]
        for i, o in enumerate(W["orders"], 1):
            L.append(f"| {i} | **{o['side']}** {o['name']} | `{o['ticker']}` | {abs(o['qty']):,.2f} | "
                     f"£{o['gbp']:,.0f} | {o['why']} |")
        L.append("\n_Sells first, then buys. Share counts leave a small margin so a price rise before the "
                 "order fills can't overspend; the rest goes into the tracker next day._\n")
    else:
        L.append("**No orders.** The account already matches the strategy.\n")
    L += ["### Safety checks\n", "| Check | Result | Detail |", "|---|---|---|"]
    L += [f"| {c} | {'✅' if r else '➖' if r is None else '⚠️'} | {d} |" for c, r, d in W["checks"]]
    if W["notes"]:
        L += ["\n### Notes\n"] + [f"- {x}" for x in W["notes"]]
    md = "\n".join(L) + "\n"

    import html as _h
    e = _h.escape
    f = "font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;"
    td = "padding:7px 4px;border-bottom:1px solid #eaeef2;vertical-align:top"
    B = [f'<div style="{f}color:#1f2328;max-width:600px;margin:0 auto;padding:8px;font-size:16px;line-height:1.45">',
         '<div style="font-size:22px;font-weight:700">Trading 212 orders — dry run</div>',
         f'<div style="color:#57606a;margin-bottom:10px">{e(now)} · plan of {e(W["as_of"])} · £1 = ${W["rate"]:.4f}</div>',
         '<div style="background:#fff8c5;border-radius:8px;padding:10px 12px;font-weight:700;margin-bottom:12px">'
         'Nothing has been sent to Trading 212.</div>']
    for o in W["orders"]:
        col = "#1a7f37" if o["side"] == "BUY" else "#cf222e"
        B.append(f'<div style="border-left:6px solid {col};background:#f6f8fa;border-radius:6px;padding:10px 12px;margin:0 0 10px">'
                 f'<div style="font-size:18px;font-weight:800;color:{col}">{o["side"]} {e(o["name"])}</div>'
                 f'<div>{abs(o["qty"]):,.2f} shares of <code>{e(o["ticker"])}</code> ≈ £{o["gbp"]:,.0f}</div>'
                 f'<div style="color:#57606a;font-size:14px">{e(o["why"])}</div></div>')
    if not W["orders"]:
        B.append('<div style="background:#dafbe1;border-radius:8px;padding:12px;font-weight:700;color:#1a7f37">'
                 '✅ No orders — the account matches the strategy</div>')
    B.append('<div style="font-size:18px;font-weight:700;margin:18px 0 6px">Safety checks</div><table style="width:100%;border-collapse:collapse;font-size:14px">')
    for c, r, d in W["checks"]:
        B.append(f'<tr><td style="{td}">{"✅" if r else "➖" if r is None else "⚠️"}</td><td style="{td}">{e(c)}'
                 + (f'<div style="color:#57606a;font-size:12px">{e(d)}</div>' if d else "") + "</td></tr>")
    B.append("</table>")
    for x in W["notes"]:
        B.append(f'<div style="font-size:14px;color:#57606a;margin-top:6px">• {e(x)}</div>')
    B.append("</div>")
    if not ok:
        subj += " - check warnings"
    return md, "".join(B), subj


def main() -> int:
    import yaml
    cfg = yaml.safe_load(CFG.read_text()) if CFG.exists() else {}
    plan = json.loads((DOCS / "plan.json").read_text())
    for f in ("ORDERS_EMAIL.html", "ORDERS_EMAIL.md", "ORDERS_SUBJECT.txt"):
        (DOCS / f).unlink(missing_ok=True)
    if not plan.get("strategy"):
        (DOCS / "ORDERS.md").write_text("# Trading 212 orders — DRY RUN\n\nNo strategy in last night's plan; nothing worked out.\n")
        return 0
    key, sec = os.environ.get("T212_API_KEY", ""), os.environ.get("T212_API_SECRET", "")
    api = T212(key, sec) if key and sec else None
    acct = read_account(api, plan)
    W = work_out(plan, acct, cfg)
    md, html, subj = report(plan, acct, W)
    # Your real account (money, share counts) is NEVER written to the repository or
    # the run log: a public repo and its run logs can be read by anyone. It goes
    # only to your email. With no key (pretend account) the full page is published.
    if acct["real"]:
        pub = ("# Trading 212 orders — DRY RUN\n\n"
               f"_{pd.Timestamp.now('Europe/London').strftime('%a %d %b %Y %H:%M')} UK time. Plan of {W['as_of']}._\n\n"
               "Your real account was read. Its figures are sent only by email and are not published here.\n\n"
               + (f"**{len(W['orders'])} order(s) worked out** — see your email.\n" if W["orders"] else
                  "**No orders.** The account already matches the strategy.\n")
               + "\n| Check | Result |\n|---|---|\n"
               + "".join(f"| {c} | {'✅' if r else '➖' if r is None else '⚠️'} |\n" for c, r, _ in W["checks"]))
    else:
        pub = md
    (DOCS / "ORDERS.md").write_text(pub)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    sig = sorted((o["side"], o["ticker"]) for o in W["orders"])
    prev = None
    if LOG.exists():
        rows = [json.loads(x) for x in LOG.read_text().splitlines() if x.strip()]
        if rows:
            prev = sorted((o["side"], o["ticker"]) for o in rows[-1].get("orders", []))
    changed = sig != prev
    with LOG.open("a") as fh:
        fh.write(json.dumps({"run": pd.Timestamp.now("UTC").isoformat(), "plan": W["as_of"],
                             "real_account": acct["real"],
                             "total": None if acct["real"] else round(W["total"], 2),
                             "orders": [{"side": o["side"], "ticker": o["ticker"]} if acct["real"] else
                                        {k: (round(v, 4) if isinstance(v, float) else v) for k, v in o.items()}
                                        for o in W["orders"]],
                             "checks_ok": all(c[1] is not False for c in W["checks"])}) + "\n")
    # email when the orders change, or a safety check fails -- not the same list every day
    if (W["orders"] and changed) or not all(c[1] is not False for c in W["checks"]):
        (DOCS / "ORDERS_EMAIL.md").write_text(md)
        (DOCS / "ORDERS_EMAIL.html").write_text(html)
        (DOCS / "ORDERS_SUBJECT.txt").write_text(subj + "\n")
    print(pub)                              # run logs of a public repo are public too
    return 0


if __name__ == "__main__":
    sys.exit(main())
