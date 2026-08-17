# Implementation Plan: Company Module (Base Entity)

## Overview

Build the Company domain entity module end-to-end in TDD, vertical slices, from domain → infrastructure → application → presentation. This is the root aggregate for the entire accounting system — nothing else can function without it.

**Architecture:** Clean Architecture / Hexagonal
**Standards:** CODING_CONVENTION.md, AGENTS.md
**Testing:** pytest, TDD (red-green-refactor per slice)
**DB:** SQLAlchemy 2.0 DeclarativeBase + Flask-Migrate
**Style:** black, ruff, mypy

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Company as root aggregate | All financial entities (Partner, Invoice, Voucher) must belong to a legal entity per Luật Doanh nghiệp 2020 Art. 31 |
| Single company per deployment in v1 | Simpler; schema supports multi-company later |
| Domain enums duplicated in SQLAlchemy | Per AGENTS.md convention: enums live in `domain/entities/base.py` AND `infrastructure/database/models.py` |
| `company_id` nullable initially, backfill later | Safe migration path; existing data not lost |
| Tenant middleware deferred to v1.5 | Single-company v1 doesn't need it; design for it in schema |
| No soft-delete on Company | DISSOLVED status = soft-disable; record retained indefinitely for 10y retention |

---

## Task List

### Phase 1: Foundation (Domain Layer)

#### Task 1: Company Domain Entity + Value Objects + Exceptions

**Description:** Create the Company aggregate root in domain layer. Pure Python — no Flask, no SQLAlchemy. Create supporting enums (CompanyType, CompanyStatus, AccountingRegime), value objects (BankAccount), and domain exceptions. This is the foundation everything else builds on.

**Files:**
- `src/domain/entities/company.py` (new)
- `src/domain/entities/base.py` (extend — add enums + BankAccount VO)
- `src/domain/exceptions/company.py` (new)

**Acceptance criteria:**
- [ ] `Company` dataclass with all 20+ fields from BRD
- [ ] `CompanyType` enum covers: SINGLE_LLC, MULTI_LLC, JSC, LISTED_JSC, SOLE_PROP, PARTNERSHIP, HOUSEHOLD, COOP
- [ ] `CompanyStatus` enum: ACTIVE, SUSPENDED, DISSOLVED
- [ ] `AccountingRegime` enum: TT200, TT99, TT58_MICRO, TT133
- [ ] `BankAccount` dataclass with validation
- [ ] `CompanyNotFoundError`, `DuplicateMSTError`, `CompanyLockedError` exceptions
- [ ] Domain rules: MST format (TaxId already exists, reuse it), fiscal year day/month validation
- [ ] All tests pass, ruff clean, black formatted, mypy clean

**Verification:**
```bash
pytest tests/unit/company/ -v
ruff check src/domain/ tests/unit/company/
black --check src/domain/ tests/unit/company/
mypy src/domain/entities/company.py
```

**Dependencies:** None
**Estimated scope:** M (4 files)

---

#### Task 2: Company Repository Port (Interface)

**Description:** Define the abstract repository interface in application layer following Clean Architecture. Domain layer defines the port; infrastructure implements it.

**Files:**
- `src/application/ports/company_repo.py` (new)

**Acceptance criteria:**
- [ ] `CompanyRepositoryPort` ABC with all required methods: create, get_by_id, get_by_mst, list_active, update, deactivate, list_subsidiaries
- [ ] Type hints correct
- [ ] Tests: verify interface can be instantiated with mock (no impl needed)

**Verification:**
```bash
pytest tests/unit/company/ -v
ruff check src/application/ports/
```

**Dependencies:** Task 1
**Estimated scope:** S (1 file)

---

#### Task 3: Unit Tests for Company Entity (TDD Red-Green)

**Description:** Write unit tests FIRST (TDD red), then implement to make them pass. Cover all domain validation rules, happy paths, exception paths, edge cases.

**Files:**
- `tests/unit/company/test_company_entity.py` (new)
- `tests/unit/company/conftest.py` (new)

**Acceptance criteria:**
- [ ] Test valid company creation (all mandatory fields)
- [ ] Test MST format invalid → ValueError
- [ ] Test MST branch suffix format
- [ ] Test legal_name empty → CompanyValidationError
- [ ] Test company_type invalid → InvalidCompanyTypeError
- [ ] Test fiscal year month out of range (13)
- [ ] Test fiscal year day invalid for Feb (30)
- [ ] Test HOUSEHOLD skips BHXH requirement
- [ ] Test LLC requires BHXH
- [ ] Test duplicate MST (when checking uniqueness in service)
- [ ] All tests pass

