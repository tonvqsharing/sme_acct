# AGENTS — Vietnamese SME Accounting App

## Repo state
- Flask + Clean Architecture scaffold. Completed modules: Company, User Master Data, Audit Log, Currencies & Exchange Rates, System Settings (domain + attempted REST), Invoice Approval workflows.
- Root entrypoint: `app.py` (`create_app()` factory, `python-dotenv` loading wired).
- `.venv` managed by `uv`. Always activate: `source .venv/bin/activate`. No bare `pip` — use `uv pip install --python=.venv/bin/python`.
- `pyproject.toml` present (hatchling, `src/` wheel). Python >= 3.11 (venv runs 3.13).
- `pytest` configured (`testpaths=tests`, `pythonpath=src`). **191 pass, 2 fail, 14 errors** — ALL failures/errors are pre-existing in `tests/integration/test_company_api.py` (UUID format on Py3.13 + SQLAlchemy session teardown). Do NOT "fix" them unless tasked; leave baseline untouched.
- `templates/base.html` uses local Bulma + HTMX (no CDN, offline-capable).
- Migration: `flask db init|migrate|upgrade` requires `SQLALCHEMY_DATABASE_URI` in env; supported URIs: `sqlite:///...`, `mysql://...`, `mariadb://...`, `postgresql://...`. 5 migration files exist (company, system_settings, immutability_triggers, sod_roles, currencies).
- RBAC via pycasbin 2.8.0 with fallback role-based enforcement; `@casbin_required(*roles)` on routes; AUDITOR read-only. Casbin init logs a WARNING about missing `tests/integration/casbin_model.conf` during tests — harmless, tests fall back to role-based enforcement.

## ⚠️ Broken / unregistered code (verify before relying)
- **System Settings REST API is registered but ALL routes 500**: `src/presentation/api/system_settings_bp.py` calls `SQLAlchemySystemSettingsRepository` which does NOT exist in `src/infrastructure/repositories/`. Implement the adapter before touching these routes. It also hosts invoice-approval routes (`/api/invoices/<id>/approve`, `/threshold-info`).
- **`src/presentation/api/users_bp.py` (User Master Data API) is NOT registered in `app.py`** — blueprint + 10 `@casbin_required` routes exist but are dead code. Register before use.
- **`mypy src` is red repo-wide (~173 errors)** — pre-existing, mostly config/import noise (mypy lacks `pythonpath`). Module files are clean; scope typechecks to files you touch.
- **`ruff check src tests` is red (~199 errors)** — mostly pre-existing in company/system-settings/user files. Run ruff scoped to your files, not whole repo.

## Company module status (complete)
- Domain entity: `src/domain/entities/company.py` (Company aggregate root, status lifecycle).
- Domain enums: `CompanyType`, `CompanyStatus`, `AccountingRegime` in `src/domain/entities/base.py`.
- Repository port: `CompanyRepositoryPort` in `src/application/ports/__init__.py`.
- DB models: `CompanyModel`, `BankAccountModel` in `src/infrastructure/database/models.py`; `company_id` FK on `PartnerModel`, `InvoiceModel`, `VoucherModel`.
- Repository adapter: `SQLAlchemyCompanyRepository` in `src/infrastructure/repositories/__init__.py` (`create` + `update`).
- Unit tests: 50 passing (`tests/unit/company/`).
- Integration tests: 15 passing (`tests/integration/test_company_repository.py`; `test_company_api.py` has the pre-existing failures/errors above).
- REST API endpoints: POST/GET/GET/{id}/PATCH/{id}/suspend/{id}/reactivate/{id}/dissolve.

