#!/usr/bin/env python3
"""
The daily plan: what to do with what you own, and what you should own.

TWO OUTPUTS, EVERY WEEKDAY
--------------------------
1. YOUR HOLDINGS   one clear action per stock: BUY (add), HOLD, or SELL.
2. THE MODEL       the GBP 10,000 portfolio the rules say to hold today, picked
                   from the whole S&P 500, with the amount in each.

Written to docs/PLAN.md (readable on GitHub) and docs/plan.json.

WHAT THE RULES ARE, AND WHY THESE ONES
--------------------------------------
Only rules that survived the tests make decisions here:

  MARKET SWITCH   the S&P 500 against its 200-day average, needing three
                  consecutive closes to flip. Over a century this cut the loss
                  in 5 of 6 major bear markets. When it is OFF, the model is
                  cash and every holding is SELL.

  INDUSTRY        GICS sub-industries ranked by average 3/6/12-month momentum.
                  Holding the strongest industries beat the market by about
                  5% a year over 1927-1999 on data the rule had never seen
                  (t above 5), and by about 4% a year since 2000. This is the
                  part with real evidence, so it drives the choice.

  STOCK TREND     a stock is in a confirmed DOWNTREND when it is below its
                  200-day average and its 50-day average is below its 200-day,
                  for three consecutive closes. This is insurance, not a
                  forecast: it rescued the collapses and cost on the
                  recoveries. It is the SELL trigger for a single stock.

  STOCK RANK      within the strong industries, the strongest stocks by the
                  same 3/6/12-month momentum. Plausible and widely documented,
                  but NOT separately proven in this project.

THE MODEL PORTFOLIO
-------------------
  - 10 stocks, GBP 1,000 each, from industries in the top fifth by momentum,
    that are in an uptrend, strongest first; at most 2 per sub-industry and 3
    per sector so no single theme dominates.
  - Rebalanced on the first trading day of each month -- the evidence is for
    monthly rotation, and Hargreaves Lansdown charges about GBP 11.95 a trade
    plus FX on US shares, so churn is expensive. Between rebalances a model
    holding is only replaced if it hits a SELL condition.
  - Hysteresis: a holding stays while its industry is still in the top 40%
    and it is not in a downtrend. New entries must be in the top 20%. That
    stops stocks flickering in and out.

YOUR HOLDINGS
-------------
  SELL  market switch OFF; or confirmed downtrend; or industry in the bottom
        fifth AND the stock below its 200-day average.
  BUY   qualifies to add: industry in the top fifth AND a confirmed uptrend.
  HOLD  everything else. "No signal" is a HOLD, not a guess.

This is what tested rules say. It is not personal financial advice.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CONSTITUENTS = ("https://raw.githubusercontent.com/datasets/"
                "s-and-p-500-companies/main/data/constituents.csv")
BUDGET = 10_000.0
N_MODEL = 10
MAX_PER_SUB, MAX_PER_SECTOR = 2, 3
ENTER_PCT, KEEP_PCT = 0.20, 0.40
MIN_SUB = 3                      # sub-industries smaller than this use sector
CONFIRM = 3
DEAL_GBP, FX_PCT = 11.95, 0.01   # HL share dealing and FX on US shares, approx

# Holdings the S&P 500 list does not cover. An `industry:` field in
# config/holdings.yml overrides these.
INDUSTRY_OVERRIDE = {
    "CELH": ("Consumer Staples", "Soft Drinks & Non-alcoholic Beverages"),
    "TEM": ("Health Care", "Health Care Services"),
    "SPCX": ("Industrials", "Aerospace & Defense"),
    "FRES.L": ("Materials", "Gold"),
    "IQE.L": ("Information Technology", "Semiconductors"),
    "ZOO.L": ("Communication Services", "Movies & Entertainment"),
    "LIT.L": ("Financials", "Asset Management & Custody Banks"),
    "DEBS.L": ("Consumer Discretionary", "Broadline Retail"),
}


def yf_symbol(s: str) -> str:
    return s.strip().replace(".", "-") if not s.endswith(".L") else s.strip()


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

def load_constituents(src=CONSTITUENTS) -> pd.DataFrame:
    d = pd.read_csv(src)
    d["yf"] = d["Symbol"].map(yf_symbol)
    return d[["Symbol", "yf", "Security", "GICS Sector", "GICS Sub-Industry"]]


IWB = ("https://www.ishares.com/us/products/239707/ishares-russell-1000-etf/"
       "1467271812596.ajax?fileType=csv&fileName=IWB_holdings&dataType=fund")
NDX_WIKI = "https://en.wikipedia.org/wiki/Nasdaq-100"


def parse_ishares(text: str) -> pd.DataFrame:
    """iShares holdings CSV: a few preamble lines, then the table."""
    import io
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Ticker,"))
    d = pd.read_csv(io.StringIO("\n".join(lines[start:])), on_bad_lines="skip")
    d = d[(d.get("Asset Class") == "Equity") & d["Ticker"].astype(str).str.match(r"^[A-Z][A-Z0-9.\-]*$")]
    if "Location" in d:
        d = d[d["Location"] == "United States"]
    fix = {"Communication": "Communication Services", "Information Technology": "Information Technology"}
    sec = d["Sector"].astype(str).replace(fix) if "Sector" in d else "Unknown"
    return pd.DataFrame({"Symbol": d["Ticker"].astype(str), "Security": d["Name"].astype(str).str.title(),
                         "GICS Sector": sec})


def load_universe(sp_src=CONSTITUENTS, man: dict | None = None) -> pd.DataFrame:
    """
    WHERE UP-AND-COMING COMPANIES ARE. Many of the newest AI and technology
    names are not in the S&P 500 yet. The universe is the Russell 1000 -- the
    1,000 largest US companies -- with the S&P 500's detailed industry labels
    where they exist. Companies without a detailed label are still grouped
    correctly, by the THEMES found from how they trade (see themes()). If the
    Russell list cannot be fetched it falls back to NASDAQ-100 + S&P 500, then
    to the S&P 500 alone -- it never simply stops.
    """
    man = man if man is not None else {}
    sp = load_constituents(sp_src)
    extra = None
    try:
        import requests
        r = requests.get(IWB, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        extra = parse_ishares(r.text)
        man["universe"] = f"Russell 1000 ({len(extra)}) + S&P 500 labels"
    except Exception as e:                                         # noqa: BLE001
        man["russell_error"] = f"{type(e).__name__}: {e}"
        try:
            import io
            import requests
            h = requests.get(NDX_WIKI, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
            h.raise_for_status()
            t = pd.read_html(io.StringIO(h.text))
            tab = next(x for x in t if "Ticker" in x.columns or "Symbol" in x.columns)
            col = "Ticker" if "Ticker" in tab.columns else "Symbol"
            extra = pd.DataFrame({"Symbol": tab[col].astype(str),
                                  "Security": tab.get("Company", tab[col]).astype(str),
                                  "GICS Sector": tab.get("GICS Sector", "Unknown")})
            man["universe"] = f"NASDAQ-100 ({len(extra)}) + S&P 500"
        except Exception as e2:                                    # noqa: BLE001
            man["nasdaq_error"] = f"{type(e2).__name__}: {e2}"
            man["universe"] = "S&P 500 only"
    if extra is not None:
        extra["yf"] = extra["Symbol"].map(yf_symbol)
        extra = extra[~extra["yf"].isin(sp["yf"])]
        extra["GICS Sub-Industry"] = ""                # grouped by theme, not label
        sp = pd.concat([sp, extra[sp.columns]], ignore_index=True)
    return sp.drop_duplicates("yf")


def load_watchlist(path="config/watchlist.yml") -> list[str]:
    """Any extra tickers you want considered -- they compete on equal terms."""
    p = Path(path)
    if not p.exists():
        return []
    import yaml
    cfg = yaml.safe_load(p.read_text()) or {}
    return [yf_symbol(str(t)) for t in (cfg.get("watchlist") or [])]


def load_holdings(path="config/holdings.yml") -> list[dict]:
    import yaml
    cfg = yaml.safe_load(Path(path).read_text()) or {}
    return [h for h in (cfg.get("holdings") or []) if h.get("ticker")]


def download(tickers: list[str]) -> pd.DataFrame:
    import yfinance as yf
    frames = []
    for i in range(0, len(tickers), 100):
        chunk = tickers[i:i + 100]
        # fixed start (not a rolling "2y"), so the strategy replay from Jan 2024
        # sees identical history every day
        d = yf.download(chunk, start="2022-06-01", auto_adjust=True, progress=False,
                        threads=True, group_by="column")
        c = d["Close"] if isinstance(d.columns, pd.MultiIndex) else d[["Close"]].rename(
            columns={"Close": chunk[0]})
        frames.append(c)
    P = pd.concat(frames, axis=1)
    P = P.loc[:, ~P.columns.duplicated()].sort_index()
    return P.dropna(how="all")


# ---------------------------------------------------------------------------
# signals
# ---------------------------------------------------------------------------

def last_valid(s: pd.Series, i: int):
    v = s.iloc[: i + 1].dropna()
    return v.iloc[-1] if len(v) else np.nan


def momentum(P: pd.DataFrame) -> pd.Series:
    """Average of 3, 6 and 12-month return, the pre-registered definition."""
    out = {}
    for c in P.columns:
        s = P[c].dropna()
        if len(s) < 253:
            out[c] = np.nan
            continue
        out[c] = np.mean([s.iloc[-1] / s.iloc[-1 - n] - 1 for n in (63, 126, 252)])
    return pd.Series(out)


METHOD = "risk_adjusted_12_1_themes_v3"


def stock_score(P: pd.DataFrame) -> pd.Series:
    """
    How the ten are chosen WITHIN strong industries.

    The first version ranked on raw momentum and picked the most violent
    movers: Sandisk +606% (it fell 56% within the year), Moderna at 263%
    annualised volatility. Those are the stocks that crash hardest when
    momentum turns. The documented fix is to rank on momentum PER UNIT OF
    VOLATILITY, and to skip the latest month, which tends to reverse:
        score = (price 1 month ago / price 12 months ago - 1) / 6-month volatility
    On a year of real prices this made nearly the same money (GBP 17,922
    against 18,263 from GBP 10,000) with a smaller worst drop (-21.5% against
    -28.5%). One year is a sanity check, not proof; the choice rests on the
    published evidence that volatility-scaled momentum crashes less.
    """
    out = {}
    for c in P.columns:
        x = P[c].dropna()
        if len(x) < 253 or c in pinned(P):
            out[c] = np.nan
            continue
        vol = max(x.pct_change().iloc[-126:].std() * np.sqrt(252), VOL_FLOOR)
        m = x.iloc[-22] / x.iloc[-253] - 1
        out[c] = m / vol
    return pd.Series(out)


VOL_FLOOR, PINNED_VOL = 0.15, 0.08


def pinned(P: pd.DataFrame) -> set[str]:
    """
    TAKEOVER TARGETS. When a company agrees to be bought for cash, its share
    price freezes just under the offer price. Its volatility collapses, and
    "momentum per unit of volatility" explodes -- the first theme version put
    AES (being taken private by GIP/EQT at a fixed price) in the ten with a
    score of 4.4. There is no upside left in a stock like that. A real
    listed company almost never moves less than 8% a year; a frozen one does.
    """
    key = (id(P), P.shape, P.index[-1])
    if _PIN.get("key") != key:
        R = P.pct_change(fill_method=None).iloc[-63:]
        v = R.std() * np.sqrt(252)
        W = P.iloc[-63:]
        rng = W.max() / W.min() - 1                  # whole 3-month range
        _PIN["key"], _PIN["val"] = key, {c for c in P.columns if c != "SPY" and (
            v.get(c, 1) < PINNED_VOL or rng.get(c, 1) < 0.05)}
    return _PIN["val"]


_PIN: dict = {}


N_THEME_DIMS, THEME_WINDOW, MAX_PER_THEME, MIN_THEME = 20, 126, 3, 6


def themes(P: pd.DataFrame, cols: list[str], score: pd.Series, univ: pd.DataFrame,
           seed: int = 0) -> tuple[pd.Series, pd.DataFrame]:
    """
    THEMES FROM THE DATA, NOT FROM LABELS.

    Official industry labels are slow and backward-looking. "AI" is not a
    label at all: it is spread across semiconductors, hardware, communications
    equipment, electrical equipment and utilities, so a label-based rule only
    ever sees it in pieces, and would miss the NEXT theme until someone
    invents a category for it.

    Stocks that move together ARE a theme, whatever they are called. So: take
    the last six months of daily returns, remove each stock's ordinary market
    movement, and group stocks by how their remaining moves line up. On real
    prices this, with no labels at all, produced a 17-stock AI data-centre
    theme spanning four official industries -- Sandisk, Micron, Lumentum,
    Western Digital, Seagate, AMD, Intel, Ciena -- alongside separate pharma,
    oil, bank and logistics themes. A new theme appears on its own the moment
    its stocks start trading together.

    Method: residual returns -> 20-dimension fingerprint (SVD) -> k-means on
    the fingerprints (cosine), about 15 stocks per theme. numpy only.
    """
    spy = P["SPY"].dropna()
    cols = [c for c in dict.fromkeys(cols) if c in P.columns and c != "SPY"]
    Q = P[cols].reindex(spy.index).ffill(limit=3).iloc[-THEME_WINDOW - 1:]
    use = [c for c in cols if Q[c].notna().all()]
    if len(use) < 60:
        return pd.Series(dtype=float), pd.DataFrame()
    Q = Q[use]
    R = Q.pct_change().iloc[1:]
    m = spy.pct_change().iloc[-THEME_WINDOW:].to_numpy()
    X = R.to_numpy()
    mv = m.var()
    beta = ((X * m[:, None]).mean(0) - X.mean(0) * m.mean()) / mv
    X = X - np.outer(m, beta)
    X = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1)
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    E = Vt[:N_THEME_DIMS].T * S[:N_THEME_DIMS]
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    k = max(20, len(use) // 15)
    rng = np.random.default_rng(seed)
    best, best_fit = None, -np.inf
    for _ in range(8):                         # several starts, keep the tightest
        C = E[rng.choice(len(E), k, replace=False)]
        for _ in range(60):
            lab = np.argmax(E @ C.T, axis=1)
            C = np.array([E[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
            C /= np.linalg.norm(C, axis=1, keepdims=True)
        # a "theme" of two or three stocks is noise, not a theme: fold tiny
        # groups into the nearest real one (smallest first, one at a time)
        while True:
            cnt = np.bincount(lab, minlength=len(C))
            small = [j for j in np.argsort(cnt) if 0 < cnt[j] < MIN_THEME]
            if not small or (cnt >= MIN_THEME).sum() == 0:
                break
            j = small[0]
            keep = np.where(cnt >= MIN_THEME)[0] if (cnt >= MIN_THEME).any() else None
            idx = np.where(lab == j)[0]
            lab[idx] = keep[np.argmax(E[idx] @ C[keep].T, axis=1)]
            for q in set(lab):
                C[q] = E[lab == q].mean(0); C[q] /= np.linalg.norm(C[q])
        fit = float((E * C[lab]).sum())
        if fit > best_fit:
            best, best_fit = lab.copy(), fit
    lab = pd.Series(best, index=use)
    names = dict(zip(univ["yf"], univ["Security"]))
    labels = dict(zip(univ["yf"], univ["GICS Sub-Industry"].fillna("").replace("", np.nan)
                      .fillna(univ["GICS Sector"])))
    rows = []
    for j in sorted(lab.unique()):
        mem = list(lab[lab == j].index)
        sc = score.reindex(mem).dropna()
        if len(mem) < 3 or len(sc) < 3:
            continue
        lead = list(sc.sort_values(ascending=False).index[:4])
        off = pd.Series([labels.get(c, "?") for c in mem]).value_counts()
        rows.append({"theme": int(j), "score": float(sc.median()), "n": len(mem),
                     "mom": float(pd.Series({c: P[c].dropna().iloc[-1] / P[c].dropna().iloc[-253] - 1
                                             for c in mem if P[c].dropna().size > 253}).median()),
                     "leaders": ", ".join(names.get(c, c) for c in lead),
                     "labels": ", ".join(f"{a} ({b})" for a, b in off.head(3).items()),
                     "members": mem})
    T = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
    T["pct"] = T["score"].rank(pct=True)
    T["rank"] = np.arange(1, len(T) + 1)
    T["of"] = len(T)
    tid = lab[lab.isin(T["theme"])]
    return tid, T


def trend_table(P: pd.DataFrame) -> pd.DataFrame:
    rows = {}
    for c in P.columns:
        s = P[c].dropna()
        if len(s) < 200:
            rows[c] = {"trend": "insufficient", "price": s.iloc[-1] if len(s) else np.nan,
                       "vs200": np.nan}
            continue
        ma50 = s.rolling(50).mean()
        ma200 = s.rolling(200).mean()
        down = ((s < ma200) & (ma50 < ma200)).astype(int)
        up = ((s > ma200) & (ma50 > ma200)).astype(int)
        confirmed_down = down.iloc[-CONFIRM:].sum() == CONFIRM
        confirmed_up = up.iloc[-CONFIRM:].sum() == CONFIRM
        rows[c] = {"trend": "down" if confirmed_down else ("up" if confirmed_up else "mixed"),
                   "price": float(s.iloc[-1]),
                   "vs200": float(s.iloc[-1] / ma200.iloc[-1] - 1)}
    return pd.DataFrame(rows).T


def market_switch(spy: pd.Series) -> dict:
    s = spy.dropna()
    ma = s.rolling(200).mean()
    above = (s > ma).astype(int)
    below = (s < ma).astype(int)
    # the switch only flips on three consecutive closes the other side
    state = True
    runs_a = above.rolling(CONFIRM).sum() == CONFIRM
    runs_b = below.rolling(CONFIRM).sum() == CONFIRM
    for i in range(len(s)):
        if state and runs_b.iat[i]:
            state = False
        elif not state and runs_a.iat[i]:
            state = True
    return {"on": bool(state), "spy": float(s.iloc[-1]), "ma200": float(ma.iloc[-1]),
            "vs200": float(s.iloc[-1] / ma.iloc[-1] - 1),
            "ret_12m": float(s.iloc[-1] / s.iloc[-253] - 1) if len(s) > 253 else None}


def industry_ranks(univ: pd.DataFrame, mom: pd.Series) -> pd.DataFrame:
    """Percentile rank of each stock's industry (1.0 = strongest)."""
    u = univ.copy()
    u["mom"] = u["yf"].map(mom)
    u["GICS Sub-Industry"] = u["GICS Sub-Industry"].fillna("")
    u["GICS Sector"] = u["GICS Sector"].fillna("Unknown").astype(str)
    sub_n = u.groupby("GICS Sub-Industry")["yf"].transform("count")
    ok = (sub_n >= MIN_SUB) & (u["GICS Sub-Industry"] != "")
    u["group"] = np.where(ok, u["GICS Sub-Industry"], "SECTOR:" + u["GICS Sector"])
    # stocks with no known industry at all are ranked by theme only; lumping
    # them into one "Unknown" group would invent an industry that doesn't exist
    g = u[u["GICS Sector"] != "Unknown"].groupby("group")["mom"].mean().dropna()
    pct = g.rank(pct=True)
    u["ind_mom"] = u["group"].map(g)
    u["ind_pct"] = u["group"].map(pct)
    return u, g.sort_values(ascending=False)


