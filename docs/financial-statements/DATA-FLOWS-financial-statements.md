# Financial Statements — Data Flows, Processes, Rules

**Module:** Financial Statements
**Date:** 2026-08-28

---

## 1. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Invoices │  │ Purchase │  │  Bank/   │  │  Fixed   │       │
│  │ (sales)  │  │ Invoices │  │  Cash    │  │  Assets  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │             │
│       ▼              ▼              ▼              ▼             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              VOUCHER / JOURNAL ENTRY                     │    │
│  │  (debit, credit, account_code, cash_flow_class)         │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    GENERAL LEDGER                         │   │
│  │  Aggregates voucher lines by account_code + period       │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                     │
│              ┌────────────┼────────────┐                        │
│              ▼            ▼            ▼                        │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │ Trial Balance │ │ Account Type  │ │ Cash Flow     │         │
│  │ (S06-DN)     │ │ Classifier    │ │ Classifier    │         │
│  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘         │
│          │                 │                 │                   │
│          ▼                 ▼                 ▼                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              REPORT COMPUTATION ENGINE                    │   │
│  │  Template lines + formulas → aggregated values           │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       OUTPUT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │ Balance Sheet │ │ Income Stmt   │ │ Cash Flow     │         │
│  │ (B01-DN)     │ │ (B02-DN)     │ │ (B03-DN)     │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
│                                                                 │
│  ┌───────────────┐ ┌───────────────┐                           │
│  │ Retained      │ │ Period-End    │                           │
│  │ Earnings      │ │ Close         │                           │
│  └───────────────┘ └───────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Data Flows

### 2.1 Trial Balance → All Reports

```
VoucherModel (POSTED)
    ↓
SQLAlchemyLedgerSource.get_posted_lines(company_id, from_date, to_date)
    ↓
LedgerService.trial_balance()
    ↓
Aggregated by account_code: {debit, credit, net_debit}
    ↓
AccountTypeClassifier.classify(account_code) → {ASSET|LIABILITY|EQUITY|REVENUE|EXPENSE}
    ↓
ReportEngine.compute(template, trial_balance) → report_instance_lines
```

### 2.2 Balance Sheet Data Flow

```
Trial Balance
    ↓
Filter: account_type IN (ASSET, LIABILITY, EQUITY)
    ↓
Group by TT99 sections:
    Assets: 100-180 (short-term) + 200-260 (long-term)
    Liabilities: 300-330
    Equity: 400
    ↓
Aggregate: section_total = sum(account_closing_balance)
    ↓
Validate: Total Assets == Total Liabilities + Total Equity
    ↓
Output: B01-DN with current + prior year columns
```

### 2.3 Income Statement Data Flow

```
Trial Balance
    ↓
Filter: account_type IN (REVENUE, EXPENSE)
    ↓
Group by TT99 sections:
    Revenue: 511 - 521 (net revenue)
    COGS: 632
    Sales Expenses: 641
    Admin Expenses: 642
    Financial Income: 515
    Financial Expenses: 635
    Other Income: 711
    Other Expenses: 811
    Tax: 821
    ↓
Calculate:
    Gross Profit = Revenue - COGS
    Operating Profit = Gross Profit - Sales Exp - Admin Exp
    Pre-tax = Operating + (Financial Income - Financial Exp) + Other Inc - Other Exp
    Net Profit = Pre-tax - Tax
    ↓
Output: B02-DN with current + prior period columns
```

### 2.4 Cash Flow Data Flow

```
VoucherLines WHERE cash_flow_class IS NOT NULL
    ↓
Group by activity:
    Operating: lines tagged OPERATING
    Investing: lines tagged INVESTING
    Financing: lines tagged FINANCING
    ↓
For each activity:
    Cash In = sum(credit) WHERE account_type = ASSET
    Cash Out = sum(debit) WHERE account_type = ASSET
    Net = Cash In - Cash Out
    ↓
Validate: Ending Cash (sum of all bank/cash accounts) == B01 Code 110
    ↓
Output: B03-DN
```

### 2.5 Retained Earnings Data Flow

```
Year-End Close Triggered
    ↓
Sum Revenue accounts (4xx): total_credit
Sum Expense accounts (5xx): total_debit
    ↓
Net Income = total_credit - total_debit
    ↓
Generate closing voucher:
    If profit:  Dr. 911 / Cr. 4212
    If loss:    Dr. 4212 / Cr. 911
    ↓
Transfer: Dr. 4212 / Cr. 4211 (current → prior)
    ↓
Update RetainedEarnings record:
    opening = prior year closing
    net_income = calculated
    closing = opening + net_income - dividends
```

