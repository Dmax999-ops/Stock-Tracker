# What predicts which stocks do best? — every score tested side by side

_Generated 2026-11-01 08:42 UTC. 789 stocks ever in the S&P 500 (170 from the delisted archive), 1997-02-03 → 2026-10-30. Only stocks in the S&P 500 on each date. 'random' is the control: a score that does no better than it predicts nothing._

**Bar:** t ≥ 3 overall and t ≥ 2 in BOTH halves, and the commit-rules portfolio beats the S&P 500 by 1%/yr after HL costs in both halves.

## 1. Did the score predict the next month / year?

| Score (years tested; halves split at) | Rank corr. (1m) | t (all) | t first half | t second half | Top 10% next 12m | Bottom 10% | Average stock | Verdict |
|---|---|---|---|---|---|---|---|---|
| reversal_1m (1997–2026; 2011) | +0.025 | +2.9 | +2.6 | +1.5 | +14.2% | +14.9% | +12.9% | no |
| quality_value (2010–2026; 2018) | +0.010 | +1.1 | +1.0 | +0.7 | +17.0% | +15.9% | +15.2% | no |
| quality_momentum (2010–2026; 2018) | +0.014 | +1.1 | +1.4 | +0.3 | +16.1% | +15.0% | +15.3% | no |
| gross_profitability (2010–2026; 2018) | +0.011 | +1.1 | +1.2 | +0.5 | +13.9% | +12.5% | +15.3% | no |
| mom_12_1_riskadj (1997–2026; 2011) | +0.009 | +0.9 | +1.1 | +0.2 | +11.8% | +12.2% | +12.9% | no |
| fcf_yield (2010–2026; 2018) | +0.008 | +0.8 | +0.4 | +0.7 | +16.5% | +14.9% | +14.6% | no |
| roa (2010–2026; 2018) | +0.008 | +0.7 | +0.4 | +0.7 | +16.3% | +16.1% | +14.5% | no |
| earnings_yield (2010–2026; 2018) | +0.007 | +0.7 | -0.5 | +1.4 | +14.2% | +18.0% | +14.5% | no |
| earnings_reaction (2004–2026; 2015) | +0.003 | +0.7 | +0.9 | +0.0 | +14.1% | +14.3% | +13.1% | no |
| rise_weak_peers (1997–2026; 2011) | +0.005 | +0.7 | -0.6 | +1.5 | +16.8% | +12.0% | +12.9% | no |
| mom_12_1 (1997–2026; 2011) | +0.007 | +0.6 | +0.8 | +0.1 | +13.3% | +16.1% | +12.9% | no |
| low_accruals (2010–2026; 2018) | +0.004 | +0.5 | +0.9 | -0.5 | +18.8% | +15.4% | +14.5% | no |
| low_asset_growth (2010–2026; 2018) | +0.003 | +0.5 | +0.7 | +0.1 | +15.7% | +13.8% | +14.6% | no |
| value_momentum (2010–2026; 2018) | +0.004 | +0.4 | +0.0 | +0.6 | +13.1% | +16.5% | +14.5% | no |
| rise_weak_sector_LABELS (1997–2026; 2011) | +0.003 | +0.4 | -0.5 | +1.1 | +18.8% | +13.9% | +14.6% | no |
| mom_6_1 (1997–2026; 2011) | -0.002 | -0.2 | -0.2 | -0.1 | +13.6% | +14.8% | +12.9% | no |
| low_vol (1997–2026; 2011) | -0.003 | -0.2 | +0.1 | -0.4 | +10.9% | +19.4% | +12.9% | no |
| smooth_mom (1997–2026; 2011) | -0.004 | -0.4 | -0.3 | -0.4 | +11.8% | +15.0% | +12.9% | no |
| rise3m_weak_peers (1997–2026; 2011) | -0.004 | -0.5 | -0.9 | +0.2 | +14.6% | +14.6% | +12.9% | no |
| random (1997–2026; 2011) | -0.002 | -0.6 | -0.2 | -0.6 | +12.6% | +12.6% | +12.9% | no |
| book_to_market (2010–2026; 2018) | -0.007 | -0.6 | -0.9 | -0.1 | +15.3% | +16.9% | +14.4% | no |
| near_52w_high (1997–2026; 2011) | -0.011 | -0.9 | -0.5 | -0.8 | +10.9% | +16.1% | +12.9% | no |
| trend_200 (1997–2026; 2011) | -0.012 | -1.1 | -1.1 | -0.6 | +13.7% | +15.2% | +12.9% | no |
| mom_3 (1997–2026; 2011) | -0.020 | -2.0 | -1.6 | -1.3 | +14.8% | +14.9% | +12.9% | no |

