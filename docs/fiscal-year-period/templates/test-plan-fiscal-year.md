# Test Plan — Fiscal Years & Accounting Periods Module

Follows `docs/TESTING_STRATEGY.md` (levels per mục 6.4, naming/layout mục 7.4–7.5,
data mục 9, anti-patterns mục 17).

## Level 1 — Unit (domain, no DB) · `tests/unit/fiscal_year/`

| ID | Case | Expect |
|---|---|---|
| U-01 | Calendar FY 2026 | 12 periods, 01/01–31/12 |
| U-02 | FISCAL_APR 2026 | 01/04/2026–31/03/2027, 12 periods |
| U-03 | FISCAL_JUL / FISCAL_OCT | same math, other quarters |
| U-04 | Non-quarter start (2026-07-15) | `InvalidFiscalYearError` |
| U-05 | First period 15/08/2026–31/12/2026 | ≤15 months, label "Kỳ kế toán đầu tiên" |
| U-06 | First period > 15 months | `InvalidFiscalYearError` |
| U-07 | Short period < 90 days merge | merged, no standalone period |
| U-08 | Period boundaries contiguous/non-overlapping | invariant holds |
| U-09 | Leap year (2024-02) | period end 29/02 |
| U-10 | State machine OPEN→LOCKED | valid |
| U-11 | OPEN→YEAR_CLOSED direct | rejected |
| U-12 | YEAR_CLOSED→OPEN | rejected |
| U-13 | Self-approval close/reopen | `SelfApprovalError` |
| U-14 | Reopen without reason | `InvalidPeriodTransitionError` (422) |
| U-15 | Locked period date lookup | `is_locked` True |
| U-16 | Boundary dates (start/end inclusive) | exact match |
| U-17 | `validate_before_entry` locked | `PeriodLockedError` carries period_id |
| U-18 | Year-end preconditions (one period OPEN) | `YearEndPreconditionsError` lists it |
| U-19 | Kết chuyển math 911→421 | balances zero out, retained earnings correct |
| U-20 | Legacy FISCAL_15 migration flag | company flagged, posting blocked |

≥ 30 cases (incl. property tests for date math on quarter start dates).

## Level 2 — Integration (repo adapters + SQLite) · `tests/integration/test_fiscal_year_repository.py`

- I-01 `SQLAlchemyFiscalYearRepository.create/list/get_active`
- I-02 `SQLAlchemyPeriodLockRepository.is_locked` overlap query (mirror
  currency_repo test pattern)
- I-03 lock flip concurrency: two concurrent closes → exactly one wins
- I-04 unique constraints: duplicate (company, year_code); duplicate
  (fiscal_year_id, period_number)
- I-05 lock-event checksum chain verifies end-to-end

## Level 3 — API (blueprint via test client; copy currencies test-engine hooks) · `tests/integration/test_fiscal_year_api.py`

- A-01 CRUD fiscal year, RBAC: accountant 403 on configure
- A-02 close period happy path; A-03 reopen; A-04 self-approval 403
- A-05 posting into locked period via real `VoucherService.post` → 409
- A-06 FX CSV import with locked-date rows → atomic reject
- A-07 year-end close flow → opening balances equal prior closing
- A-08 AUDITOR read-only on all endpoints
- A-09 error contract shape `{error, message, period_id}`

## Level 4 — E2E (browser) — skip; pure logic covered above (TESTING_STRATEGY 6.4)

## Not tested (explicitly)
- No `sleep`/retry hacks; no order-dependent tests; no implementation-detail
  assertions (state via public service API).
- Vendor UI parity (MISA screens) — not our code.

## CI gates
- `ruff` + `black --check` scoped to new files; `mypy` on touched modules;
  `pytest` full green (existing 191 baseline + new suite).
