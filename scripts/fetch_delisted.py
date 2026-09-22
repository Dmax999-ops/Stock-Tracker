#!/usr/bin/env python3
"""
Incremental delisted-ticker archiver.

THE PROBLEM THIS SOLVES
-----------------------
Yahoo served only 18.4% of the 625 tickers that left the S&P 500 since 1996.
The other 510 are the companies that failed — exactly the ones whose absence
makes "buy the dip" look profitable. Alpha Vantage *does* serve them: AMR Corp
(AAMRQ) returns complete weekly history from January 2001 to its delisting on
2013-12-17, including the fall from $40.66 to $0.20 and the Chapter 11 recovery
to $11.39 in the US Airways merger.

THE CONSTRAINT
--------------
Alpha Vantage free tier: 25 calls/day, 1 request/second. 500+ tickers cannot be
fetched in one run. So this script does ~20 per run and remembers where it got
to. Run daily and the archive completes itself in about three weeks with no
intervention.

WHY NOT JUST ASSUME THEY WENT TO ZERO
-------------------------------------
Because most of them did not. Of tickers that leave an index, the majority leave
by acquisition — at a premium — not by liquidation. Assuming zero would bias the
data as hard in the pessimistic direction as omitting them biases it in the
optimistic one. So we record the real prices, and record the delisting date
alongside, which is what lets a takeout be told apart from a wipeout.

STATE
-----
    data/delisted/_worklist.json     what has been tried, what succeeded, fate
    data/delisted/_listing_status.csv  cached Alpha Vantage delisting dates
    data/delisted/<TICKER>.csv       weekly adjusted OHLCV
    data/delisted/delisted_weekly.parquet  everything, concatenated

The worklist is committed to git, so a run never repeats work another run did.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
import yaml

AV = "https://www.alphavantage.co/query"

# Free tier: 25 calls/day, 1 request/second burst ceiling. 1.5s is the margin
# that stopped the parallel-call failures earlier in this project.
SLEEP = 1.5
MAX_ATTEMPTS = 3          # after three empty/error results, stop retrying a ticker
REUSE_GAP_DAYS = 1095     # history starting >3y after the index exit = a new company
LISTING_MAX_AGE_DAYS = 30  # refresh the delisting-date index monthly (1 call)


# ---------------------------------------------------------------------------
# Who are we still missing?
# ---------------------------------------------------------------------------

def index_leavers(cfg: dict) -> tuple[list[str], dict[str, tuple[str, str]]]:
    """
    Every ticker that was in the S&P 500 at some point since `start` but is not
    in the most recent snapshot — i.e. the ones that left. Returns them sorted,
    plus each ticker's membership window.
    """
    src = next(s for s in cfg["constituent_sources"]
               if s.get("format") == "historical_union")
    h = pd.read_csv(src["url"])
    h["date"] = pd.to_datetime(h["date"])
    h = h.sort_values("date")

    first: dict[str, pd.Timestamp] = {}
    last: dict[str, pd.Timestamp] = {}
    for d, row in zip(h["date"], h["tickers"]):
        for t in str(row).split(","):
            t = t.strip().upper()
            if not t:
                continue
            first.setdefault(t, d)
            last[t] = d

    latest = h["date"].max()
    leavers = sorted(t for t in first if last[t] < latest)
    windows = {t: (first[t].strftime("%Y-%m-%d"), last[t].strftime("%Y-%m-%d"))
               for t in first}
    return leavers, windows


# ---------------------------------------------------------------------------
# Alpha Vantage
# ---------------------------------------------------------------------------

class RateLimited(Exception):
    """Daily quota exhausted. Stop cleanly and keep what we have."""


def _get(params: dict, key: str) -> requests.Response:
    params = dict(params, apikey=key)
    r = requests.get(AV, params=params, timeout=60)
    r.raise_for_status()
    head = r.text[:400]
    # Alpha Vantage signals quota exhaustion with HTTP 200 and a JSON note.
    if '"Note"' in head or ('"Information"' in head
                            and "rate limit" in head.lower()):
        raise RateLimited(head.strip())
    return r


def refresh_listing_status(out: Path, key: str) -> pd.DataFrame:
    """
    Cache the delisted-symbol index. One API call, refreshed monthly.
    Earliest delisting date on record is 2008-11-21 — the Enron/WorldCom era
    predates this feed, so those tickers will simply come back empty.
    """
    cache = out / "_listing_status.csv"
    if cache.exists():
        age = date.today() - date.fromtimestamp(cache.stat().st_mtime)
        if age < timedelta(days=LISTING_MAX_AGE_DAYS):
            return pd.read_csv(cache)

    print("  refreshing delisting-date index (1 call)...", flush=True)
    r = _get({"function": "LISTING_STATUS", "state": "delisted"}, key)
    df = pd.read_csv(io.StringIO(r.text))
    df.to_csv(cache, index=False)
    time.sleep(SLEEP)
    return df


def candidates(t: str) -> list[str]:
    """
    Symbol spellings to try. Bankrupt names often carry a 'Q' suffix in the
    membership file (ENRNQ, AAMRQ) but not always in the price feed; class
    shares use a dash on some feeds and a dot on others.
    """
    out = [t]
    if t.endswith("Q") and len(t) > 3:
        out.append(t[:-1])
    if "." in t:
        out.append(t.replace(".", "-"))
    if "-" in t:
        out.append(t.replace("-", "."))
    seen, uniq = set(), []
    for c in out:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def fetch_weekly(symbol: str, key: str) -> pd.DataFrame | None:
    """
    TIME_SERIES_WEEKLY_ADJUSTED — free, full history, dividend-adjusted.
    (DAILY_ADJUSTED and outputsize=full on daily are premium-only.)
    """
    r = _get({"function": "TIME_SERIES_WEEKLY_ADJUSTED",
              "symbol": symbol, "datatype": "csv"}, key)
    txt = r.text.strip()
    if not txt or txt.lstrip().startswith("{"):
        return None
    df = pd.read_csv(io.StringIO(txt))
    if "timestamp" not in df.columns or df.empty:
        return None
    df = df.rename(columns={"timestamp": "date",
                            "adjusted close": "adj_close"})
    keep = [c for c in ["date", "open", "high", "low", "close",
                        "adj_close", "volume", "dividend amount"]
            if c in df.columns]
    df = df[keep].rename(columns={"dividend amount": "dividend"})
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Fate classification — acquisition or wipeout?
# ---------------------------------------------------------------------------

def classify_fate(df: pd.DataFrame) -> tuple[str, float]:
    """
    Heuristic, and labelled as one. A company taken out at a premium and a
    company liquidated both stop having prices; the difference is the shape of
    the last year.

        final price under $1, or down >80% from its two-year high  -> wipeout
        otherwise                                                  -> takeout

    Returns (fate, final_drawdown). Nothing downstream should treat this as
    fact — it is a label for slicing, and the delisting date plus the price
    series are the actual evidence.
    """
    if df.empty:
        return "unknown", float("nan")
    tail = df.tail(104)
    last = float(tail["adj_close"].iloc[-1])
    peak = float(tail["adj_close"].max())
    dd = (last / peak - 1.0) if peak > 0 else float("nan")
    if last < 1.0 or (pd.notna(dd) and dd < -0.80):
        return "wipeout", dd
    return "takeout", dd


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/universe.yml")
    ap.add_argument("--out", default="data/delisted")
    ap.add_argument("--limit", type=int, default=20,
                    help="tickers to fetch this run (free tier allows ~24)")
    a = ap.parse_args()

    key = os.environ.get("ALPHAVANTAGE_API_KEY", "").strip()
    if not key:
        print("ALPHAVANTAGE_API_KEY not set — skipping delisted fetch.")
        return 0

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load(Path(a.config).read_text())

    wl_path = out / "_worklist.json"
    wl = json.loads(wl_path.read_text()) if wl_path.exists() else {}

    # The first release rejected on overlap and wrongly discarded real companies
    # whose history begins after their index exit. Re-queue anything the old rule
    # threw out so the new gap test gets a look at it.
    stale = [t for t, v in wl.items()
             if v.get("status") == "recycled" and "gap_days" not in v]
    for t in stale:
        wl[t] = {"attempts": 0, "status": "requeued_after_rule_change"}
    if stale:
        print(f"re-queued {len(stale)} tickers rejected by the old overlap rule: "
              f"{', '.join(stale[:8])}{'...' if len(stale) > 8 else ''}")

    print("Resolving index leavers...")
    leavers, windows = index_leavers(cfg)
    print(f"  {len(leavers)} tickers have left the index since "
          f"{cfg.get('start', '?')}")

    try:
        listing = refresh_listing_status(out, key)
    except RateLimited as e:
        print(f"Rate limited before starting: {e}")
        return 0
    dl_dates = dict(zip(listing["symbol"].astype(str).str.upper(),
                        listing["delistingDate"].astype(str)))

    # Deterministic order, so progress is predictable and resumable.
    todo = [t for t in leavers
            if wl.get(t, {}).get("status") != "done"
            and wl.get(t, {}).get("attempts", 0) < MAX_ATTEMPTS]
    batch = todo[:a.limit]

    done = sum(1 for v in wl.values() if v.get("status") == "done")
    print(f"  {done} archived, {len(todo)} remaining, "
          f"fetching {len(batch)} this run\n")

    if not batch:
        print("Archive complete — nothing left to fetch.")

    fetched = 0
    for t in batch:
        rec = wl.setdefault(t, {})
        rec["attempts"] = rec.get("attempts", 0) + 1
        rec["last_try"] = date.today().isoformat()
        rec["index_window"] = "..".join(windows.get(t, ("", "")))

        df = None
        used = None
        try:
            for sym in candidates(t):
                df = fetch_weekly(sym, key)
                time.sleep(SLEEP)
                if df is not None and len(df) > 20:
                    used = sym
                    break
                df = None
        except RateLimited as e:
            print(f"  {t:8} quota exhausted — stopping cleanly")
            rec["attempts"] -= 1          # don't burn an attempt on our own limit
            rec["status"] = rec.get("status", "pending")
            break
        except Exception as e:                                   # noqa: BLE001
            rec["status"] = "error"
            rec["error"] = str(e)[:200]
            print(f"  {t:8} error: {str(e)[:80]}")
            continue

        if df is None:
            rec["status"] = "empty"
            print(f"  {t:8} no data (predates the feed, or symbol not served)")
            continue

        # Ticker-reuse defence, same test as fetch_universe.py: the price
        # history must overlap the period the ticker was actually in the index.
        # Ticker-reuse defence. The first version of this rejected anything whose
        # price history did not overlap the index window by 180 days, and it threw
        # away the very companies we are hunting: Ambac really is ABKFQ, but Alpha
        # Vantage's history for it starts in 2010, two years AFTER it crashed out
        # of the index in 2008. A gap is normal for a company that kept trading as
        # a penny stock; a gap of many years means a different company got the
        # symbol. So the test is the size of the gap, not the size of the overlap.
        ws, we = windows.get(t, (None, None))
        if ws:
            ds, de = df["date"].min(), df["date"].max()
            gap = (ds - pd.Timestamp(we)).days        # data starts after index exit
            rec["data_window"] = f"{ds.date()}..{de.date()}"
            if de < pd.Timestamp(ws):
                rec["status"] = "recycled"
                rec["reason"] = "history ends before the ticker entered the index"
                print(f"  {t:8} RECYCLED — data {rec['data_window']} ends before "
                      f"index {rec['index_window']}")
                continue
            if gap > REUSE_GAP_DAYS:
                rec["status"] = "recycled"
                rec["gap_days"] = int(gap)
                print(f"  {t:8} RECYCLED — data starts {gap} days after it left "
                      f"the index ({rec['data_window']} vs {rec['index_window']})")
                continue
            rec["post_exit_only"] = bool(gap > 0)

        fate, dd = classify_fate(df)
        df.insert(1, "ticker", t)
        df.to_csv(out / f"{t}.csv", index=False)

        rec.update(status="done",
                   symbol_used=used,
                   rows=int(len(df)),
                   first=str(df["date"].min().date()),
                   last=str(df["date"].max().date()),
                   delisting_date=dl_dates.get(t) or dl_dates.get(used) or None,
                   fate_heuristic=fate,
                   final_drawdown=None if pd.isna(dd) else round(float(dd), 4))
        fetched += 1
        print(f"  {t:8} {len(df):>4} bars  {rec['first']}..{rec['last']}  "
              f"delisted {rec['delisting_date'] or '?'}  {fate}")

    wl_path.write_text(json.dumps(wl, indent=2, sort_keys=True))

    # Rebuild the combined panel from everything archived so far, so downstream
    # scripts have one file to read regardless of how far through we are.
    csvs = sorted(p for p in out.glob("*.csv") if not p.name.startswith("_"))
    if csvs:
        panel = pd.concat([pd.read_csv(p, parse_dates=["date"]) for p in csvs],
                          ignore_index=True)
        panel.to_parquet(out / "delisted_weekly.parquet", index=False)
    else:
        panel = pd.DataFrame()

    ok = [v for v in wl.values() if v.get("status") == "done"]
    manifest = {
        "generated": datetime.utcnow().isoformat(),
        "leavers_total": len(leavers),
        "archived": len(ok),
        "empty": sum(1 for v in wl.values() if v.get("status") == "empty"),
        "recycled": sum(1 for v in wl.values() if v.get("status") == "recycled"),
        "errors": sum(1 for v in wl.values() if v.get("status") == "error"),
        "remaining": max(len(leavers) - len(wl), 0) + sum(
            1 for v in wl.values()
            if v.get("status") not in ("done", "empty", "recycled")
            and v.get("attempts", 0) < MAX_ATTEMPTS),
        "fetched_this_run": fetched,
        "rows": int(len(panel)),
        "fate_wipeout": sum(1 for v in ok if v.get("fate_heuristic") == "wipeout"),
        "fate_takeout": sum(1 for v in ok if v.get("fate_heuristic") == "takeout"),
        "coverage": round(len(ok) / max(len(leavers), 1), 3),
        "NOTE": ("Weekly bars, not daily — Alpha Vantage's free daily endpoint is "
                 "truncated. Compare against a weekly resample of the survivor "
                 "universe, never against daily results."),
    }
    (out / "_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("\n" + json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
