# What predicts which stocks do best? — ten scores tested side by side

_Generated 2026-09-24 18:22 UTC. 642 stocks ever in the S&P 500 (19 from the delisted archive), 1997-02-03 → 2026-09-24. Only stocks in the S&P 500 on each date. 'random' is the control: a score that does no better than it predicts nothing._

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
| trend_200 | £378,191 | £1,175,807 | £162,403 | +13.0% | +9.9% | -70% | -55% | 19.1 | 239 days | -2.3%/yr | +10.2%/yr | no |
| mom_3 | £143,944 | £1,891,508 | £162,403 | +9.4% | +9.9% | -71% | -55% | 38.3 | 123 days | -2.1%/yr | +1.7%/yr | no |
| random | £129,378 | £167,091 | £162,403 | +9.0% | +9.9% | -53% | -55% | 4.4 | 79 days | -1.0%/yr | -0.7%/yr | no |
| low_vol | £114,201 | £153,502 | £162,403 | +8.6% | +9.9% | -38% | -55% | 1.2 | 2061 days | +2.8%/yr | -6.2%/yr | no |
| mom_12_1_riskadj | £81,757 | £185,136 | £162,403 | +7.3% | +9.9% | -61% | -55% | 14.4 | 326 days | -0.3%/yr | -5.2%/yr | no |
| near_52w_high | £70,968 | £156,931 | £162,403 | +6.8% | +9.9% | -42% | -55% | 13.3 | 221 days | -1.6%/yr | -4.7%/yr | no |
| mom_12_1 | £56,195 | £204,859 | £162,403 | +6.0% | +9.9% | -80% | -55% | 14.0 | 307 days | -9.3%/yr | +3.3%/yr | no |
| smooth_mom | £49,970 | £142,186 | £162,403 | +5.6% | +9.9% | -67% | -55% | 14.3 | 297 days | -4.5%/yr | -4.1%/yr | no |
| mom_6_1 | £180 | £1,277,812 | £162,403 | -12.7% | +9.9% | -99% | -55% | 22.0 | 166 days | -16.4%/yr | -29.6%/yr | no |
| reversal_1m | £46 | £778,405 | £162,403 | -16.6% | +9.9% | -100% | -55% | 18.4 | 57 days | -26.7%/yr | -26.1%/yr | no |

**Result:** No score cleared the bar. None told you reliably, in advance, which S&P 500 stocks would do best.

---
_Known bias: most bankrupt or taken-over companies have no Yahoo prices; those in the delisted archive are included. That flatters every score equally, so it does not change which score ranks best — but it flatters the £ figures._
