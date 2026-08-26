# AGENTS — Vietnamese SME Accounting App

_Flask + SQLAlchemy app for Vietnamese SME accounting. Architecture: Modular Hexagonal ("Lego bricks"). DB: SQLite3. RBAC: Flask-Login built-in._

## Commands

Package manager is `uv`. Prefix everything with `uv run` — no venv activation needed.

```bash
uv run pytest -q                                  # full suite (currently 548 passing)
uv run pytest tests/unit/company/ -k "<name>" -v  # single test / focused run
uv run ruff check src tests                       # lint
uv run black --check src tests                    # format check
uv run mypy --ignore-missing-imports src/bricks/  # typecheck
uv run python -c "from src.app import create_app; create_app().run(port=5000)"  # dev server
```

**Quality gate order before EVERY commit:** ruff ➔ black ➔ mypy ➔ pytest. All four must pass. CI (`.github/workflows/ci.yml`) runs the same gates on Python 3.11 + 3.12.

## Toolchain Gotchas (hard-won — don't rediscover)

- **`mypy` fails without `--ignore-missing-imports`** — `pyproject.toml` sets `strict = true`, and `flask_login` ships no stubs (`import-untyped`). The flag is mandatory; CI includes it.
- **Untyped-decorator ignores go on the `@login_required` line**, NOT the `def` line. Mypy attributes the `[untyped-decorator]` error to the decorator line; an ignore on `def` reports as `unused-ignore` while the real error survives.
- **Route return annotation is `tuple[Any, int]`**, not `tuple[dict, int]` — `jsonify()` returns a Flask `Response`, so `tuple[dict, int]` triggers `[return-value]` errors.
- **Line length is 100** (ruff + black both configured in `pyproject.toml`), not the 88 default.
- **Never use `uv sync --no-dev` locally or in CI** — it strips ruff/black/mypy/pytest (they are dev deps).
- **mypy strict bans bare `dict`** — write `dict[str, Any]` everywhere, including port/contract signatures and JSON-typed SQLAlchemy columns.
- **ruff C408** forbids `dict(...)` calls (use literals) and **RUF059** flags unused tuple-unpack targets (`_`-prefix them).
- **SQLAlchemy + `from __future__ import annotations`:** all types referenced in `Mapped[...]` annotations MUST be imported in the module namespace — SQLAlchemy evaluates the stringified annotations at class-definition time. Missing `date`, `Decimal`, `JSON`, or `uuid4` imports cause cryptic `NameError`/`MappedAnnotationError` at import time.

## Architecture: Lego Bricks

Each module = one self-contained brick under `src/bricks/<name>/`:

```
src/bricks/<name>/
├── contract.py     # PUBLIC interface — ABC ports, primitives only in/out
├── domain.py       # Pure Python entities/value objects. ZERO Flask/SQLAlchemy imports
├── services.py     # Business logic, orchestrates repo via port
├── storage.py      # SQLAlchemy models + repository adapter implementing port
└── web_adapter.py  # Flask blueprint + routes. ONLY file allowed to import Flask
```

`src/app.py` = composition root. **SECRET_KEY env var is mandatory outside TESTING** (fail-fast at factory). Wiring order matters: COA + FY services must exist before invoice/voucher blocks (they consume `app.coa_service` / `app.fy_service`). Cross-brick needs are met by thin adapters defined inline there (`_NumberingAdapter`, `_TermsAdapter`) that translate brick contracts to narrow callables — do NOT import one brick's storage into another's service.

**Transaction gate order (invoice & voucher services):** fiscal-period open → COA posting accounts (ACTIVE + detail only) → balance/invariant. Keep this order; reports and tests assume it.

**Ledger reads:** reports never touch voucher models — they consume a `LedgerSourcePort` returning flat primitive rows. Swap storage behind the port freely.

**Brick boundaries (violations = PR reject):**
- No cross-brick SQLAlchemy joins. Cross-brick calls go through the target's `contract.py`, passing primitives (`str`, `int`, `Decimal`, `UUID`, `dict`) only.
- Domain layer purity is architectural law: no Flask/SQLAlchemy imports in `domain.py`.
- When testing cross-brick calls, mock the target brick's `contract.py`.

