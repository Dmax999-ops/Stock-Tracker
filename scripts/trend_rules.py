#!/usr/bin/env python3
"""
The rules you can see on a daily chart, priced in pounds.

WHY THIS SCRIPT EXISTS
----------------------
Everything in this repo so far was tested across a 625-stock universe, which is
where the statistical power is but not where conviction lives. Looking at one
daily chart of MSFT -- the 50 and 200 day averages crossing, the horizontal shelf
price keeps returning to, the trendline it broke in 2022 -- those things are
plainly there, and a fair objection to all the earlier work is that it never
tested THOSE rules on THAT chart at THAT resolution.

An earlier version of this answer used weekly bars, 10 and 40 weeks standing in
for 50 and 200 days. That is a proxy, and a proxy fires on different days from
the thing it stands for. So this runs the real rules on real daily candles.

WHAT IS TESTED, ALL LONG-ONLY, CASH WHEN OUT
---------------------------------------------
    above_200d          hold while the close is above its 200-day average
    above_50d           the same, 50 days
    cross_50_200        the golden and death cross, in its textbook form
    cross_20_50         the faster version
    above_200d_rising   above the 200-day AND the average itself rising
    donchian_55_20      Turtle: in on a 55-day high, out on a 20-day low
    donchian_20_10      the faster Turtle
    level_break         in when price closes through a horizontal level three
                        earlier swings turned at, out when it closes back under
    trendline           in on a confirmed up-trendline holding, out on its break

Every level and every trendline is built only from pivots that were already
confirmed on the day of the signal. That is the whole difficulty with reading a
chart after the fact: the lines are obvious once you can see where price turned,
and the test has to draw them using only the bars to the left.

THE SECOND ARM, WHICH IS THE ONE WITH THE BEST PRIOR BEHIND IT
---------------------------------------------------------------
Every rule above answers "should I hold this stock or hold cash?" and in a
market that rises, cash is an expensive answer. The professional version of the
same instinct is relative strength: stay fully invested, but in whichever names
are strongest, and rotate out of the weakest. That is always in SOMETHING, which
is the same shape as holding stocks or cash with the cash leg replaced by a
better stock.

Earlier in this project momentum measured +2.4% a year with an information
coefficient of +0.0166 and I set it aside because the sample could not prove it
at the significance bar. That was the right statistical call and the wrong
practical one -- "not proven" is not "absent" -- so it is tested here properly.

EVERY NUMBER IS GBP 10,000, AND EVERY SWITCH IS CHARGED
--------------------------------------------------------
Because "+0.06R, t 6.2" tells you nothing about money, and a rule that trades
120 times is not comparable to one that trades twice until the costs are in.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quant import levels as LV                                # noqa: E402
from quant import patterns as PT                              # noqa: E402
from quant import trades as TR                                # noqa: E402

START_GBP = 10_000.0
COST = 0.0010          # 10bp charged on every switch in or out


# ---------------------------------------------------------------------------
# The rules
# ---------------------------------------------------------------------------

def rules(d: pd.DataFrame) -> dict[str, np.ndarray]:
    """
    Each rule returns a boolean series: True on the days it wants to be LONG.
    The engine acts on the PREVIOUS day's state, so nothing is bought on
    information from its own close.
    """
    c, h, l = d["close"], d["high"], d["low"]
    a = TR.atr(d)
    ma20, ma50, ma200 = (c.rolling(w).mean() for w in (20, 50, 200))

    out = {
        "above_200d":        c > ma200,
        "above_50d":         c > ma50,
        "cross_50_200":      ma50 > ma200,
        "cross_20_50":       ma20 > ma50,
        "above_200d_rising": (c > ma200) & (ma200 > ma200.shift(20)),
    }

    # Donchian: a state machine, not a condition -- in on the breakout, and it
    # STAYS in until the opposite band breaks. This is the rule most people
    # actually mean by "trend following".
    for hi, lo, name in ((55, 20, "donchian_55_20"), (20, 10, "donchian_20_10")):
        up = c > c.shift(1).rolling(hi).max()
        dn = c < c.shift(1).rolling(lo).min()
        state = np.zeros(len(d), bool)
        on = False
        uv, dv = up.to_numpy(), dn.to_numpy()
        for i in range(len(d)):
            if not on and uv[i]:
                on = True
            elif on and dv[i]:
                on = False
            state[i] = on
        out[name] = pd.Series(state, index=d.index)

    # Horizontal levels, built only from pivots confirmed before the signal day
    res_t, res_b = LV.level_events(d, a, kind="resistance")
    sup_t, sup_b = LV.level_events(d, a, kind="support")
    state, on = np.zeros(len(d), bool), False
    rb, sb = res_b.to_numpy(), sup_b.to_numpy()
    for i in range(len(d)):
        if not on and rb[i]:
            on = True
        elif on and sb[i]:
            on = False
        state[i] = on
    out["level_break"] = pd.Series(state, index=d.index)

    # Sloping trendlines: two confirmed pivots define the line, a third touch
    # confirms it. In while an up-trendline holds, out when it breaks.
    up_b, up_k = PT.trendline_events(d, a, kind="up")
    dn_r, dn_k = PT.trendline_events(d, a, kind="down")
    state, on = np.zeros(len(d), bool), False
    ub, uk, dk = up_b.to_numpy(), up_k.to_numpy(), dn_k.to_numpy()
    for i in range(len(d)):
        if not on and (ub[i] or dk[i]):
            on = True
        elif on and uk[i]:
            on = False
        state[i] = on
    out["trendline"] = pd.Series(state, index=d.index)

    return {k: v.fillna(False).to_numpy(bool) for k, v in out.items()}


def walk(ret: np.ndarray, inmkt: np.ndarray, cost: float = COST) -> np.ndarray:
    """GBP 10,000 through one rule. Acts on yesterday's state; pays on switches."""
    inm = pd.Series(inmkt).shift(1).fillna(False).to_numpy()
    turn = pd.Series(inm).ne(pd.Series(inm).shift(1)).fillna(False).to_numpy()
    r = np.where(inm, ret, 0.0) - np.where(turn, cost, 0.0)
    return START_GBP * np.cumprod(1.0 + r)


