#!/usr/bin/env python3
"""
THE LIVE STRATEGY -- exactly the rules that passed the stress tests.

    Score    how far each S&P 500 stock trades above its own 200-day average
    ENTER    a stock ranks in the top 5% of the S&P 500 on 3 weekly checks in a
             row (checked on the last trading day of each week), and one of the
             10 slots is free. Each slot = one tenth of the pot at the time.
    STAY     until the evidence clearly turns
    EXIT     it has fallen into the bottom half on 3 weekly checks in a row
    MARKET   S&P 500 below its 200-day average for 3 closes -> sell everything
             into a bond fund; back into the S&P tracker after 3 closes above
    IDLE     money not in a stock sits in an S&P 500 tracker fund

Stress tests (docs/ROBUSTNESS*.md): at a GBP 100k pot it beat the S&P 500 after
HL costs in both 1997-2011 and 2011-2026 in 20 of 20 variations; at GBP 10k in
15 of 20 -- costs bite harder on small positions.

How today's position is worked out: the rules are replayed over the last two
years of prices, check by check, exactly as they would have run. The result is
the portfolio you would hold today had you followed them -- and this week's
BUYs and SELLs. Recomputed from scratch every day, so it can never drift.

From the first run on, every day's value is logged to data/strategy_log.jsonl:
a live, forward record that no backtest can fake.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("fs", HERE / "factor_screen.py")
fs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fs)
bp = fs.bp

SCORE = "trend_200"
REPLAY_FROM = "2024-01-05"   # fixed anchor, so the replay is identical every day


def week_ends(idx: pd.DatetimeIndex) -> list[int]:
    """Index of the last trading day of each calendar week."""
    s = pd.Series(np.arange(len(idx)), index=idx)
    ends = list(s.groupby(idx.to_period("W-FRI")).max().astype(int))
    # the current week only counts once it is complete (Friday's close is in)
    if ends and idx[ends[-1]].weekday() != 4:
        ends = ends[:-1]
    return ends


def live(P: pd.DataFrame, sp500: list[str], pot: float, bond: pd.Series | None = None) -> dict:
    """P: daily closes incl. SPY. sp500: today's S&P 500 tickers (Yahoo symbols)."""
    spy = P["SPY"].dropna()
    cols = [c for c in sp500 if c in P.columns and c != "SPY"]
    C = P[cols].reindex(spy.index)
    Cff = C.ffill()
    member = np.ones(C.shape, bool)
    sig = Cff / Cff.rolling(200, min_periods=200).mean() - 1
    if bond is None or bond.reindex(spy.index).notna().mean() < 0.5:
        bond = pd.Series(1.02 ** (np.arange(len(spy)) / 252), index=spy.index)
    bond = bond.reindex(spy.index).ffill().bfill()
    switch = bp.market_state(spy).shift(1).fillna(True).astype(bool)
    fs.START = pot
    checks = week_ends(spy.index)
    anchor = pd.Timestamp(REPLAY_FROM)
    start = next(i for i in checks if spy.index[i] >= anchor and i >= 220)
    eq, t = fs.commit_portfolio(sig, Cff, spy, member, start, True, switch.values, bond.values,
                                check_idx=checks, return_state=True)
    st = t["state"]
    last_check = st["as_of_check"]
    today = str(spy.index[-1].date())
    this_week = [a for a in st["actions"] if a[0] == last_check]
    total = sum(h["value"] for h in st["holdings"]) + st["tracker_value"] + st["bond_value"]
    # show everything as shares of YOUR pot today (the replay has grown or shrunk since 2024)
    f = pot / total if total else 1.0
    hold = sorted(st["holdings"], key=lambda h: -h["value"])
    for h in hold:
        h["weight"] = h["value"] / total if total else 0
        h["value"] *= f
        h["gain"] = h["price"] / h["bought_at"] - 1
        h["score"] = float(sig[h["ticker"]].iloc[-1])
    return {
        "score": SCORE, "pot": pot, "as_of": today, "last_check": last_check,
        "is_check_day": last_check == today,
        "market_on": bool(switch.iloc[-1]),
        "spy_vs_200d": float(spy.iloc[-1] / spy.rolling(200).mean().iloc[-1] - 1),
        "holdings": hold, "tracker_value": st["tracker_value"] * f, "bond_value": st["bond_value"] * f,
        "total_value": pot, "replay_total": total,
        "this_week": [(d, a, tk, g * f) for d, a, tk, g in this_week], "recent": st["actions"][-15:],
        "on_deck": st["on_deck"],
        "replay_from": str(spy.index[start].date()),
        "replay_vs_spy": float(eq.iloc[-1] / pot - 1) - float(spy.iloc[-1] / spy.iloc[start] - 1) if len(eq) else None,
        "replay_value_start": pot, "replay_value_now": float(eq.iloc[-1]) if len(eq) else pot,
        "spy_since_replay": float(spy.iloc[-1] / spy.iloc[start] - 1),
    }


