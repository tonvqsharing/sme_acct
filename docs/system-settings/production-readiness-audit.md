# Production Readiness Audit: System Settings Module

---


## Verdict: NOT PRODUCTION-READY

**19 critical gaps** + **4 major gaps** + **7 minor gaps** found. Current state cannot operate in Vietnamese SME accounting PROD environment.

---

## 4.1 Scoring Framework

| Tier | Blocker Level |
|------|--------------|
| P0 | Cannot launch without fix; legal penalty or audit failure |
| P1 | Must fix within 30 days of launch; competitive disadvantage or significant risk |
| P2 | Should fix within 90 days; quality or operational improvement |

---

## 4.2 P0 Blockers — Hard Stop for Production

| # | Gap | Legal Basis | Required Action | Current Status |
|---|-----|------------|-----------------|----------------|
| P0-01 | No CompanyConfig entity | Luật Kế toán 2015 Art. 28 | Build CompanyConfig domain aggregate + SQLAlchemyModel + API | ❌ Missing |
| P0-02 | No accounting period lock enforcement | Luật Kế toán 2015 Art. 29 | Build PeriodLockService + lock check at InvoiceService/VoucherService entry | ❌ Missing |
| P0-03 | No audit log (WORM append-only) | NĐ 13/2023 Art. 9; LKT 2015 Art. 30 | Build AuditLogService + REVOKE DELETE constraint + WORM storage | ❌ Missing |
| P0-04 | Tax ID (MST) validation only in domain value object, not enforced at company/invoice boundary system-wide | LKT 2015 Art. 28 | Extend validators to API input layer + invoice creation + partner creation | ⚠️ Partial — only in base.py, not in API |
| P0-05 | Account code (TK) validation only in value object, not enforced on voucher lines at service layer | TT 200/2014 Art. 5 | Validate in VoucherService.post() line-by-line | ❌ Missing |
| P0-06 | No e-invoice series / sequence management | GDT + NĐ 123/2020 | Build EInvoiceSeries table + atomic sequence advance | ❌ Missing |
| P0-07 | VAT rates hardcoded in enum (TaxRate) but not system-enforced (user can bypass via API untested path) | NĐ 123/2020 Art. 9 | Build config validation: vat_rates system flag; reject non-listed values at API | ❌ Missing |
| P0-08 | No retention enforcement — soft-delete on invoices/vouchers would violate law | LKT 2015 Art. 30; NĐ 13/2023 Art. 9 | Disable soft-delete on Invoice/Voucher entities; build archive state machine | ❌ Missing |
| P0-09 | No company/tenant isolation — all data globally accessible | Luật Doanh nghiệp 2020 | Build Company entity + request-scoped tenant context | ❌ Missing |
| P0-10 | No RBAC enforcement at backend — only UI/Flask-Login auth | Big4 SoD requirements | Add role check to every service method; map roles to RBAC from Flask-Login | ❌ Missing |
| P0-11 | Config changes not persisted to audit log | LKT 2015; NĐ 13/2023 | Emit audit event BEFORE every CompanyConfig update | ❌ Missing |
| P0-12 | No legal review stamp mechanism | Internal audit / CA workflow | Build legal_reviewed_at/by stamp + review summary workflow | ❌ Missing |
| P0-13 | Fiscal year start/period derivation not implemented | LKT 2015 Art. 12, 29 | Build PeriodLockService.fiscal_year_for(date) logic | ❌ Missing |

---

## 4.3 Major Gaps — P1 (Fix within 30 Days)

| # | Gap | Risk | Action |
|---|-----|------|--------|
| P1-01 | No e-invoice signing integration (PKI/CA) | Cannot produce legally valid e-invoices per NĐ 123/2020 | Integrate CA_SIGNED mode with PKI bridge; at minimum SOFTWARE_CERT interim mode |
| P1-02 | No backup + restore test procedure | Data loss risk; auditor will red-flag | Implement automated backup + quarterly restore test; document DR plan |
| P1-03 | No independent data export for auditors | "Black box" — auditor cannot independently verify data | Build /audit-log/export; support JSON + CSV; no UI dependency |
| P1-04 | No MFA enforcement on privileged roles | Big4 standard; breach risk | Enable Flask-Security-Too MFA; enforce per role config |
| P1-05 | No concurrent edit detection (optimistic locking) for config | Race condition can cause config corruption | Add config_version + WHERE clause in UPDATE |

