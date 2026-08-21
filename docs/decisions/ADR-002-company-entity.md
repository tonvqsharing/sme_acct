# ADR-002: Company Entity as Root Aggregate

## Status
Accepted

## Date
2026-08-17

## Context

Vietnamese accounting law treats every accounting system as anchored to a legally registered entity (đơn vị kế toán). Luật Kế toán 2015 Art. 6 defines an accounting entity as a legal person registered under Luật Doanh nghiệp 2020.

Current codebase has NO Company entity, NO `companies` table, and NO `company_id` FK on any financial table (partners, invoices, vouchers). All data is globally accessible with no tenant isolation. This means:

- We cannot issue a legally valid invoice (NĐ 123/2020 requires seller MST on each invoice)
- We cannot track which entity a voucher belongs to
- We cannot implement period lock per entity
- We cannot scope System Settings (CompanyConfig) to a company
- We cannot support multi-company without first adding single-company
- Auditor cannot verify data segregation

Competitors (Fast, MISA, Tryton) all have this as a core concept. Tryton's `company` module is since v1.0 (2008) — 18 years of production hardening.

We need a Company module that:
1. Stores all mandatory legal info per Luật Doanh nghiệp 2020
2. Enforces MST uniqueness + format
3. Provides company_type classification (TNHH/CTCP/HKD/etc.)
4. Enables tenant isolation via company_id FK
5. Feeds fiscal_year, accounting_regime, and CompanyConfig
6. Supports company status lifecycle (ACTIVE/SUSPENDED/DISSOLVED)
7. Is extended by ALL other modules

## Decision

Add a `Company` domain entity in `src/bricks/company/domain.py`, backed by a `companies` table, with these key properties:

1. **Root aggregate**: Company is the root. Partner, Invoice, Voucher all have non-nullable `company_id` FK after migration.

2. **Legal-first fields**: 20+ fields covering all mandatory info from Luật Doanh nghiệp 2020 Art. 31. Legal name, MST, address, legal rep, ĐKKD, company type, tax agency, BHXH code.

3. **MST uniqueness at DB level**: UNIQUE constraint on `companies.mst`. Domain validates format via existing `TaxId` value object.

4. **Single company per deployment in v1**: Simpler. Hard-code `company_id = 1` in middleware. Future multi-company adds role-based company selection.

5. **Company type enum**: `SINGLE_LLC`, `MULTI_LLC`, `JSC`, `LISTED_JSC`, `SOLE_PROP`, `PARTNERSHIP`, `HOUSEHOLD`, `COOP` — per Luật Doanh nghiệp 2020 Art. 2.

6. **Accounting regime derived from company_type**: HOUSEHOLD → TT58_MICRO; enterprise types → TT99. Enforced in service layer.

7. **Status lifecycle**: `ACTIVE` → `SUSPENDED` → `DISSOLVED`. Irreversible post-DISSOLVED (archive-only).

8. **Audit trail on all changes**: Company changes logged in `audit_log` + `config_changes` before commit (write-ahead pattern).

9. **MST change is restricted**: Can only be changed with external GDT notification proof. Historical documents retain old MST (WORM).

10. **No soft-delete on Company**: DISSOLVED status = soft-disable. Record retained indefinitely.

## Alternatives Considered

### A. Skip Company Entity; Use Config-Only Approach

Store company info as system settings (CompanyConfig with legal_name, MST fields).

- **Pros:** Faster to implement; no DB migration on existing tables
- **Cons:** No FK enforcement; no per-entity isolation; cannot extend to multi-company; violates DDD aggregate root principle; auditors cannot verify data belongs to registered entity
- **Rejected:** Coarse-grained; violates Big4 golden-record principle.

### B. Multi-Company from Day 1 (Full Tryton Model)

Build multi-company UI, user-company join table, company selector at login, from start.

- **Pros:** Future-proof; matches Tryton's mature pattern
- **Cons:** 2-3x scope; most Vietnamese SMEs are single-entity; delays all other modules
- **Decision:** Architect FOR multi-company (schema supports it), but ship SINGLE company per deployment. Add company selector later.

### C. Use External ERP ID (Import from ĐKKD API)

Auto-fetch company info from government business registration API.

- **Pros:** Eliminates manual data entry; guarantees ĐKKD match
- **Cons:** No public API exists yet (dichvucong.gov.vn is portal, not API); manual verification still required
- **Deferred:** Manual entry in v1; API integration in v2 when government publishes.

### D. Defer Company Module; Build Invoices Without It

Assume single company with hardcoded legal info in config.

- **Pros:** Fastest path to demo
- **Cons:** Every invoice legally requires valid MST (NĐ 123/2020); cannot demo real invoicing; data un-auditable
- **Rejected:** Product cannot issue a single legal invoice without Company. Blocking for all production revenue.

## Consequences

- **Positive:**
  - Single source of truth for legal identity
  - All financial data traceable to a registered entity
  - Enables every downstream module (settings, invoice, voucher, tax, audit)
  - Clean extension to multi-company later
  - Auditors can verify entity identity per BCTC

- **Negative:**
  - Requires migration on all existing tables (partners, invoices, vouchers)
  - Adds latency: every INSERT now requires company_id (extra FK)
  - Existing data must be backfilled (manual or script)
  - Tenant middleware adds per-request overhead (~1ms)

- **Risks:**
  - MST changes after go-live require careful migration (historical vs. future documents)
  - Company type misclassification at setup leads to wrong COA/templates — must validate at CA setup stage
  - Single-company assumption may be wrong: if first customer is multi-entity, schema change required

- **Runtime:**
  - Company lookup by MST: indexed, <5ms
  - Company create: ~200ms (domain validation + INSERT + audit)
  - Tenant scoping per query: +1 WHERE clause, negligible

## Compliance

- Luật Doanh nghiệp 2020 Art. 31: Company fields legal_name, MST, address, legal_rep → ✅ All captured
- Luật Kế toán 2015 Art. 6: Accounting entity definition → ✅ Company IS the accounting entity
- Luật Kế toán 2015 Art. 44: 10-year retention per entity → ✅ Company is retention anchor
- NĐ 123/2020 Art. 16: Invoice must show legal name + MST → ✅ Scoped to company
- Big4 golden record: One authoritative entity per MST → ✅ DB UNIQUE constraint

## Follow-up ADRs

- ADR-003: Tenant Isolation Strategy (when multi-company v2 is planned)
- ADR-004: MST Change Data Migration Strategy (when first MST change occurs)