# What predicts which stocks do best? — every score tested side by side

_Generated 2026-10-01 08:17 UTC. 652 stocks ever in the S&P 500 (31 from the delisted archive), 1997-02-03 → 2026-09-30. Only stocks in the S&P 500 on each date. 'random' is the control: a score that does no better than it predicts nothing._

**Bar:** t ≥ 3 overall and t ≥ 2 in BOTH halves, and the commit-rules portfolio beats the S&P 500 by 1%/yr after HL costs in both halves.

## 1. Did the score predict the next month / year?

| Score (years tested; halves split at) | Rank corr. (1m) | t (all) | t first half | t second half | Top 10% next 12m | Bottom 10% | Average stock | Verdict |
|---|---|---|---|---|---|---|---|---|
| reversal_1m (1997–2026; 2011) | +0.020 | +2.3 | +2.2 | +1.1 | +14.8% | +14.9% | +13.2% | no |
| quality_value (2010–2026; 2018) | +0.010 | +1.2 | +1.0 | +0.8 | +17.0% | +15.6% | +15.2% | no |
| gross_profitability (2010–2026; 2018) | +0.011 | +1.1 | +1.1 | +0.6 | +13.8% | +12.4% | +15.3% | no |
| quality_momentum (2010–2026; 2018) | +0.013 | +1.1 | +1.4 | +0.2 | +16.2% | +14.9% | +15.3% | no |
| rise_weak_peers (1997–2026; 2011) | +0.008 | +1.0 | -0.3 | +1.9 | +17.5% | +12.8% | +13.2% | no |
| fcf_yield (2010–2026; 2018) | +0.008 | +0.8 | +0.3 | +0.7 | +16.7% | +14.6% | +14.6% | no |
| earnings_yield (2010–2026; 2018) | +0.007 | +0.7 | -0.6 | +1.4 | +14.2% | +17.8% | +14.5% | no |
| earnings_reaction (2004–2026; 2015) | +0.003 | +0.7 | +0.9 | +0.1 | +14.2% | +14.2% | +13.1% | no |
| roa (2010–2026; 2018) | +0.007 | +0.7 | +0.4 | +0.5 | +16.3% | +15.9% | +14.5% | no |
| mom_12_1_riskadj (1997–2026; 2011) | +0.006 | +0.6 | +0.9 | -0.1 | +12.0% | +13.1% | +13.2% | no |
| rise_weak_sector_LABELS (1997–2026; 2011) | +0.004 | +0.6 | -0.4 | +1.3 | +19.0% | +14.3% | +14.6% | no |
| low_asset_growth (2010–2026; 2018) | +0.004 | +0.5 | +0.6 | +0.1 | +15.7% | +13.7% | +14.6% | no |
| low_accruals (2010–2026; 2018) | +0.003 | +0.5 | +1.0 | -0.6 | +18.7% | +15.4% | +14.5% | no |
| mom_12_1 (1997–2026; 2011) | +0.004 | +0.4 | +0.6 | -0.1 | +13.3% | +17.3% | +13.2% | no |
| value_momentum (2010–2026; 2018) | +0.004 | +0.4 | +0.0 | +0.3 | +13.0% | +16.2% | +14.5% | no |
| random (1997–2026; 2011) | +0.001 | +0.2 | +0.6 | -0.5 | +12.8% | +12.8% | +13.2% | no |
| rise3m_weak_peers (1997–2026; 2011) | -0.002 | -0.2 | -0.7 | +0.4 | +15.2% | +15.4% | +13.2% | no |
| mom_6_1 (1997–2026; 2011) | -0.006 | -0.6 | -0.7 | -0.2 | +13.8% | +15.8% | +13.2% | no |
| book_to_market (2010–2026; 2018) | -0.007 | -0.6 | -0.9 | -0.1 | +15.4% | +17.0% | +14.4% | no |
| low_vol (1997–2026; 2011) | -0.008 | -0.6 | -0.1 | -0.7 | +10.8% | +20.2% | +13.2% | no |
| smooth_mom (1997–2026; 2011) | -0.006 | -0.7 | -0.4 | -0.6 | +11.7% | +15.7% | +13.2% | no |
| near_52w_high (1997–2026; 2011) | -0.012 | -1.0 | -0.6 | -0.8 | +11.1% | +17.1% | +13.2% | no |
| trend_200 (1997–2026; 2011) | -0.013 | -1.2 | -1.2 | -0.5 | +13.7% | +16.2% | +13.2% | no |
| mom_3 (1997–2026; 2011) | -0.019 | -1.9 | -1.6 | -1.1 | +14.9% | +15.8% | +13.2% | no |

