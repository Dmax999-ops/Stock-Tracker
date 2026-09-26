# Trading 212 orders — DRY RUN

_Sat 26 Sep 2026 23:32 UK time. Plan of 2026-09-25. Exchange rate £1 = $1.3246. **Nothing has been sent to Trading 212.**_

**Account:** pretend new account (no API key yet) — worth £10,014, £10,014 cash.

| # | Order | Trading 212 ticker | Shares | ≈ £ | Why |
|---|---|---|---|---|---|
| 1 | **BUY** MU | `MU_US_EQ` | 2.19 | £1,792 | The strategy holds it (18% of the pot) and this account doesn't yet |
| 2 | **BUY** SNDK | `SNDK_US_EQ` | 1.08 | £1,452 | The strategy holds it (15% of the pot) and this account doesn't yet |
| 3 | **BUY** STX | `STX_US_EQ` | 1.82 | £1,262 | The strategy holds it (13% of the pot) and this account doesn't yet |
| 4 | **BUY** BE | `BE_US_EQ` | 4.79 | £1,046 | The strategy holds it (11% of the pot) and this account doesn't yet |
| 5 | **BUY** WDC | `WDC_US_EQ` | 2.67 | £922 | The strategy holds it (9% of the pot) and this account doesn't yet |
| 6 | **BUY** LITE | `LITE_US_EQ` | 1.11 | £790 | The strategy holds it (8% of the pot) and this account doesn't yet |
| 7 | **BUY** TER | `TER_US_EQ` | 2.62 | £789 | The strategy holds it (8% of the pot) and this account doesn't yet |
| 8 | **BUY** GLW | `GLW_US_EQ` | 6.08 | £721 | The strategy holds it (7% of the pot) and this account doesn't yet |
| 9 | **BUY** COHR | `COHR_US_EQ` | 2.89 | £646 | The strategy holds it (6% of the pot) and this account doesn't yet |

_Sells first, then buys. Share counts leave a small margin so a price rise before the order fills can't overspend; the rest goes into the tracker next day._

### Safety checks

| Check | Result | Detail |
|---|---|---|
| Plan is up to date | ✅ | plan of 2026-09-25 (1 days old) |
| Strategy ran without errors | ✅ |  |
| Account is in pounds | ✅ | GBP |
| No orders already waiting | ✅ | 0 pending |
| Every ticker found on Trading 212 | ➖ | not checked yet -- needs the API key |
| No stock order above 30% of the account | ✅ | applies to single stocks; whole-account moves into the tracker or bonds are allowed |
| Buys covered by cash + sales | ✅ | buys £9,419 vs £10,014 |
| Reading the real account | ➖ | no API key yet -- shown as a new account holding the set-up deposit |

### Notes

- Can't buy the S&P 500 tracker: no price found (£595)
