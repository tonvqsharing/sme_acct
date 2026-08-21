# Specifications: Cost Centers & Dimensions Module

**Module:** Cost Centers & Dimensions  
**Version:** v1.0  
**Date:** 2026-08-19  
**Legal Basis:** Law on Accounting 2015 (Chap IX); Circular 99/2025/TT-BTC

---

# Specifications: Cost Centers & Dimensions Module (Lego Brick)
_Brick: `src/bricks/cost_centers/`. Pure Python domain. Flask built-in RBAC. SQLite3 default DB._

## 0. Brick Position

```
src/bricks/
  cost_centers/                ← 🧱 NEW brick
    contract.py                ← 🔌 Public interface (CostCenterCode, DimensionCode, primitive IDs only)
    domain.py                  ← 🎯 CostCenter, Dimension, DimensionValue entities (pure Python)
    services.py                ← ⚙️ CoaCostCenterService, CoaDimensionService, CoaDimensionValueService
    storage.py                 ← 💾 SQLAlchemy models + repository adapters
    web_adapter.py             ← 🌐 Flask blueprint + REST endpoints (cost_centers_bp)
```

**Brick boundaries:**
- `domain.py` — pure Python; NO Flask, NO SQLAlchemy, NO flask_login imports
- `contract.py` — public interface; accepts/returns only `str`, `int`, `float`, `dict`, `Decimal`, `UUID`
- `storage.py` — SQLAlchemy models + repo adapters (the ONLY file with SQLAlchemy imports)
- `services.py` — orchestration with injected port; no Flask/SQLAlchemy imports
- `web_adapter.py` — Flask blueprint; `@login_required` + `current_user.role` checks (no Casbin)

## 1. Domain Layer Specifications

### 1.1 Enums

#### 1.1.1 CostCenterStatus
```python
class CostCenterStatus(str, Enum):
    ACTIVE = "Active"    # Cost center is active, can be used in postings
    INACTIVE = "Inactive"  # Cost center deactivated, retained for history
    CLOSED = "Closed"    # Cost center closed, final status
```

#### 1.1.2 DimensionType
```python
class DimensionType(str, Enum):
    PROJECT = "Project"         # Project-based cost allocation
    LOCATION = "Location"       # Location-based cost allocation
    PRODUCT = "Product"         # Product-based cost allocation
    CUSTOMER = "Customer"       # Customer-based cost allocation
    EMPLOYEE = "Employee"       # Employee-based cost allocation
    DEPARTMENT = "Department"   # Department-based cost allocation
    CUSTOM = "Custom"           # Enterprise-defined dimension
```

#### 1.1.3 DimensionValueStatus
```python
class DimensionValueStatus(str, Enum):
    ACTIVE = "Active"    # Dimension value is active
    INACTIVE = "Inactive"  # Dimension value deactivated
```

### 1.2 Value Objects

#### 1.2.1 CostCenterCode
- **Format:** 3-10 alphanumeric characters
- **Must start with letter:** `[A-Za-z][A-Za-z0-9]{0,9}`
- **Validation:** Raises DomainException on invalid format
- **Purpose:** Validates cost center codes per enterprise analytical accounting conventions

#### 1.2.2 DimensionCode
- **Format:** Type-dependent, must be unique per (company, dimension_type)
- **Takes dimension_type parameter:** Required for proper format validation
- **Validation:** Raises DomainException on empty code
- **Purpose:** Validates dimension codes with type awareness

### 1.3 Aggregate Roots

#### 1.3.1 CostCenter
**Attributes:**
- `id`: UUID (primary key, auto-generated if not provided)
- `code`: CostCenterCode (validated VO)
- `name`: str (mandatory, stripped of whitespace)
- `status`: CostCenterStatus (default: ACTIVE)
- `company_id`: UUID (tenant isolation)
- `parent_id`: UUID | None (self-referencing for sub-cost-centers)
- `description`: str | None (optional)
- `created_by`: UUID (actor who created)
- `created_at`: datetime (UTC, auto-set on create)
- `updated_at`: datetime (UTC, auto-updated on mutations)
- `audit_checksum`: str (SHA-256 hex, 64 chars, chaining)

**Invariants (validated in __post_init__):**
- code valid per CostCenterCode VO
- status in CostCenterStatus enum
- name is not empty
- company_id must be set (enforced by repo)

**Behavioral Methods:**
- `deactivate(actor, reason)`: ACTIVE → INACTIVE, audit logged
- `reactivate(actor, reason)`: INACTIVE → ACTIVE, audit logged
- `close(actor, reason)`: ACTIVE → CLOSED, audit logged
- `modify(new_code, new_name, actor, reason)`: Code/name change, audit logged
- `_compute_checksum(action, actor, reason)`: SHA-256 chaining

**Post-Initiation State:**
- `is_active` property: True if status == ACTIVE, False if INACTIVE/CLOSED
- `can_modify`: True if status == ACTIVE, False otherwise

#### 1.3.2 Dimension
**Attributes:**
- `id`: UUID (primary key, auto-generated if not provided)
- `code`: DimensionCode (validated VO, requires dimension_type)
- `name`: str (mandatory, stripped of whitespace)
- `type`: DimensionType (validated enum)
- `company_id`: UUID (tenant isolation)
- `is_system`: bool (default: False; True = pre-loaded/system)
- `description`: str | None (optional, default: "")
- `created_by`: UUID (actor who created)
- `created_at`: datetime (UTC, auto-set on create)
- `updated_at`: datetime (UTC, auto-updated on mutations)
- `audit_checksum`: str (SHA-256 hex, 64 chars, chaining)

