# What predicts which stocks do best? — every score tested side by side

_Generated 2026-09-25 22:15 UTC. 644 stocks ever in the S&P 500 (21 from the delisted archive), 1997-02-03 → 2026-09-25. Only stocks in the S&P 500 on each date. 'random' is the control: a score that does no better than it predicts nothing._

**Bar:** t ≥ 3 overall and t ≥ 2 in BOTH halves, and the commit-rules portfolio beats the S&P 500 by 1%/yr after HL costs in both halves.

## 1. Did the score predict the next month / year?

| Score (years tested; halves split at) | Rank corr. (1m) | t (all) | t first half | t second half | Top 10% next 12m | Bottom 10% | Average stock | Verdict |
|---|---|---|---|---|---|---|---|---|
| reversal_1m (1997–2026; 2011) | +0.020 | +2.2 | +2.1 | +1.0 | +14.9% | +15.0% | +13.2% | no |
| quality_value (2010–2026; 2018) | +0.010 | +1.2 | +1.0 | +0.8 | +17.0% | +15.6% | +15.2% | no |
| gross_profitability (2010–2026; 2018) | +0.011 | +1.1 | +1.1 | +0.6 | +13.8% | +12.4% | +15.3% | no |
| quality_momentum (2010–2026; 2018) | +0.013 | +1.1 | +1.4 | +0.2 | +16.2% | +14.9% | +15.3% | no |
| rise_weak_peers (1997–2026; 2011) | +0.008 | +1.0 | -0.4 | +1.9 | +17.5% | +13.0% | +13.2% | no |
| fcf_yield (2010–2026; 2018) | +0.008 | +0.8 | +0.3 | +0.7 | +16.7% | +14.6% | +14.6% | no |
| earnings_yield (2010–2026; 2018) | +0.007 | +0.7 | -0.6 | +1.4 | +14.2% | +17.8% | +14.5% | no |
| earnings_reaction (2004–2026; 2015) | +0.003 | +0.7 | +0.9 | +0.1 | +14.2% | +14.2% | +13.1% | no |
| roa (2010–2026; 2018) | +0.007 | +0.7 | +0.4 | +0.5 | +16.3% | +15.9% | +14.5% | no |
| mom_12_1_riskadj (1997–2026; 2011) | +0.006 | +0.6 | +0.9 | -0.1 | +12.0% | +13.1% | +13.2% | no |
| rise_weak_sector_LABELS (1997–2026; 2011) | +0.004 | +0.5 | -0.5 | +1.3 | +19.0% | +14.3% | +14.6% | no |
| low_asset_growth (2010–2026; 2018) | +0.004 | +0.5 | +0.6 | +0.1 | +15.7% | +13.7% | +14.6% | no |
| low_accruals (2010–2026; 2018) | +0.003 | +0.5 | +1.0 | -0.6 | +18.7% | +15.4% | +14.5% | no |
| mom_12_1 (1997–2026; 2011) | +0.004 | +0.4 | +0.6 | -0.1 | +13.2% | +17.3% | +13.2% | no |
| value_momentum (2010–2026; 2018) | +0.004 | +0.4 | +0.0 | +0.3 | +13.0% | +16.2% | +14.5% | no |
| random (1997–2026; 2011) | +0.001 | +0.2 | -0.6 | +1.2 | +12.7% | +13.6% | +13.2% | no |
| rise3m_weak_peers (1997–2026; 2011) | -0.002 | -0.2 | -0.7 | +0.5 | +15.2% | +15.6% | +13.2% | no |
| low_vol (1997–2026; 2011) | -0.007 | -0.6 | -0.1 | -0.7 | +10.8% | +20.4% | +13.2% | no |
| book_to_market (2010–2026; 2018) | -0.007 | -0.6 | -0.9 | -0.1 | +15.4% | +17.0% | +14.4% | no |
| mom_6_1 (1997–2026; 2011) | -0.006 | -0.6 | -0.7 | -0.2 | +13.8% | +16.0% | +13.2% | no |
| smooth_mom (1997–2026; 2011) | -0.006 | -0.6 | -0.4 | -0.6 | +11.8% | +16.3% | +13.2% | no |
| near_52w_high (1997–2026; 2011) | -0.011 | -0.9 | -0.5 | -0.8 | +11.1% | +17.0% | +13.2% | no |
| trend_200 (1997–2026; 2011) | -0.012 | -1.1 | -1.1 | -0.5 | +13.6% | +16.4% | +13.2% | no |
| mom_3 (1997–2026; 2011) | -0.018 | -1.9 | -1.6 | -1.0 | +15.0% | +15.8% | +13.2% | no |

