"""
Horizontal support and resistance, found mechanically.

WHY HORIZONTAL LEVELS DESERVE A BETTER TEST THAN TRENDLINES
-----------------------------------------------------------
A diagonal trendline has two free parameters, slope and anchor, so with a
thousand bars you can nearly always find one that "works". A horizontal level
has ONE: the price. That is a far smaller space to search, which means far less
room to fool yourself.

It also has a mechanism behind it that a diagonal does not. A price where a lot
of business was done is a price people remember: buyers who missed it wait for
it, holders who bought there add or get out flat, stop orders pile just beneath.
None of that is true of a sloping line, which sits at a different price every day
and corresponds to no transaction anyone actually made.

So this module looks for prices that have repeatedly turned the market, and it
does so using only information that existed at the time.

THE LOOK-AHEAD TRAP, WHICH IS EASY TO FALL INTO HERE
----------------------------------------------------
A swing low is only a swing low once you have seen the bars AFTER it. A pivot at
bar t is not knowable until bar t + LOOKAHEAD. Every level built here is assembled
from pivots that were already confirmed at the moment of the signal -- otherwise
the test would be reading tomorrow's chart, which is precisely how support looks
so convincing in hindsight.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LOOKAHEAD = 10        # bars either side that make a swing a swing
MEMORY = 20           # how many recent confirmed pivots stay in mind
MIN_TOUCHES = 3       # a level means nothing until three separate turns
TOL_ATR = 0.75        # how close counts as "at" the level


def _pivots(s: pd.Series, n: int, kind: str) -> np.ndarray:
    """Index positions of confirmed swing highs or lows."""
    w = 2 * n + 1
    if kind == "low":
        hit = s == s.rolling(w, center=True).min()
    else:
        hit = s == s.rolling(w, center=True).max()
    return np.flatnonzero(hit.fillna(False).to_numpy())


def level_events(df: pd.DataFrame, atr: pd.Series, *, kind: str = "support",
                 lookahead: int = LOOKAHEAD, memory: int = MEMORY,
                 min_touches: int = MIN_TOUCHES,
                 tol_atr: float = TOL_ATR) -> tuple[pd.Series, pd.Series]:
    """
    Returns two boolean series:

      tested  the bar traded into a level confirmed by at least `min_touches`
              earlier pivots, and closed back on the right side of it
      broken  the bar closed decisively through such a level

    For support, "right side" means closing above it; for resistance, below.
    """
    o, h, l, c = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    a = atr.to_numpy(float)
    n = len(df)

    piv = _pivots(df["low" if kind == "support" else "high"], lookahead,
                  "low" if kind == "support" else "high")
    piv_price = (l if kind == "support" else h)[piv]
    # a pivot at bar p is only knowable at p + lookahead
    piv_known = piv + lookahead

    tested = np.zeros(n, bool)
    broken = np.zeros(n, bool)

    j = 0                      # how many pivots are known so far
    recent: list[float] = []
    for t in range(n):
        while j < len(piv) and piv_known[j] <= t:
            recent.append(float(piv_price[j]))
            if len(recent) > memory:
                recent.pop(0)
            j += 1
        if len(recent) < min_touches or not np.isfinite(a[t]) or a[t] <= 0:
            continue

        arr = np.asarray(recent)
        tol = tol_atr * a[t]
        # Only one cluster matters: the one at the price we are standing on.
        # "Has this price turned the market before?" -- so count the remembered
        # pivots within a tolerance band of TODAY, and take their median as the
        # level. The earlier version searched every cluster on the chart, which
        # was both slower and a different question.
        near = np.abs(arr - c[t]) <= 2 * tol
        if near.sum() < min_touches:
            continue
        best_level = float(np.median(arr[near]))
        if not np.isfinite(best_level):
            continue

        if kind == "support":
            touched = l[t] <= best_level + tol and c[t] > best_level
            through = c[t] < best_level - tol
        else:
            touched = h[t] >= best_level - tol and c[t] < best_level
            through = c[t] > best_level + tol
        tested[t] = touched
        broken[t] = through

    idx = df.index
    return pd.Series(tested, index=idx), pd.Series(broken, index=idx)