def group_of(sub: str, sector: str, groups: pd.Index) -> str:
    return sub if sub in groups else "SECTOR:" + sector


# ---------------------------------------------------------------------------
# the plan
# ---------------------------------------------------------------------------

def build_model(u: pd.DataFrame, tr: pd.DataFrame, score: pd.Series, prev: list[str],
                rebalance: bool, mkt_on: bool) -> tuple[list[dict], list[str]]:
    """
    The ten best stocks to own, from the S&P 500 AND every stock you already
    own, all competing on the same terms. Ownership gives no advantage and no
    penalty.
    """
    notes = []
    if not mkt_on:
        notes.append("Market switch is OFF: the model holds cash.")
        return [], notes
    u = u.join(tr, on="yf")
    u["score"] = u["yf"].map(score)
    held = []
    for t in prev:
        r = u[u["yf"] == t]
        if r.empty:
            notes.append(f"{t} is no longer in the candidate list: dropped.")
            continue
        r = r.iloc[0]
        if r["trend"] == "down":
            notes.append(f"{t} is in a confirmed downtrend: SELL.")
            continue
        if rebalance:
            continue                         # rebuilt from scratch below
        held.append(t)
    if rebalance or not prev:
        held = []
        # ONE ranking, purely on score. Last month's picks may stay if their
        # industry is still in the top 40% (not just the top 20%), and they get
        # a 10% tie-break -- only enough to avoid paying HL fees to swap two
        # near-identical stocks. The first version put last month's picks
        # FIRST, and that let Dell (2.50) block IQE (3.55): the opposite of
        # "the ten best, regardless".
        strong = (u["ind_pct"] >= 1 - ENTER_PCT) | (u["theme_pct"] >= 1 - ENTER_PCT)
        kept = u["yf"].isin(prev) & ((u["ind_pct"] >= 1 - KEEP_PCT)
                                     | (u["theme_pct"] >= 1 - KEEP_PCT))
        elig = u[(u["trend"] == "up") & u["score"].notna() & (strong | kept)].copy()
        elig["rank_score"] = elig["score"] * np.where(elig["yf"].isin(prev), 1.10, 1.0)
        order = elig.sort_values("rank_score", ascending=False)
        # Concentration is capped by THEME (what actually moves together), not
        # by official sector: at most 3 from any one theme, 2 per labelled
        # industry. A sector cap wrongly treated AI chips and AI-unrelated
        # software as the same risk, and AI power stocks as different.
        subs, ths = {}, {}
        for _, r in order.iterrows():
            if len(held) == N_MODEL:
                break
            sub = r["GICS Sub-Industry"] or f"_{r['yf']}"
            th = r.get("theme_id")
            th = f"_{r['yf']}" if pd.isna(th) else th
            if subs.get(sub, 0) >= MAX_PER_SUB or ths.get(th, 0) >= MAX_PER_THEME:
                continue
            held.append(r["yf"])
            subs[sub] = subs.get(sub, 0) + 1
            ths[th] = ths.get(th, 0) + 1
    elif len(held) < N_MODEL:
        notes.append(f"{N_MODEL - len(held)} slot(s) in cash until the next monthly rebalance.")
    per = BUDGET / N_MODEL
    out = []
    held = sorted(held, key=lambda t: -float(score.get(t, -9)))
    for t in held:
        r = u[u["yf"] == t].iloc[0]
        x = r.get("vol", np.nan)
        out.append({"ticker": r["Symbol"], "yf": t, "name": r["Security"],
                    "sector": r["GICS Sector"],
                    "industry": r["GICS Sub-Industry"] or r["GICS Sector"],
                    "theme": r.get("theme_leaders", "") if isinstance(r.get("theme_leaders"), str) else "",
                    "theme_rank_pct": None if pd.isna(r.get("theme_pct")) else round(float(r["theme_pct"]), 3),
                    "theme_rank": None if pd.isna(r.get("theme_rank")) else int(r["theme_rank"]),
                    "industry_rank_pct": None if pd.isna(r["ind_pct"]) else round(float(r["ind_pct"]), 3),
                    "momentum": round(float(r["mom"]), 4),
                    "score": round(float(r["score"]), 3), "gbp": per,
                    "price": round(float(r["price"]), 2), "owned": bool(r.get("owned", False))})
    return out, notes