## 2. £10,000 run by commit rules — no calendar, trade only on strong evidence

Money waits in an S&P 500 tracker. A stock is bought only when it has been in the top 5% on the score for 3 weekly checks in a row (up to 10 stocks), and sold only when it has fallen into the bottom half on 3 weekly checks in a row.

| Score | £ after HL costs | £ with no costs | S&P 500 £ | Yearly (costs) | S&P yearly | Worst fall | S&P worst | Trades / year | Typical hold | First half vs S&P | Second half vs S&P | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trend_200 (1997–2026; 2011) | £505,222 | £865,688 | £162,403 | +14.1% | +9.9% | -69% | -55% | 19.4 | 231 days | -1.6%/yr | +11.2%/yr | no |
| rise_weak_sector_LABELS (1997–2026; 2011) | £341,752 | £796,743 | £162,403 | +12.7% | +9.9% | -67% | -55% | 22.8 | 239 days | +1.1%/yr | +4.7%/yr | no |
| mom_3 (1997–2026; 2011) | £277,747 | £1,787,335 | £162,403 | +11.9% | +9.9% | -66% | -55% | 39.0 | 115 days | +3.0%/yr | +0.9%/yr | no |
| mom_6_1 (1997–2026; 2011) | £235,326 | £1,428,865 | £162,403 | +11.2% | +9.9% | -80% | -55% | 26.0 | 170 days | -6.2%/yr | +10.6%/yr | no |
| roa (2010–2026; 2018) | £182,645 | £192,424 | £92,861 | +19.2% | +14.4% | -31% | -29% | 1.6 | 1561 days | +0.8%/yr | +8.8%/yr | no |
| rise_weak_peers (1997–2026; 2011) | £174,015 | £416,546 | £162,403 | +10.1% | +9.9% | -75% | -55% | 29.5 | 195 days | +1.9%/yr | -1.7%/yr | no |
| low_accruals (2010–2026; 2018) | £155,933 | £197,182 | £92,861 | +18.0% | +14.4% | -37% | -29% | 4.0 | 731 days | +6.5%/yr | +0.8%/yr | no |
| random (1997–2026; 2011) | £137,224 | £168,845 | £162,403 | +9.2% | +9.9% | -55% | -55% | 4.4 | 101 days | -1.1%/yr | -0.1%/yr | no |
| mom_12_1_riskadj (1997–2026; 2011) | £115,652 | £186,297 | £162,403 | +8.6% | +9.9% | -59% | -55% | 14.6 | 326 days | +0.7%/yr | -3.4%/yr | no |
| low_vol (1997–2026; 2011) | £114,083 | £153,918 | £162,403 | +8.6% | +9.9% | -38% | -55% | 1.3 | 2036 days | +3.4%/yr | -6.2%/yr | no |
| low_asset_growth (2010–2026; 2018) | £104,433 | £127,211 | £92,861 | +15.2% | +14.4% | -37% | -29% | 7.0 | 724 days | +0.0%/yr | +1.6%/yr | no |
| gross_profitability (2010–2026; 2018) | £76,955 | £78,689 | £92,861 | +13.1% | +14.4% | -29% | -29% | 0.7 | 775 days | +3.6%/yr | -5.8%/yr | no |
| quality_value (2010–2026; 2018) | £75,529 | £77,654 | £92,861 | +13.0% | +14.4% | -28% | -29% | 0.9 | 2181 days | +2.2%/yr | -5.1%/yr | no |
| smooth_mom (1997–2026; 2011) | £68,464 | £142,756 | £162,403 | +6.7% | +9.9% | -64% | -55% | 14.3 | 297 days | -2.6%/yr | -3.7%/yr | no |
| near_52w_high (1997–2026; 2011) | £65,157 | £123,909 | £162,403 | +6.5% | +9.9% | -42% | -55% | 13.7 | 224 days | +0.8%/yr | -7.6%/yr | no |
| fcf_yield (2010–2026; 2018) | £55,008 | £70,751 | £92,861 | +10.8% | +14.4% | -33% | -29% | 2.7 | 529 days | -5.0%/yr | -2.0%/yr | no |
| mom_12_1 (1997–2026; 2011) | £54,222 | £204,859 | £162,403 | +5.9% | +9.9% | -81% | -55% | 14.4 | 311 days | -10.1%/yr | +3.4%/yr | no |
| earnings_yield (2010–2026; 2018) | £53,038 | £55,369 | £92,861 | +10.6% | +14.4% | -50% | -29% | 5.3 | 558 days | -3.8%/yr | -3.7%/yr | no |
| book_to_market (2010–2026; 2018) | £50,102 | £52,805 | £92,861 | +10.2% | +14.4% | -47% | -29% | 1.1 | 1420 days | -3.3%/yr | -4.8%/yr | no |
| quality_momentum (2010–2026; 2018) | £48,547 | £70,858 | £92,861 | +10.0% | +14.4% | -38% | -29% | 2.5 | 855 days | +0.7%/yr | -9.2%/yr | no |
| value_momentum (2010–2026; 2018) | £41,071 | £36,464 | £92,861 | +8.9% | +14.4% | -49% | -29% | 9.5 | 456 days | -7.8%/yr | -3.1%/yr | no |
| earnings_reaction (2004–2026; 2015) | £17,136 | £173,741 | £102,019 | +2.5% | +11.2% | -68% | -54% | 40.9 | 123 days | -9.4%/yr | -8.0%/yr | no |
| rise3m_weak_peers (1997–2026; 2011) | £13,957 | £259,099 | £162,403 | +1.1% | +9.9% | -70% | -55% | 42.7 | 130 days | -6.0%/yr | -11.8%/yr | no |
| reversal_1m (1997–2026; 2011) | £67 | £971,810 | £162,403 | -15.6% | +9.9% | -100% | -55% | 36.0 | 57 days | -32.5%/yr | -16.5%/yr | no |

