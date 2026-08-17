# Functional Specification: System Settings / Global Flags Module

| Field | Value |
|-------|-------|
| Version | 0.1.0 |
| Status | DRAFT |
| Audience | Engineering + QA + Audit |

---

## 1. Glossary

| Term | Definition |
|------|-----------|
| **CompanyConfig** | Domain aggregate holding all system-level settings for a single company. Exactly one per company. |
| **GlobalFlag** | Individual setting within CompanyConfig. Two types: `LAW` (immutable legal constant) and `CONFIG` (admin-changeable with audit). |
| **Legal Constant** | System-enforced value derived from Vietnamese law. Cannot be overridden without patch. |
| **Period Lock** | Hard enforcement that prevents posting in a closed fiscal/accounting period. |
| **Retention Policy** | Legal requirement that certain document types cannot be deleted for N years. |
| **Tax ID (MST)** | Mã số thuế — Vietnamese tax identification number (10 digits or XXXXXXXXXX-XXX). |
| **Account Code (TK)** | Chart of accounts code per Thông tư 200/2014/TT-BTC (3 or 4 digits, 111-8999). |
| **E-Invoice** | Hóa đơn điện tử — legally required invoice format per NĐ 123/2020. |
| **CA** | Certificate Authority — PKI provider approved by GDT for e-invoice signing. |
| **Audit Log** | WORM append-only system event log. ≥10 years retention. |
| **SoD** | Segregation of Duties — CREATOR ≠ APPROVER ≠ POSTER enforced at backend. |

---

## 2. Architecture Position

```
src/
  domain/
    entities/
      company_config.py          ← NEW: CompanyConfig aggregate
      base.py                    ← EXTEND: add SystemFlag enum, AccountingRegime enum
    exceptions/
      system_settings.py         ← NEW: SystemSettingsError, FlagLockedError, ConfigVersionConflict
    repositories/
      system_settings_repo.py    ← NEW: port (interface)
  application/
    services/
      system_settings_service.py ← NEW: orchestration, validation, change management
      period_lock_service.py     ← NEW: period boundary checks
      audit_log_service.py       ← NEW: audit event publication
  infrastructure/
    database/
      models.py                  ← EXTEND: CompanyConfigModel, SystemFlagModel, AuditLogModel, PeriodLockModel
    repositories/
      sqlalchemy_system_settings.py ← NEW: adapter
  presentation/
    api/
      system_settings.py         ← NEW: REST endpoints
    ui/
      system_settings/           ← NEW: HTML pages (if applicable)
```

---

## 3. Domain Model Specification

### 3.1 CompanyConfig Entity

```python
@dataclass
class CompanyConfig:
    company_id: UUID  # FK to Company (or root if no Company entity yet)

    # ── Legal constants (LAW type — cannot be changed without migration) ──
    accounting_period_type: AccountingPeriodType   # CALENDAR | FISCAL_15 | FISCAL_APR
    accounting_regime: AccountingRegime           # TT200 | TT99 | TT58_MICRO | TT133
    chart_of_accounts_type: ChartOfAccountsType   # COA_200 | COA_99 | COA_ENTERPRISE
    tax_id_pattern: str                           # r"^\d{10}(-\d{3})?$" (hardcoded; mirror for override clarity)
    account_code_pattern: str                     # r"^[1-9]\d{2}$|^[1-9]\d{3}$" (hardcoded)
    vat_rates: frozenset[int]                     # {0, 5, 10} ← system managed
    minimum_retention_years: int                  # ≥10; ties to company type
    data_deletable: bool                          # False after fiscal year close

    # ── Config flags (CONFIG type — changeable with admin role + audit log) ──
    fiscal_year_start_month: int                  # 1-12; default 1 (Jan)
    fiscal_year_start_day: int                    # 1-31; default 1
    vat_settlement_cycle: SettlementCycle         # MONTHLY | QUARTERLY
    vat_method: VATMethod                         # DEDUCTION | OUTPUT_ONLY
    e_invoice_mode: EInvoiceMode                  # SOFTWARE_CERT | CA_SIGNED
    ca_list: frozenset[str]                       # List of GDT-approved CA identifiers
    e_invoice_series: list[EInvoiceSeries]        # Max 15 active; each has prefix, next_seq
    decimal_places: int                           # 0 | 2
    default_currency: str                         # "VND" default
    cost_center_required: bool                    # False default
    multi_level_cost_centers: bool                # False default
    default_cost_formula: str                     # "FIFO" (TT200 standard)
    data_retention_years: int                     # ≥10 per decree

    # ── Audit-only metadata (never user-editable) ──
    created_at: datetime
    created_by: UUID
    updated_at: datetime
    updated_by: UUID
    config_version: int                           # optimistic-lock; increments per change
    legal_reviewed_at: datetime | None            # When chief accountant approved
    legal_reviewed_by: UUID | None
```

