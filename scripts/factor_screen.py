#!/usr/bin/env python3
"""
WHAT, IF ANYTHING, PREDICTS WHICH S&P 500 STOCKS DO BEST?

WHY THIS EXISTS
---------------
The year-by-year backtest of the daily plan (docs/BACKTEST.md) answered the
question it was built for, and the answer was no. The plan's stock score --
12-month momentum per unit of volatility -- had NO predictive power across
S&P 500 stocks from 1997 to 2026: the top tenth by score went on to make
+11.9% a year, the bottom tenth +12.8%, the average stock +13.0%. Rank
correlation +0.002, t = +0.5. The measuring instrument itself was checked:
on random prices it found nothing (t = +0.9), on prices with a planted
momentum effect it found it at once (t = +17.9). So the zero is real.

Rather than guess the next score, this tests ten candidate scores side by
side, on the same stocks, the same dates and the same rules, and reports
which -- if any -- actually told you in advance which stocks would do best.

THE CANDIDATES (all computed only from prices known on the day)
---------------------------------------------------------------
    mom_12_1_riskadj   the current plan's score
    mom_12_1           12-month return, skipping the last month (classic momentum)
    mom_6_1            6-month version
    mom_3              last 3 months
    reversal_1m        last month's LOSERS (short-term reversal)
    near_52w_high      price / 12-month high (stocks near their highs)
    low_vol            the CALMEST stocks (low volatility anomaly)
    trend_200          % above the 200-day average
    smooth_mom         share of the last 12 months that were up months
                       (steady climbers vs one big jump)
    random             a random number -- the control. Anything that does no
                       better than this does not predict.

THE TESTS
---------
  1. Prediction: each month, rank every eligible stock by the score, then see
     what each did over the next month and the next 12 months. Rank
     correlation (IC) and its t-statistic on non-overlapping periods.
  2. Stability: the same, separately for 1997-2012 and 2013-today.
  3. Money: GBP 10,000 run by COMMIT rules, against GBP 10,000 in the S&P 500.
     There is no calendar -- no monthly or yearly rebuild. Money sits in an
     S&P 500 tracker until the evidence on a stock is strong; only then does
     it move into that stock, and it stays until the evidence has clearly
     turned. The evidence is checked every week, but trades only happen when
     a rule fires:
         ENTER  the stock has ranked in the top 5% on the score on three
                weekly checks in a row, and one of the 10 slots is free
         EXIT   the stock has fallen into the bottom half, confirmed on three
                weekly checks in a row -- or it stops trading
     The gap between "top 5%" and "bottom half" is deliberate: a stock that
     slips from 3rd to 40th is not sold. That band is what stops the
     churning that cost the monthly plan more than its whole starting pot.
     Costs (HL 2026): GBP 6.95 a deal, FX on US shares tiered 1% -> 0.25% by
     trade size; GBP 6.95 (no FX) to move in or out of a UK-listed S&P 500 tracker.

THE BAR -- stricter than usual, because ten scores are tested at once and one
in ten will look good by luck: t >= 3 overall AND t >= 2 in BOTH halves, AND
the commit-rules portfolio beats the S&P 500 by 1%/yr after costs in both
halves.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("bp", HERE / "backtest_plan.py")
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)

SPLIT = pd.Timestamp("2013-01-01")
TOP_N = 20
DEAL, FX = bp.DEAL, 0.01          # HL 2026: GBP 6.95 a deal; FX tiered, see bp.fx_cost
START = bp.START_GBP
T_ALL, T_HALF, MARGIN = 3.0, 2.0, 0.01


# ---------------------------------------------------------------------------
# signals
# ---------------------------------------------------------------------------

def build_signals(C: pd.DataFrame, seed: int = 7) -> dict[str, pd.DataFrame]:
    Cf = C.ffill(limit=10)
    R = Cf.pct_change(fill_method=None)
    vol126 = (R.rolling(126, min_periods=100).std() * np.sqrt(252)).clip(lower=0.15)
    vol252 = R.rolling(252, min_periods=200).std() * np.sqrt(252)
    lag21, lag252 = Cf.shift(21), Cf.shift(252)
    m12 = lag21 / lag252 - 1
    ma200 = Cf.rolling(200, min_periods=200).mean()
    hi252 = Cf.rolling(252, min_periods=200).max()
    monthly_up = (Cf / Cf.shift(21) - 1 > 0).astype(float).where(Cf.notna())
    smooth = sum(monthly_up.shift(21 * k) for k in range(12)) / 12
    rng = np.random.default_rng(seed)
    return {
        "mom_12_1_riskadj": m12 / vol126,
        "mom_12_1": m12,
        "mom_6_1": lag21 / Cf.shift(126) - 1,
        "mom_3": Cf / Cf.shift(63) - 1,
        "reversal_1m": -(Cf / lag21 - 1),
        "near_52w_high": Cf / hi252,
        "low_vol": -vol252,
        "trend_200": Cf / ma200 - 1,
        "smooth_mom": smooth,
        "random": pd.DataFrame(rng.normal(size=C.shape), index=C.index, columns=C.columns),
    }


PEERS = 20


def peer_momentum(C: pd.DataFrame, every: int = 21) -> pd.DataFrame:
    """
    Each stock's PEER GROUP's return over the past year -- with peers found from
    the data, not from industry labels: the 20 stocks whose daily moves were most
    closely correlated with it over the past year. Recomputed monthly, using only
    past prices, for every stock including ones later delisted -- so no
    survivorship bias from using today's industry lists.
    """
    Cf = C.ffill(limit=10)
    R = Cf.pct_change(fill_method=None).to_numpy(float)
    r12 = (Cf.shift(21) / Cf.shift(252) - 1).to_numpy(float)
    out = np.full(C.shape, np.nan)
    for i in range(252, len(C), every):
        W = R[i - 251:i + 1]
        ok = np.isfinite(W).all(axis=0) & np.isfinite(r12[i])
        k = np.where(ok)[0]
        if len(k) < 60:
            continue
        Z = W[:, k]
        Z = (Z - Z.mean(0)) / Z.std(0).clip(1e-12)
        corr = Z.T @ Z / len(Z)
        np.fill_diagonal(corr, -np.inf)
        top = np.argpartition(-corr, PEERS, axis=1)[:, :PEERS]
        pm = r12[i, k][top].mean(axis=1)
        out[i:i + every, k] = pm
    return pd.DataFrame(out, index=C.index, columns=C.columns)


def build_group_signals(C: pd.DataFrame, labels: pd.Series | None) -> dict[str, pd.DataFrame]:
    """
    THE WINNERS STUDY'S BEST FINDING, TESTED AS A STOCK PICKER.

    Among every pattern pair searched on 1997-2011, the one that held up best on
    2012-now was: a stock rising strongly off its 12-month low WHILE ITS SECTOR IS
    STILL WEAK. On the unseen years it was 2.2 times as likely as average to be a
    top-5% winner, LESS likely than average to be a bottom-5% loser, and beat the
    average stock by 13.7% over the next 12 months. Two related pairs (3-month
    and 1-month risers in weak sectors) also held up.

    That study used today's sector labels, which exist only for today's index
    members -- so it could only ever pick survivors. Here the same idea is scored
    two ways: with those labels, and with a peer group found from the price data
    (no survivorship). The score is high only when BOTH conditions are strong:
        min( rank of rise off the 12-month low , rank of peer-group WEAKNESS )
    """
    Cf = C.ffill(limit=10)
    rk = lambda D: D.rank(axis=1, pct=True)                     # noqa: E731
    lo = Cf.rolling(252, min_periods=200).min()
    off_low = rk(Cf / lo - 1)
    ret3 = rk(Cf / Cf.shift(63) - 1)
    out = {}
    pm = peer_momentum(C)
    weak = 1 - rk(pm)
    out["rise_weak_peers"] = np.minimum(off_low, weak).where(pm.notna())
    out["rise3m_weak_peers"] = np.minimum(ret3, weak).where(pm.notna())
    if labels is not None and len(labels):
        sec = labels.reindex(C.columns)
        r12 = Cf.shift(21) / Cf.shift(252) - 1
        sm = pd.DataFrame(np.nan, index=C.index, columns=C.columns)
        for _, cols in sec.groupby(sec).groups.items():
            cols = list(cols)
            if len(cols) >= 5:
                sm[cols] = np.repeat(r12[cols].mean(axis=1).to_numpy()[:, None], len(cols), axis=1)
        out["rise_weak_sector_LABELS"] = np.minimum(off_low, 1 - rk(sm)).where(sm.notna())
    return out


def _asof_panel(F: pd.DataFrame, item: str, index, columns, stale_days=550) -> pd.DataFrame:
    """Latest annual value of one item that had been FILED by each date."""
    f = F[F["item"] == item].sort_values(["ticker", "filed", "end"])
    out = {}
    for t, g in f.groupby("ticker"):
        if t not in columns:
            continue
        g = g[g["end"] >= g["end"].cummax()]            # a late filing of an OLD year is ignored
        v = g.groupby("filed")["val"].last()
        u = index.union(v.index)
        filed_on = pd.Series(v.index, index=v.index).reindex(u).ffill().reindex(index)
        s = v.reindex(u).ffill().reindex(index)
        s[(index.to_series() - filed_on).dt.days > stale_days] = np.nan
        out[t] = s
    return pd.DataFrame(out, index=index).reindex(columns=columns)


def _prior_year(F: pd.DataFrame, item: str) -> pd.DataFrame:
    """Each annual value paired with the SAME company's value one year earlier."""
    f = F[F["item"] == item][["ticker", "end", "filed", "val"]].sort_values("end")
    p = f.rename(columns={"val": "prev", "end": "prev_end"}).drop(columns="filed")
    f = f.assign(want=f["end"] - pd.Timedelta(days=365)).sort_values("want")
    p = p.sort_values("prev_end")
    m = pd.merge_asof(f, p, left_on="want", right_on="prev_end", by="ticker",
                      tolerance=pd.Timedelta(days=30), direction="nearest")
    return m.dropna(subset=["prev"]).assign(item=item + "_prev",
                                            val=lambda d: d["prev"])[["ticker", "item", "end", "filed", "val"]]


