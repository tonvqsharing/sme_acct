# AGENTS — Vietnamese SME Accounting App

_Flask + SQLAlchemy, Modular Hexagonal ("Lego bricks"), SQLite, Flask-Login RBAC._

## Commands

`uv` is the package manager. Always `uv run` — no venv activation.

```bash
uv run pytest -q                                   # full suite (954 passing)
uv run pytest tests/unit/company/ -k "<name>" -v   # single test / focused
uv run pytest tests/integration/test_company_api.py -v
uv run ruff check src tests                        # lint
uv run black --check src tests                     # format check
uv run mypy --ignore-missing-imports src/bricks/   # typecheck
uv run python -c "from src.app import create_app; create_app().run(port=5000)"
```

Quality gate order (CI `.github/workflows/ci.yml` on 3.11 + 3.12 enforces same): `ruff` → `black` → `mypy --ignore-missing-imports` → `pytest -q`. `uv sync --frozen` in CI is minimal (lockfile only pins `alembic`/`sqlalchemy`); local `.venv` already has `flask`/`flask-login` — use `uv run` directly, never `uv sync --no-dev` (strips dev tools).

`pyproject.toml`: `testpaths=["tests"]`, `pythonpath=["src"]`, `line-length=100` (ruff + black), `mypy strict=true`.

## Toolchain Gotchas

- `mypy` without `--ignore-missing-imports` fails — `flask_login` has no stubs (`import-untyped`). CI includes the flag.
- `mypy` override: `src.bricks.tools_equipment.storage` has `ignore_errors = true` (complex SQLAlchemy generics).
- `@login_required` `# type: ignore[untyped-decorator]` goes on the decorator line, not `def` — mypy attributes error to decorator.
- Route return: `tuple[Any, int]` not `tuple[dict, int]` (`jsonify()` → `Response`).
- `strict` bans bare `dict` → `dict[str, Any]` everywhere (port signatures, JSON columns).
- `ruff` C408: use `{"k": v}` not `dict(k=v)`; RUF059: prefix unused unpack with `_`.
- `from __future__ import annotations` + `Mapped[...]`: every type in annotation must be imported in module or `NameError`/`MappedAnnotationError` at import time (`date`, `Decimal`, `JSON`, `uuid4`, etc.).
- `SECRET_KEY` env var required outside `TESTING` — factory raises `RuntimeError` if missing and `TESTING` is falsy. Defaults to `dev-secret-change-in-production` only in testing.

## Architecture: Lego Bricks

```
src/bricks/<name>/
  contract.py     # ABC ports, primitives only (str/int/Decimal/UUID/dict)
  domain.py       # pure Python, ZERO Flask/SQLAlchemy imports
  services.py     # business logic via port
  storage.py      # SQLAlchemy models + repo adapter
  web_adapter.py  # Flask blueprint — ONLY file that may import Flask
```

`src/app.py` is the composition root. Wiring order matters: `coa_service` + `fy_service` before invoice/voucher (they consume `app.coa_service`/`app.fy_service`). Cross-brick calls use thin adapters defined inline in `app.py` (`_NumberingAdapter`, `_TermsAdapter`, `_COAServiceAdapter`) — never import another brick's `storage` into a service. Add `Base.metadata.create_all(engine)` there and `Base` to `alembic/env.py:target_metadata` (16 Bases currently).

Transaction gate order (invoice & voucher services): `fiscal period open` → `COA posting accounts (ACTIVE + detail)` → `balance/invariant`. Ledger reports never touch voucher models — they read via `LedgerSourcePort` (flat primitive rows).

Brick boundaries (PR reject if violated):
- No cross-brick SQLAlchemy joins; go through `contract.py` with primitives.
- `domain.py` purity is law.
- Mock target brick's `contract.py` in tests.
- Config flags need `CONFIG_FLAGS = frozenset({...})` allowlist in domain; `with_flag_update()` validates.

Spec-vs-repo: specs mention Casbin/"CASRBAC" and paths like `src/presentation/api/*_bp.py` — ignore both. Use Flask built-in checks and brick layout.

## RBAC

`@login_required` on every route + `current_user.role` check:

| Action | Roles |
|---|---|
| Create company | ADMIN |
| Update company | ADMIN, ACCOUNTANT |
| Suspend company | CHIEF_ACCOUNTANT |
| Read anything | any authenticated (incl. AUDITOR) |
| AUDITOR writes | forbidden |