### 3.2 Supporting Enums

Add to `src/domain/entities/base.py`:

```python
class AccountingPeriodType(Enum):
    CALENDAR = "calendar"         # Jan 1 – Dec 31
    FISCAL_APR = "fiscal_apr"     # Apr 1 – Mar 31 (common for legacy enterprises)
    FISCAL_15 = "fiscal_15"       # Jul 15 – Jul 14 (rare; must be declared)

class AccountingRegime(Enum):
    TT200 = "tt200"               # Thông tư 200/2014/TT-BTC (enterprise, current standard)
    TT99_NEW = "tt99"             # Thông tư 99/2025/TT-BTC (new, effective 2026)
    TT58_MICRO = "tt58_micro"     # Thông tư 58/2026/TT-BTC (micro-enterprise)
    TT133 = "tt133"               # Thông tư 133/2016/TT-BTC (sme alternative, being replaced)

class ChartOfAccountsType(Enum):
    COA_200 = "coa_200"
    COA_99 = "coa_99"
    COA_ENTERPRISE = "coa_enterprise"

class SettlementCycle(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class VATMethod(Enum):
    DEDUCTION = "deduction"       # Khấu trừ — standard
    OUTPUT_ONLY = "output_only"   # Đầu ra — small/VAT-registered

class EInvoiceMode(Enum):
    SOFTWARE_CERT = "software_cert"   # Self-signed cert; transitional
    CA_SIGNED = "ca_signed"          # GDT-approved CA; mandatory post-2026

@dataclass
class EInvoiceSeries:
    prefix: str                   # e.g., "AA/2026"
    next_sequence: int            # next integer to issue; non-resettable
    active: bool                  # max 15 active
    ca_signer: str | None         # CA identifier for this series
```

### 3.3 Flag Type Definitions

```python
class FlagType(Enum):
    LAW = "law"                     # Never changeable without migration patch
    CONFIG = "config"               # Admin-changeable with audit log + 2nd approval

class FlagScope(Enum):
    COMPANY = "company"             # One value per company
    SYSTEM = "system"               # Single global value (all companies; rare in production)

class FlagCategory(Enum):
    LEGAL = "legal"
    TAX = "tax"
    ACCOUNTING = "accounting"
    E_INVOICE = "e_invoice"
    INTEGRATION = "integration"
    SECURITY = "security"
    UI = "ui"
```

---

## 4. Port Interface (Repository Contract)

Add to `src/application/ports/__init__.py`:

```python
class SystemSettingsRepositoryPort(ABC):
    @abstractmethod
    def get_company_config(self, company_id: UUID) -> CompanyConfig | None: ...

    @abstractmethod
    def create_company_config(self, config: CompanyConfig) -> CompanyConfig: ...

    @abstractmethod
    def update_company_config(self, config: CompanyConfig, actor: UUID) -> CompanyConfig: ...

    @abstractmethod
    def get_flag(self, company_id: UUID, flag_name: str) -> str | int | bool | None: ...

    @abstractmethod
    def set_flag(self, company_id: UUID, flag_name: str, value: Any, actor: UUID) -> None: ...

    @abstractmethod
    def get_config_version(self, company_id: UUID) -> int: ...

    @abstractmethod
    def get_e_invoice_series_next(self, company_id: UUID, prefix: str) -> int: ...

    @abstractmethod
    def advance_e_invoice_sequence(self, company_id: UUID, prefix: str, actor: UUID) -> int: ...

    @abstractmethod
    def append_audit_log(self, event: AuditLogEntry) -> AuditLogEntry: ...

    @abstractmethod
    def list_audit_log(self, company_id: UUID, from_date: date, to_date: date) -> list[AuditLogEntry]: ...

    @abstractmethod
    def is_period_locked(self, company_id: UUID, period: str) -> bool: ...

    @abstractmethod
    def lock_period(self, company_id: UUID, period: str, actor: UUID) -> None: ...
```

