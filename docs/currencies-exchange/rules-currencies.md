# Rules — Currencies & Exchange Rates Module

| | |
|---|---|
| Version | 1.0 |
| Date | 2026-08-19 |

## 1. Legal rules (hard-coded, source-cited)

### R1 — Booking rates (Nợ/Có asymmetry)
- **Nợ (debit) side:** tỷ giá giao dịch thực tế (actual transaction rate).
- **Có (credit) side:** tỷ giá ghi sổ bình quân gia quyền hoặc giao dịch thực tế.
- Source: TT 99/2025/TT-BTC (mới, hiệu lực 01/01/2026); TT 133/2016/TT-BTC Điều 52-53 (SME).

### R2 — Period-end revaluation rate
- Revalue monetary items at **tỷ giá mua bán chuyển khoản trung bình** of the NHTM
  nơi doanh nghiệp thường xuyên giao dịch.
- Demand deposits: rate at NHTM where account opened.
- Source: TT 99/2025/TT-BTC.

### R3 — FX difference posting
- Gain → TK 515 (Doanh thu hoạt động tài chính); Loss → TK 635 (Chi phí tài chính) — direct.
- TK 413 (Chênh lệch tỷ giá) exists per Điều 60 TT 99/2025; configurable path.
- Source: TT 99/2025/TT-BTC Điều 60; VAS 10 (QĐ 165/2002/QĐ-BTC); TT 200/2014 Điều 69 (legacy).

### R4 — Monetary vs non-monetary items
- Monetary (tiền tệ): cash, bank, receivables, payables → revalue at closing rate.
- Non-monetary (phi tiền tệ): inventory, fixed assets, prepaid → historical rate,
  never revalued; fair-value items at valuation-date rate.
- Source: VAS 10; IAS 21.

### R5 — E-invoice FX (ND 254/2026/NĐ-CP)
- Invoice in FX only in permitted cases (TT 32/2013/TT-NHNN).
- Invoice must show tỷ giá quy đổi ra VND.
- Tax: revenue → tỷ giá mua commercial bank; expense → tỷ giá bán (TT 26/2015/TT-BTC reference).
- Effective 01/07/2026; replaces ND 123/2020.

### R6 — FX use restrictions (Vietnam)
- Foreign currency may not be freely used for payments/pricing inside Vietnam;
  permitted cases per Pháp lệnh ngoại hối 2005 (sửa đổi 2013) + ND 70/2014/NĐ-CP + TT 32/2013/TT-NHNN.
- Violations sanctioned per ND 340/2025/NĐ-CP.

### R7 — Accounting currency
- Books kept in VND. Foreign-currency transactions recorded in original currency
  AND VND equivalent. FS presented in VND.
- Source: TT 99/2025/TT-BTC; VAS 10.

### R8 — Consistency (nhất quán)
- Once rate-application policy chosen (actual vs weighted avg per side), apply
  consistently; changes require documented reason + approval.
- Source: TT 99/2025/TT-BTC.

## 2. Domain rules (hard-coded, mirroring existing patterns)

### D1 — Currency code format
- `^[A-Z]{3}$` (ISO 4217). Else InvalidCurrencyError.

### D2 — Rate invariants
- `rate > 0`. Numeric(18,6).
- Unique (currency_code, rate_date, rate_type); new row supersedes old for lookups
  (history preserved — no in-place update).

### D3 — Rate immutability
- Rate referenced by a posted transaction is locked (RateLockedError on delete/change).
- "Change" = insert new rate row.

### D4 — Base currency immutability
- VND (or configured base) immutable once any transaction exists (FlagLockedError pattern).

### D5 — Weighted average formula
- `avg_rate = Σ(amount_original × rate) / Σ(amount_original)`
- Computed over open FX balance of account at booking time (Có side).

### D6 — Balance preservation
- Revaluation postings must balance: `Σ debit == Σ credit` within tol 0.01
  (reuse Voucher.post() rule).

### D7 — Idempotent re-run
- Revaluation for same (company, period): reverse prior POSTED run, then re-apply.

### D8 — Period lock
- Revaluation/post blocked in locked period (period_locks integration) → PeriodLockedError.

### D9 — Approval chain
- Revaluation POST requires APPROVED status; APPROVED requires CHIEF_ACCOUNTANT
  (2nd-approval pattern from system-settings).

### D10 — Clean Architecture
- Domain layer: no sqlalchemy, no Flask imports (lint-enforced, per AGENTS.md).

### D11 — RBAC
- All API mutations require actor UUID + `@casbin_required(*roles)`.
- AUDITOR read-only everywhere (RBAC backend enforcement, not just UI).

## 3. Rule conflicts / precedence

| Conflict | Resolution |
|---|---|
| TT 200/2014 vs TT 99/2025 | TT 99/2025 wins from 01/01/2026 (new regime) |
| ND 123/2020 vs ND 254/2026 | ND 254/2026 wins from 01/07/2026 |
| VAS 10 vs TT 99/2025 detail | Align; where TT 99/2025 explicit, follow TT 99/2025 |
| Booking vs tax rate | Booking = accounting rule (R1); tax declaration rate per R5 |
| Company config vs law | LAW-type flags immutable; CONFIG-type admin-changeable + audit |

## 4. Version history

| Ver | Date | Change |
|---|---|---|
| 0.1 | 2026-08-18 | Initial rules |