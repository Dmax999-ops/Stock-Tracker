# What predicts which stocks do best? — every score tested side by side

_Generated 2026-09-24 18:59 UTC. 641 stocks ever in the S&P 500 (19 from the delisted archive), 1997-02-03 → 2026-09-24. Only stocks in the S&P 500 on each date. 'random' is the control: a score that does no better than it predicts nothing._

**Bar:** t ≥ 3 overall and t ≥ 2 in BOTH halves, and the commit-rules portfolio beats the S&P 500 by 1%/yr after HL costs in both halves.

## 1. Did the score predict the next month / year?

| Score (years tested; halves split at) | Rank corr. (1m) | t (all) | t first half | t second half | Top 10% next 12m | Bottom 10% | Average stock | Verdict |
|---|---|---|---|---|---|---|---|---|
| reversal_1m (1997–2026; 2011) | +0.020 | +2.2 | +2.1 | +1.0 | +14.8% | +15.0% | +13.2% | no |
| quality_value (2010–2026; 2018) | +0.010 | +1.2 | +1.0 | +0.8 | +17.0% | +15.6% | +15.2% | no |
| gross_profitability (2010–2026; 2018) | +0.011 | +1.1 | +1.1 | +0.6 | +13.8% | +12.4% | +15.3% | no |
| quality_momentum (2010–2026; 2018) | +0.013 | +1.1 | +1.4 | +0.2 | +16.2% | +14.9% | +15.3% | no |
| fcf_yield (2010–2026; 2018) | +0.008 | +0.8 | +0.3 | +0.7 | +16.7% | +14.6% | +14.6% | no |
| earnings_yield (2010–2026; 2018) | +0.007 | +0.7 | -0.6 | +1.4 | +14.2% | +17.8% | +14.5% | no |
| earnings_reaction (2004–2026; 2015) | +0.003 | +0.7 | +0.9 | +0.1 | +14.2% | +14.2% | +13.1% | no |
| roa (2010–2026; 2018) | +0.007 | +0.7 | +0.4 | +0.5 | +16.3% | +15.9% | +14.5% | no |
| mom_12_1_riskadj (1997–2026; 2011) | +0.006 | +0.6 | +0.9 | -0.1 | +12.0% | +13.1% | +13.2% | no |
| low_asset_growth (2010–2026; 2018) | +0.004 | +0.5 | +0.6 | +0.1 | +15.7% | +13.7% | +14.6% | no |
| low_accruals (2010–2026; 2018) | +0.003 | +0.5 | +1.0 | -0.6 | +18.7% | +15.4% | +14.5% | no |
| mom_12_1 (1997–2026; 2011) | +0.004 | +0.4 | +0.6 | -0.1 | +13.3% | +17.3% | +13.2% | no |
| value_momentum (2010–2026; 2018) | +0.004 | +0.4 | +0.0 | +0.3 | +13.0% | +16.2% | +14.5% | no |
| random (1997–2026; 2011) | -0.001 | -0.2 | -0.5 | +0.4 | +13.3% | +13.5% | +13.2% | no |
| low_vol (1997–2026; 2011) | -0.008 | -0.6 | -0.1 | -0.7 | +10.8% | +20.3% | +13.2% | no |
| book_to_market (2010–2026; 2018) | -0.007 | -0.6 | -0.9 | -0.1 | +15.4% | +17.0% | +14.4% | no |
| mom_6_1 (1997–2026; 2011) | -0.006 | -0.6 | -0.7 | -0.2 | +13.8% | +16.0% | +13.2% | no |
| smooth_mom (1997–2026; 2011) | -0.006 | -0.6 | -0.4 | -0.6 | +11.8% | +15.8% | +13.2% | no |
| near_52w_high (1997–2026; 2011) | -0.011 | -0.9 | -0.6 | -0.8 | +11.2% | +17.2% | +13.2% | no |
| trend_200 (1997–2026; 2011) | -0.012 | -1.1 | -1.1 | -0.5 | +13.7% | +16.2% | +13.2% | no |
| mom_3 (1997–2026; 2011) | -0.018 | -1.8 | -1.6 | -1.0 | +15.0% | +15.8% | +13.2% | no |

## 2. £10,000 run by commit rules — no calendar, trade only on strong evidence

