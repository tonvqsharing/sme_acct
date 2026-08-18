# Fiscal Years & Accounting Periods Module — Production Readiness Audit

Audit date: **2026-08-18** · Auditor: BA lead + chief accountant (20+ yrs each)
Baseline: `git rev-parse HEAD` (master), codegraph + grep verification.

## Verdict: ❌ NOT PROD-READY

Module has scaffolding only. **No operation can be trusted in production.**
Posting to any date is currently unrestricted; period locks are cosmetic.

## What exists in codebase

| Artifact | Location | State |
|---|---|---|
| `AccountingPeriodType` enum | `src/domain/entities/base.py:124` | ❌ Contains `FISCAL_15` (illegal, see G-01) |
| `Company.get_fiscal_year_and_period()` | `src/domain/entities/company.py:188-209` | ✅ Logic sound (fiscal_year_start_month/day, default 1/1) |
| `CompanyConfig.accounting_period_type` + start fields | system-settings domain | ✅ Field exists |
| `PeriodLockModel` (`period_locks` table) | `src/infrastructure/database/models.py:301` | ❌ Primitive: no fiscal_year, period_number, status enum, audit fields (G-02) |
| `PeriodLockService` | `src/application/services/period_lock_service.py` | ❌ Stub: `is_locked` always False; `validate_before_entry` never blocks (G-03) |
| `SystemSettingsService.lock_period/unlock_period` | `src/application/services/system_settings_service.py` | ❌ 500 — calls missing `SQLAlchemySystemSettingsRepository` (G-04) |
| `currency_repo.period_is_locked()` | `src/infrastructure/repositories/currency_repo.py:203` | ✅ Working overlap query — pattern to copy |
| `RevaluationService.create_run` raises `PeriodLockedError` | `src/application/services/revaluation_service.py:75` | ✅ Raises — but backed by stub → never fires |
| `SystemSettingsRepositoryPort` / `period_is_locked` port | `src/application/ports/__init__.py` | ⚠️ Port exists; no real adapter |

## Gap analysis (critical → minor)

### G-01 CRITICAL — Illegal enum value `FISCAL_15`
`AccountingPeriodType.FISCAL_15` (15-month period starting mid-month, e.g.
15/07) violates Luật Kế toán 88/2015 Điều 12: fiscal year MUST start at the
beginning of a quarter month (01/04, 01/07, 01/10). If any company config uses
it, BCTC periods are legally invalid.
**Fix**: remove enum; migration maps legacy rows → require admin redefinition
(UC-12, R-15).

### G-02 CRITICAL — `period_locks` table cannot model a period
Columns are primitive (no fiscal_year/period_number/status enum, no
open/close audit, no reason/approval). Cannot distinguish month vs year close,
cannot enforce contiguous non-overlapping periods, no lock-event history.
**Fix**: new tables per specs §4.1 (`fiscal_years`, `accounting_periods`,
`period_lock_events`) + migration.

### G-03 CRITICAL — `PeriodLockService` is a no-op
- `is_locked(...)` → always `False`.
- `validate_before_entry(...)` → never raises, and is **called by nothing**:
  `VoucherService.post`, `InvoiceService`, `ExchangeRateService` CSV import do
  NOT invoke it. Zero tests cover period-lock behavior.
**Fix**: real implementation + enforcement hooks in every posting service
(specs §3.3) + tests.

### G-04 HIGH — System Settings lock routes 500
`lock_period`/`unlock_period` in `system_settings_bp.py` call
`SQLAlchemySystemSettingsRepository`, which does not exist. Registered routes
→ 500. (Known issue in AGENTS.md; this module makes them moot — delegate to new
`PeriodLockService`, keep routes for compat.)

### G-05 HIGH — No FiscalYear aggregate / period model
No entity for fiscal year, no period-generation service (12-month split,
quarter-aligned boundaries, first-period ≤15 months, <90-day merge). Cannot
create, close, or carry-forward.
**Fix**: entities + services per specs §2–§3.

