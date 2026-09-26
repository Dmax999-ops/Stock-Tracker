# Stock-Tracker

A tested, rules-based stock strategy with a daily plan, run entirely on GitHub Actions.

**Start here:** [docs/PLAN.md](docs/PLAN.md), updated every weeknight around 22:30 UK time.

---

## The strategy

S&P 500 stocks trading furthest above their own 200-day average, held under commit rules, with a market switch.

| Rule | What it does |
|---|---|
| **BUY** | A stock ranks in the top 5% of the S&P 500 on 3 weekly checks in a row (Friday closes), and one of the 10 slots is free. Each slot is one tenth of the pot. |
| **HOLD** | Stays until the evidence clearly turns, however much it wobbles. |
| **SELL** | It has fallen into the bottom half on 3 weekly checks in a row. |
| **Market switch** | S&P 500 below its 200-day average for 3 closes → everything into a bond fund. Back into an S&P 500 tracker after 3 closes above. |
| **Idle money** | Waits in an S&P 500 tracker. |

## Why these rules

| Test | Page |
|---|---|
| Year-by-year backtest of the old ten-stock plan (it failed) | [docs/BACKTEST.md](docs/BACKTEST.md) |
| 24 ways of ranking stocks, with and without the market switch | [docs/FACTORS.md](docs/FACTORS.md) |
| What the biggest winners looked like beforehand | [docs/WINNERS.md](docs/WINNERS.md) |
| Stress tests: settings, universes, bad data | [docs/ROBUSTNESS_100k.md](docs/ROBUSTNESS_100k.md) |
| Trust checks: trading delay, check day, costs, 5-year periods, simulated futures | [docs/VALIDATION_100k.md](docs/VALIDATION_100k.md) |

At a £100k pot the strategy passes every check. At £10k with Hargreaves Lansdown charges it does not: costs are too large a share of £1,000 positions.

## Paper test

Six pretend accounts (£10k and £100k × Hargreaves Lansdown, Trading 212, Interactive Brokers) from 28 September 2026 to 28 December 2026, logged daily in [data/paper_test.csv](data/paper_test.csv). The live record of the strategy is in [data/strategy_log.jsonl](data/strategy_log.jsonl).

## What runs, and when

| Workflow | When | What |
|---|---|---|
| Daily plan | Weeknights 22:15 UTC | The plan, the strategy, the paper test, your holdings, emails |
| ETF rotation | Weeknights 22:00 UTC | Sector and bond prices used by the tests |
| Fetch delisted | Every 4 hours | Collects price history of companies that failed (free Alpha Vantage allowance) |
| Backtest, factor screen, winners study, ensemble, robustness, validation | Monthly, on the 1st | Re-tests everything on the latest data |
| Century | Monthly, on the 5th | 100-year industry and market history |

## Settings

| Where | What |
|---|---|
| `config/holdings.yml` | The stocks you own (the BUY / HOLD / SELL section of the plan) |
| `config/watchlist.yml` | Extra stocks to consider |
| Repository variable `STRATEGY_POT` | Pot size for the strategy and the monthly validation (default 10000) |
| Repository secrets `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_TO` | Turn on the daily and ACTION NEEDED emails |

_Tested rules, not personal financial advice._
