# AGENTS — Vietnamese SME Accounting App
_Session-startup guide. Architecture: Lego brick (Modular Hexagonal). RBAC: Flask built-in. DB: SQLite3 default._

## PART 1: REPO CONTEXT, TOOLCHAIN & COMMANDS

### 1.1. Current Repo State & Health
- **Tech:** Flask app scaffold being rebuilt as Modular Hexagonal (Lego bricks). Commit `1200199 "reset"` deleted `app.py`, `scripts/manage.py`, `src/application/`, `src/domain/`, `src/infrastructure/`, all migration files. Working tree also has unstaged deletions: `pyproject.toml`, `casbin_model.conf`, `rbac_policy.csv`.
- **Package Manager:** `.venv` managed by `uv`. Always activate: `source .venv/bin/activate`.
- **Python:** `>= 3.11` (venv runs `3.13`).
- **Testing:** `pytest` configured (`testpaths=tests`, `pythonpath=src`). Status unknown after reset — re-run to confirm.
- **Frontend:** `templates/base.html` uses local Bulma + HTMX (offline-capable, no CDN).
- **Database & Migration:** Default `SQLite3` via SQLAlchemy. `SQLALCHEMY_DATABASE_URI` env overrides if needed. Migration files were deleted — new migrations needed from specs.
- **Security & RBAC:** Flask built-in via `@login_required` + role checks using `current_user.is_authenticated` and `current_user.role`. **Casbin model/policy CSV deleted — do not import `pycasbin` or `casbin`.** `AUDITOR` role read-only.

### 1.2. Essential Development Commands
- **Activate venv:** `source .venv/bin/activate`
- **Run dev server:** `flask run` (ensure `FLASK_APP`/`PYTHONPATH=src` set)
- **Run tests:** `uv run pytest` or `pytest` from activated venv
- **Single test:** `pytest tests/unit/<module>/ -k "<name>" -v`
- **CI quality order:** `ruff check` ➔ `black --check` ➔ `mypy` ➔ `pytest`

### 1.3. What Was Deleted (reset + unstaged)
- `app.py`, `scripts/manage.py`
- `src/application/`, `src/domain/`, `src/infrastructure/`
- All migration files + `migrations/env.py`
- `pyproject.toml`, `casbin_model.conf`, `rbac_policy.csv`
- *Result:* Working tree is dirty — 6 unstaged deletions. Decide to commit or restore before proceeding.

## PART 2: ARCHITECTURE & PHILOSOPHY
_System re-architected as Modular Hexagonal (Lego bricks). Old Clean Architecture deleted. Docs/ contains module specs as source of truth._

- **Old architecture:** Monolithic with Casbin RBAC, multi-DB support. Code deleted in reset.
- **New architecture:** Lego brick model — each brick is a self-contained module with pure Python domain, port interfaces, SQLAlchemy storage adapters, and Flask blueprint adapters.
- **Docs as truth:** `docs/` directory holds BRD/Specs/Use Cases/User Journeys for modules: company, system-settings, cost-centers-dimensions, currencies-exchange, fiscal-year-period, payment-terms, tax-engine, multi-company, etc. Read these before implementing.
- **Brick boundaries (enforced):** No cross-brick SQLAlchemy joins. Communicate via `contract.py` primitives only (`account_code`, `account_id` as `str`/`int`). Domain layer pure Python — no Flask/SQLAlchemy imports.
- **RBAC:** Flask-Login built-in only. `@login_required` on routes. Role checks via `current_user.role` (e.g. `if current_user.role != 'AUDITOR'`). No Casbin.

## PART 3: SESSION START — MANDATORY READS (DO THIS FIRST)
_Every agent session MUST read these docs before writing any code. Non-negotiable._

**Step 1: Read coding & testing rules (before ANY code changes):**
```
1. Read docs/CODING_CONVENTION.md    — naming, formatting, imports, error handling, review checklist
2. Read docs/TESTING_STRATEGY.md     — test pyramid, what/where to test, factory pattern, CI rules
```

**Step 2: Run quality gates before committing (EVERY TIME):**
```bash
ruff check src tests          # MUST pass — 0 errors
black --check src tests       # MUST pass — no reformat needed
pytest tests/ -v              # MUST pass — all green
```

**Step 3: Follow these guardrails (violations = PR reject):**
- **Data isolation:** No `join` across brick tables — pass `account_code` / `account_id` as primitives via `contract.py`.
- **Vietnamese accounting codes:** Match regex `^[1-9]\d{2}$` or `^[1-9]\d{3}$`.
- **Contract pattern:** File `contract.py` is the public interface — only receive/return primitive types (`str`, `int`, `float`, `dict`, `Decimal`).
- **RBAC:** Flask built-in only. `@login_required` + `current_user.role` checks. No Casbin imports.
- **Testing:** Each brick needs its own test suite. Mock `contract.py` of target brick when testing cross-brick calls. No `sleep` in tests.
- **Database:** Default SQLite3. If changing DB, update `SQLALCHEMY_DATABASE_URI` and rewrite migrations.
- **No `print()` in production code.** Use `logging` module.
- **No bare `except:`.** Catch specific exceptions, log, re-raise.
- **Domain layer:** ZERO Flask/SQLAlchemy imports (enforced by architecture).
- **Commit messages:** MUST follow Conventional Commits: `type(scope): description`.

## PART 4: COMPLETED MODULES STATUS (POST-RESET)
_What code remains vs what was deleted. Docs/specs remain for all modules._

- **Company module:** Code deleted. Specs in `docs/company-module/`. 50 unit tests were passing before reset.
- **System Settings:** Code deleted. Specs in `docs/system-settings/`.
- **Cost Centers & Dimensions:** Code deleted. Specs in `docs/cost-centers-dimensions/`.
- **Payment Terms & Document Numbering:** Specs completed `2026-08-20` in `docs/payment-terms/`. Code status: PENDING.
- **Currencies & Exchange Rates:** Code deleted. Specs in `docs/currencies-exchange/`. 80 green currency tests were passing before reset.
- **Audit Log:** Code deleted. Specs in `docs/audit-log/`.
- **Fiscal Years & Accounting Periods:** Old plan in `tasks/plan.md` and `tasks/todo.md` — may be superseded by new architecture.
- **All other modules** (tax-engine, bank-cash, multi-company, etc.): code deleted, specs intact in `docs/`.

**Action:** Read `docs/<module>/` specs to define new lego brick architecture. Rebuild modules from specs, not from old code.