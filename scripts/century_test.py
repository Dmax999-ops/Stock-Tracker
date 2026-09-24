#!/usr/bin/env python3
"""
The same rules, on a hundred years.

The ETF test's best rule -- the three strongest sectors, switching to bonds when
the market is below its 200-day average -- beat the S&P 500 by about 2% a year
from 2000 with a third of the drawdown, but with a full-period excess t of
+0.39. Its whole case rested on two bear markets. This runs the SAME rules, with
the SAME settings translated to months (200 days -> 10 months; 3/6/12-month
momentum unchanged), on US market, industry, T-bill and 10-year Treasury
returns from 1926.

Nothing is re-tuned on the new data. 1927-1999 is history these rules have never
been tested on, so it is a genuine out-of-sample test -- the strongest one
available.

RULES
-----
    market_hold       the US market, never sold. The benchmark.
    mkt10_cash        market when above its 10-month average, else T-bills
    mkt10_bonds       ... else 10-year Treasuries
    mkt10_safe        ... else Treasuries only if they are in their own uptrend,
                      otherwise T-bills
    ind_top3          the three strongest of ten industries (avg 3/6/12-month
                      momentum), always invested
    ind_top3_bonds    the same, Treasuries when the market is below its 10-month
    ind_top3_safe     the same, trend-checked safe haven
    ens_mkt_safe      market exposure = share of six trend signals positive
                      (price above 2/5/10-month average, 3/6/12-month return
                      positive); the rest in the safe haven
    ens_ind_safe      the same, holding the top three industries

VERDICT
-------
Reported for 1927-1999 (out of sample), 2000-2026, and the whole century, plus
every US bear market deeper than 25%, one by one. A rule passes only if, in
1927-1999, it beats the market by 1% a year, on Calmar, AND with an excess-return
t above 2. --calibrate runs the whole thing on random walks first.
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
OOS_END = pd.Timestamp("1999-12-31")
CAGR_MARGIN, CALMAR_MULT, T_BAR = 0.01, 1.10, 2.0


def load_fine(root="data/history"):
    """30- and 49-industry panels, if the fetch job has saved them."""
    out = {}
    for n in (30, 49):
        f = Path(root) / f"industries{n}.csv"
        if f.exists():
            out[n] = pd.read_csv(f, index_col=0, parse_dates=True)
    return out


def load(root="data/history"):
    m = pd.read_csv(f"{root}/market.csv", index_col=0, parse_dates=True)
    ind = pd.read_csv(f"{root}/industries.csv", index_col=0, parse_dates=True)
    b = pd.read_csv(f"{root}/bond10y.csv", index_col=0, parse_dates=True)["BOND"]
    R = ind.copy()
    R["MKT"] = m["MKT"]
    R["RF"] = m["RF"]
    R["BOND"] = b
    return R.sort_index()


def rules(R: pd.DataFrame) -> dict:
    inds = [c for c in R.columns if c not in ("MKT", "RF", "BOND")]
    L = (1 + R.fillna(0)).cumprod()              # total-return index levels
    L = L.where(R.notna().cumsum() > 0)          # nothing before a series starts
    ma = {k: L.rolling(k, min_periods=k).mean() for k in (2, 5, 10)}

    def up(col, t, k=10):
        a, b = L[col].iat[t], ma[k][col].iat[t]
        return bool(np.isfinite(a) and np.isfinite(b) and a > b)

    def ret(col, t, n):
        if t - n < 0:
            return np.nan
        a, b = L[col].iat[t - n], L[col].iat[t]
        return b / a - 1 if np.isfinite(a) and np.isfinite(b) and a > 0 else np.nan

    def ready(t):
        return np.isfinite(ma[10]["MKT"].iat[t])

    def bonds(t):
        return {"BOND": 1.0} if np.isfinite(R["BOND"].iat[t]) else {"RF": 1.0}

    def safe(t):
        if np.isfinite(ma[10]["BOND"].iat[t]) and up("BOND", t):
            return {"BOND": 1.0}
        return {"RF": 1.0}

    def top3(t):
        sc = {}
        for c in inds:
            xs = [ret(c, t, n) for n in (3, 6, 12)]
            if all(np.isfinite(x) for x in xs):
                sc[c] = np.mean(xs)
        if len(sc) < 5:
            return None
        pick = sorted(sc, key=sc.get, reverse=True)[:3]
        return {c: 1 / 3 for c in pick}

    def score(t):
        s = [up("MKT", t, k) for k in (2, 5, 10)]
        s += [ret("MKT", t, n) > 0 for n in (3, 6, 12)]
        return float(np.mean(s))

    def mix(eq_w, sc, haven):
        w = {k: v * sc for k, v in eq_w.items()}
        if 1 - sc > 1e-9:
            for k, v in haven.items():
                w[k] = w.get(k, 0) + (1 - sc) * v
        return w

    A = {}
    A["market_hold"] = lambda t: {"MKT": 1.0} if ready(t) else None
    A["mkt10_cash"] = lambda t: None if not ready(t) else ({"MKT": 1.0} if up("MKT", t) else {"RF": 1.0})
    A["mkt10_bonds"] = lambda t: None if not ready(t) else ({"MKT": 1.0} if up("MKT", t) else bonds(t))
    A["mkt10_safe"] = lambda t: None if not ready(t) else ({"MKT": 1.0} if up("MKT", t) else safe(t))
    A["ind_top3"] = lambda t: None if not ready(t) else top3(t)

    def it_b(t):
        if not ready(t):
            return None
        return (top3(t) if up("MKT", t) else bonds(t))
    A["ind_top3_bonds"] = it_b

    def it_s(t):
        if not ready(t):
            return None
        return (top3(t) if up("MKT", t) else safe(t))
    A["ind_top3_safe"] = it_s
    A["ens_mkt_safe"] = lambda t: None if not ready(t) else mix({"MKT": 1.0}, score(t), safe(t))

    def ens_i(t):
        if not ready(t):
            return None
        tp = top3(t)
        return None if tp is None else mix(tp, score(t), safe(t))
    A["ens_ind_safe"] = ens_i
    return A


def fine_rules(R: pd.DataFrame, F: pd.DataFrame, tag: str) -> dict:
    """
    The SAME pre-registered rule on finer industries: average of 3/6/12-month
    momentum, hold the top fifth (30 -> 6, 49 -> 10), equal weight, monthly.
    Plus the same market filter into the same safe haven. Nothing re-tuned.
    """
    cols = list(F.columns)
    k = max(3, round(len(cols) / 5))
    J = F.reindex(R.index)
    LF = (1 + J.fillna(0)).cumprod().where(J.notna().cumsum() > 0)
    LM = (1 + R["MKT"].fillna(0)).cumprod()
    ma10 = LM.rolling(10, min_periods=10).mean()
    LB = (1 + R["BOND"].fillna(0)).cumprod().where(R["BOND"].notna().cumsum() > 0)
    mb = LB.rolling(10, min_periods=10).mean()

    def pick(t):
        if t < 12:
            return None
        sc = sum(LF.iloc[t] / LF.iloc[t - n] - 1 for n in (3, 6, 12)) / 3
        sc = sc.dropna()
        if len(sc) < k * 2:
            return None
        top = sc.sort_values(ascending=False).index[:k]
        return {f"{tag}:{c}": 1 / k for c in top}

    def safe(t):
        if np.isfinite(mb.iat[t]) and LB.iat[t] > mb.iat[t]:
            return {"BOND": 1.0}
        return {"RF": 1.0}

    def filt(t):
        p = pick(t)
        if p is None or not np.isfinite(ma10.iat[t]):
            return None
        return p if LM.iat[t] > ma10.iat[t] else safe(t)
    return {f"{tag}_top": pick, f"{tag}_top_safe": filt}


def run(R: pd.DataFrame, decide) -> pd.Series:
    """Decide at the end of month t with data to t; earn month t+1's returns."""
    n = len(R)
    eq = np.full(n, np.nan)
    v, w = START, None
    for t in range(n):
        if w is not None:
            r = 0.0
            for k, x in w.items():
                rk = R[k].iat[t]
                r += x * (0.0 if not np.isfinite(rk) else rk)
            v *= 1 + r
            eq[t] = v
        new = decide(t)
        if new is not None:
            if w is None:
                eq[t] = v
            turn = sum(abs(new.get(k, 0) - (w or {}).get(k, 0))
                       for k in set(new) | set(w or {}))
            v *= 1 - COST * turn / 2
            w = new
    return pd.Series(eq, index=R.index).dropna()