**Verification:**
```bash
pytest tests/unit/company/test_company_entity.py -v
```

**Dependencies:** Task 1
**Estimated scope:** M (2 files)

---

### Phase 2: Infrastructure Layer

#### Task 4: SQLAlchemy Company Model

**Description:** Create the `CompanyModel` in SQLAlchemy 2.0 DeclarativeBase style, matching existing pattern in `models.py`. Include all 20+ fields with proper types, constraints, and indexes. Follow existing code style exactly.

**Files:**
- `src/infrastructure/database/models.py` (extend)

**Acceptance criteria:**
- [ ] `CompanyModel(Base)` with all fields matching spec
- [ ] `mst` column: String(20), nullable=False, unique=True, index=True
- [ ] `company_type` column: String(30), nullable=False, default='multi_llc'
- [ ] `accounting_regime` column: String(30), nullable=False, default='tt99'
- [ ] `status` column: String(30), nullable=False, default='active'
- [ ] Constraints: fiscal_year_start_month 1-12, fiscal_year_start_day 1-31
- [ ] Indexes: `idx_companies_mst` on mst, `idx_companies_status` on status+is_active
- [ ] `created_at`, `updated_at` with `date.today` defaults
- [ ] `config_version` int, default=1
- [ ] `legal_reviewed_at`, `legal_reviewed_by` nullable
- [ ] `mst_changed_at` nullable
- [ ] Enums: `CompanyTypeEnum`, `CompanyStatusEnum`, `AccountingRegimeEnum` defined in models.py
- [ ] All tests pass, ruff clean, black formatted

**Verification:**
```bash
ruff check src/infrastructure/database/models.py
black --check src/infrastructure/database/models.py
mypy src/infrastructure/database/models.py
```

**Dependencies:** Task 1
**Estimated scope:** M (1 file)

---

#### Task 5: SQLAlchemy Company Repository Adapter

**Description:** Implement the `CompanyRepositoryPort` interface using SQLAlchemy. Follow existing repo pattern exactly (see `SQLAlchemyPartnerRepository` in `repositories/__init__.py`). Include `_to_domain` mapper.

**Files:**
- `src/infrastructure/repositories/__init__.py` (extend — add SQLAlchemyCompanyRepository)

**Acceptance criteria:**
- [ ] `SQLAlchemyCompanyRepository(CompanyRepositoryPort)`
- [ ] `create(company: Company) -> Company` — INSERT + `_to_domain`
- [ ] `get_by_id(company_id) -> Company | None` — `db.session.get()`
- [ ] `get_by_mst(mst) -> Company | None` — SELECT WHERE mst=?
- [ ] `list_active() -> list[Company]` — WHERE is_active=True AND status='active'
- [ ] `update(company, actor) -> Company` — UPDATE with optimistic lock
- [ ] `deactivate(company_id, actor) -> Company` — SET is_active=False
- [ ] `list_subsidiaries(parent_id) -> list[Company]` — WHERE parent_company_id=?
- [ ] `_to_domain(model) -> Company` static method
- [ ] All tests pass, ruff clean

**Verification:**
```bash
pytest tests/unit/company/ -v
ruff check src/infrastructure/repositories/
```

**Dependencies:** Task 4
**Estimated scope:** M (1 file)

---

#### Task 6: Add company_id to Existing Tables (Nullable)

**Description:** Add `company_id` UUID column (nullable) to `partners`, `invoices`, `vouchers` tables. Create FK constraints to `companies(id)`. This is a safe migration — existing data preserved, backfill in later task.

**Files:**
- `src/infrastructure/database/models.py` (extend — add company_id to PartnerModel, InvoiceModel, VoucherModel)
- `tests/unit/company/test_company_fk.py` (new — verify FK constraints)

**Acceptance criteria:**
- [ ] `PartnerModel` has `company_id: Mapped[UUID | None]` with `ForeignKey("companies.id")`
- [ ] `InvoiceModel` has `company_id: Mapped[UUID | None]` with `ForeignKey("companies.id")`
- [ ] `VoucherModel` has `company_id: Mapped[UUID | None]` with `ForeignKey("companies.id")`
- [ ] Relationships: `partner.company`, `invoice.company`, `voucher.company`
- [ ] Tests verify FK constraint exists
- [ ] All existing tests still pass (no breaking change since nullable)

