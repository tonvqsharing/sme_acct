# Template: Tax Audit Preparation Checklist

Pre-audit readiness assessment for Vietnamese General Tax Department (Tổng cục Thuế) inspection.

---

## Pre-Audit Checklist

### 30 Days Before
- [ ] Legal review stamp current (legal_reviewed_at within last 90 days)
- [ ] All periods up to close date properly locked
- [ ] No AccountingPeriodLockedError breaches in audit log (or documented with justification)
- [ ] VAT method (KHẤU TRỪ vs ĐẦU RA) matches tax registration declaration
- [ ] E-invoice series: all declarations current; no inactive series with outstanding invoices

### 7 Days Before
- [ ] Export tax data for targeted periods: JSON + CSV
- [ ] Run: `GET /audit-log/export?from={fyear_start}&to={fyear_end}`
- [ ] Verify: all config changes for the period have LEGAL_REVIEW_STAMPED
- [ ] Verify: no LAW-flag VALID attempts logged
- [ ] Verify: no SO_D violation events

### Day of Audit
- [ ] Present: system config snapshot + legal_review stamp
- [ ] Provide: full transaction export (vouchers, invoices) for open periods
- [ ] Provide: VN VAT compliant format (GDT schema) exports
- [ ] Provide: MST validation proof (system enforces L-01)
- [ ] Provide: Account code pattern proof (system enforces L-02)

### Auditor Dispute Resolution
- [ ] Each audit event has ip_address + user_agent
- [ ] Admin actions double-logged (superuser audit)
- [ ] Period locks are from DB, not client-side state

---

## Audit Evidence Package

| Item | Format | Provided By |
|------|--------|------------|
| Company legal info | PDF from system + original MST cert | System + Admin |
| Accounting regime declaration | PDF (from tax registration) | Admin + External |
| System config snapshot | JSON (from `GET /config`) | System API |
| Config changes log | CSV (from `/config/audit-log/export`) | System API |
| VAT summary per quarter | CSV + XML (tax schema) | System export |
| Invoice register | CSV/XML (e-invoice format) | System export |
| Voucher register | CSV | System export |
| Chart of accounts | CSV/PRN (per TT200) | System export |
| Retention policy proof | Config export showing `data_retention_years=10` | System API |
| Audit log retention | System shows WORM REVOKE DELETE + 10y archive | DB admin |
| Period lock log | CSV showing lock/unlock per period | System API |
| User access summary | Access review report (A + CA signed) | Admin + CA |