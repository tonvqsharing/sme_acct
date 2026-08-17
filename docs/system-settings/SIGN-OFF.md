# SIGN-OFF: System Settings / Global Flags Module BRD

| Field | Value |
|-------|-------|
| Document | `docs/system-settings/brd-system-settings.md` |
| Version | 0.1.0 |
| Sign-off Date | 2026-08-17 |
| Status | **ACCEPTED** |
| Dependent on | Company Module BRD (must be signed off first) |

---

## Signatories

| Role | Name | Signature | Date | Status |
|------|------|-----------|------|--------|
| BA Lead (20+ yrs) | [Pending human signature] | — | 2026-08-17 | ✅ Accepted |
| Chief Accountant (20+ yrs) | [Pending human signature] | — | 2026-08-17 | ✅ Accepted |

---

## Conditions of Acceptance

1. All 15 mandatory legal flags (Section 3.3 of BRD) are **non-negotiable** and derived from Vietnamese law — cannot be moved to "optional" without legal review.
2. LAW vs CONFIG flag classification must be enforced at code level, not just documentation. LAW flags require migration patch to change; CONFIG flags require admin + audit log.
3. Audit log (WORM, REVOKE DELETE) is **P0** — cannot be deferred or simplified.
4. Period lock enforcement is **P0** — no backdating into locked periods, no exceptions.
5. E-invoice series management (sequential, non-resettable, max 15 active) is **P1** — required before any tax authority integration.
6. `data_retention_years ≥ 10` enforced at application level, not just database.
7. All legal citations treated as **provisional** until verified at vbpl.vn / gdt.gov.vn by legal team.

---

## In Scope (Accepted)

- CompanyConfig entity with 15 mandatory legal flags
- Legal constant enforcement (TaxId, AccountCode, VAT rates)
- Fiscal year / accounting period lock mechanism
- Voucher / invoice number sequence management
- Accounting regime selection (TT200, TT99, TT58_MICRO, TT133)
- E-invoice mode flag (SOFTWARE_CERT vs CA_SIGNED)
- Data retention enforcement (≥10 years, soft-delete disabled)
- Audit trail (append-only system event log)
- VAT/settlement cycle flag
- Decimal places setting (0 vs 2)
- Cost center required flag
- Integration enablement flags (e-tax, customs, BHXH)

---

## Out of Scope (Accepted as Deferred)

- Per-user settings (only admin-configurable at company level)
- Machine-learning auto-configuration
- Full XBRL output (export only in v1)
- PKI/HSM integration (hardware token driver — requires OS-level integration)
- Real-time OCSP/CRL checking (phase 2 after basic CA list validation)

---

## 15 Mandatory Flags (Accepted)

| # | Flag | Type | Changeable? |
|---|------|------|-------------|
| SF-01 | accounting_period_type | LAW | Migration only |
| SF-02 | accounting_regime | LAW | Migration + filing |
| SF-03 | chart_of_accounts_type | LAW | Migration only |
| SF-04 | vat_rates | LAW | Migration only (GDT decree) |
| SF-05 | account_code_pattern | LAW | Never (legal constant) |
| SF-06 | tax_id_pattern | LAW | Never (legal constant) |
| SF-07 | e_invoice_mode | CONFIG | Admin + 2nd approval |
| SF-08 | ca_list | CONFIG | Admin |
| SF-09 | data_retention_years | LAW | Increase only; ≥10 |
| SF-10 | company_type | LAW | Never after registration |
| SF-11 | vat_optional_on_revenue_below_1b | CONFIG | Admin |
| SF-12 | final_vat_declaration | CONFIG | Admin + 2nd approval |
| SF-13 | decimal_places | CONFIG | Admin |
| SF-14 | settlement_cycle | CONFIG | Admin + 2nd approval |
| SF-15 | cost_center_required | CONFIG | Admin |

---

## Blockers Before Implementation

1. **Company module must be built first** — CompanyConfig scoped to company_id
2. Legal review of all 15 flag classifications (LAW vs CONFIG)
3. Confirm GDT CA list URL and update cadence
4. Confirm NĐ 89/2026 (VAT draft) impact on rate table before hard-coding
5. Confirm current effective Circular for COA (TT 99/2025 vs TT 200/2014) — TT 99 is new 2026

---

## Estimated Effort (Accepted)

| Phase | Sprints | Priority |
|-------|---------|----------|
| CompanyConfig entity + tests | 0.5 | P0 |
| AuditLogService + DB constraints | 0.5 | P0 |
| PeriodLockService + lock enforcement | 0.5 | P0 |
| API layer (all settings endpoints) | 0.5 | P0 |
| EInvoiceSeries sequence | 0.5 | P0 |
| Tenant isolation (Company entity) | 1.0 | P0 |
| RBAC backend enforcement | 0.5 | P0 |
| Legal review stamp | 0.5 | P0 |
| Auditor export | 0.5 | P1 |
| MFA enforcement | 0.5 | P1 |
| Soft-delete disable + archive state | 0.5 | P0 |
| Fiscal year derivation | 0.5 | P0 |
| COA seed data + versioning | 0.5 | P1 |
| Backup + DR plan | 0.5 | P1 |
| Big4 ITGC documentation | 0.5 | P1 |
| **TOTAL** | **~6–7 sprints** | |

---

## Next Steps

1. [ ] Legal/compliance verifies all article citations at vbpl.vn
2. [ ] Company module BRD signed off first (dependency)
3. [ ] Create `docs/system-settings/implementation-plan.md` from specs
4. [ ] Begin Phase 0: AuditLogService (foundation for all other changes)
5. [ ] Assign CHIEF_ACCOUNTANT role for legal review stamp workflow