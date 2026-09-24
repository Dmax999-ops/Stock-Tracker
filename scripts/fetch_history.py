#!/usr/bin/env python3
"""
A hundred years of monthly history, saved into the repo.

WHY
---
The ETF test found the sector-rotation-plus-bonds rule beating the S&P 500 by
about 2% a year with a third of the drawdown -- but with a full-period excess
t of +0.39. The whole edge came from two bear markets, 2000-02 and 2008, and two
events cannot prove a rule.

More bear markets can. Kenneth French's data library (Dartmouth) publishes
monthly returns for the US market, T-bills and ten industry portfolios from
1926: 1929, 1937, 1946, 1962, 1973-74, 1987, 2000, 2008 and more. 1926-1999 is
history these rules have never been tested on, so it is a genuine out-of-sample
test.

The files are committed to data/history/ so every later test can run from the
repo -- including in the analysis sandbox, which cannot reach Dartmouth itself.

OUTPUT (all monthly, decimal returns, month-end dates)
------------------------------------------------------
    data/history/market.csv       US market total return, and the T-bill rate
    data/history/industries.csv   10 value-weighted industry portfolios
    data/history/bond10y.csv      10-year Treasury total return, built from yields
    data/history/manifest.json    sources, spans, and anything that failed
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
F_FACTORS = FRENCH + "F-F_Research_Data_Factors_CSV.zip"
F_IND10 = FRENCH + "10_Industry_Portfolios_CSV.zip"
# Finer industries. Momentum is consistently stronger with finer groupings --
# ten broad sectors blur it -- and many of these finer industries now have
# their own ETFs.
F_IND30 = FRENCH + "30_Industry_Portfolios_CSV.zip"
F_IND49 = FRENCH + "49_Industry_Portfolios_CSV.zip"
FRED_GS10 = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS10"
FRED_GS10_ALT = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS10&cosd=1953-04-01"
SHILLER = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
UA = {"User-Agent": "Mozilla/5.0 (research; Stock-Tracker)"}


def french_first_monthly_table(text: str) -> pd.DataFrame:
    """
    French's CSVs are several tables in one file. The FIRST block of rows whose
    first field is a six-digit YYYYMM is the monthly table (value-weighted, for
    the industry file). Stop at the first line that breaks the run.
    """
    rows, header, started = [], None, False
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if not started:
            if len(parts) > 2 and parts[0] == "" and all(p for p in parts[1:]):
                header = parts[1:]
            if parts and len(parts[0]) == 6 and parts[0].isdigit() and header:
                started = True
            else:
                continue
        if not (parts and len(parts[0]) == 6 and parts[0].isdigit()):
            break
        rows.append(parts)
    if not rows or header is None:
        raise ValueError("no monthly table found")
    df = pd.DataFrame([r[1:len(header) + 1] for r in rows], columns=header)
    df.index = pd.to_datetime([r[0] for r in rows], format="%Y%m") + pd.offsets.MonthEnd(0)
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.mask(df <= -99.0)             # French's missing-value code
    return df / 100.0


def get_zip_csv(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=120)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
    return z.read(name).decode("latin-1")


def bond_returns_from_yields(y: pd.Series, maturity_years: int = 10) -> pd.Series:
    """
    Monthly total return of a constant-maturity 10-year Treasury, from its
    yield. Each month: buy a par bond at last month's yield, reprice it one
    month later at this month's yield with one month less to run, collect the
    coupon. The standard reconstruction when no bond fund existed yet.
    """
    y = y.dropna() / 100.0
    out = {}
    prev_t, prev_y = None, None
    for t, yt in y.items():
        if prev_y is not None:
            c = prev_y                         # par coupon at purchase
            n = maturity_years * 12 - 1        # months remaining after one month
            i = yt / 12.0
            if i > 0:
                price = c / 12.0 * (1 - (1 + i) ** -n) / i + (1 + i) ** -n
            else:
                price = c / 12.0 * n + 1
            out[t] = price - 1 + c / 12.0
        prev_t, prev_y = t, yt
    return pd.Series(out, name="BOND")


def long_yields(man: dict) -> pd.Series:
    """Shiller's long rate from 1871, spliced with FRED GS10 where it exists."""
    parts = []
    try:
        r = requests.get(SHILLER, headers=UA, timeout=120)
        r.raise_for_status()
        x = pd.read_excel(io.BytesIO(r.content), sheet_name="Data", header=7)
        date_col = [c for c in x.columns if str(c).strip().lower().startswith("date")][0]
        rate_col = [c for c in x.columns if "GS10" in str(c) or "Rate GS10" in str(c)
                    or str(c).strip().lower().startswith("long")][0]
        x = x[[date_col, rate_col]].dropna()
        d = x[date_col].astype(float)
        yr = d.astype(int)
        mo = ((d - yr) * 100).round().astype(int).clip(1, 12)
        idx = pd.to_datetime(dict(year=yr, month=mo, day=1)) + pd.offsets.MonthEnd(0)
        s = pd.Series(pd.to_numeric(x[rate_col], errors="coerce").to_numpy(), index=idx)
        parts.append(s.dropna())
        man["shiller"] = f"ok {s.index[0].date()} -> {s.index[-1].date()}"
    except Exception as e:                                         # noqa: BLE001
        man["shiller"] = f"FAILED: {type(e).__name__}: {e}"
    try:
        r, last = None, None
        for attempt in range(4):
            for url in (FRED_GS10, FRED_GS10_ALT):
                try:
                    r = requests.get(url, headers=UA, timeout=300)
                    r.raise_for_status()
                    break
                except Exception as e:                             # noqa: BLE001
                    last, r = e, None
            if r is not None:
                break
            import time
            time.sleep(20 * (attempt + 1))
        if r is None:
            raise last
        f = pd.read_csv(io.StringIO(r.text))
        f.columns = ["date", "GS10"]
        f["date"] = pd.to_datetime(f["date"]) + pd.offsets.MonthEnd(0)
        s = pd.to_numeric(f.set_index("date")["GS10"], errors="coerce").dropna()
        parts.append(s)
        man["fred_gs10"] = f"ok {s.index[0].date()} -> {s.index[-1].date()}"
    except Exception as e:                                         # noqa: BLE001
        man["fred_gs10"] = f"FAILED: {type(e).__name__}: {e}"
    if not parts:
        raise RuntimeError("no long-yield source reachable")
    y = parts[0]
    for p in parts[1:]:
        y = p.combine_first(y)                 # FRED wins where both exist
    return y.sort_index()