def build_fund_signals(C, mom12, fpath, epath, spy) -> dict[str, pd.DataFrame]:
    """
    ACCOUNT-BASED SCORES -- what the published stock-picking evidence rests on.
    All point in time: a figure is used only from the day it was filed.

        gross_profitability  gross profit / total assets  (Novy-Marx 2013)
        roa                  net income / total assets
        low_accruals         profits that ARE cash: -(net income - operating cash) / assets
                             (Sloan 1996)
        low_asset_growth     companies NOT bloating their balance sheet (Cooper et al 2008)
        earnings_yield       net income / market value
        fcf_yield            free cash flow / market value
        book_to_market       equity / market value (Fama-French value)
        quality_value        gross profitability AND cheap on free cash flow, together
        quality_momentum     gross profitability AND 12-month momentum, together
        value_momentum       earnings yield AND 12-month momentum, together
                             (Asness, Moskowitz, Pedersen 2013: value and momentum
                             work best combined)
        earnings_reaction    how the stock moved vs the S&P 500 over the two days
                             around its results, held as a score for the next
                             three months (post-earnings drift; Bernard & Thomas 1989)

    Market value comes from the "public float" each company states in its 10-K,
    rolled forward with the share price -- so no split or dividend adjustment
    can distort it.
    """
    out = {}
    idx, cols = C.index, list(C.columns)
    Cf = C.ffill(limit=10)
    if Path(fpath).exists():
        F = pd.read_parquet(fpath)
        F["end"], F["filed"] = pd.to_datetime(F["end"]), pd.to_datetime(F["filed"])
        F = pd.concat([F, _prior_year(F, "assets")], ignore_index=True)
        get = lambda it: _asof_panel(F, it, idx, cols)          # noqa: E731
        A = get("assets").where(lambda x: x > 0)
        GP = get("gross_profit")
        GP = GP.fillna(get("revenue") - get("cogs"))
        NI, CFO, CAPEX, EQ = get("net_income"), get("cfo"), get("capex"), get("equity")
        A0 = get("assets_prev").where(lambda x: x > 0)
        # market value: float stated at date d, moved with the price since d
        fl = F[F["item"] == "public_float"].sort_values(["ticker", "filed"])
        mv = {}
        for t, g in fl.groupby("ticker"):
            if t not in cols:
                continue
            g = g[g["end"] >= g["end"].cummax()]
            px_at = [Cf[t].asof(e) for e in g["end"]]
            ratio = pd.Series(np.array(g["val"], float) / np.array(px_at, float),
                              index=g["filed"].to_numpy())
            ratio = ratio[np.isfinite(ratio)].groupby(level=0).last()
            r = ratio.reindex(idx.union(ratio.index)).ffill().reindex(idx)
            mv[t] = r * Cf[t]
        MV = pd.DataFrame(mv, index=idx).reindex(columns=cols).where(lambda x: x > 0)
        out.update({
            "gross_profitability": GP / A,
            "roa": NI / A,
            "low_accruals": -(NI - CFO) / A,
            "low_asset_growth": -(A / A0 - 1),
            "earnings_yield": NI / MV,
            "fcf_yield": (CFO - CAPEX.fillna(0)) / MV,
            "book_to_market": (EQ / MV).where(EQ > 0),
        })
        rk = lambda D: D.rank(axis=1, pct=True)                 # noqa: E731
        out["quality_value"] = (rk(out["gross_profitability"]) + rk(out["fcf_yield"])) / 2
        out["quality_momentum"] = (rk(out["gross_profitability"]) + rk(mom12)) / 2
        out["value_momentum"] = (rk(out["earnings_yield"]) + rk(mom12)) / 2
    if Path(epath).exists():
        E = pd.read_csv(epath, usecols=["ticker", "date"])
        E["date"] = pd.to_datetime(E["date"])
        R = Cf.pct_change(fill_method=None)
        rs = spy.pct_change()
        pos = {c: k for k, c in enumerate(cols)}
        X = np.full(C.shape, np.nan)
        Rv, rsv = R.to_numpy(), rs.to_numpy()
        for t, d in zip(E["ticker"], E["date"]):
            k = pos.get(str(t).upper().replace(".", "-"))
            if k is None:
                continue
            i = idx.searchsorted(d)                    # first trading day on/after the filing
            if i < 1 or i + 2 >= len(idx):
                continue
            # the day before (results often land after the close) through the day after
            ab = np.nansum(Rv[i - 1:i + 2, k]) - np.nansum(rsv[i - 1:i + 2])
            X[i + 2:min(i + 2 + 63, len(idx)), k] = ab     # usable from two days later
        out["earnings_reaction"] = pd.DataFrame(X, index=idx, columns=cols)
    return out


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def t_stat(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(len(x))) if len(x) > 3 and x.std() > 0 else 0.0