**Verification:**
```bash
pytest tests/ -v
ruff check src/infrastructure/database/models.py
```

**Dependencies:** Task 4
**Estimated scope:** S (1 file + tests)

---

### Phase 3: Application Layer

#### Task 7: CompanyService (Business Logic + Validation)

**Description:** Implement the service layer with all business rules from BRD Section 6 and rules-company.md. Enforce MST uniqueness, company type validation, status lifecycle, fiscal year derivation. Follow existing `PartnerService` pattern.

**Files:**
- `src/application/services/company_service.py` (new)

**Acceptance criteria:**
- [ ] `create_company(**kwargs) -> Company` — validate MST format + uniqueness, all required fields
- [ ] `update_company(company_id, changes, actor) -> Company` — check RESTRICTED fields, emit audit log
- [ ] `change_company_type(company_id, new_type, actor)` — validate external re-registration required
- [ ] `deactivate_company(company_id, actor) -> Company` — check no open periods, no DRAFT journals
- [ ] `dissolve_company(company_id, actor) -> Company` — CHIEF_ACCOUNTANT only, all periods closed
- [ ] `advance_legal_rep(company_id, new_rep, actor)` — validate Mẫu 12 filed
- [ ] `get_company_config(company_id)` — proxy to SystemSettingsService (future)
- [ ] All domain validation rules enforced
- [ ] All tests pass, ruff clean, mypy clean

**Verification:**
```bash
pytest tests/unit/company/ -v
ruff check src/application/services/
mypy src/application/services/
```

**Dependencies:** Task 3, Task 5
**Estimated scope:** M (1 file)

---

#### Task 8: Unit Tests for CompanyService (TDD)

**Description:** Write comprehensive unit tests for CompanyService before implementation (TDD). Mock the repository. Cover happy path, alternative paths, exception paths per use-cases-company.md.

**Files:**
- `tests/unit/company/test_company_service.py` (new)

**Acceptance criteria:**
- [ ] `test_create_company_success` — valid data
- [ ] `test_create_duplicate_mst` — DuplicateMSTError
- [ ] `test_create_invalid_mst_format` — ValueError from TaxId
- [ ] `test_update_restricted_field_requires_reregistration` — legal_name blocked
- [ ] `test_mst_cannot_change_after_invoices` — MST_CHANGE_BLOCKED
- [ ] `test_suspend_with_open_periods` — COMPANY_HAS_OPEN_PERIODS
- [ ] `test_deactivate_with_draft_invoices` — blocked
- [ ] `test_dissolve_requires_closed_fyear` — blocked
- [ ] `test_legal_review_stamp` — sets legal_reviewed_at
- [ ] All tests pass

**Verification:**
```bash
pytest tests/unit/company/test_company_service.py -v
```

**Dependencies:** Task 7
**Estimated scope:** M (1 file)

---

### Phase 4: API Layer

#### Task 9: Company REST API Endpoints

**Description:** Implement Flask blueprint with REST endpoints per specs-company.md Section 7. Follow existing API patterns. Error translation from domain exceptions to JSON responses.

**Files:**
- `src/presentation/api/companies.py` (new)
- `src/presentation/api/__init__.py` (extend — register blueprint)

**Acceptance criteria:**
- [ ] `POST /api/v1/companies` — create company (ADMIN)
- [ ] `GET /api/v1/companies` — list companies (AUTH)
- [ ] `GET /api/v1/companies/{id}` — get detail (AUTH)
- [ ] `PATCH /api/v1/companies/{id}` — update company (ADMIN + ACCOUNTANT)
- [ ] `POST /api/v1/companies/{id}/suspend` — suspend (CHIEF_ACCOUNTANT)
- [ ] `POST /api/v1/companies/{id}/reactivate` — reactivate (ADMIN)
- [ ] `POST /api/v1/companies/{id}/change-mst` — MST change (ADMIN + LEGAL_REVIEW)
- [ ] `POST /api/v1/companies/{id}/legal-review` — stamp legal review (CHIEF_ACCOUNTANT)
- [ ] `GET /api/v1/companies/{id}/audit-log` — company change history
- [ ] Error responses match spec (409 MST_TAKEN, 422 INVALID_MST, etc.)
- [ ] All tests pass, ruff clean

