# Financial Statements — Specifications

**Module:** `src/bricks/financial_statements/`
**Regulatory basis:** TT99/2025/TT-BTC
**Date:** 2026-08-28

---

## 1. Account Type Classification (Prerequisite)

### 1.1 Requirement
Every COA account must have an `account_type` that determines which financial statement section it feeds.

### 1.2 TT99 Account Groups (Appendix II)

| First Digit | Account Type | Vietnamese | BS/IS Section |
|---|---|---|---|
| 1 | ASSET | Tài sản | Balance Sheet — Assets |
| 2 | LIABILITY | Nợ phải trả | Balance Sheet — Liabilities |
| 3 | EQUITY | Vốn chủ sở hữu | Balance Sheet — Equity |
| 4 | REVENUE | Doanh thu | Income Statement — Revenue |
| 5 | EXPENSE | Chi phí | Income Statement — Expenses |

### 1.3 Data Model

```python
class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"
```

### 1.4 Auto-Classification Rule

```python
def classify_account(code: str) -> AccountType:
    first = int(code[0])
    mapping = {1: ASSET, 2: LIABILITY, 3: EQUITY, 4: REVENUE, 5: EXPENSE}
    return mapping[first]
```

### 1.5 Acceptance Criteria
- [ ] `Account` domain has `account_type: AccountType` field
- [ ] `create_account()` auto-classifies based on code prefix
- [ ] `get_by_id()` returns `account_type`
- [ ] Existing accounts retroactively classified on migration
- [ ] Level 2/3 child accounts inherit parent's `account_type`

---

## 2. Trial Balance (S06-DN)

### 2.1 Requirement
Generate a trial balance with subtotals by account group. Format per TT99 Form S06-DN.

### 2.2 Data Source
Existing `LedgerService.trial_balance(company_id, from_date, to_date)`.

### 2.3 Output Format

```json
{
  "company_id": "...",
  "period": {"from": "2026-01-01", "to": "2026-08-31"},
  "groups": [
    {
      "code": "1",
      "name": "Tài sản",
      "debit_opening": 500000000,
      "credit_opening": 0,
      "debit_period": 200000000,
      "credit_period": 50000000,
      "debit_closing": 650000000,
      "credit_closing": 0,
      "accounts": [...]
    }
  ],
  "totals": {
    "debit_opening": 500000000,
    "credit_opening": 500000000,
    "debit_period": 300000000,
    "credit_period": 300000000,
    "debit_closing": 650000000,
    "credit_closing": 650000000
  }
}
```

### 2.4 Balance Checks (TT99 Art. 14)
```
Total debit_opening == Total credit_opening
Total debit_period == Total credit_period
Total debit_closing == Total credit_closing
```

### 2.5 Acceptance Criteria
- [ ] API returns trial balance grouped by account_type
- [ ] Each group shows opening, period, closing balances
- [ ] Balance checks pass
- [ ] Supports date range filtering
- [ ] Accounts with zero balance can be optionally excluded

---

## 3. Statement of Financial Position (B01-DN)

### 3.1 Requirement
Generate Balance Sheet per TT99 Appendix IV.

### 3.2 Structure

```
A. SHORT-TERM ASSETS (100-180)
   I.   Cash and cash equivalents (111, 112, 113)
   II.  Short-term financial investments (121, 128)
   III. Short-term receivables (131, 132, 133, 138)
   IV.  Inventories (151, 152, 154, 155, 156)
   V.   Other short-term assets (180)

B. LONG-TERM ASSETS (200-260)
   I.   Long-term financial investments (211, 212, 219)
   II.  Fixed assets (211x, 214, 213, 217, 215)
   III. Investment property (230)
   IV.  Long-term prepayments (240)
   V.   Deferred income tax assets (250)
   VI.  Other long-term assets (260)

TOTAL ASSETS (280)

C. LIABILITIES (300-330)
   I.   Short-term liabilities (341, 331, 332, 333, 338)
   II.  Long-term liabilities (341x, 343x, 336)

D. OWNERS' EQUITY (400)
   1. Contributed capital (411)
   2. Share premium (412)
   3. Revaluation surplus (413)
   4. Retained earnings (421 = 4211 + 4212)

TOTAL LIABILITIES + EQUITY (280)
```

### 3.3 Balance Check
```
Total Assets (280) == Total Liabilities (C) + Owners' Equity (D)
```

### 3.4 Data Source
Trial Balance → classify accounts → aggregate by section.

### 3.5 Acceptance Criteria
- [ ] Total Assets = Total Liabilities + Equity
- [ ] Current/Non-current classification correct
- [ ] Fixed assets show net book value (cost - accumulated depreciation)
- [ ] Retained earnings reflects year-to-date net income + prior year
- [ ] Comparative columns (current year vs prior year)

---

## 4. Statement of Profit or Loss (B02-DN)

### 4.1 Requirement
Generate Income Statement per TT99 Appendix IV.

### 4.2 Structure

```
A. Net Revenue (511 - 521)                              [510]
B. Cost of Goods Sold (632)                              [632]

GROSS PROFIT (A - B)

C. Sales Expenses (641)                                  [641]
D. Admin Expenses (642)                                  [642]

OPERATING PROFIT (A - B - C - D)

E. Financial Income (515)                                [515]
F. Financial Expenses (635)                              [635]

NET FINANCIAL INCOME/EXPENSE (E - F)

G. Other Income (711)                                    [711]
H. Other Expenses (811)                                  [811]

PROFIT BEFORE TAX

I. Income Tax Expense (821)                              [821]

NET PROFIT FOR THE PERIOD
```

### 4.3 Data Source
Trial Balance → filter 4xx/5xx accounts → group by revenue type.

