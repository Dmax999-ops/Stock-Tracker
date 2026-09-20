"""
Technical indicator library.

Every function takes a DataFrame with columns open/high/low/close/volume indexed
by date (ascending) and returns a Series or DataFrame aligned to that index.

CRITICAL CONVENTION: every indicator here is computed using data up to and
including the bar at index t. Nothing peeks forward. Any strategy that acts on
indicator[t] must trade at t+1's open or later -- the backtester enforces this.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------

def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window, min_periods=window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False, min_periods=span).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Moving Average Convergence Divergence. Returns macd / signal / histogram."""
    line = ema(close, fast) - ema(close, slow)
    sig = line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return pd.DataFrame({"macd": line, "macd_signal": sig, "macd_hist": line - sig})


def golden_cross(close: pd.Series, fast: int = 50, slow: int = 200) -> pd.Series:
    """+1 when fast MA above slow MA (golden), -1 when below (death), else NaN."""
    f, s = sma(close, fast), sma(close, slow)
    out = np.where(f > s, 1.0, np.where(f < s, -1.0, np.nan))
    return pd.Series(out, index=close.index).where(s.notna())


def trend_filter(close: pd.Series, window: int = 200) -> pd.Series:
    """Faber-style filter: price relative to its long moving average, as a ratio."""
    return close / sma(close, window) - 1.0


