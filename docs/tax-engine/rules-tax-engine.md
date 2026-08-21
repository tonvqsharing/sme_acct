# Rules — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-19 |

Legal rules (hard-coded, source-cited) + Domain rules.

---

## 1. Legal rules (hard-coded, source-cited)

### R1 — VAT rates per Vietnamese law (verified 2026-08-19)

- **VAT 0%** — Xuất khẩu hàng hóa, dịch vụ quốc tế, không chịu thuế GTGT.
  Legal basis: Luật GTDD Art. 9; Thông tư 219/2013/TT-BTC.
- **VAT 5%** — Hàng hóa và dịch vụ bắt buộc (nước dùng: nước sạch, thuốc y học, sách giáo khoa,
  phân bón, pesticide). Legal basis: Luật GTDD Art. 10; Thông tư 219/2013/TT-BTC.
- **VAT 10%** — Chuẩn mực — hàng hóa và dịch vụ thường (dịch vụ thương mại, bất động sản,
  nội địa vận chuyển, v.v.). Legal basis: Luật GTDD chung.
- **8% (temporary)** — Giảm 2% từ 10% cho nhiều mặt hàng trong thời gian 01/07/2025 đến
  31/12/2026 theo Thông tư 180/2024/ND-CP; Quy định mới của Luật GTDD 48/2024/QH15.
  **Sectors excluded from 8%:** telecom, IT/software, banking/finance/insurance, real estate,
  metals/mining/petroleum, goods subject to SST.

### R2 — VAT rate invariants

- Rate must be one of {0, 5, 10} in current v1 (Temporary 8% out of scope).
- Any other rate → InvalidRegimeError, message: "Thuế GTGT {rate} không hợp lệ.
  Các mức được phép: {0, 5, 10}".

### R3 — E-invoice series limit

- Maximum 15 active e-invoice series per company per ND 254/2026/NĐ-CP.
- Attempting 16th → SystemSettingsError "Đã đạt giới hạn 15 series số hóa đơn điện tử.active".

### R4 — LAW-type flag immutability

- `vat_rates` in CompanyConfig is LAW-type — immutable without migration patch.
- Attempted change without migration → FlagLockedError
  "Cơ quan quy định là hằng pháp lý, không thể thay đổi mà không có bản vá migration."
- Change requires: documented reason + migration + 2nd approval (CHIEF_ACCOUNTANT).

### R5 — 2nd approval pattern for CONFIG-type

- CONFIG-type flag changes (e.g., e-invoice series prefix, CA signer) require:
  1. Request by actor (ADMIN or CHIEF_ACCOUNTANT).
  2. First approval recorded.
  3. Second approval by CHIEF_ACCOUNTANT.
  4. Change applied; config_version incremented; audit-logged.

### R6 — VAT amount calculation formula

- `VAT amount = round(line_total × rate / 100, 2)` where rate ∈ {0, 5, 10}.
- Rounding implied at 0.01 VND tolerance (matching Voucher.post() rule D6).
- Formula immutable after invoice post (rate frozen).

### R7 — Invoice VAT frozen after post

- Once invoice is posted, `vat_rate` and `vat_amount` on each item are immutable.
- Any change requires reversing (UC-05 in currencies module pattern) and re-applying.

### R8 — AUDITOR read-only backend enforcement

- All API mutations require `@login_required + current_user.role` check with AUDITOR excluded from
  write roles.
- Backend service methods also enforce RBAC; UI-only checks prohibited.
- AUDITOR can GET all tax config / invoice data; POST/PATCH/PUT → 403.

---

## 2. Domain rules (hard-coded, mirroring existing patterns)

### D1 — TaxRate enum values

- `TaxRate.VAT_0` = 0, `TaxRate.VAT_5` = 5, `TaxRate.VAT_10` = 10, `TaxRate.NOT_TAXED` = -1.
- Domain layer: no sqlalchemy/Flask imports (lint-enforced, per AGENTS.md).

### D2 — VAT rate validation

- `validate_vat_rate(rate)` → raises `InvalidRegimeError` if rate ∉ {0, 5, 10}.
- Used by SystemSettingsService before any config update.

### D3 — CompanyConfig vat_rates is LAW-type

- `vat_rates: frozenset[int]` default `{0, 5, 10}`.
- Change requires migration + reason + 2nd approval.
- `FlagLockedError` raised on direct change attempt without migration.

### D4 — VAT amount rounding

- `vat_amount = round(line_total × rate / 100, 2)`.
- Tol 0.01 matching Voucher.post() rule; consistent with D6 balance preservation.

### D5 — E-invoice series max 15

- `len(config.e_invoice_series) >= 15` → SystemSettingsError.
- Per ND 254/2026/NĐ-CP effective 01/07/2026.

### D6 — AUDITOR read-only backend enforcement

- RBAC enforced in service layer + `@login_required + current_user.role` check.
- AUDITOR role constant: read-only; cannot mutate CompanyConfig, e-invoice series, invoices.
- Violations → 403 Permission denied.

---

## 3. Rule conflicts / precedence

| Conflict | Resolution |
|---|---|
| VAT 8% temporary vs current {0,5,10} | 8% out of scope v1; can be added as CONFIG flag v2 |
| LAW-type vs CONFIG-type flag change | LAW immutable without migration (R4); CONFIG with 2nd approval (R5) |
| Rate outside company's vat_rates | 409 conflict; must UC-01 configure new rate first |
| Invoice post with frozen rate vs rate change | Rate frozen on post (R8); change requires reverse+re-apply |