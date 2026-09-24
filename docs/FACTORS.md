# What predicts which stocks do best? — ten scores tested side by side

_Generated 2026-09-24 18:42 UTC. 642 stocks ever in the S&P 500 (19 from the delisted archive), 1997-02-03 → 2026-09-24. Only stocks in the S&P 500 on each date. 'random' is the control: a score that does no better than it predicts nothing._

**Bar:** t ≥ 3 overall and t ≥ 2 in BOTH halves, and the commit-rules portfolio beats the S&P 500 by 1%/yr after HL costs in both halves.

## 1. Did the score predict the next month / year?

| Score | Rank corr. (1m) | t (all) | t 1997–2012 | t 2013–now | Top 10% next 12m | Bottom 10% | Average stock | Verdict |
|---|---|---|---|---|---|---|---|---|
| reversal_1m | +0.020 | +2.2 | +2.3 | +0.9 | +14.9% | +15.0% | +13.2% | no |
| mom_12_1_riskadj | +0.006 | +0.6 | +0.9 | -0.1 | +12.0% | +13.0% | +13.2% | no |
| mom_12_1 | +0.004 | +0.4 | +0.7 | -0.2 | +13.2% | +17.3% | +13.2% | no |
| random | +0.001 | +0.3 | -0.5 | +1.3 | +12.9% | +13.1% | +13.2% | no |
| low_vol | -0.007 | -0.6 | -0.2 | -0.6 | +10.8% | +20.4% | +13.2% | no |
| mom_6_1 | -0.006 | -0.6 | -0.9 | +0.1 | +13.8% | +16.1% | +13.2% | no |
| smooth_mom | -0.006 | -0.6 | -0.5 | -0.4 | +11.8% | +16.2% | +13.2% | no |
| near_52w_high | -0.011 | -0.9 | -0.7 | -0.7 | +11.1% | +17.1% | +13.2% | no |
| trend_200 | -0.013 | -1.1 | -1.4 | -0.2 | +13.6% | +16.4% | +13.2% | no |
| mom_3 | -0.018 | -1.9 | -1.6 | -1.0 | +15.0% | +15.9% | +13.2% | no |

## 2. £10,000 run by commit rules — no calendar, trade only on strong evidence

Money waits in an S&P 500 tracker. A stock is bought only when it has been in the top 5% on the score for 3 weekly checks in a row (up to 10 stocks), and sold only when it has fallen into the bottom half on 3 weekly checks in a row.

| Score | £ after HL costs | £ with no costs | S&P 500 £ | Yearly (costs) | S&P yearly | Worst fall | S&P worst | Trades / year | Typical hold | 1997–2012 vs S&P | 2013–now vs S&P | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trend_200 | £378,190 | £1,175,806 | £162,403 | +13.0% | +9.9% | -70% | -55% | 19.1 | 239 days | -2.3%/yr | +10.2%/yr | no |
| mom_3 | £143,944 | £1,891,509 | £162,403 | +9.4% | +9.9% | -71% | -55% | 38.3 | 123 days | -2.1%/yr | +1.7%/yr | no |
| random | £129,378 | £167,091 | £162,403 | +9.0% | +9.9% | -53% | -55% | 4.4 | 79 days | -1.0%/yr | -0.7%/yr | no |
| low_vol | £114,201 | £153,501 | £162,403 | +8.6% | +9.9% | -38% | -55% | 1.2 | 2061 days | +2.8%/yr | -6.2%/yr | no |
| mom_12_1_riskadj | £81,757 | £185,136 | £162,403 | +7.3% | +9.9% | -61% | -55% | 14.4 | 326 days | -0.3%/yr | -5.2%/yr | no |
| mom_12_1 | £56,195 | £204,859 | £162,403 | +6.0% | +9.9% | -80% | -55% | 14.0 | 307 days | -9.3%/yr | +3.3%/yr | no |
| near_52w_high | £50,008 | £117,817 | £162,403 | +5.6% | +9.9% | -42% | -55% | 13.7 | 217 days | -1.1%/yr | -8.0%/yr | no |
| smooth_mom | £49,970 | £142,186 | £162,403 | +5.6% | +9.9% | -67% | -55% | 14.3 | 297 days | -4.5%/yr | -4.1%/yr | no |
| mom_6_1 | £180 | £1,277,811 | £162,403 | -12.7% | +9.9% | -99% | -55% | 22.0 | 166 days | -16.4%/yr | -29.6%/yr | no |
| reversal_1m | £46 | £778,405 | £162,403 | -16.6% | +9.9% | -100% | -55% | 18.4 | 57 days | -26.7%/yr | -26.1%/yr | no |

