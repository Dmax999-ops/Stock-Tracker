#!/usr/bin/env python3
"""
Retrain the state classifier on the full universe and write the evidence table.

This is the file that decides whether the system is trusted. It measures, for each
state, the forward return and a t-statistic against the universe average. If a
state's t-statistic falls below the threshold, it stops being tradeable -- the
signal is retired automatically rather than by anyone's judgement.

Published factors decay after publication (McLean & Pontiff 2016). Committing this
table on every run means git history shows each signal's t-statistic trending over
time, so decay is visible rather than discovered the expensive way.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quant import states                                    # noqa: E402

HORIZONS = [5, 10, 21, 63]
MIN_T = 2.5        # set BEFORE seeing results; strict because six states x four
                   # horizons is 24 tests and roughly one will pass at p<0.05 by luck


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-bars", type=int, default=400)
    a = ap.parse_args()

    px = pd.read_parquet(Path(a.data) / "prices.parquet")
    px["date"] = pd.to_datetime(px["date"])

    frames = []
    for t, g in px.groupby("ticker", sort=False):
        if len(g) < a.min_bars:
            continue
        g = g.sort_values("date").set_index("date")
        cl = states.classify(g)
        C = g["close"]
        d = pd.DataFrame({"state": cl["state"], "ticker": t,
                          **{f"f{h}": C.shift(-h) / C - 1 for h in HORIZONS}})
        d = d[d.state != ""].dropna()
        frames.append(d.reset_index().rename(columns={"index": "date"}))
    D = pd.concat(frames, ignore_index=True)

    # ------------------------------------------------------------------
    # TWO BENCHMARKS, AND THE DIFFERENCE BETWEEN THEM IS THE WHOLE STORY
    #
    # pooled   -- the average stock-day over the entire sample. Beating it can
    #             mean the state simply fires at good moments for the market.
    # same-day -- the average of every other stock ON THAT DAY. Beating it means
    #             the state actually picks stocks.
    #
    # CAPITULATION scored t = +6.3 against the pooled mean and t = -0.3 against
    # same-day peers: on 2015-08-25, 69% of the universe was "capitulating" at
    # once. It was reading the market, not the company. Only the same-day
    # number may set `tradeable`.
    # ------------------------------------------------------------------
    for h in HORIZONS:
        D[f"x{h}"] = D[f"f{h}"] - D.groupby("date")[f"f{h}"].transform("mean")

    pooled = {h: D[f"f{h}"].mean() for h in HORIZONS}
    table = {}
    for st, g in D.groupby("state"):
        rec = {"n": int(len(g)), "pct_of_time": round(len(g) / len(D), 4)}
        for h in HORIZONS:
            # overlapping windows: n/h independent observations, not n
            n_eff = max(len(g) / h, 1)
            v, xv = g[f"f{h}"].mean(), g[f"x{h}"].mean()
            se_p = g[f"f{h}"].std() / np.sqrt(n_eff)
            se_x = g[f"x{h}"].std() / np.sqrt(n_eff)
            rec[f"fwd_{h}d"] = round(float(v), 5)
            rec[f"excess_{h}d"] = round(float(xv), 5)
            rec[f"t_{h}d"] = round(float(xv / se_x), 2) if se_x else None
            rec[f"timing_excess_{h}d"] = round(float(v - pooled[h]), 5)
            rec[f"timing_t_{h}d"] = (round(float((v - pooled[h]) / se_p), 2)
                                     if se_p else None)
        t21 = rec.get("t_21d")
        # Direction matters. A state with t = -3 is an AVOID, not a buy; the old
        # code took |t| and flagged the worst states as tradeable alongside the best.
        rec["direction"] = ("BUY" if t21 is not None and t21 >= MIN_T else
                            "AVOID" if t21 is not None and t21 <= -MIN_T else "NONE")
        rec["tradeable"] = rec["direction"] != "NONE"
        table[st] = rec

    payload = {
        "generated": pd.Timestamp.now("UTC").isoformat(),
        "universe_tickers": int(D.ticker.nunique()),
        "observations": int(len(D)),
        "min_t_threshold": MIN_T,
        "states": table,
        "buy_states": [k for k, v in table.items() if v["direction"] == "BUY"],
        "avoid_states": [k for k, v in table.items() if v["direction"] == "AVOID"],
        "tradeable_states": [k for k, v in table.items() if v["tradeable"]],
        "NOTE": ("t_* is measured against SAME-DAY peers and is the only number "
                 "that may drive a decision. timing_t_* is measured against the "
                 "pooled all-history average and reflects WHEN the state fires, "
                 "not which stock it picks. Direction is signed: a large negative "
                 "t is an AVOID, never a buy."),
    }
    Path(a.out).write_text(json.dumps(payload, indent=2))
    print(json.dumps({k: {"t_21d": v["t_21d"], "tradeable": v["tradeable"]}
                      for k, v in table.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
