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
    ("12 slots instead of 10", "Position size", {"SLOTS": 12}),
    ("swap out a holding below the top 30% for a newcomer", "Full slots", {"SWAP_BELOW": 0.70}),
    ("swap out a holding below the top 20% for a newcomer", "Full slots", {"SWAP_BELOW": 0.80}),
    ("swap out a holding below the top 10% for a newcomer", "Full slots", {"SWAP_BELOW": 0.90}),
    # FAST LANE: the core 10 keep 80-90% of the money under the live rules; a small
    # second pot of 3 slots buys after ONE week in the top 5% and sells after ONE weak week
    ("fast lane: 10% of the money, 3 stocks, in and out after 1 week", "Fast risers",
     {"sleeve": (0.10, {"SLOTS": 3}, 1, 1)}),
    ("fast lane: 20% of the money, 3 stocks, in and out after 1 week", "Fast risers",
     {"sleeve": (0.20, {"SLOTS": 3}, 1, 1)}),
    ("fast lane: 20%, 3 stocks, sold once out of the top 25%", "Fast risers",
     {"sleeve": (0.20, {"SLOTS": 3, "EXIT_PCT": 0.75}, 1, 1)}),
    ("core buys after 2 weeks in the top 5% (not 3)", "Fast risers", {"enter_after": 2}),
    ("core buys after 1 week in the top 5% (not 3)", "Fast risers", {"enter_after": 1}),
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


SPECIAL = ("confirm", "cash", "sleeve", "enter_after")


def run_one(sig, Cff, spy, member, start, switch, bond, enter=None, exit_=None):
    """val.run, optionally with a different number of weeks to BUY / to SELL."""
    orig = fs.commit_portfolio
    if enter or exit_:
        def patched(*a, **k):
            if enter:
                fs.CONFIRM_CHECKS = enter
            if exit_:
                fs.EXIT_CONFIRM = exit_
            return orig(*a, **k)
        fs.commit_portfolio = patched
    try:
        return val.run(sig, Cff, spy, member, start, switch, bond, delay=1)
    finally:
        fs.commit_portfolio = orig


def run_variant(st, sig, Cff, spy, member, start, switch, bond):
    """One run of a challenger: plain, faster entry, or core + fast-lane pot."""
    if "sleeve" not in st:
        return run_one(sig, Cff, spy, member, start, switch, bond, enter=st.get("enter_after"))
    share, over, en, ex = st["sleeve"]
    try:
        fs.START = POT * (1 - share)                                  # the core 10, live rules
        e1, t1 = run_one(sig, Cff, spy, member, start, switch, bond)
        saved = {a: getattr(fs, a) for a in over}
        for a, v in over.items():
            setattr(fs, a, v)
        try:
            fs.START = POT * share                                    # the fast lane
            e2, t2 = run_one(sig, Cff, spy, member, start, switch, bond, enter=en, exit_=ex)
        finally:
            for a, v in saved.items():
                setattr(fs, a, v)
    finally:
        fs.START = POT
    e1, e2 = e1.astype(float), e2.astype(float)
    eq = e1 + e2.reindex(e1.index).ffill().fillna(POT * share)
    t = dict(t1)
    t["trades_per_year"] = round((t1.get("trades_per_year") or 0) + (t2.get("trades_per_year") or 0), 1)
    return eq, t


def evaluate(sig, Cff, spy, member, bond, idx, first, mid, starts, st=None):
    st = st or {}
    switch = bp.market_state(spy).shift(1).fillna(True).astype(bool).values
    eq, t = run_variant(st, sig, Cff, spy, member, first, switch, bond)
    eq = eq.astype(float)
    s = spy.reindex(eq.index)
    halves = {}
    for lab, a, b in (("1997-2011", eq.index[0], idx[mid]), ("2011-2026", idx[mid], eq.index[-1])):
        e, sp_ = eq.loc[a:b], s.loc[a:b]
        halves[lab] = {"strategy": POT * float(e.iloc[-1] / e.iloc[0]), "spy": POT * float(sp_.iloc[-1] / sp_.iloc[0])}
    tens = []
    st_ = st
    for st in starts:
        e2, _ = run_variant(st_, sig, Cff, spy, member, st, switch, bond)
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


