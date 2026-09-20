# Trading Strategy — evidence-backed rules

*Built 20 September 2026. Every rule below survived testing on your own holdings;
everything that failed was removed. Confidence levels are stated honestly — some
of this is well-evidenced, some is marginal, and it says which.*

---

## The one-page version

| Holding | Overlay? | Call today | Watch level |
|---|---|---|---|
| **FRES.LON** | **YES** | **REDUCE** | Trend re-establishes above **3,193** |
| AAPL | No | Hold | Add zone below ~252 (−25%) |
| AMZN | No | Hold | Add zone below ~206 (−19%) |
| MSFT | No | Hold | Add zone below ~389 (−21%) |
| NVDA | No | Hold | Add zone below ~173 (−22%) |
| TSLA | No | Hold | Add zone below ~361 (−1%) |

**Five of six holdings should not be timed at all.** That is itself a decision —
it saves you trading costs, tax events and attention.

---

## Rule 1 — Decide eligibility before anything else

A timing overlay only goes on a stock where it has *historically* beaten holding
that stock. Measured as the annualised log excess of a 10/40-week trend rule
against buy-and-hold, over the full available history:

| | Overlay excess | Verdict |
|---|---|---|
| FRES.LON | **+1.2%** | Overlay on |
| AMZN | −3.2% | Leave alone |
| AAPL | −4.8% | Leave alone |
| MSFT | −7.0% | Leave alone |
| NVDA | −8.5% | Leave alone |
| TSLA | −19.7% | Leave alone |

**Why FRES is different:** it spends 56% of its rolling 3-year windows returning
under +20%. The overlay is insurance, and Fresnillo is the only holding where the
house burns down often enough to justify the premium. AAPL spends 6% of its life
going nowhere — you'd be paying premiums for two decades to collect once.

**Confidence: moderate for the ranking, weak for FRES specifically.** The +1.2%
has a bootstrap p-value of 0.52 — indistinguishable from luck on its own. What
carries the weight is that the *ordering* matches the mechanism (insurance pays
where declines are frequent and persistent) across all six names and six
different rules.

**Re-run this test annually.** Eligibility is not permanent.

---

## Rule 2 — Size by volatility, not by conviction

Target weight = 25% ÷ (stock's 26-week realised volatility), capped at 25%.

Current volatilities: FRES 45%, TSLA 46%, MSFT 43%, AMZN 38%, NVDA 36%, AAPL 24%.

A 45%-volatility miner and a 24%-volatility Apple are not the same position at
the same weight. This requires no forecast and is the single most reliable
improvement available.

**Confidence: high.** Mechanical, well-evidenced, no fitting involved.

---

## Rule 3 — For eligible names only: trend decides exposure

- Price above the 40-week moving average → hold full position
- Price sustains below it → reduce
- Check **monthly**, not weekly. Turnover was the one thing that hurt in every
  single test.

**FRES today: 3,035 against a 40-week MA of 3,193 — trend is broken, 5% below.**

**Confidence: moderate.** Slow trend rules were the only family that didn't lose
badly, and the golden cross did it in 22 trades over 18 years.

---

## Rule 4 — Adding: wait for confluence, then ladder in

Five indicators, each ranked against its own history (expanding, no hindsight):
RSI, 3-month momentum, ATR percentage, price z-score, distance from 52-week high.

**When 3 or more sit in their top decile simultaneously, you are 4× more likely
to be near a major trough than at a random moment.** That is the strongest signal
found in this entire project.

But it is *territory*, not timing: median 7 weeks early, median 11.7% further
fall, and 54% of signals saw another 10%+ decline. So:

- **Buy in three tranches, not one.** Being early becomes averaging down rather
  than a mistake.
- Applies to *all* holdings, including the ones with no overlay.

**Nothing is firing today — 0/5 on every holding.** The add-zone prices in the
table above are roughly where they would start to.

**Confidence: good for the 4× lift, poor for the timing.** Don't treat a
confluence signal as "the bottom."

---

## Rule 5 — New positions: breakout entry, tight stop

For anything you're buying that you don't already own:

- **Entry:** close above the most recent confirmed swing high
- **Initial stop:** 1 ATR below entry
- **Trailing stop:** 3 ATR from the running high
- **Risk 1% of portfolio per position**, sized from the stop distance

Tested across 180 trades on your holdings:

| | |
|---|---|
| Win rate | 33% |
| Average win | +76.4% |
| Average loss | −11.5% |
| **Profit factor** | **3.24** |
| Expectancy | +17.3% per trade |
| Median hold | 12 weeks |

You will be wrong twice as often as you're right. That is the design, not a flaw.

**Confidence: good at trade level, unproven at portfolio level.** The backtest
assumes you fill at your stop price — in a gap down you won't, so real losses
will exceed −11.5%. Treat the win/loss ratio as optimistic.

---

## What was tested and rejected

So you don't revisit these:

| Rejected | Result |
|---|---|
| RSI 30/70, Bollinger reversion | −15% to −18%/yr. Worst of everything tested. |
| MACD, Donchian, Chandelier, Ichimoku, Faber, Parabolic SAR | All negative across 6 stocks |
| Breakouts, volume-confirmed breakouts, squeeze breakouts, trendlines | 0–2 wins in 48 tests |
| Connors RSI(2), short-horizon dip-buying | −20% to −26%/yr, worse the faster they trade |
| Selling on peak signals | Peaks are undetectable: 1.9× lift, 20 weeks early, 83% of further upside forgone |
| Every standard re-entry signal after a drawdown | All 10 lost to holding on MSFT's five drawdowns |

**The consistent finding across everything: less trading beat more trading, monotonically.**

---

## Honest limits

- **Six stocks, all large winners.** Rules that reduce exposure are structurally
  disadvantaged on a sample with no disasters in it.
- **Weekly bars.** Daily history is paywalled on the current data source.
- **IQE, ZOO, LIT, DEBS have no adjusted data** on Alpha Vantage — the four AIM
  holdings can't be modelled at all yet, and they are the names most likely to
  resemble FRES's profile.
- **SPCX and TEM are too recently listed** to carry any long-horizon signal.
- Nothing here is financial advice, and the strongest single result in the whole
  project is that doing less beat doing more.

---

## Review cadence

- **Monthly:** check the trend line on eligible names; check confluence on all.
- **Annually:** re-run the eligibility test. A name can move between buckets.
- **When credits renew:** run this across a 500+ stock universe including
  delisted companies. Everything above is built on six survivors, which is the
  single biggest weakness in it.
