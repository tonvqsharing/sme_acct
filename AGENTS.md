# AGENTS — Vietnamese SME Accounting App

_Flask + SQLAlchemy app for Vietnamese SME accounting. Architecture: Modular Hexagonal ("Lego bricks"). DB: SQLite3. RBAC: Flask-Login built-in._

## Commands

Package manager is `uv`. Prefix everything with `uv run` — no venv activation needed.

```bash
uv run pytest -q                                  # full suite (currently 325 passing)
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

`src/app.py` = composition root. Wiring order matters: COA + FY services must exist before invoice/voucher blocks (they consume `app.coa_service` / `app.fy_service`). Cross-brick needs are met by thin adapters defined inline there (`_NumberingAdapter`, `_TermsAdapter`) that translate brick contracts to narrow callables — do NOT import one brick's storage into another's service.

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
- **Shared fixtures live in `tests/integration/conftest.py`** (`app`, `admin_client`, `accountant_client`, `chief_client`, `auditor_client`, `UUID_*`). Import the UUID *constants* from there — never import the fixture functions themselves (they shadow pytest params → F811).
- **Auth seam for tests:** `create_app()`'s `user_loader` returns `None` (user brick not built yet). Integration tests override it post-hoc: `app.login_manager` → register test `user_loader` + `unauthorized_handler` returning 401. See `tests/integration/test_company_api.py` fixture block — copy that pattern.
- Each brick gets its own suite. No `sleep()` in tests.

## Docs Are Truth — Read Before Implementing

Mandatory reads before ANY code change:
1. `docs/CODING_CONVENTION.md`
2. `docs/TESTING_STRATEGY.md`

Then read the target module's specs under `docs/<module>/` (BRD → specs → use cases). Rebuild from specs, never from git archaeology.

**Audit-chain data rules (audit_log + payment_terms checksums):**
- Chain events need deterministic ordering → per-entity `seq` column, NOT timestamps (ties broke chains when uuid tiebreak was used).
- Any string hashed into a checksum must be persisted verbatim: SQLite datetime round-trip loses microseconds vs `.isoformat()`, so audit rows carry a `ts_iso` string column.
- Auto-numbering increments require a real UUID actor — use a `uuid5(NAMESPACE_URL, "system:numbering")` system identity, `None` trips EX-001.

Vietnamese compliance rules baked into specs: MST tax-ID format (`^[1-9]\d{2}(-\d{3})?$`-family — see `TaxId` in company domain), accounting codes match `^[1-9]\d{2}$` or `^[1-9]\d{3}$`, regimes per mof.gov.vn/vbpl.vn as of 2026-08: TT99/2025 (eff 01/01/2026, replaced TT200), TT58/2026 (eff 01/07/2026, replaced TT132/2018), TT133/2016 still in force, 10-year retention (Luật Kế toán 2015 Art. 11).

## Module Status

| Module | Code | Specs |
|---|---|---|
| Company | ✅ done — unit + integration suites green | `docs/company-module/` |
| Payment Terms & Doc Numbering | ✅ done incl. SOD two-actor flow (request→202, approve/reject) | `docs/payment-terms/` |
| Audit Log | ✅ core done — append-only checksum chain (17 tests); API/filters pending spec session | `docs/audit-log/` |
| Fiscal Year & Periods | ✅ core done — years/monthly periods/posting gate (10 tests); web layer pending | `docs/fiscal-year-period/` |
| Chart of Accounts | ✅ core done — codes/hierarchy/posting gate + SQLite repo (21 tests); web API pending | `docs/coa/` |
| Invoice + Voucher + Ledger core loop | ✅ invoice/voucher bricks done; ledger reports done (325 total) | — |
| System Settings, Cost Centers, Currencies, Tax Engine, Bank/Cash, Multi-company | pending | `docs/<module>/` |

## Commits

Conventional Commits required: `type(scope): description` — types: feat/fix/refactor/perf/docs/test/chore/build/ci/style/revert. Scope = brick name when applicable (`fix(company): ...`).