def judge_holding(h: dict, u: pd.DataFrame, groups: pd.Series, gpct: pd.Series,
                  tr: pd.DataFrame, mom: pd.Series, model: list[str],
                  mkt_on: bool) -> dict:
    t = yf_symbol(h["ticker"])
    row = u[u["yf"] == t]
    tpct = float(row.iloc[0].get("theme_pct", np.nan)) if len(row) else np.nan
    tlead = row.iloc[0].get("theme_leaders", "") if len(row) else ""
    tlead = tlead if isinstance(tlead, str) else ""
    trank = row.iloc[0].get("theme_rank", np.nan) if len(row) else np.nan
    tpct = tpct if np.isfinite(tpct) else np.nan
    if len(row) and row.iloc[0]["GICS Sub-Industry"]:
        sector, sub = row.iloc[0]["GICS Sector"], row.iloc[0]["GICS Sub-Industry"]
    else:
        sector, sub = INDUSTRY_OVERRIDE.get(h["ticker"], ("Unknown", "Unknown"))
        if h.get("industry"):
            sub = h["industry"]
    g = group_of(sub, sector, groups.index)
    ipct = float(gpct.get(g, np.nan))
    order = list(groups.index)
    irank = order.index(g) + 1 if g in order else None
    trend = tr.loc[t, "trend"] if t in tr.index else "insufficient"
    vs200 = tr.loc[t, "vs200"] if t in tr.index else np.nan
    price = tr.loc[t, "price"] if t in tr.index else np.nan
    reason = []
    if not mkt_on:
        act = "SELL"; reason.append("the whole market's trend has broken -- rules move to cash")
    elif trend == "insufficient":
        act = "HOLD"; reason.append("too little price history to judge -- no signal")
    elif trend == "down":
        act = "SELL"; reason.append("confirmed downtrend: below its 200-day, 50-day below 200-day")
    elif np.isfinite(ipct) and ipct <= ENTER_PCT and np.isfinite(vs200) and vs200 < 0:
        act = "SELL"; reason.append("weak industry (bottom fifth) and below its 200-day")
    elif trend == "up" and ((np.isfinite(ipct) and ipct >= 1 - ENTER_PCT)
                            or (np.isfinite(tpct) and tpct >= 1 - ENTER_PCT)):
        act = "BUY"
        what = ("strong industry (top fifth)" if np.isfinite(ipct) and ipct >= 1 - ENTER_PCT
                else "strong theme (top fifth)")
        reason.append(what + " and a confirmed uptrend -- qualifies to add"
                      + (" (also in the model)" if t in model else ""))
    else:
        act = "HOLD"
        if trend == "up":
            reason.append("uptrend, but neither its industry nor its theme is in the top fifth")
        else:
            reason.append("no confirmed trend either way")
    return {"ticker": h["ticker"], "name": h.get("name", h["ticker"]), "action": act,
            "why": "; ".join(reason), "industry": sub,
            "theme_rank_pct": None if not np.isfinite(tpct) else round(tpct, 3),
            "theme": tlead,
            "theme_rank": None if pd.isna(trank) else int(trank),
            "industry_rank_pct": None if not np.isfinite(ipct) else round(ipct, 3),
            "industry_rank": irank, "industries_total": len(order),
            "trend": trend, "vs_200d": None if not np.isfinite(vs200) else round(float(vs200), 4),
            "price": None if not np.isfinite(price) else round(float(price), 2),
            "momentum": None if t not in mom or not np.isfinite(mom.get(t, np.nan))
            else round(float(mom[t]), 4)}