## 2. £10,000 run by commit rules — no calendar, trade only on strong evidence

Money waits in an S&P 500 tracker. A stock is bought only when it has been in the top 5% on the score for 3 weekly checks in a row (up to 10 stocks), and sold only when it has fallen into the bottom half on 3 weekly checks in a row.

| Score | £ after HL costs | £ with no costs | S&P 500 £ | Yearly (costs) | S&P yearly | Worst fall | S&P worst | Trades / year | Typical hold | First half vs S&P | Second half vs S&P | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mom_3 (1997–2026; 2011) | £534,675 | £1,900,891 | £161,307 | +14.4% | +9.8% | -59% | -55% | 37.7 | 115 days | +4.7%/yr | +4.4%/yr | no |
| trend_200 (1997–2026; 2011) | £322,785 | £776,353 | £161,307 | +12.4% | +9.8% | -62% | -55% | 18.9 | 235 days | -1.6%/yr | +7.5%/yr | no |
| rise_weak_sector_LABELS (1997–2026; 2011) | £262,547 | £662,249 | £161,307 | +11.7% | +9.8% | -67% | -55% | 23.3 | 239 days | +1.2%/yr | +2.5%/yr | no |
| mom_6_1 (1997–2026; 2011) | £229,458 | £819,213 | £161,307 | +11.1% | +9.8% | -77% | -55% | 24.0 | 166 days | -4.9%/yr | +8.8%/yr | no |
| roa (2010–2026; 2018) | £183,261 | £193,087 | £91,913 | +19.2% | +14.3% | -31% | -29% | 1.6 | 1561 days | +0.8%/yr | +8.9%/yr | no |
| low_accruals (2010–2026; 2018) | £151,531 | £192,056 | £91,913 | +17.8% | +14.3% | -37% | -29% | 4.0 | 731 days | +6.5%/yr | +0.5%/yr | no |
| random (1997–2026; 2011) | £133,709 | £157,220 | £161,307 | +9.1% | +9.8% | -55% | -55% | 3.6 | 72 days | -0.5%/yr | -0.9%/yr | no |
| rise_weak_peers (1997–2026; 2011) | £127,976 | £433,444 | £161,307 | +9.0% | +9.8% | -82% | -55% | 27.2 | 202 days | -0.8%/yr | -1.1%/yr | no |
| low_vol (1997–2026; 2011) | £114,201 | £151,744 | £161,307 | +8.6% | +9.8% | -36% | -55% | 1.2 | 2061 days | +3.6%/yr | -6.3%/yr | no |
| mom_12_1_riskadj (1997–2026; 2011) | £105,247 | £151,813 | £161,307 | +8.3% | +9.8% | -59% | -55% | 14.9 | 326 days | +0.3%/yr | -3.6%/yr | no |
| low_asset_growth (2010–2026; 2018) | £104,336 | £127,099 | £91,913 | +15.2% | +14.3% | -37% | -29% | 7.0 | 724 days | +0.0%/yr | +1.7%/yr | no |
| gross_profitability (2010–2026; 2018) | £77,672 | £79,419 | £91,913 | +13.2% | +14.3% | -29% | -29% | 0.7 | 775 days | +3.6%/yr | -5.6%/yr | no |
| quality_value (2010–2026; 2018) | £75,248 | £77,365 | £91,913 | +13.0% | +14.3% | -28% | -29% | 0.9 | 2181 days | +2.2%/yr | -5.0%/yr | no |
| near_52w_high (1997–2026; 2011) | £69,857 | £127,896 | £161,307 | +6.8% | +9.8% | -40% | -55% | 13.2 | 210 days | -0.0%/yr | -6.0%/yr | no |
| smooth_mom (1997–2026; 2011) | £66,812 | £139,534 | £161,307 | +6.6% | +9.8% | -64% | -55% | 14.3 | 304 days | -2.9%/yr | -3.6%/yr | no |
| mom_12_1 (1997–2026; 2011) | £64,498 | £199,108 | £161,307 | +6.5% | +9.8% | -78% | -55% | 13.6 | 304 days | -8.7%/yr | +3.0%/yr | no |
| fcf_yield (2010–2026; 2018) | £53,252 | £68,846 | £91,913 | +10.6% | +14.3% | -33% | -29% | 2.7 | 529 days | -5.0%/yr | -2.3%/yr | no |
| earnings_yield (2010–2026; 2018) | £51,339 | £53,473 | £91,913 | +10.4% | +14.3% | -50% | -29% | 5.2 | 558 days | -3.8%/yr | -4.0%/yr | no |
| book_to_market (2010–2026; 2018) | £48,668 | £51,324 | £91,913 | +10.0% | +14.3% | -47% | -29% | 1.1 | 1420 days | -3.3%/yr | -5.1%/yr | no |
| quality_momentum (2010–2026; 2018) | £48,601 | £80,423 | £91,913 | +10.0% | +14.3% | -38% | -29% | 2.5 | 855 days | +0.7%/yr | -9.0%/yr | no |
| value_momentum (2010–2026; 2018) | £36,717 | £34,827 | £91,913 | +8.2% | +14.3% | -49% | -29% | 9.4 | 460 days | -7.9%/yr | -4.4%/yr | no |
| earnings_reaction (2004–2026; 2015) | £17,141 | £173,920 | £100,978 | +2.5% | +11.1% | -68% | -54% | 40.9 | 123 days | -9.4%/yr | -7.9%/yr | no |
| rise3m_weak_peers (1997–2026; 2011) | £14,455 | £261,087 | £161,307 | +1.2% | +9.8% | -68% | -55% | 39.5 | 130 days | -5.9%/yr | -11.6%/yr | no |
| reversal_1m (1997–2026; 2011) | £69 | £783,136 | £161,307 | -15.5% | +9.8% | -100% | -55% | 33.9 | 57 days | -36.6%/yr | -10.2%/yr | no |

