#!/usr/bin/env python3
"""
Year by year: what WOULD the daily plan have told you to own, and did those
stocks actually go on to do best?

WHAT IS TESTED
--------------
The exact code that writes docs/PLAN.md -- scripts/daily_plan.py's run() -- is
called once a month from 1998 to today, each time seeing ONLY the prices up to
that day, and ONLY stocks that were in the S&P 500 on that day (no picking from
a list of companies already known to have succeeded). Between rebalances the
plan's own daily SELL rules apply: a pick in a confirmed downtrend is sold to
cash, and when the market switch turns off everything goes to cash.

Costs are Hargreaves Lansdown's 2026 tariff: GBP 6.95 a deal, plus tiered FX on every US buy
and every sale. Cash earns 2% a year.

THE QUESTIONS IT ANSWERS
------------------------
  1. Money: GBP 10,000 in the plan vs GBP 10,000 in the S&P 500, every year.
  2. Did the ranking PREDICT? Each month, every eligible stock's score is
     compared with what it did over the NEXT 12 months. If the score has no
     predictive power, the top tenth by score does no better than the bottom
     tenth, and the rank correlation is zero.
  3. Hit rate: of the ten picked, how many beat the S&P 500 over the next year?
  4. The ten actual best stocks of each year -- how many did the plan hold?

Two versions are run: with themes (the current plan) and with official
industries only, so the effect of themes is measured, not assumed.

KNOWN BIAS, STATED UP FRONT
---------------------------
Yahoo has no prices for most companies that went bust or were taken over.
Where the Alpha Vantage delisted archive (data/delisted) has them, they are
merged in; the rest are missing. Missing failures flatter any stock picker,
so a pass here is necessary, not sufficient.

PASS BAR (the same bar every test in this repo has used)
--------------------------------------------------------
Beat the S&P 500 by at least 1% a year after costs AND have a better
return-to-worst-drawdown (Calmar), in BOTH 1998-2012 AND 2013-today.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


dp = _load("dp", "daily_plan.py")

import os
# pot size: set POT_GBP in the workflow (default GBP 10,000)
START_GBP = float(os.environ.get("POT_GBP", "10000") or 10000)
# Hargreaves Lansdown, 2026 tariff: GBP 6.95 an online deal (0-19 deals a month);
# FX on US shares tiered by the size of each trade: 1% on the first GBP 5,000,
# 0.75% on the next 5,000, 0.5% on the next 10,000, 0.25% above 20,000.
# Which broker's charges to model: BROKER=hl (default), t212 or ibkr.
#   hl    Hargreaves Lansdown: GBP 6.95 a deal; FX 1% / 0.75% / 0.5% / 0.25% tiers
#   t212  Trading 212: no dealing charge; 0.15% FX
#   ibkr  Interactive Brokers UK: about GBP 1 a US deal; about 0.03% FX
BROKER = (os.environ.get("BROKER", "hl") or "hl").strip().lower()
DEAL = {"hl": 6.95, "t212": 0.0, "ibkr": 1.0}.get(BROKER, 6.95)
FX = 0.01                                  # kept for the report text
BROKER_NAME = {"hl": "Hargreaves Lansdown", "t212": "Trading 212",
               "ibkr": "Interactive Brokers"}.get(BROKER, "Hargreaves Lansdown")


def fx_cost(v: float) -> float:
    v = max(float(v), 0.0)
    if BROKER == "t212":
        return v * 0.0015
    if BROKER == "ibkr":
        return v * 0.0003
    return (min(v, 5000) * 0.01 + min(max(v - 5000, 0), 5000) * 0.0075
            + min(max(v - 10000, 0), 10000) * 0.005 + max(v - 20000, 0) * 0.0025)


def out_tag(pot: float) -> str:
    """Suffix for report files, so each pot/broker combination keeps its own page."""
    t = "" if pot == 10_000 else f"_{int(pot / 1000)}k"
    return t + ("" if BROKER == "hl" else f"_{BROKER}")
CASH = 0.02
WINDOW = 320                       # trading days of history run() sees
SPLIT = pd.Timestamp("2013-01-01")
MARGIN = 0.01


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

def load_panel(prices: str, delisted: str) -> tuple[pd.DataFrame, dict]:
    info = {}
    px = pd.read_parquet(prices)
    px["date"] = pd.to_datetime(px["date"])
    C = px.pivot_table(index="date", columns="ticker", values="close").sort_index()
    info["yahoo_stocks"] = int(C.shape[1])
    try:
        d = pd.read_parquet(delisted)
        d.columns = [c.lower() for c in d.columns]
        col = next(c for c in ("adjusted_close", "adj_close", "adjclose", "close") if c in d)
        d["date"] = pd.to_datetime(d["date"])
        W = d.pivot_table(index="date", columns="ticker", values=col).sort_index()
        new = [c for c in W.columns if c not in C.columns]
        # weekly bars onto the daily grid: carry each weekly close forward for
        # at most one week, and stop at the last bar (delisting)
        W = W[new].reindex(C.index.union(W.index)).ffill(limit=5).reindex(C.index)
        for c in new:
            last = d.loc[d["ticker"] == c, "date"].max()
            W.loc[W.index > last, c] = np.nan
        C = pd.concat([C, W], axis=1)
        info["delisted_added"] = len(new)
    except Exception as e:                                         # noqa: BLE001
        info["delisted_added"] = 0
        info["delisted_error"] = f"{type(e).__name__}: {e}"
    return C, info


MEMBERSHIP_URL = ("https://raw.githubusercontent.com/hanshof/sp500_constituents/"
                  "main/sp_500_historical_components.csv")


def membership_mask(idx, cols, url=MEMBERSHIP_URL):
    """
    A stock is eligible on a date only if it was IN the S&P 500 on that date.
    Choosing from today's members would be choosing from companies already
    known to have succeeded. The file is dated snapshots; each holds until the
    next. (Kept inside this script so it depends on no other file.)
    """
    h = pd.read_csv(url)
    h["date"] = pd.to_datetime(h["date"])
    h = h.sort_values("date")
    norm = lambda x: x.strip().upper().replace(".", "-")          # noqa: E731
    col_pos = {norm(c): i for i, c in enumerate(cols)}
    M = np.zeros((len(idx), len(cols)), bool)
    snap_dates = h["date"].to_numpy()
    snaps = [[col_pos[norm(t)] for t in str(r).split(",")
              if t.strip() and norm(t) in col_pos] for r in h["tickers"]]
    pos = np.searchsorted(snap_dates, idx.to_numpy(), side="right") - 1
    for t in range(len(idx)):
        if pos[t] >= 0:
            M[t, snaps[pos[t]]] = True
    return M


def load_spy(idx: pd.DatetimeIndex, log=print) -> pd.Series:
    """S&P 500 (SPY, dividends included). Several routes, because one failing
    download must not sink an hour-long test."""
    import time
    import yfinance as yf
    for attempt in range(4):
        for how in ("download", "history"):
            try:
                if how == "download":
                    d = yf.download("SPY", start="1993-01-01", auto_adjust=True, progress=False)
                    s = d["Close"]
                    s = s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s
                else:
                    s = yf.Ticker("SPY").history(period="max", auto_adjust=True)["Close"]
                s.index = pd.to_datetime(s.index)
                if s.index.tz is not None:
                    s.index = s.index.tz_localize(None)
                s.index = s.index.normalize()
                s = s[~s.index.duplicated()].sort_index()
                if len(s) > 1000:
                    return s.reindex(idx).ffill()
            except Exception as e:                                 # noqa: BLE001
                log(f"  SPY via {how} failed: {type(e).__name__}: {e}")
        time.sleep(15 * (attempt + 1))
    return pd.Series(dtype=float)


# ---------------------------------------------------------------------------
# the simulation
# ---------------------------------------------------------------------------

def downtrend_flags(C: pd.DataFrame) -> pd.DataFrame:
    """The plan's daily SELL rule, for every stock on every day at once."""
    ma50 = C.rolling(50, min_periods=50).mean()
    ma200 = C.rolling(200, min_periods=200).mean()
    down = ((C < ma200) & (ma50 < ma200)).astype(int)
    return down.rolling(dp.CONFIRM).sum() == dp.CONFIRM