### 4.4 Acceptance Criteria
- [ ] Revenue = sum(511) - sum(521)
- [ ] COGS = sum(632)
- [ ] Gross Profit = Revenue - COGS
- [ ] Operating Profit = Gross Profit - Sales Exp - Admin Exp
- [ ] Pre-tax Profit = Operating Profit + Net Financial + Other
- [ ] Net Profit = Pre-tax Profit - Tax
- [ ] Comparative columns

---

## 5. Cash Flow Statement (B03-DN)

### 5.1 Requirement
Generate Cash Flow Statement using direct method.

### 5.2 Structure

```
A. OPERATING ACTIVITIES
   1. Cash received from customers
   2. Cash paid to suppliers
   3. Cash paid to employees
   4. Cash paid for income tax

B. INVESTING ACTIVITIES
   1. Purchase of fixed assets
   2. Proceeds from sale of fixed assets

C. FINANCING ACTIVITIES
   1. Proceeds from borrowings
   2. Repayment of borrowings
   3. Capital contributions
   4. Dividends paid

NET INCREASE/DECREASE (A + B + C)
Cash at beginning of period
Cash at end of period = B01 Code 110
```

### 5.3 Data Source
Requires `cash_flow_class` on voucher lines. Each line tagged: OPERATING/INVESTING/FINANCING.

### 5.4 Acceptance Criteria
- [ ] Ending cash matches B01-DN Code 110
- [ ] All three activity sections populated
- [ ] Direct method used (not indirect)

---

## 6. Retained Earnings Engine

### 6.1 Requirement
Track retained earnings across fiscal years. Generate year-end closing entries.

### 6.2 Data Model

```python
@dataclass
class RetainedEarnings:
    company_id: UUID
    fiscal_year_id: UUID
    opening_balance: Decimal    # From prior year 4211
    net_income: Decimal         # Sum of 911 (revenue - expenses)
    dividends: Decimal          # Declared dividends
    closing_balance: Decimal    # opening + net_income - dividends
    checksum: str
```

### 6.3 Year-End Close Entry

**Profit case:**
```
Dr. 911 (Xác định KQKD)           XXX
    Cr. 4212 (LNST chưa PH năm nay)  XXX
```

**Loss case:**
```
Dr. 4212 (LNST chưa PH năm nay)   XXX
    Cr. 911 (Xác định KQKD)           XXX
```

**New year start:**
```
Dr. 4212 (current year)           XXX
    Cr. 4211 (prior year)             XXX
```

### 6.4 Acceptance Criteria
- [ ] Year-end close calculates net income from all 4xx/5xx accounts
- [ ] Closing entry zeros out revenue/expense accounts
- [ ] Retained earnings balance carries forward to next year
- [ ] Dividends deducted from retained earnings
- [ ] Can only close a fiscal year once (idempotent)

---

## 7. Month-End Close Checklist

### 7.1 Automated Steps

| Step | Entry | Debit | Credit | Status |
|---|---|---|---|---|
| 1 | Depreciate fixed assets | 154/622/641/642 | 214 | ✅ Done (fixed_assets brick) |
| 2 | Allocate CCDC | 154/641/642 | 242 | ✅ Done (tools_equipment brick) |
| 3 | Transfer revenue to 911 | 911 | 511/515/711 | ❌ Need to build |
| 4 | Transfer costs to 911 | 632/635/641/642/811 | 911 | ❌ Need to build |
| 5 | Calculate CIT provision | 8211 | 3334 | ❌ Need to build |

### 7.2 Manual Steps (User Responsibility)

1. Bank reconciliation (all accounts)
2. Receivables aging review
3. Inventory count + reconciliation
4. Fixed asset physical count
5. Foreign currency revaluation (all monetary items)

### 7.3 Acceptance Criteria
- [ ] Close button triggers steps 1-5 in sequence
- [ ] Each step generates a journal entry (voucher)
- [ ] Step completion is logged
- [ ] Cannot close period if any step fails
- [ ] Period status changes to LOCKED after close

---

## 8. Report Template Engine

### 8.1 Architecture (Tryton pattern)

```
report_template
  └── report_template_line (each row: name, code, formula, level)
        └── maps to account codes or calculation

report_instance (calculated snapshot)
  └── report_instance_line (computed values)
```

### 8.2 Template Line Types

| Type | Formula Example | Description |
|---|---|---|
| ACCOUNT_AGGREGATE | `sum(111, 112, 113)` | Sum of specified accounts |
| FORMULA | `line_a - line_b` | Arithmetic on other lines |
| HEADER | — | Section header, no value |
| TOTAL | `sum_children` | Sum of child lines |

### 8.3 Pre-Built Templates

| Template | Code | Form |
|---|---|---|
| Trial Balance | S06-DN | TT99 Appendix III |
| Statement of Financial Position | B01-DN | TT99 Appendix IV |
| Statement of Profit or Loss | B02-DN | TT99 Appendix IV |
| Cash Flow Statement | B03-DN | TT99 Appendix IV |

### 8.4 Acceptance Criteria
- [ ] Templates stored in DB, not hardcoded
- [ ] Each line has formula + account mapping
- [ ] "Calculate" button triggers computation
- [ ] Results cached in `report_instance_line`
- [ ] Recalculation clears prior values

---

## 9. API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/reports/trial-balance` | Trial balance (existing, extend) |
| GET | `/api/v1/reports/balance-sheet` | Statement of Financial Position |
| GET | `/api/v1/reports/income-statement` | Statement of Profit or Loss |
| GET | `/api/v1/reports/cash-flow` | Cash Flow Statement |
| POST | `/api/v1/reports/close-month` | Execute month-end close |
| POST | `/api/v1/reports/close-year` | Execute year-end close |
| GET | `/api/v1/reports/retained-earnings` | Retained earnings summary |
