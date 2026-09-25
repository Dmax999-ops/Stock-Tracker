# All the evidence at once — a stock picker that learns, tested only on unseen years

_Generated 2026-09-25 21:28 UTC. 644 stocks ever in the S&P 500, 2003-01-02 → 2026-09-25, halves split at 2014-11-03. Every prediction for year Y uses weights fitted only on outcomes known before Y. 24 patterns combined._

## Verdict: **DOES NOT PASS**

Combining every pattern still did not reliably pick next year's winners.

## Did it predict?

Rank correlation with the next month: -0.005 (t = -0.6; first half t = -1.2, second half t = +0.4). Stocks it ranked in the top tenth went on to make **+14.4%** over the next 12 months; the bottom tenth +15.8%; the average stock +14.1%.

## £10,000 under the commit rules, after HL costs

| | £ | Yearly | Worst fall | First half vs S&P | Second half vs S&P |
|---|---|---|---|---|---|
| Ensemble picker | **£1,766** | -7.0% | -99% | -31.4%/yr | -2.7%/yr |
| S&P 500 | £130,335 | +11.4% | -55% | | |

12.4 trades a year, typical hold 123 days. Best trades: AMZN +122% (2006-12), MTG +140% (2008-01), XOM +44% (2003-03), TROW +40% (2005-04), VIAV +36% (2005-11)

## What the model learned makes a winner (weights, latest year vs first year)

Positive = more of this, more likely a winner. The model re-learns every year; a pattern it keeps the same sign on year after year is a real tendency, one that flips is noise.

| Pattern | First year | Latest year | Same sign in … |
|---|---|---|---|
| How far above its 12-month low | +0.018 | +0.080 | 23 of 24 years |
| Book value / market value | +0.000 | -0.077 | 15 of 24 years |
| Return over the past year (skipping last month) | -0.038 | -0.051 | 24 of 24 years |
| Daily swings, last 6 months | -0.102 | -0.051 | 24 of 24 years |
| % above the 200-day average | +0.075 | -0.046 | 16 of 24 years |
| Free cash flow / market value | +0.000 | +0.034 | 14 of 24 years |
| Made a new 12-month high in the last 20 days | +0.007 | +0.031 | 24 of 24 years |
| Moves with the market (beta) | +0.048 | +0.027 | 13 of 24 years |
| Sales growth, last reported year | +0.000 | +0.022 | 12 of 24 years |
| Net profit / assets | +0.000 | -0.022 | 9 of 24 years |
| Gross profit / assets | +0.000 | +0.022 | 14 of 24 years |
| rise_weak_peers | -0.006 | +0.021 | 22 of 24 years |
| Earnings / market value | +0.000 | +0.019 | 13 of 24 years |
| Balance-sheet growth, last year | +0.000 | -0.018 | 11 of 24 years |
| Return over the past month | +0.002 | -0.017 | 23 of 24 years |
| Company size (market value) | +0.000 | +0.013 | 13 of 24 years |
| Trading volume, last month vs last year | -0.023 | +0.010 | 15 of 24 years |
| RSI (14-day) | -0.004 | -0.008 | 12 of 24 years |
| Move vs S&P on last results (within 3 months) | +0.000 | +0.007 | 18 of 24 years |
| Return over the past 3 months | +0.016 | -0.006 | 22 of 24 years |
| How close to its 12-month high | -0.042 | +0.003 | 21 of 24 years |
| Profit NOT backed by cash (accruals) | +0.000 | +0.002 | 12 of 24 years |
| Biggest single-day jump last month | -0.007 | +0.001 | 22 of 24 years |
| 50-day average above the 200-day | -0.037 | -0.001 | 16 of 24 years |