def market_state(spy: pd.Series) -> pd.Series:
    s = spy.dropna()
    ma = s.rolling(200).mean()
    a = ((s > ma).astype(int).rolling(dp.CONFIRM).sum() == dp.CONFIRM).to_numpy()
    b = ((s < ma).astype(int).rolling(dp.CONFIRM).sum() == dp.CONFIRM).to_numpy()
    st, out = True, []
    for i in range(len(s)):
        if st and b[i]:
            st = False
        elif not st and a[i]:
            st = True
        out.append(st)
    return pd.Series(out, index=s.index).reindex(spy.index).ffill().fillna(True)


def simulate(C, member, spy, univ_labels, use_themes, log=print):
    idx = C.index
    cols = list(C.columns)
    cp = {c: k for k, c in enumerate(cols)}
    down = downtrend_flags(C).to_numpy()
    mkt = market_state(spy).reindex(idx).fillna(True).to_numpy()
    X = C.to_numpy(float)
    months = pd.Series(idx, index=idx).groupby(idx.to_period("M")).first()
    rebal = [idx.get_loc(d) for d in months if idx.get_loc(d) >= WINDOW]
    real_themes = dp.themes
    if not use_themes:
        dp.themes = lambda *a, **k: (pd.Series(dtype=float), pd.DataFrame())
    state = Path(tempfile.mkdtemp()) / "state.json"
    cash, pos = START_GBP, {}          # pos: ticker -> shares
    eq = np.full(len(idx), np.nan)
    picks_log, ic_rows = [], []
    costs = 0.0
    rb_set = set(rebal)
    last_px = {}
    try:
        for i in range(rebal[0], len(idx)):
            # mark to market; a stock with no price today keeps its last price,
            # and one that has stopped trading for good is sold at that price
            val = 0.0
            for t in list(pos):
                k = cp.__getitem__(t)
                p = X[i, k]
                if np.isfinite(p):
                    last_px[t] = p
                elif not np.isfinite(X[i:min(i + 10, len(idx)), k]).any():
                    amt = pos.pop(t) * last_px[t]
                    cash += amt - fx_cost(amt) - DEAL
                    costs += DEAL + fx_cost(amt)
                    continue
                val += pos[t] * last_px[t]
            cash *= (1 + CASH) ** (1 / 252)
            eq[i] = cash + val
            # the plan's daily SELL rules between rebalances
            if i not in rb_set:
                sell = list(pos) if not mkt[i] else [t for t in pos if down[i, cp.__getitem__(t)]]
                for t in sell:
                    amt = pos.pop(t) * last_px[t]
                    cash += amt - fx_cost(amt) - DEAL
                    costs += DEAL + fx_cost(amt)
                continue
            # monthly: ask the real plan what to own
            live = [c for k, c in enumerate(cols) if member[i, k] and np.isfinite(X[i, k])]
            live = list(dict.fromkeys(live + [t for t in pos]))
            P = C.iloc[i - WINDOW + 1:i + 1][live].copy()
            P["SPY"] = spy.iloc[i - WINDOW + 1:i + 1].to_numpy()
            u = univ_labels.reindex(live).reset_index()
            u.columns = ["yf", "Security", "GICS Sector", "GICS Sub-Industry"]
            u["Symbol"] = u["yf"]
            u["Security"] = u["Security"].fillna(u["yf"])
            u["GICS Sector"] = u["GICS Sector"].fillna("Unknown")
            u["GICS Sub-Industry"] = u["GICS Sub-Industry"].fillna("")
            dp._PIN.clear()
            plan = dp.run(P, u, [], state)
            want = [m["yf"] for m in plan["model"]]
            # prediction check: every eligible stock's score vs its next 12 months
            sc = dp.stock_score(P.drop(columns="SPY")).dropna()
            j12 = min(i + 252, len(idx) - 1)
            if j12 - i >= 200 and len(sc) > 50:
                fwd = pd.Series(X[j12, [cp.__getitem__(t) for t in sc.index]] /
                                X[i, [cp.__getitem__(t) for t in sc.index]] - 1, index=sc.index)
                ok = fwd.notna()
                s2, f2 = sc[ok], fwd[ok]
                q = s2.rank(pct=True)
                spy12 = spy.iloc[j12] / spy.iloc[i] - 1
                j1 = min(i + 21, len(idx) - 1)
                f1 = pd.Series(X[j1, [cp.__getitem__(t) for t in s2.index]] /
                               X[i, [cp.__getitem__(t) for t in s2.index]] - 1, index=s2.index)
                ic_rows.append({
                    "date": str(idx[i].date()),
                    "ic_12m": float(s2.rank().corr(f2.rank())),
                    "ic_1m": float(s2.rank().corr(f1.rank())) if f1.notna().sum() > 50 else np.nan,
                    "top10pct_12m": float(f2[q >= 0.9].mean()),
                    "bottom10pct_12m": float(f2[q <= 0.1].mean()),
                    "all_12m": float(f2.mean()),
                    "spy_12m": float(spy12),
                    "picks_beat_spy": int(sum(1 for t in want if t in f2 and f2[t] > spy12)),
                    "picks_n": len(want)})
            # trade to the new ten, equal money each; unchanged picks are not
            # touched (no fee to "top up")
            for t in [t for t in pos if t not in want]:
                amt = pos.pop(t) * last_px[t]
                cash += amt - fx_cost(amt) - DEAL
                costs += DEAL + fx_cost(amt)
            new = [t for t in want if t not in pos]
            if new:
                total = cash + sum(pos[t] * last_px[t] for t in pos)
                per = min(total / 10, cash / len(new))
                for t in new:
                    p = X[i, cp.__getitem__(t)]
                    if not np.isfinite(p) or per <= DEAL * 2:
                        continue
                    spend = per - DEAL
                    pos[t] = (spend - fx_cost(spend)) / p
                    last_px[t] = p
                    cash -= per
                    costs += DEAL + fx_cost(spend)
            picks_log.append({"date": str(idx[i].date()), "picks": want,
                              "market_on": bool(plan["market"]["on"])})
            if len(picks_log) % 24 == 0:
                log(f"    {idx[i].date()}  GBP {eq[i]:,.0f}  holding {', '.join(want) or 'cash'}")
    finally:
        dp.themes = real_themes
    return pd.Series(eq, index=idx).dropna(), picks_log, pd.DataFrame(ic_rows), costs