**Verification:**
```bash
pytest tests/integration/company/ -v
ruff check src/presentation/api/
```

**Dependencies:** Task 7
**Estimated scope:** M (2 files)

---

#### Task 10: Integration Tests for Company API (TDD)

**Description:** Write integration tests using Flask test client. Test full request/response cycle. Cover happy path, all error paths, RBAC enforcement.

**Files:**
- `tests/integration/company/test_company_api.py` (new)

**Acceptance criteria:**
- [ ] `test_create_company_success` — 201 Created
- [ ] `test_create_duplicate_mst` — 409 MST_TAKEN
- [ ] `test_create_invalid_mst` — 422 INVALID_MST
- [ ] `test_get_company_not_found` — 404
- [ ] `test_update_company_restricted_field` — 422 LEGAL_CHANGE_REQUIRED
- [ ] `test_suspend_requires_chief_accountant` — 403 for regular accountant
- [ ] `test_change_mst_requires_notification_ref` — 422
- [ ] `test_legal_review_stamp` — 200, legal_reviewed_at set
- [ ] All tests pass

**Verification:**
```bash
pytest tests/integration/company/test_company_api.py -v
```

**Dependencies:** Task 9
**Estimated scope:** M (1 file)

---

### Phase 5: Database Migration

#### Task 11: Alembic Migration for Company Module

**Description:** Generate Flask-Migrate/Alembic migration for the new `companies` table and `company_id` additions to 3 existing tables. Include proper indexes and constraints.

**Files:**
- `migrations/versions/013_company.py` (new, or via `flask db migrate`)

**Acceptance criteria:**
- [ ] `companies` table created with all columns + constraints
- [ ] `partners.company_id` nullable UUID + FK
- [ ] `invoices.company_id` nullable UUID + FK
- [ ] `vouchers.company_id` nullable UUID + FK
- [ ] `uq_companies_mst` unique constraint
- [ ] `idx_companies_mst` index
- [ ] `idx_companies_status` index
- [ ] `fiscal_year_start_month` CHECK constraint 1-12
- [ ] `fiscal_year_start_day` CHECK constraint 1-31
- [ ] Up migration applies cleanly on fresh SQLite/PostgreSQL
- [ ] Down migration drops cleanly
- [ ] Tests: `flask db upgrade` + `downgrade` succeeds

**Verification:**
```bash
cd /home/projects/sme_acct && PYTHONPATH=src flask db migrate -m "add_company"
PYTHONPATH=src flask db upgrade
PYTHONPATH=src flask db downgrade
```

**Dependencies:** Task 4, Task 6
**Estimated scope:** S (auto-generated + manual tweaks)

---

### Phase 6: First Vertical Slice — End-to-End

#### Task 12: Company Setup Wizard — UI (First Vertical Slice)

**Description:** Build the first complete vertical slice: user can create a company via UI, see it in a list, and view details. This connects DB → API → UI for one happy path. This validates the entire stack works.

**Files:**
- `src/presentation/ui/companies.py` (new — HTMX blueprint)
- `templates/companies/new.html` (new)
- `templates/companies/list.html` (new)
- `templates/companies/detail.html` (new)
- `static/js/companies.js` (new, optional)

**Acceptance criteria:**
- [ ] `/companies/new` shows setup wizard form with all 15+ mandatory fields
- [ ] Form submits via HTMX POST to `/api/v1/companies`
- [ ] On success: redirect to company detail
- [ ] `/companies` lists all companies
- [ ] `/companies/{id}` shows company detail with all fields
- [ ] MST validation shown inline on form
- [ ] Company type dropdown with all VN types
- [ ] Fiscal year start picker (month + day)
- [ ] Bank accounts section (add/remove)
- [ ] Legal review stamp button
- [ ] ruff + black pass on new files

**Verification:**
```bash
PYTHONPATH=src flask run
# Manual: go to http://localhost:5000/companies/new
# Fill form, submit, verify company created
```

**Dependencies:** Task 9
**Estimated scope:** M (5 files)

---

### Phase 7: Edge Functionality

#### Task 13: Company Status Lifecycle + Tenant Scoping Stubs

**Description:** Implement company status lifecycle (ACTIVE → SUSPENDED → DISSOLVED) enforcement in services. Add tenant scoping stubs (resolve company from request context) for future multi-company. This prepares the system for v2 without overbuilding.