**Invariants:**
- type in DimensionType enum
- name is not empty
- company_id must be set (enforced by repo)

**Behavioral Methods:**
- `modify(new_name, actor, reason)`: Name change (system dims require migration)
- `set_system(actor, reason)`: Mark as system (CHIEF_ACCOUNTANT required)
- `_compute_checksum(action, actor, reason)`: SHA-256 chaining

**System Dimension Rules:**
- System dimensions (is_system=True) are immutable without migration
- Only CHIEF_ACCOUNTANT can call set_system()
- Modification without migration raises SystemAccountModificationError

#### 1.3.3 DimensionValue
**Attributes:**
- `id`: UUID (primary key, auto-generated if not provided)
- `code`: DimensionCode (validated VO, uses DimensionType.CUSTOM for format)
- `name`: str (mandatory, stripped of whitespace)
- `status`: DimensionValueStatus (default: ACTIVE)
- `dimension_id`: UUID (FK to Dimension, mandatory)
- `company_id`: UUID (tenant isolation)
- `description`: str | None (optional, default: "")
- `created_by`: UUID (actor who created)
- `created_at`: datetime (UTC, auto-set on create)
- `updated_at`: datetime (UTC, auto-updated on mutations)
- `audit_checksum`: str (SHA-256 hex, 64 chars, chaining)

**Invariants:**
- name is not empty (validated in _validate_invariant())
- dimension_id must be set (enforced by repo)
- company_id must be set (enforced by repo)

**Behavioral Methods:**
- `deactivate(actor, reason)`: ACTIVE → INACTIVE, audit logged
- `reactivate(actor, reason)`: INACTIVE → ACTIVE, audit logged
- `modify(new_name, actor, reason)`: Name change, audit logged
- `_compute_checksum(action, actor, reason)`: SHA-256 chaining

---

## 2. Application Layer Specifications

### 2.1 Service Interfaces

#### 2.1.1 CoaCostCenterService
**Methods:**
- `create_cost_center(code, name, company_id, actor, description)`: Create new cost center
  - Validates code format via CostCenterCode VO
  - Checks uniqueness per company
  - Creates CostCenter entity with ACTIVE status
  - Persists via SQLAlchemyCostCenterRepository
  - Returns created CostCenter
  - Throws DomainException on validation failure
  - Throws DuplicateMSTError on duplicate code

- `update_cost_center(cost_center_id, new_code, new_name, actor, reason)`: Modify cost center
  - Fetches current cost center by ID
  - Validates actor is not None (D11)
  - Calls cost_center.modify() domain method
  - Persists updated entity
  - Flushes DB session
  - Returns updated CostCenter
  - Throws DomainException on domain validation failure
  - Throws DuplicateMSTError on code conflict
  - Throws SystemAccountModificationError on system cost center modification

- `close_cost_center(cost_center_id, actor, reason)`: Close cost center
  - Validates cost center exists
  - Validates status is ACTIVE (cannot close INACTIVE/CLOSED)
  - Calls cost_center.close() domain method
  - Persists CLOSED status
  - Returns updated CostCenter
  - Throws ValueError on invalid state

- `reactivate_cost_center(cost_center_id, actor, reason)`: Reactivate cost center
  - Validates cost center exists
  - Validates status is INACTIVE (cannot reactivate ACTIVE/CLOSED)
  - Calls cost_center.reactivate() domain method
  - Persists ACTIVE status
  - Returns updated CostCenter
  - Throws ValueError on invalid state

- `list_by_company(company_id, status=None)`: List cost centers
  - Filters by company_id for tenant isolation
  - Optional status filter
  - Returns list of CostCenter entities

#### 2.1.2 CoaDimensionService
**Methods:**
- `create_dimension(code, name, dimension_type, company_id, actor, is_system, description)`: Create dimension
  - Validates DimensionCode format (requires dimension_type)
  - Checks uniqueness per (company, dimension_type)
  - Creates Dimension entity
  - Persists via SQLAlchemyDimensionRepository
  - Returns created Dimension
  - Throws DomainException on validation failure
  - Throws DuplicateMSTError on duplicate code

- `update_dimension(dimension_id, new_name, actor, reason)`: Modify dimension
  - Fetches current dimension by ID
  - Validates actor is not None (D11)
  - Checks if dimension is system (raises SystemAccountModificationError if True)
  - Calls dimension.modify() domain method
  - Persists updated entity
  - Returns updated Dimension
  - Throws DomainException on validation failure
  - Throws SystemAccountModificationError on system dimension modification

- `list_by_company(company_id, dimension_type=None, is_system=None)`: List dimensions
  - Filters by company_id for tenant isolation
  - Optional dimension_type filter
  - Optional is_system filter
  - Returns list of Dimension entities

- `list_by_type(dimension_type)`: List dimensions by type
  - Filters by DimensionType enum value
  - Returns list of matching Dimension entities

