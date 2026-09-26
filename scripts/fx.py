#!/usr/bin/env python3
"""
The pound/dollar exchange rate: how many US dollars one pound buys (e.g. 1.34).

Every US price is turned into pounds with the rate ON THAT DAY, so that
  * the value of every holding, gain and paper-test account is in real pounds,
    including the effect of the pound rising or falling against the dollar;
  * every purchase cost and sale proceed used for UK tax is converted at the
    rate on the day of the trade (what HMRC requires);
  * today's trade instructions use the latest rate available when the plan runs.

Sources, in order:
  1. Yahoo Finance, GBPUSD=X (daily, includes today's latest quote)
  2. Alpha Vantage FX_DAILY (uses the ALPHAVANTAGE_API_KEY secret; 1 of the 25 free daily calls)
  3. European Central Bank reference rates via frankfurter.app (weekdays)
  4. the copy saved by the last successful run, data/gbpusd.csv
If all three fail the plan stops rather than guess.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

CACHE = Path("data/gbpusd.csv")
START = "2022-06-01"
SOURCE = ""          # which source today's rate came from, for the plan


def _yahoo(start: str) -> pd.Series:
    import yfinance as yf
    for attempt in range(3):
        try:
            d = yf.download("GBPUSD=X", start=start, auto_adjust=True, progress=False)
            s = d["Close"]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            s = s.dropna()
            if len(s) > 100:
                return s
        except Exception:                                          # noqa: BLE001
            pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("Yahoo GBPUSD=X unavailable")


def _alpha(start: str) -> pd.Series:
    import io
    import os
    import urllib.request
    key = os.environ.get("ALPHAVANTAGE_API_KEY", "")
    if not key:
        raise RuntimeError("no Alpha Vantage key")
    url = ("https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=GBP&to_symbol=USD"
           f"&outputsize=full&datatype=csv&apikey={key}")
    with urllib.request.urlopen(url, timeout=60) as r:
        d = pd.read_csv(io.StringIO(r.read().decode()), index_col=0, parse_dates=True)
    s = d["close"].sort_index().loc[start:]
    if len(s) < 100:
        raise RuntimeError("Alpha Vantage rates too short")
    return s


def _ecb(start: str) -> pd.Series:
    import json
    import urllib.request
    url = f"https://api.frankfurter.app/{start}..?from=GBP&to=USD"
    with urllib.request.urlopen(url, timeout=30) as r:
        js = json.loads(r.read())
    s = pd.Series({pd.Timestamp(d): v["USD"] for d, v in js["rates"].items()}).sort_index()
    if len(s) < 100:
        raise RuntimeError("ECB rates too short")
    return s


def load(start: str = START) -> pd.Series:
    """Daily GBP/USD (dollars per pound), newest last. Saves a copy for next time."""
    global SOURCE
    old = pd.Series(dtype=float)
    if CACHE.exists():
        try:
            old = pd.read_csv(CACHE, index_col=0, parse_dates=True).iloc[:, 0].dropna()
        except Exception:                                          # noqa: BLE001
            pass
    for name, fn in (("Yahoo Finance", _yahoo), ("Alpha Vantage", _alpha), ("European Central Bank", _ecb)):
        try:
            s = fn(start)
            s.index = pd.DatetimeIndex(s.index).tz_localize(None).normalize()
            s = s[~s.index.duplicated(keep="last")].astype(float)
            s = s[(s > 0.8) & (s < 2.5)]                           # sanity: pound has stayed inside this
            if len(old):                                           # keep history the source no longer serves
                s = pd.concat([old[old.index < s.index[0]], s])
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            s.rename("usd_per_gbp").to_csv(CACHE, index_label="date", float_format="%.5f")
            SOURCE = name
            return s
        except Exception:                                          # noqa: BLE001
            continue
    if len(old) > 100:
        SOURCE = "saved copy — live sources unavailable today"
        return old
    raise RuntimeError("No pound/dollar exchange rate available from any source")


def on(index: pd.DatetimeIndex, rate: pd.Series) -> pd.Series:
    """The rate on each trading day of `index` (last known rate if the FX market had none)."""
    both = rate.index.union(index)
    r = rate.reindex(both).ffill().bfill()
    out = r.reindex(index)
    # the last trading day uses the very latest quote available now
    if len(index) and rate.index[-1] >= index[-1]:
        out.iloc[-1] = float(rate.iloc[-1])
    return out


def to_gbp(prices, rate_on_days: pd.Series):
    """US-dollar prices (Series or DataFrame on the same days) -> pounds."""
    if isinstance(prices, pd.DataFrame):
        return prices.div(rate_on_days, axis=0)
    return prices / rate_on_days
