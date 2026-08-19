# Test Plan — Currencies & Exchange Rates Module

| | |
|---|---|
| Version | 1.0 |
| Date | 2026-08-19 |
| Follows | docs/TESTING_STRATEGY.md (esp. mục 5, 6, 7) |
| Level selection | mục 6.4 decision tree — pure logic → unit; repo/API → integration; no UI-level for pure logic; no E2E for edge cases |

## 1. Test levels

| Level | Scope | Count (est) |
|---|---|---|
| Unit | domain rules (R1–R8, D1–D11), service algorithms | ~60 |
| Integration | repository adapters, API endpoints, RBAC | ~40 |
| Total | | ~100 |

## 2. Unit tests (domain)

Location: `tests/unit/currencies/` (mirror company pattern)

| # | Test | Rule |
|---|---|---|
| U1 | currency code regex `^[A-Z]{3}$` | D1 |
| U2 | VND base immutable | D4 |
| U3 | rate > 0 invariant | D2 |
| U4 | unique (currency, date, type) | D2 |
| U5 | new rate supersedes old; last-available fallback for gaps | D3 / Tryton |
| U6 | rate referenced by posted txn → RateLockedError | D3 |
| U7 | debit side → actual transaction rate | R1 |
| U8 | credit side → weighted avg `Σ(orig×rate)/Σ(orig)` | R1, D5 |
| U9 | weighted avg empty balance → fallback/error | alt UC-05 |
| U10 | revaluation: new_vnd = orig × closing rate | R2, D |
| U11 | revaluation postings balance (tol 0.01) | D6 |
| U12 | gain→515, loss→635; TK 413 path per config | R3 |
| U13 | re-run idempotent (reverse + re-apply) | D7 |
| U14 | locked period → PeriodLockedError | D8 |
| U15 | post without approval → error | D9 |
| U16 | monetary vs non-monetary classification | R4 |
| U17 | e-invoice tỷ giá quy đổi mandatory on FX invoice | R5 |
| U18 | base currency immutable once transactions exist | D4 |
| U19 | CSV row validation (bad date/currency/rate/type) | UC-04 |
| U20 | atomic import: 1 bad row → none applied | UC-04 |

## 3. Integration tests

Location: `tests/integration/test_currency_repository.py`, `test_currency_api.py`
(mirror company module pattern).

| # | Test | Scope |
|---|---|---|
| I1 | CurrencyModel + repository create/list/update | repo |
| I2 | ExchangeRateModel persistence + unique constraint | repo |
| I3 | RevaluationRun + entries persistence, status transitions | repo |
| I4 | POST /api/currencies (role-gated) | API |
| I5 | POST /api/exchange-rates (actor required) | API |
| I6 | POST /api/exchange-rates/import CSV | API |
| I7 | POST /api/revaluations → approve → post | API |
| I8 | POST /api/revaluations without approval → 403 | API |
| I9 | AUDITOR GET ok, POST → 403 (RBAC backend) | API/RBAC |
| I10 | period locked → 409/403 | API |
| I11 | fx-differences report query | API/repo |
| I12 | rate history audit query | API/repo |

## 4. Test data (per mục 9 TESTING_STRATEGY)

- Factories for Currency, ExchangeRate, RevaluationRun.
- Isolated state per test (in-memory/transaction rollback); order-independent.
- No real client data; realistic VN SME scenarios (USD export invoice, EUR import, JPY bank).
- Use TT 99/2025 rate semantics (transfer rate for revaluation).

## 5. Anti-patterns to avoid (mục 17)

- ❌ UI-level tests for pure logic (booking rate, weighted avg).
- ❌ E2E for edge cases.
- ❌ `sleep` in E2E.
- ❌ order-dependent tests.
- ❌ retry to hide flakes (policy mục 11: Fix/Quarantine/Delete).
- ❌ coverage-chasing.

## 6. CI gates

`ruff → black --check → mypy → pytest` all green before merge.

## 7. Version history

| Ver | Date | Change |
|---|---|---|
| 0.1 | 2026-08-18 | Initial test plan |