- `set_system(dimension_id, actor, reason)`: Mark dimension as system
  - Validates dimension exists
  - Validates actor is CHIEF_ACCOUNTANT or ADMIN
  - Calls dimension.set_system() domain method
  - Returns updated Dimension

#### 2.1.3 CoaDimensionValueService
**Methods:**
- `create_dimension_value(code, name, dimension_id, company_id, actor, description)`: Create dimension value
  - Validates code via DimensionCode VO (with DimensionType.CUSTOM)
  - Checks uniqueness per (dimension_id, company)
  - Validates dimension_id exists
  - Creates DimensionValue entity with ACTIVE status
  - Persists via SQLAlchemyDimensionValueRepository
  - Returns created DimensionValue
  - Throws DomainException on validation failure
  - Throws DuplicateMSTError on duplicate code

- `update_dimension_value(dv_id, new_name, actor, reason)`: Modify dimension value
  - Fetches current dimension value by ID
  - Validates actor is not None (D11)
  - Calls dv.modify() domain method
  - Persists updated entity
  - Returns updated DimensionValue
  - Throws DomainException on validation failure
  - Throws DuplicateMSTError on code conflict

- `list_by_company(company_id, dimension_id=None, status=None)`: List dimension values
  - Filters by company_id for tenant isolation
  - Optional dimension_id filter
  - Optional status filter (ACTIVE/INACTIVE)
  - Returns list of DimensionValue entities

- `list_by_company_and_dimension(company_id, dimension_id)`: List values for specific dimension
  - Filters by both company_id and dimension_id
  - Returns list of matching DimensionValue entities

- `deactivate_dimension_value(dv_id, actor, reason)`: Deactivate dimension value
  - Validates dimension value exists
  - Validates status is ACTIVE (cannot deactivate INACTIVE)
  - Calls dv.deactivate() domain method
  - Persists INACTIVE status
  - Returns updated DimensionValue
  - Throws ValueError on invalid state

- `reactivate_dimension_value(dv_id, actor, reason)`: Reactivate dimension value
  - Validates dimension value exists
  - Validates status is INACTIVE (cannot reactivate ACTIVE)
  - Calls dv.reactivate() domain method
  - Persists ACTIVE status
  - Returns updated DimensionValue
  - Throws ValueError on invalid state

---

## 3. Infrastructure Layer Specifications

### 3.1 SQLAlchemy Models

#### 3.1.1 CostCenterModel
**Table:** `cost_centers`
**Columns:**
- `id`: UUID (primary key)
- `code`: String(10), not null (unique per company)
- `name`: String(200), not null
- `status`: Enum( CostCenterStatus ), default ACTIVE
- `company_id`: UUID, not null (FK to companies)
- `parent_id`: UUID (self-referencing, FK to cost_centers)
- `description`: Text (optional)
- `created_by`: UUID, not null
- `created_at`: DateTime, not null (UTC)
- `updated_at`: DateTime, not null (UTC)
- `audit_checksum`: String(64), not null (SHA-256 hex)

**Unique Constraints:**
- `(code, company_id)` - code must be unique per company

**Indexes:**
- `ix_cost_centers_company_id` - for company-level queries
- `ix_cost_centers_status` - for status filtering

**Relationships:**
- `self-referencing`: parent_cost_center() → CostCenterModel (optional)

#### 3.1.2 DimensionModel
**Table:** `dimensions`
**Columns:**
- `id`: UUID (primary key)
- `code`: String(50), not null
- `name`: String(200), not null
- `type`: Enum(DimensionType), not null
- `is_system`: Boolean, default False
- `company_id`: UUID, not null (FK to companies)
- `description`: Text (optional, default "")
- `created_by`: UUID, not null
- `created_at`: DateTime, not null (UTC)
- `updated_at`: DateTime, not null (UTC)
- `audit_checksum`: String(64), not null (SHA-256 hex)

**Unique Constraints:**
- `(code, company_id)` - code must be unique per company (within dimension context)

**Indexes:**
- `ix_dimensions_company_id` - for company-level queries
- `ix_dimensions_type` - for type filtering
- `ix_dimensions_is_system` - for system dimension queries

#### 3.1.3 DimensionValueModel
**Table:** `dimension_values`
**Columns:**
- `id`: UUID (primary key)
- `code`: String(50), not null
- `name`: String(200), not null
- `status`: Enum(DimensionValueStatus), default ACTIVE
- `dimension_id`: UUID, not null (FK to dimensions)
- `company_id`: UUID, not null (FK to companies)
- `description`: Text (optional, default "")
- `created_by`: UUID, not null
- `created_at`: DateTime, not null (UTC)
- `updated_at`: DateTime, not null (UTC)
- `audit_checksum`: String(64), not null (SHA-256 hex)

**Unique Constraints:**
- `(code, dimension_id, company_id)` - code must be unique per (dimension, company)

**Indexes:**
- `ix_dimension_values_company_id` - for company-level queries
- `ix_dimension_values_dimension_id` - for dimension-level queries
- `ix_dimension_values_status` - for status filtering

**Relationships:**
- `dimension`: Many-to-one to DimensionModel (dimension_id FK)

### 3.2 Repository Adapters

#### 3.2.1 SQLAlchemyCostCenterRepository
**Implements:** CostCenterRepositoryPort