def theme_txt(lead, rank, of) -> str:
    if not lead:
        return "— (moves on its own)"
    first = ", ".join(str(lead).split(", ")[:2])
    return f"{first}…" + ("" if rank is None else f" (#{rank} of {of})")


def write_markdown(plan: dict, path: Path):
    m = plan["market"]
    L = []
    L.append(f"# Daily plan — {plan['as_of']}\n")
    L.append(f"_Generated {plan['generated'][:16].replace('T', ' ')} UTC from closing prices "
             f"of {plan['as_of']}. Tested rules, not personal financial advice._\n")
    L.append(f"## Market: **{'RISK ON — invested' if m['on'] else 'RISK OFF — cash'}**\n")
    L.append(f"S&P 500 {m['vs200']:+.1%} vs its 200-day average"
             + (f", {m['ret_12m']:+.1%} over 12 months." if m.get('ret_12m') is not None else ".")
             + "\n")
    if plan.get("strategy_md"):
        L.extend(plan["strategy_md"])
    if plan.get("paper_md"):
        L.extend(plan["paper_md"])
    elif plan.get("strategy_error"):
        L.append("## ▶ THE STRATEGY — could not be calculated today\n\n```\n"
                 + "\n".join(plan["strategy_error"]) + "\n```\n")
    L.append("## 1. Your holdings\n")
    L.append("| Action | Stock | Why | Industry (rank) | Theme it trades with | Trend |")
    L.append("|---|---|---|---|---|---|")
    order = {"SELL": 0, "BUY": 1, "HOLD": 2}
    for h in sorted(plan["holdings"], key=lambda x: (order[x["action"]], x["ticker"])):
        rk = "" if not h.get("industry_rank") else f" (#{h['industry_rank']} of {h['industries_total']})"
        L.append(f"| **{h['action']}** | {h['ticker']} — {h['name']} | {h['why']} | "
                 f"{h['industry']}{rk} | {theme_txt(h.get('theme'), h.get('theme_rank'), plan.get('themes_total'))} | "
                 f"{h['trend']} |")
    if plan.get("strategy_md"):
        return _tail(plan, L, path)
    L.append("\n## 2. What you should own — £10,000 model portfolio\n")
    bt = plan.get("backtest") or {}
    th = bt.get("themes") or {}
    if th and not th.get("passes"):
        f = th.get("full", {})
        pr = th.get("prediction", {})
        L.append("> **⚠ THIS STOCK LIST FAILED ITS BACKTEST — DO NOT BUY FROM IT.** Run every "
                 f"month since {bt.get('from', '1997')}, the same rules turned £10,000 into "
                 f"£{f.get('plan', {}).get('gbp_from_10k', 0):,} against "
                 f"£{f.get('spy', {}).get('gbp_from_10k', 0):,} in the S&P 500, after HL costs. "
                 f"The score did not predict: the stocks it ranked highest went on to make "
                 f"{pr.get('top10_12m', 0):+.1%} a year, the lowest-ranked "
                 f"{pr.get('bottom10_12m', 0):+.1%}. It is shown only so you can see what it "
                 "would pick. **What the tests support today:** one low-cost S&P 500 tracker "
                 "fund, with the market switch above as the only timing rule that has held up. "
                 "See docs/BACKTEST.md and docs/FACTORS.md.\n")
    if not plan["model"]:
        L.append("**Hold cash (a money-market fund).** " + " ".join(plan["model_notes"]) + "\n")
    else:
        L.append(f"_{'Rebalance day.' if plan['rebalance_day'] else 'Between rebalances — changes only on a SELL.'}"
                 f" Next rebalance: first trading day of next month._\n")
        L.append(f"The ten best stocks right now — chosen from {plan.get('universe', 'the S&P 500')} "
                 "**and** everything you already own, on identical terms. If you already own it, "
                 "the action is HOLD.\n")
        L.append("| Action | Stock | £ | Industry | Theme it trades with | 12m momentum | Score |")
        L.append("|---|---|---|---|---|---|---|")
        for r in plan["model"]:
            act = "HOLD (you own it)" if r.get("owned") else "BUY"
            L.append(f"| **{act}** | {r['ticker']} — {r['name']} | £{r['gbp']:,.0f} | "
                     f"{r['industry']} | {theme_txt(r.get('theme'), r.get('theme_rank'), plan.get('themes_total'))} | "
                     f"{r['momentum']:+.0%} | {r['score']:.2f} |")
        L.append("\n_Score = momentum per unit of volatility: it prefers steady strength over "
                 "violent swings. Expect this portfolio to move roughly three times as much as "
                 "the S&P 500 in both directions._")
        if plan["model_notes"]:
            L.append("\n" + "\n".join(f"- {n}" for n in plan["model_notes"]))
    if plan.get("holding_ranks"):
        L.append("\n### Where your stocks rank among all candidates\n")
        L.append("| Stock | Rank | Score | In the ten? | Why |")
        L.append("|---|---|---|---|---|")
        for r in plan["holding_ranks"]:
            L.append(f"| {r['ticker']} | {('#' + str(r['rank'])) if r['rank'] else '—'} of "
                     f"{r['of']} | {'' if r['score'] is None else format(r['score'], '.2f')} | "
                     f"{'yes' if r['in_model'] else 'no'} | {r.get('why', '')} |")
    return _tail(plan, L, path)


