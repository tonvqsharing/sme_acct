# Implementation Plan: Fiscal Years & Accounting Periods Module

## Overview
Implement spec `docs/fiscal-year-period/` (signed off 2026-08-18). Domain-first:
enums/exceptions → entities (period math) → ports → repo adapters → services →
enforcement hooks → REST API → migration. TDD per slice, vertical core-to-edge.
No third-party integration (next version).

## Architecture Decisions
- `PeriodLockService` has ZERO external callers — free redesign, zero breakage.
- `FISCAL_15` referenced nowhere but its definition — safe removal per law.
- Keep `PeriodLockModel` (legacy currencies D8 path + 80 green tests). New
  service dual-writes: `accounting_periods.status` (new truth) + legacy
  `period_locks` row (keeps `RevaluationRepositoryPort.period_is_locked`
  working without touching currency_repo).
- No Voucher/Invoice services exist → enforcement hooks only where services
  exist: `RevaluationService` (existing), `ExchangeRateService` CSV import
  (optional repo injection, default None → no behavior change).
- Lazy FY auto-seed: `ensure_fiscal_year(company_id, entry_date)` in service
  (idempotent) creates default calendar FY + 12 periods. Mirrors MISA/Fast.
- Domain layer stays free of sqlalchemy/web imports (repo convention).

## Task List (slices, TDD red→green)

### Slice 1: Domain enums + exceptions
- [ ] base.py: fix AccountingPeriodType (CALENDAR/FISCAL_APR/FISCAL_JUL/FISCAL_OCT), add PeriodStatus, PeriodLockAction
- [ ] exceptions: FiscalYearError base + InvalidFiscalYearError, FiscalYearExistsError, PeriodTransitionError, PeriodNotClosableError, YearEndPreconditionsError, SelfApprovalError
- [ ] tests/unit/fiscal_year/test_fiscal_year_enums.py (red first)

### Slice 2: FiscalYear/AccountingPeriod/PeriodLockEvent entities
- [ ] src/domain/entities/fiscal_year.py — period math, state machine, invariants
- [ ] tests/unit/fiscal_year/test_fiscal_year_entity.py (U-01..U-16)

### Slice 3: Models + ports + repo adapters
- [ ] models.py: FiscalYearModel, AccountingPeriodModel, PeriodLockEventModel + enum mirrors
- [ ] ports: FiscalYearRepositoryPort, PeriodLockRepositoryPort
- [ ] src/infrastructure/repositories/fiscal_year_repo.py
- [ ] tests/integration/test_fiscal_year_repository.py (I-01..I-05)

### Slice 4: PeriodLockService (real implementation)
- [ ] Rewrite period_lock_service.py: ensure_fiscal_year, is_locked, validate_before_entry, close_period (SOD), reopen_period, close_fiscal_year (911/421 + opening balances), create_fiscal_year, change_fiscal_year
- [ ] tests/unit/fiscal_year/test_period_lock_service.py (fake repos)

### Slice 5: Enforcement hooks
- [x] ExchangeRateService CSV hook: SKIPPED by design — rates are company-agnostic
      (create_rate/import_csv carry no company_id; currency table is global), period
      locks are company-scoped → enforcing lock on CSV import would wrongly couple a
      global rate table to one company's period state. Enforcement stays where company
      context exists: RevaluationService D8 period_is_locked (already wired, verified
      via dual-write PeriodLockModel bridge in slice 3) + future Voucher/Invoice services.

### Slice 6: Serializers + REST API
- [ ] serializers/fiscal_year.py
- [ ] presentation/api/fiscal_year_bp.py (currencies test-engine hook pattern, @casbin_required)
- [ ] app.py registration
- [ ] tests/integration/test_fiscal_year_api.py (A-01..A-09)

### Slice 7: Migration
- [ ] migrations/versions/xxx_fiscal_years_periods.py (3 tables, manual, alembic style)

### Slice 8: Docs sync + review + git
- [ ] Update docs status (README, audit, AGENTS.md)
- [ ] ruff/black/mypy scoped + full pytest green
- [ ] codegraph sync, commit (no push — review required)

## Checkpoints
- After Slice 2: domain math tests green; period boundaries exact.
- After Slice 4: service tests green; full pytest (191 baseline) still green.
- After Slice 6: API integration green; currencies tests untouched (80 green).
- After Slice 7: migration applies on fresh sqlite; seed FY works.

## Risks
| Risk | Mitigation |
|---|---|
| Breaking 80 currency tests | dual-write PeriodLockModel bridge; default-None injection |
| Migration drift vs models | manual alembic file matching models.py; verify on sqlite |
| FISCAL_15 legacy data | service flags non-quarter-aligned configs on ensure |