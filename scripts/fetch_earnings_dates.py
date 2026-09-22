#!/usr/bin/env python3
"""
Earnings announcement dates for the whole universe, from SEC EDGAR.

WHY THIS EXISTS
---------------
The one signal that showed promise -- how a stock reacts in the week its results
land -- needs the announcement date for every stock, not just the fifteen we own.
Alpha Vantage would give us that at one call per ticker, 25 calls a day: six months
for 600 tickers.

EDGAR gives the same thing for free, with no key and no daily cap. When a US company
reports results it files an 8-K carrying **item 2.02, "Results of Operations and
Financial Condition"**. That filing date IS the announcement date, and it is the
legal record of it rather than a vendor's reconstruction.

Coverage runs from 2001 (when the item-numbering scheme began) to today.

RATE LIMITS AND MANNERS
-----------------------
SEC asks for max 10 requests/second and a User-Agent naming a real contact. Set
SEC_USER_AGENT in the repo (Settings -> Secrets and variables -> Actions ->
Variables) to something like "Dave Maxwell david@example.com". Without it this
script refuses to run rather than hammering EDGAR anonymously.

OUTPUT
------
    data/earnings_dates.csv      ticker,date,items,form,accession
    data/earnings_dates_manifest.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import yaml

TICKER_MAP = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
PAGED = "https://data.sec.gov/submissions/{name}"

SLEEP = 0.12          # ~8 requests/second, under SEC's 10/s ceiling
EARNINGS_ITEM = "2.02"


def session() -> requests.Session:
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua or "@" not in ua:
        print("SEC_USER_AGENT not set (needs a name and email, e.g. "
              "'Dave Maxwell dave@example.com'). Refusing to call EDGAR.",
              file=sys.stderr)
        raise SystemExit(2)
    s = requests.Session()
    s.headers.update({"User-Agent": ua, "Accept-Encoding": "gzip, deflate"})
    return s


def ticker_to_cik(s: requests.Session) -> dict[str, int]:
    r = s.get(TICKER_MAP, timeout=60)
    r.raise_for_status()
    out: dict[str, int] = {}
    for row in r.json().values():
        out.setdefault(str(row["ticker"]).upper(), int(row["cik_str"]))
    return out


def _rows(block: dict) -> list[tuple[str, str, str, str]]:
    """(form, filingDate, items, accession) from a filings block."""
    n = len(block.get("form", []))
    items = block.get("items") or [""] * n
    acc = block.get("accessionNumber") or [""] * n
    return list(zip(block["form"], block["filingDate"], items, acc))


def announcements(s: requests.Session, cik: int) -> list[tuple[str, str, str, str]]:
    """
    Every 8-K carrying item 2.02 for one company, across all submission pages.
    'recent' holds roughly the last 1,000 filings; anything older lives in the
    paged files listed alongside it, which is where the pre-2015 history is.
    """
    r = s.get(SUBMISSIONS.format(cik=cik), timeout=60)
    r.raise_for_status()
    doc = r.json()
    time.sleep(SLEEP)

    rows = _rows(doc["filings"]["recent"])
    for f in doc["filings"].get("files", []):
        try:
            rp = s.get(PAGED.format(name=f["name"]), timeout=60)
            rp.raise_for_status()
            rows += _rows(rp.json())
        except Exception as e:                                   # noqa: BLE001
            print(f"    page {f['name']} failed: {str(e)[:60]}", file=sys.stderr)
        time.sleep(SLEEP)

    return [r_ for r_ in rows
            if r_[0].startswith("8-K") and EARNINGS_ITEM in (r_[2] or "")]


def universe(cfg_path: str) -> list[str]:
    cfg = yaml.safe_load(Path(cfg_path).read_text())
    src = next(s for s in cfg["constituent_sources"]
               if s.get("format") == "historical_union")
    h = pd.read_csv(src["url"])
    t: set[str] = set()
    for row in h["tickers"]:
        t.update(x.strip().upper() for x in str(row).split(",") if x.strip())
    t.update(x.upper() for x in cfg.get("extra_tickers", []))
    return sorted(t)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/universe.yml")
    ap.add_argument("--out", default="data")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap tickers per run (0 = all); state is the output file")
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    dest = out / "earnings_dates.csv"

    s = session()
    print("Resolving ticker -> CIK...")
    cik = ticker_to_cik(s)
    time.sleep(SLEEP)

    want = universe(a.config)
    have: set[str] = set()
    if dest.exists():
        have = set(pd.read_csv(dest, usecols=["ticker"]).ticker.unique())
    todo = [t for t in want if t not in have]
    if a.limit:
        todo = todo[:a.limit]

    matched = [t for t in todo if t in cik]
    print(f"universe {len(want)}, already done {len(have)}, "
          f"this run {len(matched)} (no CIK for {len(todo) - len(matched)})\n")

    rows = []
    for i, t in enumerate(matched, 1):
        try:
            for form, date, items, acc in announcements(s, cik[t]):
                rows.append({"ticker": t, "date": date, "items": items,
                             "form": form, "accession": acc})
        except Exception as e:                                   # noqa: BLE001
            print(f"  {t:6} FAILED {str(e)[:70]}", file=sys.stderr)
        if i % 25 == 0:
            print(f"  {i}/{len(matched)} tickers, {len(rows)} announcements",
                  flush=True)

    new = pd.DataFrame(rows)
    if dest.exists() and not new.empty:
        new = pd.concat([pd.read_csv(dest), new], ignore_index=True)
    elif dest.exists():
        new = pd.read_csv(dest)
    if new.empty:
        print("nothing fetched", file=sys.stderr)
        return 1

    new = new.drop_duplicates(["ticker", "accession"]).sort_values(["ticker", "date"])
    new.to_csv(dest, index=False)

    man = {
        "generated": pd.Timestamp.now("UTC").isoformat(),
        "tickers_with_announcements": int(new.ticker.nunique()),
        "announcements": int(len(new)),
        "date_min": str(new.date.min()),
        "date_max": str(new.date.max()),
        "universe_size": len(want),
        "no_cik_match": len([t for t in want if t not in cik]),
        "SOURCE": "SEC EDGAR 8-K item 2.02 (Results of Operations). Filing date "
                  "is the announcement date. Item numbering starts 2001, so "
                  "earlier results are not covered.",
    }
    (out / "earnings_dates_manifest.json").write_text(json.dumps(man, indent=2))
    print("\n" + json.dumps(man, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