## 2. £10,000 run by commit rules — no calendar, trade only on strong evidence

Money waits in an S&P 500 tracker. A stock is bought only when it has been in the top 5% on the score for 3 weekly checks in a row (up to 10 stocks), and sold only when it has fallen into the bottom half on 3 weekly checks in a row.

| Score | £ after HL costs | £ with no costs | S&P 500 £ | Yearly (costs) | S&P yearly | Worst fall | S&P worst | Trades / year | Typical hold | First half vs S&P | Second half vs S&P | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rise_weak_sector_LABELS (1997–2026; 2011) | £345,138 | £735,679 | £163,355 | +12.7% | +9.8% | -71% | -55% | 23.2 | 239 days | +1.9%/yr | +3.7%/yr | no |
| trend_200 (1997–2026; 2011) | £307,750 | £633,556 | £163,355 | +12.2% | +9.8% | -63% | -55% | 16.6 | 231 days | -0.7%/yr | +6.0%/yr | no |
| mom_3 (1997–2026; 2011) | £189,185 | £804,878 | £163,355 | +10.4% | +9.8% | -56% | -55% | 32.6 | 115 days | +2.9%/yr | -1.9%/yr | no |
| roa (2010–2026; 2018) | £179,634 | £189,183 | £91,884 | +18.9% | +14.2% | -31% | -29% | 1.6 | 1561 days | +1.1%/yr | +8.5%/yr | no |
| low_accruals (2010–2026; 2018) | £158,358 | £200,992 | £91,884 | +18.0% | +14.2% | -37% | -29% | 4.0 | 731 days | +7.1%/yr | +0.6%/yr | no |
| low_vol (1997–2026; 2011) | £129,304 | £166,752 | £163,355 | +9.0% | +9.8% | -36% | -55% | 1.4 | 2036 days | +3.6%/yr | -5.5%/yr | no |
| random (1997–2026; 2011) | £127,647 | £148,429 | £163,355 | +8.9% | +9.8% | -57% | -55% | 3.7 | 57 days | -1.0%/yr | -0.8%/yr | no |
| low_asset_growth (2010–2026; 2018) | £104,426 | £127,182 | £91,884 | +15.1% | +14.2% | -37% | -29% | 7.0 | 724 days | -0.2%/yr | +2.0%/yr | no |
| mom_12_1 (1997–2026; 2011) | £96,446 | £278,419 | £163,355 | +7.9% | +9.8% | -68% | -55% | 12.1 | 318 days | -4.3%/yr | +0.8%/yr | no |
| mom_12_1_riskadj (1997–2026; 2011) | £93,871 | £142,281 | £163,355 | +7.8% | +9.8% | -63% | -55% | 14.9 | 318 days | -1.1%/yr | -3.0%/yr | no |
| gross_profitability (2010–2026; 2018) | £81,316 | £83,148 | £91,884 | +13.4% | +14.2% | -29% | -29% | 0.7 | 775 days | +3.2%/yr | -4.8%/yr | no |
| quality_value (2010–2026; 2018) | £80,406 | £82,657 | £91,884 | +13.3% | +14.2% | -28% | -29% | 0.9 | 2181 days | +2.5%/yr | -4.3%/yr | no |
| mom_6_1 (1997–2026; 2011) | £79,628 | £223,756 | £163,355 | +7.2% | +9.8% | -73% | -55% | 21.8 | 173 days | -5.1%/yr | +0.4%/yr | no |
| rise_weak_peers (1997–2026; 2011) | £75,708 | £319,932 | £163,355 | +7.0% | +9.8% | -73% | -55% | 23.3 | 210 days | +2.1%/yr | -8.1%/yr | no |
| fcf_yield (2010–2026; 2018) | £54,268 | £61,398 | £91,884 | +10.7% | +14.2% | -33% | -29% | 2.6 | 529 days | -5.0%/yr | -2.1%/yr | no |
| earnings_yield (2010–2026; 2018) | £53,379 | £56,180 | £91,884 | +10.6% | +14.2% | -50% | -29% | 5.2 | 558 days | -4.0%/yr | -3.3%/yr | no |
| quality_momentum (2010–2026; 2018) | £51,170 | £66,040 | £91,884 | +10.3% | +14.2% | -36% | -29% | 2.4 | 775 days | -0.8%/yr | -7.1%/yr | no |
| book_to_market (2010–2026; 2018) | £51,147 | £53,916 | £91,884 | +10.3% | +14.2% | -47% | -29% | 1.1 | 1420 days | -3.3%/yr | -4.6%/yr | no |
| smooth_mom (1997–2026; 2011) | £47,187 | £103,650 | £163,355 | +5.4% | +9.8% | -62% | -55% | 14.1 | 304 days | -2.9%/yr | -6.2%/yr | no |
| value_momentum (2010–2026; 2018) | £41,941 | £57,472 | £91,884 | +9.0% | +14.2% | -49% | -29% | 8.8 | 485 days | -6.8%/yr | -3.7%/yr | no |
| near_52w_high (1997–2026; 2011) | £40,922 | £73,042 | £163,355 | +4.9% | +9.8% | -39% | -55% | 9.4 | 202 days | -0.7%/yr | -9.3%/yr | no |
| earnings_reaction (2004–2026; 2015) | £20,999 | £180,149 | £100,947 | +3.4% | +11.1% | -68% | -54% | 40.7 | 123 days | -9.0%/yr | -6.2%/yr | no |
| rise3m_weak_peers (1997–2026; 2011) | £1,663 | £113,161 | £163,355 | -5.9% | +9.8% | -90% | -55% | 34.2 | 123 days | -9.3%/yr | -22.4%/yr | no |
| reversal_1m (1997–2026; 2011) | £22 | £637,889 | £163,355 | -18.6% | +9.8% | -100% | -55% | 29.0 | 57 days | -34.9%/yr | -20.2%/yr | no |

