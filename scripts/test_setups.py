#!/usr/bin/env python3
"""
Technical setups, tested as trades rather than as factors.

THE SETUPS, DEFINED BEFORE ANY DATA WAS TOUCHED
-----------------------------------------------
Each is a mechanical reading of a pattern traders describe in words. No parameter
was chosen by looking at results; the numbers are the conventional ones.

  breakout20        close above the highest close of the prior 20 days
  breakout20_vol    the same, but only when volume is 1.5x its 50-day average
  breakout55        the Turtle rule: close above the prior 55-day high
  squeeze           Bollinger bandwidth in the bottom fifth of its own two-year
                    range, then a close above the upper band -- a volatility
                    contraction resolving upward
  pullback          close above the 200-day average (trend intact), price dips
                    below the 20-day average for at least two days, then closes
                    back above it
  failed_breakdown  close below the prior 20-day low, then back above that low
                    within three days -- the trap that traps the sellers
  breakdown_short   short entry on a close below the prior 20-day low

THE CONTROL THAT MAKES THIS WORTH ANYTHING
------------------------------------------
Any long strategy in a rising market makes money. So every setup is compared to
RANDOM ENTRIES in the same stocks, run through the identical stop, trail and
holding rules. The difference between the two is the part attributable to the
pattern rather than to the market going up. With thousands of trades this control
has real statistical power -- which is precisely what the factor tests lacked.

WALK-FORWARD
------------
Everything is reported twice: 2004-2014 and 2015 onwards. No parameter is fitted
on either, so this is a stability check rather than a tuning exercise.

WHAT COUNTS AS A PASS, FIXED NOW
--------------------------------
  1. expectancy above the random control by at least 0.10R, with t >= 3.0 on the
     setup's own trades (t = 3 because seven setups x two horizons is fourteen
     tests, and the best of fourteen pure noise draws lands near t = 2.5)
  2. profit factor >= 1.3 after costs
  3. the same sign in both halves of the walk-forward
Anything short of all three is reported as a failure, whatever it looks like.
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

RNG = np.random.default_rng(20260922)

HORIZONS = {
    # swing: tight stop, quick trail, out within a month
    "swing":    dict(k_stop=1.5, k_trail=2.0, max_hold=20),
    # position: wider stop, loose trail, room to run for months
    "position": dict(k_stop=2.5, k_trail=4.0, max_hold=120),
}

# Round-trip cost as a fraction of notional, on a nominal GBP 10,000 position.
COSTS = {
    "US": 2 * 0.0004 + 2 * 1.0 / 10000,             # 4bps half-spread, $1 a side
    "UK": 2 * 0.0008 + 0.005 + 2 * 11.95 / 10000,   # 8bps, stamp duty, GBP 11.95
}

PASS_EDGE, PASS_T, PASS_PF = 0.10, 3.0, 1.3


# ---------------------------------------------------------------------------
# Setups
# ---------------------------------------------------------------------------

def setups(df: pd.DataFrame) -> dict[str, pd.Series]:
    c, v = df["close"], df["volume"]
    ma20, ma50, ma200 = (c.rolling(w).mean() for w in (20, 50, 200))
    prior20 = c.shift(1).rolling(20).max()
    prior55 = c.shift(1).rolling(55).max()
    low20 = c.shift(1).rolling(20).min()
    vol50 = v.rolling(50).mean()

    sd20 = c.rolling(20).std(ddof=0)
    upper = ma20 + 2 * sd20
    bw = (4 * sd20) / ma20
    bw_pct = bw.rolling(504, min_periods=252).rank(pct=True)

    below20 = (c < ma20)
    back_above = below20.shift(1) & below20.shift(2) & (c > ma20)

    broke_down = c < low20
    reclaimed = (broke_down.shift(1) | broke_down.shift(2) | broke_down.shift(3)) \
        & (c > low20)

    return {
        "breakout20":       c > prior20,
        "breakout20_vol":   (c > prior20) & (v > 1.5 * vol50),
        "breakout55":       c > prior55,
        "squeeze":          (bw_pct < 0.20) & (c > upper),
        "pullback":         (c > ma200) & back_above,
        "failed_breakdown": reclaimed & (c > ma200),
        "breakdown_short":  c < low20,
    }


SHORT = {"breakdown_short"}


def random_entries(df: pd.DataFrame, n: int, rng) -> pd.Series:
    """n random signal days in this instrument, same machinery applied after."""
    s = pd.Series(False, index=df.index)
    valid = np.arange(210, len(df) - 2)          # skip the indicator warm-up
    if len(valid) == 0 or n == 0:
        return s
    pick = rng.choice(valid, size=min(n, len(valid)), replace=False)
    s.iloc[pick] = True
    return s


# ---------------------------------------------------------------------------

def run_market(px: pd.DataFrame, market: str, cost: float) -> dict:
    out = {}
    by_ticker = {t: g.sort_values("date").set_index("date")
                 for t, g in px.groupby("ticker")}
    print(f"\n{market}: {len(by_ticker)} instruments")

    for hname, hp in HORIZONS.items():
        for sname in setups(next(iter(by_ticker.values()))).keys():
            real, rand = [], []
            for t, g in by_ticker.items():
                if len(g) < 300:
                    continue
                sig = setups(g)[sname]
                d = -1 if sname in SHORT else 1
                tr = TR.simulate(g, sig.fillna(False), direction=d,
                                 cost_pct=cost, **hp)
                if not tr.empty:
                    real.append(tr)
                    rnd = TR.simulate(g, random_entries(g, len(tr), RNG),
                                      direction=d, cost_pct=cost, **hp)
                    if not rnd.empty:
                        rand.append(rnd)
            if not real:
                continue
            R = pd.concat(real, ignore_index=True)
            Q = pd.concat(rand, ignore_index=True) if rand else pd.DataFrame()

            s = TR.stats(R)
            s["random_expectancy_R"] = (float(Q.R.mean()) if not Q.empty
                                        else None)
            s["random_trades"] = int(len(Q))
            s["edge_vs_random_R"] = (None if Q.empty else
                                     float(R.R.mean() - Q.R.mean()))

            # walk-forward halves, no fitting in either
            ed = pd.to_datetime(R.entry_date)
            early, late = R[ed < "2015-01-01"], R[ed >= "2015-01-01"]
            s["early"] = {"trades": int(len(early)),
                          "expectancy_R": float(early.R.mean()) if len(early) else None}
            s["late"] = {"trades": int(len(late)),
                         "expectancy_R": float(late.R.mean()) if len(late) else None}

            both_signs = (s["early"]["expectancy_R"] is not None
                          and s["late"]["expectancy_R"] is not None
                          and np.sign(s["early"]["expectancy_R"])
                          == np.sign(s["late"]["expectancy_R"]))
            s["passed"] = bool(
                s.get("edge_vs_random_R") is not None
                and s["edge_vs_random_R"] >= PASS_EDGE
                and s.get("t_stat") is not None and s["t_stat"] >= PASS_T
                and s.get("profit_factor") is not None
                and s["profit_factor"] >= PASS_PF
                and both_signs and s["expectancy_R"] > 0)

            out[f"{market}:{hname}:{sname}"] = s
            print(f"  {hname:8} {sname:17} n={s['trades']:6,}  "
                  f"win {s['win_rate']:5.1%}  exp {s['expectancy_R']:+.3f}R  "
                  f"rand {s['random_expectancy_R']:+.3f}R  "
                  f"edge {s['edge_vs_random_R']:+.3f}R  "
                  f"PF {s['profit_factor'] or float('nan'):.2f}  "
                  f"t {s['t_stat'] or float('nan'):+.2f}  "
                  f"{'PASS' if s['passed'] else ''}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--uk-prices", default=None)
    ap.add_argument("--out", default="data/setup_evidence.json")
    a = ap.parse_args()

    out_path = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)
    try:
        px = pd.read_parquet(a.prices)
        px["date"] = pd.to_datetime(px["date"])
        res = run_market(px, "US", COSTS["US"])

        if a.uk_prices and Path(a.uk_prices).exists():
            uk = pd.read_parquet(a.uk_prices)
            uk["date"] = pd.to_datetime(uk["date"])
            res.update(run_market(uk, "UK", COSTS["UK"]))

        passed = [k for k, v in res.items() if v.get("passed")]
        print(f"\n  setups tested: {len(res)}   passed: {len(passed)}")
        for k in passed:
            print(f"    PASS  {k}")
        if not passed:
            print("    none cleared the bar")

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "horizons": HORIZONS, "costs": COSTS,
             "pass_mark": {"edge_vs_random_R": PASS_EDGE, "t": PASS_T,
                           "profit_factor": PASS_PF,
                           "same_sign_both_halves": True},
             "results": res, "passed": passed}, indent=2, default=str))
        return 0
    except Exception as exc:                                     # noqa: BLE001
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "error": f"{type(exc).__name__}: {exc}",
             "traceback": tb.splitlines()[-25:]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