### G-06 HIGH — No year-end close / carry-forward
No kết chuyển 911/421 pipeline, no opening-balance generation, no new-FY
creation. Everything P-2/DF-3 is greenfield.
**Fix**: `close_fiscal_year()` + `YearEndClosingService` + opening-balance
entry (specs §3.2, §8).

### G-07 HIGH — No change-of-fiscal-year support
No transition BCTC snapshot, no tax-notification workflow, no "Số đầu năm"
carry per TT133 Đ.73.
**Fix**: `change_fiscal_year()` + templates (UC-08, P-3).

### G-08 MEDIUM — No REST API / RBAC
No blueprint for fiscal years/periods. Posting enforcement absent at API
layer; `@casbin_required` gap.
**Fix**: `fiscal_year_bp.py` per specs §5, registered in `app.py`.

### G-09 MEDIUM — No cache/concurrency guards
Hot-path `is_locked` per query, no TTL cache; no row-lock/conditional UPDATE
discipline for status flips.
**Fix**: 60s cache + `SELECT ... FOR UPDATE` + guarded UPDATE (NFR-2, DF-1).

### G-10 MEDIUM — SOD enforcement missing
No approval flow for close/reopen; self-approval not blocked.
**Fix**: close/reopen approval + `SelfApprovalError` (R-07).

### G-11 LOW — Duplicate enums (domain vs SQLAlchemy)
Project rule requires syncing `base.py` enums with `models.py` enum classes.
New enums must be mirrored (specs §2.1).

### G-12 LOW — Doc debt
- `AGENTS.md` still cites TT 200/2014 as current chart-of-accounts source.
- Root-level `docs/audit_log_brd.md`/`specs`/`use_cases` sat outside
  `docs/<module>/` convention — moved to `docs/audit-log/` 2026-08-18.

## Requirements coverage map

| FR | Status | Where |
|---|---|---|
| FR-01 fiscal year definition | ❌ | G-01/G-05 |
| FR-02 first period ≤ 15 months | ❌ | G-05 |
| FR-03 < 90-day merge | ❌ | G-05 |
| FR-04 lock enforcement | ❌ | G-03 |
| FR-05 SOD | ❌ | G-10 |
| FR-06 year-end close | ❌ | G-06 |
| FR-07 change of FY | ❌ | G-07 |
| FR-08 audit trail | ⚠️ partial | audit-log module exists; no lock events |
| FR-09 RBAC | ❌ | G-08 |

## Green items worth keeping
- `Company.get_fiscal_year_and_period()` — reuse as period-resolution helper.
- `currency_repo.period_is_locked()` overlap-query shape — copy for
  `PeriodLockRepositoryPort.is_locked`.
- `RevaluationService` raising `PeriodLockedError` — keep, wire to real check.
- currencies test-engine hook pattern (`init_test_engine`/`_req_session`) —
  copy for new blueprint tests.

## Recommended build order
1. Enums + exceptions + entities (G-01, G-05) — domain, no DB.
2. Repo port + SQLAlchemy adapters + migration (G-02).
3. `PeriodLockService` real impl + enforcement hooks on Voucher/Invoice/
   Revaluation/FX (G-03) + tests.
4. REST blueprint + RBAC (G-08) + cache/concurrency (G-09) + SOD (G-10).
5. Year-end close + change-of-FY (G-06, G-07) + templates.
6. Doc/AGENTS cleanup (G-12).

## Verification protocol before PROD sign-off
- [ ] `pytest` green (existing 191 baseline + new suite; no regressions).
- [ ] Posting blocked in locked period at service AND API layer (unit + integration).
- [ ] SOD: self-approval returns 403.
- [ ] Year-end close: opening balances match prior closing balances exactly.
- [ ] Migration on legacy DB with `FISCAL_15` data completes with admin flag.
- [ ] `ruff`/`black --check`/`mypy` scoped to new files green.
