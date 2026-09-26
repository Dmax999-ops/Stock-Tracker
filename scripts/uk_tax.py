#!/usr/bin/env python3
"""
UK Capital Gains Tax on a share account (a general investment account, NOT an ISA:
gains inside a Stocks & Shares ISA are tax-free and none of this applies).

Rules used (2026/27, HMRC):
  * Tax year runs 6 April to 5 April. Gains are reported through Self Assessment
    and the tax is PAID by 31 January after the tax year ends (2026/27 -> 31 Jan 2028).
    Nothing is payable before then, so the money can stay invested until that date.
  * Annual exempt amount: GBP 3,000 of net gains a year, tax-free.
  * Rates on shares: 18% for the part of gains inside your basic-rate band,
    24% above it. Both are shown, because the split depends on your income.
  * Losses are set against gains of the same year first; unused losses are
    carried forward and used only to bring later gains down to the exempt amount.
  * Share matching, in HMRC order, for every sale:
        1. shares of the same company bought the SAME DAY
        2. shares bought in the NEXT 30 DAYS ("bed and breakfast" rule)
        3. the Section 104 pool (average cost of everything else held)
  * Dealing charges and currency-exchange fees are allowable costs: they are
    added to the purchase cost and taken off the sale proceeds.

This is an estimate to plan with, not tax advice. It ignores dividends (a
GBP 500 allowance applies; an accumulating S&P 500 tracker avoids payouts) and
currency gains/losses on the dollars themselves.
"""
from __future__ import annotations

from collections import defaultdict

import pandas as pd

AEA = 3_000.0
RATES = (0.18, 0.24)


def tax_year(d) -> str:
    d = pd.Timestamp(d)
    y = d.year if (d.month, d.day) >= (4, 6) else d.year - 1
    return f"{y}/{str(y + 1)[-2:]}"


def due_date(ty: str) -> str:
    y = int(ty[:4]) + 2
    return f"31 Jan {y}"


def disposals(trades: list[dict]) -> list[dict]:
    """
    trades: {"date", "asset", "side" ("BUY"/"SELL"), "qty", "gbp"} where gbp is the
    total cost paid (buys, incl. charges) or net proceeds received (sells, after charges).
    Returns one row per sale: proceeds, allowable cost, gain.
    """
    by = defaultdict(list)
    for t in trades:
        if t["qty"] > 0:
            by[t["asset"]].append(dict(t, date=pd.Timestamp(t["date"]), left=t["qty"]))
    out = []
    for asset, ev in by.items():
        ev.sort(key=lambda t: (t["date"], 0 if t["side"] == "BUY" else 1))
        buys = [t for t in ev if t["side"] == "BUY"]
        sells = [t for t in ev if t["side"] == "SELL"]
        # rules 1 and 2: same day, then the next 30 days
        matched = {id(s): [] for s in sells}
        for s in sells:
            need = s["left"]
            cands = ([b for b in buys if b["date"] == s["date"]]
                     + [b for b in buys if s["date"] < b["date"] <= s["date"] + pd.Timedelta(days=30)])
            for b in cands:
                if need <= 1e-12:
                    break
                q = min(need, b["left"])
                if q > 0:
                    matched[id(s)].append(q * b["gbp"] / b["qty"])
                    b["left"] -= q
                    need -= q
            s["left"] = need
        # rule 3: the Section 104 pool, in date order
        pool_q = pool_c = 0.0
        for t in ev:
            if t["side"] == "BUY":
                if t["left"] > 1e-12:
                    pool_c += t["left"] * t["gbp"] / t["qty"]
                    pool_q += t["left"]
            else:
                cost = sum(matched[id(t)])
                q = min(t["left"], pool_q)
                if q > 0 and pool_q > 0:
                    c = pool_c * q / pool_q
                    cost += c
                    pool_c -= c
                    pool_q -= q
                out.append({"date": t["date"], "asset": asset, "qty": t["qty"],
                            "proceeds": t["gbp"], "cost": cost, "gain": t["gbp"] - cost,
                            "tax_year": tax_year(t["date"])})
    return sorted(out, key=lambda r: r["date"])


def by_tax_year(disp: list[dict]) -> list[dict]:
    years = sorted({d["tax_year"] for d in disp})
    carried = 0.0
    rows = []
    for ty in years:
        g = [d["gain"] for d in disp if d["tax_year"] == ty]
        gains, losses = sum(x for x in g if x > 0), -sum(x for x in g if x < 0)
        net = gains - losses
        used_bf = min(carried, max(net - AEA, 0.0)) if net > AEA else 0.0
        carried -= used_bf
        if net < 0:
            carried += -net
        taxable = max(net - AEA - used_bf, 0.0)
        rows.append({"tax_year": ty, "gains": gains, "losses": losses, "net": net,
                     "taxable": taxable, "tax_basic": taxable * RATES[0],
                     "tax_higher": taxable * RATES[1], "due": due_date(ty),
                     "losses_carried": carried, "sales": len(g)})
    return rows
