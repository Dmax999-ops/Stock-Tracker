#!/usr/bin/env python3
"""
A register of who failed, and when — built from the filings themselves.

THE INSIGHT THIS RESTS ON
-------------------------
We have been hunting PRICE HISTORY for dead companies, which is the expensive
half and the half nobody gives away. But most of the survivorship damage can be
repaired without it, because what actually biases a backtest is not the missing
prices -- it is the silent deletion. A stock that simply stops appearing looks,
to a simulator, like a position that was never opened.

Give the simulator a delisting DATE and a CAUSE and it can do the honest thing:
close every open position on that date, at zero for a liquidation and at the last
traded price for a takeover. The bias is then bounded rather than invisible.

And the delisting date is free, complete and authoritative, because a US listing
cannot end without a filing:

    25-NSE   Notification of Removal from Listing. Filed by the EXCHANGE when it
             delists a security. This is the delisting, in the exchange's own hand.
    25       The issuer's own version of the same notice.
    15-12B   Certification of termination of registration of a listed class --
             the company telling the SEC it has stopped reporting.
    15-12G   The same for a registered, unlisted class.
    8-K 1.03 "Bankruptcy or Receivership". The failure event itself, dated.

Cause is inferred from which of those appears and in what order. A company that
files 8-K item 1.03 and then a 25-NSE went bankrupt and was thrown off the
exchange. One that files only a 25-NSE and a 15-12B was almost certainly bought.

WHAT THIS DOES NOT SOLVE
------------------------
It gives dates and causes, not prices. For the price history itself the options
are Alpha Vantage at 25 calls a day (already running), Stooq, or paid feeds.
But a dated register plus a terminal assumption is enough to put an honest error
bar on every result in this repo, which is the thing we actually lack.

OUTPUT
------
    data/delistings.csv    ticker,cik,company,event,form,date,source
    data/delistings_manifest.json
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
FTS = "https://efts.sec.gov/LATEST/search-index"

SLEEP = 0.12
FORMS = {"25-NSE": "exchange_delisting",
         "25": "issuer_delisting",
         "15-12B": "deregistration_listed",
         "15-12G": "deregistration_unlisted"}
BANKRUPTCY_ITEM = "1.03"


def session() -> requests.Session:
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua or "@" not in ua:
        print("SEC_USER_AGENT not set. Refusing to call EDGAR.", file=sys.stderr)
        raise SystemExit(2)
    s = requests.Session()
    s.headers.update({"User-Agent": ua, "Accept-Encoding": "gzip, deflate"})
    return s


def ticker_to_cik(s: requests.Session) -> dict[str, int]:
    r = s.get(TICKER_MAP, timeout=60)
    r.raise_for_status()
    return {str(v["ticker"]).upper(): int(v["cik_str"]) for v in r.json().values()}


def _rows(block: dict):
    n = len(block.get("form", []))
    items = block.get("items") or [""] * n
    return list(zip(block["form"], block["filingDate"], items))


def events_for(s: requests.Session, cik: int) -> tuple[str, list[tuple[str, str, str]]]:
    """(company name, [(event, form, date)]) for one filer."""
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
        except Exception:                                        # noqa: BLE001
            pass
        time.sleep(SLEEP)

    out = []
    for form, date, items in rows:
        base = form.split("/")[0].strip().upper()
        if base in FORMS:
            out.append((FORMS[base], form, date))
        elif base.startswith("8-K") and BANKRUPTCY_ITEM in (items or ""):
            out.append(("bankruptcy", form, date))
    return doc.get("name", ""), out


def find_cik_by_ticker(s: requests.Session, ticker: str) -> int | None:
    """
    For a ticker the current SEC map has never heard of -- because the company
    is long gone -- ask full-text search. It covers 2001 onwards, which is the
    same window the rest of this register lives in.
    """
    try:
        r = s.get(FTS, params={"q": f'"{ticker}"', "forms": "25-NSE,25"},
                  timeout=60)
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])
        time.sleep(SLEEP)
        for h in hits:
            ciks = h.get("_source", {}).get("ciks") or []
            if ciks:
                return int(str(ciks[0]).lstrip("0") or 0)
    except Exception:                                            # noqa: BLE001
        pass
    return None


def universe(cfg_path: str) -> list[str]:
    cfg = yaml.safe_load(Path(cfg_path).read_text())
    src = next(x for x in cfg["constituent_sources"]
               if x.get("format") == "historical_union")
    h = pd.read_csv(src["url"])
    t: set[str] = set()
    for row in h["tickers"]:
        t.update(x.strip().upper() for x in str(row).split(",") if x.strip())
    return sorted(t)


def classify(events: list[dict]) -> tuple[str, str | None]:
    """Terminal date and inferred cause for one company."""
    if not events:
        return "unknown", None
    df = pd.DataFrame(events).sort_values("date")
    kinds = set(df.event)
    date = df[df.event.isin(["exchange_delisting", "issuer_delisting"])]["date"]
    terminal = date.min() if len(date) else df.date.max()
    if "bankruptcy" in kinds:
        return "bankruptcy", terminal
    if {"exchange_delisting", "issuer_delisting"} & kinds:
        return ("deregistered_after_delisting"
                if "deregistration_listed" in kinds else "delisted"), terminal
    return "deregistered", terminal


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/universe.yml")
    ap.add_argument("--out", default="data")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    dest = out / "delistings.csv"
    env = {"pandas": pd.__version__, "python": sys.version.split()[0]}

    try:
        s = session()
        cik = ticker_to_cik(s)
        time.sleep(SLEEP)
        want = universe(a.config)

        done: set[str] = set()
        if dest.exists():
            done = set(pd.read_csv(dest, usecols=["ticker"]).ticker.unique())
        todo = [t for t in want if t not in done]
        if a.limit:
            todo = todo[:a.limit]
        print(f"universe {len(want)}, already done {len(done)}, "
              f"this run {len(todo)}")

        rows, resolved_by_search = [], 0
        for i, t in enumerate(todo, 1):
            c = cik.get(t)
            if c is None:
                c = find_cik_by_ticker(s, t)
                if c:
                    resolved_by_search += 1
            if not c:
                rows.append({"ticker": t, "cik": None, "company": None,
                             "event": "no_cik", "form": None, "date": None,
                             "source": "unresolved"})
                continue
            try:
                name, evs = events_for(s, c)
                if not evs:
                    rows.append({"ticker": t, "cik": c, "company": name,
                                 "event": "still_listed_or_no_event",
                                 "form": None, "date": None, "source": "edgar"})
                for ev, form, date in evs:
                    rows.append({"ticker": t, "cik": c, "company": name,
                                 "event": ev, "form": form, "date": date,
                                 "source": "edgar"})
            except Exception as e:                               # noqa: BLE001
                print(f"  {t:8} FAILED {str(e)[:60]}", file=sys.stderr)
            if i % 25 == 0:
                print(f"  {i}/{len(todo)}  rows {len(rows)}", flush=True)

        new = pd.DataFrame(rows)
        if dest.exists() and not new.empty:
            new = pd.concat([pd.read_csv(dest), new], ignore_index=True)
        elif dest.exists():
            new = pd.read_csv(dest)
        new.to_csv(dest, index=False)

        # one line per company: when it ended and why
        reg = []
        for t, g in new[new.date.notna()].groupby("ticker"):
            cause, date = classify(g.to_dict("records"))
            reg.append({"ticker": t, "cause": cause, "terminal_date": date})
        R = pd.DataFrame(reg)
        if not R.empty:
            R.to_csv(out / "delisting_register.csv", index=False)

        man = {
            "generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
            "universe": len(want),
            "tickers_processed": int(new.ticker.nunique()),
            "with_terminal_event": int(len(R)),
            "resolved_by_full_text_search": resolved_by_search,
            "unresolved": int((new.event == "no_cik").sum()),
            "by_cause": (R.cause.value_counts().to_dict() if not R.empty else {}),
            "SOURCE": "SEC EDGAR forms 25-NSE, 25, 15-12B, 15-12G and 8-K item "
                      "1.03. Dates are filing dates, which for a 25-NSE is the "
                      "exchange's own notice of removal.",
        }
        (out / "delistings_manifest.json").write_text(json.dumps(man, indent=2))
        print("\n" + json.dumps(man, indent=2))
        return 0
    except Exception as exc:                                     # noqa: BLE001
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        (out / "delistings_manifest.json").write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(), "env": env,
             "error": f"{type(exc).__name__}: {exc}",
             "traceback": tb.splitlines()[-25:]}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
