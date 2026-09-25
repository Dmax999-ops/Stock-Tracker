# What predicts which stocks do best? — every score tested side by side

_Generated 2026-09-25 22:34 UTC. 643 stocks ever in the S&P 500 (21 from the delisted archive), 1997-02-03 → 2026-09-25. Only stocks in the S&P 500 on each date. 'random' is the control: a score that does no better than it predicts nothing._

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
| rise3m_weak_peers (1997–2026; 2011) | -0.002 | -0.2 | -0.7 | +0.5 | +15.2% | +15.4% | +13.2% | no |
| book_to_market (2010–2026; 2018) | -0.007 | -0.6 | -0.9 | -0.1 | +15.4% | +17.0% | +14.4% | no |
| mom_6_1 (1997–2026; 2011) | -0.006 | -0.6 | -0.7 | -0.2 | +13.8% | +15.9% | +13.2% | no |
| low_vol (1997–2026; 2011) | -0.008 | -0.6 | -0.1 | -0.7 | +10.8% | +20.3% | +13.2% | no |
| smooth_mom (1997–2026; 2011) | -0.006 | -0.6 | -0.4 | -0.6 | +11.8% | +15.7% | +13.2% | no |
| near_52w_high (1997–2026; 2011) | -0.011 | -1.0 | -0.6 | -0.8 | +11.1% | +17.2% | +13.2% | no |
| trend_200 (1997–2026; 2011) | -0.012 | -1.1 | -1.1 | -0.5 | +13.7% | +16.2% | +13.2% | no |
| mom_3 (1997–2026; 2011) | -0.018 | -1.8 | -1.5 | -1.0 | +15.0% | +15.8% | +13.2% | no |

## 2. £100,000 run by commit rules — no calendar, trade only on strong evidence

Money waits in an S&P 500 tracker. A stock is bought only when it has been in the top 5% on the score for 3 weekly checks in a row (up to 10 stocks), and sold only when it has fallen into the bottom half on 3 weekly checks in a row.

