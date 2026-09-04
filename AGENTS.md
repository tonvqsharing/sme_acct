# AGENTS — Vietnamese SME Accounting App

_Flask + SQLAlchemy, Lego bricks, SQLite, Flask-Login RBAC._

## Commands

`uv` only — always `uv run`, never venv activate.

```bash
uv run pytest -q                                   # full suite (1037 passed)
uv run pytest tests/unit/company/ -k "<name>" -v   # single test
uv run pytest tests/integration/test_company_api.py -v
uv run ruff check src tests
uv run black --check src tests
uv run mypy --ignore-missing-imports src/bricks/   # python_version 3.13, strict=true
uv run python -c "from src.app import create_app; create_app().run(port=5000)"
```

Gate order (CI `.github/workflows/ci.yml` on 3.11 + 3.12): `ruff` → `black` → `mypy --ignore-missing-imports` → `pytest -q`. `uv sync --frozen` in CI is minimal (only `alembic`/`sqlalchemy` pinned); local `.venv` already has `flask`/`flask-login` — never `uv sync --no-dev`.

`pyproject.toml`: `testpaths=["tests"]`, `pythonpath=["src"]`, `line-length=100`, `mypy strict=true`.

## Toolchain Gotchas

- `mypy` without `--ignore-missing-imports` fails — `flask_login` no stubs. Always include flag.
- `mypy` overrides: `src.bricks.tools_equipment.storage` and `src.bricks.inventory.storage` need `ignore_errors` or per-line `type: ignore` — complex SQLAlchemy generics / `Any` repo ports.
- `@login_required  # type: ignore[untyped-decorator]` on decorator line, not `def`.
- Route return `tuple[Any, int]` not `tuple[dict, int]` (`jsonify()` → `Response`).
- `strict` bans bare `dict` → `dict[str, Any]`; `from __future__ import annotations` + `Mapped[...]` requires every type imported (`date`, `Decimal`, `UUID`).
- `ruff` C408: `{"k": v}` not `dict(k=v)`; RUF059: prefix unused unpack `_`; DTZ011/BLE001/S110 need `noqa` if intentional.
- `SECRET_KEY` required outside `TESTING` — factory raises `RuntimeError` if missing and `TESTING` falsy. Testing defaults to `dev-secret-change-in-production`.

## Architecture: Lego Bricks

```
src/bricks/<name>/
  contract.py     # ABC ports, primitives only (str/int/Decimal/UUID/dict)
  domain.py       # pure Python, ZERO Flask/SQLAlchemy
  services.py     # business logic via port
  storage.py      # SQLAlchemy models + repo adapter
  web_adapter.py  # Flask blueprint — ONLY Flask file
```

`src/app.py` = composition root. Wiring order: `coa_service` + `fy_service` before `invoice`/`voucher`/`inventory` (they consume `app.coa_service`/`app.fy_service`). Cross-brick via thin adapters inline (`_SeriesIssueAdapter` HD/PT/PN/PX/CK, `_TermsAdapter`, `_COAServiceAdapter`, `_InventoryNumbering`, `_PeriodLockAdapter`) — never import another brick's `storage` into a service. Add `Base.metadata.create_all(engine)` per brick and `Base` to `alembic/env.py:target_metadata` (20 Bases).

Gate order (invoice/voucher/inventory): `fiscal period OPEN` → `period not closed` → `COA/product active+detail` → `balance/cost invariant`. Ledger/reports read via `LedgerSourcePort` flat primitives, never join voucher models. Inventory `611` banned — direct `152/156` via stock moves.

Brick boundaries (PR reject if violated): no cross-brick SQL joins; `domain.py` purity law; mock target `contract.py` in tests; `CONFIG_FLAGS = frozenset({...})` allowlist + `with_flag_update()`.

Spec-vs-repo: specs mention Casbin/"CASRBAC" and `src/presentation/api/*_bp.py` — ignore, use Flask built-in checks + brick layout.

## RBAC

`@login_required` + `current_user.role`:

| Action | Roles |
|---|---|
| Create company | ADMIN |
| Update company | ADMIN, ACCOUNTANT |
| Suspend / close period / cost method change | CHIEF_ACCOUNTANT (+ ADMIN) |
| Inventory create/post | ACCOUNTANT, CHIEF_ACCOUNTANT |
| Read anything | any authenticated (incl. AUDITOR) |
| AUDITOR writes | forbidden (403) |

