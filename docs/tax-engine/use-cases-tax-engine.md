# Use Cases — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-19 |

Format: each UC has Description, Preconditions, Actors, Main flow (happy path),
Alternative flows, Exception paths.

---

## UC-01 Configure VAT rates for company

- **Actors:** Chief Accountant (primary), Admin (with migration)
- **Preconditions:** Company exists; actor provided; LAW-type flag immutable note read.
- **Main flow:**
  1. User opens Tax Config → VAT Rates.
  2. System shows current `vat_rates` frozenset: {0, 5, 10}.
  3. Chief Accountant requests rate change via API PATCH /api/v1/system_settings/config;
     provides `flag_name="vat_rates"`, `new_value={0, 5}` (example), `actor`, `reason`.
  4. System validates: LAW-type flag → raises `FlagLockedError` if attempting change
     without migration; if migration approved, change allowed with documented reason.
  5. System audit-logs change: actor, old_value, new_value, timestamp, reason.
  6. Success: new `vat_rates` displayed; config_version incremented.
- **Alternative A1 (migration):** Admin requests migration patch; after migration, LAW flag
  becomes changeable; 2nd approval (CHIEF_ACCOUNTANT) required.
- **Alternative A2 (no change):** User closes screen; no changes applied.
- **Exception E1 (invalid rate):** Rate outside {0, 5, 10} → 400, "Thuế GTGT {rate} không hợp lệ.
  Các mức được phép: {0, 5, 10}".
- **Exception E2 (no actor):** → 400, "actor is required".
- **Exception E3 (migration not done):** → 403, "Cơ quan quy định là hằng pháp lý, không thể thay đổi
  mà không có bản vá migration."

## UC-02 Enter invoice with VAT

- **Actors:** Accountant
- **Preconditions:** Company config vat_rates set; currency = VND (or FX with exchange_rate).
- **Main flow:**
  1. User creates Invoice; selects currency VND (default) or FX.
  2. User adds InvoiceItem(s); for each item, selects `vat_rate` from TaxRate enum:
     {VAT_0 (0%), VAT_5 (5%), VAT_10 (10%)}.
  3. System auto-calculates `vat_amount = round(line_total × vat_rate.value / 100, 2)`
     and `total_amount = round(line_total + vat_amount, 2)`.
  4. User reviews original + VND amounts; posts invoice.
  5. System freezes rate reference (immutable after post), stores TaxRate + VAT amount.
- **Alternative A1 (no rate):** System defaults to VAT_10 (10%); user can change.
- **Exception E1 (invalid vat_rate):** Rate not in TaxRate enum → 400, "Tỷ lệ thuế không hợp lệ.
  Chọn VAT_0, VAT_5 hoặc VAT_10".
- **Exception E2 (vat_rate not in config):** If company's `vat_rates` frozenset excludes the
  selected rate → 409, "Mã thuế không thuộc cấu hình company. Cấu hình lại vat_rates".
- **Exception E3 (unbalanced):** Invoice items don't balance → Recalc triggered; if still
  unbalanced after recalc, 422 error.

## UC-03 Add e-invoice series

- **Actors:** Chief Accountant (primary), Admin (secondary 2nd approval)
- **Preconditions:** Company config exists; actor provided; prefix valid; CA signer info.
- **Main flow:**
  1. User opens Add E-Invoice Series; enters `prefix` (e.g., "HD"), `ca_signer` (e.g.,
   "CA001").
  2. System validates: prefix not empty, max 15 active series per company.
  3. System checks current series count: if ≥ 15 → 400, "Đã đạt giới hạn 15 series số HDĐ".
  4. User submits; system creates EInvoiceSeries with prefix, next_sequence=1, active=True,
     ca_signer; audit-logs actor + timestamp.
  5. CONFIG-type flag → 2nd approval triggered: CHIEF_ACCOUNTANT must approve via API.
  6. After approval: series activated; config_version incremented; audit-logged.
- **Alternative A1 (partial):** User adds series with admin-only mode (bypasses 2nd approval
  only if LAW-flag config change, but e-invoice series is CONFIG-type, so always needs 2nd).
- **Exception E1 (prefix exists):** → 409, "Tên series đã tồn tại".
- **Exception E2 (at limit 15):** → 400, "Đã đạt giới hạn 15 series số hóa đơn điện tử.active".
- **Exception E3 (no actor):** → 400, "actor is required".
- **Exception E4 (CA signer missing):** → 400, "CA signer là bắt buộc cho series hóa đơn".

## UC-04 Validate VAT rate on invoice post

- **Actors:** Accountant (initiates), Chief Accountant (approves if config change needed)
- **Preconditions:** Invoice with items has VAT rates; company config vat_rates set.
- **Main flow:**
  1. Accountant attempts to post invoice.
  2. System validates each item's `vat_rate` ∈ TaxRate enum {0, 5, 10}.
  3. System validates each `vat_amount = round(line_total × vat_rate.value / 100, 2)` is
     consistent (no manual override that diverges from formula).
  4. System checks: if any item's rate ∉ company's `vat_rates` frozenset → 409,
     "Mã thuế {rate} không thuộc cấu hình vat_rates của công ty {current_config}".
  5. If all valid → invoice posted; audit-logged with rate per item.
- **Alternative A1 (rate outside config):** User must first configure VAT rates (UC-01) to
  include the needed rate, then re-post.
- **Exception E2 (rate 8% used but config only has 0/5/10):** → 409, "Thuế suất 8% hiện chưa
  hỗ trợ trong v1. Cập nhật cấu hình hoặc sử dụng mức 10% tạm thời."

---

---

## UC-05 Review tax treatment (Auditor)

- **Actors:** Auditor (read), Chief Accountant (read), Accountant (read)
- **Preconditions:** Invoices exist with VAT; company config vat_rates set.
- **Main flow:**
  1. Auditor opens Tax Config → Tax Rates view.
  2. System displays: current `vat_rates` frozenset, rate history, config changes with
     actor, timestamp, reason.
  3. Auditor filters invoices by VAT rate, period, company.
  4. System shows: invoice serial, VAT rate per item, VAT amount, total, frozen rate ref.
  5. Auditor exports report (CSV/PDF); read-only, no mutation possible.
- **Alternative A1 (no data):** Empty state: "Chưa có dữ liệu thuế cho kỳ này".
- **Exception E1 (no permission):** → 403, "AUDITOR chỉ đọc được; không thể sửa cấu hình thuế".

---

---

**Coverage matrix vs BRD**

| UC | BR |
|---|---|
| UC-01 | BR-01, BR-06 |
| UC-02 | BR-03, BR-05 |
| UC-03 | BR-06 |
| UC-04 | BR-05 |
| UC-05 | BR-06 |