## 2b. The same stock picks + the MARKET SWITCH

Identical rules, plus the one timing rule that held up on 1927–1999 data it had never seen: when the S&P 500 closes below its 200-day average 3 days running, everything moves to a bond fund; it goes back in after 3 closes above. **Beats buy-and-hold** means: +1%/yr or more in BOTH halves after HL costs, AND a smaller worst fall than the S&P 500. Compare every row with the first two: a score only adds value if it beats 'random picks + switch'.

| Score | £ after HL costs | S&P 500 £ | Yearly | S&P yearly | Worst fall | S&P worst | First half vs S&P | Second half vs S&P | Trades / yr | Beats buy-and-hold? | Picks add value vs random + switch? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| *S&P tracker + switch, no stocks* | £185,096 | £163,355 | +10.3% | +9.8% | -21% | -55% | +4.1%/yr | -3.9%/yr | 4.8 | — | — |
| rise_weak_sector_LABELS (1997–2026; 2011) | £685,589 | £163,355 | +15.3% | +9.8% | -42% | -55% | +10.6%/yr | +0.5%/yr | 34.4 | no | yes, +5.6%/yr |
| mom_6_1 (1997–2026; 2011) | £513,776 | £163,355 | +14.2% | +9.8% | -35% | -55% | +7.3%/yr | +1.5%/yr | 42.7 | **YES** | yes, +4.5%/yr |
| mom_12_1 (1997–2026; 2011) | £341,116 | £163,355 | +12.6% | +9.8% | -35% | -55% | +8.6%/yr | -2.9%/yr | 32.8 | no | yes, +3.0%/yr |
| trend_200 (1997–2026; 2011) | £248,848 | £163,355 | +11.4% | +9.8% | -36% | -55% | +3.8%/yr | -0.4%/yr | 37.6 | no | yes, +1.8%/yr |
| random (1997–2026; 2011) | £154,174 | £163,355 | +9.6% | +9.8% | -23% | -55% | +4.7%/yr | -4.9%/yr | 7.6 | no | — |
| rise_weak_peers (1997–2026; 2011) | £147,763 | £163,355 | +9.5% | +9.8% | -51% | -55% | +6.4%/yr | -7.0%/yr | 42.0 | no | no, -0.2%/yr |
| mom_12_1_riskadj (1997–2026; 2011) | £143,555 | £163,355 | +9.4% | +9.8% | -31% | -55% | +6.4%/yr | -7.1%/yr | 34.1 | no | no, -0.3%/yr |
| mom_3 (1997–2026; 2011) | £102,240 | £163,355 | +8.1% | +9.8% | -45% | -55% | +4.2%/yr | -7.4%/yr | 50.1 | no | no, -1.5%/yr |
| near_52w_high (1997–2026; 2011) | £80,254 | £163,355 | +7.3% | +9.8% | -24% | -55% | +1.7%/yr | -6.8%/yr | 20.1 | no | no, -2.4%/yr |
| smooth_mom (1997–2026; 2011) | £72,593 | £163,355 | +6.9% | +9.8% | -31% | -55% | +2.8%/yr | -8.6%/yr | 22.4 | no | no, -2.7%/yr |
| low_accruals (2010–2026; 2018) | £56,573 | £91,884 | +11.0% | +14.2% | -33% | -29% | -5.5%/yr | -1.0%/yr | 27.2 | no | yes, +1.3%/yr |
| low_vol (1997–2026; 2011) | £48,938 | £163,355 | +5.5% | +9.8% | -38% | -55% | +1.6%/yr | -10.2%/yr | 28.2 | no | no, -4.2%/yr |
| quality_value (2010–2026; 2018) | £28,789 | £91,884 | +6.6% | +14.2% | -34% | -29% | -6.6%/yr | -8.8%/yr | 23.9 | no | no, -3.1%/yr |
| rise3m_weak_peers (1997–2026; 2011) | £26,217 | £163,355 | +3.3% | +9.8% | -47% | -55% | +3.1%/yr | -15.8%/yr | 48.3 | no | no, -6.3%/yr |
| quality_momentum (2010–2026; 2018) | £24,754 | £91,884 | +5.6% | +14.2% | -26% | -29% | -7.0%/yr | -10.3%/yr | 22.3 | no | no, -4.0%/yr |
| low_asset_growth (2010–2026; 2018) | £22,765 | £91,884 | +5.1% | +14.2% | -43% | -29% | -10.6%/yr | -7.7%/yr | 30.0 | no | no, -4.6%/yr |
| book_to_market (2010–2026; 2018) | £22,445 | £91,884 | +5.0% | +14.2% | -50% | -29% | -11.8%/yr | -6.7%/yr | 25.8 | no | no, -4.7%/yr |
| fcf_yield (2010–2026; 2018) | £22,053 | £91,884 | +4.9% | +14.2% | -49% | -29% | -13.7%/yr | -4.8%/yr | 27.2 | no | no, -4.8%/yr |
| roa (2010–2026; 2018) | £20,019 | £91,884 | +4.3% | +14.2% | -33% | -29% | -7.2%/yr | -12.7%/yr | 25.8 | no | no, -5.4%/yr |
| gross_profitability (2010–2026; 2018) | £17,645 | £91,884 | +3.5% | +14.2% | -37% | -29% | -7.5%/yr | -14.0%/yr | 23.6 | no | no, -6.2%/yr |
| earnings_yield (2010–2026; 2018) | £12,163 | £91,884 | +1.2% | +14.2% | -50% | -29% | -12.6%/yr | -13.6%/yr | 30.5 | no | no, -8.5%/yr |
| earnings_reaction (2004–2026; 2015) | £9,625 | £100,947 | -0.2% | +11.1% | -57% | -54% | -11.1%/yr | -11.4%/yr | 53.0 | no | no, -9.8%/yr |
| value_momentum (2010–2026; 2018) | £5,209 | £91,884 | -3.8% | +14.2% | -57% | -29% | -17.8%/yr | -18.4%/yr | 29.9 | no | no, -13.5%/yr |
| reversal_1m (1997–2026; 2011) | £0 | £163,355 | -100.0% | +9.8% | -100% | -55% | -12.5%/yr | -114.9%/yr | 47.6 | no | no, -109.6%/yr |

