# Trading signal tool — handover

*Paste this into a new chat. It carries everything established so far.*

---

## What I'm building

A signal tool for my own equity holdings. Tells me **buy / hold / reduce / stay out**
per stock. Horizon is **days to months** — not day trading, not decades. Runs
automatically and free on GitHub Actions, publishes to GitHub Pages, alerts me on
my phone only when something changes.

I'm a data engineer (medallion architecture, Power BI, Azure SQL). UK-based, so UK
costs apply — 0.5% stamp duty on purchases, ~£11.95 flat commission, ~8bps spread.

**My GitHub:** `github.com/Dmax999-ops`. Repo is created and public. The previous
session couldn't use the GitHub connector because it started before I added it —
a fresh chat should pick it up.

---

## Holdings (the TEST set — never used for fitting)

**UK (LSE/AIM):** FRES.L (Fresnillo), IQE.L, ZOO.L (ZOO Digital), LIT.L (Litigation
Capital Management), DEBS.L (Debenhams Group)

**US:** AAPL, AMZN, GOOG, MSFT, NVDA, TSLA, CELH, VST, TEM (Tempus AI), SPCX (SpaceX)

TEM and SPCX are recent listings — too short for long-horizon signals.

---

## What the evidence actually says

### The validated model

A **six-state classifier** on trend × heat, trained on **498 S&P stocks,
461,930 stock-days, daily bars, 2013–2018**:

| State | 1-month fwd | t vs universe | Verdict |
|---|---|---|---|
| **CAPITULATION** (3+/5 indicators in bottom decile) | +1.57% | **+4.35** | **Tradeable — buy** |
| FALLING (cold + downtrend) | +1.19% | +1.81 | Noise |
| COOLING (cold + uptrend) | +0.94% | +0.64 | Noise |
| STEADY | +0.82% | −0.58 | Noise |
| STRONG (hot + uptrend) | +0.80% | −0.86 | Noise |
| **TOPPING** (hot + broken trend) | +0.41% | **−3.82** | **Tradeable — reduce** |

**Only two of six states carry weight, and they're the extremes.** Threshold
(|t| ≥ 2.5) was fixed before results were seen.

### Three things that cost me time, so don't repeat them

1. **An earlier version tested on just my 6 large holdings said STRONG was the
   second-best state. At 498 stocks it's t = −0.86 — nothing.** The apparent
   momentum effect was an artifact of testing on six of the biggest winners of the
   decade. **Breadth is not optional.**

2. **"Cold" is not a buy signal.** General weakness (COOLING) has no edge. Only
   *capitulation* — the rare 3-of-5 extreme, ~10% of the time — carries signal.
   Most cold readings are stocks that keep falling.

3. **Capitulation is territory, not timing.** 4× lift on finding major troughs, but
   median signal fires **7 weeks early** with a median **11.7% further fall**, and
   54% of signals saw another 10%+ decline. **Ladder in over three tranches** —
   that converts being early from an error into the mechanism.

### Economics

| | |
|---|---|
| Long/short CAPITULATION − TOPPING, monthly rebalance | 14.8% gross → **1.3% after costs** |
| **Long-only CAPITULATION vs universe** | **+8.6%/yr gross** |

Costs eat thirteen of fourteen points on the long/short version. **The long-only,
low-turnover configuration is the only one where the edge survives friction.**

### THE BIG UNRESOLVED PROBLEM

**The training universe is S&P 500 membership as of 2018.** Every company that
capitulated and then went bankrupt or was delisted is *missing from the data*.

Buy-the-dip looks excellent when the dips that never recovered have been deleted.
**The +8.6% is an optimistic ceiling, biased in exactly the direction that costs
money.** Fixing this is the single highest-value next step — historical constituent
lists, or a survivorship-free source (Norgate ~$500/yr, CRSP).

---

## What was tested and rejected — don't rebuild these

| Rejected | Result |
|---|---|
| RSI 30/70, Bollinger reversion | −15% to −18%/yr across 6 stocks. Worst of everything. |
| MACD, Donchian/Turtle, Chandelier, Ichimoku, Faber 10-month, Parabolic SAR, golden cross | 12 published rules × 6 stocks = 72 tests, **2 wins, neither replicated** |
| Breakouts, volume-confirmed breakouts, squeeze breakouts, trendlines, support/resistance | 0–2 wins in 48 tests. Volume confirmation made it *worse*. |
| Connors RSI(2), short-horizon dip buying | −20% to −26%/yr, and **worse the faster they trade** |
| Selling on peak signals | **Peaks are not detectable**: 1.9× lift (drops *below* random with more confirmation), 20 weeks early, **83% of further upside forgone** |
| All 10 standard re-entry signals after a drawdown (RSI, MACD, Bollinger reclaim, MA reclaim, capitulation volume, volatility spike, RSI divergence, 2 up weeks) | Tested on MSFT's five drawdowns — **every one lost to simply holding**. Best re-entry still fires 9% above the low. |
| Parameter tuning | Rank correlation between train and test performance: **−0.065**. Tuning predicts nothing. 15% of apparent edge survived out of sample. |