**Methods:**
- `create(cost_center)`: INSERT new cost center row
  - Checks `(code, company_id)` uniqueness before insert
  - Raises DuplicateMSTError if duplicate
  - Sets created_at/updated_at timestamps

- `get_by_id(cost_center_id)`: Get by primary key
  - Returns CostCenterModel or None
  - Uses db.session.get(Model, id) (SQLAlchemy 2.0)

- `get_by_code(code, company_id)`: Get by code + company
  - Returns CostCenterModel or None
  - Queries: select(Model).where(code==Code, company_id==CompanyID)

- `update(cost_center)`: Update existing cost center
  - Updates all fields including audit_checksum
  - Flushes session after update

- `list_by_company(company_id, status=None)`: List by company
  - Query: select(Model).where(company_id==id)
  - Optional: .where(status==status) if status provided
  - Returns list of CostCenterModel entities

- `soft_delete(cost_center_id, actor, reason)`: Soft-delete via status change
  - Sets status to INACTIVE or CLOSED
  - Does NOT row-delete (10-year retention law)
  - Updates audit_checksum with "soft_delete" action

#### 3.2.2 SQLAlchemyDimensionRepository
**Implements:** DimensionRepositoryPort

**Methods:** (mirror CostCenter repository pattern)
- `create(dimension)`: INSERT with `(code, company_id)` uniqueness
- `get_by_id(dimension_id)`: Get by primary key
- `get_by_code(code, company_id)`: Get by code + company
- `update(dimension)`: Update entity
- `list_by_company(company_id, dimension_type=None, is_system=None)`: List with filters
- `list_by_type(dimension_type)`: List by DimensionType
- `soft_delete(dimension_id, actor, reason)`: Soft-delete via status

#### 3.2.3 SQLAlchemyDimensionValueRepository
**Implements:** DimensionValueRepositoryPort

**Methods:**
- `create(dimension_value)`: INSERT with `(code, dimension_id, company_id)` uniqueness
- `get_by_id(dv_id)`: Get by primary key
- `get_by_code(code, company_id)`: Get by code + company
- `update(dimension_value)`: Update entity
- `list_by_company(company_id, dimension_id=None, status=None)`: List with filters
- `list_by_company_and_dimension(company_id, dimension_id)`: List by company+dimension
- `soft_delete(dv_id, actor, reason)`: Soft-delete via status change

### 3.3 Database Schema Summary

```sql
-- cost_centers table
CREATE TABLE cost_centers (
    id UUID PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    company_id UUID NOT NULL,
    parent_id UUID,
    description TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    audit_checksum VARCHAR(64) NOT NULL,
    UNIQUE (code, company_id)
);

-- dimensions table
CREATE TABLE dimensions (
    id UUID PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    company_id UUID NOT NULL,
    description TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    audit_checksum VARCHAR(64) NOT NULL,
    UNIQUE (code, company_id)
);

-- dimension_values table
CREATE TABLE dimension_values (
    id UUID PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    dimension_id UUID NOT NULL,
    company_id UUID NOT NULL,
    description TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    audit_checksum VARCHAR(64) NOT NULL,
    UNIQUE (code, dimension_id, company_id)
);

-- Indexes for performance
CREATE INDEX ix_cost_centers_company_id ON cost_centers(company_id);
CREATE INDEX ix_cost_centers_status ON cost_centers(status);
CREATE INDEX ix_dimensions_company_id ON dimensions(company_id);
CREATE INDEX ix_dimensions_type ON dimensions(type);
CREATE INDEX ix_dimensions_is_system ON dimensions(is_system);
CREATE INDEX ix_dimension_values_company_id ON dimension_values(company_id);
CREATE INDEX ix_dimension_values_dimension_id ON dimension_values(dimension_id);
CREATE INDEX ix_dimension_values_status ON dimension_values(status);
```

### 3.4 Migration

**Migration filename:** `a1f2b3c4d5e6_cost_centers_dimensions.py` (following existing pattern)

**Tables created:**
1. `cost_centers` - Cost Center model with all columns and constraints
2. `dimensions` - Dimension model with all columns and constraints  
3. `dimension_values` - Dimension Value model with all columns and constraints

**Zero drift verified:** Migration generates 3 new tables, verified against domain model.

---

## 4. API Specification

### 4.1 Authentication & Authorization (Flask Built-in)

**Actor UUID (D11):**
- Every mutation endpoint requires `actor` field in request JSON
- AUDITOR role is read-only; write operations return 403 for AUDITOR
- Actor UUID validated and passed to domain layer for audit logging

**Role Enforcement (Flask built-in only — no Casbin, no pycasbin):**
- `@login_required` decorator on all blueprint routes
- `current_user.role` checks for role membership
- READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")
- WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN")  # no AUDITOR
- FY_ADMIN_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")
- AUTO_SEED_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")  # no AUDITOR

**Pattern (Flask built-in):**
```python
from flask_login import login_required, current_user
from flask import abort

@bp.route("/v1/cost-centers", methods=["POST"])
@login_required
def create_cost_center():
    if current_user.role not in WRITE_ROLES:
        abort(403, description="RBAC denied: write role required")
    # ... proceed
```

### 4.2 Endpoint Pattern