def prediction(sig: pd.DataFrame, Cff: pd.DataFrame, member: np.ndarray,
               dates: list[int]) -> pd.DataFrame:
    S, X = sig.to_numpy(float), Cff.to_numpy(float)
    rows = []
    for i in dates:
        ok = member[i] & np.isfinite(S[i]) & np.isfinite(X[i])
        if ok.sum() < 50:
            continue
        s = pd.Series(S[i, ok])
        row = {"date": Cff.index[i]}
        for h, name in ((21, "1m"), (252, "12m")):
            if i + h >= len(X):
                continue
            f = pd.Series(X[i + h, ok] / X[i, ok] - 1)
            good = f.notna()
            if good.sum() < 50:
                continue
            ss, ff = s[good], f[good]
            row[f"ic_{name}"] = ss.rank().corr(ff.rank())
            if name == "12m":
                q = ss.rank(pct=True)
                row["top10_12m"] = ff[q >= 0.9].mean()
                row["bot10_12m"] = ff[q <= 0.1].mean()
                row["all_12m"] = ff.mean()
        rows.append(row)
    return pd.DataFrame(rows).set_index("date")


def summarise(P: pd.DataFrame, split=SPLIT) -> dict:
    out = {}
    for name, sl in (("all", slice(None)), ("first", slice(None, split)),
                     ("second", slice(split, None))):
        p = P.loc[sl]
        if p.empty:
            continue
        # 12-month results overlap, so the t-stat uses one start month a year.
        # No month is special: do it for all twelve and report the median.
        t12 = [t_stat(p[p.index.month == m].get("ic_12m", pd.Series(dtype=float)))
               for m in range(1, 13)]
        out[name] = {"ic_1m": round(float(p["ic_1m"].mean()), 4),
                     "t_1m": round(t_stat(p["ic_1m"]), 2),
                     "ic_12m": round(float(p["ic_12m"].mean()), 4) if "ic_12m" in p else None,
                     "t_12m": round(float(np.median(t12)), 2),
                     "top10_12m": round(float(p["top10_12m"].mean()), 4),
                     "bot10_12m": round(float(p["bot10_12m"].mean()), 4),
                     "all_12m": round(float(p["all_12m"].mean()), 4)}
    return out