def stats(eq: pd.Series) -> dict:
    if len(eq) < 30:
        return {}
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / yrs) - 1
    dd = float((eq / eq.cummax() - 1).min())
    return {"start_gbp": round(float(eq.iloc[0])), "end_gbp": round(float(eq.iloc[-1])),
            "gbp_from_10k": round(START_GBP * float(eq.iloc[-1] / eq.iloc[0])),
            "cagr": round(float(cagr), 4), "max_drawdown": round(dd, 4),
            "calmar": round(float(cagr / -dd), 3) if dd < 0 else None}


def yearly(eq: pd.Series, spy: pd.Series) -> list[dict]:
    rows = []
    for y, g in eq.groupby(eq.index.year):
        prev = eq[eq.index.year < y]
        a = g.iloc[-1] / (prev.iloc[-1] if len(prev) else g.iloc[0]) - 1
        s = spy.reindex(eq.index)
        sp = s[s.index.year < y]
        b = s[s.index.year == y].iloc[-1] / (sp.iloc[-1] if len(sp) else s[s.index.year == y].iloc[0]) - 1
        rows.append({"year": int(y), "plan": round(float(a), 4), "spy": round(float(b), 4),
                     "beat": bool(a > b)})
    return rows


def best_ten_caught(C, member, picks_log) -> list[dict]:
    """The ten actual best S&P 500 stocks of each calendar year -- did we hold them?"""
    out = []
    # what the plan held going INTO the year (its January picks). Counting
    # anything held "at some point" would be hindsight: a stock that soars in
    # March becomes a momentum pick by June, after the gain.
    held = {}
    for p in picks_log:
        held.setdefault(int(p["date"][:4]), set(p["picks"]))
    idx = C.index
    for y in sorted(held):
        m = idx.year == y
        if m.sum() < 200:
            continue
        i0, i1 = np.where(m)[0][[0, -1]]
        elig = [c for k, c in enumerate(C.columns) if member[i0, k]]
        r = (C.iloc[i1][elig] / C.iloc[i0][elig] - 1).dropna().sort_values(ascending=False)
        top = list(r.index[:10])
        out.append({"year": y, "best_ten": [f"{t} {r[t]:+.0%}" for t in top],
                    "we_held": [t for t in top if t in held[y]]})
    return out