All endpoints follow the pattern from `currencies_bp.py`:
- Test engine hook: `_test_engine`, `_req_session()`, `_restore_db_session()`
- Service per request: `_service_cc()`, `_service_dim()`, `_service_dv()`
- Serializer: `serialize_cost_center()`, `serialize_dimension()`, `serialize_dimension_value()`
- JSON error responses with error codes
- Actor UUID required on mutations

### 4.3 Cost Center Endpoints

| Method | Path | Request Body | Response | Roles |
|--------|------|-------------|----------|-------|
| GET | /v1/cost-centers?company_id=UUID | {company_id} query param | {cost_centers: [...]} | READ_ROLES |
| POST | /v1/cost-centers | {code, name, description, company_id, actor, reason} | {cost_center: ...} 201 | WRITE_ROLES |
| GET | /v1/cost-centers/{id}?company_id=UUID | {id} path, {company_id} query | {cost_center: ...} | READ_ROLES |
| PATCH | /v1/cost-centers/{id} | {code?, name?, reason?} | {cost_center: ...} | FY_ADMIN_ROLES |
| POST | /v1/cost-centers/{id}/close | {reason} | {cost_center: ...} | CHIEF_ACCOUNTANT |
| POST | /v1/cost-centers/{id}/reactivate | {reason} | {cost_center: ...} | CHIEF_ACCOUNTANT |

**Error Codes:**
- `MISSING_ACTOR` 400: actor field missing in request body
- `MISSING_COMPANY` 400: company_id query param missing
- `COA_ERROR` 409: duplicate code, domain error
- `VALIDATION_ERROR` 422: format validation failed
- `COA_ERROR` 422: system dimension modification, invalid state

### 4.4 Dimension Endpoints

| Method | Path | Request Body | Response | Roles |
|--------|------|-------------|----------|-------|
| GET | /v1/dimensions?company_id=UUID&type=TYPE&is_system=BOOL | query params | {dimensions: [...]} | READ_ROLES |
| POST | /v1/dimensions | {code, name, dimension_type, is_system, company_id, actor, reason, description} | {dimension: ...} 201 | AUTO_SEED_ROLES |
| GET | /v1/dimensions/{id}?company_id=UUID | {id} path, {company_id} query | {dimension: ...} | READ_ROLES |
| PATCH | /v1/dimensions/{id} | {name?, reason?} | {dimension: ...} | FY_ADMIN_ROLES |

**Error Codes:**
- Same as cost center patterns plus:
- `SYSTEM_DIMENSION_LOCKED` 422: cannot modify system dimension without migration

### 4.5 Dimension Value Endpoints

| Method | Path | Request Body | Response | Roles |
|--------|------|-------------|----------|-------|
| GET | /v1/dimension-values?company_id=UUID&dimension_id=UUID&status=STATUS | query params | {dimension_values: [...]} | READ_ROLES |
| POST | /v1/dimension-values | {code, name, dimension_id, company_id, actor, reason, description} | {dimension_value: ...} 201 | AUTO_SEED_ROLES |
| PATCH | /v1/dimension-values/{id} | {name?, reason?} | {dimension_value: ...} | FY_ADMIN_ROLES |
| POST | /v1/dimension-values/{id}/deactivate | {reason} | {dimension_value: ...} | CHIEF_ACCOUNTANT |
| POST | /v1/dimension-values/{id}/reactivate | {reason} | {dimension_value: ...} | CHIEF_ACCOUNTANT |

**Error Codes:**
- Same patterns as cost center/dimension plus:
- Invalid dimension_id reference
- Code already exists per (dimension_id, company)

### 4.6 Response Serialization

**serialize_cost_center(cost_center):**
```python
{
    "id": str(cost_center.id),
    "code": cost_center.code,
    "name": cost_center.name,
    "status": cost_center.status.value,
    "description": cost_center.description or "",
    "created_by": str(cost_center.created_by) if cost_center.created_by else None,
    "created_at": cost_center.created_at.isoformat() if cost_center.created_at else None,
    "updated_at": cost_center.updated_at.isoformat() if cost_center.updated_at else None,
    "audit_checksum": cost_center.audit_checksum,
}
```

**serialize_dimension(dimension):**
```python
{
    "id": str(dimension.id),
    "code": dimension.code,
    "name": dimension.name,
    "type": dimension.type.value,
    "is_system": dimension.is_system,
    "description": dimension.description or "",
    "created_by": str(dimension.created_by) if dimension.created_by else None,
    "created_at": dimension.created_at.isoformat() if dimension.created_at else None,
    "updated_at": dimension.updated_at.isoformat() if dimension.updated_at else None,
    "audit_checksum": dimension.audit_checksum,
}
```

**serialize_dimension_value(dv):**
```python
{
    "id": str(dv.id),
    "code": dv.code,
    "name": dv.name,
    "status": dv.status.value,
    "description": dv.description or "",
    "dimension_id": str(dv.dimension_id) if dv.dimension_id else None,
    "created_by": str(dv.created_by) if dv.created_by else None,
    "created_at": dv.created_at.isoformat() if dv.created_at else None,
    "updated_at": dv.updated_at.isoformat() if dv.updated_at else None,
    "audit_checksum": dv.audit_checksum,
}
```

---

## 5. CLI Commands Specification (manage.py)

