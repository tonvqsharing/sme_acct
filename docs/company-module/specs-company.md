# Functional Specification: Company Module (Base Entity)

> Vietnamese SME Accounting System — Company Entity Technical Specifications v0.1.0

---

## 1. Position in Architecture (Lego Brick)

```
src/bricks/
  company/                 ← 🧱 NEW brick: company-module
    contract.py            ← 🔌 Public interface (only cross-brick touchpoint)
    domain.py              ← 🎯 Pure Python entities (no Flask/SQLAlchemy imports)
    services.py            ← ⚙️ Business orchestration
    storage.py             ← 💾 SQLAlchemy models + repository adapters
    web_adapter.py         ← 🌐 Flask blueprint + REST endpoints
  contact/                 ← existing brick (extend with company_id FK)
    ...
  invoice/                 ← existing brick (extend with company_id FK)
    ...
  voucher/                 ← existing brick (extend with company_id FK)
    ...
```

**Brick boundaries (enforced):**
- `domain.py` — pure Python; NO `flask`, NO `sqlalchemy`, NO `flask_login` imports
- `contract.py` — public interface; receives/returns only `str`, `int`, `float`, `dict`, `Decimal`, `UUID`
- `storage.py` — SQLAlchemy models + repo adapters (the ONLY file with SQLAlchemy imports)
- `services.py` — orchestration, validation, accepts injected port, no Flask/SQLAlchemy imports
- `web_adapter.py` — Flask blueprint + REST endpoints; `@login_required` + `current_user.role` checks (no Casbin)

**Critical positioning:** Company is the root aggregate. ALL other bricks MUST carry `company_id` (as `str` UUID passed via `contract.py`) once Company module is live. **No cross-brick SQLAlchemy joins** — communicate via primitive IDs only.

---

## 2. Domain Model

### 2.1 Company Entity (`src/bricks/company/domain.py`)

```python
@dataclass
class Company:
    """Doanh nghiệp / Đơn vị kế toán — root aggregate for all accounting data."""

    # ── Mandatory legal (from Luật Doanh nghiệp 2020 Art. 31) ──
    id: UUID                    # PK
    legal_name: str             # Full registered name from ĐKKD (Tên doanh nghiệp)
    mst: TaxId                  # Mã số thuế — validated format
    headquarters_address: str   # Địa chỉ trụ sở chính
    legal_representative: str   # Người đại diện pháp luật

    # ── Registration (from Luật Doanh nghiệp 2020 Art. 37) ──
    business_reg_number: str    # Số GCN ĐKKD
    business_reg_date: date     # Ngày cấp ĐKKD
    business_fields: list[str]  # Ngành nghề kinh doanh (NACE codes)

    # ── Classification (from Luật Doanh nghiệp 2020 Ch. II) ──
    company_type: CompanyType   # Enum: SINGLE_LLC, MULTI_LLC, JSC, SOLE_PROP, PARTNERSHIP, HDKD, COOP
    accounting_regime: AccountingRegime  # TT99, TT58_MICRO, TT133

    # ── Accounting (from Luật Kế toán 2015 Art. 13) ──
    fiscal_year_start_month: int       # 1-12; default 1
    fiscal_year_start_day: int         # 1-31; default 1
    responsible_accountant_name: str   # Kế toán trưởng (LKT 2015 Art. 16)
    responsible_accountant_license: str  # MSKHMN

    # ── Tax (from Luật Quản lý thuế 2019) ──
    tax_agency: str             # Cơ quan thuế quản lý trực tiếp
    controlling_tax_office: str # Cục/Chi cục Thuế

    # ── BHXH (from Luật BHXH 2024) ──
    bhxh_code: str              # Mã số BHXH đơn vị
    bhxh_agency: str            # Cơ quan BHXH quản lý

    # ── Operational ──
    authorized_capital: float   # Vốn điều lệ (VND)
    phone: str
    email: str
    website: str
    bank_accounts: list[BankAccount]
    short_name: str             # Tên giao dịch (on invoices)

    # ── Status ──
    status: CompanyStatus      # ACTIVE, SUSPENDED, DISSOLVED
    is_active: bool            # Soft-disabled flag

    # ── Audit ──
    created_at: date
    updated_at: date
    created_by: UUID
    updated_by: UUID
    config_version: int        # Optimistic lock
    legal_reviewed_at: Optional[date]
    legal_reviewed_by: Optional[UUID]
    mst_changed_at: Optional[date]  # For MST change audit trail
```

