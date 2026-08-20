# User Journeys — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-19 |

Role-based journeys. Emotional/practical steps; exit criteria.

---

## UJ-01 Chief Accountant configures VAT rates

1. Notices business needs VAT rate change (new regime, audit finding, policy update).
2. Opens Tax Config → VAT Rates.
3. Sees current `vat_rates` frozenset: {0, 5, 10} with note "LAW-type, immutable without migration".
4. Requests rate change via API PATCH /api/v1/system_settings/config;
   provides `flag_name="vat_rates"`, `new_value={0, 5}` (example), `actor`, `reason`.
5. System validates: LAW-type flag → FlagLockedError if migration not done;
   shows message "Cơ quan quy định là hằng pháp lý, không thể thay đổi mà không có bản vá migration."
6. If migration already applied: change accepted; config_version incremented;
   audit-logged: actor, old_value, new_value, timestamp, reason.
7. New `vat_rates` displayed; all subsequent invoices use new rates.
8. Done: VAT rates updated; compliance supported.

## UJ-02 Accountant enters invoice with VAT

1. Opens Create Invoice; selects currency VND (default) or FX.
2. Adds InvoiceItem(s); for each item selects `vat_rate` from TaxRate enum:
   {VAT_0 (0%), VAT_5 (5%), VAT_10 (10%)}.
3. System auto-calculates `vat_amount = round(line_total × vat_rate.value / 100, 2)`
   and `total_amount = round(line_total + vat_amount, 2)`.
4. Reviews original + VND amounts; confirms VAT rates correct.
5. On post: system freezes rate reference; invoice posted with dual amounts
   (original + VND), VAT-frozen rate; audit-logged.
6. Done: invoice shows both currencies + tỷ giá quy đổi; e-invoice ready (ND 254/2026).

## UJ-03 Chief Accountant adds e-invoice series

1. Opens Add E-Invoice Series; enters `prefix` (e.g., "HD"), `ca_signer` (e.g., "CA001").
2. System validates: prefix not empty; current series count < 15.
3. If count ≥ 15 → error "Đã đạt giới hạn 15 series số HDĐ"; stop.
4. System creates series; CONFIG-type flag → 2nd approval triggered.
5. Chief Accountant approves via API; series activated; config_version incremented.
6. Done: new series active; prefix usable on invoices; audit trail complete.

## UJ-04 Auditor reviews tax treatment

1. Opens Tax Config → Tax Rates view.
2. Sees current `vat_rates` frozenset, rate change history, config changes with actor,
   timestamp, reason.
3. Filters invoices by VAT rate, period, company.
4. Per-invoice: serial, VAT rate per item, VAT amount, total, frozen rate ref.
5. Exports report (CSV/PDF); read-only; no anomalies.
6. Done: audit opinion supported; no anomalies.

## UJ-05 Accountant validates VAT rate on invoice post

1. Attempts to post invoice.
2. System validates each item's `vat_rate` ∈ TaxRate enum {0, 5, 10}.
3. System validates each `vat_amount = round(line_total × vat_rate.value / 100, 2)`.
4. System checks: if any item's rate ∉ company's `vat_rates` frozenset → 409,
   "Mã thuế {rate} không thuộc cấu hình vat_rates của công ty {current_config}".
5. If all valid → invoice posted; audit-logged with rate per item.
6. If invalid → error displayed; must configure rates first (UJ-01), then re-post.

---

## Journey map (roles × stages)

| Stage | Admin | Accountant | Chief Acct | Auditor |
|---|---|---|---|---|
| VAT rate config | UJ-01 (migration) | — | UJ-01 (set rates) | — |
| Daily ops (invoice) | — | UJ-02, UJ-05 | — | — |
| Period end / audit | — | — | — | UJ-04 |
| E-invoice series | — | — | UJ-03 | — |

---

## Pain points addressed

- VAT rate hunting: system auto-resolves from TaxRate enum {0, 5, 10} — no manual lookup.
- Approval discipline: e-invoice series needs CHIEF_ACCOUNTANT 2nd approval (D9 pattern) — no rogue postings.
- Auditability: every VAT rate change, e-invoice series add, config update logged (BR-06) — auditor self-service.
- Rate freeze: posted invoice rates immutable (D8) — no silent overrides; forced reverse requires documented reason.