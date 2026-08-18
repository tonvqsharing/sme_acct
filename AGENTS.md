# AGENTS — Vietnamese SME Accounting App

## Repo state
- Flask + Clean Architecture scaffold + Company module complete.
- Root entrypoint: `app.py` (`create_app()` factory, `python-dotenv` loading wired).
- `.venv` managed by `uv`. Always activate: `source .venv/bin/activate`. No bare `pip` — use `uv pip install --python=.venv/bin/python`.
- `pyproject.toml` present (hatchling, `src/` wheel). Python >= 3.11.
- `pytest` configured (`testpaths=tests`, `pythonpath=src`). 65 tests passing.
- `templates/base.html` uses local Bulma + HTMX (no CDN, offline-capable).
- Migration: `flask db init|migrate|upgrade` requires `SQLALCHEMY_DATABASE_URI` in env; supported URIs: `sqlite:///...`, `mysql://...`, `mariadb://...`, `postgresql://...`.

## Company module status (complete)
- Domain entity: `src/domain/entities/company.py` (Company aggregate root, status lifecycle).
- Domain enums: `CompanyType`, `CompanyStatus`, `AccountingRegime` in `src/domain/entities/base.py`.
- Repository port: `CompanyRepositoryPort` in `src/application/ports/__init__.py`.
- DB models: `CompanyModel`, `BankAccountModel` in `src/infrastructure/database/models.py`; `company_id` FK on `PartnerModel`, `InvoiceModel`, `VoucherModel`.
- Repository adapter: `SQLAlchemyCompanyRepository` in `src/infrastructure/repositories/__init__.py` (`create` + `update`).
- Unit tests: 32 passing (`tests/unit/company/`).
- Integration tests: 15 passing (`tests/integration/test_company_repository.py`, `test_company_api.py`).
- REST API endpoints: POST/GET/GET/{id}/PATCH/{id}/suspend/{id}/reactivate/{id}/dissolve.

## System Settings module status (Phase 1 domain complete, migration applied)
- **Domain layer** (complete): `FlagType`/`FlagScope`/`FlagCategory` enums; `AccountingPeriodType`; `VATMethod`/`EInvoiceMode`/ `EInvoiceSeries` dataclass; `CompanyConfig` aggregate; exceptions (`SystemSettingsError`, `FlagLockedError`, `ConfigVersionConflict`, `InvalidVATRateError`, `InvalidCAListError`, `InvalidRegimeError`).
- **Migration** (applied): `flask db migrate` generated 4 new tables (`audit_log`, `ca_list_entries`, `e_invoice_series`, `period_locks`); `flask db upgrade` applied.
- **Service layer** (complete): `SystemSettingsService` with `get_config`, `update_config`, `lock_period`, `unlock_period`, `validate_vat_rate`, `add_e_invoice_series` — follows `CompanyService` pattern, NO Flask/SQLAlchemy imports.
- **Repository port** (complete): `SystemSettingsRepositoryPort` in `src/application/ports/__init__.py`.
- **REST API** (deferred): Requires separate model migration to avoid test breakage; will be implemented in next version.

## Toolchain
- Install deps: `uv pip install --python=.venv/bin/python <package>`
- Editable install: `uv pip install --python=.venv/bin/python -e .`
- Do NOT use bare `pip`.
- Code imports use `src.` prefix (e.g. `src.domain.entities`). `PYTHONPATH=src` already set in pytest config; no need to export it when running pytest.
- `uv` locks dependency versions in `uv.lock`.

## Commands
- Run dev server: `PYTHONPATH=src flask run` (or `FLASK_APP=app.py flask run`)
- Run tests: `uv run pytest` or `pytest` from venv
- Run one test: `pytest tests/unit/test_partner.py -k test_name -v`
- Lint: `ruff check src tests`
- Format: `black src tests`
- Typecheck: `mypy src`
- Order for CI green: `ruff -> black --check -> mypy -> pytest`
- Migrations: `flask db init|migrate|upgrade` requires `SQLALCHEMY_DATABASE_URI` in env
- Supported DB URIs: `sqlite:///...`, `mysql://...`, `mariadb://...`, `postgresql://...`

## Architecture
```
src/
  domain/           # pure Python, NO sqlalchemy / web imports
    entities/       # Partner, Invoice, Voucher + value objects (TaxId, AccountCode) + CompanyConfig + enums
    exceptions/     # NotFoundError, AlreadyExistsError, InvalidVoucher, InvalidInvoice + SystemSettings exceptions
    repositories/   # ports (abc interfaces)
  application/
    ports/          # repository/service interfaces (CompanyRepositoryPort, SystemSettingsRepositoryPort)
    services/       # CompanyService (18 unit tests, all pass), SystemSettingsService
  infrastructure/
    database/
      models.py     # SQLAlchemy 2.0 DeclarativeBase models (CompanyModel + new System Settings tables)
    repositories/   # SQLAlchemyRepo adapters (SQLAlchemyCompanyRepository + system settings adapter)
  presentation/
    api/            # REST-ish blueprints (Company API endpoints + System Settings API)
    ui/             # HTML blueprints
    forms/          # WTForms
    serializers/    # domain -> JSON
```
- Domain layer MUST stay free of `sqlalchemy` and web imports.
- Enums duplicated: domain (`src/domain/entities/base.py`) AND SQLAlchemy (`src/infrastructure/database/models.py`). Sync both when adding states/types.

## Domain rules (hard-coded)
- Tax IDs: `^\d{10}$` or `^\d{10}-\d{3}$` (Vietnamese MST).
- Account codes: `^[1-9]\d{2}$` or `^[1-9]\d{3}$` (Vietnamese chart of accounts per Thông tư 200/2014/TT-BTC).
- `Invoice.add_item()` recalculates `subtotal`, `vat_total`, `grand_total`.
- `Voucher.post()` requires balanced debit/credit (tol 0.01) and `DRAFT` status.
- `Partner.tax_id` joins invoices by value; domain wraps raw string in `TaxId`.
- System Settings: LAW-type flags immutable without migration; CONFIG-type admin-changeable with audit log + 2nd approval.

## Framework / infra
- Flask + `flask-migrate` + `Flask-Talisman` + `Flask-Bcrypt` + `Flask-Login` + `Flask-Security-Too` + `pycasbin` + `Flask-Babel` + `Flask-Caching` + `Flask-Marshmallow` (extensions installed).
- ⚠️ CRITICAL: `pycasbin 2.8.0` is installed but NOT implemented in the codebase. RBAC enforcement is currently UI/Flask-Login only — ❌ P0-10 production-readiness gap.
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
- Don't implement System Settings REST API in this version — deferred until model separation is resolved without test breakage.
- ❌ Do NOT assume RBAC is enforced — pycasbin is installed but not implemented; UI/Flask-Login checks are insufficient for PROD (P0-10 audit gap).
- ❌ Do NOT add role-based checks only in presentation templates — backend service methods must also enforce RBAC, or use the `@casbin_required` decorator pattern.
- ❌ Do NOT mix UI-only auth with backend logic that bypasses RBAC — this creates security shadows that audit will flag.

## CI / Git
- Commit: Conventional Commits format: `type(scope): description`; subject ≤50 chars.
- Branch: `type/ISSUE-ID-description` (feature/bugfix/hotfix/refactor).
- PR: Must have 1 reviewer approve before merge.
- CI gates: `ruff -> black --check -> mypy -> pytest` must all pass.
- Codegraph sync: run `codegraph_explore` at milestones after domain/entity changes.
- Do not git push if review has not passed.