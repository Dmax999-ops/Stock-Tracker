#!/usr/bin/env python3
"""
START-DATE LUCK -- how much does the day you start decide the result?

The strategy buys the strongest confirmed stocks on the day it starts, so two
people starting a few weeks apart can hold quite different stocks. This test
starts the strategy on EVERY week since 2000 and follows each start for 10
years (and 5 years), with Trading 212 costs and a one-day trading delay.

Two ways of putting GBP 10,000 in:
  ONE START   all GBP 10,000 into the strategy on one day (the current plan)
  FOUR STARTS four portfolios of GBP 2,500, started one week apart, each
              following the same rules on its own. Money waiting to start sits
              in the S&P 500 tracker. You end up holding a blend of four start
              dates instead of one.

Each result is compared with GBP 10,000 in the S&P 500 tracker over exactly the
same years. Written to docs/START_LUCK.md and data/start_luck.json.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("validation", HERE / "validation.py")
val = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(val)
fs, bp = val.fs, val.bp

POT = 10_000.0
TRANCHES = 4
FIRST_START = "2000-01-01"


def load(a):
    C, _ = bp.load_panel(a.prices, a.delisted)
    C = C.loc[:, C.notna().sum() > 260]
    member = bp.membership_mask(C.index, list(C.columns))
    spy = bp.load_spy(C.index)
    keep = C.index >= spy.first_valid_index()
    C, member, spy = C.loc[keep], member[keep], spy.loc[keep]
    try:
        bond = pd.read_csv(a.etfs, index_col=0, parse_dates=True)["VFITX"].reindex(C.index).ffill()
    except Exception:                                              # noqa: BLE001
        bond = None
    if bond is None or bond.isna().mean() > 0.5:
        bond = pd.Series(1.02 ** (np.arange(len(C)) / 252), index=C.index)
    return C, member, spy, bond.bfill().values


def run_all_starts(C, member, spy, bond, horizon_years: list[int]):
    Cff = C.ffill()
    sig = Cff / Cff.rolling(200, min_periods=200).mean() - 1          # trend_200, as live
    switch = bp.market_state(spy).shift(1).fillna(True).astype(bool).values
    cnt = (sig.notna().to_numpy() & member).sum(axis=1)
    idx = C.index
    # one possible start per week (the first trading day of each week)
    wk = pd.Series(np.arange(len(idx)), index=idx).groupby(idx.to_period("W-FRI")).first()
    starts = [int(i) for i in wk if idx[i] >= pd.Timestamp(FIRST_START) and cnt[i] >= 100 and i >= 260]
    longest = max(horizon_years)
    last_ok = idx[-1] - pd.DateOffset(years=min(horizon_years))
    starts = [s for s in starts if idx[s] <= last_ok + pd.Timedelta(weeks=TRANCHES)]
    fs.START = POT
    curves = {}
    for n, s in enumerate(starts):
        eq, _ = val.run(sig, Cff, spy, member, s, switch, bond, delay=1)
        curves[s] = (eq / POT).astype(float)                       # growth of 1 from the start
        if n % 50 == 0:
            print(f"start {n + 1}/{len(starts)}  {idx[s].date()}", flush=True)
    return starts, curves


def value_at(curve: pd.Series, when: pd.Timestamp) -> float | None:
    c = curve[curve.index <= when]
    return float(c.iloc[-1]) if len(c) else None


def outcomes(starts, curves, spy, years: int):
    idx = spy.index
    rows = []
    for j, s in enumerate(starts):
        d0 = idx[s]
        end = d0 + pd.DateOffset(years=years)
        if end > idx[-1]:
            break
        # ONE START
        g1 = value_at(curves[s], end)
        # FOUR STARTS: tranche k starts k weeks later; until then it waits in the tracker
        parts = []
        for k in range(TRANCHES):
            if j + k >= len(starts):
                parts = []
                break
            sk = starts[j + k]
            wait = float(spy.iloc[sk] / spy.iloc[s])
            gk = value_at(curves[sk], end)
            if gk is None:
                parts = []
                break
            parts.append(wait * gk)
        g4 = float(np.mean(parts)) if parts else None
        gs = float(spy[spy.index <= end].iloc[-1] / spy.iloc[s])
        if g1 is None:
            continue
        rows.append({"start": str(d0.date()), "one": POT * g1, "four": POT * g4 if g4 else None,
                     "spy": POT * gs})
    return pd.DataFrame(rows)


def describe(df: pd.DataFrame, col: str) -> dict:
    d = df.dropna(subset=[col])
    diff = d[col] - d["spy"]
    return {"n": int(len(d)),
            "median": float(d[col].median()), "p10": float(d[col].quantile(0.10)),
            "p90": float(d[col].quantile(0.90)), "worst": float(d[col].min()), "best": float(d[col].max()),
            "spy_median": float(d["spy"].median()),
            "beat_share": float((diff > 0).mean()),
            "vs_spy_median": float(diff.median()), "vs_spy_p10": float(diff.quantile(0.10)),
            "vs_spy_p90": float(diff.quantile(0.90)),
            "luck_range": float(diff.quantile(0.90) - diff.quantile(0.10)),
            "worst_vs_spy": float(diff.min())}


def gbp(v: float) -> str:
    return f"£{v:,.0f}" if v >= 0 else f"−£{-v:,.0f}"


def write_md(out: dict, path: Path):
    L = ["# Start-date luck — does the day you start decide the result?\n",
         f"_Generated {out['generated'][:10]}. £10,000, {out['broker']} costs, one-day trading delay. "
         f"The strategy started on every week from {out['first']} and followed for 10 and 5 years._\n",
         "**One start:** all £10,000 on one day (the current plan). "
         "**Four starts:** four £2,500 portfolios started a week apart, each following the same rules.\n"]
    for yrs in ("10", "5"):
        r = out.get(f"y{yrs}")
        if not r:
            continue
        o, f = r["one"], r["four"]
        L += [f"## After {yrs} years ({o['n']} different start weeks)\n",
              "| | One start | Four starts | S&P 500 tracker |", "|---|---|---|---|",
              f"| Typical result | {gbp(o['median'])} | {gbp(f['median'])} | {gbp(o['spy_median'])} |",
              f"| Bad luck (1 start in 10 did worse) | {gbp(o['p10'])} | {gbp(f['p10'])} | |",
              f"| Good luck (1 start in 10 did better) | {gbp(o['p90'])} | {gbp(f['p90'])} | |",
              f"| Worst start | {gbp(o['worst'])} | {gbp(f['worst'])} | |",
              f"| Starts that beat the tracker | {o['beat_share']:.0%} | {f['beat_share']:.0%} | |",
              f"| Typical lead over the tracker | {gbp(o['vs_spy_median'])} | {gbp(f['vs_spy_median'])} | |",
              f"| Worst gap to the tracker | {gbp(o['worst_vs_spy'])} | {gbp(f['worst_vs_spy'])} | |",
              f"| **Luck range** (good-luck lead minus bad-luck lead) | **{gbp(o['luck_range'])}** | "
              f"**{gbp(f['luck_range'])}** | |", ""]
    v = out.get("verdict")
    if v:
        L += ["## Verdict\n", v, ""]
    L.append("_The luck range is how much the start week alone moved the result against the tracker. "
             "Smaller is steadier. Tested rules, not personal financial advice._")
    path.write_text("\n".join(L) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--delisted", default="data/delisted/delisted_weekly.parquet")
    ap.add_argument("--etfs", default="data/etf_prices.csv")
    ap.add_argument("--out", default="data/start_luck.json")
    ap.add_argument("--md", default="docs/START_LUCK.md")
    a = ap.parse_args()
    out = {"generated": pd.Timestamp.now("UTC").isoformat(), "broker": bp.BROKER_NAME, "pot": POT}
    C, member, spy, bond = load(a)
    starts, curves = run_all_starts(C, member, spy, bond, [10, 5])
    out["first"] = str(C.index[starts[0]].date())
    for yrs in (10, 5):
        df = outcomes(starts, curves, spy, yrs)
        if len(df) < 20:
            continue
        out[f"y{yrs}"] = {"one": describe(df, "one"), "four": describe(df, "four")}
        df.round(0).to_csv(f"data/start_luck_{yrs}y.csv", index=False)
    r = out.get("y10") or out.get("y5")
    if r:
        o, f = r["one"], r["four"]
        steadier = f["luck_range"] < o["luck_range"] * 0.9
        keeps = f["vs_spy_median"] >= 0.8 * o["vs_spy_median"] and f["beat_share"] >= o["beat_share"] - 0.05
        out["verdict"] = (
            ("**Use four starts.** " if steadier and keeps else
             "**Keep one start.** " if not steadier else
             "**Trade-off.** ")
            + f"Four starts cut the luck range from {gbp(o['luck_range'])} to {gbp(f['luck_range'])}, "
            f"with a typical lead over the tracker of {gbp(f['vs_spy_median'])} "
            f"(one start: {gbp(o['vs_spy_median'])}) and {f['beat_share']:.0%} of starts ahead "
            f"(one start: {o['beat_share']:.0%}).")
        out["use_four"] = bool(steadier and keeps)
    Path(a.out).write_text(json.dumps(out, indent=2))
    write_md(out, Path(a.md))
    print(Path(a.md).read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