## 3a. Sanity check of the 'no costs' column

Several scores that predict nothing show millions of pounds with no costs. That is not believable, so here is where each no-cost result came from. A one-day price move of more than 50% on a large company is usually bad data from Yahoo.

| Score | £ no costs | Best 3 trades | Share of profit from them | Holdings with a >50% one-day move |
|---|---|---|---|---|
| mom_3 | £1,787,335 | WDC +537% (2025-08), STX +531% (2025-07), MU +356% (2025-11) | 56% | 8: UIS 1999-07-21, EP 2001-02-12, EP 2003-06-23, EP 2006-02-17, EP 2006-09-08, EP 2007-02-09 |
| mom_6_1 | £1,428,865 | MRNA +276% (2026-04), MU +342% (2025-11), WDC +280% (2025-10) | 44% | 11: EP 2000-12-20, EP 2003-06-02, EP 2004-08-24, EP 2006-06-14, THC 2008-04-14, EP 2009-05-15 |
| reversal_1m | £971,810 | SMCI +46% (2025-09), CRWD +39% (2024-08), CZR +29% (2025-10) | 9% | 34: MCIC 1997-12-09, EP 2000-05-11, AMCC 2001-03-06, EP 2001-09-10, CNP 2002-05-28, WMB 2002-06-04 |
| trend_200 | £865,688 | STX +460% (2025-08), MU +380% (2025-11), WDC +197% (2025-11) | 52% | 6: EP 2000-11-14, EP 2004-04-07, EP 2006-08-10, EP 2009-04-09, EP 2010-02-02, TMUS 2010-08-16 |
| rise_weak_sector_LABELS | £796,743 | CEG +230% (2023-07), NEM +134% (2025-05), NRG +127% (2023-11) | 33% | 2: STT 2008-02-22, OKE 2019-12-23 |
| rise_weak_peers | £416,546 | WBD +170% (2025-03), ALB +112% (2025-09), IRM +130% (2023-10) | 22% | 9: PTC 1998-05-19, EP 2000-12-13, MBI 2008-02-29, THC 2007-12-24, FHN 2008-08-13, LNC 2009-01-28 |
| rise3m_weak_peers | £259,099 | RCL +168% (2022-10), AMD +98% (2025-06), T +96% (2023-10) | 27% | 3: EP 2009-05-01, HAL 2019-12-31, APA 2020-01-23 |
| mom_12_1 | £204,859 | MU +190% (2026-02), WDC +152% (2025-12), NVDA +313% (2024-01) | 36% | 8: UIS 1998-02-13, AAPL 1999-12-10, THC 2001-02-27, CF 2008-09-11, THC 2008-10-09, EP 2009-12-03 |
| low_accruals | £197,182 | AMZN +3708% (2010-03), FANG +167% (2021-06), DVN +178% (2021-04) | 44% | 3: NBR 2010-03-15, OXY 2015-03-17, PARA 2025-02-24 |
| roa | £192,424 | NVDA +3557% (2018-03), MA +2379% (2010-03), PM +705% (2010-03) | 88% | 0 |
| mom_12_1_riskadj | £186,297 | WDC +152% (2025-12), NVDA +314% (2016-05), NVDA +189% (2024-01) | 33% | 6: UIS 1998-03-09, AAPL 1999-12-03, THC 2008-10-23, TMUS 2011-04-11, NFLX 2011-02-18, NKTR 2018-04-03 |
| earnings_reaction | £173,741 | DELL +174% (2026-04), STX +127% (2026-02), TER +92% (2025-11) | 32% | 1: HBAN 2008-08-04 |
| random | £168,845 | BG +24% (2025-10), MPC +17% (2026-06), KKR +23% (2025-04) | 68% | 0 |
| low_vol | £153,918 | NEE +2177% (1997-02), JNJ +586% (2008-01), KO +666% (2005-10) | 42% | 1: PARA 2023-10-24 |
| smooth_mom | £142,756 | STX +145% (2026-03), GE +184% (2023-07), NVDA +309% (2016-08) | 40% | 2: AAPL 2000-03-29, PARA 2022-12-29 |
| low_asset_growth | £127,211 | HWM +764% (2021-03), GE +479% (2022-03), WDC +62% (2026-02) | 70% | 2: DVN 2019-03-14, PARA 2023-09-08 |
| near_52w_high | £123,909 | GE +140% (2023-03), MA +90% (2018-02), NEE +89% (2018-04) | 40% | 2: CSR 1998-08-20, PARA 2022-05-11 |
| gross_profitability | £78,689 | SHW +1696% (2010-03), UNH +1413% (2010-03), FAST +1124% (2010-07) | 67% | 1: NFLX 2011-01-04 |
| quality_value | £77,654 | UNH +1413% (2010-03), GWW +1408% (2010-03), WMT +729% (2010-04) | 58% | 0 |
| quality_momentum | £70,858 | UNH +1006% (2011-11), FAST +1076% (2010-06), SHW +1122% (2010-06) | 55% | 1: NFLX 2011-04-07 |
| fcf_yield | £70,751 | APA +140% (2025-03), UAL +163% (2024-03), WBD +144% (2022-12) | 32% | 1: LUMN 2021-03-02 |
| earnings_yield | £55,369 | PHM +579% (2014-03), UNM +284% (2021-03), SYF +225% (2016-03) | 54% | 1: FMC 2025-02-24 |
| book_to_market | £52,805 | HIG +542% (2010-03), RF +504% (2010-03), CNX +267% (2015-10) | 45% | 2: PCG 2010-03-15, GNW 2010-03-15 |
| value_momentum | £36,464 | NRG +222% (2022-05), SYF +89% (2024-04), VRSN +144% (2016-03) | 38% | 0 |

