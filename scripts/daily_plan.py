#!/usr/bin/env python3
"""
The daily plan: what to do with what you own, and what you should own.

TWO OUTPUTS, EVERY WEEKDAY
--------------------------
1. YOUR HOLDINGS   one clear action per stock: BUY (add), HOLD, or SELL.
2. THE MODEL       the GBP 10,000 portfolio the rules say to hold today, picked
                   from the whole S&P 500, with the amount in each.

Written to docs/PLAN.md (readable on GitHub) and docs/plan.json.

WHAT THE RULES ARE, AND WHY THESE ONES
--------------------------------------
Only rules that survived the tests make decisions here:

  MARKET SWITCH   the S&P 500 against its 200-day average, needing three
                  consecutive closes to flip. Over a century this cut the loss
                  in 5 of 6 major bear markets. When it is OFF, the model is
                  cash and every holding is SELL.

  INDUSTRY        GICS sub-industries ranked by average 3/6/12-month momentum.
                  Holding the strongest industries beat the market by about
                  5% a year over 1927-1999 on data the rule had never seen
                  (t above 5), and by about 4% a year since 2000. This is the
                  part with real evidence, so it drives the choice.

  STOCK TREND     a stock is in a confirmed DOWNTREND when it is below its
                  200-day average and its 50-day average is below its 200-day,
                  for three consecutive closes. This is insurance, not a
                  forecast: it rescued the collapses and cost on the
                  recoveries. It is the SELL trigger for a single stock.

  STOCK RANK      within the strong industries, the strongest stocks by the
                  same 3/6/12-month momentum. Plausible and widely documented,
                  but NOT separately proven in this project.

THE MODEL PORTFOLIO
-------------------
  - 10 stocks, GBP 1,000 each, from industries in the top fifth by momentum,
    that are in an uptrend, strongest first; at most 2 per sub-industry and 3
    per sector so no single theme dominates.
  - Rebalanced on the first trading day of each month -- the evidence is for
    monthly rotation, and Hargreaves Lansdown charges about GBP 11.95 a trade
    plus FX on US shares, so churn is expensive. Between rebalances a model
    holding is only replaced if it hits a SELL condition.
  - Hysteresis: a holding stays while its industry is still in the top 40%
    and it is not in a downtrend. New entries must be in the top 20%. That
    stops stocks flickering in and out.

YOUR HOLDINGS
-------------
  SELL  market switch OFF; or confirmed downtrend; or industry in the bottom
        fifth AND the stock below its 200-day average.
  BUY   qualifies to add: industry in the top fifth AND a confirmed uptrend.
  HOLD  everything else. "No signal" is a HOLD, not a guess.

This is what tested rules say. It is not personal financial advice.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CONSTITUENTS = ("https://raw.githubusercontent.com/datasets/"
                "s-and-p-500-companies/main/data/constituents.csv")
BUDGET = 10_000.0
N_MODEL = 10
MAX_PER_SUB, MAX_PER_SECTOR = 2, 3
ENTER_PCT, KEEP_PCT = 0.20, 0.40
MIN_SUB = 3                      # sub-industries smaller than this use sector
CONFIRM = 3
DEAL_GBP, FX_PCT = 11.95, 0.01   # HL share dealing and FX on US shares, approx

# Holdings the S&P 500 list does not cover. An `industry:` field in
# config/holdings.yml overrides these.
INDUSTRY_OVERRIDE = {
    "CELH": ("Consumer Staples", "Soft Drinks & Non-alcoholic Beverages"),
    "TEM": ("Health Care", "Health Care Services"),
    "SPCX": ("Industrials", "Aerospace & Defense"),
    "FRES.L": ("Materials", "Gold"),
    "IQE.L": ("Information Technology", "Semiconductors"),
    "ZOO.L": ("Communication Services", "Movies & Entertainment"),
    "LIT.L": ("Financials", "Asset Management & Custody Banks"),
    "DEBS.L": ("Consumer Discretionary", "Broadline Retail"),
}


def yf_symbol(s: str) -> str:
    return s.strip().replace(".", "-") if not s.endswith(".L") else s.strip()


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

def load_constituents(src=CONSTITUENTS) -> pd.DataFrame:
    d = pd.read_csv(src)
    d["yf"] = d["Symbol"].map(yf_symbol)
    return d[["Symbol", "yf", "Security", "GICS Sector", "GICS Sub-Industry"]]


def load_holdings(path="config/holdings.yml") -> list[dict]:
    import yaml
    cfg = yaml.safe_load(Path(path).read_text()) or {}
    return [h for h in (cfg.get("holdings") or []) if h.get("ticker")]


def download(tickers: list[str]) -> pd.DataFrame:
    import yfinance as yf
    frames = []
    for i in range(0, len(tickers), 100):
        chunk = tickers[i:i + 100]
        d = yf.download(chunk, period="2y", auto_adjust=True, progress=False,
                        threads=True, group_by="column")
        c = d["Close"] if isinstance(d.columns, pd.MultiIndex) else d[["Close"]].rename(
            columns={"Close": chunk[0]})
        frames.append(c)
    P = pd.concat(frames, axis=1)
    P = P.loc[:, ~P.columns.duplicated()].sort_index()
    return P.dropna(how="all")


# ---------------------------------------------------------------------------
# signals
# ---------------------------------------------------------------------------

def last_valid(s: pd.Series, i: int):
    v = s.iloc[: i + 1].dropna()
    return v.iloc[-1] if len(v) else np.nan


def momentum(P: pd.DataFrame) -> pd.Series:
    """Average of 3, 6 and 12-month return, the pre-registered definition."""
    out = {}
    for c in P.columns:
        s = P[c].dropna()
        if len(s) < 253:
            out[c] = np.nan
            continue
        out[c] = np.mean([s.iloc[-1] / s.iloc[-1 - n] - 1 for n in (63, 126, 252)])
    return pd.Series(out)


def trend_table(P: pd.DataFrame) -> pd.DataFrame:
    rows = {}
    for c in P.columns:
        s = P[c].dropna()
        if len(s) < 200:
            rows[c] = {"trend": "insufficient", "price": s.iloc[-1] if len(s) else np.nan,
                       "vs200": np.nan}
            continue
        ma50 = s.rolling(50).mean()
        ma200 = s.rolling(200).mean()
        down = ((s < ma200) & (ma50 < ma200)).astype(int)
        up = ((s > ma200) & (ma50 > ma200)).astype(int)
        confirmed_down = down.iloc[-CONFIRM:].sum() == CONFIRM
        confirmed_up = up.iloc[-CONFIRM:].sum() == CONFIRM
        rows[c] = {"trend": "down" if confirmed_down else ("up" if confirmed_up else "mixed"),
                   "price": float(s.iloc[-1]),
                   "vs200": float(s.iloc[-1] / ma200.iloc[-1] - 1)}
    return pd.DataFrame(rows).T


def market_switch(spy: pd.Series) -> dict:
    s = spy.dropna()
    ma = s.rolling(200).mean()
    above = (s > ma).astype(int)
    below = (s < ma).astype(int)
    # the switch only flips on three consecutive closes the other side
    state = True
    runs_a = above.rolling(CONFIRM).sum() == CONFIRM
    runs_b = below.rolling(CONFIRM).sum() == CONFIRM
    for i in range(len(s)):
        if state and runs_b.iat[i]:
            state = False
        elif not state and runs_a.iat[i]:
            state = True
    return {"on": bool(state), "spy": float(s.iloc[-1]), "ma200": float(ma.iloc[-1]),
            "vs200": float(s.iloc[-1] / ma.iloc[-1] - 1),
            "ret_12m": float(s.iloc[-1] / s.iloc[-253] - 1) if len(s) > 253 else None}


def industry_ranks(univ: pd.DataFrame, mom: pd.Series) -> pd.DataFrame:
    """Percentile rank of each stock's industry (1.0 = strongest)."""
    u = univ.copy()
    u["mom"] = u["yf"].map(mom)
    sub_n = u.groupby("GICS Sub-Industry")["yf"].transform("count")
    u["group"] = np.where(sub_n >= MIN_SUB, u["GICS Sub-Industry"], "SECTOR:" + u["GICS Sector"])
    g = u.groupby("group")["mom"].mean().dropna()
    pct = g.rank(pct=True)
    u["ind_mom"] = u["group"].map(g)
    u["ind_pct"] = u["group"].map(pct)
    return u, g.sort_values(ascending=False)


