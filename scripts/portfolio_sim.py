#!/usr/bin/env python3
"""
What would GBP 10,000 have become?

WHY THIS EXISTS, AND WHY IT EXISTS NOW RATHER THAN EARLIER
-----------------------------------------------------------
Every test so far has been reported in R-multiples and t-statistics, which are
the right units for deciding whether an effect is real but useless for deciding
whether it is worth having. "+0.063R against random entry, t +6.20" is a true
sentence that tells you nothing about money.

This converts every candidate into the only question that matters: start with
GBP 10,000 in 2004, follow the rule to the letter, and see what is in the account
in 2026 -- next to what would have been there for doing nothing at all.

THE CONSTRAINT THAT CHANGES EVERYTHING
---------------------------------------
Every previous test simulated trades as if capital were unlimited: each signal
became a trade, independent of every other. A real account cannot do that. It
holds a finite number of positions, and a signal arriving when every slot is
full is a signal you cannot act on.

That matters enormously here, because these signals do not arrive evenly. The
cross-section found 42% of all lower-low signals landing on 5.7% of the dates.
They come in bursts, during selloffs, when every slot is already occupied by a
position taken three days earlier and now underwater. A per-trade backtest
counts all of them; an account takes the first two and watches the rest go by.

So this engine holds at most `slots` positions, funds them equally, and COUNTS
THE SIGNALS IT HAD TO DECLINE. That count is part of the result, not a footnote.

THE ARMS
--------
    hold_basket     buy the basket equally at the start, never trade again
    signal_exits    the lower-low signal with the ATR stop and trail
    signal_hold20   the same entries, no stop, no trail, out after 20 bars
    signal_hold120  the same entries, out after 120 bars
    random_slots    entries drawn at random, same count, same machinery -- the
                    null every arm above has to beat before it means anything
    timing_*        in the equal-weight basket when universe-wide lower-low
                    breadth is elevated, in cash otherwise

`random_slots` is the arm to watch. If a strategy cannot beat randomly-timed
entries run through the identical position limits and exits, its signal is
contributing nothing and the returns belong to the market.

WHAT THIS CANNOT TELL YOU
--------------------------
The panel is survivor-tilted: the delisting register is incomplete, so companies
that failed are under-represented. That flatters BUY AND HOLD more than it
flatters anything with a stop, because holding a company to zero is the outcome
most likely to be missing. Every number here that favours holding should be read
with that thumb on the scale.

Cash earns nothing by default. That is deliberately harsh on the timing arms,
which sit in cash for long stretches; --cash-rate puts a real rate back in.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quant import trades as TR                                # noqa: E402
from quant import patterns as PT                              # noqa: E402

START = 10_000.0
COST = 2 * 0.0004 + 2 * 1.0 / 10000        # round trip, fraction of notional
LOOKAHEAD = PT.LOOKAHEAD
MAX_GAP = 60
SEED = 20260926
# Calibrated, not chosen: on random-walk panels an 80% bar fired on 2 of 14.
# At 95% it fired on none. --calibrate re-measures this on any panel size.
PASS_WIN = 0.95


def lower_low_signal(df: pd.DataFrame) -> np.ndarray:
    """Confirmed swing low, lower than the one before, marked when knowable."""
    n = len(df)
    piv = PT.pivot_idx(df["low"], LOOKAHEAD, "low")
    p = df["low"].to_numpy(float)
    out = np.zeros(n, bool)
    for i in range(1, len(piv)):
        a_, b_ = int(piv[i - 1]), int(piv[i])
        k = b_ + LOOKAHEAD
        if b_ - a_ > MAX_GAP or k >= n - 2:
            continue
        if p[b_] < p[a_]:
            out[k] = True
    return out


# ---------------------------------------------------------------------------
# The account
# ---------------------------------------------------------------------------

def run_account(O, H, L, C, A, S, *, slots, k_stop, k_trail, max_hold,
                cost=COST, cash_rate=0.0, rng=None, start=START,
                mimic=None):
    """
    One account, walked day by day.

    Chronology within a day, kept honest:
        at the open   signals from YESTERDAY's close are filled, into free slots
        during the day stops are checked against the low, gaps filled at the open
        at the close  positions at their holding limit are closed, equity marked

    O/H/L/C/A are (days x tickers) arrays; S is the boolean signal array, True on
    the bar whose CLOSE produced the signal. Returns the equity curve and a log.
    """
    nd, nt = C.shape
    cash = float(start)
    pos = {}                       # ticker index -> dict
    eq = np.full(nd, np.nan)
    trades, declined, costs_paid = [], 0, 0.0
    fills = np.zeros(nd, int)
    daily_cash_rate = cash_rate / 252.0

    for i in range(1, nd):
        cash *= (1.0 + daily_cash_rate)

        # ---- 1. at the open: act on yesterday's signals -------------------
        eligible = (np.isfinite(O[i]) & (O[i] > 0)
                    & np.isfinite(A[i - 1]) & (A[i - 1] > 0))
        if mimic is None:
            want = np.flatnonzero(S[i - 1] & eligible)
        else:
            # THE MATCHED NULL. Buy on exactly the days the real strategy
            # bought, exactly as many times, but in a stock picked at random
            # from those trading that morning. Time in market, clustering,
            # market timing and regime are all held identical, so the ONLY
            # thing left to differ is which stock was chosen -- which is the
            # only thing the signal claims to know.
            k = int(mimic[i])
            pool = np.flatnonzero(eligible)
            pool = pool[~np.isin(pool, list(pos))]
            want = (rng.choice(pool, size=min(k, len(pool)), replace=False)
                    if k and len(pool) else np.array([], int))
        want = [j for j in want if j not in pos]
        if want:
            free = slots - len(pos)
            if free <= 0:
                declined += len(want)
            else:
                if len(want) > free:
                    declined += len(want) - free
                    # no claim is being made about WHICH of the competing
                    # signals is better, so the tie is broken at random
                    want = list(rng.choice(want, size=free, replace=False))
                for j in want:
                    risk = k_stop * A[i - 1, j]
                    entry = O[i, j]
                    if entry < TR.MIN_PRICE or risk / entry < TR.MIN_RISK_PCT:
                        continue
                    # equal weight across the slots, funded from cash
                    budget = min(cash, (cash + _mtm(pos, C, i)) / max(slots, 1))
                    if budget <= 1.0:
                        declined += 1
                        continue
                    sh = budget / entry
                    fee = budget * cost / 2.0
                    cash -= budget + fee
                    costs_paid += fee
                    pos[j] = {"sh": sh, "entry": entry, "entry_i": i,
                              "stop": entry - risk, "best": entry,
                              "atr": A[i - 1, j]}
                    fills[i] += 1

        # ---- 2. during the day: stops ------------------------------------
        for j in list(pos):
            p = pos[j]
            lo, op = L[i, j], O[i, j]
            if not np.isfinite(lo):
                continue
            if lo <= p["stop"]:
                px = op if (np.isfinite(op) and op < p["stop"]) else p["stop"]
                cash, costs_paid = _close(pos, j, px, i, cash, cost,
                                          costs_paid, trades, "stop")
                continue
            c = C[i, j]
            if np.isfinite(c):
                p["best"] = max(p["best"], c)
                p["stop"] = max(p["stop"], p["best"] - k_trail * p["atr"])

        # ---- 3. at the close: time exits and mark to market ---------------
        for j in list(pos):
            if i - pos[j]["entry_i"] >= max_hold:
                px = C[i, j]
                if np.isfinite(px):
                    cash, costs_paid = _close(pos, j, px, i, cash, cost,
                                              costs_paid, trades, "time")
        eq[i] = cash + _mtm(pos, C, i)

    # close anything still open at the final price
    last = nd - 1
    for j in list(pos):
        px = C[last, j]
        if np.isfinite(px):
            cash, costs_paid = _close(pos, j, px, last, cash, cost,
                                      costs_paid, trades, "end")
    eq[last] = cash + _mtm(pos, C, last)
    eq[0] = start
    return (pd.Series(eq).ffill().to_numpy(), trades, declined,
            costs_paid, fills)


def _mtm(pos, C, i):
    v = 0.0
    for j, p in pos.items():
        px = C[i, j]
        if np.isfinite(px):
            v += p["sh"] * px
    return v


def _close(pos, j, px, i, cash, cost, costs_paid, trades, reason):
    p = pos.pop(j)
    proceeds = p["sh"] * px
    fee = proceeds * cost / 2.0
    trades.append({"ticker": int(j), "entry_i": p["entry_i"], "exit_i": i,
                   "bars": i - p["entry_i"], "ret": px / p["entry"] - 1.0,
                   "reason": reason})
    return cash + proceeds - fee, costs_paid + fee


# ---------------------------------------------------------------------------

def summarise(eq, dates, *, trades=None, declined=0, costs=0.0,
              label="", start=START) -> dict:
    eq = np.asarray(eq, float)
    yrs = (dates[-1] - dates[0]).days / 365.25
    final = float(eq[-1])
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1.0
    ser = pd.Series(eq, index=dates)
    yearly = ser.resample("YE").last().pct_change().dropna()
    out = {
        "label": label,
        "final_gbp": round(final, 2),
        "profit_gbp": round(final - start, 2),
        "multiple": round(final / start, 3),
        "cagr": float((final / start) ** (1 / yrs) - 1) if yrs > 0 and final > 0 else None,
        "max_drawdown": float(dd.min()),
        "worst_year": float(yearly.min()) if len(yearly) else None,
        "best_year": float(yearly.max()) if len(yearly) else None,
        "losing_years": int((yearly < 0).sum()) if len(yearly) else None,
        "years": round(yrs, 1),
    }
    if trades is not None:
        rets = np.array([t["ret"] for t in trades], float) if trades else np.array([])
        out.update({
            "trades": len(trades),
            "win_rate": float((rets > 0).mean()) if len(rets) else None,
            "avg_trade_pct": float(rets.mean()) if len(rets) else None,
            "median_hold_days": float(np.median([t["bars"] for t in trades]))
            if trades else None,
            "signals_declined_no_capital": int(declined),
            "costs_paid_gbp": round(costs, 2),
        })
    return out


def buy_and_hold(C, dates, cols, start=START, cost=COST) -> np.ndarray:
    """
    Equal money into every name that is trading on day one, never touched again.
    Names that start later are simply never bought -- buying them would require
    knowing in advance that they would list, which is the whole survivorship
    problem in miniature.
    """
    first = C[1]
    live = np.flatnonzero(np.isfinite(first) & (first > 0))
    if len(live) == 0:
        return np.full(len(dates), start)
    per = start * (1 - cost / 2) / len(live)
    sh = per / first[live]
    val = np.nansum(C[:, live] * sh[None, :], axis=1)
    val[0] = start
    return pd.Series(val).ffill().to_numpy()



def _synthetic(seed, n_tick=150, n=1500):
    """A panel where nothing can possibly be predictable."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-04", periods=n)
    mkt = rng.normal(0.0002, 0.011, n)
    rows = []
    for i in range(n_tick):
        r = 0.9 * mkt + rng.normal(0.0001, 0.016, n)
        c = 100 * np.exp(np.cumsum(r))
        o = c * (1 + rng.normal(0, 0.003, n))
        h = np.maximum(o, c) * (1 + abs(rng.normal(0, 0.005, n)))
        l = np.minimum(o, c) * (1 - abs(rng.normal(0, 0.005, n)))
        rows.append(pd.DataFrame(dict(ticker=f"T{i:03d}", date=dates, open=o,
                                      high=h, low=l, close=c, volume=1e6)))
    return pd.concat(rows, ignore_index=True)