## 3. Where the money came from — was it a rule, or a few lucky stocks?

For every score whose commit portfolio ended ahead of the S&P 500 (after costs): its five best trades, and how much of all its trading profit came from just three stocks. If three trades are most of the profit, the 'rule' is really a few lucky holdings, and it would not repeat. A price jump of more than 100% in one day is flagged as a possible data error.

**trend_200** — trading profit £516,901; 49% of it from the best three trades. Possible data errors: EP 2000-11-14, EP 2004-04-07, EP 2006-08-10, EP 2009-04-09, EP 2010-02-02, TMUS 2010-08-16

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| STX | 2025-08-26 | still held | +460% | £112,057 |
| MU | 2025-11-19 | still held | +380% | £92,839 |
| WDC | 2025-11-19 | still held | +197% | £48,249 |
| NVDA | 2023-05-17 | 2025-03-19 | +290% | £34,503 |
| PLTR | 2024-11-19 | 2026-02-10 | +122% | £25,333 |

**rise_weak_sector_LABELS** — trading profit £355,265; 27% of it from the best three trades. Possible data errors: STT 2008-02-22, OKE 2019-12-23

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| CEG | 2023-07-17 | 2025-02-11 | +230% | £45,671 |
| META | 2023-01-06 | 2023-11-14 | +159% | £25,680 |
| NRG | 2023-11-14 | 2025-02-11 | +127% | £25,187 |
| CRL | 2025-07-22 | still held | +79% | £22,499 |
| MGM | 2020-04-20 | 2021-03-11 | +190% | £16,536 |