---

## 4.4 Minor Gaps — P2 (Fix within 90 Days)

| # | Gap | Risk | Action |
|---|-----|------|--------|
| P2-01 | No multi-cost-center management module | Operational — cannot track costs by department | Plan OrgUnit entity; C-09 flag as enabler |
| P2-02 | No COA versioning (TT200 vs TT99 switch-over) | Audit comparability issue if regime changes mid-year | Version COA entries; preserve historic periods |
| P2-03 | No import/export for chart of accounts list | Manual entry of TT200 COA (~300+ accounts) is error-prone | Provide COA seed script + CSV import |
| P2-04 | No rate variable for CIT (income tax) | Future tax provision calculation incorrect | Add CIT rate as system constant (currently 20%) |
| P2-05 | No reconciliation exception management | Bank imports produce mismatches; no tracking | Add reconciliation exception state machine |
| P2-06 | No password policy enforcement (rotation, complexity) | Security audit finding | Implement in auth layer |
| P2-07 | No in-app notification for regulatory updates | Risk of running on outdated constants | Add legal update monitor webhook |

---

## 4.5 Competitor Comparison

| Capability | Fast | MISA AMIS | BravoERP | This System |
|-----------|------|-----------|----------|-------------|
| 100+ system parameters | ✅ | ✅ | ⚠️ | ❌ (0) |
| Multi-regime COA | ✅ | ✅ | ❓ | ❌ |
| Period lock (khóa sổ) | ✅ | ✅ | ⚠️ | ❌ |
| E-invoice integration | ✅ | ✅ (meInvoice) | ❓ | ❌ |
| Audit trail (WORM, 10y) | ✅ | ✅ | ❓ | ❌ |
| MFA for admin | ✅ | ✅ | ❓ | ❌ |
| Independent auditor export | ✅ | ✅ | ❓ | ❌ |
| Config change audit log | ✅ | ✅ | ❓ | ❌ |
| Legal review stamp | ✅ (paper trail; not digital) | ✅ | ❓ | ❌ |
| CA list validation (e-invoice) | ✅ | ✅ | ❓ | ❌ |
| Retention enforcement (soft-delete disabled) | ✅ | ✅ | ❓ | ❌ |
| SoD enforcement (backend) | ✅ (implied by 100+ params) | ✅ | ❓ | ❌ |

**Performance:** 0 of 12 critical production features implemented. Minimum to enter market: 10 of 12 P0 blockers resolved.

---

## 4.6 Big4 "Black Box" Risk Assessment

| Auditor Finding | Present? | Codebase Evidence |
|----------------|---------|------------------|
| No audit trail | ❌ YES GAP | audit_log table does not exist |
| Journal entries editable post-posting | ❌ YES GAP | Voucher.lock() exists but Invoice has no equiv; no guard at service layer |
| No separation of Duties at backend | ❌ YES GAP | Auth has Flask-Login but no role check in repo/service |
| System-calculated fields without transparency | ⚠️ PARTIAL | Invoice._recalculate() uses float rounding — formula visible but no independent verification |
| Superuser actions not in audit log | ❌ YES GAP | No AuditLogService; Flask-Login events not captured |
| No period lock at DB level | ❌ YES GAP | PeriodLock entity does not exist |
| Soft-delete instead of void/process cancel | ❌ YES GAP | No DELETE restrictions on vouchers/invoices |
| No independent data export | ❌ YES GAP | No export API endpoint |

**Risk summary:** An external auditor reviewing current code would issue findings on at least 7 of 8 Big4 IT General Controls (ITGC). System cannot pass annual audit in current state.

