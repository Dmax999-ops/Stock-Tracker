#!/usr/bin/env python3
"""
Out-of-sample test: does the results-week reaction predict the next three months?

THE HYPOTHESIS, FIXED BEFORE THIS RAN
-------------------------------------
On the fifteen holdings, ranking each stock's results-week move against *its own*
history gave +6.8% over 12 weeks with t = 3.3. That version was chosen after seeing
the data, so it proves nothing. This script is its honest test: same rule, ~600
stocks we do not own, none of which were looked at when the rule was written.

    Signal    within each stock, rank the results-week abnormal return against
              that stock's own previous announcements (expanding window only --
              never the full sample). Top third = BUY, bottom third = SELL.
    Entry     the weekly close AFTER the announcement week. No acting on the
              news at a price printed before the news.
    Horizon   12 weeks.
    Benchmark the same-week average of every other stock in the universe. Not a
              long-run average -- that is the mistake that made CAPITULATION look
              like a stock-picking signal when it was really a market-timing one.

PASS MARK (fixed now, before any result is seen)
    1. BUY minus SELL > 0 with t >= 2.5, where the t-statistic is computed across
       CALENDAR WEEKS, not across events. Events in the same week share a market,
       so treating them as independent inflates significance.
    2. BUY events beat their peers at least 55% of the time.
    3. The sign holds in BOTH halves of the sample.
All three, or the signal does not go into the daily messages.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

H = 12            # weeks held
MIN_HISTORY = 8   # a stock needs 8 prior announcements before it can be ranked
MIN_T = 2.5
MIN_HIT = 0.55


def weekly(px: pd.DataFrame) -> pd.DataFrame:
    """Daily panel -> Friday-stamped weekly closes."""
    px = px.copy()
    px["date"] = pd.to_datetime(px["date"])
    w = (px.set_index("date").groupby("ticker")["close"]
           .resample("W-FRI").last().dropna().reset_index())
    return w


def build(px_w: pd.DataFrame, ann: pd.DataFrame) -> pd.DataFrame:
    px_w = px_w.sort_values(["ticker", "date"])
    px_w["ret"] = px_w.groupby("ticker")["close"].pct_change()
    # same-week universe average, computed across every stock trading that week
    px_w["mkt"] = px_w.groupby("date")["ret"].transform("mean")
    px_w["abn"] = px_w["ret"] - px_w["mkt"]

    idx = {t: g.reset_index(drop=True) for t, g in px_w.groupby("ticker")}
    rows = []
    for t, g in ann.groupby("ticker"):
        if t not in idx:
            continue
        p = idx[t]
        dates = p["date"].values
        for d in pd.to_datetime(g["date"]).sort_values():
            k = int(np.searchsorted(dates, np.datetime64(d)))   # announcement week
            if k < 1 or k + 1 + H >= len(p):
                continue
            ear = p["abn"].iloc[k]
            if not np.isfinite(ear):
                continue
            entry, exit_ = k + 1, k + 1 + H          # buy the week AFTER the news
            fwd = p["close"].iloc[exit_] / p["close"].iloc[entry] - 1
            bench = p["mkt"].iloc[entry + 1:exit_ + 1].add(1).prod() - 1
            rows.append({"ticker": t, "week": p["date"].iloc[k],
                         "ear": float(ear), "drift": float(fwd - bench)})
    return pd.DataFrame(rows).sort_values(["ticker", "week"])


def rank_expanding(e: pd.DataFrame) -> pd.DataFrame:
    """
    Each announcement is ranked against that stock's EARLIER announcements only.
    Using the stock's whole history would mean knowing, in 2004, how big its 2019
    reactions were.
    """
    out = []
    for t, g in e.groupby("ticker"):
        g = g.sort_values("week").reset_index(drop=True)
        pct = [np.nan] * len(g)
        for i in range(MIN_HISTORY, len(g)):
            past = g["ear"].iloc[:i]
            pct[i] = float((past < g["ear"].iloc[i]).mean())
        g["pct"] = pct
        out.append(g)
    e = pd.concat(out, ignore_index=True).dropna(subset=["pct"])
    e["bucket"] = np.where(e.pct >= 2 / 3, "BUY",
                  np.where(e.pct <= 1 / 3, "SELL", "MID"))
    return e


MIN_PER_BUCKET = 3        # a week only counts if it holds a real group on each side
MIN_WEEKS = 20            # below this the t-statistic is not worth quoting


def weekly_spread(e: pd.DataFrame) -> pd.Series:
    """
    Mean BUY drift minus mean SELL drift, one observation per calendar week.
    Weeks are the unit because stocks reporting in the same week share a market;
    counting each event separately would treat one market move as many.
    """
    g = e.groupby(["week", "bucket"])["drift"].agg(["mean", "size"]).unstack()
    ok = ((g[("size", "BUY")] >= MIN_PER_BUCKET)
          & (g[("size", "SELL")] >= MIN_PER_BUCKET))
    return (g[("mean", "BUY")] - g[("mean", "SELL")])[ok].dropna()


def report(e: pd.DataFrame, label: str) -> dict:
    sp = weekly_spread(e)
    t, p = stats.ttest_1samp(sp, 0.0) if len(sp) > 2 else (np.nan, np.nan)
    buy = e[e.bucket == "BUY"].drift
    hit = float((buy > 0).mean()) if len(buy) else np.nan
    r = {"label": label, "events": int(len(e)), "weeks": int(len(sp)),
         "buy_minus_sell": float(sp.mean()), "t": float(t), "p": float(p),
         "buy_hit_rate": hit,
         "buy_mean": float(buy.mean()) if len(buy) else np.nan,
         "sell_mean": float(e[e.bucket == "SELL"].drift.mean()),
         "mid_mean": float(e[e.bucket == "MID"].drift.mean())}
    print(f"\n=== {label}")
    print(f"  events {r['events']:,}  calendar weeks {r['weeks']:,}")
    print(f"  BUY {r['buy_mean']:+.2%}   MID {r['mid_mean']:+.2%}   "
          f"SELL {r['sell_mean']:+.2%}")
    print(f"  BUY-SELL {r['buy_minus_sell']:+.2%}   t={r['t']:.2f}   "
          f"hit {r['buy_hit_rate']:.1%}")
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--dates", default="data/earnings_dates.csv")
    ap.add_argument("--out", default="data/ear_evidence.json")
    a = ap.parse_args()

    px = pd.read_parquet(a.prices)
    ann = pd.read_csv(a.dates)
    print(f"prices: {px.ticker.nunique()} tickers   "
          f"announcements: {len(ann):,} across {ann.ticker.nunique()} tickers")

    e = rank_expanding(build(weekly(px), ann))
    if e.empty:
        print("no usable events")
        return 1

    full = report(e, "FULL SAMPLE")
    mid = e.week.quantile(0.5)
    h1 = report(e[e.week <= mid], f"first half (to {pd.Timestamp(mid).date()})")
    h2 = report(e[e.week > mid], "second half")

    if full["weeks"] < MIN_WEEKS:
        print(f"\n  Only {full['weeks']} usable weeks (need {MIN_WEEKS}). "
              f"INCONCLUSIVE — not enough breadth to judge.")
        passed = False
    else:
        passed = (full["t"] >= MIN_T and full["buy_hit_rate"] >= MIN_HIT
                  and h1["buy_minus_sell"] > 0 and h2["buy_minus_sell"] > 0)
    print(f"\n  t >= {MIN_T}: {full['t'] >= MIN_T}")
    print(f"  hit >= {MIN_HIT:.0%}: {full['buy_hit_rate'] >= MIN_HIT}")
    print(f"  both halves positive: {h1['buy_minus_sell'] > 0 and h2['buy_minus_sell'] > 0}")
    print(f"\n  VERDICT: {'PASS — eligible for daily messages' if passed else 'FAIL — stays out'}")

    Path(a.out).write_text(json.dumps(
        {"generated": pd.Timestamp.now("UTC").isoformat(), "horizon_weeks": H,
         "pass_mark": {"min_t": MIN_T, "min_hit": MIN_HIT,
                       "both_halves_positive": True},
         "full": full, "first_half": h1, "second_half": h2,
         "passed": bool(passed)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
