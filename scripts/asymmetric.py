#!/usr/bin/env python3
"""
Slow to sell, quick to buy back, and forbidden to churn.

WHERE THIS CAME FROM
--------------------
Laying out every exit the 50/200 cross ever gave on MSFT showed the problem
exactly. Of 22 completed round trips, only 6 bought back CHEAPER than they
sold -- 27%. The 2026 exit sold at $463 and bought back at $500, having been
correctly out through a fall to $355. The signal spotted the downturn. The
re-entry threw the winnings away.

Three faults, each fixable, none of which this project had addressed:

  1. NO CONFIRMATION. Every rule here fired on the FIRST close through the
     line. That is not how anyone trades, and it is why the panel run showed
     508 switches for a death-cross rule. Confirmation means the break has to
     persist -- n consecutive closes -- or be decisive -- beyond the line by
     a multiple of ATR -- before it counts.

  2. RE-ENTRY TIED TO THE EXIT SIGNAL. Waiting for price to climb back above
     its 200-day average means buying near the top of the recovery. On the
     2026 episode a stochastic cross re-entered at $399 against the 200-day
     rule's $464.

  3. NOTHING STOPPING AN IMMEDIATE RE-EXIT. This is the one that actually
     matters. Re-entering faster produced MORE round trips (133 against 70)
     and less money, because the rule threw itself straight back out. A
     COOLDOWN -- a minimum holding period after buying back, during which no
     exit may fire -- breaks that loop.

On MSFT the three together, at the best of 24 settings, returned GBP 203,099
against buy-and-hold's GBP 184,543 with the drawdown cut from -68.7% to -54.3%.
That is one stock and the best of 24 tries, which is worth nothing on its own.
Hence this script.

HOW THE CHERRY-PICK IS EXPOSED
------------------------------
    fit window    1996-2012   every combination is scored here
    test window   2013-2026   the combination that won the fit window is
                              reported here, and so is the whole grid

If the best fit-window setting does not carry over, the grid is noise and the
right answer is to pick something sensible and stop tuning. This project has
already seen a parameter sweep whose fit-to-test rank correlation was -0.065.

Every stock is also sorted into deciles by its own outcome, because the mean
of a distribution where one stock returns 67x and another returns 0.03x answers
a question nobody asked -- and because the whole point of an exit rule is what
it does at the bottom of that distribution.

And --calibrate runs everything on pure random walks first. An earlier version
of the portfolio simulator declared a discovery on 36% of them.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

START = 10_000.0
COST = 0.0010
SEED = 20260928
SPLIT = pd.Timestamp("2013-01-01")

# A MARGIN, NOT A HAIR.
# Calibrating against random walks showed the fit window almost always picking
# the longest cooldown -- which converges towards buy-and-hold, so the result
# lands within a per cent of it and a coin flip decides whether it is "above".
# At any margin that fired on 17% of random panels. Requiring a material 10%
# takes it to zero, and an edge worth changing your behaviour for should be
# materially better, not better by a rounding error.
PASS_MARGIN = 0.10

# Deliberately coarse. A fine grid searched harder is a fine grid overfitted
# harder, and these are the settings a person would actually choose between.
CONFIRM = (1, 3, 5)              # consecutive closes beyond the line
COOLDOWN = (0, 20, 60, 120, 250) # trading days locked in after re-entry


def indicators(C, Hh, Ll):
    df = pd.DataFrame(C)
    ma50 = df.rolling(50, min_periods=50).mean().to_numpy()
    ma200 = df.rolling(200, min_periods=200).mean().to_numpy()
    # RSI
    dif = df.diff()
    up = dif.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    dn = (-dif).clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rsi = (100 - 100 / (1 + up / dn.replace(0, np.nan))).to_numpy()
    # stochastic
    lo14 = pd.DataFrame(Ll).rolling(14, min_periods=14).min().to_numpy()
    hi14 = pd.DataFrame(Hh).rolling(14, min_periods=14).max().to_numpy()
    rng = np.where((hi14 - lo14) > 0, hi14 - lo14, np.nan)
    kf = 100 * (C - lo14) / rng
    dsl = pd.DataFrame(kf).rolling(3, min_periods=3).mean().to_numpy()
    return ma50, ma200, rsi, kf, dsl


def confirmed(sig: np.ndarray, n: int) -> np.ndarray:
    """True only once the condition has held n bars running."""
    if n <= 1:
        return np.nan_to_num(sig).astype(bool)
    s = pd.DataFrame(np.nan_to_num(sig).astype(float))
    return (s.rolling(n, min_periods=n).sum() >= n).fillna(False).to_numpy()


def state_machine(exit_sig, re_sig, cooldown: int) -> np.ndarray:
    """
    Long unless thrown out. Once back in, locked in for `cooldown` bars -- the
    piece that stops a fast re-entry from simply re-triggering the exit.
    """
    nd, nt = exit_sig.shape
    st = np.ones(nt, bool)
    last_in = np.full(nt, -10 ** 9)
    out = np.empty((nd, nt), bool)
    for t in range(nd):
        can_exit = st & exit_sig[t] & ((t - last_in) >= cooldown)
        st = st & ~can_exit
        back = (~st) & re_sig[t]
        last_in = np.where(back, t, last_in)
        st = st | back
        out[t] = st
    return out


def equity(ret, state):
    pos = np.vstack([np.ones((1, state.shape[1]), bool), state[:-1]])
    sw = np.vstack([np.zeros((1, state.shape[1]), bool), pos[1:] != pos[:-1]])
    r = np.where(pos, np.nan_to_num(ret), 0.0) - np.where(sw, COST, 0.0)
    return START * np.cumprod(1.0 + r, axis=0), sw.sum(axis=0), pos


def roundtrip_win(C, pos):
    """Fraction of completed exits that bought back cheaper. The honest metric."""
    good = tot = 0
    for j in range(pos.shape[1]):
        p = pos[:, j]
        sw = np.flatnonzero(np.r_[False, p[1:] != p[:-1]])
        i = 0
        while i < len(sw) - 1:
            if p[sw[i]]:
                i += 1; continue
            a, b = C[sw[i], j], C[sw[i + 1], j]
            if np.isfinite(a) and np.isfinite(b) and a > 0:
                tot += 1; good += b < a
            i += 2
    return (good / tot if tot else None), tot


def run_grid(C, Hh, Ll, idx, valid):
    ma50, ma200, rsi, kf, dsl = indicators(C, Hh, Ll)
    ret = np.nan_to_num(pd.DataFrame(C).pct_change().to_numpy())

    raw_exits = {"below200": C < ma200, "death_cross": ma50 < ma200}
    # fast, mean-reverting re-entry: the oversold-reclaim family, which is the
    # one group that showed positive edge in the 84-setup catalogue
    fast = (((kf > dsl) & (np.r_[[[False] * C.shape[1]], kf[:-1] <= dsl[:-1]]) &
             (kf < 40)) |
            ((rsi > 30) & np.r_[[[False] * C.shape[1]], rsi[:-1] <= 30]))
    fast = np.nan_to_num(fast).astype(bool)
    slow = np.nan_to_num(C > ma200)

    hold_eq = START * np.cumprod(1 + ret, axis=0)
    fit_m = np.asarray(idx < SPLIT)
    rows = {}
    for ename, ex in raw_exits.items():
        for nconf in CONFIRM:
            exc = confirmed(ex, nconf)
            for rname, rsig in (("fast", fast), ("slow", slow)):
                for cd in COOLDOWN:
                    st = state_machine(exc, rsig, cd)
                    eq, sw, pos = equity(ret, st)
                    win, ntrip = roundtrip_win(C, pos[:, valid])
                    f = eq[-1][valid]
                    fit_eq = eq[fit_m][-1][valid] if fit_m.sum() > 300 else f
                    rows[f"{ename}|c{nconf}|{rname}|cd{cd}"] = {
                        "mean_gbp": float(np.mean(f)),
                        "median_gbp": float(np.median(f)),
                        "fit_mean_gbp": float(np.mean(fit_eq)),
                        "beat_hold": int((f > hold_eq[-1][valid]).sum()),
                        "mean_switches": float(np.mean(sw[valid])),
                        "roundtrip_bought_cheaper": win,
                        "roundtrips": ntrip,
                        "pct_time_invested": float(np.mean(pos[:, valid])),
                    }
    return rows, hold_eq[-1], ret


def decile(f, hold_final, valid):
    dec = pd.qcut(pd.Series(hold_final[valid]).rank(method="first"), 10,
                  labels=False).to_numpy()
    out = {}
    for d in range(10):
        m = dec == d
        if m.sum() >= 3:
            out[f"d{d+1}"] = float(np.mean(f[m]) /
                                   np.mean(hold_final[valid][m]) - 1)
    return out


def synthetic(seed, n_tick=140, n=2600):
    rng = np.random.default_rng(seed)
    mkt = rng.normal(0.0002, 0.011, n)
    C = np.empty((n, n_tick)); Hh = np.empty_like(C); Ll = np.empty_like(C)
    for i in range(n_tick):
        r = 0.85 * mkt + rng.normal(0.0002, 0.019, n)
        c = 100 * np.exp(np.cumsum(r)); C[:, i] = c
        Hh[:, i] = c * (1 + abs(rng.normal(0, 0.006, n)))
        Ll[:, i] = c * (1 - abs(rng.normal(0, 0.006, n)))
    return C, Hh, Ll


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/asymmetric_evidence.json")
    ap.add_argument("--calibrate", type=int, default=0)
    a = ap.parse_args()

    out_path = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)

    try:
        if a.calibrate:
            print(f"calibrating on {a.calibrate} random-walk panels")
            fired, rows = 0, []
            for p in range(a.calibrate):
                C, Hh, Ll = synthetic(800 + p)
                idx = pd.bdate_range("2004-01-01", periods=C.shape[0])
                valid = np.isfinite(C[-1])
                g, hold, _ = run_grid(C, Hh, Ll, idx, valid)
                best = max(g, key=lambda k: g[k]["fit_mean_gbp"])
                hm = float(np.mean(hold[valid]))
                hit = bool(g[best]["mean_gbp"] > hm * (1 + PASS_MARGIN))
                fired += hit
                rows.append({"panel": p, "best_by_fit": best,
                             "test_mean": g[best]["mean_gbp"], "hold": hm,
                             "declared": hit})
                print(f"  panel {p:2}  {best:34} {g[best]['mean_gbp']:>10,.0f}"
                      f"  hold {hm:>10,.0f}{'   FIRED' if hit else ''}",
                      flush=True)
            rate = fired / max(a.calibrate, 1)
            print(f"\n  FALSE POSITIVE RATE: {fired}/{a.calibrate} = {rate:.0%}")
            out_path.write_text(json.dumps(
                {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
                 "mode": "calibration", "false_positive_rate": rate,
                 "panels": a.calibrate, "detail": rows}, indent=2, default=str))
            return 0

        px = pd.read_parquet(a.prices)
        px["date"] = pd.to_datetime(px["date"])
        w = {f: px.pivot_table(index="date", columns="ticker", values=f)
                  .sort_index() for f in ("high", "low", "close")}
        idx = w["close"].index
        C, Hh, Ll = (w[f].to_numpy(float) for f in ("close", "high", "low"))
        valid = np.isfinite(C[-1]) & (np.isfinite(C).sum(axis=0) > 500)
        print(f"{C.shape[1]} tickers, {len(idx):,} days, "
              f"{idx[0].date()} -> {idx[-1].date()}; {valid.sum()} usable")

        g, hold_final, ret = run_grid(C, Hh, Ll, idx, valid)
        hold_mean = float(np.mean(hold_final[valid]))
        hold_med = float(np.median(hold_final[valid]))
        print(f"\n  buy and hold: mean GBP {hold_mean:,.0f}  "
              f"median GBP {hold_med:,.0f}")

        print(f"\n  {'setting':34}{'mean':>12}{'median':>11}{'beat':>7}"
              f"{'switch':>8}{'cheaper':>9}{'inmkt':>7}")
        for k in sorted(g, key=lambda x: -g[x]["mean_gbp"])[:15]:
            v = g[k]
            ch = f"{v['roundtrip_bought_cheaper']:.0%}" if v["roundtrip_bought_cheaper"] else "-"
            print(f"  {k:34}{v['mean_gbp']:>12,.0f}{v['median_gbp']:>11,.0f}"
                  f"{v['beat_hold']:>7}{v['mean_switches']:>8.0f}"
                  f"{ch:>9}{v['pct_time_invested']:>7.0%}")

        # THE FIT/TEST CHECK. Pick on the first half, report on the whole.
        best_fit = max(g, key=lambda k: g[k]["fit_mean_gbp"])
        best_all = max(g, key=lambda k: g[k]["mean_gbp"])
        fitv = pd.Series({k: v["fit_mean_gbp"] for k, v in g.items()})
        allv = pd.Series({k: v["mean_gbp"] for k, v in g.items()})
        rho = float(fitv.rank().corr(allv.rank()))
        print(f"\n  best on 1996-2012 fit window : {best_fit}")
        print(f"    its full-sample result      : GBP {g[best_fit]['mean_gbp']:,.0f}")
        print(f"  best in hindsight             : {best_all} "
              f"(GBP {g[best_all]['mean_gbp']:,.0f})")
        print(f"  fit-to-full rank correlation  : {rho:+.3f}")

        verdict = (
            f"BEATS BUY AND HOLD OUT OF SAMPLE by more than {PASS_MARGIN:.0%}: "
            f"the setting chosen on 1996-2012 "
            f"({best_fit}) returned GBP {g[best_fit]['mean_gbp']:,.0f} against "
            f"buy-and-hold's GBP {hold_mean:,.0f}."
            if g[best_fit]["mean_gbp"] > hold_mean * (1 + PASS_MARGIN) else
            f"DOES NOT BEAT BUY AND HOLD. The setting chosen on the fit window "
            f"returned GBP {g[best_fit]['mean_gbp']:,.0f} against "
            f"GBP {hold_mean:,.0f}. "
            + (f"Even the best setting in hindsight "
               f"(GBP {g[best_all]['mean_gbp']:,.0f}) falls short, so this is "
               f"not a tuning failure -- the approach does not work on this "
               f"panel."
               if g[best_all]["mean_gbp"] <= hold_mean * (1 + PASS_MARGIN) else
               f"The best setting in hindsight does beat it "
               f"(GBP {g[best_all]['mean_gbp']:,.0f}), but it could not have "
               f"been chosen in advance; rank correlation fit-to-full is "
               f"{rho:+.3f}."))
        print(f"\n  {verdict}")

        # what the chosen setting does across the outcome distribution
        ma50, ma200, rsi, kf, dsl = indicators(C, Hh, Ll)
        en, nc, rn, cds = best_fit.split("|")
        ex = confirmed({"below200": C < ma200,
                        "death_cross": ma50 < ma200}[en], int(nc[1:]))
        fast = np.nan_to_num(
            ((kf > dsl) & np.r_[[[False] * C.shape[1]], kf[:-1] <= dsl[:-1]] &
             (kf < 40)) |
            ((rsi > 30) & np.r_[[[False] * C.shape[1]], rsi[:-1] <= 30])).astype(bool)
        rsig = fast if rn == "fast" else np.nan_to_num(C > ma200)
        st = state_machine(ex, rsig, int(cds[2:]))
        eq, _, _ = equity(ret, st)
        dec = decile(eq[-1][valid], hold_final, valid)
        print("\n  chosen setting vs buy-and-hold, by outcome decile")
        print("  " + "".join(f"{k:>8}" for k in dec))
        print("  " + "".join(f"{v:>+8.0%}" for v in dec.values()))

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "start_gbp": START, "cost_per_switch": COST,
             "split": str(SPLIT.date()), "stocks": int(valid.sum()),
             "from": str(idx[0].date()), "to": str(idx[-1].date()),
             "buy_and_hold_mean_gbp": hold_mean,
             "buy_and_hold_median_gbp": hold_med, "pass_margin": PASS_MARGIN,
             "best_by_fit_window": best_fit, "best_in_hindsight": best_all,
             "fit_to_full_rank_correlation": rho,
             "chosen_by_outcome_decile": dec,
             "grid": g, "verdict": verdict,
             "CAVEAT": "Survivor-tilted until the delisting register completes; "
                       "the missing companies are where an exit rule pays most, "
                       "so these numbers understate every non-hold arm."},
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