def main() -> int:
    out = Path("data/history")
    out.mkdir(parents=True, exist_ok=True)
    man: dict = {"generated": pd.Timestamp.now("UTC").isoformat(),
                 "sources": {"french": FRENCH, "fred": FRED_GS10, "shiller": SHILLER}}
    try:
        fac = french_first_monthly_table(get_zip_csv(F_FACTORS))
        mkt = pd.DataFrame({"MKT": fac["Mkt-RF"] + fac["RF"], "RF": fac["RF"]})
        mkt.to_csv(out / "market.csv", index_label="date")
        man["market"] = f"{mkt.index[0].date()} -> {mkt.index[-1].date()} ({len(mkt)} months)"

        ind = french_first_monthly_table(get_zip_csv(F_IND10))
        ind.to_csv(out / "industries.csv", index_label="date")
        man["industries"] = (f"{list(ind.columns)} {ind.index[0].date()} -> "
                             f"{ind.index[-1].date()}")

        for name, url in (("industries30", F_IND30), ("industries49", F_IND49)):
            try:
                d = french_first_monthly_table(get_zip_csv(url))
                d.to_csv(out / f"{name}.csv", index_label="date")
                man[name] = f"{d.shape[1]} industries {d.index[0].date()} -> {d.index[-1].date()}"
            except Exception as e:                                 # noqa: BLE001
                man[name] = f"FAILED: {type(e).__name__}: {e}"

        y = long_yields(man)
        b = bond_returns_from_yields(y)
        b.to_frame().to_csv(out / "bond10y.csv", index_label="date")
        man["bond10y"] = f"{b.index[0].date()} -> {b.index[-1].date()} ({len(b)} months)"
        man["status"] = "ok"
        print(json.dumps(man, indent=2))
        (out / "manifest.json").write_text(json.dumps(man, indent=2))
        return 0
    except Exception as exc:                                       # noqa: BLE001
        import traceback
        man["status"] = "error"
        man["error"] = f"{type(exc).__name__}: {exc}"
        man["traceback"] = traceback.format_exc().splitlines()[-20:]
        (out / "manifest.json").write_text(json.dumps(man, indent=2))
        print(json.dumps(man, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