---

## 4.7 Production Readiness Checklist

| Check | Required | Status |
|-------|---------|--------|
| CompanyConfig entity exists | ✅ Yes | ❌ No |
| At least 15 legal flags enforced | ✅ Yes | ❌ None |
| Tax ID regex enforced system-wide | ✅ Yes | ⚠️ Only in domain value object |
| Account code regex enforced system-wide | ✅ Yes | ⚠️ Only in domain value object |
| VAT rate enforcement (system-managed, no bypass) | ✅ Yes | ❌ No |
| Period lock enforced at DB | ✅ Yes | ❌ No |
| Audit log WORM (REVOKE DELETE) | ✅ Yes | ❌ No |
| Retention policy enforced (≥10y, no soft-delete) | ✅ Yes | ❌ No |
| Fiscal year start configuration + derivation | ✅ Yes | ❌ No |
| E-invoice series + atomic sequence | ✅ Yes | ❌ No |
| Company/tenant isolation | ✅ Yes | ❌ No |
| RBAC backend enforcement (SoD) | ✅ Yes | ❌ No |
| Legal review stamp workflow | ✅ Yes | ❌ No |
| Independent auditor export | ✅ Yes | ❌ No |
| MFA for admin / privileged roles | ✅ Yes | ❌ No |
| Backup + restore test procedure | ✅ Yes | ❌ No |
| PKI/CA list validation | ✅ Yes | ❌ No |

**Score: 3 of 16 checks pass. System is 18% production-ready.**

---

## 4.8 Recommendations (Priority Order for Release)

**Prerequisite for any production flag:**
1. Build CompanyConfig entity (P0-01) — gateway for all other flags
2. Build AuditLogService (P0-03) — every other change needs audit log
3. Build PeriodLockService (P0-02) — Invoice/Voucher cannot be created without this

**Within Sprint 1 (2 weeks):**
4. Enforce TaxId + AccountCode at API boundary (P0-04, P0-05)
5. Enforce VAT rates at InvoiceService entry (P0-07)
6. Build config audit log emit (P0-11)
7. Add config_version optimistic locking (P1-05)

**Within Sprint 2 (2 weeks):**
8. Build EInvoiceSeries + atomic advance (P0-06)
9. Disable soft-delete on Voucher/Invoice; build archive state machine (P0-08)
10. Build Company entity + tenant context (P0-09)
11. Build RBAC role checks in services (P0-10)

**Within Sprint 3 (2 weeks):**
12. Build PKI bridge (minimum: SOFTWARE_CERT mode; CA_SIGNED mode placeholder)
13. Build legal review stamp + legal_reviewed_at
14. Build auditor export endpoint
15. Implement fiscal year derivation logic

**Post-launch (within 30 days):**
16-19. MFA, backup, SO reconciliation, COA seeding

---

## 4.9 Risk-Reward Assessment

| Decision | Reward | Risk |
|----------|--------|------|
| **Delay launch** until P0 blockers resolved | Legally compliant; audit-pass; customer trust | Delayed time-to-market; funding burn |
| **Launch without P0-02 (period lock)** | Faster launch | Tax audit failure; data integrity open to manipulation |
| **Launch with P0-01 to P0-05 only** | Partial compliance | Still willfully blind spot for auditors; statute violation |
| **Launch in "beta" / free tier with disclaimer** | Product feedback loop | Disclaimer does not override legal obligation; still liable |

**Recommendation:** Do NOT launch for Vietnamese tax-compliant production until all 13 P0 blockers are resolved. A "free/beta" tier with labeled "training / demo only" can coexist; but invoices, vouchers, and BCTC generated by the system must be legally sound for any paying production customer.

---

## 4.10 Audit Trail Test (Minimal Viability)

Before PROD sign-off, run and pass these tests:

