# Execution Plan — Tools & Equipment (CCDC) Module

**Date:** 2026-08-27  
**Status:** Ready for implementation  
**Estimated effort:** 3–5 days (TDD + five-axis review)

---

## Phase 1: Domain Layer (Day 1)

### 1.1 Entity Model
**File:** `src/bricks/tools_equipment/domain.py`

```python
# Entities:
# - ToolEquipment (main CCDC entity)
# - ToolEquipmentAllocation (monthly allocation record)

# Value Objects:
# - CCDCCategory (enum: OFFICE_EQUIP, TOOLS, CONTAINERS, RENTAL, SPARE_PARTS)
# - ToolEquipmentStatus (enum: ACTIVE, INACTIVE, WRITTEN_OFF)

# Domain Events:
# - ToolEquipmentCreated
# - ToolEquipmentAllocated
# - ToolEquipmentWrittenOff
```

**Acceptance criteria:**
- [ ] Domain entities are pure Python (no Flask/SQLAlchemy imports)
- [ ] Regex `^[A-Z0-9-]{2,50}$` for code validation
- [ ] Status state machine: ACTIVE → INACTIVE → WRITTEN_OFF
- [ ] Audit checksum computation (pipe-delimited format)

### 1.2 Port Interfaces
**File:** `src/bricks/tools_equipment/contract.py`

```python
# Ports:
# - ToolEquipmentRepositoryPort (CRUD + query)
# - ToolEquipmentAllocationRepositoryPort (CRUD + query)
# - FiscalPeriodServicePort (verify open period)
# - COAServicePort (validate posting accounts)
```

**Acceptance criteria:**
- [ ] Ports use primitives only (str, int, Decimal, UUID, date)
- [ ] No cross-brick imports
- [ ] Methods match spec API endpoints

---

## Phase 2: Storage Layer (Day 1–2)

### 2.1 SQLAlchemy Models
**File:** `src/bricks/tools_equipment/storage.py`

```python
# Tables:
# - tool_equipment (17 columns + 4 audit columns)
# - tool_equipment_allocation (12 columns + 4 audit columns)
```

**Acceptance criteria:**
- [ ] `sa.ForeignKey("tool_equipment.id")` on allocation
- [ ] `sa.ForeignKey("accounts.code")` on expense_account_code
- [ ] `sa.ForeignKey("accounts.code")` on prepaid_account_code
- [ ] `sa.ForeignKey("cost_centers.id")` on cost_center_id (nullable)
- [ ] `sa.ForeignKey("dimension_values.id")` on dimension_value_id (nullable)
- [ ] `UniqueConstraint("code", "company_id", name="uq_tool_equipment_code_company")`
- [ ] All `Mapped[...]` type args imported at module level

### 2.2 Repository Adapters
**File:** `src/bricks/tools_equipment/storage.py`

```python
# Repositories:
# - ToolEquipmentRepo (implements ToolEquipmentRepositoryPort)
# - ToolEquipmentAllocationRepo (implements ToolEquipmentAllocationRepositoryPort)
```

**Acceptance criteria:**
- [ ] `create()`, `get_by_id()`, `update()`, `delete()`, `list_by_company()`
- [ ] `list_active_by_company()` for allocation engine
- [ ] `find_by_code_and_company()` for duplicate guard

---

## Phase 3: Service Layer (Day 2–3)

### 3.1 ToolEquipmentService
**File:** `src/bricks/tools_equipment/services.py`

```python
# Methods:
# - create(data: ToolEquipmentCreate) → ToolEquipment
# - update(id: UUID, data: ToolEquipmentUpdate) → ToolEquipment
# - deactivate(id: UUID) → ToolEquipment
# - reactivate(id: UUID) → ToolEquipment
# - write_off(id: UUID, reason: WriteOffReason) → ToolEquipment
# - list_by_company(company_id: UUID) → list[ToolEquipment]
```

**Business rules:**
- [ ] BR-001: Code unique per company
- [ ] BR-002: Allocation period 1–36 months
- [ ] BR-003: Category in allowed set
- [ ] BR-004: Price > 0
- [ ] BR-005: Deactivate requires ACTIVE status
- [ ] BR-006: Reactivate requires INACTIVE status
- [ ] BR-007: Write-off requires CHIEF_ACCOUNTANT role
- [ ] BR-008: Write-off requires non-zero remaining value
- [ ] BR-009: Create set created_by = current_user.id
- [ ] BR-010: Deactivate set deactivated_by = current_user.id
- [ ] BR-011: Update set updated_by = current_user.id

### 3.2 Allocation Engine
**File:** `src/bricks/tools_equipment/services.py`

```python
# Methods:
# - calculate_allocations(year: int, month: int) → list[AllocationResult]
# - post_allocations(year: int, month: int) → list[Allocation]
```

**Business rules:**
- [ ] BR-012: Allocation = original_price / useful_life_months
- [ ] BR-013: Allocation only for ACTIVE status
- [ ] BR-014: Allocation only in open fiscal periods
- [ ] BR-015: Amount rounded to VND (no decimal)
- [ ] BR-016: Maximum 36-month allocation period

---

## Phase 4: Integration (Day 3–4)

### 4.1 App.py Wiring
**File:** `src/app.py`

```python
# Order:
# 1. COA service (already exists)
# 2. FY service (already exists)
# 3. Cost Centers service (already exists)
# 4. Dimensions service (already exists)
# 5. Tools Equipment service (NEW - depends on COA, FY, CC, Dimensions)
```

