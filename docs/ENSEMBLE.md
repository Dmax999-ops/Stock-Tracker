# All the evidence at once — a stock picker that learns, tested only on unseen years

_Generated 2026-10-01 12:12 UTC. 652 stocks ever in the S&P 500, 2003-01-02 → 2026-09-30, halves split at 2014-11-03. Every prediction for year Y uses weights fitted only on outcomes known before Y. 24 patterns combined._

## Verdict: **DOES NOT PASS**

Combining every pattern still did not reliably pick next year's winners.

## Did it predict?

Rank correlation with the next month: -0.005 (t = -0.6; first half t = -1.3, second half t = +0.4). Stocks it ranked in the top tenth went on to make **+14.2%** over the next 12 months; the bottom tenth +15.5%; the average stock +14.0%.

## £10,000 under the commit rules, after HL costs

| | £ | Yearly | Worst fall | First half vs S&P | Second half vs S&P |
|---|---|---|---|---|---|
| Ensemble picker | **£41,116** | +6.1% | -73% | -8.7%/yr | -1.6%/yr |
| S&P 500 | £130,335 | +11.4% | -55% | | |

15.5 trades a year, typical hold 152 days. Best trades: CIEN +3022% (2009-05), HRB +122% (2017-09), HSY +119% (2017-08), CIEN +138% (2005-05), MTG +118% (2008-01)

## What the model learned makes a winner (weights, latest year vs first year)

Positive = more of this, more likely a winner. The model re-learns every year; a pattern it keeps the same sign on year after year is a real tendency, one that flips is noise.

| Pattern | First year | Latest year | Same sign in … |
|---|---|---|---|
| How far above its 12-month low | +0.013 | +0.081 | 23 of 24 years |
| Book value / market value | +0.000 | -0.077 | 15 of 24 years |
| Return over the past year (skipping last month) | -0.034 | -0.050 | 24 of 24 years |
| Daily swings, last 6 months | -0.101 | -0.048 | 24 of 24 years |
| % above the 200-day average | +0.077 | -0.046 | 16 of 24 years |
| Free cash flow / market value | +0.000 | +0.035 | 14 of 24 years |
| Made a new 12-month high in the last 20 days | +0.006 | +0.032 | 24 of 24 years |
| Moves with the market (beta) | +0.047 | +0.023 | 13 of 24 years |
| Sales growth, last reported year | +0.000 | +0.022 | 12 of 24 years |
| Net profit / assets | +0.000 | -0.022 | 9 of 24 years |
| Gross profit / assets | +0.000 | +0.021 | 14 of 24 years |
| rise_weak_peers | -0.006 | +0.020 | 22 of 24 years |
| Earnings / market value | +0.000 | +0.019 | 13 of 24 years |
| Balance-sheet growth, last year | +0.000 | -0.019 | 11 of 24 years |
| Return over the past month | +0.004 | -0.017 | 22 of 24 years |
| Company size (market value) | +0.000 | +0.013 | 12 of 24 years |
| Trading volume, last month vs last year | -0.024 | +0.009 | 16 of 24 years |
| Move vs S&P on last results (within 3 months) | +0.000 | +0.007 | 18 of 24 years |
| RSI (14-day) | -0.004 | -0.007 | 13 of 24 years |
| Return over the past 3 months | +0.017 | -0.006 | 23 of 24 years |
| Profit NOT backed by cash (accruals) | +0.000 | +0.003 | 12 of 24 years |
| 50-day average above the 200-day | -0.036 | -0.002 | 16 of 24 years |
| Biggest single-day jump last month | -0.007 | +0.002 | 22 of 24 years |
| How close to its 12-month high | -0.044 | -0.001 | 23 of 24 years |