def group_of(sub: str, sector: str, groups: pd.Index) -> str:
    return sub if sub in groups else "SECTOR:" + sector


# ---------------------------------------------------------------------------
# the plan
# ---------------------------------------------------------------------------

def build_model(u: pd.DataFrame, tr: pd.DataFrame, prev: list[str],
                rebalance: bool, mkt_on: bool) -> tuple[list[dict], list[str]]:
    notes = []
    if not mkt_on:
        notes.append("Market switch is OFF: the model holds cash.")
        return [], notes
    u = u.join(tr, on="yf")
    ok = u["trend"] == "up"
    held = []
    # keep existing model holdings unless they break (hysteresis)
    for t in prev:
        r = u[u["yf"] == t]
        if r.empty:
            notes.append(f"{t} left the S&P 500 list: dropped.")
            continue
        r = r.iloc[0]
        if r["trend"] == "down":
            notes.append(f"{t} is in a confirmed downtrend: SELL.")
            continue
        if rebalance and not (r["ind_pct"] >= 1 - KEEP_PCT):
            notes.append(f"{t}'s industry fell out of the top 40%: replaced at rebalance.")
            continue
        held.append(t)
    need = N_MODEL - len(held)
    if need > 0 and (rebalance or not prev):
        cand = u[ok & (u["ind_pct"] >= 1 - ENTER_PCT) & u["mom"].notna()
                 & ~u["yf"].isin(held)].sort_values("mom", ascending=False)
        subs = u[u["yf"].isin(held)]["GICS Sub-Industry"].value_counts().to_dict()
        secs = u[u["yf"].isin(held)]["GICS Sector"].value_counts().to_dict()
        for _, r in cand.iterrows():
            if need == 0:
                break
            if subs.get(r["GICS Sub-Industry"], 0) >= MAX_PER_SUB:
                continue
            if secs.get(r["GICS Sector"], 0) >= MAX_PER_SECTOR:
                continue
            held.append(r["yf"]); need -= 1
            subs[r["GICS Sub-Industry"]] = subs.get(r["GICS Sub-Industry"], 0) + 1
            secs[r["GICS Sector"]] = secs.get(r["GICS Sector"], 0) + 1
    elif need > 0:
        notes.append(f"{need} slot(s) held in cash until the next monthly rebalance.")
    per = BUDGET / N_MODEL
    out = []
    for t in held:
        r = u[u["yf"] == t].iloc[0]
        out.append({"ticker": r["Symbol"], "yf": t, "name": r["Security"],
                    "sector": r["GICS Sector"], "industry": r["GICS Sub-Industry"],
                    "industry_rank_pct": round(float(r["ind_pct"]), 3),
                    "momentum": round(float(r["mom"]), 4), "gbp": per,
                    "price": round(float(r["price"]), 2)})
    return out, notes