## 2b. The same stock picks + the MARKET SWITCH

Identical rules, plus the one timing rule that held up on 1927–1999 data it had never seen: when the S&P 500 closes below its 200-day average 3 days running, everything moves to a bond fund; it goes back in after 3 closes above. **Beats buy-and-hold** means: +1%/yr or more in BOTH halves after HL costs, AND a smaller worst fall than the S&P 500. Compare every row with the first two: a score only adds value if it beats 'random picks + switch'.

| Score | £ after HL costs | S&P 500 £ | Yearly | S&P yearly | Worst fall | S&P worst | First half vs S&P | Second half vs S&P | Trades / yr | Beats buy-and-hold? | Picks add value vs random + switch? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| *S&P tracker + switch, no stocks* | £182,777 | £161,307 | +10.3% | +9.8% | -21% | -55% | +4.1%/yr | -3.9%/yr | 4.9 | — | — |
| rise_weak_sector_LABELS (1997–2026; 2011) | £572,672 | £161,307 | +14.6% | +9.8% | -44% | -55% | +9.8%/yr | -0.1%/yr | 35.7 | no | yes, +4.8%/yr |
| mom_6_1 (1997–2026; 2011) | £547,637 | £161,307 | +14.4% | +9.8% | -37% | -55% | +7.5%/yr | +2.0%/yr | 41.8 | **YES** | yes, +4.6%/yr |
| mom_12_1 (1997–2026; 2011) | £428,047 | £161,307 | +13.5% | +9.8% | -36% | -55% | +9.3%/yr | -1.8%/yr | 32.6 | no | yes, +3.7%/yr |
| trend_200 (1997–2026; 2011) | £383,140 | £161,307 | +13.1% | +9.8% | -33% | -55% | +5.4%/yr | +1.4%/yr | 36.5 | **YES** | yes, +3.3%/yr |
| mom_3 (1997–2026; 2011) | £327,994 | £161,307 | +12.5% | +9.8% | -42% | -55% | +6.2%/yr | -0.7%/yr | 48.9 | no | yes, +2.7%/yr |
| rise_weak_peers (1997–2026; 2011) | £205,329 | £161,307 | +10.7% | +9.8% | -46% | -55% | +7.3%/yr | -5.3%/yr | 42.3 | no | no, +0.9%/yr |
| mom_12_1_riskadj (1997–2026; 2011) | £166,404 | £161,307 | +10.0% | +9.8% | -30% | -55% | +6.5%/yr | -6.1%/yr | 34.4 | no | no, +0.1%/yr |
| random (1997–2026; 2011) | £160,899 | £161,307 | +9.8% | +9.8% | -22% | -55% | +5.0%/yr | -4.9%/yr | 7.9 | no | — |
| smooth_mom (1997–2026; 2011) | £91,931 | £161,307 | +7.8% | +9.8% | -31% | -55% | +3.4%/yr | -7.3%/yr | 21.1 | no | no, -2.0%/yr |
| near_52w_high (1997–2026; 2011) | £76,004 | £161,307 | +7.1% | +9.8% | -24% | -55% | +1.9%/yr | -7.3%/yr | 20.3 | no | no, -2.7%/yr |
| low_accruals (2010–2026; 2018) | £50,363 | £91,913 | +10.2% | +14.3% | -33% | -29% | -6.1%/yr | -2.3%/yr | 27.3 | no | no, +0.4%/yr |
| rise3m_weak_peers (1997–2026; 2011) | £48,432 | £161,307 | +5.5% | +9.8% | -36% | -55% | +3.3%/yr | -11.8%/yr | 48.5 | no | no, -4.4%/yr |
| low_vol (1997–2026; 2011) | £41,728 | £161,307 | +4.9% | +9.8% | -38% | -55% | +1.9%/yr | -11.5%/yr | 28.1 | no | no, -4.9%/yr |
| quality_momentum (2010–2026; 2018) | £27,059 | £91,913 | +6.2% | +14.3% | -26% | -29% | -7.5%/yr | -9.0%/yr | 22.6 | no | no, -3.6%/yr |
| book_to_market (2010–2026; 2018) | £26,769 | £91,913 | +6.1% | +14.3% | -50% | -29% | -11.5%/yr | -4.6%/yr | 25.9 | no | no, -3.7%/yr |
| quality_value (2010–2026; 2018) | £26,524 | £91,913 | +6.1% | +14.3% | -34% | -29% | -7.6%/yr | -9.4%/yr | 24.0 | no | no, -3.8%/yr |
| low_asset_growth (2010–2026; 2018) | £22,281 | £91,913 | +5.0% | +14.3% | -43% | -29% | -10.3%/yr | -8.4%/yr | 30.2 | no | no, -4.9%/yr |
| fcf_yield (2010–2026; 2018) | £21,563 | £91,913 | +4.7% | +14.3% | -49% | -29% | -13.4%/yr | -5.5%/yr | 27.4 | no | no, -5.1%/yr |
| roa (2010–2026; 2018) | £20,181 | £91,913 | +4.3% | +14.3% | -33% | -29% | -7.1%/yr | -12.7%/yr | 25.9 | no | no, -5.5%/yr |
| gross_profitability (2010–2026; 2018) | £16,789 | £91,913 | +3.2% | +14.3% | -37% | -29% | -7.5%/yr | -14.5%/yr | 23.8 | no | no, -6.7%/yr |
| earnings_yield (2010–2026; 2018) | £11,594 | £91,913 | +0.9% | +14.3% | -50% | -29% | -12.4%/yr | -14.4%/yr | 30.6 | no | no, -8.9%/yr |
| earnings_reaction (2004–2026; 2015) | £9,927 | £100,978 | -0.0% | +11.1% | -57% | -54% | -10.2%/yr | -11.7%/yr | 53.2 | no | no, -9.8%/yr |
| value_momentum (2010–2026; 2018) | £5,534 | £91,913 | -3.5% | +14.3% | -56% | -29% | -17.3%/yr | -18.4%/yr | 30.1 | no | no, -13.3%/yr |
| reversal_1m (1997–2026; 2011) | £0 | £161,307 | -100.0% | +9.8% | -100% | -55% | -11.9%/yr | -114.9%/yr | 48.0 | no | no, -109.8%/yr |