## 3a. Sanity check of the 'no costs' column

Several scores that predict nothing show millions of pounds with no costs. That is not believable, so here is where each no-cost result came from. A one-day price move of more than 50% on a large company is usually bad data from Yahoo.

| Score | £ no costs | Best 3 trades | Share of profit from them | Holdings with a >50% one-day move |
|---|---|---|---|---|
| mom_3 | £804,878 | WDC +507% (2025-08), NVDA +316% (2023-05), MU +92% (2026-03) | 53% | 9: UIS 1999-07-21, EP 2001-02-12, KMG 2002-04-01, EP 2003-04-25, EP 2006-02-17, EP 2007-02-16 |
| rise_weak_sector_LABELS | £735,679 | CEG +150% (2023-11), NRG +127% (2023-11), META +135% (2023-01) | 24% | 4: FITB 2008-07-30, STT 2008-03-14, MS 2008-04-07, APA 2020-01-23 |
| reversal_1m | £637,889 | SMCI +46% (2025-09), JWN +95% (2020-06), CRWD +39% (2024-08) | 9% | 40: MCIC 1997-12-09, EP 2000-05-11, CTXS 2000-04-19, GRA 2000-09-19, BVSN 2000-12-28, AMCC 2001-03-06 |
| trend_200 | £633,556 | STX +294% (2025-08), WDC +158% (2025-11), NVDA +285% (2023-05) | 46% | 8: EP 2000-11-14, KMG 2002-07-10, EP 2003-06-02, EP 2006-08-10, JNY 2008-09-25, EP 2009-03-26 |
| rise_weak_peers | £319,932 | APA +75% (2025-09), WELL +96% (2023-10), CMA +86% (2023-07) | 21% | 5: PTC 1998-05-19, MBI 2008-02-29, WMB 2016-02-02, OKE 2019-09-13, CAM 2015-12-24 |
| mom_12_1 | £278,419 | NVDA +351% (2023-12), GE +278% (2023-05), MU +116% (2026-01) | 36% | 10: UIS 1998-02-13, AAPL 1999-12-10, THC 2001-02-27, KMG 2002-10-31, CF 2008-09-11, THC 2008-10-02 |
| mom_6_1 | £223,756 | NVDA +436% (2023-04), WDC +132% (2025-11), PLTR +111% (2024-12) | 44% | 9: EP 2000-12-20, KMG 2002-05-20, EP 2003-06-02, EP 2004-08-24, EP 2006-06-14, THC 2008-04-14 |
| low_accruals | £200,992 | AMZN +3566% (2010-03), FANG +203% (2021-06), DVN +178% (2021-04) | 43% | 3: NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24 |
| roa | £189,183 | NVDA +3225% (2018-03), MA +2691% (2010-03), PM +790% (2010-03) | 87% | 0 |
| earnings_reaction | £180,149 | STX +127% (2026-02), DELL +107% (2026-04), TER +92% (2025-11) | 28% | 1: HBAN 2008-08-04 |
| low_vol | £166,752 | NEE +2177% (1997-02), RSG +206% (2019-08), JNJ +644% (2008-01) | 40% | 1: PARA 2023-10-24 |
| random | £148,429 | NEM +36% (2023-11), CTSH +20% (2026-04), DLR +17% (2025-03) | 303% | 1: MS 2008-09-04 |
| mom_12_1_riskadj | £142,281 | MU +141% (2026-04), NVDA +189% (2024-01), AXON +204% (2023-06) | 34% | 5: UIS 1998-03-09, AAPL 1999-12-03, TMUS 2011-04-11, NFLX 2011-02-18, CAM 2016-03-16 |
| low_asset_growth | £127,182 | HWM +764% (2021-03), GE +479% (2022-03), DD +245% (2020-03) | 71% | 2: DVN 2019-03-14, PARA 2023-09-08 |
| rise3m_weak_peers | £113,161 | T +94% (2023-11), PM +73% (2024-06), NFLX +165% (2012-11) | 23% | 9: EP 2007-02-02, JNS 2008-06-10, SOV 2008-08-20, JNY 2008-06-10, FHN 2008-09-25, EP 2009-03-26 |
| smooth_mom | £103,650 | GE +184% (2023-07), MSFT +209% (2018-02), NVDA +138% (2023-09) | 43% | 2: AAPL 2000-03-29, PARA 2022-12-29 |
| gross_profitability | £83,148 | SHW +1715% (2010-03), UNH +1535% (2010-03), FAST +1166% (2010-07) | 67% | 1: NFLX 2011-01-04 |
| quality_value | £82,657 | GWW +1549% (2010-03), UNH +1535% (2010-03), WMT +849% (2010-04) | 60% | 0 |
| near_52w_high | £73,042 | MA +90% (2018-02), FRX +120% (2013-06), CSX +67% (2016-09) | 40% | 2: CSR 1998-08-20, PARA 2023-03-21 |
| quality_momentum | £66,040 | UNH +1095% (2011-11), SBUX +1058% (2010-03), FAST +1117% (2010-06) | 63% | 1: NFLX 2011-04-07 |
| fcf_yield | £61,398 | APA +198% (2025-03), UAL +141% (2024-03), ETR +317% (2013-03) | 41% | 1: LUMN 2021-03-02 |
| value_momentum | £57,472 | WDC +357% (2025-08), NRG +169% (2024-02), LEN +380% (2020-03) | 51% | 0 |
| earnings_yield | £56,180 | PHM +607% (2014-03), UNM +282% (2021-03), SYF +236% (2016-03) | 50% | 1: FMC 2025-02-24 |
| book_to_market | £53,916 | HIG +585% (2010-03), RF +525% (2010-03), CNX +320% (2015-10) | 46% | 2: PCG 2010-03-15, GNW 2010-03-15 |