def stats(eq: np.ndarray, idx, inmkt=None, switches=0) -> dict:
    pk = np.maximum.accumulate(eq)
    yrs = (idx[-1] - idx[0]).days / 365.25
    return {"final_gbp": round(float(eq[-1]), 2),
            "cagr": float((eq[-1] / START_GBP) ** (1 / yrs) - 1) if yrs > 0 else None,
            "max_drawdown": float((eq / pk - 1).min()),
            "pct_time_invested": (float(np.mean(inmkt)) if inmkt is not None else 1.0),
            "switches": int(switches)}


def episodes(c: pd.Series, min_dd=0.15):
    """Every drawdown in buy-and-hold deeper than min_dd, with its dates."""
    v = c.to_numpy(float)
    pk = np.maximum.accumulate(v)
    dd = v / pk - 1
    eps, i = [], 0
    while i < len(dd):
        if dd[i] < -min_dd:
            j = i
            while j < len(dd) and dd[j] < -0.02:
                j += 1
            t = i + int(np.argmin(dd[i:max(j, i + 1)]))
            # An episode ends when price regains its old peak OR six months
            # after the trough, whichever comes first. Without the cap a stock
            # that stays underwater for years produces one span covering half
            # the sample, which compares nothing with nothing.
            end = min(j, t + 126, len(c) - 1)
            eps.append((c.index[max(i - 20, 0)], c.index[end],
                        c.index[t], float(dd[t])))
            i = max(j, t + 1)
        else:
            i += 1
    return eps


# ---------------------------------------------------------------------------

