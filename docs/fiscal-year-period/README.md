# Fiscal Years & Accounting Periods Module — README

## Status: 📋 SPEC APPROVED — NOT IMPLEMENTED — NOT PROD-READY

Doc set **signed off 2026-08-18** (SIGN-OFF.md) — BA lead + chief accountant.
Tech lead + security review pending. Spec baseline for implementation.

**Verdict: codebase has stub-only support (period_locks table + PeriodLockService no-op).
Cannot operate in PROD ENV.** See `production-readiness-audit-fiscal-year-period.md`.

## Why now (2026 regulatory drivers)

| Driver | Legal basis | Effective |
|---|---|---|
| New enterprise accounting regime (replaces TT 200/2014) | **TT 99/2025/TT-BTC** | 01/01/2026 |
| Accounting periods law (kỳ kế toán) | **Luật Kế toán 88/2015/QH13 Điều 12** | 01/01/2017 |
| Guidance on Luật Kế toán | **NĐ 174/2016/NĐ-CP** (hợp nhất 02/VBHN-BTC/2019) | 01/01/2017 |
| Change of accounting period (SME regime) | **TT 133/2016/TT-BTC Điều 73** | 01/01/2017 |
| First fiscal period of new entity ≤ 15 months | Luật Kế toán 88/2015 Điều 12 | in force |
| Fiscal-year reporting requirement (IFRS) | **IAS 1 para 36** → superseded by **IFRS 18** | 01/01/2027 |

> ⚠️ Existing code/docs referencing the old `AccountingPeriodType.FISCAL_15`
> (15-month period starting mid-month) is LEGALLY WRONG — Điều 12 requires a
> fiscal year to start at the beginning of a quarter month (01/04, 01/07, 01/10).

## Doc index

| Doc | Purpose |
|---|---|
| [BRD](brd-fiscal-year-period.md) | Business requirements, scope, stakeholders |
| [Specs](specs-fiscal-year-period.md) | Technical/functional spec, data model, API |
| [Use cases](use-cases-fiscal-year-period.md) | UC-01..UC-12 with happy/alt/exception paths |
| [Processes](processes-fiscal-year-period.md) | End-to-end business processes |
| [Rules](rules-fiscal-year-period.md) | Legal rules + domain rules (hard-coded) |
| [Data flows](data-flows-fiscal-year-period.md) | DF diagrams + flows |
| [Workflows](workflows-fiscal-year-period.md) | State machines, approvals, statuses |
| [User journeys](user-journeys-fiscal-year-period.md) | Role-based journeys |
| [Prod-readiness audit](production-readiness-audit-fiscal-year-period.md) | Gap analysis, verdict NOT PROD-ready |
| [SIGN-OFF](SIGN-OFF.md) | Sign-off ledger |
| [Templates](templates/) | Year-end close checklist, change-of-period notice, lock approval form |

## Core concepts (summary)

- **Kỳ kế toán năm (fiscal year)** — default 12 months, 01/01–31/12. Đơn vị đặc thù
  may choose a different 12-month period that starts at the beginning of a quarter
  month (01/04, 01/07, 01/10) and must notify the tax authority in advance.
- **Kỳ kế toán đầu tiên (first period)** — of a new entity may be ≤ 15 months.
- **Kỳ kế toán ngắn (short period)** — the period before/after a change is shorter
  than 90 days: merged with the following/preceding period.
- **Khóa sổ (period close / lock)** — after closing, no new/modified entries dated
  inside the locked period. Posting attempts raise `PeriodLockedError`.
- **Khóa sổ cuối năm (year-end close)** — close all periods, run kết chuyển
  (911/421 P&L appropriation), then carry opening balances into the new fiscal year.
- **Đổi kỳ kế toán (change of fiscal year)** — must close books, prepare separate
  BCTC for the transition period, and opening balances become "Số đầu năm" of the
  new period (TT 133/2016 Điều 73; same principle under TT 99/2025).

## References (primary sources, verified 2026-08-18)

- Luật Kế toán 88/2015/QH13 Điều 12 — kỳ kế toán: năm/quý/tháng; 12-month fiscal
  year; quarter-start requirement; ≤15-month first period; <90-day merge; tax
  authority notification.
- Nghị định 174/2016/NĐ-CP — hướng dẫn Luật Kế toán (hợp nhất 02/VBHN-BTC/2019).
- TT 99/2025/TT-BTC — chế độ kế toán doanh nghiệp mới (thay TT 200/2014), hiệu lực
  01/01/2026; Điều 31: áp dụng cho kỳ kế toán năm bắt đầu từ 01/01/2026; tài khoản
  911/421; SMEs may choose to apply (consistent ≥ 1 fiscal year); BCTC: "Báo cáo
  tình hình tài chính" (formerly Bảng cân đối kế toán).
- TT 133/2016/TT-BTC Điều 73 — đổi kỳ kế toán: khóa sổ, BCTC chuyển tiếp, số dư
  đầu kỳ mới.
- VAS 01 (QĐ 165/2002/QĐ-BTC) — nhất quán phương pháp ≥ 1 kỳ kế toán năm; hoạt
  động liên tục; dồn tích.
- IAS 1 para 36 — FS presented at least annually; period ≠ 12 months → disclose
  reason; IFRS 18 supersedes from 01/01/2027.
- ERP benchmarks: Tryton (period/journal-period, fiscal-year renewal wizard, P&L
  appropriation), Odoo 17 (fiscal year 12 months, lock dates, "Irreversible Lock
  Date" module), Forvis Mazars (year-end: mark historical → beginning balances →
  retained earnings), Manager.io (lock date blocks edits on/before date), Patriot
  (closing entry zeroes income/expense to equity), Fast/MISA SME 2026/BRAVO 10
  (khóa sổ tự động, carry-forward opening balances per TT 99/2025 updates).
- Official portals verified ACTIVE (2026-08-18, playwright): gdt.gov.vn,
  mof.gov.vn, vbpl.vn, thuedientu.gdt.gov.vn, dichvucong.gov.vn, vacpa.org.vn,
  vaa.net.vn, pwc.com/vn, kpmg.com/vn, ey.com/en_vn.

## Related docs / modules

- `docs/system-settings/` — `CompanyConfig.accounting_period_type`,
  `fiscal_year_start_month/day`; broken `lock_period` REST routes.
- `docs/currencies-exchange/` — `currency_repo.period_is_locked()` working pattern;
  FX revaluation must not run into locked periods.
- `docs/company-module/` — Company entity, `get_fiscal_year_and_period()`.
- `docs/decisions/` — ADR context for accounting regime (TT 99/2025).