| Score | £ after HL costs | £ with no costs | S&P 500 £ | Yearly (costs) | S&P yearly | Worst fall | S&P worst | Trades / year | Typical hold | First half vs S&P | Second half vs S&P | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mom_3 (1997–2026; 2011) | £11,752,469 | £17,187,235 | £1,624,027 | +17.4% | +9.9% | -64% | -55% | 39.4 | 115 days | +8.6%/yr | +6.5%/yr | no |
| mom_6_1 (1997–2026; 2011) | £7,488,633 | £12,979,786 | £1,624,027 | +15.7% | +9.9% | -77% | -55% | 26.4 | 173 days | -3.3%/yr | +16.8%/yr | no |
| trend_200 (1997–2026; 2011) | £7,151,350 | £9,207,853 | £1,624,027 | +15.5% | +9.9% | -69% | -55% | 19.9 | 224 days | +0.3%/yr | +11.8%/yr | no |
| rise_weak_sector_LABELS (1997–2026; 2011) | £5,411,094 | £7,967,432 | £1,624,027 | +14.4% | +9.9% | -67% | -55% | 22.8 | 239 days | +3.0%/yr | +6.2%/yr | no |
| reversal_1m (1997–2026; 2011) | £2,625,851 | £11,810,808 | £1,624,027 | +11.7% | +9.9% | -72% | -55% | 94.0 | 57 days | +5.4%/yr | -2.0%/yr | no |
| low_accruals (2010–2026; 2018) | £2,139,022 | £1,971,819 | £928,605 | +20.3% | +14.4% | -34% | -29% | 4.1 | 724 days | +7.4%/yr | +4.4%/yr | no |
| mom_12_1_riskadj (1997–2026; 2011) | £1,889,048 | £1,970,936 | £1,624,027 | +10.4% | +9.9% | -56% | -55% | 14.9 | 326 days | +3.1%/yr | -2.1%/yr | no |
| roa (2010–2026; 2018) | £1,884,417 | £1,924,237 | £928,605 | +19.4% | +14.4% | -31% | -29% | 1.6 | 1561 days | +1.2%/yr | +8.8%/yr | no |
| rise_weak_peers (1997–2026; 2011) | £1,525,721 | £3,277,712 | £1,624,027 | +9.6% | +9.9% | -84% | -55% | 28.8 | 195 days | -0.2%/yr | -0.4%/yr | no |
| low_vol (1997–2026; 2011) | £1,514,156 | £1,544,993 | £1,624,027 | +9.6% | +9.9% | -37% | -55% | 1.3 | 2087 days | +4.7%/yr | -5.3%/yr | no |
| random (1997–2026; 2011) | £1,513,955 | £1,611,835 | £1,624,027 | +9.6% | +9.9% | -55% | -55% | 3.5 | 68 days | -0.6%/yr | +0.2%/yr | no |
| low_asset_growth (2010–2026; 2018) | £1,173,394 | £1,268,175 | £928,605 | +16.0% | +14.4% | -36% | -29% | 7.0 | 724 days | +1.1%/yr | +2.1%/yr | no |
| earnings_reaction (2004–2026; 2015) | £1,126,587 | £1,737,413 | £1,020,189 | +11.7% | +11.2% | -63% | -54% | 41.3 | 123 days | -1.0%/yr | +2.0%/yr | no |
| smooth_mom (1997–2026; 2011) | £1,063,806 | £1,408,962 | £1,624,027 | +8.3% | +9.9% | -62% | -55% | 14.3 | 297 days | -1.1%/yr | -2.0%/yr | no |
| mom_12_1 (1997–2026; 2011) | £1,040,134 | £2,326,346 | £1,624,027 | +8.2% | +9.9% | -74% | -55% | 14.4 | 304 days | -5.9%/yr | +3.2%/yr | no |
| near_52w_high (1997–2026; 2011) | £975,081 | £1,237,474 | £1,624,027 | +8.0% | +9.9% | -39% | -55% | 13.6 | 224 days | +2.4%/yr | -6.2%/yr | no |
| rise3m_weak_peers (1997–2026; 2011) | £930,063 | £2,074,296 | £1,624,027 | +7.8% | +9.9% | -68% | -55% | 43.3 | 130 days | +0.3%/yr | -4.8%/yr | no |
| gross_profitability (2010–2026; 2018) | £779,707 | £786,894 | £928,605 | +13.2% | +14.4% | -29% | -29% | 0.7 | 775 days | +3.8%/yr | -5.8%/yr | no |
| quality_value (2010–2026; 2018) | £767,716 | £776,535 | £928,605 | +13.1% | +14.4% | -28% | -29% | 0.9 | 2181 days | +2.4%/yr | -5.1%/yr | no |
| quality_momentum (2010–2026; 2018) | £614,390 | £630,606 | £928,605 | +11.6% | +14.4% | -31% | -29% | 2.3 | 876 days | +1.7%/yr | -6.9%/yr | no |
| book_to_market (2010–2026; 2018) | £518,589 | £528,047 | £928,605 | +10.4% | +14.4% | -46% | -29% | 1.1 | 1420 days | -3.0%/yr | -4.7%/yr | no |
| earnings_yield (2010–2026; 2018) | £498,536 | £553,690 | £928,605 | +10.2% | +14.4% | -51% | -29% | 5.4 | 543 days | -3.3%/yr | -5.1%/yr | no |
| fcf_yield (2010–2026; 2018) | £340,011 | £707,507 | £928,605 | +7.7% | +14.4% | -36% | -29% | 2.1 | 597 days | -6.3%/yr | -7.1%/yr | no |
| value_momentum (2010–2026; 2018) | £332,690 | £364,638 | £928,605 | +7.5% | +14.4% | -47% | -29% | 9.6 | 420 days | -7.0%/yr | -6.7%/yr | no |

## 2b. The same stock picks + the MARKET SWITCH

Identical rules, plus the one timing rule that held up on 1927–1999 data it had never seen: when the S&P 500 closes below its 200-day average 3 days running, everything moves to a bond fund; it goes back in after 3 closes above. **Beats buy-and-hold** means: +1%/yr or more in BOTH halves after HL costs, AND a smaller worst fall than the S&P 500. Compare every row with the first two: a score only adds value if it beats 'random picks + switch'.

