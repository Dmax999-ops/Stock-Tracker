"""
The technical canon, made mechanical.

Everything a chartist points at, expressed as a rule a computer can apply the
same way every time, using only information that existed on the signal bar.

    SLOPING LINES      up-trend support, down-trend resistance, and the breaks
                       of both. Two confirmed pivots define the line; a third
                       touch confirms it before it may fire.
    MOVING AVERAGES    golden and death crosses, reclaims, ribbon alignment,
                       and the 50-day as dynamic support.
    DIVERGENCE         price makes a lower low while momentum makes a higher
                       low, and the bearish mirror.
    STRUCTURE          the turn from lower-lows to higher-lows, double bottoms
                       and double tops.
    OSCILLATORS        RSI reclaiming 30, losing 70, stochastic and MACD crosses,
                       ADX confirming a trend has started.
    VOLATILITY         Bollinger band reclaim, inside-bar and narrow-range breaks.
    VOLUME             climax reversal, and on-balance-volume divergence.
    CANDLES            engulfing, hammer, shooting star.

THE ONE RULE THROUGHOUT
-----------------------
A swing point is not knowable until the bars after it have printed. Every pivot
used here is gated by its confirmation bar, never its own bar. Skip that and
support looks miraculous, because you drew it after watching the bounce.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LOOKAHEAD = 10
MEMORY = 20
MIN_TOUCHES = 3
TOL_ATR = 0.75


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d).clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def macd(c: pd.Series) -> tuple[pd.Series, pd.Series]:
    line = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    return line, line.ewm(span=9, adjust=False).mean()


def stoch(df: pd.DataFrame, n: int = 14) -> tuple[pd.Series, pd.Series]:
    ll = df["low"].rolling(n).min()
    hh = df["high"].rolling(n).max()
    k = 100 * (df["close"] - ll) / (hh - ll).replace(0, np.nan)
    return k, k.rolling(3).mean()


def adx(df: pd.DataFrame, n: int = 14) -> tuple[pd.Series, pd.Series, pd.Series]:
    h, l, c = df["high"], df["low"], df["close"]
    up, dn = h.diff(), -l.diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()],
                   axis=1).max(axis=1)
    atr_ = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pd.Series(plus, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr_
    mdi = 100 * pd.Series(minus, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr_
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean(), pdi, mdi


def obv(df: pd.DataFrame) -> pd.Series:
    sign = np.sign(df["close"].diff()).fillna(0)
    return (sign * df["volume"]).cumsum()


def pivot_idx(s: pd.Series, n: int, kind: str) -> np.ndarray:
    w = 2 * n + 1
    hit = (s == s.rolling(w, center=True).min()) if kind == "low" else \
          (s == s.rolling(w, center=True).max())
    return np.flatnonzero(hit.fillna(False).to_numpy())


# ---------------------------------------------------------------------------
# Sloping trendlines
# ---------------------------------------------------------------------------

def trendline_events(df: pd.DataFrame, atr: pd.Series, *, kind: str = "up",
                     lookahead: int = LOOKAHEAD, memory: int = MEMORY,
                     min_touches: int = MIN_TOUCHES,
                     tol_atr: float = TOL_ATR) -> tuple[pd.Series, pd.Series]:
    """
    An up-trendline is drawn through the two most recent confirmed swing LOWS
    that are rising. It only counts once a third pivot has also touched it --
    two points define any line, so two points prove nothing.

    Returns (bounce, break_):
      bounce  price traded down to the line and closed back above it
      break_  price closed a full tolerance below the line
    (mirrored for a down-trendline drawn across falling highs)
    """
    up = kind == "up"
    src = df["low"] if up else df["high"]
    c = df["close"].to_numpy(float)
    lo = df["low"].to_numpy(float)
    hi = df["high"].to_numpy(float)
    a = atr.to_numpy(float)
    n = len(df)

    piv = pivot_idx(src, lookahead, "low" if up else "high")
    piv_px = src.to_numpy(float)[piv]
    known = piv + lookahead

    bounce = np.zeros(n, bool)
    brk = np.zeros(n, bool)

    j = 0
    xs: list[int] = []
    ys: list[float] = []
    for t in range(n):
        while j < len(piv) and known[j] <= t:
            xs.append(int(piv[j])); ys.append(float(piv_px[j]))
            if len(xs) > memory:
                xs.pop(0); ys.pop(0)
            j += 1
        if len(xs) < min_touches or not np.isfinite(a[t]) or a[t] <= 0:
            continue

        x2, y2 = xs[-1], ys[-1]
        x1, y1 = xs[-2], ys[-2]
        if x2 == x1:
            continue
        slope = (y2 - y1) / (x2 - x1)
        # an up-trendline must rise, a down-trendline must fall
        if (up and slope <= 0) or (not up and slope >= 0):
            continue

        line = lambda x: y2 + slope * (x - x2)            # noqa: E731
        tol = tol_atr * a[t]
        # a third pivot has to sit on the line for it to mean anything
        touches = sum(1 for xi, yi in zip(xs, ys) if abs(yi - line(xi)) <= tol)
        if touches < min_touches:
            continue

        lv = line(t)
        if not np.isfinite(lv) or lv <= 0:
            continue
        if up:
            bounce[t] = lo[t] <= lv + tol and c[t] > lv
            brk[t] = c[t] < lv - tol
        else:
            bounce[t] = hi[t] >= lv - tol and c[t] < lv      # rejection
            brk[t] = c[t] > lv + tol                         # breakout
    idx = df.index
    return pd.Series(bounce, index=idx), pd.Series(brk, index=idx)


# ---------------------------------------------------------------------------
# Divergence
# ---------------------------------------------------------------------------

def divergence(df: pd.DataFrame, osc: pd.Series, *, bullish: bool = True,
               lookahead: int = LOOKAHEAD, max_gap: int = 60) -> pd.Series:
    """
    Bullish: price prints a confirmed lower low while the oscillator prints a
    higher low against the previous swing. Bearish is the mirror. The signal
    fires on the bar the second pivot is CONFIRMED, not on the pivot itself.
    """
    src = df["low"] if bullish else df["high"]
    piv = pivot_idx(src, lookahead, "low" if bullish else "high")
    p = src.to_numpy(float)
    o = osc.to_numpy(float)
    out = np.zeros(len(df), bool)
    for i in range(1, len(piv)):
        a_, b_ = piv[i - 1], piv[i]
        if b_ - a_ > max_gap or b_ + lookahead >= len(df):
            continue
        if not (np.isfinite(o[a_]) and np.isfinite(o[b_])):
            continue
        if bullish and p[b_] < p[a_] and o[b_] > o[a_]:
            out[b_ + lookahead] = True
        if not bullish and p[b_] > p[a_] and o[b_] < o[a_]:
            out[b_ + lookahead] = True
    return pd.Series(out, index=df.index)


def double_pattern(df: pd.DataFrame, atr: pd.Series, *, bottom: bool = True,
                   lookahead: int = LOOKAHEAD, tol_atr: float = 1.0,
                   max_gap: int = 90) -> pd.Series:
    """Two swing points at the same price within a window: double bottom or top."""
    src = df["low"] if bottom else df["high"]
    piv = pivot_idx(src, lookahead, "low" if bottom else "high")
    p = src.to_numpy(float)
    a = atr.to_numpy(float)
    out = np.zeros(len(df), bool)
    for i in range(1, len(piv)):
        a_, b_ = piv[i - 1], piv[i]
        k = b_ + lookahead
        if b_ - a_ > max_gap or k >= len(df) or not np.isfinite(a[k]):
            continue
        if abs(p[b_] - p[a_]) <= tol_atr * a[k]:
            out[k] = True
    return pd.Series(out, index=df.index)


def structure_turn(df: pd.DataFrame, *, up: bool = True,
                   lookahead: int = LOOKAHEAD) -> pd.Series:
    """
    The moment market structure flips: after a run of lower highs and lower
    lows, a higher high and a higher low both appear. The classic 'trend change'
    a discretionary trader marks on the chart.
    """
    lows = pivot_idx(df["low"], lookahead, "low")
    highs = pivot_idx(df["high"], lookahead, "high")
    l, h = df["low"].to_numpy(float), df["high"].to_numpy(float)
    out = np.zeros(len(df), bool)
    for i in range(2, len(lows)):
        b_, a_ = lows[i], lows[i - 1]
        k = b_ + lookahead
        if k >= len(df):
            continue
        prior_h = highs[highs < b_]
        if len(prior_h) < 2:
            continue
        h2, h1 = prior_h[-1], prior_h[-2]
        if up and l[b_] > l[a_] and h[h2] > h[h1]:
            out[k] = True
        if not up and l[b_] < l[a_] and h[h2] < h[h1]:
            out[k] = True
    return pd.Series(out, index=df.index)