**The one finding that held across everything: less trading beat more trading,
monotonically, in every single test.**

### Other established facts

- **Return concentration:** removing the best 20 weeks of ~1,400 turns AMZN from
  +6,671% to −27%. 1.4% of weeks carry 100% of returns. This is why sitting out is
  so expensive.
- **Trend overlays are regime-dependent.** They add 8–16%/yr when a stock falls
  *persistently*, and destroy value on V-shaped recoveries. MSFT's 2020 drop ran
  peak-to-trough in 5 weeks — a 40-week average physically cannot react.
- **Of my holdings, only FRES passes overlay eligibility** (+1.2%/yr, but p = 0.52
  — weak evidence). It spends 56% of rolling 3-year windows going nowhere; AAPL
  spends 6%.
- **Breakout entry with 1 ATR stop + 3 ATR trail**: 180 trades, 33% win rate,
  avg win +76.4%, avg loss −11.5%, **profit factor 3.24**, expectancy +17.3%/trade,
  median hold 12 weeks. Good at trade level; unproven at portfolio level, and stop
  fills are assumed optimistic.

---

## Data constraints (hard-won)

**Alpha Vantage** (connected, free tier):
- 25 calls/day, **1 request/second** burst limit — no parallel calls
- `TIME_SERIES_DAILY_ADJUSTED` and `outputsize=full` on daily are **premium**
- `TIME_SERIES_WEEKLY_ADJUSTED` and `MONTHLY_ADJUSTED` are **free and include
  dividends** — this is the workaround for adjusted UK prices
- **IQE.LON and ZOO.LON return "Invalid API call" on adjusted endpoints** — AIM
  small caps have no adjusted coverage. LIT and DEBS almost certainly the same.
  **These four need yfinance.**
- UK tickers use `.LON` on Alpha Vantage, `.L` on yfinance. Prices in GBX (pence).
- `DIVIDENDS` endpoint returns empty for UK tickers but works for US.

**Sandbox networking:**
- All market data hosts blocked (Yahoo, Stooq, Alpha Vantage direct, FRED, CDN)
- **`raw.githubusercontent.com` works** — this is the data pipe
- `api.github.com` returns 403 (scoped to pre-configured repos only)
- Large MCP results get written to disk rather than inline — parse them in Python,
  they cost nothing in context

**Training data currently used:**
`https://raw.githubusercontent.com/plotly/datasets/master/all_stocks_5yr.csv`
— 505 S&P stocks, daily OHLCV, 2013-02-08 to 2018-02-07, 619,040 rows. Free,
survivorship-biased.

---

## Repo status

A complete repo was built and delivered as a zip but **not yet pushed**. Contains:

```
.github/workflows/fetch-universe.yml     weekly: pull history, retrain, commit
.github/workflows/daily-signals.yml      weekdays: classify, write signals.json
quant/states.py                          the six-state classifier
quant/indicators.py, data.py, metrics.py, evaluate.py
scripts/fetch_universe.py                universe pull + survivorship reporting
scripts/train_states.py                  retrain, t-statistics, auto-retire signals
scripts/daily_signals.py                 per-holding call + prediction log
scripts/alert.py                         ntfy push, only on actionable change
config/holdings.yml                      my 14 tickers
config/universe.yml                      training universe
docs/index.html                          dashboard
```

Validated before packaging: all six states classify correctly, **no-lookahead check
100% clean**.

Setup needs: Actions → Workflow permissions → Read and write; Pages → main/docs.

---

## Design principles baked in — please keep them

- **Expanding/rolling normalisation only.** Never full-sample — that leaks the
  future into every historical score.
- **Execution lag.** Signal on close of t, trade at open of t+1, overnight gap
  accrues at the old weight.
- **Costs always.** Half-spread each way, commission, UK stamp duty on buys.
- **Non-overlapping windows for significance.** 963 weekly bars contain 18
  independent annual observations, not 911.
- **Holdings are the test set.** Signal selection happens on the universe only.
- **The prediction log is committed to git** so it's tamper-evident. In 12 months
  it's the only genuinely out-of-sample record that will exist.

---

## Where to pick up

1. **Push the repo** (built, zipped, validated — just needs `git push`)
2. **Fix survivorship** — this matters more than any signal work. Historical
   constituent lists into `config/universe.yml`, or price a survivorship-free feed.
3. **Retest the capitulation signal on delisted-inclusive data.** If +8.6% survives,
   there's a real strategy. If it collapses, better to know now.
4. Verify the first workflow run and read `data/manifest.json` for the survivorship
   exposure number.
5. Wire yfinance for the four AIM holdings Alpha Vantage can't serve.

**Open question I keep coming back to:** the capitulation signal is the only thing
with real statistical support. Everything else tested as noise. I want to know
whether that survives honest data — and if it does, whether laddering into it
across a wider universe produces something worth running.