**Known spec-vs-repo conflicts** — specs predate the brick structure:
1. Specs reference Casbin ("CASRBAC"). **Never import casbin/pycasbin** — translate role matrices to Flask built-in checks.
2. Some specs give paths like `src/presentation/api/*_bp.py`. Follow the brick layout above instead.

## RBAC (Flask built-in only)

`@login_required` on every route + explicit role checks on `current_user.role`:

| Action | Allowed roles |
|---|---|
| Create company | ADMIN |
| Update company | ADMIN, ACCOUNTANT |
| Suspend company | CHIEF_ACCOUNTANT |
| Read anything | any authenticated user (incl. AUDITOR) |
| AUDITOR writes | forbidden — read-only role |

## Testing

- Unit tests: `tests/unit/<brick>/` — may hand-build a minimal Flask app with fixtures (see `tests/unit/test_company_web_adapter.py`: `FakeUser(UserMixin)` + `_store` dict + `session_transaction` login).
- Integration tests: `tests/integration/` — MUST go through real `create_app()`.
- **Shared fixtures live in `tests/integration/conftest.py`**
- **`tests/__init__.py` must exist** — without it pytest imports conftest as top-level `conftest` while explicit imports create a second module instance; two `_store` dicts → mystery 401s across the suite (`app`, `admin_client`, `accountant_client`, `chief_client`, `auditor_client`, `UUID_*`). Import the UUID *constants* from there — never import the fixture functions themselves (they shadow pytest params → F811).
- **Auth:** real `user_loader` is wired (looks up users table). Two options for tests:
  1. **Stub override** (legacy, still works): register test `user_loader` on `app.login_manager` — see `tests/unit/test_company_web_adapter.py`
  2. **Real login**: create a user via `_user_service.create_user(...)` then POST `/api/v1/auth/login` — see `tests/integration/test_auth_api.py`
  Unauthorized requests return 401 JSON via permanent `unauthorized_handler` in the factory.
- Each brick gets its own suite. No `sleep()` in tests.

## Adding a New Brick (checklist)

When implementing a new brick from specs:

1. Create `src/bricks/<name>/` with the 5-file layout above
2. Add `Base.metadata.create_all(engine)` in `app.py`
3. Add the brick's `Base` import + metadata to `alembic/env.py` `target_metadata`
4. Add blueprint registration + `init_*_service()` wiring in `app.py` **in dependency order**
5. Create `tests/unit/<name>/` and `tests/integration/test_<name>_api.py`
6. Bump test count in AGENTS.md Commands section

## Docs Are Truth — Read Before Implementing

Mandatory reads before ANY code change:
1. `docs/CODING_CONVENTION.md`
2. `docs/TESTING_STRATEGY.md`

Then read the target module's specs under `docs/<module>/` (BRD → specs → use cases). Rebuild from specs, never from git archaeology.

**Audit-chain data rules (audit_log + payment_terms checksums):**
- Chain events need deterministic ordering → per-entity `seq` column, NOT timestamps (ties broke chains when uuid tiebreak was used).
- Any string hashed into a checksum must be persisted verbatim: SQLite datetime round-trip loses microseconds vs `.isoformat()`, so audit rows carry a `ts_iso` string column.
- Auto-numbering increments require a real UUID actor — use a `uuid5(NAMESPACE_URL, "system:numbering")` system identity, `None` trips EX-001.

