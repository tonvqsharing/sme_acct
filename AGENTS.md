# AGENTS — Vietnamese SME Accounting App

_Flask + SQLAlchemy app for Vietnamese SME accounting. Architecture: Modular Hexagonal ("Lego bricks"). DB: SQLite3. RBAC: Flask-Login built-in._

## Commands

Package manager is `uv`. Prefix everything with `uv run` — no venv activation needed.

```bash
uv run pytest -q                                  # full suite (currently 227 passing)
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

`src/app.py` = application factory (`create_app`) wiring bricks together.

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
- **Auth seam for tests:** `create_app()`'s `user_loader` returns `None` (user brick not built yet). Integration tests override it post-hoc: `app.login_manager` → register test `user_loader` + `unauthorized_handler` returning 401. See `tests/integration/test_company_api.py` fixture block — copy that pattern.
- Each brick gets its own suite. No `sleep()` in tests.

## Docs Are Truth — Read Before Implementing

Mandatory reads before ANY code change:
1. `docs/CODING_CONVENTION.md`
2. `docs/TESTING_STRATEGY.md`

Then read the target module's specs under `docs/<module>/` (BRD → specs → use cases). Rebuild from specs, never from git archaeology.

Vietnamese compliance rules baked into specs: MST tax-ID format (`^[1-9]\d{2}(-\d{3})?$`-family — see `TaxId` in company domain), accounting codes match `^[1-9]\d{2}$` or `^[1-9]\d{3}$`, TT200/TT133/TT99 regimes, 10-year retention (Luật Kế toán 2015 Art. 11).

## Module Status

| Module | Code | Specs |
|---|---|---|
| Company | ✅ done — unit + integration suites green | `docs/company-module/` |
| Payment Terms & Doc Numbering | ✅ done — 114 tests (unit+repo+API); SOD two-actor flow deferred | `docs/payment-terms/` |
| System Settings, Cost Centers, Currencies, Audit Log, Fiscal Year, Tax Engine, Bank/Cash, Multi-company, COA | pending | `docs/<module>/` |

## Commits

Conventional Commits required: `type(scope): description` — types: feat/fix/refactor/perf/docs/test/chore/build/ci/style/revert. Scope = brick name when applicable (`fix(company): ...`).
