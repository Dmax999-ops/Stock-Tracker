# All the evidence at once — a stock picker that learns, tested only on unseen years

_Generated 2026-11-01 12:32 UTC. 789 stocks ever in the S&P 500, 2003-01-02 → 2026-10-30, halves split at 2014-12-01. Every prediction for year Y uses weights fitted only on outcomes known before Y. 24 patterns combined._

## Verdict: **DOES NOT PASS**

Combining every pattern still did not reliably pick next year's winners.

## Did it predict?

Rank correlation with the next month: -0.001 (t = -0.1; first half t = -0.9, second half t = +0.8). Stocks it ranked in the top tenth went on to make **+13.8%** over the next 12 months; the bottom tenth +14.6%; the average stock +13.7%.

## £10,000 under the commit rules, after HL costs

| | £ | Yearly | Worst fall | First half vs S&P | Second half vs S&P |
|---|---|---|---|---|---|
| Ensemble picker | **£35,543** | +5.5% | -79% | -9.3%/yr | -2.2%/yr |
| S&P 500 | £127,694 | +11.3% | -55% | | |

14.9 trades a year, typical hold 188 days. Best trades: CIEN +2746% (2009-05), MTG +138% (2008-03), HSY +128% (2017-08), NTAP +146% (2016-03), OKE +168% (2016-01)

## What the model learned makes a winner (weights, latest year vs first year)

Positive = more of this, more likely a winner. The model re-learns every year; a pattern it keeps the same sign on year after year is a real tendency, one that flips is noise.

| Pattern | First year | Latest year | Same sign in … |
|---|---|---|---|
| Book value / market value | +0.000 | -0.075 | 15 of 24 years |
| How far above its 12-month low | -0.004 | +0.070 | 21 of 24 years |
| Daily swings, last 6 months | -0.104 | -0.069 | 24 of 24 years |
| Moves with the market (beta) | +0.043 | +0.049 | 24 of 24 years |
| % above the 200-day average | +0.087 | -0.043 | 16 of 24 years |
| Return over the past year (skipping last month) | -0.023 | -0.038 | 20 of 24 years |
| Free cash flow / market value | +0.000 | +0.034 | 14 of 24 years |
| Made a new 12-month high in the last 20 days | +0.003 | +0.029 | 24 of 24 years |
| Net profit / assets | +0.000 | -0.024 | 9 of 24 years |
| Gross profit / assets | +0.000 | +0.023 | 14 of 24 years |
| Sales growth, last reported year | +0.000 | +0.022 | 12 of 24 years |
| Earnings / market value | +0.000 | +0.021 | 14 of 24 years |
| rise_weak_peers | -0.004 | +0.019 | 23 of 24 years |
| Balance-sheet growth, last year | +0.000 | -0.017 | 11 of 24 years |
| Return over the past month | +0.003 | -0.016 | 23 of 24 years |
| Trading volume, last month vs last year | -0.025 | +0.010 | 15 of 24 years |
| Company size (market value) | +0.000 | +0.009 | 13 of 24 years |
| Move vs S&P on last results (within 3 months) | +0.000 | +0.006 | 17 of 24 years |
| RSI (14-day) | -0.003 | -0.004 | 17 of 24 years |
| 50-day average above the 200-day | -0.036 | +0.003 | 21 of 24 years |
| Biggest single-day jump last month | -0.003 | +0.003 | 21 of 24 years |
| Return over the past 3 months | +0.016 | -0.003 | 21 of 24 years |
| How close to its 12-month high | -0.043 | -0.003 | 24 of 24 years |
| Profit NOT backed by cash (accruals) | +0.000 | -0.001 | 15 of 24 years |