## 3a. Sanity check of the 'no costs' column

Several scores that predict nothing show millions of pounds with no costs. That is not believable, so here is where each no-cost result came from. A one-day price move of more than 50% on a large company is usually bad data from Yahoo.

| Score | £ no costs | Best 3 trades | Share of profit from them | Holdings with a >50% one-day move |
|---|---|---|---|---|
| mom_3 | £1,900,891 | WDC +462% (2025-09), MU +349% (2025-11), STX +336% (2025-09) | 49% | 8: UIS 1999-07-21, EP 2003-06-23, EP 2006-02-17, EP 2007-02-09, HBAN 2008-10-02, EP 2009-04-02 |
| mom_6_1 | £819,213 | MU +335% (2025-11), WDC +278% (2025-10), STX +261% (2025-10) | 46% | 9: EP 2000-12-20, EP 2003-06-02, EP 2004-08-24, EP 2006-05-31, THC 2008-04-07, EP 2009-05-15 |
| reversal_1m | £783,136 | SMCI +46% (2025-09), CRWD +39% (2024-08), CZR +29% (2025-10) | 10% | 32: MCIC 1997-12-09, EP 2000-05-11, BVSN 2000-12-28, AMCC 2001-03-06, BVSN 2001-07-06, EP 2001-09-10 |
| trend_200 | £776,353 | STX +463% (2025-08), MU +372% (2025-11), WDC +196% (2025-11) | 52% | 6: EP 2000-11-14, EP 2004-04-07, EP 2006-09-15, EP 2009-04-09, EP 2010-02-02, TMUS 2011-03-21 |
| rise_weak_sector_LABELS | £662,249 | CEG +180% (2023-10), META +159% (2023-01), NRG +127% (2023-11) | 28% | 2: STT 2008-02-22, OKE 2019-12-23 |
| rise_weak_peers | £433,444 | WBD +171% (2025-03), RL +147% (2023-07), APA +75% (2025-09) | 26% | 8: PTC 1998-05-19, EP 2000-12-13, MBI 2008-02-29, THC 2007-12-24, LNC 2009-01-28, FMCC 2008-04-28 |
| rise3m_weak_peers | £261,087 | LRCX +70% (2025-06), T +96% (2023-10), PM +73% (2024-06) | 20% | 3: EP 2009-05-01, APA 2020-01-23, CAM 2015-09-23 |
| mom_12_1 | £199,108 | STX +223% (2025-12), MU +186% (2026-02), WDC +189% (2025-11) | 42% | 8: UIS 1998-02-13, AAPL 1999-12-10, THC 2001-02-27, CF 2008-09-11, THC 2008-10-09, EP 2010-08-02 |
| roa | £193,087 | NVDA +3611% (2018-03), MA +2308% (2010-03), PM +706% (2010-03) | 88% | 0 |
| low_accruals | £192,056 | AMZN +3700% (2010-03), FANG +163% (2021-06), DVN +178% (2021-04) | 44% | 3: NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24 |
| earnings_reaction | £173,920 | DELL +162% (2026-04), STX +127% (2026-02), TER +92% (2025-11) | 31% | 1: HBAN 2008-08-04 |
| random | £157,220 | META +30% (2024-09), MCHP +17% (2021-10), IFF +20% (2020-03) | 105% | 0 |
| mom_12_1_riskadj | £151,813 | WDC +151% (2025-12), NVDA +314% (2016-05), NVDA +189% (2024-01) | 37% | 5: UIS 1998-03-09, AAPL 1999-12-03, TMUS 2011-04-11, NFLX 2011-02-18, NKTR 2018-04-03 |
| low_vol | £151,744 | NEE +2177% (1997-02), JNJ +570% (2008-01), KO +666% (2005-09) | 41% | 1: PARA 2023-10-24 |
| smooth_mom | £139,534 | STX +147% (2026-03), GE +184% (2023-07), NVDA +309% (2016-08) | 40% | 2: AAPL 2000-03-29, PARA 2022-12-29 |
| near_52w_high | £127,896 | GE +140% (2023-03), NVDA +289% (2015-10), L +65% (2023-09) | 47% | 2: CSR 1998-08-20, PARA 2022-05-11 |
| low_asset_growth | £127,099 | HWM +764% (2021-03), GE +479% (2022-03), WDC +62% (2026-02) | 70% | 2: DVN 2019-03-14, PARA 2023-09-08 |
| quality_momentum | £80,423 | NRG +191% (2022-06), UNH +978% (2011-11), FAST +1056% (2010-06) | 53% | 1: NFLX 2011-04-07 |
| gross_profitability | £79,419 | SHW +1664% (2010-03), UNH +1375% (2010-03), FAST +1102% (2010-07) | 67% | 1: NFLX 2011-01-04 |
| quality_value | £77,365 | GWW +1412% (2010-03), UNH +1375% (2010-03), WMT +698% (2010-04) | 58% | 0 |
| fcf_yield | £68,846 | APA +133% (2025-03), UAL +156% (2024-03), WBD +144% (2022-12) | 32% | 1: LUMN 2021-03-02 |
| earnings_yield | £53,473 | PHM +558% (2014-03), UNM +266% (2021-03), GS +367% (2010-03) | 54% | 1: FMC 2025-02-24 |
| book_to_market | £51,324 | HIG +532% (2010-03), RF +488% (2010-03), CNX +249% (2015-10) | 44% | 2: PCG 2010-03-15, GNW 2010-03-15 |
| value_momentum | £34,827 | NRG +222% (2022-05), SYF +84% (2024-04), VRSN +144% (2016-03) | 40% | 0 |

