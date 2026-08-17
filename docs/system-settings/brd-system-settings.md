# BRD: System Settings / Global Flags Module

| Field | Value |
|-------|-------|
| Version | 0.2.0 |
| Status | DRAFT — Engineering review |
| Owner | Product + Chief Accountant |
| Date | 2026-08-17 |
| Audience | Vietnamese SME accounting software, CFO/Accountant/Owner persona |

---

## 1. Executive Summary

Vietnamese accounting law **mandates** a set of system-enforced constants, configuration flags, and validation rules that no user can bypass at form level. A "Global Flags / System Settings" module is **required for PROD use**, not optional. This BRD defines the minimum legally-compliant scope for a Vietnamese SME accounting system.

**Current codebase status**: **DOMAIN LAYER IMPLEMENTED**, migration applied, service layer complete. **IN PROGRESS** for API + DB constraint layer. 32% of P0 gaps resolved (6 of 19).

---

## 2. Business Context

### 2.1 Target Users

| Persona | Role | Pain Point |
|---------|------|------------|
| **Giám đốc / Chủ doanh nghiệp** | System owner, legal responsibility for accounting compliance | Wants one-time setup that "just works"; fears tax penalties |
| **Kế toán trưởng (Chief Accountant)** | Configures system, responsible for compliance sign-off | Needs verified legal-regime selection, period lock control, audit export |
| **Kế toán viên (Staff Accountant)** | Data entry, posting | Needs system to prevent errors; flags should be invisible to staff, enforced at boundary |
| **Thuế / Kiểm toán viên** | External auditor, tax inspector | Needs independent export path; no "black box" |

### 2.2 Regulatory Drivers (Vietnam)

| Driver | Implication |
|--------|------------|
| Luật Kế toán 2015 (Art. 28-30) | System must enforce chart of accounts, retention ≥10y |
| NĐ 123/2020/NĐ-CP + Thông tư 91/2026 | E-invoice mandatory; system must produce compliant output |
| NĐ 13/2023/NĐ-CP | Data retention + deletion rights; PDPA applies to employee data |
| Digital Signature Law 29/2005-CTN | CA-signed e-invoices require system integration |
| Thông tư 200/2014/TT-BTC | Chart of accounts (Số TK 111-899); system validation mandatory |
| Thông tư 100/2019/TT-BTC | SME accounting regime; simplified BCTC rules differ from enterprise |
| Luật Doanh nghiệp 2020 | Business registration sync; company type affects filing obligations |
| Big4 ITGC standards (ISA 315, AS 2201) | Audit trail, immutability, SoD — all system-enforced, not UI-only |

### 2.3 Competitor Baseline

| Software | System Settings Scope | MOQ Conclusion |
|----------|----------------------|----------------|
| **Fast Accounting** | 100+ parameters, 1 system + 14 business modules; installation explicitly covers "thiết lập ban đầu tham số hệ thống" | Table stakes for Viet market entry |
| **MISA AMIS** | Multi-regime COA, dual-book, meInvoice + mTax + BankHub integrations; cloud-first | Leading edge; SME ACCT must match at minimum |
| **BravoERP** | Active but smaller; training focus | Lower bar; confirm viability before launch |

---

## 3. Scope

### 3.1 In Scope (Implemented)

- Company-level configuration entity (one per tenant/company) — **Domain entity complete; Migration table `company_configs` created**
- Legal constant enforcement (tax ID format, account code pattern, VAT rates) — **Domain enums + validation; API boundary pending**
- Fiscal year / accounting period lock mechanism — **PeriodLockModel created via migration; service stub exists**
- Voucher / invoice number sequence management — **EInvoiceSeries table + model created via migration**
- Accounting regime selection (THONG TU 200, THONG TU 99, TT58_MICRO, TT133) — **Domain enum complete**
- E-invoice mode flag (SOFTWARE_CERT vs CA_SIGNED) — **Domain enum + config field complete**
- Data retention enforcement (≥10 years, soft-delete disabled) — **Not yet enforced at DB level**
- Audit trail (append-only system event log) — **SystemAuditLogModel created via migration; REVOKE DELETE pending**
- VAT/settlement cycle flag — **Domain complete; API validation pending**
- Decimal places setting (0 vs 2) — **Domain complete**
- Cost center required flag — **Domain complete**
- Integration enablement flags (e-tax, customs, BHXH) — **Domain complete**

### 3.2 In Scope (Pending)

- API layer validation for all CompanyConfig fields
- DB constraints (REVOKE DELETE, unique constraints)
- Service-layer enforcement of period locks
- RBAC backend checks
- Export API for auditors
- MFA for privileged roles

### 3.2 Out of Scope (v1)

- Multi-company consolidation (requires Company entity — separate spec)
- Per-user settings (only admin-configurable at company level)
- Full XBRL output (export to format; IFRS taxonomy future version)
- PKI/HSM integration (hardware token driver — requires OS-level integration)
- Real-time OCSP/CRL checking (phase 2 after basic CA list validation)


---