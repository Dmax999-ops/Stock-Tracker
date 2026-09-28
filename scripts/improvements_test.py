#!/usr/bin/env python3
"""
IMPROVEMENTS TEST -- three possible changes, each tested on the full history
(S&P 500 members at the time, delisted companies included), GBP 10,000,
Trading 212 costs, one-day trading delay:

  CASH      when the market switch is OFF and the bond fund is ALSO below its
            own 200-day average, hold cash instead of bonds (years like 2022)
  PARTIAL   when a sale leaves less than a full slot in the tracker, still buy
            the next confirmed stock with what is there (30% or 50% of a slot)
  SWITCH    the market switch after 2 or 5 closes instead of 3

A change is only recommended if it beats the current rules in BOTH halves of
history (1997-2011 and 2011-2026) and on a typical 10-year start.
Results: docs/IMPROVEMENTS.md
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_vs = importlib.util.spec_from_file_location("validation", HERE / "validation.py")
val = importlib.util.module_from_spec(_vs)
_vs.loader.exec_module(val)
fs, bp = val.fs, val.bp

POT = 10_000.0
EVERY_WEEKS = 8
VARIANTS = [
    {"name": "current rules"},
    {"name": "cash when bonds are falling too", "cash": True},
    {"name": "fill a slot from 50% of its size", "partial": 0.5},
    {"name": "fill a slot from 30% of its size", "partial": 0.3},
    {"name": "market switch after 2 closes", "confirm": 2},
    {"name": "market switch after 5 closes", "confirm": 5},
]


def gbp(v: float) -> str:
    return f"£{v:,.0f}" if v >= 0 else f"−£{-v:,.0f}"


def load():
    C, _ = bp.load_panel("data/prices.parquet", "data/delisted/delisted_weekly.parquet")
    C = C.loc[:, C.notna().sum() > 260]
    member = bp.membership_mask(C.index, list(C.columns))
    spy = bp.load_spy(C.index)
    keep = C.index >= spy.first_valid_index()
    C, member, spy = C.loc[keep], member[keep], spy.loc[keep]
    try:
        bond = pd.read_csv("data/etf_prices.csv", index_col=0, parse_dates=True)["VFITX"].reindex(C.index).ffill()
    except Exception:                                              # noqa: BLE001
        bond = None
    if bond is None or bond.isna().mean() > 0.5:
        bond = pd.Series(1.02 ** (np.arange(len(C)) / 252), index=C.index)
    return C, member, spy, bond.bfill().values


def cash_when_weak(bond: np.ndarray) -> np.ndarray:
    """Bond fund, but earning nothing (cash) on days after it closed below its own 200-day average."""
    b = pd.Series(bond)
    weak = (b < b.rolling(200, min_periods=200).mean()).shift(1, fill_value=False).to_numpy(bool)
    r = b.pct_change().fillna(0).to_numpy().copy()
    r[weak] = 0.0
    return np.cumprod(1 + r) * float(b.iloc[0])


def main() -> int:
    C, member, spy, bond0 = load()
    Cff = C.ffill()
    sig = Cff / Cff.rolling(200, min_periods=200).mean() - 1
    confirm0 = bp.dp.CONFIRM
    cnt = (sig.notna().to_numpy() & member).sum(axis=1)
    idx = C.index
    first = next(i for i in range(260, len(idx)) if cnt[i] >= 100)
    mid = idx.searchsorted(pd.Timestamp("2011-01-01"))
    wk = pd.Series(np.arange(len(idx)), index=idx).groupby(idx.to_period("W-FRI")).first()
    starts = [int(i) for i in wk if i >= first and idx[i] >= pd.Timestamp("2000-01-01")
              and idx[i] <= idx[-1] - pd.DateOffset(years=10)][::EVERY_WEEKS]
    fs.START = POT
    out = {"generated": pd.Timestamp.now("UTC").isoformat(), "broker": bp.BROKER_NAME,
           "from": str(idx[first].date()), "to": str(idx[-1].date()), "variants": {}}
    for v in VARIANTS:
        name = v["name"]
        bp.dp.CONFIRM = v.get("confirm", confirm0)
        fs.PARTIAL_SLOT = v.get("partial")
        switch = bp.market_state(spy).shift(1).fillna(True).astype(bool).values
        bond = cash_when_weak(bond0) if v.get("cash") else bond0
        try:
            eq, t = val.run(sig, Cff, spy, member, first, switch, bond, delay=1)
            eq = eq.astype(float)
            s = spy.reindex(eq.index)
            halves = {}
            for lab, a, b in (("1997-2011", eq.index[0], idx[mid]), ("2011-2026", idx[mid], eq.index[-1])):
                e = eq.loc[a:b]
                sp_ = s.loc[a:b]
                halves[lab] = {"strategy": POT * float(e.iloc[-1] / e.iloc[0]),
                               "spy": POT * float(sp_.iloc[-1] / sp_.iloc[0])}
            tens = []
            for st in starts:
                e2, _ = val.run(sig, Cff, spy, member, st, switch, bond, delay=1)
                e2 = e2.astype(float)
                end = idx[st] + pd.DateOffset(years=10)
                e2 = e2[e2.index <= end]
                g = float(e2.iloc[-1] / POT)
                gs = float(spy[spy.index <= end].iloc[-1] / spy.iloc[st])
                tens.append((g, gs))
            g = np.array(tens)
            yr = eq.resample("YE").last()
            yret = (yr / yr.shift(1) - 1)
            ys = s.resample("YE").last()
            ysr = (ys / ys.shift(1) - 1)
            out["variants"][name] = {
                "y2008": float(yret.get(pd.Timestamp("2008-12-31"), np.nan)),
                "y2022": float(yret.get(pd.Timestamp("2022-12-31"), np.nan)),
                "spy2008": float(ysr.get(pd.Timestamp("2008-12-31"), np.nan)),
                "spy2022": float(ysr.get(pd.Timestamp("2022-12-31"), np.nan)),
                "whole": POT * float(eq.iloc[-1] / eq.iloc[0]),
                "spy_whole": POT * float(s.iloc[-1] / s.iloc[0]),
                "max_fall": float((eq / eq.cummax() - 1).min()),
                "trades_per_year": t.get("trades_per_year"),
                "halves": halves,
                "ten_median": POT * float(np.median(g[:, 0])),
                "ten_p10": POT * float(np.percentile(g[:, 0], 10)),
                "ten_spy_median": POT * float(np.median(g[:, 1])),
                "ten_beat": float((g[:, 0] > g[:, 1]).mean()),
                "n_starts": len(g)}
            print(name, out["variants"][name], flush=True)
        finally:
            fs.PARTIAL_SLOT = None
            bp.dp.CONFIRM = confirm0
    base = out["variants"]["current rules"]
    L = ["# Improvements test — cash, slot filling, market switch speed\n",
         f"_Generated {out['generated'][:10]}. £10,000, {out['broker']} costs, one-day trading delay, "
         f"{out['from']} to {out['to']}, S&P 500 members at the time including companies that later failed._\n",
         "Each row changes ONE thing from the current rules.\n",
         "| | Whole period | 1997–2011 | 2011–2026 | 10 years, typical | 10 years, bad luck (1 in 10) "
         "| Starts beating the S&P | Worst fall | 2008 | 2022 | Trades a year |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, v in out["variants"].items():
        h = v["halves"]
        L.append(f"| **{name}** | {gbp(v['whole'])} | {gbp(h['1997-2011']['strategy'])} | "
                 f"{gbp(h['2011-2026']['strategy'])} | {gbp(v['ten_median'])} | {gbp(v['ten_p10'])} | "
                 f"{v['ten_beat']:.0%} | {v['max_fall']:.0%} | {v['y2008']:+.0%} | {v['y2022']:+.0%} | "
                 f"{v['trades_per_year']} |")
    h = base["halves"]
    L.append(f"| *S&P 500 tracker* | {gbp(base['spy_whole'])} | {gbp(h['1997-2011']['spy'])} | "
             f"{gbp(h['2011-2026']['spy'])} | {gbp(base['ten_spy_median'])} | | | | "
             f"{base['spy2008']:+.0%} | {base['spy2022']:+.0%} | |")
    # verdict: a stop must beat the current rules in BOTH halves and on the typical 10 years
    best, winners = None, []
    for name, v in out["variants"].items():
        if name == "current rules":
            continue
        ok = (v["halves"]["1997-2011"]["strategy"] > base["halves"]["1997-2011"]["strategy"]
              and v["halves"]["2011-2026"]["strategy"] > base["halves"]["2011-2026"]["strategy"]
              and v["ten_median"] > base["ten_median"] and v["ten_beat"] >= base["ten_beat"] - 0.03)
        if ok:
            winners.append(name)
        if ok and (best is None or v["ten_median"] > out["variants"][best]["ten_median"]):
            best = name
    out["verdict"] = best or "current rules"
    out["passed"] = winners
    L += ["", "## Verdict\n",
          ("**Passed:** " + "; ".join(f"{w} ({gbp(out['variants'][w]['ten_median'])} typical over 10 years)"
                                       for w in winners)
           + f" — against {gbp(base['ten_median'])} for the current rules. Best: **{best}**."
           if winners else
           "**Keep the current rules.** None of the changes beat them in both halves of history and on a "
           "typical 10-year start."),
          "", "_A change only counts if it wins in both halves of history, so it is not fitted to one period. "
          "Tested rules, not personal financial advice._"]
    Path("docs/IMPROVEMENTS.md").write_text("\n".join(L) + "\n")
    Path("data/improvements.json").write_text(json.dumps(out, indent=2, default=str))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