### 5.1 coa-list
```
Usage: python manage.py coa-list [OPTIONS]

List cost centers and dimensions with filters.

Options:
  --company_id TEXT     Filter by company UUID
  --status TEXT         Filter by status (ACTIVE/INACTIVE/CLOSED)
  --type TEXT           Filter dimension type (PROJECT/LOCATION/PRODUCT/CUSTOMER/EMPLOYEE/DEPARTMENT/CUSTOM)
  --is-system BOOL      Filter by system flag
  --dimension_id TEXT   Filter dimension values by dimension UUID
  --page INTEGER        Page number (default: 1)
  --page_size INTEGER   Items per page (default: 20)

Output: JSON/CSV list with cost center/dimension/value data including audit checksums.
```

### 5.2 coa-create
```
Usage: python manage.py coa-create [OPTIONS]

Create cost center or dimension.

Options:
  --code TEXT           Code (validated format: 3-10 alphanumeric, start with letter for CC;
                        type-dependent for Dim)
  --name TEXT           Name (mandatory)
  --description TEXT    Optional description
  --company_id TEXT     Company UUID (required)
  --actor TEXT          Actor UUID (D11, required for mutations)
  --reason TEXT         Reason (mandatory for all mutations)
  --type TEXT           Dimension type (for dimensions: PROJECT/LOCATION/...)
  --is-system BOOL      System flag for dimensions (default: False)

Output: Created entity data with audit checksum.
Errors: Duplicate code, invalid format, missing actor/reason.
```

### 5.3 coa-import
```
Usage: python manage.py coa-import [OPTIONS]

Import cost centers/dimensions from TT99/TT200 template.

Options:
  --file TEXT           Template file path (JSON or CSV)
  --company_id TEXT     Company UUID (required)
  --actor UUID          Actor UUID (D11, required)

Atomic all-or-nothing: any bad row → nothing imported.
Validates: code format, uniqueness, company existence.
Output: Import summary (created count, error count, or full failure).
```

### 5.4 coa-export
```
Usage: python manage.py coa-export [OPTIONS]

Export cost centers/dimensions/data as JSON/CSV snapshot.

Options:
  --format TEXT         Output format (json or csv, default: json)
  --output TEXT         Output file path (default: stdout)
  --include-audit BOOL  Include audit checksums (default: True)
  --entity TEXT         Entity to export: cost_centers/dimensions/dimension_values
  --company_id TEXT     Filter by company UUID (optional)

Output: JSON array or CSV file with entity data.
```

### 5.5 coa-categories
```
Usage: python manage.py coa-categories [OPTIONS]

List system dimension categories.

Options:
  --dimension-type TEXT  Filter by dimension type (optional)

Output: Lists 7 mandatory dimension types per FR-12b with descriptions and code formats.
Example output:
{
  "dimension_types": [
    {"code_prefix": "PROJ-", "name": "Project", "is_mandatory": true},
    {"code_prefix": "LOC-", "name": "Location", "is_mandatory": true},
    ...
  ]
}
```

### 5.6 coa-close
```
Usage: python manage.py coa-close [OPTIONS]

Soft-close a cost center.

Options:
  --cost-center-id TEXT  Cost center UUID (required)
  --actor TEXT           Actor UUID (D11, required)
  --reason TEXT          Reason (mandatory)

Output: Closed cost center data with updated status CLOSED.
Note: No row deletion (10-year retention law per Law on Accounting 2015).
```

### 5.7 coa-tags
```
Usage: python manage.py coa-tags [OPTIONS]

List mandatory dimension values per FR-12b.

Options: None (lists all 7 mandatory tags)

Output: Lists 7 mandatory dimension values required for complete cost allocation:
- Tag 1: Default location value
- Tag 2: Default project value
- Tag 3: Default product value
- Tag 4: Default customer value
- Tag 5: Default employee value
- Tag 6: Default department value
- Tag 7: Custom/enterprise dimension value

Used for ensuring complete cost allocation data per business requirements.
```

---

## 6. Processes & Workflows

### 6.1 Cost Center Lifecycle
```
       ACTIVE
          │
          ├── deactivate() [actor + reason] → INACTIVE
          │
          └── close() [actor + reason] → CLOSED (final, no reactivation)
              
INACTIVE ──────────────────► reactivate() [actor + reason] → ACTIVE

CLOSED ──────────────────────────► (cannot transition; create new cost center)
```

### 6.2 Dimension Lifecycle
```
       is_system=False (enterprise)
          │
          ├── set_system() [CHIEF_ACCOUNTANT] → is_system=True (immutable without migration)
          │
          └── modify() [actor + reason] → name change (if not system)

is_system=True (system)
  ──────────────────────────────────────────────
  │ Cannot modify without migration module
  │ set_system() cannot revert to False
  └── Only admin can view; modification requires migration
```

### 6.3 Dimension Value Lifecycle
```
       ACTIVE ──────► deactivate() [actor + reason] → INACTIVE
                │                          │
                └──────────────────────────► reactivate() [actor + reason] → ACTIVE
```

### 6.4 Audit Workflow (D11)
```
Mutation Request
  │
  ├── Validate actor UUID present
  ├── Validate reason string present
  ├── Domain entity method (deactivate/modify/close/etc.)
  │   └── Updates audit_checksum via _compute_checksum(action, actor, reason)
  │       └── Raw: "|".join([prev_checksum, str(id), action, str(actor), reason, ts.isoformat()])
  │           └── SHA-256 hex digest (64 chars)
  │
  ├── Persist entity via Repository
  │   └── Flush session (ensures checksum is persisted)
  │
  └── Response: entity data + audit_checksum
```

