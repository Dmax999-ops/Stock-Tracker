#!/usr/bin/env python3
"""
IS THE WINNER REAL? Stress-testing the first stock picker to beat buy-and-hold.

WHAT PASSED (docs/FACTORS.md, section 2b)
-----------------------------------------
Momentum stock picks, run by the commit rules, with the market switch, beat
the S&P 500 in BOTH 1997-2011 and 2011-2026 after Hargreaves Lansdown costs,
with a smaller worst fall -- at both a GBP 10k and a GBP 100k pot:
    6-month momentum, 3-month momentum, distance above the 200-day average.

WHY THAT IS NOT YET PROOF
-------------------------
24 scores were tried. Some will look good by luck, and a result that depends
on one exact setting, a handful of stocks, or a few bad prices would not
survive real money. So each passing score is run again, many ways:

  1. SETTINGS   each commit rule nudged either way (slots 7/15, entry top 3%/8%,
                exit bottom 40%/60%, confirmation 2/4 weeks). A real effect
                survives small changes; a tuned fluke does not.
  2. UNIVERSES  10 runs, each on a random 80% of the stocks. If the result needs
                a few particular companies, this exposes it.
  3. CLEAN DATA  every stock that ever moved more than 60% in one day (often a bad
                price, a spin-off or a split error) removed.
  4. YEAR BY YEAR  every calendar year against the S&P 500.

A score is called ROBUST only if it beats the S&P 500 after costs, in both
halves, in at least 80% of all these runs.

Results: docs/ROBUSTNESS.md, data/robustness.json
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

CANDIDATES = ["mom_6_1", "mom_3", "trend_200"]
DEFAULTS = dict(SLOTS=10, ENTER_PCT=0.95, EXIT_PCT=0.50, CONFIRM_CHECKS=3)
NUDGES = [("SLOTS", 7), ("SLOTS", 15), ("ENTER_PCT", 0.97), ("ENTER_PCT", 0.92),
          ("EXIT_PCT", 0.40), ("EXIT_PCT", 0.60), ("CONFIRM_CHECKS", 2), ("CONFIRM_CHECKS", 4)]
N_SUB, SUB_FRAC = 10, 0.8
ROBUST_SHARE = 0.8


def set_rules(**kw):
    for k, v in {**DEFAULTS, **kw}.items():
        setattr(fs, k, v)
    fs.EXIT_CONFIRM = fs.CONFIRM_CHECKS


def run_one(sig, Cff, spy, member, start, split, switch, bond):
    eq, turn = fs.commit_portfolio(sig, Cff, spy, member, start, True, switch, bond)
    m = fs.money(eq, spy, split)
    ok = all(m.get(h) and m[h]["cagr"] >= m[h]["spy_cagr"] + fs.MARGIN for h in ("first", "second"))
    return eq, m, turn, bool(ok)


def yearly(eq, spy):
    rows = []
    for y, g in eq.groupby(eq.index.year):
        prev = eq[eq.index.year < y]
        a = g.iloc[-1] / (prev.iloc[-1] if len(prev) else g.iloc[0]) - 1
        s = spy.reindex(eq.index)
        sp = s[s.index.year < y]
        b = s[s.index.year == y].iloc[-1] / (sp.iloc[-1] if len(sp) else s[s.index.year == y].iloc[0]) - 1
        rows.append({"year": int(y), "strategy": float(a), "sp500": float(b)})
    return rows


def write_md(out, path):
    pot = out["pot_gbp"]
    L = ["# Is the winner real? — stress tests\n",
         f"_Generated {out['generated'][:16].replace('T', ' ')} UTC. £{pot:,.0f} pot, HL costs, commit "
         f"rules + market switch, {out['from']} → {out['to']}. **Robust** = beats the S&P 500 by "
         f"1%/yr after costs in BOTH halves in at least {ROBUST_SHARE:.0%} of all runs._\n",
         "| Score | Default run £ | S&P £ | Runs that beat S&P in both halves | Settings nudged | "
         "Random 80% universes | Clean data only | Verdict |",
         "|---|---|---|---|---|---|---|---|"]
    for name, r in out["scores"].items():
        b = r["base"]["money"]["all"]
        L.append(f"| {name} | £{b['gbp_from_10k']:,} | £{b['spy_gbp_from_10k']:,} | "
                 f"**{r['share']:.0%}** ({r['passed']} of {r['runs']}) | "
                 f"{sum(x['ok'] for x in r['nudges'])} of {len(r['nudges'])} | "
                 f"{sum(x['ok'] for x in r['subsets'])} of {len(r['subsets'])} | "
                 f"{'passes' if r['clean']['ok'] else 'fails'} | "
                 f"{'**ROBUST**' if r['robust'] else 'not robust'} |")
    for name, r in out["scores"].items():
        L += [f"\n## {name}: every setting and universe\n",
              "| Run | £ | First half vs S&P | Second half vs S&P | Worst fall | Trades / yr |",
              "|---|---|---|---|---|---|"]
        for lab, x in ([("default", r["base"])] + [(n["label"], n) for n in r["nudges"]]
                       + [(s["label"], s) for s in r["subsets"]] + [("clean data", r["clean"])]):
            m = x["money"]
            L.append(f"| {lab} | £{m['all']['gbp_from_10k']:,} | "
                     f"{m['first']['cagr'] - m['first']['spy_cagr']:+.1%}/yr | "
                     f"{m['second']['cagr'] - m['second']['spy_cagr']:+.1%}/yr | "
                     f"{m['all']['worst']:.0%} | {x['trades_per_year']} |")
    best = max(out["scores"], key=lambda k: out["scores"][k]["share"])
    L += [f"\n## Year by year — {best} (default settings) vs the S&P 500\n",
          "| Year | Strategy | S&P 500 | Ahead? |", "|---|---|---|---|"]
    for y in out["scores"][best]["years"]:
        L.append(f"| {y['year']} | {y['strategy']:+.1%} | {y['sp500']:+.1%} | "
                 f"{'yes' if y['strategy'] > y['sp500'] else 'no'} |")
    ys = out["scores"][best]["years"]
    L.append(f"\nAhead of the S&P 500 in {sum(y['strategy'] > y['sp500'] for y in ys)} of {len(ys)} years.")
    L.append(f"\n**Clean data** removed {out['clean_removed']} stocks with a one-day move above 60%.")
    path.write_text("\n".join(L) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--delisted", default="data/delisted/delisted_weekly.parquet")
    ap.add_argument("--etfs", default="data/etf_prices.csv")
    ap.add_argument("--out", default="data/robustness.json")
    ap.add_argument("--md", default="docs/ROBUSTNESS.md")
    ap.add_argument("--spy-csv", default="")
    ap.add_argument("--no-membership", action="store_true")
    a = ap.parse_args()
    if fs.START != 10_000:
        tag = f"_{int(fs.START / 1000)}k"
        a.out, a.md = a.out.replace(".json", f"{tag}.json"), a.md.replace(".md", f"{tag}.md")
    out = {"generated": pd.Timestamp.now("UTC").isoformat(), "pot_gbp": fs.START, "scores": {}}
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
        # clean universe: drop stocks with any one-day move above 60%
        R = C.ffill(limit=10).pct_change(fill_method=None).abs()
        bad = R.max() > 0.6
        member_clean = member & ~bad.to_numpy()[None, :]
        out["clean_removed"] = int(bad.sum())
        rng = np.random.default_rng(2026)
        for name in CANDIDATES:
            sig = sigs[name]
            cnt = (sig.notna().to_numpy() & member).sum(axis=1)
            d_sig = [i for i in dates if cnt[i] >= 100]
            start, split = d_sig[0], C.index[d_sig[len(d_sig) // 2]]
            out.update({"from": str(C.index[start].date()), "to": str(C.index[-1].date())})
            set_rules()
            eq, m, t, ok = run_one(sig, Cff, spy, member, start, split, switch, bond)
            r = {"base": {"money": m, "ok": ok, "trades_per_year": t["trades_per_year"]},
                 "years": yearly(eq, spy), "nudges": [], "subsets": []}
            for k, v in NUDGES:
                set_rules(**{k: v})
                _, m, t, ok = run_one(sig, Cff, spy, member, start, split, switch, bond)
                r["nudges"].append({"label": f"{k}={v}", "money": m, "ok": ok,
                                    "trades_per_year": t["trades_per_year"]})
            set_rules()
            for n in range(N_SUB):
                keepc = rng.random(C.shape[1]) < SUB_FRAC
                _, m, t, ok = run_one(sig, Cff, spy, member & keepc[None, :], start, split, switch, bond)
                r["subsets"].append({"label": f"random 80% #{n + 1}", "money": m, "ok": ok,
                                     "trades_per_year": t["trades_per_year"]})
            _, m, t, ok = run_one(sig, Cff, spy, member_clean, start, split, switch, bond)
            r["clean"] = {"money": m, "ok": ok, "trades_per_year": t["trades_per_year"]}
            allruns = [r["base"]] + r["nudges"] + r["subsets"] + [r["clean"]]
            r["passed"] = sum(x["ok"] for x in allruns)
            r["runs"] = len(allruns)
            r["share"] = r["passed"] / r["runs"]
            r["robust"] = bool(r["share"] >= ROBUST_SHARE)
            out["scores"][name] = r
            print(f"{name}: {r['passed']}/{r['runs']} runs beat the S&P in both halves", flush=True)
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
        Path(a.md).write_text("# Robustness FAILED\n\n```\n" + "\n".join(out["traceback"]) + "\n```\n")
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