### 2.2 Supporting Value Objects

Add to `src/bricks/company/domain.py`:

```python
class CompanyType(Enum):
    """Loại hình doanh nghiệp per Luật Doanh nghiệp 2020 Art. 2."""
    SINGLE_LLC = "single_llc"              # Công ty TNHH 1 thành viên
    MULTI_LLC = "multi_llc"                # Công ty TNHH 2+ thành viên
    JSC = "jsc"                            # Công ty cổ phần
    LISTED_JSC = "listed_jsc"              # Công ty cổ phần niêm yết
    SOLE_PROP = "sole_prop"                # Doanh nghiệp tư nhân
    PARTNERSHIP = "partnership"            # Công ty hợp danh
    HOUSEHOLD = "household"                # Hộ kinh doanh (special — simplified accounting)
    COOP = "coop"                          # Hợp tác xã

class CompanyStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"    # Tạm ngừng hoạt động
    DISSOLVED = "dissolved"    # Giải thể

# AccountingRegime already partially defined in system-settings; consolidate:
class AccountingRegime(Enum):
    TT200 = "tt200"               # Thông tư 200/2014/TT-BTC (legacy enterprise)
    TT99 = "tt99"                 # Thông tư 99/2025/TT-BTC (current enterprise)
    TT58_MICRO = "tt58_micro"     # Thông tư 58/2026/TT-BTC (super-micro)
    TT133 = "tt133"               # Thông tư 133/2016/TT-BTC (SME alternative)

@dataclass
class BankAccount:
    bank_name: str
    account_number: str
    account_holder: str  # Usually same as company legal name
    branch: str
    is_primary: bool
```

### 2.3 Changes to Existing Entities (add `company_id`)

```python
# Partner entity (cross-brick reference via contract.py)
class Partner:
    company_id: UUID  # NEW — FK to Company; partners are per-entity

# Invoice entity (cross-brick reference via contract.py)
class Invoice:
    company_id: UUID  # NEW — issuing entity

# Voucher entity (cross-brick reference via contract.py)
class Voucher:
    company_id: UUID  # NEW — owning entity
```

---

## 3. Port Interface

```python
class CompanyRepositoryPort(ABC):
    @abstractmethod
    def create(self, company: Company) -> Company: ...

    @abstractmethod
    def get_by_id(self, company_id: UUID) -> Company | None: ...

    @abstractmethod
    def get_by_mst(self, mst: str) -> Company | None: ...

    @abstractmethod
    def list_active(self) -> list[Company]: ...

    @abstractmethod
    def update(self, company: Company, actor: UUID) -> Company: ...

    @abstractmethod
    def deactivate(self, company_id: UUID, actor: UUID) -> Company: ...

    @abstractmethod
    def list_subsidiaries(self, parent_id: UUID) -> list[Company]: ...
```

---

## 4. Service Contracts

### 4.1 CompanyService

| Method | Responsibility |
|--------|---------------|
| `create_company(**kwargs)` | Validate MST uniqueness, legal fields completeness, create entity + audit log |
| `get_company(company_id)` | Return company; enforce RBAC |
| `update_company(company_id, **changes, actor)` | Validate change is allowed (MST locked post-invoicing); emit audit log; increment config_version |
| `change_company_type(company_id, new_type, actor)` | Validate legal re-registration required; flag for COA migration |
| `deactivate_company(company_id, actor)` | Check no open periods, no pending invoices; set SUSPENDED |
| `dissolve_company(company_id, actor)` | Only CHIEF_ACCOUNTANT; check all periods closed, retention archived |
| `advance_legal_rep(company_id, new_rep, actor)` | Validate Mẫu 12 filed; emit MST_CHANGED if MST also changed |
| `get_company_config(company_id)` | Proxy to SystemSettingsService for company-scoped config |