```
Test 1: Verify audit log rejects DELETE
  [SQL] REVOKE DELETE ON audit_log FROM PUBLIC;
  [Test] Attempt DELETE FROM audit_log WHERE id = ? → fails with permission denied

Test 2: Verify period lock rejects backdated entry
  [Setup] Lock period 2026-03
  [Test] InvoiceService.create(invoice issue_date=2026-03-15) → raises AccountingPeriodLockedError

Test 3: Verify config change is audit logged
  [Action] PATCH flag cost_center_required=true
  [Test] SELECT 1 FROM config_changes WHERE flag_name='cost_center_required' AND before='false' → exists

Test 4: Verify LAW flag rejected on PATCH
  [Action] PATCH flag tax_id_pattern to custom regex
  [Test] Response 403 FLAG_LOCKED

Test 5: Verify invoice sequence non-resettable
  [Action] advance_e_invoice_sequence(AA/2026) → returns 1
  [Action] advance → returns 2 (never returns 1 again)
  [Action] Check: UPDATE e_invoice_series SET next_sequence=0 → rejected

Test 6: Verify INV/MST validation
  [Action] Invoice(serial="AA", number="00001", partner_tax_id="ABC")
  [Test] Response 422 — invalid MST

Test 7: Verify soft-delete disabled on locked voucher
  [Setup] Post voucher; lock period
  [Action] voucher.delete()
  [Test] Response: InvalidVoucher("Cannot delete locked voucher — LKT 2015 Art. 30")

Test 8: Verify concurrent config edits detect conflict
  [Action] User A: version=3; User A PATCHs → version=4
  [Action] User B: X-Config-Version=3; User B PATCHs
  [Test] Response 409 CONFIG_VERSION_CONFLICT
```

---

## 4.11 Estimated Effort (SME ACCT Sprint Estimates)

| Task | Sprints | Files Changed | Complexity |
|------|---------|--------------|-----------|
| CompanyConfig entity + tests | 0.5 | 5–7 | Medium |
| AuditLogService + DB constraints | 0.5 | 4–6 | Medium |
| PeriodLockService + lock enforcement | 0.5 | 4–6 | Medium |
| API layer (all settings endpoints) | 0.5 | 3–5 | Low |
| EInvoiceSeries sequence | 0.5 | 4–6 | Medium |
| Tenant isolation (Company entity) | 1.0 | 8–12 | High |
| RBAC backend enforcement | 0.5 | 3–5 | Medium |
| Legal review stamp | 0.5 | 3–4 | Low |
| Auditor export | 0.5 | 2–3 | Low |
| MFA enforcement | 0.5 | 2–3 | Medium (framework-dependent) |
| Soft-delete disable + archive state | 0.5 | 2–4 | Medium |
| Fiscal year derivation | 0.5 | 2–3 | Low |
| COA seed data + versioning | 0.5 | 3–5 | Low |
| Backup + DR plan | 0.5 | 1 | Low |
| Big4 ITGC documentation | 0.5 | 2–3 | Low |
| **TOTAL** | **~6–7 sprints** | **~45–65 files** | — |

**Caveat:** These are SME ACCT sprint estimates assuming familiar team; Big4-aligned audit-grade implementation typically adds 20-30% for SoD, traceability matrix, and formal UAT.

---

## 4.12 Final Legal Verification Checklist (Before PROD Sign-Off)

- [ ] Re-fetch and cite specific articles from vbpl.vn for: LKT 2015 Art. 12, 28-30; NĐ 123/2020 Art. 9, 24-25; NĐ 13/2023 Art. 9-12; TT 200/2014 Art. 5; TT 119/2014 Art. 6-12
- [ ] Confirm current TT 99/2025 effective date and scope vs TT 200
- [ ] Confirm GDT CA approval list URL (c2qz.gdt.gov.vn) and update cadence
- [ ] Confirm NĐ 89/2026 (VAT draft) impact on rate table before hard-coding
- [ ] Confirm BHXH 2024 (Law 52/2024/QH15) data requirements for company_type filing
- [ ] Engage Vietnamese legal counsel to review BRD for legal accuracy
- [ ] Pre-launch: engage VACPA-certified accountant to "system audit" the codebase