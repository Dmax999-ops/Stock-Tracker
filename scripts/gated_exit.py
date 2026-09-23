#!/usr/bin/env python3
"""
Don't sell a winner having a wobble. Do sell a loser dying.

THE PROBLEM, STATED EXACTLY
---------------------------
Running the textbook trend rules on the holdings gave a table that was perfectly
monotonic in outcome:

    NVDA    hold GBP 667,931   50/200 cross GBP 441,455    holding won
    MSFT    hold GBP  53,137   50/200 cross GBP  37,745    holding won
    ...
    ZOO.L   hold GBP   1,589   >200d        GBP  10,850    the rule won
    LIT.L   hold GBP     346   50/200 cross GBP   9,276    the rule won, 27x

Every stock that rose, holding beat the rule. Every stock that fell, the rule
beat holding, sometimes enormously. So a trend filter is not a return signal at
all -- it is INSURANCE. It charges a premium on the winners and pays out on the
losers, and across a basket dominated by one NVDA the premium swamps the payout.

That makes the objective precise, and it is not "find a better entry". It is:

    KEEP THE PAYOUT. STOP PAYING THE PREMIUM.

Which requires answering one question at the moment a sell triggers: is this a
strong stock having a normal drawdown, or a weak one beginning to die? Those
look identical in the price alone -- both are "below the 200-day average" --
but they are not identical in the information available at the time.

THE GATES
---------
Each gate is a reason to OVERRIDE a sell signal and keep holding. All are
computable on the day, none look forward.

    rs70      the stock's 12-month return is in the top 30% of the universe
              TODAY. Falling 20% while the market falls 25% is strength.
              Falling 20% while the market rises is not.
    slope     the 200-day average is still HIGHER than it was 60 days ago.
              Price below a RISING average is a pullback; price below a
              FALLING average is a downtrend. Same price, opposite meaning.
    near_ath  price is within 15% of its own 250-day high. A stock making
              new highs all year and dipping is not the same animal as one
              that has not seen its high in three years.
    relstr    the stock divided by the equal-weight index is above its own
              100-day average -- it is still outperforming while falling.
    any2      at least two of the four agree.
    all4      all four agree. The strictest veto, sells the most.

THE TEST THAT DECIDES IT
------------------------
Not the average. The average is what misled me for weeks: on a distribution
where one NVDA returns 67x and one LIT.L returns 0.03x, the mean answers a
question nobody asked.

Instead every stock is sorted into DECILES BY ITS OWN OUTCOME, and the gate is
judged on whether it does two things at once:

    in the TOP deciles   the gate should recover most of what the ungated rule
                         gave away -- it should stop selling the winners
    in the BOTTOM deciles the gate should keep nearly all of the ungated rule's
                         protection -- it should still sell the dying

A gate that helps the top by wrecking the bottom has simply turned the filter
off. A gate that keeps the bottom but not the top has done nothing. Both are
reported so neither can hide.

AND THE PROCEDURE IS CALIBRATED BEFORE IT IS BELIEVED
------------------------------------------------------
Twenty-one arms is twenty-one chances to get lucky. --calibrate runs the whole
thing on panels of pure random walks, where by construction no gate can know
anything, and reports how often it declares a winner. The portfolio simulator
fired on 36% of random walks before that check was added to it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

START = 10_000.0
COST = 0.0010           # charged on every switch, in or out
SEED = 20260927


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

def build(C: np.ndarray, Hh: np.ndarray, Ll: np.ndarray) -> dict:
    """Everything the rules need, as (days x tickers) arrays, no look-ahead."""
    df = pd.DataFrame(C)
    ma50 = df.rolling(50, min_periods=50).mean().to_numpy()
    ma200 = df.rolling(200, min_periods=200).mean().to_numpy()
    slope = ma200 > pd.DataFrame(ma200).shift(60).to_numpy()
    hi250 = pd.DataFrame(Hh).rolling(250, min_periods=100).max().to_numpy()
    lo20 = pd.DataFrame(Ll).shift(1).rolling(20, min_periods=20).min().to_numpy()

    # 12-month return, ranked ACROSS the universe on each day. The rank is what
    # matters: "up 5%" means something different in 2009 than in 2021.
    r252 = df.pct_change(252).to_numpy()
    rank = pd.DataFrame(r252).rank(axis=1, pct=True).to_numpy()

    # equal-weight index of everything trading, and each stock against it
    with np.errstate(invalid="ignore"):
        ret = df.pct_change().to_numpy()
    idx_ret = np.nanmean(np.where(np.isfinite(ret), ret, np.nan), axis=1)
    idx = np.cumprod(1 + np.nan_to_num(idx_ret))
    rel = C / idx[:, None]
    rel_ma = pd.DataFrame(rel).rolling(100, min_periods=100).mean().to_numpy()

    return {
        "ma50": ma50, "ma200": ma200, "slope": slope,
        "hi250": hi250, "lo20": lo20, "rank": rank,
        "rel": rel, "rel_ma": rel_ma, "ret": ret,
    }


def triggers(C, S) -> dict[str, np.ndarray]:
    return {
        "below200":    C < S["ma200"],
        "death_cross": S["ma50"] < S["ma200"],
        "donchian20":  C < S["lo20"],
    }


def gates(C, S) -> dict[str, np.ndarray]:
    g1 = S["rank"] >= 0.70
    g2 = S["slope"]
    g3 = C >= 0.85 * S["hi250"]
    g4 = S["rel"] > S["rel_ma"]
    for g in (g1, g2, g3, g4):
        np.nan_to_num(g, copy=False)
    cnt = (g1.astype(int) + g2.astype(int) + g3.astype(int) + g4.astype(int))
    return {"none": np.zeros_like(g1, bool),
            "rs70": g1, "slope": g2, "near_ath": g3, "relstr": g4,
            "any2": cnt >= 2, "all4": cnt >= 4}


def walk_state(exit_sig: np.ndarray, reenter: np.ndarray) -> np.ndarray:
    """
    In the market unless told otherwise. Vectorised across tickers, looped over
    days, because the state depends on yesterday and there is no way round that.
    """
    nd, nt = exit_sig.shape
    st = np.ones(nt, bool)
    out = np.empty((nd, nt), bool)
    for t in range(nd):
        st = (st & ~exit_sig[t]) | (~st & reenter[t])
        out[t] = st
    return out


def equity(ret: np.ndarray, state: np.ndarray, cost=COST):
    """GBP 10,000 per stock. Acts on yesterday's state, pays on every switch."""
    pos = np.vstack([np.ones((1, state.shape[1]), bool), state[:-1]])
    sw = np.vstack([np.zeros((1, state.shape[1]), bool), pos[1:] != pos[:-1]])
    r = np.where(pos, np.nan_to_num(ret), 0.0) - np.where(sw, cost, 0.0)
    eq = START * np.cumprod(1.0 + r, axis=0)
    return eq, sw.sum(axis=0), pos.mean(axis=0)


