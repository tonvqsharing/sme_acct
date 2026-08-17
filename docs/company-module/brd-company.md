# BRD: Company Module (Base Entity)

| Field | Value |
|-------|-------|
| Version | 0.1.0 |
| Status | DRAFT |
| Owner | Product + Chief Accountant |
| Date | 2026-08-17 |
| Audience | Vietnamese SME accounting system — legal entity onboarding |

---

## 1. Executive Summary

Every accounting transaction in a Vietnamese SME system must belong to a legally registered entity. **The Company module is the foundational aggregate root — nothing else can exist without it.**

Current codebase: **NO Company entity, no company_id FK, no tenant isolation.** This is P0 blocker for ALL other modules. Cannot enter a single invoice or voucher without a company to own it.

**Production verdict: NOT PRODUCTION-READY. Zero Company implementation exists.**

---

## 2. Business Context

### 2.1 Target Users

| Persona | Role | Pain Point |
|---------|------|-----------|
| **Giám đốc / Chủ doanh nghiệp** | System owner | Needs one-time setup matching business registration |
| **Kế toán trưởng** | Configures company, signs BCTC | Needs verified legal info on every document |
| **Kế toán viên** | Enters transactions | Needs company choice (if multi-company); otherwise implicit |
| **Thuế viên / Kiểm toán viên** | External auditor | Needs single company identification per document |

### 2.2 Regulatory Drivers

| Law | Implication |
|-----|-----------|
| Luật Doanh nghiệp 2020 Art. 31 | System must store registered name, MST, address, legal rep, ĐKKD |
| Luật Kế toán 2015 Art. 6 | Accounting entity (đơn vị kế toán) must be legal person |
| Luật Kế toán 2015 Art. 13 | Fiscal year defined per entity |
| Luật Kế toán 2015 Art. 44 | 10-year retention per entity |
| NĐ 123/2020/NĐ-CP Art. 16 | Invoice must show seller legal name + MST |
| Thông tư 99/2025/TT-BTC | COA regime + accounting method per entity |
| Thông tư 58/2026/TT-BTC | Micro-enterprise simplified regime |
| Luật Quản lý thuế 2019 Art. 6 | MST is primary unique key for tax entity |
| NĐ 13/2023/NĐ-CP | Data retention per entity |
| Luật BHXH 2024 | BHXH code per entity |

### 2.3 Competitor Baseline

| Product | Company Module | Type | Setup Fields | Multi-Entity |
|---------|---------------|------|-------------|--------------|
| Fast Accounting | YES | Single | 15+ fields | NO (desktop) |
| Fast Business Online | YES | Per entity | Full legal info | YES master/subs |
| MISA AMIS | YES | Per entity | Full | YES (enterprise tier) |
| Tryton | YES (core `company` module) | Per entity | From Party model | YES native |
| BravoERP | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| **This system** | **NO** | **None** | **None** | **NO** |

---

## 3. Scope

### 3.1 In Scope (v1)

- Company domain entity with 20+ mandatory fields
- Company type classification (LLC 1TV, LLC 2TV+, JSC, Sole Prop, Hộ KD, HTX)
- MST validation at company creation (regex + uniqueness)
- Legal info enforcement: registered name, address, legal rep, ĐKKD
- Fiscal year definition per company (calendar Apr, custom)
- Accounting regime selection per company (TT 200/2014, TT 99/2025, TT 58/2026, TT 133)
- BHXH code tracking per company
- Bank account list per company
- Company status lifecycle: ACTIVE → SUSPENDED → DISSOLVED
- Company setup wizard (one-time, mandatory)
- Company info change notification workflow (Mẫu 12)
- Tenant isolation via `company_id` FK on all financial tables
- Audit trail for company info changes

### 3.2 Out of Scope (v1)

- Multi-company consolidation (BCTC hợp nhất) — separate `docs/multi-company/` spec
- Branch management (Chi nhánh) — each branch gets separate Company record in v1
- Foreign exchange / multi-currency per company
- XBRL entity tagging
- Company dissolution workflow (legal process — manual + audit)
- IFRS entity ID tagging

---

## 4. Business Objectives

