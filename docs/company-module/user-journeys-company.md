# User Journeys: Company Module

---

## Journey 01: New Company Onboarding (CA Perspective)

**Persona:** Kế toán trưởng setting up a new LLC
**Goal:** Register new company in accounting system — match ĐKKD exactly

```
DAY 0 — PREP
  CA gathers:
    ✓ ĐKKD scan (business registration certificate)
    ✓ MST card from GDT
    ✓ Legal rep ID card
    ✓ BHXH code confirmation
    ✓ Tax agency registration confirmation
    ✓ Bank account opening docs
    ↓

DAY 1 — SETUP WIZARD (30 min)
  Login → System detects no companies → /companies/new
  ↓
  Step 1 — Legal Info
    legal_name: "Công ty TNHH ABC Việt Nam"  [from ĐKKD, exact match]
    mst: "0123456789"  [validated: 10 digits ✓]
    headquarters_address: "123 Nguyễn Văn Linh, P. Tân Phong, Q.7, TP.HCM"
    legal_representative: "Nguyễn Văn A"
    business_reg_number: "0312345678"
    business_reg_date: 2020-01-15
    business_fields: ["6202", "4791"]  [NACE codes from ĐKKD]
    ↓
  Step 2 — Company Type
    company_type: MULTI_LLC  → System derives accounting_regime=TT99
    ↓
  Step 3 — Accounting Setup
    fiscal_year_start: Jan 1 (calendar) [default]
    responsible_accountant_name: "Trần Thị B"
    responsible_accountant_license: "KHMN-01234"
    tax_agency: "Chi cục Thuế Quận 7"
    controlling_tax_office: "Cục Thuế TP.HCM"
    ↓
  Step 4 — BHXH
    bhxh_code: "0070123456"
    bhxh_agency: "BHXH Quận 7"
    ↓
  Step 5 — Bank + Contact
    bank_accounts: [
      { bank: "VCB", account: "0071234567890", branch: "PGD Quận 7", primary: true }
    ]
    phone: "0281234567"
    email: "info@abc.com"
    website: "https://abc.com"
    short_name: "ABC Co."
    ↓
  Step 6 — Legal Review
    System shows checklist:
      □ Legal name matches ĐKKD exactly ✓
      □ MST format valid ✓
      □ BHXH code registered ✓
      □ Accountant license valid ✓
    CA stamps: LEGAL_REVIEWED
    System: legal_reviewed_at = 2026-08-17
    ├── Company active ✓
    └── CompanyConfig created ✓

DAY 2 — SMOKE TEST
  CA runs guide:
    1. Customer "Khách hàng X" created ✓
    2. Invoice "AA/2026-00001" issued with company MST ✓
    3. Voucher "PC01" posted ✓
  All pass → CA confirms "Ready for team"
```

---

## Journey 02: MST Change Due to Merger (CA Perspective)

**Persona:** Kế toán trưởng
**Goal:** Update system with new MST after corporate restructuring

```
PRE-EVENT
  ABC Co. merges with XYZ Co.; new entity = ABD Co.
  GDT issues new MST = "9876543210"
  CA files Mẫu 47 notification with old tax authority
  ↓
DAY 1 — PREPARE
  CA gathers:
    ✓ New MST card: 9876543210
    ✓ Mẫu 47 notification reference: MT-2026-0089
    ✓ Effective date: 2026-09-01
  ↓
DAY 2 — SYSTEM UPDATE
  CA: POST /companies/{id}/change-mst
    new_mst: "9876543210"
    gdt_notification_ref: "MT-2026-0089"
    effective_date: "2026-09-01"
  ↓
  System:
    ✓ Validates new MST format
    ✓ Checks uniqueness (new MST not in use)
    ✓ Sets mst_changed_at = 2026-09-01
    ✓ Emits MST_CHANGED audit event (old_mst=0123, new_mst=9876)
  ↓
DAY 3 — BATCH RE-TAGGING
  System runs: UPDATE invoices SET mst='9876' WHERE company_id=? AND issue_date>='2026-09-01'
  Historical invoices (before Sept 1): keep old MST — legally valid
  ↓
LINGERING OBLIGATIONS
  - Tax filings for Aug 2026: use old MST
  - Tax filings from Sep 2026 onward: use new MST
  - E-invoice series: new MST must be registered with CA provider for CA_SIGNED mode
```

