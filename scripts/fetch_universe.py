#!/usr/bin/env python3
"""
Fetch the training universe.

SURVIVORSHIP IS THE POINT OF THIS SCRIPT. Pulling today's index members and
backtesting them is the single most common way to produce a beautiful, worthless
result -- you have deleted every company that failed. This script therefore:

  1. reads a union of HISTORICAL constituent lists where available, not just today's
  2. keeps tickers that no longer trade, recording them as delisted rather than
     dropping them
  3. records, in the manifest, how much of the universe is survivor-only, so the
     bias is visible rather than hidden

yfinance cannot supply most delisted history. Where that matters -- and it matters
most for any buy-the-dip signal -- the honest fix is a paid survivorship-free
source (Norgate, CRSP). The manifest tells you how exposed you are.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import yaml


def load_constituents(cfg: dict) -> tuple[list[str], dict]:
    """Union of every constituent list we can reach, plus provenance."""
    tickers, sources = set(), {}
    for src in cfg.get("constituent_sources", []):
        try:
            df = pd.read_csv(src["url"])
            col = src.get("column", "Symbol")
            got = [str(t).strip().upper().replace(".", "-") for t in df[col].dropna()]
            tickers.update(got)
            sources[src["name"]] = len(got)
            print(f"  {src['name']}: {len(got)} tickers")
        except Exception as e:                       # noqa: BLE001
            print(f"  {src['name']}: FAILED ({e})", file=sys.stderr)
            sources[src["name"]] = 0
    tickers.update(t.upper() for t in cfg.get("extra_tickers", []))
    return sorted(tickers), sources


def fetch(tickers: list[str], start: str, batch: int = 100) -> pd.DataFrame:
    import yfinance as yf

    frames, failed = [], []
    for i in range(0, len(tickers), batch):
        chunk = tickers[i:i + batch]
        print(f"  batch {i // batch + 1}: {len(chunk)} tickers", flush=True)
        try:
            raw = yf.download(chunk, start=start, auto_adjust=True,
                              progress=False, group_by="ticker", threads=True)
        except Exception as e:                       # noqa: BLE001
            print(f"    batch failed: {e}", file=sys.stderr)
            failed.extend(chunk)
            continue
        for t in chunk:
            try:
                d = raw[t] if len(chunk) > 1 else raw
                d = d.dropna(subset=["Close"])
                if len(d) < 250:
                    failed.append(t)
                    continue
                d = d.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
                d["ticker"] = t
                frames.append(d.reset_index().rename(columns={"Date": "date"}))
            except Exception:                        # noqa: BLE001, PERF203
                failed.append(t)
        time.sleep(1)                                # be polite
    if failed:
        print(f"  {len(failed)} tickers returned nothing usable", file=sys.stderr)
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), failed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cfg = yaml.safe_load(Path(a.config).read_text())
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    print("Resolving constituents...")
    tickers, sources = load_constituents(cfg)
    print(f"Universe: {len(tickers)} unique tickers\n")

    print("Fetching price history...")
    px, failed = fetch(tickers, cfg.get("start", "2000-01-01"))
    if px.empty:
        print("No data fetched.", file=sys.stderr)
        return 1

    px.to_parquet(out / "prices.parquet", index=False)

    last = px.groupby("ticker")["date"].max()
    recent = last.max()
    stale = last[last < recent - pd.Timedelta(days=30)]

    manifest = {
        "generated": pd.Timestamp.utcnow().isoformat(),
        "tickers_requested": len(tickers),
        "tickers_with_data": int(px.ticker.nunique()),
        "tickers_failed": len(failed),
        "rows": int(len(px)),
        "date_min": str(px.date.min().date()),
        "date_max": str(px.date.max().date()),
        "constituent_sources": sources,
        "likely_delisted": int(len(stale)),
        "SURVIVORSHIP_WARNING": (
            f"{len(stale)} of {px.ticker.nunique()} tickers stopped updating and are "
            "probably delisted. If that number is near zero, this universe is "
            "survivor-only and any dip-buying result from it is optimistic."
        ),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("\n" + json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
