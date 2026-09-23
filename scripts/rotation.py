#!/usr/bin/env python3
"""
Buy-and-hold, with the dying stocks taken out.

THE DESIGN FLAW THIS FIXES
--------------------------
Every rule built in this repo so far answered one question: "this stock, or
cash?" Buy-and-hold answers a different one: "all stocks, always." When a rule
here sold a failing stock, the money sat in cash at 0% -- for a quarter of the
time, in the best confirmation arm. When buy-and-hold held that same failing
stock, the loss was absorbed by six hundred others still compounding.

So the comparison was a single-stock timing rule against a fully invested
portfolio, and the timing rule kept losing the pound race while WINNING the
risk race: the retest confirmation with an escape hatch returned 11.9% a year
against 15.1%, but with a worst drawdown of -30.6% against -54.0%, a Sharpe of
0.90 against 0.78 and a Calmar of 0.39 against 0.28. The entire pound gap is
explained by the cash it sat in.

THE FIX, IN ONE SENTENCE
------------------------
When a stock is sold, its money does not go to cash; it goes to the stocks that
are currently in healthy trends. Always invested, but never in the failing ones.
That is buy-and-hold minus the stocks that are dying.

THE ARMS, ALL REBALANCED ON THE SAME CALENDAR
----------------------------------------------
    index           equal weight in every live stock, rebalanced. The fair
                    benchmark -- the index-fund version of buy-and-hold. Every
                    other arm differs from it ONLY by its rules.
    trend           equal weight in every stock the confirmed-exit rules say is
                    healthy; failing stocks get nothing and their money is
                    redistributed. Cash only if too few stocks qualify.
    trend_top100    the same, but among healthy stocks hold only the 100 with
                    the strongest 12-month-minus-1-month momentum
    trend_top50     the same, top 50
    trend_invvol    healthy stocks weighted by inverse volatility, so a wild
                    stock and a calm one carry the same risk, not the same money
    top100_invvol   momentum top 100, inverse-vol weighted

A sale is executed the day the rule fires, not at month end: an escape hatch
that waits three weeks is not an escape hatch. Freed money waits in cash, at a
cash rate, until the next rebalance redeploys it.

HONESTY
-------
    - Stocks that delist are sold at their last price, in every arm alike.
    - Cash earns --cash-rate (default 2%, a rough 30-year average for a UK
      instant-access or US T-bill rate); 0% is also reported.
    - Fit on 1996-2012, reported separately on 2013-2026.
    - --calibrate runs the whole thing on random walks first.
    - Costs: 10bp round trip on all turnover, rebalancing included.
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
_spec = importlib.util.spec_from_file_location("cf", HERE / "confirmation.py")
cf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cf)

START = 10_000.0
COST_SIDE = 0.0005             # 10bp round trip
SPLIT = pd.Timestamp("2013-01-01")
MIN_NAMES = 20                 # below this many healthy stocks, hold cash
# THE BAR, SET BY THE NULL. On 12 random-walk panels the best of these arms, in
# its weaker half, never beat the index by more than -1.3% a year. Beating it by
# "any amount" fired on 1 panel in 5. Requiring +1% a year in BOTH halves sits
# clear of that noise -- and 1% a year compounded over thirty years is about a
# third more money, so it is also where the effort starts being worth it.
CAGR_MARGIN = 0.01
SEED = 20260930


def healthy_state(C, Hh, Ll, V):
    """
    The best rule found so far, as a per-stock daily in/out state:
    retest-confirmed exit, fast oversold re-entry after an ordinary exit,
    trend repair required after a hard exit, 60-day cooldown.
    """
    S = cf.indicators(C, Hh, Ll, V)
    conf = cf.retest_confirm(C, S["ma200"], S["atr"])
    hard = cf.hard_exit(C, Ll, S)
    z = np.zeros((1, C.shape[1]), bool)
    fast = np.nan_to_num(
        ((S["kf"] > S["dsl"]) & np.r_[z, S["kf"][:-1] <= S["dsl"][:-1]]
         & (S["kf"] < 40))
        | ((S["rsi"] > 30) & np.r_[z, S["rsi"][:-1] <= 30])).astype(bool)
    ma50s = np.r_[np.full((20, C.shape[1]), np.nan), S["ma50"][:-20]]
    repair = np.nan_to_num((C > S["ma200"]) & (S["ma50"] > ma50s)).astype(bool)
    st = cf.machine(conf, hard, fast, C, 60, True, repair)
    # a stock without 200 days of history has no trend to judge yet
    return st & np.isfinite(S["ma200"])


# ---------------------------------------------------------------------------
# MARKET AND INDUSTRY -- the flaw in blind reinvestment
# ---------------------------------------------------------------------------
# The first rotation run sold failing stocks and put the money into stocks that
# had NOT FAILED YET. In 2008 those were about to. The portfolio stayed fully
# invested all the way down a market-wide crash: worst drawdown -50.6% against
# the index's -55.3%, barely any protection, and it lost the 1996-2012 half by
# 3.2% a year because of it. A stock-level rule cannot see that everything is
# falling together. These can.

def market_regime(C, state, confirm=3, member=None):
    """
    Two views of the whole market, both point-in-time.

    trend    the equal-weight index of every live stock, against its own
             200-day average -- confirmed by `confirm` consecutive closes either
             side, the confirmation that did best in the battery. Off = cash.
    breadth  the share of stocks the rules call healthy. Exposure scales with
             it: at 50% healthy or more, fully invested; at 25%, half invested;
             at 0%, all cash. Selling INTO strength of evidence rather than on
             a single line.
    """
    R = pd.DataFrame(C).pct_change().to_numpy()
    live = np.isfinite(R) if member is None else (np.isfinite(R) & member)
    mr = np.where(live.sum(axis=1) > 0,
                  np.nansum(np.where(live, R, 0), axis=1) / np.maximum(live.sum(axis=1), 1),
                  0.0)
    lvl = np.cumprod(1 + np.nan_to_num(mr))
    ma = pd.Series(lvl).rolling(200, min_periods=200).mean().to_numpy()
    above = np.nan_to_num(lvl > ma).astype(bool)
    below = np.nan_to_num(lvl < ma).astype(bool)
    run_a = pd.Series(above.astype(float)).rolling(confirm).sum().to_numpy() >= confirm
    run_b = pd.Series(below.astype(float)).rolling(confirm).sum().to_numpy() >= confirm
    on = np.ones(len(lvl), bool); cur = True
    for t in range(len(lvl)):
        if cur and run_b[t]:
            cur = False
        elif not cur and run_a[t]:
            cur = True
        on[t] = cur
    alive = np.isfinite(C) if member is None else (np.isfinite(C) & member)
    br = np.where(alive.sum(axis=1) > 0,
                  (state & alive).sum(axis=1) / np.maximum(alive.sum(axis=1), 1), 0.0)
    exposure = np.clip(br / 0.5, 0.0, 1.0)
    return on.astype(float), exposure


def industry_health(C, state, every=21, lookback=252, peers=20):
    """
    Is this stock's INDUSTRY healthy?

    Industry here is measured, not labelled: each month, each stock's peer group
    is the 20 stocks whose daily returns moved most closely with its own over the
    previous year. Three reasons for that over a sector label:
      - it exists for every company, including the ones that were delisted,
        which no free sector list covers
      - it is point-in-time: the groups are built only from past returns
      - it captures what actually moves together. A chip-maker and a cloud
        company may sit in different official sectors and trade as one.
    The industry is healthy when more than half its peers are healthy by the
    same rules. A stock can look fine while its whole group is rolling over;
    this sees that.
    """
    nd, nt = C.shape
    R = pd.DataFrame(C).pct_change().to_numpy()
    out = np.zeros((nd, nt))
    stf = state.astype(float)
    for t0 in range(0, nd, every):
        t1 = min(t0 + every, nd)
        if t0 < lookback:
            out[t0:t1] = 1.0          # not enough history: do not block
            continue
        W = R[t0 - lookback:t0]
        ok = np.isfinite(W)
        cnt = ok.sum(axis=0)
        use = cnt >= 150
        X = np.where(ok, W, 0.0)
        mu = X.sum(axis=0) / np.maximum(cnt, 1)
        X = np.where(ok, W - mu, 0.0)
        sd = np.sqrt((X ** 2).sum(axis=0) / np.maximum(cnt, 1))
        X = np.where(sd > 0, X / np.where(sd > 0, sd, 1), 0.0)
        corr = (X.T @ X) / lookback
        np.fill_diagonal(corr, -np.inf)
        corr[:, ~use] = -np.inf
        P = np.zeros((nt, nt))
        k = min(peers, int(use.sum()) - 1)
        if k < 5:
            out[t0:t1] = 1.0
            continue
        top = np.argpartition(-corr, k - 1, axis=1)[:, :k]
        rows = np.repeat(np.arange(nt), k)
        P[rows, top.ravel()] = 1.0 / k
        out[t0:t1] = stf[t0:t1] @ P.T
        out[t0:t1, ~use] = 1.0        # a stock with no measurable group: do not block
    return out


MEMBERSHIP_URL = ("https://raw.githubusercontent.com/hanshof/sp500_constituents/"
                  "main/sp_500_historical_components.csv")


def membership_mask(idx, cols, url=MEMBERSHIP_URL):
    """
    THE LOOK-AHEAD THIS REMOVES -- the largest flaw in the whole project.

    The universe is every stock that was EVER in the S&P 500 between 1996 and
    2026, and until now every portfolio could hold those stocks from the day
    they listed. Amazon from 1997, though it joined the index in 2005. Nvidia
    from 1999, joined 2001. Netflix from 2002, joined 2010. Tesla from 2010,
    joined 2020. 660 of the stocks were not in the index at the end of 1996.

    Choosing from a list of FUTURE index members is choosing from a list of
    companies already known to have succeeded. It is why the "index" showed
    +20.4% a year for 1996-2012, a period containing two 50% crashes.

    The fix is standard: a stock is eligible on a date only if it was IN the
    index on that date. The membership file is dated snapshots; each snapshot
    holds until the next one.
    """
    h = pd.read_csv(url)
    h["date"] = pd.to_datetime(h["date"])
    h = h.sort_values("date")
    norm = lambda x: x.strip().upper().replace(".", "-")          # noqa: E731
    col_pos = {norm(c): i for i, c in enumerate(cols)}
    M = np.zeros((len(idx), len(cols)), bool)
    snap_dates = h["date"].to_numpy()
    snaps = [[col_pos[norm(t)] for t in str(r).split(",")
              if t.strip() and norm(t) in col_pos] for r in h["tickers"]]
    pos = np.searchsorted(snap_dates, idx.to_numpy(), side="right") - 1
    for t in range(len(idx)):
        if pos[t] >= 0:
            M[t, snaps[pos[t]]] = True
    return M


def run_portfolio(C, target_fn, rebal_every, cash_rate):
    """
    Daily portfolio walk. Holdings drift with prices between rebalances.
    `target_fn(t)` returns target weights over stocks (summing to <= 1; the
    remainder is cash). A stock whose weight target is zero is SOLD THAT DAY
    -- exits are immediate; only redeployment waits for the rebalance.
    """
    nd, nt = C.shape
    R = np.nan_to_num(pd.DataFrame(C).pct_change().to_numpy())
    alive = np.isfinite(C)
    val = np.zeros(nt)
    cash = START
    eq = np.empty(nd)
    turnover = 0.0
    daily_cash = (1 + cash_rate) ** (1 / 252) - 1
    for t in range(nd):
        if t > 0:
            val *= (1 + R[t])
            cash *= (1 + daily_cash)
        # a delisted stock is sold at its last price
        dead = (val > 0) & ~alive[t]
        if dead.any():
            cash += val[dead].sum() * (1 - COST_SIDE)
            turnover += val[dead].sum(); val[dead] = 0.0
        tw = target_fn(t)
        # immediate exits
        sell = (val > 0) & (tw <= 0)
        if sell.any():
            cash += val[sell].sum() * (1 - COST_SIDE)
            turnover += val[sell].sum(); val[sell] = 0.0
        if t % rebal_every == 0:
            total = cash + val.sum()
            want = tw * total
            delta = want - val
            cost = np.abs(delta).sum() * COST_SIDE
            turnover += np.abs(delta).sum()
            val = want.copy()
            cash = total - want.sum() - cost
        eq[t] = cash + val.sum()
    return eq, turnover / START


def metrics(eq, idx, mask=None):
    if mask is not None:
        eq = eq[mask]; idx = idx[mask]
    eq = eq / eq[0] * START
    return {"final_gbp": float(eq[-1]), **cf.risk(eq, idx)}


def build_targets(C, state, mode, mom=None, vol=None, top=None,
                  regime=None, industry=None, member=None):
    nd, nt = C.shape
    alive = np.isfinite(C) if member is None else (np.isfinite(C) & member)

    def fn(t):
        if mode == "index":
            m = alive[t].copy()
        else:
            m = alive[t] & state[t]
        if industry is not None:
            m &= industry[t] > 0.5
        if top is not None and mom is not None:
            sc = np.where(m & np.isfinite(mom[t]), mom[t], -np.inf)
            k = int(min(top, np.isfinite(sc).sum()))
            m = np.zeros(nt, bool)
            if k > 0:
                m[np.argpartition(-sc, k - 1)[:k]] = True
                m &= np.isfinite(sc)
        n = int(m.sum())
        w = np.zeros(nt)
        if mode != "index" and n < MIN_NAMES:
            return w
        if n == 0:
            return w
        if vol is not None:
            # THE BUG THE FIRST RUN HIT: a delisted stock with a stale, flat
            # price has volatility near zero, so inverse-vol handed it nearly
            # all the money. Floor the volatility at 10% a year and cap any
            # single position at 5%.
            v = np.where(np.isfinite(vol[t]), np.maximum(vol[t], 0.10), np.nan)
            iv = np.where(m & np.isfinite(v), 1 / v, 0.0)
            if iv.sum() > 0:
                w = iv / iv.sum()
                for _ in range(5):
                    over = w > 0.05
                    if not over.any():
                        break
                    excess = (w[over] - 0.05).sum()
                    w[over] = 0.05
                    rest = (w > 0) & ~over
                    if rest.any():
                        w[rest] += excess * w[rest] / w[rest].sum()
        else:
            w[m] = 1.0 / n
        if regime is not None:
            w = w * float(regime[t])       # the remainder is cash
        return w
    return fn


def run_all(C, Hh, Ll, V, idx, rebal, cash_rate, member=None):
    state = healthy_state(C, Hh, Ll, V)
    df = pd.DataFrame(C)
    # 12-1 momentum, the standard academic definition: skip the latest month
    mom = (df.shift(21) / df.shift(252) - 1).to_numpy()
    vol = (df.pct_change().rolling(63, min_periods=40).std()
           * np.sqrt(252)).to_numpy()
    mkt_on, breadth = market_regime(C, state, member=member)
    ind = industry_health(C, state)
    T, I = "trend", "index"
    arms = {
        "index":            build_targets(C, state, I, member=member),
        # the OLD benchmark, kept only to show how big the look-ahead was
        "index_lookahead":  build_targets(C, state, I),
        "index+mkt":        build_targets(C, state, I, regime=mkt_on, member=member),
        "trend_top50":      build_targets(C, state, T, mom=mom, top=50, member=member),
        "top50+mkt":        build_targets(C, state, T, mom=mom, top=50, regime=mkt_on, member=member),
        "top50+breadth":    build_targets(C, state, T, mom=mom, top=50, regime=breadth, member=member),
        "top50+ind":        build_targets(C, state, T, mom=mom, top=50, industry=ind, member=member),
        "top50+mkt+ind":    build_targets(C, state, T, mom=mom, top=50, regime=mkt_on, industry=ind, member=member),
        "top50+brd+ind":    build_targets(C, state, T, mom=mom, top=50, regime=breadth, industry=ind, member=member),
        "top100+mkt+ind":   build_targets(C, state, T, mom=mom, top=100, regime=mkt_on, industry=ind, member=member),
        "trend+mkt+ind":    build_targets(C, state, T, regime=mkt_on, industry=ind, member=member),
        "top50_iv+mkt+ind": build_targets(C, state, T, mom=mom, vol=vol, top=50, regime=mkt_on, industry=ind, member=member),
    }
    res = {}
    fit = np.asarray(idx < SPLIT)
    for name, fn in arms.items():
        eq, to = run_portfolio(C, fn, rebal, cash_rate)
        res[name] = {"full": metrics(eq, idx),
                     "fit_1996_2012": metrics(eq, idx, fit),
                     "test_2013_on": metrics(eq, idx, ~fit),
                     "turnover_x": float(to)}
    return res


def synthetic(seed, n_tick=160, n=2600):
    C, Hh, Ll, V = cf.synthetic(seed, n_tick, n)
    return C, Hh, Ll, V


def verdict_for(res, key="full"):
    b = res["index"][key]
    wins = []
    for k, v in res.items():
        if k in ("index", "index_lookahead"):
            continue
        m = v[key]
        if (m["cagr"] > b["cagr"] + CAGR_MARGIN
                and (m["calmar"] or 0) > (b["calmar"] or 0) * 1.10):
            wins.append(k)
    return wins


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/rotation_evidence.json")
    ap.add_argument("--rebal", type=int, default=21)
    ap.add_argument("--cash-rate", type=float, default=0.02)
    ap.add_argument("--calibrate", type=int, default=0)
    a = ap.parse_args()
    out_path = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)
    try:
        if a.calibrate:
            fired, rows = 0, []
            for p in range(a.calibrate):
                C, Hh, Ll, V = synthetic(1000 + p)
                idx = pd.bdate_range("2004-01-01", periods=C.shape[0])
                res = run_all(C, Hh, Ll, V, idx, a.rebal, a.cash_rate)
                # the verdict must hold IN THE TEST WINDOW, not just overall
                w = verdict_for(res, "test_2013_on")
                w = [k for k in w if k in verdict_for(res, "fit_1996_2012")]
                fired += bool(w)
                rows.append({"panel": p, "winners": w})
                print(f"  panel {p:2}  {'FIRED ' + ', '.join(w) if w else 'nothing'}",
                      flush=True)
            rate = fired / max(a.calibrate, 1)
            print(f"\n  FALSE POSITIVE RATE: {fired}/{a.calibrate} = {rate:.0%}")
            out_path.write_text(json.dumps(
                {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
                 "mode": "calibration", "false_positive_rate": rate,
                 "detail": rows}, indent=2, default=str))
            return 0

        px = pd.read_parquet(a.prices)
        px["date"] = pd.to_datetime(px["date"])
        w = {f: px.pivot_table(index="date", columns="ticker", values=f)
                  .sort_index() for f in ("high", "low", "close", "volume")}
        idx = w["close"].index
        C, Hh, Ll, V = (w[f].to_numpy(float) for f in ("close", "high", "low", "volume"))
        keep = np.isfinite(C).sum(axis=0) > 500
        C, Hh, Ll, V = C[:, keep], Hh[:, keep], Ll[:, keep], V[:, keep]
        cols = [c for c, k in zip(w["close"].columns, keep) if k]
        try:
            member = membership_mask(idx, cols)
            print(f"membership: {member.any(axis=0).sum()} of {len(cols)} stocks "
                  f"matched to the index history; avg {member.sum(axis=1).mean():.0f} "
                  f"eligible per day")
        except Exception as e:                                # noqa: BLE001
            member = None
            print(f"membership file unavailable ({e}); running WITHOUT it")
        print(f"{C.shape[1]} stocks (delisted ones INCLUDED, sold at last price), "
              f"{len(idx):,} days, {idx[0].date()} -> {idx[-1].date()}")

        out = {}
        for cr in (a.cash_rate, 0.0):
            res = run_all(C, Hh, Ll, V, idx, a.rebal, cr, member)
            out[f"cash_{cr:.0%}"] = res
            print(f"\n  === cash earns {cr:.0%}, rebalance every {a.rebal} days ===")
            for win in ("full", "fit_1996_2012", "test_2013_on"):
                print(f"\n  {win}")
                print(f"  {'arm':16}{'GBP':>13}{'CAGR':>8}{'maxDD':>8}"
                      f"{'Sharpe':>8}{'Calmar':>8}")
                for k in sorted(res, key=lambda x: -res[x][win]["final_gbp"]):
                    m = res[k][win]
                    print(f"  {k:16}{m['final_gbp']:>13,.0f}{m['cagr']:>+8.1%}"
                          f"{m['max_drawdown']:>8.1%}{(m['sharpe'] or 0):>8.2f}"
                          f"{(m['calmar'] or 0):>8.2f}")

        res = out[f"cash_{a.cash_rate:.0%}"]
        both = [k for k in verdict_for(res, "fit_1996_2012")
                if k in verdict_for(res, "test_2013_on")]
        b = res["index"]["full"]
        if both:
            best = max(both, key=lambda k: res[k]["full"]["final_gbp"])
            m = res[best]["full"]
            verdict = (f"BEATS BUY AND HOLD, IN BOTH HALVES: {best} turns "
                       f"GBP 10,000 into GBP {m['final_gbp']:,.0f} against the "
                       f"index's GBP {b['final_gbp']:,.0f} — CAGR "
                       f"{m['cagr']:+.1%} vs {b['cagr']:+.1%}, worst drawdown "
                       f"{m['max_drawdown']:.1%} vs {b['max_drawdown']:.1%}. "
                       f"Passing arms: {', '.join(both)}.")
        else:
            verdict = (f"No arm beat the index by {CAGR_MARGIN:.0%} a year AND "
                       f"on Calmar in BOTH halves of the sample.")
        print(f"\n  {verdict}")
        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "stocks": int(C.shape[1]), "from": str(idx[0].date()),
             "to": str(idx[-1].date()), "rebalance_days": a.rebal,
             "min_names": MIN_NAMES, "results": out,
             "passes_both_halves": both, "verdict": verdict}, indent=2, default=str))
        return 0
    except Exception as exc:                                     # noqa: BLE001
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "error": f"{type(exc).__name__}: {exc}",
             "traceback": tb.splitlines()[-25:]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
