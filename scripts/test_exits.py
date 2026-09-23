#!/usr/bin/env python3
"""
If the exits are doing the work, can the exits be improved?

WHAT THE SETUP TEST FOUND
-------------------------
Random entry dates, run through a 2.5x ATR stop and a 4x ATR trail, returned
+0.28R per trade with a profit factor of 1.5 across 22 years and 600 stocks.
Every technical entry we tested landed within a rounding error of that, except
the failed breakdown, which added +0.05R. The money is in the exit policy.

So this script asks the obvious next question, and asks it honestly.

THE TRAP THIS IS DESIGNED TO AVOID
----------------------------------
Searching two dozen exit configurations and keeping the best one is how people
produce backtests that never work again. Earlier in this project a parameter
sweep showed a rank correlation of -0.065 between how a configuration scored in
the fitting window and how it scored afterwards -- tuning predicted nothing.

So the fit and the test are strictly separated:

    fit window   2004-2014   pick the best configuration, by expectancy
    test window  2015-2026   report what that configuration actually did

and then the whole grid's test-window results are reported too, alongside the
rank correlation between fit-window and test-window performance. If that
correlation is near zero, exit parameters are not tunable either, and the right
conclusion is to pick a sensible default and stop fiddling.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quant import trades as TR                                # noqa: E402

SEED = 20260923
COST_US = 2 * 0.0004 + 2 * 1.0 / 10000

# Deliberately coarse. A fine grid searched harder is a fine grid overfitted
# harder; these are the spacings a trader would actually choose between.
GRID = [(ks, kt, mh)
        for ks in (1.5, 2.5)
        for kt in (2.0, 3.0, 4.0, 6.0)
        for mh in (20, 60, 120)]

SPLIT = pd.Timestamp("2015-01-01")


def sample_entries(g: pd.DataFrame, n: int, rng) -> pd.Series:
    s = pd.Series(False, index=g.index)
    valid = np.arange(210, len(g) - 2)
    if len(valid) == 0:
        return s
    s.iloc[rng.choice(valid, size=min(n, len(valid)), replace=False)] = True
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/exit_evidence.json")
    ap.add_argument("--max-tickers", type=int, default=600)
    ap.add_argument("--entries", type=int, default=40,
                    help="random entries per ticker per configuration")
    a = ap.parse_args()

    out = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)

    try:
        px = pd.read_parquet(a.prices)
        px["date"] = pd.to_datetime(px["date"])
        rng = np.random.default_rng(SEED)

        frames = {t: g.sort_values("date").set_index("date")
                  for t, g in px.groupby("ticker") if len(g) >= 400}
        keys = sorted(frames)
        if len(keys) > a.max_tickers:
            keys = list(rng.choice(keys, size=a.max_tickers, replace=False))
        print(f"{len(keys)} instruments, {len(GRID)} configurations, "
              f"{a.entries} random entries each")

        # One fixed set of entry dates, reused by every configuration, so the
        # grid compares exit policies rather than different random draws.
        entry_rng = np.random.default_rng(SEED)
        entries = {t: sample_entries(frames[t], a.entries, entry_rng)
                   for t in keys}

        rows = []
        for i, (ks, kt, mh) in enumerate(GRID, 1):
            got = []
            for t in keys:
                tr = TR.simulate(frames[t], entries[t], k_stop=ks, k_trail=kt,
                                 max_hold=mh, cost_pct=COST_US)
                if not tr.empty:
                    got.append(tr)
            if not got:
                continue
            T = pd.concat(got, ignore_index=True)
            ed = pd.to_datetime(T.entry_date)
            fit, test = T[ed < SPLIT], T[ed >= SPLIT]
            if len(fit) < 500 or len(test) < 500:
                continue
            rows.append({
                "k_stop": ks, "k_trail": kt, "max_hold": mh,
                "trades": int(len(T)),
                "fit_expectancy_R": float(fit.R.mean()),
                "fit_trades": int(len(fit)),
                "test_expectancy_R": float(test.R.mean()),
                "test_trades": int(len(test)),
                "test_t": float(test.R.mean() / (test.R.std(ddof=1)
                                                 / np.sqrt(len(test)))),
                "test_profit_factor": float(
                    test[test.R > 0].R.sum() / -test[test.R <= 0].R.sum())
                if (test.R <= 0).any() else None,
                "avg_net_pct": float(T.net_pct.mean()),
                "median_bars": float(T.bars.median()),
            })
            print(f"  [{i:2}/{len(GRID)}] stop {ks} trail {kt} hold {mh:3}  "
                  f"fit {rows[-1]['fit_expectancy_R']:+.3f}R  "
                  f"test {rows[-1]['test_expectancy_R']:+.3f}R", flush=True)

        g = pd.DataFrame(rows)

        # Save the grid BEFORE computing anything else. The first run of this
        # script produced every number below and then threw all of them away
        # when one line failed, costing a full rebuild of the price panel to
        # get back. Partial results are worth more than none.
        out.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "status": "grid complete, verdict pending", "grid": rows},
            indent=2, default=str))

        best = g.loc[g.fit_expectancy_R.idxmax()]
        # Does fitting-window performance predict test-window performance at all?
        # Spearman via ranks and a plain Pearson: pandas' own method="spearman"
        # imports scipy behind the scenes, which the runner does not have. That
        # is exactly how this script died the first time.
        rho = float(g.fit_expectancy_R.rank().corr(g.test_expectancy_R.rank()))

        print(f"\n  best in fit window:  stop {best.k_stop} trail {best.k_trail} "
              f"hold {int(best.max_hold)}  ->  fit {best.fit_expectancy_R:+.3f}R")
        print(f"  that same config out of sample: {best.test_expectancy_R:+.3f}R "
              f"(t {best.test_t:+.1f})")
        print(f"  best achievable in the test window: "
              f"{g.test_expectancy_R.max():+.3f}R")
        print(f"  rank correlation fit vs test: {rho:+.3f}")
        print(f"  spread across configurations in test: "
              f"{g.test_expectancy_R.min():+.3f}R to {g.test_expectancy_R.max():+.3f}R")

        tunable = bool(rho >= 0.5)
        verdict = ("EXITS ARE TUNABLE — fit-window ranking carries over, so "
                   "choosing exit parameters on past data is worth doing."
                   if tunable else
                   "EXITS ARE NOT TUNABLE — fit-window ranking does not carry "
                   "over. Pick a sensible default, never optimise it, and spend "
                   "the effort on costs and position sizing instead.")
        print(f"\n  {verdict}")

        out.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "seed": SEED, "split": str(SPLIT.date()),
             "instruments": len(keys), "entries_per_ticker": a.entries,
             "best_by_fit": {k: (float(v) if isinstance(v, (int, float, np.floating))
                                 else v) for k, v in best.to_dict().items()},
             "fit_test_rank_correlation": rho, "tunable": tunable,
             "verdict": verdict, "grid": rows}, indent=2, default=str))
        return 0
    except Exception as exc:                                     # noqa: BLE001
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        out.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "error": f"{type(exc).__name__}: {exc}",
             "traceback": tb.splitlines()[-25:]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
