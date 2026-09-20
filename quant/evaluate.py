"""
Signal-level evidence harness.

PURPOSE
-------
Take each individual signal from the established literature -- golden cross,
12-1 momentum, RSI, MACD, Donchian breakout and the rest -- and ask one question
of each, across a WIDE universe of stocks:

    When this signal fired, what happened next, and was it better than doing
    nothing over the same period?

METHODOLOGY, AND WHY IT IS BUILT THIS WAY
-----------------------------------------
1. PRIORS COME FROM OUTSIDE. Every signal tested here is one that published
   research already proposed. Nothing is invented by searching this data for
   patterns. The data's job is to CONFIRM OR REFUTE, never to suggest.

2. NON-OVERLAPPING SAMPLES. A naive test of 52-week forward returns on daily
   data reports thousands of observations from twenty years of history. They are
   almost entirely the same years counted repeatedly. Overlapping windows inflate
   apparent significance enormously, and it is the single most common way a
   backtest lies about its own confidence. Every t-statistic here is computed on
   strictly non-overlapping windows.

3. BREADTH BEATS DEPTH. A signal that works on 70% of a 500-stock universe is
   evidence. A signal that works spectacularly on three stocks is an anecdote.
   Results are aggregated across the universe and ranked by CONSISTENCY, not by
   the size of the best result.

4. THE SELECTION UNIVERSE AND THE TEST UNIVERSE MUST NOT OVERLAP. Signals chosen
   using a stock's history cannot then be honestly validated on that same stock.
   Hold your own positions out entirely.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import indicators as ind


# Signals drawn from published work. Each maps to (column, direction) where
# direction +1 means "high values are bullish" and -1 means the reverse.
SIGNAL_SPECS: dict[str, tuple[str, int, str]] = {
    "golden_cross":    ("golden_cross",       +1, "50/200 MA cross (Brock et al. 1992)"),
    "trend_filter":    ("trend_200",          +1, "Price vs 200d MA (Faber 2007)"),
    "momentum_12_1":   ("mom_12_1",           +1, "12-1 momentum (Jegadeesh-Titman 1993)"),
    "momentum_3m":     ("mom_63",             +1, "Quarterly momentum"),
    "macd_hist":       ("macd_hist",          +1, "MACD histogram (Appel 1979)"),
    "adx_strength":    ("adx",                +1, "Trend strength (Wilder 1978)"),
    "rsi_oversold":    ("rsi_14",             -1, "RSI mean reversion (Wilder 1978)"),
    "bollinger_low":   ("bb_pct",             -1, "Bollinger %B reversion (Bollinger 1980s)"),
    "price_zscore":    ("price_z_200",        -1, "Price stretch vs own history"),
    "from_52w_high":   ("pct_from_high_52w",  +1, "52-week high proximity (George-Hwang 2004)"),
    "short_reversal":  ("mom_21",             -1, "1-month reversal (Jegadeesh 1990)"),
    "low_volatility":  ("vol_20",             -1, "Low-vol anomaly (Baker et al. 2011)"),
    "vol_regime":      ("vol_regime",         -1, "Volatility regime shift"),
    "drawdown_depth":  ("drawdown",           -1, "Drawdown as entry (contrarian)"),
    "obv_trend":       ("obv_trend",          +1, "On-balance volume (Granville 1963)"),
}


def non_overlapping_forward(close: pd.Series, horizon: int) -> pd.DataFrame:
    """
    Forward returns sampled so that no two windows share a day.

    Taking every h-th bar is the cheap, correct fix for overlap. It throws away
    data, which is the point: the discarded rows were never independent evidence.
    """
    fwd = close.shift(-horizon) / close - 1.0
    idx = close.index[::horizon]
    return pd.DataFrame({"fwd": fwd.reindex(idx)}).dropna()


def evaluate_signal(signal: pd.Series,
                    close: pd.Series,
                    horizon: int,
                    quantile: float = 0.70) -> dict | None:
    """
    Edge of one signal at one horizon on one instrument.

    The signal fires when it sits in its top `quantile` of values observed SO FAR
    (expanding, never full-sample -- that would leak the future into the trigger).
    """
    rank = signal.expanding(min_periods=52).rank(pct=True)
    fired = rank >= quantile

    sample = non_overlapping_forward(close, horizon)
    fired_at = fired.reindex(sample.index).fillna(False)

    hit = sample["fwd"][fired_at]
    base = sample["fwd"]
    if len(hit) < 8 or len(base) < 12:
        return None

    edge = hit.mean() - base.mean()
    # Welch's t-test: does the fired subset differ from the unconditional sample?
    t_stat, p_val = stats.ttest_ind(hit, base, equal_var=False)

    return {
        "n_fired": int(len(hit)),
        "n_total": int(len(base)),
        "hit_rate": float((hit > 0).mean()),
        "base_hit_rate": float((base > 0).mean()),
        "mean_return": float(hit.mean()),
        "base_mean_return": float(base.mean()),
        "edge": float(edge),
        "t_stat": float(t_stat),
        "p_value": float(p_val),
    }


def evaluate_instrument(px: pd.DataFrame,
                        horizons: tuple[int, ...] = (4, 13, 26, 52),
                        bars_per_year: int = 52) -> pd.DataFrame:
    """Every signal, every horizon, for one instrument."""
    panel = ind.compute_all(px, bars_per_year=bars_per_year)
    close = px["close"]

    rows = []
    for name, (col, direction, source) in SIGNAL_SPECS.items():
        if col not in panel.columns:
            continue
        series = panel[col] * direction
        for h in horizons:
            r = evaluate_signal(series, close, h)
            if r:
                rows.append({"signal": name, "horizon": h, "source": source, **r})
    return pd.DataFrame(rows)


def aggregate_universe(per_instrument: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Pool results across the universe.

    `consistency` -- the share of instruments on which a signal showed a positive
    edge -- is the column that matters most. A signal with a huge mean edge driven
    by two outliers and a consistency of 0.45 is noise wearing a good suit.
    """
    frames = [df.assign(symbol=sym) for sym, df in per_instrument.items() if len(df)]
    if not frames:
        return pd.DataFrame()
    allr = pd.concat(frames, ignore_index=True)

    out = (allr.groupby(["signal", "horizon"])
                .agg(n_instruments=("edge", "size"),
                     mean_edge=("edge", "mean"),
                     median_edge=("edge", "median"),
                     consistency=("edge", lambda s: float((s > 0).mean())),
                     mean_hit_rate=("hit_rate", "mean"),
                     mean_base_hit=("base_hit_rate", "mean"),
                     mean_t=("t_stat", "mean"))
                .reset_index())

    # Cross-sectional t-statistic: is the AVERAGE edge across instruments
    # distinguishable from zero? This is the number that decides inclusion.
    tvals = (allr.groupby(["signal", "horizon"])["edge"]
                 .apply(lambda s: stats.ttest_1samp(s, 0.0)[0] if len(s) > 2 else np.nan))
    out = out.merge(tvals.rename("cross_sectional_t").reset_index(), on=["signal", "horizon"])
    out["source"] = out["signal"].map(lambda s: SIGNAL_SPECS[s][2])
    return out.sort_values("cross_sectional_t", ascending=False)


def verdict(row: pd.Series, min_consistency: float = 0.60,
            min_t: float = 2.0) -> str:
    """
    Blunt include/exclude call.

    Thresholds are set BEFORE seeing results and are deliberately strict. A t of
    2.0 is a low bar for a single hypothesis and a high one after testing fifteen
    signals at four horizons -- sixty tests means roughly three false positives at
    p<0.05 by chance alone, so treat marginal passes with suspicion.
    """
    if pd.isna(row["cross_sectional_t"]):
        return "INSUFFICIENT DATA"
    if row["consistency"] >= min_consistency and row["cross_sectional_t"] >= min_t:
        return "KEEP"
    if row["consistency"] <= (1 - min_consistency) and row["cross_sectional_t"] <= -min_t:
        return "KEEP (INVERTED)"
    return "DROP"
