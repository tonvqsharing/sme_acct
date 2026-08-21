# Business Requirements Document (BRD): Cost Centers & Dimensions Module

**Module:** Cost Centers & Dimensions  
**Version:** v1.0  
**Date:** 2026-08-19  
**Author:** SME Accounting Application Team  
**Legal Basis:** Law on Accounting 2015 (Chap IX); Circular 99/2025/TT-BTC (effective 01/01/2026)

---

## 1. Overview

### 1.1 Purpose
The Cost Centers & Dimensions module enables analytical accounting for Vietnamese SMEs, allowing organizations to track and allocate costs across departments, branches, projects, locations, products, customers, and other analytical categories. This module supports compliance with Circular 99/2025/TT-BTC and the Law on Accounting 2015 requirements for 10-year retention of accounting records.

### 1.2 Business Context
- **Cost Centers (Chi phí trung tâm):** Departments, branches, or organizational units that incur costs
- **Dimensions (Khối đoán):** Analytical categories for cost allocation (Project, Location, Product, Customer, Employee, Department, Custom)
- **Dimension Values (Giá trị khối đoán):** Specific instances within dimensions (e.g., "Hanoi" under Location, "Project Alpha" under Project)

### 1.3 Target Users
- **CHIEF_ACCOUNTANT:** Full CRUD access to cost centers and dimensions
- **ADMIN:** Full CRUD access
- **ACCOUNTANT:** Read-only access + own cost center assignments
- **AUDITOR:** Read-only access (audit log verification)
- **DIRECTOR:** Read/write access to strategic dimensions

### 1.4 High-Level Requirements
- Cost centers support status lifecycle: ACTIVE → INACTIVE → CLOSED
- Dimensions are system-defined or enterprise-defined with modification restrictions
- Dimension values must belong to a valid dimension and company
- All mutations require actor UUID and reason (audit trail per D11)
- SHA-256 checksum chaining for audit integrity (mirrors audit-log module)
- System dimensions/prohibited from modification without migration
- 10-year retention with soft-delete (no row deletion per Law on Accounting 2015)

---

## 2. Legal & Regulatory Framework

### 2.1 Law on Accounting 2015
- **Chapter IX:** Analytical accounting and cost calculation
- **10-year retention** of all accounting records
- **Certificate of Destruction** requirement after retention period
- **SHA-256 checksum chaining** for audit log integrity

### 2.2 Circular 99/2025/TT-BTC (effective 01/01/2026)
- Enterprise analytical accounting requirements
- Cost center code format: 3-10 alphanumeric characters, starting with letter
- Dimension code format: type-dependent, unique per company
- VAT Method and E-Invoice mode integration requirements

### 2.3 Circular 133/2016/TT-BTC
- Cost allocation methodologies
- Inter-department cost transfer rules

### 2.4 Vietnamese Chart of Accounts (TT 99/2025/TT-BTC)
- Effective from 01/01/2026
- Account code format: `^[1-9]\d{2}$` or `^[1-9]\d{3}$`
- System categories with mandatory report lines

---

## 3. Module Scope

### 3.1 In Scope
- [x] Cost Center management (CRUD, status lifecycle)
- [x] Dimension management (CRUD, system/enterprise classification)
- [x] Dimension Value management (CRUD, per-dimension validation)
- [x] Code validation (CostCenterCode VO: 3-10 alphanumeric, start with letter)
- [x] DimensionCode VO with type awareness
- [x] SHA-256 audit checksum chaining
- [x] Actor UUID requirement on all mutations (D11)
- [x] System dimension protection (requires migration)
- [x] Soft-delete (status-based, no row deletion)
- [x] Uniqueness per company per dimension
- [x] REST API endpoints (13 endpoints)
- [x] 7 CLI commands (manage.py)
- [x] Flask built-in role-based enforcement (@login_required + current_user.role)
- [x] AUDITOR read-only restriction on writes

### 3.2 Out of Scope (v2)
- [ ] kết chuyển accounts 911/421 + real opening balances (awaits ledger module)
- [ ] CSV locked-date hook (rates company-agnostic, skipped by design)
- [ ] Multi-company consolidation logic (research report flags 7 critical gaps)
- [ ] Real opening balance posting for first period creation

---

## 4. Entity Relationship Diagram

```
CostCenter (1)────(m) DimensionValue
     │
     └── parent_id (self-referencing for sub-cost-centers)

Dimension (1)────(m) DimensionValue

CostCenter and Dimension are independent aggregates:
- Both have company_id for tenant isolation
- Both have audit_checksum for SHA-256 chaining
- Both have status lifecycle (ACTIVE/INACTIVE/CLOSED)
- Dimensions have is_system flag (pre-loaded vs enterprise-defined)
```

