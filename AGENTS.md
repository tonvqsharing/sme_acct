# AGENTS.md

## Repo state

- Python workflow app, skeleton scaffolded but no business logic yet.
- `pyproject.toml` present (hatchling backend, Flask stack, dev deps).
- No README.
- No tests scaffolded.
- `migrations/` empty.
- Entrypoint: `app.py` (Flask factory, env loading wired up).
- `.env` loading via `python-dotenv` already in `app.py`.
- Frontend baseline scaffolded: `templates/`, `static/css/`, `static/js/`.
  - `templates/base.html` loads Bulma CDN + HTMX.
  - Extend by adding partials under `templates/` and JS/CSS assets under `static/`.

## Toolchain

- Venv: `/home/projects/sme_acct/.venv` (created by `uv`).
- Install: `uv pip install --python=/home/projects/sme_acct/.venv/bin/python <package>`
- Editable install: `uv pip install --python=/home/projects/sme_acct/.venv/bin/python -e .`
  - Adds `src/` to path so `src.domain.entities...` imports resolve.
- Do not use bare `pip`.
- Python path: code lives under `src/`.
  - Imports written as `src.domain.entities...` — watch out for relative-import mistakes in tests.

## Architecture

```
src/
  domain/           # pure Python, no external deps
    entities/       # Partner, Invoice, Voucher + value objects/validators
  application/
    ports/          # repository/service interfaces
    services/       # use cases
  infrastructure/
    database/
      models.py     # SQLAlchemy 2.0 (DeclarativeBase, mapped_column, Mapped)
    repositories/   # ORM implementations
  presentation/
    api/            # REST-ish layer
    serializers/
    forms/
    ui/
```

- Domain layer must stay free of `sqlalchemy` and web imports.
- Enums exist in both domain (`src/domain/entities/base.py`) AND SQLAlchemy models (`src/infrastructure/database/models.py`). Keep them in sync when adding states/types.

## Domain rules (hard-coded)

- Tax IDs validated: `^\d{10}$` or `^\d{10}-\d{3}$`.
- Account codes validated: `^[1-9]\d{2}$` or `^[1-9]\d{3}$` (Vietnamese chart of accounts).
- `Invoice` items auto-calc `subtotal`, `vat_total`, `grand_total`; `add_item()` recalculates.
- `Voucher` must be balanced (≈equal debit/credit, tol 0.01) before `post()`.
- `Partner.tax_id` joins invoices by value; model stores raw string, domain wraps `TaxId`.

## Framework / infra

- Flask + `flask-migrate` + `Flask-Talisman` (configured in `app.py`).
- `Flask-Talisman` enforces HTTPS in DEBUG=False; auto-disabled in DEBUG mode.
  - Use `DEBUG=1` for local dev unless explicitly configuring origins.
- `flask db init|migrate|upgrade` requires `SQLALCHEMY_DATABASE_URI` in env; run after entrypoint exists.
- Supported databases: sqlite (latest, default), mariadb, mysql, postgresql v16+.
  - URIs: `sqlite:///...`, `mysql://...`, `mariadb://...`, `postgresql://...`.

## Commands (pending)

- Venv: `source /home/projects/sme_acct/.venv/bin/activate`
- Install: `uv pip install --python=/home/projects/sme_acct/.venv/bin/python <package>`
- Tests: none yet. First step is `pytest` + `tests/` scaffold.
- Lint/format/typecheck: none yet. Plan `black` + `ruff` + `mypy` and expose explicit commands.
- Migrations: `flask db ...` once env + entrypoint exist.

## Skills reference (5W1H decision table)

Use this to pick the right skill. Current session has `caveman` active for compressed output.

| Skill | WHO | WHAT | WHEN | WHERE | WHY | HOW invoke |
|---|---|---|---|---|---|---|
| **test-driven-development** | agent + user | red-green-refactor | before non-trivial code / bug fix | `tests/` + `src/` | prove behavior, catch regressions | "TDD" or load skill |
| **planning-and-task-breakdown** | agent, user with spec | break work into ordered tasks | feature >1 step, estimating scope | planning phase | avoid large-blind leaps | "break this into tasks" |
| **incremental-implementation** | agent | deliver changes incrementally | >1 file, large change | implementation | lower risk, easier review | "incremental" / invoke |
| **code-review-and-quality** | agent, reviewer | multi-axis review (standards + spec) | before merge, PR / branch diff | PR / branch | catch issues before main | "review this PR" |
| **caveman** | agent | ultra-compressed comms | token efficiency, any session | all output | save 60%+ context | `/caveman` / "caveman mode" |
| **caveman-commit** | agent | concise conventional commits | staging changes | git | clean history, no noise | "write commit message" |
| **caveman-review** | agent | compressed review comments | PR / diff review | code review | signal only, no praise | "review this diff" |
| **domain-modeling** | agent + user | DDD ubiquitous language | terms ambiguous, architecture unclear | planning / design | shared vocab prevents mismatch | "domain model" / "ubiquitous language" |
| **documentation-and-adrs** | agent | record architectural decisions | public API change, shipping feature | `docs/`, ADR files | future context | "record this decision" |
| **security-and-hardening** | agent | harden against vulns | auth, user input, data storage, external integrations | feature code | prevent vulnerabilities | "security review" / load skill |
| **context-engineering** | agent | optimize agent context setup | session start, output degrades, task switch | session config | agent needs good context | "context engineering" / invoke |
| **git-workflow-and-versioning** | agent | structure git practices | commits, branches, conflicts, releases | git workflow | clean history, proper semver | "git workflow" / load skill |
| **cavecrew** | agent (main thread) | delegate to subagents (investigator / builder / reviewer) | save context, large explore, 1-2 file edits, diff review | any task | subagent output ~60% smaller | "delegate to cavecrew" |
| **api-and-interface-design** | agent + user | stable API / module boundaries | REST endpoints, module interfaces | `presentation/api/` | prevent breaking changes | "design the API" / invoke |
| **debugging-and-error-recovery** | agent | systematic root-cause debugging | tests fail, builds break, unexpected behavior | any broken code | fix root cause, not symptoms | "debug this" / invoke |
| **ci-cd-and-automation** | agent | CI / CD pipeline setup | build / deploy automation, quality gates | `.github/workflows/` | automate quality | "set up CI" / invoke |
| **interview-me** | agent + user | extract actual requirements | underspecified ask ("build me X") | requirement gathering | avoid building wrong thing | "interview me" / invoke |
| **handoff** | agent | compact conversation into handoff doc | passing work to agent, long session | handoff file | next agent picks up immediately | "handoff" / invoke |
| **karpathy-guidelines** | agent | reduce LLM coding mistakes | writing / reviewing / refactoring code | all code | avoid overcomplication | auto-loaded session start |
| **setup-pre-commit** | agent + user | pre-commit hooks (lint, typecheck, tests) | setting up quality gates | `.git/hooks/` | catch issues before commit | "set up pre-commit" / invoke |
| **implement** | agent | implement from spec / tickets | spec exists, ready to code | `src/` | execute plan systematically | "implement this spec" |

**Notes**
- Variants: `caveman-commit` and `caveman-review` are commit / review submodes of `caveman`.
- `interview-me` and `grill-me` share trigger phrases; both extract requirements.
- Omitted from table: Obsidian, canvas, markdown-writing, TypeScript-only, and QA-only skills — not applicable to this repo.