## 3. Where the money came from — was it a rule, or a few lucky stocks?

For every score whose commit portfolio ended ahead of the S&P 500 (after costs): its five best trades, and how much of all its trading profit came from just three stocks. If three trades are most of the profit, the 'rule' is really a few lucky holdings, and it would not repeat. A price jump of more than 100% in one day is flagged as a possible data error.

**mom_3** — trading profit £595,147; 47% of it from the best three trades. Possible data errors: UIS 1999-07-21, EP 2003-06-23, EP 2006-02-17, EP 2007-02-09, EP 2009-04-02, TMUS 2010-06-04, NKTR 2018-04-10

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| WDC | 2025-08-12 | 2026-09-09 | +537% | £121,624 |
| MU | 2025-11-12 | still held | +335% | £85,402 |
| STX | 2025-09-17 | still held | +336% | £75,053 |
| PLTR | 2024-11-12 | 2026-01-20 | +182% | £39,299 |
| META | 2023-03-21 | 2024-05-22 | +132% | £23,465 |

**trend_200** — trading profit £334,335; 39% of it from the best three trades. Possible data errors: EP 2000-11-14, EP 2004-04-07, EP 2006-09-08, EP 2009-04-09, EP 2010-02-02, TMUS 2011-03-21

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| MU | 2025-11-19 | still held | +372% | £67,271 |
| WDC | 2025-11-19 | still held | +196% | £35,400 |
| STX | 2026-02-10 | still held | +134% | £28,206 |
| NVDA | 2023-05-17 | 2025-03-19 | +290% | £27,260 |
| NVDA | 2015-11-25 | 2018-11-02 | +601% | £20,356 |

