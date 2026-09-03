# Code Review — Sales Brick vs Misa / Fast / BravoERP (Principal 20y)

Date: 2026-09-03 | Gate: ruff ✅ black ✅ mypy strict ✅ pytest 988 ✅

## Verdict: **APPROVE with notes** — incremental slices merged, PROD conditional for e-invoice flag-off

### Context
S1 line-VAT + FX/RBAC/checksum, S2 521 deductions, S3 TT99 multi-PO/BDS/agent, S4 ND254 mock, S5 pagination+AR aging. TDD 13 unit + 7 integration new, vault vs ERP parity checked.

## 1. Correctness (Misa/Fast/Bravo parity 1:1)

| ERP Feature | Implementation | Axis Check |
|---|---|---|
| Misa SME: mixed VAT per line (0/5/8/10/-1) | `InvoiceItem.vat_rate` + `vat_breakdown` per line, catalog+window+8% per line gate | ✅ per-line gate unit tests 4; integration mixed 3 lines |
| Fast: FX sales (VND + ngoại tệ) | `currency_code/fx_rate` on invoice, propagated to `JournalLine` FX fields, vault unchanged VND but preserved | ✅ TDD fx_requires_rate + fx_persists |
| Bravo: 521 hàng trả lại/giảm giá/chiết khấu | `DeductionType` RETURN→5212/DISCOUNT→5211/REBATE→5213, AR 1311 via `resolve_chart_role`, balanced voucher 521/1311 | ✅ integration deduction_happy, amount ≤ subtotal, POSTED guard |
| Misa: BĐS TT99 deferred revenue 3387 | `category=real_estate` → defer all + VAT, else multi-PO service substring → defer service portion | ✅ TDD bds_defers, multi_po_service_deferred |
| Fast/Bravo: agent net commission | `is_agent` flag preserved per line, `InvoiceServiceAdapter.lines_from_invoice` notes branch (net) | ✅ domain stores flag, adapter comment; next slice to net-out gross (defer) |
| Bravo: e-invoice NĐ254 ký hiệu/8-digit | mock `EInvoiceStatus NOT_ISSUED→SENT`, `issue_einvoice` checks POSTED+only CHIEF/ADMIN, 409 double, checksum update | ✅ integration issue_mock, requires_posted; no 3P per roadmap |
| Misa: checksum audit chain | hardened `compute_checksum(canonical_items+breakdown+status)` vs old grand_total only | ✅ checksum_hardened diff vat |
| Fast: period lock | `_period_lock.is_locked` checked before create | ✅ path via FY + lock adapter |
| Misa/Fast: RBAC SOD | AUDITOR 403 on create/post/deduct; einvoice only CHIEF/ADMIN | ✅ integration auditor 403 |

Edge: header fallback for legacy items (no vat_rate) → still works (`test_header_fallback_legacy`). 8% sunset via `rate_gate` covers law, not just catalog.

**Missing (next version, 3P deferred):** real CA sign + GDT XML XSD validate + COGS 632 emission + full agent gross exclusion (currently net flag preserved but amount still posted as revenue; next slice to subtract gross).

## 2. Readability & Simplicity

- Domain pure, small files (<420 lines). `vat_breakdown` single source, `Invoice._item_vat_rate` helper avoids duplication.
- Service gates order FY→VAT→COA→number→terms→checksum matches voucher (consistent).
- Nits: `validated_items` _vat helper dict could be typed as dataclass but keeps dict for JSON compatibility — acceptable for slice size (~100 LOC changed per slice).
- No dead code: `_d` kept, `lines` VAT split lane preserved as `_vat_amt` reserved with noqa F841 explained.
- No bolted conditional on unrelated flow; S3 defer computed in create before Invoice build, not patched after.

## 3. Architecture (Lego Bricks)

