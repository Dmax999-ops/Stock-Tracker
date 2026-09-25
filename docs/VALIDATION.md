# Can we trust it? — validation of the live strategy

_Generated 2026-09-25 23:24 UTC. £10,000 pot, HL costs, 1997-02-03 → 2026-09-25. Strategy: S&P 500 stocks furthest above their 200-day average, commit rules, market switch._

**Baseline (as tested before):** £427,879 vs £162,403 in the S&P 500 (+13.5%/yr vs +9.9%/yr; worst fall -33%).

## 1–3. Trading delay, check day, double costs

| Test | £ | Yearly | vs S&P, first half | vs S&P, second half | Worst fall | Still beats S&P in both halves? |
|---|---|---|---|---|---|---|
| Trade 1 day after the signal | £421,442 | +13.5% | +6.4%/yr | +1.0%/yr | -35% | no |
| Trade 2 days after the signal | £655,001 | +15.2% | +7.2%/yr | +3.6%/yr | -31% | **yes** |
| Check every Monday, trade next day | £437,492 | +13.6% | +6.7%/yr | +1.0%/yr | -37% | no |
| Check every Tuesday, trade next day | £384,558 | +13.1% | +5.7%/yr | +1.0%/yr | -34% | no |
| Check every Wednesday, trade next day | £772,100 | +15.8% | +7.6%/yr | +4.1%/yr | -34% | **yes** |
| Check every Thursday, trade next day | £440,231 | +13.6% | +3.9%/yr | +3.6%/yr | -39% | **yes** |
| Check every Friday, trade next day | £359,444 | +12.8% | +4.4%/yr | +2.0%/yr | -35% | **yes** |
| Check DAILY (15-day confirmation), trade next day | £709,579 | +15.5% | +9.6%/yr | +1.4%/yr | -35% | **yes** |
| Double costs, trade next day | £59,852 | +6.2% | -1.1%/yr | -6.0%/yr | -47% | no |

## 4. Any 5 years

Of 95 five-year periods (starting every quarter since the start), the strategy beat the S&P 500 in **52** (55%). Its worst 5-year period vs the S&P 500: -13.9% a year.

## 5. 2,000 simulated 10-year futures

Built from reshuffled calendar years of its own history (paired with the S&P 500's return in the same year). Chance it **trails** the S&P 500 over 10 years: **36%**. Chance it **loses money** over 10 years: 1%. Typical outcome for £10,000: £30,194 vs £24,543 in the S&P 500.

## 6. Does re-selecting the strategy each year work? ("keep learning")

Each January from 2006, a selector looked back 8 years at all 21 candidate strategies, picked the most consistent winner, and held it for one year it had not seen.

| | £10,000 became | Yearly | Years ahead of S&P |
|---|---|---|---|
| **Selector (re-picks every year)** | £76,704 | +10.2% | 8 of 21 |
| Fixed: trend_200 throughout | £104,873 | +11.8% | 9 of 21 |
| S&P 500 | £89,141 | +11.0% | |

| Year | Selector picked | Its return | S&P 500 |
|---|---|---|---|
| 2006 | mom_12_1 | -11.3% | +14.7% |
| 2007 | mom_12_1 | -0.4% | +7.3% |
| 2008 | trend_200 | +3.6% | -40.4% |
| 2009 | mom_3 | +25.9% | +32.4% |
| 2010 | rise_weak_peers | +4.4% | +14.0% |
| 2011 | rise_weak_peers | -8.6% | +2.7% |
| 2012 | rise_weak_peers | +18.2% | +14.5% |
| 2013 | rise_weak_peers | +50.7% | +32.9% |
| 2014 | rise_weak_peers | +6.8% | +15.2% |
| 2015 | rise_weak_peers | -10.6% | +0.6% |
| 2016 | rise_weak_peers | +27.3% | +11.4% |
| 2017 | rise_weak_peers | +23.7% | +21.5% |
| 2018 | mom_12_1 | +1.3% | -6.2% |
| 2019 | mom_12_1 | +14.8% | +33.2% |
| 2020 | mom_3 | -7.8% | +17.8% |
| 2021 | mom_12_1 | +28.9% | +29.3% |
| 2022 | mom_12_1 | -21.1% | -18.0% |
| 2023 | mom_12_1 | +20.9% | +26.2% |
| 2024 | mom_12_1 | +53.1% | +27.8% |
| 2025 | mom_12_1 | +4.4% | +16.1% |
| 2026 | mom_12_1 | +23.7% | +12.1% |

## Verdict

**0 of 5 trust checks passed.**

- ❌ survives a trading delay
- ❌ not tied to one check day
- ❌ survives double costs
- ❌ beats S&P in 60%+ of 5-year periods
- ❌ under 25% chance of trailing over 10 years
- ❌ re-selecting each year beat the S&P on unseen years (+10.2% vs +11.0%/yr)

Passing these makes it a candidate for real money; the final check is the live forward record in data/strategy_log.jsonl, which no backtest can fake.
