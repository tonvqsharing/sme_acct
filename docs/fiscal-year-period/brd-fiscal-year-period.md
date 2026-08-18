# Fiscal Years & Accounting Periods Module — BRD

## 1. Background

Every accounting entry, voucher, invoice, revaluation run and report in the
application belongs to a **kỳ kế toán** (accounting period). VN law defines the
fiscal year, its start/end rules, the first period of a new entity, short-period
merging, and the notification duty when a company changes its fiscal year.
Systems that ignore period rules silently corrupt BCTC (financial statements),
audit trails and tax filings.

The current codebase has period-lock scaffolding only: a `period_locks` table,
a no-op `PeriodLockService`, and a `period_is_locked()` query used by the
currencies module. **Nothing enforces period rules on voucher/invoice posting.**

This module makes fiscal years and period locks a first-class, enforced domain.

## 2. Business drivers (2026)

- **TT 99/2025/TT-BTC** replaces TT 200/2014 from 01/01/2026 — chart of accounts
  renamed/restructured (e.g. Bảng cân đối kế toán → Báo cáo tình hình tài chính),
  SMEs may elect to apply it; regime must stay consistent ≥ 1 fiscal year.
- **Luật Kế toán 88/2015 Điều 12** — hard legal requirements for fiscal year
  definition, change, notification to cơ quan thuế, ≤15-month first period,
  <90-day merge rule.
- **TT 133/2016 Điều 73** — changing fiscal year requires closing books and
  preparing transition-period BCTC.
- Vendors (Fast, MISA SME 2026/AMIS, BRAVO 10) all ship TT99-compliant
  khóa sổ (period close) + carry-forward opening balances. Customers expect it.

## 3. Stakeholders

| Role | Interest |
|---|---|
| Kế toán tổng hợp | Open/close periods, post entries, detect locked-period errors |
| Kế toán trưởng | Approve period closes, unlock with justification, year-end close, sign-off |
| Chủ doanh nghiệp / Giám đốc | Decide fiscal year, notify tax authority, sign notice |
| Kiểm toán viên | Read-only access to locked periods + close evidence |
| Quản trị hệ thống | Configure fiscal year, audit close history |

## 4. Scope

### In scope
1. Fiscal year definition per company (calendar default; quarter-aligned
   alternatives 01/04, 01/07, 01/10; first period ≤ 15 months; short-period merge).
2. Period model: fiscal year → 12 periods (or first/short period set).
3. Period lock/unlock with SOD approval (no self-approval) + audit trail.
4. Enforcement: posting/editing operations reject when period locked.
5. Year-end close: close all periods → kết chuyển 911/421 → opening balances
   carry-forward into new fiscal year.
6. Change of fiscal year: transition period BCTC + "Số đầu năm" opening balances.
7. REST API + RBAC (`@casbin_required`) + domain service.
8. Reopen locked period (restricted, justified, audited) for correcting entries.

### Out of scope
- Tax declarations (Tờ khai thuế) — separate module.
- Full BCTC report generation — separate reporting module (period data only).
- Multi-company consolidation (see `docs/multi-company/` research gaps).
- NHNN / external sync.

## 5. Business requirements

### FR-01 Fiscal year definition
System MUST support, per company: calendar year (default) or 12-month fiscal
year starting 01/04, 01/07 or 01/10 (Luật 88/2015 Điều 12).
MUST reject any other start date (e.g. 15/07 — not quarter-aligned).

### FR-02 First fiscal period
New company's first kỳ kế toán may be up to 15 months. System MUST allow
creating a first period ≠ 12 months, and MUST show "Kỳ kế toán đầu tiên" label.

### FR-03 Short-period merge
Period shorter than 90 days (start/end of change, or liquidation start)
MUST be merged into adjacent period. System MUST NOT create standalone
periods < 90 days.

### FR-04 Period lock enforcement
Posting, editing or deleting any entry dated within a locked period MUST fail
with `PeriodLockedError`. Applies to vouchers, invoices, revaluation runs,
FX differences, opening balances.

### FR-05 SOD on lock/unlock
Opening a period lock: allowed by CFO/Kế toán trưởng. Closing a period: any
user may request; approval required from a different user with
`period_lock_approve` permission. Unlock (reopen): always requires approval +
mandatory justification. Self-approval blocked (D9 SOD pattern from
currencies module).

### FR-06 Year-end close
Process MUST: require all periods closed → verify no draft/unposted entries →
run kết chuyển (911/421) automatically or via scheduled task → produce opening
balances for the new fiscal year → mark year CLOSED.

### FR-07 Change of fiscal year
MUST support: close current books → create transition BCTC (short period) →
opening balances as "Số đầu năm" of new period → notify tax authority
(warning/checklist; actual filing is external).

### FR-08 Audit trail
Every lock/unlock/close/reopen MUST record: actor, timestamp, period, fiscal
year, reason, evidence (approval ref). Locked-period records remain
immutable (append-only, checksum per audit-log module).

### FR-09 RBAC
| Action | Roles |
|---|---|
| View periods/locks | all logged-in |
| Close period (request) | accountant |
| Approve close / unlock | ke_toan_truong, admin (not same as requester) |
| Configure fiscal year | ke_toan_truong, admin |
| Reopen | ke_toan_truong + justification |
| Year-end close | ke_toan_truong |

## 6. Non-functional requirements

- **NFR-1 Correctness**: period boundary math must be timezone-safe (VN, ICT);
  use UTC storage + local period dates.
- **NFR-2 Concurrency**: lock check + insert must be atomic (no TOCTOU race);
  use DB transaction with `SELECT ... FOR UPDATE` or unique constraint.
- **NFR-3 Performance**: `is_locked` check < 5ms cached; period boundary queries
  indexed (`fiscal_year`, `period_number`, `start_date`, `end_date`).
- **NFR-4 Audit**: all state changes immutable; 10-year retention per
  Luật Kế toán 2015 (mirror audit-log module).
- **NFR-5 Security**: enforcement in service layer, NOT only UI/templates;
  REST routes behind `@casbin_required`.
- **NFR-6 Data**: dates as `date`, amounts `Decimal`, UUID PKs for rows that
  need external references.

## 7. Risks / open questions

| Risk | Mitigation |
|---|---|
| TT99 vs TT133 SME choice | Support per-company accounting regime; consistent ≥ 1 fiscal year (VAS 01) |
| Reopening closed year after BCTC filed | Lock after report generation; reopen requires written justification (audit-safe) |
| Old `FISCAL_15` enum value in DB | Migration: replace with legal values (see specs) |
| Vendor parity (MISA khóa sổ tự động) | Ship manual lock first, auto-lock as enhancement |
| IFRS 18 (2027) impact | Reporting layer concern; period model unaffected |