## 3. Where the money came from — was it a rule, or a few lucky stocks?

For every score whose commit portfolio ended ahead of the S&P 500 (after costs): its five best trades, and how much of all its trading profit came from just three stocks. If three trades are most of the profit, the 'rule' is really a few lucky holdings, and it would not repeat. A price jump of more than 100% in one day is flagged as a possible data error.

**rise_weak_sector_LABELS** — trading profit £362,472; 22% of it from the best three trades. Possible data errors: STT 2008-03-14, MS 2008-04-07, APA 2020-01-23

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| CEG | 2023-11-14 | 2025-02-11 | +150% | £30,197 |
| NRG | 2023-11-14 | 2025-02-11 | +127% | £25,605 |
| META | 2023-01-23 | 2023-11-14 | +135% | £23,344 |
| APA | 2026-02-10 | 2026-04-30 | +49% | £16,514 |
| HAL | 2020-04-13 | 2021-04-01 | +182% | £16,040 |

**trend_200** — trading profit £280,163; 42% of it from the best three trades. Possible data errors: EP 2000-11-14, KMG 2002-07-10, EP 2003-06-02, EP 2006-08-10, JNY 2008-09-25, EP 2009-03-26, DISCK 2021-03-04

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| STX | 2025-08-26 | still held | +294% | £54,648 |
| WDC | 2025-11-19 | 2026-10-28 | +158% | £30,954 |
| NVDA | 2023-05-24 | 2025-03-19 | +285% | £30,903 |
| MU | 2026-01-27 | still held | +116% | £26,428 |
| PLTR | 2024-11-19 | 2026-02-10 | +122% | £19,975 |