### 4.2 TenantService

| Method | Responsibility |
|--------|---------------|
| `resolve_company(request)` | Extract company_id from JWT sub / header / subdomain via Flask request context |
| `check_access(user_id, company_id)` | Enforce user belongs to company (Flask built-in: `current_user.role` check) |
| `scope_query(query, company_id)` | Append `WHERE company_id = :cid` to all queries |

**Flask built-in RBAC:** `TenantService.check_access` uses `current_user.role` and `current_user.company_id` from Flask-Login session. No Casbin, no `pycasbin`, no policy CSV.

---

## 5. Database Schema

### 5.1 companies (root table)

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Legal mandatory
    legal_name VARCHAR(255) NOT NULL,
    mst VARCHAR(20) NOT NULL UNIQUE,  -- Tax ID; unique across system
    headquarters_address VARCHAR(500) NOT NULL DEFAULT '',
    legal_representative VARCHAR(255) NOT NULL DEFAULT '',
    business_reg_number VARCHAR(100),       -- Số GCN ĐKKD
    business_reg_date DATE,
    business_fields JSON DEFAULT '[]',       -- Ngành nghề ĐKKD codes

    -- Classification
    company_type VARCHAR(30) NOT NULL DEFAULT 'multi_llc',
    accounting_regime VARCHAR(30) NOT NULL DEFAULT 'tt99',
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Accounting
    fiscal_year_start_month INT NOT NULL DEFAULT 1 CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
    fiscal_year_start_day INT NOT NULL DEFAULT 1 CHECK (fiscal_year_start_day BETWEEN 1 AND 31),
    responsible_accountant_name VARCHAR(255) NOT NULL DEFAULT '',
    responsible_accountant_license VARCHAR(100),  -- MSKHMN

    -- Tax / BHXH
    tax_agency VARCHAR(300) NOT NULL DEFAULT '',
    controlling_tax_office VARCHAR(300) NOT NULL DEFAULT '',
    bhxh_code VARCHAR(50),
    bhxh_agency VARCHAR(300),

    -- Operational
    authorized_capital NUMERIC(18, 2) DEFAULT 0,
    phone VARCHAR(30) NOT NULL DEFAULT '',
    email VARCHAR(120) NOT NULL DEFAULT '',
    website VARCHAR(255) NOT NULL DEFAULT '',
    short_name VARCHAR(100),  -- Trading name on invoices
    bank_accounts JSON DEFAULT '[]',

    -- Audit
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    updated_at DATE NOT NULL DEFAULT CURRENT_DATE,
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    config_version INT NOT NULL DEFAULT 1,
    legal_reviewed_at DATE,
    legal_reviewed_by UUID,
    mst_changed_at DATE  -- MST change effective date

    -- Constraints
    CONSTRAINT uq_companies_mst UNIQUE (mst)
);

CREATE INDEX idx_companies_mst ON companies(mst);
CREATE INDEX idx_companies_status ON companies(status, is_active);
```

### 5.2 Alter existing tables (add `company_id`)

```sql
-- Add nullable company_id to existing tables (backfill-compatible)
ALTER TABLE partners ADD COLUMN company_id UUID;
ALTER TABLE invoices ADD COLUMN company_id UUID;
ALTER TABLE vouchers ADD COLUMN company_id UUID;

