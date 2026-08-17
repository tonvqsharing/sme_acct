# Business Rules Catalog: System Settings Module

Organization:
- **Category L** — LAW (immutable without migration patch)
- **Category C** — CONFIG (changeable by admin with audit + 2nd approval as flagged)
- Sources cited by abbreviation: LKT=Luật Kế toán, ND=Nghị định, TT=Thông tư, GDT=Tổng cục Thuế, IFRS=IFRS for SMEs

---

## Section L — Legal Constants (cannot be overridden)

| Rule ID | Statement | Enforcement | Source | Blocking? |
|---------|-----------|-------------|--------|-----------|
| L-01 | Tax ID (MST) must match `^\d{10}$` or `^\d{10}-\d{3}$` | Domain: `TaxId.__post_init__` → ValueError; API: 422 | Luật Quản lý thuế 2019 Art. 7 | YES |
| L-02 | Account code (TK) must match `^[1-9]\d{2}$` or `^[1-9]\d{3}$` | Domain: `AccountCode.__post_init__` → ValueError | TT 200/2014 Art. 5 | YES |
| L-03 | VAT rates at system level must be subset of {0%, 5%, 10%, NT} | Config validation at SystemSettingsService | NĐ 123/2020 Art. 9 | YES |
| L-04 | Data retention for vouchers, invoices, BCTC ≥ 10 years | DB constraint: NO DELETE on audit_log, voucher, invoice tables for rows >10y | LKT 2015 Art. 30 | YES |
| L-05 | Soft-delete must be disabled on documents that have legally-mandated retention | Domain layer raises if `delete()` called on locked voucher/invoice | LKT 2015; NĐ 13/2023 | YES |
| L-06 | E-invoice numbering is sequential and non-resettable | `e_invoice_series.next_sequence` increments atomically; never allows RESET | GDT + NĐ 123/2020 | YES |
| L-07 | Maximum active e-invoice series: 15 per company | DB trigger: check_max_series() | GDT guidance | YES |
| L-08 | Printed vouchers must bear company name, MST, address, configured at system level | CompanyConfig fields enforced non-nullable | LKT 2015 + TT 119/2014 | YES |
| L-09 | After period LOCK, no posting to that period allowed | PeriodLockService.is_locked() checked at entry time; repo rejects | LKT 2015 | YES |
| L-10 | After FYEAR_CLOSED, no changes to any entry in that year | Same check; FYEAR_CLOSED outranks PERIOD_LOCK | LKT 2015 | YES |
| L-11 | VAT ID (MST) on invoices must trace to a customer/supplier with valid MST | CompanyConfig enforces format at partner creation | LKT 2015 + NĐ 123 | YES |
| L-12 | Number of decimal places is uniform per company (0 or 2) | Monitored at Invoice._recalculate and Voucher line totals | LKT 2015 | WARN only (per VN: reports can display rounded but underlying can keep decimals) |
| L-13 | Accounting period type (Jan1, Apr1, custom) cannot change retroactively without BCTC restatement | PeriodLockService + legal review gating | LKT 2015 Art. 29 | YES |
| L-14 | User cannot delete accounting period before migrating entries | Domain raises if period has entries and DELETE requested | LKT 2015 | YES |
| L-15 | PKI signing certificate must be on GDT-approved CAs list if using CA_SIGNED mode | Config validation + signing-time re-check | Digital Signature Law 2005 + GDT list | YES |

---

## Section C — Config Flags (changeable with audit + role check)

| Rule ID | Statement | Category | Enforcement | 2nd Approval? | Source |
|---------|-----------|----------|-------------|---------------|--------|
| C-01 | Accounting regime (TT200, TT99, TT58_MICRO, TT133) selectable at setup only; not changeable mid-period without filing accounting policy change | Legal | Config check + audit log | YES (CHIEF_ACCOUNTANT) | LKT 2015 |
| C-02 | VAT settlement cycle: MONTHLY (default) or QUARTERLY (opt-in if revenue ≤ VND 1B/year) | Tax | Config validation | YES | TT 92/2015 |
| C-03 | VAT method: DEDUCTION or OUTPUT_ONLY — declared at tax registration; changes require tax authority approval | Tax | Config validation | YES | Luật Quản lý thuế 2019 |
| C-04 | Fiscal year start month/day — default 1/1 but may select 4/1 | Accounting | Config validation | NO | LKT 2015 |
| C-05 | Decimal places: must be 0 or 2 | Accounting | Config validation | NO | LKT 2015 |
| C-06 | E-invoice mode: SOFTWARE_CERT or CA_SIGNED | Legal | Config validation | YES | NĐ 123/2020 |
| C-07 | CA list — populate from GDT published list | Legal | Config validation | NO at runtime | GDT c2qz.gdt.gov.vn |
| C-08 | Cost center required on vouchers (False default; can be enabled) | Operational | Service check; domain validation | NO | Internal |
| C-09 | Multi-level cost centers (False default) | Operational | Service check | NO | Internal |
| C-10 | Default currency (VND default; multi-currency requires foreign trading license) | Legal | Config validation matches company info | NO | LKT 2015 |
| C-11 | Default cost formula (FIFO per TT200; AVG permitted) | Accounting | Config validation | NO | TT 200/2014 |
| C-12 | Data retention years (≥10 default; can be increased) | Legal | Config validation | NO | LKT 2015 |
| C-13 | Print template version — selects between standard and customized mẫu in TT | UI | Config validation | NO | TT 119/2014 |

---

## Section S — System Enforced Rules (no user override)

| Rule ID | Statement | Enforcement Point |
|---------|-----------|-------------------|
| S-01 | All config changes write audit log BEFORE commit | SystemSettingsService.update_flag() — emit before mutation |
| S-02 | Audit log append-only (REVOKE DELETE) | DB role: REVOKE DELETE ON audit_log FROM app_role |
| S-03 | Period lock populates from data, not UI-only | PeriodLockService.is_locked() checks DB; no client-side-only gate |
| S-04 | Concurrent config edits detected via config_version (optimistic lock) | Database CHECK constraint: config_version always incremented |
| S-05 | Concurrent period locks detected via unique constraint | period_locks UNIQUE (company_id, fiscal_year, period) |
| S-06 | E-invoice sequence atomic — never returns same sequence to two requests | advance_e_invoice_sequence: FOR UPDATE + increment in single DB transaction |
| S-07 | System constants (VAT rates 0/5/10) cannot be bypassed by API value injection | Config validation rejects non-listed values |
| S-08 | CompanyConfig not found → all write operations rejected | Guard at entry to every service |
| S-09 | Legal review stamp (legal_reviewed_at not null) required before PROD use flag true | Smoke test gating |
| S-10 | System settings are never in client-side-only state (JWT, localStorage) | All setting reads go through SystemSettingsService |

---

## Section A — Auditor-Centric Rules

| Rule ID | Statement | Enforcement |
|---------|-----------|-------------|
| A-01 | Auditor can export all config + transaction data without UI assistance | REST API: POST /audit-log/export returns full set |
| A-02 | Auditor access role has MFA enforced | Auth config |
| A-03 | All admin changes visible in audit export | CONFIG_CHANGES included in export |
| A-04 | Superuser (god-mode) actions logged as normal audit events | AuditLogService logs all role changes including admin |
| A-05 | No system action can delete or anonymize audit log within retention window | DB REVOKE DELETE; hard delete enforcement |
| A-06 | System settings can be extracted into standalone export for "snapshot" at any moment | GET /config/audit-log/export with DATE range |