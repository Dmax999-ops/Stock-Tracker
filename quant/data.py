"""
Data adapters.

The engine only ever needs a DataFrame indexed by date with columns
open / high / low / close / volume. Where that comes from is interchangeable,
which is deliberate: data feeds change, the model should not have to.

ADJUSTED PRICES MATTER. Use split- and dividend-adjusted closes. Raw closes make
every stock that has ever split look like it crashed, and every signal built on
them is nonsense.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

REQUIRED = ["open", "high", "low", "close", "volume"]


def _finalise(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=str.lower)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}. Got {list(df.columns)}")
    df = df[REQUIRED].apply(pd.to_numeric, errors="coerce")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df.dropna(subset=["close"])


def from_csv(path: str | Path, date_column: str = "Date") -> pd.DataFrame:
    """
    Read a CSV exported from a broker, Yahoo, Stooq or similar.

    Expected headers (case-insensitive): Date, Open, High, Low, Close, Volume.
    If an 'Adj Close' column is present it replaces Close, which is what you want.
    """
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}
    date_col = cols.get(date_column.lower(), df.columns[0])
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", utc=False)
    df = df.dropna(subset=[date_col]).set_index(date_col)
    df.index.name = "date"

    if "adj close" in cols:
        df["Close"] = df[cols["adj close"]]
    return _finalise(df)


def from_yfinance(ticker: str, period: str = "max", interval: str = "1d") -> pd.DataFrame:
    """
    Convenience loader for a machine with internet access.

        pip install yfinance

    LSE tickers take a .L suffix -- SHEL.L, HSBA.L, AZN.L.
    """
    import yfinance as yf  # imported lazily so the package works without it

    df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for {ticker!r}.")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"
    return _finalise(df)


def from_alpha_vantage_daily(payload: dict) -> pd.DataFrame:
    """
    Parse TIME_SERIES_DAILY_ADJUSTED output from the Alpha Vantage MCP connector.

    Uses the adjusted close and back-adjusts open/high/low by the same factor so
    the whole bar stays internally consistent.
    """
    key = next((k for k in payload if "Time Series" in k), None)
    if key is None:
        raise ValueError(f"Unexpected payload shape. Top-level keys: {list(payload)[:5]}")

    rows = []
    for date, v in payload[key].items():
        close = float(v["4. close"])
        adj = float(v.get("5. adjusted close", close))
        f = adj / close if close else 1.0
        rows.append({
            "date": pd.Timestamp(date),
            "open": float(v["1. open"]) * f,
            "high": float(v["2. high"]) * f,
            "low": float(v["3. low"]) * f,
            "close": adj,
            "volume": float(v.get("6. volume", v.get("5. volume", 0))),
        })
    return _finalise(pd.DataFrame(rows).set_index("date"))


def from_av_csv(csv_text: str) -> pd.DataFrame:
    """
    Parse any Alpha Vantage CSV time series (daily, weekly-adjusted, monthly-adjusted).

    Where an 'adjusted close' column exists, the whole bar is scaled by
    adjusted/raw so open, high and low stay consistent with the adjusted close.
    """
    df = pd.read_csv(io.StringIO(csv_text))
    df = df.rename(columns=lambda c: c.strip().lower())
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()

    if "adjusted close" in df.columns:
        factor = df["adjusted close"] / df["close"]
        for col in ["open", "high", "low"]:
            df[col] = df[col] * factor
        df["close"] = df["adjusted close"]
    df.index.name = "date"
    return _finalise(df)


def adjust_daily_from_periodic(daily_raw: pd.DataFrame,
                               periodic_adj: pd.DataFrame) -> pd.DataFrame:
    """
    Reconstruct an adjusted DAILY series from raw daily bars plus a lower-frequency
    adjusted series.

    WHY THIS EXISTS: Alpha Vantage paywalls TIME_SERIES_DAILY_ADJUSTED, and its
    DIVIDENDS endpoint returns nothing for UK (.LON) listings. But the weekly and
    monthly adjusted endpoints are free and DO carry UK dividends. The cumulative
    adjustment factor is a step function that only moves on ex-dividend and split
    dates, so sampling it weekly and carrying it across the intervening days
    reproduces the daily adjusted series almost exactly.

    RESIDUAL ERROR: the factor step lands on the period boundary rather than the
    exact ex-dividend day, so bars between the true ex-date and the period end
    carry a stale factor -- at most a few days, of a step typically under 1%.
    Immaterial for a multi-month holding horizon; it would NOT be acceptable for
    a strategy trading around ex-dividend dates.

    `periodic_adj` must be the UNADJUSTED close alongside the adjusted close, i.e.
    the raw frame straight from the API before from_av_csv() rescales it.
    """
    factor = (periodic_adj["adjusted close"] / periodic_adj["close"]).sort_index()
    # Carry each period's factor backward across the days it covers, then forward-fill
    # the tail. bfill first because a factor dated at period END applies to the days
    # leading up to it.
    daily_factor = factor.reindex(daily_raw.index.union(factor.index)).bfill().ffill()
    daily_factor = daily_factor.reindex(daily_raw.index)

    out = daily_raw.copy()
    for col in ["open", "high", "low", "close"]:
        out[col] = out[col] * daily_factor
    return out


def clean_bad_ticks(df: pd.DataFrame, max_intraday_range: float = 0.25) -> pd.DataFrame:
    """
    Repair implausible highs and lows.

    Free feeds carry bad prints: the SHEL.LON daily series shows a low of 2643
    against a close of 3147 on 14 July 2026 -- a 16% intraday collapse that did not
    happen. Left alone these corrupt ATR, Donchian channels, stochastics and
    52-week ranges, all of which read the extremes rather than the close.

    A bar whose range exceeds `max_intraday_range` of its close has its high and
    low clipped back to the open/close envelope. The close itself is never altered
    -- closes are the reliable field, and inventing one would be worse than a wide bar.
    """
    out = df.copy()
    body_hi = out[["open", "close"]].max(axis=1)
    body_lo = out[["open", "close"]].min(axis=1)
    suspect = (out["high"] - out["low"]) / out["close"] > max_intraday_range

    out.loc[suspect, "high"] = body_hi[suspect]
    out.loc[suspect, "low"] = body_lo[suspect]
    out.attrs["bad_ticks_repaired"] = int(suspect.sum())
    return out


def align(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Restrict a set of instruments to their common trading calendar."""
    if not frames:
        return frames
    common = None
    for df in frames.values():
        common = df.index if common is None else common.intersection(df.index)
    return {k: df.loc[common] for k, df in frames.items()}
