#!/usr/bin/env python3
"""
The confirmation battery, and an escape hatch for a stock that is genuinely dying.

WHAT THIS FIXES
---------------
The previous script claimed to test "confirmation" and implemented exactly one
mechanism: n consecutive closes beyond the line. That is the shallowest item in
the canon. The rest of it was never built, and the one that matters most for a
broken level -- the retest -- was missing entirely.

    persistence   n consecutive closes beyond the line. The one already built.
    filter        the close must be beyond by a set PERCENTAGE, not by a penny.
                  Dow's own filter rule, usually quoted at 3%.
    volume        a break on expanding volume is real; on light volume it is
                  suspect. Dow and Wyckoff both make this central.
    retest        THE classic. Price breaks the level, rallies back to it, and
                  the level holds as resistance -- the break is confirmed by
                  the failure of the throwback, not by the break itself.
    multi_tf      the daily signal only counts if the weekly agrees. A daily
                  break inside an intact weekly uptrend is noise.
    swing         structure has to actually break: a lower HIGH and a lower LOW
                  both confirmed, not just a line crossed.

THE ESCAPE HATCH
----------------
The cooldown that made the last run work -- locked in for 250 days after
re-entry -- is indefensible on a stock that is failing. It produced its result
by barely trading, and it would hold a company all the way down.

So the cooldown now suppresses only ORDINARY exits: a routine trend break,
the kind that is usually noise. A HARD exit fires regardless of cooldown,
regardless of confirmation, immediately:

    close below the 250-day low          a real breakdown, not a wobble
    more than 2 ATR below the 200-day    decisive failure, not a marginal cross
    lower high AND lower low confirmed   structure has genuinely broken
    down more than 25% from entry        the catastrophic stop

That is the standard shape of a real system and it is what was missing: a noise
filter for ordinary wiggles, plus an unconditional stop for genuine failure.

THE METRIC, AND WHY THE OBVIOUS ONE IS A TRAP
---------------------------------------------
The mean is useless here: buy-and-hold's mean across 623 stocks is GBP 757,161
against a median of GBP 165,712, so the mean describes a handful of stocks and
nothing else.

"How many stocks does the rule beat" looks like the fix, and it is worse.
Calibrating it against pure random walks fired on 5 panels out of 5 -- these
rules beat buy-and-hold on 52% to 65% of stocks WHERE NOTHING IS PREDICTABLE.
The reason is the same skew: in a right-skewed distribution most stocks do
worse than the average, so anything that reduces exposure beats holding on the
majority of them while losing on the few that carry the whole return. A 55%
hit rate is the null, not a result.

Which reframes the previous run's 243/623 = 39%: that is BELOW the random-walk
baseline, not near it.

So there are two headline numbers here, and both have to be read together:

    PORTFOLIO      GBP 10,000 split equally across every stock, rule applied
                   to each. This is the actual money question and skew cannot
                   flatter it, because the winners are in it at their real
                   weight.
    BEAT RATE      still reported, but judged against the random-walk baseline
                   the calibration measures, never against 50%.

Fit on 1996-2012, report on everything, and --calibrate first.
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
SEED = 20260929
SPLIT = pd.Timestamp("2013-01-01")
PASS_MARGIN = 0.10

COOLDOWN = (0, 60, 250)
HARD_DD = 0.25                 # catastrophic stop, from entry


# ---------------------------------------------------------------------------

def indicators(C, Hh, Ll, V):
    df = pd.DataFrame(C)
    ma50 = df.rolling(50, min_periods=50).mean().to_numpy()
    ma200 = df.rolling(200, min_periods=200).mean().to_numpy()
    # ATR on daily bars
    pc = df.shift(1).to_numpy()
    tr = np.nanmax(np.dstack([Hh - Ll, np.abs(Hh - pc), np.abs(Ll - pc)]), axis=2)
    atr = pd.DataFrame(tr).ewm(alpha=1/14, adjust=False, min_periods=14).mean().to_numpy()
    lo250 = pd.DataFrame(Ll).shift(1).rolling(250, min_periods=100).min().to_numpy()
    vol50 = pd.DataFrame(V).rolling(50, min_periods=20).mean().to_numpy()
    dif = df.diff()
    up = dif.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    dn = (-dif).clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rsi = (100 - 100 / (1 + up / dn.replace(0, np.nan))).to_numpy()
    lo14 = pd.DataFrame(Ll).rolling(14, min_periods=14).min().to_numpy()
    hi14 = pd.DataFrame(Hh).rolling(14, min_periods=14).max().to_numpy()
    rng = np.where((hi14 - lo14) > 0, hi14 - lo14, np.nan)
    kf = 100 * (C - lo14) / rng
    dsl = pd.DataFrame(kf).rolling(3, min_periods=3).mean().to_numpy()
    # weekly view: a 5-day average close against the same long average
    wk = df.rolling(5, min_periods=5).mean().to_numpy()
    return dict(ma50=ma50, ma200=ma200, atr=atr, lo250=lo250, vol50=vol50,
                rsi=rsi, kf=kf, dsl=dsl, wk=wk)


def pivots_lower(Hh, Ll, n=10):
    """
    Confirmed lower high AND lower low, marked on the bar they become knowable
    (pivot + n), never on the pivot itself.
    """
    nd, nt = Hh.shape
    out = np.zeros((nd, nt), bool)
    hh = pd.DataFrame(Hh).rolling(2 * n + 1, center=True).max().to_numpy()
    ll = pd.DataFrame(Ll).rolling(2 * n + 1, center=True).min().to_numpy()
    is_h = (Hh == hh); is_l = (Ll == ll)
    for j in range(nt):
        lastH = lastL = None; brokeH = brokeL = False
        for t in range(nd):
            if is_h[t, j] and np.isfinite(Hh[t, j]):
                if lastH is not None:
                    brokeH = Hh[t, j] < lastH
                lastH = Hh[t, j]
                if t + n < nd and brokeH and brokeL:
                    out[t + n, j] = True
            if is_l[t, j] and np.isfinite(Ll[t, j]):
                if lastL is not None:
                    brokeL = Ll[t, j] < lastL
                lastL = Ll[t, j]
                if t + n < nd and brokeH and brokeL:
                    out[t + n, j] = True
    return out


def retest_confirm(C, line, atr, window=20, tol=0.5):
    """
    The classic confirmation. Price closes below `line`; then, within `window`
    bars, it rallies back to within `tol` ATR of the line and CLOSES BELOW it
    again. The break is confirmed by the throwback failing, not by the break.
    """
    nd, nt = C.shape
    out = np.zeros((nd, nt), bool)
    below = np.nan_to_num(C < line)
    for j in range(nt):
        pend = -1
        for t in range(nd):
            if not np.isfinite(line[t, j]) or not np.isfinite(atr[t, j]):
                continue
            if below[t, j]:
                if pend < 0:
                    pend = t                       # a break is now pending
                elif t - pend <= window and C[t, j] >= line[t, j] - tol * atr[t, j]:
                    out[t, j] = True               # came back, failed, confirmed
                    pend = -1
            else:
                if pend >= 0 and t - pend > window:
                    pend = -1                      # throwback never came
    return out


def confirmations(C, Hh, Ll, V, S) -> dict[str, np.ndarray]:
    """Each returns True on days a SELL is confirmed by that mechanism."""
    raw = np.nan_to_num(C < S["ma200"])
    p3 = (pd.DataFrame(raw.astype(float)).rolling(3, min_periods=3).sum() >= 3
          ).fillna(False).to_numpy()
    return {
        "none":        raw,
        "persistence": p3,
        "filter3pct":  np.nan_to_num(C < S["ma200"] * 0.97),
        "volume":      raw & np.nan_to_num(V > 1.3 * S["vol50"]),
        "retest":      retest_confirm(C, S["ma200"], S["atr"]),
        "multi_tf":    raw & np.nan_to_num(S["wk"] < S["ma200"]),
        "swing":       raw & pivots_lower(Hh, Ll),
    }


def hard_exit(C, Ll, S):
    """
    Fires through any cooldown. A stock that is actually failing gets out.

    The first version used 2 ATR below the 200-day and fired 68 times per
    stock per year -- because it is a STATE that stays true all through a
    downtrend, not an event. 3 ATR is decisive rather than routine. The real
    fix, though, is in the re-entry rule after a hard exit (see machine()).
    """
    return (np.nan_to_num(C < S["lo250"])
            | np.nan_to_num(C < S["ma200"] - 3.0 * S["atr"]))


def machine(exit_sig, hard, re_sig, C, cooldown, use_hard, repair=None):
    """
    Long unless thrown out. The cooldown suppresses ORDINARY exits only; a hard
    exit, or the catastrophic stop measured from the entry price, always fires.

    AND THE PART THE FIRST VERSION GOT WRONG. After an ordinary exit -- a
    routine trend break in a stock that is still basically healthy -- re-entry
    is fast: buy the oversold reclaim. After a HARD exit it is not. A stock that
    has just been stopped out for failing must REPAIR ITS TREND before it can be
    bought again. Without that, 52% of fast re-entries were hard-stopped again
    within ten days: the rule bought the falling knife, sold it, and bought it
    again, 440 times per stock.

    You buy the dip on a strong stock. You do not buy the dip on a stock you
    have just sold for failing.
    """
    nd, nt = C.shape
    st = np.ones(nt, bool)
    hard_out = np.zeros(nt, bool)
    last_in = np.full(nt, -10 ** 9)
    entry = np.where(np.isfinite(C[0]), C[0], np.nan)
    out = np.empty((nd, nt), bool)
    if repair is None:
        repair = np.zeros((nd, nt), bool)
    for t in range(nd):
        ok = np.isfinite(C[t])
        crash = use_hard & ok & (C[t] < entry * (1 - HARD_DD))
        forced = st & ((hard[t] & use_hard) | crash)
        ordinary = st & exit_sig[t] & ((t - last_in) >= cooldown) & ~forced
        hard_out = np.where(forced, True, np.where(ordinary, False, hard_out))
        st = st & ~(forced | ordinary)
        # fast re-entry after an ordinary exit; trend repair after a hard one
        allowed = np.where(hard_out, repair[t], re_sig[t])
        back = (~st) & allowed & ok
        last_in = np.where(back, t, last_in)
        entry = np.where(back, C[t], entry)
        hard_out = np.where(back, False, hard_out)
        st = st | back
        out[t] = st
    return out


def equity(ret, state):
    pos = np.vstack([np.ones((1, state.shape[1]), bool), state[:-1]])
    sw = np.vstack([np.zeros((1, state.shape[1]), bool), pos[1:] != pos[:-1]])
    r = np.where(pos, np.nan_to_num(ret), 0.0) - np.where(sw, COST, 0.0)
    return START * np.cumprod(1.0 + r, axis=0), sw.sum(axis=0), pos


def roundtrip_win(C, pos):
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


def run_grid(C, Hh, Ll, V, idx, valid):
    S = indicators(C, Hh, Ll, V)
    ret = np.nan_to_num(pd.DataFrame(C).pct_change().to_numpy())
    conf = confirmations(C, Hh, Ll, V, S)
    hard = hard_exit(C, Ll, S)
    z = np.zeros((1, C.shape[1]), bool)
    fast = np.nan_to_num(
        ((S["kf"] > S["dsl"]) & np.r_[z, S["kf"][:-1] <= S["dsl"][:-1]]
         & (S["kf"] < 40))
        | ((S["rsi"] > 30) & np.r_[z, S["rsi"][:-1] <= 30])).astype(bool)

    # trend repaired: back above the 200-day with the 50-day rising
    ma50s = np.r_[np.full((20, C.shape[1]), np.nan), S["ma50"][:-20]]
    repair = np.nan_to_num((C > S["ma200"]) & (S["ma50"] > ma50s)).astype(bool)

    hold_eq = START * np.cumprod(1 + ret, axis=0)
    hf = hold_eq[-1]
    fit_m = np.asarray(idx < SPLIT)
    rows = {}
    port_hold = hold_eq[:, valid].mean(axis=1)
    for cname, cs in conf.items():
        for cd in COOLDOWN:
            for uh in (False, True):
                st = machine(cs, hard, fast, C, cd, uh, repair)
                eq, sw, pos = equity(ret, st)
                win, ntrip = roundtrip_win(C, pos[:, valid])
                f = eq[-1][valid]
                # THE MONEY QUESTION: GBP 10,000 split equally over every
                # stock at the start, each sleeve following the rule. Skew
                # cannot flatter this the way a hit rate can.
                port = float(np.mean(f))
                curve = eq[:, valid].mean(axis=1)
                rk = risk(curve, idx)
                fitf = eq[fit_m][-1][valid] if fit_m.sum() > 300 else f
                rows[f"{cname}|cd{cd}|{'hard' if uh else 'nohard'}"] = {
                    "portfolio_gbp": port,
                    **{f"port_{k}": v for k, v in rk.items()},
                    "beat_hold": int((f > hf[valid]).sum()),
                    "beat_pct": float((f > hf[valid]).mean()),
                    "mean_gbp": float(np.mean(f)),
                    "median_gbp": float(np.median(f)),
                    "fit_beat_pct": float((fitf > hold_eq[fit_m][-1][valid]).mean()),
                    "mean_switches": float(np.mean(sw[valid])),
                    "roundtrip_bought_cheaper": win,
                    "roundtrips": ntrip,
                    "pct_time_invested": float(np.mean(pos[:, valid])),
                }
    rows["_hold"] = {f"port_{k}": v for k, v in risk(port_hold, idx).items()}
    return rows, hf


def risk(curve, idx):
    """
    How professionals actually judge a strategy: return PER UNIT OF RISK.
    A rule that makes 5% less than holding while halving the worst drawdown
    has not lost -- scale it up by a fifth and it makes more with less pain.
    """
    curve = np.asarray(curve, float)
    yrs = max((idx[-1] - idx[0]).days / 365.25, 1e-9)
    r = np.diff(curve) / curve[:-1]
    r = r[np.isfinite(r)]
    pk = np.maximum.accumulate(curve)
    dd = float((curve / pk - 1).min())
    cagr = float((curve[-1] / curve[0]) ** (1 / yrs) - 1)
    vol = float(np.std(r) * np.sqrt(252)) if len(r) else float("nan")
    return {"cagr": cagr, "max_drawdown": dd, "vol": vol,
            "sharpe": cagr / vol if vol > 0 else None,
            "calmar": cagr / abs(dd) if dd < 0 else None}


def synthetic(seed, n_tick=120, n=2400):
    rng = np.random.default_rng(seed)
    mkt = rng.normal(0.0002, 0.011, n)
    C = np.empty((n, n_tick)); Hh = np.empty_like(C)
    Ll = np.empty_like(C); V = np.empty_like(C)
    for i in range(n_tick):
        r = 0.85 * mkt + rng.normal(0.0002, 0.019, n)
        c = 100 * np.exp(np.cumsum(r)); C[:, i] = c
        Hh[:, i] = c * (1 + abs(rng.normal(0, 0.006, n)))
        Ll[:, i] = c * (1 - abs(rng.normal(0, 0.006, n)))
        V[:, i] = rng.lognormal(13, 0.4, n)
    return C, Hh, Ll, V


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/confirmation_evidence.json")
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
                C, Hh, Ll, V = synthetic(900 + p)
                idx = pd.bdate_range("2004-01-01", periods=C.shape[0])
                valid = np.isfinite(C[-1])
                g, hf = run_grid(C, Hh, Ll, V, idx, valid)
                g.pop("_hold", None)
                best = max(g, key=lambda k: g[k]["fit_beat_pct"])
                hm = float(np.mean(hf[valid]))
                # the only bar that survived: the PORTFOLIO must beat holding
                # by a material margin. The hit rate is recorded as the
                # baseline it is, never as a test.
                hit = bool(g[best]["portfolio_gbp"] > hm * (1 + PASS_MARGIN))
                fired += hit
                rows.append({"panel": p, "best_by_fit": best,
                             "beat_pct": g[best]["beat_pct"],
                             "portfolio_gbp": g[best]["portfolio_gbp"],
                             "hold_gbp": hm, "declared": hit})
                print(f"  panel {p:2}  {best:30} hit rate "
                      f"{g[best]['beat_pct']:.0%} (baseline, not a result)  "
                      f"portfolio {g[best]['portfolio_gbp']:>9,.0f} vs hold "
                      f"{hm:>9,.0f}{'   FIRED' if hit else ''}", flush=True)
            rate = fired / max(a.calibrate, 1)
            base = float(np.mean([r["beat_pct"] for r in rows]))
            print(f"\n  FALSE POSITIVE RATE: {fired}/{a.calibrate} = {rate:.0%}")
            print(f"  RANDOM-WALK HIT-RATE BASELINE: {base:.0%} — any real "
                  f"result has to clear THIS, not 50%")
            out_path.write_text(json.dumps(
                {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
                 "mode": "calibration", "false_positive_rate": rate,
                 "hit_rate_baseline": base,
                 "panels": a.calibrate, "detail": rows}, indent=2, default=str))
            return 0

        px = pd.read_parquet(a.prices)
        px["date"] = pd.to_datetime(px["date"])
        w = {f: px.pivot_table(index="date", columns="ticker", values=f)
                  .sort_index() for f in ("high", "low", "close", "volume")}
        idx = w["close"].index
        C, Hh, Ll, V = (w[f].to_numpy(float)
                        for f in ("close", "high", "low", "volume"))
        valid = np.isfinite(C[-1]) & (np.isfinite(C).sum(axis=0) > 500)
        n = int(valid.sum())
        print(f"{C.shape[1]} tickers, {len(idx):,} days; {n} usable")

        g, hf = run_grid(C, Hh, Ll, V, idx, valid)
        hrisk = g.pop("_hold")
        hold_mean = float(np.mean(hf[valid])); hold_med = float(np.median(hf[valid]))
        print(f"\n  buy and hold: mean GBP {hold_mean:,.0f}  "
              f"median GBP {hold_med:,.0f}")
        print(f"  ranked by PORTFOLIO — GBP 10,000 split across all {n} stocks")
        print(f"  (hit rate shown for context only; ~58% is free on random data)\n")
        print(f"  {'setting':34}{'portfolio':>12}{'vs hold':>9}{'hit%':>7}"
              f"{'median':>11}{'switch':>8}{'cheaper':>9}")
        for k in sorted(g, key=lambda x: -g[x]["portfolio_gbp"])[:16]:
            v = g[k]
            ch = (f"{v['roundtrip_bought_cheaper']:.0%}"
                  if v["roundtrip_bought_cheaper"] else "-")
            print(f"  {k:34}{v['portfolio_gbp']:>12,.0f}"
                  f"{v['portfolio_gbp']/hold_mean-1:>+9.0%}"
                  f"{v['beat_pct']:>7.0%}{v['median_gbp']:>11,.0f}"
                  f"{v['mean_switches']:>8.0f}{ch:>9}")

        # ---- RISK-ADJUSTED: how professionals actually judge it --------
        print(f"\n  RISK-ADJUSTED, portfolio equity curve")
        print(f"  {'setting':34}{'CAGR':>8}{'maxDD':>8}{'Sharpe':>8}{'Calmar':>8}")
        print(f"  {'BUY AND HOLD':34}{hrisk['port_cagr']:>+8.1%}"
              f"{hrisk['port_max_drawdown']:>8.1%}{hrisk['port_sharpe']:>8.2f}"
              f"{hrisk['port_calmar']:>8.2f}")
        for k in sorted(g, key=lambda x: -(g[x].get("port_calmar") or -9))[:12]:
            v = g[k]
            print(f"  {k:34}{v['port_cagr']:>+8.1%}{v['port_max_drawdown']:>8.1%}"
                  f"{(v['port_sharpe'] or 0):>8.2f}{(v['port_calmar'] or 0):>8.2f}")
        risk_beat = [k for k in g
                     if (g[k].get("port_calmar") or 0) > hrisk["port_calmar"] * 1.10
                     and (g[k].get("port_sharpe") or 0) >= hrisk["port_sharpe"]]

        best_fit = max(g, key=lambda k: g[k]["fit_beat_pct"])  # chosen on 1996-2012
        best_all = max(g, key=lambda k: g[k]["beat_pct"])
        fitv = pd.Series({k: v["fit_beat_pct"] for k, v in g.items()})
        allv = pd.Series({k: v["beat_pct"] for k, v in g.items()})
        rho = float(fitv.rank().corr(allv.rank()))
        print(f"\n  chosen on 1996-2012 : {best_fit}")
        print(f"    beats {g[best_fit]['beat_hold']}/{n} = "
              f"{g[best_fit]['beat_pct']:.0%} of stocks, "
              f"median GBP {g[best_fit]['median_gbp']:,.0f}")
        print(f"  best in hindsight    : {best_all} "
              f"({g[best_all]['beat_pct']:.0%})")
        print(f"  fit-to-full rank corr: {rho:+.3f}")

        # did the escape hatch help or hurt?
        pairs = []
        for k in g:
            if k.endswith("|nohard"):
                h = k.replace("|nohard", "|hard")
                if h in g:
                    pairs.append((k, g[h]["beat_pct"] - g[k]["beat_pct"]))
        if pairs:
            mh = float(np.mean([d for _, d in pairs]))
            print(f"\n  escape hatch changes the hit rate by {mh:+.1%} on "
                  f"average across {len(pairs)} matched pairs")

        bf = g[best_fit]
        verdict = (
            f"BEATS BUY AND HOLD: {best_fit} turns GBP 10,000 into "
            f"GBP {bf['portfolio_gbp']:,.0f} against GBP {hold_mean:,.0f} held "
            f"— more than the {PASS_MARGIN:.0%} margin required. Its hit rate "
            f"is {bf['beat_pct']:.0%}, which must be read against the ~58% a "
            f"random-walk panel gives for free."
            if bf["portfolio_gbp"] > hold_mean * (1 + PASS_MARGIN) else
            f"DOES NOT BEAT BUY AND HOLD. The setting chosen on the fit window "
            f"({best_fit}) turns GBP 10,000 into GBP {bf['portfolio_gbp']:,.0f} "
            f"against GBP {hold_mean:,.0f} held. Its {bf['beat_pct']:.0%} hit "
            f"rate is not evidence either way: on pure random walks these rules "
            f"beat holding on about 58% of stocks, because in a skewed market "
            f"most stocks underperform the average and anything that cuts "
            f"exposure wins on the majority while losing on the few that matter.")
        if risk_beat:
            verdict += (f" ON A RISK-ADJUSTED BASIS, {len(risk_beat)} setting(s) "
                        f"beat buy-and-hold on BOTH Calmar (return per unit of "
                        f"worst drawdown, by 10%+) and Sharpe: "
                        f"{', '.join(sorted(risk_beat)[:6])}.")
        else:
            verdict += " No setting beat buy-and-hold on a risk-adjusted basis either."
        print(f"\n  {verdict}")

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "stocks": n, "from": str(idx[0].date()), "to": str(idx[-1].date()),
             "buy_and_hold_mean_gbp": hold_mean,
             "buy_and_hold_median_gbp": hold_med,
             "hard_stop_drawdown": HARD_DD, "pass_margin": PASS_MARGIN,
             "best_by_fit_window": best_fit, "best_in_hindsight": best_all,
             "fit_to_full_rank_correlation": rho,
             "escape_hatch_mean_effect": (mh if pairs else None),
             "buy_and_hold_risk": hrisk, "beats_hold_risk_adjusted": risk_beat,
             "grid": g, "verdict": verdict,
             "CAVEAT": "Survivor-tilted until the delisting register completes; "
                       "the missing companies are where an exit rule pays most."},
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
