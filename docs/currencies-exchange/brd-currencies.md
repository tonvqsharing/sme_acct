# BRD — Currencies & Exchange Rates Module

| | |
|---|---|
| Module | Currencies & Exchange Rates |
| Status | ✅ IMPLEMENTED + PROD-READY — all BR-01..BR-06 verified against code |
| Version | 1.0 |
| Date | 2026-08-19 |
| Related | specs-currencies.md, rules-currencies.md, ADR-003 |
| Related | production-readiness-audit-currencies.md, SIGN-OFF.md |

## 1. Background

Vietnamese SME accounting requires booking transactions in VND (Đồng Việt Nam).
Enterprises with foreign-currency transactions (exports, imports, FX loans,
foreign partners) must:

1. Record foreign-currency transactions in both original currency and VND equivalent.
2. Revalue monetary items (cash, bank, receivables, payables) at period end.
3. Book FX differences (chênh lệch tỷ giá) to P&L (515/635) per VAS 10 + TT 99/2025.
4. Produce financial statements fully in VND.

No such capability exists today in the application. Current domain models have
no currency concept; all amounts are implicitly VND.

## 2. Regulatory drivers (verified 2026-08-18)

### 2.1 Accounting regime

- **TT 99/2025/TT-BTC** (new enterprise accounting regime), effective **01/01/2026**,
  replaces **TT 200/2014/TT-BTC**. Entities must revalue monetary FX items at period
  end using **tỷ giá mua bán chuyển khoản trung bình** of the NHTM where the
  enterprise regularly transacts; demand deposits revalued at the bank where the
  account is held. Revaluation postings go directly to 515 (lãi) / 635 (lỗ).
  TK 413 (Chênh lệch tỷ giá) retained (Điều 60). Consistency (nhất quán) principle applies.
- **VAS 10** (QĐ 165/2002/QĐ-BTC, effective 01/01/2003): monetary items at closing
  rate; non-monetary items at historical transaction-date rate; non-monetary at fair
  value use valuation-date rate; FX differences to P&L; TK 413 for certain cases.
- **TT 133/2016/TT-BTC** Điều 52-53 (SME regime): Nợ sides booked at tỷ giá giao dịch
  thực tế; Có sides at tỷ giá ghi sổ bình quân gia quyền or giao dịch thực tế.
- **IAS 21** (reference): functional currency concept, monetary at closing rate,
  non-monetary historical, translation to presentation currency.

### 2.2 E-invoice regime (foreign currency invoices)

- **ND 254/2026/NĐ-CP** (hóa đơn, chứng từ điện tử), effective **01/07/2026**,
  replaces **ND 123/2020**; implements **Luật Quản lý thuế 108/2025/QH15**.
- Invoices may be issued in foreign currency only within permitted FX cases
  (TT 32/2013/TT-NHNN); must state the tỷ giá quy đổi ra VND.
- Tax determination: revenue → tỷ giá mua (buy rate) of commercial bank; expense →
  tỷ giá bán (sell rate) (TT 26/2015/TT-BTC reference).

### 2.3 FX law

- Pháp lệnh ngoại hối 28/2005/PL-UBTVQH11 + Pháp lệnh 06/2013/UBTVQH13 — in force.
- ND 70/2014/NĐ-CP — implementing decree, in force (replaced ND 160/2006).
- TT 32/2013/TT-NHNN — restricts FX use in Vietnam (permitted cases for pricing,
  payment, invoicing in FX).
- ND 340/2025/NĐ-CP — administrative sanctions for monetary/banking violations (2025).

## 3. Scope

### In scope (v1)

1. Currency master data (ISO 4217) — CRUD + activate/deactivate.
2. Exchange rate maintenance — manual entry, batch import, scheduled NHNN source.
3. Base currency (VND) configuration per company (default, immutable).
4. Booking rate (tỷ giá ghi sổ) determination for transactions.
5. Closing-rate revaluation (đánh giá lại cuối kỳ) of monetary items, auto postings
   to 515/635 (direct) with optional TK 413 path per configuration.
6. FX difference reporting (sổ chi tiết chênh lệch tỷ giá).
7. Currency field on Invoice, Voucher, BankAccount; dual-currency amounts (original + VND).
8. Period-lock integration (revaluation only in unlocked periods).
9. Audit trail (audit_log) for rate changes and revaluation runs.
10. RBAC: `@casbin_required` enforcement on all API routes.

### Out of scope (v1)

- Full multi-currency general ledger (per-currency account balances) — v2.
- Automatic daily NHNN rate sync cron — v1.5 (rate import supported in v1).
- FX contract management (forward contracts, hedges) — v2.
- Currency consolidation for multi-company reports — blocked by research gap
  (see AGENTS.md: no consolidation until tenant isolation complete).
- Functional-currency switching mid-period — v2.

## 4. Stakeholders

