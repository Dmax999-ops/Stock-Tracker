# What predicts which stocks do best? — every score tested side by side

_Generated 2026-09-25 22:29 UTC. 643 stocks ever in the S&P 500 (21 from the delisted archive), 1997-02-03 → 2026-09-25. Only stocks in the S&P 500 on each date. 'random' is the control: a score that does no better than it predicts nothing._

**Bar:** t ≥ 3 overall and t ≥ 2 in BOTH halves, and the commit-rules portfolio beats the S&P 500 by 1%/yr after HL costs in both halves.

## 1. Did the score predict the next month / year?

| Score (years tested; halves split at) | Rank corr. (1m) | t (all) | t first half | t second half | Top 10% next 12m | Bottom 10% | Average stock | Verdict |
|---|---|---|---|---|---|---|---|---|
| reversal_1m (1997–2026; 2011) | +0.020 | +2.2 | +2.1 | +1.0 | +14.8% | +15.0% | +13.2% | no |
| random (1997–2026; 2011) | +0.004 | +1.2 | +1.1 | +0.6 | +13.1% | +13.0% | +13.2% | no |
| quality_value (2010–2026; 2018) | +0.010 | +1.2 | +1.0 | +0.8 | +17.0% | +15.6% | +15.2% | no |
| gross_profitability (2010–2026; 2018) | +0.011 | +1.1 | +1.1 | +0.6 | +13.8% | +12.4% | +15.3% | no |
| quality_momentum (2010–2026; 2018) | +0.013 | +1.1 | +1.4 | +0.2 | +16.2% | +14.9% | +15.3% | no |
| rise_weak_peers (1997–2026; 2011) | +0.008 | +1.0 | -0.3 | +1.9 | +17.6% | +12.8% | +13.2% | no |
| fcf_yield (2010–2026; 2018) | +0.008 | +0.8 | +0.3 | +0.7 | +16.7% | +14.6% | +14.6% | no |
| earnings_yield (2010–2026; 2018) | +0.007 | +0.7 | -0.6 | +1.4 | +14.2% | +17.8% | +14.5% | no |
| earnings_reaction (2004–2026; 2015) | +0.003 | +0.7 | +0.9 | +0.1 | +14.2% | +14.2% | +13.1% | no |
| roa (2010–2026; 2018) | +0.007 | +0.7 | +0.4 | +0.5 | +16.3% | +15.9% | +14.5% | no |
| mom_12_1_riskadj (1997–2026; 2011) | +0.006 | +0.6 | +0.9 | -0.1 | +12.0% | +13.1% | +13.2% | no |
| rise_weak_sector_LABELS (1997–2026; 2011) | +0.004 | +0.5 | -0.5 | +1.3 | +19.0% | +14.3% | +14.6% | no |
| low_asset_growth (2010–2026; 2018) | +0.004 | +0.5 | +0.6 | +0.1 | +15.7% | +13.7% | +14.6% | no |
| low_accruals (2010–2026; 2018) | +0.003 | +0.5 | +1.0 | -0.6 | +18.7% | +15.4% | +14.5% | no |
| mom_12_1 (1997–2026; 2011) | +0.004 | +0.4 | +0.6 | -0.1 | +13.3% | +17.3% | +13.2% | no |
| value_momentum (2010–2026; 2018) | +0.004 | +0.4 | +0.0 | +0.3 | +13.0% | +16.2% | +14.5% | no |
| rise3m_weak_peers (1997–2026; 2011) | -0.002 | -0.2 | -0.7 | +0.5 | +15.2% | +15.5% | +13.2% | no |
| book_to_market (2010–2026; 2018) | -0.007 | -0.6 | -0.9 | -0.1 | +15.4% | +17.0% | +14.4% | no |
| mom_6_1 (1997–2026; 2011) | -0.006 | -0.6 | -0.7 | -0.2 | +13.8% | +15.9% | +13.2% | no |
| low_vol (1997–2026; 2011) | -0.008 | -0.6 | -0.1 | -0.7 | +10.8% | +20.3% | +13.2% | no |
| smooth_mom (1997–2026; 2011) | -0.006 | -0.6 | -0.4 | -0.6 | +11.8% | +15.7% | +13.2% | no |
| near_52w_high (1997–2026; 2011) | -0.011 | -1.0 | -0.6 | -0.8 | +11.1% | +17.2% | +13.2% | no |
| trend_200 (1997–2026; 2011) | -0.012 | -1.1 | -1.1 | -0.5 | +13.7% | +16.2% | +13.2% | no |
| mom_3 (1997–2026; 2011) | -0.018 | -1.8 | -1.5 | -1.0 | +15.0% | +15.8% | +13.2% | no |

