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
LAST: dict | None = None     # latest figures, for the email
TRADES: dict = {}            # every trade of every account, for the tax tracker
SETUP: dict = {}             # what each account bought on day one


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
    global TRADES, SETUP
    TRADES, SETUP = {}, {}
    TR, BD = "S&P 500 tracker", "Bond fund"
    broker0, deal0 = bp.BROKER, fs.DEAL
    try:
        for b, (bname, deal) in BROKERS.items():
            bp.BROKER = b
            fx = bp.fx_cost
            for pot in POTS:
                # START: exactly `pot` goes into the investments; the charges are paid on top
                log, setup = [], []
                d0s = str(d0.date())
                sh = {}
                for tk, wt in w.items():
                    amt = pot * wt
                    paid = amt + fx(amt) + deal
                    sh[tk] = amt / X[tk].iloc[s_i]
                    log.append({"date": d0s, "asset": tk, "side": "BUY", "qty": sh[tk], "gbp": paid})
                    setup.append((tk, amt, paid - amt))
                tr = pot * w_tr / spy.iloc[s_i] if w_tr > 0 else 0.0
                if tr:
                    log.append({"date": d0s, "asset": TR, "side": "BUY", "qty": tr, "gbp": pot * w_tr + deal})
                    setup.append((TR, pot * w_tr, deal))
                bd = pot * w_bd / bond.iloc[s_i] if w_bd > 0 else 0.0
                if bd:
                    log.append({"date": d0s, "asset": BD, "side": "BUY", "qty": bd, "gbp": pot * w_bd + deal})
                    setup.append((BD, pot * w_bd, deal))
                deposit = sum(x[1] + x[2] for x in setup)
                SETUP[f"{bname} £{pot:,.0f}"] = {"deposit": deposit, "rows": setup}
                cash = 0.0
                by_day = {}
                for a in acts:
                    by_day.setdefault(a[0], []).append(a)
                vals = []
                for d in days:
                    i = spy.index.get_loc(d)
                    ds = str(d.date())
                    px = lambda t: float(X[t].iloc[i])                       # noqa: E731
                    for _, act, tk, _g in by_day.get(ds, []):
                        if act.startswith("SELL") and tk in sh:
                            q = sh.pop(tk)
                            g = q * px(tk)
                            net = max(g - fx(g) - deal, 0)
                            log.append({"date": ds, "asset": tk, "side": "SELL", "qty": q, "gbp": net})
                            if act == "SELL":
                                u = max(net - deal, 0) / spy.iloc[i]
                                tr += u
                                log.append({"date": ds, "asset": TR, "side": "BUY", "qty": u, "gbp": net})
                            else:
                                cash += net
                        elif act == "MOVE ALL TO BONDS":
                            if tr > 0:
                                net = max(tr * spy.iloc[i] - deal, 0)
                                log.append({"date": ds, "asset": TR, "side": "SELL", "qty": tr, "gbp": net})
                                cash += net
                            tr = 0.0
                            u = max(cash - deal, 0) / bond.iloc[i]
                            if u:
                                log.append({"date": ds, "asset": BD, "side": "BUY", "qty": u, "gbp": cash})
                            bd += u
                            cash = 0.0
                        elif act.startswith("MOVE BONDS BACK"):
                            if bd > 0:
                                net = max(bd * bond.iloc[i] - deal, 0)
                                log.append({"date": ds, "asset": BD, "side": "SELL", "qty": bd, "gbp": net})
                                u = max(net - deal, 0) / spy.iloc[i]
                                log.append({"date": ds, "asset": TR, "side": "BUY", "qty": u, "gbp": net})
                                tr += u
                            bd = 0.0
                        elif act == "BUY":
                            total = tr * spy.iloc[i] + bd * bond.iloc[i] + cash + sum(
                                u * px(t) for t, u in sh.items())
                            per = total / fs.SLOTS
                            if tr * spy.iloc[i] >= per + deal:
                                u = (per + deal) / spy.iloc[i]
                                tr -= u
                                log.append({"date": ds, "asset": TR, "side": "SELL", "qty": u, "gbp": per})
                                q = max(per - deal - fx(per - deal), 0) / px(tk)
                                sh[tk] = sh.get(tk, 0) + q
                                log.append({"date": ds, "asset": tk, "side": "BUY", "qty": q, "gbp": per})
                    vals.append(tr * spy.iloc[i] + bd * bond.iloc[i] + cash
                                + sum(u * px(t) for t, u in sh.items() if np.isfinite(px(t))))
                key = f"{bname} £{pot:,.0f}"
                out[key] = pd.Series(vals, index=days)
                # what it would be worth, and the gain, if everything were sold at today's close
                li = len(spy) - 1
                TRADES[key] = {"log": log,
                               "holdings": {**{t: u * float(X[t].iloc[li]) for t, u in sh.items()},
                                            TR: tr * float(spy.iloc[li]), BD: bd * float(bond.iloc[li])},
                               "qty": {**sh, TR: tr, BD: bd}}
        for pot in POTS:
            s = spy.loc[days]
            out[f"S&P 500 tracker £{pot:,.0f}"] = s / s.iloc[0] * pot
    finally:
        bp.BROKER, fs.DEAL = broker0, deal0
    return pd.DataFrame(out).round(2)