SLOTS, ENTER_PCT, EXIT_PCT, CONFIRM_CHECKS, CHECK_EVERY = 10, 0.95, 0.50, 3, 5
EXIT_CONFIRM = CONFIRM_CHECKS


def commit_portfolio(sig, Cff, spy, member, start_i, costs=True) -> tuple[pd.Series, dict]:
    """
    No calendar. Idle money is in an S&P 500 tracker. Every week the evidence
    is checked; a trade happens only when ENTER or EXIT fires (see top).
    Returns weekly values and turnover statistics.
    """
    S, X = sig.to_numpy(float), Cff.to_numpy(float)
    Y = spy.to_numpy(float)
    idx = Cff.index
    fee = DEAL if costs else 0.0
    fxc = bp.fx_cost if costs else (lambda v: 0.0)
    index_units = (START - fee) / Y[start_i]          # start fully in the tracker
    pos, strikes, opened = {}, {}, {}
    streak = np.zeros(X.shape[1], int)            # weeks in a row in the top 5%
    marks, trades, holds = {}, 0, []
    book, entry = [], {}                          # every round trip, for the audit
    cols = list(Cff.columns)

    def close(k, i, px):
        e_i, e_px = entry.pop(k)
        seg = X[e_i:i + 1, k]
        day = np.nanmax(np.abs(np.diff(np.log(seg[np.isfinite(seg)])))) if np.isfinite(seg).sum() > 2 else 0
        book.append({"ticker": cols[k], "in": str(idx[e_i].date()), "out": str(idx[i].date()),
                     "ret": float(px / e_px - 1), "gbp": 0.0, "shares": 0.0,
                     "biggest_day_move": float(np.expm1(day)), "open": False, "_e": e_px, "_x": px})
    for i in range(start_i, len(idx), CHECK_EVERY):
        ok = member[i] & np.isfinite(S[i]) & np.isfinite(X[i])
        ref = np.sort(S[i, ok])
        if len(ref) < 50:
            continue
        pct = lambda v: np.searchsorted(ref, v) / len(ref)     # noqa: E731
        top = np.zeros(X.shape[1], bool)
        top[ok] = (np.searchsorted(ref, S[i, ok]) / len(ref)) >= ENTER_PCT
        streak = np.where(top, streak + 1, 0)
        # EXIT: stopped trading, or bottom half on EXIT_CONFIRM checks in a row
        for k in list(pos):
            alive = np.isfinite(X[i:min(i + 10, len(idx)), k]).any()
            weak = np.isfinite(S[i, k]) and pct(S[i, k]) < EXIT_PCT
            strikes[k] = strikes.get(k, 0) + 1 if weak else 0
            if not alive or strikes[k] >= EXIT_CONFIRM:
                px = X[i, k] if np.isfinite(X[i, k]) else Cff.iloc[:i + 1, k].dropna().iloc[-1]
                sh = pos[k]
                close(k, i, px)
                book[-1]["gbp"] = float(sh * (px - book[-1]["_e"]))
                gross = pos.pop(k) * px
                amt = gross - fxc(gross) - fee
                index_units += max(amt - fee, 0) / Y[i]          # back into the tracker
                trades += 1
                holds.append(i - opened.pop(k))
                strikes.pop(k, None)
        # ENTER: top ENTER_PCT, while a slot is free; strongest first
        free = SLOTS - len(pos)
        if free > 0:
            cand = np.where(ok)[0]
            cand = [k for k in cand[np.argsort(-S[i, cand])]
                    if k not in pos and streak[k] >= CONFIRM_CHECKS][:free]
            total = index_units * Y[i] + sum(p * X[i, k] for k, p in pos.items())
            for k in cand:
                per = total / SLOTS
                need = per + fee                                   # sell tracker, buy stock
                if index_units * Y[i] < need or per <= 2 * fee:
                    break
                index_units -= need / Y[i]
                pos[k] = (per - fee - fxc(per - fee)) / X[i, k]
                entry[k] = (i, X[i, k])
                opened[k] = i
                strikes[k] = 0
                trades += 1
        marks[idx[i]] = index_units * Y[i] + sum(
            p * X[i, k] for k, p in pos.items() if np.isfinite(X[i, k]))
    last = len(idx) - 1
    for k in list(pos):                            # still held: mark at today's price
        sh = pos[k]
        close(k, last, X[last, k])
        book[-1].update(gbp=float(sh * (X[last, k] - book[-1]["_e"])), open=True)
    for b in book:
        b.pop("_e"); b.pop("_x"); b.pop("shares")
    gains = sorted(book, key=lambda b: -b["gbp"])
    total_gain = sum(b["gbp"] for b in book)
    top3 = sum(b["gbp"] for b in gains[:3])
    yrs = max((idx[-1] - idx[start_i]).days / 365.25, 1e-9)
    return pd.Series(marks), {
        "best_trades": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in b.items()}
                        for b in gains[:5]],
        "worst_trades": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in b.items()}
                         for b in gains[-3:]],
        "net_trading_gain_gbp": round(total_gain),
        "share_of_gain_from_best_3": round(top3 / total_gain, 2) if total_gain > 0 else None,
        "suspect_price_jumps": [f"{b['ticker']} {b['in']}" for b in book
                                if b["biggest_day_move"] > 0.5],
        "trades_per_year": round(trades / yrs, 1),
        "median_hold_days": int(np.median(holds) * 365.25 / 252) if holds else None,
        "still_held": len(pos)}


