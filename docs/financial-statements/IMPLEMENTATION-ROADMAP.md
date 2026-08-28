# Financial Statements — Implementation Roadmap & Execution Plan

**Module:** `src/bricks/financial_statements/`
**Date:** 2026-08-28
**Status:** Ready for execution
**Estimated effort:** 9 sprints (4-5 weeks @ 2-day sprints)

---

## 1. Executive Summary

### 1.1 What We're Building

Four mandatory financial statements for Vietnamese SMEs under TT99/2025:
1. **Trial Balance (S06-DN)** — with account group subtotals
2. **Statement of Financial Position (B01-DN)** — Balance Sheet
3. **Statement of Profit or Loss (B02-DN)** — Income Statement
4. **Cash Flow Statement (B03-DN)** — direct method

Plus supporting engines: account type classification, retained earnings, period-end close.

### 1.2 Why It Matters

- **Regulatory compliance**: TT99/2025 mandates these reports
- **Audit readiness**: No financial statements = no audit = no bank loans
- **Tax filing**: 01/GTGT cross-checks with Income Statement revenue
- **Investor confidence**: Balance Sheet = proof of solvency

### 1.3 Current State

| Component | Status | Gap |
|---|---|---|
| Trial Balance | ⚠️ Partial | No account_type grouping |
| Balance Sheet | ❌ Missing | No account_type, no retained earnings |
| Income Statement | ❌ Missing | No account_type |
| Cash Flow Statement | ❌ Missing | No cash_flow_class on voucher lines |
| Year-End Close | ❌ Missing | No closing entries logic |
| Retained Earnings | ❌ Missing | No RE model |

---

## 2. Architecture Decisions

### 2.1 Brick Structure

```
src/bricks/financial_statements/
├── contract.py        # Public ports (FinancialStatementsPort, etc.)
├── domain.py          # AccountType enum, ReportTemplate, RetainedEarnings
├── services.py        # ReportEngine, PeriodCloseService
├── storage.py         # SQLAlchemy models + repository adapters
└── web_adapter.py     # Flask blueprint + API endpoints
```

### 2.2 Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Template storage | DB, not hardcoded | TT99 format may change; DB allows runtime updates |
| Account type | Auto-classify by first digit | TT99 specifies 1xx=Asset, 2xx=Liability, etc. |
| Cash flow tagging | Optional for MVP, mandatory later | Disruptive schema change; defer to minimize risk |
| Report computation | On-demand, not real-time | Performance; cache in DB |
| Period close | Sequential (month → year) | Prevents out-of-order closes |
| Comparative periods | Prior year column | TT99 requires it for B01-DN, B02-DN |

### 2.3 Dependency Chain

```
AccountTypeClassifier (Sprint 1)
    ↓
CashFlowClassifier (Sprint 2)
    ↓
ReportTemplateEngine (Sprint 3-4)
    ↓
├── TrialBalance (Sprint 5)
├── BalanceSheet (Sprint 5)
├── IncomeStatement (Sprint 6)
├── CashFlowStatement (Sprint 6)
├── PeriodCloseService (Sprint 7)
└── RetainedEarningsEngine (Sprint 8)
```

---

## 3. Ticket Breakdown

### Sprint 1: Account Type Classification

**Goal:** Every COA account has an `account_type` field.

| Ticket | Title | Description | Acceptance Criteria | Files |
|---|---|---|---|---|
| FS-001 | Add `AccountType` enum to domain | Create `AccountType` enum (ASSET/LIABILITY/EQUITY/REVENUE/EXPENSE) in `coa/domain.py` | - Enum values match TT99 spec<br>- Can be imported from domain | `src/bricks/coa/domain.py` |
| FS-002 | Add `account_type` to `Account` dataclass | Add `account_type: AccountType` field with auto-classify logic | - Auto-classifies by first digit<br>- Backward compatible (default=None)<br>- `is_detail` still works | `src/bricks/coa/domain.py` |
| FS-003 | Add `account_type` to `AccountModel` | Add `account_type` column to SQLAlchemy model | - Column exists in DB<br>- `_to_domain()` maps correctly<br>- `create()` persists correctly | `src/bricks/coa/storage.py` |
| FS-004 | Migration: add column + retroactive classify | Alembic migration adds column, then Python script classifies existing accounts | - All existing accounts classified<br>- No data loss<br>- Rollback possible | `alembic/versions/...`, `scripts/classify_accounts.py` |
| FS-005 | Auto-classify in `create_account()` | Service auto-classifies new accounts by code prefix | - New account gets correct type<br>- User cannot override auto-classify<br>- Invalid prefix rejected | `src/bricks/coa/services.py` |
| FS-006 | Unit tests for classification | Test all 5 types, edge cases, invalid codes | - 10+ unit tests<br>- All pass | `tests/unit/coa/test_account_type.py` |
| FS-007 | Integration tests | Test account creation with auto-type via API | - 3+ integration tests<br>- All pass | `tests/integration/test_coa_api.py` |