def stats(eq: pd.Series) -> dict:
    if len(eq) < 24:
        return {}
    yrs = len(eq) / 12
    r = eq.pct_change().dropna()
    dd = float((eq / eq.cummax() - 1).min())
    cagr = float((eq.iloc[-1] / eq.iloc[0]) ** (1 / yrs) - 1)
    vol = float(r.std() * np.sqrt(12))
    yearly = eq.resample("YE").last().pct_change().dropna()
    return {"final_gbp": float(START * eq.iloc[-1] / eq.iloc[0]), "cagr": cagr,
            "max_drawdown": dd, "sharpe": cagr / vol if vol else None,
            "calmar": cagr / abs(dd) if dd < 0 else None,
            "worst_year": float(yearly.min()) if len(yearly) else None}


def excess_t(a: pd.Series, b: pd.Series) -> float:
    j = a.index.intersection(b.index)
    d = (a.loc[j].pct_change() - b.loc[j].pct_change()).dropna()
    if len(d) < 24 or d.std() == 0:
        return float("nan")
    return float(d.mean() / d.std() * np.sqrt(len(d)))


def periods(eq):
    return {"oos_1927_1999": eq[eq.index <= OOS_END],
            "2000_on": eq[eq.index > OOS_END], "century": eq}


def evaluate(R, fine=None):
    A = rules(R)
    if fine:
        for n, F in fine.items():
            tag = f"ind{n}"
            for c in F.columns:
                R[f"{tag}:{c}"] = F[c].reindex(R.index)
            A.update(fine_rules(R, F, tag))
    curves = {k: run(R, f) for k, f in A.items()}
    t0 = max(c.index[0] for c in curves.values())
    curves = {k: v[v.index >= t0] for k, v in curves.items()}
    return curves