Money waits in an S&P 500 tracker. A stock is bought only when it has been in the top 5% on the score for 3 weekly checks in a row (up to 10 stocks), and sold only when it has fallen into the bottom half on 3 weekly checks in a row.

| Score | £ after HL costs | £ with no costs | S&P 500 £ | Yearly (costs) | S&P yearly | Worst fall | S&P worst | Trades / year | Typical hold | First half vs S&P | Second half vs S&P | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trend_200 (1997–2026; 2011) | £262,940 | £1,098,782 | £162,403 | +11.7% | +9.9% | -73% | -55% | 19.4 | 235 days | -4.3%/yr | +9.0%/yr | no |
| roa (2010–2026; 2018) | £171,719 | £192,424 | £92,861 | +18.7% | +14.4% | -30% | -29% | 1.8 | 1268 days | +0.1%/yr | +8.7%/yr | no |
| low_accruals (2010–2026; 2018) | £161,845 | £197,182 | £92,861 | +18.3% | +14.4% | -34% | -29% | 4.1 | 739 days | +6.7%/yr | +1.1%/yr | no |
| random (1997–2026; 2011) | £143,580 | £181,636 | £162,403 | +9.4% | +9.9% | -54% | -55% | 4.3 | 86 days | -0.3%/yr | -0.6%/yr | no |
| mom_3 (1997–2026; 2011) | £136,824 | £1,658,686 | £162,403 | +9.2% | +9.9% | -68% | -55% | 39.0 | 115 days | -3.0%/yr | +2.0%/yr | no |
| low_vol (1997–2026; 2011) | £112,052 | £154,499 | £162,403 | +8.5% | +9.9% | -38% | -55% | 1.3 | 2036 days | +3.3%/yr | -6.2%/yr | no |
| low_asset_growth (2010–2026; 2018) | £97,890 | £127,211 | £92,861 | +14.8% | +14.4% | -38% | -29% | 7.0 | 724 days | -0.6%/yr | +1.3%/yr | no |
| mom_12_1_riskadj (1997–2026; 2011) | £89,206 | £196,312 | £162,403 | +7.7% | +9.9% | -61% | -55% | 14.5 | 326 days | -0.3%/yr | -4.2%/yr | no |
| gross_profitability (2010–2026; 2018) | £76,234 | £78,689 | £92,861 | +13.1% | +14.4% | -29% | -29% | 0.7 | 775 days | +3.5%/yr | -5.8%/yr | no |
| quality_value (2010–2026; 2018) | £74,745 | £77,653 | £92,861 | +12.9% | +14.4% | -28% | -29% | 0.9 | 2181 days | +2.1%/yr | -5.1%/yr | no |
| near_52w_high (1997–2026; 2011) | £71,284 | £157,613 | £162,403 | +6.9% | +9.9% | -42% | -55% | 13.3 | 228 days | -0.8%/yr | -5.2%/yr | no |
| mom_12_1 (1997–2026; 2011) | £58,279 | £232,651 | £162,403 | +6.1% | +9.9% | -79% | -55% | 13.9 | 318 days | -8.0%/yr | +1.2%/yr | no |
| book_to_market (2010–2026; 2018) | £56,248 | £52,805 | £92,861 | +11.0% | +14.4% | -47% | -29% | 1.0 | 1739 days | -1.2%/yr | -5.5%/yr | no |
| fcf_yield (2010–2026; 2018) | £48,492 | £70,751 | £92,861 | +10.0% | +14.4% | -33% | -29% | 2.4 | 529 days | -5.4%/yr | -3.3%/yr | no |
| smooth_mom (1997–2026; 2011) | £48,429 | £139,191 | £162,403 | +5.5% | +9.9% | -68% | -55% | 14.3 | 297 days | -3.9%/yr | -4.8%/yr | no |
| earnings_yield (2010–2026; 2018) | £47,350 | £55,369 | £92,861 | +9.8% | +14.4% | -50% | -29% | 5.1 | 579 days | -4.5%/yr | -4.5%/yr | no |
| quality_momentum (2010–2026; 2018) | £45,383 | £61,683 | £92,861 | +9.6% | +14.4% | -38% | -29% | 2.7 | 750 days | +0.2%/yr | -9.6%/yr | no |
| value_momentum (2010–2026; 2018) | £41,741 | £36,464 | £92,861 | +9.0% | +14.4% | -55% | -29% | 9.1 | 452 days | -8.7%/yr | -1.9%/yr | no |
| mom_6_1 (1997–2026; 2011) | £216 | £1,282,036 | £162,403 | -12.1% | +9.9% | -99% | -55% | 22.0 | 166 days | -15.4%/yr | -28.6%/yr | no |
| earnings_reaction (2004–2026; 2015) | £215 | £173,741 | £102,019 | -16.1% | +11.2% | -99% | -54% | 23.7 | 115 days | -21.3%/yr | -33.4%/yr | no |
| reversal_1m (1997–2026; 2011) | £33 | £1,144,477 | £162,403 | -17.5% | +9.9% | -100% | -55% | 18.4 | 57 days | -29.0%/yr | -25.3%/yr | no |