## 2. £10,000 run by commit rules — no calendar, trade only on strong evidence

Money waits in an S&P 500 tracker. A stock is bought only when it has been in the top 5% on the score for 3 weekly checks in a row (up to 10 stocks), and sold only when it has fallen into the bottom half on 3 weekly checks in a row.

| Score | £ after HL costs | £ with no costs | S&P 500 £ | Yearly (costs) | S&P yearly | Worst fall | S&P worst | Trades / year | Typical hold | First half vs S&P | Second half vs S&P | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trend_200 (1997–2026; 2011) | £426,157 | £920,785 | £162,403 | +13.5% | +9.9% | -69% | -55% | 19.7 | 231 days | -2.0%/yr | +10.2%/yr | no |
| mom_3 (1997–2026; 2011) | £303,774 | £1,718,724 | £162,403 | +12.2% | +9.9% | -66% | -55% | 39.2 | 115 days | +3.4%/yr | +1.1%/yr | no |
| mom_6_1 (1997–2026; 2011) | £251,774 | £1,297,979 | £162,403 | +11.5% | +9.9% | -83% | -55% | 26.1 | 173 days | -8.3%/yr | +13.9%/yr | no |
| rise_weak_sector_LABELS (1997–2026; 2011) | £238,378 | £559,363 | £162,403 | +11.3% | +9.9% | -67% | -55% | 23.2 | 239 days | +1.0%/yr | +1.9%/yr | no |
| roa (2010–2026; 2018) | £182,645 | £192,424 | £92,861 | +19.2% | +14.4% | -31% | -29% | 1.6 | 1561 days | +0.8%/yr | +8.8%/yr | no |
| rise_weak_peers (1997–2026; 2011) | £177,760 | £327,772 | £162,403 | +10.2% | +9.9% | -80% | -55% | 29.3 | 195 days | +1.9%/yr | -1.6%/yr | no |
| low_accruals (2010–2026; 2018) | £155,933 | £197,182 | £92,861 | +18.0% | +14.4% | -37% | -29% | 4.0 | 731 days | +6.5%/yr | +0.8%/yr | no |
| random (1997–2026; 2011) | £137,669 | £161,184 | £162,403 | +9.2% | +9.9% | -55% | -55% | 3.5 | 68 days | -0.9%/yr | -0.2%/yr | no |
| low_vol (1997–2026; 2011) | £114,083 | £154,499 | £162,403 | +8.6% | +9.9% | -38% | -55% | 1.3 | 2036 days | +3.4%/yr | -6.2%/yr | no |
| mom_12_1_riskadj (1997–2026; 2011) | £108,431 | £197,094 | £162,403 | +8.4% | +9.9% | -59% | -55% | 14.8 | 326 days | +0.3%/yr | -3.4%/yr | no |
| low_asset_growth (2010–2026; 2018) | £104,433 | £127,211 | £92,861 | +15.2% | +14.4% | -37% | -29% | 7.0 | 724 days | +0.0%/yr | +1.6%/yr | no |
| near_52w_high (1997–2026; 2011) | £87,261 | £158,591 | £162,403 | +7.6% | +9.9% | -42% | -55% | 13.4 | 231 days | +0.2%/yr | -4.7%/yr | no |
| gross_profitability (2010–2026; 2018) | £76,955 | £78,689 | £92,861 | +13.1% | +14.4% | -29% | -29% | 0.7 | 775 days | +3.6%/yr | -5.8%/yr | no |
| quality_value (2010–2026; 2018) | £75,529 | £77,654 | £92,861 | +13.0% | +14.4% | -28% | -29% | 0.9 | 2181 days | +2.2%/yr | -5.1%/yr | no |
| smooth_mom (1997–2026; 2011) | £66,574 | £139,505 | £162,403 | +6.6% | +9.9% | -64% | -55% | 14.3 | 297 days | -2.8%/yr | -3.7%/yr | no |
| mom_12_1 (1997–2026; 2011) | £62,795 | £232,634 | £162,403 | +6.4% | +9.9% | -77% | -55% | 14.3 | 304 days | -8.5%/yr | +2.4%/yr | no |
| fcf_yield (2010–2026; 2018) | £55,008 | £70,751 | £92,861 | +10.8% | +14.4% | -33% | -29% | 2.7 | 529 days | -5.0%/yr | -2.0%/yr | no |
| earnings_yield (2010–2026; 2018) | £53,038 | £55,369 | £92,861 | +10.6% | +14.4% | -50% | -29% | 5.3 | 558 days | -3.8%/yr | -3.7%/yr | no |
| book_to_market (2010–2026; 2018) | £50,102 | £52,805 | £92,861 | +10.2% | +14.4% | -47% | -29% | 1.1 | 1420 days | -3.3%/yr | -4.8%/yr | no |
| value_momentum (2010–2026; 2018) | £41,071 | £36,464 | £92,861 | +8.9% | +14.4% | -49% | -29% | 9.5 | 456 days | -7.8%/yr | -3.1%/yr | no |
| quality_momentum (2010–2026; 2018) | £37,078 | £63,061 | £92,861 | +8.2% | +14.4% | -38% | -29% | 2.9 | 869 days | -0.3%/yr | -11.7%/yr | no |
| earnings_reaction (2004–2026; 2015) | £17,136 | £173,741 | £102,019 | +2.5% | +11.2% | -68% | -54% | 40.9 | 123 days | -9.4%/yr | -8.0%/yr | no |
| rise3m_weak_peers (1997–2026; 2011) | £13,995 | £198,029 | £162,403 | +1.1% | +9.9% | -73% | -55% | 42.7 | 130 days | -7.5%/yr | -10.1%/yr | no |
| reversal_1m (1997–2026; 2011) | £17 | £1,181,080 | £162,403 | -19.4% | +9.9% | -100% | -55% | 36.2 | 57 days | -32.5%/yr | -25.3%/yr | no |

