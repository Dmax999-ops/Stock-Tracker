"""
Six-state classifier.

WHAT THE EVIDENCE SAYS (498 S&P stocks, 461,930 stock-days, 2013-2018, daily bars):

    state            1-month fwd    t vs universe
    CAPITULATION        +1.57%          +4.35      <- buy
    FALLING             +1.19%          +1.81
    COOLING             +0.94%          +0.64
    STEADY              +0.82%          -0.58
    STRONG              +0.80%          -0.86
    TOPPING             +0.41%          -3.82      <- avoid / reduce

Only two states carry statistical weight, and they are the two extremes. Everything
between them is noise -- do not trade on STRONG/STEADY/COOLING distinctions, they
did not survive breadth.

A WARNING ABOUT THE CAPITULATION RESULT: the training universe is index membership
as of the end of the sample, so companies that capitulated and then went bankrupt
or were delisted are ABSENT. Buy-the-dip always looks good when the dips that never
recovered have been deleted. Treat +1.57% as an optimistic ceiling until this is
retrained on a survivorship-free universe.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LOOKBACK = 252          # normalisation window, trading days


def _z(x: pd.Series, w: int = LOOKBACK) -> pd.Series:
    m = x.rolling(w, min_periods=w // 2).mean()
    s = x.rolling(w, min_periods=w // 2).std(ddof=0)
    return (x - m) / s.replace(0, np.nan)


def components(px: pd.DataFrame, w: int = LOOKBACK) -> pd.DataFrame:
    """
    The five inputs to the heat reading. All backward-looking: each value uses
    only the trailing window, never the full sample.
    """
    C, = (px["close"],)
    d = C.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    loss = (-d).clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rsi = 100 - 100 / (1 + gain / loss.replace(0, np.nan))

    ma200 = C.rolling(200, min_periods=100).mean()
    sd = C.rolling(w, min_periods=w // 2).std(ddof=0)

    return pd.DataFrame({
        "rsi":    _z(rsi, w),
        "z200":   (C - ma200) / sd.replace(0, np.nan),
        "vs_ma":  _z(C / ma200 - 1, w),
        "fromhi": _z(C / C.rolling(w, min_periods=w // 2).max() - 1, w),
        "mom63":  _z(C / C.shift(63) - 1, w),
    })


def classify(px: pd.DataFrame, w: int = LOOKBACK) -> pd.DataFrame:
    """Return per-bar state, heat percentile, trend flag and capitulation count."""
    C = px["close"]
    comp = components(px, w)

    heat = comp.mean(axis=1)
    heat_pct = heat.rolling(w, min_periods=w // 2).rank(pct=True)

    ma50 = C.rolling(50, min_periods=25).mean()
    ma200 = C.rolling(200, min_periods=100).mean()
    uptrend = ma50 > ma200

    # capitulation: 3+ of the 5 components in their own bottom decile
    low_count = (comp.rolling(w, min_periods=w // 2).rank(pct=True) <= 0.10).sum(axis=1)
    cap = low_count >= 3

    state = pd.Series("", index=C.index, dtype=object)
    state[uptrend & (heat_pct >= 0.70)] = "STRONG"
    state[uptrend & (heat_pct >= 0.35) & (heat_pct < 0.70)] = "STEADY"
    state[uptrend & (heat_pct < 0.35)] = "COOLING"
    state[~uptrend & (heat_pct >= 0.35)] = "TOPPING"
    state[~uptrend & (heat_pct < 0.35)] = "FALLING"
    state[cap] = "CAPITULATION"

    return pd.DataFrame({
        "state": state, "heat": heat_pct, "uptrend": uptrend,
        "capitulation_count": low_count,
    })


ACTIONS = {
    "CAPITULATION": ("BUY",     "statistically unusual low (t=+4.35). Ladder in over "
                                "3 tranches -- median signal is 7 weeks early."),
    "FALLING":      ("WATCH",   "weak but not extreme. No edge either way."),
    "COOLING":      ("HOLD",    "no measurable edge in this state."),
    "STEADY":       ("HOLD",    "no measurable edge in this state."),
    "STRONG":       ("HOLD",    "looks good, tested as nothing (t=-0.86). Do not "
                                "confuse strength with expected return."),
    "TOPPING":      ("REDUCE",  "extended into a broken trend -- worst state measured "
                                "(t=-3.82)."),
}


def latest(px: pd.DataFrame) -> dict:
    """Today's classification for one instrument."""
    cl = classify(px)
    row = cl.iloc[-1]
    if not row["state"]:
        return {"state": "INSUFFICIENT DATA", "action": "HOLD", "reason":
                "not enough history to classify"}
    action, reason = ACTIONS[row["state"]]
    prev = cl["state"].iloc[-2] if len(cl) > 1 else ""
    return {
        "state": row["state"],
        "action": action,
        "reason": reason,
        "heat_pct": None if pd.isna(row["heat"]) else round(float(row["heat"]), 3),
        "uptrend": bool(row["uptrend"]),
        "capitulation_count": int(row["capitulation_count"]),
        "changed_today": bool(prev and prev != row["state"]),
        "previous_state": prev or None,
    }