---

## 5. Key Business Rules (Hard-Coded)

### 5.1 Cost Center Rules
| Rule ID | Rule Description | Enforcement |
|---------|-----------------|-------------|
| CC-001 | Code must be 3-10 alphanumeric characters, starting with a letter | CostCenterCode VO validation |
| CC-002 | Code must be unique per company | Repository-level unique constraint |
| CC-003 | New cost centers are ACTIVE by default | Domain entity default |
| CC-004 | Status can only change: ACTIVE→INACTIVE→CLOSED | Domain deactivate()/close() methods |
| CC-005 | System check: cannot deactivate CLOSED cost center | Domain invariant validation |
| CC-006 | Modifications require actor UUID and reason | Service layer defense-in-depth |
| CC-007 | Cannot modify system-generated cost centers | SystemAccountModificationError |
| CC-008 | Audit checksum chaining: SHA-256 hash of prev+id+action+actor+reason+ts | _compute_checksum() method |

### 5.2 Dimension Rules
| Rule ID | Rule Description | Enforcement |
|---------|-----------------|-------------|
| DIM-001 | Code format depends on dimension type | DimensionCode VO (takes dimension_type) |
| DIM-002 | Code must be unique per (company, dimension) | Repository composite unique constraint |
| DIM-003 | New dimensions are is_system=False by default | Domain entity default |
| DIM-004 | System dimensions (is_system=True) require CHIEF_ACCOUNTANT to set | set_system() method with actor validation |
| DIM-005 | System dimensions cannot be modified without migration | SystemAccountModificationError in modify() |
| DIM-006 | at least 1 dimension value per dimension required | Repository validation |
| DIM-007 | Dimension values inherit company_id for tenant isolation | Model-level FK |
| DIM-008 | Audit checksum chaining same pattern as CostCenter | _compute_checksum() method |

### 5.3 Dimension Value Rules
| Rule ID | Rule Description | Enforcement |
|---------|-----------------|-------------|
| DV-001 | Code must be unique per (dimension_id, company) | Repository composite unique constraint |
| DV-002 | Name is mandatory | _validate_invariant() raises ValueError if empty |
| DV-003 | Status can only change: ACTIVE→INACTIVE | deactivate() method |
| DV-004 | Reactivation returns to ACTIVE status | reactivate() method |
| DV-005 | Modifications require actor UUID and reason | Service layer defense-in-depth |
| DV-006 | Must belong to valid dimension_id | FK constraint + repository validation |
| DV-007 | Audit checksum chaining SHA-256 | _compute_checksum() method |

### 5.4 Actor & Audit Rules (D11)
| Rule ID | Rule Description | Enforcement |
|---------|-----------------|-------------|
| D11-001 | Every mutation must include actor UUID | @login_required + current_user.role check + service layer validation |
| D11-002 | Every mutation must include reason string | Service method signature (reason parameter) |
| D11-003 | AUDITOR role is read-only on writes | @login_required + current_user.role check restricts AUDITOR |
| D11-004 | Audit log entries chained via SHA-256 | Mirrors audit-log module pattern |
| D11-005 | 10-year retention per Law on Accounting 2015 | Soft-delete + retention-status endpoint |

### 5.5 Role-Based Access Control
| Role | Cost Centers | Dimensions | Dimension Values |
|------|-------------|-----------|------------------|
| AUDITOR | Read-only | Read-only | Read-only |
| ACCOUNTANT | Read + own writes | Read + own writes | Read + own writes |
| ADMIN | Full CRUD | Full CRUD | Full CRUD |
| CHIEF_ACCOUNTANT | Full CRUD | Full CRUD | Full CRUD |
| DIRECTOR | Read + strategic writes | Read + strategic writes | Read + strategic writes |

---

## 6. Workflows & Processes

### 6.1 Cost Center Creation Workflow
```
1. User submits: code, name, description, company_id, actor, reason
2. Validation: CostCenterCode format check (3-10 chars, starts with letter)
3. Uniqueness check: code not exists per company
4. Domain create: CostCenter(code, name, company_id, created_by, ACTIVE)
5. Persist: SQLAlchemyCostCenterRepository.create()
6. Audit: SHA-256 checksum chaining "create" action
7. Response: 201 Created + serialized cost center
```

### 6.2 Cost Center Status Modification Workflow
```
ACTIVE → INACTIVE (deactivate)
   │           │
   │           └── actor + reason required
   │
   └── admin/CHIEF_ACCOUNTANT only

INACTIVE → ACTIVE (reactivate)
   │           │
   │           └── actor + reason required
   │
   └── CHIEF_ACCOUNTANT only

ACTIVE → CLOSED (close)
   │           │
   │           └── actor + reason required
   │
   └── CHIEF_ACCOUNTANT only

CLOSED → (cannot reactivate/renew; must create new cost center)
```