## 3a. Sanity check of the 'no costs' column

Several scores that predict nothing show millions of pounds with no costs. That is not believable, so here is where each no-cost result came from. A one-day price move of more than 50% on a large company is usually bad data from Yahoo.

| Score | £ no costs | Best 3 trades | Share of profit from them | Holdings with a >50% one-day move |
|---|---|---|---|---|
| mom_3 | £1,658,686 | WDC +537% (2025-08), STX +525% (2025-07), MU +352% (2025-11) | 56% | 8: UIS 1999-07-21, EP 2001-02-12, EP 2003-06-23, EP 2006-02-17, EP 2007-02-09, HBAN 2008-10-02 |
| mom_6_1 | £1,282,036 | MRNA +262% (2026-04), MU +338% (2025-11), WDC +279% (2025-10) | 44% | 10: EP 2000-12-20, EP 2003-06-02, EP 2004-01-05, EP 2006-05-31, THC 2008-04-07, EP 2009-05-15 |
| reversal_1m | £1,144,477 | SMCI +46% (2025-09), CRWD +39% (2024-08), CZR +29% (2025-10) | 9% | 31: MCIC 1997-12-09, EP 2000-05-11, AMCC 2001-03-06, EP 2001-09-10, CNP 2002-05-28, WMB 2002-06-04 |
| trend_200 | £1,098,782 | STX +455% (2025-08), MU +375% (2025-11), WDC +196% (2025-11) | 52% | 7: EP 2000-11-14, EP 2003-09-03, EP 2006-09-08, EP 2008-02-22, EP 2009-04-09, EP 2010-02-02 |
| mom_12_1 | £232,651 | MU +187% (2026-02), NVDA +394% (2023-12), WDC +151% (2025-12) | 41% | 8: UIS 1998-02-13, AAPL 1999-12-10, THC 2001-02-27, CF 2008-09-11, THC 2008-10-09, EP 2009-12-03 |
| low_accruals | £197,182 | AMZN +3710% (2010-03), FANG +170% (2021-06), DVN +178% (2021-04) | 44% | 3: NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24 |
| mom_12_1_riskadj | £196,312 | WDC +151% (2025-12), NVDA +314% (2016-05), NVDA +189% (2024-01) | 33% | 5: UIS 1998-03-09, AAPL 1999-12-03, TMUS 2011-04-11, NFLX 2011-02-18, NKTR 2018-04-03 |
| roa | £192,424 | NVDA +3542% (2018-03), MA +2358% (2010-03), PM +709% (2010-03) | 88% | 0 |
| random | £181,636 | PAYC +68% (2026-03), MS +24% (2024-10), TSLA +24% (2025-05) | 86% | 0 |
| earnings_reaction | £173,741 | DELL +166% (2026-04), STX +127% (2026-02), TER +92% (2025-11) | 31% | 1: HBAN 2008-08-04 |
| near_52w_high | £157,613 | GE +140% (2023-03), NVDA +289% (2015-10), TRGP +107% (2023-08) | 41% | 2: CSR 1998-08-20, PARA 2022-05-11 |
| low_vol | £154,499 | NEE +2177% (1997-02), JNJ +587% (2008-01), KO +687% (2005-09) | 42% | 1: PARA 2023-10-24 |
| smooth_mom | £139,191 | STX +143% (2026-03), GE +184% (2023-07), NVDA +309% (2016-08) | 40% | 2: AAPL 2000-03-29, PARA 2022-12-29 |
| low_asset_growth | £127,211 | HWM +764% (2021-03), GE +479% (2022-03), WDC +62% (2026-02) | 70% | 2: DVN 2019-03-14, PARA 2023-09-08 |
| gross_profitability | £78,689 | SHW +1643% (2010-03), UNH +1404% (2010-03), FAST +1127% (2010-07) | 67% | 1: NFLX 2011-01-04 |
| quality_value | £77,653 | GWW +1448% (2010-03), UNH +1404% (2010-03), WMT +732% (2010-04) | 59% | 0 |
| fcf_yield | £70,751 | APA +147% (2025-03), UAL +157% (2024-03), WBD +144% (2022-12) | 33% | 1: LUMN 2021-03-02 |
| quality_momentum | £61,683 | UNH +999% (2011-11), FAST +1079% (2010-06), SHW +1122% (2010-06) | 68% | 1: NFLX 2011-04-07 |
| earnings_yield | £55,369 | PHM +571% (2014-03), UNM +283% (2021-03), GS +367% (2010-03) | 54% | 1: FMC 2025-02-24 |
| book_to_market | £52,805 | HIG +551% (2010-03), RF +496% (2010-03), CNX +272% (2015-10) | 45% | 2: PCG 2010-03-15, GNW 2010-03-15 |
| value_momentum | £36,464 | NRG +222% (2022-05), SYF +85% (2024-04), VRSN +144% (2016-03) | 38% | 0 |