def passes(curves, key, per="oos_1927_1999"):
    a, b = periods(curves[key])[per], periods(curves["market_hold"])[per]
    sa, sb = stats(a), stats(b)
    if not sa or not sb:
        return False
    return bool(sa["cagr"] > sb["cagr"] + CAGR_MARGIN
                and (sa["calmar"] or 0) > (sb["calmar"] or 0) * CALMAR_MULT
                and excess_t(a, b) > T_BAR)


def bears(mkt_eq: pd.Series, depth=0.25):
    """Every peak-to-recovery episode in the market deeper than `depth`."""
    pk = mkt_eq.cummax(); dd = mkt_eq / pk - 1
    out, i, n = [], 0, len(dd)
    while i < n:
        if dd.iat[i] < -depth:
            s = i
            while s > 0 and dd.iat[s - 1] < 0:
                s -= 1
            e = i
            while e < n and dd.iat[e] < 0:
                e += 1
            tr = s + int(np.argmin(dd.iloc[s:e].to_numpy()))
            out.append((dd.index[max(s - 1, 0)], dd.index[min(e, n - 1)],
                        dd.index[tr], float(dd.iat[tr])))
            i = e
        else:
            i += 1
    return out


def synthetic(seed, months=1200):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("1926-07-31", periods=months, freq="ME")
    mkt = rng.normal(0.0075, 0.045, months)
    R = pd.DataFrame(index=idx)
    for k in range(10):
        R[f"I{k}"] = mkt + rng.normal(0, 0.03, months)
    R["MKT"] = mkt
    R["RF"] = 0.003
    R["BOND"] = rng.normal(0.004, 0.02, months)
    return R


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/history")
    ap.add_argument("--out", default="data/century_evidence.json")
    ap.add_argument("--calibrate", type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__, "python": sys.version.split()[0]}
    try:
        if a.calibrate:
            fired = 0
            rows = []
            for p in range(a.calibrate):
                c = evaluate(synthetic(5000 + p))
                hits = [k for k in c if k != "market_hold" and passes(c, k)]
                fired += bool(hits); rows.append(hits)
                print(f"  panel {p:2}  {'FIRED ' + ', '.join(hits) if hits else 'nothing'}", flush=True)
            rate = fired / a.calibrate
            print(f"\n  FALSE POSITIVE RATE: {fired}/{a.calibrate} = {rate:.0%}")
            out.write_text(json.dumps({"generated": pd.Timestamp.now("UTC").isoformat(),
                                       "mode": "calibration", "false_positive_rate": rate,
                                       "detail": rows}, indent=2))
            return 0

        R = load(a.data)
        fine = load_fine(a.data)
        print("finer industry panels:", {n: f.shape[1] for n, f in fine.items()} or "none")
        curves = evaluate(R, fine)
        mh = curves["market_hold"]
        table, ts = {}, {}
        for k, eq in curves.items():
            table[k] = {p: stats(v) for p, v in periods(eq).items()}
            if k != "market_hold":
                ts[k] = {p: excess_t(v, periods(mh)[p]) for p, v in periods(eq).items()}
        for p in ("oos_1927_1999", "2000_on", "century"):
            b = table["market_hold"][p]
            print(f"\n  === {p} ===")
            print(f"  {'rule':16}{'GBP':>16}{'CAGR':>7}{'vsMkt':>7}{'maxDD':>7}{'Calm':>6}{'wrstyr':>8}{'t':>7}")
            for k in sorted(table, key=lambda x: -(table[x][p].get("cagr") or -9)):
                m = table[k][p]
                t = ts.get(k, {}).get(p, float("nan"))
                print(f"  {k:16}{m['final_gbp']:>16,.0f}{m['cagr']:>+7.1%}{m['cagr']-b['cagr']:>+7.1%}"
                      f"{m['max_drawdown']:>7.1%}{(m['calmar'] or 0):>6.2f}{(m['worst_year'] or 0):>+8.1%}{t:>+7.2f}")

        # bear market by bear market
        ep = bears(mh)
        bear_rows = []
        print(f"\n  EVERY US BEAR MARKET DEEPER THAN 25% ({len(ep)})")
        keys = [k for k in curves if k != "market_hold"]
        print(f"  {'peak':>10} {'recovered':>10} {'depth':>7}  " + " ".join(f"{k[:12]:>12}" for k in ["market_hold"] + keys))
        for s, e, tr, dep in ep:
            row = {"peak": str(s.date()), "recovered": str(e.date()), "depth": dep}
            line = f"  {str(s.date()):>10} {str(e.date()):>10} {dep:>+7.1%}  "
            for k in ["market_hold"] + keys:
                c = curves[k]
                if s in c.index and e in c.index:
                    x = c.loc[e] / c.loc[s] - 1
                    row[k] = float(x); line += f"{x:>+12.1%} "
                else:
                    line += f"{'-':>12} "
            bear_rows.append(row); print(line)

        winners = [k for k in keys if passes(curves, k)]
        verdict = (f"PASSES OUT OF SAMPLE (1927-1999): {', '.join(winners)} -- beat the market by "
                   f"{CAGR_MARGIN:.0%} a year, on Calmar, and with excess t > {T_BAR}, on history "
                   f"these rules were never tested on." if winners else
                   "No rule passed the out-of-sample bar on 1927-1999.")
        print(f"\n  {verdict}")
        out.write_text(json.dumps({"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
                                   "from": str(mh.index[0].date()), "to": str(mh.index[-1].date()),
                                   "results": table, "excess_t": ts, "bears": bear_rows,
                                   "passes_oos": winners, "verdict": verdict}, indent=2, default=str))
        return 0
    except Exception as exc:                                       # noqa: BLE001
        import traceback
        out.write_text(json.dumps({"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
                                   "error": f"{type(exc).__name__}: {exc}",
                                   "traceback": traceback.format_exc().splitlines()[-25:]}, indent=2))
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