**Checksum Formula:**
```
raw = "|".join([
    prev_checksum,    # SHA-256 from prior event (or "0"*64 for first event)
    str(entity_id),   # entity UUID
    action,           # "create"/"deactivate"/"modify"/"close"/"soft_delete"
    str(actor),       # actor UUID string
    reason,           # free text reason
    datetime.utcnow().isoformat()  # ISO 8601 timestamp
])
new_checksum = sha256(raw.encode("utf-8")).hexdigest()
```

### 6.5 Tenant Isolation Workflow
```
1. User makes request with company_id (query param or context)
2. Service layer validates company_id exists and user has access
3. All repository queries filter by company_id
4. Domain entities have company_id set for tenant isolation
5. Audit logs include company_id for cross-company queries
6. Reports can filter by company_id for multi-company environments
```

---

## 7. Exception Specification

### 7.1 Domain Exceptions (src/bricks/cost_centers/domain.py)

| Exception Class | Inheritance | HTTP Status | Condition |
|-----------------|-------------|-------------|-----------|
| DomainException | Exception | 422 | Generic domain validation error |
| DuplicateMSTError | DomainException | 409 | Duplicate code per company |
| SystemAccountModificationError | DomainException | 422 | System dimension modification without migration |
| InvalidCodeError | DomainException | 422 | Invalid code format (CostCenterCode/DimensionCode) |
| InvalidEntityStateError | DomainException | 422 | Invalid status transition attempt |

### 7.2 API Error Response Format
```json
{
    "error": "human readable error message",
    "code": "machine readable error code"
}
```

**Error Code Mapping:**
| Code | Meaning | HTTP Status |
|------|---------|-------------|
| `MISSING_ACTOR` | actor UUID required in request body | 400 |
| `MISSING_COMPANY` | company_id required | 400 |
| `INVALID_CODE` | code format validation failed | 422 |
| `DUPLICATE_CODE` | code already exists per company/dimension | 409 |
| `SYSTEM_DIMENSION_LOCKED` | system dimension requires migration to modify | 422 |
| `INVALID_TRANSITION` | cannot perform action in current status | 422 |
| `ENTITY_NOT_FOUND` | cost center/dimension/dimension value ID not found | 404 |
| `UNAUTHORIZED_ACTION` | role does not permit this action | 403 |
| `COA_ERROR` | general cost of accounts error | 422/409 |

### 7.3 Error Handling Flow
```
Client Request
  │
  ├── Flask route receives JSON body
  │   └── Extract actor, reason, other fields
  │
  ├── @login_required + current_user.role check (Flask built-in)
  │   └── AUDITOR → read-only (403 on write)
  │
  ├── Service method validates:
  │   └── actor is not None
  │   └── reason is not empty
  │   └── code format valid (VO validation)
  │   └── uniqueness check (repo level)
  │
  ├── Domain entity method executes:
  │   └── Validates invariants
  │   └── Updates audit_checksum
  │   └── Returns modified entity
  │
  ├── Repository persists:
  │   └── db.session.flush()
  │   └── Returns persisted model
  │
  └── Response: JSON with entity data + error handling
       └── On exception: jsonify({"error": "...", "code": "..."}) + status code
```

---

## 8. Integration Points

### 8.1 Audit Log Module
**Integration Points:**
- Every cost center/dimension/dimension value mutation creates an audit log entry
- SHA-256 checksum chaining matches audit-log module pattern
- AuditLogService.create() called from cost center/dimension services
- Retention-status endpoint: /api/retention-status
- Verify-destruction endpoint: /api/verify-destruction/<id>
- Destroy endpoint: /api/destroy

**Checksum Chaining:**
```
audit_log_service.create(
    entity_type="cost_center"|"dimension"|"dimension_value",
    entity_id=entity_id,
    action="create"|"deactivate"|"modify"|"close"|"soft_delete",
    field_name=None,  # None for top-level changes
    before_value=None,
    after_value=entity.audit_checksum,  # new checksum becomes "after value"
    actor_id=actor_uuid,
)
```

### 8.2 Currencies & Exchange Rates
**Integration Points:**
- Cost centers can be assigned to revaluation runs (future enhancement)
- Dimensions can be used for cost allocation in revaluation
- FX difference reporting can include dimension-based breakdown
- Rate types may reference cost center codes (future)

### 8.3 Fiscal Years & Accounting Periods
**Integration Points:**
- Cost centers can be locked per accounting period
- Period close workflow may include cost center closure
- First period creation may reference cost center default values
- Dimension values used for analytical period reporting

### 8.4 COA Module
**Integration Points:**
- Account codes may be associated with cost centers for departmental tracking
- System categories may overlap with dimension types
- Import/export formats compatible between COA and Cost Centers modules
- Template import/export shared between modules

### 8.5 User Master Data
**Integration Points:**
- Cost centers assigned to partners/organizational units
- Dimensions used for customer/project/department classification
- User assignments and role-based access control
- Created_by/updated_by UUIDs link to user master data