**Definition of Done:** All 7 tickets complete, all tests pass, code reviewed.

---

### Sprint 2: Cash Flow Tagging

**Goal:** Voucher lines can be tagged with cash flow class.

| Ticket | Title | Description | Acceptance Criteria | Files |
|---|---|---|---|---|
| FS-010 | Add `CashFlowClass` enum | Create enum (OPERATING/INVESTING/FINANCING) | - Enum values correct<br>- Can be imported | `src/bricks/voucher/domain.py` |
| FS-011 | Add field to `VoucherLine` | Add `cash_flow_class` to voucher line model | - Field exists<br>- Optional for non-cash vouchers<br>- Required for cash/bank vouchers | `src/bricks/voucher/domain.py` |
| FS-012 | Migration: add column | Alembic migration adds column | - Column exists<br>- Default NULL for existing rows | `alembic/versions/...` |
| FS-013 | Validation in voucher service | Cash/bank vouchers must have cash_flow_class | - Validation enforced<br>- Error message clear | `src/bricks/voucher/services.py` |
| FS-014 | Unit tests | Test enum, validation, edge cases | - 8+ unit tests<br>- All pass | `tests/unit/voucher/test_cash_flow.py` |

**Definition of Done:** All 5 tickets complete, all tests pass.

---

### Sprint 3: Report Template Storage

**Goal:** Store report templates in DB.

| Ticket | Title | Description | Acceptance Criteria | Files |
|---|---|---|---|---|
| FS-020 | `ReportTemplate` domain | Template + template line dataclasses | - Domain models correct<br>- No Flask/SQLAlchemy imports | `src/bricks/financial_statements/domain.py` |
| FS-021 | `ReportTemplateRepository` port | CRUD port for templates | - Port defined<br>- Primitives in/out | `src/bricks/financial_statements/contract.py` |
| FS-022 | SQLAlchemy storage | Models + repository adapter | - Storage works<br>- CRUD operations correct | `src/bricks/financial_statements/storage.py` |
| FS-023 | Template seeding | Seed B01-DN, B02-DN, B03-DN, S06-DN templates | - All 4 templates seeded<br>- Correct TT99 format | `src/bricks/financial_statements/services.py` |
| FS-024 | Alembic migration | Create template tables | - Tables exist<br>- No data loss | `alembic/versions/...` |
| FS-025 | Unit tests | Test CRUD, seeding | - 12+ unit tests<br>- All pass | `tests/unit/financial_statements/test_templates.py` |

**Definition of Done:** All 6 tickets complete, all tests pass.

---

### Sprint 4: Report Computation Engine

**Goal:** Compute report lines from trial balance.

| Ticket | Title | Description | Acceptance Criteria | Files |
|---|---|---|---|---|
| FS-030 | `ReportEngine` service | Core computation logic | - Engine computes template lines<br>- Correct arithmetic | `src/bricks/financial_statements/services.py` |
| FS-031 | `ACCOUNT_AGGREGATE` type | Sum of account codes | - Correct sum<br>- Handles missing accounts | `src/bricks/financial_statements/services.py` |
| FS-032 | `FORMULA` type | Arithmetic on other lines | - Correct evaluation<br>- Handles circular refs | `src/bricks/financial_statements/services.py` |
| FS-033 | `TOTAL` type | Sum of children | - Correct hierarchy<br>- Handles empty groups | `src/bricks/financial_statements/services.py` |
| FS-034 | `ReportInstance` models | Store computed results | - Instance + line models<br>- Store correctly | `src/bricks/financial_statements/storage.py` |
| FS-035 | Cache invalidation | Invalidate on new voucher | - Cache cleared when voucher posted<br>- Recomputation on demand | `src/bricks/financial_statements/services.py` |
| FS-036 | Unit tests | Test computation engine | - 15+ unit tests<br>- All pass | `tests/unit/financial_statements/test_engine.py` |