---

## 5. Service Layer Contracts

### 5.1 SystemSettingsService

Key methods:

| Method | Responsibility |
|--------|---------------|
| `get_config(company_id)` | Return CompanyConfig; all LAW fields as-is; CONFIG fields proxy via flag table |
| `init_company(company_info, legal_regime)` | One-time company setup; validates legal regime against known list; creates initial CompanyConfig with default CONFIG values |
| `update_flag(company_id, flag_name, value, actor)` | Validate actor has ADMIN role; LOG before change; check FlagType (LAW rejected); increment config_version |
| `lock_period(company_id, period, actor)` | Verify actor is ACCOUNTANT or ADMIN; mark period LOCKED in PeriodLockModel; emit audit log |
| `is_period_locked(company_id, period)` | Used by InvoiceService and VoucherService before accepting new entries |
| `advance_invoice_sequence(company_id, prefix, actor)` | Atomic increment; returns next_seq; never returns same seq twice |
| `validate_e_invoice_signing(company_id, cert_info)` | Check EInvoiceMode; if CA_SIGNED, verify cert is in ca_list; check cert expiry; reject if not |
| `get_audit_export(company_id, from_date, to_date)` | Generate full audit trail export in JSON+CSV |

### 5.2 PeriodLockService

```python
class PeriodLockService:
    PERIOD_LOCK_KEY = "period_lock:{company_id}:{period}"  # Redis or DB

    def is_locked(self, company_id: UUID, period: str) -> bool:
        """Returns True if period is LOCKED or FYEAR_CLOSED."""

    def lock(self, company_id: UUID, period: str, actor: UUID) -> None:
        """Sets PERIOD_LOCKED. Requires ACCOUNTANT+ role."""

    def close_fyear(self, company_id: UUID, fyear: int, actor: UUID) -> None:
        """Sets FYEAR_CLOSED. Requires CHIEF_ACCOUNTANT role. Irreversible."""

    def validate_before_entry(self, company_id: UUID, entry_date: date) -> None:
        """Raise AccountingPeriodLockedError if entry_date falls in locked period."""
```

### 5.3 AuditLogService

```python
class AuditLogEntry:
    id: UUID
    company_id: UUID
    actor_user_id: UUID | None        # None for system-initiated
    action: str                       # CONFIG_UPDATED | PERIOD_LOCKED | INVOICE_ISSUED | FLAG_VIOLATION
    entity_type: str | None
    entity_id: UUID | None
    before_value: str | None          # JSON serialized
    after_value: str | None           # JSON serialized
    ip_address: str | None
    user_agent: str | None
    created_at: datetime              # system-assigned; immutable

class AuditLogService:
    def emit(self, company_id, actor, action, entity_type, entity_id, before, after, ip=None, ua=None) -> None: ...

    def list_for_export(self, company_id, from_date, to_date) -> list[AuditLogEntry]: ...

    # Appender pattern — never UPDATE or DELETE; only INSERT
```

---

## 6. API Specification

### 6.1 Endpoints

All endpoints prefixed with `/api/v1/companies/{company_id}/settings`.

