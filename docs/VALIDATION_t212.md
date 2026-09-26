# Can we trust it? — validation of the live strategy

_Generated 2026-09-26 21:04 UTC. £10,000 pot, Trading 212 costs, 1997-02-03 → 2026-09-25. Strategy: S&P 500 stocks furthest above their 200-day average, commit rules, market switch._

**Baseline (as tested before):** £1,623,606 vs £162,403 in the S&P 500 (+18.7%/yr vs +9.9%/yr; worst fall -31%).

## 1–3. Trading delay, check day, double costs

| Test | £ | Yearly | vs S&P, first half | vs S&P, second half | Worst fall | Still beats S&P in both halves? |
|---|---|---|---|---|---|---|
| Trade 1 day after the signal | £1,586,865 | +18.6% | +12.1%/yr | +5.7%/yr | -30% | **yes** |
| Trade 2 days after the signal | £2,116,449 | +19.8% | +13.0%/yr | +7.1%/yr | -30% | **yes** |
| Check every Monday, trade next day | £1,170,056 | +17.4% | +11.2%/yr | +4.1%/yr | -33% | **yes** |
| Check every Tuesday, trade next day | £1,144,711 | +17.3% | +10.1%/yr | +5.1%/yr | -30% | **yes** |
| Check every Wednesday, trade next day | £2,330,114 | +20.2% | +12.4%/yr | +8.1%/yr | -30% | **yes** |
| Check every Thursday, trade next day | £1,464,563 | +18.3% | +10.6%/yr | +6.1%/yr | -31% | **yes** |
| Check every Friday, trade next day | £1,392,300 | +18.1% | +10.5%/yr | +6.5%/yr | -32% | **yes** |
| Check DAILY (15-day confirmation), trade next day | £1,701,770 | +18.9% | +13.3%/yr | +4.6%/yr | -33% | **yes** |
| Double costs, trade next day | £1,179,517 | +17.5% | +11.5%/yr | +3.8%/yr | -32% | **yes** |

## 4. Any 5 years

Of 95 five-year periods (starting every quarter since the start), the strategy beat the S&P 500 in **70** (74%). Its worst 5-year period vs the S&P 500: -10.2% a year.

## 5. 2,000 simulated 10-year futures

Built from reshuffled calendar years of its own history (paired with the S&P 500's return in the same year). Chance it **trails** the S&P 500 over 10 years: **12%**. Chance it **loses money** over 10 years: 0%. Typical outcome for £10,000: £46,295 vs £24,543 in the S&P 500.

## 6. Does re-selecting the strategy each year work? ("keep learning")

Each January from 2006, a selector looked back 8 years at all 21 candidate strategies, picked the most consistent winner, and held it for one year it had not seen.

| | £10,000 became | Yearly | Years ahead of S&P |
|---|---|---|---|
| **Selector (re-picks every year)** | £157,983 | +14.0% | 11 of 21 |
| Fixed: trend_200 throughout | £264,550 | +16.9% | 12 of 21 |
| S&P 500 | £89,141 | +11.0% | |

| Year | Selector picked | Its return | S&P 500 |
|---|---|---|---|
| 2006 | mom_12_1 | -3.5% | +14.7% |
| 2007 | mom_6_1 | +4.8% | +7.3% |
| 2008 | rise_weak_peers | +8.8% | -40.4% |
| 2009 | rise_weak_peers | +47.3% | +32.4% |
| 2010 | rise_weak_peers | +16.5% | +14.0% |
| 2011 | rise_weak_peers | -9.6% | +2.7% |
| 2012 | rise_weak_peers | +21.8% | +14.5% |
| 2013 | rise_weak_peers | +54.6% | +32.9% |
| 2014 | rise_weak_peers | +10.7% | +15.2% |
| 2015 | rise_weak_peers | -8.6% | +0.6% |
| 2016 | reversal_1m | +7.7% | +11.4% |
| 2017 | rise_weak_peers | +25.6% | +21.5% |
| 2018 | mom_3 | +8.0% | -6.2% |
| 2019 | mom_3 | +17.8% | +33.2% |
| 2020 | mom_3 | +0.1% | +17.8% |
| 2021 | mom_12_1 | +29.8% | +29.3% |
| 2022 | mom_12_1 | -19.1% | -18.0% |
| 2023 | mom_12_1 | +26.3% | +26.2% |
| 2024 | mom_12_1 | +67.5% | +27.8% |
| 2025 | mom_12_1 | +2.4% | +16.1% |
| 2026 | mom_12_1 | +23.9% | +12.1% |

## Verdict

**5 of 5 trust checks passed.**

- ✅ survives a trading delay
- ✅ not tied to one check day
- ✅ survives double costs
- ✅ beats S&P in 60%+ of 5-year periods
- ✅ under 25% chance of trailing over 10 years
- ✅ re-selecting each year beat the S&P on unseen years (+14.0% vs +11.0%/yr)

Passing these makes it a candidate for real money; the final check is the live forward record in data/strategy_log.jsonl, which no backtest can fake.
