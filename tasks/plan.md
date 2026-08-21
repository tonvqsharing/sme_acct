# Implementation Plan: Company Module (Root Aggregate)

## Overview
Implement Company module per `docs/company-module/specs-company.md`. Lego brick architecture.
Company is root aggregate — ALL other bricks need `company_id`. Build from domain out:
enums/exceptions → entities → contract → storage → services → web_adapter → migration → tests.
TDD per slice. No third-party integration (next version). SQLite3 default.

## Architecture Decisions
- Company is root aggregate. All other bricks reference via `company_id: str` (UUID passed as primitive).
- No cross-brick SQLAlchemy joins. Communication via `contract.py` primitives only.
- Domain layer pure Python — no Flask/SQLAlchemy imports.
- RBAC: Flask-Login `@login_required` + `current_user.role` checks only.
- MST uniqueness enforced at DB level + domain validation.
- Audit trail via `created_by`, `updated_by`, `config_version` (optimistic lock).
- `BankAccount` stored as JSON field (not separate table) per spec v1.

## Task List (slices, TDD red-green)

### Slice 1: Domain enums + exceptions
- [ ] `src/bricks/company/domain.py`: CompanyType, CompanyStatus, AccountingRegime enums
- [ ] `src/bricks/company/domain.py`: Company dataclass, BankAccount dataclass, TaxId value object
- [ ] `src/bricks/company/domain.py`: CompanyError base + DuplicateMSTError, CompanyNotFoundError, CompanyLockedError, InvalidCompanyStateError
- [ ] `tests/unit/company/test_company_enums.py` (red first)
- [ ] `tests/unit/test_company_domain.py` (entity construction, validation, state machine)

**Acceptance criteria:**
- [ ] Enums match spec values exactly
- [ ] TaxId validates format: `r"^\d{10}(-\d{3})?$"`
- [ ] Company dataclass has all 30+ fields from spec
- [ ] All domain tests pass, zero Flask/SQLAlchemy imports in domain.py

### Slice 2: Contract interface
- [ ] `src/bricks/company/contract.py`: CompanyRepositoryPort (ABC)
- [ ] `src/bricks/company/contract.py`: CompanyServiceProtocol (typing.Protocol)
- [ ] `tests/unit/test_company_contract.py` (verify interface shape)

**Acceptance criteria:**
- [ ] Port methods match spec: create, get_by_id, get_by_mst, list_active, update, deactivate, list_subsidiaries
- [ ] Only primitive types in/out (str, int, float, dict, Decimal, UUID)
- [ ] No domain/model imports in contract.py

### Slice 3: Storage layer (models + repo adapters)
- [ ] `src/bricks/company/storage.py`: CompanyModel (SQLAlchemy 2.0 mapped_column)
- [ ] `src/bricks/company/storage.py`: SQLAlchemyCompanyRepository (implements CompanyRepositoryPort)
- [ ] `tests/integration/test_company_repository.py` (CRUD + MST uniqueness + list_active)

**Acceptance criteria:**
- [ ] CompanyModel maps all DB columns per spec schema
- [ ] MST unique constraint enforced
- [ ] company_id as UUID PK with default gen_random_uuid
- [ ] JSON fields for business_fields, bank_accounts
- [ ] Audit fields: created_at, updated_at, created_by, updated_by, config_version
- [ ] Repository tests use SQLite in-memory

### Slice 4: Service layer
- [ ] `src/bricks/company/services.py`: CompanyService (create, get, update, deactivate, dissolve)
- [ ] `src/bricks/company/services.py`: TenantService (resolve_company, check_access, scope_query)
- [ ] `tests/unit/test_company_service.py` (business rules, RBAC, audit log)

**Acceptance criteria:**
- [ ] create_company: validates MST uniqueness, legal fields completeness
- [ ] update_company: MST locked after invoicing, config_version increment
- [ ] deactivate_company: checks no open periods, no pending invoices
- [ ] dissolve_company: CHIEF_ACCOUNTANT only, all periods closed
- [ ] TenantService.scope_query appends WHERE company_id = :cid
- [ ] All service tests use fake repo (no DB)

### Slice 5: Web adapter (Flask blueprint + REST API)
- [ ] `src/bricks/company/web_adapter.py`: companies_bp Blueprint
- [ ] `src/bricks/company/web_adapter.py`: REST endpoints (POST/GET/PATCH/DELETE /api/v1/companies)
- [ ] `tests/integration/test_company_api.py` (endpoint tests with test client)

**Acceptance criteria:**
- [ ] All endpoints have `@login_required`
- [ ] Role checks: ACCOUNTANT/CHIEF_ACCOUNTANT can CRUD, AUDITOR read-only
- [ ] POST validates MST format + uniqueness
- [ ] PATCH returns 409 on MST change if invoices exist
- [ ] DELETE (deactivate) returns 200 with updated status
- [ ] Error responses match spec format: `{"error": "Mô tả lỗi", "code": "ERROR_CODE"}`

### Slice 6: App registration + migration
- [ ] `src/app.py`: Register companies_bp blueprint
- [ ] `migrations/versions/xxx_add_companies_table.py`: Alembic migration
- [ ] Verify migration applies on fresh SQLite

**Acceptance criteria:**
- [ ] Blueprint registered at `/api/v1/companies`
- [ ] Migration creates companies table with all columns + constraints
- [ ] Migration rollback works

### Slice 7: Full test suite + quality gates
- [ ] Run `ruff check src/bricks/company/`
- [ ] Run `black --check src/bricks/company/`
- [ ] Run `mypy src/bricks/company/`
- [ ] Run `pytest tests/unit/company/ tests/integration/test_company_*`
- [ ] Verify all tests pass, no regressions

### Slice 8: Docs sync + git
- [ ] Update `docs/company-module/README.md` status
- [ ] Update `AGENTS.md` Company module status
- [ ] codegraph sync
- [ ] git commit (no push — review required)

## Checkpoints
- After Slice 2: Domain + contract defined; unit tests green.
- After Slice 4: Service tests green; full pytest still green.
- After Slice 5: API integration tests green.
- After Slice 6: Migration applies; app starts.
- After Slice 8: Ready for review.

## Risks
| Risk | Mitigation |
|---|---|
| Breaking existing tests | Run full suite after each slice |
| MST validation drift | TaxId value object centralizes format |
| JSON field portability | SQLite JSON function limited; keep queries simple |
| Audit trail gaps | Service layer enforces created_by/updated_by |

## Files Likely Touched
```
src/bricks/company/__init__.py
src/bricks/company/domain.py
src/bricks/company/contract.py
src/bricks/company/storage.py
src/bricks/company/services.py
src/bricks/company/web_adapter.py
src/app.py
migrations/versions/xxx_add_companies_table.py
tests/unit/company/__init__.py
tests/unit/test_company_domain.py
tests/unit/test_company_enums.py
tests/unit/test_company_contract.py
tests/unit/test_company_service.py
tests/integration/test_company_repository.py
tests/integration/test_company_api.py
```