**Files:**
- `src/application/services/tenant_service.py` (new)
- `src/presentation/api/middleware.py` (extend)

**Acceptance criteria:**
- [ ] `TenantService.resolve_company(request) -> UUID` — extracts company_id from JWT/header/subdomain
- [ ] `TenantService.check_access(user_id, company_id) -> bool`
- [ ] `TenantService.scope_query(query, company_id)` — appends WHERE clause
- [ ] Middleware sets `g.company_id` on every request
- [ ] SUSPENDED company blocks invoice creation (integration test)
- [ ] DISSOLVED company blocks all writes

**Verification:**
```bash
pytest tests/unit/company/test_tenant_service.py -v
pytest tests/integration/company/ -v
```

**Dependencies:** Task 12
**Estimated scope:** M (2 files)

---

#### Task 14: Audit Trail for Company Changes

**Description:** Wire company creation/update/suspend/dissolve events into the existing audit log infrastructure (when System Settings audit log is built). For v1, implement company-specific audit logging using application-level events stored in a `company_changes` table.

**Files:**
- `src/infrastructure/database/models.py` (extend — `CompanyChangeModel`)
- `src/application/services/company_service.py` (extend — emit events)
- `migrations/versions/014_company_changes.py` (new)

**Acceptance criteria:**
- [ ] `CompanyChangeModel` table: id, company_id, actor_user_id, action, before_value JSON, after_value JSON, created_at
- [ ] CompanyService emits event BEFORE and AFTER every mutation
- [ ] `GET /api/v1/companies/{id}/audit-log` returns change history
- [ ] Audit log append-only (no UPDATE, no DELETE in service layer)

**Verification:**
```bash
pytest tests/unit/company/ -v
```

**Dependencies:** Task 12
**Estimated scope:** M (2 files + migration)

---

### Phase 8: Backfill + Hardening

#### Task 15: Data Backfill Script for Existing Records

**Description:** Create a one-time backfill script to populate `company_id` on all existing partners, invoices, vouchers. For single-company deployments, assign all to the default company.

**Files:**
- `scripts/backfill_company_id.py` (new)

**Acceptance criteria:**
- [ ] Script creates a default company if none exists
- [ ] Script backfills partners, invoices, vouchers with default company_id
- [ ] Script dry-run mode (count only)
- [ ] Script idempotent (safe to re-run)
- [ ] Script logs all changes

**Verification:**
```bash
python scripts/backfill_company_id.py --dry-run
python scripts/backfill_company_id.py
```

**Dependencies:** Task 11
**Estimated scope:** S (1 file)

---

#### Task 16: Full Integration Test Suite + CI Gate

**Description:** Complete integration test suite covering all API endpoints. Set up CI-friendly test command. Target: 80% coverage per CODING_CONVENTION.md.

**Files:**
- `tests/integration/company/test_company_api.py` (extend)
- `tests/unit/company/` (comprehensive)

**Acceptance criteria:**
- [ ] All 8 API endpoints have at least 1 happy path test
- [ ] All 8 API endpoints have error path tests
- [ ] Coverage ≥ 80% for `src/domain/entities/company.py`
- [ ] Coverage ≥ 70% for `src/application/services/company_service.py`
- [ ] `pytest --cov=src/domain/entities/company.py --cov-report=term-missing` shows ≥80%
- [ ] `pytest tests/` passes in CI

**Verification:**
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

**Dependencies:** All prior tasks
**Estimated scope:** M (2-3 files)

---

### Phase 9: Competitor Review + Polish

#### Task 17: Competitor Parity Review vs Fast/MISA/Tryton

**Description:** Review implemented module against competitor baseline. Verify all mandatory fields from BRD are present. Check UI quality, validation, error messages match Vietnamese accounting software standards.

**Acceptance criteria:**
- [ ] All 20+ mandatory fields from BRD present in UI + API
- [ ] MST validation matches Fast/MISA regex pattern
- [ ] Company type dropdown matches Fast's 8 types
- [ ] Fiscal year setup matches Fast (calendar vs Apr-start)
- [ ] Bank account management present
- [ ] BHXH code field present
- [ ] Responsible accountant + MSKHMN field present
- [ ] Legal review stamp workflow present
- [ ] UI responsive (Bulma + HTMX, offline-capable per AGENTS.md)
- [ ] Vietnamese error messages, English field names

