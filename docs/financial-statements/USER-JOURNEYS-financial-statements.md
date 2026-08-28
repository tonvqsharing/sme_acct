# Financial Statements — User Journeys

**Module:** Financial Statements
**Date:** 2026-08-28

---

## Journey 1: First-Time Setup (New Company)

```
User: Accountant
Goal: Set up reporting infrastructure for a new company

Step 1: Company created (existing flow)
    ↓
Step 2: COA created with TT99-compliant codes
    ↓
Step 3: System auto-classifies accounts by first digit
    → 1xx = Asset, 2xx = Liability, 3xx = Equity, 4xx = Revenue, 5xx = Expense
    ↓
Step 4: Fiscal year created (existing flow)
    ↓
Step 5: User navigates to Reports → sees empty Trial Balance
    ↓
Step 6: User posts first voucher → Trial Balance populates
    ↓
Step 7: User generates first Balance Sheet → may show errors until sufficient data
    ↓
Done: Reporting infrastructure ready
```

**Touchpoints:** Reports menu, Trial Balance page, Balance Sheet page

---

## Journey 2: Monthly Reporting (Recurring)

```
User: Accountant
Goal: Close month and produce financial reports

Step 1: Post all outstanding invoices and vouchers
    ↓
Step 2: Run bank reconciliation
    ↓
Step 3: Navigate to Reports → Trial Balance
    → Review: are debits = credits? Any unexpected balances?
    ↓
Step 4: Click "Generate Balance Sheet"
    → Check: Total Assets == Liabilities + Equity?
    ↓
Step 5: Click "Generate Income Statement"
    → Check: Revenue - COGS - Expenses = Net Profit?
    ↓
Step 6: Click "Generate Cash Flow" (if cash flow tags exist)
    → Check: Ending cash == Balance Sheet Code 110?
    ↓
Step 7: Cross-check: Income Statement Revenue ≈ VAT declaration amount
    ↓
Step 8: Navigate to Period-End → Month-End Close
    → Click "Close Month" → system runs depreciation, allocations, transfers
    ↓
Step 9: Period locked → all reports finalized for the month
    ↓
Done: Month closed, reports ready for management review
```

**Touchpoints:** Trial Balance, B01-DN, B02-DN, B03-DN, Period-End Close

---

## Journey 3: Year-End Reporting (Annual)

```
User: Chief Accountant
Goal: Close fiscal year and produce annual financial statements

Step 1: Complete all 12 monthly closes
    ↓
Step 2: Navigate to Period-End → Year-End Close
    ↓
Step 3: System verifies all months are locked
    ↓
Step 4: System calculates net income from all 4xx/5xx accounts
    ↓
Step 5: System generates closing entry:
    → Dr. 911 / Cr. 4212 (profit) or reverse (loss)
    → Dr. 4212 / Cr. 4211 (transfer to prior year)
    ↓
Step 6: System creates next fiscal year periods
    ↓
Step 7: Generate annual Balance Sheet (B01-DN)
    → Two columns: current year, prior year
    ↓
Step 8: Generate annual Income Statement (B02-DN)
    → Two columns: current year, prior year
    ↓
Step 9: Generate annual Cash Flow (B03-DN)
    → Three sections: Operating, Investing, Financing
    ↓
Step 10: Prepare Notes to Financial Statements (B09-DN)
    → Semi-manual: accounting policies, related party transactions, etc.
    ↓
Step 11: Submit to tax authority (within 90 days of year-end)
    ↓
Done: Annual financial statements completed and filed
```

**Touchpoints:** Year-End Close, B01-DN, B02-DN, B03-DN, Retained Earnings

---

## Journey 4: Drill-Down Investigation

```
User: Auditor / Chief Accountant
Goal: Investigate an unexpected number on a financial statement

Step 1: View Balance Sheet → see "Other long-term assets" is unusually high
    ↓
Step 2: Click on line → drill-down shows underlying accounts
    ↓
Step 3: See Account 260 (Other long-term assets) has large balance
    ↓
Step 4: Click on Account 260 → see all voucher lines
    ↓
Step 5: See individual transactions that make up the balance
    ↓
Step 6: Identify the problematic voucher
    ↓
Step 7: Navigate to Voucher → view/edit/correct
    ↓
Done: Issue identified and corrected
```

**Touchpoints:** Balance Sheet, Account detail, Voucher detail

---

## Journey 5: Comparative Analysis

```
User: CFO / Management
Goal: Compare current year performance vs prior year

Step 1: Navigate to Reports → Income Statement
    ↓
Step 2: Select "Annual" view with prior year column
    ↓
Step 3: See side-by-side comparison:
    → Revenue: current vs prior → +15% growth
    → COGS: current vs prior → +12% (improving margin)
    → Net Profit: current vs prior → +20%
    ↓
Step 4: Click on Revenue line → see monthly breakdown
    ↓
Step 5: Identify seasonal patterns
    ↓
Step 6: Export to Excel for further analysis
    ↓
Done: Management informed of financial performance trends
```

**Touchpoints:** Income Statement, Balance Sheet, Excel export