| Stakeholder | Role |
|---|---|
| Chief Accountant (Kế toán trưởng) | Approves rates, revaluation runs, config |
| Accountant (Kế toán viên) | Enters rates, books FX transactions, runs revaluation |
| Auditor (AUDITOR) | Read-only review of rates, revaluations, FX reports |
| Admin | Currency master data, NHNN source config |
| Tax authority (external) | e-invoice FX reporting compliance |

## 5. Business requirements

### BR-01 Currency master data
BR-01.1 System SHALL support ISO 4217 currency codes (VND, USD, EUR, JPY, GBP,
SGD, CNY, KRW, AUD, THB minimum).
BR-01.2 VND SHALL be default base currency; base currency SHALL be immutable after
first use.
BR-01.3 Currency SHALL have name, symbol, code, decimal places, active flag.
BR-01.4 Deactivated currency SHALL be rejected in new transactions but retained in history.

### BR-02 Exchange rates
BR-02.1 Rate SHALL be stored per (currency, date) — rate valid from that date until
next rate (Tryton pattern).
BR-02.2 Rate SHALL be expressed as VND per 1 unit foreign currency
(or configurable inverse; default VND/FCU).
BR-02.3 Multiple rate types SHALL be supported: buying (mua), selling (bán),
transfer/central (chuyển khoản/trung tâm), booking (ghi sổ).
BR-02.4 Manual entry SHALL require actor + source reference; audit logged.
BR-02.5 Batch import SHALL accept CSV with (date, currency, buy, sell, transfer) rows;
validation errors reported per row.
BR-02.6 NHNN source sync (v1.5) SHALL fetch central rates; third-party modules may
add sources (Odoo provider pattern).

### BR-03 Booking transactions
BR-03.1 Transaction SHALL store original currency amount AND VND equivalent.
BR-03.2 Nợ entries SHALL book at tỷ giá giao dịch thực tế; Có entries at tỷ giá ghi
sổ bình quân gia quyền or giao dịch thực tế (TT 99/2025; TT 133/2016 Điều 52-53).
BR-03.3 Rate used SHALL be recorded on the entry (immutable after post).
BR-03.4 Invoice/voucher in FX SHALL capture e-invoice tỷ giá quy đổi (ND 254/2026).

### BR-04 Period-end revaluation
BR-04.1 Revaluation SHALL apply closing rate (tỷ giá mua bán chuyển khoản trung bình
of NHTM nơi DN giao dịch; demand deposits at bank of account) to monetary items:
cash FX, bank FX, receivables, payables.
BR-04.2 Revaluation SHALL generate automatic journal entries: FX gain → 515,
FX loss → 635 (direct); TK 413 path only for configured cases (Điều 60).
BR-04.3 Revaluation SHALL be per (company, period, date); re-run SHALL be idempotent
(reverses prior run then re-applies) OR blocked for locked periods.
BR-04.4 Revaluation SHALL require unlocked period (period_locks integration).
BR-04.5 Revaluation SHALL require 2nd approval (approver role) before posting
(reference: system-settings 2nd approval pattern).

### BR-05 Reporting
BR-05.1 FX difference report SHALL show per (account, currency, period): opening
balance, movements, closing balance, revaluation adjustment, cumulative difference.
BR-05.2 Rate history report SHALL show rate changes with actor + timestamp + source.
BR-05.3 VND FS totals SHALL be produced with dual-currency breakdown available.

### BR-06 Compliance & audit
BR-06.1 All rate changes, revaluation runs, config changes SHALL be audit-logged
(actor, timestamp, old/new, reason).
BR-06.2 RBAC SHALL enforce: ADMIN/ACCOUNTANT can manage rates; CHIEF_ACCOUNTANT
approves; AUDITOR read-only.
BR-06.3 No SQLAlchemy/Flask imports in domain layer (Clean Architecture rule).

## 6. Success criteria

- Accountant books FX transaction in < 2 min including rate selection.
- Period-end revaluation for 100 accounts < 30 s.
- Revaluation postings balance (debit = credit) always (tol 0.01, matching Voucher rule).
- 100% of rate changes and revaluations in audit log.
- All API routes RBAC-enforced; AUDITOR cannot mutate.
- Domain tests: unit + integration per TESTING_STRATEGY.md.

## 7. Open questions / assumptions

| # | Question | Assumption for v1 | Owner |
|---|---|---|---|
| 1 | NHNN automatic sync in v1? | No — manual + CSV import (v1.5 cron) | BA |
| 2 | TK 413 vs direct 515/635 default? | Default direct; TK 413 flag in CompanyConfig | Chief Acct |
| 3 | Rate source of truth per company? | CompanyConfig: `fx_rate_source` (MANUAL/NHNN/BANK) | BA |
| 4 | Bình quân gia quyền calculation scope? | Per (account, currency) moving average at Có-side booking | Chief Acct |
| 5 | FX on partial payments? | Same rate as invoice unless re-settled (configurable) | Chief Acct |

## 8. Version history

| Ver | Date | Change |
|---|---|---|
| 0.1 | 2026-08-18 | Initial draft after legal + ERP research |