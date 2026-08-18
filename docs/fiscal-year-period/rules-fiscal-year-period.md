# Fiscal Years & Accounting Periods Module — Rules

## A. Legal rules (verified 2026-08-18)

### A1. Kỳ kế toán năm — Luật Kế toán 88/2015/QH13 Điều 12
- Kỳ kế toán năm = 12 months.
- Default: calendar year, 01/01 → 31/12.
- Đơn vị đặc thù (đặc thù riêng về tổ chức, hoạt động) MAY choose a different
  fiscal year of 12 months **starting at the beginning of a quarter month**
  (01/04, 01/07 or 01/10). Quarter-alignment is a hard legal constraint.
- Changing the fiscal year: MUST notify cơ quan tài chính (và cơ quan thuế trực
  tiếp quản lý) before implementation.
- Kỳ kế toán đầu tiên of a new unit: from establishment date to the end of the
  chosen fiscal year, **≤ 15 months**.
- Kỳ kế toán cuối cùng at dissolution: from end of last full fiscal year to the
  dissolution date.
- Periods of < 90 days: merged into preceding/following period; no standalone
  short period.

### A2. Nghị định 174/2016/NĐ-CP (hợp nhất 02/VBHN-BTC/2019)
- Detailed guidance on Luật Kế toán. Đơn vị thay đổi kỳ kế toán phải:
  1. Notify tax authority;
  2. Close books at the end of the previous period;
  3. Prepare financial statements for the transition period;
  4. Use opening balances of the new period = closing balances of the old.

### A3. TT 99/2025/TT-BTC (thay TT 200/2014, hiệu lực 01/01/2026)
- Applies to fiscal years starting on/after 01/01/2026 (Điều 31).
- SMEs may elect to apply TT99 (Điều 2.4) — choice must be consistent for at
  least one full fiscal year.
- BCTC: "Bảng cân đối kế toán" renamed **"Báo cáo tình hình tài chính"**;
  presentation consistent across periods (VAS 01).
- Year-end: kết chuyển to TK 911 (Xác định kết quả kinh doanh), final to
  TK 421 (Lợi nhuận sau thuế chưa phân phối).
- Internal-control duty (Điều 3): khóa sổ/period control is part of internal
  control system; Quy chế mở tài khoản per Điều 11.

### A4. TT 133/2016/TT-BTC Điều 73 (SME regime; mirrored in TT99 practice)
- Đổi kỳ kế toán → phải khóa sổ kế toán;
- Lập báo cáo tài chính riêng cho giai đoạn chuyển tiếp;
- Số dư cuối kỳ cũ trở thành **"Số đầu năm"** của kỳ mới.

### A5. VAS 01 — Khuôn mẫu chuẩn mực chung (QĐ 165/2002/QĐ-BTC)
- Accounting policies applied consistently ≥ 1 fiscal year; a change is
  restated as if the new policy had always applied (comparative restatement).
- Going concern, accrual basis.

### A6. IAS 1 para 36 / IFRS 18 (for multi-national group reporting)
- FS presented at least annually. If fiscal period ≠ 12 months (e.g. 52-week
  cycle), disclose: (a) period covered, (b) reason for shorter/longer period,
  (c) comparatives are not entirely comparable.
- IFRS 18 supersedes IAS 1 for periods beginning on/after 01/01/2027 — same
  annual-period requirement preserved.

## B. Domain rules (hard-coded in implementation)

| ID | Rule |
|---|---|
| R-01 | Fiscal year start = 01/01 (calendar) OR 01/04, 01/07, 01/10 (special). Any other start → `InvalidFiscalYearError`. |
| R-02 | Fiscal year length = 12 months exactly (except first period ≤ 15 months per FR-02). |
| R-03 | No standalone period < 90 days (merged per A1). |
| R-04 | `period_is_locked(company_id, entry_date)`: entry_date inside a locked period → `PeriodLockedError` blocks POST/EDIT/DELETE of entries. |
| R-05 | Lock scope: at minimum whole period (`LOCK_SCOPE=PERIOD`); optional per-journal lock (Tryton "Journal Period") as later enhancement. |
| R-06 | Lock transitions: OPEN → LOCKED (close, requires approval); LOCKED → OPEN (reopen, requires approval + justification). No direct CLOSED → OPEN without justification. |
| R-07 | SOD: requester ≠ approver; self-approval → `SelfApprovalError`. |
| R-08 | Year-end close requires ALL periods of the fiscal year LOCKED and no DRAFT/UNPOSTED entries in period range. |
| R-09 | Carry-forward: opening balances (Số đầu năm) = closing balances of prior year, per account, after 911/421 appropriation. |
| R-10 | Entries in locked periods are immutable; corrections happen in current period (or reopen per R-06 with justification). |
| R-11 | Actor UUID required on every mutation (D11 pattern from currencies). |
| R-12 | Change of fiscal year requires: existing years closed → create transition period (per A2/A4) → opening balances move to "Số đầu năm". |
| R-13 | Enforcement in service layer (backend), not only UI; REST routes guarded by `@casbin_required`. |
| R-14 | Money = Decimal; dates = `date` (period boundaries local ICT). |
| R-15 | `FISCAL_15` (15-month period starting 15/07) is ILLEGAL — deprecated, migration required. |

## C. RBAC matrix

| Permission | accountant | ke_toan_truong | admin | auditor |
|---|---|---|---|---|
| period.view | ✓ | ✓ | ✓ | ✓ (read-only) |
| period.close.request | ✓ | ✓ | ✓ | ✗ |
| period.close.approve | ✗ | ✓ | ✓ | ✗ |
| period.reopen | ✗ | ✓ | ✓ | ✗ |
| fiscal_year.configure | ✗ | ✓ | ✓ | ✗ |
| year_end.run | ✗ | ✓ | ✓ | ✗ |
| lock.history | ✓ | ✓ | ✓ | ✓ (read-only) |