| Obj ID | Objective | Success Metric | Priority |
|--------|-----------|----------------|----------|
| OBJ-01 | Every invoice/voucher/partner linked to valid Company | 100% coverage; no orphan records | P0 |
| OBJ-02 | MST validated + unique across system | Zero duplicate MST; zero invalid format | P0 |
| OBJ-03 | Company setup wizard covers all mandatory legal fields | Setup completion in ≤30 min | P0 |
| OBJ-04 | Company type determines accounting regime defaults | Correct COA + BCTC template auto-selected | P0 |
| OBJ-05 | Company info changes tracked + audited | All changes in config_changes + audit_log | P0 |
| OBJ-06 | Fiscal year per company enforced | Period lock scoped per company | P0 |
| OBJ-07 | Company status lifecycle enforced | Cannot create invoices for SUSPENDED/DISOLVED | P0 |
| OBJ-08 | Tenant isolation enforced at DB layer | No cross-company data access | P0 |

---

## 5. Non-Functional Requirements

| NFR-ID | Requirement | Target | Priority |
|--------|-------------|--------|----------|
| NFR-01 | Company lookup by MST | <5ms indexed query | P0 |
| NFR-02 | Company setup smoke test | ≤30 min for accountant | P0 |
| NFR-03 | Company info change audit log | Write-ahead, WORM, ≥10y | P0 |
| NFR-04 | Tenant isolation at DB | Enforced by FK + application middleware | P0 |
| NFR-05 | Company config propagation | <1s cache invalidation | P1 |
| NFR-06 | Concurrent company edits | Optimistic locking; config_version | P1 |
| NFR-07 | MB per company record | <5KB | P2 |
| NFR-08 | Setup wizard offline-capable | Works without tax authority API | P2 |

---

## 6. Assumptions

| ASM-ID | Assumption | Risk if False |
|--------|-----------|---------------|
| ASM-01 | Company has valid ĐKKD before system setup | Cannot issue legal invoices |
| ASM-02 | MST is assigned by GDT, not self-selected | MST validation rule is authoritative |
| ASM-03 | Company type is stable (changes via Mẫu 12 re-registration) | Company type change requires COA migration |
| ASM-04 | Single company per deployment in v1 | Multi-company not active in v1 |
| ASM-05 | Fiscal year can be calendar or Apr-start | Custom fiscal year requires explicit support |

---

## 7. Dependencies

| DEP-ID | Dependency | Owner | Risk |
|--------|-----------|-------|------|
| DEP-01 | System Settings module (CompanyConfig) | Dev team | CompanyConfig depends on Company entity existing first |
| DEP-02 | Auth/RBAC (ADMIN role for company setup) | Dev team | PARTIALLY SCOPED |
| DEP-03 | DB migration framework (Flask-Migrate) | Infra | In stack |
| DEP-04 | Tax authority MST verification API | External | Not yet integrated; manual entry + validation only |
| DEP-05 | Legal review of company type classification | CA | MUST BEFORE PROD |

---

## 8. Acceptance Criteria

- [ ] `Company` domain entity exists with ≥20 fields
- [ ] `companies` table exists with UNIQUE constraint on MST
- [ ] `company_id` FK added to `partners`, `invoices`, `vouchers` tables
- [ ] MST validation (`^\d{10}$` or `\d{10}-\d{3}`) enforced at domain boundary
- [ ] Company type enum covers all VN enterprise types
- [ ] Company setup wizard enforces all mandatory fields
- [ ] Fiscal year start configurable per company (calendar 1/1 or 4/1 default)
- [ ] Accounting regime selection stored per company (TT 200, TT 99, TT 58, TT 133)
- [ ] Company status lifecycle enforced (ACTIVE → SUSPENDED → DISSOLVED)
- [ ] Company info changes emitted to audit_log + config_changes
- [ ] Cannot create invoice/voucher/partner without valid company_id
- [ ] Tenant isolation verified: user A cannot see company B's data
- [ ] All 15+ legal fields validated against VN law requirements
- [ ] Unit tests cover happy/exception paths for company CRUD
- [ ] Integration test: create company → add partner → create invoice → audit trail exists