def _tail(plan: dict, L: list, path: Path):
    if plan.get("excluded_takeovers") and not plan.get("strategy_md"):
        L.append("\n_Left out because the price is frozen (agreed takeover): "
                 + ", ".join(plan["excluded_takeovers"]) + "._")
    if plan.get("changes"):
        L.append("\n## Changes since the last run\n")
        L.extend(f"- {c}" for c in plan["changes"])
    if plan.get("themes"):
        L.append("\n## Top themes today — found from how stocks trade, not from labels\n")
        L.append("Stocks that move together form a theme, whatever their official industry. "
                 "This is how new trends such as AI show up before any label exists for them.\n")
        L.append("| # | Theme (its strongest stocks) | Official labels it spans | Stocks | "
                 "Median 12m | Score |")
        L.append("|---|---|---|---|---|---|")
        for i, t in enumerate(plan["themes"][:10], 1):
            L.append(f"| {i} | {t['leaders']} | {t['labels']} | {t['n']} | {t['mom']:+.0%} | "
                     f"{t['score']:.2f} |")
    L.append("\n## Strongest official industries today\n")
    L.append(", ".join((f"{k[7:]} (sector)" if k.startswith("SECTOR:") else k) + f" {v:+.0%}"
                       for k, v in plan["top_industries"][:10]))
    L.append("\n\n---\n_Costs (Hargreaves Lansdown, 2026): £6.95 a deal; FX on US shares 1% on the "
             "first £5,000 of each trade, then 0.75%, 0.5% and 0.25%. Tested rules, not personal "
             "financial advice. SELL on a single holding is insurance, not a forecast._")
    path.write_text("\n".join(L) + "\n")


PLAN_URL = "https://github.com/Dmax999-ops/Stock-Tracker/blob/main/docs/PLAN.md"