def _gbp(v: float) -> str:
    return f"£{v:,.0f}" if v >= 0 else f"−£{-v:,.0f}"


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
    global LAST
    LAST = {"day": days, "start": START.strftime("%d %b %Y"),
            "pots": {pot: [(bname, float(last[f"{bname} £{pot:,.0f}"]),
                            float(last[f"{bname} £{pot:,.0f}"] - last[f"S&P 500 tracker £{pot:,.0f}"]))
                           for b, (bname, _) in BROKERS.items()]
                          + [("S&P 500 tracker", float(last[f"S&P 500 tracker £{pot:,.0f}"]), None)]
                     for pot in POTS}}
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
    # ---- UK tax on each account (general investment account; an ISA pays none) --
    spec = importlib.util.spec_from_file_location("uk_tax", HERE / "uk_tax.py")
    ut = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ut)
    tax, rows_csv = {}, []
    for key, t in TRADES.items():
        disp = ut.disposals(t["log"])
        years = ut.by_tax_year(disp)
        realised = sum(d["gain"] for d in disp)
        # gain not yet taxed: sell everything at today's close (before sale charges)
        today = str(A.index[-1].date())
        hyp = t["log"] + [{"date": pd.Timestamp(today) + pd.Timedelta(days=3650), "asset": a,
                           "side": "SELL", "qty": q, "gbp": t["holdings"][a]}
                          for a, q in t["qty"].items() if q > 0]
        unreal = sum(d["gain"] for d in ut.disposals(hyp)) - realised
        tax[key] = {"years": years, "realised": realised, "unrealised": unreal,
                    "sales": len(disp)}
        for r in t["log"]:
            rows_csv.append({"account": key, **r})
    pd.DataFrame(rows_csv).to_csv(CSV.with_name("paper_trades.csv"), index=False)
    LAST["tax"] = tax
    LAST["setup"] = SETUP
    L += ["### UK tax so far (if held outside an ISA)\n",
          "| Account | Gains taken (realised) | Tax this year at 18% / 24% | Pay by | Gain not yet taken |",
          "|---|---|---|---|---|"]
    for key, t in tax.items():
        y = t["years"][-1] if t["years"] else None
        L.append(f"| {key} | {_gbp(t['realised'])} | "
                 + (f"£{y['tax_basic']:,.0f} / £{y['tax_higher']:,.0f} | {y['due']}" if y else "£0 / £0 | —")
                 + f" | {_gbp(t['unrealised'])} |")
    L.append("\n_First £3,000 of net gains each tax year is tax-free. Nothing is paid until 31 January "
             "after the tax year ends. In a Stocks & Shares ISA none of this is taxed. Estimate, not tax advice._\n")
    return L