| Score | £ after HL costs | S&P 500 £ | Yearly | S&P yearly | Worst fall | S&P worst | First half vs S&P | Second half vs S&P | Trades / yr | Beats buy-and-hold? | Picks add value vs random + switch? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| *S&P tracker + switch, no stocks* | £1,889,353 | £1,624,027 | +10.4% | +9.9% | -21% | -55% | +4.2%/yr | -3.9%/yr | 4.9 | — | — |
| mom_6_1 (1997–2026; 2011) | £12,483,399 | £1,624,027 | +17.7% | +9.9% | -32% | -55% | +11.4%/yr | +4.4%/yr | 41.9 | **YES** | yes, +7.3%/yr |
| rise_weak_sector_LABELS (1997–2026; 2011) | £10,076,902 | £1,624,027 | +16.8% | +9.9% | -46% | -55% | +13.2%/yr | +0.9%/yr | 35.7 | no | yes, +6.4%/yr |
| mom_3 (1997–2026; 2011) | £8,939,090 | £1,624,027 | +16.4% | +9.9% | -37% | -55% | +10.8%/yr | +2.4%/yr | 48.8 | **YES** | yes, +5.9%/yr |
| trend_200 (1997–2026; 2011) | £8,725,911 | £1,624,027 | +16.3% | +9.9% | -32% | -55% | +9.3%/yr | +3.7%/yr | 36.5 | **YES** | yes, +5.8%/yr |
| mom_12_1 (1997–2026; 2011) | £6,931,206 | £1,624,027 | +15.4% | +9.9% | -32% | -55% | +11.5%/yr | -0.3%/yr | 32.7 | no | yes, +4.9%/yr |
| rise_weak_peers (1997–2026; 2011) | £5,837,571 | £1,624,027 | +14.7% | +9.9% | -47% | -55% | +11.9%/yr | -2.0%/yr | 42.2 | no | yes, +4.3%/yr |
| mom_12_1_riskadj (1997–2026; 2011) | £3,692,284 | £1,624,027 | +13.0% | +9.9% | -25% | -55% | +9.5%/yr | -3.2%/yr | 34.3 | no | yes, +2.5%/yr |
| rise3m_weak_peers (1997–2026; 2011) | £2,148,807 | £1,624,027 | +10.9% | +9.9% | -31% | -55% | +8.7%/yr | -6.4%/yr | 48.4 | no | no, +0.5%/yr |
| random (1997–2026; 2011) | £1,891,772 | £1,624,027 | +10.4% | +9.9% | -21% | -55% | +4.8%/yr | -3.5%/yr | 7.9 | no | — |
| smooth_mom (1997–2026; 2011) | £1,395,413 | £1,624,027 | +9.3% | +9.9% | -28% | -55% | +4.5%/yr | -5.5%/yr | 21.2 | no | no, -1.1%/yr |
| near_52w_high (1997–2026; 2011) | £1,227,557 | £1,624,027 | +8.8% | +9.9% | -23% | -55% | +3.6%/yr | -5.5%/yr | 20.1 | no | no, -1.6%/yr |
| low_vol (1997–2026; 2011) | £884,540 | £1,624,027 | +7.6% | +9.9% | -32% | -55% | +5.1%/yr | -9.4%/yr | 28.3 | no | no, -2.8%/yr |
| earnings_reaction (2004–2026; 2015) | £762,003 | £1,020,189 | +9.7% | +11.2% | -35% | -54% | -2.3%/yr | +0.0%/yr | 54.1 | no | no, -0.7%/yr |
| low_accruals (2010–2026; 2018) | £726,839 | £928,605 | +12.7% | +14.4% | -31% | -29% | -3.3%/yr | -0.2%/yr | 27.8 | no | yes, +2.3%/yr |
| reversal_1m (1997–2026; 2011) | £501,167 | £1,624,027 | +5.6% | +9.9% | -61% | -55% | +4.6%/yr | -12.9%/yr | 85.0 | no | no, -4.8%/yr |
| quality_value (2010–2026; 2018) | £424,580 | £928,605 | +9.1% | +14.4% | -30% | -29% | -5.2%/yr | -5.8%/yr | 24.0 | no | no, -1.3%/yr |
| fcf_yield (2010–2026; 2018) | £409,357 | £928,605 | +8.9% | +14.4% | -42% | -29% | -9.1%/yr | -1.7%/yr | 27.9 | no | no, -1.6%/yr |
| quality_momentum (2010–2026; 2018) | £396,141 | £928,605 | +8.7% | +14.4% | -24% | -29% | -4.7%/yr | -7.0%/yr | 22.8 | no | no, -1.8%/yr |
| low_asset_growth (2010–2026; 2018) | £359,768 | £928,605 | +8.0% | +14.4% | -34% | -29% | -6.7%/yr | -6.0%/yr | 30.8 | no | no, -2.4%/yr |
| roa (2010–2026; 2018) | £357,689 | £928,605 | +8.0% | +14.4% | -31% | -29% | -3.5%/yr | -9.4%/yr | 26.6 | no | no, -2.4%/yr |
| book_to_market (2010–2026; 2018) | £314,504 | £928,605 | +7.2% | +14.4% | -43% | -29% | -8.9%/yr | -5.3%/yr | 26.3 | no | no, -3.3%/yr |
| gross_profitability (2010–2026; 2018) | £245,660 | £928,605 | +5.6% | +14.4% | -27% | -29% | -5.2%/yr | -12.2%/yr | 24.0 | no | no, -4.9%/yr |
| earnings_yield (2010–2026; 2018) | £225,695 | £928,605 | +5.0% | +14.4% | -41% | -29% | -8.1%/yr | -10.5%/yr | 31.3 | no | no, -5.4%/yr |
| value_momentum (2010–2026; 2018) | £122,102 | £928,605 | +1.2% | +14.4% | -40% | -29% | -12.8%/yr | -13.6%/yr | 30.7 | no | no, -9.2%/yr |