| Method | Path | Auth | RBAC | Description |
|--------|------|------|------|-------------|
| `GET` | `/config` | JWT | ACCOUNTANT, ADMIN | Retrieve full CompanyConfig (LAW fields masked or shown per policy) |
| `GET` | `/config/flags` | JWT | ACCOUNTANT, ADMIN | List all flags with current values, types, categories |
| `GET` | `/config/flags/{flag_name}` | JWT | ACCOUNTANT, ADMIN | Single flag value |
| `PATCH` | `/config/flags/{flag_name}` | JWT | ADMIN | Update CONFIG-flagged value (LAW-flagged rejected 403) |
| `POST` | `/config/audit-log/export` | JWT | ADMIN, AUDITOR | Trigger audit export (JSON + CSV) for date range |
| `POST` | `/config/period/lock` | JWT | ACCOUNTANT, ADMIN | Lock a specific accounting period |
| `POST` | `/config/period/close-fyear` | JWT | CHIEF_ACCOUNTANT | Close fiscal year (irreversible) |
| `GET` | `/config/period/status` | JWT | ACCOUNTANT, ADMIN | Period lock status for date range |
| `POST` | `/invoice-series/advance` | JWT | ACCOUNTANT | Advance next_seq atomically; returns new sequence |
| `GET` | `/invoice-series` | JWT | ACCOUNTANT, ADMIN | List active e-invoice series |
| `POST` | `/invoice-series` | JWT | ADMIN | Add new series (max 15 active) |
| `PATCH` | `/invoice-series/{prefix}` | JWT | ADMIN | Update active flag (cannot modify prefix or next_seq via API) |
| `POST` | `/config/legal-review` | JWT | CHIEF_ACCOUNTANT | Mark config as legally reviewed (stamps legal_reviewed_at/by) |

### 6.2 Response Schemas

```json
GET /api/v1/companies/{id}/settings/config/flags
{
  "company_id": "uuid",
  "config_version": 3,
  "flags": [
    {
      "name": "accounting_period_type",
      "flag_type": "LAW",
      "flag_scope": "COMPANY",
      "category": "ACCOUNTING",
      "current_value": "calendar",
      "editable": false,
      "description": "Ngày bắt đầu năm tài chính",
      "legal_basis": "Luật Kế toán 2015 Art. 29"
    },
    {
      "name": "vat_settlement_cycle",
      "flag_type": "CONFIG",
      "category": "TAX",
      "current_value": "monthly",
      "editable": true,
      "requires_2nd_approval": true,
      "description": "Chu kỳ kê khai thuế GTGT",
      "legal_basis": "NĐ 123/2020/NĐ-CP Art. 24"
    }
  ]
}
```

### 6.3 Error Responses

| HTTP | Code | Condition |
|------|------|-----------|
| 403 | `FLAG_LOCKED` | Attempt to modify LAW-flagged value as admin |
| 403 | `PERIOD_LOCKED` | Posting to locked period |
| 409 | `CONFIG_VERSION_CONFLICT` | Optimistic lock failure; config changed by another writer |
| 422 | `INVALID_FLAG_VALUE` | Value fails domain validator (e.g., invalid VAT rate) |
| 422 | `INVALID_PERIOD` | Cannot lock future period; cannot re-open locked period |
| 422 | `MAX_SERIES_EXCEEDED` | Attempt to add >15th active e-invoice series |
| 422 | `CA_NOT_APPROVED` | Attempt to use non-GDT CA for signing |

---

## 7. Database Schema

### 7.1 company_configs (1 row per company)

```sql
CREATE TABLE company_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL UNIQUE,  -- FK to companies table

    -- Legal constants
    accounting_period_type VARCHAR(20) NOT NULL,
    accounting_regime VARCHAR(30) NOT NULL,
    chart_of_accounts_type VARCHAR(30) NOT NULL,
    vat_rates JSON NOT NULL DEFAULT '[0,5,10]',
    minimum_retention_years INT NOT NULL DEFAULT 10,
    data_deletable BOOLEAN NOT NULL DEFAULT false,

    -- Config flags
    fiscal_year_start_month INT NOT NULL DEFAULT 1 CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
    fiscal_year_start_day INT NOT NULL DEFAULT 1 CHECK (fiscal_year_start_day BETWEEN 1 AND 31),
    vat_settlement_cycle VARCHAR(20) NOT NULL DEFAULT 'monthly',
    vat_method VARCHAR(20) NOT NULL DEFAULT 'deduction',
    e_invoice_mode VARCHAR(20) NOT NULL DEFAULT 'software_cert',
    ca_list JSON NOT NULL DEFAULT '[]',
    decimal_places INT NOT NULL DEFAULT 2 CHECK (decimal_places IN (0, 2)),
    default_currency VARCHAR(3) NOT NULL DEFAULT 'VND',
    cost_center_required BOOLEAN NOT NULL DEFAULT false,
    multi_level_cost_centers BOOLEAN NOT NULL DEFAULT false,
    data_retention_years INT NOT NULL DEFAULT 10 CHECK (data_retention_years >= 10),

    -- Audit metadata
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_by UUID NOT NULL,
    config_version INT NOT NULL DEFAULT 1,
    legal_reviewed_at TIMESTAMP,
    legal_reviewed_by UUID,

    CONSTRAINT uq_company UNIQUE (company_id)
);

CREATE INDEX idx_configs_company ON company_configs(company_id);
```