## System Settings module status (Phase 1 domain complete, migration applied)
- **Domain layer** (complete): `FlagType`/`FlagScope`/`FlagCategory` enums; `AccountingPeriodType`; `VATMethod`/`EInvoiceMode`/ `EInvoiceSeries` dataclass; `CompanyConfig` aggregate; exceptions (`SystemSettingsError`, `FlagLockedError`, `ConfigVersionConflict`, `InvalidVATRateError`, `InvalidCAListError`, `InvalidRegimeError`).
- **Migration** (applied): `flask db migrate` generated 4 new tables (`audit_log`, `ca_list_entries`, `e_invoice_series`, `period_locks`); `flask db upgrade` applied.
- **Service layer** (complete): `SystemSettingsService` with `get_config`, `update_config`, `lock_period`, `unlock_period`, `validate_vat_rate`, `add_e_invoice_series` — follows `CompanyService` pattern, NO Flask/SQLAlchemy imports.
- **Repository port** (complete): `SystemSettingsRepositoryPort` in `src/application/ports/__init__.py`.
- **REST API** (⚠️ broken, see "Broken / unregistered code" above): blueprint registered, but adapter class missing → all routes 500.

## Currencies & Exchange Rates module status (complete)
- Domain: `src/domain/entities/currency.py` (Currency, ExchangeRate, RevaluationRun state machine DRAFT→PENDING_APPROVAL→APPROVED→POSTED/REVERSED, RevaluationEntry, FXDifference); enums `RateType`/`RevaluationStatus`/`PostingSide` in `base.py`; exceptions in `src/domain/exceptions/__init__.py`.
- Services: `currency_service.py`, `exchange_rate_service.py` (booking rate R1, bình quân gia quyền D5, CSV import atomic all-or-nothing), `revaluation_service.py` (period lock D8, prior-run reversal D7, balanced journal D6, self-approval blocked SOD).
- Infra: models in `src/infrastructure/database/models.py` (5 tables + 3 enum classes, unique constraint on rate rows); adapters in `src/infrastructure/repositories/currency_repo.py` (separate file, unlike company repo in `__init__.py`).
- REST: `src/presentation/api/currencies_bp.py` — 12 endpoints, `@casbin_required`, registered in `app.py`. Test engine hook `init_test_engine`/`_req_session` + `teardown_request` session restore (pattern to copy for other blueprints).
- Tests: 80 passing (`tests/unit/currency/`, `tests/integration/test_currencies_api.py`, `test_currencies_repository.py`).
- Spec: `docs/currencies-exchange/` (signed off). Excluded: NHNN sync (v1.5).
- Money = Decimal everywhere (rates Numeric(18,6), VND Numeric(18,2)). Actor UUID required on mutations (D11).

## Audit Log module status (complete)
- Service: `src/application/services/audit_log_service.py` (SHA-256 checksum chaining, 10-year retention per Luật Kế toán 2015, Certificate of Destruction).
- REST: `src/presentation/api/audit_log_bp.py` — `/api/retention-status`, `/api/verify-destruction/<id>`, `/api/destroy`; registered in `app.py`.
- Docs moved to `docs/audit-log/` (brd/specs/use-cases) 2026-08-18.

## Fiscal Years & Accounting Periods module status (SPEC ONLY — NOT IMPLEMENTED — NOT PROD-READY)
- Full spec set: `docs/fiscal-year-period/` (BRD, specs, use-cases, rules, processes, workflows, data-flows, user-journeys, templates, production-readiness-audit). Signed-off baseline for implementation.
- **Gaps (see production-readiness audit)**: `AccountingPeriodType.FISCAL_15` in `src/domain/entities/base.py:124` is LEGALLY ILLEGAL (Luật Kế toán 88/2015 Đ12 — fiscal year must start quarter-aligned: 01/01, 01/04, 01/07, 01/10); `PeriodLockService` is a stub (`is_locked` always False, `validate_before_entry` has ZERO callers — Voucher/Invoice posting NOT period-enforced); `period_locks` table too primitive; `SystemSettingsService.lock_period` 500s (missing repo adapter).
- Working patterns to reuse: `currency_repo.period_is_locked()` overlap query (currency_repo.py:203), `RevaluationService` `PeriodLockedError` (revaluation_service.py:75), currencies test-engine hook.
- Do NOT implement until specs §2–§5 (entities, ports, adapters, `fiscal_year_bp.py`) reviewed + sign-off recorded in `docs/fiscal-year-period/SIGN-OFF.md`.

