# Company Module — Documentation Index

> Vietnamese SME Accounting System — Base Company Entity Module

## Module Status: NOT PRODUCTION-READY

Current codebase has zero Company entity implementation. This module is the **root dependency** for all other modules. No accounting data can exist without a Company.

---

## Why This Module Exists

Vietnamese accounting law (Luật Kế toán 2015 Art. 6; Luật Doanh nghiệp 2020 Art. 31) requires that every accounting system be anchored to a legally registered entity. The company provides:
- Legal identity for all BCTC, invoices, vouchers
- Tax regime selection (TT 99/2025 vs TT 58/2026)
- MST validation anchor
- Fiscal year boundary
- Chart of accounts regime
- Retention policy anchor
- Tenant isolation root (future multi-company)

---

## Documents

| File | Lines | Purpose |
|------|-------|---------|
| [README.md](README.md) | this | Index + gap summary |
| [brd-company.md](brd-company.md) | — | Business Requirements — "why" + scope |
| [specs-company.md](specs-company.md) | — | Functional/Technical Spec — "what to build" |
| [use-cases-company.md](use-cases-company.md) | — | Use cases: happy, alternative, exception paths |
| [processes-company.md](processes-company.md) | — | End-to-end process flows |
| [rules-company.md](rules-company.md) | — | Business rules catalog |
| [data-flows-company.md](data-flows-company.md) | — | Data flow diagrams + mappings |
| [workflows-company.md](workflows-company.md) | — | State machine workflows |
| [user-journeys-company.md](user-journeys-company.md) | — | End-to-end user journeys |
| [production-readiness-audit-company.md](production-readiness-audit-company.md) | — | Gap analysis + competitor comparison |
| [templates/](templates/) | — | Migrations, test plans, audit prep, change request |

---

## Relationship to Other Docs

| Doc | Relationship |
|-----|-------------|
| `docs/system-settings/` | Dependent — SystemSettings assumes CompanyConfig exists and is scoped to company_id |
| `docs/multi-company/` | Builds on this — Multi-company consolidation requires base Company entity first |
| `src/bricks/company/domain.py` | Extends — this module adds Company entity to domain |
| `src/bricks/company/storage.py` | Extends — adds companies table + company_id FKs |

---

## Critical Gaps (Current State)

| # | Gap | Blocking? |
|---|-----|-----------|
| 1 | No Company domain entity | P0 — all modules need it |
| 2 | No `companies` DB table | P0 |
| 3 | No `company_id` FK on Invoice, Voucher, Partner | P0 |
| 4 | No tenant isolation middleware | P0 |
| 5 | No Company setup wizard/API | P0 |
| 6 | No company type classification (TNHH/CTCP/HKD/HTX) | P0 |
| 7 | No fiscal year per-company | P0 |
| 8 | No legal representative tracking | P0 |
| 9 | No company change notification workflow | P1 |
| 10 | No company status lifecycle (ACTIVE/SUSPENDED/DISSOLVED) | P1 |

---

## Legal Citations (Verified via Research)

| Law | Articles | What it mandates |
|-----|----------|------------------|
| Luật Doanh nghiệp 2020 | Art. 2, 31, 32, 37 | Registered name, MST, address, legal rep, ĐKKD |
| Luật Kế toán 2015 | Art. 6, 13, 16, 28, 44 | Accounting entity definition, fiscal year, KTT |
| TT 99/2025/TT-BTC | Full | New accounting regime replacing TT 200/2014 |
| TT 58/2026/TT-BTC | Full | Micro-enterprise regime |
| NĐ 123/2020/NĐ-CP | Art. 16 | Invoice fields required |
| NĐ 13/2023/NĐ-CP | Art. 9-12 | Data retention obligations |
| Luật Quản lý thuế 2019 | Art. 6, 50 | MST registration, change notifications |
| Luật BHXH 2024 | — | BHXH registration per entity |

> ⚠️ Primary sources (vbpl.vn, gdt.gov.vn) were blocked during research. Verify article numbers before PROD compliance sign-off.

---

## Competitor Baseline

| Software | Company Module | Multi-Company | Prod-Ready | Notes |
|----------|---------------|---------------|-----------|-------|
| Fast Business Online | YES | YES | ✅ YES | Per-entity setup; master+subsidiary |
| Fast Accounting (desktop) | YES (single) | NO | ✅ single-entity | Different SKU |
| MISA AMIS | YES | UNKNOWN | ✅ single-entity | Separate SKUs per entity type |
| Tryton | YES (core) | YES (core) | ✅ globally | No VN locale |
| BravoERP | UNKNOWN | UNKNOWN | ❓ | Cannot verify |
| **This system** | ❌ NO | ❌ NO | ❌ NO | 0% — module does not exist |

---

## Dependencies

| Module | Depends on Company? |
|--------|---------------------|
| System Settings | YES — CompanyConfig scoped to company_id |
| Partner (Customer/Supplier) | YES — partner belongs to company |
| Invoice | YES — invoice issued by company |
| Voucher | YES — voucher belongs to company |
| Chart of Accounts | YES — COA is per-company |
| E-Invoice | YES — e-invoice bears company MST |
| Tax Filing | YES — per-entity declarations |
| Multi-Company Consolidation | YES — builds on Company |

**Conclusion:** Company module is the foundational aggregate root. Build it first.

---

## ADR

See: `docs/decisions/ADR-002-company-entity.md`