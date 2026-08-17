# Template: Unit Test Plan — System Settings Module

---

## Coverage Target

- Domain: 95%+ (value objects, entities)
- Service: 90%+ (all exception paths)
- API: 80%+ (happy + exception paths)
- Integration: P0 paths covered

---

## Test Suite Structure

```
tests/unit/system_settings/
├── test_company_config_entity.py
├── test_flag_validation.py
├── test_system_settings_service.py
├── test_period_lock_service.py
├── test_audit_log_service.py
├── test_e_invoice_series.py
└── conftest.py

tests/integration/system_settings/
├── test_system_settings_api.py
├── test_period_lock_enforcement.py
├── test_config_audit_log.py
└── conftest.py
```

---

## Critical Test Cases

### test_company_config_entity.py

| Test | Scenario | Expected |
|------|---------|----------|
| `test_valid_init` | All mandatory fields valid | CompanyConfig created |
| `test_invalid_mst` | tax_id_pattern invalid | ValueError |
| `test_invalid_retention` | data_retention_years=5 | ConfigValidationError |
| `test_invalid_decimal_places` | decimal_places=1 | ConfigValidationError |
| `test_invalid_vat_rates` | vat_rates contains 7 | InvalidVATRateError |
| `test_law_flag_update_rejected` | update_flag(tax_id_pattern, ...) | FlagLockedError |
| `test_config_version_incremented` | update_flag with matching version | version += 1 |
| `test_config_version_conflict` | update_flag with stale version | ConfigVersionConflict (409) |

### test_period_lock_service.py

| Test | Scenario | Expected |
|------|---------|----------|
| `test_lock_open_period` | CA locks open period | PeriodLock record created |
| `test_lock_already_locked` | Second CA locks same period | IntegrityError (unique constraint) |
| `test_post_to_locked_period_raises` | is_period_locked=True | AccountingPeriodLockedError |
| `test_close_fyear_admin_not_sufficient` | Admin (not CA CFO) tries FY_CLOSE | ForbiddenError |
| `test_fyear_close_irreversible` | FY_CLOSE without migration | Cannot re-open; locked period blocks |
| `test_fiscal_year_for_date_apr_start` | date=2026-05-15, start=Apr1 | fiscal_year=2026, period=2 |

### test_audit_log_service.py

| Test | Scenario | Expected |
|------|---------|----------|
| `test_emit_writes_row` | emit() called with valid event | INSERT succeeds |
| `test_delete_revoked` | Attempt DELETE FROM audit_log | PermissionError (REVOKE DELETE) |
| `test_created_at_db_side` | before/after stored with DB now() | created_at != app time (test DB sync) |
| `test_export_full_range` | list_for_export(range) | All events in range returned |

### test_e_invoice_series.py

| Test | Scenario | Expected |
|------|---------|----------|
| `test_series_created_successfully` | POST /invoice-series | created, next_seq=1 |
| `test_sequence_advances_atomically` | advance_series → returns 1 then 2 | Never returns duplicate |
| `test_max_series_enforced` | 16th POST attempt | 422 MAX_SERIES_EXCEEDED |
| `test_series_deactivated` | PATCH active=false | inactive but history preserved |
| `test_duplicate_prefix` | Same prefix for same company | 422 DUPLICATE_SERIES |