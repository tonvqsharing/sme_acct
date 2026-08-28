# Financial Statements — Implementation Plan

**Date:** 2026-08-28
**Status:** Ready for implementation
**Estimated effort:** 4-6 sprints (2-3 weeks)

---

## Phase 1: Foundation (Prerequisites)

### Sprint 1: Account Type Classification

| Ticket | Description | Depends |
|---|---|---|
| FS-001 | Add `account_type` field to `Account` domain | — |
| FS-002 | Auto-classify accounts by first digit in `create_account()` | FS-001 |
| FS-003 | Migration: retroactively classify existing accounts | FS-001 |
| FS-004 | `AccountTypeClassifier` service (classify + validate) | FS-001 |
| FS-005 | Unit tests for classification engine | FS-004 |
| FS-006 | Integration tests for account creation with auto-type | FS-002 |

### Sprint 2: Cash Flow Tagging

| Ticket | Description | Depends |
|---|---|---|
| FS-010 | Add `cash_flow_class` enum (OPERATING/INVESTING/FINANCING) | — |
| FS-011 | Add `cash_flow_class` to voucher line model | FS-010 |
| FS-012 | Migration: add column to existing voucher lines | FS-011 |
| FS-013 | Validation: cash/bank vouchers must have cash_flow_class | FS-011 |
| FS-014 | Unit tests for cash flow classification | FS-010 |

---

## Phase 2: Report Template Engine

### Sprint 3: Template Storage

| Ticket | Description | Depends |
|---|---|---|
| FS-020 | `ReportTemplate` + `ReportTemplateLine` domain models | — |
| FS-021 | `ReportTemplateRepository` port (CRUD) | FS-020 |
| FS-022 | SQLAlchemy storage for templates | FS-021 |
| FS-023 | Template seeding: B01-DN, B02-DN, B03-DN, S06-DN | FS-022 |
| FS-024 | Unit tests for template CRUD | FS-022 |
| FS-025 | Alembic migration for template tables | FS-022 |

### Sprint 4: Report Computation Engine

| Ticket | Description | Depends |
|---|---|---|
| FS-030 | `ReportEngine` service: compute template lines from trial balance | FS-004 |
| FS-031 | `ACCOUNT_AGGREGATE` line type (sum of account codes) | FS-030 |
| FS-032 | `FORMULA` line type (arithmetic on other lines) | FS-031 |
| FS-033 | `TOTAL` line type (sum of children) | FS-032 |
| FS-034 | `ReportInstance` + `ReportInstanceLine` models | FS-030 |
| FS-035 | Store computed results in DB | FS-034 |
| FS-036 | Unit tests for computation engine | FS-030 |

---

## Phase 3: Financial Statements

### Sprint 5: Trial Balance + Balance Sheet

| Ticket | Description | Depends |
|---|---|---|
| FS-040 | Extend `LedgerService.trial_balance()` to include account_type grouping | FS-004 |
| FS-041 | API: `GET /api/v1/reports/trial-balance` (enhanced) | FS-040 |
| FS-042 | B01-DN template lines (TT99 format) | FS-023 |
| FS-043 | Balance Sheet computation service | FS-030, FS-042 |
| FS-044 | API: `GET /api/v1/reports/balance-sheet` | FS-043 |
| FS-045 | Balance validation (Assets = Liabilities + Equity) | FS-043 |
| FS-046 | Unit + integration tests | FS-044 |

### Sprint 6: Income Statement + Cash Flow

| Ticket | Description | Depends |
|---|---|---|
| FS-050 | B02-DN template lines (TT99 format) | FS-023 |
| FS-051 | Income Statement computation service | FS-030, FS-050 |
| FS-052 | API: `GET /api/v1/reports/income-statement` | FS-051 |
| FS-053 | B03-DN template lines (TT99 format) | FS-011, FS-023 |
| FS-054 | Cash Flow computation service | FS-030, FS-053 |
| FS-055 | API: `GET /api/v1/reports/cash-flow` | FS-054 |
| FS-056 | Cash flow reconciliation (ending cash = B01 Code 110) | FS-054 |
| FS-057 | Unit + integration tests | FS-055 |

---

## Phase 4: Period-End Close

### Sprint 7: Month-End Close

| Ticket | Description | Depends |
|---|---|---|
| FS-060 | `PeriodCloseService` domain: close logic | — |
| FS-061 | Revenue transfer to 911 (month-end) | FS-060 |
| FS-062 | Expense transfer to 911 (month-end) | FS-061 |
| FS-063 | CIT provision calculation | FS-062 |
| FS-064 | Period lock after close | FS-063 |
| FS-065 | API: `POST /api/v1/reports/close-month` | FS-064 |
| FS-066 | Unit + integration tests | FS-065 |

### Sprint 8: Year-End Close + Retained Earnings

| Ticket | Description | Depends |
|---|---|---|
| FS-070 | `RetainedEarnings` domain model | — |
| FS-071 | Year-end close: calculate net income | FS-070, FS-064 |
| FS-072 | Generate closing entry (Dr. 911 / Cr. 4212 or reverse) | FS-071 |
| FS-073 | Transfer 4212 → 4211 (current → prior year) | FS-072 |
| FS-074 | Create next fiscal year periods | FS-073 |
| FS-075 | API: `POST /api/v1/reports/close-year` | FS-074 |
| FS-076 | API: `GET /api/v1/reports/retained-earnings` | FS-070 |
| FS-077 | Unit + integration tests | FS-075 |

---

## Phase 5: Polish

### Sprint 9: Comparative Periods + Export

| Ticket | Description | Depends |
|---|---|---|
| FS-080 | Prior year column support for B01-DN, B02-DN | FS-043, FS-051 |
| FS-081 | Monthly breakdown view | FS-030 |
| FS-082 | PDF export (Vietnamese formatting) | FS-043 |
| FS-083 | Excel export | FS-043 |
| FS-084 | Report caching (invalidated on new voucher) | FS-035 |

---

## Dependencies on Existing Bricks

| Brick | Dependency |
|---|---|
| `ledger` | Trial balance source (existing) |
| `coa` | Account model (add `account_type` field) |
| `fiscal_year_period` | Period status (LOCKED/OPEN) |
| `fixed_assets` | Depreciation entries (existing) |
| `tools_equipment` | CCDC allocation entries (existing) |
| `currencies` | Foreign exchange revaluation (existing) |
| `tax_engine` | CIT provision calculation |

---

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Cash flow tagging too disruptive | Delays B03-DN | Start with bank/cash vouchers only, defer others |
| Year-end close complexity | Bugs in closing entries | Thorough unit tests, manual verification tool |
| Multi-currency in reports | Edge cases | VND-only for MVP, defer multi-currency reports |
| Performance on large datasets | Slow reports | Implement pagination, cache computed results |
| TT99 format changes | Template invalidation | Store templates in DB, not hardcoded |
