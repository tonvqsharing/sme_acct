# Use Cases — Currencies & Exchange Rates Module

| | |
|---|---|
| Version | 0.1 |
| Date | 2026-08-18 |

Format: each UC has Description, Preconditions, Actors, Main flow (happy path),
Alternative flows, Exception paths.

---

## UC-01 Create currency

- **Actors:** Admin
- **Preconditions:** Logged in with ADMIN role; currency code not existing.
- **Main flow:**
  1. Admin opens Currencies list.
  2. Clicks "Thêm mới" (Create).
  3. Enters code (ISO 4217), name, symbol, decimal places.
  4. Submits.
  5. System validates (code `^[A-Z]{3}$`, unique, ISO known), creates currency (inactive by default), audit-logs.
  6. System shows success; new currency in list (inactive badge).
- **Alternative A1 (activate on create):** Admin ticks "Kích hoạt ngay"; system activates after validation.
- **Alternative A2 (import):** Admin uses batch import (UC-05) instead of single create.
- **Exception E1 (duplicate):** Code exists → 409, "Mã tiền tệ đã tồn tại".
- **Exception E2 (invalid code):** Non-ISO or wrong format → 400, field error.
- **Exception E3 (VND attempt):** Creating VND as non-base → 400, "VND là tiền tệ cơ sở, không tạo mới".

## UC-02 Update / deactivate currency

- **Actors:** Admin
- **Preconditions:** Currency exists.
- **Main flow:**
  1. Admin opens currency detail.
  2. Edits name/symbol/decimal places; or clicks "Vô hiệu hóa".
  3. Submits; system validates no active transactions reference currency (for deactivate).
  4. System audit-logs change; deactivated currency hidden from new-transaction pickers.
- **Exception E1 (referenced):** Posted transactions exist → 409, "Tiền tệ đang được sử dụng, không thể vô hiệu hóa".
- **Exception E2 (base currency):** Attempt to deactivate VND/base → 403 FlagLockedError-style, "Không thể vô hiệu hóa tiền tệ cơ sở".
- **Exception E3 (decimal change in use):** decimal_places change while transactions exist → 409.

## UC-03 Enter exchange rate manually

- **Actors:** Accountant, Chief Accountant
- **Preconditions:** Currency active; actor provided.
- **Main flow:**
  1. User opens Exchange Rates.
  2. Clicks "Thêm tỷ giá".
  3. Selects currency, date, rate type (mua/bán/chuyển khoản/trung tâm), enters rate, source=MANUAL, note (required).
  4. Submits; system validates rate > 0, date not in locked period (warning only), unique (currency,date,type).
  5. System stores rate; audit-logs actor + old value if replacing.
- **Alternative A1 (replace):** If rate for same (currency,date,type) exists, system keeps both (history) — new row supersedes for lookups.
- **Exception E1 (invalid):** rate ≤ 0 or non-numeric → 400.
- **Exception E2 (inactive currency):** → 400, "Tiền tệ không hoạt động".
- **Exception E3 (audit fail):** Audit log write fails → transaction rollback.

## UC-04 Batch import exchange rates (CSV)

- **Actors:** Accountant, Chief Accountant
- **Preconditions:** CSV file valid format; currency codes exist.
- **Main flow:**
  1. User opens Import Rates; uploads CSV.
  2. System validates all rows (code, date, type, rate).
  3. All valid → import applied atomically; success report (n rows).
  4. Any invalid → whole file rejected (default); error list per row returned.
- **Alternative A1 (partial mode):** Config `fx_import_partial=true` → valid rows applied, invalid reported (not default).
- **Exception E1 (empty file / wrong header):** → 400.
- **Exception E2 (unknown currency):** → row error "Mã tiền tệ không tồn tại".

## UC-05 Book FX transaction (invoice/voucher in foreign currency)

- **Actors:** Accountant
- **Preconditions:** Currency active; rate exists for transaction date (or manual entry allowed).
- **Main flow:**
  1. User creates invoice/voucher; selects currency ≠ base.
  2. System applies booking rate:
     - Nợ (debit) lines: actual transaction rate (giao dịch thực tế).
     - Có (credit) lines: bình quân gia quyền (weighted avg) per config.
  3. User confirms amounts (original + VND shown).
  4. On post: system freezes rate reference (immutable), stores currency + rate + VND amounts.
  5. E-invoice: tỷ giá quy đổi captured for ND 254/2026 compliance.
