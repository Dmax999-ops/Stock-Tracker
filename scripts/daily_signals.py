#!/usr/bin/env python3
"""
Daily signal run.

Refreshes only the holdings, classifies each into a state, and writes signals.json
-- which is what the dashboard renders and what Claude reads back through
raw.githubusercontent.com.

Also appends to data/signal_history.csv. That file is the point: every call is
committed with a timestamp, so git makes the prediction log tamper-evident. After
twelve months it is the only genuinely out-of-sample record you will have, and it
is the one that can prove the system wrong.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quant import states                                    # noqa: E402


def load_prices(ticker: str, start: str = "2015-01-01") -> pd.DataFrame:
    import yfinance as yf
    d = yf.Ticker(ticker).history(start=start, auto_adjust=True)
    if d.empty:
        raise ValueError(f"no data for {ticker}")
    d.index = pd.to_datetime(d.index).tz_localize(None)
    return d.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdings", required=True)
    ap.add_argument("--evidence", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cfg = yaml.safe_load(Path(a.holdings).read_text())
    evidence = {}
    if a.evidence and Path(a.evidence).exists():
        evidence = json.loads(Path(a.evidence).read_text())

    rows = []
    for h in cfg["holdings"]:
        t = h["ticker"]
        try:
            px = load_prices(t)
        except Exception as e:                               # noqa: BLE001
            rows.append({"ticker": t, "name": h.get("name", t),
                         "state": "NO DATA", "action": "HOLD", "reason": str(e)})
            continue

        res = states.latest(px)
        C = px["close"]
        vol = C.pct_change().rolling(126).std().iloc[-1] * (252 ** 0.5)
        rows.append({
            "ticker": t,
            "name": h.get("name", t),
            "price": round(float(C.iloc[-1]), 4),
            "currency": h.get("currency", "USD"),
            "as_of": str(C.index[-1].date()),
            **res,
            "vol_6mo": round(float(vol), 3),
            # volatility-scaled target weight: no forecast involved
            "target_weight": round(min(0.25, 0.25 / vol), 3) if vol and vol > 0 else None,
            "from_52w_high": round(float(C.iloc[-1] / C.rolling(252).max().iloc[-1] - 1), 3),
        })

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "evidence_version": evidence.get("generated"),
        "state_evidence": evidence.get("states"),
        "holdings": rows,
        "changes_today": [r["ticker"] for r in rows if r.get("changed_today")],
        "disclaimer": ("Signals, not advice. Two of six states carry statistical "
                       "weight; the rest are noise. See README."),
    }

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))

    # tamper-evident prediction log
    hist = Path("data/signal_history.csv")
    hist.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([{"date": r.get("as_of"), "ticker": r["ticker"],
                        "state": r.get("state"), "action": r.get("action"),
                        "price": r.get("price")} for r in rows])
    df.to_csv(hist, mode="a", header=not hist.exists(), index=False)

    print(json.dumps({r["ticker"]: f"{r.get('state')} -> {r.get('action')}"
                      for r in rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
