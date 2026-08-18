# Currencies & Exchange Rates — Implementation TODO

Spec baseline: docs/currencies-exchange/ (signed off 2026-08-18), ADR-003 accepted.
Excluded from this version: NHNN sync (v1.5, third-party).

## Order: domain → infra → app → presentation, TDD per slice, simple → complex

### Phase 1 — Domain layer
- [ ] T1: Enums `RateType`, `RevaluationStatus` + `CurrencyCode` VO in `src/domain/entities/base.py`
- [ ] T2: Domain exceptions (`currency.py`): CurrencyNotFoundError, RateNotFoundError, RateLockedError, InvalidRateError, RevaluationError, PeriodLockedError
- [ ] T3: Entities (`currency.py`): Currency, ExchangeRate, FXDifference, RevaluationEntry, RevaluationRun (pure Python, Decimal)
- [ ] T4: Unit tests: `tests/unit/currency/test_currency_entity.py` (TDD red-green)

### Phase 2 — Infrastructure layer
- [ ] T5: SQLAlchemy models: CurrencyModel, ExchangeRateModel, RevaluationRunModel, RevaluationEntryModel, FXDifferenceModel
- [ ] T6: Repo ports in `src/application/ports/__init__.py`: CurrencyRepositoryPort, ExchangeRateRepositoryPort, RevaluationRepositoryPort
- [ ] T7: SQLAlchemy adapters `src/infrastructure/repositories/currency_repo.py`

### Phase 3 — Application layer
- [ ] T8: `currency_service.py` — currency CRUD + rate maintenance + CSV import
- [ ] T9: `exchange_rate_service.py` — booking rate resolution (R1), bình quân gia quyền (D5), last-rate≤date fallback
- [ ] T10: `revaluation_service.py` — period-end revalue, idempotent re-run (D7), period lock (D8), approval chain (D9), balanced postings (D6)
- [ ] T11: Unit tests per service (mocked repo ports)

### Phase 4 — Presentation layer
- [ ] T12: Serializer `currency_serializer.py`
- [ ] T13: Blueprint `currencies_bp.py` + `@casbin_required` + register in app.py
- [ ] T14: Integration tests (`tests/integration/test_currencies_api.py`, `test_currencies_repository.py`)

### Phase 5 — Migration + hardening
- [ ] T15: Alembic migration (`flask db migrate` + `upgrade`), fresh + existing DB
- [ ] T16: Full gate: ruff → black --check → mypy → pytest (no regressions)
- [ ] T17: codegraph sync + commit (no push)

## Verification per task
- pytest targeted: `pytest tests/unit/currency/ -v` etc.
- ruff check src tests; black --check src tests; mypy src
- Full: `uv run pytest`