- **Alternative A1 (no rate):** User manually enters rate; audit-flagged source=MANUAL.
- **Exception E1 (rate missing, manual disallowed):** → 400, "Chưa có tỷ giá cho ngày …".
- **Exception E2 (weighted avg zero balance):** Có side with no prior FX balance → falls back to actual rate or error per config.

## UC-06 Period-end revaluation (run + approve + post)

- **Actors:** Accountant (create), Chief Accountant (approve/post)
- **Preconditions:** Period unlocked; closing rates available; monetary FX items exist.
- **Main flow:**
  1. Accountant opens Revaluation; selects period + rate date.
  2. System computes draft: items (FX cash/bank/receivables/payables), closing rate
     (tỷ giá mua bán chuyển khoản trung bình — transfer type), old/new VND, differences.
  3. Draft status PENDING_APPROVAL; summary shown.
  4. Chief Accountant reviews; approves.
  5. Chief Accountant posts → journal entries 515/635 (or TK 413 per config), balanced (tol 0.01).
  6. Status POSTED; audit-logged; FXDifference rows updated.
- **Alternative A1 (no differences):** All diffs zero → post no-op journal or mark POSTED without entries.
- **Alternative A2 (TK 413 path):** Config fx_revaluation_account=413 → differences to TK 413 Điều 60 path.
- **Exception E1 (locked period):** → PeriodLockedError, "Kỳ kế toán đã khóa".
- **Exception E2 (missing closing rate):** → 400 listing missing (currency,date).
- **Exception E3 (unbalanced):** computed postings don't balance → RevaluationError, run stays DRAFT.
- **Exception E4 (no approval):** Post attempted without approval → 403.
- **Exception E5 (re-run same period):** Existing POSTED run → reverse first (idempotent), then re-apply.

## UC-07 Reverse revaluation run

- **Actors:** Chief Accountant
- **Preconditions:** Run POSTED; period not locked (or force flag + reason).
- **Main flow:** Reverse postings (storno), status REVERSED, audit-logged with reason.
- **Exception E1 (locked period):** blocked unless force + documented reason.

## UC-08 FX difference report

- **Actors:** Accountant, Chief Accountant, Auditor (read)
- **Main flow:** Select period, currency, account → report: opening (orig/VND), movements,
  closing, revaluation adjustment, cumulative difference.
- **Exception E1 (no data):** empty report with message.

## UC-09 Rate history / audit view

- **Actors:** Chief Accountant, Auditor
- **Main flow:** View rate changes for (currency, range) with actor, timestamp, old/new, source.
- **Exception E1 (no changes):** empty list.

## UC-10 Configure FX settings (CompanyConfig)

- **Actors:** Chief Accountant, Admin
- **Preconditions:** actor provided; CONFIG-type flags only.
- **Main flow:** Change fx_rate_source, fx_revaluation_account, approval-required, etc.
  via existing system-settings PATCH /api/config; audit-logged; 2nd-approval pattern for CONFIG.
- **Exception E1 (LAW-type):** → FlagLockedError 403 "hằng pháp lý, không thể thay đổi".
- **Exception E2 (base currency change after use):** → FlagLockedError 403.

## UC-11 NHNN rate sync (v1.5)

- **Actors:** Chief Accountant, Admin
- **Main flow:** Trigger sync → fetch NHNN central rates for date range → upsert rates
  (source=NHNN) → report rows imported.
- **Exception E1 (NHNN down):** → 502, rates unchanged; manual fallback.
- **Exception E2 (partial):** some currencies missing → report, apply available.

## UC-12 Deactivate/report currency usage check (support)

- **Actors:** Admin, Auditor
- **Main flow:** Query all transactions referencing currency → usage list.
- **Exception E1 (none):** "Chưa sử dụng" → safe to deactivate.

---

## Coverage matrix vs BRD

| UC | BR |
|---|---|
| UC-01,02 | BR-01 |
| UC-03,04,11 | BR-02 |
| UC-05 | BR-03 |
| UC-06,07 | BR-04 |
| UC-08,09 | BR-05 |
| UC-10,12 | BR-06 |