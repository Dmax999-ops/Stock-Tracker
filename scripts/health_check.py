#!/usr/bin/env python3
"""
HEALTH CHECK -- is what is happening live inside what the tests saw?

Runs the live rules over the full history (S&P 500 members at the time, companies
that later failed included, Trading 212 costs, one-day delay, GBP 10,000) and reports:

  1. the worst falls from a high, with dates and how long recovery took
  2. short bad stretches: how far the strategy has trailed the S&P 500 over any
     7 weeks, and what happened in the 12 months after the worst of them
  3. the fresh-start case: the first 7 weeks of a portfolio started from cash on
     every week of history (this is what a new account lives through)

Results: docs/HEALTH.md
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("challengers", HERE / "challengers.py")
ch = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ch)
fs, bp, POT = ch.fs, ch.bp, ch.POT
WEEKS = 7


def gbp(v: float) -> str:
    return f"£{v:,.0f}" if v >= 0 else f"−£{-v:,.0f}"


def falls(eq: pd.Series, n: int = 6) -> list[dict]:
    """The n deepest separate falls from a high: peak, low, depth, date back at the old high."""
    peak = eq.cummax()
    dd = eq / peak - 1
    out, i, vals = [], 0, eq.to_numpy()
    idx = eq.index
    while i < len(eq):
        if dd.iloc[i] < 0:
            j = i
            while j < len(eq) and dd.iloc[j] < 0:
                j += 1
            seg = dd.iloc[i:j]
            lo = seg.idxmin()
            out.append({"peak": str(idx[i - 1].date()) if i else str(idx[0].date()), "low": str(lo.date()),
                        "depth": float(seg.min()), "back": str(idx[j].date()) if j < len(eq) else None,
                        "months": round((idx[min(j, len(eq) - 1)] - idx[max(i - 1, 0)]).days / 30.4)})
            i = j
        else:
            i += 1
    return sorted(out, key=lambda r: r["depth"])[:n]


def main() -> int:
    C, member, spy, bond = ch.load()
    Cff = C.ffill()
    sig = Cff / Cff.rolling(200, min_periods=200).mean() - 1
    cnt = (sig.notna().to_numpy() & member).sum(axis=1)
    idx = C.index
    first = next(i for i in range(260, len(idx)) if cnt[i] >= 100)
    switch = bp.market_state(spy).shift(1).fillna(True).astype(bool).values
    fs.START = POT
    eq, _ = ch.run_one(sig, Cff, spy, member, first, switch, bond)
    eq = eq.astype(float)
    sp = spy.reindex(eq.index).astype(float)
    sp_eq = POT * sp / sp.iloc[0]

    # 2. any 7 weeks: strategy minus S&P 500 (eq has one value per weekly check)
    rel = (eq.pct_change(WEEKS) - sp.pct_change(WEEKS)).dropna()
    own = eq.pct_change(WEEKS).dropna()
    worst = []
    r2 = rel.copy()
    while len(worst) < 8 and len(r2):
        d = r2.idxmin()
        worst.append(d)
        r2 = r2[(r2.index < d - pd.Timedelta(weeks=26)) | (r2.index > d + pd.Timedelta(weeks=26))]
    after = []
    for d in worst:
        e = d + pd.DateOffset(years=1)
        a, b = eq[eq.index <= e], sp[sp.index <= e]
        done = eq.index[-1] >= e
        after.append({"end": str(d.date()), "seven_weeks": float(rel[d]), "own": float(own[d]),
                      "next12_strategy": float(a.iloc[-1] / eq[d] - 1) if done else None,
                      "next12_spy": float(b.iloc[-1] / sp[d] - 1) if done else None})

    # 3. fresh starts: first 7 weeks from cash, a start every 4 weeks
    wk = pd.Series(np.arange(len(idx)), index=idx).groupby(idx.to_period("W-FRI")).first()
    starts = [int(i) for i in wk if i >= first and idx[i] <= idx[-1] - pd.Timedelta(weeks=WEEKS + 1)][::4]
    fresh = []
    for st in starts:
        e2, _ = ch.run_one(sig, Cff, spy, member, st, switch, bond)
        e2 = e2.astype(float)
        end = idx[st] + pd.Timedelta(weeks=WEEKS)
        e2 = e2[e2.index <= end]
        s2 = spy[(spy.index >= idx[st]) & (spy.index <= end)]
        if len(e2) and len(s2) > 1:
            fresh.append((str(idx[st].date()), float(e2.iloc[-1] / POT - 1), float(s2.iloc[-1] / s2.iloc[0] - 1)))
    F = pd.DataFrame(fresh, columns=["start", "strategy", "spy"])
    F["gap"] = F["strategy"] - F["spy"]

    out = {"generated": pd.Timestamp.now("UTC").isoformat(), "from": str(eq.index[0].date()),
           "to": str(eq.index[-1].date()), "companies": int(C.shape[1]),
           "falls": falls(eq), "spy_falls": falls(sp_eq, 4), "after_worst": after,
           "seven_week": {"p01": float(rel.quantile(0.01)), "p05": float(rel.quantile(0.05)),
                          "median": float(rel.median()), "worst": float(rel.min()),
                          "share_below_10": float((rel <= -0.10).mean()),
                          "share_below_15": float((rel <= -0.15).mean()),
                          "share_below_20": float((rel <= -0.20).mean())},
           "fresh": {"n": int(len(F)), "worst_gap": float(F["gap"].min()), "p05_gap": float(F["gap"].quantile(0.05)),
                     "median_gap": float(F["gap"].median()), "worst_own": float(F["strategy"].min()),
                     "share_gap_below_10": float((F["gap"] <= -0.10).mean()),
                     "share_gap_below_20": float((F["gap"] <= -0.20).mean()),
                     "worst5": F.nsmallest(5, "gap").to_dict("records")}}
    sw, fr = out["seven_week"], out["fresh"]
    L = ["# Health check — is the live strategy inside what the tests saw?\n",
         f"_Run {out['generated'][:10]}. Live rules, £10,000, Trading 212 costs, one-day delay, {out['from']} to "
         f"{out['to']}, {out['companies']} companies (including ones that later failed)._\n",
         "## 1. The worst falls from a high\n",
         "| From high | Lowest point | Fall | £10,000 at the high became | Back at the old high | Months |",
         "|---|---|---|---|---|---|"]
    for r in out["falls"]:
        L.append(f"| {r['peak']} | {r['low']} | **{r['depth']:.0%}** | {gbp(POT * (1 + r['depth']))} | "
                 f"{r['back'] or '**not yet**'} | {r['months']} |")
    L += ["", "_The S&P 500's own worst falls over the same years: "
          + ", ".join(f"{r['depth']:.0%} ({r['low'][:4]})" for r in out["spy_falls"]) + "._\n",
          f"## 2. Any {WEEKS} weeks: strategy compared with the S&P 500\n",
          f"- Typical {WEEKS} weeks: {sw['median']:+.1%} against the S&P 500",
          f"- 1 stretch in 20 was worse than {sw['p05']:+.0%}; 1 in 100 worse than {sw['p01']:+.0%}",
          f"- Worst ever: **{sw['worst']:+.0%}**",
          f"- Trailed by 10 points or more in {sw['share_below_10']:.1%} of stretches, by 15 or more in "
          f"{sw['share_below_15']:.1%}, by 20 or more in {sw['share_below_20']:.1%}\n",
          "**The worst stretches, and the 12 months that followed:**\n",
          f"| {WEEKS} weeks ending | Strategy | vs S&P 500 | Next 12 months: strategy | Next 12 months: S&P 500 |",
          "|---|---|---|---|---|"]
    for a in after:
        L.append(f"| {a['end']} | {a['own']:+.0%} | **{a['seven_weeks']:+.0%}** | "
                 + (f"{a['next12_strategy']:+.0%} | {a['next12_spy']:+.0%} |" if a["next12_strategy"] is not None
                    else "too recent | too recent |"))
    L += ["", f"## 3. A brand-new account: its first {WEEKS} weeks ({fr['n']} different start dates)\n",
          f"- Typical first {WEEKS} weeks: {fr['median_gap']:+.1%} against the S&P 500",
          f"- 1 start in 20 was worse than {fr['p05_gap']:+.0%}",
          f"- Worst start ever: **{fr['worst_gap']:+.0%}** against the S&P 500 (the account itself: "
          f"{fr['worst_own']:+.0%})",
          f"- Behind by 10 points or more after {WEEKS} weeks: {fr['share_gap_below_10']:.1%} of starts; "
          f"by 20 or more: {fr['share_gap_below_20']:.1%}\n",
          "| Worst starts | Strategy | S&P 500 | Gap |", "|---|---|---|---|"]
    for r in fr["worst5"]:
        L.append(f"| {r['start']} | {r['strategy']:+.0%} | {r['spy']:+.0%} | **{r['gap']:+.0%}** |")
    L += ["", "_Tested rules, not personal financial advice._"]
    Path("docs/HEALTH.md").write_text("\n".join(L) + "\n")
    Path("data/health.json").write_text(json.dumps(out, indent=2, default=str))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