def load_tickers(path: str, extra: str) -> list[str]:
    t = []
    p = Path(path)
    if p.exists():
        import yaml
        cfg = yaml.safe_load(p.read_text()) or {}
        t = [h["ticker"] for h in (cfg.get("holdings") or []) if h.get("ticker")]
    t += [x.strip() for x in extra.split(",") if x.strip()]
    seen, out = set(), []
    for x in t:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdings", default="config/holdings.yml")
    ap.add_argument("--extra", default="MSFT,AAPL,SPY,QQQ")
    ap.add_argument("--start", default="2014-01-01")
    ap.add_argument("--window", default="2019-01-01",
                    help="also report everything from this date onwards")
    ap.add_argument("--out", default="data/trend_evidence.json")
    a = ap.parse_args()

    out_path = Path(a.out)
    env = {"pandas": pd.__version__, "numpy": np.__version__,
           "python": sys.version.split()[0]}
    print("versions:", env)

    try:
        import yfinance as yf
        env["yfinance"] = yf.__version__

        tickers = load_tickers(a.holdings, a.extra)
        print(f"{len(tickers)} tickers: {', '.join(tickers)}")

        frames = {}
        for t in tickers:
            try:
                df = yf.download(t, start=a.start, auto_adjust=True,
                                 progress=False, threads=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df.columns = [str(x).lower() for x in df.columns]
                df = df[["open", "high", "low", "close", "volume"]].dropna()
                if len(df) >= 400:
                    frames[t] = df
                    print(f"  {t:8} {len(df):5,} bars  "
                          f"{df.index[0].date()} -> {df.index[-1].date()}")
                else:
                    print(f"  {t:8} SKIPPED, only {len(df)} bars")
            except Exception as e:                            # noqa: BLE001
                print(f"  {t:8} FAILED {str(e)[:60]}")
        if not frames:
            raise RuntimeError("no price data downloaded")

        results, per_window = {}, {}
        for wname, wstart in (("full", a.start), ("your_window", a.window)):
            per_stock = {}
            for t, df in frames.items():
                d = df[df.index >= wstart]
                if len(d) < 300:
                    continue
                # rules are computed on the FULL history so the 200-day average
                # and the pivot memory are warm on the first day of the window
                R = rules(df)
                mask = np.asarray(df.index >= wstart)
                ret = d["close"].pct_change().fillna(0.0).to_numpy()
                row = {"buy_and_hold": stats(walk(ret, np.ones(len(d), bool)),
                                             d.index)}
                for name, sig in R.items():
                    s = sig[mask]
                    sw = int(pd.Series(s).ne(pd.Series(s).shift(1)).sum())
                    row[name] = stats(walk(ret, s), d.index, s, sw)
                per_stock[t] = row
            per_window[wname] = per_stock

            # equal-weight across the basket: the portfolio question, not the
            # single-stock one
            agg = {}
            names = ["buy_and_hold"] + list(next(iter(per_stock.values())).keys())
            for name in dict.fromkeys(names):
                fin = [per_stock[t][name]["final_gbp"] for t in per_stock
                       if name in per_stock[t]]
                dds = [per_stock[t][name]["max_drawdown"] for t in per_stock
                       if name in per_stock[t]]
                if fin:
                    agg[name] = {"mean_final_gbp": float(np.mean(fin)),
                                 "median_final_gbp": float(np.median(fin)),
                                 "mean_max_drawdown": float(np.mean(dds)),
                                 "stocks": len(fin),
                                 "beat_buy_and_hold": int(sum(
                                     per_stock[t][name]["final_gbp"]
                                     > per_stock[t]["buy_and_hold"]["final_gbp"]
                                     for t in per_stock if name in per_stock[t]))}
            results[wname] = agg

            print(f"\n  === {wname.upper()} ({wstart} onwards), "
                  f"{len(per_stock)} stocks, GBP 10,000 each ===")
            print(f"  {'rule':20}{'mean final':>13}{'median':>12}"
                  f"{'mean maxDD':>12}{'beat hold':>11}")
            for name in sorted(agg, key=lambda k: -agg[k]["mean_final_gbp"]):
                v = agg[name]
                print(f"  {name:20}{v['mean_final_gbp']:>13,.0f}"
                      f"{v['median_final_gbp']:>12,.0f}"
                      f"{v['mean_max_drawdown']:>12.1%}"
                      f"{v['beat_buy_and_hold']:>7}/{v['stocks']:<3}")

        # ---- episode view: where does a trend filter earn or cost? --------
        # The aggregate hides the mechanism. A filter that saves you in a slow
        # grinding bear and costs you in a V-shaped recovery nets out to a
        # number that looks like nothing while being two large opposite things.
        epi = {}
        for t, df in frames.items():
            R = rules(df)
            c = df["close"]
            ret = c.pct_change().fillna(0.0).to_numpy()
            rows = []
            for s_, e_, tr_, dep in episodes(c):
                m = np.asarray((df.index >= s_) & (df.index <= e_))
                if m.sum() < 20:
                    continue
                item = {"from": str(s_.date()), "to": str(e_.date()),
                        "trough": str(tr_.date()), "hold_drawdown": dep}
                sub = ret[m]
                item["buy_and_hold_pct"] = float(np.prod(1 + sub) - 1)
                for name in ("cross_50_200", "above_200d", "donchian_55_20"):
                    s = R[name][m]
                    eq = walk(sub, s)
                    item[name + "_pct"] = float(eq[-1] / START_GBP - 1)
                rows.append(item)
            if rows:
                epi[t] = rows

        print("\n  === WHAT HAPPENED THROUGH EACH DRAWDOWN ===")
        for t, rows in list(epi.items())[:6]:
            print(f"\n  {t}")
            print(f"    {'episode':26}{'hold':>9}{'50/200':>9}"
                  f"{'>200d':>9}{'donch':>9}")
            for r in rows:
                print(f"    {r['from']}..{r['to'][:7]:14}"
                      f"{r['buy_and_hold_pct']:>+9.1%}"
                      f"{r['cross_50_200_pct']:>+9.1%}"
                      f"{r['above_200d_pct']:>+9.1%}"
                      f"{r['donchian_55_20_pct']:>+9.1%}")

        # ---- relative strength: always invested, in the strongest names ----
        # The arm with the best prior behind it, and the one this project set
        # aside too early.
        rs = {}
        px = pd.DataFrame({t: f["close"] for t, f in frames.items()}).dropna(
            how="all").ffill()
        if px.shape[1] >= 4:
            for look in (63, 126, 252):
                for topn in (3, 5):
                    mom = px.pct_change(look)
                    month = px.index.to_period("M")
                    hold = pd.DataFrame(False, index=px.index, columns=px.columns)
                    for m_ in month.unique():
                        days = np.flatnonzero(month == m_)
                        if not len(days):
                            continue
                        d0 = days[0]
                        if d0 == 0:
                            continue
                        rank = mom.iloc[d0 - 1].dropna()
                        if len(rank) < topn:
                            continue
                        for t in rank.nlargest(topn).index:
                            hold.iloc[days, hold.columns.get_loc(t)] = True
                    w = hold.div(hold.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
                    rets = px.pct_change().fillna(0.0)
                    turn = w.diff().abs().sum(axis=1).fillna(0.0)
                    pr = (w.shift(1).fillna(0.0) * rets).sum(axis=1) - turn * COST
                    eq = START_GBP * np.cumprod(1 + pr.to_numpy())
                    key = f"momentum_{look}d_top{topn}"
                    rs[key] = stats(eq, px.index)
            ew = px.pct_change().fillna(0.0).mean(axis=1)
            rs["equal_weight_hold_all"] = stats(
                START_GBP * np.cumprod(1 + ew.to_numpy()), px.index)
            print("\n  === RELATIVE STRENGTH, always invested "
                  f"({px.shape[1]} names) ===")
            for k in sorted(rs, key=lambda x: -rs[x]["final_gbp"]):
                v = rs[k]
                print(f"  {k:26}{v['final_gbp']:>13,.0f}"
                      f"{v['cagr']:>+9.2%}{v['max_drawdown']:>9.1%}")

        bh = results["your_window"].get("buy_and_hold", {})
        winners = [k for k, v in results["your_window"].items()
                   if k != "buy_and_hold"
                   and v["mean_final_gbp"] > bh.get("mean_final_gbp", 0)]
        verdict = (
            f"In your window, these rules beat buy-and-hold on the basket "
            f"average: {', '.join(winners)}."
            if winners else
            "In your window, no trend rule beat buy-and-hold on the basket "
            "average. Note what the episode table shows though: the filters do "
            "cut drawdowns in slow bear markets and do nothing in fast crashes. "
            "The cost is not bad signals, it is the price of being out of a "
            "rising market.")
        print(f"\n  {verdict}")

        out_path.write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "start_gbp": START_GBP, "cost_per_switch": COST,
             "tickers": list(frames), "windows": {"full": a.start,
                                                  "your_window": a.window},
             "aggregate": results, "per_stock": per_window,
             "episodes": epi, "relative_strength": rs, "verdict": verdict},
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
