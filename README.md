# sme_acct — Vietnamese SME Accounting

Flask + SQLAlchemy, Modular Hexagonal ("Lego bricks"), SQLite, Flask-Login RBAC. Covers Vietnamese SME compliance: `TT99/2025`, `TT58/2026`, `NĐ254/2026+TT91/2026` (e-invoice 01/07/2026), VAT `0/5/8/10/-1` with `NQ204/ND174` 8% window →31/12/2026, `NĐ181` non-cash ≥5tr.

**Status:** 18 bricks, 17 DB Bases, 968 tests green (`ruff`/`black`/`mypy strict` + `pytest`), CI `3.11+3.12`.

---

## Quickstart

```bash
# 1) Install (uv auto-creates .venv)
uv sync

# 2) Run dev server (auto-creates SQLite :memory: or file via env)
uv run python -c "from src.app import create_app; create_app().run(port=5000)"
# or:
DATABASE_URL="sqlite:///./sme_acct.db" uv run python -m src.app

# 3) Quality gates (CI order)
uv run ruff check src tests
uv run black --check src tests
uv run mypy --ignore-missing-imports src/bricks/   # python_version 3.13
uv run pytest -q                                   # 968 passing

# 4) Focused test
uv run pytest tests/unit/company/ -k "<name>" -v
uv run pytest tests/integration/test_company_api.py -v
```

**Env:** `SECRET_KEY` required outside `TESTING` (factory raises `RuntimeError`); defaults to `dev-secret-change-in-production` only when `TESTING=True`. `SQLALCHEMY_DATABASE_URI` / `DATABASE_URL` default `sqlite:///:memory:`.

---

## Tech Stack

| Layer | Choice |
|---|---|
| App | Flask 3.1, Flask-Login 0.6 (session, not JWT), Werkzeug |
| ORM | SQLAlchemy 2.0, Alembic 1.19 |
| DB | SQLite (dev/test/PROD single-file), 17 `Base` aggregated in `alembic/env.py` |
| Auth | Flask-Login `user_loader` → `users` table, pbkdf2 hashing, `@login_required` + `current_user.role` |
| Docs→MD | `markitdown[all] 0.1.7` (Microsoft) — PDF/DOCX/XLSX/HTML/CSV → Markdown for LLM |
| Lint/Format/Type | ruff 0.16 + black 26.5 + mypy 2.3 `strict=true` (ignore `markitdown.*`, `numpy.*`, `tools_equipment.storage`) |
| Test | pytest 9.1, 968 tests (unit + integration), `testpaths=["tests"]`, `pythonpath=["src"]` |

**Line length 100** (ruff + black).

---

## Architecture — Lego Bricks

```
src/bricks/<name>/
  contract.py     # ABC ports — primitives only (str/int/Decimal/UUID/dict)
  domain.py       # pure Python, ZERO Flask/SQLAlchemy — business rules + enums
  services.py     # orchestration via port (FY gate → COA gate → invariant)
  storage.py      # SQLAlchemy models + repo adapter (only file with SQLAlchemy)
  web_adapter.py  # Flask Blueprint — ONLY file with Flask (routes, @login_required, RBAC)
```

`src/app.py` = composition root. Wiring order matters: `coa_service` + `fy_service` first (invoice/voucher consume `app.coa_service`/`app.fy_service`). Cross-brick calls via thin adapters inline (`_NumberingAdapter`, `_TermsAdapter`, `_COAServiceAdapter`, `_PeriodLockAdapter`) — never import another brick's `storage` into a service. Add `Base.metadata.create_all(engine)` per brick and `Base` to `alembic/env.py:target_metadata`.

**Gate order (invoice & voucher):** `fiscal period OPEN` → `COA posting accounts (ACTIVE + detail)` → `balance/invariant (TOLERANCE 0.01)`. Ledger reports read via `LedgerSourcePort` flat primitive rows — never join voucher models.

**Brick boundaries (PR reject if violated):** no cross-brick SQLAlchemy joins; `domain.py` purity law; mock target `contract.py` in tests; `CONFIG_FLAGS = frozenset({...})` allowlist in domain, `with_flag_update()` validates.

Specs may mention Casbin/`src/presentation/api/*_bp.py` — ignore; use Flask built-in checks + brick layout.

---

## Bricks (18) — Module Status