def md_to_html(md: str) -> str:
    """Markdown (headings, tables, bullets, bold, links) -> email-safe HTML with inline styles."""
    import html as _h
    import re as _re

    def inline(t):
        t = _h.escape(t)
        t = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = _re.sub(r"(?<![\w*])_(.+?)_(?![\w*])", r"<i>\1</i>", t)
        t = _re.sub(r"(?<![\w*])\*([^*]+?)\*(?![\w*])", r"<i>\1</i>", t)
        t = _re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2" style="color:#1a56db">\1</a>', t)
        t = _re.sub(r"(?<![\"'>])(https?://[^\s<]+)", r'<a href="\1" style="color:#1a56db">\1</a>', t)
        return t
    td = "padding:6px 10px;border:1px solid #d0d7de;font-size:14px;vertical-align:top"
    out, rows, bullets = [], [], []

    def flush_table():
        if not rows:
            return
        head, body = rows[0], rows[1:]
        h = "".join(f'<th style="{td};background:#f0f3f6;text-align:left">{inline(c)}</th>' for c in head)
        b = "".join("<tr>" + "".join(f'<td style="{td}">{inline(c)}</td>' for c in r) + "</tr>" for r in body)
        out.append(f'<table style="border-collapse:collapse;margin:6px 0 14px 0">'
                   f"<tr>{h}</tr>{b}</table>")
        rows.clear()

    def flush_bullets():
        if bullets:
            out.append('<ul style="margin:4px 0 12px 18px;padding:0">'
                       + "".join(f'<li style="font-size:14px;margin:2px 0">{inline(x)}</li>' for x in bullets)
                       + "</ul>")
            bullets.clear()
    for line in md.splitlines():
        l = line.rstrip()
        if l.startswith("|"):
            flush_bullets()
            cells = [c.strip() for c in l.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            rows.append(cells)
            continue
        flush_table()
        if l.startswith("- "):
            bullets.append(l[2:])
            continue
        flush_bullets()
        if not l.strip():
            continue
        if l.startswith("### "):
            out.append(f'<h3 style="font-size:15px;margin:14px 0 6px">{inline(l[4:])}</h3>')
        elif l.startswith("## "):
            out.append(f'<h2 style="font-size:17px;margin:20px 0 8px;border-bottom:1px solid #d0d7de;'
                       f'padding-bottom:4px">{inline(l[3:])}</h2>')
        elif l.startswith("# "):
            out.append(f'<h1 style="font-size:20px;margin:0 0 10px">{inline(l[2:])}</h1>')
        else:
            out.append(f'<p style="font-size:14px;margin:6px 0">{inline(l)}</p>')
    flush_table()
    flush_bullets()
    return ('<div style="font-family:Segoe UI,Arial,sans-serif;color:#1f2328;max-width:900px">'
            + "".join(out) + "</div>")


def _todo(plan: dict) -> list[dict]:
    """Every instruction for today, in plain words. Empty list = nothing to do."""
    res = plan.get("strategy") or {}
    out = []
    for c in plan.get("changes", []):
        if c.startswith("MARKET SWITCH"):
            off = "OFF" in c
            out.append({"kind": "SELL" if off else "BUY",
                        "title": ("SELL all strategy stocks and your S&P 500 tracker, "
                                  "and BUY the bond fund with the money") if off else
                                 "SELL the bond fund and BUY the S&P 500 tracker with the money",
                        "amount": "Everything in the strategy",
                        "why": "The S&P 500 has closed " + ("below" if off else "above")
                               + " its 200-day average 3 days running (the market switch)."})
    if res.get("is_check_day"):
        br = res.get("broker", "your broker")
        for t in res.get("this_week_detail", []):
            a, tk = t["action"], t["ticker"]
            if a == "BUY":
                out.append({"kind": "BUY", "title": f"BUY {tk}",
                            "steps": [f"Sell £{t['sell_tracker']:,.0f} of your S&P 500 tracker "
                                      f"→ you receive £{t['cash']:,.0f}" + (f" (after a £{t['deal']:.2f} deal charge)" if t['deal'] else " (no dealing charge)"),
                                      f"Buy {tk} with that £{t['cash']:,.0f} → about £{t['into_shares']:,.0f} "
                                      f"ends up in {tk} shares (" + (f"£{t['deal']:.2f} deal + " if t['deal'] else "")
                                      + f"£{t['fx']:,.2f} currency exchange)"],
                            "amount": f"Buy {tk} with £{t['cash']:,.0f}",
                            "cost": f"£{t['total_cost']:,.2f} in {br} charges",
                            "why": "3 weekly checks in a row in the top 5% of the S&P 500 "
                                   "(furthest above its 200-day average)."})
            elif a == "SELL":
                out.append({"kind": "SELL", "title": f"SELL all of your {tk}",
                            "steps": [f"Sell all your {tk} shares (worth about £{t['value']:,.0f}) "
                                      f"→ you receive about £{t['proceeds']:,.0f} (£{t['fx']:,.2f} currency exchange"
                                      + (f" + £{t['deal']:.2f} deal)" if t['deal'] else ")"),
                                      f"Buy £{t['proceeds']:,.0f} of your S&P 500 tracker "
                                      + (f"→ about £{t['into_tracker']:,.0f} invested after the £{t['deal']:.2f} deal" if t['deal'] else "(no dealing charge)")],
                            "amount": "All your shares",
                            "cost": f"£{t['total_cost']:,.2f} in {br} charges",
                            "why": "3 weekly checks in a row in the bottom half of the S&P 500: "
                                   "its trend has turned."})
    for c in plan.get("changes", []):
        if c.startswith("MARKET SWITCH") or c.startswith("Model:"):
            continue
        tk = c.split(":")[0].strip()
        h = next((x for x in plan.get("holdings", []) if x["ticker"] == tk), None)
        if h and h["action"] == "SELL":
            out.append({"kind": "SELL", "title": f"SELL all of your {tk} ({h.get('name', tk)})",
                        "amount": "All your shares",
                        "why": h["why"][:1].upper() + h["why"][1:] + "."})
    return out


def _next_check(as_of: str) -> str:
    d = pd.Timestamp(as_of)
    d = d + pd.Timedelta(days=(4 - d.weekday()) % 7 or 7)
    return d.strftime("%a %d %b")


def phone_html(plan: dict, todo: list[dict], action_only: bool = False) -> str:
    """Single-column layout that reads well on a phone: big text, short tables, no wide columns."""
    import html as _h
    esc = _h.escape
    res = plan.get("strategy") or {}
    on = res.get("market_on", plan["market"]["on"])
    C = {"BUY": "#1a7f37", "SELL": "#cf222e", "HOLD": "#57606a"}
    f = "font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;"
    B = []
    B.append(f'<div style="{f}color:#1f2328;max-width:600px;margin:0 auto;padding:8px;font-size:16px;line-height:1.45">')
    B.append(f'<div style="font-size:22px;font-weight:700;margin:4px 0 2px">'
             f'{"Action needed" if action_only else "Daily plan"}</div>'
             f'<div style="color:#57606a;margin-bottom:12px">Closing prices of {pd.Timestamp(plan["as_of"]).strftime("%a %d %b %Y")}</div>')
    pill = ("#dafbe1", "#1a7f37", "ON — invested") if on else ("#ffebe9", "#cf222e", "OFF — everything in bonds")
    B.append(f'<div style="background:{pill[0]};color:{pill[1]};border-radius:8px;padding:10px 12px;'
             f'font-weight:700;margin-bottom:14px">Market switch: {pill[2]}'
             f'<div style="font-weight:400;font-size:14px;color:#1f2328">S&amp;P 500 '
             f'{plan["market"]["vs200"]:+.1%} vs its 200-day average</div></div>')

    def h2(t):
        B.append(f'<div style="font-size:18px;font-weight:700;margin:20px 0 8px">{t}</div>')
    if todo:
        if not action_only:
            h2("▶ Do this")
        for t in todo:
            col = C.get(t["kind"], "#57606a")
            B.append(f'<div style="border-left:6px solid {col};background:#f6f8fa;border-radius:6px;'
                     f'padding:10px 12px;margin:0 0 10px">'
                     f'<div style="font-size:19px;font-weight:800;color:{col}">{esc(t["title"])}</div>'
                     + "".join(f'<div style="margin-top:4px"><b>Step {n}:</b> {esc(st)}</div>'
                               for n, st in enumerate(t.get("steps", []), 1))
                     + (f'<div style="margin-top:4px"><b>Amount:</b> {esc(t["amount"])}</div>'
                        if not t.get("steps") else "")
                     + (f'<div style="margin-top:4px"><b>Costs:</b> {esc(t["cost"])}</div>' if t.get("cost") else "")
                     + f'<div style="margin-top:2px;color:#57606a;font-size:14px"><b>Why:</b> {esc(t["why"])}</div></div>')
    elif not action_only:
        B.append(f'<div style="background:#dafbe1;border-radius:8px;padding:12px;font-size:18px;font-weight:700;color:#1a7f37">'
                 f'✅ No action today — HOLD everything'
                 f'<div style="font-size:14px;font-weight:400;color:#1f2328">Next weekly check: '
                 f'{_next_check(plan["as_of"])} close</div></div>')
    th = "text-align:left;padding:6px 4px;border-bottom:2px solid #d0d7de;font-size:13px;color:#57606a"
    td = "padding:7px 4px;border-bottom:1px solid #eaeef2;vertical-align:top"
    setup = res.get("setup")
    start = pd.Timestamp("2026-09-28")
    if setup and not action_only and pd.Timestamp(plan["as_of"]) <= start + pd.Timedelta(days=7):
        h2(f"Setting up · {esc(res.get('broker', ''))}")
        B.append(f'<div style="font-size:15px">To have exactly <b>£{setup["invested"]:,.0f}</b> invested, put in '
                 f'<b>£{setup["deposit"]:,.0f}</b> (£{setup["charges"]:,.0f} of charges). Then buy:</div>')
        B.append(f'<table style="width:100%;border-collapse:collapse;font-size:15px"><tr>'
                 f'<th style="{th}">Buy</th><th style="{th};text-align:right">Invest</th>'
                 f'<th style="{th};text-align:right">Charges</th></tr>')
        for name, amt, ch in setup["rows"]:
            B.append(f'<tr><td style="{td}"><b>{esc(name)}</b></td><td style="{td};text-align:right">£{amt:,.0f}</td>'
                     f'<td style="{td};text-align:right">£{ch:,.2f}</td></tr>')
        B.append("</table><div style='font-size:13px;color:#57606a'>Buy on the first day of the test, at "
                 "any time the market is open. Amounts are worked out from Friday's close.</div>")
    if action_only:
        B.append(f'<p style="font-size:14px;color:#57606a">Trades are for the day after this email, '
                 f'at any time the market is open.</p>')
    if res and not action_only:
        h2(f"Strategy holdings · £{res.get('pot', 0):,.0f}")
        B.append(f'<table style="width:100%;border-collapse:collapse;font-size:15px">'
                 f'<tr><th style="{th}">Stock</th><th style="{th};text-align:right">Value</th>'
                 f'<th style="{th};text-align:right">Gain</th></tr>')
        for h in res.get("holdings", []):
            warn = (f'<div style="color:#cf222e;font-size:12px">⚠ weak {h["weeks_weak"]} of 3 weeks</div>'
                    if h["weeks_weak"] else "")
            gc = "#1a7f37" if h["gain"] >= 0 else "#cf222e"
            B.append(f'<tr><td style="{td}"><b>{esc(h["ticker"])}</b>'
                     f'<div style="color:#57606a;font-size:12px">since {pd.Timestamp(h["bought"]).strftime("%d %b %y")}</div>{warn}</td>'
                     f'<td style="{td};text-align:right">£{h["value"]:,.0f}'
                     f'<div style="color:#57606a;font-size:12px">{h["weight"]:.0%} of pot</div></td>'
                     f'<td style="{td};text-align:right;color:{gc};font-weight:600">{h["gain"]:+.0%}</td></tr>')
        for lab, key in (("S&amp;P 500 tracker", "tracker_value"), ("Bond fund", "bond_value")):
            if res.get(key, 0) > 1:
                B.append(f'<tr><td style="{td}">{lab}</td><td style="{td};text-align:right">£{res[key]:,.0f}'
                         f'<div style="color:#57606a;font-size:12px">{res[key] / res["total_value"]:.0%} of pot</div></td>'
                         f'<td style="{td}"></td></tr>')
        B.append("</table>")
        if res.get("on_deck"):
            B.append('<div style="font-size:14px;margin-top:8px"><b>Next to buy</b> (if still in the top 5% '
                     'at 3 weekly checks): ' + ", ".join(f"{esc(d['ticker'])} ({d['weeks_in_top']} of 3)"
                                                          for d in res["on_deck"]) + "</div>")
        trust = [l.strip().replace("**", "") for l in plan.get("strategy_md", []) if "Trust checks" in l]
        if trust:
            B.append(f'<div style="font-size:13px;color:#57606a;margin-top:6px">{esc(trust[0])}</div>')
    if plan.get("paper_rows") and not action_only:
        pr = plan["paper_rows"]
        h2(f"🧪 Paper test · day {pr['day']}")
        for pot, rows in pr["pots"].items():
            B.append(f'<div style="font-weight:600;margin:8px 0 2px">£{pot:,.0f} started {esc(pr["start"])}</div>')
            B.append(f'<table style="width:100%;border-collapse:collapse;font-size:15px"><tr>'
                     f'<th style="{th}">Account</th><th style="{th};text-align:right">Now</th>'
                     f'<th style="{th};text-align:right">vs S&amp;P</th></tr>')
            for name, now, diff in rows:
                dc = "#57606a" if diff is None else ("#1a7f37" if diff >= 0 else "#cf222e")
                ds = "—" if diff is None else f"£{diff:+,.0f}"
                B.append(f'<tr><td style="{td}">{esc(name)}</td><td style="{td};text-align:right">£{now:,.0f}</td>'
                         f'<td style="{td};text-align:right;color:{dc};font-weight:600">{ds}</td></tr>')
            B.append("</table>")
    my = f"{res.get('broker', '')} £{res.get('pot', 0):,.0f}"
    tax = ((plan.get("paper_rows") or {}).get("tax") or {}).get(my)
    if tax and not action_only:
        h2(f"UK tax · {esc(my)}")
        B.append('<div style="font-size:13px;color:#57606a;margin-bottom:6px">Only if this is NOT an ISA '
                 '(an ISA pays no tax). First £3,000 of gains each tax year is tax-free. Tax is paid by '
                 '31 January after the tax year ends — until then the money stays invested.</div>')
        B.append(f'<table style="width:100%;border-collapse:collapse;font-size:15px"><tr>'
                 f'<th style="{th}">Tax year</th><th style="{th};text-align:right">Gains taken</th>'
                 f'<th style="{th};text-align:right">Tax 18% / 24%</th><th style="{th};text-align:right">Pay by</th></tr>')
        for y in tax["years"] or [{"tax_year": "2026/27", "net": 0, "tax_basic": 0, "tax_higher": 0, "due": "31 Jan 2028"}]:
            net = y["net"]
            B.append(f'<tr><td style="{td}">{y["tax_year"]}</td>'
                     f'<td style="{td};text-align:right">{"£" if net >= 0 else "−£"}{abs(net):,.0f}</td>'
                     f'<td style="{td};text-align:right">£{y["tax_basic"]:,.0f} / £{y["tax_higher"]:,.0f}</td>'
                     f'<td style="{td};text-align:right">{y["due"]}</td></tr>')
        B.append("</table>")
        u = tax["unrealised"]
        B.append(f'<div style="font-size:14px;margin-top:6px">Gain not yet taken: <b>{"£" if u >= 0 else "−£"}{abs(u):,.0f}</b> '
                 f'<span style="color:#57606a">— only taxed when sold.</span></div>')
    if plan.get("holdings") and not action_only:
        h2("Your own holdings")
        sells = [h for h in plan["holdings"] if h["action"] == "SELL"]
        strong = [h for h in plan["holdings"] if h["action"] == "BUY"]
        keep = [h for h in plan["holdings"] if h["action"] == "HOLD"]
        for h in sells:
            B.append(f'<div style="border-left:6px solid #cf222e;padding:6px 10px;margin:0 0 8px;background:#fff5f5">'
                     f'<b style="color:#cf222e">SELL all</b> <b>{esc(h["ticker"])}</b> '
                     f'<span style="color:#57606a">{esc(h.get("name", ""))}</span>'
                     f'<div style="font-size:13px;color:#57606a">{esc(h["why"])}</div></div>')
        if strong:
            B.append('<div style="margin:8px 0"><b style="color:#1a7f37">KEEP — strong:</b> '
                     + ", ".join(esc(h["ticker"]) for h in strong)
                     + '<div style="font-size:13px;color:#57606a">Uptrend and a strong industry. No need to do anything.</div></div>')
        if keep:
            B.append('<div style="margin:8px 0"><b>KEEP:</b> ' + ", ".join(esc(h["ticker"]) for h in keep)
                     + '<div style="font-size:13px;color:#57606a">No clear signal either way. No need to do anything.</div></div>')
    B.append(f'<a href="{PLAN_URL}" style="display:block;text-align:center;background:#0969da;color:#fff;'
             f'text-decoration:none;border-radius:8px;padding:12px;margin:20px 0 6px;font-weight:600">'
             f'Open the full plan</a>')
    B.append('<div style="font-size:12px;color:#57606a;text-align:center">Tested rules, not personal financial advice.</div>')
    B.append("</div>")
    return "".join(B)


def write_emails(plan: dict, docs: Path):
    """
    docs/EMAIL.html / EMAIL.md   -- the daily summary, laid out for a phone
    docs/ACTION.html / ACTION.md -- ONLY when there is something to do; ACTION_SUBJECT.txt
                                    holds its subject line
    None of these is committed; the workflow emails them and discards them.
    """
    for f in ("EMAIL.md", "EMAIL.html", "ACTION.md", "ACTION.html", "ACTION_SUBJECT.txt"):
        (docs / f).unlink(missing_ok=True)
    todo = _todo(plan)
    txt = [f"Daily plan - {plan['as_of']}", ""]
    txt += ([f"DO: {t['title']} | " + (" / ".join(t.get("steps", [])) or t["amount"]) + f" | {t['why']}"
             for t in todo] or ["No action today - HOLD everything."])
    txt += ["", f"Full plan: {PLAN_URL}"]
    (docs / "EMAIL.md").write_text("\n".join(txt) + "\n")
    (docs / "EMAIL.html").write_text(phone_html(plan, todo))
    if todo:
        subj = "ACTION NEEDED: " + "; ".join(t["title"] for t in todo)
        (docs / "ACTION_SUBJECT.txt").write_text(subj[:150] + "\n")
        (docs / "ACTION.md").write_text("\n".join(
            [subj, ""] + [f"- {t['title']}: " + (" / ".join(f"Step {n}: {x}" for n, x in enumerate(t.get("steps", []), 1))
                                               or t["amount"]) + (f". Costs: {t['cost']}" if t.get("cost") else "")
                          + f". Why: {t['why']}" for t in todo]
            + ["", f"Full plan: {PLAN_URL}"]) + "\n")
        (docs / "ACTION.html").write_text(phone_html(plan, todo, action_only=True))


def run(P: pd.DataFrame, univ: pd.DataFrame, holdings: list[dict], state_path: Path,
        today=None, watchlist: list[str] | None = None, universe_note: str = "") -> dict:
    P = P.dropna(how="all")
    as_of = P.index[-1]
    mom = momentum(P)
    tr = trend_table(P)
    mk = market_switch(P["SPY"])
    u, groups = industry_ranks(univ, mom)
    gpct = groups.rank(pct=True)
    # your holdings join the candidate list on the same terms
    owned_yf = {yf_symbol(h["ticker"]) for h in holdings}
    u["owned"] = u["yf"].isin(owned_yf)
    extra = []
    for h in holdings:
        t = yf_symbol(h["ticker"])
        if t in set(u["yf"]):
            continue
        sector, sub = INDUSTRY_OVERRIDE.get(h["ticker"], ("Unknown", "Unknown"))
        if h.get("industry"):
            sub = h["industry"]
        g = group_of(sub, sector, groups.index)
        extra.append({"Symbol": h["ticker"], "yf": t, "Security": h.get("name", t),
                      "GICS Sector": sector, "GICS Sub-Industry": sub, "mom": mom.get(t, np.nan),
                      "group": g, "ind_mom": groups.get(g, np.nan),
                      "ind_pct": gpct.get(g, np.nan), "owned": True})
    for t in watchlist or []:
        if t in set(u["yf"]) or t in {e["yf"] for e in extra} or t not in P.columns:
            continue
        extra.append({"Symbol": t, "yf": t, "Security": t, "GICS Sector": "Unknown",
                      "GICS Sub-Industry": "", "mom": mom.get(t, np.nan), "group": "SECTOR:Unknown",
                      "ind_mom": np.nan, "ind_pct": np.nan, "owned": False})
    if extra:
        u = pd.concat([u, pd.DataFrame(extra)], ignore_index=True)
    u["owned"] = u["owned"].fillna(False).astype(bool)
    score = stock_score(P)
    tid, T = themes(P, list(u["yf"]), score, u)
    if len(T):
        u["theme_id"] = u["yf"].map(tid)
        u["theme_pct"] = u["theme_id"].map(T.set_index("theme")["pct"])
        u["theme_leaders"] = u["theme_id"].map(T.set_index("theme")["leaders"])
        u["theme_rank"] = u["theme_id"].map(T.set_index("theme")["rank"])
        n_themes = len(T)
    else:
        u["theme_id"], u["theme_pct"], u["theme_leaders"], u["theme_rank"] = np.nan, np.nan, "", np.nan
        n_themes = 0
    prev = {}
    if state_path.exists():
        prev = json.loads(state_path.read_text())
    prev_model = prev.get("model", [])
    last_month = prev.get("as_of", "")[:7]
    rebalance = ((not prev_model) or last_month != str(as_of.date())[:7]
                 or prev.get("method") != METHOD)
    model, notes = build_model(u, tr, score, prev_model, rebalance, mk["on"])
    model_yf = [m["yf"] for m in model]
    hold = [judge_holding(h, u, groups, gpct, tr, mom, model_yf, mk["on"]) for h in holdings]
    changes = []
    old_act = {h["ticker"]: h["action"] for h in prev.get("holdings", [])}
    for h in hold:
        if old_act.get(h["ticker"]) and old_act[h["ticker"]] != h["action"]:
            changes.append(f"{h['ticker']}: {old_act[h['ticker']]} → **{h['action']}**")
    for t in set(prev_model) - set(model_yf):
        changes.append(f"Model: **SELL** {t}")
    for t in set(model_yf) - set(prev_model):
        changes.append(f"Model: **BUY** {t}")
    if prev.get("market_on") is not None and prev["market_on"] != mk["on"]:
        changes.insert(0, f"MARKET SWITCH → **{'ON' if mk['on'] else 'OFF'}**")
    ranked = u.assign(sc=u["yf"].map(score)).dropna(subset=["sc"]).drop_duplicates("yf")
    ranked = ranked.sort_values("sc", ascending=False).reset_index(drop=True)
    pos = {t: i + 1 for i, t in enumerate(ranked["yf"])}
    uj = u.join(tr, on="yf", rsuffix="_t").drop_duplicates("yf").set_index("yf")
    cut = sorted([float(score[m]) for m in model_yf if m in score.index])[0] if model_yf else np.inf

    def why_not(t):
        if t in model_yf:
            return "in the ten"
        if not mk["on"]:
            return "market switch off -- model is cash"
        if t in pinned(P):
            return "price frozen -- looks like an agreed takeover, no upside left"
        if t not in pos:
            return "not enough price history"
        r = uj.loc[t] if t in uj.index else None
        if r is None or r.get("trend") != "up":
            return "not in a confirmed uptrend"
        ip, tp = r.get("ind_pct"), r.get("theme_pct")
        ip = ip if pd.notna(ip) else 0
        tp = tp if pd.notna(tp) else 0
        if not (ip >= 1 - ENTER_PCT or tp >= 1 - ENTER_PCT):
            return "neither its industry nor its theme is in the top fifth"
        if float(score[t]) >= cut:
            return (f"qualifies, but its theme/industry places went to higher scores "
                    f"(limit {MAX_PER_THEME} per theme, {MAX_PER_SUB} per industry)")
        return "qualifies, but scores below the tenth place"

    holding_ranks = sorted([{"ticker": h["ticker"], "rank": pos.get(yf_symbol(h["ticker"])),
                             "why": why_not(yf_symbol(h["ticker"])),
                             "of": len(ranked),
                             "score": None if yf_symbol(h["ticker"]) not in pos
                             else round(float(score[yf_symbol(h["ticker"])]), 2),
                             "in_model": yf_symbol(h["ticker"]) in model_yf} for h in holdings],
                           key=lambda r: r["rank"] or 10 ** 6)
    plan = {"generated": pd.Timestamp.now("UTC").isoformat(), "as_of": str(as_of.date()),
            "holding_ranks": holding_ranks,
            "market": mk, "rebalance_day": bool(rebalance), "holdings": hold,
            "model": model, "model_notes": notes, "prev_model": prev_model,
            "changes": changes,
            "top_industries": [(k, float(v)) for k, v in groups.head(15).items()],
            "universe": universe_note or "the S&P 500",
            "excluded_takeovers": sorted(pinned(P)),
            "themes_total": n_themes,
            "themes": [] if not len(T) else
            [{k: v for k, v in row.items() if k != "members"}
             for row in T.drop(columns=["theme"]).head(15).to_dict("records")]}
    state_path.write_text(json.dumps({"as_of": plan["as_of"], "model": model_yf, "method": METHOD,
                                      "market_on": mk["on"],
                                      "holdings": [{"ticker": h["ticker"], "action": h["action"]}
                                                   for h in hold]}, indent=2))
    return plan


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdings", default="config/holdings.yml")
    ap.add_argument("--constituents", default=CONSTITUENTS)
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--watchlist", default="config/watchlist.yml")
    ap.add_argument("--prices-out", default="data/live_prices.csv")
    a = ap.parse_args()
    docs = Path(a.docs); docs.mkdir(parents=True, exist_ok=True)
    try:
        man: dict = {}
        univ = load_universe(a.constituents, man)
        holdings = load_holdings(a.holdings)
        watch = load_watchlist(a.watchlist)
        tickers = sorted(set(univ["yf"]) | {yf_symbol(h["ticker"]) for h in holdings}
                         | set(watch) | {"SPY", "VFITX"})
        print(f"downloading {len(tickers)} tickers")
        P = download(tickers)
        Path(a.prices_out).parent.mkdir(parents=True, exist_ok=True)
        P.to_csv(a.prices_out, float_format="%.4f")
        plan = run(P, univ, holdings, docs / "plan_state.json", watchlist=watch,
                   universe_note=man.get("universe", ""))
        plan["universe_detail"] = man
        bt_path = Path("data/plan_backtest.json")
        if bt_path.exists():
            try:
                plan["backtest"] = {k: v for k, v in json.loads(bt_path.read_text()).items()
                                    if k in ("from", "to", "themes")}
                plan["backtest"].get("themes", {}).pop("picks", None)
                plan["backtest"].get("themes", {}).pop("best_ten", None)
            except Exception:                                      # noqa: BLE001
                pass
        try:
            import importlib.util, os
            spec = importlib.util.spec_from_file_location("strategy", Path(__file__).parent / "strategy.py")
            strat = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(strat)
            pot = float(os.environ.get("STRATEGY_POT", "10000") or 10000)
            sp = load_constituents(a.constituents)["yf"].tolist()
            res = strat.live(P, sp, pot, P["VFITX"] if "VFITX" in P else None)
            rows = strat.log_day(res)
            plan["strategy"] = res
            plan["strategy_md"] = strat.markdown(res, rows)
            try:
                spec2 = importlib.util.spec_from_file_location("paper_test", Path(__file__).parent / "paper_test.py")
                pt = importlib.util.module_from_spec(spec2)
                spec2.loader.exec_module(pt)
                plan["paper_md"] = pt.update(P, sp, P["VFITX"] if "VFITX" in P else None)
                plan["paper_rows"] = pt.LAST
            except Exception:                                      # noqa: BLE001
                import traceback
                plan["paper_md"] = ["## 🧪 Paper test — could not be updated today\n", "```",
                                    *traceback.format_exc().splitlines()[-5:], "```\n"]
        except Exception as e:                                     # noqa: BLE001
            import traceback
            plan["strategy_error"] = traceback.format_exc().splitlines()[-6:]
            print("strategy failed:", e, file=sys.stderr)
        (docs / "plan.json").write_text(json.dumps(plan, indent=2, default=str))
        write_markdown(plan, docs / "PLAN.md")
        write_emails(plan, docs)
        print((docs / "PLAN.md").read_text())
        return 0
    except Exception as exc:                                       # noqa: BLE001
        import traceback
        (docs / "plan_error.json").write_text(json.dumps(
            {"generated": pd.Timestamp.now("UTC").isoformat(),
             "error": f"{type(exc).__name__}: {exc}",
             "traceback": traceback.format_exc().splitlines()[-25:]}, indent=2))
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