**Acceptance criteria:**
- [ ] `_ToolEquipmentServiceAdapter` translates brick contracts
- [ ] Blueprint registered with `url_prefix="/api/v1/tools-equipment"`
- [ ] All dependencies injected via constructor

### 4.2 Alembic Migration
**File:** `alembic/versions/xxxx_add_tool_equipment.py`

```python
# Tables created:
# - tool_equipment
# - tool_equipment_allocation
```

**Acceptance criteria:**
- [ ] No `src.bricks.*.*Type()` references (use `sa.Text()` etc.)
- [ ] Foreign keys match parent tables
- [ ] Unique constraints match domain rules

---

## Phase 5: Web Adapter (Day 4)

### 5.1 Flask Blueprint
**File:** `src/bricks/tools_equipment/web_adapter.py`

```python
# Endpoints:
# POST   /api/v1/tools-equipment          — create CCDC
# GET    /api/v1/tools-equipment          — list CCDC
# GET    /api/v1/tools-equipment/<id>     — get CCDC detail
# PUT    /api/v1/tools-equipment/<id>     — update CCDC
# DELETE /api/v1/tools-equipment/<id>     — deactivate CCDC
# POST   /api/v1/tools-equipment/<id>/reactivate — reactivate
# POST   /api/v1/tools-equipment/<id>/write-off  — write off (CHIEF_ACCOUNTANT)
# POST   /api/v1/tools-equipment/allocate — run monthly allocation
```

**Acceptance criteria:**
- [ ] `@login_required` on every route
- [ ] Role checks: ADMIN, ACCOUNTANT can create/update
- [ ] Role checks: CHIEF_ACCOUNTANT for write-off
- [ ] Response includes `created_by`, `created_at`, `updated_at`
- [ ] Error responses follow RFC 7807 Problem Details

---

## Phase 6: Testing (Day 4–5)

### 6.1 Unit Tests
**File:** `tests/unit/tools_equipment/test_tool_equipment_service.py`

```python
# Tests:
# - create with valid data → success
# - create with duplicate code → EX-001
# - create with invalid price → EX-002
# - create with invalid useful_life → EX-003
# - create with invalid category → EX-004
# - deactivate ACTIVE → INACTIVE
# - deactivate INACTIVE → error
# - reactivate INACTIVE → ACTIVE
# - reactivate ACTIVE → error
# - write_off with CHIEF_ACCOUNTANT → success
# - write_off with ACCOUNTANT → forbidden
# - allocate with open period → journal entries
# - allocate with closed period → error
# - allocate only ACTIVE status
```

### 6.2 Integration Tests
**File:** `tests/integration/test_tools_equipment_api.py`

```python
# Tests:
# - POST /tools-equipment → 201
# - GET /tools-equipment → 200
# - GET /tools-equipment/<id> → 200
# - PUT /tools-equipment/<id> → 200
# - DELETE /tools-equipment/<id> → 204
# - POST /tools-equipment/<id>/reactivate → 200
# - POST /tools-equipment/<id>/write-off → 200 (CHIEF_ACCOUNTANT)
# - POST /tools-equipment/allocate → 200
# - Unauthorized → 401
# - Forbidden → 403
```

---

## Quality Gates (Before EVERY Commit)

```
1. uv run ruff check src tests           — lint
2. uv run black --check src tests        — format
3. uv run mypy --ignore-missing-imports src/bricks/tools_equipment/  — typecheck
4. uv run pytest tests/unit/tools_equipment/ -v  — unit tests
5. uv run pytest tests/integration/test_tools_equipment_api.py -v  — integration tests
```

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| COA brick | ✅ done | Required for expense/prepaid accounts |
| Fiscal Year brick | ✅ done | Required for open period check |
| Cost Centers brick | ✅ done | Optional FK on cost_center_id |
| Dimensions brick | ✅ done | Optional FK on dimension_value_id |
| Purchases brick | ✅ done | Future: auto-create CCDC from purchase invoices |
| Voucher brick | ✅ done | Required for journal entry creation |

---

## Test Count Target

**Current:** 622 tests  
**Target after CCDC:** ~680 tests (58 new tests)

| Test Type | Count |
|-----------|-------|
| Unit: ToolEquipmentService | 15 |
| Unit: AllocationEngine | 10 |
| Unit: Domain entities | 8 |
| Integration: API endpoints | 20 |
| Integration: Workflow | 5 |
| **Total** | **58** |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| TK 153 not in COA | High | Verify during integration test |
| Fiscal period not open | Medium | Check FY service before allocation |
| Concurrent allocation | Low | Use database transactions |
| Audit checksum integrity | Medium | Use pipe-delimited format with timestamp |

---

## Post-Implementation

1. **Update AGENTS.md** — add CCDC to module status, increment test count
2. **Git commit** — conventional commit: `feat(tools-equipment): implement CCDC brick`
3. **Codegraph sync** — `codegraph sync`
4. **Codebase memory index** — update knowledge graph
5. **Git push** — requires remote configuration first

---

## Blockers

| Blocker | Status | Resolution |
|---------|--------|------------|
| No git remote | Open | `git remote add origin <url>` |
| XML ingest v2 | Blocked | Waiting for TT91 annex field-mapping |
| NHNN FX auto-sync | Blocked | Spec says v1.5 |