def judge_holding(h: dict, u: pd.DataFrame, groups: pd.Series, gpct: pd.Series,
                  tr: pd.DataFrame, mom: pd.Series, model: list[str],
                  mkt_on: bool) -> dict:
    t = yf_symbol(h["ticker"])
    row = u[u["yf"] == t]
    if len(row):
        sector, sub = row.iloc[0]["GICS Sector"], row.iloc[0]["GICS Sub-Industry"]
    else:
        sector, sub = INDUSTRY_OVERRIDE.get(h["ticker"], ("Unknown", "Unknown"))
        if h.get("industry"):
            sub = h["industry"]
    g = group_of(sub, sector, groups.index)
    ipct = float(gpct.get(g, np.nan))
    order = list(groups.index)
    irank = order.index(g) + 1 if g in order else None
    trend = tr.loc[t, "trend"] if t in tr.index else "insufficient"
    vs200 = tr.loc[t, "vs200"] if t in tr.index else np.nan
    price = tr.loc[t, "price"] if t in tr.index else np.nan
    reason = []
    if not mkt_on:
        act = "SELL"; reason.append("the whole market's trend has broken -- rules move to cash")
    elif trend == "insufficient":
        act = "HOLD"; reason.append("too little price history to judge -- no signal")
    elif trend == "down":
        act = "SELL"; reason.append("confirmed downtrend: below its 200-day, 50-day below 200-day")
    elif np.isfinite(ipct) and ipct <= ENTER_PCT and np.isfinite(vs200) and vs200 < 0:
        act = "SELL"; reason.append("weak industry (bottom fifth) and below its 200-day")
    elif trend == "up" and np.isfinite(ipct) and ipct >= 1 - ENTER_PCT:
        act = "BUY"
        reason.append("strong industry (top fifth) and a confirmed uptrend -- qualifies to add"
                      + (" (also in the model)" if t in model else ""))
    else:
        act = "HOLD"
        if trend == "up":
            reason.append("uptrend" + (", industry in the top fifth" if ipct >= 1 - ENTER_PCT
                                       else ", industry not in the top fifth"))
        else:
            reason.append("no confirmed trend either way")
    return {"ticker": h["ticker"], "name": h.get("name", h["ticker"]), "action": act,
            "why": "; ".join(reason), "industry": sub,
            "industry_rank_pct": None if not np.isfinite(ipct) else round(ipct, 3),
            "industry_rank": irank, "industries_total": len(order),
            "trend": trend, "vs_200d": None if not np.isfinite(vs200) else round(float(vs200), 4),
            "price": None if not np.isfinite(price) else round(float(price), 2),
            "momentum": None if t not in mom or not np.isfinite(mom.get(t, np.nan))
            else round(float(mom[t]), 4)}