## 2b. The same stock picks + the MARKET SWITCH

Identical rules, plus the one timing rule that held up on 1927–1999 data it had never seen: when the S&P 500 closes below its 200-day average 3 days running, everything moves to a bond fund; it goes back in after 3 closes above. **Beats buy-and-hold** means: +1%/yr or more in BOTH halves after HL costs, AND a smaller worst fall than the S&P 500. Compare every row with the first two: a score only adds value if it beats 'random picks + switch'.

| Score | £ after HL costs | S&P 500 £ | Yearly | S&P yearly | Worst fall | S&P worst | First half vs S&P | Second half vs S&P | Trades / yr | Beats buy-and-hold? | Picks add value vs random + switch? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| *S&P tracker + switch, no stocks* | £184,017 | £162,403 | +10.3% | +9.9% | -21% | -55% | +4.1%/yr | -3.9%/yr | 4.9 | — | — |
| rise_weak_sector_LABELS (1997–2026; 2011) | £537,451 | £162,403 | +14.4% | +9.9% | -44% | -55% | +9.7%/yr | -0.5%/yr | 35.8 | no | yes, +4.3%/yr |
| mom_6_1 (1997–2026; 2011) | £535,257 | £162,403 | +14.4% | +9.9% | -36% | -55% | +7.5%/yr | +1.7%/yr | 41.7 | **YES** | yes, +4.3%/yr |
| trend_200 (1997–2026; 2011) | £421,905 | £162,403 | +13.5% | +9.9% | -33% | -55% | +5.5%/yr | +1.9%/yr | 36.3 | **YES** | yes, +3.4%/yr |
| mom_12_1 (1997–2026; 2011) | £401,509 | £162,403 | +13.3% | +9.9% | -34% | -55% | +8.9%/yr | -2.0%/yr | 32.8 | no | yes, +3.2%/yr |
| mom_3 (1997–2026; 2011) | £322,687 | £162,403 | +12.4% | +9.9% | -42% | -55% | +6.2%/yr | -0.9%/yr | 48.7 | no | yes, +2.4%/yr |
| rise_weak_peers (1997–2026; 2011) | £242,576 | £162,403 | +11.4% | +9.9% | -49% | -55% | +7.8%/yr | -4.6%/yr | 42.2 | no | yes, +1.3%/yr |
| random (1997–2026; 2011) | £171,291 | £162,403 | +10.1% | +9.9% | -21% | -55% | +4.4%/yr | -3.9%/yr | 7.9 | no | — |
| mom_12_1_riskadj (1997–2026; 2011) | £159,505 | £162,403 | +9.8% | +9.9% | -27% | -55% | +6.2%/yr | -6.2%/yr | 34.6 | no | no, -0.3%/yr |
| smooth_mom (1997–2026; 2011) | £90,372 | £162,403 | +7.7% | +9.9% | -31% | -55% | +3.2%/yr | -7.4%/yr | 21.2 | no | no, -2.3%/yr |
| near_52w_high (1997–2026; 2011) | £81,053 | £162,403 | +7.3% | +9.9% | -24% | -55% | +2.0%/yr | -6.9%/yr | 20.1 | no | no, -2.7%/yr |
| rise3m_weak_peers (1997–2026; 2011) | £56,948 | £162,403 | +6.0% | +9.9% | -36% | -55% | +3.6%/yr | -11.1%/yr | 48.3 | no | no, -4.0%/yr |
| low_accruals (2010–2026; 2018) | £50,618 | £92,861 | +10.3% | +14.4% | -33% | -29% | -6.1%/yr | -2.4%/yr | 27.3 | no | no, +0.2%/yr |
| low_vol (1997–2026; 2011) | £42,056 | £162,403 | +5.0% | +9.9% | -38% | -55% | +1.9%/yr | -11.5%/yr | 28.1 | no | no, -5.1%/yr |
| quality_momentum (2010–2026; 2018) | £27,760 | £92,861 | +6.4% | +14.4% | -26% | -29% | -7.3%/yr | -9.0%/yr | 22.7 | no | no, -3.7%/yr |
| book_to_market (2010–2026; 2018) | £27,610 | £92,861 | +6.3% | +14.4% | -50% | -29% | -11.5%/yr | -4.4%/yr | 26.0 | no | no, -3.7%/yr |
| quality_value (2010–2026; 2018) | £27,006 | £92,861 | +6.2% | +14.4% | -34% | -29% | -7.6%/yr | -9.3%/yr | 24.0 | no | no, -3.9%/yr |
| fcf_yield (2010–2026; 2018) | £22,700 | £92,861 | +5.1% | +14.4% | -49% | -29% | -13.4%/yr | -4.9%/yr | 27.4 | no | no, -5.0%/yr |
| low_asset_growth (2010–2026; 2018) | £22,077 | £92,861 | +4.9% | +14.4% | -43% | -29% | -10.3%/yr | -8.6%/yr | 30.2 | no | no, -5.2%/yr |
| roa (2010–2026; 2018) | £20,629 | £92,861 | +4.5% | +14.4% | -33% | -29% | -7.1%/yr | -12.6%/yr | 26.0 | no | no, -5.6%/yr |
| gross_profitability (2010–2026; 2018) | £17,214 | £92,861 | +3.3% | +14.4% | -35% | -29% | -7.5%/yr | -14.4%/yr | 23.8 | no | no, -6.7%/yr |
| earnings_yield (2010–2026; 2018) | £11,929 | £92,861 | +1.1% | +14.4% | -50% | -29% | -12.4%/yr | -14.2%/yr | 30.7 | no | no, -9.0%/yr |
| earnings_reaction (2004–2026; 2015) | £9,932 | £102,019 | -0.0% | +11.2% | -57% | -54% | -10.2%/yr | -11.8%/yr | 53.2 | no | no, -10.1%/yr |
| value_momentum (2010–2026; 2018) | £5,440 | £92,861 | -3.6% | +14.4% | -57% | -29% | -17.3%/yr | -18.7%/yr | 30.2 | no | no, -13.7%/yr |
| reversal_1m (1997–2026; 2011) | £0 | £162,403 | -100.0% | +9.9% | -100% | -55% | -9.6%/yr | -115.0%/yr | 52.8 | no | no, -110.1%/yr |