def calibrate(n_panels: int, slots: int, draws: int) -> dict:
    """
    HOW OFTEN DOES THIS SCRIPT CLAIM A DISCOVERY WHEN THERE IS NOTHING THERE?

    Run the entire procedure on panels of pure random walks and count. The
    first version of this script, with an unmatched random-entry null and an
    80% bar, fired on 36% of them -- it would have certified noise as a
    strategy one time in three. Anything above roughly 5% here means the
    verdict below is worthless, whatever it says.
    """
    fired = 0
    rows = []
    for p in range(n_panels):
        px = _synthetic(500 + p)
        wide = {f: px.pivot_table(index="date", columns="ticker", values=f)
                     .sort_index() for f in ("open", "high", "low", "close")}
        cols, dates = list(wide["close"].columns), wide["close"].index
        O, H, L, C = (wide[f].to_numpy(float)
                      for f in ("open", "high", "low", "close"))
        A = np.full(C.shape, np.nan); S = np.zeros(C.shape, bool)
        for k, t in enumerate(cols):
            g = px[px.ticker == t].sort_values("date").set_index("date")
            g = g[~g.index.duplicated()]
            idx = dates.get_indexer(g.index); ok = idx >= 0
            A[idx[ok], k] = TR.atr(g).to_numpy(float)[ok]
            S[idx[ok], k] = lower_low_signal(g)[ok]
        kw = dict(k_stop=1e6, k_trail=1e6, max_hold=120)
        bh = buy_and_hold(C, dates, cols)[-1]
        sig, fills = [], None
        for d in range(draws):
            eq, _, _, _, fl = run_account(O, H, L, C, A, S, slots=slots,
                                          rng=np.random.default_rng(d), **kw)
            sig.append(eq[-1])
            if fills is None:
                fills = fl
        nul = [run_account(O, H, L, C, A, S, slots=slots, mimic=fills,
                           rng=np.random.default_rng(900 + d), **kw)[0][-1]
               for d in range(draws)]
        sig, nul = np.array(sig), np.array(nul)
        win = float((sig[:, None] > nul[None, :]).mean())
        hit = bool(np.median(sig) > bh and win >= PASS_WIN)
        fired += hit
        rows.append({"panel": p, "buy_hold": round(bh, 0),
                     "signal_median": round(float(np.median(sig)), 0),
                     "matched_null_median": round(float(np.median(nul)), 0),
                     "win_pct": win, "declared_discovery": hit})
        print(f"  panel {p:2}  bh {bh:9,.0f}  sig {np.median(sig):9,.0f}  "
              f"null {np.median(nul):9,.0f}  win {win:4.0%}"
              f"{'   FALSE POSITIVE' if hit else ''}", flush=True)
    rate = fired / max(n_panels, 1)
    print(f"\n  FALSE POSITIVE RATE: {fired}/{n_panels} = {rate:.0%}  "
          f"(bar: median > buy-and-hold AND win >= {PASS_WIN:.0%})")
    return {"panels": n_panels, "false_positives": fired,
            "false_positive_rate": rate, "pass_win": PASS_WIN, "detail": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/portfolio_evidence.json")
    ap.add_argument("--slots", type=int, default=12)
    ap.add_argument("--basket", type=int, default=0,
                    help="if set, restrict to this many randomly chosen tickers")
    ap.add_argument("--cash-rate", type=float, default=0.0)
    ap.add_argument("--calibrate", type=int, default=0,
                    help="run the WHOLE procedure on this many random-walk "
                         "panels and report how often it declares a discovery. "
                         "Anything above about 5 per cent means the bar is too "
                         "low and no result from this script can be trusted.")
    ap.add_argument("--draws", type=int, default=40,
                    help="independent draws per arm; one path is not a result")
    a = ap.parse_args()

    out_path = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)

    try:
        if a.calibrate:
            print(f"calibrating on {a.calibrate} random-walk panels "
                  f"({a.draws} draws each)")
            cal = calibrate(a.calibrate, a.slots, a.draws)
            out_path.write_text(json.dumps(
                {"generated": pd.Timestamp.now("UTC").isoformat(),
                 "env": env, "mode": "calibration", "calibration": cal},
                indent=2, default=str))
            return 0
        rng = np.random.default_rng(SEED)
        px = pd.read_parquet(a.prices)
        px["date"] = pd.to_datetime(px["date"])
        keep = [t for t, g in px.groupby("ticker") if len(g) >= 300]
        if a.basket:
            keep = list(rng.choice(sorted(keep),
                                   size=min(a.basket, len(keep)), replace=False))
        px = px[px.ticker.isin(keep)]

        wide = {f: px.pivot_table(index="date", columns="ticker", values=f)
                       .sort_index() for f in ("open", "high", "low", "close")}
        cols = list(wide["close"].columns)
        dates = wide["close"].index
        O, H, L, C = (wide[f].to_numpy(float)
                      for f in ("open", "high", "low", "close"))
        print(f"{len(cols)} tickers, {len(dates):,} days, "
              f"{dates[0].date()} to {dates[-1].date()}")

        # ATR and signals, per ticker, aligned back onto the grid
        A = np.full(C.shape, np.nan)
        S = np.zeros(C.shape, bool)
        for k, t in enumerate(cols):
            g = px[px.ticker == t].sort_values("date").set_index("date")
            g = g[~g.index.duplicated()]
            idx = dates.get_indexer(g.index)
            ok = idx >= 0
            A[idx[ok], k] = TR.atr(g).to_numpy(float)[ok]
            S[idx[ok], k] = lower_low_signal(g)[ok]
        print(f"{int(S.sum()):,} signals on the grid", flush=True)

        results = {}
        dist = {}

        # ---- the thing to beat -------------------------------------------
        bh = buy_and_hold(C, dates, cols)
        results["hold_basket"] = summarise(bh, dates,
                                           label="buy and hold, never trade")
        base = results["hold_basket"]["final_gbp"]
        print(f"  hold_basket      GBP {base:>12,.0f}  "
              f"CAGR {results['hold_basket']['cagr']:+.2%}", flush=True)

        # ------------------------------------------------------------------
        # EVERY ARM IS RUN MANY TIMES, AND THE REASON IS NOT FUSSINESS.
        #
        # When more signals arrive than there are free slots, something has to
        # choose between them, and this engine chooses at random because no
        # claim is being made about which is better. That single arbitrary
        # choice moves the final balance enormously: on a test panel, the SAME
        # signal on the SAME data returned anywhere from GBP 17,213 to GBP
        # 26,807 depending only on the tie-break seed.
        #
        # So one equity curve is not a result, it is one draw from a wide
        # distribution, and comparing one curve to one null curve -- which is
        # what this script did in its first version, and it duly announced a
        # discovery on a random-walk panel -- is not evidence of anything.
        # Everything below is therefore a distribution, and the comparison is
        # between distributions.
        # ------------------------------------------------------------------
        arms = {
            "signal_exits":   dict(k_stop=2.5, k_trail=4.0, max_hold=120),
            "signal_hold20":  dict(k_stop=1e6, k_trail=1e6, max_hold=20),
            "signal_hold120": dict(k_stop=1e6, k_trail=1e6, max_hold=120),
            "signal_swing":   dict(k_stop=1.5, k_trail=2.0, max_hold=20),
        }

        def many(sig_fn, kw, k=a.draws, tag="", mimic=None):
            fins, cagrs, dds, decl, trs = [], [], [], [], []
            fills0 = None
            for d in range(k):
                Sd = S if sig_fn is None else sig_fn(d)
                eq, tr, dec, cst, _fl = run_account(
                    O, H, L, C, A, Sd, slots=a.slots, cash_rate=a.cash_rate,
                    rng=np.random.default_rng(SEED + 1000 * d),
                    mimic=mimic, **kw)
                if fills0 is None:
                    fills0 = _fl
                r = summarise(eq, dates, trades=tr, declined=dec, costs=cst)
                fins.append(r["final_gbp"]); cagrs.append(r["cagr"] or 0.0)
                dds.append(r["max_drawdown"]); decl.append(dec); trs.append(len(tr))
            return {"draws": k,
                    "final_gbp_median": float(np.median(fins)),
                    "final_gbp_p10": float(np.percentile(fins, 10)),
                    "final_gbp_p90": float(np.percentile(fins, 90)),
                    "final_gbp_min": float(np.min(fins)),
                    "final_gbp_max": float(np.max(fins)),
                    "cagr_median": float(np.median(cagrs)),
                    "max_drawdown_median": float(np.median(dds)),
                    "trades_median": float(np.median(trs)),
                    "declined_median": float(np.median(decl)),
                    "_fins": np.array(fins, float), "_fills": fills0,
                    "label": tag}

        real_sig = lambda d: S                                   # noqa: E731

        # VOLATILITY-MATCHED RANDOM ENTRY, AND WHY A PLAIN ONE IS USELESS
        # -----------------------------------------------------------------
        # The first version of this null drew entry days uniformly. On a panel
        # of pure random walks -- where by construction no signal can know
        # anything -- the lower-low rule still showed +5.59% forward return
        # against +4.83% for all bars, and the account duly "beat" the null
        # 99 times out of 100.
        #
        # The cause is not the signal. A lower low prints when a stock is
        # moving, so signal bars sit in HIGH-VOLATILITY stretches, and over a
        # fixed horizon a more volatile path has a higher SIMPLE return for
        # the same log drift -- exp(mu + sigma^2/2) rises with sigma. Uniform
        # random entry lands mostly on calm bars. So the comparison was
        # volatile entries against quiet ones, and the gap was convexity, not
        # skill: extra arithmetic return bought with exactly matching extra
        # risk, available to anyone who simply holds a volatile stock.
        #
        # The fix is to draw each null entry from the SAME ticker and the same
        # volatility decile as the real signal it replaces. Anything the real
        # signal still has after that is information about timing rather than
        # about which regime it happens to fire in.
        volpct = np.full(C.shape, np.nan)
        for k in range(C.shape[1]):
            v = A[:, k] / np.where(C[:, k] > 0, C[:, k], np.nan)
            ok = np.isfinite(v)
            if ok.sum() > 50:
                volpct[ok, k] = pd.Series(v[ok]).rank(pct=True).to_numpy()
        voldec = np.where(np.isfinite(volpct),
                          np.clip((volpct * 10).astype(int), 0, 9), -1)

        def rand_sig(d):
            """Random entries in the same ticker and volatility decile."""
            rr = np.random.default_rng(SEED + 7 + 31 * d)
            Sd = np.zeros_like(S)
            for k in range(S.shape[1]):
                hits = np.flatnonzero(S[:, k])
                if not len(hits):
                    continue
                valid = np.isfinite(C[:, k]) & (voldec[:, k] >= 0)
                valid[:211] = False
                valid[len(dates) - 2:] = False
                for dec in range(10):
                    want = int((voldec[hits, k] == dec).sum())
                    if not want:
                        continue
                    pool = np.flatnonzero(valid & (voldec[:, k] == dec))
                    if len(pool) == 0:
                        continue
                    pick = rr.choice(pool, size=min(want, len(pool)),
                                     replace=False)
                    Sd[pick, k] = True
            return Sd

        for name, kw in arms.items():
            dist[name] = many(real_sig, kw, tag=name)
            dist["null_" + name] = many(None, kw, tag="matched null " + name,
                                        mimic=dist[name]["_fills"])
            dist[name].pop("_fills_keep", None)
            r, q = dist[name], dist["null_" + name]
            # common-language effect size: pick one draw from each at random,
            # how often does the signal win? 50% is exactly no information.
            win = float((r["_fins"][:, None] > q["_fins"][None, :]).mean())
            r["beats_null_pct"] = win
            print(f"  {name:16} GBP {r['final_gbp_median']:>10,.0f} "
                  f"[{r['final_gbp_p10']:>9,.0f} - {r['final_gbp_p90']:>10,.0f}]"
                  f"   null {q['final_gbp_median']:>10,.0f}"
                  f"   signal wins {win:.0%}", flush=True)

        # ---- market timing on breadth -------------------------------------
        # The cross-section said these signals carry information about the DAY
        # rather than the STOCK. If so, universe-wide breadth should say
        # something about the market. Three thresholds, all reported, and each
        # against a null that stays invested the same FRACTION of the time but
        # in randomly placed blocks -- otherwise "invested 79% of the time" is
        # being compared with "invested always", which is a different question.
        live = np.isfinite(C).sum(axis=1)
        breadth = np.divide(S.sum(axis=1), np.maximum(live, 1))
        roll = pd.Series(breadth).rolling(504, min_periods=252)
        bh_ret = pd.Series(bh).pct_change().fillna(0.0).to_numpy()
        nd = len(dates)

        def walk(inv):
            eq = np.empty(nd); v = START
            for i in range(nd):
                v *= (1 + bh_ret[i]) if inv[i] else (1 + a.cash_rate / 252.0)
                eq[i] = v
            return eq

        for q_ in (0.80, 0.90, 0.95):
            thresh = roll.quantile(q_).to_numpy()
            hot = pd.Series(breadth > thresh).fillna(False).to_numpy()
            inv = (pd.Series(hot).shift(1).fillna(False)
                   .rolling(20, min_periods=1).max().astype(bool).to_numpy())
            key = f"timing_q{int(q_*100)}"
            results[key] = summarise(walk(inv), dates,
                                     label=f"in market after breadth > p{int(q_*100)}")
            results[key]["pct_time_invested"] = float(inv.mean())

            # block-shuffled null at the same invested fraction
            rr = np.random.default_rng(SEED + 99)
            nulls = []
            blocks = max(int(inv.mean() * nd / 20), 1)
            for _ in range(a.draws):
                z = np.zeros(nd, bool)
                for st in rr.integers(0, max(nd - 20, 1), size=blocks):
                    z[st:st + 20] = True
                nulls.append(walk(z)[-1])
            nulls = np.array(nulls, float)
            results[key]["null_median_gbp"] = float(np.median(nulls))
            results[key]["percentile_vs_null"] = float((nulls < results[key]["final_gbp"]).mean())
            r = results[key]
            print(f"  {key:16} GBP {r['final_gbp']:>10,.0f}   "
                  f"null {r['null_median_gbp']:>10,.0f}   "
                  f"invested {inv.mean():.0%}   "
                  f"pctile {r['percentile_vs_null']:.0%}", flush=True)

        # ---- the table ----------------------------------------------------
        print(f"\n  GBP {START:,.0f} from {dates[0].date()} to {dates[-1].date()}"
              f"   ({a.slots} slots, {a.draws} draws per arm)")
        print(f"  {'arm':18}{'median':>12}{'p10':>12}{'p90':>12}"
              f"{'CAGR':>9}{'maxDD':>8}{'vs null':>9}")
        print(f"  {'hold_basket':18}{base:>12,.0f}{'-':>12}{'-':>12}"
              f"{results['hold_basket']['cagr']:>+9.2%}"
              f"{results['hold_basket']['max_drawdown']:>8.1%}{'-':>9}")
        for k in sorted([x for x in dist if not x.startswith("null_")],
                        key=lambda x: -dist[x]["final_gbp_median"]):
            r = dist[k]
            print(f"  {k:18}{r['final_gbp_median']:>12,.0f}"
                  f"{r['final_gbp_p10']:>12,.0f}{r['final_gbp_p90']:>12,.0f}"
                  f"{r['cagr_median']:>+9.2%}{r['max_drawdown_median']:>8.1%}"
                  f"{r['beats_null_pct']:>9.0%}")
        for k in sorted([x for x in results if x.startswith("timing")],
                        key=lambda x: -results[x]["final_gbp"]):
            r = results[k]
            print(f"  {k:18}{r['final_gbp']:>12,.0f}{'-':>12}{'-':>12}"
                  f"{r['cagr']:>+9.2%}{r['max_drawdown']:>8.1%}"
                  f"{r['percentile_vs_null']:>9.0%}")

        # ---- verdict, the bar fixed in advance ----------------------------
        # An arm counts only if its MEDIAN clears buy-and-hold AND it beats its
        # own random-entry null in at least 80% of matched draws. Anything less
        # is inside the noise the tie-break alone generates.
        for k in list(dist):
            dist[k].pop("_fins", None)
            dist[k].pop("_fills", None)
        winners = [k for k in dist if not k.startswith("null_")
                   and dist[k]["final_gbp_median"] > base
                   and dist[k].get("beats_null_pct", 0) >= PASS_WIN]
        if winners:
            verdict = ("CLEARS BOTH BARS: " + ", ".join(winners) +
                       f" beat buy-and-hold on the median draw AND beat the "
                       f"day-matched null in at least {PASS_WIN:.0%} of matched "
                       f"draws. The day-matched null buys on the same days, the "
                       f"same number of times, in randomly chosen stocks -- so "
                       f"this is a claim about stock selection and nothing else.")
        else:
            near = [k for k in dist if not k.startswith("null_")
                    and dist[k]["final_gbp_median"] > base]
            verdict = (
                "NOTHING CLEARS BOTH BARS. "
                + (f"{', '.join(near)} beat buy-and-hold on the median draw, but "
                   f"did not beat the day-matched null, so the gain comes from "
                   f"being in the market more of the time, not from choosing "
                   f"better stocks. "
                   if near else
                   f"No arm beat buy-and-hold's GBP {base:,.0f} on the median "
                   f"draw. ")
                + "On this panel the honest instruction is to own the basket "
                  "and leave it alone.")
        print(f"\n  {verdict}")

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "start_gbp": START, "slots": a.slots, "draws": a.draws,
             "cash_rate": a.cash_rate, "cost_round_trip": COST,
             "tickers": len(cols), "from": str(dates[0].date()),
             "to": str(dates[-1].date()),
             "buy_and_hold": results["hold_basket"],
             "arms": dist, "timing": {k: v for k, v in results.items()
                                      if k.startswith("timing")},
             "verdict": verdict,
             "CAVEAT": "Panel is survivor-tilted; the delisting register is "
                       "incomplete. That flatters buy-and-hold more than it "
                       "flatters any arm that uses a stop."},
            indent=2, default=str))
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