## Testing

- Unit `tests/unit/<brick>/` — may hand-build Flask app (`FakeUser(UserMixin)` + `_store` + `session_transaction`). See `tests/unit/test_company_web_adapter.py`. Use `FakeRepo` fakes for ports.
- Integration `tests/integration/` — must go through real `create_app(config={"TESTING": True})`.
- Fixtures `tests/integration/conftest.py` (`app`, `admin_client`… `UUID_*`, `_store`, `FakeUser`). Import `UUID_*`/`FakeUser` from there — never import fixture functions (F811). `tests/__init__.py` must exist (empty) else two `_store` → 401.
- Auth: real `user_loader` → `users` table. Stub `load_user` or `POST /api/v1/auth/login` via `UserService` (`tests/integration/test_auth_api.py`). Unauthorized → `401` JSON.
- No `sleep()` in tests. Each brick has its own suite. Inventory needs PN/PX/CK + PT series + COA 1521/3311/6321 seeded before POST.

## Adding a New Brick

1. `src/bricks/<name>/` 5-file layout.
2. `src/app.py`: `Base.metadata.create_all(engine)` + blueprint + `init_*_service()` in dependency order.
3. `alembic/env.py`: import `Base` → append to `target_metadata`.
4. `tests/unit/<name>/` + `tests/integration/test_<name>_api.py`.
5. No cross-brick model imports.

## Docs Are Truth

Before code change, read `docs/CODING_CONVENTION.md` + `docs/TESTING_STRATEGY.md`, then `docs/<module>/` (BRD→specs→use cases). Rebuild from specs, not git archaeology.

Audit-chain: `seq` per entity (not timestamps); persist verbatim `ts_iso` (SQLite loses µs); auto-numbering needs real UUID actor `uuid5(NAMESPACE_URL, "system:numbering")`, `None` → EX-001.

Compliance (2026-09, mof.gov.vn/vbpl.vn): MST `^[1-9]\d{2}(-\d{3})?$`, `^[1-9]\d{2}$|^[1-9]\d{3}$` accounts, TT99/2025 replaces TT200, TT58/2026 replaces TT132, NĐ 254/2026+TT91/2026 replace NĐ123/2020+70/2025 & TT32/2025 (e-invoice 01/07/2026), input VAT ≥5tr non-cash (Luật GTGT 2024 Đ.14 + NĐ181 Đ.26 sửa NĐ144/2026), VAT 8% NQ204+ NĐ174 →31/12/2026 (`rate_windows.py`), 10y retention.

## Module Status (22 bricks, 1037 tests)

| Module | State |
|---|---|
| Company, Payment Terms & Numbering (SOD 202), Audit Log, FY & Periods, COA, Invoice/Voucher/Ledger (line VAT 0/5/8/10/-1 + 521 deductions + FX + mock e-invoice, pagination), Bank/Cash (+ reconciliation), Purchases (deductibility, XML ingest v2), Tax Engine (windows+SOD), Currencies (ISO4217+gap-fill+revaluation), Auth/User, Fixed Assets (SL), Tools & Equipment (CCDC), XML Ingest (TT91), Cost Centers+Dimensions, System Settings (period lock/CONFIG_FLAGS), Financial Statements (B01/B02/B03), Document Conversion (MarkItDown), **Inventory (HTK: product/location/move/shipment/period, 4 cost methods per SKU wavg/fifo/specific/standard, no 611, NXT/turnover, 152/632)**, **Party (Tryton party base: Customer/Supplier/Employee + Department, MST, company isolation)**, **UOM (code/name/factor>0/base)** | ✅ done — unit+integration |

## Migrations

`alembic/env.py` aggregates 20 Bases (ledger has no Base).

```bash
DATABASE_URL="sqlite:///./sme_acct.db" uv run alembic upgrade head
DATABASE_URL="sqlite:///./sme_acct.db" uv run alembic revision --autogenerate -m "desc"
# review autogenerated: replace src.bricks.*.*Type() with sa types (e.g. sa.Text() for JSONType)
```

## Commits

Conventional Commits: `type(scope): description` — `feat/fix/refactor/perf/docs/test/chore/build/ci/style/revert`; scope = brick name (`fix(company): …`).
