#!/usr/bin/env python3
"""
WHAT MAKES A WINNER?

Take every S&P 500 stock on the first trading day of every month since 1997.
Look 12 months ahead and mark:
    WINNER  in the top 5% of all stocks over the next 12 months
    LOSER   in the bottom 5%
Then describe every stock AS IT LOOKED ON THE START DATE -- only information
available that day -- across price action, technical patterns, trading volume
and the company's accounts, and ask:

  1. Which stocks returned the most, and what did they look like beforehand?
  2. For each pattern: if a stock has it, how much likelier is it to be a
     winner -- and, just as important, how much likelier to be a LOSER?
     A pattern that makes both likelier (e.g. wild volatility) is a gamble,
     not an edge.
  3. Is the pattern consistent -- does it hold in most years, or in a few?
  4. Combinations: pairs of patterns are DISCOVERED on 1997-2011 only, then
     tested, untouched, on 2012-today. Anything found by searching hundreds of
     combinations will look good on the data it was found in; only the ones
     that still work on the later, unseen years count.

Results: docs/WINNERS.md and data/winners_study.json
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
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


fs = _load("fs", "factor_screen.py")
bp = fs.bp
dp = bp.dp

WIN_PCT, LOSE_PCT = 0.95, 0.05
H = 252
DISCOVER_END = pd.Timestamp("2012-01-01")

# plain-English descriptions of each measure, and of its top fifth
DESCRIBE = {
    "ret_12_1": ("Return over the past year (skipping last month)", "strongest risers"),
    "ret_3m": ("Return over the past 3 months", "strongest recent risers"),
    "ret_1m": ("Return over the past month", "biggest risers last month"),
    "dist_52w_high": ("How close to its 12-month high", "at or near their high"),
    "dist_52w_low": ("How far above its 12-month low", "furthest above their low"),
    "above_200d": ("% above the 200-day average", "furthest above the 200-day"),
    "golden_cross": ("50-day average above the 200-day", "in a golden cross"),
    "new_high_20d": ("Made a new 12-month high in the last 20 days", "fresh breakouts"),
    "rsi14": ("RSI (14-day)", "most overbought"),
    "volatility": ("Daily swings, last 6 months", "most volatile"),
    "beta": ("Moves with the market (beta)", "highest beta"),
    "biggest_day_1m": ("Biggest single-day jump last month", "biggest one-day jumps"),
    "rel_volume": ("Trading volume, last month vs last year", "volume surging"),
    "size": ("Company size (market value)", "largest companies"),
    "gross_profitability": ("Gross profit / assets", "most profitable"),
    "roa": ("Net profit / assets", "highest return on assets"),
    "revenue_growth": ("Sales growth, last reported year", "fastest sales growth"),
    "asset_growth": ("Balance-sheet growth, last year", "fastest-growing balance sheets"),
    "accruals": ("Profit NOT backed by cash (accruals)", "least cash-backed profits"),
    "earnings_yield": ("Earnings / market value", "cheapest on earnings"),
    "fcf_yield": ("Free cash flow / market value", "cheapest on cash flow"),
    "book_to_market": ("Book value / market value", "cheapest on book value"),
    "earnings_reaction": ("Move vs S&P on last results (within 3 months)", "best results-day reactions"),
    "sector_momentum": ("Its sector's return over the past year", "in the hottest sectors"),
}


def features(C, V, spy, member, labels, fpath, epath) -> dict[str, pd.DataFrame]:
    Cf = C.ffill(limit=10)
    R = Cf.pct_change(fill_method=None)
    rs = spy.pct_change()
    hi, lo = Cf.rolling(252, min_periods=200).max(), Cf.rolling(252, min_periods=200).min()
    ma50, ma200 = Cf.rolling(50, min_periods=50).mean(), Cf.rolling(200, min_periods=200).mean()
    up = R.clip(lower=0).rolling(14).mean()
    dn = (-R.clip(upper=0)).rolling(14).mean()
    mR, mS = R.rolling(252, min_periods=200).mean(), rs.rolling(252, min_periods=200).mean()
    cov = R.mul(rs, axis=0).rolling(252, min_periods=200).mean().sub(mR.mul(mS, axis=0))
    beta = cov.div(rs.rolling(252, min_periods=200).var(), axis=0)
    out = {
        "ret_12_1": Cf.shift(21) / Cf.shift(252) - 1,
        "ret_3m": Cf / Cf.shift(63) - 1,
        "ret_1m": Cf / Cf.shift(21) - 1,
        "dist_52w_high": Cf / hi - 1,
        "dist_52w_low": Cf / lo - 1,
        "above_200d": Cf / ma200 - 1,
        "golden_cross": (ma50 > ma200).astype(float).where(ma200.notna()),
        "new_high_20d": (Cf.rolling(20).max() >= hi * 0.999).astype(float).where(hi.notna()),
        "rsi14": 100 - 100 / (1 + up / dn.replace(0, np.nan)),
        "volatility": R.rolling(126, min_periods=100).std() * np.sqrt(252),
        "beta": beta,
        "biggest_day_1m": R.rolling(21).max(),
    }
    if V is not None:
        V = V.reindex_like(C)
        out["rel_volume"] = V.rolling(21).mean() / V.rolling(252, min_periods=200).mean()
    # sector momentum (sector labels known only for current members)
    sec = labels.reindex(C.columns)
    r12 = out["ret_12_1"]
    sm = pd.DataFrame(np.nan, index=C.index, columns=C.columns)
    for s_name, cols in sec.groupby(sec).groups.items():
        cols = list(cols)
        if len(cols) >= 5:
            m = r12[cols].mean(axis=1)
            sm[cols] = np.repeat(m.to_numpy()[:, None], len(cols), axis=1)
    out["sector_momentum"] = sm
    # company accounts
    fsig = fs.build_fund_signals(C, r12, fpath, epath, spy)
    for k in ("gross_profitability", "roa", "earnings_yield", "fcf_yield", "book_to_market",
              "earnings_reaction"):
        if k in fsig:
            out[k] = fsig[k]
    if "low_accruals" in fsig:
        out["accruals"] = -fsig["low_accruals"]
    if "low_asset_growth" in fsig:
        out["asset_growth"] = -fsig["low_asset_growth"]
    if Path(fpath).exists():
        F = pd.read_parquet(fpath)
        F["end"], F["filed"] = pd.to_datetime(F["end"]), pd.to_datetime(F["filed"])
        F = pd.concat([F, fs._prior_year(F, "revenue")], ignore_index=True)
        rev = fs._asof_panel(F, "revenue", C.index, list(C.columns))
        rev0 = fs._asof_panel(F, "revenue_prev", C.index, list(C.columns)).where(lambda x: x > 0)
        out["revenue_growth"] = rev / rev0 - 1
        # size: the stated public float rolled forward with the price
        ey = fsig.get("earnings_yield")
        ni = fs._asof_panel(F, "net_income", C.index, list(C.columns))
        if ey is not None:
            out["size"] = np.log((ni / ey).where(lambda x: x > 0))
    return out


def sample(C, member, feats, spy):
    """One row per stock per month: its features on that day and what happened next."""
    Cff = C.ffill()
    X = Cff.to_numpy(float)
    idx = C.index
    firsts = pd.Series(np.arange(len(idx)), index=idx).groupby(idx.to_period("M")).first()
    dates = [int(i) for i in firsts if 260 <= i < len(idx) - H]
    F = {k: v.to_numpy(float) for k, v in feats.items()}
    rows = []
    for i in dates:
        ok = member[i] & np.isfinite(X[i]) & np.isfinite(X[i + H])
        ks = np.where(ok)[0]
        if len(ks) < 100:
            continue
        f12 = X[i + H, ks] / X[i, ks] - 1
        q = pd.Series(f12).rank(pct=True).to_numpy()
        d = {"date": np.repeat(idx[i], len(ks)), "ticker": np.array(C.columns)[ks], "fwd_12m": f12,
             "winner": q >= WIN_PCT, "loser": q <= LOSE_PCT,
             "spy_12m": np.repeat(spy.iloc[i + H] / spy.iloc[i] - 1, len(ks))}
        for k, A in F.items():
            v = A[i, ks]
            d[k] = v
            d[k + "_q"] = pd.Series(v).rank(pct=True).to_numpy()   # NaN stays NaN
        rows.append(pd.DataFrame(d))
    return pd.concat(rows, ignore_index=True)


def profile(S: pd.DataFrame, feats: list[str]) -> list[dict]:
    base_w, base_l = S["winner"].mean(), S["loser"].mean()
    out = []
    for k in feats:
        q = S[k + "_q"]
        has = S[q.notna()]
        if len(has) < 2000:
            continue
        top = has[has[k + "_q"] >= 0.8]
        bot = has[has[k + "_q"] <= 0.2]
        years = has.assign(y=has["date"].dt.year, t=has[k + "_q"] >= 0.8)
        by = years.groupby("y").apply(
            lambda g: (g.loc[g.t, "winner"].mean() / max(g["winner"].mean(), 1e-9)) if g.t.any() else np.nan,
            include_groups=False).dropna()
        out.append({
            "feature": k,
            "winners_median": float(has.loc[has.winner, k].median()),
            "everyone_median": float(has[k].median()),
            "losers_median": float(has.loc[has.loser, k].median()),
            "p_win_top": float(top["winner"].mean() / base_w),
            "p_lose_top": float(top["loser"].mean() / base_l),
            "p_win_bottom": float(bot["winner"].mean() / base_w),
            "p_lose_bottom": float(bot["loser"].mean() / base_l),
            "avg_12m_top": float(top["fwd_12m"].mean()),
            "avg_12m_bottom": float(bot["fwd_12m"].mean()),
            "years_top_favoured": int((by > 1).sum()), "years": int(len(by)),
            "since": str(has["date"].min().date()),
        })
    return out


def combos(S: pd.DataFrame, feats: list[str], top_n=12) -> list[dict]:
    """Pairs of patterns found on 1997-2011, then checked on 2012-now."""
    conds = []
    for k in feats:
        conds += [(k, "top"), (k, "bottom")]
    disc, test = S[S["date"] < DISCOVER_END], S[S["date"] >= DISCOVER_END]
    bw_d, bl_d = disc["winner"].mean(), disc["loser"].mean()
    bw_t, bl_t = test["winner"].mean(), test["loser"].mean()

    def mask(D, c):
        k, side = c
        q = D[k + "_q"]
        return (q >= 0.8) if side == "top" else (q <= 0.2)
    res = []
    for a, b in itertools.combinations(conds, 2):
        if a[0] == b[0]:
            continue
        m = mask(disc, a) & mask(disc, b)
        if m.sum() < 300:
            continue
        g = disc[m]
        score = g["winner"].mean() / bw_d - g["loser"].mean() / bl_d
        res.append((score, a, b, g["winner"].mean() / bw_d, g["loser"].mean() / bl_d,
                    g["fwd_12m"].mean() - disc["fwd_12m"].mean(), int(m.sum())))
    res.sort(key=lambda r: -r[0])
    out = []
    for score, a, b, pw, pl, ex, n in res[:top_n]:
        m = mask(test, a) & mask(test, b)
        g = test[m]
        out.append({"a": a, "b": b, "discover_p_win": pw, "discover_p_lose": pl,
                    "discover_excess_12m": ex, "discover_n": n,
                    "test_p_win": float(g["winner"].mean() / bw_t) if len(g) else None,
                    "test_p_lose": float(g["loser"].mean() / bl_t) if len(g) else None,
                    "test_excess_12m": float(g["fwd_12m"].mean() - test["fwd_12m"].mean()) if len(g) else None,
                    "test_n": int(m.sum()),
                    "holds": bool(len(g) >= 100 and g["winner"].mean() / bw_t > 1.2
                                  and g["fwd_12m"].mean() > test["fwd_12m"].mean())})
    return out


def label(c):
    k, side = c
    d = DESCRIBE.get(k, (k, k))
    return d[1] if side == "top" else f"lowest on: {d[0].lower()}"


def write_md(out, path):
    L = ["# What makes a winner? — every S&P 500 stock, every month since 1997\n",
         f"_Generated {out['generated'][:16].replace('T', ' ')} UTC. {out['n_obs']:,} stock-months. "
         f"A **winner** is in the top 5% of all S&P 500 stocks over the next 12 months; a **loser** "
         f"the bottom 5%. Everything describing a stock uses only what was known on the start date._\n",
         "## 1. The biggest 12-month runs\n",
         "What each looked like on the day the run started.\n",
         "| Stock | Start | Next 12m | Past year | vs 12m high | Volatility | Gross profit / assets | "
         "Sales growth | Earnings yield |",
         "|---|---|---|---|---|---|---|---|---|"]
    fmt = lambda v, f: "—" if v is None or not np.isfinite(v) else format(v, f)   # noqa: E731
    for r in out["biggest"]:
        L.append(f"| {r['ticker']} | {r['date'][:7]} | {r['fwd_12m']:+.0%} | "
                 f"{fmt(r.get('ret_12_1'), '+.0%')} | {fmt(r.get('dist_52w_high'), '+.0%')} | "
                 f"{fmt(r.get('volatility'), '.0%')} | {fmt(r.get('gross_profitability'), '.0%')} | "
                 f"{fmt(r.get('revenue_growth'), '+.0%')} | {fmt(r.get('earnings_yield'), '+.1%')} |")
    L += ["\n## 2. The winner's profile — pattern by pattern\n",
          "**How to read:** '×1.5 winners' means stocks in the top fifth on that measure were 1.5 "
          "times as likely as average to become a top-5% winner. Always read it next to the "
          "loser column: a pattern that raises BOTH is a gamble, not an edge. 'Years' = in how "
          "many years the top fifth produced more winners than average.\n",
          "| Pattern (top fifth) | Winners' typical value | Everyone | Losers' typical value | "
          "Winner odds | Loser odds | Avg next 12m (top fifth) | Avg next 12m (bottom fifth) | Years it held |",
          "|---|---|---|---|---|---|---|---|---|"]
    for p in sorted(out["profile"], key=lambda p: -(p["p_win_top"] - p["p_lose_top"])):
        k = p["feature"]
        f = ".0%" if k not in ("rsi14", "beta", "size", "rel_volume") else ".2f"
        L.append(f"| **{DESCRIBE.get(k, (k, k))[1]}** — {DESCRIBE.get(k, (k,))[0]} (from {p['since'][:4]}) | "
                 f"{format(p['winners_median'], f)} | {format(p['everyone_median'], f)} | "
                 f"{format(p['losers_median'], f)} | ×{p['p_win_top']:.2f} | ×{p['p_lose_top']:.2f} | "
                 f"{p['avg_12m_top']:+.1%} | {p['avg_12m_bottom']:+.1%} | "
                 f"{p['years_top_favoured']} of {p['years']} |")
    L += ["\n## 3. Combinations — found on 1997–2011, then tested on 2012–now\n",
          "Hundreds of pairs were searched on the early years; these were the best there. The "
          "right-hand columns are the honest part: the same pair on later years it never saw.\n",
          "| Pattern pair | Winner odds (found) | Loser odds (found) | Winner odds (TEST) | "
          "Loser odds (TEST) | Extra return (TEST) | Stocks (TEST) | Held up? |",
          "|---|---|---|---|---|---|---|---|"]
    for c in out["combos"]:
        L.append(f"| {label(c['a'])} + {label(c['b'])} | ×{c['discover_p_win']:.2f} | "
                 f"×{c['discover_p_lose']:.2f} | "
                 f"{'—' if c['test_p_win'] is None else '×' + format(c['test_p_win'], '.2f')} | "
                 f"{'—' if c['test_p_lose'] is None else '×' + format(c['test_p_lose'], '.2f')} | "
                 f"{'—' if c['test_excess_12m'] is None else format(c['test_excess_12m'], '+.1%')} | "
                 f"{c['test_n']:,} | {'**YES**' if c['holds'] else 'no'} |")
    L += ["\n## 4. Where winners came from — sector mix by period\n",
          "| Period | Top sectors among winners (share of winners) |", "|---|---|"]
    for per, s in out["sectors"].items():
        L.append(f"| {per} | {s} |")
    L.append("\n---\n_Bias: most companies that went bust have no price or accounts data, so "
             "losers are under-counted. Accounts data starts in 2010._")
    path.write_text("\n".join(L) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--delisted", default="data/delisted/delisted_weekly.parquet")
    ap.add_argument("--fundamentals", default="data/fundamentals.parquet")
    ap.add_argument("--earnings", default="data/earnings_dates.csv")
    ap.add_argument("--labels", default=dp.CONSTITUENTS)
    ap.add_argument("--out", default="data/winners_study.json")
    ap.add_argument("--md", default="docs/WINNERS.md")
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
        feats = features(C, V, spy, member, lab, a.fundamentals, a.earnings)
        names = [k for k in DESCRIBE if k in feats]
        print("features:", names, flush=True)
        S = sample(C, member, {k: feats[k] for k in names}, spy)
        out["n_obs"] = int(len(S))
        big = (S.sort_values("fwd_12m", ascending=False).drop_duplicates("ticker").head(30))
        out["biggest"] = [{**{k: (float(v) if isinstance(v, (float, np.floating)) else v)
                              for k, v in r.items() if not k.endswith("_q")},
                           "date": str(r["date"].date())}
                          for r in big[["ticker", "date", "fwd_12m"] + names].to_dict("records")]
        out["profile"] = profile(S, names)
        out["combos"] = combos(S, names)
        W = S[S["winner"]].assign(sec=lambda d: d["ticker"].map(lab).fillna("not in today's index"))
        out["sectors"] = {}
        for per, lo, hi in (("1997–2003", 1997, 2003), ("2004–2009", 2004, 2009),
                            ("2010–2016", 2010, 2016), ("2017–2025", 2017, 2026)):
            w = W[(W["date"].dt.year >= lo) & (W["date"].dt.year <= hi)]
            vc = w["sec"].value_counts(normalize=True).head(4)
            out["sectors"][per] = ", ".join(f"{k} {v:.0%}" for k, v in vc.items())
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
        Path(a.md).write_text("# Winners study FAILED\n\n```\n" + "\n".join(out["traceback"]) + "\n```\n")
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