**Definition of Done:** All 7 tickets complete, all tests pass.

---

### Sprint 5: Trial Balance + Balance Sheet

**Goal:** Generate Trial Balance and Balance Sheet.

| Ticket | Title | Description | Acceptance Criteria | Files |
|---|---|---|---|---|
| FS-040 | Extend trial balance | Add account_type grouping to `LedgerService` | - Groups by account type<br>- Subtotals per group | `src/bricks/ledger/services.py` |
| FS-041 | Trial balance API | Enhance existing endpoint | - Returns grouped data<br>- Correct totals | `src/bricks/ledger/web_adapter.py` |
| FS-042 | B01-DN template | Define Balance Sheet template lines | - Correct TT99 format<br>- All sections present | `src/bricks/financial_statements/templates.py` |
| FS-043 | Balance sheet computation | Compute B01-DN from trial balance | - Correct aggregation<br>- Balance check works | `src/bricks/financial_statements/services.py` |
| FS-044 | Balance sheet API | `GET /api/v1/reports/balance-sheet` | - Returns correct JSON<br>- Handles missing data | `src/bricks/financial_statements/web_adapter.py` |
| FS-045 | Balance validation | Assets = Liabilities + Equity check | - Validation enforced<br>- Error message clear | `src/bricks/financial_statements/services.py` |
| FS-046 | Tests | Unit + integration tests | - 18+ tests<br>- All pass | `tests/unit/financial_statements/test_balance_sheet.py`, `tests/integration/test_reports_api.py` |

**Definition of Done:** All 7 tickets complete, all tests pass, balance sheet balances.

---

### Sprint 6: Income Statement + Cash Flow

**Goal:** Generate Income Statement and Cash Flow Statement.

| Ticket | Title | Description | Acceptance Criteria | Files |
|---|---|---|---|---|
| FS-050 | B02-DN template | Define Income Statement template lines | - Correct TT99 format<br>- All sections present | `src/bricks/financial_statements/templates.py` |
| FS-051 | Income statement computation | Compute B02-DN from trial balance | - Correct aggregation<br>- Gross/Operating/Net profit | `src/bricks/financial_statements/services.py` |
| FS-052 | Income statement API | `GET /api/v1/reports/income-statement` | - Returns correct JSON<br>- Handles missing data | `src/bricks/financial_statements/web_adapter.py` |
| FS-053 | B03-DN template | Define Cash Flow template lines | - Correct TT99 format<br>- Three activity sections | `src/bricks/financial_statements/templates.py` |
| FS-054 | Cash flow computation | Compute B03-DN from tagged voucher lines | - Correct aggregation<br>- Reconciliation works | `src/bricks/financial_statements/services.py` |
| FS-055 | Cash flow API | `GET /api/v1/reports/cash-flow` | - Returns correct JSON<br>- Handles missing tags | `src/bricks/financial_statements/web_adapter.py` |
| FS-056 | Cash flow reconciliation | Ending cash = B01 Code 110 check | - Validation enforced<br>- Error message clear | `src/bricks/financial_statements/services.py` |
| FS-057 | Tests | Unit + integration tests | - 20+ tests<br>- All pass | `tests/unit/financial_statements/test_income_statement.py`, `tests/unit/financial_statements/test_cash_flow.py` |

**Definition of Done:** All 8 tickets complete, all tests pass.

---

### Sprint 7: Month-End Close

**Goal:** Execute month-end close procedure.

| Ticket | Title | Description | Acceptance Criteria | Files |
|---|---|---|---|---|
| FS-060 | `PeriodCloseService` domain | Close logic domain | - Domain models correct<br>- No Flask/SQLAlchemy imports | `src/bricks/financial_statements/domain.py` |
| FS-061 | Revenue transfer | Transfer revenue to 911 | - Correct entry generated<br>- All revenue accounts zeroed | `src/bricks/financial_statements/services.py` |
| FS-062 | Expense transfer | Transfer expenses to 911 | - Correct entry generated<br>- All expense accounts zeroed | `src/bricks/financial_statements/services.py` |
| FS-063 | CIT provision | Calculate CIT provision | - Correct calculation<br>- Entry generated | `src/bricks/financial_statements/services.py` |
| FS-064 | Period lock | Lock period after close | - Period locked<br>- No new vouchers allowed | `src/bricks/financial_statements/services.py` |
| FS-065 | Close API | `POST /api/v1/reports/close-month` | - Returns success<br>- Handles errors | `src/bricks/financial_statements/web_adapter.py` |
| FS-066 | Tests | Unit + integration tests | - 15+ tests<br>- All pass | `tests/unit/financial_statements/test_period_close.py` |