## 3a. Sanity check of the 'no costs' column

Several scores that predict nothing show millions of pounds with no costs. That is not believable, so here is where each no-cost result came from. A one-day price move of more than 50% on a large company is usually bad data from Yahoo.

| Score | £ no costs | Best 3 trades | Share of profit from them | Holdings with a >50% one-day move |
|---|---|---|---|---|
| mom_3 | £1,718,724 | WDC +537% (2025-08), STX +531% (2025-07), MU +356% (2025-11) | 56% | 8: UIS 1999-07-21, EP 2001-02-12, EP 2003-06-23, EP 2006-02-17, EP 2007-02-09, HBAN 2008-10-02 |
| mom_6_1 | £1,297,979 | MRNA +276% (2026-04), MU +342% (2025-11), WDC +280% (2025-10) | 44% | 10: EP 2000-12-20, EP 2003-06-02, EP 2004-08-24, EP 2006-05-31, THC 2008-04-07, EP 2009-05-15 |
| reversal_1m | £1,181,080 | SMCI +46% (2025-09), CRWD +39% (2024-08), CZR +29% (2025-10) | 9% | 31: MCIC 1997-12-09, EP 2000-05-11, AMCC 2001-03-06, EP 2001-09-10, CNP 2002-05-28, WMB 2002-06-04 |
| trend_200 | £920,785 | STX +460% (2025-08), MU +380% (2025-11), WDC +197% (2025-11) | 52% | 6: EP 2000-11-14, EP 2004-04-07, EP 2006-09-15, EP 2009-04-09, EP 2010-02-02, TMUS 2011-03-21 |
| rise_weak_sector_LABELS | £559,363 | NEM +114% (2025-07), CEG +150% (2023-11), META +159% (2023-01) | 28% | 2: STT 2008-02-22, OKE 2019-12-23 |
| rise_weak_peers | £327,772 | WBD +170% (2025-03), ALB +112% (2025-09), IRM +130% (2023-10) | 22% | 11: PTC 1998-05-19, EP 2000-12-13, EP 2008-01-24, MBI 2008-02-29, THC 2007-12-24, FHN 2008-08-13 |
| mom_12_1 | £232,634 | MU +190% (2026-02), NVDA +396% (2023-12), WDC +152% (2025-12) | 41% | 8: UIS 1998-02-13, AAPL 1999-12-10, THC 2001-02-27, CF 2008-09-11, THC 2008-10-09, EP 2009-12-03 |
| rise3m_weak_peers | £198,029 | RCL +168% (2022-10), AMD +98% (2025-06), T +96% (2023-10) | 28% | 4: FHN 2008-09-18, EP 2009-05-01, HAL 2019-12-31, APA 2020-01-23 |
| low_accruals | £197,182 | AMZN +3708% (2010-03), FANG +167% (2021-06), DVN +178% (2021-04) | 44% | 3: NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24 |
| mom_12_1_riskadj | £197,094 | WDC +152% (2025-12), NVDA +314% (2016-05), NVDA +189% (2024-01) | 34% | 5: UIS 1998-03-09, AAPL 1999-12-03, TMUS 2011-04-11, NFLX 2011-02-18, NKTR 2018-04-03 |
| roa | £192,424 | NVDA +3557% (2018-03), MA +2379% (2010-03), PM +705% (2010-03) | 88% | 0 |
| earnings_reaction | £173,741 | DELL +174% (2026-04), STX +127% (2026-02), TER +92% (2025-11) | 32% | 1: HBAN 2008-08-04 |
| random | £161,184 | UDR +49% (2021-01), WYNN +56% (2020-10), CAT +19% (2021-10) | 114% | 0 |
| near_52w_high | £158,591 | GE +140% (2023-03), NVDA +289% (2015-10), TRGP +107% (2023-08) | 42% | 2: CSR 1998-08-20, PARA 2022-05-11 |
| low_vol | £154,499 | NEE +2177% (1997-02), JNJ +586% (2008-01), KO +681% (2005-09) | 42% | 1: PARA 2023-10-24 |
| smooth_mom | £139,505 | STX +145% (2026-03), GE +184% (2023-07), NVDA +309% (2016-08) | 40% | 2: AAPL 2000-03-29, PARA 2022-12-29 |
| low_asset_growth | £127,211 | HWM +764% (2021-03), GE +479% (2022-03), WDC +62% (2026-02) | 70% | 2: DVN 2019-03-14, PARA 2023-09-08 |
| gross_profitability | £78,689 | SHW +1696% (2010-03), UNH +1413% (2010-03), FAST +1124% (2010-07) | 67% | 1: NFLX 2011-01-04 |
| quality_value | £77,654 | UNH +1413% (2010-03), GWW +1408% (2010-03), WMT +729% (2010-04) | 58% | 0 |
| fcf_yield | £70,751 | APA +140% (2025-03), UAL +163% (2024-03), WBD +144% (2022-12) | 32% | 1: LUMN 2021-03-02 |
| quality_momentum | £63,061 | FAST +480% (2016-04), UNH +1006% (2011-11), SHW +1122% (2010-06) | 69% | 1: NFLX 2011-04-07 |
| earnings_yield | £55,369 | PHM +579% (2014-03), UNM +284% (2021-03), SYF +225% (2016-03) | 54% | 1: FMC 2025-02-24 |
| book_to_market | £52,805 | HIG +542% (2010-03), RF +504% (2010-03), CNX +267% (2015-10) | 45% | 2: PCG 2010-03-15, GNW 2010-03-15 |
| value_momentum | £36,464 | NRG +222% (2022-05), SYF +89% (2024-04), VRSN +144% (2016-03) | 38% | 0 |