def email_html(out: dict, base: dict, passed: list, streak: dict) -> str:
    """Phone-friendly email: verdict first, then the passers, near misses and the full list."""
    import html as _h
    e = _h.escape
    F = "font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;"
    MUT = "color:#57606a"
    lh, rh = base["halves"]["1997-2011"]["strategy"], base["halves"]["2011-2026"]["strategy"]

    def diff(v, b):
        d = v - b
        if abs(d) < 1:
            return f'<span style="color:#57606a;font-size:13px">same</span>'
        col = "#1a7f37" if d > 0 else "#cf222e"
        return f'<span style="color:{col};font-size:13px">{"+" if d > 0 else "−"}{gbp(abs(d))}</span>'

    def why_not(v):
        bits = []
        if v["halves"]["1997-2011"]["strategy"] <= lh:
            bits.append("lost 1997–2011")
        if v["halves"]["2011-2026"]["strategy"] <= rh:
            bits.append("lost 2011–2026")
        if v["ten_median"] <= base["ten_median"]:
            bits.append("lower typical 10 years")
        if v["ten_beat"] < base["ten_beat"] - 0.03:
            bits.append("beat the S&P less often")
        return ", ".join(bits) or "—"

    def card(name, v, colour, tag):
        h = v["halves"]
        cells = [("1997–2011", h["1997-2011"]["strategy"], lh), ("2011–2026", h["2011-2026"]["strategy"], rh),
                 ("Typical 10 years", v["ten_median"], base["ten_median"])]
        rows = "".join(f'<tr><td style="padding:4px 0;{MUT}">{lab}</td><td style="padding:4px 0;text-align:right">'
                       f'<b>{gbp(x)}</b> {diff(x, b)}</td></tr>' for lab, x, b in cells)
        return (f'<div style="border-left:6px solid {colour};background:#f6f8fa;border-radius:6px;padding:10px 12px;'
                f'margin:0 0 10px"><div style="font-weight:700">{e(name)}</div>'
                f'<div style="font-size:13px;{MUT};margin-bottom:4px">{tag}</div>'
                f'<table style="width:100%;border-collapse:collapse;font-size:15px">{rows}'
                f'<tr><td style="padding:4px 0;{MUT}">Worst fall</td><td style="padding:4px 0;text-align:right">'
                f'{v["max_fall"]:.0%} <span style="font-size:13px;{MUT}">(live {base["max_fall"]:.0%})</span></td></tr>'
                f'</table></div>')

    ready = [n for n in passed if streak.get(n, 0) >= 3]
    if ready:
        bg, fg, msg = "#dafbe1", "#1a7f37", (f"{ready[0]} has passed 3 months running. Worth a serious look — "
                                             "nothing changes unless you decide to switch.")
    elif passed:
        bg, fg, msg = "#fff8c5", "#9a6700", (f"{len(passed)} challenger{'s' if len(passed) > 1 else ''} beat the live "
                                             "rules this month. Not enough yet: it needs 3 months running.")
    else:
        bg, fg, msg = "#f6f8fa", "#1f2328", "Nothing beat the live rules this month. Keep them."
    B = [f'<div style="{F}color:#1f2328;max-width:600px;margin:0 auto;padding:8px;font-size:16px;line-height:1.45">',
         '<div style="font-size:22px;font-weight:700">Strategy challengers</div>',
         f'<div style="{MUT};margin-bottom:12px">{e(out["generated"][:10])} · £10,000 from {e(out["from"][:4])} · '
         f'{out["companies"]} companies incl. failed ones</div>',
         f'<div style="background:{bg};color:{fg};border-radius:8px;padding:10px 12px;font-weight:700;'
         f'margin-bottom:16px">{e(msg)}</div>',
         '<div style="font-size:18px;font-weight:700;margin:0 0 8px">The live rules</div>',
         f'<table style="width:100%;border-collapse:collapse;font-size:15px;margin-bottom:6px">'
         f'<tr><td style="padding:4px 0;{MUT}">1997–2011</td><td style="text-align:right"><b>{gbp(lh)}</b></td></tr>'
         f'<tr><td style="padding:4px 0;{MUT}">2011–2026</td><td style="text-align:right"><b>{gbp(rh)}</b></td></tr>'
         f'<tr><td style="padding:4px 0;{MUT}">Typical 10 years</td><td style="text-align:right"><b>'
         f'{gbp(base["ten_median"])}</b> <span style="font-size:13px;{MUT}">(S&amp;P {gbp(base["ten_spy_median"])})'
         f'</span></td></tr><tr><td style="padding:4px 0;{MUT}">Worst fall</td><td style="text-align:right">'
         f'{base["max_fall"]:.0%}</td></tr></table>']
    R = {n: v for n, v in out["results"].items() if n != LIVE and "error" not in v}
    if passed:
        B.append('<div style="font-size:18px;font-weight:700;margin:16px 0 8px">Passed this month</div>')
        for n in passed:
            k = streak.get(n, 1)
            B.append(card(n, R[n], "#1a7f37", f"✅ {k} of 3 months running · {e(R[n].get('group', ''))}"))
    misses = sorted((n for n in R if n not in passed), key=lambda n: -R[n]["ten_median"])[:3]
    if misses:
        B.append('<div style="font-size:18px;font-weight:700;margin:16px 0 8px">Closest misses</div>')
        for n in misses:
            B.append(card(n, R[n], "#d4a72c", "✗ " + e(why_not(R[n]))))
    B.append('<div style="font-size:18px;font-weight:700;margin:16px 0 8px">Every challenger</div>'
             '<table style="width:100%;border-collapse:collapse;font-size:14px">'
             f'<tr><th style="text-align:left;padding:6px 4px;border-bottom:2px solid #d0d7de;{MUT}">Challenger</th>'
             f'<th style="text-align:right;padding:6px 4px;border-bottom:2px solid #d0d7de;{MUT}">Typical 10y</th></tr>')
    for n, v in out["results"].items():
        if n == LIVE:
            continue
        td = "padding:7px 4px;border-bottom:1px solid #eaeef2;vertical-align:top"
        if "error" in v:
            B.append(f'<tr><td style="{td}">{e(n)}<div style="font-size:12px;color:#cf222e">error</div></td>'
                     f'<td style="{td}"></td></tr>')
            continue
        res = ("✅ passed" if n in passed else "✗ " + why_not(v))
        B.append(f'<tr><td style="{td}">{e(n)}<div style="font-size:12px;{MUT}">{e(res)}</div></td>'
                 f'<td style="{td};text-align:right;white-space:nowrap">{gbp(v["ten_median"])}<br>'
                 f'{diff(v["ten_median"], base["ten_median"])}</td></tr>')
    B.append(f'</table><div style="font-size:12px;{MUT};margin-top:12px">A challenger passes only if it beats the live '
             'rules in both halves of history and on a typical 10-year start. Nothing changes in your account by '
             'itself. Full table: docs/CHALLENGERS.md.</div></div>')
    return "".join(B)


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
    defaults = {a: getattr(fs, a) for _, _, st in CHALLENGERS for a in st if a not in SPECIAL}
    out = {"generated": pd.Timestamp.now("UTC").isoformat(), "broker": bp.BROKER_NAME,
           "from": str(idx[first].date()), "to": str(idx[-1].date()), "companies": int(C.shape[1]),
           "results": {}}
    for name, group, st in [(LIVE, "", {})] + CHALLENGERS:
        try:
            for a, v in st.items():
                if a not in SPECIAL:
                    setattr(fs, a, v)
            bp.dp.CONFIRM = st.get("confirm", confirm0)
            bond = cash_when_weak(bond0) if st.get("cash") else bond0
            r = evaluate(sig, Cff, spy, member, bond, idx, first, mid, starts, st)
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
    # streaks count MONTHS, not runs: extra manual runs in a month must not
    # look like extra months of evidence. The last run of each month counts.
    by_month = {}
    for r in rows:
        by_month[r["run"][:7]] = r
    monthly = [by_month[m] for m in sorted(by_month)]
    streak = {n: 0 for n, _, _ in CHALLENGERS}
    for n in streak:
        for r in reversed(monthly):
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
    for f in ("CHALLENGERS_EMAIL.md", "CHALLENGERS_EMAIL.html", "CHALLENGERS_SUBJECT.txt"):
        Path("docs", f).unlink(missing_ok=True)
    if passed:
        ready = [n for n in passed if streak.get(n, 0) >= 3]
        Path("docs/CHALLENGERS_SUBJECT.txt").write_text(
            ("Strategy: a change has passed 3 months running - " + ready[0] if ready else
             f"Strategy: {len(passed)} challenger(s) beat the live rules this month") + "\n")
        Path("docs/CHALLENGERS_EMAIL.md").write_text("\n".join(L) + "\n")
        Path("docs/CHALLENGERS_EMAIL.html").write_text(email_html(out, base, passed, streak))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
