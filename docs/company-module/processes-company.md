# Processes: Company Module

---

## P-01: Company Setup Process

**Trigger:** New customer onboarded; system first-run detected

```
[External] Business Registration Office issues ĐKKD
  ↓
[A] Accesses system — no companies exist
  ↓
[System] Shows setup wizard at /companies/new
  ↓
[CA] Enters company legal info:
    ├── legal_name (from ĐKKD)
    ├── MST (validated: ^\d{10}$ or \d{10}-\d{3}$)
    ├── headquarters_address
    ├── legal_representative
    ├── business_reg_number + business_reg_date
    └── business_fields (NACE codes from ĐKKD)
  ↓
[System] Validates: all mandatory fields present, MST unique in DB
  ↓
[CA] Selects company_type:
    ├── SINGLE_LLC / MULTI_LLC / JSC / SOLE_PROP / PARTNERSHIP / HOUSEHOLD / COOP
  ↓
[System] Auto-derives:
    ├── accounting_regime (TT99 default; TT58 for HOUSEHOLD)
    └── required_BHXH registration flag
  ↓
[CA] Enters accounting info:
    ├── fiscal_year_start_month/day
    ├── responsible_accountant_name + MSKHMN license
    └── tax_agency + controlling_tax_office
  ↓
[CA] Enters BHXH (if required):
    ├── bhxh_code + bhxh_agency
  ↓
[CA] Enters operational info:
    ├── phone, email, website
    ├── bank_accounts list (primary + optional)
    └── short_name (trading name)
  ↓
[System] Creates Company record:
    ├── config_version=1
    ├── status=ACTIVE
    ├── is_active=True
    └── legal_reviewed_at = NULL (pending)
  ↓
[CA] Stamps: POST /companies/{id}/legal-review
  ↓
[System] Sets legal_reviewed_at, legal_reviewed_by
  ↓
[System] Emits COMPANY_CREATED + LEGAL_REVIEW_STAMPED audit events
  ↓
[System] Creates CompanyConfig (from system-settings)
  ↓
[COMPANY_ACTIVE] — Ready for invoice/voucher/partner creation
```

**Exit criteria:** Company record in DB; legal_reviewed_at not null; CompanyConfig exists; 3-entry smoke test passes.

---

## P-02: Company Info Change Process (Mẫu 12 Simulation)

**Trigger:** Legal representative changes, name change, address change, MST change, capital change

```
[A/CA] Identifies change needed
  ↓
[System] Classifies change:
    ├── RESTRICTED (legal_name, MST, company_type, business_reg_number)
    │   └── → Requires external re-registration
    └── NON-RESTRICTED (phone, email, short_name, bank_accounts)
        └── → In-system update only
  ↓
[RESTRICTED PATH]:
  [CA] Files Mẫu số 12 with DPI/Sở KH&ĐT
  [CA] Receives confirmation + new ĐKKD
  [CA] Submits: PATCH /companies/{id} with change reason + reference
  [System] Validates: change is RESTRICTED → requires legal_review stamp
  [System] For MST change specifically:
      ├── Creates MST_CHANGE_PENDING record
      ├── Sets mst_changed_at = proposed effective date
      ├── Backfills future-dated documents with new MST
      └── Archives old MST for historical document integrity
  [System] Emits COMPANY_INFO_CHANGED audit event
[NON-RESTRICTED PATH]:
  [Admin] Submits PATCH directly
  [System] Updates; config_version++; emits audit event
  ↓
[System] NOTIFIES:
    ├── Tax authority (if MST/legal_name changed) — future API
    ├── BHXH agency (if address/legal_rep changed)
    └── Bank (if bank_accounts changed)
  ↓
[System] Marks documents from effective_date onward with new info
  ↓
[Historical records preserved] — WORM; unchanged
```

---

## P-03: Company Deactivation / Dissolution Process

**Trigger:** Company ceases operations (temporary suspension or permanent dissolution)

### Suspend (temporary)
```
[CA] Requests: POST /companies/{id}/suspend
  ↓
[System] Pre-checks:
    ├── All periods locked (PeriodLock query)
    ├── No DRAFT invoices/vouchers
    └── No open consolidation runs (if multi-company)
  ↓
[System] Sets status=SUSPENDED, is_active=False
  ↓
[System] Emits COMPANY_SUSPENDED audit event
  ↓
[All SA attempts to create invoice/voucher → 403 COMPANY_SUSPENDED]
  ↓
[CA] May reactivate later: POST /companies/{id}/reactivate
  ↓
[System] Sets status=ACTIVE, is_active=True
  ↓
[System] Emits COMPANY_REACTIVATED audit event
```

