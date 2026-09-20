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
        frames.append(d[d.state != ""].dropna())
    D = pd.concat(frames)

    base = {h: D[f"f{h}"].mean() for h in HORIZONS}
    table = {}
    for st, g in D.groupby("state"):
        rec = {"n": int(len(g)), "pct_of_time": round(len(g) / len(D), 4)}
        for h in HORIZONS:
            v = g[f"f{h}"].mean()
            # deflate standard error for overlapping windows
            se = g[f"f{h}"].std() / np.sqrt(max(len(g) / h, 1))
            rec[f"fwd_{h}d"] = round(float(v), 5)
            rec[f"excess_{h}d"] = round(float(v - base[h]), 5)
            rec[f"t_{h}d"] = round(float((v - base[h]) / se), 2) if se else None
        rec["tradeable"] = bool(rec.get("t_21d") is not None and abs(rec["t_21d"]) >= MIN_T)
        table[st] = rec

    payload = {
        "generated": pd.Timestamp.utcnow().isoformat(),
        "universe_tickers": int(D.ticker.nunique()),
        "observations": int(len(D)),
        "min_t_threshold": MIN_T,
        "states": table,
        "tradeable_states": [k for k, v in table.items() if v["tradeable"]],
        "NOTE": ("Only states flagged tradeable should drive decisions. The rest "
                 "are reported so decay is visible, not so they can be used."),
    }
    Path(a.out).write_text(json.dumps(payload, indent=2))
    print(json.dumps({k: {"t_21d": v["t_21d"], "tradeable": v["tradeable"]}
                      for k, v in table.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