---

## 3. Business Rules

### 3.1 Trial Balance Rules

| Rule | Code | Description |
|---|---|---|
| TB-01 | Balance check | Total debit == Total credit for opening, period, and closing |
| TB-02 | Period gate | Only POSTED vouchers included |
| TB-03 | Date range | from_date <= to_date |
| TB-04 | Company scope | Only lines belonging to the company |

### 3.2 Balance Sheet Rules

| Rule | Code | Description |
|---|---|---|
| BS-01 | Balance equation | Total Assets == Total Liabilities + Equity |
| BS-02 | Current/Non-current | Assets/Liabilities split at 12-month threshold |
| BS-03 | Net book value | Fixed assets shown as cost - accumulated depreciation |
| BS-04 | Retained earnings | Must reflect current year net income |
| BS-05 | Comparative | Prior year column required |

### 3.3 Income Statement Rules

| Rule | Code | Description |
|---|---|---|
| IS-01 | Net revenue | = Revenue (511) - Sales returns (521) |
| IS-02 | Gross profit | = Net Revenue - COGS |
| IS-03 | Operating profit | = Gross Profit - Sales Exp - Admin Exp |
| IS-04 | Pre-tax profit | = Operating + Net Financial + Other Income - Other Expenses |
| IS-05 | Net profit | = Pre-tax Profit - Income Tax |

### 3.4 Cash Flow Rules

| Rule | Code | Description |
|---|---|---|
| CF-01 | Reconciliation | Ending cash must equal B01 Code 110 |
| CF-02 | Activity tagging | Every cash/bank voucher line must have cash_flow_class |
| CF-03 | Three activities | Must show Operating, Investing, Financing separately |

### 3.5 Period-End Close Rules

| Rule | Code | Description |
|---|---|---|
| PE-01 | Sequential | Month-end must complete before next month can start |
| PE-02 | Posted only | All vouchers in period must be POSTED |
| PE-03 | Idempotent | Closing entries generated only once per period |
| PE-04 | Locked | Closed period cannot accept new vouchers |
| PE-05 | Year-end gate | All 12 months must be closed before year-end close |

### 3.6 Retained Earnings Rules

| Rule | Code | Description |
|---|---|---|
| RE-01 | Carry forward | Prior year balance carries to current year |
| RE-02 | Dividends | Dividends declared reduce retained earnings |
| RE-03 | Net income | = Sum of all revenue - Sum of all expenses |
| RE-04 | Account 4211 | Prior year undistributed |
| RE-05 | Account 4212 | Current year undistributed |

---

## 4. Workflows

### 4.1 Monthly Reporting Workflow

```
1. Post all transactions for the month
        ↓
2. Run bank reconciliation
        ↓
3. Run fixed asset depreciation (auto)
        ↓
4. Run CCDC allocation (auto)
        ↓
5. Review Trial Balance
        ↓
6. Generate Balance Sheet
        ↓
7. Generate Income Statement
        ↓
8. Generate Cash Flow Statement
        ↓
9. Cross-check: Revenue on B02 ≈ VAT declaration revenue
        ↓
10. Month-End Close (locks period)
```

### 4.2 Annual Reporting Workflow

```
1. Complete all 12 monthly closes
        ↓
2. Run year-end close
        ↓
3. Generate annual Balance Sheet (B01-DN)
        ↓
4. Generate annual Income Statement (B02-DN)
        ↓
5. Generate annual Cash Flow (B03-DN)
        ↓
6. Prepare Notes to FS (B09-DN) — manual
        ↓
7. Submit to tax authority (within 90 days)
        ↓
8. Create next fiscal year periods
```

---

## 5. Exception Handling Matrix

| Exception | Impact | Recovery |
|---|---|---|
| Trial balance doesn't balance | All reports invalid | Fix unbalanced vouchers |
| Balance sheet doesn't balance | Report rejected by tax authority | Check retained earnings, fix account classification |
| Cash flow doesn't reconcile | Report incomplete | Check cash_flow_class tags on vouchers |
| Year-end close fails | Cannot create next FY | Fix underlying data, retry |
| Period locked with errors | Cannot reverse | Must unlock period (admin action) |
| Missing account_type | Report sections empty | Run account classification migration |
