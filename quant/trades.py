"""
Trade-level simulation: entries, stops, trails, exits, costs.

WHY THIS EXISTS
---------------
Every test in this repo until now measured the AVERAGE FORWARD RETURN of a signal.
That is the wrong statistic for technical trading. A breakout system that cuts
losers at -11% and rides winners to +76% is right one time in three; its average
forward return is unremarkable, and every factor test would call it noise. The
edge lives in the asymmetry, not the accuracy.

So this module simulates actual trades:

    signal on the close of day t  ->  enter at the OPEN of day t+1
    initial stop  = entry - k_stop  * ATR(14) at entry
    trailing stop = highest close since entry - k_trail * ATR(14) at entry
    exit          = stop hit, trail hit, or max holding period reached

Returns are measured in R-MULTIPLES: R is the initial risk per share, so a trade
that loses exactly its stop is -1R and one that makes three times its risk is +3R.
That is how the strategies being mimicked here are actually judged.

FILL ASSUMPTIONS, DELIBERATELY PESSIMISTIC
------------------------------------------
Daily bars cannot tell us whether a stop inside the day's range was really filled
at that price, so:
  - a stop is triggered when the day's LOW reaches it,
  - and filled at min(stop, that day's OPEN) -- if the stock gapped straight
    through the level overnight, the fill is the gap price, not the stop.
  - exits on trail/time happen at the NEXT open, never at the closing price that
    generated the signal.
Every one of those choices costs the strategy money. That is the point.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


MIN_RISK_PCT = 0.005     # a stop closer than 0.5% of price is not a real stop
MIN_PRICE = 1.00         # below this, spreads and tick size dominate everything
R_CLIP = 10.0            # no single trade may dominate the average


def simulate(df: pd.DataFrame, entries: pd.Series, *, k_stop: float,
             k_trail: float, max_hold: int, direction: int = 1,
             cost_pct: float = 0.0, min_risk_pct: float = MIN_RISK_PCT,
             min_price: float = MIN_PRICE) -> pd.DataFrame:
    """
    Walk one instrument and turn entry flags into trades.

    entries   True on the bar whose CLOSE produced the signal. Entry is the next
              open, so nothing is ever bought at a price printed before the
              information existed.
    direction +1 long, -1 short.
    cost_pct  round-trip cost as a fraction of notional, charged to every trade.
    """
    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    lo = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    a = atr(df).to_numpy(float)
    sig = entries.to_numpy(bool)
    dates = df.index.to_numpy()
    n = len(df)

    trades = []
    i = 0
    while i < n - 2:
        if not sig[i] or not np.isfinite(a[i]) or a[i] <= 0:
            i += 1
            continue

        entry_i = i + 1
        entry = o[entry_i]
        if not np.isfinite(entry) or entry <= 0:
            i += 1
            continue

        risk = k_stop * a[i]                      # one R, in price terms

        # THE GUARD THAT THIS FILE ORIGINALLY LACKED.
        # R is net return divided by risk-as-a-fraction-of-price. On a stock
        # that has gone stale -- a delisted shell, a suspended line, a penny
        # stock printing the same price for weeks -- ATR collapses toward zero
        # and that division explodes: a 10bp cost against a 0.001% stop reads as
        # a 100R loss. Real breakout signals need movement so they rarely land
        # on such bars, but RANDOM entries land on them constantly, which is how
        # the control column filled up with values in the millions.
        if entry < min_price or risk / entry < min_risk_pct:
            i += 1
            continue

        stop = entry - direction * risk
        best = entry                              # best close seen so far
        exit_i, exit_px, reason = None, None, None

        for j in range(entry_i, min(entry_i + max_hold, n)):
            # 1. stop first: within a bar we cannot know the order of events, so
            #    assume the adverse extreme came first.
            hit = lo[j] <= stop if direction == 1 else h[j] >= stop
            if hit:
                gap = o[j] < stop if direction == 1 else o[j] > stop
                exit_i = j
                exit_px = o[j] if gap else stop   # gapped through? take the gap
                reason = "gap" if gap else "stop"
                break
            # 2. trail on closes, acted on at the next open
            best = max(best, c[j]) if direction == 1 else min(best, c[j])
            new_stop = best - direction * k_trail * a[i]
            stop = max(stop, new_stop) if direction == 1 else min(stop, new_stop)
            if j == min(entry_i + max_hold, n) - 1:
                exit_i, exit_px, reason = j, c[j], "time"

        if exit_i is None or exit_px is None or not np.isfinite(exit_px):
            i += 1
            continue

        gross = direction * (exit_px - entry) / entry
        net = gross - cost_pct
        r_raw = net * entry / risk                # net return expressed in R
        r_mult = float(np.clip(r_raw, -R_CLIP, R_CLIP))
        trades.append({
            "R_raw": r_raw, "clipped": bool(r_mult != r_raw),
            "entry_date": dates[entry_i], "exit_date": dates[exit_i],
            "bars": int(exit_i - entry_i), "entry": entry, "exit": exit_px,
            "gross_pct": gross, "net_pct": net, "R": r_mult, "reason": reason,
            "risk_pct": risk / entry,
        })
        i = exit_i + 1                            # no overlapping trades
    return pd.DataFrame(trades)


def stats(t: pd.DataFrame) -> dict:
    """Trade-level summary, in the terms a systems trader would recognise."""
    if t.empty:
        return {"trades": 0}
    wins, losses = t[t.R > 0], t[t.R <= 0]
    gross_win = wins.R.sum()
    gross_loss = -losses.R.sum()
    sd = t.R.std(ddof=1)
    return {
        "trades": int(len(t)),
        "win_rate": float(len(wins) / len(t)),
        "avg_win_R": float(wins.R.mean()) if len(wins) else 0.0,
        "avg_loss_R": float(losses.R.mean()) if len(losses) else 0.0,
        "expectancy_R": float(t.R.mean()),
        "expectancy_sd": float(sd),
        "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else None,
        "t_stat": float(t.R.mean() / (sd / np.sqrt(len(t)))) if sd > 0 else None,
        # what could this sample have proven, whatever the answer turned out to be
        "min_detectable_R": float(2 * sd / np.sqrt(len(t))) if sd > 0 else None,
        "median_bars": float(t.bars.median()),
        "pct_stopped": float((t.reason.isin(["stop", "gap"])).mean()),
        "pct_gapped_through": float((t.reason == "gap").mean()),
        "avg_net_pct": float(t.net_pct.mean()),
        "pct_clipped": float(t["clipped"].mean()) if "clipped" in t else 0.0,
    }
