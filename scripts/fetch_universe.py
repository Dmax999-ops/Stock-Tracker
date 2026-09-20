#!/usr/bin/env python3
"""
Fetch the training universe — survivorship-aware.

WHY THIS FILE IS SHAPED LIKE THIS
---------------------------------
Pulling today's index members and backtesting them is the most common way to
produce a beautiful, worthless result: you have deleted every company that failed.
Measured on this universe, the gap is not marginal — 504 current members against
1,128 that were ever in the index. **55% of the real universe was missing.**

So this script reads HISTORICAL membership and fetches the union: every ticker that
was ever in the index, including the ones that went to zero.

THE TICKER-REUSE TRAP
---------------------
Exchanges recycle symbols. 'AL' was Alcan until 2007; today it is Air Lease.
Fetching 'AL' now returns Air Lease's history, which then gets silently attributed
to a company that no longer exists. That is worse than missing data — it is wrong
data wearing the right label.

Defence: for every ticker we record the window during which it was actually in the
index, and we require the fetched history to OVERLAP that window. A ticker whose
data begins after it left the index is a different company and is dropped.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import yaml


# ---------------------------------------------------------------------------
# Constituent resolution
# ---------------------------------------------------------------------------

def load_historical(url: str) -> tuple[list[str], dict[str, tuple[str, str]]]:
    """
    Parse a `date,tickers` membership file into the union plus, for each ticker,
    the first and last date it appears in the index.
    """
    h = pd.read_csv(url)
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

    windows = {t: (first[t].strftime("%Y-%m-%d"), last[t].strftime("%Y-%m-%d"))
               for t in first}
    return sorted(first), windows


def load_simple(url: str, column: str = "Symbol") -> list[str]:
    df = pd.read_csv(url)
    return sorted({str(t).strip().upper() for t in df[column].dropna()})


def resolve(cfg: dict) -> tuple[list[str], dict, dict]:
    tickers: set[str] = set()
    windows: dict[str, tuple[str, str]] = {}
    sources: dict[str, int] = {}

    for src in cfg.get("constituent_sources", []):
        name = src["name"]
        try:
            if src.get("format") == "historical_union":
                got, win = load_historical(src["url"])
                windows.update(win)
            else:
                got = load_simple(src["url"], src.get("column", "Symbol"))
            tickers.update(got)
            sources[name] = len(got)
            print(f"  {name}: {len(got)} tickers")
        except Exception as e:                                   # noqa: BLE001
            print(f"  {name}: FAILED ({e})", file=sys.stderr)
            sources[name] = 0

    tickers.update(t.upper() for t in cfg.get("extra_tickers", []))
    return sorted(tickers), windows, sources


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def to_yahoo(t: str) -> str:
    """Class shares use a dash on Yahoo (BRK.B -> BRK-B)."""
    return t.replace(".", "-")


def fetch(tickers: list[str], start: str, batch: int = 100) -> tuple[pd.DataFrame, list[str]]:
    import yfinance as yf

    frames: list[pd.DataFrame] = []
    failed: list[str] = []

    for i in range(0, len(tickers), batch):
        chunk = tickers[i:i + batch]
        print(f"  batch {i // batch + 1}/{-(-len(tickers) // batch)}: "
              f"{len(chunk)} tickers", flush=True)
        try:
            raw = yf.download([to_yahoo(t) for t in chunk], start=start,
                              auto_adjust=True, progress=False,
                              group_by="ticker", threads=True)
        except Exception as e:                                   # noqa: BLE001
            print(f"    batch failed: {e}", file=sys.stderr)
            failed.extend(chunk)
            continue

        for t in chunk:
            y = to_yahoo(t)
            try:
                d = raw[y] if len(chunk) > 1 else raw
                d = d.dropna(subset=["Close"])
                if len(d) < 250:
                    failed.append(t)
                    continue
                d = d.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
                d = d.reset_index().rename(columns={"Date": "date", "index": "date"})
                d["ticker"] = t
                frames.append(d)
            except Exception:                                    # noqa: BLE001, PERF203
                failed.append(t)
        time.sleep(1)

    px = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return px, failed


# ---------------------------------------------------------------------------
# Ticker-reuse defence
# ---------------------------------------------------------------------------

def drop_reused_symbols(px: pd.DataFrame, windows: dict[str, tuple[str, str]],
                        min_overlap_days: int = 180) -> tuple[pd.DataFrame, list[dict]]:
    """
    Drop tickers whose fetched price history does not overlap the period they were
    actually in the index — those are recycled symbols belonging to a different company.
    """
    if not windows:
        return px, []

    span = px.groupby("ticker")["date"].agg(["min", "max"])
    suspect = []
    for t, (w_start, w_end) in windows.items():
        if t not in span.index:
            continue
        ws, we = pd.Timestamp(w_start), pd.Timestamp(w_end)
        ds, de = span.loc[t, "min"], span.loc[t, "max"]
        overlap = (min(we, de) - max(ws, ds)).days
        if overlap < min_overlap_days:
            suspect.append({"ticker": t,
                            "index_window": f"{w_start}..{w_end}",
                            "data_window": f"{ds.date()}..{de.date()}",
                            "overlap_days": int(overlap)})
    if suspect:
        bad = {s["ticker"] for s in suspect}
        px = px[~px.ticker.isin(bad)]
    return px, suspect


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cfg = yaml.safe_load(Path(a.config).read_text())
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    print("Resolving constituents...")
    tickers, windows, sources = resolve(cfg)
    print(f"Universe: {len(tickers)} unique tickers "
          f"({len(windows)} with membership windows)\n")

    print("Fetching price history...")
    px, failed = fetch(tickers, cfg.get("start", "2000-01-01"))
    if px.empty:
        print("No data fetched.", file=sys.stderr)
        return 1

    fetched_before = px.ticker.nunique()
    px, reused = drop_reused_symbols(px, windows)
    print(f"\nDropped {fetched_before - px.ticker.nunique()} recycled symbols")
    for s in reused[:10]:
        print(f"    {s['ticker']:6} in index {s['index_window']} but data "
              f"{s['data_window']} (overlap {s['overlap_days']}d)")

    px.to_parquet(out / "prices.parquet", index=False)

    # How much of the vanished universe did we actually recover?
    got = set(px.ticker)
    ever = set(windows) if windows else got
    last_snapshot = {t for t, (s, e) in windows.items()
                     if e == max(e for _, e in windows.values())} if windows else set()
    delisted_wanted = ever - last_snapshot
    delisted_got = delisted_wanted & got

    manifest = {
        "generated": pd.Timestamp.utcnow().isoformat(),
        "tickers_requested": len(tickers),
        "tickers_with_data": int(px.ticker.nunique()),
        "tickers_failed": len(failed),
        "recycled_symbols_dropped": len(reused),
        "rows": int(len(px)),
        "date_min": str(px.date.min().date()),
        "date_max": str(px.date.max().date()),
        "constituent_sources": sources,
        "universe_ever": len(ever),
        "delisted_sought": len(delisted_wanted),
        "delisted_recovered": len(delisted_got),
        "delisted_recovery_rate": round(len(delisted_got) / max(len(delisted_wanted), 1), 3),
        "SURVIVORSHIP": (
            f"Recovered {len(delisted_got)} of {len(delisted_wanted)} tickers that "
            f"left the index. Anything below ~0.7 still flatters dip-buying results, "
            f"because the companies that fell and never recovered are the ones Yahoo "
            f"is least likely to serve."
        ),
        "recycled_examples": reused[:25],
        "failed_examples": failed[:40],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("\n" + json.dumps({k: v for k, v in manifest.items()
                             if k not in ("recycled_examples", "failed_examples")},
                            indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
