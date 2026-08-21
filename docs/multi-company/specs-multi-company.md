# Specifications — Multi-Company / Master-Module
> Vietnamese SME Accounting Platform — Multi-Tenant Master-Module Technical Specifications
> Version: 0.1.0 | Status: DRAFT | Derives from: docs/brd-multi-company.md

---

## 1. Scope Alignment

This spec covers FR-MC-01 through FR-MC-16 from the BRD. Out-of-scope items remain per BRD Section 3.2.

---

## 2. Domain Model

### 2.1 New Domain Entities

**`Company`** (`src/bricks/company/domain.py`)
- Fields: id (UUID), name (str), legal_name (str), mst (TaxId), tax_agency (str), accounting_regime (AccountingRegime), fiscal_year_start (date, default=01-01), parent_company_id (UUID | None), consolidation_method (ConsolidationMethod), status (CompanyStatus), is_active (bool), created_at (date), updated_at (date)
- Rule: MST validated at construction; cannot change once invoices posted against it
- Method: `deactivate()` — sets is_active=False; only if no open periods
- Method: `get_display_name()` — returns `legal_name` or `name` if no legal_name

**`ConsolidationGroup`** (new)
- Fields: id, name, description, master_company_id, companies: list[Company]
- Method: `add_company(company)`, `remove_company(company_id)`, `all_active_sub_companies()`

**`ConsolidationRun`** (new)
- Fields: id, group_id, period_start, period_end, status (DRAFT/POSTED/LOCKED), created_by, approved_by, created_at
- Method: `add_adjusting_entry(entry)`, `calculate_eliminations()`, `approve()` → POSTED

### 2.2 Modifications to Existing Entities

**`Invoice`** — add field:
- `company_id: UUID | None` — FK to Company; set at creation; immutable once issued

**`Voucher`** — add field:
- `company_id: UUID | None` — FK to Company

**`Partner`** — add field:
- `company_id: UUID | None` — FK to Company; partners are per-entity

**`VoucherLine`** — no change to fields; container filters by voucher.company_id

### 2.3 Value Objects (new)

**`AccountingRegime`** (`src/domain/value_objects/`)
- `MICRO` — Thông tư 58/2026/TT-BTC (hộ kinh doanh, micro enterprise)
- `SME` — Thông tư 99/2025/TT-BTC (SME regime)
- `ENTERPRISE` — Thông tư 99/2025/TT-BTC (enterprise regime)

**`ConsolidationMethod`** — FULL / PROPORTIONAL (v2)

**`FiscalYear`** — year (int), start_date (date), end_date (date), is_closed (bool)

---

## 3. Service Layer

### 3.1 New Ports (`src/application/ports/`)

```python
class CompanyRepository(ABC):
    @abstractmethod
    def get_by_id(self, company_id: UUID) -> Company | None: ...
    @abstractmethod
    def get_by_mst(self, mst: str) -> Company | None: ...
    @abstractmethod
    def list_active(self, parent_id: UUID | None = None) -> list[Company]: ...
    @abstractmethod
    def list_subsidiaries(self, parent_id: UUID) -> list[Company]: ...
    @abstractmethod
    def create(self, company: Company) -> Company: ...

class ConsolidationGroupRepository(ABC):
    @abstractmethod
    def create_group(self, name: str, master_company_id: UUID) -> ConsolidationGroup: ...
    @abstractmethod
    def add_company(self, group_id: UUID, company_id: UUID) -> None: ...

class ConsolidationRunRepository(ABC):
    @abstractmethod
    def create_run(self, run: ConsolidationRun) -> ConsolidationRun: ...
    @abstractmethod
    def get_by_id(self, run_id: UUID) -> ConsolidationRun | None: ...
```

### 3.2 New Services (`src/bricks/multi_company/services.py`)

**`CompanyService`**
- `create_subsidiary(parent_id, **kwargs)` — validates MST, creates Company with parent link
- `update_company(company_id, **kwargs)` — restricted fields (name only; MST locked after postings)
- `deactivate_company(company_id)` — checks no open periods, sets inactive

**`ConsolidationService`**
- `initiate_consolidation(group_id, period)` — creates ConsolidationRun
- `add_adjusting_entry(run_id, entry)` — master-only adjusting entry
- `calculate_trial_balance(group_id, as_of_date)` — pulls from all subsidiaries
- `run_elimination(run_id)` — computes NST/NLD eliminations based on intercompany flags
- `approve_consolidation(run_id, approved_by)` — locks run; posts consolidated BCTC

---

## 4. Database Schema

### 4.1 New Tables

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    mst VARCHAR(20) NOT NULL UNIQUE,
    tax_agency VARCHAR(300) NOT NULL DEFAULT '',
    accounting_regime VARCHAR(30) NOT NULL DEFAULT 'sme',
    fiscal_year_start DATE NOT NULL DEFAULT '2025-01-01',
    parent_company_id UUID,
    consolidation_method VARCHAR(30) NOT NULL DEFAULT 'full',
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    updated_at DATE NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (parent_company_id) REFERENCES companies(id)
);

CREATE TABLE consolidation_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1000) DEFAULT '',
    master_company_id UUID NOT NULL REFERENCES companies(id),
    created_at DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE consolidation_group_companies (
    group_id UUID REFERENCES consolidation_groups(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, company_id)
);