**rise_weak_sector_LABELS** — trading profit £282,232; 24% of it from the best three trades. Possible data errors: STT 2008-02-22, OKE 2019-12-23

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| CEG | 2023-11-14 | 2025-02-11 | +150% | £24,971 |
| META | 2023-01-06 | 2023-11-14 | +159% | £22,648 |
| NRG | 2023-11-14 | 2025-02-11 | +127% | £21,174 |
| DVN | 2020-04-20 | 2021-04-01 | +173% | £15,295 |
| FANG | 2020-04-20 | 2021-04-01 | +173% | £15,264 |

**mom_6_1** — trading profit £240,591; 41% of it from the best three trades. Possible data errors: EP 2003-05-23, EP 2004-06-04, EP 2006-05-31, THC 2008-04-07, EP 2009-05-15, EP 2010-03-17, TMUS 2010-08-30, EXPE 2011-09-16

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| MU | 2025-11-26 | still held | +363% | £41,502 |
| STX | 2025-10-01 | still held | +261% | £32,569 |
| PLTR | 2024-10-08 | 2026-03-18 | +269% | £24,220 |
| WDC | 2025-11-12 | still held | +174% | £20,824 |
| NVDA | 2023-04-04 | 2025-01-03 | +426% | £18,868 |

**roa** — trading profit £167,560; 88% of it from the best three trades. No suspect price jumps.

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| NVDA | 2018-03-15 | still held | +3611% | £117,513 |
| MA | 2010-03-15 | still held | +2308% | £23,413 |
| PM | 2010-03-15 | still held | +706% | £7,161 |
| WAT | 2010-05-18 | still held | +548% | £4,981 |
| MCO | 2010-03-15 | 2017-08-09 | +399% | £4,045 |

