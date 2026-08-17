# BRD: System Settings / Global Flags Module

| Field | Value |
|-------|-------|
| Version | 0.1.0 |
| Status | SIGNED_OFF — pending stakeholder review |
| Owner | Product + Chief Accountant |
| Date | 2026-08-17 |
| Audience | Vietnamese SME accounting software, CFO/Accountant/Owner persona |

---

## 1. Executive Summary

Vietnamese accounting law **mandates** a set of system-enforced constants, configuration flags, and validation rules that no user can bypass at form level. A "Global Flags / System Settings" module is **required for PROD use**, not optional. This BRD defines the minimum legally-compliant scope for a Vietnamese SME accounting system.

Current codebase status: **NOT PRODUCTION-READY** — no config module, no period lock, no audit trail, no retention enforcement, no e-invoice integration, no tenant isolation.

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

### 3.1 In Scope

- Company-level configuration entity (one per tenant/company)
- Legal constant enforcement (tax ID format, account code pattern, VAT rates)
- Fiscal year / accounting period lock mechanism
- Voucher / invoice number sequence management
- Accounting regime selection (THONG TU 200, THONG TU 99, SME regime)
- E-invoice mode flag (software cert vs CA-signed)
- Data retention enforcement (≥10 years, soft-delete disabled)
- Audit trail (append-only system event log)
- VAT/settlement cycle flag
- Decimal places setting (0 vs 2)
- Cost center required flag
- Integration enablement flags (e-tax, customs, BHXH)

### 3.2 Out of Scope (v1)

- Multi-company consolidation (requires Company entity — separate spec)
- Per-user settings (only admin-configurable at company level)
- Machine-learning auto-configuration (future, after P0 audit trail in place)
- Full XBRL output (export to format; IFRS taxonomy future version)
- PKI/HSM integration (hardware token driver — requires OS-level integration)
- Real-time OCSP/CRL checking (phase 2 after basic CA list validation)

---

## 4. Business Objectives

| Obj ID | Objective | Success Metric | Priority |
|--------|-----------|----------------|----------|
| OBJ-01 | All Vietnamese legal constants enforced at system boundary | Zero user-input bypass of MST format, account code format, VAT rate | P0 |
| OBJ-02 | Company setup is one-time with legal review | Accountant completes setup in ≤1 day | P0 |
| OBJ-03 | No post-period-lock backdating | 100% rejection of posted-period entries | P0 |
| OBJ-04 | Audit can independently export data | Auditor gets full schema + CSV/JSON export without UI | P0 |
| OBJ-05 | All config changes are logged with who/when/what | Config audit log ≥10 years retention | P0 |
| OBJ-06 | E-invoice output compliant with Circular 91/2026 | Passes GDT validator | P1 |
| OBJ-07 | VAT/CIT declarations mapped to system data | 95%+ field pre-population on tax forms | P1 |
| OBJ-08 | Multi-regime COA switchable at setup | No data re-entry when switching TT200 → TT99 | P2 |

---

## 5. Non-Functional Requirements

| REQ-ID | NFR | Target | Priority |
|--------|-----|--------|----------|
| NFR-01 | Config read latency | <10ms from cache | P0 |
| NFR-02 | Period lock write | <50ms, atomic | P0 |
| NFR-03 | Audit log write | Non-blocking async, due-write guarantee | P0 |
| NFR-04 | Audit log retention | 10 years minimum; LEDAS/GLFS for high-value; hard delete disabled | P0 |
| NFR-05 | Config change propagation | <1 second to all app instances (cache invalidation) | P0 |
| NFR-06 | Data export speed | Full ledger: <30s for 1M row dataset | P1 |
| NFR-07 | Backup frequency | Every 6 hours; restore test quarterly | P1 |
| NFR-08 | Concurrent access | 50 simultaneous config reads; 1 writer locked | P1 |
| NFR-09 | Regulatory update response | System constants (VAT rates) patchable in <4h | P0 |
| NFR-10 | Language | All UI labels: Vietnamese (vi) + English (en) fallback | P1 |
| NFR-11 | Security | MFA for admin; password 8+ chars; 90-day rotation | P0 |
| NFR-12 | Data residency | VN lawful basis; PDPA compliance; no cross-border data flow without consent | P1 |

---

## 6. Assumptions

| ASM-ID | Assumption | Risk if False |
|--------|-----------|---------------|
| ASM-01 | GDT publishes and maintains approved CA list at c2qz.gdt.gov.vn | E-invoice signing breaks; need manual CA list update |
| ASM-02 | Company registers with GDT before system setup (MST valid at setup) | Company info becomes false; re-setup needed |
| ASM-03 | Accounting period definition is set at fiscal year start, not mid-period | Period lock cannot be calibrated retroactively |
| ASM-04 | Single Company per deployment (v1) | Multi-tenant isolation not yet needed |
| ASM-05 | SQLAlchemy 2.0 sufficient for all persistence (no need for temporal tables in v1) | Hard audit trail on history requires temporal table upgrade |

---

## 7. Dependencies

| DEP-ID | Dependency | Owner | Risk |
|--------|-----------|-------|------|
| DEP-01 | Company entity (tenant root) | Dev team | Current codebase has no Company entity — must add |
| DEP-02 | Authentication + RBAC (role admin-level) | Dev team | Partially scoped in AGENTS.md; must enforce backend |
| DEP-03 | Vietnamese locale (Flask-Babel) | Infra | Currently in stack; verify boilerplate |
| DEP-04 | Database migration tool (Flask-Migrate) | Infra | Already in stack |
| DEP-05 | GDT Circular 91/2026 e-invoice validator specs | External | If not published, implement draft version + flag upgrade path |

---

## 8. Acceptance Criteria (Overall Module)

- [ ] `CompanyConfig` entity exists with ≥15 mandatory fields (SF-01 through SF-15 from research)
- [ ] All 7 legal pattern validators (MST, AccountCode, VAT) enforce at domain boundary
- [ ] Period lock is enforced at repo layer — no bypass via direct SQL or API call
- [ ] All config changes written to immutable audit log with user_id, timestamp, before, after
- [ ] Retention policy enforced at DB constraint level (soft-delete disabled on vouchers ≥10y)
- [ ] VAT rate table is system-managed; user-input rejected
- [ ] E-invoice series number non-resettable; sequence persisted and audited
- [ ] Company setup wizard covers all mandatory fields with legal validation
- [ ] Admin cannot delete CompanyConfig or reset mandatory flags to defaults without migration
- [ ] Unit tests cover all exception paths in config change workflows
- [ ] Integration tests verify period lock + audit log + retention simultaneously
- [ ] Audit export ships full schema + config log + transaction log in open format (CSV/JSON)
- [ ] No diagnostic page or internal endpoint reveals raw system constants to unauthenticated users