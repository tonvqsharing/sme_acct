# Data Flows — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-19 |

DF diagrams + flows.

---

## DF-1 VAT rate config change flow (CompanyConfig → DB → Audit)

```
Request: PATCH /api/v1/system_settings/config
  │
  ▼
JSON body: {flag_name: "vat_rates", new_value: {0, 5, 10}, actor: <UUID>, reason: "..."}
  │
  ▼
SystemSettingsService.update_config()
  │
  ├─ Validates actor UUID
  │
  ├─ Validates flag_name exists on CompanyConfig
  │
  ├─ If flag in _LAW_TYPE_FIELDS: raises FlagLockedError
  │    (unless migration patch already applied — tracked separately)
  │
  ├─ If flag in _CONFIG_TYPE_FIELDS: allows with 2nd approval enforcement at API layer
  │
  ├─ setattr(config, field, value)
  │
  ├─ validate_vat_rate(config.vat_rates) → if invalid → InvalidRegimeError
  │
  ├─ config.updated_by = actor; config.config_version += 1
  │
  ├─ repo.update_config(config) → DB UPDATE
  │
  ├─ audit_log write: entity="CompanyConfig", entity_id=config.id,
  │                  action="UPDATE", old_value=old_frozenset,
  │                  new_value=new_frozenset, actor_id=actor,
  │                  reason=<from request>, timestamp=now
  │
  ▼
Response: {success: true, config_version: new_version}
  │
  □
```

---

## DF-2 E-invoice series add flow

```
Request: POST /api/v1/system_settings/e-invoice-series
  │
  ▶ JSON body: {prefix: "HD", ca_signer: "CA001", actor: <UUID>}
  │
  ▼
SystemSettingsService.add_e_invoice_series(company_id, actor, prefix, ca_signer)
  │
  ├─ Validates actor UUID
  │
  ├─ Validates prefix: not empty, not already in config.e_invoice_series prefixes
  │
  ├─ Checks len(config.e_invoice_series) >= 15
  │    → raises SystemSettingsError("Đã đạt giới hạn 15 series...")
  │
  ├─ Creates EInvoiceSeries(prefix=prefix, next_sequence=1, active=True,
  │    ca_signer=ca_signer)
  │
  ├─ config.e_invoice_series = frozenset(list(...) + [new_series])
  │
  ├─ config.updated_by = actor; config.config_version += 1
  │
  ├─ repo.update_config(config) → DB INSERT/UPDATE
  │
  ├─ CONFIG-type flag → triggers 2nd-approval workflow:
  │    1. First approval recorded (ADMIN or CHIEF_ACCOUNTANT)
  │    2. CHIEF_ACCOUNTANT must approve via API before applied
  │
  ├─ audit_log write: entity="CompanyConfig", action="EINVOICE_SERIES_ADD",
  │                  new_series_prefix=prefix, actor_id=actor,
  │                  timestamp=now
  │
  ▼
Response: {success: true, series_prefix: prefix, series_id: <UUID>,
  pending_approval: true/false}
```

---

## DF-3 Invoice VAT calculation flow

```
InvoiceItem creation:
  │
  ▼
vat_rate selected from TaxRate enum {VAT_0(0%), VAT_5(5%), VAT_10(10%)}
  │
  ├─ line_total = round(quantity × unit_price - discount, 2)
  │
  ├─ vat_amount = round(line_total × vat_rate.value / 100, 2)
  │
  ├─ total_amount = round(line_total + vat_amount, 2)
  │
  ▼
Invoice._recalculate():
  │
  ├─ subtotal = round(sum(quantity × unit_price - discount), 2)
  │
  ├─ vat_total = round(sum(vat_amount), 2)
  │
  ├─ grand_total = round(subtotal + vat_total, 2)
  │
  └─ updated_at = date.today()
  │
  ▼
On post: system freezes: invoice.id + vat_rate per item + vat_amount per item +
  config_version at post time; stored immutably.
```

---

## DF-4 VAT rate validation flow (service-level)

```
Service: validate_vat_rate(rate)
  │
  ▼
  ├─ if rate ∉ {0, 5, 10}: raise InvalidRegimeError(
  │       f"Thuế GTGT {rate} không hợp lệ. Các mức được phép: {{0, 5, 10}}"
  │   )
  │
  ▼
  └─ return None (rate valid)
```

---

## DF-5 Audit trail flow (any mutation)

```
any mutation (VAT rate change, e-invoice series add, config update)
  │
  ▼
audit_log entry: entity, entity_id, action, actor_id,
               old_value, new_value, reason, timestamp
  │
  □
```