def adx(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Average Directional Index -- trend STRENGTH (not direction). Wilder smoothing."""
    high, low, close = df["high"], df["low"], df["close"]

    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)

    tr = _true_range(df)
    # Wilder's smoothing == EMA with alpha = 1/window
    atr_w = tr.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(
        alpha=1 / window, adjust=False, min_periods=window).mean() / atr_w
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(
        alpha=1 / window, adjust=False, min_periods=window).mean() / atr_w

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_val = dx.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    return pd.DataFrame({"adx": adx_val, "plus_di": plus_di, "minus_di": minus_di})


def donchian(df: pd.DataFrame, window: int = 55) -> pd.DataFrame:
    """Turtle-style breakout channel. Uses only bars strictly BEFORE t."""
    upper = df["high"].shift(1).rolling(window, min_periods=window).max()
    lower = df["low"].shift(1).rolling(window, min_periods=window).min()
    return pd.DataFrame({"dc_upper": upper, "dc_lower": lower,
                         "dc_mid": (upper + lower) / 2})


# ---------------------------------------------------------------------------
# Momentum
# ---------------------------------------------------------------------------

def momentum_12_1(close: pd.Series) -> pd.Series:
    """
    Classic Jegadeesh-Titman cross-sectional momentum: the trailing 12-month
    return EXCLUDING the most recent month, which is skipped because short-term
    reversal contaminates it. The most robust single equity anomaly on record.
    """
    return close.shift(21) / close.shift(252) - 1.0


def momentum(close: pd.Series, window: int) -> pd.Series:
    return close / close.shift(window) - 1.0


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Wilder's Relative Strength Index."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    # all-gain window -> RSI 100
    return out.where(avg_loss != 0, 100.0).where(avg_gain.notna())


def stochastic(df: pd.DataFrame, window: int = 14, smooth: int = 3) -> pd.DataFrame:
    low_n = df["low"].rolling(window, min_periods=window).min()
    high_n = df["high"].rolling(window, min_periods=window).max()
    k = 100 * (df["close"] - low_n) / (high_n - low_n).replace(0, np.nan)
    return pd.DataFrame({"stoch_k": k, "stoch_d": k.rolling(smooth, min_periods=smooth).mean()})


# ---------------------------------------------------------------------------
# Mean reversion / stretch
# ---------------------------------------------------------------------------

def bollinger(close: pd.Series, window: int = 20, n_std: float = 2.0) -> pd.DataFrame:
    mid = sma(close, window)
    sd = close.rolling(window, min_periods=window).std(ddof=0)
    upper, lower = mid + n_std * sd, mid - n_std * sd
    pct_b = (close - lower) / (upper - lower).replace(0, np.nan)
    return pd.DataFrame({"bb_mid": mid, "bb_upper": upper, "bb_lower": lower,
                         "bb_pct": pct_b, "bb_width": (upper - lower) / mid})


def price_zscore(close: pd.Series, window: int = 200) -> pd.Series:
    """How stretched price is versus its own recent history, in standard deviations."""
    mean = close.rolling(window, min_periods=window).mean()
    sd = close.rolling(window, min_periods=window).std(ddof=0)
    return (close - mean) / sd.replace(0, np.nan)


def pct_from_high(close: pd.Series, window: int = 252) -> pd.Series:
    """Distance below the rolling 52-week high (negative = below)."""
    return close / close.rolling(window, min_periods=window).max() - 1.0


def pct_from_low(close: pd.Series, window: int = 252) -> pd.Series:
    return close / close.rolling(window, min_periods=window).min() - 1.0


# ---------------------------------------------------------------------------
# Volatility & risk
# ---------------------------------------------------------------------------

def _true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range -- the unit of position sizing and stop placement."""
    return _true_range(df).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


def realised_vol(close: pd.Series, window: int = 20,
                 bars_per_year: int = TRADING_DAYS) -> pd.Series:
    """Annualised realised volatility from log returns."""
    r = np.log(close / close.shift(1))
    return r.rolling(window, min_periods=window).std(ddof=0) * np.sqrt(bars_per_year)


def vol_regime(close: pd.Series, short: int = 20, long: int = 252) -> pd.Series:
    """Short-run vol relative to its own long-run level. >1 = stressed."""
    return realised_vol(close, short) / realised_vol(close, long)


def drawdown(close: pd.Series) -> pd.Series:
    return close / close.cummax() - 1.0


def ulcer_index(close: pd.Series, window: int = 252) -> pd.Series:
    """Depth-and-duration measure of pain. Penalises long deep drawdowns."""
    dd = 100 * (close / close.rolling(window, min_periods=window).max() - 1.0)
    return np.sqrt((dd ** 2).rolling(window, min_periods=window).mean())


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------

def obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume -- cumulative volume signed by daily direction."""
    direction = np.sign(df["close"].diff()).fillna(0.0)
    return (direction * df["volume"]).cumsum()


def volume_ratio(df: pd.DataFrame, window: int = 50) -> pd.Series:
    """Today's volume against its recent average. Confirmation filter."""
    return df["volume"] / df["volume"].rolling(window, min_periods=window).mean()


# ---------------------------------------------------------------------------
# Relative strength
# ---------------------------------------------------------------------------

def relative_strength(close: pd.Series, benchmark: pd.Series, window: int = 126) -> pd.Series:
    """Excess return versus a benchmark over the window. The 'is it just the market?' test."""
    aligned = benchmark.reindex(close.index).ffill()
    return (close / close.shift(window)) - (aligned / aligned.shift(window))


def rolling_beta(close: pd.Series, benchmark: pd.Series, window: int = 252) -> pd.Series:
    r = close.pct_change()
    rb = benchmark.reindex(close.index).ffill().pct_change()
    cov = r.rolling(window, min_periods=window).cov(rb)
    var = rb.rolling(window, min_periods=window).var(ddof=0)
    return cov / var.replace(0, np.nan)


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

def periods(bars_per_year: int = TRADING_DAYS) -> dict[str, int]:
    """
    Window lengths scaled to the bar frequency.

    A "200-day moving average" is really a ten-month trend filter. On weekly bars
    that is 40 weeks, not 200 -- the classic 40-week MA chartists have used for
    decades. Scaling by frequency keeps every indicator measuring the same span of
    calendar time whatever bars it is fed.
    """
    y = bars_per_year
    return {
        "fast_ma": max(2, round(y * 50 / 252)),
        "slow_ma": max(3, round(y * 200 / 252)),
        "year": y,
        "half_year": max(3, round(y / 2)),
        "quarter": max(2, round(y / 4)),
        "month": max(2, round(y / 12)),
        "rsi": 14 if y <= 60 else 14,       # 14 periods is standard at any frequency
        "atr": 14,
        "bollinger": 20 if y > 60 else 10,
        "stoch": 14,
    }


def compute_all(df: pd.DataFrame,
                benchmark: pd.Series | None = None,
                bars_per_year: int = TRADING_DAYS) -> pd.DataFrame:
    """
    Compute the full indicator panel for one instrument.

    `bars_per_year` adapts every window to the data's frequency: 252 for daily
    bars, 52 for weekly, 12 for monthly.
    """
    p = periods(bars_per_year)
    close = df["close"]
    out = pd.DataFrame(index=df.index)

    out["sma_fast"] = sma(close, p["fast_ma"])
    out["sma_slow"] = sma(close, p["slow_ma"])
    out["golden_cross"] = golden_cross(close, p["fast_ma"], p["slow_ma"])
    out["trend_200"] = trend_filter(close, p["slow_ma"])
    out = out.join(macd(close))
    out = out.join(adx(df, p["atr"]))
    out = out.join(donchian(df, max(3, round(p["quarter"] * 55 / 63))))

    # 12-1 momentum: trailing year, skipping the most recent month
    out["mom_12_1"] = close.shift(p["month"]) / close.shift(p["year"]) - 1.0
    out["mom_63"] = momentum(close, p["quarter"])
    out["mom_21"] = momentum(close, p["month"])
    out["rsi_14"] = rsi(close, p["rsi"])
    out = out.join(stochastic(df, p["stoch"]))

    out = out.join(bollinger(close, p["bollinger"]))
    out["price_z_200"] = price_zscore(close, p["slow_ma"])
    out["pct_from_high_52w"] = pct_from_high(close, p["year"])
    out["pct_from_low_52w"] = pct_from_low(close, p["year"])

    out["atr_14"] = atr(df, p["atr"])
    out["atr_pct"] = out["atr_14"] / close
    out["vol_20"] = realised_vol(close, p["month"], bars_per_year)
    out["vol_252"] = realised_vol(close, p["year"], bars_per_year)
    out["vol_regime"] = (out["vol_20"] / out["vol_252"])
    out["drawdown"] = drawdown(close)
    out["ulcer_252"] = ulcer_index(close, p["year"])

    out["obv"] = obv(df)
    out["obv_trend"] = out["obv"].diff(p["month"])
    out["volume_ratio_50"] = volume_ratio(df, p["fast_ma"])

    if benchmark is not None:
        out["rel_strength_126"] = relative_strength(close, benchmark, p["half_year"])
        out["beta_252"] = rolling_beta(close, benchmark, p["year"])

    return out