**Definition of Done:** All 7 tickets complete, all tests pass.

---

### Sprint 8: Year-End Close + Retained Earnings

**Goal:** Execute year-end close and track retained earnings.

| Ticket | Title | Description | Acceptance Criteria | Files |
|---|---|---|---|---|
| FS-070 | `RetainedEarnings` domain | RE domain model | - Domain model correct<br>- No Flask/SQLAlchemy imports | `src/bricks/financial_statements/domain.py` |
| FS-071 | Year-end close | Calculate net income | - Correct calculation<br>- All revenue/expense accounts zeroed | `src/bricks/financial_statements/services.py` |
| FS-072 | Closing entry | Generate Dr. 911 / Cr. 4212 (or reverse) | - Correct entry<br>- Idempotent | `src/bricks/financial_statements/services.py` |
| FS-073 | RE transfer | Transfer 4212 → 4211 | - Correct transfer<br>- Balance carried forward | `src/bricks/financial_statements/services.py` |
| FS-074 | Next FY creation | Create next fiscal year periods | - Periods created<br>- Correct dates | `src/bricks/financial_statements/services.py` |
| FS-075 | Year-end API | `POST /api/v1/reports/close-year` | - Returns success<br>- Handles errors | `src/bricks/financial_statements/web_adapter.py` |
| FS-076 | RE API | `GET /api/v1/reports/retained-earnings` | - Returns correct JSON<br>- Handles missing data | `src/bricks/financial_statements/web_adapter.py` |
| FS-077 | Tests | Unit + integration tests | - 18+ tests<br>- All pass | `tests/unit/financial_statements/test_retained_earnings.py` |

**Definition of Done:** All 8 tickets complete, all tests pass.

---

### Sprint 9: Comparative Periods + Export

**Goal:** Add comparative periods and export capabilities.

| Ticket | Title | Description | Acceptance Criteria | Files |
|---|---|---|---|---|
| FS-080 | Prior year column | Add prior year data to B01-DN, B02-DN | - Prior year column shown<br>- Correct data | `src/bricks/financial_statements/services.py` |
| FS-081 | Monthly breakdown | Show monthly columns | - Monthly breakdown works<br>- Correct totals | `src/bricks/financial_statements/services.py` |
| FS-082 | PDF export | Vietnamese formatting PDF | - PDF generated<br>- Vietnamese characters correct | `src/bricks/financial_statements/export.py` |
| FS-083 | Excel export | Excel export | - Excel generated<br>- Formatted correctly | `src/bricks/financial_statements/export.py` |
| FS-084 | Report caching | Cache computed results | - Cache works<br>- Invalidated on voucher | `src/bricks/financial_statements/services.py` |

**Definition of Done:** All 5 tickets complete, all tests pass.

---

## 4. Dependency Graph