| Brick | What | Routes |
|---|---|---|
| **company** | Tenant root, `TaxId` `^[1-9]\d{2}(-\d{3})?$`, `AccountingRegime` TT99/TT58/TT133 | `web_adapter_bp` |
| **payment_terms** | Terms + numbering series `HD*/PT*` SOD `202`, approvals `request→202→approve/reject` | `payment_terms_bp`, `document_numbering_bp` |
| **audit_log** | Append-only checksum chain `seq` + `ts_iso` (SQLite µs fix), `actor uuid5(system:numbering)` | `audit_log_bp` |
| **fiscal_year_period** | FY + monthly periods + posting gate | `fiscal_year_bp` |
| **coa** | Chart `^[1-9]\d{2}$|^[1-9]\d{3}$`, hierarchy, posting/active/detail | `coa_bp` |
| **invoice** | HD* numbering, VAT catalog `{0,5,8,10,-1}` + `rate_gate` by doc date + 8% `is_8pct_eligible` category gate (all lines) | `invoice_bp` |
| **voucher** | PT* numbering, double-entry `TOLERANCE 0.01`, FY+COA gates, `on_posted` → cash/bank | `voucher_bp` |
| **ledger** | `general_journal` + `trial_balance` via `LedgerSourcePort` (POSTED only) | `ledger_bp` |
| **bank_cash** | Bank/cash masters, balances, reconciliation SOD | `bank_cash_bp` |
| **purchases** | Supplier invoices, `Deductibility {DEDUCTIBLE/PENDING_PROOF/NON_DEDUCTIBLE}` R-P4/R-P5, `NON_CASH_THRESHOLD=5tr` (NĐ181), `submit_proof` `PENDING→DEDUCTIBLE` | `purchases_bp` |
| **system_settings** | Period lock, `CONFIG_FLAGS`, `CompanyConfig` LAW/CONFIG, `TaxRate {0,5,8,10,-1}`, `TaxRateWindow` `VAT_REDUCTION_END 2026-12-31`, `VatCarryModel` carry persist, `VatDeclaration 01/GTGT` monthly/quarterly + `?format=gdt_xml` | `settings_bp` |
| **currencies** | `Currency` ISO4217 (VND base), `ExchangeRate` Tryton gap-fill, `resolve_booking_rate` Nợ=actual/Có=weighted-avg (TT99), `RevaluationRun` SOD | `currencies_bp` |
| **user_master_data** | `User` pbkdf2, `login/logout/me` + user CRUD, real `user_loader` | `auth_bp`, `users_bp` |
| **fixed_assets** | TSCĐ SL depreciation, grouped journal, capped remaining, deactivate | `fixed_assets_bp` |
| **tools_equipment** | CCDC lifecycle `ACTIVE→INACTIVE→WRITTEN_OFF`, monthly allocation SOD | `tools_equipment_bp` |
| **xml_ingest** | TT91 symbol parser, GDT XML namespace-aware, `PurchaseService` bridge, batch | `xml_ingest_bp` |
| **cost_centers** | Centers + `Dimension/DimensionValue` lifecycle, checksum chain | `cost_centers_bp` |
| **financial_statements** | `ReportEngine` B01-DN/B02-DN/B03-DN per TT99 Appendix IV, `PeriodCloseService` TT99 §7 (revenue→911, expense→911, CIT 8211/3334, lock) | `reports_bp` (`/close-month`, `/b01`, `/b02`, `/b03`, `/general-journal`, `/trial-balance`, `/vat-declaration`) |
| **document_conversion** | MarkItDown `PDF/DOCX/XLSX/HTML/CSV→Markdown` for LLM, `MAX_BYTES 20MB`, `ALLOWED 24 ext`, `convert/convert-batch/supported-types` | `document_conversion_bp` |

---

## RBAC

`@login_required` on every route + `current_user.role`:

| Action | Roles |
|---|---|
| Create company | `ADMIN` |
| Update company | `ADMIN, ACCOUNTANT` |
| Suspend company | `CHIEF_ACCOUNTANT` |
| Read anything | any authenticated (incl. `AUDITOR`) |
| AUDITOR writes | forbidden (403) |

---

## API Overview

Base `/api/v1/` — JSON `snake_case`, errors `{"error":"...","code":"..."}` Vietnamese message, English keys.

```
# Company
POST   /api/v1/companies
GET    /api/v1/companies /<id>
PATCH  /api/v1/companies/<id>
POST   /api/v1/companies/<id>/suspend

# VAT & Config
GET    /api/v1/system-settings/tax-rates
GET/POST /api/v1/tax-rate-windows[?on=YYYY-MM-DD]
GET/PATCH /api/v1/system-settings/config/<cid>
POST   /api/v1/system-settings/e-invoice-series

# VAT declaration
GET    /api/v1/reports/vat-declaration?company_id&year&month|quarter[&format=gdt_xml]
# gdt_xml → <?xml 01/GTGT ...> for thuedientu.gdt.gov.vn

# Invoices / Vouchers / Ledger
POST   /api/v1/invoices            # vat_rate + items[].category + rate_gate + 8% gate
GET    /api/v1/invoices[?company_id]
POST   /api/v1/invoices/<id>/post # auto-journal voucher
POST   /api/v1/vouchers            # FY+COA+balance gates
POST   /api/v1/vouchers/<id>/post
GET    /api/v1/reports/general-journal?company_id&from&to
GET    /api/v1/reports/trial-balance?company_id&from&to
GET    /api/v1/reports/b01|b02|b03?company_id&year&month

# Purchases
POST   /api/v1/purchase-invoices            # lines[].vat_rate + category + rate_gate
POST   /api/v1/purchase-invoices/<id>/post
POST   /api/v1/purchase-invoices/<id>/proof # PENDING_PROOF → DEDUCTIBLE (NĐ181)
POST   /api/v1/purchase-invoices/<id>/cancel

# Document conversion (MarkItDown)
POST   /api/v1/documents/convert            # multipart file → {markdown}
POST   /api/v1/documents/convert-batch      # ≤10 files
GET    /api/v1/documents/supported-types

# Other
POST   /api/v1/xml-ingest/upload  (single/batch)
GET    /api/v1/bank-accounts /cash-accounts /reconciliations
GET    /api/v1/fiscal-years /periods /coa/accounts
```