def log_day(res: dict, path="data/strategy_log.jsonl"):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
    if rows and rows[-1]["as_of"] == res["as_of"]:
        rows = rows[:-1]
    rows.append({"as_of": res["as_of"], "value": round(res["replay_total"], 2),
                 "market_on": res["market_on"],
                 "holdings": [h["ticker"] for h in res["holdings"]]})
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return rows


def markdown(res: dict, log_rows: list[dict], spy_now: float | None = None) -> list[str]:
    L = ["## ▶ THE STRATEGY — what to do\n",
         "_Momentum stocks held under commit rules, with the market switch. The only stock "
         "picker to beat the S&P 500 in both halves of 1997–2026 after HL costs and survive the "
         "stress tests (20 of 20 variations at a £100k pot; 15 of 20 at £10k). Rules are checked "
         "on the last trading day of each week; nothing happens between checks except the "
         "market switch._\n",
         f"**Market switch: {'ON — invested' if res['market_on'] else 'OFF — everything in bonds'}** "
         f"(S&P 500 {res['spy_vs_200d']:+.1%} vs its 200-day average)\n"]
    wk = res["this_week"]
    if res["is_check_day"]:
        L.append("### Today is a check day. Actions:\n")
    else:
        L.append(f"### Last check: {res['last_check']}. Actions from that check "
                 "(nothing new until the next weekly check):\n")
    if wk:
        L += ["| Action | Stock | Amount |", "|---|---|---|"]
        for d, act, tk, gbp in wk:
            L.append(f"| **{act}** | {tk or '—'} | £{gbp:,.0f} |")
        L.append("\n_Buys are paid for by selling the same amount of your S&P 500 tracker; sales go "
                 "back into the tracker._\n")
    else:
        L.append("**No trades. HOLD everything.**\n")
    L += [f"### Holdings (£{res['pot']:,.0f} pot, as the rules would hold it today)\n",
          "| Stock | Bought | Gain since | Value | Share of pot | Weeks weak (3 = SELL) |",
          "|---|---|---|---|---|---|"]
    for h in res["holdings"]:
        L.append(f"| **{h['ticker']}** | {h['bought']} | {h['gain']:+.0%} | £{h['value']:,.0f} | "
                 f"{h['weight']:.0%} | {h['weeks_weak']} |")
    if res["tracker_value"] > 1:
        L.append(f"| S&P 500 tracker (e.g. Vanguard S&P 500 UCITS ETF) | | | £{res['tracker_value']:,.0f} | "
                 f"{res['tracker_value'] / res['total_value']:.0%} | |")
    if res["bond_value"] > 1:
        L.append(f"| Bond fund | | | £{res['bond_value']:,.0f} | "
                 f"{res['bond_value'] / res['total_value']:.0%} | |")
    if res["on_deck"]:
        L.append("\n**On deck** (in the top 5%, not yet confirmed — a BUY if still there at "
                 "3 weekly checks): " + ", ".join(f"{d['ticker']} ({d['weeks_in_top']} of 3)"
                                                for d in res["on_deck"]))
    if res["recent"]:
        L += ["\n**Recent actions:** " + "; ".join(f"{d} {a} {t}".strip() for d, a, t, _ in res["recent"][-8:])]
    if len(log_rows) >= 2:
        first = log_rows[0]
        g = log_rows[-1]["value"] / first["value"]
        L.append(f"\n**Live record since {first['as_of']}:** £{res['pot']:,.0f} would now be "
                 f"£{res['pot'] * g:,.0f} ({g - 1:+.1%}).")
    else:
        L.append(f"\n**Live record starts today** ({res['as_of']}). From tomorrow this line shows "
                 "the strategy's real, forward performance.")
    # standing verdict from the latest monthly validation run for this pot
    try:
        tag = bp.out_tag(res["pot"])
        v = json.loads(Path(f"data/validation{tag}.json").read_text())
        ok = sum(1 for x in v.get("checks", {}).values() if x is True or str(x) == "True")
        n = len(v.get("checks", {}))
        L.append(f"\n**Trust checks (validation of {v['generated'][:10]}, £{res['pot']:,.0f} pot): "
                 f"{ok} of {n} passed.** "
                 + ("Cleared for consideration — watch the live record." if n and ok == n else
                    "⚠ NOT cleared at this pot size — do not trade real money on it yet. "
                    "See docs/VALIDATION" + tag + ".md"))
    except Exception:                                              # noqa: BLE001
        pass
    L.append("")
    return L