---

## Journey 03: Company Suspension for Audit (CA Perspective)

**Persona:** Kế toán trưởng
**Goal:** Temporarily suspend company operations pending tax audit

```
DAILY ROUTINE
  CA receives: GDT notification of pending tax audit for FY2025
  CA decides:暂停 operations during audit to prevent data contamination
  ↓
[CA] POST /companies/{id}/suspend
  reason: "Pending GDT tax audit — freeze from 2026-09-01"
  ↓
System:
  ✓ All FY2025 periods locked ✓
  ✓ No DRAFT vouchers ✓
  ✓ Pre-flight checks pass
  ↓
System sets: status=SUSPENDED
  ↓
[SA next day] tries to create Aug 2026 invoice (back-dated into audit scope)
  → System rejects: 403 COMPANY_SUSPENDED
  ↓
SA creates Sep 2026 invoice (post-audit) → REJECTED still (company suspended)
  CA must: POST /companies/{id}/reactivate AFTER audit completes
  ↓
[Audit] proceeds; CA provides frozen data export
  [Audit complete] → CA reactivates
  System: status=ACTIVE
  System: emits COMPANY_REACTIVATED
```

---

## Journey 04: Dissolution (End-of-Life Company)

**Persona:** Chief Accountant
**Goal:** Properly close company per legal requirements

```
YEAR 10 — PREPARATION
  Company operations ceased; assets liquidated; employees paid
  CA ensures:
    ✓ All tax returns filed per GDT
    ✓ All BHXH settled per Luật BHXH 2024
    ✓ All periods closed (FYEAR_CLOSED for all years)
    ✓ No open invoices, vouchers, or partners with balances
  ↓
[CA] POST /companies/{id}/dissolve
  ↓
System validates:
  ✓ CHIEF_ACCOUNTANT role
  ✓ All periods FYEAR_CLOSED (last 10+ years)
  ✓ Zero open documents
  ✓ All BHXH settled (future API check)
  ↓
System sets: status=DISSOLVED, is_active=False
System: emits COMPANY_DISSOLVED
  ↓
[Archive] All documents moved to WORM cold storage
[Legal]: Company record retained ≥10 years minimum; indefinite for LLC with liability exposure
[System]: read-only access preserved for auditors and legal proceedings
```

---

## Journey 05: Multi-Company User (Future)

**Personas:** SA manages books for 3 different companies
**Goal:** Switch between companies efficiently

```
SA login
  System: detects SA belongs to 3 companies
  System: shows company selector dropdown
  ↓
  SA selects: "Công ty ABC"
  [System]: g.request.company_id = ABC UUID
  SA: sees ABC's invoices, partners, vouchers only
  ↓
  SA clicks company selector
  Selects: "Công ty XYZ"
  [System]: g.request.company_id = XYZ UUID
  SA: sees XYZ's data only (ABC data invisible)
  ↓
  Concurrent audit trail:
    - ABC actions logged with ABC context
    - XYZ actions logged with XYZ context
    - Cross-company access attempts: 403 COMPANY_NOT_AUTHORIZED
```

---

## Journey 06: Negative Path — Duplicate MST Registration

**Persona:** Admin attempting to register already-registered company

```
[A] Accesses setup wizard
  Enters MST: "0123456789" (already used by another entity)
  ↓
[System]: TaxId("0123456789") → valid format ✓
[System]: duplicate check: SELECT 1 FROM companies WHERE mst = "0123456789"
  → EXISTS
  ↓
System: 409 MST_TAKEN
{ "error": "MST_TAKEN",
  "message": "Mã số thuế 0123456789 đã được đăng ký cho Công ty XYZ. Vui lòng kiểm tra lại." }
  ↓
[A] realizes: data entry error; enters corrected MST: "0123456798"
System: 201 Created ✓
```