## 3. Where the money came from — was it a rule, or a few lucky stocks?

For every score whose commit portfolio ended ahead of the S&P 500 (after costs): its five best trades, and how much of all its trading profit came from just three stocks. If three trades are most of the profit, the 'rule' is really a few lucky holdings, and it would not repeat. A price jump of more than 100% in one day is flagged as a possible data error.

**trend_200** — trading profit £437,170; 49% of it from the best three trades. Possible data errors: EP 2000-11-14, EP 2004-04-07, EP 2006-08-10, EP 2009-04-09, EP 2010-02-02, TMUS 2011-03-21

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| STX | 2025-08-26 | still held | +460% | £94,556 |
| MU | 2025-11-19 | still held | +380% | £78,310 |
| WDC | 2025-11-19 | still held | +197% | £40,698 |
| NVDA | 2023-05-17 | 2025-03-19 | +290% | £29,170 |
| PLTR | 2024-11-19 | 2026-02-10 | +122% | £21,396 |

**mom_3** — trading profit £364,428; 45% of it from the best three trades. Possible data errors: UIS 1999-07-21, EP 2001-02-12, EP 2003-06-23, EP 2006-02-17, EP 2007-02-09, EP 2009-04-02, TMUS 2010-06-04

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| WDC | 2025-08-12 | 2026-09-09 | +537% | £69,550 |
| MU | 2025-11-05 | still held | +356% | £50,978 |
| STX | 2025-09-17 | still held | +334% | £42,259 |
| PLTR | 2024-11-12 | 2026-01-20 | +182% | £21,548 |
| NVDA | 2015-10-14 | 2017-04-11 | +264% | £14,886 |