**Verification:**
- Manual review against `docs/company-module/production-readiness-audit-company.md` competitor table
- Browser test via Playwright

**Dependencies:** All prior tasks
**Estimated scope:** S (review + minor fixes)

---

#### Task 18: Code Review Pass (Full Module)

**Description:** Run full code review on all new files using code-review-and-quality skill. Five axes: correctness, readability, architecture, security, performance. Fix all Critical and Required findings.

**Verification:**
- [ ] `ruff check src/ tests/` — zero errors
- [ ] `black --check src/ tests/` — zero errors
- [ ] `mypy src/` — zero errors
- [ ] `pytest tests/` — all pass
- [ ] Code review checklist completed
- [ ] No domain layer imports Flask/SQLAlchemy
- [ ] All enum syncs verified
- [ ] No magic numbers
- [ ] All public functions have docstrings

**Dependencies:** Task 17
**Estimated scope:** S (review + fixes)

---

## Checkpoints

### Checkpoint 1: After Task 3 (Domain Layer Complete)
- [ ] All domain tests pass
- [ ] Company entity has all mandatory fields
- [ ] Ruff + black + mypy clean
- [ ] Ready for infrastructure layer

### Checkpoint 2: After Task 7 (Service Layer Complete)
- [ ] CompanyService implements all business rules
- [ ] All service unit tests pass
- [ ] Repository adapter ready

### Checkpoint 3: After Task 10 (API Layer Complete)
- [ ] All API endpoints functional
- [ ] Integration tests pass
- [ ] End-to-end flow works via curl/httpie

### Checkpoint 4: After Task 14 (UI Vertical Slice Complete)
- [ ] User can create company via UI
- [ ] User can view company list
- [ ] Full stack verified: DB → API → UI

### Checkpoint 5: After Task 16 (Hardening Complete)
- [ ] 80% coverage achieved
- [ ] CI-ready
- [ ] Backfill script tested

### Checkpoint 6: Final (Ready for Merge)
- [ ] Competitor parity review passed
- [ ] Full code review passed
- [ ] All CI checks green
- [ ] Signed off by BA Lead + Chief Accountant

---

## Dependencies Graph

```
T1: Company entity + enums + exceptions
  └── T2: Repository port (interface)
  └── T3: Unit tests for entity
  └── T4: SQLAlchemy CompanyModel
      └── T5: SQLAlchemy repo adapter
          └── T7: CompanyService
              └── T8: Service unit tests
                  └── T9: REST API endpoints
                      └── T10: API integration tests
                          └── T12: UI setup wizard
                      └── T6: Add company_id to existing tables
                          └── T11: Alembic migration
                      └── T14: Audit trail
                  └── T13: Tenant service + middleware
              └── T15: Backfill script
          └── T16: Full test suite + CI
      └── T17: Competitor review
  └── T18: Final code review
```

**Parallelizable:** T1, T4 (both define data models — do sequentially to avoid merge conflicts), T14+T15 (independent)
**Must be sequential:** T4 → T5 → T7 → T9 → T12 (each depends on prior)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| MST regex mismatch with current GDT rules | HIGH | Mark as provisional; verify with legal team before PROD |
| Company type enum missing a rare type | MEDIUM | Add extension point; log warning for unrecognized types |
| Existing data backfill corrupts records | HIGH | Dry-run mode; idempotent script; backup before running |
| Tenant middleware breaks single-company flow | MEDIUM | Single-company bypass flag; test both paths |
| Alembic migration fails on existing DB | MEDIUM | Test on SQLite + PostgreSQL; provide manual SQL fallback |

---

## Open Questions

| Q | Owner | Needed By |
|---|-------|-----------|
| Confirm MST regex against current GDT rules | Legal/compliance | Before Task 4 (models.py) |
| Confirm all 8 company types per Luật Doanh nghiệp 2020 | Legal | Before Task 1 |
| Decision: single-company only at v1 launch? | Product | Before Task 13 |
| Decision: branch (Chi nhánh) as separate Company or child? | Legal | Before Task 1 |

---

*Plan created: 2026-08-17*
*Estimated total: 18 tasks, ~6-8 focused sessions*
*Each task: S or M scope (1-5 files)*
*TDD: Red (test first) → Green (implement) → Refactor per task*