## 3a. Sanity check of the 'no costs' column

Several scores that predict nothing show millions of pounds with no costs. That is not believable, so here is where each no-cost result came from. A one-day price move of more than 50% on a large company is usually bad data from Yahoo.

| Score | £ no costs | Best 3 trades | Share of profit from them | Holdings with a >50% one-day move |
|---|---|---|---|---|
| mom_3 | £17,187,235 | WDC +537% (2025-08), STX +531% (2025-07), MU +356% (2025-11) | 56% | 8: UIS 1999-07-21, EP 2001-02-12, EP 2003-06-23, EP 2006-02-17, EP 2007-02-09, HBAN 2008-10-02 |
| mom_6_1 | £12,979,786 | MRNA +276% (2026-04), MU +342% (2025-11), WDC +280% (2025-10) | 44% | 10: EP 2000-12-20, EP 2003-06-02, EP 2004-08-24, EP 2006-05-31, THC 2008-04-07, EP 2009-05-15 |
| reversal_1m | £11,810,808 | SMCI +46% (2025-09), CRWD +39% (2024-08), CZR +29% (2025-10) | 9% | 31: MCIC 1997-12-09, EP 2000-05-11, AMCC 2001-03-06, EP 2001-09-10, CNP 2002-05-28, WMB 2002-06-04 |
| trend_200 | £9,207,853 | STX +460% (2025-08), MU +380% (2025-11), WDC +197% (2025-11) | 52% | 6: EP 2000-11-14, EP 2004-04-07, EP 2006-09-15, EP 2009-04-09, EP 2010-02-02, TMUS 2011-03-21 |
| rise_weak_sector_LABELS | £7,967,432 | CEG +230% (2023-07), NEM +134% (2025-05), NRG +127% (2023-11) | 33% | 2: STT 2008-02-22, OKE 2019-12-23 |
| rise_weak_peers | £3,277,712 | WBD +170% (2025-03), ALB +112% (2025-09), IRM +130% (2023-10) | 22% | 11: PTC 1998-05-19, EP 2000-12-13, EP 2008-01-24, MBI 2008-02-29, THC 2007-12-24, FHN 2008-08-13 |
| mom_12_1 | £2,326,346 | MU +190% (2026-02), NVDA +396% (2023-12), WDC +152% (2025-12) | 41% | 8: UIS 1998-02-13, AAPL 1999-12-10, THC 2001-02-27, CF 2008-09-11, THC 2008-10-09, EP 2009-12-03 |
| rise3m_weak_peers | £2,074,296 | RCL +168% (2022-10), AMD +98% (2025-06), T +96% (2023-10) | 27% | 2: HAL 2019-12-31, APA 2020-01-23 |
| low_accruals | £1,971,819 | AMZN +3708% (2010-03), FANG +167% (2021-06), DVN +178% (2021-04) | 44% | 3: NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24 |
| mom_12_1_riskadj | £1,970,936 | WDC +152% (2025-12), NVDA +314% (2016-05), NVDA +189% (2024-01) | 34% | 5: UIS 1998-03-09, AAPL 1999-12-03, TMUS 2011-04-11, NFLX 2011-02-18, NKTR 2018-04-03 |
| roa | £1,924,237 | NVDA +3557% (2018-03), MA +2379% (2010-03), PM +705% (2010-03) | 88% | 0 |
| earnings_reaction | £1,737,413 | DELL +174% (2026-04), STX +127% (2026-02), TER +92% (2025-11) | 32% | 1: HBAN 2008-08-04 |
| random | £1,611,835 | UDR +49% (2021-01), WYNN +56% (2020-10), CAT +19% (2021-10) | 114% | 0 |
| low_vol | £1,544,993 | NEE +2177% (1997-02), JNJ +586% (2008-01), KO +681% (2005-09) | 42% | 1: PARA 2023-10-24 |
| smooth_mom | £1,408,962 | STX +145% (2026-03), GE +184% (2023-07), NVDA +309% (2016-08) | 40% | 2: AAPL 2000-03-29, PARA 2022-12-29 |
| low_asset_growth | £1,268,175 | HWM +764% (2021-03), GE +479% (2022-03), WDC +62% (2026-02) | 70% | 2: DVN 2019-03-14, PARA 2023-09-08 |
| near_52w_high | £1,237,474 | GE +140% (2023-03), MA +90% (2018-02), NEE +89% (2018-04) | 40% | 2: CSR 1998-08-20, PARA 2022-05-11 |
| gross_profitability | £786,894 | SHW +1696% (2010-03), UNH +1413% (2010-03), FAST +1124% (2010-07) | 67% | 1: NFLX 2011-01-04 |
| quality_value | £776,535 | UNH +1413% (2010-03), GWW +1408% (2010-03), WMT +729% (2010-04) | 58% | 0 |
| fcf_yield | £707,507 | APA +140% (2025-03), UAL +163% (2024-03), WBD +144% (2022-12) | 32% | 1: LUMN 2021-03-02 |
| quality_momentum | £630,606 | FAST +480% (2016-04), UNH +1006% (2011-11), SHW +1122% (2010-06) | 69% | 1: NFLX 2011-04-07 |
| earnings_yield | £553,690 | PHM +579% (2014-03), UNM +284% (2021-03), SYF +225% (2016-03) | 54% | 1: FMC 2025-02-24 |
| book_to_market | £528,047 | HIG +542% (2010-03), RF +504% (2010-03), CNX +267% (2015-10) | 45% | 2: PCG 2010-03-15, GNW 2010-03-15 |
| value_momentum | £364,638 | NRG +222% (2022-05), SYF +89% (2024-04), VRSN +144% (2016-03) | 38% | 0 |

