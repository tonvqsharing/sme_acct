# ADR-003: Currencies & Exchange Rates Module Design

## Status
Accepted (2026-08-18 — signed off)

## Date
2026-08-18

## Context

Vietnamese SME accounting requires:

1. Recording foreign-currency transactions in original currency AND VND equivalent.
2. Period-end revaluation of monetary FX items at the closing rate.
3. Booking FX differences to P&L (TK 515/635) or TK 413 per the new regime.
4. E-invoice FX data capture per ND 254/2026/NĐ-CP (effective 01/07/2026).
5. Financial statements presented in VND.

Current codebase (verified 2026-08-18 via codegraph): **no currency/FX capability exists.**
All amounts are implicitly VND Decimals. No Currency/ExchangeRate/Revaluation entities,
no FX tables, no FX API routes, no FX config flags.

Regulatory anchor points (all primary-source verified):
- **TT 99/2025/TT-BTC** (effective 01/01/2026, replaces TT 200/2014): revalue monetary
  FX items at tỷ giá mua bán chuyển khoản trung bình of NHTM nơi DN thường xuyên giao
  dịch; demand deposits at bank of account; consistency principle; direct post to 515/635;
  TK 413 per Điều 60.
- **VAS 10** (QĐ 165/2002/QĐ-BTC): monetary at closing rate; non-monetary at historical.
- **TT 133/2016/TT-BTC** Điều 52-53 (SME): Nợ at actual transaction rate; Có at bình
  quân gia quyền or actual.
- **ND 254/2026/NĐ-CP** + Luật 108/2025/QH15: e-invoice FX rules, tỷ giá quy đổi mandatory.
- **Pháp lệnh ngoại hối 2005/2013 + ND 70/2014/NĐ-CP + TT 32/2013/TT-NHNN**: FX use limits.
- **IAS 21** (reference): functional currency, monetary at closing rate.
- ERP benchmarks: Tryton (rate = (currency, date), base rate=1, scheduled updates),
  Odoo currency_rate_update (provider pattern, ECB source), MISA/Fast/Bravo/est-invoice
  (NHNN as rate source).

## Decision

Adopt the following design for v1 (specified in `docs/currencies-exchange/`):

1. **Domain entities** (pure Python, no sqlalchemy/Flask):
   - `Currency` (ISO 4217, decimal places, active, base flag).
   - `ExchangeRate` (currency, rate_date, rate_type, rate, source, actor) —
     immutable history; new row supersedes old (Tryton semantics).
   - `RevaluationRun` + `RevaluationEntry` (status machine DRAFT→PENDING_APPROVAL→
     APPROVED→POSTED/REVERSED).
   - `FXDifference` for reporting.

2. **Booking-rate rule (R1)** hard-coded in service:
   - Nợ side → actual transaction rate (giao dịch thực tế).
   - Có side → weighted average `Σ(orig×rate)/Σ(orig)` or actual, per config.

3. **Revaluation algorithm (R2/R3/D6)**:
   - Closing rate = tỷ giá mua bán chuyển khoản trung bình (transfer type).
   - Difference → 515 (gain) / 635 (loss) direct by default; TK 413 path per config.
   - Postings must balance (tol 0.01); atomic transaction; idempotent re-run.

4. **Config flags on CompanyConfig** (reuse ADR-001 aggregate):
   - LAW: base_currency, fx_gain_account(515), fx_loss_account(635), booking-rate side rules.
   - CONFIG: fx_rate_source, fx_revaluation_account(DIRECT/413),
     fx_revaluation_approval_required, fx_nhnn_auto_sync (v1.5).

5. **Persistence**: SQLAlchemy 2.0 models (`currencies`, `exchange_rates`,
   `revaluation_runs`, `revaluation_entries`, `fx_differences`) + flask-migrate.

6. **API + RBAC**: REST blueprint `currencies_bp.py`; every route `@casbin_required(...)`;
   AUDITOR read-only; actor UUID required on all mutations; audit_log wiring.

7. **Rate sources**: MANUAL + CSV import in v1; NHNN sync (provider pattern) v1.5 —
   matches Tryton/Odoo precedent, avoids blocking on external service (Tryton forum lesson).

8. **Out of scope v1** (explicit): per-currency GL, forward contracts, multi-company
   consolidation (blocked by tenant-isolation research gap per AGENTS.md).

## Consequences

Positive:
- Domain rules R1–R8 testable pure (unit tests per TESTING_STRATEGY.md).
- History-preserving rates → full audit trail, no in-place edits.
- Period-lock + approval chain prevent FS restatement accidents.
- Aligned with TT 99/2025 + ND 254/2026 → compliance-ready.
- Matches ERP best practice (Tryton/Odoo) → proven patterns.

Negative:
- Schema changes on Invoice/Voucher/BankAccount (currency + dual amounts) — migration
  needed, existing tests must be revisited.
- Weighted-average complexity — needs careful unit coverage.
- NHNN sync deferred to v1.5 → manual entry burden until then.
- Greenfield: full module build before any PROD use (see production-readiness audit).

## Alternatives considered

1. **Multi-currency GL from day 1** — rejected: large scope, conflicts with
   AGENTS.md multi-company blocker; VND-reporting requirement can be met with
   dual-currency fields + revaluation.
2. **Odoo-style provider with ECB source** — rejected for v1: Vietnamese regime
   mandates NHNN-commercial-bank rates, not ECB; NHNN fetcher scheduled v1.5.
3. **In-place rate editing** — rejected: breaks audit trail; immutability chosen.

## References

- docs/currencies-exchange/README.md, brd-currencies.md, specs-currencies.md,
  rules-currencies.md, production-readiness-audit-currencies.md
- ADR-001 (CompanyConfig), ADR-002 (Company entity)
- TT 99/2025/TT-BTC, ND 254/2026/NĐ-CP, VAS 10, TT 133/2016, IAS 21,
  Pháp lệnh ngoại hối 2005/2013, ND 70/2014/NĐ-CP, TT 32/2013/TT-NHNN,
  ND 340/2025/NĐ-CP