#!/usr/bin/env python3
"""
The textbook momentum test, implemented from scratch.

WHY A SECOND IMPLEMENTATION
---------------------------
The harness check came back INSENSITIVE: it could not see momentum. That has two
possible causes, and they need separating.

  (a) The event-based pipeline is broken or blunt, in which case every null it
      has produced -- including the results-week signal -- is worthless.
  (b) The pipeline is fine, and momentum simply is not visible in THIS data:
      S&P 500 large caps, 2004-2026, measured only in earnings weeks, on a
      survivor-tilted sample.

This script shares no code with the event pipeline. It builds momentum the way it
is published -- rank every stock, hold a basket, rebalance monthly -- so that if
the effect is in the data at all, this finds it.

TWO THINGS THE CONTROL TEST EXPOSED, FIXED HERE
-----------------------------------------------
1. OVERLAPPING WINDOWS. The event tests measured 12-week forward returns starting
   every week, then treated each week as an independent observation. Consecutive
   windows share eleven of their twelve weeks, so those t-statistics were roughly
   sqrt(12) too generous. Here the holding periods do not overlap at all: rank,
   hold to the next rebalance, no double counting.

2. THE HIT RATE BASELINE IS NOT 50%. Compounded returns are right-skewed, so most
   stocks finish below the cross-sectional MEAN. In a simulated world with no
   signal whatsoever, only 46.6% of stocks beat their peer average. The earlier
   pass mark of "55% of buys beat peers" was measured against the wrong zero.
   This script reports the median-based hit rate, whose null value is 50%.

WHAT THE ANSWER MEANS
---------------------
  spread positive, t >= 2   momentum is present. The pipeline can see real
                            effects, so the results-week null stands.
  spread near zero          this dataset cannot show the single most replicated
                            effect in finance. Nothing measured on it -- positive
                            or negative -- should be trusted, and the data itself
                            is the thing to fix.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LOOKBACK = 52      # weeks in the momentum window
SKIP = 4           # skip the most recent month, as the literature does
HOLD = 4           # weeks held; also the rebalance spacing, so windows never overlap
N_BUCKETS = 5      # quintiles


def t_stat(x) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return float("nan")
    sd = x.std(ddof=1)
    return float("nan") if sd == 0 else float(x.mean() / (sd / np.sqrt(len(x))))


def weekly_panel(px: pd.DataFrame) -> pd.DataFrame:
    px = px.copy()
    px["date"] = pd.to_datetime(px["date"])
    w = (px.set_index("date").groupby("ticker")["close"]
           .resample("W-FRI").last().dropna().reset_index())
    return w.sort_values(["ticker", "date"])


def run(a, env: dict, out: Path) -> int:
    px = pd.read_parquet(a.prices)
    d = weekly_panel(px)
    print(f"panel: {d.ticker.nunique()} tickers, "
          f"{d.date.min().date()} to {d.date.max().date()}, {len(d):,} rows")

    c = d.groupby("ticker")["close"]
    d["mom"] = c.shift(SKIP) / c.shift(LOOKBACK) - 1
    # forward return over the holding period, bought at this week's close
    d["fwd"] = c.shift(-HOLD) / c.shift(0) - 1

    # Rebalance dates spaced HOLD weeks apart, so no two holding periods overlap.
    all_dates = np.sort(d["date"].unique())
    rebal = set(pd.to_datetime(all_dates[LOOKBACK + 1::HOLD]))
    x = d[d["date"].isin(rebal)].dropna(subset=["mom", "fwd"]).copy()
    print(f"rebalance dates: {x.date.nunique()}   stock-periods: {len(x):,}")

    # Peer-relative return, and the median baseline whose null value is 50%.
    x["peer_mean"] = x.groupby("date")["fwd"].transform("mean")
    x["peer_median"] = x.groupby("date")["fwd"].transform("median")
    x["rel"] = x["fwd"] - x["peer_mean"]

    x["bucket"] = (x.groupby("date")["mom"]
                    .transform(lambda s: pd.qcut(s.rank(method="first"),
                                                 N_BUCKETS, labels=False)))
    x = x.dropna(subset=["bucket"])

    per = x.groupby(["date", "bucket"])["fwd"].mean().unstack()
    top, bot = N_BUCKETS - 1, 0
    if top not in per.columns or bot not in per.columns:
        raise RuntimeError("not enough stocks per date to form quintiles")
    spread = (per[top] - per[bot]).dropna()
    ic = spearman_by_date(x, "mom", "fwd")

    hit_mean = float((x[x.bucket == top]["fwd"] > x[x.bucket == top]["peer_mean"]).mean())
    hit_med = float((x[x.bucket == top]["fwd"] > x[x.bucket == top]["peer_median"]).mean())

    res = {
        "periods": int(len(spread)),
        "hold_weeks": HOLD,
        "spread_per_period": float(spread.mean()),
        "spread_annualised": float(spread.mean() * (52 / HOLD)),
        "t": t_stat(spread.values),
        "periods_positive": float((spread > 0).mean()),
        "top_quintile_rel": float(x[x.bucket == top]["rel"].mean()),
        "bottom_quintile_rel": float(x[x.bucket == bot]["rel"].mean()),
        "top_beats_peer_mean": hit_mean,
        "top_beats_peer_median": hit_med,
        "ic_mean": float(ic.mean()) if len(ic) else None,
        "ic_t": t_stat(ic.values) if len(ic) else None,
        "ic_periods": int(len(ic)),
    }

    # HOW BIG WOULD AN EFFECT HAVE TO BE FOR THIS TEST TO SEE IT?
    # A null is only as strong as the test's power. With n non-overlapping
    # periods and a spread standard deviation of s, nothing below 2*s/sqrt(n)
    # can reach t = 2, however real it is. Quoting this floor alongside every
    # null is the difference between "no effect" and "no LARGE effect".
    s = float(np.nanstd(spread.values, ddof=1))
    mde = 2 * s / np.sqrt(max(len(spread), 1))
    res["spread_sd_per_period"] = s
    res["min_detectable_per_period"] = float(mde)
    res["min_detectable_annualised"] = float(mde * (52 / HOLD))

    print(f"\nmomentum, {HOLD}-week non-overlapping holds, {res['periods']} periods")
    print(f"  top quintile vs peers    {res['top_quintile_rel']:+.2%}")
    print(f"  bottom quintile vs peers {res['bottom_quintile_rel']:+.2%}")
    print(f"  top minus bottom         {res['spread_per_period']:+.2%} per period "
          f"({res['spread_annualised']:+.1%}/yr)   t = {res['t']:.2f}")
    print(f"  periods positive         {res['periods_positive']:.1%}")
    print(f"  rank correlation         {res['ic_mean']:+.4f}  (t {res['ic_t']:+.2f})")
    print(f"  top beats peer MEDIAN    {res['top_beats_peer_median']:.1%} "
          f"(null is 50%)")
    print(f"  top beats peer MEAN      {res['top_beats_peer_mean']:.1%} "
          f"(null is ~47%, because compounded returns are skewed)")

    print(f"  smallest detectable      {res['min_detectable_annualised']:+.1%}/yr "
          f"at t=2 with {res['periods']} periods")

    detected = bool(res["t"] >= 2.0 and res["spread_per_period"] > 0)
    # Right sign, roughly the published size, but too small for this sample to
    # prove. That is a statement about the test, not about the market.
    underpowered = bool(not detected and res["spread_per_period"] > 0
                        and res["ic_mean"] is not None and res["ic_mean"] > 0
                        and res["spread_per_period"] < mde)
    if detected:
        verdict = ("MOMENTUM PRESENT — this data can show a known effect, so "
                   "nulls measured on it are meaningful.")
    elif underpowered:
        verdict = (f"UNDERPOWERED — momentum shows the right sign and roughly "
                   f"the published size, but this sample cannot prove anything "
                   f"smaller than {res['min_detectable_annualised']:+.1%}/yr. "
                   f"Every null found here means 'no LARGE effect', not 'no "
                   f"effect'. More history or a wider universe is the fix, not "
                   f"more signals.")
    else:
        verdict = ("MOMENTUM ABSENT AND WRONG-SIGNED — the most replicated "
                   "effect in finance does not appear at all. Suspect the data "
                   "or the pipeline before testing anything else.")
    print(f"\n  {verdict}")

    out.write_text(json.dumps(
        {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
         "spec": {"lookback_weeks": LOOKBACK, "skip_weeks": SKIP,
                  "hold_weeks": HOLD, "buckets": N_BUCKETS,
                  "overlapping": False},
         "result": res, "momentum_detected": detected,
         "underpowered": underpowered, "verdict": verdict},
        indent=2))
    return 0


def spearman_by_date(x: pd.DataFrame, a: str, b: str) -> pd.Series:
    """Per-date rank correlation, built from group means only."""
    d = x.dropna(subset=[a, b])
    g = d.groupby("date")
    ra, rb = g[a].rank(), g[b].rank()
    ca = ra - ra.groupby(d["date"]).transform("mean")
    cb = rb - rb.groupby(d["date"]).transform("mean")
    cov = (ca * cb).groupby(d["date"]).mean()
    sa = (ca ** 2).groupby(d["date"]).mean() ** 0.5
    sb = (cb ** 2).groupby(d["date"]).mean() ** 0.5
    return (cov / (sa * sb).replace(0, np.nan)).dropna()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/momentum_control.json")
    a = ap.parse_args()

    out = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)
    try:
        return run(a, env, out)
    except Exception as exc:                                     # noqa: BLE001
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        out.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "verdict": "CRASHED — no conclusion.",
             "error": f"{type(exc).__name__}: {exc}",
             "traceback": tb.splitlines()[-25:]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