### Dissolve (permanent)
```
[CA] Requests: POST /companies/{id}/dissolve
  ↓
[System] Pre-checks (stricter than suspend):
    ├── ALL periods locked (all-time, not just current)
    ├── Zero DRAFT journals for all time
    ├── All tax returns filed per GDT (future API check)
    ├── All BHXH settled
    └── Retention archive completed (documents to WORM storage)
  ↓
[CHIEF_ACCOUNTANT only]: additional authorization
  ↓
[System] Sets status=DISSOLVED, is_active=False
  ↓
[System] Emits COMPANY_DISSOLVED audit event
  ↓
[System] Freezes all data — read-only archive mode
  ↓
[Legal team]: company record retained ≥10 years (LKT 2015)
```

---

## P-04: Fiscal Year Boundary Process

**Trigger:** Fiscal year end; period close

```
[CA] Determines fiscal year boundary from fiscal_year_start_month/day
  ↓
[System] Derives:
    fiscal_year = date.year if date.month >= fiscal_year_start_month
                  else date.year - 1
    accounting_period = (date.month - fiscal_year_start_month + 12) % 12 + 1
  ↓
[CA] Locks period (from period-lock module)
  → System checks: company.status = ACTIVE
  → Period lock scoped by company_id
  ↓
[After FYEAR_CLOSED]:
  [System] Prevents company_type change
  [System] Prevents fiscal_year_start change
  [System] Archives full year data to WORM
  ↓
[New fiscal year]:
  [System] Auto-creates opening entries from prior year close
  [System] Preserves company settings (legal_name, MST unchanged unless changed)
```

---

## P-5: MST Validation at Company Creation

**Trigger:** CA enters MST during setup

```
[CA] Enters MST = "0123456789-123"
  ↓
[Domain] TaxId value object construction:
    ├── Checks regex: ^\d{10}(-\d{3})?$
    ├── Checks not all same digit
    └── Checks length (10 or 13)
  ↓
[Service] CompanyService.create():
    ├── Checks MST uniqueness: SELECT 1 FROM companies WHERE mst=?
    └── IF EXISTS → DuplicateMSTError (409)
  ↓
[Future: External API check against GDT database]
  ↓
[System] Persists Company with validated MST
```

---

## P-06: Audit Trail — Company Change History

**Trigger:** Any company info change, status change, MST change, legal review

```
[Any authorized user] Performs company change
  ↓
[Service] BEFORE mutation:
    ├── Captures before state (full company JSON)
    ├── Creates AuditLogEntry:
    │     ├── action = COMPANY_UPDATED / COMPANY_SUSPENDED / MST_CHANGED / etc.
    │     ├── entity_type = "Company"
    │     ├── entity_id = company.id
    │     ├── before_value = JSON snapshot
    │     └── after_value = pending (will fill after)
    └── Emits to AuditLogService.emit()
  ↓
[Service] Performs DB UPDATE on companies
  ↓
[Service] AFTER commit:
    └── Updates AuditLogEntry.after_value = new state
  ↓
[System] Config changes also logged in config_changes
  ↓
[Background] Companies with any MST_CHANGED event flagged for annual legal review
```

---

## P-07: Tenant Isolation (Application Layer)

**Trigger:** Every incoming HTTP request (future multi-company)

```
[API Request arrives]
  ↓
[Auth Middleware]: Authenticates user → user_id
  ↓
[TenantMiddleware]: resolve_company(request)
    ├── Source 1: subdomain (abc.sme.vn → company_id from subdomain map)
    ├── Source 2: X-Company-ID header
    └── Source 3: user's default_company_id from user record
  ↓
[TenantService.check_access(user_id, company_id)]
    └── Verifies user has role in company (future: user_company join table)
  ↓
[g.request.company_id] = resolved_company_id
  ↓
[All repo queries scoped by company_id]:
    PartnerRepository.list() → WHERE company_id = :cid
    InvoiceRepository.list() → WHERE company_id = :cid
    VoucherRepository.list() → WHERE company_id = :cid
  ↓
[Result]: User only sees data for their company
```

**v1 shortcut:** Single company per deployment → skip tenant middleware; derive company_id from config.