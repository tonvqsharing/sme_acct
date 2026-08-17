# Business Rules Catalog: Company Module

Organization:
- **Category L** — LAW (immutable without external re-registration)
- **Category C** — CONFIG (changeable in-system with audit log)
- **Category S** — SYSTEM ENFORCED (no user override)
- **Category A** — AUDITOR (audit-specific rules)

---

## Section L — Legal Constants (cannot be overridden)

| Rule ID | Statement | Enforcement | Source | Blocking? |
|---------|-----------|-------------|--------|-----------|
| L-01 | MST must match `^\d{10}$` or `^\d{10}-\d{3}$` | Domain: TaxId VO | Luật Quản lý thuế 2019 Art. 6 | YES |
| L-02 | MST must be unique across system | DB UNIQUE constraint on companies.mst | Luật Quản lý thuế 2019 Art. 6 | YES |
| L-03 | Legal name must match ĐKKD (business registration certificate) | Domain validation at creation; legal review stamp | Luật Doanh nghiệp 2020 Art. 31 | YES |
| L-04 | Headquarters address must match ĐKKD registered address | Same | Luật Doanh nghiệp 2020 Art. 31 | YES |
| L-05 | Legal representative must match ĐKKD | Same | Luật Doanh nghiệp 2020 Art. 31 | YES |
| L-06 | MST cannot be changed after any invoice posted against company | Service layer check | NĐ 123/2020 Art. 16 | YES |
| L-07 | Company type determines accounting regime (cannot mismatch) | Config validation | TT 99/2025, TT 58/2026 | YES |
| L-08 | Listed JSC (CTCP niêm yết) requires quarterly BCTC | System flag | LKT 2015 Art. 8 | WARN |
| L-09 | Household Business (Hộ KD) requires simplified accounting module | Company type → simplified templates | Luật Doanh nghiệp 2020 | YES |
| L-10 | BHXH code required for all enterprise types except Hộ KD | Validation rule | Luật BHXH 2024 Art. 128 | YES |
| L-11 | Responsible accountant (Kế toán trưởng) must have valid MSKHMN | Validation at setup | LKT 2015 Art. 16 | YES |
| L-12 | Data retention ≥ 10 years for all accounting documents per company | Retention service | LKT 2015 Art. 44 | YES |
| L-13 | Company info historical records cannot be modified (WORM) | Audit log append-only | LKT 2015 + NĐ 13/2023 | YES |

---

## Section C — Config Flags (changeable with audit + role check)

| Rule ID | Statement | Category | Enforcement | Requires 2nd Approval? | Source |
|---------|-----------|----------|-------------|----------------------|--------|
| C-01 | Company type change requires external business registration re-filing | Legal | Service checks Mẫu 12 filed flag | YES (CHIEF_ACCOUNTANT) | Luật Doanh nghiệp 2020 Art. 32 |
| C-02 | MST change requires GDT notification (Mẫu 47) within 10 working days | Legal | Service checks notification reference | YES (CHIEF_ACCOUNTANT) | Luật Quản lý thuế 2019 Art. 50 |
| C-03 | Fiscal year start can be changed at company setup only | Operational | Service checks period locks | YES | LKT 2015 Art. 13 |
| C-04 | Accounting regime change requires policy change filing | Legal | Service blocks without external proof | YES | TT 99/2025 |
| C-05 | Bank accounts can be added/removed in-system | Operational | No external filing needed | NO | Internal |
| C-06 | Phone/email/website editable in-system | Operational | No external filing needed | NO | Internal |
| C-07 | Legal representative change requires DPI filing | Legal | Service checks Mẫu 12 filed flag | YES | Luật Doanh nghiệp 2020 Art. 32 |
| C-08 | Company status ACTIVE → SUSPENDED → DISSOLVED lifecycle | Operational | Service validates state transitions | YES (CHIEF_ACCOUNTANT for DISSOLVED) | LKT 2015 |

---

## Section S — System Enforced Rules

| Rule ID | Statement | Enforcement Point |
|---------|-----------|-------------------|
| S-01 | All company changes emit audit log BEFORE commit | CompanyService.update() |
| S-02 | Audit log append-only (REVOKE DELETE on audit_log) | DB role constraint |
| S-03 | Company cannot be created without legal_reviewed_at | Setup wizard gating; InvoiceService blocks if null |
| S-04 | MST uniqueness enforced at DB UNIQUE constraint | DB level; caught as DuplicateMSTError at service |
| S-05 | Company SUSPENDED → no new invoices/vouchers/partners | Each service checks company.status |
| S-06 | Company DISSOLVED → read-only; all writes rejected | Same |
| S-07 | Tenant isolation: every query scoped by company_id | TenantService.scope_query() appends WHERE |
| S-08 | Optimistic locking via config_version on company updates | UPDATE ... WHERE config_version = :v AND company_id = :id |
| S-09 | Company deactivate requires all periods locked + no DRAFT journals | CompanyService.deactivate() pre-check |
| S-10 | MST cannot be reused after company dissolution | DELETE from companies disallowed; DISSOLVED status = soft-delete |

---

## Section A — Auditor-Centric Rules

| Rule ID | Statement | Enforcement |
|---------|-----------|------------|
| A-01 | Auditor can export full company master data change history | GET /companies/{id}/audit-log |
| A-02 | MST change trail shows old MST (historical) vs new MST (from effective date) | Audit log before/after snapshot |
| A-03 | All company fields (legal name, MST, address) matchable against ĐKKD scan | Export includes current state JSON |
| A-04 | Company lifecycle events (create/suspend/dissolve) timestamped | Audit log with created_at DB-side |
| A-05 | Superuser company changes visible in audit | No privileged bypass |
| A-06 | Company creation event includes legal_review_stamp details | COMPANY_CREATED audit event includes CA user_id |

---

## Section D — Data Quality Rules

| Rule ID | Statement | Enforcement |
|---------|-----------|------------|
| D-01 | MST format pre-validated at TaxId VO construction | ValueError at construction |
| D-02 | Legal name non-empty, stripped | Domain validation |
| D-03 | Address minimum length | Domain validation |
| D-04 | Company type enum validation | InvalidCompanyTypeError |
| D-05 | Fiscal year start day valid for month (Feb ≤29) | Domain validation |
| D-06 | BHXH code format per BHXH agency rules (future integration) | Future: API check |
| D-07 | Bank account number format per bank (future) | Future: per-bank regex |
| D-08 | Duplicate bank account number prevented within company | DB unique constraint per company |