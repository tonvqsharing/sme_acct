# AGENTS.md

## Repo state

- Vietnamese SME accounting app, Flask + Clean Architecture scaffold + Company module implemented.
- Root entrypoint: `app.py` (`create_app()` factory, `python-dotenv` loading wired).
- `.venv` managed by `uv`. Always activate it first: `source .venv/bin/activate`. No bare `pip` — use `uv pip install --python=.venv/bin/python`.
- `pyproject.toml` present (hatchling, `src/` wheel). Python >= 3.11.
- `pytest` configured (`testpaths=tests`, `pythonpath=src`). 47 tests: 32 unit + 15 integration.
- `templates/base.html` uses local Bulma + HTMX (no CDN, offline-capable).
- `docs/multi-company/` has research/BRD/specs/workflows (multi-company NOT ready per research report).

## Company module status

- Domain entity: `src/domain/entities/company.py` (Company aggregate root, 20+ fields, status lifecycle).
- Domain enums: `CompanyType`, `CompanyStatus`, `AccountingRegime` in `src/domain/entities/base.py`.
- Repository port: `CompanyRepositoryPort` in `src/application/ports/__init__.py`.
- DB models: `CompanyModel`, `BankAccountModel` in `src/infrastructure/database/models.py`; `company_id` FK on `PartnerModel`, `InvoiceModel`, `VoucherModel`.
- Repository adapter: `SQLAlchemyCompanyRepository` in `src/infrastructure/repositories/__init__.py` (`create` + `update`).
- Unit tests: 32 passing (TDD red-green-refactor): `tests/unit/company/`.
- Integration tests: 15 passing (in-memory SQLite, no Flask app context): `tests/integration/test_company_repository.py`.
- Migration: `flask db migrate` not yet run (local SQLite; no env var file present per AGENTS.md).

## Toolchain

- Install deps: `uv pip install --python=/home/projects/sme_acct/.venv/bin/python <package>`
- Editable install: `uv pip install --python=/home/projects/sme_acct/.venv/bin/python -e .`
- Do NOT use bare `pip`.
- Code imports use `src.` prefix (e.g. `src.domain.entities`). `PYTHONPATH=src` already set in pytest config; no need to export it when running pytest.

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
    entities/       # Partner, Invoice, Voucher + value objects (TaxId, AccountCode)
    exceptions/     # NotFoundError, AlreadyExistsError, InvalidVoucher, InvalidInvoice
    repositories/   # ports (abc interfaces)
  application/
    ports/          # repository/service interfaces
    services/       # PartnerService, InvoiceService, VoucherService
  infrastructure/
    database/
      models.py     # SQLAlchemy 2.0 DeclarativeBase models
    repositories/   # SQLAlchemyRepo adapters
  presentation/
    api/            # REST-ish blueprints
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

## Framework / infra

- Flask + `flask-migrate` + `Flask-Talisman` + `Flask-Bcrypt` + `Flask-Login` + `Flask-Security-Too` + `pycasbin` + `Flask-Babel` + `Flask-Caching` + `Flask-Marshmallow` (extensions installed).
- `Flask-Talisman` enforces HTTPS only when `DEBUG=False`. Use `DEBUG=1` for local dev.
- `.env.example` not present — copy required vars from `app.py` config block if spinning up fresh.

## Coding Convention (MUST read before coding)

`docs/CODING_CONVENTION.md` is the source of truth for style, naming, layer boundaries, commits, and review rules.
When writing or modifying ANY code:
1. Read and apply rules from that doc first.
2. Use it as referee when choices conflict.
3. If a rule must be bent, surface the tradeoff explicitly.

## What NOT to do

- Don't add SQLAlchemy or Flask imports inside `src/domain/`.
- Don't use bare `pip`; use `uv pip install --python=.venv/bin/python`.
- Don't add multi-company consolidation logic until Company entity + tenant isolation exist (research report flags 7 critical gaps).