```
FS-001 (AccountType enum)
    ↓
FS-002 (Add to Account)
    ↓
FS-003 (Storage) → FS-004 (Migration)
    ↓
FS-005 (Auto-classify) → FS-006 (Unit tests) → FS-007 (Integration tests)
    ↓
FS-010 (CashFlowClass enum) → FS-011 (Add to VoucherLine) → FS-012 (Migration)
    ↓
FS-013 (Validation) → FS-014 (Unit tests)
    ↓
FS-020 (Template domain) → FS-021 (Port) → FS-022 (Storage) → FS-023 (Seeding)
    ↓
FS-024 (Migration) → FS-025 (Unit tests)
    ↓
FS-030 (ReportEngine) → FS-031 (ACCOUNT_AGGREGATE) → FS-032 (FORMULA) → FS-033 (TOTAL)
    ↓
FS-034 (Instance models) → FS-035 (Cache) → FS-036 (Unit tests)
    ↓
FS-040 (Extend trial balance) → FS-041 (Trial balance API)
    ↓
FS-042 (B01-DN template) → FS-043 (Balance sheet computation) → FS-044 (API) → FS-045 (Validation)
    ↓
FS-046 (Tests)
    ↓
FS-050 (B02-DN template) → FS-051 (Income statement) → FS-052 (API)
    ↓
FS-053 (B03-DN template) → FS-054 (Cash flow) → FS-055 (API) → FS-056 (Reconciliation)
    ↓
FS-057 (Tests)
    ↓
FS-060 (PeriodClose domain) → FS-061 (Revenue) → FS-062 (Expense) → FS-063 (CIT)
    ↓
FS-064 (Period lock) → FS-065 (API) → FS-066 (Tests)
    ↓
FS-070 (RetainedEarnings) → FS-071 (Year-end) → FS-072 (Closing entry) → FS-073 (Transfer)
    ↓
FS-074 (Next FY) → FS-075 (API) → FS-076 (RE API) → FS-077 (Tests)
    ↓
FS-080 (Prior year) → FS-081 (Monthly) → FS-082 (PDF) → FS-083 (Excel) → FS-084 (Cache)
```

---

## 5. Sprint Planning

### Sprint 1 (Days 1-2): Account Type Classification

**Focus:** Foundation for all reports.

| Day | Morning | Afternoon |
|---|---|---|
| Day 1 | FS-001: Add `AccountType` enum<br>FS-002: Add to `Account` dataclass<br>FS-003: Add to `AccountModel` | FS-004: Migration<br>FS-005: Auto-classify in service |
| Day 2 | FS-006: Unit tests<br>FS-007: Integration tests | Code review + fixes |

**Exit criteria:** All 7 tickets complete, all tests pass.

---

### Sprint 2 (Days 3-4): Cash Flow Tagging

**Focus:** Prepare for Cash Flow Statement.

| Day | Morning | Afternoon |
|---|---|---|
| Day 3 | FS-010: `CashFlowClass` enum<br>FS-011: Add to `VoucherLine`<br>FS-012: Migration | FS-013: Validation |
| Day 4 | FS-014: Unit tests | Code review + fixes |

**Exit criteria:** All 5 tickets complete, all tests pass.

---

### Sprint 3 (Days 5-6): Report Template Storage

**Focus:** Template infrastructure.

| Day | Morning | Afternoon |
|---|---|---|
| Day 5 | FS-020: Domain models<br>FS-021: Port<br>FS-022: Storage | FS-023: Template seeding |
| Day 6 | FS-024: Migration<br>FS-025: Unit tests | Code review + fixes |

**Exit criteria:** All 6 tickets complete, all tests pass.

---

### Sprint 4 (Days 7-8): Report Computation Engine

**Focus:** Core computation logic.

| Day | Morning | Afternoon |
|---|---|---|
| Day 7 | FS-030: `ReportEngine`<br>FS-031: `ACCOUNT_AGGREGATE`<br>FS-032: `FORMULA` | FS-033: `TOTAL`<br>FS-034: Instance models |
| Day 8 | FS-035: Cache<br>FS-036: Unit tests | Code review + fixes |

**Exit criteria:** All 7 tickets complete, all tests pass.

---

### Sprint 5 (Days 9-10): Trial Balance + Balance Sheet

**Focus:** First financial statement.

| Day | Morning | Afternoon |
|---|---|---|
| Day 9 | FS-040: Extend trial balance<br>FS-041: Trial balance API<br>FS-042: B01-DN template | FS-043: Balance sheet computation |
| Day 10 | FS-044: API<br>FS-045: Validation<br>FS-046: Tests | Code review + fixes |

**Exit criteria:** All 7 tickets complete, balance sheet balances.

---

### Sprint 6 (Days 11-12): Income Statement + Cash Flow

**Focus:** Second and third financial statements.

| Day | Morning | Afternoon |
|---|---|---|
| Day 11 | FS-050: B02-DN template<br>FS-051: Income statement<br>FS-052: API | FS-053: B03-DN template<br>FS-054: Cash flow |
| Day 12 | FS-055: API<br>FS-056: Reconciliation<br>FS-057: Tests | Code review + fixes |

**Exit criteria:** All 8 tickets complete, all tests pass.

---

### Sprint 7 (Days 13-14): Month-End Close

**Focus:** Period-end procedures.

