#!/usr/bin/env python3
"""
Does the test harness work? Run known answers through it.

WHY
---
test_ear.py said the results-week signal is worth nothing: 45,699 events, t = -0.27.
That is either a real finding or a bug. A measuring instrument that always reads
zero looks identical to a world with nothing in it, and I have shipped two broken
files into this repo already. So: feed the SAME harness signals whose answers are
known in advance, and see whether it reports them correctly.

FOUR SIGNALS, ONE PIPELINE
--------------------------
Every one uses the identical event set, entry timing, benchmark and statistics as
test_ear.py -- the functions are imported from it, not re-implemented. Only the
number being ranked changes.

  1. ear_within    the failed signal, re-run. Should reproduce ~0.
  2. mom_within    12-month momentum, ranked against the stock's OWN history,
                   exactly as EAR was. Momentum is not really a within-stock
                   signal, so a null here is uninformative on its own -- it is
                   here to show what the EAR treatment does to a real effect.
  3. mom_cross     12-month momentum, ranked ACROSS stocks in the same week.
                   This is the real control. Momentum is the most replicated
                   anomaly in finance (Jegadeesh & Titman 1993, and still alive
                   in out-of-sample tests thirty years on).
  4. random        a seeded random number. The negative control.

PREDICTIONS, WRITTEN BEFORE RUNNING
-----------------------------------
  mom_cross   positive spread, somewhere around +1% to +3% over 12 weeks.
              Large caps and a survivor-tilted sample both weaken it, so t
              between 1.5 and 4 is the expected zone.
  random      spread indistinguishable from zero, |t| < 2.
  ear_within  ~0, reproducing the earlier run.

HOW TO READ THE RESULT
----------------------
  mom_cross positive AND random flat   -> the harness measures what it should.
                                          The EAR null is a real null.
  mom_cross also flat                  -> the instrument cannot detect a known
                                          effect. Every null it has produced is
                                          suspect, including EAR, and the
                                          pipeline needs debugging before any
                                          further conclusion is drawn.
  random NOT flat                      -> the statistics are broken. Nothing
                                          measured so far can be trusted.

This script asserts nothing and tunes nothing. It writes what it found.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_ear as T                                          # noqa: E402

SEED = 20260922       # fixed so the random control is reproducible


def build_signals(px_w: pd.DataFrame, ann: pd.DataFrame) -> pd.DataFrame:
    """
    One row per earnings announcement, carrying every candidate signal measured
    at that week plus the forward drift. Drift is computed by the same arithmetic
    as test_ear.build -- entry one week AFTER the announcement, 12 weeks held,
    minus the same-week universe average.
    """
    px_w = px_w.sort_values(["ticker", "date"]).copy()
    px_w["ret"] = px_w.groupby("ticker")["close"].pct_change()
    px_w["mkt"] = px_w.groupby("date")["ret"].transform("mean")
    px_w["abn"] = px_w["ret"] - px_w["mkt"]

    # 12-month momentum skipping the most recent month: the standard definition.
    c = px_w.groupby("ticker")["close"]
    px_w["mom"] = c.shift(4) / c.shift(52) - 1
    # cross-sectional percentile among every stock trading that week
    px_w["mom_pct"] = px_w.groupby("date")["mom"].rank(pct=True)

    idx = {t: g.reset_index(drop=True) for t, g in px_w.groupby("ticker")}
    rng = np.random.default_rng(SEED)
    rows = []
    for t, g in ann.groupby("ticker"):
        if t not in idx:
            continue
        p = idx[t]
        dates = p["date"].values
        for d in pd.to_datetime(g["date"]).sort_values():
            k = int(np.searchsorted(dates, np.datetime64(d)))
            if k < 1 or k + 1 + T.H >= len(p):
                continue
            ear = p["abn"].iloc[k]
            if not np.isfinite(ear):
                continue
            entry, exit_ = k + 1, k + 1 + T.H
            fwd = p["close"].iloc[exit_] / p["close"].iloc[entry] - 1
            bench = p["mkt"].iloc[entry + 1:exit_ + 1].add(1).prod() - 1
            rows.append({"ticker": t, "week": p["date"].iloc[k],
                         "ear": float(ear),
                         "mom": float(p["mom"].iloc[k]),
                         "mom_pct": float(p["mom_pct"].iloc[k]),
                         "rand": float(rng.random()),
                         "drift": float(fwd - bench)})
    return pd.DataFrame(rows).sort_values(["ticker", "week"])


def spearman_by_week(e: pd.DataFrame, a: str, b: str) -> pd.Series:
    """Per-week Spearman correlation, computed with group means only."""
    d = e.dropna(subset=[a, b]).copy()
    if d.empty:
        return pd.Series(dtype=float)
    g = d.groupby("week")
    ra, rb = g[a].rank(), g[b].rank()
    ca = ra - ra.groupby(d["week"]).transform("mean")
    cb = rb - rb.groupby(d["week"]).transform("mean")
    cov = (ca * cb).groupby(d["week"]).mean()
    sa = (ca ** 2).groupby(d["week"]).mean() ** 0.5
    sb = (cb ** 2).groupby(d["week"]).mean() ** 0.5
    denom = (sa * sb).replace(0, np.nan)
    return (cov / denom).dropna()


def bucket_within(e: pd.DataFrame, col: str) -> pd.DataFrame:
    """Rank against the stock's own past — the treatment EAR received."""
    # Keep only the columns the ranker needs. Renaming onto "ear" while the real
    # "ear" column is still present would create two columns of the same name.
    x = e[["ticker", "week", "drift", col]].dropna(subset=[col]).copy()
    x = x.rename(columns={col: "ear"})
    return T.rank_expanding(x)