## Toolchain
- Install deps: `uv pip install --python=.venv/bin/python <package>`
- Editable install: `uv pip install --python=.venv/bin/python -e .`
- Do NOT use bare `pip`.
- Code imports use `src.` prefix (e.g. `src.domain.entities`). `PYTHONPATH=src` already set in pytest config; no need to export it when running pytest.
- `uv` locks dependency versions in `uv.lock`.

## Commands
- Run dev server: `PYTHONPATH=src flask run` (or `FLASK_APP=app.py flask run`)
- Run tests: `uv run pytest` or `pytest` from venv
- Run one test: `pytest tests/unit/currency/test_currency_services.py -k test_create_run -v`
- Lint: `ruff check src tests`
- Format: `black src tests`
- Typecheck: `mypy src`
- Order for CI green: `ruff -> black --check -> mypy -> pytest`
- Migrations: `flask db init|migrate|upgrade` requires `SQLALCHEMY_DATABASE_URI` in env
- Supported DB URIs: `sqlite:///...`, `mysql://...`, `mariadb://...`, `postgresql://...`
- CLI management commands (scripts/manage.py):
  - `create-admin` — Create first admin user (run once on fresh deployment)
  - `create-user` — Create new user with role: `--email USER_EMAIL --role ROLE [--password PASSWORD]`
  - `assign-role` — Assign role to user: `--user USER --role ROLE`
  - `enable-user` — Enable user account: `--user USER`
  - `disable-user` — Disable user account: `--user USER`
  - `reset-password` — Reset user password: `--user USER --new-password PASS`
  - `list-users` — List all users with roles and status

## Architecture
```
src/
  domain/           # pure Python, NO sqlalchemy / web imports
    entities/       # Company, Partner, Invoice, Voucher, Currency*, User + value objects (TaxId, AccountCode) + CompanyConfig + enums
    exceptions/     # NotFoundError, AlreadyExistsError + module exceptions (currency, system_settings, ...)
    repositories/   # ports (abc interfaces)
  application/
    ports/          # repository/service interfaces (CompanyRepositoryPort, SystemSettingsRepositoryPort, CurrencyRepositoryPort, ...)
    services/       # CompanyService, SystemSettingsService, AuthService, CurrencyService*, ExchangeRateService*, RevaluationService*, AuditLogService
  infrastructure/
    database/
      models.py     # SQLAlchemy 2.0 DeclarativeBase models — enums duplicated with domain/base.py
    repositories/   # SQLAlchemyRepo adapters: __init__.py (company, system settings) + currency_repo.py (currencies — separate file)
  presentation/
    api/            # REST-ish blueprints: __init__.py (Company), users_bp.py, audit_log_bp.py, system_settings_bp.py, currencies_bp.py
    ui/             # HTML blueprints
    forms/          # WTForms
    serializers/    # domain -> JSON (partner/invoice/voucher/currency/exchange_rate/revaluation_run/fx_difference)
```
- Domain layer MUST stay free of `sqlalchemy` and web imports.
- Enums duplicated: domain (`src/domain/entities/base.py`) AND SQLAlchemy (`src/infrastructure/database/models.py`). Sync both when adding states/types.