# ---------------------------------------------------------------------------

def run_panel(C, Hh, Ll, valid) -> tuple[dict, np.ndarray]:
    S = build(C, Hh, Ll)
    T, G = triggers(C, S), gates(C, S)
    ret = np.nan_to_num(S["ret"])
    reenter = np.nan_to_num(C > S["ma200"])

    hold_eq = START * np.cumprod(1 + ret, axis=0)
    arms = {"buy_and_hold": {"final": hold_eq[-1], "switches": np.zeros(C.shape[1]),
                             "invested": np.ones(C.shape[1])}}
    for tn, tv in T.items():
        tvv = np.nan_to_num(tv)
        for gn, gv in G.items():
            st = walk_state(tvv & ~gv, reenter)
            eq, sw, inv = equity(ret, st)
            arms[f"{tn}+{gn}"] = {"final": eq[-1], "switches": sw,
                                  "invested": inv}
    return arms, hold_eq[-1]


def summarise(arms, hold_final, valid, label="") -> dict:
    """Aggregate, plus the decile table that is the actual point."""
    dec = pd.qcut(pd.Series(hold_final[valid]).rank(method="first"),
                  10, labels=False)
    out = {}
    for name, a in arms.items():
        f = a["final"][valid]
        by = {}
        for d in range(10):
            m = (dec == d).to_numpy()
            if m.sum() >= 3:
                by[f"d{d+1}"] = {
                    "mean_gbp": float(np.mean(f[m])),
                    "median_gbp": float(np.median(f[m])),
                    "vs_hold_pct": float(np.mean(f[m]) /
                                         np.mean(hold_final[valid][m]) - 1),
                }
        out[name] = {
            "mean_gbp": float(np.mean(f)),
            "median_gbp": float(np.median(f)),
            "beat_hold": int((f > hold_final[valid]).sum()),
            "stocks": int(valid.sum()),
            "mean_switches": float(np.mean(a["switches"][valid])),
            "pct_time_invested": float(np.mean(a["invested"][valid])),
            "by_outcome_decile": by,
        }
    return out


