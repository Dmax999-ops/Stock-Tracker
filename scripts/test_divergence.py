#!/usr/bin/env python3
"""
The only three setups that cleared the bar were all the same thing.
This asks whether that thing is what it claims to be.

WHAT THE 84-TEST RUN FOUND
--------------------------
Out of 84 tests across 622 stocks and 22 years, three passed, and the top four
by edge over random were the four members of one family:

    swing    macd_div_bull   edge +0.117R
    swing    rsi_div_bull    edge +0.108R
    position macd_div_bull   edge +0.100R
    position rsi_div_bull    edge +0.088R

Bullish divergence: price prints a LOWER swing low while the oscillator prints a
HIGHER one. The story is that selling pressure is exhausting even as price makes
a new low.

THE REASON TO DOUBT THE STORY
-----------------------------
Every divergence signal in that run fired exactly LOOKAHEAD bars after a
confirmed swing low -- because that is the first bar on which the swing low is
knowable. So each of those trades is, mechanically, "buy ten days after the
lowest low of a twenty-one day window". That is a mean-reversion timing device
all by itself, and the random control does not control for it: random entries
fire on random days, not on days ten bars after a confirmed bottom.

There is already a hint in the same results. Three families fire on exactly the
same clock, at exactly the same lag, and differ only in what they demand of the
price at the second pivot:

    divergence      the new low is LOWER than the last     edge +0.10 to +0.12
    double bottom   the new low is EQUAL to the last       edge +0.06
    structure up    the new low is HIGHER than the last    edge -0.02 to -0.03

The edge orders itself perfectly by how far price fell. Not by anything the
oscillator did. That is the signature of a depth-of-decline effect wearing an
oscillator as a hat.

HOW THIS SETTLES IT
-------------------
Nested arms, all fired on the identical bar with the identical machinery, so the
only thing that changes between them is the condition:

    piv_any        every confirmed swing low                 timing alone
    piv_lower      + the low is lower than the previous one  timing + depth
    piv_higher     + the low is higher than the previous one timing, no depth
    rsi_div        + RSI made a higher low        (the signal)
    rsi_conf       + RSI made a lower low         (the anti-signal)
    macd_div       + MACD made a higher low       (the signal)
    macd_conf      + MACD made a lower low        (the anti-signal)

`div` and `conf` partition `lower` exactly; `lower` and `higher` partition
`any`. Nothing is left over, so the arithmetic has nowhere to hide.

    edge(piv_any)                      how much is just the clock
    edge(piv_lower) - edge(piv_any)    how much is the depth of the fall
    edge(rsi_div)   - edge(piv_lower)  HOW MUCH THE OSCILLATOR ACTUALLY ADDS

That last line is the whole question. If it is near zero, divergence is not a
signal -- it is a slow, complicated way of noticing that a stock has fallen, and
the honest name for the finding is "buy the deeper low".

If it is materially positive, and rsi_div beats rsi_conf on the same bars, then
the oscillator is carrying real information and we have something to build on.

AND WHETHER YOU COULD ACTUALLY TRADE IT
---------------------------------------
Every arm is also run late, entering five and ten bars after the confirmation
bar. A bounce edge that has evaporated by the time you are a week late is not a
strategy anyone can run; one that survives being late is robust and forgiving.

Random entries in the same instruments, through the same stops and trails, are
the baseline for all of it, and the edge is reported with its own two-sample
t -- not the expectancy's t, which is the wrong statistic and flatters every
long strategy in a rising market.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quant import trades as TR                                # noqa: E402
from quant import patterns as PT                              # noqa: E402

RNG = np.random.default_rng(20260924)

LOOKAHEAD = PT.LOOKAHEAD          # 10 -- the lag a swing low needs to be knowable
MAX_GAP = 60                      # the two pivots must be within a quarter

HORIZONS = {
    "swing":    dict(k_stop=1.5, k_trail=2.0, max_hold=20),
    "position": dict(k_stop=2.5, k_trail=4.0, max_hold=120),
}
DELAYS = (0, 5, 10)               # bars late, on top of the confirmation lag
COST_US = 2 * 0.0004 + 2 * 1.0 / 10000

SPLIT = pd.Timestamp("2015-01-01")

ARMS = ("piv_any", "piv_lower", "piv_higher",
        "rsi_div", "rsi_conf", "macd_div", "macd_conf")


def required_t(n_tests: int) -> float:
    """The bar rises with the number of chances taken to get lucky."""
    return float(np.sqrt(2 * np.log(max(n_tests, 2))) + 1.0)


# ---------------------------------------------------------------------------

def arms_for(df: pd.DataFrame, delay: int) -> dict[str, pd.Series]:
    """
    Boolean series per arm, every one firing at pivot + LOOKAHEAD + delay.

    The pivot itself is found with a centred window, so bar p is only declared a
    swing low once bar p + LOOKAHEAD has printed. Firing on p would be reading
    the future; firing on p + LOOKAHEAD is the earliest honest moment.
    """
    n = len(df)
    low = df["low"]
    piv = PT.pivot_idx(low, LOOKAHEAD, "low")
    p = low.to_numpy(float)

    r = PT.rsi(df["close"]).to_numpy(float)
    ml, _ = PT.macd(df["close"])
    m = ml.to_numpy(float)

    hits = {k: np.zeros(n, bool) for k in ARMS}
    for i in range(1, len(piv)):
        a_, b_ = int(piv[i - 1]), int(piv[i])
        k = b_ + LOOKAHEAD + delay
        if b_ - a_ > MAX_GAP or k >= n - 2:
            continue

        hits["piv_any"][k] = True
        lower = p[b_] < p[a_]
        if lower:
            hits["piv_lower"][k] = True
        else:
            hits["piv_higher"][k] = True
            continue                       # oscillator arms are inside `lower`

        if np.isfinite(r[a_]) and np.isfinite(r[b_]):
            hits["rsi_div" if r[b_] > r[a_] else "rsi_conf"][k] = True
        if np.isfinite(m[a_]) and np.isfinite(m[b_]):
            hits["macd_div" if m[b_] > m[a_] else "macd_conf"][k] = True

    return {k: pd.Series(v, index=df.index) for k, v in hits.items()}


def random_entries(df: pd.DataFrame, n: int, rng) -> pd.Series:
    s = pd.Series(False, index=df.index)
    valid = np.arange(210, len(df) - 2)
    if len(valid) == 0 or n == 0:
        return s
    s.iloc[rng.choice(valid, size=min(n, len(valid)), replace=False)] = True
    return s


def contrast(a: dict, b: dict) -> tuple[float | None, float | None]:
    """
    Difference between two DISJOINT arms, with a proper two-sample t.

    Only ever applied to arms that share no trades: div against conf (both sit
    inside `lower` and partition it), and lower against higher (they partition
    `any`). Comparing an arm with a set it is contained in -- div against lower
    -- gives a difference worth reading but a t that cannot be computed this
    way, because the samples overlap. So the difference is reported there and
    the significance is taken from the disjoint comparison instead.
    """
    if not a or not b:
        return None, None
    d = a["expectancy_R"] - b["expectancy_R"]
    se = float(np.sqrt(a["var_R"] / max(a["trades"], 2)
                       + b["var_R"] / max(b["trades"], 2)))
    return d, (d / se if se > 0 else None)


def summarise(R: pd.DataFrame, Q: pd.DataFrame) -> dict:
    """One arm against its own random control, with the edge's own t."""
    mR, vR, nR = float(R.R.mean()), float(R.R.var(ddof=1)), len(R)
    out = {
        "trades": int(nR),
        "var_R": vR,
        "win_rate": float((R.R > 0).mean()),
        "expectancy_R": mR,
        "profit_factor": (float(R[R.R > 0].R.sum() / -R[R.R <= 0].R.sum())
                          if (R.R <= 0).any() else None),
        "avg_net_pct": float(R.net_pct.mean()),
        "median_bars": float(R.bars.median()),
    }
    ed = pd.to_datetime(R.entry_date)
    for half, sel in (("early", ed < SPLIT), ("late", ed >= SPLIT)):
        h = R[sel]
        out[half] = {"trades": int(len(h)),
                     "expectancy_R": float(h.R.mean()) if len(h) else None}

    if Q is None or Q.empty:
        return out
    mQ, vQ, nQ = float(Q.R.mean()), float(Q.R.var(ddof=1)), len(Q)
    se = float(np.sqrt(vR / max(nR, 2) + vQ / max(nQ, 2)))
    out["random_expectancy_R"] = mQ
    out["random_trades"] = int(nQ)
    out["edge_vs_random_R"] = mR - mQ
    # THE statistic. Not the expectancy's t -- that measures "was the market up",
    # which it was, for twenty-two years.
    out["edge_t"] = (mR - mQ) / se if se > 0 else None

    qd = pd.to_datetime(Q.entry_date)
    for half, sel_r, sel_q in (("early", ed < SPLIT, qd < SPLIT),
                               ("late", ed >= SPLIT, qd >= SPLIT)):
        hr, hq = R[sel_r], Q[sel_q]
        out[half]["random_expectancy_R"] = (float(hq.R.mean()) if len(hq) else None)
        out[half]["edge_vs_random_R"] = (
            float(hr.R.mean() - hq.R.mean()) if len(hr) and len(hq) else None)
    return out


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/divergence_evidence.json")
    a = ap.parse_args()

    out_path = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)

    try:
        px = pd.read_parquet(a.prices)
        px["date"] = pd.to_datetime(px["date"])
        frames = {t: g.sort_values("date").set_index("date")
                  for t, g in px.groupby("ticker") if len(g) >= 300}
        print(f"{len(frames)} instruments")

        n_tests = len(ARMS) * len(HORIZONS) * len(DELAYS)
        bar = required_t(n_tests)
        print(f"{n_tests} tests -> edge must clear t >= {bar:.2f}")

        # Signals cached once per (ticker, delay); recomputing them inside the
        # horizon loop is how the last script became needlessly slow.
        cache = {d: {t: arms_for(g, d) for t, g in frames.items()}
                 for d in DELAYS}
        print("signals built", flush=True)

        res: dict[str, dict] = {}
        for delay in DELAYS:
            for hname, hp in HORIZONS.items():
                for arm in ARMS:
                    real, rand = [], []
                    for t, g in frames.items():
                        sig = cache[delay][t][arm]
                        if not sig.any():
                            continue
                        tr = TR.simulate(g, sig, cost_pct=COST_US, **hp)
                        if tr.empty:
                            continue
                        real.append(tr)
                        rq = TR.simulate(g, random_entries(g, len(tr), RNG),
                                         cost_pct=COST_US, **hp)
                        if not rq.empty:
                            rand.append(rq)
                    if not real:
                        continue
                    R = pd.concat(real, ignore_index=True)
                    Q = pd.concat(rand, ignore_index=True) if rand else None
                    s = summarise(R, Q)
                    key = f"{hname}:d{delay}:{arm}"
                    res[key] = s
                    print(f"  {key:26} n={s['trades']:7,}  "
                          f"exp {s['expectancy_R']:+.3f}R  "
                          f"edge {s.get('edge_vs_random_R') or 0:+.3f}R  "
                          f"t {s.get('edge_t') or 0:+6.2f}", flush=True)

        # Partial results are worth more than none; the verdict comes after.
        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "status": "arms complete, decomposition pending",
             "lookahead": LOOKAHEAD, "delays": list(DELAYS),
             "significance_bar_t": bar, "n_tests": n_tests,
             "results": res}, indent=2, default=str))

        # ------------------------------------------------------------------
        # The decomposition. Each line is a difference between two arms that
        # fired on the same bars under the same rules, so the difference is
        # attributable to the condition and to nothing else.
        # ------------------------------------------------------------------
        decomp = {}
        for delay in DELAYS:
            for hname in HORIZONS:
                pre = f"{hname}:d{delay}:"
                g = lambda arm: (res.get(pre + arm) or {}).get("edge_vs_random_R")  # noqa: E731
                A = lambda arm: res.get(pre + arm)                    # noqa: E731
                any_, low_, high_ = g("piv_any"), g("piv_lower"), g("piv_higher")
                rd, rc = g("rsi_div"), g("rsi_conf")
                md, mc = g("macd_div"), g("macd_conf")
                d_rsi, t_rsi = contrast(A("rsi_div"), A("rsi_conf"))
                d_mac, t_mac = contrast(A("macd_div"), A("macd_conf"))
                d_dep, t_dep = contrast(A("piv_lower"), A("piv_higher"))
                decomp[f"{hname}:d{delay}"] = {
                    "clock_alone": any_,
                    "depth_adds": (None if None in (low_, any_) else low_ - any_),
                    "rsi_oscillator_adds": (None if None in (rd, low_) else rd - low_),
                    "macd_oscillator_adds": (None if None in (md, low_) else md - low_),
                    # The disjoint, properly testable contrasts.
                    "rsi_div_minus_conf": d_rsi, "rsi_div_minus_conf_t": t_rsi,
                    "macd_div_minus_conf": d_mac, "macd_div_minus_conf_t": t_mac,
                    "lower_minus_higher": d_dep, "lower_minus_higher_t": t_dep,
                }

        print("\n  DECOMPOSITION (edge over random, in R; last two are t-stats)")
        print(f"  {'window':18}{'clock':>9}{'depth':>9}{'RSI+':>9}{'MACD+':>9}"
              f"{'rsi d-c':>9}{'  t':>7}{'low-high':>10}{'  t':>7}")
        for k, v in decomp.items():
            f = lambda x: f"{x:+.3f}" if isinstance(x, float) else "    -"  # noqa: E731
            tt = lambda x: f"{x:+.2f}" if isinstance(x, float) else "   -"  # noqa: E731
            print(f"  {k:18}{f(v['clock_alone']):>9}{f(v['depth_adds']):>9}"
                  f"{f(v['rsi_oscillator_adds']):>9}{f(v['macd_oscillator_adds']):>9}"
                  f"{f(v['rsi_div_minus_conf']):>9}{tt(v['rsi_div_minus_conf_t']):>7}"
                  f"{f(v['lower_minus_higher']):>10}"
                  f"{tt(v['lower_minus_higher_t']):>7}")

        # ------------------------------------------------------------------
        # THE VERDICT, FIXED BEFORE THE RUN.
        #
        # The decisive comparison is divergence against CONFIRMATION: the same
        # confirmed lower lows, at the same lag, split by whether the oscillator
        # rose or fell. Disjoint samples, so the t is honest, and it is the
        # cleanest statement of the chartist's claim -- if a rising oscillator
        # at a lower low means anything, these two groups must differ.
        #
        # Requiring a real magnitude AND significance at the multiple-testing
        # bar. The first draft of this script demanded only magnitude, and duly
        # declared a random-walk panel a discovery.
        # ------------------------------------------------------------------
        cands = []
        for k, v in decomp.items():
            for osc_name in ("rsi", "macd"):
                d = v.get(f"{osc_name}_div_minus_conf")
                t = v.get(f"{osc_name}_div_minus_conf_t")
                if isinstance(d, float) and isinstance(t, float):
                    cands.append({"window": k, "oscillator": osc_name,
                                  "div_minus_conf_R": d, "t": t})
        best = max(cands, key=lambda x: x["t"]) if cands else None
        real_signal = bool(best and best["t"] >= bar and best["div_minus_conf_R"] >= 0.05)
        verdict = (
            f"THE OSCILLATOR CARRIES INFORMATION -- at {best['window']} the "
            f"{best['oscillator'].upper()} divergences beat the confirmations on "
            f"the same kind of bar by {best['div_minus_conf_R']:+.3f}R "
            f"(t {best['t']:+.2f}, bar {bar:.2f}). Divergence is a signal in its "
            f"own right, not a relabelled dip."
            if real_signal else
            "THE OSCILLATOR IS DECORATION -- divergences do no better than "
            "confirmations on the same confirmed lower lows. What is working is "
            "the depth of the fall and the timing of the entry, and the honest "
            "name for it is 'buy a confirmed lower low, ten bars later'. Build "
            "that, drop the indicator, and stop claiming a mechanism we cannot "
            "demonstrate.")
        if best:
            print(f"\n  strongest divergence-vs-confirmation contrast: "
                  f"{best['window']} {best['oscillator']} "
                  f"{best['div_minus_conf_R']:+.3f}R  t {best['t']:+.2f}  "
                  f"(bar {bar:.2f})")
        print(f"  {verdict}")
        best_osc = best["div_minus_conf_R"] if best else None

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "instruments": len(frames), "lookahead": LOOKAHEAD,
             "delays": list(DELAYS), "cost_pct": COST_US,
             "horizons": HORIZONS, "split": str(SPLIT.date()),
             "significance_bar_t": bar, "n_tests": n_tests,
             "decomposition": decomp,
             "div_vs_conf_contrasts": cands,
             "strongest_contrast": best,
             "oscillator_best_contribution_R": best_osc,
             "oscillator_is_real": real_signal,
             "verdict": verdict,
             "results": res}, indent=2, default=str))
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
