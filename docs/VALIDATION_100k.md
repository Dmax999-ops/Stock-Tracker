# Can we trust it? — validation of the live strategy

_Generated 2026-09-25 23:21 UTC. £100,000 pot, HL costs, 1997-02-03 → 2026-09-25. Strategy: S&P 500 stocks furthest above their 200-day average, commit rules, market switch._

**Baseline (as tested before):** £8,725,919 vs £1,624,027 in the S&P 500 (+16.3%/yr vs +9.9%/yr; worst fall -32%).

## 1–3. Trading delay, check day, double costs

| Test | £ | Yearly | vs S&P, first half | vs S&P, second half | Worst fall | Still beats S&P in both halves? |
|---|---|---|---|---|---|---|
| Trade 1 day after the signal | £12,071,420 | +17.6% | +10.6%/yr | +4.9%/yr | -30% | **yes** |
| Trade 2 days after the signal | £12,287,325 | +17.6% | +10.8%/yr | +4.9%/yr | -30% | **yes** |
| Check every Monday, trade next day | £7,515,778 | +15.7% | +9.0%/yr | +2.8%/yr | -36% | **yes** |
| Check every Tuesday, trade next day | £8,636,687 | +16.2% | +9.1%/yr | +3.9%/yr | -31% | **yes** |
| Check every Wednesday, trade next day | £15,494,314 | +18.6% | +11.0%/yr | +6.2%/yr | -29% | **yes** |
| Check every Thursday, trade next day | £12,236,446 | +17.6% | +9.1%/yr | +6.2%/yr | -31% | **yes** |
| Check every Friday, trade next day | £9,097,342 | +16.4% | +9.3%/yr | +4.2%/yr | -33% | **yes** |
| Check DAILY (15-day confirmation), trade next day | £13,678,962 | +18.1% | +12.0%/yr | +4.2%/yr | -33% | **yes** |
| Double costs, trade next day | £5,938,085 | +14.8% | +8.0%/yr | +2.0%/yr | -34% | **yes** |

## 4. Any 5 years

Of 95 five-year periods (starting every quarter since the start), the strategy beat the S&P 500 in **65** (68%). Its worst 5-year period vs the S&P 500: -10.7% a year.

## 5. 2,000 simulated 10-year futures

Built from reshuffled calendar years of its own history (paired with the S&P 500's return in the same year). Chance it **trails** the S&P 500 over 10 years: **15%**. Chance it **loses money** over 10 years: 0%. Typical outcome for £100,000: £419,993 vs £245,428 in the S&P 500.

## 6. Does re-selecting the strategy each year work? ("keep learning")

Each January from 2006, a selector looked back 8 years at all 21 candidate strategies, picked the most consistent winner, and held it for one year it had not seen.

| | £100,000 became | Yearly | Years ahead of S&P |
|---|---|---|---|
| **Selector (re-picks every year)** | £1,266,239 | +12.8% | 10 of 21 |
| Fixed: trend_200 throughout | £2,296,054 | +16.1% | 12 of 21 |
| S&P 500 | £891,406 | +11.0% | |

| Year | Selector picked | Its return | S&P 500 |
|---|---|---|---|
| 2006 | mom_12_1 | -2.1% | +14.7% |
| 2007 | mom_12_1 | +5.3% | +7.3% |
| 2008 | rise_weak_peers | +8.3% | -40.4% |
| 2009 | rise_weak_peers | +46.5% | +32.4% |
| 2010 | rise_weak_peers | +14.8% | +14.0% |
| 2011 | rise_weak_peers | -10.2% | +2.7% |
| 2012 | rise_weak_peers | +21.1% | +14.5% |
| 2013 | rise_weak_peers | +53.9% | +32.9% |
| 2014 | rise_weak_peers | +10.4% | +15.2% |
| 2015 | rise_weak_peers | -8.1% | +0.6% |
| 2016 | reversal_1m | +5.4% | +11.4% |
| 2017 | rise_weak_peers | +24.9% | +21.5% |
| 2018 | rise_weak_peers | +3.5% | -6.2% |
| 2019 | mom_3 | +15.1% | +33.2% |
| 2020 | mom_3 | -1.2% | +17.8% |
| 2021 | mom_12_1 | +29.6% | +29.3% |
| 2022 | mom_12_1 | -19.2% | -18.0% |
| 2023 | mom_12_1 | +22.6% | +26.2% |
| 2024 | mom_12_1 | +53.4% | +27.8% |
| 2025 | mom_12_1 | +4.9% | +16.1% |
| 2026 | mom_12_1 | +24.1% | +12.1% |

## Verdict

**5 of 5 trust checks passed.**

- ✅ survives a trading delay
- ✅ not tied to one check day
- ✅ survives double costs
- ✅ beats S&P in 60%+ of 5-year periods
- ✅ under 25% chance of trailing over 10 years
- ✅ re-selecting each year beat the S&P on unseen years (+12.8% vs +11.0%/yr)

Passing these makes it a candidate for real money; the final check is the live forward record in data/strategy_log.jsonl, which no backtest can fake.
