# ADR-001: CompanyConfig Aggregate for System Settings / Global Flags

## Status
Accepted

## Date
2026-08-17

## Context

Vietnamese accounting law mandates that certain settings be enforced at the system application boundary — not at the user form level. These include:

- MST (Tax ID) format: `^\d{10}$` or `\d{10}-\d{3}`
- Account code (mã tài khoản): `^[1-9]\d{2}$` or `^[1-9]\d{3}$`
- VAT rates: 0%, 5%, 10%, NT (non-taxable) — cannot be overridden by users
- Data retention: ≥10 years — cannot be soft-deleted
- Period lock: entries cannot backdate into locked fiscal period

Current codebase: no System Settings module exists. Validators (`TaxId`, `AccountCode`) are implemented as domain value objects in `src/bricks/company/domain.py` but are only enforced when those value objects are constructed in domain code. No enforcement at API boundary — a user posting raw JSON could bypass validation via direct SQL or a future API endpoint.

We need a system-wide configuration aggregate that:
1. Stores all legal constants and configurable flags in one place
2. Distinguishes between LAW-type (immutable without legal patch) and CONFIG-type (changeable by admin with audit)
3. Emits audit log on every change
4. Enforces optimistic locking for concurrent edits
5. Provides the basis for building the first 12 P0 production blockers

## Decision

Use a `CompanyConfig` domain aggregate (one per company) backed by a `company_configs` table in SQLAlchemy 2.0:

```python
@dataclass
class CompanyConfig:
    company_id: UUID          # FK to Company (or placeholder in v1)
    accounting_period_type: AccountingPeriodType
    accounting_regime: AccountingRegime
    tax_id_pattern: str       # LAW — docs only; enforced by TaxId VO
    account_code_pattern: str # LAW — docs only; enforced by AccountCode VO
    vat_rates: frozenset[int] # LAW
    data_retention_years: int # LAW (range: >=10)
    fiscal_year_start_month: int  # CONFIG
    fiscal_year_start_day: int    # CONFIG
    vat_settlement_cycle: SettlementCycle  # CONFIG
    vat_method: VATMethod     # CONFIG (requires legal change approval)
    e_invoice_mode: EInvoiceMode  # CONFIG
    ca_list: frozenset[str]   # CONFIG, system-sourced from GDT
    e_invoice_series: list[EInvoiceSeries]  # CONFIG
    decimal_places: int       # CONFIG (0 or 2)
    cost_center_required: bool  # CONFIG
    ...
    config_version: int       # Optimistic lock version
    legal_reviewed_at: Optional[datetime]
    legal_reviewed_by: Optional[UUID]
```

Key architectural decisions:

1. **LAW vs CONFIG flag_type** stored as attribute on each field definition, not in DB schema. Enforcement is: LAW flags rejected by `set_flag` / `update_flag` at service layer.

2. **Optimistic locking** via `config_version` integer column. UPDATE requires matching client-supplied version; increments on success. No pessimistic locks.

3. **Single row per company** at DB level — `company_id` is UNIQUE constraint. Not a key-value pair table (would be harder to reason about; all COMPANY-scoped flags fit in one row for SMEs).

4. **Audit log integration**: Every CONFIG change writes to `config_changes` table AND `audit_log` table in a single transaction before `company_configs` UPDATE.

5. **WORM audit_log**: `REVOKE DELETE, UPDATE ON audit_log FROM app_role;` at DB level. No application-level enforcement — DB-enforced.

6. **Tax ID and Account Code** dual-layer enforcement: value objects (domain) AND system-level documented constants in CompanyConfig. API layer validates by constructing VOs; failed construction → 422.

7. **No key-value store**: Rationale — SME ACCT has ≤ 50 config flags. Key-value would add Redis layer complexity without benefit. All read via single SELECT; cache in Redis for hot reads only (Cache-Control on API response).

## Alternatives Considered

### A. No SystemConfig — Keep Validators Scattered

- **Pros:** Less code; ad-hoc approach
- **Cons:** LAW constants not centrally auditable; no single source of truth; bypass via SQL/stored proc; admin cannot view full legal compliance state
- **Rejected:** Violates Big4 principle of single source of truth for system settings. Audit trail cannot reconstruct "what was system configured as" at any point in time.

### B. Key-Value Table (Flag Name → Value)

Schema: `(company_id, flag_name, flag_value, flag_type, ...)`

- **Pros:** Flexible; easy to add new flags without migration
- **Cons:** No DB-level constraint on flag_value (enum/range validation requires application code); harder to enforce one-row-per-company invariants; queries require JSONB aggregation; less transparent to auditors
- **Rejected:** SMEs have ≤ 50 flags; key-value schema is indirection without benefit. SQLAlchemy 2.0 model with typed columns is more auditable (DB schema itself documents legal requirements).

### C. Separate Config Service (SaaS Pattern)

- **Pros:** Can evolve independently; clean bounded context
- **Cons:** Overkill for v1; network hop per config read; eventual consistency adds complexity
- **Deferred:** Right approach for multi-company / multi-tenant SaaS evolution. Today, CompanyConfig lives in application DB.

### D. Code as Configuration (Hardcode All Constants)

- **Pros:** Fast to implement; no DB table
- **Cons:** Cannot change without deployment; audit trail of changes impossible; LAW constants require migration script for any update; Serbian problem (NĐ 89/2026 draft — but even 1 change requires deploy)
- **Rejected:** Violates LKT 2015 Art. 30 — no record of configuration changes. At minimum one change (VAT rate, COA version) is regulatory requirement. Code-config mix (constants in code, configurable flags in DB) — decide: LAW constants in code with version tag, CONFIG flags in DB.

## Consequences

- **Positive:**
  - Single source of truth for system settings
  - All legal constants documented in one model
  - Audit trail of every change via config_changes WORM table
  - Optimistic locking prevents concurrent config corruption
  - Easy for auditors to verify system state

- **Negative:**
  - Requires migration script (Phase 1 upfront cost)
  - All existing repositories must be patched to use CompanyConfig (P0-01 blocker)
  - Flag changes require cache invalidation (Redis or application-level) — adds infra

- **Risks:**
  - Concurrent CA+A edits possible if both have ADMIN role; optimistic lock catches but requires retry UX
  - LAW flag type is psychologically mutable ("what does 'immutable' mean?"); must train CAs that LAW flags require IT migration, not PATCH

- **Runtime:**
  - Config read: 1 SELECT per request; cache with TTL=60s during config transaction
  - Config write: 1 SELECT + 1 UPDATE + 2 INSERTs in transaction; ~20ms on SQLite, ~5ms on PostgreSQL

## Compliance

- Luật Kế toán 2015 Art. 28-30: System must enforce COA, retention — ✅ Addressable via CompanyConfig + AuditLog
- NĐ 123/2020 Art. 24-25: VAT settlement cycle, e-invoice series — ✅ Stored as CONFIG flags
- NĐ 13/2023 Art. 9-12: Data retention, deletion rights — ✅ Retention flag + WORM audit log
- Big4 ITGC (ISA 315): Change management, access, audit trail — ✅ All implemented in this design

## Follow-up ADRs

- ADR-002: E-Invoice PKI Integration (when PKI bridge is built)
- ADR-003: Audit Log Cold Storage Strategy (when retention scale is validated)