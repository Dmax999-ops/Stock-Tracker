#!/usr/bin/env python3
"""
Trend rules where they are actually used: indices, sectors and bonds.

WHY THE TERRAIN CHANGES
-----------------------
Six weeks of single-stock testing kept failing for reasons that had nothing to
do with technical analysis: survivorship, look-ahead in index membership (worth
4% a year to buy-and-hold and 10% a year to momentum), recycled tickers and bad
prints. Every fix exposed another data problem.

Professional trend-followers do not trade 600 single stocks. They apply exactly
these rules -- 200-day filters, momentum, confirmation -- to indices, sectors and
bonds. The data is clean: an ETF never delists, never gets recycled, and never
joins an index with hindsight. And every instrument here can actually be bought.

THE MISTAKE EVERY FILTER SO FAR MADE
------------------------------------
When the market filter got out of 2000-02 and 2008, the money earned 2% in
cash. In those same crashes government bonds RALLIED. The documented way trend
rules beat buy-and-hold on return, not only on risk, is to rotate into
Treasuries when the equity trend breaks. Not one test in this repo did that.

THE ARMS (all decisions at month end, traded next day, 10bp per switch)
-----------------------------------------------------------------------
    spy_hold          buy and hold the S&P 500. The benchmark.
    spy_200_cash      S&P when above its 200-day, else cash (T-bills)
    spy_200_bonds     S&P when above its 200-day, else Treasuries
    spy_absmom        S&P when its 12-month return beats cash, else Treasuries
                      (absolute momentum)
    gem               if absolute momentum is positive, whichever of US or
                      international is stronger over 12 months; else Treasuries
                      (dual momentum)
    sect_top3         the three strongest of the nine original sector funds,
                      always invested (relative momentum at industry level)
    sect_top3_bonds   the same, but Treasuries when the S&P is below its 200-day
                      (industry momentum + market filter + no idle cash)
    sect_top3_conf    the same, but the market exit is checked DAILY and needs
                      three consecutive closes below the 200-day to fire --
                      confirmation from the technical canon -- while re-entry
                      waits for month end
    sect_trend        every sector above its OWN 200-day, equal weight; the
                      share of sectors in downtrends goes to Treasuries
                      (industry-by-industry filter)
    walkforward       every January, pick whichever of the arms above had the
                      best return-per-drawdown over the previous five years --
                      using ONLY past data -- and run it for the year. The
                      reported result is the stitched real-time record: the
                      system improving itself without ever seeing the future.

THE BAR
-------
Beat the S&P 500 by 1% a year AND on Calmar (return per unit of worst drawdown),
in 1999-2012 AND in 2013 onwards, separately. --calibrate runs everything on
random walks first; nothing is believed until that comes back near zero.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

START = 10_000.0
COST = 0.0010                 # per switch, ETF spread + commission, generous
SPLIT = pd.Timestamp("2013-01-01")
CAGR_MARGIN = 0.01
CALMAR_MULT = 1.10
# A FIXED MARGIN IS NOT ENOUGH. A three-sector portfolio wanders a long way from
# the S&P 500 by chance alone, so over a 13-year half it beat it by 1% a year on
# 3 random-walk panels in 8. The lead has to be large relative to how noisy the
# strategy is against the benchmark: excess return divided by its standard error
# (tracking error over the square root of the years) must exceed T_BAR in EACH
# half. That is the information-ratio test professionals use.
T_BAR = 2.0
WF_LOOKBACK_YEARS = 5

SECTORS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB"]
EQUITY = "SPY"
INTL = "EFA"
INTL_FALLBACK = "VGTSX"       # Vanguard Total International, pre-2001
BONDS = "VFITX"               # Vanguard Intermediate Treasury fund, from 1991
CASH_YIELD = "^IRX"           # 13-week T-bill yield


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

def download(start: str) -> tuple[pd.DataFrame, pd.Series]:
    import yfinance as yf
    tickers = [EQUITY, INTL, INTL_FALLBACK, BONDS] + SECTORS
    px = {}
    for t in tickers:
        d = yf.download(t, start=start, auto_adjust=True, progress=False,
                        threads=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        if len(d):
            px[t] = d["Close"].astype(float)
            print(f"  {t:6} {len(d):5,} days  {d.index[0].date()} -> {d.index[-1].date()}")
        else:
            print(f"  {t:6} NO DATA")
    P = pd.DataFrame(px).sort_index()
    y = yf.download(CASH_YIELD, start=start, progress=False, threads=False)
    if isinstance(y.columns, pd.MultiIndex):
        y.columns = y.columns.get_level_values(0)
    irx = y["Close"].astype(float).reindex(P.index).ffill().fillna(2.0)
    # splice international: the fallback fund until EFA exists
    if INTL in P and INTL_FALLBACK in P:
        r = P[INTL].pct_change()
        rf = P[INTL_FALLBACK].pct_change()
        spliced = r.where(P[INTL].notna(), rf)
        P["INTL"] = (1 + spliced.fillna(0)).cumprod()
        P.loc[P[INTL].isna() & P[INTL_FALLBACK].isna(), "INTL"] = np.nan
    elif INTL in P:
        P["INTL"] = P[INTL]
    return P, irx


# ---------------------------------------------------------------------------
# the engine
# ---------------------------------------------------------------------------

def month_ends(idx: pd.DatetimeIndex) -> np.ndarray:
    s = pd.Series(np.arange(len(idx)), index=idx)
    return s.groupby([idx.year, idx.month]).max().to_numpy()


def run_arm(P, irx, decide, daily_override=None):
    """
    `decide(i)` returns target weights {asset: w} on month-end bar i, using only
    data up to and including bar i. Weights are applied from bar i+1. Assets are
    column names of P, or "CASH". `daily_override(i, w)` may change the weights
    on any day (used for confirmed intra-month exits).
    """
    R = P.pct_change()
    cash_r = (irx / 100.0 / 252.0).to_numpy()
    me = set(month_ends(P.index).tolist())
    n = len(P)
    eq = np.empty(n)
    v = START
    w = {"CASH": 1.0}
    started = False
    for i in range(n):
        if i > 0:
            day = 0.0
            for a, x in w.items():
                if a == "CASH":
                    day += x * cash_r[i]
                else:
                    ri = R[a].iat[i]
                    day += x * (0.0 if not np.isfinite(ri) else ri)
            v *= 1 + day
        new = None
        if i in me:
            new = decide(i)
            if new is not None:
                started = True
        if daily_override is not None and started:
            o = daily_override(i, new if new is not None else w)
            if o is not None:
                new = o
        if new is not None and new != w:
            turn = sum(abs(new.get(k, 0) - w.get(k, 0)) for k in set(new) | set(w))
            v *= 1 - COST * turn / 2
            w = new
        eq[i] = v if started else START
    return pd.Series(eq, index=P.index)


def build_arms(P, irx):
    C = P
    ma200 = C.rolling(200, min_periods=200).mean()
    cash_lvl = (1 + irx / 100.0 / 252.0).cumprod()

    def ret_n(col, i, n):
        if i - n < 0:
            return np.nan
        a, b = C[col].iat[i - n], C[col].iat[i]
        return b / a - 1 if np.isfinite(a) and np.isfinite(b) and a > 0 else np.nan

    def cash_n(i, n):
        return cash_lvl.iat[i] / cash_lvl.iat[i - n] - 1 if i - n >= 0 else np.nan

    def ok(col, i):
        return col in C and np.isfinite(C[col].iat[i]) and np.isfinite(ma200[col].iat[i])

    def bond_or_cash(i):
        return {BONDS: 1.0} if ok(BONDS, i) else {"CASH": 1.0}

    def safe_haven(i):
        """
        The first run's worst year for the bond-rotation rule was 2022, when
        rising rates crashed bonds AND stocks together. Rotating blindly into
        bonds has the same flaw as rotating blindly into stocks. So the safe
        haven is itself trend-checked: Treasuries only while Treasuries are
        above their own 200-day average; otherwise T-bills.
        """
        if ok(BONDS, i) and C[BONDS].iat[i] > ma200[BONDS].iat[i]:
            return {BONDS: 1.0}
        return {"CASH": 1.0}

    def spy_up(i):
        return C[EQUITY].iat[i] > ma200[EQUITY].iat[i]

    def mom_score(col, i):
        xs = [ret_n(col, i, n) for n in (63, 126, 252)]
        xs = [x for x in xs if np.isfinite(x)]
        return np.mean(xs) if len(xs) == 3 else np.nan

    def ready(i):
        return ok(EQUITY, i)

    arms = {}
    arms["spy_hold"] = lambda i: {EQUITY: 1.0} if np.isfinite(C[EQUITY].iat[i]) else None
    arms["spy_200_cash"] = lambda i: (None if not ready(i) else
                                      ({EQUITY: 1.0} if spy_up(i) else {"CASH": 1.0}))
    arms["spy_200_bonds"] = lambda i: (None if not ready(i) else
                                       ({EQUITY: 1.0} if spy_up(i) else bond_or_cash(i)))

    def absmom(i):
        if not ready(i):
            return None
        r12 = ret_n(EQUITY, i, 252)
        return {EQUITY: 1.0} if r12 > cash_n(i, 252) else bond_or_cash(i)
    arms["spy_absmom"] = absmom

    def gem(i):
        if not ready(i) or "INTL" not in C:
            return None
        r_us, r_in = ret_n(EQUITY, i, 252), ret_n("INTL", i, 252)
        if not (r_us > cash_n(i, 252)):
            return bond_or_cash(i)
        if np.isfinite(r_in) and r_in > r_us:
            return {"INTL": 1.0}
        return {EQUITY: 1.0}
    arms["gem"] = gem

    def top3(i, filt):
        if not ready(i):
            return None
        if filt and not spy_up(i):
            return bond_or_cash(i)
        sc = {s: mom_score(s, i) for s in SECTORS if s in C}
        sc = {k: v for k, v in sc.items() if np.isfinite(v)}
        if len(sc) < 5:
            return None
        pick = sorted(sc, key=sc.get, reverse=True)[:3]
        return {s: 1 / 3 for s in pick}
    arms["sect_top3"] = lambda i: top3(i, False)
    arms["sect_top3_bonds"] = lambda i: top3(i, True)

    def sect_trend(i):
        if not ready(i):
            return None
        live = [s for s in SECTORS if ok(s, i)]
        if len(live) < 5:
            return None
        up = [s for s in live if C[s].iat[i] > ma200[s].iat[i]]
        w = {s: 1 / len(live) for s in up}
        rest = 1 - sum(w.values())
        if rest > 1e-9:
            b = bond_or_cash(i)
            for k in b:
                w[k] = w.get(k, 0) + rest
        return w
    arms["sect_trend"] = sect_trend

    arms["spy_200_safe"] = lambda i: (None if not ready(i) else
                                      ({EQUITY: 1.0} if spy_up(i) else safe_haven(i)))

    def top3_safe(i):
        if not ready(i):
            return None
        if not spy_up(i):
            return safe_haven(i)
        return top3(i, False)
    arms["sect_top3_safe"] = top3_safe

    def blend(i):
        """Half the market filter, half the sector rotation: two different
        routes to the same idea, so neither's bad year is the portfolio's."""
        a, b = arms["spy_200_safe"](i), top3_safe(i)
        if a is None or b is None:
            return None
        w = {}
        for part in (a, b):
            for k, x in part.items():
                w[k] = w.get(k, 0) + 0.5 * x
        return w
    arms["blend_safe"] = blend

    # confirmation: exit checked DAILY, needs 3 closes below the 200-day
    below = (C[EQUITY] < ma200[EQUITY]).astype(float)
    conf3 = (below.rolling(3).sum() >= 3).to_numpy()

    def override(i, w):
        if conf3[i] and any(k in SECTORS or k == EQUITY for k in w):
            return bond_or_cash(i)
        return None
    arms["sect_top3_conf"] = (lambda i: top3(i, True), override)
    return arms


def risk(eq: pd.Series) -> dict:
    eq = eq.dropna()
    if len(eq) < 50 or eq.iloc[0] <= 0:
        return {}
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    r = eq.pct_change().dropna()
    pk = eq.cummax()
    dd = float((eq / pk - 1).min())
    cagr = float((eq.iloc[-1] / eq.iloc[0]) ** (1 / yrs) - 1)
    vol = float(r.std() * np.sqrt(252))
    yearly = eq.resample("YE").last().pct_change().dropna()
    return {"final_gbp": float(START * eq.iloc[-1] / eq.iloc[0]),
            "cagr": cagr, "max_drawdown": dd, "vol": vol,
            "sharpe": cagr / vol if vol > 0 else None,
            "calmar": cagr / abs(dd) if dd < 0 else None,
            "worst_year": float(yearly.min()) if len(yearly) else None}


def walkforward(curves: dict[str, pd.Series], start_year: int) -> tuple[pd.Series, list]:
    """
    Each January, choose the arm with the best Calmar over the previous
    WF_LOOKBACK_YEARS using only data before that January, then hold it for the
    year. Stitch the years. This is the only arm here whose rule-choice was
    never made with hindsight.
    """
    cands = {k: v for k, v in curves.items() if k != "spy_hold"}
    rets = {k: v.pct_change().fillna(0.0) for k, v in cands.items()}
    idx = next(iter(curves.values())).index
    out = pd.Series(np.nan, index=idx)
    choices = []
    last_year = idx[-1].year
    level = START
    for y in range(start_year, last_year + 1):
        t0 = pd.Timestamp(f"{y}-01-01")
        lb0 = pd.Timestamp(f"{y - WF_LOOKBACK_YEARS}-01-01")
        best, bestc = None, -np.inf
        for k, r in rets.items():
            hist = r[(r.index >= lb0) & (r.index < t0)]
            if len(hist) < 200 * WF_LOOKBACK_YEARS:
                continue
            m = risk((1 + hist).cumprod())
            c = m.get("calmar")
            if c is not None and c > bestc:
                best, bestc = k, c
        if best is None:
            continue
        yr = rets[best][(rets[best].index >= t0) & (rets[best].index < pd.Timestamp(f"{y+1}-01-01"))]
        if not len(yr):
            continue
        path = level * (1 + yr).cumprod()
        out.loc[path.index] = path.to_numpy()
        level = float(path.iloc[-1])
        choices.append({"year": y, "chosen": best, "trailing_calmar": float(bestc)})
    return out.dropna(), choices


def evaluate(P, irx):
    arms = build_arms(P, irx)
    curves = {}
    for name, spec in arms.items():
        if isinstance(spec, tuple):
            curves[name] = run_arm(P, irx, spec[0], spec[1])
        else:
            curves[name] = run_arm(P, irx, spec)
    # common start: once every sector fund and the 200-day exist
    starts = []
    for name, eq in curves.items():
        moved = eq[eq != START]
        if len(moved):
            starts.append(moved.index[0])
    t0 = max(starts)
    curves = {k: v[v.index >= t0] for k, v in curves.items()}
    wf, choices = walkforward(curves, t0.year + WF_LOOKBACK_YEARS)
    return curves, wf, choices, t0


def windows(eq: pd.Series) -> dict:
    return {"full": risk(eq),
            "first_half": risk(eq[eq.index < SPLIT]),
            "second_half": risk(eq[eq.index >= SPLIT])}


def excess_t(eq: pd.Series, bench_eq: pd.Series) -> float:
    """Annualised excess return over its own standard error."""
    j = eq.index.intersection(bench_eq.index)
    if len(j) < 500:
        return float("nan")
    ra = eq.loc[j].pct_change().dropna()
    rb = bench_eq.loc[j].pct_change().dropna()
    d = (ra - rb).dropna()
    yrs = len(d) / 252
    te = float(d.std() * np.sqrt(252))
    ex = float(d.mean() * 252)
    return ex / (te / np.sqrt(yrs)) if te > 0 else float("nan")


def split(eq, key):
    if key == "first_half":
        return eq[eq.index < SPLIT]
    if key == "second_half":
        return eq[eq.index >= SPLIT]
    return eq


def passes(res, bench, key, eq=None, bench_eq=None):
    a, b = res.get(key, {}), bench.get(key, {})
    if not a or not b:
        return False
    ok = (a["cagr"] > b["cagr"] + CAGR_MARGIN
          and (a.get("calmar") or 0) > (b.get("calmar") or 0) * CALMAR_MULT)
    if ok and eq is not None and bench_eq is not None:
        t = excess_t(split(eq, key), split(bench_eq, key))
        ok = bool(np.isfinite(t) and t > T_BAR)
    return ok


# ---------------------------------------------------------------------------
# calibration
# ---------------------------------------------------------------------------

def synthetic(seed, n=6800):
    """Equity, sectors, international and bonds as random walks. Nothing to find."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("1998-01-02", periods=n)
    mkt = rng.normal(0.0003, 0.012, n)
    P = {}
    P[EQUITY] = 100 * np.exp(np.cumsum(mkt))
    P["INTL"] = 100 * np.exp(np.cumsum(0.8 * mkt + rng.normal(0.0001, 0.008, n)))
    P[BONDS] = 100 * np.exp(np.cumsum(rng.normal(0.00018, 0.004, n)))
    for s in SECTORS:
        P[s] = 100 * np.exp(np.cumsum(mkt + rng.normal(0.0, 0.009, n)))
    df = pd.DataFrame(P, index=idx)
    irx = pd.Series(2.0, index=idx)
    return df, irx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="1996-01-01")
    ap.add_argument("--out", default="data/etf_rotation_evidence.json")
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
                P, irx = synthetic(3000 + p)
                curves, wf, _, _ = evaluate(P, irx)
                bench = windows(curves["spy_hold"])
                hits = []
                for k, eq in list(curves.items()) + [("walkforward", wf)]:
                    if k == "spy_hold":
                        continue
                    r = windows(eq)
                    be = curves["spy_hold"]
                    if (passes(r, bench, "first_half", eq, be)
                            and passes(r, bench, "second_half", eq, be)):
                        hits.append(k)
                fired += bool(hits)
                rows.append({"panel": p, "fired": hits})
                print(f"  panel {p:2}  {'FIRED ' + ', '.join(hits) if hits else 'nothing'}",
                      flush=True)
            rate = fired / max(a.calibrate, 1)
            print(f"\n  FALSE POSITIVE RATE: {fired}/{a.calibrate} = {rate:.0%}")
            out_path.write_text(json.dumps(
                {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
                 "mode": "calibration", "false_positive_rate": rate,
                 "detail": rows}, indent=2, default=str))
            return 0

        P, irx = download(a.start)
        curves, wf, choices, t0 = evaluate(P, irx)
        bench = windows(curves["spy_hold"])
        table = {k: windows(v) for k, v in curves.items()}
        table["walkforward"] = windows(wf)
        # benchmark over the walk-forward's own period, for a fair comparison
        spy_wf = curves["spy_hold"][curves["spy_hold"].index >= wf.index[0]]
        wf_bench = risk(spy_wf / spy_wf.iloc[0] * START)

        print(f"\n  from {t0.date()}  (all sector funds live and 200-day warm)")
        for win in ("full", "first_half", "second_half"):
            print(f"\n  === {win} ===")
            print(f"  {'arm':18}{'GBP':>12}{'CAGR':>8}{'vs SPY':>8}{'maxDD':>8}"
                  f"{'Sharpe':>8}{'Calmar':>8}{'worst yr':>10}")
            b = bench[win]
            for k in sorted(table, key=lambda x: -(table[x][win].get("final_gbp") or 0)):
                m = table[k][win]
                if not m:
                    continue
                print(f"  {k:18}{m['final_gbp']:>12,.0f}{m['cagr']:>+8.1%}"
                      f"{m['cagr']-b['cagr']:>+8.1%}{m['max_drawdown']:>8.1%}"
                      f"{(m['sharpe'] or 0):>8.2f}{(m['calmar'] or 0):>8.2f}"
                      f"{(m['worst_year'] or 0):>+10.1%}")
        wfr = table["walkforward"]["full"]
        print(f"\n  WALK-FORWARD, judged over ITS OWN years ({wf.index[0].date()} on):")
        print(f"    walk-forward  GBP {wfr['final_gbp']:>10,.0f}  CAGR {wfr['cagr']:+.1%}"
              f"  maxDD {wfr['max_drawdown']:.1%}  Calmar {wfr['calmar']:.2f}")
        print(f"    S&P 500       GBP {wf_bench['final_gbp']:>10,.0f}  CAGR {wf_bench['cagr']:+.1%}"
              f"  maxDD {wf_bench['max_drawdown']:.1%}  Calmar {wf_bench['calmar']:.2f}")
        print("  its yearly choices:",
              ", ".join(f"{c['year']}:{c['chosen']}" for c in choices))

        allc = dict(curves); allc["walkforward"] = wf
        be = curves["spy_hold"]
        print(f"\n  excess-return t-stat vs S&P 500 (must exceed {T_BAR} in BOTH halves)")
        tstats = {}
        for k, eq in allc.items():
            if k == "spy_hold":
                continue
            t1 = excess_t(split(eq, "first_half"), split(be, "first_half"))
            t2 = excess_t(split(eq, "second_half"), split(be, "second_half"))
            tf = excess_t(eq, be)
            tstats[k] = {"first_half_t": t1, "second_half_t": t2, "full_t": tf}
            print(f"    {k:18} 1999-2012 t {t1:+5.2f}   2013-on t {t2:+5.2f}"
                  f"   full t {tf:+5.2f}")
        winners = [k for k in table if k != "spy_hold"
                   and passes(table[k], bench, "first_half", allc[k], be)
                   and passes(table[k], bench, "second_half", allc[k], be)]
        verdict = (
            f"BEATS BUY AND HOLD IN BOTH HALVES: {', '.join(winners)}. Each beat "
            f"the S&P 500 by more than {CAGR_MARGIN:.0%} a year, on "
            f"return-per-drawdown, and with an excess-return t above {T_BAR}, "
            f"in 1999-2012 and again from 2013."
            if winners else
            "No arm beat the S&P 500 by 1% a year AND on Calmar in BOTH halves.")
        print(f"\n  {verdict}")

        # the live call, for each arm, as of the last bar -- this is what the
        # daily job will publish once a winner is confirmed
        arms = build_arms(P, irx)
        core = [EQUITY, BONDS] + [x for x in SECTORS if x in P]
        complete = P[core].notna().all(axis=1)
        last = int(np.flatnonzero(complete.to_numpy())[-1])
        live = {}
        for k, spec in arms.items():
            fn = spec[0] if isinstance(spec, tuple) else spec
            try:
                live[k] = fn(last)
            except Exception:                                 # noqa: BLE001
                live[k] = None
        as_of = str(P.index[last].date())
        # the rule to follow: best full-period Calmar among rules that beat the
        # S&P 500 on BOTH return and Calmar over the full sample
        bfull = bench["full"]
        eligible = [k for k in table if k not in ("spy_hold", "walkforward")
                    and table[k]["full"].get("cagr", -9) > bfull["cagr"]
                    and (table[k]["full"].get("calmar") or 0) > (bfull.get("calmar") or 0)]
        lead = max(eligible, key=lambda k: table[k]["full"]["calmar"]) if eligible else None
        sig = {"generated": pd.Timestamp.now("UTC").isoformat(), "as_of": as_of,
               "lead_rule": lead,
               "lead_position": live.get(lead) if lead else None,
               "lead_stats_full": table[lead]["full"] if lead else None,
               "sp500_stats_full": bfull,
               "all_rules": live,
               "note": ("Lead rule = best return-per-drawdown among rules that beat "
                        "the S&P 500 on BOTH return and drawdown over the full sample. "
                        "It has NOT passed the both-halves significance bar.")}
        Path("docs").mkdir(exist_ok=True)
        Path("docs/etf_signal.json").write_text(json.dumps(sig, indent=2, default=str))
        print(f"\n  LEAD RULE: {lead}  ->  as of {as_of}: {live.get(lead)}")
        print("\n  WHAT EACH RULE SAYS TODAY:")
        for k, w in live.items():
            print(f"    {k:18} {w}")

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "from": str(t0.date()), "to": str(P.index[-1].date()),
             "cost_per_switch": COST, "cagr_margin": CAGR_MARGIN,
             "results": table, "excess_t": tstats, "t_bar": T_BAR,
             "walkforward_choices": choices,
             "walkforward_benchmark": wf_bench, "passes_both_halves": winners,
             "live_positions": live, "verdict": verdict}, indent=2, default=str))
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
