# Can we trust it? — validation of the live strategy

_Generated 2026-11-01 16:33 UTC. £10,000 pot, Trading 212 costs, 1997-02-03 → 2026-10-30. Strategy: S&P 500 stocks furthest above their 200-day average, commit rules, market switch._

**Baseline (as tested before):** £971,101 vs £163,354 in the S&P 500 (+16.6%/yr vs +9.8%/yr; worst fall -31%).

## 1–3. Trading delay, check day, double costs

| Test | £ | Yearly | vs S&P, first half | vs S&P, second half | Worst fall | Still beats S&P in both halves? |
|---|---|---|---|---|---|---|
| Trade 1 day after the signal | £1,262,062 | +17.7% | +10.2%/yr | +5.7%/yr | -30% | **yes** |
| Trade 2 days after the signal | £1,458,561 | +18.2% | +11.5%/yr | +5.5%/yr | -31% | **yes** |
| Check every Monday, trade next day | £968,393 | +16.6% | +10.6%/yr | +3.2%/yr | -34% | **yes** |
| Check every Tuesday, trade next day | £750,037 | +15.6% | +9.3%/yr | +2.5%/yr | -34% | **yes** |
| Check every Wednesday, trade next day | £1,272,418 | +17.7% | +9.4%/yr | +6.2%/yr | -32% | **yes** |
| Check every Thursday, trade next day | £950,120 | +16.6% | +8.0%/yr | +5.2%/yr | -31% | **yes** |
| Check every Friday, trade next day | £762,694 | +15.7% | +9.0%/yr | +3.2%/yr | -32% | **yes** |
| Check DAILY (15-day confirmation), trade next day | £951,423 | +16.6% | +11.2%/yr | +2.2%/yr | -34% | **yes** |
| Double costs, trade next day | £852,743 | +16.1% | +9.6%/yr | +3.1%/yr | -30% | **yes** |

## 4. Any 5 years

Of 96 five-year periods (starting every quarter since the start), the strategy beat the S&P 500 in **74** (77%). Its worst 5-year period vs the S&P 500: -9.2% a year.

## 5. 2,000 simulated 10-year futures

Built from reshuffled calendar years of its own history (paired with the S&P 500's return in the same year). Chance it **trails** the S&P 500 over 10 years: **15%**. Chance it **loses money** over 10 years: 0%. Typical outcome for £10,000: £43,493 vs £24,543 in the S&P 500.

## 6. Does re-selecting the strategy each year work? ("keep learning")

Each January from 2006, a selector looked back 8 years at all 21 candidate strategies, picked the most consistent winner, and held it for one year it had not seen.

| | £10,000 became | Yearly | Years ahead of S&P |
|---|---|---|---|
| **Selector (re-picks every year)** | £95,272 | +11.3% | 10 of 21 |
| Fixed: trend_200 throughout | £211,394 | +15.6% | 11 of 21 |
| S&P 500 | £89,663 | +11.0% | |

| Year | Selector picked | Its return | S&P 500 |
|---|---|---|---|
| 2006 | mom_12_1 | +0.7% | +14.7% |
| 2007 | mom_12_1 | +7.9% | +7.3% |
| 2008 | mom_12_1 | +7.0% | -40.4% |
| 2009 | mom_12_1 | +4.4% | +32.4% |
| 2010 | reversal_1m | +18.4% | +14.0% |
| 2011 | reversal_1m | -8.6% | +2.7% |
| 2012 | reversal_1m | +24.3% | +14.5% |
| 2013 | reversal_1m | +52.0% | +32.9% |
| 2014 | reversal_1m | -6.2% | +15.2% |
| 2015 | rise_weak_peers | -9.5% | +0.6% |
| 2016 | reversal_1m | +3.0% | +11.4% |
| 2017 | rise_weak_peers | +26.4% | +21.5% |
| 2018 | mom_12_1 | -0.1% | -6.2% |
| 2019 | mom_12_1 | +17.1% | +33.2% |
| 2020 | mom_12_1 | +29.6% | +17.8% |
| 2021 | mom_12_1 | +30.5% | +29.3% |
| 2022 | mom_12_1 | -18.4% | -18.0% |
| 2023 | mom_12_1 | +17.8% | +26.2% |
| 2024 | mom_12_1 | +67.5% | +27.8% |
| 2025 | mom_12_1 | +2.4% | +16.1% |
| 2026 | mom_12_1 | +6.6% | +12.8% |

## Verdict

**5 of 5 trust checks passed.**

- ✅ survives a trading delay
- ✅ not tied to one check day
- ✅ survives double costs
- ✅ beats S&P in 60%+ of 5-year periods
- ✅ under 25% chance of trailing over 10 years
- ✅ re-selecting each year beat the S&P on unseen years (+11.3% vs +11.0%/yr)

Passing these makes it a candidate for real money; the final check is the live forward record in data/strategy_log.jsonl, which no backtest can fake.