def verdict(eq, spy) -> tuple[bool, dict]:
    res = {}
    ok = True
    for name, a, b in (("1998-2012", None, SPLIT), ("2013-now", SPLIT, None)):
        e = eq[(eq.index >= a) if a is not None else slice(None)]
        e = e[e.index < b] if b is not None else e
        s = spy.reindex(e.index).dropna()
        me, ms = stats(e), stats(s)
        res[name] = {"plan": me, "spy": ms}
        if not me or not ms:
            ok = False
            continue
        ok &= (me["cagr"] >= ms["cagr"] + MARGIN) and ((me["calmar"] or 0) > (ms["calmar"] or 0))
    return ok, res


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def write_md(out: dict, path: Path):
    L = ["# Would the daily plan have worked? — year by year\n",
         f"_Generated {out['generated'][:16].replace('T', ' ')} UTC. The exact daily-plan code, "
         f"run every month from {out['from']} seeing only what was known at the time, and only "
         f"stocks that were in the S&P 500 then. HL costs included (£{DEAL} a deal + tiered FX, 1% → 0.25% "
         f"each way). {out['data']}._\n"]
    for key, title in (("themes", "Current plan (with themes)"),
                       ("industries", "Official industries only")):
        r = out.get(key)
        if not r:
            continue
        L.append(f"## {title}\n")
        L.append(f"**Verdict: {'PASSES' if r['passes'] else 'DOES NOT PASS'}** the bar "
                 f"(beat the S&P 500 by {MARGIN:.0%}/yr after costs AND a better Calmar, in both "
                 f"halves).\n")
        f, s = r["full"]["plan"], r["full"]["spy"]
        L.append(f"£{START_GBP:,.0f} → **£{f['gbp_from_10k']:,}** with the plan, £{s['gbp_from_10k']:,} in "
                 f"the S&P 500. Yearly: {f['cagr']:+.1%} vs {s['cagr']:+.1%}. Worst fall: "
                 f"{f['max_drawdown']:.0%} vs {s['max_drawdown']:.0%}. Costs paid: "
                 f"£{r['costs_gbp']:,.0f}.\n")
        for h, v in r["halves"].items():
            if not v.get("plan") or not v.get("spy"):
                L.append(f"- {h}: not enough data")
                continue
            L.append(f"- {h}: plan {v['plan']['cagr']:+.1%}/yr (worst {v['plan']['max_drawdown']:.0%}), "
                     f"S&P {v['spy']['cagr']:+.1%}/yr (worst {v['spy']['max_drawdown']:.0%})")
        p = r["prediction"]
        if not p:
            L.append("\n_Prediction check: not enough history after each pick to measure._\n")
        else:
          L.append(f"\n**Did the score predict the next 12 months?** Rank correlation "
                 f"{p['ic_12m_mean']:+.3f} on average (t = {p['ic_1m_t']:+.1f} on non-overlapping "
                 f"months; above 2 means real). Top tenth by score went on to make "
                 f"{p['top10_12m']:+.1%} a year, bottom tenth {p['bottom10_12m']:+.1%}, the average "
                 f"stock {p['all_12m']:+.1%}. Of the ten picked, on average "
                 f"{p['picks_beat_spy_pct']:.0%} beat the S&P 500 over the following year.\n")
        L.append("| Year | Plan | S&P 500 | Beat? | Top-10% by score, next 12m | Bottom-10% |")
        L.append("|---|---|---|---|---|---|")
        icy = {d["year"]: d for d in r["prediction_by_year"]}
        for y in r["yearly"]:
            q = icy.get(y["year"], {})
            L.append(f"| {y['year']} | {y['plan']:+.1%} | {y['spy']:+.1%} | "
                     f"{'yes' if y['beat'] else 'no'} | "
                     f"{'' if 'top' not in q else format(q['top'], '+.0%')} | "
                     f"{'' if 'bottom' not in q else format(q['bottom'], '+.0%')} |")
        L.append("")
    b = out.get("themes", {}).get("best_ten") or out.get("industries", {}).get("best_ten") or []
    if b:
        L.append("## The ten best stocks of each year — was the plan holding them in January?\n")
        L.append("Pure chance would catch about 0.2 of them a year (10 picks from ~500).\n")
        L.append("| Year | Actual best ten | In the plan's January ten |")
        L.append("|---|---|---|")
        for r in b:
            L.append(f"| {r['year']} | {', '.join(r['best_ten'])} | "
                     f"{', '.join(r['we_held']) or '—'} |")
    L.append("\n---\n_Known bias: most bankrupt or taken-over companies have no Yahoo prices; "
             "those in the delisted archive are included, the rest are missing. That flatters "
             "any stock picker, so a pass here is necessary, not sufficient._")
    path.write_text("\n".join(L) + "\n")