def bucket_cross(e: pd.DataFrame, col: str) -> pd.DataFrame:
    """Rank across stocks in the same week — the standard treatment for a factor."""
    x = e.dropna(subset=[col]).copy()
    x["bucket"] = np.where(x[col] >= 2 / 3, "BUY",
                  np.where(x[col] <= 1 / 3, "SELL", "MID"))
    return x


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--dates", default="data/earnings_dates.csv")
    ap.add_argument("--out", default="data/harness_check.json")
    a = ap.parse_args()

    # The runner's log is awkward to read from outside GitHub, so anything that
    # goes wrong is written into the output file instead -- a crash that leaves
    # no trace in the repo costs another round trip to diagnose.
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
             "verdict": "CRASHED — see error below. No conclusion.",
             "error": f"{type(exc).__name__}: {exc}",
             "traceback": tb.splitlines()[-25:]}, indent=2))
        return 1


def run(a, env: dict, out: Path) -> int:
    px = pd.read_parquet(a.prices)
    ann = pd.read_csv(a.dates)
    e = build_signals(T.weekly(px), ann)
    print(f"events: {len(e):,}   tickers: {e.ticker.nunique()}   "
          f"{e.week.min().date()} to {e.week.max().date()}")

    # Reference number, independent of the event structure: the rank correlation
    # between momentum and the next 12 weeks, week by week. Published values sit
    # around 0.02-0.04.
    #
    # Built from transforms and group means rather than groupby.apply -- the
    # apply/include_groups API has shifted across pandas versions and this script
    # has to run on whatever the runner installs, not on my sandbox's build.
    ic = spearman_by_week(e, "mom", "drift")
    print(f"momentum IC vs 12-week drift: mean {ic.mean():+.4f}  "
          f"(t {T.t_stat(ic.values):+.2f} across {len(ic)} weeks)")

    results = {}
    for name, fn in [
        ("ear_within", lambda: bucket_within(e, "ear")),
        ("mom_within", lambda: bucket_within(e, "mom")),
        ("mom_cross", lambda: bucket_cross(e, "mom_pct")),
        ("random", lambda: bucket_within(e, "rand")),
    ]:
        # One signal falling over should not cost us the other three.
        try:
            results[name] = T.report(fn(), name)
        except Exception as exc:                                 # noqa: BLE001
            print(f"\n=== {name}\n  FAILED: {type(exc).__name__}: {exc}")
            results[name] = {"label": name, "error":
                             f"{type(exc).__name__}: {exc}", "events": 0,
                             "weeks": 0, "t": float("nan"),
                             "buy_minus_sell": float("nan"),
                             "buy_hit_rate": float("nan")}

    mc, rd = results["mom_cross"], results["random"]
    mom_works = bool(mc["buy_minus_sell"] > 0 and mc["t"] >= 1.5)
    random_flat = bool(np.isfinite(rd["t"]) and abs(rd["t"]) < 2.0)

    errored = [k for k, v in results.items() if "error" in v]
    thin = [k for k, v in results.items()
            if k not in errored
            and (v["weeks"] < T.MIN_WEEKS or not np.isfinite(v["t"]))]
    if errored:
        verdict = (f"INCOMPLETE — these signals errored: {', '.join(errored)}. "
                   f"See the error field. No conclusion about the harness.")
    elif thin:
        verdict = (f"INCONCLUSIVE — too few usable weeks for: {', '.join(thin)}. "
                   f"A week counts only when it holds at least "
                   f"{T.MIN_PER_BUCKET} BUY and {T.MIN_PER_BUCKET} SELL events, "
                   f"and {T.MIN_WEEKS} such weeks are needed. This says nothing "
                   f"about the signals; the sample is too small to judge.")
    elif mom_works and random_flat:
        verdict = ("HARNESS OK — it detects momentum and stays flat on noise. "
                   "The results-week null is a real null.")
    elif not mom_works and random_flat:
        verdict = ("HARNESS INSENSITIVE — it cannot see a known effect. Every "
                   "null it has produced, including the results-week signal, is "
                   "unproven. Debug the pipeline before concluding anything.")
    else:
        verdict = ("STATISTICS BROKEN — the random control did not come back "
                   "flat. Nothing measured with this harness can be trusted.")

    print(f"\n  momentum detected: {mom_works}   random flat: {random_flat}")
    print(f"\n  {verdict}")

    out.write_text(json.dumps(
        {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
         "seed": SEED, "horizon_weeks": T.H, "events": int(len(e)),
         "momentum_ic": float(ic.mean()) if len(ic) else None,
         "momentum_ic_t": T.t_stat(ic.values) if len(ic) else None,
         "momentum_ic_weeks": int(len(ic)),
         "results": results, "momentum_detected": bool(mom_works),
         "random_flat": bool(random_flat), "verdict": verdict}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
