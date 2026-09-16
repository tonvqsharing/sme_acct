# Chart of Accounts Structure

## Overview

Circular 99/2025/TT-BTC Appendix II defines the chart of accounts. Enterprises may supplement or modify accounts per Art. 25. Account hierarchy uses 4-digit Level 1 with optional deeper levels.

## Account Code Hierarchy

```
Level 1: 4 digits (e.g., 111 = Cash)
  └── Level 2: +1 digit (e.g., 1111 = Cash on hand VND)
       └── Level 3: +1 digit (e.g., 11111 = Petty cash)
            └── Level 4: +1 digit (enterprise-specific, optional)
```

## 9 Main Account Categories

| Category | Account Range | Vietnamese Name | Description | Key Changes from Circular 200 |
|----------|--------------|-----------------|-------------|-------------------------------|
| **1 — Assets** | 1xx | Tài sản | Current + non-current assets | Accounts 161 eliminated; 215 (Biological Assets) added |
| **2 — Liabilities** | 2xx, 3xx (partial) | Nợ obligations | Short-term + long-term liabilities | Account 332 (Dividends Payable) added |
| **3 — Owner's Equity** | 4xx | Vốn chủ sở hữu | Equity, retained earnings, reserves | Account 441 eliminated |
| **4 — Revenue** | 5xx | Doanh thu | Revenue and income | Account 137 (Accrued Revenue) added |
| **5 — Cost of Goods Sold** | 6xx | Giá vốn hàng bán | Cost of goods/services sold | Account 611 eliminated |
| **6 — Expenses** | 8xx | Chi phí hoạt động kinh doanh | Operating expenses | Accounts 711/811 merged into Other Income/Expenses |
| **7 — Other Income** | 7xx | Thu nhập khác | Non-operating income | Merged from old separate accounts |
| **8 — Other Expenses** | 821xx-841xx | Chi phí khác | Non-operating expenses | Account 82112 (GMT Top-Up Tax) added |
| **9 — Off-Balance Sheet** | 9xx | Outside balance sheet | Contingent items | Unchanged |

## Key Account Codes (Circular 99)

| Code | Name (English) | Name (Vietnamese) | Category | Notes |
|------|---------------|-------------------|----------|-------|
| 111 | Cash | Tiền mặt | Assets | |
| 112 | Demand deposits | Tiền gửi không kỳ hạn | Assets | Renamed in Circular 99 |
| 113 | Short-term deposits | Tiền gửi có kỳ hạn ngắn hạn | Assets | |
| 131 | Accounts receivable | Phải thu của khách hàng | Assets | |
| 133 | VAT deductible | Thuế GTGT được khấu trừ | Assets | |
| 137 | Accrued revenue | Doanh thu cần phân bổ | Assets | New in Circular 99 |
| 153 | Tangible fixed assets | Tài sản cố định hữu hình | Assets | VAS 03 — cost model only |
| 154 | Intangible fixed assets | Tài sản cố định vô hình | Assets | VAS 04 |
| 156 | Inventories | Hàng tồn kho | Assets | VAS 02 — FIFO/weighted avg |
| 211 | Short-term borrowings | Vay ngắn hạn | Liabilities | |
| 215 | Biological assets | Tài sản sinh học | Liabilities | New in Circular 99 |
| 246 | Long-term prepaid expenses | Chi phí trả trước dài hạn | Liabilities | New in Circular 99 |
| 331 | Accounts payable | Phải trả người bán | Liabilities | |
| 332 | Dividends payable | Cổ tức phải trả | Liabilities | New in Circular 99 |
| 333 | CIT payable | Thuế TNDN phải nộp | Liabilities | |
| 351 | Provision for obligations | Dự phòng nghĩa vụ phải trả | Liabilities | New in Circular 99 |
| 411 | Charter capital | Vốn đầu tư của chủ sở hữu | Equity | |
| 413 | Foreign exchange differences | Chênh lệch tỷ giá | Equity | VAS 10 |
| 511 | Revenue from sales | Doanh thu bán hàng | Revenue | |
| 515 | Revenue from services | Doanh thu cung cấp dịch vụ | Revenue | |
| 611 | ~~Periodic inventory cost~~ | ~~Chi phí hàng tồn kho theo kỳ~~ | — | Eliminated in Circular 99 |
| 711 | Other income | Thu nhập khác | Other Income | Merged |
| 811 | Other expenses | Chi phí khác | Other Expenses | Merged |
| 82112 | GMT Top-Up Tax | Thuế TNDN bổ sung (GMT) | Other Expenses | New in Circular 99 |

## Extensibility Rules (Art. 25)

1. Enterprises may add accounts not in Appendix II
2. Enterprises may modify names, codes, structure, content of existing accounts
3. Must issue internal accounting policy documenting changes
4. Policy must state necessity and legal responsibility
5. If no changes, apply Appendix II as-is

## Software Implications

`Account` entity must support:
- Dynamic account creation (not hardcoded COA)
- Account deprecation (not deletion — for audit trail)
- Account code validation (4-digit Level 1 pattern)
- Parent-child hierarchy (Level 1 → Level 2 → Level 3)

## Domain Model

```
Account (id, code, name, level, parent_id, account_type, is_active)
  └── AccountGroup (id, code, name, account_type)
```

- `Account` is aggregate root
- `AccountCode` value object validates 4+ digit numeric pattern
- `AccountType` enum: Asset, Liability, Equity, Revenue, Expense
- `Account.Deprecate()` sets `IsActive = false` (soft-delete for audit trail)

## Circular 99 Revisions Summary

| Change Type | Accounts | Impact |
|------------|----------|--------|
| Eliminated | 161, 441, 611, 631 | Software must handle deprecation/migration |
| Added | 215, 332, 82112, 246, 351, 137 | New account codes required |
| Renamed | 112 | Display name change only |
| Merged | 711/811 | Other income/expenses restructuring |