## 3. Where the money came from — was it a rule, or a few lucky stocks?

For every score whose commit portfolio ended ahead of the S&P 500 (after costs): its five best trades, and how much of all its trading profit came from just three stocks. If three trades are most of the profit, the 'rule' is really a few lucky holdings, and it would not repeat. A price jump of more than 100% in one day is flagged as a possible data error.

**trend_200** — trading profit £275,008; 48% of it from the best three trades. Possible data errors: EP 2000-11-14, EP 2003-09-03, EP 2006-08-10, EP 2009-04-09, EP 2010-02-02, TMUS 2011-03-21

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| STX | 2025-08-26 | still held | +455% | £57,912 |
| MU | 2025-11-19 | still held | +375% | £47,797 |
| WDC | 2025-11-19 | still held | +196% | £25,025 |
| NVDA | 2023-05-17 | 2025-03-19 | +290% | £18,316 |
| PLTR | 2024-11-19 | 2026-02-10 | +122% | £13,332 |

**roa** — trading profit £155,364; 89% of it from the best three trades. No suspect price jumps.

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| NVDA | 2018-03-15 | still held | +3542% | £107,691 |
| MA | 2010-03-15 | still held | +2358% | £23,783 |
| PM | 2010-03-15 | still held | +709% | £7,152 |
| MCO | 2010-03-15 | 2017-08-09 | +399% | £4,024 |
| CHRW | 2010-03-15 | still held | +295% | £2,975 |

**low_accruals** — trading profit £140,046; 46% of it from the best three trades. Possible data errors: NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| AMZN | 2010-03-15 | still held | +3710% | £37,431 |
| FANG | 2021-06-17 | still held | +170% | £14,272 |
| MMM | 2024-03-01 | 2025-02-24 | +94% | £12,543 |
| LYV | 2023-02-09 | still held | +113% | £11,031 |
| SLB | 2020-11-24 | 2023-02-09 | +153% | £10,434 |

**low_asset_growth** — trading profit £88,020; 68% of it from the best three trades. Possible data errors: DVN 2019-03-14, PARA 2023-09-08

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| HWM | 2021-03-16 | 2026-03-02 | +764% | £31,402 |
| GE | 2022-03-04 | 2026-02-13 | +479% | £22,692 |
| CTVA | 2020-03-11 | still held | +242% | £5,563 |
| WDC | 2026-02-13 | still held | +62% | £5,546 |
| DD | 2020-03-11 | still held | +222% | £5,101 |


**Result:** No score cleared the bar. None told you reliably, in advance, which S&P 500 stocks would do best.

---
_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those in the delisted archive are included. That flatters every score equally, so it does not change which score ranks best — but it flatters the £ figures._