Vietnamese compliance rules baked into specs: MST tax-ID format (`^[1-9]\d{2}(-\d{3})?$`-family — see `TaxId` in company domain), accounting codes match `^[1-9]\d{2}$` or `^[1-9]\d{3}$`, regimes per mof.gov.vn/vbpl.vn as of 2026-08: TT99/2025 (replaced TT200), TT58/2026 (replaced TT132/2018), TT133/2016 in force; e-invoice law moved 01/07/2026 - NĐ 254/2026 + TT 91/2026 replace NĐ 123/2020+70/2025 & TT 32/2025; input-VAT >=5tr non-cash proof per Luật GTGT 2024 Đ.14 + NĐ 181/2025 Đ.26 (sửa NĐ 144/2026), VAT 8% reduced rate per NQ 204/2025/QH15 + NĐ 174/2025/NĐ-CP eff →31/12/2026 (date-effective gate in rate_windows.py — sunset auto-enforced by document date) (excl. viễn thông/tài chính/BĐS/kim loại/khai khoáng/TTĐB-trừ-xăng), 10-year retention (Luật Kế toán 2015 Art. 11).

## Module Status

| Module | Code | Specs |
|---|---|---|
| Company | ✅ done — unit + integration suites green | `docs/company-module/` |
| Payment Terms & Doc Numbering | ✅ done incl. SOD two-actor flow (request→202, approve/reject) | `docs/payment-terms/` |
| Audit Log | ✅ core done — append-only checksum chain (17 tests); API/filters pending spec session | `docs/audit-log/` |
| Fiscal Year & Periods | ✅ core done — years/monthly periods/posting gate + web create/list (18 tests) | `docs/fiscal-year-period/` |
| Chart of Accounts | ✅ core done — codes/hierarchy/posting gate + SQLite repo + web CRUD (33 tests) | `docs/coa/` |
| Invoice + Voucher + Ledger core loop | ✅ invoice/voucher bricks done; ledger reports done (325 total) | — |
| Bank/Cash Accounts | ✅ core done — bank+cash masters, balances, balances auto-move with vouchers; bank reconciliation w/ SOD resolve done (15 tests) | `docs/bank-cash/` |
| Purchase Invoices | ✅ core done — supplier invoices, deductibility engine (R-P4/R-P5), duplicate guard, SOD-lite cancel (25 tests); XML ingest v2 | docs/purchases/ |
| Tax Engine (config + VAT declaration) | ✅ done — TaxRate catalog {0,5,8,10,-1} w/ date-effective windows, LAW-locked vat_rates, e-invoice series w/ SOD, 01/GTGT aggregation endpoint, tax_rate_windows master table w/ date-effective gate + SOD admin API (33 tests) | `docs/tax-engine/` |
| Currencies | ✅ slices 1-2 done — Currency master (ISO 4217, VND base), ExchangeRate w/ Tryton gap-fill, resolve_booking_rate (Nợ=actual/Có=weighted-avg per TT99), RevaluationRun engine w/ SOD + idempotent reversal (34 tests); multi-currency voucher lines w/ currency_code+fx_rate+amount_original; bank balances auto-move with bank_account_id-tagged lines | `docs/currencies-exchange/` |
| User Master Data / Auth | ✅ done — User entity w/ pbkdf2 hashing (deviation from spec SHA-256, justified), login/logout/me + user CRUD APIs, real user_loader wired in factory, session-based auth; 22+ tests | `docs/user-master-data/` |
| Fixed Assets (TSCĐ) | 📋 specs complete (`docs/fixed-assets/`, 4 docs) — code pending; straight-line depreciation per TT99/2025 Phụ lục 2 | `docs/fixed-assets/` |
| System Settings (rest), Cost Centers, Multi-company | pending | `docs/<module>/` |

## Migrations

Alembic manages schema. `alembic/env.py` aggregates all 11 brick Bases.

```bash
DATABASE_URL="sqlite:///./sme_acct.db" uv run alembic upgrade head    # apply
DATABASE_URL="sqlite:///./sme_acct.db" uv run alembic revision --autogenerate -m "desc"  # new
```

After autogenerate: **review the migration file** — replace any `src.bricks.*.*Type()` custom-type references with their underlying sa types (e.g., `sa.Text()` for JSONType).

## Commits

Conventional Commits required: `type(scope): description` — types: feat/fix/refactor/perf/docs/test/chore/build/ci/style/revert. Scope = brick name when applicable (`fix(company): ...`).