### 6.3 Dimension Creation Workflow
```
1. User submits: code, name, dimension_type, is_system, company_id, actor, reason
2. Validation: DimensionCode format check (type-dependent)
3. Uniqueness check: code not exists per (company, dimension_type)
4. Domain create: Dimension(code, name, dimension_type, company_id, created_by, is_system)
5. Persist: SQLAlchemyDimensionRepository.create()
6. Audit: SHA-256 checksum chaining "create" action
7. Response: 201 Created + serialized dimension
```

### 6.4 Dimension System Marking Workflow
```
1. CHIEF_ACCOUNTANT marks dimension as is_system=True
2. set_system(actor=CHIEF_ACCOUNTANT_UUID, reason="Migration completion")
3. System dimensions become immutable (require migration to modify)
4. Audit log records the system marking event
```

### 6.5 Dimension Value Creation Workflow
```
1. User submits: code, name, dimension_id, company_id, actor, reason, description (optional)
2. Validation: code not exists per (dimension_id, company)
3. Domain create: DimensionValue(code, name, dimension_id, company_id, created_by, ACTIVE)
4. Persist: SQLAlchemyDimensionValueRepository.create()
5. Audit: SHA-256 checksum chaining "create" action
6. Response: 201 Created + serialized dimension value
```

### 6.6 Deactivation/Reactivation Workflow (Dimension Values)
```
ACTIVE → INACTIVE (deactivate)
   │           └── actor + reason required
   └── CHIEF_ACCOUNTANT only

INACTIVE → ACTIVE (reactivate)
   │           └── actor + reason required
   └── CHIEF_ACCOUNTANT only
```

---

## 7. API Endpoints

### 7.1 Cost Centers

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | /v1/cost-centers | List cost centers by company | READ_ROLES |
| POST | /v1/cost-centers | Create cost center | WRITE_ROLES |
| GET | /v1/cost-centers/{id} | Get cost center by ID | READ_ROLES |
| PATCH | /v1/cost-centers/{id} | Modify cost center | FY_ADMIN_ROLES |
| POST | /v1/cost-centers/{id}/close | Close cost center | CHIEF_ACCOUNTANT |
| POST | /v1/cost-centers/{id}/reactivate | Reactivate cost center | CHIEF_ACCOUNTANT |

### 7.2 Dimensions

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | /v1/dimensions | List dimensions by company | READ_ROLES |
| POST | /v1/dimensions | Create dimension | AUTO_SEED_ROLES |
| GET | /v1/dimensions/{id} | Get dimension by ID | READ_ROLES |
| PATCH | /v1/dimensions/{id} | Modify dimension | FY_ADMIN_ROLES |

### 7.3 Dimension Values

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | /v1/dimension-values | List dimension values | READ_ROLES |
| POST | /v1/dimension-values | Create dimension value | AUTO_SEED_ROLES |
| PATCH | /v1/dimension-values/{id} | Modify dimension value | FY_ADMIN_ROLES |
| POST | /v1/dimension-values/{id}/deactivate | Deactivate dimension value | CHIEF_ACCOUNTANT |
| POST | /v1/dimension-values/{id}/reactivate | Reactivate dimension value | CHIEF_ACCOUNTANT |

### 7.4 Read-Only Roles
- **AUDITOR** has read-only access to all endpoints
- Write operations return 403 Forbidden for AUDITOR role
- All write operations require actor UUID in request body

---

## 8. CLI Commands (manage.py)

### 8.1 coa-list
```
List accounts with filters:
  --company_id COMPANY_ID  Filter by company
  --status STATUS         Filter by status (ACTIVE/INACTIVE/CLOSED)
  --type TYPE            Filter by dimension type
```

### 8.2 coa-create
```
Create cost center/dimension:
  --code CODE             Code (validated format)
  --name NAME             Name (mandatory)
  --description DESC      Optional description
  --company_id ID         Company UUID
  --actor UUID            Actor UUID (D11)
  --reason REASON         Reason (mandatory for mutations)
  --type TYPE             Dimension type (for dimensions)
  --is-system FLAG        System flag (for dimensions)
```

### 8.3 coa-import
```
Import from TT99/TT200 template:
  --file PATH             Template file path
  --company_id ID         Company UUID
  --actor UUID            Actor UUID
  Atomic all-or-nothing: any bad row → nothing imported
```

