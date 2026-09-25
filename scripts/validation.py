#!/usr/bin/env python3
"""
CAN WE TRUST IT WITH REAL MONEY? Every check a sceptical fund manager would ask for.

The strategy (scripts/strategy.py): S&P 500 stocks furthest above their 200-day
average, bought after 3 weekly confirmations, sold after 3 weekly confirmations
of weakness, market switch into bonds. It passed the stress tests
(docs/ROBUSTNESS*.md). These are the checks those did NOT cover:

  1. TRADING DELAY  The backtest bought at the same close the signal was read
                    from. In real life you see Friday's close, then trade on
                    Monday. Re-run with a 1 and a 2 trading-day delay.
  2. CHECK DAY      Is Friday special? Re-run checking on Monday, Tuesday,
                    Wednesday, Thursday -- and DAILY, with the confirmations
                    scaled to the same three weeks (15 trading days).
  3. DOUBLE COSTS   Every deal charge and FX fee doubled (wider spreads, worse
                    prices than the closing price).
  4. ANY 5 YEARS    Every rolling 5-year period since 1997: in how many did it
                    beat the S&P 500? This is what investing for 5 years from a
                    random start date would have felt like.
  5. BOOTSTRAP      2,000 simulated 10-year futures built from reshuffled
                    one-year blocks of its real history: the chance it trails
                    the S&P 500 over 10 years.
  6. LEARNING       The honest test of "keep looking for new strategies as the
                    market changes": a SELECTOR that, each January from 2006,
                    looks back 8 years at every candidate strategy, picks the one
                    that beat the S&P most consistently, and holds it for the
                    next year only -- never seeing the future. If the selector
                    beats the S&P on those unseen years, re-selecting works. If
                    it does not, re-selecting is chasing noise.

Results: docs/VALIDATION.md (docs/VALIDATION_100k.md), data/validation*.json
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
_spec = importlib.util.spec_from_file_location("fs", HERE / "factor_screen.py")
fs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fs)
bp = fs.bp

MAIN = "trend_200"
LOOKBACK_YEARS = 8
BOOT_N, BOOT_YEARS = 2000, 10


def run(sig, Cff, spy, member, start, switch, bond, delay=0, check_idx=None, confirm=3,
        every=5, cost_mult=1.0):
    s, sw = sig, switch
    if delay:
        s = sig.shift(delay)
        sw = np.r_[np.ones(delay, bool), switch[:-delay]]
    fs.CONFIRM_CHECKS, fs.EXIT_CONFIRM, fs.CHECK_EVERY = confirm, confirm, every
    deal0, fx0 = fs.DEAL, bp.fx_cost
    if cost_mult != 1.0:
        fs.DEAL = deal0 * cost_mult
        bp.fx_cost = lambda v, f=fx0, m=cost_mult: f(v) * m
    try:
        eq, t = fs.commit_portfolio(s, Cff, spy, member, start, True, sw, bond, check_idx=check_idx)
    finally:
        fs.DEAL, bp.fx_cost = deal0, fx0
        fs.CONFIRM_CHECKS, fs.EXIT_CONFIRM, fs.CHECK_EVERY = 3, 3, 5
    return eq, t


def summary(eq, spy, split):
    m = fs.money(eq, spy, split)
    return {"gbp": m["all"]["gbp_from_10k"], "spy_gbp": m["all"]["spy_gbp_from_10k"],
            "cagr": m["all"]["cagr"], "spy_cagr": m["all"]["spy_cagr"],
            "worst": m["all"]["worst"],
            "first": m["first"]["cagr"] - m["first"]["spy_cagr"],
            "second": m["second"]["cagr"] - m["second"]["spy_cagr"],
            "beats": bool(m["first"]["cagr"] - m["first"]["spy_cagr"] >= fs.MARGIN
                          and m["second"]["cagr"] - m["second"]["spy_cagr"] >= fs.MARGIN)}


def yearly_returns(eq: pd.Series) -> pd.Series:
    last = eq.groupby(eq.index.year).last()
    first = eq.iloc[0]
    prev = last.shift(1)
    prev.iloc[0] = first
    return last / prev - 1


def rolling_windows(eq, spy, years=5):
    e = eq.copy()
    s = spy.reindex(e.index).ffill()
    wins, n = 0, 0
    worst = None
    step = 13                                      # weekly marks -> quarterly starts
    span = int(52 * years)
    for a in range(0, len(e) - span, step):
        b = a + span
        ce = e.iloc[b] / e.iloc[a]
        cs = s.iloc[b] / s.iloc[a]
        d = ce ** (1 / years) - cs ** (1 / years)
        wins += d > 0
        n += 1
        worst = d if worst is None else min(worst, d)
    return {"windows": n, "beat": int(wins), "share": wins / n if n else None, "worst_gap": worst}


def bootstrap(eq, spy, rng):
    ys = yearly_returns(eq).iloc[1:-1]             # full calendar years only
    ss = yearly_returns(spy.reindex(eq.index).ffill()).reindex(ys.index)
    pairs = np.c_[ys.to_numpy(), ss.to_numpy()]
    idx = rng.integers(0, len(pairs), size=(BOOT_N, BOOT_YEARS))
    g = np.prod(1 + pairs[idx], axis=1)
    return {"p_trail_10y": float((g[:, 0] < g[:, 1]).mean()),
            "median_strategy_10y": float(np.median(g[:, 0])),
            "median_sp500_10y": float(np.median(g[:, 1])),
            "p_loses_money_10y": float((g[:, 0] < 1).mean())}


def selector(curves: dict, spy: pd.Series, first_year=2006):
    """Each January pick the candidate with the best trailing record; hold it a year."""
    yr = {k: yearly_returns(v) for k, v in curves.items()}
    sp = yearly_returns(spy.reindex(next(iter(curves.values())).index).ffill())
    out, picks = [], []
    prev = None
    for y in range(first_year, int(sp.index.max()) + 1):
        hist = range(y - LOOKBACK_YEARS, y)
        best, best_score = None, -np.inf
        for k, r in yr.items():
            if not all(h in r.index for h in hist) or y not in r.index:
                continue
            ex = np.array([r[h] - sp[h] for h in hist])
            # consistency first: share of years ahead, then average lead
            score = (ex > 0).mean() + ex.mean()
            if score > best_score:
                best, best_score = k, score
        if best is None:
            continue
        ret = yr[best][y]
        if prev is not None and best != prev:
            ret -= 0.02                            # switching strategy ~ a full portfolio turnover
        out.append({"year": y, "picked": best, "ret": float(ret), "sp500": float(sp[y])})
        prev = best
    df = pd.DataFrame(out)
    if df.empty:
        return {}
    g = float(np.prod(1 + df["ret"])) ; gs = float(np.prod(1 + df["sp500"]))
    n = len(df)
    return {"years": out, "cagr": g ** (1 / n) - 1, "spy_cagr": gs ** (1 / n) - 1,
            "gbp": fs.START * g, "spy_gbp": fs.START * gs,
            "years_ahead": int((df["ret"] > df["sp500"]).sum()), "n": n,
            "fixed_main": None}


def write_md(out, path):
    pot = out["pot_gbp"]
    b = out["base"]
    L = ["# Can we trust it? — validation of the live strategy\n",
         f"_Generated {out['generated'][:16].replace('T', ' ')} UTC. £{pot:,.0f} pot, HL costs, "
         f"{out['from']} → {out['to']}. Strategy: S&P 500 stocks furthest above their 200-day "
         f"average, commit rules, market switch._\n",
         f"**Baseline (as tested before):** £{b['gbp']:,} vs £{b['spy_gbp']:,} in the S&P 500 "
         f"({b['cagr']:+.1%}/yr vs {b['spy_cagr']:+.1%}/yr; worst fall {b['worst']:.0%}).\n",
         "## 1–3. Trading delay, check day, double costs\n",
         "| Test | £ | Yearly | vs S&P, first half | vs S&P, second half | Worst fall | Still beats S&P in both halves? |",
         "|---|---|---|---|---|---|---|"]
    for lab, r in out["variants"]:
        L.append(f"| {lab} | £{r['gbp']:,} | {r['cagr']:+.1%} | {r['first']:+.1%}/yr | "
                 f"{r['second']:+.1%}/yr | {r['worst']:.0%} | {'**yes**' if r['beats'] else 'no'} |")
    w = out["rolling5"]
    L += ["\n## 4. Any 5 years\n",
          f"Of {w['windows']} five-year periods (starting every quarter since the start), the strategy "
          f"beat the S&P 500 in **{w['beat']}** ({w['share']:.0%}). Its worst 5-year period vs the S&P 500: "
          f"{w['worst_gap']:+.1%} a year.\n"]
    bt = out["bootstrap"]
    L += ["## 5. 2,000 simulated 10-year futures\n",
          f"Built from reshuffled calendar years of its own history (paired with the S&P 500's "
          f"return in the same year). Chance it **trails** the S&P 500 over 10 years: "
          f"**{bt['p_trail_10y']:.0%}**. Chance it **loses money** over 10 years: "
          f"{bt['p_loses_money_10y']:.0%}. Typical outcome for £{pot:,.0f}: "
          f"£{pot * bt['median_strategy_10y']:,.0f} vs £{pot * bt['median_sp500_10y']:,.0f} in the S&P 500.\n"]
    s = out.get("selector") or {}
    if s:
        L += ["## 6. Does re-selecting the strategy each year work? (\"keep learning\")\n",
              f"Each January from {s['years'][0]['year']}, a selector looked back {LOOKBACK_YEARS} "
              f"years at all {out['n_candidates']} candidate strategies, picked the most consistent "
              f"winner, and held it for one year it had not seen.\n",
              f"| | £{pot:,.0f} became | Yearly | Years ahead of S&P |", "|---|---|---|---|",
              f"| **Selector (re-picks every year)** | £{s['gbp']:,.0f} | {s['cagr']:+.1%} | "
              f"{s['years_ahead']} of {s['n']} |",
              f"| Fixed: {MAIN} throughout | £{out['fixed_same_years']['gbp']:,.0f} | "
              f"{out['fixed_same_years']['cagr']:+.1%} | {out['fixed_same_years']['ahead']} of {s['n']} |",
              f"| S&P 500 | £{s['spy_gbp']:,.0f} | {s['spy_cagr']:+.1%} | |",
              "\n| Year | Selector picked | Its return | S&P 500 |", "|---|---|---|---|"]
        for y in s["years"]:
            L.append(f"| {y['year']} | {y['picked']} | {y['ret']:+.1%} | {y['sp500']:+.1%} |")
    L += ["\n## Verdict\n", out["verdict"]]
    path.write_text("\n".join(L) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--delisted", default="data/delisted/delisted_weekly.parquet")
    ap.add_argument("--etfs", default="data/etf_prices.csv")
    ap.add_argument("--fundamentals", default="data/fundamentals.parquet")
    ap.add_argument("--earnings", default="data/earnings_dates.csv")
    ap.add_argument("--out", default="data/validation.json")
    ap.add_argument("--md", default="docs/VALIDATION.md")
    ap.add_argument("--spy-csv", default="")
    ap.add_argument("--no-membership", action="store_true")
    a = ap.parse_args()
    if fs.START != 10_000:
        tag = f"_{int(fs.START / 1000)}k"
        a.out, a.md = a.out.replace(".json", f"{tag}.json"), a.md.replace(".md", f"{tag}.md")
    out = {"generated": pd.Timestamp.now("UTC").isoformat(), "pot_gbp": fs.START}
    try:
        C, info = bp.load_panel(a.prices, a.delisted)
        C = C.loc[:, C.notna().sum() > 260]
        member = (np.ones(C.shape, bool) if a.no_membership
                  else bp.membership_mask(C.index, list(C.columns)))
        spy = (pd.read_csv(a.spy_csv, index_col=0, parse_dates=True).iloc[:, 0].reindex(C.index).ffill()
               if a.spy_csv else bp.load_spy(C.index))
        keep = C.index >= spy.first_valid_index()
        C, member, spy = C.loc[keep], member[keep], spy.loc[keep]
        Cff = C.ffill()
        try:
            bond = pd.read_csv(a.etfs, index_col=0, parse_dates=True)["VFITX"].reindex(C.index).ffill()
        except Exception:                                          # noqa: BLE001
            bond = None
        if bond is None or bond.isna().mean() > 0.5:
            bond = pd.Series(1.02 ** (np.arange(len(C)) / 252), index=C.index)
        bond = bond.bfill().values
        switch = bp.market_state(spy).shift(1).fillna(True).astype(bool).values
        firsts = pd.Series(np.arange(len(C)), index=C.index).groupby(C.index.to_period("M")).first()
        dates = [int(i) for i in firsts if i >= 260]
        sigs = fs.build_signals(C)
        try:
            sigs.update(fs.build_fund_signals(C, sigs["mom_12_1"], a.fundamentals, a.earnings, spy))
        except Exception:                                          # noqa: BLE001
            pass
        try:
            g = fs.build_group_signals(C, None)
            sigs["rise_weak_peers"] = g["rise_weak_peers"]
        except Exception:                                          # noqa: BLE001
            pass
        sig = sigs[MAIN]
        cnt = (sig.notna().to_numpy() & member).sum(axis=1)
        d_sig = [i for i in dates if cnt[i] >= 100]
        start, split = d_sig[0], C.index[d_sig[len(d_sig) // 2]]
        out.update({"from": str(C.index[start].date()), "to": str(C.index[-1].date())})

        eq0, _ = run(sig, Cff, spy, member, start, switch, bond)
        out["base"] = summary(eq0, spy, split)
        print("base", out["base"], flush=True)
        wd = pd.Series(np.arange(len(C)), index=C.index)
        variants = []
        for d in (1, 2):
            e, _ = run(sig, Cff, spy, member, start, switch, bond, delay=d)
            variants.append((f"Trade {d} day{'s' if d > 1 else ''} after the signal", summary(e, spy, split)))
        for day, name in ((0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday")):
            idx = list(wd[wd.index.weekday == day].to_numpy())
            e, _ = run(sig, Cff, spy, member, start, switch, bond, delay=1, check_idx=idx)
            variants.append((f"Check every {name}, trade next day", summary(e, spy, split)))
        e, _ = run(sig, Cff, spy, member, start, switch, bond, delay=1, confirm=15, every=1)
        variants.append(("Check DAILY (15-day confirmation), trade next day", summary(e, spy, split)))
        e, _ = run(sig, Cff, spy, member, start, switch, bond, delay=1, cost_mult=2.0)
        variants.append(("Double costs, trade next day", summary(e, spy, split)))
        out["variants"] = variants
        for lab, r in variants:
            print(lab, r, flush=True)

        eq_real, _ = run(sig, Cff, spy, member, start, switch, bond, delay=1)
        out["rolling5"] = rolling_windows(eq_real, spy, 5)
        out["bootstrap"] = bootstrap(eq_real, spy, np.random.default_rng(7))

        curves = {}
        for name, s in sigs.items():
            if name == "random":
                continue
            c = (s.notna().to_numpy() & member).sum(axis=1)
            ds = [i for i in dates if c[i] >= 100]
            if len(ds) < 36:
                continue
            e, _ = run(s, Cff, spy, member, ds[0], switch, bond, delay=1)
            curves[name] = e
            print("candidate", name, flush=True)
        out["n_candidates"] = len(curves)
        sel = selector(curves, spy)
        out["selector"] = sel
        if sel:
            yrs = [y["year"] for y in sel["years"]]
            ym = yearly_returns(eq_real).reindex(yrs)
            out["fixed_same_years"] = {"gbp": fs.START * float(np.prod(1 + ym)),
                                       "cagr": float(np.prod(1 + ym)) ** (1 / len(ym)) - 1,
                                       "ahead": int(sum(ym[y] > s_["sp500"] for y, s_ in zip(yrs, sel["years"])))}
        ok_delay = all(r["beats"] for lab, r in variants if "after the signal" in lab)
        ok_days = sum(r["beats"] for lab, r in variants if lab.startswith("Check")) >= 5
        ok_cost = next(r["beats"] for lab, r in variants if lab.startswith("Double"))
        ok_roll = out["rolling5"]["share"] is not None and out["rolling5"]["share"] >= 0.6
        ok_boot = out["bootstrap"]["p_trail_10y"] <= 0.25
        checks = {"survives a trading delay": ok_delay, "not tied to one check day": ok_days,
                  "survives double costs": ok_cost, "beats S&P in 60%+ of 5-year periods": ok_roll,
                  "under 25% chance of trailing over 10 years": ok_boot}
        out["checks"] = checks
        passed = sum(checks.values())
        lines = [f"- {'✅' if v else '❌'} {k}" for k, v in checks.items()]
        if sel:
            lines.append(f"- {'✅' if sel['cagr'] > sel['spy_cagr'] else '❌'} re-selecting each year "
                         f"beat the S&P on unseen years ({sel['cagr']:+.1%} vs {sel['spy_cagr']:+.1%}/yr)")
        out["verdict"] = (f"**{passed} of {len(checks)} trust checks passed.**\n\n" + "\n".join(lines) +
                          "\n\nPassing these makes it a candidate for real money; the final check is the "
                          "live forward record in data/strategy_log.jsonl, which no backtest can fake.")
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
        Path(a.md).write_text("# Validation FAILED\n\n```\n" + "\n".join(out["traceback"]) + "\n```\n")
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