**mom_3** — trading profit £336,545; 44% of it from the best three trades. Possible data errors: UIS 1999-07-21, EP 2001-02-12, EP 2003-06-23, EP 2006-02-17, EP 2006-09-08, EP 2007-02-09, EP 2009-04-24, TMUS 2010-06-04

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| WDC | 2025-08-12 | 2026-09-09 | +537% | £63,661 |
| MU | 2025-11-05 | still held | +356% | £46,637 |
| STX | 2025-09-17 | still held | +334% | £38,656 |
| PLTR | 2024-11-12 | 2026-01-20 | +182% | £19,954 |
| NVDA | 2015-10-14 | 2017-04-11 | +264% | £13,932 |

**mom_6_1** — trading profit £249,005; 42% of it from the best three trades. Possible data errors: EP 2003-05-23, EP 2004-08-24, EP 2006-06-14, THC 2008-04-14, EP 2009-05-15, EP 2010-03-10, TMUS 2010-09-07, NFLX 2011-07-07

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| MU | 2025-11-12 | still held | +342% | £41,403 |
| WDC | 2025-10-22 | still held | +280% | £32,622 |
| STX | 2025-10-01 | still held | +259% | £31,731 |
| PLTR | 2024-10-08 | 2026-03-18 | +269% | £22,432 |
| NVDA | 2023-03-21 | 2025-01-03 | +452% | £16,833 |

**roa** — trading profit £166,536; 88% of it from the best three trades. No suspect price jumps.

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| NVDA | 2018-03-15 | still held | +3557% | £115,763 |
| MA | 2010-03-15 | still held | +2379% | £24,130 |
| PM | 2010-03-15 | still held | +705% | £7,146 |
| WAT | 2010-05-18 | still held | +540% | £4,903 |
| MCO | 2010-03-15 | 2017-08-09 | +399% | £4,045 |

**rise_weak_peers** — trading profit £201,776; 18% of it from the best three trades. Possible data errors: PTC 1998-05-19, EP 2000-12-13, MBI 2008-02-29, THC 2007-12-24, FHN 2008-08-13, EP 2008-11-13, LNC 2009-01-28, FMCC 2008-04-28

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| WBD | 2025-03-05 | still held | +170% | £16,658 |
| ALB | 2025-09-03 | 2026-03-04 | +112% | £11,638 |
| HII | 2025-05-01 | 2026-03-04 | +96% | £8,323 |
| WELL | 2023-10-03 | 2025-05-01 | +96% | £7,863 |
| APA | 2025-09-03 | 2026-04-09 | +75% | £7,840 |

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


**Result:** No score cleared the bar. None told you reliably, in advance, which S&P 500 stocks would do best.

---
_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those in the delisted archive are included. That flatters every score equally, so it does not change which score ranks best — but it flatters the £ figures._