## 3a. Sanity check of the 'no costs' column

Several scores that predict nothing show millions of pounds with no costs. That is not believable, so here is where each no-cost result came from. A one-day price move of more than 50% on a large company is usually bad data from Yahoo.

| Score | £ no costs | Best 3 trades | Share of profit from them | Holdings with a >50% one-day move |
|---|---|---|---|---|
| mom_3 | £1,891,509 | WDC +537% (2025-08), STX +522% (2025-07), MU +351% (2025-11) | 56% | 8: UIS 1999-07-21, EP 2001-02-12, EP 2003-06-23, EP 2006-02-17, EP 2006-09-08, EP 2007-02-09 |
| mom_6_1 | £1,277,811 | MRNA +258% (2026-04), MU +337% (2025-11), WDC +275% (2025-10) | 44% | 11: EP 2000-12-20, EP 2003-06-02, EP 2004-08-24, EP 2006-06-14, THC 2008-04-14, EP 2009-05-15 |
| trend_200 | £1,175,806 | STX +451% (2025-08), MU +374% (2025-11), WDC +194% (2025-11) | 52% | 6: EP 2000-11-14, EP 2003-09-03, EP 2006-09-08, EP 2009-04-09, EP 2010-02-02, TMUS 2010-08-16 |
| reversal_1m | £778,405 | SMCI +46% (2025-09), CRWD +39% (2024-08), CZR +29% (2025-10) | 9% | 35: MCIC 1997-12-09, EP 2000-05-11, AMCC 2001-03-06, EP 2001-09-10, CNP 2002-05-28, WMB 2002-06-04 |
| mom_12_1 | £204,859 | MU +187% (2026-02), WDC +149% (2025-12), NVDA +311% (2024-01) | 36% | 8: UIS 1998-02-13, AAPL 1999-12-10, THC 2001-02-27, CF 2008-09-11, THC 2008-10-09, EP 2009-12-03 |
| mom_12_1_riskadj | £185,136 | WDC +149% (2025-12), NVDA +314% (2016-05), NVDA +189% (2024-01) | 33% | 6: UIS 1998-03-09, AAPL 1999-12-03, THC 2008-10-23, TMUS 2011-04-11, NFLX 2011-02-18, NKTR 2018-04-03 |
| random | £167,091 | FDS +26% (2026-05), BALL +19% (2026-01), QCOM +30% (2023-10) | 93% | 0 |
| low_vol | £153,501 | NEE +2177% (1997-02), JNJ +588% (2008-01), KO +689% (2005-09) | 42% | 1: PARA 2023-10-24 |
| smooth_mom | £142,186 | STX +142% (2026-03), GE +184% (2023-07), NVDA +309% (2016-08) | 40% | 2: AAPL 2000-03-29, PARA 2022-12-29 |
| near_52w_high | £117,817 | GE +140% (2023-03), MA +90% (2018-02), NEE +89% (2018-04) | 39% | 2: CSR 1998-08-20, PARA 2022-05-11 |

## 3. Where the money came from — was it a rule, or a few lucky stocks?

For every score whose commit portfolio ended ahead of the S&P 500 (after costs): its five best trades, and how much of all its trading profit came from just three stocks. If three trades are most of the profit, the 'rule' is really a few lucky holdings, and it would not repeat. A price jump of more than 100% in one day is flagged as a possible data error.

**trend_200** — trading profit £388,722; 48% of it from the best three trades. Possible data errors: EP 2000-11-14, EP 2003-09-03, EP 2006-08-10, EP 2009-04-09, EP 2010-02-02, TMUS 2010-08-16

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| STX | 2025-08-26 | still held | +451% | £82,653 |
| MU | 2025-11-19 | still held | +374% | £68,510 |
| WDC | 2025-11-19 | still held | +194% | £35,513 |
| NVDA | 2023-05-17 | 2025-03-19 | +290% | £26,271 |
| PLTR | 2024-11-19 | 2026-02-10 | +122% | £19,152 |


**Result:** No score cleared the bar. None told you reliably, in advance, which S&P 500 stocks would do best.

---
_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those in the delisted archive are included. That flatters every score equally, so it does not change which score ranks best — but it flatters the £ figures._
