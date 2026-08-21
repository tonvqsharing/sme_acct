# Production Readiness Audit: Company Module

> Vietnamese SME Accounting System — Base Company Entity

## Verdict: NOT PRODUCTION-READY

**Score: 0% (0 of 12 production checks pass).**

Current state: **NO Company entity exists in database. NO company_id FK on any financial table. NO tenant isolation.** System cannot associate a single invoice or voucher with a legal entity.

---

## 12 Critical Checks

| # | Check | Required | Status |
|---|-------|----------|--------|
| 1 | `companies` table exists | YES | ❌ Missing |
| 2 | Company domain entity with ≥20 fields | YES | ❌ Missing |
| 3 | MST validation at domain boundary | YES | ❌ Missing (TaxId exists but not used in Company) |
| 4 | MST uniqueness at DB level | YES | ❌ Missing |
| 5 | `company_id` FK on `partners` table | YES | ❌ Missing |
| 6 | `company_id` FK on `invoices` table | YES | ❌ Missing |
| 7 | `company_id` FK on `vouchers` table | YES | ❌ Missing |
| 8 | Tenant isolation middleware | YES | ❌ Missing |
| 9 | Company status lifecycle enforced (ACTIVE/SUSPENDED/DISOLVED) | YES | ❌ Missing |
| 10 | Fiscal year per company + derivation logic | YES | ❌ Missing |
| 11 | Company setup wizard covering 15+ mandatory fields | YES | ❌ Missing |
| 12 | Legal review stamp workflow | YES | ❌ Missing |

---

## Gap Analysis by Domain

### Domain Layer
- [ ] No `Company` entity (`src/bricks/company/domain.py` missing)
- [ ] No `CompanyStatus` enum in `domain.py`
- [ ] No `CompanyType` enum in `domain.py`
- [ ] No `BankAccount` value object
- [ ] Existing entities (Partner, Invoice, Voucher) lack `company_id` attribute
- [ ] No `DuplicateMSTError`, `CompanyNotFoundError`, `CompanyLockedError` exceptions

### Application Layer
- [ ] No `CompanyRepositoryPort` interface
- [ ] No `CompanyService` with CRUD + legal validation
- [ ] No `TenantService` for request-scoped company resolution
- [ ] MST change logic (block post-invoicing) not enforced
- [ ] Company status lifecycle rules not enforced
- [ ] deactivate/dissolve pre-checks not implemented

### Infrastructure Layer
- [ ] `companies` table missing from `models.py`
- [ ] No `company_id` column on `partners`, `invoices`, `vouchers` tables
- [ ] No FK constraints from child tables to `companies`
- [ ] No `idx_companies_mst` index (critical for MST lookups)
- [ ] No tenant query-scoping middleware

### Presentation Layer
- [ ] No `/companies` API endpoints
- [ ] No company setup wizard UI
- [ ] No tenant resolution middleware
- [ ] No company management pages

### Legal Compliance
- [ ] Legal name validation against ĐKKD not enforced
- [ ] MST format not validated at company creation (only at TaxId VO level)
- [ ] LST uniqueness not enforced (unique constraint missing)
- [ ] Fiscal year boundary logic not implemented
- [ ] BHXH code requirement not enforced
- [ ] Company type → accounting regime mapping not enforced
- [ ] Legal review stamp workflow not implemented

---

## Competitor Comparison: Company Module

| Feature | Fast | MISA | Tryton | BravoERP | This System |
|---------|------|------|--------|----------|-------------|
| Company legal info (MST, name, address) | ✅ | ✅ | ✅ (Party) | ❓ | ❌ |
| Company type classification | ✅ | ✅ | ❌ | ❓ | ❌ |
| MST validation at setup | ✅ | ✅ | ❌ (user-managed) | ❓ | ❌ |
| MST uniqueness across system | ✅ | ✅ | ✅ | ❓ | ❌ |
| Fiscal year per company | ✅ | ✅ | ✅ | ❓ | ❌ |
| BHXH code tracking | ✅ | ✅ | ❌ | ❓ | ❌ |
| Legal rep tracking | ✅ | ✅ | ❌ | ❓ | ❌ |
| Company status lifecycle | ✅ | ✅ | ✅ | ❓ | ❌ |
| Audit trail for company changes | ✅ | ✅ | ✅ | ❓ | ❌ |
| Multi-company (separate entities) | ✅ (FBO) | ✅ (enterprise) | ✅ (core) | ❓ | ❌ |
| Tenant isolation in app | ✅ | ✅ | ✅ | ❓ | ❌ |
| Company setup wizard | ✅ | ✅ | ✅ | ❓ | ❌ |

---

## Dependency Chain (Why Company is P0)

```
Company module (THIS — missing)
  ↓
System Settings / CompanyConfig (depends on company_id)
  ↓
Partner / Customer-Supplier (depends on company_id)
  ↓
Invoice (depends on company_id + partner.company_id)
  ↓
Voucher (depends on company_id)
  ↓
Chart of Accounts (per company)
  ↓
E-Invoice / Tax / BHXH integrations (all per company)
  ↓
Multi-Company Consolidation (builds on Company)
```

**Without Company module:** No invoice can be created. No voucher can be posted. No partner can be registered. System is architecturally non-functional.

---

## Business Impact of Delay

| Delay Scenario | Impact |
|---------------|--------|
| **1 week delay** | Slight — building Company module correctly prevents rework |
| **1 month delay** | All other module development blocked; cannot demo invoicing |
| **3 month delay** | Project credibility risk; competitors have this |
| **No Company module at launch** | System cannot issue a single legal invoice — product is worthless for Vietnamese accounting |

---

## Estimated Effort

| Task | Sprints | Scope |
|------|---------|-------|
| Company entity + models + 20+ fields | 0.5 | M |
| Add company_id to 3 existing tables | 0.5 | M |
| CompanyService + all business rules | 0.5 | M |
| TenantService + middleware | 0.5 | M |
| Company API endpoints | 0.5 | S |
| Audit trail for company changes | 0.25 | S |
| Setup wizard UI | 0.5 | M |
| Integration tests (tenant isolation) | 0.5 | M |
| Migrations + data backfill script | 0.5 | M |
| **TOTAL** | **~2–3 sprints** | **~5L + 10M files** |

---

## Open Questions (Blocking Implementation)

| # | Question | Owner | Risk |
|---|---------|-------|------|
| Q1 | Will v1 be single-company or multi-company? | Product | Affects API design |
| Q2 | How to handle existing data with no company_id? | Dev team | Migration strategy |
| Q3 | Should branches be separate Company records or sub-entities? | Legal | Affects schema |
| Q4 | Who approves company creation? | CA | RBAC design |
| Q5 | How does MST uniqueness check integrate with GDT API? | External | Manual entry until API available |

---

## Recommendations

1. **Build Company module FIRST** before any other feature. No other feature is functional without it.
2. **Treat as v0.5 milestone:** Company module must be complete and audited before any invoice flows to PROD.
3. **Get MST validated externally:** Have a VACPA-certified accountant verify MST logic against current GDT rules before PROD.
4. **Legal review required:** Company setup wizard content must be reviewed by a Vietnamese legal team before launch.
5. **Multi-company from Day 1:** Architect for multi-company even if v1 ships single-company. Adding multi-company later to a single-company schema is a nightmare.