**mom_6_1** — trading profit £269,553; 42% of it from the best three trades. Possible data errors: EP 2003-06-02, EP 2004-08-24, EP 2006-05-31, THC 2008-04-14, EP 2009-05-08, EP 2010-03-17, TMUS 2010-09-28, NFLX 2011-07-07

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| MRNA | 2026-04-23 | still held | +276% | £46,292 |
| MU | 2025-11-12 | still held | +342% | £37,421 |
| STX | 2025-10-01 | still held | +259% | £29,688 |
| PLTR | 2024-10-08 | 2026-03-18 | +269% | £19,613 |
| WDC | 2025-11-12 | still held | +176% | £19,185 |

**rise_weak_sector_LABELS** — trading profit £257,438; 24% of it from the best three trades. Possible data errors: STT 2008-02-22, OKE 2019-12-23

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| CEG | 2023-11-14 | 2025-02-11 | +150% | £22,831 |
| META | 2023-01-06 | 2023-11-14 | +159% | £20,165 |
| NRG | 2023-11-14 | 2025-02-11 | +127% | £19,359 |
| DVN | 2020-04-20 | 2021-04-01 | +173% | £14,711 |
| FANG | 2020-04-20 | 2021-04-01 | +173% | £14,681 |

**roa** — trading profit £166,536; 88% of it from the best three trades. No suspect price jumps.

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| NVDA | 2018-03-15 | still held | +3557% | £115,763 |
| MA | 2010-03-15 | still held | +2379% | £24,130 |
| PM | 2010-03-15 | still held | +705% | £7,146 |
| WAT | 2010-05-18 | still held | +540% | £4,903 |
| MCO | 2010-03-15 | 2017-08-09 | +399% | £4,045 |

