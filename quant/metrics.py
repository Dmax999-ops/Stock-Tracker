"""Performance and risk statistics. Deliberately unflattering."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def cagr(equity: pd.Series) -> float:
    if len(equity) < 2:
        return np.nan
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    if years <= 0 or equity.iloc[0] <= 0:
        return np.nan
    return (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1


def annual_vol(returns: pd.Series, bars_per_year: int = TRADING_DAYS) -> float:
    return returns.std(ddof=0) * np.sqrt(bars_per_year)


def sharpe(returns: pd.Series, rf: float = 0.0, bars_per_year: int = TRADING_DAYS) -> float:
    excess = returns - rf / bars_per_year
    sd = excess.std(ddof=0)
    return np.nan if sd == 0 else excess.mean() / sd * np.sqrt(bars_per_year)


def sortino(returns: pd.Series, rf: float = 0.0, bars_per_year: int = TRADING_DAYS) -> float:
    excess = returns - rf / bars_per_year
    downside = excess[excess < 0].std(ddof=0)
    return np.nan if not downside else excess.mean() / downside * np.sqrt(bars_per_year)


def max_drawdown(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1).min())


def calmar(equity: pd.Series) -> float:
    mdd = max_drawdown(equity)
    return np.nan if mdd == 0 else cagr(equity) / abs(mdd)


def time_underwater(equity: pd.Series) -> float:
    """Fraction of days spent below a previous peak. The number that tests patience."""
    return float((equity < equity.cummax()).mean())


def summary(equity: pd.Series, returns: pd.Series, label: str = "",
            bars_per_year: int = TRADING_DAYS) -> dict:
    return {
        "label": label,
        "cagr": cagr(equity),
        "vol": annual_vol(returns, bars_per_year),
        "sharpe": sharpe(returns, 0.0, bars_per_year),
        "sortino": sortino(returns, 0.0, bars_per_year),
        "max_drawdown": max_drawdown(equity),
        "calmar": calmar(equity),
        "time_underwater": time_underwater(equity),
        "total_return": float(equity.iloc[-1] / equity.iloc[0] - 1),
        "days": int(len(equity)),
    }


# ---------------------------------------------------------------------------
# Per-signal honesty test
# ---------------------------------------------------------------------------

def forward_returns(close: pd.Series, horizons=(21, 63, 126, 252)) -> pd.DataFrame:
    """Realised forward return over each horizon. Used only for EVALUATION."""
    return pd.DataFrame({f"fwd_{h}": close.shift(-h) / close - 1.0 for h in horizons})


def signal_hit_rate(signal: pd.Series,
                    close: pd.Series,
                    horizons=(21, 63, 126, 252),
                    threshold: float = 0.0) -> pd.DataFrame:
    """
    The honest question: when this signal fired positive, what happened next --
    and was it better than doing nothing?

    'edge' is the part that matters. A 70% hit rate in a market that rose 70% of
    the time is not a signal, it is a bull market.
    """
    fwd = forward_returns(close, horizons)
    fired = signal > threshold
    rows = []
    for h in horizons:
        col = f"fwd_{h}"
        sub = fwd[col][fired].dropna()
        base = fwd[col].dropna()
        if len(sub) < 30:
            continue
        rows.append({
            "horizon_days": h,
            "n_observations": int(len(sub)),
            "hit_rate": float((sub > 0).mean()),
            "baseline_hit_rate": float((base > 0).mean()),
            "mean_return": float(sub.mean()),
            "baseline_mean_return": float(base.mean()),
            "edge": float(sub.mean() - base.mean()),
            "median_return": float(sub.median()),
            "worst": float(sub.min()),
            "best": float(sub.max()),
        })
    return pd.DataFrame(rows)


def deflated_note(n_strategies_tried: int, best_sharpe: float) -> str:
    """
    Blunt multiple-testing warning. Try enough rules and one looks brilliant by
    luck alone; the expected maximum Sharpe of N pure-noise strategies grows with N.
    """
    if n_strategies_tried <= 1:
        return "Single configuration tested -- no multiple-testing inflation."
    expected_max = np.sqrt(2 * np.log(max(n_strategies_tried, 2)))
    return (
        f"{n_strategies_tried} configurations tested. Pure noise would be expected to "
        f"produce a best t-statistic near {expected_max:.2f} by chance alone. "
        f"Observed best Sharpe {best_sharpe:.2f} should be discounted accordingly."
    )
