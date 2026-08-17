# Workflows: Company Module

---

## WF-01: Company Creation Workflow

```
States: (none) → LEGAL_INFO_ENTERED → REGIME_CONFIGURED → ACCOUNTING_CONFIGURED → REVIEWED → ACTIVE

  [CA accesses system first time]
    [none]
    └── Enters legal info (legal_name, MST, address, legal_rep)
      └── MST validated: TaxId format ✓
      └── MST uniqueness checked ✓
    [LEGAL_INFO_ENTERED]
    └── Selects company_type
    └── System derives accounting_regime from type:
          ├── HOUSEHOLD → TT58_MICRO
          ├── SOLE_PROP, LLC, JSC → TT99
          └── LISTED_JSC → TT99 + quarterly flag
    [REGIME_CONFIGURED]
    └── Enters fiscal_year_start (1/1 or 4/1)
    └── Enters responsible_accountant_name + MSKHMN
    └── Enters tax_agency, controlling_tax_office
    └── Enters BHXH code (if required)
    [ACCOUNTING_CONFIGURED]
    └── Enters bank accounts
    └── Enters short_name (trading name)
    └── CA confirms legal review
    [REVIEWED]
    └── legal_reviewed_at, legal_reviewed_by stamped
    [ACTIVE]
      └── Company can create invoices, vouchers, partners
      └── CompanyConfig created
```

---

## WF-02: MST Change Workflow

```
States: ACTIVE → MST_CHANGE_REQUESTED → MT_PENDING → NEW_MST_ACTIVE

  [CA detects MST change needed (merger, correction)]
  [ACTIVE]
    └── Files Mẫu 47 with GDT
    └── Receives: new_mst = "9876543210", effective_date = "2026-09-01"
    └── Submits: POST /companies/{id}/change-mst
          ├── new_mst: "9876543210"
          ├── gdt_notification_ref: "MT-2026-0089"
          └── effective_date: "2026-09-01"
  [MST_CHANGE_REQUESTED]
    └── System validates:
          ├── new_mst format ✓
          ├── new_mst uniqueness ✓
          └── GDT reference present ✓
    └── System sets mst_changed_at = effective_date
    └── System: emits MST_CHANGED audit event (old_mst=0123, new_mst=9876)
  [MT_PENDING] (awaiting effective date)
    └── Pre-effective date: old MST still used
    └── Effective date reached:
  [NEW_MST_ACTIVE]
    └── System: batch updates future invoices with new MST
    └── System: new documents use new MST
    └── Historical documents: preserve old MST (WORM)
```

---

## WF-03: Company Suspension Workflow

```
States: ACTIVE → SUSPENSION_REQUESTED → VALIDATING → SUSPENDED → (REACTIVATE)

  [CA determines company needs temp suspension]
  [ACTIVE]
    └── Submits: POST /companies/{id}/suspend
  [SUSPENSION_REQUESTED]
    └── System validates:
          ├── CHIEF_ACCOUNTANT role ✓
          ├── All periods locked ✓
          ├── No DRAFT invoices/vouchers ✓
          └── No open consolidation runs ✓
    [VALIDATING]
      └── All checks pass → status = SUSPENDED, is_active = FALSE
  [SUSPENDED]
    └── All new invoices/vouchers rejected with COMPANY_SUSPENDED (403)
    └── Existing data readable (auditors, CA can still view)
    └── SA cannot create any transactions
  [REACTIVATION]:
    └── CA: POST /companies/{id}/reactivate
    └── System sets status=ACTIVE, is_active=True
    └── System: emits COMPANY_REACTIVATED audit event
```

---

## WF-04: Company Field Change Lifecycle

```
States: DRAFT → VALIDATING → PENDING_EXTERNAL → AWAITING_CONFIRMATION → APPLIED

  [Admin requests change to RESTRICTED field: legal_name]
  [DRAFT]
    └── Submits: PATCH with legal_name + change_reason + mẫu_12_ref
  [VALIDATING]
    └── System checks: Mẫu 12 reference valid?
    └── System creates COMPANY_CHANGE_REQUEST audit record
    └── System marks: pending_external_confirmation = TRUE
  [PENDING_EXTERNAL]
    └── [External] DPI processes Mẫu 12
    └── [Future] API callback from dichvucong.gov.vn confirms
    └── [Manual] CA uploads confirmation scan
    [AWAITING_CONFIRMATION]
      └── System waits for confirmation
  [APPLIED]
    └── Upon confirmation:
        ├── UPDATE legal_name
        ├── UPDATE before/after in audit log
        ├── Invalidate cache
        └── Notify downstream (e-invoice templates, tax filing)
```

---

## WF-05: Fiscal Year Boundary Determination (Automated)

```
States: ANY_DATE → FY_DERIVED → PERIOD_SCOPED

  [System receives: any date (invoice issue_date, voucher_date)]
  [ANY_DATE]
    └── [TenantService] get_fiscal_year_for_date(company_id, date)
        ├── Read company.fiscal_year_start_month, fiscal_year_start_day
        ├── Calculate:
        │   fiscal_year = date.year if date.month >= fym
        │                 else date.year - 1
        │   accounting_period = (date.month - fym + 12) % 12 + 1
        └── Return: fiscal_year, accounting_period
  [FY_DERIVED]
    └── Used by:
          ├── InvoiceService (period lock check)
          ├── VoucherService (period lock check)
          ├── Tax service (declaration period)
          └── Reporting (BCTC period)
    [PERIOD_SCOPED]
```

**Edge cases:**
- Fiscal year start = 4/1, date = 2026-03-31 → fiscal_year=2025, period=12
- Fiscal year start = 4/1, date = 2026-04-01 → fiscal_year=2026, period=1

---

## WF-06: Tenant Access Control (Multi-Company)

```
States: UNAUTHENTICATED → AUTHENTICATED → COMPANY_RESOLVED → ACCESS_GRANTED

  [HTTP Request]
  [UNAUTHENTICATED]
    └── [AuthMiddleware] validate JWT
    [AUTHENTICATED]
      └── user_id = "user-uuid"
      └── [TenantMiddleware] resolve_company(request)
          ├── Try X-Company-ID header
          ├── Try subdomain mapping
          └── Fallback: user.default_company
      [COMPANY_RESOLVED]
        └── company_id = "resolved-uuid"
        └── [TenantService.check_access(user_id, company_id)]
            ├── Future: SELECT 1 FROM user_companies WHERE user_id=? AND company_id=?
            └── v1: always TRUE (single company)
        [ACCESS_GRANTED]
          └── All subsequent repo queries: WHERE company_id = :cid
```

**Security invariant:** No request can reach InvoiceService, VoucherService, PartnerService without g.request.company_id set. Raise `CompanyContextRequiredError` if missing.