### 7.2 audit_log (append-only; NO UPDATE, NO DELETE)

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    actor_user_id UUID,
    action VARCHAR(50) NOT NULL,      -- CONFIG_UPDATED | PERIOD_LOCKED | INVOICE_ISSUED ...
    entity_type VARCHAR(50),
    entity_id UUID,
    before_value JSONB,
    after_value JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Time-series partitioning recommended for >1M rows/month
CREATE INDEX idx_audit_log_company_time ON audit_log(company_id, created_at DESC);
-- NO DELETE trigger enforced via DB role
REVOKE DELETE ON audit_log FROM PUBLIC;
```

### 7.3 period_locks

```sql
CREATE TABLE period_locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    fiscal_year INT NOT NULL,
    accounting_period INT NOT NULL,    -- 1-12 or custom; system-managed
    lock_type VARCHAR(20) NOT NULL,    -- PERIOD | FYEAR_CLOSED
    locked_at TIMESTAMP NOT NULL DEFAULT now(),
    locked_by UUID NOT NULL,
    notes TEXT,

    UNIQUE (company_id, fiscal_year, accounting_period)
);

CREATE INDEX idx_period_locks_company ON period_locks(company_id, fiscal_year, accounting_period);
```

### 7.4 e_invoice_series

```sql
CREATE TABLE e_invoice_series (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    prefix VARCHAR(20) NOT NULL,        -- e.g., AA/2026
    next_sequence INT NOT NULL,         -- NEVER reset below 1
    active BOOLEAN NOT NULL DEFAULT true,
    ca_signer VARCHAR(100),
    declared_to_gdt_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,

    UNIQUE (company_id, prefix),
    CHECK (next_sequence >= 1)
);

-- Trigger: enforce 15 max active
CREATE OR REPLACE FUNCTION check_max_series()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT COUNT(*) FROM e_invoice_series WHERE company_id = NEW.company_id AND active = true)
    >= 15 THEN
    RAISE EXCEPTION 'Max 15 active e-invoice series per company';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tgr_max_series BEFORE INSERT OR UPDATE ON e_invoice_series
FOR EACH ROW EXECUTE FUNCTION check_max_series();
```

### 7.5 config_audit_log

```sql
CREATE TABLE config_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL,
    config_version INT NOT NULL,
    actor_user_id UUID NOT NULL,
    flag_name VARCHAR(100) NOT NULL,
    flag_type VARCHAR(20) NOT NULL,
    before_value JSONB,
    after_value JSONB,
    change_reason TEXT,
    legal_reviewed BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_config_changes_company ON config_changes(company_id, config_version DESC);
