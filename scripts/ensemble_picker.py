#!/usr/bin/env python3
"""
ALL THE EVIDENCE AT ONCE: a stock picker that learns, year by year, how to
weigh every pattern together -- and is only ever tested on years it has not
seen.

WHY
---
25 single scores have now been tested (momentum, trend, breakouts, RSI,
volatility, volume, profitability, value, cash quality, growth, results-day
reactions, sector and peer strength). Several showed a real but small tilt --
e.g. stocks rising while their peer group is weak: top tenth +17.5% a year vs
+13.2% for the average stock -- but none was strong enough ALONE to beat the
S&P 500 after Hargreaves Lansdown costs. Professional quant funds do not use
one signal; they combine many weak ones, because their errors partly cancel.

HOW (no hindsight)
------------------
For each year Y from 2003 on:
  * TRAIN on every stock-month whose 12-month outcome was fully known a year
    before Y starts. The model is a ridge regression: which patterns, weighted
    how, best ranked the next 12 months' returns.
  * PREDICT every month of year Y with those weights -- then throw them away
    and retrain for Y+1 with one more year of history.
So every prediction is made with rules fitted only on the past, exactly as it
would have been in real time.

TESTED WITH THE SAME RULES AS EVERYTHING ELSE
  * does the prediction rank next year's winners? (t >= 3, both halves)
  * GBP 10,000 under the commit rules, HL costs, vs the S&P 500
  * the learned weights each year are reported: that is the model's own
    answer to "what makes a winner", and whether it stays stable.

Results: docs/ENSEMBLE.md, data/ensemble.json
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


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ws = _load("ws", "winners_study.py")
fs, bp, dp = ws.fs, ws.bp, ws.dp
RIDGE = 50.0
FIRST_YEAR = 2003


def monthly_quantiles(feats: dict, member: np.ndarray, idx) -> tuple[list[int], dict]:
    firsts = pd.Series(np.arange(len(idx)), index=idx).groupby(idx.to_period("M")).first()
    dates = [int(i) for i in firsts if i >= 260]
    Q = {}
    for k, D in feats.items():
        A = D.to_numpy(float)
        M = np.full((len(dates), A.shape[1]), np.nan)
        for n, i in enumerate(dates):
            ok = member[i] & np.isfinite(A[i])
            if ok.sum() >= 30:
                M[n, ok] = pd.Series(A[i, ok]).rank(pct=True).to_numpy()
        Q[k] = M
    return dates, Q


def walk_forward(C, member, feats, spy):
    idx = C.index
    X = C.ffill().to_numpy(float)
    names = list(feats)
    dates, Q = monthly_quantiles(feats, member, idx)
    n_d, n_s = len(dates), C.shape[1]
    # target: cross-sectional rank of the next 12 months' return (known only 252 days later)
    Y = np.full((n_d, n_s), np.nan)
    for n, i in enumerate(dates):
        if i + 252 < len(idx):
            ok = member[i] & np.isfinite(X[i]) & np.isfinite(X[i + 252])
            if ok.sum() >= 30:
                Y[n, ok] = pd.Series(X[i + 252, ok] / X[i, ok] - 1).rank(pct=True).to_numpy() - 0.5
    F = np.stack([Q[k] for k in names], axis=-1) - 0.5          # (dates, stocks, features)
    F = np.nan_to_num(F, nan=0.0)                               # unknown = neutral
    pred = np.full((n_d, n_s), np.nan)
    weights = {}
    ddates = idx[dates]
    for year in range(FIRST_YEAR, idx[-1].year + 1):
        start = pd.Timestamp(f"{year}-01-01")
        known_by = start - pd.Timedelta(days=365)           # outcome fully known before Y
        tr = np.where(ddates <= known_by)[0]
        te = np.where((ddates >= start) & (ddates < pd.Timestamp(f"{year + 1}-01-01")))[0]
        if len(tr) < 36 or not len(te):
            continue
        Xt = F[tr].reshape(-1, len(names))
        yt = Y[tr].reshape(-1)
        ok = np.isfinite(yt)
        Xt, yt = Xt[ok], yt[ok]
        w = np.linalg.solve(Xt.T @ Xt + RIDGE * np.eye(len(names)), Xt.T @ yt)
        weights[year] = dict(zip(names, np.round(w, 4)))
        for n in te:
            live = member[dates[n]] & np.isfinite(X[dates[n]])
            pred[n, live] = F[n, live] @ w
    # daily panel for the commit rules: each month's prediction holds until the next
    P = pd.DataFrame(np.nan, index=idx, columns=C.columns)
    P.iloc[dates] = pred
    P = P.ffill(limit=25)
    return P, weights


def write_md(out, path):
    L = ["# All the evidence at once — a stock picker that learns, tested only on unseen years\n",
         f"_Generated {out['generated'][:16].replace('T', ' ')} UTC. {out['data']}. Every prediction "
         f"for year Y uses weights fitted only on outcomes known before Y. {len(out['features'])} "
         f"patterns combined._\n",
         f"## Verdict: **{'PASSES' if out['passes'] else 'DOES NOT PASS'}**\n",
         out["verdict"] + "\n"]
    p, m, t = out["prediction"], out["money_costs"], out["turnover"]
    L += ["## Did it predict?\n",
          f"Rank correlation with the next month: {p['all']['ic_1m']:+.3f} (t = {p['all']['t_1m']:+.1f}; "
          f"first half t = {p.get('first', {}).get('t_1m', 0):+.1f}, second half t = "
          f"{p.get('second', {}).get('t_1m', 0):+.1f}). Stocks it ranked in the top tenth went on to make "
          f"**{p['all']['top10_12m']:+.1%}** over the next 12 months; the bottom tenth "
          f"{p['all']['bot10_12m']:+.1%}; the average stock {p['all']['all_12m']:+.1%}.\n",
          "## £10,000 under the commit rules, after HL costs\n",
          "| | £ | Yearly | Worst fall | First half vs S&P | Second half vs S&P |",
          "|---|---|---|---|---|---|"]
    a = m["all"]
    h = [m.get(k, {}) for k in ("first", "second")]
    d = [f"{x['cagr'] - x['spy_cagr']:+.1%}/yr" if x else "" for x in h]
    L += [f"| Ensemble picker | **£{a['gbp_from_10k']:,}** | {a['cagr']:+.1%} | {a['worst']:.0%} | {d[0]} | {d[1]} |",
          f"| S&P 500 | £{a['spy_gbp_from_10k']:,} | {a['spy_cagr']:+.1%} | {a['spy_worst']:.0%} | | |",
          f"\n{t['trades_per_year']} trades a year, typical hold {t['median_hold_days'] or '—'} days. "
          f"Best trades: " + ", ".join(f"{b['ticker']} {b['ret']:+.0%} ({b['in'][:7]})"
                                       for b in t.get("best_trades", [])[:5]) + "\n",
          "## What the model learned makes a winner (weights, latest year vs first year)\n",
          "Positive = more of this, more likely a winner. The model re-learns every year; a "
          "pattern it keeps the same sign on year after year is a real tendency, one that flips "
          "is noise.\n",
          "| Pattern | First year | Latest year | Same sign in … |", "|---|---|---|---|"]
    ys = sorted(out["weights"])
    for k in sorted(out["features"], key=lambda k: -abs(out["weights"][ys[-1]][k])):
        signs = [np.sign(out["weights"][y][k]) for y in ys]
        same = max(sum(1 for s in signs if s > 0), sum(1 for s in signs if s < 0))
        L.append(f"| {ws.DESCRIBE.get(k, (k,))[0]} | {out['weights'][ys[0]][k]:+.3f} | "
                 f"{out['weights'][ys[-1]][k]:+.3f} | {same} of {len(ys)} years |")
    path.write_text("\n".join(L) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--delisted", default="data/delisted/delisted_weekly.parquet")
    ap.add_argument("--fundamentals", default="data/fundamentals.parquet")
    ap.add_argument("--earnings", default="data/earnings_dates.csv")
    ap.add_argument("--labels", default=dp.CONSTITUENTS)
    ap.add_argument("--out", default="data/ensemble.json")
    ap.add_argument("--md", default="docs/ENSEMBLE.md")
    ap.add_argument("--spy-csv", default="")
    ap.add_argument("--no-membership", action="store_true")
    a = ap.parse_args()
    out = {"generated": pd.Timestamp.now("UTC").isoformat()}
    try:
        C, info = bp.load_panel(a.prices, a.delisted)
        C = C.loc[:, C.notna().sum() > 260]
        try:
            px = pd.read_parquet(a.prices, columns=["date", "ticker", "volume"])
            px["date"] = pd.to_datetime(px["date"])
            V = px.pivot_table(index="date", columns="ticker", values="volume").reindex(
                index=C.index, columns=C.columns)
        except Exception:                                          # noqa: BLE001
            V = None
        member = (np.ones(C.shape, bool) if a.no_membership
                  else bp.membership_mask(C.index, list(C.columns)))
        spy = (pd.read_csv(a.spy_csv, index_col=0, parse_dates=True).iloc[:, 0].reindex(C.index).ffill()
               if a.spy_csv else bp.load_spy(C.index))
        keep = C.index >= spy.first_valid_index()
        C, member, spy = C.loc[keep], member[keep], spy.loc[keep]
        V = V.loc[keep] if V is not None else None
        try:
            lab = dp.load_constituents(a.labels).set_index("yf")["GICS Sector"]
        except Exception:                                          # noqa: BLE001
            lab = pd.Series(dtype=str)
        feats = ws.features(C, V, spy, member, lab, a.fundamentals, a.earnings)
        try:
            g = fs.build_group_signals(C, None)
            feats["rise_weak_peers"] = g["rise_weak_peers"]
        except Exception:                                          # noqa: BLE001
            pass
        # sector momentum uses today's labels (survivors only) -- left out on purpose
        feats.pop("sector_momentum", None)
        names = [k for k in feats]
        out["features"] = names
        print("features:", names, flush=True)
        P, W = walk_forward(C, member, feats, spy)
        out["weights"] = {int(k): v for k, v in W.items()}
        Cff = C.ffill()
        firsts = pd.Series(np.arange(len(C)), index=C.index).groupby(C.index.to_period("M")).first()
        dates = [int(i) for i in firsts if i >= 260]
        cnt = (P.notna().to_numpy() & member).sum(axis=1)
        d_sig = [i for i in dates if cnt[i] >= 100]
        split = C.index[d_sig[len(d_sig) // 2]]
        pr = fs.summarise(fs.prediction(P, Cff, member, d_sig), split)
        eq_c, turn = fs.commit_portfolio(P, Cff, spy, member, d_sig[0], True)
        mc = fs.money(eq_c, spy, split)
        predicts = pr["all"]["t_1m"] >= fs.T_ALL and all(
            pr.get(h, {}).get("t_1m", 0) >= fs.T_HALF for h in ("first", "second"))
        beats = all(mc.get(h) and mc[h]["cagr"] >= mc[h]["spy_cagr"] + fs.MARGIN
                    for h in ("first", "second"))
        out.update({"data": f"{C.shape[1]} stocks ever in the S&P 500, {C.index[d_sig[0]].date()} → "
                            f"{C.index[-1].date()}, halves split at {split.date()}",
                    "prediction": pr, "money_costs": mc, "turnover": turn,
                    "predicts": bool(predicts), "beats_after_costs": bool(beats),
                    "passes": bool(predicts and beats)})
        out["verdict"] = (
            "It predicted AND beat the S&P 500 by at least 1%/yr after costs in both halves."
            if out["passes"] else
            ("It predicted, but did not beat the S&P 500 by 1%/yr after costs in both halves."
             if predicts else
             ("It beat the S&P 500 after costs in both halves, but its predictions did not clear "
              "the statistical bar — so the money may be luck." if beats else
              "Combining every pattern still did not reliably pick next year's winners.")))
        print(json.dumps({k: out[k] for k in ("predicts", "beats_after_costs")}), flush=True)
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
        Path(a.md).write_text("# Ensemble FAILED\n\n```\n" + "\n".join(out["traceback"]) + "\n```\n")
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
