# Financial Statements — Use Cases

**Module:** Financial Statements
**Date:** 2026-08-28

---

## UC-01: View Trial Balance

**Actor:** Accountant
**Precondition:** Posted vouchers exist in the ledger

**Happy Path:**
1. Accountant navigates to Reports → Trial Balance
2. Selects fiscal year and period (month/quarter/year)
3. System queries all posted voucher lines in period
4. System aggregates by account code
5. System groups by account type (Assets/Liabilities/Equity/Revenue/Expense)
6. System displays: Opening balance, Period transactions, Closing balance
7. System validates: Total debit = Total credit

**Alternative Paths:**
- UC-01a: Accountant filters by specific account group → shows only that group
- UC-01b: Accountant selects "Include zero balances" → accounts with 0 balance shown
- UC-01c: Accountant selects "Summary only" → shows only group totals, no detail accounts

**Exception Paths:**
- UC-01-E1: No posted vouchers in period → "No data for selected period"
- UC-01-E2: Balance check fails → Warning displayed, but report still shown

---

## UC-02: View Balance Sheet (B01-DN)

**Actor:** Accountant, Chief Accountant
**Precondition:** Trial balance is balanced for the period

**Happy Path:**
1. Accountant navigates to Reports → Balance Sheet
2. Selects "As of" date
3. System generates trial balance as of that date
4. System classifies accounts into: Assets, Liabilities, Equity
5. System aggregates into TT99 B01-DN format
6. System calculates: Total Assets, Total Liabilities, Total Equity
7. System validates: Assets = Liabilities + Equity
8. System displays with comparative prior year column

**Alternative Paths:**
- UC-02a: Accountant selects "Monthly" → shows 12 monthly columns
- UC-02b: Accountant selects "Quarterly" → shows 4 quarterly columns
- UC-02c: Accountant drills down on a line → shows underlying accounts

**Exception Paths:**
- UC-02-E1: Assets ≠ Liabilities + Equity → Error: "Balance sheet does not balance"
- UC-02-E2: Retained earnings not calculated → Warning: "Run year-end close first"
- UC-02-E3: No data for prior year → Prior year column shows zeros

---

## UC-03: View Income Statement (B02-DN)

**Actor:** Accountant, Chief Accountant
**Precondition:** Posted vouchers exist in the period

**Happy Path:**
1. Accountant navigates to Reports → Income Statement
2. Selects start and end date
3. System generates trial balance for the period
4. System classifies: Revenue (511-521), COGS (632), Expenses (641, 642), Financial (515, 635), Other (711, 811), Tax (821)
5. System calculates: Gross Profit, Operating Profit, Pre-tax Profit, Net Profit
6. System displays with comparative prior period column

**Alternative Paths:**
- UC-03a: Accountant selects "By month" → shows monthly columns
- UC-03b: Accountant selects "By quarter" → shows quarterly columns
- UC-03c: Accountant drills down on revenue → shows individual revenue accounts

**Exception Paths:**
- UC-03-E1: No revenue in period → Revenue shows 0, report still generated
- UC-03-E2: Tax expense not calculated → Warning: "CIT provision not run"

---

## UC-04: View Cash Flow Statement (B03-DN)

**Actor:** Accountant, Chief Accountant
**Precondition:** Voucher lines have cash_flow_class tags

**Happy Path:**
1. Accountant navigates to Reports → Cash Flow Statement
2. Selects start and end date
3. System queries voucher lines with cash_flow_class
4. System groups: Operating, Investing, Financing
5. System calculates: Net cash from each activity
6. System validates: Ending cash = B01 Cash line (110)

**Alternative Paths:**
- UC-04a: No cash flow tags → Warning: "Cash flow tags missing on some vouchers"
- UC-04b: Accountant selects "Indirect method" → starts from net profit

**Exception Paths:**
- UC-04-E1: Ending cash ≠ B01 Cash → Error: "Cash flow does not reconcile"
- UC-04-E2: No bank/cash vouchers → All sections show 0

---

## UC-05: Execute Month-End Close

**Actor:** Chief Accountant
**Precondition:** All transactions for the month are posted

**Happy Path:**
1. Chief Accountant navigates to Period-End → Month-End Close
2. Selects month to close
3. System runs close checklist:
   a. Depreciate fixed assets → generates voucher
   b. Allocate CCDC → generates voucher
   c. Transfer revenue to 911 → generates voucher
   d. Transfer costs to 911 → generates voucher
   e. Calculate CIT provision → generates voucher
4. System locks the period
5. System displays summary of all entries generated

**Alternative Paths:**
- UC-05a: Accountant skips a step → Step marked as "skipped", next step runs
- UC-05b: Accountant wants to reverse close → Unlock period, reverse vouchers

**Exception Paths:**
- UC-05-E1: Fixed asset depreciation fails → "Asset #X has no useful life remaining"
- UC-05-E2: Period already locked → "Period is already closed"
- UC-05-E3: Unposted vouchers exist → "Post all vouchers before closing"
- UC-05-E4: Depreciation calculation error → Stop, show error, do not lock

---

## UC-06: Execute Year-End Close

**Actor:** Chief Accountant
**Precondition:** All months in the fiscal year are closed

**Happy Path:**
1. Chief Accountant navigates to Period-End → Year-End Close
2. System verifies all 12 months are locked
3. System calculates net income: sum(911)
4. System generates closing entry:
   - Profit: Dr. 911 / Cr. 4212
   - Loss: Dr. 4212 / Cr. 911
5. System transfers 4212 → 4211 (current year → prior year)
6. System creates next fiscal year periods
7. System displays retained earnings summary

**Exception Paths:**
- UC-06-E1: Not all months closed → "Close all months before year-end"
- UC-06-E2: Year already closed → "Fiscal year already closed"
- UC-06-E3: Net income calculation error → Show error, do not close

---

## UC-07: View Retained Earnings

**Actor:** Accountant
**Precondition:** At least one fiscal year with data

**Happy Path:**
1. Accountant navigates to Reports → Retained Earnings
2. Selects fiscal year
3. System displays:
   - Opening balance (from prior year 4211)
   - Net income for the year
   - Dividends declared
   - Closing balance (4211 + 4212)

**Exception Paths:**
- UC-07-E1: No prior year data → Opening balance = 0

---

## UC-08: Recalculate Report

**Actor:** Accountant
**Precondition:** Report instance exists

**Happy Path:**
1. Accountant views a report (B01/B02/B03)
2. Clicks "Recalculate"
3. System re-queries trial balance
4. System re-aggregates values
5. System updates report instance
6. System displays updated values

**Exception Paths:**
- UC-08-E1: New vouchers posted since last calc → Values update correctly