**mom_3** — trading profit £212,402; 42% of it from the best three trades. Possible data errors: UIS 1999-07-21, EP 2001-02-12, KMG 2002-04-01, EP 2003-04-25, EP 2006-04-10, EP 2007-02-16, EP 2009-04-02, TMUS 2010-06-04

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| WDC | 2025-08-26 | 2026-09-09 | +507% | £52,654 |
| NVDA | 2023-05-03 | 2024-09-17 | +316% | £23,349 |
| NVDA | 2015-10-14 | 2017-04-11 | +264% | £13,235 |
| MU | 2026-03-18 | still held | +92% | £12,335 |
| MRNA | 2026-09-09 | still held | +64% | £11,397 |

**roa** — trading profit £160,256; 88% of it from the best three trades. No suspect price jumps.

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| NVDA | 2018-03-15 | still held | +3225% | £104,959 |
| MA | 2010-03-15 | still held | +2691% | £27,290 |
| PM | 2010-03-15 | still held | +790% | £8,007 |
| WAT | 2010-05-18 | still held | +583% | £5,294 |
| MCO | 2010-03-15 | 2017-08-09 | +399% | £4,045 |

**low_accruals** — trading profit £139,577; 46% of it from the best three trades. Possible data errors: MUR 2016-02-29, NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| AMZN | 2010-03-15 | still held | +3566% | £36,167 |
| FANG | 2021-06-17 | still held | +203% | £16,537 |
| MMM | 2024-03-01 | 2025-02-24 | +94% | £12,135 |
| LYV | 2023-02-09 | still held | +122% | £11,387 |
| SLB | 2020-12-02 | 2023-02-09 | +158% | £10,446 |

**low_asset_growth** — trading profit £91,340; 69% of it from the best three trades. Possible data errors: DVN 2019-03-14, PARA 2023-09-08

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| HWM | 2021-03-16 | 2026-03-02 | +764% | £33,296 |
| GE | 2022-03-04 | 2026-02-13 | +479% | £24,054 |
| DD | 2020-03-11 | still held | +245% | £5,946 |
| CTVA | 2020-03-11 | still held | +235% | £5,707 |
| QCOM | 2019-03-07 | 2020-11-24 | +183% | £4,982 |


**Result:** No score cleared the bar. None told you reliably, in advance, which S&P 500 stocks would do best. WITH THE MARKET SWITCH, these beat buy-and-hold in both halves after costs with a smaller worst fall: mom_6_1.

---
_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those in the delisted archive are included. That flatters every score equally, so it does not change which score ranks best — but it flatters the £ figures._