def summarise_ic(ic: pd.DataFrame) -> tuple[dict, list[dict]]:
    if ic.empty:
        return {}, []
    one = ic["ic_1m"].dropna()
    s = {"months": int(len(ic)),
         "ic_12m_mean": round(float(ic["ic_12m"].mean()), 4),
         "ic_1m_mean": round(float(one.mean()), 4),
         "ic_1m_t": round(float(one.mean() / one.std() * np.sqrt(len(one))), 2) if len(one) > 2 else 0,
         "top10_12m": round(float(ic["top10pct_12m"].mean()), 4),
         "bottom10_12m": round(float(ic["bottom10pct_12m"].mean()), 4),
         "all_12m": round(float(ic["all_12m"].mean()), 4),
         "picks_beat_spy_pct": round(float(ic["picks_beat_spy"].sum()
                                           / max(ic["picks_n"].sum(), 1)), 3)}
    ic = ic.assign(year=ic["date"].str[:4].astype(int))
    by = [{"year": int(y), "top": float(g["top10pct_12m"].mean()),
           "bottom": float(g["bottom10pct_12m"].mean()), "ic": float(g["ic_12m"].mean())}
          for y, g in ic.groupby("year")]
    return s, by


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--delisted", default="data/delisted/delisted_weekly.parquet")
    ap.add_argument("--labels", default=dp.CONSTITUENTS)
    ap.add_argument("--out", default="data/plan_backtest.json")
    ap.add_argument("--md", default="docs/BACKTEST.md")
    ap.add_argument("--variants", default="themes,industries")
    ap.add_argument("--spy-csv", default="")
    ap.add_argument("--allow-no-membership", action="store_true")
    ap.add_argument("--no-membership", action="store_true", help="test data only")
    a = ap.parse_args()
    if START_GBP != 10_000:                   # a different pot writes its own report
        tag = f"_{int(START_GBP / 1000)}k"
        a.out = a.out.replace(".json", f"{tag}.json")
        a.md = a.md.replace(".md", f"{tag}.md")
    out = {"generated": pd.Timestamp.now("UTC").isoformat(), "pot_gbp": START_GBP}
    try:
        C, info = load_panel(a.prices, a.delisted)
        C = C.loc[:, C.notna().sum() > 260]
        try:
            if a.no_membership:
                raise RuntimeError("membership disabled (test mode)")
            member = membership_mask(C.index, list(C.columns))
        except Exception as e:                                     # noqa: BLE001
            if not (a.allow_no_membership or a.no_membership):
                raise
            info["membership_error"] = str(e)
            member = np.ones(C.shape, bool)
        if a.spy_csv:
            spy = pd.read_csv(a.spy_csv, index_col=0, parse_dates=True).iloc[:, 0].reindex(C.index).ffill()
        else:
            spy = load_spy(C.index)
        if spy.notna().sum() < 0.5 * len(C):
            raise RuntimeError("could not get SPY history")
        C = C.loc[spy.first_valid_index():]
        member = member[-len(C):]
        spy = spy.loc[C.index]
        lab = dp.load_constituents(a.labels).set_index("yf")[
            ["Security", "GICS Sector", "GICS Sub-Industry"]]
        info["membership_matched"] = int(member.any(axis=0).sum())
        out.update(from_=str(C.index[WINDOW].date()), to=str(C.index[-1].date()), info=info)
        out["from"] = out.pop("from_")
        out["data"] = (f"{C.shape[1]} stocks ever in the index ({info.get('delisted_added', 0)} "
                       f"from the delisted archive)")
        print(json.dumps(info), flush=True)
        for v in a.variants.split(","):
            print(f"\n=== {v} ===", flush=True)
            eq, picks, ic, costs = simulate(C, member, spy, lab, use_themes=(v == "themes"))
            ok, halves = verdict(eq, spy)
            p, by = summarise_ic(ic)
            out[v] = {"passes": bool(ok), "full": {"plan": stats(eq), "spy": stats(spy.reindex(eq.index))},
                      "halves": halves, "yearly": yearly(eq, spy), "prediction": p,
                      "prediction_by_year": by, "costs_gbp": round(costs),
                      "best_ten": best_ten_caught(C, member, picks), "picks": picks[-36:]}
            print(json.dumps({k: out[v][k] for k in ("passes", "full", "prediction")}, indent=1),
                  flush=True)
            Path(a.out).write_text(json.dumps(out, indent=2, default=str))
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        write_md(out, Path(a.md))
        print(Path(a.md).read_text())
        return 0
    except Exception as exc:                                       # noqa: BLE001
        import traceback
        out["error"] = f"{type(exc).__name__}: {exc}"
        out["traceback"] = traceback.format_exc().splitlines()[-25:]
        Path(a.out).write_text(json.dumps(out, indent=2, default=str))
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text("# Backtest FAILED\n\n```\n" + "\n".join(out["traceback"]) + "\n```\n")
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
