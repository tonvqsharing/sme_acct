# Template: Test Plan — Company Module

## Test Suite Structure

```
tests/unit/company/
├── test_company_entity.py
├── test_company_service.py
├── test_tenant_service.py
└── conftest.py

tests/integration/company/
├── test_company_api.py
├── test_tenant_isolation.py
└── conftest.py
```

---

## Critical Test Cases

### test_company_entity.py

| Test | Scenario | Expected |
|------|----------|----------|
| `test_valid_company_creation` | All mandatory fields valid | Company entity created |
| `test_mst_format_invalid_10_digit_wrong` | MST = "012345678" (9 digits) | ValueError from TaxId |
| `test_mst_format_branch_suffix` | MST = "0123456789-001" | Valid (branch code) |
| `test_mst_alphanumeric` | MST = "01234ABC89" | ValueError |
| `test_legal_name_empty` | legal_name = "" | CompanyValidationError |
| `test_company_type_invalid` | company_type = "invalid" | InvalidCompanyTypeError |
| `test_fiscal_year_month_out_of_range` | fiscal_year_start_month = 13 | ValueError |
| `test_fiscal_year_day_invalid_for_feb` | month=2, day=30 | ValueError |
| `test_household_skip_bhxh` | company_type=HOUSEHOLD, bhxh_code=None | Valid (optional) |
| `test_llc_requires_bhxh` | company_type=LLC, bhxh_code=None | CompanyValidationError |

### test_company_service.py

| Test | Scenario | Expected |
|------|----------|----------|
| `test_create_company_success` | Valid data | Company created; COMPANY_CREATED audit event |
| `test_create_duplicate_mst` | MST already in system | DuplicateMSTError (409) |
| `test_mst_cannot_change_after_invoices` | Company has invoices, PATCH mst | MST_CHANGE_BLOCKED (409) |
| `test_company_type_change_requires_rereg` | PATCH company_type without Mẫu 12 | LEGAL_CHANGE_REQUIRES_REREGISTRATION (422) |
| `test_suspend_with_open_periods` | PATCH suspend when periods open | COMPANY_HAS_OPEN_PERIODS (409) |
| `test_deactivate_with_draft_invoices` | DRAFT invoices exist | 422: "Có chứng từ chưa đăng sổ" |
| `test_dissolve_requires_closed_fyear` | Not all periods closed | 409 |
| `test_legal_review_stamp` | POST legal-review | legal_reviewed_at set |
| `test_update_without_auth` | No ADMIN role | 403 |
| `test_optimistic_lock_conflict` | config_version mismatch | 409 |
| `test_mst_change_with_invoices_posted` | Invoices exist with old MST | rejected |

### test_tenant_service.py

| Test | Scenario | Expected |
|------|----------|----------|
| `test_resolve_from_header` | X-Company-ID header present | company_id from header |
| `test_resolve_from_subdomain` | subdomain abc.sme.vn | company_id from mapping |
| `test_resolve_default` | No header/subdomain | user.default_company_id |
| `test_scope_query_appends_cid` | Query list invoices | WHERE company_id = :cid appended |
| `test_cross_company_blocked` | User A tries to access Company B | 403 COMPANY_NOT_AUTHORIZED |
| `test_missing_company_context` | No company_id in request | CompanyContextRequiredError |

---

## Integration Test: Company Setup → Invoice Flow

```
1. POST /companies with valid data → 201 Created
2. GET /companies/{id} → returns company
3. POST /config/legal-review → 200 stamped
4. POST /partners with company_id → 201
5. POST /invoices with company_id + partner_id → 201
6. GET /audit-log → includes COMPANY_CREATED + INVOICE_ISSUED events
7. GET /invoices → returns only this company's invoices
```

---

## Regression Test Guardrails

- [ ] All existing tests pass after adding `company_id` nullable columns
- [ ] Partner, Invoice, Voucher creation requires `company_id` (post-migration)
- [ ] Tenant scoping verified: multi-company user cannot see other companies' data