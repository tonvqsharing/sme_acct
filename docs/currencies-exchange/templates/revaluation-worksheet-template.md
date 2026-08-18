# Template — Revaluation Worksheet (đánh giá lại cuối kỳ)

Working sheet for period-end FX revaluation review (pre-post sanity check).

## Header

| Field | Value |
|---|---|
| Company | |
| Period | e.g. 2026-08 |
| Rate date | |
| Closing rate source | NHTM / NHNN / manual |
| Prepared by | |
| Reviewed by (approver) | |

## Closing rates used

| Currency | Buy (mua) | Sell (bán) | Transfer (chuyển khoản) | Applied rate | Source |
|---|---|---|---|---|---|
| USD | | | | | |
| EUR | | | | | |
| JPY | | | | | |
| GBP | | | | | |
| SGD | | | | | |
| CNY | | | | | |
| KRW | | | | | |
| AUD | | | | | |
| THB | | | | | |

## Monetary items

| Account | Name | Currency | Balance (orig) | Old VND | Rate | New VND | Difference | Gain/Loss |
|---|---|---|---|---|---|---|---|---|
| 1112 | Ngoại tệ (cash) | USD | | | | | | |
| 1122 | Ngoại tệ (bank) | USD | | | | | | |
| 131 | Phải thu KH | USD | | | | | | |
| 331 | Phải trả NB | USD | | | | | | |

## Posting summary (auto-generated)

| Account | Debit | Credit | Amount |
|---|---|---|---|
| 515 (lãi) | | ✓ | |
| 635 (lỗ) | ✓ | | |
| or 413 path | | | |

Debit total = Credit total (tol 0.01) ✅/❌

## Approval

- [ ] Differences plausible (no outliers > threshold)
- [ ] All monetary accounts covered
- [ ] Rates match bank sheet
- [ ] Period unlocked
- Approver signature / date: