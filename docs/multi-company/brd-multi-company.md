# BRD — Multi-Company / Master-Module
> Vietnamese SME Accounting Platform — Multi-Tenant Master-Module Business Requirements Document
> Version: 0.1.0 | Status: DRAFT | Authors: BA Lead (20+ yrs), Chief Accountant (20+ yrs)

---

## 1. Executive Summary

This BRD defines business requirements for a **multi-company / master-module** capability within the SME Accounting Platform. The module enables a **parent (master) company** to:
- Manage multiple legal-entity subsidiaries
- Consolidate financial statements (BCTC hợp nhất)
- Maintain per-entity accounting books while enforcing group-level policies
- Comply with Vietnamese tax, accounting, and regulatory frameworks

### Production Readiness Verdict

| Question | Answer |
|---|---|
| Can current repo operate as multi-company PROD? | **NO** |
| Blocking gaps | 7 critical (see Section 8) |
| Estimated effort to PROD-ready v1 | 12–18 weeks |
| Recommended approach | Vertical slice: one subsidiary → master sync → consolidated BCTC |

---

## 2. Business Context & Drivers

### 2.1 Market Reality
Vietnam's enterprise landscape includes **enterprise groups** (tập đoàn, tổng công ty) that own multiple legal subsidiaries. Regulatory filing requires:
- **Separate accounting books** per legal entity (Luật Kế toán 2015, Thông tư 99/2025/TT-BTC)
- **Consolidated BCTC** for parent companies with ≥1 controlled subsidiary (Luật Doanh nghiệp 2020 Art. 218–224)

### 2.2 Competitive Benchmark
| Product | Multi-Company | Vietnamese Compliant | Production Ready |
|---|---|---|---|
| Fast Business Online | YES | YES | ✅ YES |
| Fast Accounting (desktop) | NO | YES (single) | ❌ NO multi |
| MISA AMIS | NOT CONFIRMED | YES (single) | ❓ UNKNOWN |
| BravoERP | UNKNOWN | UNKNOWN | ❓ CANNOT VERIFY |
| Tryton v8 | YES (native) | PARTIAL (no VN locale) | ⚠️ NEEDS LOCALIZATION |

### 2.3 Stakeholders
| Role | Name/Role | Pain Point |
|---|---|---|
| Group CFO / Kế toán trưởng Tổng công ty | Consolidated reporting, adjusting entries, eliminations | Manual Excel consolidation; 15–30 days to close |
| Subsidiary Bookkeeper | Entity-level books, tax filing, invoices | Separate systems per entity; no unified view |
| Tax / Compliance Officer | Annual BCTC hợp nhất filing, tax audit trail | Data reconciliation errors multi-entity |
| System Administrator | User provisioning across entities | No role-based entity access |
| Statutory Auditor | Audit trail per entity and group | Disconnected primary/secondary books |

---

## 3. Scope

### 3.1 In Scope (v1)
- Multi-company tenant model (1 master = N subsidiaries)
- Per-entity chart of accounts (COA) configurable by regime
- Per-entity tax ID (MST), tax agency, fiscal year
- Subsidiary ledger posting; master receives consolidated data
- Adjusting entries at parent level (NST/NLD elimination entries)
- Consolidated BCTC: Balance Sheet, Income Statement, Cash Flow (direct)
- Consolidated BCTC: Notes / Thuyết minh (per Circular 99/2025)
- Role separation: Master user vs. Subsidiary bookkeeper
- Consolidation group configuration (Nhóm hợp nhất)
- Audit trail: entity-level + group-level

### 3.2 Out of Scope (v1)
- Real-time sync across subsidiaries (async batch acceptable)
- Multi-currency consolidation (v2)
- Equity method / proportional consolidation for joint ventures (v2)
- Intercompany transaction auto-matching (v2)
- IFRS full compliance mode (v2)
- Multi-branch within one legal entity (v2)

---

## 4. Legal & Regulatory Requirements

### 4.1 Mandatory Per-Entity Requirements
| Req | Legal Basis | Description |
|---|---|---|
| L1 | Luật Quản lý thuế 2019 | Each entity has separate MST; separate GTGT/TNDN/TNCN declarations |
| L2 | Luật Kế toán 2015 Art. 28 | Separate accounting books (Sổ sách kế toán) per legal entity |
| L3 | Thông tư 99/2025/TT-BTC | COA per entity per accounting regime (micro / SME / enterprise) |
| L4 | Nghị định 123/2024/NĐ-CP | E-invoice must reference issuing entity's MST |
| L5 | Luật BHXH 2024; NĐ 158/2025 | BHXH/BHYT declarations per entity |
| L6 | Tổng cục Thuế recognition list | Software must appear on recognized list per entity registration |

### 4.2 Mandatory Consolidated Requirements (Parent Only)
| Req | Legal Basis | Description |
|---|---|---|
| C1 | Luật Doanh nghiệp 2020 Art. 218–224 | Parent with ≥1 subsidiary must prepare BCTC hợp nhất |
| C2 | Circular 200/2014 (old) / 99/2025 (new) | Thuyết minh BCTC hợp nhất required |
| C3 | VAS/IFRS consolidation standards | NST elimination, NLD elimination, uniform accounting policies |
| C4 | Enterprise Law 2020 | NST/NLD transactions eliminated; minority interest disclosed |

### 4.3 Compliance Checklist
- [ ] Per-entity MST in master profile
- [ ] Per-entity COA mapped and validated against Circular 99/2025
- [ ] Per-entity fiscal year start/end configurable
- [ ] Per-entity tax agency (Cục Thuế) assigned
- [ ] Master can select consolidation method (full / proportional)
- [ ] Consolidated BCTC templates per Circular 99/2025 Mẫu BCTC
- [ ] Audit log for all consolidated adjusting entries
- [ ] Software registration tracking per entity MST

---

## 5. User Roles

| Role | Code | Description |
|---|---|---|
| MASTER_ADMIN | SysAdmin | Full access to all companies; user management |
| GROUP_CFO | CFO | Master-level reporting; adjusting entries; consolidation approval |
| SUBSIDIARY_BOOKKEEPER | Bookkeeper | Entity-level CRUD; cannot access other entities |
| SUBSIDIARY_MANAGER | Manager | Entity-level approval (invoices, vouchers) |
| AUDITOR | Auditor | Read-only across all entities + consolidated |
| TAX_OFFICER (internal) | Compliance | Filing review per entity |

---

## 6. Requirements Summary

### 6.1 Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| FR-MC-01 | Create subsidiary company under master | Must | Parent creates child with MST, COA, fiscal year, tax agency |
| FR-MC-02 | Edit company profile | Must | Change name, address, MST, tax agency; history preserved |
| FR-MC-03 | Deactivate company | Must | Soft-deactivate; historical records intact; no new posting |
| FR-MC-04 | Assign user to company | Must | User gets role-scoped access to only assigned companies |
| FR-MC-05 | Per-company COA configuration | Must | Add/edit/delete accounts; validate against `^[1-9]\d{2,3}$`; per Circular 99 |
| FR-MC-06 | Per-company fiscal year | Must | FY can differ per entity; closing must occur per entity |
| FR-MC-07 | Post invoice/voucher to specific company | Must | All records tagged with `company_id`; validation per-entity rules |
| FR-MC-08 | Initialize subsidiary from master | Should | Copy COA, opening balances, customers, suppliers from parent if needed |
| FR-MC-09 | Pull subsidiary balances (period close) | Must | Snapshot of trial balance per subsidiary at period end |
| FR-MC-10 | Enter master adjusting entry | Must | NST/NLD elimination entry with source reference; cannot affect subsidiary books |
| FR-MC-11 | Generate consolidated BCTC | Must | BS, P&L, CF per Circular 99 BCTC templates |
| FR-MC-12 | Consolidation approval workflow | Must | CFO approves consolidated BCTC before finalization |
| FR-MC-13 | Consolidated audit log | Must | Record who, what, when for every consolidated entry |
| FR-MC-14 | Master group CRUD | Should | Create/merge/rename consolidation groups |
| FR-MC-15 | Per-entity e-invoice series | Must | Separate serials per MST; Tổng cục Thuế registration per entity |
| FR-MC-16 | Intercompany invoice (optional) | Should | Invoice from entity A to B; flagged for elimination |

### 6.2 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-MC-01 | Tenant isolation: no cross-entity data leakage |
| NFR-MC-02 | Support 5 databases: sqlite, mariadb, mysql, postgresql 16+ |
| NFR-MC-03 | Local Bulma + HTMX only (offline server) |
| NFR-MC-04 | Concurrent posting: 2 users to 2 different entities must not deadlock |
| NFR-MC-05 | Consolidation run for N subsidiaries < 30s for N ≤ 10 |
| NFR-MC-06 | All audit logs immutable (append-only) |

---

## 7. Processes

### 7.1 Subsidiary Onboarding Process
```
Request → [Create company profile with MST] → Validate MST format → 
Configure COA (Circular 99 regime) → Assign fiscal year → Assign bookkeeper → 
Complete.
```

### 7.2 Period-End Close (Per Entity)
```
[Halt subsidiary] → [Post all invoices/vouchers for period] → 
[Run trial balance check] → [Lock period for subsidiary] →
[Notify master that TB available]
```

### 7.3 Consolidated BCTC Generation (Group)
```
[All subsidiaries locked] → [Pull TB from each subsidiary] → 
[Master enters adjusting entries for NST/NLD] → 
[Run consolidation engine] → [Generate BCTC hợp nhất] → 
[CFO approval] → [Lock consolidated period] → [Export / file]
```

### 7.4 Intercompany Elimination Process
```
[Run intercompany matching] → Flag uncleared intercompany balances → 
[Enter NST/NLD adjusting entry] → Recalculate consolidated TB → 
[Approve elimination] → Lock
```

---

## 8. Key Gaps — Why This Cannot Operate in PROD Today

### 8.1 Critical Gaps (Blocking)

| # | Gap | Impact | Required |
|---|---|---|---|
| G1 | No `Company` / `Tenant` entity | Cannot represent legal entity; cannot multi-post | Create `src/bricks/company/domain.py` |
| G2 | No tenant isolation in DB models | Data leak across entities; invalid consolidation | Add `company_id` FK to all transactional tables |
| G3 | No master-subsidiary hierarchy | Cannot model group relationship | Add `parent_company_id`, `consolidation_method` |
| G4 | No per-company COA regime | Invalid chart per Circular 99/2025 | Add `AccountingRegime` value object + entity |
| G5 | No consolidation engine | Cannot produce BCTC hợp nhất | Build `consolidation/` service with NST/NLD elimination |
| G6 | No role-based entity access | Subsidiary bookkeeper sees all data | Authz layer per company_id + role |
| G7 | No authz model for master vs. subsidiary | Cannot separate duties | Add roles + policy engine |

### 8.2 High Gaps (v1 required)

| # | Gap | Impact |
|---|---|---|
| G8 | No per-entity MST lifecycle | Cannot register software per entity with Tổng cục Thuế |
| G9 | No period-lock per company | Risk of backdated entries in subsidiary books |
| G10 | No BCTC templates per Circular 99 | Report output not compliant |
| G11 | No audit log for consolidated entries | Non-compliant with audit requirements |

### 8.3 Medium Gaps (v2)

| # | Gap | Description |
|---|---|---|
| G12 | No intercompany matching | Manual reconciliation required |
| G13 | No multi-currency | VND/foreign currency consolidation |
| G14 | No equity method | For associates / joint ventures |

---

## 9. Data Model Sketch

### 9.1 New Entities Required

```python
# src/bricks/multi_company/domain.py additions
class AccountingRegime(Enum):
    MICRO = "micro"          # Thông tư 58/2026/TT-BTC
    SME = "sme"              # Circular 99/2025 SME regime
    ENTERPRISE = "enterprise"  # Circular 99/2025 enterprise

class ConsolidationMethod(Enum):
    FULL = "full"            # 100% control, full consolidation
    PROPORTIONAL = "proportional"  # Joint control (v2)

class CompanyStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LIQUIDATED = "liquidated"
```

```python
# src/bricks/company/domain.py
class Company:
    """Legal entity in the enterprise group."""
    __slots__ = ("id", "name", "tax_id", "entity_type", "mst", 
                 "tax_agency", "accounting_regime", "fiscal_year_start",
                 "parent_company_id", "consolidation_method", "status",
                 "created_at", "updated_at")
    
    # Tax validated: ^\d{10}(-\d{3})?$
    # COA regime determines allowed account code patterns
    # parent_company_id = None for standalone; set for subsidiaries
```

### 9.2 DB Model Additions (models.py)

Add to all existing transactional tables:
- `company_id: Mapped[UUID | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)`
- `company: Mapped["CompanyModel"] = relationship(lazy="selectin")`

--- END OF FILE ---