## 3. Where the money came from — was it a rule, or a few lucky stocks?

For every score whose commit portfolio ended ahead of the S&P 500 (after costs): its five best trades, and how much of all its trading profit came from just three stocks. If three trades are most of the profit, the 'rule' is really a few lucky holdings, and it would not repeat. A price jump of more than 100% in one day is flagged as a possible data error.

**mom_3** — trading profit £12,145,906; 50% of it from the best three trades. Possible data errors: UIS 1999-07-21, EP 2001-02-12, EP 2003-06-23, EP 2006-02-17, EP 2007-02-09, EP 2009-04-02, TMUS 2010-06-04

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| WDC | 2025-08-12 | 2026-09-09 | +537% | £2,591,743 |
| MU | 2025-11-12 | still held | +342% | £1,864,573 |
| STX | 2025-09-17 | still held | +334% | £1,587,258 |
| PLTR | 2024-11-05 | 2026-01-20 | +230% | £995,505 |
| META | 2023-02-28 | 2024-05-22 | +168% | £607,048 |

**mom_6_1** — trading profit £7,614,917; 44% of it from the best three trades. Possible data errors: EP 2000-12-20, EP 2003-05-23, EP 2004-06-04, EP 2006-05-31, THC 2008-04-07, EP 2009-05-15, EP 2010-03-10, TMUS 2010-09-28

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| MRNA | 2026-04-23 | still held | +276% | £1,381,598 |
| MU | 2025-11-12 | still held | +342% | £1,111,142 |
| STX | 2025-10-01 | still held | +259% | £878,885 |
| PLTR | 2024-10-08 | 2026-03-18 | +269% | £576,544 |
| WDC | 2025-11-12 | still held | +176% | £569,650 |

**trend_200** — trading profit £7,079,354; 51% of it from the best three trades. Possible data errors: EP 2003-09-03, EP 2006-08-10, EP 2009-04-09, EP 2010-02-02, TMUS 2011-03-21

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| STX | 2025-08-26 | still held | +460% | £1,595,851 |
| MU | 2025-11-19 | still held | +380% | £1,339,030 |
| WDC | 2025-11-19 | still held | +197% | £695,905 |
| NVDA | 2023-05-17 | 2025-03-19 | +290% | £475,177 |
| HWM | 2024-08-12 | 2026-09-23 | +148% | £367,956 |