def write_markdown(plan: dict, path: Path):
    m = plan["market"]
    L = []
    L.append(f"# Daily plan — {plan['as_of']}\n")
    L.append(f"_Generated {plan['generated'][:16].replace('T', ' ')} UTC from closing prices "
             f"of {plan['as_of']}. Tested rules, not personal financial advice._\n")
    L.append(f"## Market: **{'RISK ON — invested' if m['on'] else 'RISK OFF — cash'}**\n")
    L.append(f"S&P 500 {m['vs200']:+.1%} vs its 200-day average"
             + (f", {m['ret_12m']:+.1%} over 12 months." if m.get('ret_12m') is not None else ".")
             + "\n")
    L.append("## 1. Your holdings\n")
    L.append("| Action | Stock | Why | Industry (rank) | Trend |")
    L.append("|---|---|---|---|---|")
    order = {"SELL": 0, "BUY": 1, "HOLD": 2}
    for h in sorted(plan["holdings"], key=lambda x: (order[x["action"]], x["ticker"])):
        rk = "" if not h.get("industry_rank") else f" (#{h['industry_rank']} of {h['industries_total']})"
        L.append(f"| **{h['action']}** | {h['ticker']} — {h['name']} | {h['why']} | "
                 f"{h['industry']}{rk} | {h['trend']} |")
    L.append("\n## 2. What you should own — £10,000 model portfolio\n")
    if not plan["model"]:
        L.append("**Hold cash (a money-market fund).** " + " ".join(plan["model_notes"]) + "\n")
    else:
        L.append(f"_{'Rebalance day.' if plan['rebalance_day'] else 'Between rebalances — changes only on a SELL.'}"
                 f" Next rebalance: first trading day of next month._\n")
        L.append("| Action | Stock | £ | Industry | Momentum |")
        L.append("|---|---|---|---|---|")
        owned = {x["ticker"] for x in plan["holdings"]}
        for r in plan["model"]:
            act = "HOLD" if r["ticker"] in owned or r["yf"] in plan.get("prev_model", []) else "BUY"
            L.append(f"| **{act}** | {r['ticker']} — {r['name']} | £{r['gbp']:,.0f} | "
                     f"{r['industry']} | {r['momentum']:+.0%} |")
        if plan["model_notes"]:
            L.append("\n" + "\n".join(f"- {n}" for n in plan["model_notes"]))
    if plan.get("changes"):
        L.append("\n## Changes since the last run\n")
        L.extend(f"- {c}" for c in plan["changes"])
    L.append("\n## Strongest industries today\n")
    L.append(", ".join((f"{k[7:]} (sector)" if k.startswith("SECTOR:") else k) + f" {v:+.0%}"
                       for k, v in plan["top_industries"][:10]))
    L.append(f"\n\n---\n_Costs: about £{DEAL_GBP} per trade on Hargreaves Lansdown plus "
             f"~{FX_PCT:.0%} FX on US shares. A full 10-stock rebuild costs roughly "
             f"£{N_MODEL * DEAL_GBP + BUDGET * FX_PCT:,.0f}, which is why the model rebalances monthly "
             f"and keeps holdings until they break. SELL on a single stock is insurance, not a "
             f"forecast: historically it rescued collapses and cost on recoveries._")
    path.write_text("\n".join(L) + "\n")


