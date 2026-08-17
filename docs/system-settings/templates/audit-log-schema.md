# Template: Audit Log Event Schema (WORM)

Canonical event types. System enforces enum constraint at DB level.

---

## Event Types Catalog

| event_type | Severity | Actor | Trigger | Retention |
|-----------|---------|-------|---------|-----------|
| CONFIG_CREATED | INFO | ACCOUNTANT | Company setup completion | ≥10y |
| CONFIG_UPDATED | WARN | ADMIN, ACCOUNTANT | CONFIG flag PATCH | ≥10y |
| CONFIG_LOCKED (LAW-flag attempted) | CRITICAL | ADMIN | LAW-type flag PATCH attempt | ≥10y |
| PERIOD_LOCKED | INFO | ACCOUNTANT | Period close | ≥10y |
| PERIOD_UNLOCKED | CRITICAL | CHIEF_ACCOUNTANT | Period re-open after lock | ≥10y |
| FYEAR_CLOSED | CRITICAL | CHIEF_ACCOUNTANT | Fiscal year close | ≥10y (indefinite for listed companies) |
| LEGAL_REVIEW_STAMPED | INFO | CHIEF_ACCOUNTANT | Legal review stamp | ≥10y |
| INVOICE_ISSUED | INFO | ACCOUNTANT, SYSTEM | Invoice creation | ≥10y |
| INVOICE_CANCELLED | WARN | ACCOUNTANT | Invoice cancel/replace | ≥10y |
| INVOICE_SERIES_ADDED | INFO | ADMIN | New series created | ≥10y |
| INVOICE_SERIES_DEACTIVATED | WARN | ADMIN | Series inactivated | ≥10y |
| VOUCHER_POSTED | INFO | ACCOUNTANT, POSTER | Voucher posted | ≥10y |
| VOUCHER_LOCKED | INFO | SYSTEM | Period lock cascade | ≥10y |
| VOUCHER_DELETE_ATTEMPTED | CRITICAL | ANY | Delete attempted on locked voucher | ≥10y |
| TAX_EXPORT | INFO | ACCOUNTANT | Tax data export | 10y (VAT) / 10y (CIT) |
| FLAG_VIOLATION | WARN | SYSTEM | User attempted invalid value for LAW flag | ≥10y |
| AUDITOR_EXPORT | INFO | AUDITOR | Full data export for external audit | ≥10y |
| LEGAL_CONSTANT_UPDATE | CRITICAL | SYSTEM | System patch updates lawyer constant | ≥10y |
| BACKUP_COMPLETED | INFO | SYSTEM | Backup job | 1 cycle |
| BACKUP_FAILED | CRITICAL | SYSTEM | Backup job failure | ≥1 cycle |
| LEGAL_REVIEW_VIOLATION | WARN | SYSTEM | Config fails legal review checklist | ≥10y |
| USER_ACCESS_CHANGE | INFO | ADMIN | RBAC change | ≥10y |
| USER_ACCESS_REVIEW_COMPLETE | INFO | ADMIN, ACCOUNTANT | Quarterly UAR sign-off | ≥10y |
| PASSWORD_CHANGED | INFO | USER | Self-service password change | 10y |
| MFA_ENABLED_DISABLED | WARN | USER, ADMIN | MFA toggle | ≥10y |
| SO_D_VIOLATION | CRITICAL | SYSTEM | Attempt to perform incompatible 2 SoD roles | ≥10y |
| PERIOD_LOCK_BREACH_ATTEMPT | CRITICAL | ANY | Failed attempt to enter invoice after lock | ≥10y |
| SYSTEM_ERROR | ERROR | SYSTEM | Unhandled exception in settings service | ≥10y |

---

## Audit Log JSON Schema (before_value / after_value for CONFIG_UPDATED)

```json
{
  "timestamp": "2026-07-15T14:23:00Z",
  "config_version": 4,
  "changed_flag": "vat_settlement_cycle",
  "flag_type": "CONFIG",
  "before": "monthly",
  "after": "quarterly",
  "change_reason": "Opted quarterly filing per tax authority notification",
  "approved_by": "ca_user_uuid",
  "actor_role": "admin",
  "ip_address": "203.162.4.22",
  "user_agent": "Mozilla/5.0...",
  "legal_reviewed": false,
  "requires_tax_authority_notification": true
}
```