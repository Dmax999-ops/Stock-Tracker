#!/usr/bin/env python3
"""
THE THREE-MONTH PAPER TEST -- six pretend accounts, run forward on real prices.

From Monday 28 September 2026, the live strategy is "invested" at:
    GBP 10,000 and GBP 100,000
with each broker's real charges:
    Hargreaves Lansdown, Trading 212, Interactive Brokers
and compared every day with the same money in an S&P 500 tracker.

How each account works: on the start day it buys exactly what the strategy
holds (paying that broker's dealing and FX charges on every purchase), then
follows the rules -- weekly checks, 3-week confirmations, the market switch --
paying that broker's charges on every trade. The size of the account decides
the costs (HL's FX is tiered), so each pot is simulated at its true size.

Nothing here can be tuned after the fact: the rules were fixed before the test
started, and each day's values are appended to data/paper_test.csv and never
rewritten. This is a TEST -- to be replaced when real money goes in.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("strategy", HERE / "strategy.py")
strat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(strat)
fs, bp = strat.fs, strat.bp

START = pd.Timestamp("2026-09-28")
END = START + pd.DateOffset(months=3)
POTS = [10_000, 100_000]
BROKERS = {"hl": ("Hargreaves Lansdown", 6.95), "t212": ("Trading 212", 0.0),
           "ibkr": ("Interactive Brokers", 1.0)}
CSV = Path("data/paper_test.csv")


def accounts(P: pd.DataFrame, sp500: list[str], bond: pd.Series | None) -> pd.DataFrame:
    """
    Daily value of every account from START to the latest close.

    The DECISIONS (what to buy and sell, and when) come from one run of the
    strategy's rules, so all six accounts hold exactly the same stocks. Each
    account then pays its own broker's charges on every one of those trades.
    """
    spy = P["SPY"].dropna()
    if spy.index[-1] < START:
        return pd.DataFrame()
    cols = [c for c in sp500 if c in P.columns and c != "SPY"]
    C = P[cols].reindex(spy.index)
    Cff = C.ffill()
    X = Cff
    sig = Cff / Cff.rolling(200, min_periods=200).mean() - 1
    if bond is None or bond.reindex(spy.index).notna().mean() < 0.5:
        bond = pd.Series(1.02 ** (np.arange(len(spy)) / 252), index=spy.index)
    bond = bond.reindex(spy.index).ffill().bfill()
    switch = bp.market_state(spy).shift(1).fillna(True).astype(bool).values
    checks = strat.week_ends(spy.index)
    anchor = pd.Timestamp(strat.REPLAY_FROM)
    r0 = next(i for i in checks if spy.index[i] >= anchor and i >= 220)
    s_i = int(spy.index.searchsorted(START))
    d0 = spy.index[s_i]
    member = np.ones(C.shape, bool)
    fs.START = 100_000
    # the portfolio the rules hold at the start day's close ...
    n0 = s_i + 1
    _, t0 = fs.commit_portfolio(sig.iloc[:n0], Cff.iloc[:n0], spy.iloc[:n0], member[:n0], r0, True,
                                switch[:n0], bond.values[:n0], check_idx=[c for c in checks if c < n0],
                                return_state=True)
    st0 = t0["state"]
    # ... and every decision the rules take after it
    _, t1 = fs.commit_portfolio(sig, Cff, spy, member, r0, True, switch, bond.values,
                                check_idx=checks, return_state=True)
    acts = [a for a in t1["state"]["all_actions"] if pd.Timestamp(a[0]) > d0]
    tot0 = sum(h["value"] for h in st0["holdings"]) + st0["tracker_value"] + st0["bond_value"]
    w = {h["ticker"]: h["value"] / tot0 for h in st0["holdings"]}
    w_tr, w_bd = st0["tracker_value"] / tot0, st0["bond_value"] / tot0
    days = spy.index[s_i:]
    out = {}
    broker0, deal0 = bp.BROKER, fs.DEAL
    try:
        for b, (bname, deal) in BROKERS.items():
            bp.BROKER = b
            fx = bp.fx_cost
            for pot in POTS:
                sh = {}
                for tk, wt in w.items():
                    amt = pot * wt
                    sh[tk] = max(amt - deal - fx(amt - deal), 0) / X[tk].iloc[s_i]
                tr = max(pot * w_tr - deal, 0) / spy.iloc[s_i] if w_tr > 0 else 0.0
                bd = max(pot * w_bd - deal, 0) / bond.iloc[s_i] if w_bd > 0 else 0.0
                cash = 0.0
                by_day = {}
                for a in acts:
                    by_day.setdefault(a[0], []).append(a)
                vals = []
                for d in days:
                    i = spy.index.get_loc(d)
                    px = lambda t: float(X[t].iloc[i])                       # noqa: E731
                    for _, act, tk, _g in by_day.get(str(d.date()), []):
                        if act.startswith("SELL") and tk in sh:
                            g = sh.pop(tk) * px(tk)
                            net = max(g - fx(g) - deal, 0)
                            if act == "SELL":
                                tr += max(net - deal, 0) / spy.iloc[i]
                            else:
                                cash += net
                        elif act == "MOVE ALL TO BONDS":
                            cash += max(tr * spy.iloc[i] - deal, 0) if tr > 0 else 0
                            tr = 0.0
                            bd += max(cash - deal, 0) / bond.iloc[i]
                            cash = 0.0
                        elif act.startswith("MOVE BONDS BACK"):
                            tr += max(bd * bond.iloc[i] - 2 * deal, 0) / spy.iloc[i]
                            bd = 0.0
                        elif act == "BUY":
                            total = tr * spy.iloc[i] + bd * bond.iloc[i] + cash + sum(
                                u * px(t) for t, u in sh.items())
                            per = total / fs.SLOTS
                            if tr * spy.iloc[i] >= per + deal:
                                tr -= (per + deal) / spy.iloc[i]
                                sh[tk] = sh.get(tk, 0) + max(per - deal - fx(per - deal), 0) / px(tk)
                    vals.append(tr * spy.iloc[i] + bd * bond.iloc[i] + cash
                                + sum(u * px(t) for t, u in sh.items() if np.isfinite(px(t))))
                out[f"{bname} £{pot:,.0f}"] = pd.Series(vals, index=days)
        for pot in POTS:
            s = spy.loc[days]
            out[f"S&P 500 tracker £{pot:,.0f}"] = s / s.iloc[0] * (pot - 6.95)
    finally:
        bp.BROKER, fs.DEAL = broker0, deal0
    return pd.DataFrame(out).round(2)


def update(P, sp500, bond) -> list[str]:
    """Recompute, append new days to the CSV (never rewrite old ones), return markdown."""
    A = accounts(P, sp500, bond)
    if A.empty:
        return [f"## 🧪 Paper test — starts Monday {START.date()}\n",
                "Six pretend accounts (£10k and £100k × Hargreaves Lansdown, Trading 212, "
                "Interactive Brokers) will be invested in the strategy at Monday's close and "
                "tracked every day for three months against the S&P 500.\n"]
    A.index.name = "date"
    CSV.parent.mkdir(parents=True, exist_ok=True)
    if CSV.exists():
        old = pd.read_csv(CSV, index_col=0, parse_dates=True)
        new = A[A.index > old.index.max()]
        A = pd.concat([old, new])
    A.to_csv(CSV)
    last = A.iloc[-1]
    days = len(A)
    L = [f"## 🧪 Paper test — day {days} of about 65 (started {START.date()}, ends {END.date()})\n",
         "Pretend money, real prices, rules fixed in advance. Values after each broker's charges.\n",
         "| Account | Started | Now | Change | vs S&P 500 tracker (same money) |",
         "|---|---|---|---|---|"]
    for pot in POTS:
        spy_now = last[f"S&P 500 tracker £{pot:,.0f}"]
        for b, (bname, _) in BROKERS.items():
            v = last[f"{bname} £{pot:,.0f}"]
            L.append(f"| {bname} | £{pot:,.0f} | £{v:,.0f} | {v / pot - 1:+.1%} | "
                     f"{(v - spy_now) / pot:+.1%} (£{v - spy_now:+,.0f}) |")
        L.append(f"| *S&P 500 tracker* | £{pot:,.0f} | £{spy_now:,.0f} | {spy_now / pot - 1:+.1%} | — |")
    L.append(f"\nDaily history: data/paper_test.csv\n")
    return L