-- After data migration: add FK + NOT NULL
ALTER TABLE partners ADD CONSTRAINT fk_partners_company FOREIGN KEY (company_id) REFERENCES companies(id);
ALTER TABLE invoices ADD CONSTRAINT fk_invoices_company FOREIGN KEY (company_id) REFERENCES companies(id);
ALTER TABLE vouchers ADD CONSTRAINT fk_vouchers_company FOREIGN KEY (company_id) REFERENCES companies(id);
```

---

## 6. Validation Rules

### 6.1 At Domain Boundary (Construction Time)

| Field | Rule | Error |
|-------|------|-------|
| `legal_name` | Required; non-empty; max 255 chars | `CompanyValidationError("Tên doanh nghiệp là bắt buộc")` |
| `mst` | `TaxId` value object enforced: `^\d{10}$` or `^\d{10}-\d{3}$` | ValueError from TaxId |
| `mst` | UNIQUE across companies | `DuplicateMSTError("MST đã tồn tại trong hệ thống")` |
| `headquarters_address` | Required; min 5 chars | `CompanyValidationError` |
| `legal_representative` | Required | same |
| `business_reg_number` | Required for LLC/JSC | same |
| `company_type` | Must be valid enum | `InvalidCompanyTypeError` |
| `accounting_regime` | Must match company_type capabilities | `InvalidRegimeError` |
| `fiscal_year_start_month` | 1-12 | same |
| `fiscal_year_start_day` | 1-31 + valid for month | same |
| `bhxh_code` | Required if company_type != HOUSEHOLD | same |
| `responsible_accountant_license` | Required for enterprise types | same |

### 6.2 At Service Layer

| Rule | Enforcement |
|------|------------|
| MST cannot be changed after any invoice posted | CompanyService checks Invoice.count where company_id=X AND issue_date > mst_changed_at — reject if >0 |
| Company type change re-registration check | If company_type changes, system requires external filing confirmation before COA migration |
| Company SUSPENDED → no new invoices | InvoiceService checks Company.status before CREATE |
| Company DISSOLVED → read-only | All write operations rejected |
| Fiscal year cannot be changed retroactively | PeriodLockService checks against fiscal_year_start for existing locked periods |
| Company deactivate only if all periods closed | PeriodLockService + InvoiceService checks |

---

## 7. API Specification

### 7.1 Endpoints

| Method | Path | Auth | Role Check | Description |
|--------|------|------|------------|-------------|
| `POST` | `/api/v1/companies` | `@login_required` | `current_user.role == "ADMIN"` | Create company (one-time setup) |
| `GET` | `/api/v1/companies` | `@login_required` | any auth role | List companies user can access |
| `GET` | `/api/v1/companies/{id}` | `@login_required` | any auth role | Company detail |
| `PATCH` | `/api/v1/companies/{id}` | `@login_required` | `current_user.role in ("ADMIN", "ACCOUNTANT")` | Update company (restricted fields only) |
| `POST` | `/api/v1/companies/{id}/suspend` | `@login_required` | `current_user.role == "CHIEF_ACCOUNTANT"` | Suspend operations |
| `POST` | `/api/v1/companies/{id}/reactivate` | `@login_required` | `current_user.role == "ADMIN"` | Reactivate from suspended |
| `POST` | `/api/v1/companies/{id}/change-mst` | `@login_required` | `current_user.role in ("ADMIN", "LEGAL_REVIEW")` | MST change (requires re-registration proof) |
| `POST` | `/api/v1/companies/{id}/legal-review` | `@login_required` | `current_user.role == "CHIEF_ACCOUNTANT"` | Stamp legal review |
| `GET` | `/api/v1/companies/{id}/audit-log` | `@login_required` | `current_user.role in ("ACCOUNTANT", "AUDITOR")` | Company change history |

**RBAC pattern (Flask built-in):**
```python
from flask_login import login_required, current_user
from flask import abort

@web_adapter_bp.post("/api/v1/companies")
@login_required
def create_company():
    if current_user.role != "ADMIN":
        abort(403, description="RBAC denied: ADMIN role required")
    # ... proceed
