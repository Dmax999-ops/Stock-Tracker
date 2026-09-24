# What predicts which stocks do best? — ten scores tested side by side

_Generated 2026-09-24 18:32 UTC. 641 stocks ever in the S&P 500 (19 from the delisted archive), 1997-02-03 → 2026-09-24. Only stocks in the S&P 500 on each date. 'random' is the control: a score that does no better than it predicts nothing._

**Bar:** t ≥ 3 overall and t ≥ 2 in BOTH halves, and the commit-rules portfolio beats the S&P 500 by 1%/yr after HL costs in both halves.

## 1. Did the score predict the next month / year?

| Score | Rank corr. (1m) | t (all) | t 1997–2012 | t 2013–now | Top 10% next 12m | Bottom 10% | Average stock | Verdict |
|---|---|---|---|---|---|---|---|---|
| reversal_1m | +0.020 | +2.2 | +2.2 | +0.9 | +14.8% | +15.0% | +13.2% | no |
| mom_12_1_riskadj | +0.006 | +0.6 | +0.9 | -0.1 | +12.0% | +13.1% | +13.2% | no |
| mom_12_1 | +0.004 | +0.4 | +0.7 | -0.2 | +13.3% | +17.3% | +13.2% | no |
| random | -0.001 | -0.2 | -1.1 | +1.2 | +13.3% | +13.5% | +13.2% | no |
| low_vol | -0.008 | -0.6 | -0.3 | -0.6 | +10.8% | +20.3% | +13.2% | no |
| mom_6_1 | -0.006 | -0.6 | -0.9 | +0.1 | +13.8% | +16.0% | +13.2% | no |
| smooth_mom | -0.006 | -0.6 | -0.5 | -0.4 | +11.8% | +15.8% | +13.2% | no |
| near_52w_high | -0.011 | -0.9 | -0.7 | -0.7 | +11.2% | +17.2% | +13.2% | no |
| trend_200 | -0.012 | -1.1 | -1.3 | -0.2 | +13.7% | +16.2% | +13.2% | no |
| mom_3 | -0.018 | -1.8 | -1.5 | -1.0 | +15.0% | +15.8% | +13.2% | no |

## 2. £10,000 run by commit rules — no calendar, trade only on strong evidence

Money waits in an S&P 500 tracker. A stock is bought only when it has been in the top 5% on the score for 3 weekly checks in a row (up to 10 stocks), and sold only when it has fallen into the bottom half on 3 weekly checks in a row.

| Score | £ after HL costs | £ with no costs | S&P 500 £ | Yearly (costs) | S&P yearly | Worst fall | S&P worst | Trades / year | Typical hold | 1997–2012 vs S&P | 2013–now vs S&P | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trend_200 | £262,940 | £1,098,783 | £162,403 | +11.7% | +9.9% | -73% | -55% | 19.4 | 235 days | -4.2%/yr | +9.8%/yr | no |
| random | £143,580 | £181,636 | £162,403 | +9.4% | +9.9% | -54% | -55% | 4.3 | 86 days | -0.3%/yr | -0.6%/yr | no |
| mom_3 | £136,825 | £1,658,687 | £162,403 | +9.2% | +9.9% | -68% | -55% | 39.0 | 115 days | -2.7%/yr | +2.0%/yr | no |
| low_vol | £112,052 | £154,499 | £162,403 | +8.5% | +9.9% | -38% | -55% | 1.3 | 2036 days | +2.7%/yr | -6.2%/yr | no |
| mom_12_1_riskadj | £89,206 | £196,312 | £162,403 | +7.7% | +9.9% | -61% | -55% | 14.5 | 326 days | -0.3%/yr | -4.5%/yr | no |
| mom_12_1 | £58,279 | £232,651 | £162,403 | +6.1% | +9.9% | -79% | -55% | 13.9 | 318 days | -8.0%/yr | +1.9%/yr | no |
| near_52w_high | £50,237 | £118,328 | £162,403 | +5.6% | +9.9% | -42% | -55% | 13.7 | 221 days | -1.1%/yr | -8.0%/yr | no |
| smooth_mom | £48,429 | £139,191 | £162,403 | +5.5% | +9.9% | -68% | -55% | 14.3 | 297 days | -4.7%/yr | -4.1%/yr | no |
| mom_6_1 | £216 | £1,282,036 | £162,403 | -12.1% | +9.9% | -99% | -55% | 22.0 | 166 days | -16.1%/yr | -28.8%/yr | no |
| reversal_1m | £33 | £1,144,476 | £162,403 | -17.5% | +9.9% | -100% | -55% | 18.4 | 57 days | -27.6%/yr | -27.0%/yr | no |

## 3. Where the money came from — was it a rule, or a few lucky stocks?

For every score whose commit portfolio ended ahead of the S&P 500 (after costs): its five best trades, and how much of all its trading profit came from just three stocks. If three trades are most of the profit, the 'rule' is really a few lucky holdings, and it would not repeat. A price jump of more than 100% in one day is flagged as a possible data error.

**trend_200** — trading profit £273,242; 48% of it from the best three trades. No suspect price jumps.

| Stock | Bought | Sold | Return | £ gain |
|---|---|---|---|---|
| STX | 2025-08-26 | still held | +453% | £57,693 |
| MU | 2025-11-19 | still held | +374% | £47,637 |
| WDC | 2025-11-19 | still held | +195% | £24,807 |
| NVDA | 2023-05-17 | 2025-03-19 | +290% | £18,316 |
| PLTR | 2024-11-19 | 2026-02-10 | +122% | £13,332 |


**Result:** No score cleared the bar. None told you reliably, in advance, which S&P 500 stocks would do best.

---
_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those in the delisted archive are included. That flatters every score equally, so it does not change which score ranks best — but it flatters the £ figures._