## Testing

- Unit: `tests/unit/<brick>/` — may hand-build minimal Flask app (`FakeUser(UserMixin)` + `_store` dict + `session_transaction`). See `tests/unit/test_company_web_adapter.py`.
- Integration: `tests/integration/` — MUST go through real `create_app(config={"TESTING": True})`.
- Shared fixtures: `tests/integration/conftest.py` (`app`, `admin_client`, `accountant_client`, `chief_client`, `auditor_client`, `UUID_*`, `_store`, `FakeUser`). Import `UUID_*`/`FakeUser` from there — never import fixture functions (shadows pytest params → F811). `tests/__init__.py` exists (empty) so `tests` is a package; without it pytest treats `conftest` as top-level and creates a second `_store` → mystery 401s.
- Auth: real `user_loader` looks up `users` table. Two options: stub `load_user` on `app.login_manager` (legacy) or create user via `UserService` then `POST /api/v1/auth/login` (see `tests/integration/test_auth_api.py`). Unauthorized → `401` JSON via `unauthorized_handler`.
- No `sleep()` in tests. Each brick has its own suite.

## Adding a New Brick

1. Create `src/bricks/<name>/` with 5-file layout.
2. `src/app.py`: `Base.metadata.create_all(engine)` + blueprint + `init_*_service()` in dependency order.
3. `alembic/env.py`: import `Base` and append to `target_metadata`.
4. `tests/unit/<name>/` + `tests/integration/test_<name>_api.py`.
5. No cross-brick model imports.

## Docs Are Truth

Before any code change, read `docs/CODING_CONVENTION.md` + `docs/TESTING_STRATEGY.md`, then `docs/<module>/` (BRD → specs → use cases). Rebuild from specs, not git archaeology.

Audit-chain rules (audit_log, payment_terms): `seq` per entity (not timestamps) for deterministic ordering; persist verbatim `ts_iso` string (SQLite round-trip loses microseconds); auto-numbering needs a real UUID actor — `uuid5(NAMESPACE_URL, "system:numbering")`, `None` trips EX-001.

Compliance (as of 2026-08, mof.gov.vn/vbpl.vn): MST `TaxId` family `^[1-9]\d{2}(-\d{3})?$`, account codes `^[1-9]\d{2}$|^[1-9]\d{3}$`, TT99/2025 replaces TT200, TT58/2026 replaces TT132/2018, NĐ 254/2026+TT91/2026 replace NĐ123/2020+70/2025 & TT32/2025 (e-invoice 01/07/2026), input VAT ≥5tr non-cash per Luật GTGT 2024 Đ.14 + NĐ181/2025 Đ.26 (sửa NĐ144/2026), VAT 8% reduced per NQ204/2025+ NĐ174/2025 →31/12/2026 (date-effective gate in `rate_windows.py`), 10-year retention (Luật Kế toán 2015 Art.11). `CONFIG_FLAGS` allowlist enforced in domain.

## Module Status

| Module | State |
|---|---|
| Company, Payment Terms & Numbering (SOD 202), Audit Log (checksum chain), FY & Periods, COA, Invoice/Voucher/Ledger, Bank/Cash (+ reconciliation SOD), Purchases (deductibility R-P4/R-P5, XML ingest v2), Tax Engine ({0,5,8,10,-1}+ windows+SOD), Currencies (ISO4217+gap-fill+revaluation SOD), Auth/User (pbkdf2), Fixed Assets (SL), Tools & Equipment (CCDC), XML Ingest (TT91), Cost Centers+Dimensions, System Settings (period lock/CONFIG_FLAGS), Financial Statements (B01/B02/B03) | ✅ done — all with unit+integration suites |

## Migrations

`alembic/env.py` aggregates 16 brick Bases.

```bash
DATABASE_URL="sqlite:///./sme_acct.db" uv run alembic upgrade head
DATABASE_URL="sqlite:///./sme_acct.db" uv run alembic revision --autogenerate -m "desc"
```

Review autogenerated files: replace `src.bricks.*.*Type()` custom types with underlying `sa` types (e.g. `sa.Text()` for `JSONType`).

## Commits

Conventional Commits: `type(scope): description` — types `feat/fix/refactor/perf/docs/test/chore/build/ci/style/revert`; scope = brick name (`fix(company): ...`).
