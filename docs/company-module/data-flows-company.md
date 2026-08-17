# Data Flow Diagrams: Company Module

---

## DFD-01: Company Creation Flow

```
[CA] POST /api/v1/companies
  Body: { legal_name, mst, company_type, ... }
  ↓
[API] AuthMiddleware → ADMIN role ✓
  ↓
[API] CompanyService.create_company(**data)
  → Validate MST: TaxId(mst) → ValueError if invalid format
  → Validate required fields: legal_name, mst, address, legal_rep, company_type
  → Validate company_type in enum
  → Validate fiscal_year_start_month in 1-12, day in 1-31
  → Validate accounting_regime compatible with company_type
  → [Repository] Check MST uniqueness: SELECT 1 FROM companies WHERE mst = ?
    → EXISTS → raise DuplicateMSTError (409)
  → Build Company entity with all mandatory fields
  ↓
[Repository] INSERT INTO companies (...) VALUES (...)
  ↓
[Service] config_version = 1, status = ACTIVE
  ↓
[AuditLogService] emit(action=COMPANY_CREATED, entity_type=Company, entity_id=id, before=null, after=company_json)
  ↓
  ↓
HTTP 201 Created
{
  "id": "uuid",
  "legal_name": "Công ty TNHH ABC",
  "mst": "0123456789",
  "company_type": "multi_llc",
  "accounting_regime": "tt99",
  "status": "active",
  "legal_review_required": true
}
```

---

## DFD-02: Company Update + Legal Change (MST Change)

```
[A] PATCH /api/v1/companies/{id}
  Body: { mst: "9876543210", change_reason: "GDT issued new MST after merger", gdt_ref: "MT-2026-0089" }
  ↓
[API] AuthMiddleware → ADMIN + ACCOUNTANT roles
  ↓
[Service] CompanyService.update_company(company_id, changes, actor)
  → [Repository] SELECT * FROM companies WHERE id = :id FOR UPDATE
  → Check: is this field RESTRICTED? MST → YES
  → Check: GDT notification reference provided? → NO → raise LEGAL_CHANGE_REQUIRES_REREGISTRATION (422)
  → Check: mst format valid → TaxId("9876543210") → ValueError if invalid
  → Check: new MST uniqueness: SELECT 1 FROM companies WHERE mst = ?
  → Check: MST cannot change if invoices posted (future: via InvoiceService.count check)
  → Check: config_version matches X-Config-Version header
  ↓
[Service] BEGIN transaction:
  ├── Emit CONFIG_CHANGED to config_changes (before=mst, after=mst, actor, version)
  ├── Emit COMPANY_MST_CHANGED to audit_log (old_mst, new_mst, effective_date, gdt_ref)
  ├── UPDATE companies SET mst = :new, mst_changed_at = :eff_date, config_version = :v+1
  └── Update future-dated documents (batch job: invoices with issue_date >= effective_date)
  ↓
[Service] COMMIT
  ↓
[System] Cache invalidation (company:{id})
  ↓
HTTP 200
{ "id": "uuid", "mst": "9876543210", "mst_changed_at": "2026-09-01" }
```

---

## DFD-03: Tenant Isolation (Request Scoping)

```
[HTTP Request] GET /api/v1/invoices
  Headers: Authorization: Bearer <token>, X-Company-ID: abc-uuid
  ↓
[AuthMiddleware]
  → decode JWT → user_id = "user-uuid"
  ↓
[TenantMiddleware]
  → [TenantService.resolve_company(request)]
      → Source 1: X-Company-ID header → company_id = "abc-uuid"
      → [TenantService.check_access(user_id, company_id)]
          → Future: SELECT 1 FROM user_companies WHERE user_id=? AND company_id=?
          → v1: always allow (single company)
  → Sets g.request.company_id = "abc-uuid"
  ↓
[API Handler] InvoiceService.list_invoices()
  → [Repository] SELECT * FROM invoices WHERE company_id = :cid
  → [Result] Only ABC company's invoices returned
  ↓
[Response] [ {invoice ABC-1}, {invoice ABC-2} ]
  (Never includes other companies' invoices)
```

---

## DFD-04: Company Creation with CompanyConfig Cascade

```
[CA] POST /api/v1/companies
  ↓
[Service] CompanyService.create_company(...)
  ↓ Creates Company entity → INSERT INTO companies
  ↓
  Now create company-scoped SystemSettings:
    [Service] SystemSettingsService.init_company(
        company_id=company.id,
        accounting_regime=company.accounting_regime,
        fiscal_year_start=(month, day),
        vat_method="deduction",
        e_invoice_mode="software_cert",
        ...
    )
    ↓
    → INSERT INTO company_configs (company_id=?, accounting_regime=?, ...)
    → INSERT INTO audit_log (action=CONFIG_CREATED, company_id=?, ...)
  ↓
[Service] Both commits in single transaction
  ↓
HTTP 201 Created
{ company: {...}, config_created: true, config_version: 1 }
```

---

## DFD-05: Tenant Data Isolation (Database Level)

```
[Query execution scope — all financial queries MUST include company_id]

SELECT * FROM invoices WHERE company_id = 'ABC-uuid' AND issue_date >= '2026-01-01'
  → Returns: ABC's 2026 invoices only

SELECT * FROM vouchers WHERE company_id = 'XYZ-uuid'
  → Returns: XYZ's vouchers only

Query WITHOUT company_id:
  → APPLICATION BLOCKED at repo layer
  → TenantService raises CompanyContextRequiredError
```

**Data mapping:**
- `companies.id` (UUID) → FK in `partners.company_id`, `invoices.company_id`, `vouchers.company_id`
- All SELECT queries on financial tables append `WHERE company_id = :request_company_id`
- INSERT requires `company_id` non-null (FK + future NOT NULL constraint)

---

## Data Dictionary: Key Tables

| Table | Primary Key | Key Columns | Growth Rate | Retention |
|-------|------------|-------------|-------------|-----------|
| companies | id | mst (UNIQUE), company_type, status, accounting_regime | ~1 row per entity | V company lifetime |
| users (future) | id | company_id FK (default) | ~N per company | V |
| partners | id | company_id, code, tax_id | High per company | V |
| invoices | id | company_id, serial, invoice_number, issue_date | High per company | ≥10y |
| vouchers | id | company_id, voucher_number, status | High per company | ≥10y |

**Growth rate notes:** One company record. High-volume child tables (partners, invoices, vouchers) are scoped per company and grow proportionally to transaction volume.