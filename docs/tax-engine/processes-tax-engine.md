# Processes — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-19 |

End-to-end business processes. Numbered steps; actors; systems; exit criteria.

---

## P-01 Configure VAT rates (initial / update)

**Trigger:** Business needs change VAT rates (new regime, audit finding, policy update).

1. Chief Accountant identifies needed VAT rate change (e.g., add/remove rate from {0, 5, 10}).
2. Chief Accountant submits migration request via API PATCH /api/v1/system_settings/config
   with `flag_name="vat_rates"`, `new_value={new set}`, `actor`, `reason`.
3. System validates: LAW-type flag → if migration not yet applied, raises
   `FlagLockedError` "Cơ quan quy định là hằng pháp lý, không thể thay đổi mà không có bản vá migration."
4. If migration approved: service applies change; `config_version` incremented;
   audit-logged: actor, old_value, new_value, timestamp, "migration: <reason>".
5. Exit: new `vat_rates` frozenset active; all subsequent invoices use new rates.

## P-02 Enter invoice with VAT

**Trigger:** Create sales/purchase invoice in foreign or domestic currency.

1. Accountant creates Invoice; selects currency VND (default) or FX.
2. Accountant adds InvoiceItem(s); for each item selects `vat_rate` from TaxRate enum:
   {VAT_0 (0%), VAT_5 (5%), VAT_10 (10%)}.
3. System auto-calculates `vat_amount = round(line_total × vat_rate.value / 100, 2)`
   and `total_amount = round(line_total + vat_amount, 2)`.
4. Accountant reviews original + VND amounts; confirms VAT rates correct.
5. On post: system freezes rate reference (immutable), stores TaxRate + VAT amount +
   config version; e-invoice data prepared per ND 254/2026/NĐ-CP.
6. Exit: posted invoice with dual amounts (original + VND), VAT-frozen rate.

## P-03 Add e-invoice series

**Trigger:** New e-invoice series needed (prefix change, CA signer update).

1. Chief Accountant opens Add E-Invoice Series; enters `prefix` (e.g., "HD"), `ca_signer`.
2. System validates: prefix not empty; current series count < 15.
3. If count ≥ 15 → error "Đã đạt giới hạn 15 series số HDĐ"; stop.
4. System creates EInvoiceSeries; CONFIG-type flag → 2nd approval triggered.
5. CHIEF_ACCOUNTANT approves via API; series activated; config_version incremented.
6. Exit: new series active; prefix usable on invoices; audit trail complete.

## P-04 Review tax treatment (audit)

**Trigger:** Periodic audit / regulatory inspection / internal review.

1. Auditor opens Tax Config → Tax Rates view.
2. System displays: current `vat_rates` frozenset, rate change history, config changes
   with actor + timestamp + reason.
3. Auditor filters invoices by VAT rate, period, company.
4. System shows per-invoice: serial, VAT rate per item, VAT amount, total, frozen rate ref.
5. Auditor exports report (CSV/PDF); read-only; no mutation possible.
6. Exit: audit opinion supported; no anomalies if rates match config + law.

---

## Process dependencies

```
P-01 ──► P-02 ──► P-03 ──► P-04
```

---

## Actors per process

| Process | Admin | Accountant | Chief Acct | Auditor |
|---|---|---|---|---|
| P-01 | ✓ (migration) | — | ✓ (approve/rate set) | — |
| P-02 | — | ✓ | — | — |
| P-03 | — | — | ✓ (approve series) | — |
| P-04 | — | — | — | ✓ (read) |