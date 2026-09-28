#!/usr/bin/env python3
"""
CHALLENGERS -- every month, try to beat the live rules.

Each challenger changes ONE thing from the live strategy and is run on the
full history (S&P 500 members at the time, delisted companies included --
this list grows as the delisted archive fills), GBP 10,000, Trading 212
costs, one-day trading delay.

A challenger PASSES only if it beats the live rules in BOTH halves of history
(1997-2011 and 2011-2026) AND on a typical 10-year start, without winning
noticeably fewer starts. Passing does not change anything by itself: you get
an email, and the switch is your decision.

Results: docs/CHALLENGERS.md (and data/challengers.json, with history in
data/challengers_log.jsonl so a challenger that passes month after month
stands out from one that passed once by luck).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_vs = importlib.util.spec_from_file_location("validation", HERE / "validation.py")
val = importlib.util.module_from_spec(_vs)
_vs.loader.exec_module(val)
fs, bp = val.fs, val.bp

POT = 10_000.0
EVERY_WEEKS = 13          # a start every quarter since 2000, each followed for 10 years
LIVE = "live rules"

# name, group, settings -- settings are module attributes of factor_screen, plus
# the two special keys "confirm" (market switch closes) and "cash" (cash when bonds fall)
CHALLENGERS = [
    ("sell below 66% instead of 50%", "Sell rule", {"EXIT_PCT": 0.66}),
    ("sell below 75% instead of 50%", "Sell rule", {"EXIT_PCT": 0.75}),
    ("cash when bonds are falling too", "Market switch", {"cash": True}),
    ("market switch after 2 closes", "Market switch", {"confirm": 2}),
    ("market switch after 5 closes", "Market switch", {"confirm": 5}),
    ("max 2 holdings moving together", "Diversify", {"CORR_CAP": (0.6, 2, 126)}),
    ("sell on a break of 13-week support", "Technical", {"TA_SUPPORT_WEEKS": 13}),
    ("sell on a break of 26-week support", "Technical", {"TA_SUPPORT_WEEKS": 26}),
    ("below 50-day average counts as a weak week", "Technical", {"TA_WEAK_BELOW_MA": 50}),
    ("below 100-day average counts as a weak week", "Technical", {"TA_WEAK_BELOW_MA": 100}),
    ("don't buy over 30% above the 50-day average", "Technical", {"TA_MAX_STRETCH": 0.30}),
    ("don't buy over 50% above the 50-day average", "Technical", {"TA_MAX_STRETCH": 0.50}),
    ("only buy within 10% of the 52-week high", "Technical", {"TA_NEAR_HIGH": 0.10}),
    ("trailing stop 25% from the high", "Technical", {"TRAIL_STOP": 0.25}),
    ("trim any holding above 15% of the account", "Position size", {"TRIM_MAX": 0.15}),
    ("trim any holding above 20% of the account", "Position size", {"TRIM_MAX": 0.20}),
    ("trim any holding above 25% of the account", "Position size", {"TRIM_MAX": 0.25}),
]


def gbp(v: float) -> str:
    return f"£{v:,.0f}" if v >= 0 else f"−£{-v:,.0f}"


def load():
    C, _ = bp.load_panel("data/prices.parquet", "data/delisted/delisted_weekly.parquet")
    C = C.loc[:, C.notna().sum() > 260]
    member = bp.membership_mask(C.index, list(C.columns))
    spy = bp.load_spy(C.index)
    keep = C.index >= spy.first_valid_index()
    C, member, spy = C.loc[keep], member[keep], spy.loc[keep]
    try:
        bond = pd.read_csv("data/etf_prices.csv", index_col=0, parse_dates=True)["VFITX"].reindex(C.index).ffill()
    except Exception:                                              # noqa: BLE001
        bond = None
    if bond is None or bond.isna().mean() > 0.5:
        bond = pd.Series(1.02 ** (np.arange(len(C)) / 252), index=C.index)
    return C, member, spy, bond.bfill().values


def cash_when_weak(bond: np.ndarray) -> np.ndarray:
    b = pd.Series(bond)
    weak = (b < b.rolling(200, min_periods=200).mean()).shift(1, fill_value=False).to_numpy(bool)
    r = b.pct_change().fillna(0).to_numpy().copy()
    r[weak] = 0.0
    return np.cumprod(1 + r) * float(b.iloc[0])


def evaluate(sig, Cff, spy, member, bond, idx, first, mid, starts):
    switch = bp.market_state(spy).shift(1).fillna(True).astype(bool).values
    eq, t = val.run(sig, Cff, spy, member, first, switch, bond, delay=1)
    eq = eq.astype(float)
    s = spy.reindex(eq.index)
    halves = {}
    for lab, a, b in (("1997-2011", eq.index[0], idx[mid]), ("2011-2026", idx[mid], eq.index[-1])):
        e, sp_ = eq.loc[a:b], s.loc[a:b]
        halves[lab] = {"strategy": POT * float(e.iloc[-1] / e.iloc[0]), "spy": POT * float(sp_.iloc[-1] / sp_.iloc[0])}
    tens = []
    for st in starts:
        e2, _ = val.run(sig, Cff, spy, member, st, switch, bond, delay=1)
        e2 = e2.astype(float)
        end = idx[st] + pd.DateOffset(years=10)
        e2 = e2[e2.index <= end]
        tens.append((float(e2.iloc[-1] / POT), float(spy[spy.index <= end].iloc[-1] / spy.iloc[st])))
    g = np.array(tens)
    return {"whole": POT * float(eq.iloc[-1] / eq.iloc[0]), "spy_whole": POT * float(s.iloc[-1] / s.iloc[0]),
            "max_fall": float((eq / eq.cummax() - 1).min()), "trades_per_year": t.get("trades_per_year"),
            "halves": halves, "ten_median": POT * float(np.median(g[:, 0])),
            "ten_p10": POT * float(np.percentile(g[:, 0], 10)),
            "ten_spy_median": POT * float(np.median(g[:, 1])), "ten_beat": float((g[:, 0] > g[:, 1]).mean())}


def main() -> int:
    C, member, spy, bond0 = load()
    Cff = C.ffill()
    sig = Cff / Cff.rolling(200, min_periods=200).mean() - 1
    cnt = (sig.notna().to_numpy() & member).sum(axis=1)
    idx = C.index
    first = next(i for i in range(260, len(idx)) if cnt[i] >= 100)
    mid = idx.searchsorted(pd.Timestamp("2011-01-01"))
    wk = pd.Series(np.arange(len(idx)), index=idx).groupby(idx.to_period("W-FRI")).first()
    starts = [int(i) for i in wk if i >= first and idx[i] >= pd.Timestamp("2000-01-01")
              and idx[i] <= idx[-1] - pd.DateOffset(years=10)][::EVERY_WEEKS]
    fs.START = POT
    confirm0 = bp.dp.CONFIRM
    defaults = {a: getattr(fs, a) for _, _, st in CHALLENGERS for a in st if a not in ("confirm", "cash")}
    out = {"generated": pd.Timestamp.now("UTC").isoformat(), "broker": bp.BROKER_NAME,
           "from": str(idx[first].date()), "to": str(idx[-1].date()), "companies": int(C.shape[1]),
           "results": {}}
    for name, group, st in [(LIVE, "", {})] + CHALLENGERS:
        try:
            for a, v in st.items():
                if a not in ("confirm", "cash"):
                    setattr(fs, a, v)
            bp.dp.CONFIRM = st.get("confirm", confirm0)
            bond = cash_when_weak(bond0) if st.get("cash") else bond0
            r = evaluate(sig, Cff, spy, member, bond, idx, first, mid, starts)
            r["group"] = group
            out["results"][name] = r
            print(name, round(r["ten_median"]), r["halves"], flush=True)
        except Exception as e:                                     # noqa: BLE001
            out["results"][name] = {"error": f"{type(e).__name__}: {e}", "group": group}
            print(name, "FAILED", e, flush=True)
        finally:
            for a, v in defaults.items():
                setattr(fs, a, v)
            bp.dp.CONFIRM = confirm0
    base = out["results"][LIVE]
    passed = []
    for name, v in out["results"].items():
        if name == LIVE or "error" in v:
            continue
        ok = (v["halves"]["1997-2011"]["strategy"] > base["halves"]["1997-2011"]["strategy"]
              and v["halves"]["2011-2026"]["strategy"] > base["halves"]["2011-2026"]["strategy"]
              and v["ten_median"] > base["ten_median"] and v["ten_beat"] >= base["ten_beat"] - 0.03)
        v["passed"] = ok
        if ok:
            passed.append(name)
    out["passed"] = passed

    # history: how often has each challenger passed?
    logp = Path("data/challengers_log.jsonl")
    rows = [json.loads(x) for x in logp.read_text().splitlines() if x.strip()] if logp.exists() else []
    rows.append({"run": out["generated"][:10], "companies": out["companies"], "passed": passed,
                 "live_ten_median": round(base["ten_median"])})
    logp.parent.mkdir(parents=True, exist_ok=True)
    logp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    streak = {n: 0 for n, _, _ in CHALLENGERS}
    for n in streak:
        for r in reversed(rows):
            if n in r["passed"]:
                streak[n] += 1
            else:
                break

    L = ["# Challengers — can anything beat the live rules?\n",
         f"_Run {out['generated'][:10]}. £10,000, {out['broker']} costs, one-day delay, {out['from']} to {out['to']}, "
         f"{out['companies']} companies (S&P 500 members at the time, including ones that later failed). "
         "Each challenger changes one thing._\n",
         "A challenger **passes** only if it beats the live rules in both halves of history and on a typical "
         "10-year start. Passing never changes anything by itself.\n",
         "| Challenger | Type | 1997–2011 | 2011–2026 | 10 years, typical | Starts beating S&P | Worst fall | Result |",
         "|---|---|---|---|---|---|---|---|"]

    def row(name, v):
        if "error" in v:
            return f"| {name} | {v.get('group', '')} | — | — | — | — | — | error |"
        h = v["halves"]
        res = ("—" if name == LIVE else
               (f"✅ PASSED ({streak.get(name, 1)} month{'s' if streak.get(name, 1) != 1 else ''} running)"
                if v.get("passed") else "no"))
        return (f"| {'**' + name + '**' if name == LIVE else name} | {v.get('group', '')} | "
                f"{gbp(h['1997-2011']['strategy'])} | {gbp(h['2011-2026']['strategy'])} | {gbp(v['ten_median'])} | "
                f"{v['ten_beat']:.0%} | {v['max_fall']:.0%} | {res} |")
    for name, v in out["results"].items():
        L.append(row(name, v))
    h = base["halves"]
    L.append(f"| *S&P 500 tracker* | | {gbp(h['1997-2011']['spy'])} | {gbp(h['2011-2026']['spy'])} | "
             f"{gbp(base['ten_spy_median'])} | | | |")
    L += ["", "## Verdict\n",
          ("**Passed this month:** " + ", ".join(passed)
           + ". Wait for a challenger to pass **3 months running** before switching, so a lucky month is not "
             "mistaken for an improvement." if passed else
           "**Nothing beat the live rules this month.** Keep them.")]
    Path("docs/CHALLENGERS.md").write_text("\n".join(L) + "\n")
    Path("data/challengers.json").write_text(json.dumps(out, indent=2, default=str))

    # email only when something passed
    for f in ("CHALLENGERS_EMAIL.md", "CHALLENGERS_SUBJECT.txt"):
        Path("docs", f).unlink(missing_ok=True)
    if passed:
        ready = [n for n in passed if streak.get(n, 0) >= 3]
        Path("docs/CHALLENGERS_SUBJECT.txt").write_text(
            ("Strategy: a change has passed 3 months running - " + ready[0] if ready else
             f"Strategy: {len(passed)} challenger(s) beat the live rules this month") + "\n")
        Path("docs/CHALLENGERS_EMAIL.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