```

### 7.2 Request/Response Schemas

**POST /api/v1/companies (Create)**
```json
{
  "legal_name": "Công ty TNHH ABC",
  "mst": "0123456789",
  "headquarters_address": "123 Nguyễn Văn Linh, Q.7, TP.HCM",
  "legal_representative": "Nguyễn Văn A",
  "company_type": "multi_llc",
  "accounting_regime": "tt99",
  "business_reg_number": "0312345678",
  "business_reg_date": "2020-01-15",
  "business_fields": ["6202", "4791"],
  "fiscal_year_start_month": 1,
  "fiscal_year_start_day": 1,
  "responsible_accountant_name": "Trần Thị B",
  "responsible_accountant_license": "KHMN-01234",
  "tax_agency": "Chi cục Thuế Quận 7",
  "bhxh_code": "0070123456",
  "authorized_capital": 1000000000,
  "phone": "0281234567",
  "email": "info@abc.com",
  "website": "https://abc.com",
  "short_name": "ABC Co."
}
```

**GET /api/v1/companies/{id}**
```json
{
  "id": "uuid",
  "legal_name": "Công ty TNHH ABC",
  "mst": "0123456789",
  "company_type": { "id": "multi_llc", "label": "Công ty TNHH 2 thành viên" },
  "accounting_regime": { "id": "tt99", "label": "Thông tư 99/2025/TT-BTC" },
  "fiscal_year_start": { "month": 1, "day": 1 },
  "status": "active",
  "bhxh_code": "0070123456",
  "responsible_accountant": "Trần Thị B (KHMN-01234)",
  "audit_trail_url": "/api/v1/companies/{id}/audit-log"
}
```

### 7.3 Error Responses

| HTTP | Code | Condition |
|------|------|-----------|
| 409 | `MST_TAKEN` | MST already registered |
| 422 | `INVALID_MST` | MST format invalid |
| 422 | `INVALID_COMPANY_TYPE` | Company type not in enum |
| 422 | `COMPANY_SUSPENDED` | Cannot create transactions for suspended company |
| 403 | `COMPANY_NOT_AUTHORIZED` | User has no access to company |
| 409 | `COMPANY_HAS_OPEN_PERIODS` | Cannot deactivate with open periods |
| 409 | `MST_CHANGE_BLOCKED` | Cannot change MST after invoices posted |

---

## 8. Migration Plan

Database: **SQLite3** (default). `SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db` for local dev. Override via env if using MySQL/PostgreSQL later.

### Phase 1 — Brick Domain + Storage + Tests
- Create `Company` entity in `src/bricks/company/domain.py` (pure Python, no Flask/SQLAlchemy)
- Add `CompanyModel` to `src/bricks/company/storage.py` (SQLAlchemy adapter only)
- Add `company_id` columns (nullable) to `partners`, `invoices`, `vouchers` in respective brick `storage.py`
- Create `companies` table
- Write domain unit tests (mock `contract.py` of cross-brick targets)

### Phase 2 — Brick Service + Validation
- `CompanyService` in `src/bricks/company/services.py` with all business rules (pure Python)
- `TenantService` for request-scoped resolution (Flask context only in `web_adapter.py`)
- MST uniqueness enforcement
- Company status lifecycle

### Phase 3 — Brick Web Adapter + Integration
- Flask blueprint in `src/bricks/company/web_adapter.py`
- `@login_required` + `current_user.role` checks on all routes
- Update `InvoiceService`, `VoucherService`, `PartnerService` to require `company_id` (via `contract.py` primitive)
- Update all repositories to scope by `company_id`

### Phase 4 — Audit + Backfill
- Audit log for company changes (in audit-log brick)
- Data migration script to backfill `company_id` on existing records
- Integration tests for tenant isolation (mock cross-brick contracts)

### Phase 5 — UI
- Company setup wizard
- Company profile page
- Change notification form (Mẫu 12 simulation)

### Migration Commands (SQLite3 default)
```bash
# Local dev
SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db flask db init
SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db flask db migrate -m "company_init"
SQLALCHEMY_DATABASE_URI=sqlite:///./dev.db flask db upgrade
```

---

## 9. Open Questions

| Q | Owner | Needed By |
|---|-------|-----------|
| Will v1 be single-company only, or allow multi-company from launch? | Product | Before Phase 3 API design |
| Should company_id be derived from auth user's default company, or from subdomain/header? | Infra | Before Phase 3 |
| How to handle migration for existing invoice/voucher/partner data (no company_id)? | Dev team | Before Phase 3 |
| Should branches (Chi nhánh) be separate Company records or child entities? | Legal | Before Phase 1 entity design |
| What happens to historical data when MST changes? | Legal | Before Phase 2 |
| Which role can approve company creation? | CA | Before Phase 1 |