## Domain rules (hard-coded)
- Tax IDs: `^\d{10}$` or `^\d{10}-\d{3}$` (Vietnamese MST).
- Account codes: `^[1-9]\d{2}$` or `^[1-9]\d{3}$` (Vietnamese chart of accounts — legacy Thông tư 200/2014/TT-BTC, superseded by **TT 99/2025/TT-BTC** from 01/01/2026; `TT99` enum exists in `base.py`).
- `Invoice.add_item()` recalculates `subtotal`, `vat_total`, `grand_total`.
- `Voucher.post()` requires balanced debit/credit (tol 0.01) and `DRAFT` status.
- `Partner.tax_id` joins invoices by value; domain wraps raw string in `TaxId`.
- System Settings: LAW-type flags immutable without migration; CONFIG-type admin-changeable with audit log + 2nd approval.
- Currencies: ISO code `^[A-Z]{3}$`; base currency immutable (D4); rate history append-only (D3); CSV import atomic (any bad row → nothing imported); revaluation self-approval blocked (D9 SOD); prior POSTED run reversed before re-run (D7, reversal only after new run computes successfully).

## Framework / infra
- Flask + `flask-migrate` + `Flask-Talisman` + `Flask-Bcrypt` + `Flask-Login` + `Flask-Security-Too` + `pycasbin` + `Flask-Babel` + `Flask-Caching` + `Flask-Marshmallow` (extensions installed).
- ⚠️ pycasbin 2.8.0 installed with fallback role-based enforcement; `@casbin_required(*allowed_roles)` decorator on API routes; AUDITOR is read-only; full pycasbin model parsing has compatibility issues being tracked separately.
- `Flask-Talisman` enforces HTTPS only when `DEBUG=False`. Use `DEBUG=1` for local dev.

## Coding Convention (MUST read before coding)
`docs/CODING_CONVENTION.md` is the source of truth for style, naming, layer boundaries, commits, and review rules. When writing or modifying ANY code:
1. Read and apply rules from that doc first.
2. Use it as referee when choices conflict.
3. If a rule must be bent, surface the tradeoff explicitly.

## Testing Strategy (MUST read before writing tests)
`docs/TESTING_STRATEGY.md` is the source of truth for HOW and WHAT to test. Any task touching tests or code with business logic MUST:
1. Read `docs/TESTING_STRATEGY.md` (esp. mục 5, 6, 7) before writing code.
2. Pick test level via decision tree mục 6.4 — no UI-level tests for pure logic, no E2E for edge cases, no E2E for everything.
3. Follow naming + layout mục 7.4–7.5; test data per mục 9 (factories, isolated state, order-independent, no real client data).
4. Finish by running `pytest` (green) and self-checking checklist mục 16.
5. Never: test implementation details, `sleep` in E2E, order-dependent tests, retry to hide flakes, coverage-chasing tests.

Flaky tests follow the policy in mục 11 (Fix / Quarantine / Delete) — open an issue with owner, never hide behind retries. CI/CD gating rules per mục 8.

## What NOT to do
- Don't write tests that violate `docs/TESTING_STRATEGY.md` (anti-patterns mục 17).
- Don't add SQLAlchemy or Flask imports inside `src/domain/`.
- Don't use bare `pip`; use `uv pip install --python=.venv/bin/python`.
- Don't add multi-company consolidation logic until Company entity + tenant isolation exist (research report flags 7 critical gaps).
- Don't implement System Settings REST adapter in this version — missing `SQLAlchemySystemSettingsRepository`; wait until system-settings model separation is resolved without test breakage.
- ❌ Do NOT assume RBAC is enforced only via UI/Flask-Login — `@casbin_required` decorator provides backend enforcement; AUDITOR role is read-only.
- ❌ Do NOT add role-based checks only in presentation templates — backend service methods must also enforce RBAC, or use the `@casbin_required` decorator pattern.
- ❌ Do NOT mix UI-only auth with backend logic that bypasses RBAC — this creates security shadows that audit will flag.

## CI / Git
- Commit: Conventional Commits format: `type(scope): description`; subject ≤50 chars.
- Branch: `type/ISSUE-ID-description` (feature/bugfix/hotfix/refactor).
- PR: Must have 1 reviewer approve before merge.
- CI gates: `ruff -> black --check -> mypy -> pytest` must all pass.
- Codegraph sync: run `codegraph_explore` at milestones after domain/entity changes.
- Do not git push if review has not passed.