# Fiscal Years & Accounting Periods Module — Use Cases

Conventions: H = happy path, A = alternative, E = exception. Actor = role.

## UC-01 Define fiscal year (default calendar)

- **Actor**: Kế toán trưởng / admin
- **Pre**: Company exists; no fiscal year configured.
- **H**: POST `/api/fiscal-years` {period_type: CALENDAR, start_date: 2026-01-01}.
  System creates FiscalYear 2026 + 12 periods (Tháng 01..12/2026), all OPEN.
  201 + detail.
- **A1**: Default auto-seed — fiscal year 2026 created at company setup
  (onboarding), no manual step.
- **E1**: Year already exists → 409 `FiscalYearExistsError`.
- **E2**: start_date not 01/01 → 422 `InvalidFiscalYearError` (R-01).

## UC-02 Define special fiscal year (quarter-aligned)

- **Actor**: Kế toán trưởng
- **H**: POST {period_type: FISCAL_APR, start_date: 2026-04-01} → FY 2026-04-01 →
  2027-03-31, 12 periods, label "Năm tài chính 01/04/2026–31/03/2027".
  System shows reminder: "Phải thông báo cơ quan thuế" (checklist, A2).
- **A1**: FISCAL_JUL / FISCAL_OCT — same path, different boundary math.
- **E1**: start_date 2026-07-15 → 422 (not quarter-aligned; legacy `FISCAL_15`
  rejected, R-15).
- **E2**: end beyond 15 months for first period handled in UC-03.

## UC-03 First fiscal period of new company (≤ 15 months)

- **Actor**: Kế toán trưởng
- **Pre**: Company registered mid-cycle (e.g. 15/08/2026).
- **H**: System creates first FY from 15/08/2026 to 31/12/2026 (4.5 months,
  calendar regime). Label "Kỳ kế toán đầu tiên". Period boundaries honor
  merge rule (A1): period < 90 days merged.
- **A1**: Registration date falls within a <90-day window → merged into next
  period.
- **E1**: Registration > 15 months before chosen FY end → 422
  `InvalidFiscalYearError` (exceeds legal max).

## UC-04 Close (lock) a period

- **Actor**: Kế toán tổng hợp (request), Kế toán trưởng (approve)
- **H**: POST `/api/periods/<id>/close` {reason}. Status OPEN → LOCKED.
  Lock event recorded (requester, approver, timestamps). Entries dated inside
  now blocked.
- **A1**: Auto-lock proposal (MISA "khóa sổ tự động" parity): system lists
  periods past their end date with no open entries; user confirms in one batch.
- **A2**: Close with open drafts — system warns, requires `force=true` +
  reason, approver re-confirms.
- **E1**: Requester == approver → 403 `SelfApprovalError` (SOD, R-07).
- **E2**: Period already LOCKED → 409 `PeriodTransitionError`.

## UC-05 Post entry into locked period → blocked

- **Actor**: Kế toán tổng hợp
- **H**: Voucher dated 2026-02-15; Feb 2026 locked. `VoucherService.post` calls
  `validate_before_entry` → 409 `PeriodLockedError` with period_id + message
  "Kỳ kế toán tháng 02/2026 đã khóa sổ".
- **A1**: Entry via API → same service-layer rejection (R-13, no UI bypass).
- **E1**: Concurrent race — two posts same instant; DB unique/row lock catches
  second → 409.

## UC-06 Reopen (unlock) a period

- **Actor**: Kế toán trưởng
- **H**: POST `/api/periods/<id>/reopen` {reason: "Điều chỉnh sai sót kỳ trước
  theo yêu cầu kiểm toán", approval_ref}. LOCKED → OPEN; event logged.
- **A1**: Audit-mandated reopening — reason + reference mandatory, history
  exported to audit package.
- **E1**: Empty reason → 422.
- **E2**: No `period.reopen` permission → 403.
- **E3**: Period YEAR_CLOSED → 409 (must use correction journal, not reopen).

## UC-07 Year-end close + kết chuyển 911/421

- **Actor**: Kế toán trưởng
- **Pre**: All 12 periods LOCKED; no unposted entries.
- **H**: POST `/api/fiscal-years/<id>/close`. System:
  1. Verifies preconditions (R-08);
  2. Generates kết chuyển entries: doanh thu/chi phí → 911 → 421;
  3. Builds opening balances (Số đầu năm) per account;
  4. Creates next fiscal year (2027) with periods OPEN and opening balances;
  5. FY status → YEAR_CLOSED. Response includes closing summary +
     opening-balance report URL.
- **A1**: Scheduled/auto-run at configured close date (FR-06 enhancement).
- **E1**: Any period not locked → 409 `YearEndPreconditionsError` (lists period).
- **E2**: Draft/unposted voucher in range → 422, user must post or void.
- **E3**: Prior year already closed → 409.

## UC-08 Change fiscal year (đổi kỳ kế toán)

- **Actor**: Kế toán trưởng
- **H**: POST `/api/fiscal-years/change` {new_period_type: FISCAL_JUL}.
  1. Validate current year closable (A2.1-2);
  2. Snapshot transition BCTC (transition period);
  3. Create new FY starting 01/07/2027 with "Số đầu năm" = closing balances;
  4. Emit "Thông báo thay đổi kỳ kế toán" template + tax-notification
     checklist (T1 template).
- **A1**: Short transition period < 90 days → merged per A1/A4.
- **E1**: Old year not closed → 409.
- **E2**: Notification not acknowledged → warning, requires checkbox
  "Đã thông báo cơ quan thuế" (evidence ref).

## UC-09 View period lock status / history

- **Actor**: any logged-in; AUDITOR read-only
- **H**: GET `/api/periods/locked?date=...` → `{locked: true, period_id, label}`.
  UI shows khóa-sổ banner on posting screens.
- **A1**: History drill-down per period: full lock-event chain + checksums.
- **E1**: Unauthenticated → 401 (existing auth).

## UC-10 Revaluation / FX blocked by locked period

- **Actor**: Kế toán tổng hợp
- **H**: `RevaluationService.create_run` for locked period → `PeriodLockedError`
  (existing path, now backed by real repo, revaluation_service.py:75).
- **E1**: CSV FX-rate import containing dates in locked periods → row rejected
  with clear message; atomic import = nothing imported (D3 parity).

## UC-11 Dissolution — final period

- **Actor**: Kế toán trưởng
- **H**: Company dissolve → final period from end of last FY to dissolution date,
  books closed, final BCTC snapshot.
- **A1**: < 90 days → merged into preceding period (A1).
- **E1**: Outstanding unposted entries → blocked with list.

## UC-12 Legacy `FISCAL_15` data migration

- **Actor**: admin (during upgrade)
- **H**: Migration script detects `accounting_period_type == FISCAL_15` →
  marks company "needs review", blocks posting until admin redefines fiscal
  year per law (R-15).
- **E1**: Company unreachable → pending flag surfaced in admin dashboard.