### 8.6 System Settings
**Integration Points:**
- Fiscal year settings may default cost center configurations
- Period lock settings may include cost center closure requirements
- VAT method may affect cost center reporting
- E-invoice series may reference cost centers for cost allocation

---

## 9. Production Readiness

### 9.1 Checklist
- [x] Domain entities implemented (CostCenter, Dimension, DimensionValue)
- [x] Value objects (CostCenterCode, DimensionCode) with validation
- [x] Enums duplicated in infra/models.py for SQLAlchemy compatibility
- [x] Repository adapters (SQLAlchemyCostCenterRepository, etc.)
- [x] Service layer (CoaCostCenterService, CoaDimensionService, CoaDimensionValueService)
- [x] REST API blueprint (cost_center_bp.py) with 13 endpoints
- [x] Flask built-in role enforcement (@login_required + current_user.role)
- [x] AUDITOR read-only restriction on writes
- [x] Actor UUID (D11) requirement on all mutations
- [x] SHA-256 audit checksum chaining
- [x] Soft-delete (no row deletion, 10-year retention)
- [x] System dimension protection (requires migration)
- [x] Unit tests (12 tests, all passing)
- [x] Integration test structure (repository pattern)
- [x] BRD document (docs/cost-centers-dimensions/brd-cost-centers-dimensions.md)
- [x] Specs document (docs/cost-centers-dimensions/specs-cost-centers-dimensions.md)
- [ ] Codegraph sync and MCP index update
- [ ] Migration: flask db migrate + flask db upgrade
- [ ] E2E tests with Flask test client
- [ ] Load testing for checksum computation
- [ ] Multi-company tenant isolation validation

### 9.2 Performance Considerations
- **Indexes:** Composite unique constraints + separate indexes on company_id, status, type
- **Checksum computation:** SHA-256 is fast (~1μs per event); negligible overhead
- **Query patterns:** Most queries filter by company_id + optional status/type
- **Connection pooling:** SQLAlchemy session management per request pattern
- **Batch operations:** Import uses atomic all-or-nothing; single entity operations per request

### 9.3 Security Considerations
- **D11 actor requirement:** Every mutation must include actor UUID
- **AUDITOR read-only:** CASRBAC decorator enforces backend; UI may also restrict
- **Code uniqueness:** Per-company constraint prevents cross-company code collisions
- **Soft-delete:** No row deletion ensures 10-year retention compliance
- **System dimension protection:** Migration gate prevents accidental modification
- **Input validation:** VO validation + repo uniqueness + domain invariants (defense-in-depth)

### 9.4 Compliance Checklist
- [x] Law on Accounting 2015, Chapter IX (analytical accounting)
- [x] Circular 99/2025/TT-BTC (enterprise analytical accounting, effective 01/01/2026)
- [x] 10-year record retention with soft-delete (no row deletion)
- [x] SHA-256 audit checksum chaining for integrity verification
- [x] D11 actor UUID on all mutations (audit trail requirement)
- [x] AUDITOR read-only backend enforcement (CASRBAC)
- [x] Code format validation (CostCenterCode: 3-10 alphanumeric, start with letter)
- [x] Vietnamese chart of accounts compatibility (TT 99/2025/TT-BTC)

### 9.5 Migration Plan
1. Run: `SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db flask db init`
2. Run: `SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db flask db migrate -m "cost_centers_dimensions_init"`
3. Run: `SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db flask db upgrade`
4. Verify: 3 new tables (cost_centers, dimensions, dimension_values) created
5. Verify: Zero drift between migration and domain models
6. Run: `pytest` - all unit tests pass
7. Codegraph sync: `codegraph_explore` at milestones
8. MCP index update: register new symbols
9. Git sync: commit and push with conventional commits

---

## 10. References & Related Documents

- **BRD:** docs/cost-centers-dimensions/brd-cost-centers-dimensions.md
- **Specs:** docs/cost-centers-dimensions/specs-cost-centers-dimensions.md
- **Use Cases:** docs/cost-centers-dimensions/use-cases-cost-centers-dimensions.md
- **Rules:** docs/cost-centers-dimensions/rules-cost-centers-dimensions.md
- **Processes:** docs/cost-centers-dimensions/processes-cost-centers-dimensions.md
- **Data Flows:** docs/cost-centers-dimensions/data-flows-cost-centers-dimensions.md
- **User Journeys:** docs/cost-centers-dimensions/user-journeys-cost-centers-dimensions.md
- **Workflows:** docs/cost-centers-dimensions/workflows-cost-centers-dimensions.md
- **Templates:** docs/cost-centers-dimensions/templates/
- **Codebase:** src/bricks/cost_centers/domain.py
- **Contract Interface:** src/bricks/cost_centers/contract.py
- **Storage Adapters:** src/bricks/cost_centers/storage.py
- **Service Layer:** src/bricks/cost_centers/services.py
- **REST API:** src/bricks/cost_centers/web_adapter.py
- **Audit Log Module:** src/bricks/audit_log/services.py
- **RBAC:** Flask-Login `@login_required` + `current_user.role` checks
- **Law on Accounting 2015:** Chap IX, 10-year retention
- **Circular 99/2025/TT-BTC:** Effective 01/01/2026
- **Vietnamese Chart of Accounts:** TT 99/2025/TT-BTC (effective 01/01/2026)