**low_accruals** — trading profit £132,158; 48% of it from the best three trades. Possible data errors: MUR 2016-02-29, NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| AMZN | 2010-03-15 | still held | +3700% | £37,528 |
| FANG | 2021-06-17 | still held | +163% | £13,248 |
| MMM | 2024-03-01 | 2025-02-24 | +94% | £12,135 |
| SLB | 2020-12-02 | 2023-02-09 | +158% | £10,446 |
| LYV | 2023-02-09 | still held | +111% | £10,386 |

**low_asset_growth** — trading profit £92,687; 68% of it from the best three trades. Possible data errors: DVN 2019-03-14, PARA 2023-09-08

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| HWM | 2021-03-16 | 2026-03-02 | +764% | £33,296 |
| GE | 2022-03-04 | 2026-02-13 | +479% | £24,054 |
| WDC | 2026-02-13 | still held | +62% | £5,876 |
| CTVA | 2020-03-11 | still held | +235% | £5,714 |
| DD | 2020-03-11 | still held | +220% | £5,339 |


**Result:** No score cleared the bar. None told you reliably, in advance, which S&P 500 stocks would do best. WITH THE MARKET SWITCH, these beat buy-and-hold in both halves after costs with a smaller worst fall: mom_6_1, trend_200.

---
_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those in the delisted archive are included. That flatters every score equally, so it does not change which score ranks best — but it flatters the £ figures._