CREATE TABLE consolidation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES consolidation_groups(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    created_by UUID,
    approved_by UUID,
    approved_at TIMESTAMP,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE consolidation_adjusting_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES consolidation_runs(id) ON DELETE CASCADE,
    description VARCHAR(500) NOT NULL,
    debit_account VARCHAR(10) NOT NULL,
    credit_account VARCHAR(10) NOT NULL,
    debit_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    credit_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    created_by UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 4.2 Schema Migration Strategy

1. Add `company_id` nullable to `partners`, `invoices`, `vouchers` (backfill with default company later)
2. Populate `companies` table from existing data or manual import
3. Backfill `company_id` via data migration script
4. Add `NOT NULL` + FK constraint in follow-up migration
5. Alembic auto-generate from SQLAlchemy models

---

## 5. API Layer (`src/presentation/api/`)

### 5.1 Company Endpoints

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/api/companies` | GROUP_CFO, MASTER_ADMIN | Create subsidiary |
| GET | `/api/companies` | Auth | List companies user has access to |
| GET | `/api/companies/<id>` | Auth | Get company detail |
| PATCH | `/api/companies/<id>` | GROUP_CFO | Update company (restricted fields) |
| DELETE | `/api/companies/<id>` | MASTER_ADMIN only | Deactivate company |

### 5.2 Consolidation Endpoints

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/api/consolidation/groups` | GROUP_CFO | Create consolidation group |
| POST | `/api/consolidation/groups/<id>/companies` | GROUP_CFO | Add company to group |
| POST | `/api/consolidation/runs` | GROUP_CFO | Initiate consolidation run |
| POST | `/api/consolidation/runs/<id>/entries` | GROUP_CFO | Add adjusting entry |
| POST | `/api/consolidation/runs/<id>/approve` | GROUP_CFO | Approve and lock |
| GET | `/api/consolidation/runs/<id>/balance` | Auth | Trial balance |

### 5.3 HTMX Endpoints (UI)

| Path | Method | Description |
|---|---|---|
| `/companies/` | GET | Company list partial |
| `/companies/new` | GET | New company form partial |
| `/companies/new` | POST | Create company → redirect |
| `/consolidation/run/<id>` | GET | Consolidation result partial |

---

## 6. Use Cases

See `docs/use-cases-multi-company.md` for full UC-0001..UC-0012 with happy/alternative/exception paths.

---

## 7. Workflows

See `docs/workflows-multi-company.md`.

---

## 8. Data Flows

See `docs/data-flow-multi-company.md`.

---

## 9. Compliance Mapping

### 9.1 Per BRD FR-MC → Legal Basis

| FR | Circular/Law | Table/Field | BCTC Template |
|---|---|---|---|
| FR-MC-01 MST validation | Luật Quản lý thuế 2019 | MST field | — |
| FR-MC-03 Company deactivate | Luật Kế toán 2015 Art. 28 | Lock periods | — |
| FR-MC-04 Role scoping | Internal RBAC | — | — |
| FR-MC-05 COA per entity | Circular 99/2025/TT-BTC | Mẫu 01/BCTC | Per regime |
| FR-MC-06 Fiscal year per entity | Circular 99/2025/TT-BTC | Period closing | — |
| FR-MC-07 Invoice MVC per entity | NĐ 123/2024/NĐ-CP | MST on invoice | — |
| FR-MC-10 Adjusting entries | Circular 200/2014 / 99/2025 | NST/NLD elim | BCTC Notes |
| FR-MC-11 Consolidated BCTC | Luật Doanh nghiệp 2020 Art. 220 | Full BCTC | BCTC hợp nhất |
| FR-MC-13 Audit trail | Luật Kế toán 2015 | Immutable log | Audit file |

---

## 10. Exception Handling Matrix

| Error | Cause | HTTP | Recovery |
|---|---|---|---|
| MST_TAKEN | Duplicate MST | 409 | Choose different MST or activate deactivated company |
| COMPANY_HAS_OPEN_PERIODS | Cannot deactivate | 422 | Close all periods first |
| PERIOD_NOT_LOCKED_ALL | Consolidation run fails | 422 | Lock all subsidiary periods |
| ELIMINATION_IMBALANCE | NST/NLD mismatch | 422 | Review adjusting entries |
| NO_CONSOLIDATION_GROUP | Group missing | 404 | Create group first |

---

## 11. Risk & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Legal source unverified (gdt/vbpl blocked) | High | High | Manual verification by compliance team before launch |
| Existing data lacks company_id | Medium | Medium | Data migration script with dry-run + count validation |
| Cross-entity data leak during refactor | Medium | Critical | Integration tests for tenant isolation before any DB change |
| Circular 99/2025 template mismatch | High | High | CFO review of BCTC output vs. Mẫu 01-06 before v1 sign-off |
| Tryton benchmark: 18yr-old codebase | Low | Low | Our design is fresh; use Tryton patterns only as reference |

---

## 12. Definition of Done (v1)

- [ ] `Company` entity + tests pass
- [ ] `company_id` on invoices/vouchers/partners + migrations run
- [ ] Role-based access restricts bookkeeper to 1 company
- [ ] Subsidiary onboarding flow (5 user actions) works end-to-end
- [ ] Period-lock per entity works
- [ ] Consolidation run produces BCTC hợp nhất matching Circular 99 Mẫu BCTC
- [ ] All 14 functional requirements from BRD satisfaction
- [ ] Legal review of BRD compliance checklist complete
- [ ] Audit log append-only verified

--- END OF FILE ---
