#!/usr/bin/env python3
"""
Does a confirmed lower low pick the STOCK, or merely the DAY?

WHERE THIS SITS
---------------
Eighty-four setups were tested; three passed; all three were divergence. Taking
that apart showed the oscillator was not the active ingredient -- what survived
was the depth of the fall and the timing of the entry. The plain rule, "a
confirmed swing low that is lower than the previous one, entered the morning
after it is confirmable", fires four times as often as divergence for two thirds
of the per-trade edge, which on breadth alone is nearly three times the total.

That rule beat RANDOM ENTRY by +0.063R with t +6.20, and its own null control
(the same clock, same machinery, higher lows instead of lower) came in at
+0.000R. So the apparatus is not manufacturing the result.

None of which means the rule is worth trading. Two things could still be true.

THE FIRST TRAP: IT MIGHT LOSE TO DOING NOTHING
-----------------------------------------------
Beating random entry is a low bar. The exit study already found a stop and a
trail losing to a plain timed hold in all twenty-four configurations tested. A
signal can beat random entry with the same exits and still be worse than simply
owning the stock. So every signal here is run twice: once through the stop and
trail, once with no stop and no trail at all. If the machinery subtracts value,
the honest recommendation is to hold and stop trading.

THE SECOND TRAP, WHICH ALREADY CAUGHT US ONCE
----------------------------------------------
Earlier in this project a six-state classifier produced t +6.3 for its
CAPITULATION state against a pooled benchmark. Measured against the SAME-DAY
cross-section it collapsed to -0.3. The state was not finding stocks about to
rise; it was finding days when everything rose. Sixty-nine percent of the
universe was "capitulating" on a single date.

A confirmed lower low is exactly the kind of signal that does this. Lower lows
cluster violently -- in a market-wide selloff, hundreds of stocks print one in
the same week. So the pooled comparison is the wrong one, and the right test has
two parts:

    SAME-DAY EXCESS    the signalled stock's forward return minus the equal-
                       weight mean of every stock trading that day. Positive
                       means the signal picked the stock.

    DATE-MATCHED       on each date, shuffle WHICH stocks signalled while
    PERMUTATION        keeping HOW MANY did. This destroys stock selection and
                       preserves day selection exactly. If the real result does
                       not beat this, the rule picks days, not stocks -- and a
                       day-picker is a market-timing claim, which is a different
                       and much harder business than the one we set out to build.

AND THE STATISTICS THAT MAKE IT HONEST
---------------------------------------
Forward windows overlap, which inflates t by roughly the square root of the
window length -- a twenty-day window on daily observations can manufacture a
t of 4 out of nothing. Everything here is therefore collapsed to one observation
per DATE first, and the t on that series is computed with a Newey-West variance
using a lag equal to the horizon. Both the naive and the corrected t are
reported, because the gap between them is the size of the illusion.

Breadth buckets split the signals by how much of the universe fired the same
day. If the excess lives only in the crowded bucket, it is the market bouncing.

OUTPUT
------
    data/lowerlow_evidence.json
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

RNG = np.random.default_rng(20260925)

LOOKAHEAD = PT.LOOKAHEAD
MAX_GAP = 60
HORIZONS = {"swing": 20, "position": 120}
EXITS = {"swing":    dict(k_stop=1.5, k_trail=2.0, max_hold=20),
         "position": dict(k_stop=2.5, k_trail=4.0, max_hold=120)}
COST_US = 2 * 0.0004 + 2 * 1.0 / 10000
N_PERM = 50
MIN_UNIVERSE = 50            # dates with fewer live tickers are not a cross-section


def lower_low_signal(df: pd.DataFrame) -> pd.Series:
    """
    A confirmed swing low, lower than the previous confirmed swing low, marked
    on the bar it first becomes knowable -- pivot + LOOKAHEAD, never the pivot
    itself. Entry is the next open, which the simulator handles.
    """
    n = len(df)
    low = df["low"]
    piv = PT.pivot_idx(low, LOOKAHEAD, "low")
    p = low.to_numpy(float)
    out = np.zeros(n, bool)
    for i in range(1, len(piv)):
        a_, b_ = int(piv[i - 1]), int(piv[i])
        k = b_ + LOOKAHEAD
        if b_ - a_ > MAX_GAP or k >= n - 2:
            continue
        if p[b_] < p[a_]:
            out[k] = True
    return pd.Series(out, index=df.index)


def newey_west_t(x: np.ndarray, lag: int,
                 pos: np.ndarray | None = None,
                 n_dates: int | None = None) -> tuple[float, float]:
    """
    (naive t, Newey-West t) for the mean of a series whose observations overlap.

    Overlapping forward windows make neighbouring observations share most of
    their data, so they are not independent draws and the plain standard error
    is far too small. Newey-West widens it using the series' own autocovariance
    out to `lag`, with Bartlett weights so the estimate stays positive.

    `pos` is each observation's position on the CALENDAR, not its position in
    this array. Signals do not occur on every date, so a series of signal-date
    observations is compressed: element i+1 may be a month after element i. Feed
    the compressed array to a lag-20 correction and "lag 20" silently means
    something different for every gap. Scattering the values back onto the full
    calendar first makes the lag mean twenty trading days, which is what the
    twenty-day forward window actually overlaps.
    """
    x = np.asarray(x, float)
    if pos is None:
        x = x[np.isfinite(x)]
        n = len(x)
        if n < 30:
            return float("nan"), float("nan")
        m = x.mean()
        e = x - m
        nobs = n
        full = e
        mask = np.ones(n, bool)
    else:
        good = np.isfinite(x)
        x, pos = x[good], np.asarray(pos)[good]
        n = len(x)
        if n < 30:
            return float("nan"), float("nan")
        m = float(x.mean())
        L = int(n_dates or (pos.max() + 1))
        full = np.zeros(L)
        mask = np.zeros(L, bool)
        full[pos] = x - m
        mask[pos] = True
        nobs = n

    g0 = float(full[mask] @ full[mask]) / nobs
    naive = m / np.sqrt(g0 / nobs) if g0 > 0 else float("nan")

    var = g0
    for l_ in range(1, min(lag, len(full) - 1) + 1):
        # only pairs where BOTH dates carry an observation contribute; the
        # normaliser stays nobs so the units match the variance above
        pair = mask[l_:] & mask[:-l_]
        if not pair.any():
            continue
        g = float(full[l_:][pair] @ full[:-l_][pair]) / nobs
        var += 2.0 * (1.0 - l_ / (lag + 1.0)) * g
    if var <= 0:
        return float(naive), float("nan")
    return float(naive), float(m / np.sqrt(var / nobs))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/lowerlow_evidence.json")
    a = ap.parse_args()

    out_path = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)

    try:
        px = pd.read_parquet(a.prices)
        px["date"] = pd.to_datetime(px["date"])
        frames = {t: g.sort_values("date").set_index("date")
                  for t, g in px.groupby("ticker") if len(g) >= 300}
        print(f"{len(frames)} instruments")

        sig = {t: lower_low_signal(g) for t, g in frames.items()}
        total = int(sum(s.sum() for s in sig.values()))
        print(f"{total:,} confirmed lower lows", flush=True)

        # ------------------------------------------------------------------
        # PART ONE  --  does the exit machinery beat doing nothing?
        # Identical entries, identical holding cap. The only difference is
        # whether a stop and a trail are present. A stop of 1,000 ATRs is never
        # touched, which turns the simulator into a plain timed hold without
        # altering a line of its logic.
        # ------------------------------------------------------------------
        part1 = {}
        for hname, hp in EXITS.items():
            traded, held = [], []
            for t, g in frames.items():
                s = sig[t]
                if not s.any():
                    continue
                tr = TR.simulate(g, s, cost_pct=COST_US, **hp)
                hd = TR.simulate(g, s, cost_pct=COST_US, k_stop=1000.0,
                                 k_trail=1000.0, max_hold=hp["max_hold"])
                if not tr.empty:
                    traded.append(tr)
                if not hd.empty:
                    held.append(hd)
            if not traded or not held:
                continue
            T = pd.concat(traded, ignore_index=True)
            H = pd.concat(held, ignore_index=True)
            part1[hname] = {
                "trades": int(len(T)),
                "with_exits_net_pct": float(T.net_pct.mean()),
                "with_exits_median_pct": float(T.net_pct.median()),
                "with_exits_win_rate": float((T.net_pct > 0).mean()),
                "with_exits_median_bars": float(T.bars.median()),
                "hold_only_net_pct": float(H.net_pct.mean()),
                "hold_only_median_pct": float(H.net_pct.median()),
                "hold_only_win_rate": float((H.net_pct > 0).mean()),
                "exits_add_pct": float(T.net_pct.mean() - H.net_pct.mean()),
                "worst_1pct_with_exits": float(T.net_pct.quantile(0.01)),
                "worst_1pct_hold_only": float(H.net_pct.quantile(0.01)),
            }
            p = part1[hname]
            print(f"  [{hname}] exits {p['with_exits_net_pct']:+.2%} vs "
                  f"hold {p['hold_only_net_pct']:+.2%}  "
                  f"-> exits add {p['exits_add_pct']:+.2%}", flush=True)

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "status": "part one complete, cross-section pending",
             "signals": total, "exits_vs_hold": part1}, indent=2, default=str))

        # ------------------------------------------------------------------
        # PART TWO  --  the stock, or the day?
        # ------------------------------------------------------------------
        close = px.pivot_table(index="date", columns="ticker", values="close")
        open_ = px.pivot_table(index="date", columns="ticker", values="open")
        close = close.sort_index()
        open_ = open_.reindex_like(close)
        S = pd.DataFrame(False, index=close.index, columns=close.columns)
        for t, s in sig.items():
            if t in S.columns:
                S.loc[s.index[s.to_numpy()], t] = True
        Sv = S.to_numpy()
        print(f"panel {close.shape[0]:,} dates x {close.shape[1]} tickers",
              flush=True)

        part2 = {}
        for hname, H in HORIZONS.items():
            # entry at the next open, exit at the close H bars after the signal
            fwd = (close.shift(-H) / open_.shift(-1) - 1.0).to_numpy(float)
            ok = np.isfinite(fwd)
            live = ok.sum(axis=1)
            peer = np.where(live > 0, np.nansum(np.where(ok, fwd, 0.0), axis=1)
                            / np.maximum(live, 1), np.nan)
            excess = fwd - peer[:, None]

            usable = (live >= MIN_UNIVERSE)
            hit = Sv & ok & usable[:, None]
            cnt = hit.sum(axis=1)
            days = np.flatnonzero(cnt > 0)

            # one observation per date -- never per trade, or the overlapping
            # windows and the cross-sectional correlation both count twice
            daily = np.array([np.nanmean(excess[d][hit[d]]) for d in days])
            breadth = cnt[days] / live[days]
            n_all = close.shape[0]
            naive_t, nw_t = newey_west_t(daily, H, pos=days, n_dates=n_all)

            # HOW BIG AN EFFECT COULD THIS EVEN SEE?
            # A null is only as strong as the test's power. Back out the
            # standard error the Newey-West t implies and state the smallest
            # excess that would have cleared the bar, so "we found nothing"
            # can be read as either "there is nothing" or "we could not tell".
            real_mean = float(np.nanmean(daily))
            nw_se = (abs(real_mean / nw_t) if isinstance(nw_t, float)
                     and np.isfinite(nw_t) and nw_t != 0 else float("nan"))
            mde = 3.0 * nw_se if np.isfinite(nw_se) else float("nan")

            # A date carrying fifty signals estimates that day far better than
            # a date carrying one, and equal weighting throws that away. The
            # weighted figure is the more precise estimate; the equal-weighted
            # one is the more conservative, because weighting tilts towards
            # exactly the crowded days this test is trying to look past. Both
            # are reported and the verdict uses the conservative one.
            w = cnt[days].astype(float)
            fin = np.isfinite(daily)
            wmean = (float(np.sum(daily[fin] * w[fin]) / np.sum(w[fin]))
                     if fin.any() else float("nan"))

            # ---- the date-matched permutation ----------------------------
            # Keep every signal DATE and the NUMBER of signals on it; shuffle
            # only which tickers carry them, among the tickers actually
            # trading that day. Day-selection survives untouched; stock-
            # selection is destroyed. The real result has to beat this.
            perm_means = []
            for _ in range(N_PERM):
                vals = []
                for j, d in enumerate(days):
                    idx = np.flatnonzero(ok[d] & usable[d])
                    k = int(cnt[d])
                    if k == 0 or len(idx) < k:
                        continue
                    pick = RNG.choice(idx, size=k, replace=False)
                    vals.append(float(np.nanmean(excess[d][pick])))
                if vals:
                    perm_means.append(float(np.mean(vals)))
            perm_means = np.array(perm_means, float)
            real = float(np.nanmean(daily))
            # the permutation mean should sit at zero by construction; its
            # SPREAD is the yardstick the real number has to clear
            p_sd = float(perm_means.std(ddof=1)) if len(perm_means) > 2 else float("nan")
            z_perm = (real - float(perm_means.mean())) / p_sd if p_sd > 0 else float("nan")

            # ---- breadth buckets ----------------------------------------
            buckets = {}
            for label, lo, hi in (("lone", 0.0, 0.01),
                                  ("normal", 0.01, 0.05),
                                  ("crowded", 0.05, 1.01)):
                m = (breadth >= lo) & (breadth < hi)
                if m.sum() >= 30:
                    nt, nwt = newey_west_t(daily[m], H, pos=days[m],
                                           n_dates=n_all)
                    buckets[label] = {
                        "dates": int(m.sum()),
                        "signals": int(cnt[days][m].sum()),
                        "mean_excess": float(np.nanmean(daily[m])),
                        "naive_t": nt, "newey_west_t": nwt}

            part2[hname] = {
                "horizon_bars": H,
                "signal_dates": int(len(days)),
                "signals_used": int(cnt[days].sum()),
                "mean_same_day_excess": real,
                "signal_weighted_excess": wmean,
                "naive_t": naive_t,
                "newey_west_t": nw_t,
                "newey_west_se": nw_se,
                "min_detectable_excess_at_t3": mde,
                "permutation_mean": float(perm_means.mean()) if len(perm_means) else None,
                "permutation_sd": p_sd,
                "z_vs_permutation": z_perm,
                "median_breadth": float(np.median(breadth)),
                "pct_signals_on_crowded_days": float(
                    cnt[days][breadth >= 0.05].sum() / max(cnt[days].sum(), 1)),
                "by_breadth": buckets,
            }
            p = part2[hname]
            print(f"\n  [{hname}] same-day excess {real:+.3%} over "
                  f"{p['signal_dates']:,} dates")
            print(f"      naive t {naive_t:+.2f}   Newey-West t {nw_t:+.2f} "
                  f"(lag {H})")
            print(f"      signal-weighted {wmean:+.3%}   "
                  f"smallest detectable at t=3: {mde:+.3%}")
            print(f"      vs date-matched permutation: z {z_perm:+.2f}")
            for lab, b in buckets.items():
                print(f"      {lab:8} {b['dates']:5,} dates  "
                      f"{b['mean_excess']:+.3%}  NW t {b['newey_west_t']:+.2f}")

        # ------------------------------------------------------------------
        # VERDICT, fixed before the numbers were seen.
        # Three independent hurdles, all of which must clear:
        #   1. the exits must not destroy value against a plain hold
        #   2. same-day excess positive with a Newey-West t above 3
        #   3. it must beat the date-matched permutation by 3 sd
        # ------------------------------------------------------------------
        checks = {}
        for hname in HORIZONS:
            p1, p2 = part1.get(hname), part2.get(hname)
            if not p1 or not p2:
                continue
            checks[hname] = {
                "exits_beat_hold": bool(p1["exits_add_pct"] > 0),
                "same_day_excess_positive": bool(p2["mean_same_day_excess"] > 0),
                "newey_west_t_over_3": bool(
                    isinstance(p2["newey_west_t"], float)
                    and p2["newey_west_t"] > 3.0),
                "beats_permutation_3sd": bool(
                    isinstance(p2["z_vs_permutation"], float)
                    and p2["z_vs_permutation"] > 3.0),
            }
            checks[hname]["picks_stocks"] = bool(
                checks[hname]["same_day_excess_positive"]
                and checks[hname]["newey_west_t_over_3"]
                and checks[hname]["beats_permutation_3sd"])

        any_picks = any(c["picks_stocks"] for c in checks.values())
        any_exits = any(c["exits_beat_hold"] for c in checks.values())
        if any_picks and any_exits:
            verdict = ("A LOWER LOW PICKS THE STOCK, AND THE EXITS EARN THEIR "
                       "KEEP. This is the first result in the project to clear "
                       "a same-day cross-sectional test. Build the daily signal "
                       "on it.")
        elif any_picks:
            verdict = ("A LOWER LOW PICKS THE STOCK, BUT THE EXITS DESTROY "
                       "VALUE. The selection is real; the stop and trail are "
                       "not. Signal the stock, then hold it -- do not trade it.")
        else:
            verdict = ("A LOWER LOW PICKS THE DAY, NOT THE STOCK. Against the "
                       "same-day cross-section the edge does not survive, which "
                       "means the rule fires when the whole market is about to "
                       "bounce and says nothing about WHICH stock to own. That "
                       "is a market-timing claim, not the stock-selection tool "
                       "we set out to build, and the +0.063R against random "
                       "entry was the pooled benchmark flattering it -- exactly "
                       "as it flattered CAPITULATION at t +6.3.")
        print(f"\n  {verdict}")

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "instruments": len(frames), "signals": total,
             "lookahead": LOOKAHEAD, "cost_pct": COST_US,
             "permutations": N_PERM, "min_universe": MIN_UNIVERSE,
             "exits_vs_hold": part1, "cross_section": part2,
             "checks": checks, "verdict": verdict}, indent=2, default=str))
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