def run(P: pd.DataFrame, univ: pd.DataFrame, holdings: list[dict], state_path: Path,
        today=None) -> dict:
    P = P.dropna(how="all")
    as_of = P.index[-1]
    mom = momentum(P)
    tr = trend_table(P)
    mk = market_switch(P["SPY"])
    u, groups = industry_ranks(univ, mom)
    gpct = groups.rank(pct=True)
    prev = {}
    if state_path.exists():
        prev = json.loads(state_path.read_text())
    prev_model = prev.get("model", [])
    last_month = prev.get("as_of", "")[:7]
    rebalance = (not prev_model) or last_month != str(as_of.date())[:7]
    model, notes = build_model(u, tr, prev_model, rebalance, mk["on"])
    model_yf = [m["yf"] for m in model]
    hold = [judge_holding(h, u, groups, gpct, tr, mom, model_yf, mk["on"]) for h in holdings]
    changes = []
    old_act = {h["ticker"]: h["action"] for h in prev.get("holdings", [])}
    for h in hold:
        if old_act.get(h["ticker"]) and old_act[h["ticker"]] != h["action"]:
            changes.append(f"{h['ticker']}: {old_act[h['ticker']]} → **{h['action']}**")
    for t in set(prev_model) - set(model_yf):
        changes.append(f"Model: **SELL** {t}")
    for t in set(model_yf) - set(prev_model):
        changes.append(f"Model: **BUY** {t}")
    if prev.get("market_on") is not None and prev["market_on"] != mk["on"]:
        changes.insert(0, f"MARKET SWITCH → **{'ON' if mk['on'] else 'OFF'}**")
    plan = {"generated": pd.Timestamp.now("UTC").isoformat(), "as_of": str(as_of.date()),
            "market": mk, "rebalance_day": bool(rebalance), "holdings": hold,
            "model": model, "model_notes": notes, "prev_model": prev_model,
            "changes": changes,
            "top_industries": [(k, float(v)) for k, v in groups.head(15).items()]}
    state_path.write_text(json.dumps({"as_of": plan["as_of"], "model": model_yf,
                                      "market_on": mk["on"],
                                      "holdings": [{"ticker": h["ticker"], "action": h["action"]}
                                                   for h in hold]}, indent=2))
    return plan


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdings", default="config/holdings.yml")
    ap.add_argument("--constituents", default=CONSTITUENTS)
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--prices-out", default="data/live_prices.csv")
    a = ap.parse_args()
    docs = Path(a.docs); docs.mkdir(parents=True, exist_ok=True)
    try:
        univ = load_constituents(a.constituents)
        holdings = load_holdings(a.holdings)
        tickers = sorted(set(univ["yf"]) | {yf_symbol(h["ticker"]) for h in holdings} | {"SPY"})
        print(f"downloading {len(tickers)} tickers")
        P = download(tickers)
        Path(a.prices_out).parent.mkdir(parents=True, exist_ok=True)
        P.to_csv(a.prices_out, float_format="%.4f")
        plan = run(P, univ, holdings, docs / "plan_state.json")
        (docs / "plan.json").write_text(json.dumps(plan, indent=2, default=str))
        write_markdown(plan, docs / "PLAN.md")
        print((docs / "PLAN.md").read_text())
        return 0
    except Exception as exc:                                       # noqa: BLE001
        import traceback
        (docs / "plan_error.json").write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(),
             "error": f"{type(exc).__name__}: {exc}",
             "traceback": traceback.format_exc().splitlines()[-25:]}, indent=2))
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