Full per-brick specs under `docs/<module>/` (BRD → specs → use cases).

---

## Testing

```bash
uv run pytest -q                                   # 968
uv run pytest tests/unit/document_conversion -v
uv run pytest tests/integration/test_financial_statements_api.py -v
```

- Unit: `tests/unit/<brick>/` — may hand-build minimal Flask app (`FakeUser(UserMixin)` + `_store` + `session_transaction`), mock target `contract.py`.
- Integration: `tests/integration/` — must go through real `create_app(config={"TESTING": True})`.
- Shared fixtures: `tests/integration/conftest.py` (`app`, `admin_client`, `accountant_client`, `chief_client`, `auditor_client`, `UUID_*`, `_store`, `FakeUser`). Import `UUID_*` from there, never fixture functions (F811). `tests/__init__.py` must exist (empty) else two `_store` → 401.
- Auth: real `user_loader`; stub `app.login_manager.user_loader` or `POST /api/v1/auth/login` via `UserService`.
- No `sleep()`.

---

## Migrations

`alembic/env.py` aggregates 17 `Base.metadata`.

```bash
DATABASE_URL="sqlite:///./sme_acct.db" uv run alembic upgrade head
DATABASE_URL="sqlite:///./sme_acct.db" uv run alembic revision --autogenerate -m "desc"
# review: replace src.bricks.*.*Type() with sa types (e.g. sa.Text() for JSONType)
```

Models: `companies`, `system_settings`, `tax_rate_windows`, `vat_carry_forwards`, `period_locks`, `supplier_invoices`, `vouchers`, `invoices`, `bank/cash`, etc.

---

## Document Conversion — MarkItDown Operation

See `docs/document_conversion/OPERATION.md` (237 lines) — TL;DR:

```bash
uv run markitdown path.pdf > doc.md                 # CLI
# Python
from src.bricks.document_conversion.services import DocumentConversionService
svc = DocumentConversionService()  # offline, enable_plugins=False
res = svc.convert_bytes(data=open("HoaDon.pdf","rb").read(), file_name="HoaDon.pdf")
# res.markdown → LLM → purchase_svc.create_invoice(...)
```

- `POST /documents/convert` single, `POST /convert-batch` ≤10, `GET /supported-types` — all `@login_required`, `MAX_BYTES 20MB`, `ALLOWED 24 ext`, `../` blocked → `422`.
- Security per upstream: only `convert_stream`/`convert_bytes` (narrowest), `validate_file_name` at domain boundary, `MAX_MARKDOWN_CHARS 500k` truncated with warning, plugins disabled by default.

---

## Docs Are Truth

Before code change, read `docs/CODING_CONVENTION.md` + `docs/TESTING_STRATEGY.md`, then `docs/<module>/` (BRD → specs → use cases). Rebuild from specs, not git archaeology.

Audit-chain: `seq` per entity (not timestamps), persist verbatim `ts_iso`, auto-numbering `uuid5(NAMESPACE_URL,"system:numbering")`.

Compliance (2026-08, mof.gov.vn/vbpl.vn): MST `^[1-9]\d{2}(-\d{3})?$`, account codes `^[1-9]\d{2}$|^[1-9]\d{3}$`, TT99/2025 replaces TT200, TT58/2026 replaces TT132, NĐ254/2026+TT91/2026 replaces NĐ123/2020+70/2025 & TT32/2025, input VAT ≥5tr non-cash (Luật GTGT 2024 Đ.14 + NĐ181 Đ.26), VAT 8% `NQ204/ND174` →31/12/2026 (`rate_windows.py`), 10-year retention.

---

## Adding a New Brick

1. Create `src/bricks/<name>/` 5-file layout
2. `src/app.py`: `Base.metadata.create_all(engine)` + blueprint + `init_*_service()` in dependency order + `DocConvBase` style
3. `alembic/env.py`: `Base` import + `target_metadata`
4. `tests/unit/<name>/` + `tests/integration/test_<name>_api.py`
5. No cross-brick model imports

---

## Commits

Conventional Commits: `type(scope): description` — `feat/fix/refactor/perf/docs/test/chore/build/ci/style/revert`; scope = brick name (`fix(company): ...`).

---

## License

Internal SME accounting — VACPA/VAA compliant. MarkItDown MIT (`microsoft/markitdown` 0.1.7).