**rise_weak_sector_LABELS** — trading profit £5,229,066; 33% of it from the best three trades. Possible data errors: STT 2008-02-22, OKE 2019-12-23

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| CEG | 2023-07-17 | 2025-02-11 | +230% | £717,224 |
| NEM | 2025-05-08 | still held | +134% | £583,822 |
| META | 2023-01-06 | 2023-11-14 | +159% | £399,692 |
| NRG | 2023-11-14 | 2025-02-11 | +127% | £396,800 |
| APA | 2025-12-04 | 2026-04-30 | +55% | £264,124 |

**reversal_1m** — trading profit £3,074,792; 8% of it from the best three trades. Possible data errors: MCIC 1997-12-09, EP 2000-05-11, AMCC 2001-03-06, EP 2001-09-10, CNP 2002-05-28, WMB 2002-06-04, EP 2002-08-21, EP 2002-11-14

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| SMCI | 2025-09-03 | 2025-10-08 | +46% | £95,952 |
| CRWD | 2024-08-05 | 2024-10-22 | +39% | £71,290 |
| ENPH | 2021-05-14 | 2021-06-21 | +36% | £64,719 |
| CZR | 2025-10-29 | 2025-12-11 | +29% | £61,234 |
| APA | 2019-10-25 | 2020-01-08 | +48% | £60,886 |

**low_accruals** — trading profit £1,794,790; 40% of it from the best three trades. Possible data errors: NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| AMZN | 2010-03-15 | still held | +3708% | £379,141 |
| DVN | 2021-04-21 | 2022-03-04 | +195% | £175,176 |
| FANG | 2021-06-17 | still held | +167% | £166,047 |
| SLB | 2020-04-16 | 2023-02-09 | +305% | £162,764 |
| EXPE | 2023-02-09 | still held | +127% | £162,175 |

**mom_12_1_riskadj** — trading profit £1,783,319; 33% of it from the best three trades. Possible data errors: AAPL 1999-12-10, TMUS 2011-04-11, NFLX 2011-02-18, NKTR 2018-04-03

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| WDC | 2025-12-26 | still held | +152% | £236,315 |
| NVDA | 2016-05-12 | 2019-01-10 | +314% | £189,102 |
| NVDA | 2024-01-05 | 2025-06-13 | +189% | £157,234 |
| AXON | 2023-06-01 | 2025-12-26 | +204% | £149,071 |
| VST | 2024-06-28 | 2026-01-27 | +93% | £102,496 |

**roa** — trading profit £1,715,201; 88% of it from the best three trades. No suspect price jumps.

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| NVDA | 2018-03-15 | still held | +3557% | £1,196,631 |
| MA | 2010-03-15 | still held | +2379% | £243,262 |
| PM | 2010-03-15 | still held | +705% | £72,043 |
| WAT | 2010-03-29 | still held | +542% | £56,070 |
| MCO | 2010-03-15 | 2017-08-09 | +399% | £40,782 |

**low_asset_growth** — trading profit £1,013,746; 70% of it from the best three trades. Possible data errors: DVN 2019-03-14, PARA 2023-09-08

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| HWM | 2021-03-16 | 2026-03-02 | +764% | £370,948 |
| GE | 2022-03-04 | 2026-02-13 | +479% | £268,130 |
| WDC | 2026-02-13 | still held | +62% | £67,009 |
| CTVA | 2020-03-11 | still held | +239% | £64,146 |
| DD | 2020-03-11 | still held | +224% | £60,191 |

**earnings_reaction** — trading profit £1,149,833; 29% of it from the best three trades. Possible data errors: HBAN 2008-08-04

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| DELL | 2026-04-28 | still held | +174% | £156,380 |
| STX | 2026-02-06 | 2026-08-14 | +127% | £109,909 |
| TER | 2025-11-24 | 2026-05-19 | +94% | £72,660 |
| UAL | 2024-05-06 | 2025-02-07 | +102% | £62,450 |
| NVDA | 2015-11-02 | 2017-03-03 | +248% | £53,329 |


**Result:** No score cleared the bar. None told you reliably, in advance, which S&P 500 stocks would do best. WITH THE MARKET SWITCH, these beat buy-and-hold in both halves after costs with a smaller worst fall: mom_6_1, mom_3, trend_200.

---
_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those in the delisted archive are included. That flatters every score equally, so it does not change which score ranks best — but it flatters the £ figures._