| Day | Morning | Afternoon |
|---|---|---|
| Day 13 | FS-060: Domain<br>FS-061: Revenue transfer<br>FS-062: Expense transfer | FS-063: CIT provision<br>FS-064: Period lock |
| Day 14 | FS-065: API<br>FS-066: Tests | Code review + fixes |

**Exit criteria:** All 7 tickets complete, all tests pass.

---

### Sprint 8 (Days 15-16): Year-End Close + Retained Earnings

**Focus:** Annual closing procedures.

| Day | Morning | Afternoon |
|---|---|---|
| Day 15 | FS-070: Domain<br>FS-071: Year-end<br>FS-072: Closing entry | FS-073: Transfer<br>FS-074: Next FY |
| Day 16 | FS-075: API<br>FS-076: RE API<br>FS-077: Tests | Code review + fixes |

**Exit criteria:** All 8 tickets complete, all tests pass.

---

### Sprint 9 (Days 17-18): Comparative Periods + Export

**Focus:** Polish and export.

| Day | Morning | Afternoon |
|---|---|---|
| Day 17 | FS-080: Prior year<br>FS-081: Monthly<br>FS-082: PDF | FS-083: Excel<br>FS-084: Cache |
| Day 18 | Integration tests<br>End-to-end testing | Code review + final fixes |

**Exit criteria:** All 5 tickets complete, all tests pass.

---

## 6. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Cash flow tagging too disruptive | Medium | High | Start with bank/cash vouchers only; defer others |
| Year-end close bugs | Medium | High | Thorough unit tests; manual verification tool |
| Multi-currency edge cases | Low | Medium | VND-only for MVP; defer multi-currency reports |
| Performance on large datasets | Medium | Medium | Implement pagination; cache computed results |
| TT99 format changes | Low | Medium | Store templates in DB; not hardcoded |
| Migration breaks existing data | Low | High | Test migrations on copy of production data first |
| Scope creep | High | Medium | Strict MVP scope; defer Phase 2 features |

---

## 7. Quality Gates

### 7.1 Before Each Commit

```bash
uv run ruff check src tests                    # lint
uv run black --check src tests                 # format
uv run mypy --ignore-missing-imports src/bricks/  # typecheck
uv run pytest -q                               # tests
```

### 7.2 Before Each Sprint Completion

- [ ] All tickets in sprint complete
- [ ] All tests pass
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] AGENTS.md test count updated

### 7.3 Before Module Completion

- [ ] All 9 sprints complete
- [ ] Integration tests pass
- [ ] Balance sheet balances
- [ ] Income statement correct
- [ ] Cash flow reconciles
- [ ] Year-end close works
- [ ] All APIs documented
- [ ] User journeys validated

---

## 8. Rollback Plan

### 8.1 If Sprint Fails

- Revert to last working commit
- Analyze failure
- Replan sprint with adjusted scope

### 8.2 If Module Fails

- Revert all financial_statements commits
- Keep existing functionality intact
- Replan with reduced scope (e.g., Trial Balance only)

### 8.3 If Production Issues

- Disable financial statement endpoints
- Allow existing reports to continue
- Fix issues in hotfix branch

---

## 9. Success Criteria

### 9.1 Functional

- [ ] Trial Balance shows correct subtotals by account group
- [ ] Balance Sheet balances: Total Assets = Total Liabilities + Equity
- [ ] Income Statement shows: Revenue - COGS - Expenses = Net Profit
- [ ] Cash Flow Statement reconciles: ending cash = B01 cash line
- [ ] Year-end closing entries correctly zero P&L accounts
- [ ] Retained earnings carries forward correctly

### 9.2 Non-Functional

- [ ] All reports generate in < 2 seconds
- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] No mypy errors
- [ ] No ruff errors
- [ ] Documentation complete

### 9.3 Business

- [ ] Accountant can generate all 4 reports
- [ ] Chief Accountant can close month/year
- [ ] Reports match manual calculations
- [ ] Tax authority accepts reports
- [ ] Audit trail complete

---

## 10. Next Steps

1. **Immediate:** Start Sprint 1 (Account Type Classification)
2. **Day 1:** FS-001, FS-002, FS-003, FS-004
3. **Day 2:** FS-005, FS-006, FS-007
4. **End of Sprint 1:** Code review + commit
5. **Continue:** Sprint 2 (Cash Flow Tagging)

**Ready to execute.**