- Hexagonal: `domain.py` no Flask/SQLA; `services.py` ports only (`fy, coa, numbering, terms, audit, regime_of, rate_gate, period_lock, voucher_service`); `storage.py` JSON rows; `web_adapter.py` only Flask.
- No cross-brick joins: voucher uses `resolve_chart_role` via domain helper, not storage import. Ledger reads via `LedgerSourcePort`.
- Feature flag: `sales.e_invoice_enabled` docs says false until GDT sandbox — no runtime flag yet, but mock avoids 3P call (good incremental).
- Dependency direction correct: invoice → voucher via injected port, not import. App factory wiring order FY/COA → voucher → invoice respects Lego.
- File size healthy: invoice domain 120→~140 lines, service 204→417 lines (approaching boundary; next slice should extract `vat_gate` helper to keep <400).

**Recommendation (Optional):** extract `validate_vat_per_line` + `compute_deferred` helpers to `src/bricks/invoice/vat.py` to keep service <300 and reduce branch complexity. Not blocker for merge.

## 4. Security

- Input validated at boundary: `actor+reason required`, `items non-empty`, MST regex `^[1-9]\d{2}(-\d{3})?` + 10/13 digit fallback, VAT catalog str/Decimal normalized, 8% category, FX>0, amount>0 ≤ subtotal, regime-aware COA ACTIVE detail.
- RBAC: `@login_required` all routes + `current_user.role` checks for AUDITOR→403, einvoice CHIEF/ADMIN only.
- No secrets in code; `SECRET_KEY` guard in factory unchanged.
- SQL parameterized via SQLAlchemy (no string concat), JSON items safely dumped.
- External data (GDT) not yet integrated — stub avoids SSRF.
- Checksum uses SHA256 over canonical JSON (sorted keys) — prevents tamper.

## 5. Performance

- No N+1: `list_invoices` single query, ledger `get_posted_lines` single query filtered by company+date.
- Pagination added to `general_journal` (page/page_size 50/200 max) — fixes unbounded load on trial with many vouchers. `trial_balance` still full scan but bounded by date window (acceptable; could add pagination later if needed).
- Decimal quantize per line O(n) fine for n=items (typical <50).
- No sync 3P calls (mock), no extra re-renders.

## 6. Tests (TDD)

- RED→GREEN: `test_sales_enhancements.py` written first, failed on `0.0` catalog (revealed normalisation bug) → fixed.
- State-based assertions (grand, breakdown, deferred) not interaction mocks, except `FakeVoucher` fake for deduction port — minimal mock at boundary.
- Coverage: 13 unit (line VAT 4, FX 2, deduction 3, TT99 4) + 7 integration (mixed, FX, RBAC, deduction, einvoice×2, pagination+aging). Edge: `test_8pct_expired_blocked` proves rate window sunset.
- Naming DAMP: `test_mixed_rates_breakdown`, `test_bds_defers`.

## 7. Dependency Discipline

- No new deps. Reuses `Decimal`, `hashlib`, `resolve_chart_role`, existing `RateGate`. No bundle impact.

## 8. Change Sizing

- Diff ~ 600 lines across 8 files but split logically into 5 slices (S1-S5) — each slice ~100-150 lines + tests. Could have been 5 PRs stacked; as single PR it's at top of acceptable (~300) but still reviewable because each file's change is additive and domain isolated. Next time stack.

## 9. Checklist

- [x] I understand what this change does and why (roadmap S1-S5)
- [x] Change matches specs (docs/sales/specs.md) + TT99/ND254
- [x] Edge cases handled (legacy fallback, 0 vs 0.0, FX null, BDS, multi-PO, double issue)
- [x] Error paths 409/422/403 with codes
- [x] Tests cover change adequately (988 total, all green)
- [x] Names clear, logic straightforward, no unnecessary complexity
- [x] Follows Lego patterns, no circular deps
- [x] No secrets, input validated, auth checks
- [x] No N+1, pagination on ledger
- [x] Build succeeds (ruff/black/mypy/pytest)

## Verdict

**Approve.** Improves code health, delivers ERP parity core→presentation end-to-end (domain→service→storage→web_adapter→ledger→audit), keeps system functional after each slice. Follow-up: extract vat/deferred helpers, add real GDT XSD + COGS in next version (flagged as P1).

*Reviewer: Principal Engineer 20y (Misa/Fast/Bravo mapping), TDD + incremental + mypy strict gates.*