```

---

## 8. Validation Rules

### 8.1 At Domain Boundary (Value Objects — immutable regardless of global flag state)

Already implemented:
- `TaxId`: `r"^\d{10}(-\d{3})?$"` — `src/domain/entities/base.py:68`
- `AccountCode`: `r"^[1-9]\d{2}$|^[1-9]\d{3}$"` — `src/domain/entities/base.py:84`

### 8.2 At Config Layer (LAW-type Flags — cannot be bypassed)

| Flag | Validation | Error |
|------|-----------|-------|
| `tax_id_pattern` | Regex pre-compile test on load; stored as compiled pattern | `SystemSettingsError("Invalid pattern in config")` |
| `account_code_pattern` | Same | same |
| `vat_rates` | Each rate must be int in {0, 5, 10} or configurable subset; no negatives except NT=-1 | `InvalidVATRateError` |
| `data_retention_years` | `>= 10` | `ConfigValidationError("Retention must be ≥10 per Luật Kế toán 2015 Art. 30")` |
| `fiscal_year_start_month` | `1 ≤ month ≤ 12` | same |
| `decimal_places` | `value in (0, 2)` | same |
| `ca_list` | Each entry must match `^[A-Z]{2,20}-\d{4}$` (CAID-YEAR pattern per GDT list) | `InvalidCAListError` |
| `e_invoice_series` | Prefix format: `^[A-Z]{1,4}/\d{4}$`; next_seq ≥ 1 | same |
| `accounting_regime` | Must be one of enum value | `InvalidRegimeError` |

### 8.3 At Service Layer (CONFIG-type Flags — change business rules)

| Rule | Enforcement |
|------|------------|
| LAW flags cannot be updated via API | `if flag_type == FlagType.LAW: raise FlagLockedError(403)` |
| Config change requires `config_version` match (optimistic lock) | Headers: `X-Config-Version: N`; 409 if mismatch |
| 2nd approval for certain flags (e.g., `vat_settlement_cycle`, `accounting_regime`) | `requires_2nd_approval` attribute on flag definition |
| Config change writes audit log BEFORE commit | Service emits log entry, then updates config |

---

## 9. Integration Points

| System | Flag(s) Involved | Direction | Protocol |
|--------|----------------|-----------|----------|
| InvoiceService (existing) | `period_lock`, `vat_rates`, `e_invoice_series`, `e_invoice_mode` | Read at entry time | Service call |
| VoucherService (existing) | `period_lock`, `cost_center_required`, `account_code_pattern` | Read at posting | Service call |
| Future e-tax module | `vat_method`, `settlement_cycle`, `mst_pattern` | Read/write | REST API |
| Future e-invoice module | `e_invoice_mode`, `ca_list`, `e_invoice_series` | Read at signing | Service call |
| Future BHXH module | `settlement_cycle`, `company_type` | Read at export | REST API |
| Auth/AuthZ | `roles` (reference) | Admin gate | Role check in API |

---

## 10. Migration Plan (v0 → v1)

Phase 1 — Entity + Repo + Tests:
- CompanyConfig entity in domain
- SQLAlchemyCompanyConfigRepository
- FlagType enum in base.py

Phase 2 — Service + Validation:
- SystemSettingsService
- PeriodLockService
- Validation rule engine

Phase 3 — Audit Log:
- AuditLogService
- Constraints + triggers in DB
- Storage tiering (hot/cold)

Phase 4 — API:
- REST endpoints
- Admin UI (if applicable)

Phase 5 — Integrations:
- Hook InvoiceService and VoucherService into period lock
- E-invoice series service

---

## 11. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| GDT changes legal constants without notice | Medium | HIGH — system wrong | Version pinned constants; OTA patch pipeline; quarterly legal review cadence |
| Company setup with wrong regime | Medium | HIGH — tax penalties | Mandatory accountant-led setup wizard; legal review stamp required before PROD |
| Concurrent config edits (race) | Low | MEDIUM | Optimistic locking (config_version); JSONB changelog for debugging |
| Audit log grows unbounded | HIGH (5+ years) | MEDIUM | Time-series partitioning; cold storage after 2 years; export capability maintained |
| SoD enforcement added after data in system | Medium | HIGH | Design for it now; retroactive SoD analysis on existing data is separate project |
| CA list mismatch at signing time | Low | HIGH (e-invoice rejected) | Weekly CA list sync from GDT; fail-closed if list cannot be refreshed |

---

## 12. Open Questions

| Q | Owner | Needed By |
|---|-------|-----------|
| Is there a Company entity or is company_id implicit from auth context? | Architect | Before Phase 1 code |
| What is max acceptable latency for audit_log emit? | Infra | Before Phase 3 code |
| Will we support multi-company in v1 or v2? | Product | Scope confirmation |
| Which roles have legal-review authority (legal_reviewed_by)? | Chief Accountant | Before Phase 2 |
| Should FLAG_TYPE LAW ever changeable via hot-patch vs migration? | Legal | Before Phase 1 schema |
| Export format for auditors: JSON, CSV, or direct DB read (pg_dump / mysqldump)? | Infra + Legal | Before Phase 3 |