**rise_weak_peers** — trading profit £204,401; 18% of it from the best three trades. Possible data errors: PTC 1998-05-19, EP 2000-12-13, EP 2008-01-24, MBI 2008-02-29, THC 2007-12-24, FHN 2008-08-13, LNC 2009-01-28, FMCC 2008-04-28

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| WBD | 2025-03-05 | still held | +170% | £17,013 |
| ALB | 2025-09-03 | 2026-03-04 | +112% | £11,888 |
| HII | 2025-05-01 | 2026-03-04 | +96% | £8,501 |
| WELL | 2023-10-03 | 2025-05-01 | +96% | £8,029 |
| APA | 2025-09-03 | 2026-04-09 | +75% | £8,008 |

**low_accruals** — trading profit £132,851; 48% of it from the best three trades. Possible data errors: MUR 2016-02-29, NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| AMZN | 2010-03-15 | still held | +3708% | £37,609 |
| FANG | 2021-06-17 | still held | +167% | £13,581 |
| MMM | 2024-03-01 | 2025-02-24 | +94% | £12,135 |
| LYV | 2023-02-09 | still held | +113% | £10,569 |
| SLB | 2020-12-02 | 2023-02-09 | +158% | £10,446 |

**low_asset_growth** — trading profit £92,422; 68% of it from the best three trades. Possible data errors: DVN 2019-03-14, PARA 2023-09-08

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| HWM | 2021-03-16 | 2026-03-02 | +764% | £33,296 |
| GE | 2022-03-04 | 2026-02-13 | +479% | £24,054 |
| WDC | 2026-02-13 | still held | +62% | £5,955 |
| CTVA | 2020-03-11 | still held | +239% | £5,805 |
| DD | 2020-03-11 | still held | +224% | £5,447 |


**Result:** No score cleared the bar. None told you reliably, in advance, which S&P 500 stocks would do best. WITH THE MARKET SWITCH, these beat buy-and-hold in both halves after costs with a smaller worst fall: mom_6_1, trend_200.

---
_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those in the delisted archive are included. That flatters every score equally, so it does not change which score ranks best — but it flatters the £ figures._