def money(eq: pd.Series, spy: pd.Series, split=SPLIT) -> dict:
    res = {}
    for name, sl in (("all", slice(None)), ("first", slice(None, split)),
                     ("second", slice(split, None))):
        e = eq.loc[sl]
        s = spy.reindex(e.index).ffill()
        if len(e) < 12:
            continue
        yrs = (e.index[-1] - e.index[0]).days / 365.25
        ce = (e.iloc[-1] / e.iloc[0]) ** (1 / yrs) - 1
        cs = (s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1
        res[name] = {"gbp_from_10k": round(START * float(e.iloc[-1] / e.iloc[0])),
                     "spy_gbp_from_10k": round(START * float(s.iloc[-1] / s.iloc[0])),
                     "cagr": round(float(ce), 4), "spy_cagr": round(float(cs), 4),
                     "worst": round(float((e / e.cummax() - 1).min()), 3),
                     "spy_worst": round(float((s / s.cummax() - 1).min()), 3)}
    return res


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def write_md(out: dict, path: Path):
    L = ["# What predicts which stocks do best? — every score tested side by side\n",
         f"_Generated {out['generated'][:16].replace('T', ' ')} UTC. {out['data']}, "
         f"{out['from']} → {out['to']}. Only stocks in the S&P 500 on each date. "
         f"'random' is the control: a score that does no better than it predicts nothing._\n",
         f"**Bar:** t ≥ {T_ALL:.0f} overall and t ≥ {T_HALF:.0f} in BOTH halves, and the "
         f"commit-rules portfolio beats the S&P 500 by {MARGIN:.0%}/yr after HL costs in both halves.\n",
         "## 1. Did the score predict the next month / year?\n",
         "| Score (years tested; halves split at) | Rank corr. (1m) | t (all) | t first half | t second half | Top 10% next 12m | "
         "Bottom 10% | Average stock | Verdict |",
         "|---|---|---|---|---|---|---|---|---|"]
    for name, r in sorted(out["scores"].items(), key=lambda kv: -kv[1]["prediction"]["all"]["t_1m"]):
        a = r["prediction"]["all"]
        h1 = r["prediction"].get("first", {}).get("t_1m", 0)
        h2 = r["prediction"].get("second", {}).get("t_1m", 0)
        L.append(f"| {name} ({r['period']}) | {a['ic_1m']:+.3f} | {a['t_1m']:+.1f} | {h1:+.1f} | {h2:+.1f} | "
                 f"{a['top10_12m']:+.1%} | {a['bot10_12m']:+.1%} | {a['all_12m']:+.1%} | "
                 f"{'**PREDICTS**' if r['predicts'] else 'no'} |")
    L += [f"\n## 2. £{START:,.0f} run by commit rules — no calendar, trade only on strong evidence\n",
          f"Money waits in an S&P 500 tracker. A stock is bought only when it has been in the top "
          f"{1 - ENTER_PCT:.0%} on the score for {CONFIRM_CHECKS} weekly checks in a row (up to "
          f"{SLOTS} stocks), and sold only when it has "
          f"fallen into the bottom half on {EXIT_CONFIRM} weekly checks in a row.\n",
          "| Score | £ after HL costs | £ with no costs | S&P 500 £ | Yearly (costs) | S&P yearly | "
          "Worst fall | S&P worst | Trades / year | Typical hold | First half vs S&P | "
          "Second half vs S&P | Verdict |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in sorted(out["scores"].items(),
                          key=lambda kv: -kv[1]["money_costs"]["all"]["gbp_from_10k"]):
        m, z = r["money_costs"]["all"], r["money_free"]["all"]
        h = [r["money_costs"].get(k, {}) for k in ("first", "second")]
        d = [f"{(x['cagr'] - x['spy_cagr']):+.1%}/yr" if x else "" for x in h]
        L.append(f"| {name} ({r['period']}) | £{m['gbp_from_10k']:,} | £{z['gbp_from_10k']:,} | "
                 f"£{m['spy_gbp_from_10k']:,} | {m['cagr']:+.1%} | {m['spy_cagr']:+.1%} | "
                 f"{m['worst']:.0%} | {m['spy_worst']:.0%} | {r['turnover']['trades_per_year']} | "
                 f"{r['turnover']['median_hold_days'] or '—'} days | {d[0]} | {d[1]} | "
                 f"{'**PASSES**' if r['passes'] else 'no'} |")
    L.append("\n## 3a. Sanity check of the 'no costs' column\n")
    L.append("Several scores that predict nothing show millions of pounds with no costs. That "
             "is not believable, so here is where each no-cost result came from. A one-day price "
             "move of more than 50% on a large company is usually bad data from Yahoo.\n")
    L.append("| Score | £ no costs | Best 3 trades | Share of profit from them | "
             "Holdings with a >50% one-day move |")
    L.append("|---|---|---|---|---|")
    for name, r in sorted(out["scores"].items(),
                          key=lambda kv: -kv[1]["money_free"]["all"]["gbp_from_10k"]):
        t = r.get("turnover_free", {})
        best = ", ".join(f"{b['ticker']} {b['ret']:+.0%} ({b['in'][:7]})" for b in t.get("best_trades", [])[:3])
        sh = t.get("share_of_gain_from_best_3")
        sus = t.get("suspect_price_jumps", [])
        L.append(f"| {name} | £{r['money_free']['all']['gbp_from_10k']:,} | {best} | "
                 f"{'' if sh is None else format(sh, '.0%')} | "
                 f"{len(sus)}{': ' + ', '.join(sus[:6]) if sus else ''} |")
    L.append("\n## 3. Where the money came from — was it a rule, or a few lucky stocks?\n")
    L.append("For every score whose commit portfolio ended ahead of the S&P 500 (after costs): "
             "its five best trades, and how much of all its trading profit came from just "
             "three stocks. If three trades are most of the profit, the 'rule' is really a "
             "few lucky holdings, and it would not repeat. A price jump of more than 100% in one "
             "day is flagged as a possible data error.\n")
    for name, r in sorted(out["scores"].items(),
                          key=lambda kv: -kv[1]["money_costs"]["all"]["gbp_from_10k"]):
        m, t = r["money_costs"]["all"], r["turnover"]
        if m["gbp_from_10k"] <= m["spy_gbp_from_10k"]:
            continue
        sh = t.get("share_of_gain_from_best_3")
        L.append(f"**{name}** — trading profit £{t.get('net_trading_gain_gbp', 0):,}; "
                 f"{'' if sh is None else f'{sh:.0%} of it from the best three trades. '}"
                 f"{'Possible data errors: ' + ', '.join(t['suspect_price_jumps'][:8]) if t.get('suspect_price_jumps') else 'No suspect price jumps.'}\n")
        L.append("| Stock | Bought | Sold | Return | £ gain |")
        L.append("|---|---|---|---|---|")
        for b in t.get("best_trades", []):
            L.append(f"| {b['ticker']} | {b['in']} | {'still held' if b['open'] else b['out']} | "
                     f"{b['ret']:+.0%} | £{b['gbp']:,.0f} |")
        L.append("")
    L.append(f"\n**Result:** {out['verdict']}\n")
    L.append("---\n_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those "
             "in the delisted archive are included. That flatters every score equally, so it "
             "does not change which score ranks best — but it flatters the £ figures._")
    path.write_text("\n".join(L) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--delisted", default="data/delisted/delisted_weekly.parquet")
    ap.add_argument("--out", default="data/factor_screen.json")
    ap.add_argument("--md", default="docs/FACTORS.md")
    ap.add_argument("--spy-csv", default="")
    ap.add_argument("--fundamentals", default="data/fundamentals.parquet")
    ap.add_argument("--labels", default=bp.dp.CONSTITUENTS)
    ap.add_argument("--earnings", default="data/earnings_dates.csv")
    ap.add_argument("--no-membership", action="store_true", help="test data only")
    a = ap.parse_args()
    if START != 10_000:                       # a different pot writes its own report
        tag = f"_{int(START / 1000)}k"
        a.out = a.out.replace(".json", f"{tag}.json")
        a.md = a.md.replace(".md", f"{tag}.md")
    out = {"generated": pd.Timestamp.now("UTC").isoformat(), "pot_gbp": START}
    try:
        C, info = bp.load_panel(a.prices, a.delisted)
        C = C.loc[:, C.notna().sum() > 260]
        member = (np.ones(C.shape, bool) if a.no_membership
                  else bp.membership_mask(C.index, list(C.columns)))
        if a.spy_csv:
            spy = pd.read_csv(a.spy_csv, index_col=0, parse_dates=True).iloc[:, 0]
            spy = spy.reindex(C.index).ffill()
        else:
            spy = bp.load_spy(C.index)
        if spy.notna().sum() < 0.5 * len(C):
            raise RuntimeError("could not get SPY history")
        start = spy.first_valid_index()
        keep = C.index >= start
        C, member, spy = C.loc[keep], member[keep], spy.loc[keep]
        Cff = C.ffill()                       # a delisted stock holds its last price
        firsts = pd.Series(np.arange(len(C)), index=C.index).groupby(C.index.to_period("M")).first()
        dates = [int(i) for i in firsts if i >= 260]
        out.update({"from": str(C.index[dates[0]].date()), "to": str(C.index[-1].date()),
                    "data": f"{C.shape[1]} stocks ever in the S&P 500 "
                            f"({info.get('delisted_added', 0)} from the delisted archive)",
                    "info": info, "scores": {}})
        print(out["data"], out["from"], "->", out["to"], flush=True)
        sigs = build_signals(C)
        try:
            fs = build_fund_signals(C, sigs["mom_12_1"], a.fundamentals, a.earnings, spy)
            sigs.update(fs)
            out["fundamentals"] = f"{len(fs)} account-based scores added"
        except Exception as e:                                     # noqa: BLE001
            out["fundamentals"] = f"not available: {type(e).__name__}: {e}"
        print("fundamentals:", out["fundamentals"], flush=True)
        try:
            lab = bp.dp.load_constituents(a.labels).set_index("yf")["GICS Sector"]
        except Exception:                                          # noqa: BLE001
            lab = None
        try:
            sigs.update(build_group_signals(C, lab))
        except Exception as e:                                     # noqa: BLE001
            print("group signals failed:", e, flush=True)
        for name, sig in sigs.items():
            # each score is tested from the first date it has enough stocks to rank,
            # and its halves are split at the middle of ITS OWN history
            cnt = (sig.notna().to_numpy() & member).sum(axis=1)
            d_sig = [i for i in dates if cnt[i] >= 100]
            if len(d_sig) < 36:
                print(f"  {name}: not enough history, skipped", flush=True)
                continue
            split = C.index[d_sig[len(d_sig) // 2]]
            P = prediction(sig, Cff, member, d_sig)
            pr = summarise(P, split)
            eq_c, turn = commit_portfolio(sig, Cff, spy, member, d_sig[0], True)
            eq_f, turn_f = commit_portfolio(sig, Cff, spy, member, d_sig[0], False)
            mc, mf = money(eq_c, spy, split), money(eq_f, spy, split)
            predicts = (pr["all"]["t_1m"] >= T_ALL
                        and all(pr.get(h, {}).get("t_1m", 0) >= T_HALF
                                for h in ("first", "second")))
            passes = predicts and all(
                mc.get(h) and mc[h]["cagr"] >= mc[h]["spy_cagr"] + MARGIN
                for h in ("first", "second"))
            out["scores"][name] = {"prediction": pr, "money_costs": mc, "money_free": mf,
                                   "period": f"{C.index[d_sig[0]].year}–{C.index[-1].year}; "
                                             f"{split.year}",
                                   "turnover": turn, "turnover_free": turn_f,
                                   "predicts": bool(predicts), "passes": bool(passes)}
            print(f"  {name:18} trades/yr={turn['trades_per_year']:5} hold={turn['median_hold_days'] or '-'}d t={pr['all']['t_1m']:+5.1f}  top10={pr['all']['top10_12m']:+.1%} "
                  f"bot10={pr['all']['bot10_12m']:+.1%}  GBP {mc['all']['gbp_from_10k']:>9,} "
                  f"(no costs {mf['all']['gbp_from_10k']:,}; S&P {mc['all']['spy_gbp_from_10k']:,})",
                  flush=True)
        winners = [k for k, v in out["scores"].items() if v["passes"]]
        pred = [k for k, v in out["scores"].items() if v["predicts"]]
        if winners:
            out["verdict"] = (f"{', '.join(winners)} predicted AND made more money than the "
                              f"S&P 500 after costs in both halves.")
        elif pred:
            out["verdict"] = (f"{', '.join(pred)} predicted which stocks would do better, but "
                              f"after HL costs the commit-rules portfolio did not beat the "
                              f"S&P 500 by {MARGIN:.0%}/yr in both halves.")
        else:
            out["verdict"] = ("No score cleared the bar. None told you reliably, in advance, "
                              "which S&P 500 stocks would do best.")
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(out, indent=2, default=str))
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        write_md(out, Path(a.md))
        print(Path(a.md).read_text())
        return 0
    except Exception as exc:                                       # noqa: BLE001
        import traceback
        out["error"] = f"{type(exc).__name__}: {exc}"
        out["traceback"] = traceback.format_exc().splitlines()[-25:]
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(out, indent=2, default=str))
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text("# Factor screen FAILED\n\n```\n" + "\n".join(out["traceback"]) + "\n```\n")
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
