# Financial Statements Module — BRD

**Module:** Financial Statements (Báo cáo tài chính)
**Version:** 1.0
**Date:** 2026-08-28
**Status:** Spec phase
**Author:** BA Lead + Chief Accountant (20+ years)

---

## Executive Summary

This module produces the four mandatory financial statements for Vietnamese SMEs under TT99/2025/TT-BTC. Currently the system has ledger data (vouchers, COA, invoices, fixed assets) but NO report generation capability. This BRD defines what must be built.

## Regulatory Basis

| Document | Scope |
|---|---|
| TT99/2025/TT-BTC (eff 01/01/2026) | Chart of accounts, journals, FS format |
| TT133/2016/TT-BTC | Simplified regime for SMEs (still in force) |
| Luật Kế toán 2015 Art. 11 | 10-year data retention |
| NĐ 42/2016/NĐ-CP | Detailed guidance on Accounting Law |
| VAS (26 standards) | Vietnamese Accounting Standards |

## Scope

### In Scope (Phase 1 — MVP)
1. Trial Balance (S06-DN) — with account group subtotals
2. Statement of Financial Position (B01-DN) — Balance Sheet
3. Statement of Profit or Loss (B02-DN) — Income Statement
4. Cash Flow Statement (B03-DN) — direct method preferred
5. Account type/classification engine
6. Retained earnings calculation
7. Year-end closing entries
8. Month-end closing checklist
9. Comparative period support

### Deferred to Phase 2
1. Notes to Financial Statements (B09-DN) — semi-manual
2. Consolidated financial statements (multi-company)
3. IFRS template support
4. Report PDF export with Vietnamese formatting
5. Audit trail for report changes
6. Budget vs Actual comparison reports

### Out of Scope
1. Tax declaration forms (already done: VAT 01/GTGT)
2. Payroll reports
3. Inventory valuation reports

## Production Readiness Assessment

### Current State: ❌ NOT PROD-READY

| Requirement | Status | Gap |
|---|---|---|
| Trial Balance | ⚠️ Partial | No account_type classification, no BS/IS grouping |
| Balance Sheet | ❌ Missing | No account_type, no retained earnings, no report |
| Income Statement | ❌ Missing | No account_type, no report |
| Cash Flow Statement | ❌ Missing | No cash flow tagging on vouchers |
| Year-end Close | ❌ Missing | No closing entries logic |
| Retained Earnings | ❌ Missing | No RE model or calculation |

### Key Points for PROD Readiness

1. **Account Type Classification** (CRITICAL)
   - COA `Account` model needs `account_type` field (ASSET/LIABILITY/EQUITY/REVENUE/EXPENSE)
   - Auto-classify based on first digit: 1xx→ASSET, 2xx→LIABILITY, 3xx→EQUITY, 4xx→REVENUE, 5xx→EXPENSE
   - Must support custom Level 2/3 accounts while preserving Level 1 classification

2. **Retained Earnings Engine** (CRITICAL)
   - Year-end close: sum all revenue (4xx) and expense (5xx) accounts → net income
   - Transfer to `4212` (current year) → `4211` (prior year) at year start
   - Entry: Dr. 911 / Cr. 4212 (profit) or reverse (loss)
   - Must track dividends declared

3. **Cash Flow Tagging** (HIGH)
   - Every voucher line needs `cash_flow_class` (OPERATING/INVESTING/FINANCING)
   - Direct method: tag cash received from customers, paid to suppliers, etc.
   - This is a SCHEMA CHANGE on voucher lines

4. **Report Template Engine** (HIGH)
   - Follow Tryton pattern: template lines with formulas
   - Support VAS-99 format now, IFRS templates later
   - Each report line maps to account codes or calculation formula

5. **Comparative Periods** (MEDIUM)
   - B01-DN and B02-DN require current + prior year columns
   - Must query same period from prior fiscal year

## Success Criteria

- [ ] Trial Balance shows correct subtotals by account group (Assets/Liabilities/Equity/Revenue/Expense)
- [ ] Balance Sheet balances: Total Assets = Total Liabilities + Equity
- [ ] Income Statement shows: Revenue - COGS - Expenses = Net Profit
- [ ] Cash Flow Statement reconciles: ending cash = B01 cash line
- [ ] Year-end closing entries correctly zero P&L accounts and update retained earnings
- [ ] All reports pass the "accountant's gut check" — numbers make sense
- [ ] VAT declaration data matches Income Statement revenue (for 01/GTGT cross-check)

## Open Questions

1. Should cash flow tagging be mandatory on all vouchers or optional? (Recommendation: mandatory for cash/bank vouchers only)
2. Should we support both direct and indirect cash flow methods? (Recommendation: direct only for MVP)
3. Should report templates be configurable per company or global? (Recommendation: global with company-level overrides)
4. How to handle multi-currency in reports? (VND statutory, USD for reference?)
