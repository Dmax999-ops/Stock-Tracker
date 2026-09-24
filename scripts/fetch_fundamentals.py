#!/usr/bin/env python3
"""
Company accounts for every stock in the universe, from SEC EDGAR, point in time.

WHY
---
Every stock-picking test so far used PRICES ONLY -- momentum, trends, highs,
volatility -- and none of them told you in advance which S&P 500 stocks would
do best. The stock-picking methods with the strongest published record use
the ACCOUNTS: how profitable a company is, how cheap it is against its
earnings and cash, whether it is piling up assets or paper profits that
never turn into cash. This fetches the numbers those need.

POINT IN TIME
-------------
Each number is stored with the date it was FILED with the SEC, not the date
of the period it covers. A test on 1 March 2015 may only use accounts filed
on or before 1 March 2015. Using figures before they were public is the
easiest way to fake a stock picker.

SOURCE
------
EDGAR "companyfacts" (XBRL). Free, no key, the legal filing itself. Coverage
starts 2009-2011 (when XBRL tagging became mandatory), so fundamental tests
run from about 2010.

OUTPUT
------
    data/fundamentals.parquet   ticker, item, end, filed, val   (annual, from 10-Ks)
    data/fundamentals_manifest.json
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

TICKER_MAP = "https://www.sec.gov/files/company_tickers.json"
FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
SLEEP = 0.12

# what each measure is called in the filings; first tag found wins, per year
ITEMS = {
    "assets": ["Assets"],
    "equity": ["StockholdersEquity",
               "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "cogs": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"],
    "gross_profit": ["GrossProfit"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
}
DEI_FLOAT = "EntityPublicFloat"          # market value of shares, stated in the 10-K


def session() -> requests.Session:
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua or "@" not in ua:
        print("SEC_USER_AGENT not set (repo Settings -> Secrets and variables -> Actions "
              "-> Variables). Refusing to call EDGAR anonymously.", file=sys.stderr)
        raise SystemExit(2)
    s = requests.Session()
    s.headers.update({"User-Agent": ua, "Accept-Encoding": "gzip, deflate"})
    return s


def ticker_to_cik(s) -> dict[str, int]:
    r = s.get(TICKER_MAP, timeout=60)
    r.raise_for_status()
    out = {}
    for row in r.json().values():
        out.setdefault(str(row["ticker"]).upper().replace(".", "-"), int(row["cik_str"]))
    return out


def annual_rows(doc: dict, ticker: str) -> list[dict]:
    """Annual (10-K, full-year) values for each item, with their filing dates."""
    rows = []
    gaap = doc.get("facts", {}).get("us-gaap", {})
    for item, tags in ITEMS.items():
        seen_end = set()
        for tag in tags:
            units = gaap.get(tag, {}).get("units", {}).get("USD", [])
            for u in units:
                if not str(u.get("form", "")).startswith("10-K") or u.get("fp") != "FY":
                    continue
                if "start" in u:          # flow item: must cover about a year
                    days = (pd.Timestamp(u["end"]) - pd.Timestamp(u["start"])).days
                    if not 350 <= days <= 380:
                        continue
                if u["end"] in seen_end:
                    continue
                rows.append({"ticker": ticker, "item": item, "end": u["end"],
                             "filed": u["filed"], "val": float(u["val"])})
            seen_end |= {r["end"] for r in rows if r["item"] == item}
    for u in doc.get("facts", {}).get("dei", {}).get(DEI_FLOAT, {}).get("units", {}).get("USD", []):
        if str(u.get("form", "")).startswith("10-K"):
            rows.append({"ticker": ticker, "item": "public_float", "end": u["end"],
                         "filed": u["filed"], "val": float(u["val"])})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default="data/prices.parquet")
    ap.add_argument("--out", default="data/fundamentals.parquet")
    a = ap.parse_args()
    tickers = sorted(pd.read_parquet(a.prices, columns=["ticker"])["ticker"].unique())
    s = session()
    cik = ticker_to_cik(s)
    rows, missing, failed = [], [], []
    for n, t in enumerate(tickers):
        c = cik.get(t.upper())
        if c is None:
            missing.append(t)
            continue
        try:
            r = s.get(FACTS.format(cik=c), timeout=60)
            if r.status_code == 404:
                missing.append(t)
            else:
                r.raise_for_status()
                rows += annual_rows(r.json(), t)
        except Exception as e:                                     # noqa: BLE001
            failed.append(f"{t}: {type(e).__name__}")
        time.sleep(SLEEP)
        if n % 100 == 0:
            print(f"  {n}/{len(tickers)}  rows so far {len(rows):,}", flush=True)
    df = pd.DataFrame(rows)
    df["end"] = pd.to_datetime(df["end"])
    df["filed"] = pd.to_datetime(df["filed"])
    # a figure restated in a later 10-K keeps its FIRST filing date: that is when
    # the market first saw a number for that year
    df = df.sort_values("filed").drop_duplicates(["ticker", "item", "end"], keep="first")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(a.out, index=False)
    man = {"generated": pd.Timestamp.now("UTC").isoformat(), "tickers": len(tickers),
           "with_accounts": int(df["ticker"].nunique()), "rows": len(df),
           "no_cik_or_facts": len(missing), "failed": failed[:50],
           "first_filed": str(df["filed"].min().date()), "last_filed": str(df["filed"].max().date()),
           "note": ("Tickers no longer listed usually have no CIK mapping, so failed or "
                    "acquired companies are under-represented -- the usual survivorship bias.")}
    Path(a.out).with_name("fundamentals_manifest.json").write_text(json.dumps(man, indent=2))
    print(json.dumps(man, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
