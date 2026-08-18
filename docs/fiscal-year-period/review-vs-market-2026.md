# Market Review — Fiscal Years & Accounting Periods (v1 vs 2026 market)

Date: 2026-08-18. Scope: compare `fiscal-year-period` module (v1, implemented) against
current Vietnamese accounting-software behavior for fiscal-year / period-lock / period-close.

Sources: MISA AMIS/SME help docs, FAST Accounting 11 R09 + product page, BRAVO ERP 8/10
marketing + help, Base.vn 2026 product roundup. All web, not demo-grade — treat as directional.

## Alignment (we match market)

| Capability | Our v1 | MISA | FAST | BRAVO |
|---|---|---|---|---|
| Lock period → reject new/changed entries | `period.status=LOCKED` + `validate_before_entry` → `PeriodLockedError` | Khóa sổ by date, blocks add/edit/delete of vouchers before lock date | Khóa nhập liệu blocks data entry in locked period | Không hạch toán vào kỳ đã khóa (implicit) |
| Unlock / reopen with audit trail | `reopen_period` (reason required, SOD: self-approval blocked, `PeriodLockEvent` SHA-256 chain) | Bỏ khóa sổ supported | Gỡ khóa supported | — |
| Year close state + opening-balance marker | `YEAR_CLOSED` + `opening_balance_posted` flag | Đóng sổ cuối năm, mở số dư đầu kỳ sau | Đóng sổ kế toán, tự sinh số dư cuối kỳ/đầu kỳ | Tạo bút toán khóa sổ + kết chuyển cuối kỳ |
| Quarter-aligned periods | auto-split periods by FY type (CALENDAR/APR/JUL/OCT) | follow calendar/regime | follow regime | follow regime |
| Legal year types | CALENDAR, FISCAL_APR/JUL/OCT (FISCAL_15 removed) | TT99/2025 aligned | TT99/2025 aligned | custom |
| Entry guard before booking | `PeriodLockedError` on locked period | blocks pre-lock-date vouchers | blocks locked periods | blocks closed periods |

## Gaps vs market (→ v2 candidates)

1. **Automated period-end closing entries** — BRAVO + FAST auto-generate kết chuyển lãi/lỗ,
   kết chuyển thuế GTGT, trích khấu hao, khóa sổ bút toán (one-click "Kết chuyển cuối kỳ").
   Our v1 deliberately defers 911/421 kết chuyển + real opening balances to the ledger module
   (documented in README known-gaps). This is the single biggest functional delta vs market.

2. **Two-level lock granularity** — FAST distinguishes "Khóa nhập liệu" (per voucher type) vs
   "Đóng sổ kế toán" (blocks system-generated period-end entries too). MISA khóa sổ per ngày.
   Our single `LOCKED` state ≈ khóa nhập liệu; `YEAR_CLOSED` ≈ đóng sổ năm. Per-document-type
   lock granularity + separate "khóa/đóng" flag pairs are v2.

3. **Lock-by-date vs lock-by-period** — MISA locks by absolute date (ngày khóa sổ), FAST by
   date too. We lock whole `AccountingPeriod` rows. Date-based lock is friendlier mid-period;
   period-based is simpler and matches our period-centric domain. Revisit when Voucher/Invoice
   modules land (they will need a `validate_before_entry(date)` hook — likely a date-range
   lookup over locked periods).

4. **Multi-entity / multi-branch** — BRAVO supports per-đơn-vị (khay đơn vị cơ sở), MISA
   per-branch lock. Our FY is company-scoped (single-company per DB, tenant isolation pending —
   company consolidation explicitly out of scope per AGENTS.md). OK for v1.

5. **Auto-lock scheduling** — MISA offers khóa sổ tự động. We require manual close_period.
   v2 candidate.

6. **Report/print gating** — market ties lock state to report periods (sổ cái per kỳ đã khóa
   frozen). We don't yet gate reporting; comes with reporting module.

## Conclusions

- v1 core state machine (OPEN → LOCKED → YEAR_CLOSED, reopen with audit, SOD self-approval
  block, checksum chain) matches market semantics and exceeds FAST/MISA on audit trail
  (SHA-256 tamper-evident lock events — market logs changes but not chained checksums).
- Biggest v1→v2 item: automatic closing-entry generation (911/421, VAT) once ledger module
  exists. PeriodLockService.close_fiscal_year already reserves `opening_balance_posted` marker
  for that handoff.
- No blocking design corrections from market review. No rework required.