### 8.4 coa-export
```
Export JSON/CSV snapshot:
  --format FORMAT         json or csv
  --output PATH           Output file path
  Includes: cost centers, dimensions, dimension values with audit data
```

### 8.5 coa-categories
```
List system categories:
  --dimension-type TYPE   Filter by dimension type
  Lists: 9 system dimension types with descriptions
```

### 8.6 coa-close
```
Soft-close cost center:
  --cost-center-id ID     Cost center UUID
  --actor UUID            Actor UUID (D11)
  --reason REASON         Reason (mandatory)
  Sets status: ACTIVE→CLOSED
  No row deletion (10-year retention law)
```

### 8.7 coa-tags
```
List mandatory dimension values:
  Lists: 7 mandatory tags per FR-12b business requirement
  Used for ensuring complete cost allocation data
```

---

## 9. Data Flows

### 9.1 Cost Center Data Flow
```
User Input → Validation (CostCenterCode VO) → Domain Create → Repository SQLAlchemy → Audit Checksum → Response
                                                          ↑                                    |
                                                          └──────────────────────────────────────┘
                                                    SHA-256 chaining (prev+id+action+actor+reason+ts)
```

### 9.2 Dimension Value Data Flow
```
User Input → Validation (DimensionCode VO + unique check) → Domain Create → Repository SQLAlchemy → Audit Checksum → Response
                                                                       ↑                                        |
                                                                       └────────────────────────────────────────┘
                                                                   SHA-256 chaining (prev+id+action+actor+reason+ts)
```

### 9.3 Status Change Data Flow
```
Request (id + actor + reason) → Service check (status transition valid) → Domain method (deactivate/reactivate/close) → Updated entity → Repository update → Flush → New audit checksum → Response
```

---

## 10. Exception Handling

### 10.1 Domain Exceptions
| Exception Class | HTTP Status | Condition |
|-----------------|-------------|-----------|
| DomainException | 422 | Validation errors, empty required fields, invalid format |
| DuplicateMSTError | 409 | Duplicate code per company |
| SystemAccountModificationError | 422 | System dimension modification without migration |
| InvalidCodeError | 422 | Invalid code format (CostCenterCode/DimensionCode) |

### 10.2 API Error Responses
```json
{"error": "actor là bắt buộc", "code": "MISSING_ACTOR"} 400
{"error": "company_id là bắt buộc", "code": "MISSING_COMPANY"} 400
{"error": "Cost Center code C01 already exists for company", "code": "COA_ERROR"} 409
{"error": "System dimension modification requires migration module", "code": "COA_ERROR"} 422
{"error": "Cannot deactivate cost center C01: current status is CLOSED", "code": "COA_ERROR"} 422
```

### 10.3 Audit Log Exceptions
- AuditLogService handles SHA-256 checksum validation
- Immutable audit entries (no UPDATE/DELETE on core table)
- 10-year retention with Certificate of Destruction workflow

---

## 11. Glossary

| Term | Vietnamese | English Definition |
|------|-----------|-------------------|
| Cost Center | Chi phí trung tâm | Department/branch/organizational unit that incurs costs |
| Dimension | Khối đoán | Analytical category for cost allocation |
| Dimension Value | Giá trị khối đoán | Specific instance within a dimension (e.g., "Hanoi" under Location) |
| ACTIVE | HOẠT ĐỘNG | Entity is active and can be used in postings |
| INACTIVE | KHÔNG HOẠT ĐỘNG | Entity is deactivated but retained for history |
| CLOSED | ĐÓNG | Entity is closed (final status, no further modifications) |
| System Dimension | Khối đoán hệ thống | Pre-loaded dimension, immutable without migration |
| Enterprise Dimension | Khối đoán doanh nghiệp | Defined by organization, modifiable by admins |
| Audit Checksum | Tổng kiểm tra SHA-256 | Chained hash ensuring audit integrity |
| Actor UUID | UUID người thực hiện | UUID identifying who performed the mutation (D11) |
| Reason | Lý do | Free-text reason for the mutation (mandatory per D11) |

---

## 12. References

- Law on Accounting 2015 (Luật Kế toán 2015), Chapter IX
- Circular 99/2025/TT-BTC (Người tiêu chuẩn mực 99/2025/BTC)
- Circular 133/2016/TT-BTC (Chi phí trung tâm và quy đổi chi phí)
- Circular 200/2014/TT-BTC (Kế toán phí và chi phí)
- Vietnamese Chart of Accounts TT 99/2025/TT-BTC (effective 01/01/2026)
- SME Accounting Application Codebase: src/bricks/cost_centers/domain.py
- Audit Log Module: src/bricks/audit_log/services.py
- RBAC: Flask-Login `@login_required` + `current_user.role` checks