def load_panel(path):
    px = pd.read_parquet(path)
    px["date"] = pd.to_datetime(px["date"])
    w = {f: px.pivot_table(index="date", columns="ticker", values=f).sort_index()
         for f in ("high", "low", "close")}
    C = w["close"].to_numpy(float)
    return C, w["high"].to_numpy(float), w["low"].to_numpy(float), \
        list(w["close"].columns), w["close"].index


def synthetic(seed, n_tick=150, n=2600):
    rng = np.random.default_rng(seed)
    mkt = rng.normal(0.0002, 0.011, n)
    C = np.empty((n, n_tick)); Hh = np.empty_like(C); Ll = np.empty_like(C)
    for i in range(n_tick):
        r = 0.9 * mkt + rng.normal(0.0001, 0.018, n)
        c = 100 * np.exp(np.cumsum(r))
        C[:, i] = c
        Hh[:, i] = c * (1 + abs(rng.normal(0, 0.006, n)))
        Ll[:, i] = c * (1 - abs(rng.normal(0, 0.006, n)))
    return C, Hh, Ll


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/gated_exit_evidence.json")
    ap.add_argument("--calibrate", type=int, default=0)
    a = ap.parse_args()

    out_path = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)

    try:
        if a.calibrate:
            # HOW OFTEN DOES THIS FIRE ON NOTHING?
            print(f"calibrating on {a.calibrate} random-walk panels")
            fired, rows = 0, []
            for p in range(a.calibrate):
                C, Hh, Ll = synthetic(700 + p)
                valid = np.isfinite(C[-1])
                arms, hf = run_panel(C, Hh, Ll, valid)
                s = summarise(arms, hf, valid)
                best = max((k for k in s if k != "buy_and_hold"),
                           key=lambda k: s[k]["mean_gbp"])
                hit = bool(s[best]["mean_gbp"] > s["buy_and_hold"]["mean_gbp"])
                fired += hit
                rows.append({"panel": p, "best_arm": best,
                             "best_mean": s[best]["mean_gbp"],
                             "hold_mean": s["buy_and_hold"]["mean_gbp"],
                             "declared": hit})
                print(f"  panel {p:2}  best {best:22} "
                      f"{s[best]['mean_gbp']:>10,.0f} vs hold "
                      f"{s['buy_and_hold']['mean_gbp']:>10,.0f}"
                      f"{'   FIRED' if hit else ''}", flush=True)
            rate = fired / max(a.calibrate, 1)
            print(f"\n  FALSE POSITIVE RATE: {fired}/{a.calibrate} = {rate:.0%}")
            out_path.write_text(json.dumps(
                {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
                 "mode": "calibration", "panels": a.calibrate,
                 "false_positives": fired, "false_positive_rate": rate,
                 "detail": rows}, indent=2, default=str))
            return 0

        C, Hh, Ll, cols, idx = load_panel(a.prices)
        valid = np.isfinite(C[-1]) & (np.isfinite(C).sum(axis=0) > 500)
        print(f"{C.shape[1]} tickers, {C.shape[0]:,} days, "
              f"{idx[0].date()} -> {idx[-1].date()}; {valid.sum()} usable")

        arms, hold_final = run_panel(C, Hh, Ll, valid)
        res = summarise(arms, hold_final, valid)

        print(f"\n  GBP 10,000 per stock, {valid.sum()} stocks")
        print(f"  {'arm':24}{'mean':>12}{'median':>12}{'beat hold':>11}"
              f"{'switches':>10}{'in mkt':>8}")
        for k in sorted(res, key=lambda x: -res[x]["mean_gbp"]):
            v = res[k]
            print(f"  {k:24}{v['mean_gbp']:>12,.0f}{v['median_gbp']:>12,.0f}"
                  f"{v['beat_hold']:>7}/{v['stocks']:<3}"
                  f"{v['mean_switches']:>10.1f}{v['pct_time_invested']:>8.0%}")

        # ---- THE TABLE THAT DECIDES IT --------------------------------
        print("\n  BY OUTCOME DECILE — % vs buy-and-hold in that decile")
        print("  d1 = the worst tenth of stocks, d10 = the best tenth")
        print(f"  {'arm':24}" + "".join(f"{'d'+str(i):>8}" for i in range(1, 11)))
        for k in [x for x in res if x != "buy_and_hold"]:
            by = res[k]["by_outcome_decile"]
            line = f"  {k:24}"
            for i in range(1, 11):
                v = by.get(f"d{i}")
                line += f"{v['vs_hold_pct']:>+8.0%}" if v else f"{'-':>8}"
            print(line)

        # A gate is only interesting if it does BOTH jobs. Score it on the two
        # ends: how much protection survives at the bottom, how much premium
        # stops being paid at the top.
        score = {}
        for k in [x for x in res if x != "buy_and_hold"]:
            by = res[k]["by_outcome_decile"]
            bot = np.mean([by[f"d{i}"]["vs_hold_pct"] for i in (1, 2, 3)
                           if f"d{i}" in by]) if by else None
            top = np.mean([by[f"d{i}"]["vs_hold_pct"] for i in (8, 9, 10)
                           if f"d{i}" in by]) if by else None
            if bot is not None and top is not None:
                score[k] = {"bottom3_vs_hold": float(bot),
                            "top3_vs_hold": float(top),
                            "mean_gbp": res[k]["mean_gbp"]}
        print(f"\n  {'arm':24}{'protects losers':>18}{'costs winners':>16}")
        for k in sorted(score, key=lambda x: -score[x]["bottom3_vs_hold"]):
            v = score[k]
            print(f"  {k:24}{v['bottom3_vs_hold']:>+18.0%}"
                  f"{v['top3_vs_hold']:>+16.0%}")

        ungated = {t: score.get(f"{t}+none") for t in
                   ("below200", "death_cross", "donchian20")}
        best = None
        for k, v in score.items():
            t = k.split("+")[0]
            u = ungated.get(t)
            if not u or k.endswith("+none"):
                continue
            # keeps most of the protection, gives back most of the premium
            keeps = v["bottom3_vs_hold"] >= 0.7 * u["bottom3_vs_hold"]
            cheaper = v["top3_vs_hold"] > u["top3_vs_hold"]
            if keeps and cheaper:
                gain = v["top3_vs_hold"] - u["top3_vs_hold"]
                if best is None or gain > best[1]:
                    best = (k, gain, v, u)
        if best:
            k, gain, v, u = best
            verdict = (
                f"THE GATE WORKS AS DESIGNED: {k} keeps "
                f"{v['bottom3_vs_hold']:+.0%} protection on the worst stocks "
                f"(ungated {u['bottom3_vs_hold']:+.0%}) while costing only "
                f"{v['top3_vs_hold']:+.0%} on the best (ungated "
                f"{u['top3_vs_hold']:+.0%}) — {gain:+.0%} of premium recovered.")
        else:
            verdict = ("NO GATE DID BOTH JOBS. Every veto that stopped selling "
                       "the winners also stopped selling the losers, which is "
                       "just turning the filter off. The insurance cannot be "
                       "made selective by these four signals.")
        print(f"\n  {verdict}")

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "start_gbp": START, "cost_per_switch": COST,
             "from": str(idx[0].date()), "to": str(idx[-1].date()),
             "stocks": int(valid.sum()), "arms": res,
             "gate_scores": score, "verdict": verdict,
             "CAVEAT": "Survivor-tilted until the delisting register completes. "
                       "The missing companies are the ones that died, which is "
                       "exactly where a trend filter pays most — so every "
                       "number here UNDERSTATES the gated rules."},
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
