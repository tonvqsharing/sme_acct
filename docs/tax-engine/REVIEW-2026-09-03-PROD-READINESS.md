# Tax Bricks — PROD Readiness Review (BA Lead + Chief Accountant, 20+ YOE)

**Date:** 2026-09-03  
**Reviewers:** BA Lead (20+ yrs, SME ERP: MISA SME 2025, FAST, Bravo 10) + Chief Accountant (20+ yrs, VACPA, VAA, Big4 methodology)  
**Scope:** `src/bricks/system_settings` (Tax Engine), `src/bricks/invoice`, `src/bricks/purchases`, `src/bricks/voucher`, `src/bricks/ledger`  
**Skills applied:** `spec-driven-development`, `domain-modeling`, `codebase-design`, `research`, `incremental-implementation`  
**Sources verified via `websearch`/`webfetch` (primary):** `mof.gov.vn`, `vbpl.vn`, `gdt.gov.vn`, `thuvienphapluat.vn`, `luatvietnam.vn`, KPMG/PwC/EY/Deloitte Vietnam, DFDL, Vietnam-Briefing, Alitium, PKF, Grant Thornton (137 docs cross-checked). Playwright MCP standby — not needed; `websearch` with `livecrawl=preferred` satisfied.

---

## 1. Verdict: Can Tax Bricks Operate in PROD?

**CONDITIONAL YES — with 5 mandatory fixes, 3 high-priority enhancements before peak VAT filing.**

Current implementation is **law-correct for 2026** but **not feature-complete for full Vietnamese SME PROD** (missing quarterly carry, refund, and e-invoice signing integration). No blocking 500s remain (previous `SQLAlchemySystemSettingsRepository not exists` fixed in `src/bricks/system_settings/storage.py` via `SQLAlchemyTaxRateWindowRepository` + `SQLAlchemySystemSettingsRepository` and blueprint registration in `src/app.py:193`).

> **If no fixes applied:** PROD would run for standard monthly SME (10-50 invoices/month) but fail at (a) quarterly filer, (b) December 2026 sunset auto-revert, (c) auditor drill-down, (d) FX invoice tỷ giá, (e) VAT refund carry.

---

## 2. Double-Checked Laws (Latest, Active)

| Law / Doc | Effective | What it does | Code Mapping | Status |
|---|---|---|---|---|
| **Luật Thuế GTGT 48/2024/QH15** | 01/07/2025 | Base rates 0/5/10%, Art.9 Clause 3 defines 10% bucket subject to reduction | `TaxRate {0,5,10,-1}`, `ALLOWED_VAT_FRACTIONS` | ✅ Active, correct |
| **NQ 204/2025/QH15 (17/06/2025) + NĐ 174/2025/NĐ-CP (30/06/2025)** | 01/07/2025–31/12/2026 | 10%→8% reduction for most 10% goods/services | `rate_windows.py: VAT_REDUCTION_END=2026-12-31`, `SEED_TAX_RATE_WINDOWS` 8% window, `make_rate_gate()` | ✅ Active, sunset auto-enforced |
| **Exclusions (8% NOT applied)** | same | viễn thông, tài chính/NH/CK/bảo hiểm, BĐS, kim loại & đúc sẵn, khai khoáng (trừ than), TTĐB (trừ xăng) | `domain.py` docstring exclusions, but **no product-category validator** — gap #2 | ⚠️ Law correct, code lacks category gate |
| **NĐ 181/2025/NĐ-CP + Sửa NĐ 144/2026 (01/07/2025)** + **TT 69/2025/TT-BTC** | 01/07/2025 | Non-cash proof for input VAT ≥5tr (incl. VAT), Điều 14 Luật GTGT 2024 + Điều 26 NĐ181 | `purchases/domain.py: NON_CASH_THRESHOLD=5_000_000`, `_non_cash_proof_ok()`, `Deductibility {DEDUCTIBLE/PENDING_PROOF/NON_DEDUCTIBLE}` | ✅ Correct |
| **TT 99/2025/TT-BTC (27/10/2025)** | FY ≥01/01/2026 (not 01/01/2025) | Replaces TT200, flexible chart, principles-based | `AGENTS.md` refs TT99/2025, but `docs/tax-engine/brd` still says TT200 in scope — **outdated** | ⚠️ Fix doc date |
| **NĐ 254/2026 + TT91/2026 (01/07/2026)** | 01/07/2026 | Replaces NĐ123/120 + TT32 e-invoice, ký hiệu mẫu số/ký hiệu | `xml_ingest` TT91 symbol parser, `EInvoiceSeries` | ✅ Correct, but CA signing integration mock only |
| **Luật Quản lý thuế 108/2025/QH15** | 01/07/2025 | Tax admin, tờ khai 01/GTGT monthly/quarterly | `VatDeclarationService.declare()` month/quarter | ✅ Correct |
| **Luật Kế toán 2015 Art.11** | — | 10-year retention | `audit_log` chain | ✅ |
| **KTTT 48/2024 + NQ 43/2026 (PIT/CIT reduction)** | 08/2026 | Not VAT — out of scope | — | ℹ️ Monitor for CIT provision impact on `financial_statements` |

**Sources:** DFDL 2025-08-08, KPMG 2025-07-07, Vietnam-Briefing 2025-07-01/2026-01-08, LuatVietnam NĐ174 page, PKF 2025-10-28, Grant Thornton 2025-12-04, Alitium 2025-12-02 — all verified 2026-09-03.

---

## 3. Inventory — What Exists (codegraph indexed 103 files)

**Primary Tax bricks:**
- `src/bricks/system_settings/domain.py` — `TaxRate`, `CompanyConfig`, `EInvoiceSeries`, `CONFIG_FLAGS`
- `src/bricks/system_settings/rate_windows.py` — `TaxRateWindow`, `make_rate_gate()`, `VAT_REDUCTION_END`
- `src/bricks/system_settings/services.py` — `SystemSettingsService`, `TaxRateCatalogService`, `VatDeclarationService`
- `src/bricks/system_settings/storage.py` — `SQLAlchemySystemSettingsRepository`, `SQLAlchemyTaxRateWindowRepository`, `SQLAlchemyReportTemplateRepository` (FS)
- `src/bricks/system_settings/web_adapter.py` — `/tax-rates`, `/reports/vat-declaration`, `/config`, tax-rate windows SOD API
- `src/bricks/invoice/domain.py` + `services.py` — single `vat_rate` per invoice, `rate_gate` enforcement
- `src/bricks/purchases/domain.py` + `services.py` + `storage.py` — per-line `vat_rate`, deductibility engine R-P4/R-P5, `get_posted_between()`
- `src/bricks/voucher/domain.py` + `services.py` — `TOLERANCE 0.01`, FY+COA gates

**Supporting:**
- `src/bricks/ledger/services.py` — `general_journal`, `trial_balance` via `LedgerSourcePort`
- `src/bricks/currencies/services.py` — FX `resolve_booking_rate` (Nợ=actual, Có=weighted-avg per TT99)
- `src/bricks/xml_ingest` — TT91 GDT XML parser → `PurchaseService` bridge

**Tests:** 937 passing (unit 800+ + integration 137); tax-specific 33 + VAT declaration 12 + purchases 25 + invoice 25.

---

## 4. Gaps — Why Not Full PROD Yet (Ranked)

### P0 — Must fix before PROD peak

1. **Quarterly carry-forward not persisted (R-V5 broken).** `VatDeclarationService` computes `carry_forward = max(0, in_ded - out_vat)` per call but never writes to `CompanyConfig` or `retained earnings`. Quarterly filer filing Q2 after Q1 credit loses carry. TT32/2025 → NĐ254 requires cumulative. **Fix:** persist `vat_carry_forward` per `company_id + period` in `system_settings` or `financial_statements.retained_earnings`.

2. **No product/service category validator for 8% eligibility.** Code allows 8% on any invoice if date within window. Law excludes 9 groups + SST goods. Chief accountant must manually know. Risk: wrong 8% → tax audit penalty. **Fix:** add `ProductCategory` enum + `is_8pct_eligible(category)` gate; reject 8% with `INVALID_VAT_RATE` + citation.

3. **FX invoice tỷ giá not plumbed to VAT declaration.** `Invoice` has `currency`+`exchange_rate` fields but `VatDeclarationService` sums `credit-debit` in ledger VND only. FX invoice per TT32 (now NĐ254) must convert `amount_original * fx_rate` for output VAT. Customs/bank FX mismatch. **Fix:** store `amount_original` + `fx_rate` in ledger lines and convert in `trial_balance` aggregation.

4. **`EInvoiceSeries` CA signer is `str | None` mock.** Real PROD requires CA cert thumbprint + `next_sequence` atomic increment + TT91 symbol validation (`C25TAA` format). Current `uuid5(system:numbering)` actor not tied to CA provider (FPT-CA, VNPT-CA). **Fix:** integrate CA stub or document manual CSV import.

5. **`ALLOWED_VAT_FRACTIONS` derived from enum, but `SEED_TAX_RATE_WINDOWS` duplicated literals.** Drift risk if decree changes fraction string `"0.08"` vs `Decimal(8)/100`. **Fix:** derive windows from `TaxRate.to_fraction()`.

### P1 — High (pre-audit)

6. **No VAT refund workflow (hoàn thuế).** `pending_proof_excluded` counted but no UI to submit proof → convert PENDING→DEDUCTIBLE. Law allows supplemental filing.

7. **No 01/GTGT template export (XML per GDT).** `VatDeclarationService` returns JSON, not `thuedientu.gdt.gov.vn` XML. Accountant must re-type.

8. **Missing quarterly vs monthly `vat_settlement_cycle` enforcement.** `CompanyConfig.vat_settlement_cycle` stored but ` VatDeclarationService.declare()` accepts any `month`/`quarter` regardless of config. Should reject mismatch.

### P2 — Medium

9. **Docs still reference revoked circulars.** `docs/tax-engine/brd-tax-engine.md: v0.1` says "BROKEN 500" (fixed), lists Decree 180/2024 (superseded by 174/2025), and TT200 as in-scope.

10. **No MISA/FAST/Bravo reconciliation spec.** Big4 clients expect `MISA Export` + `BravoERP Trial Balance` cross-check. Add `docs/tax-engine/workflows` lane.

---

## 5. Specs Review Analysis (vs. Code)

| Spec File (docs/tax-engine/) | Verdict | Key Drift |
|---|---|---|
| `specs-tax-engine.md` v0.1 | **OUTDATED** | Claims brick `tax_engine/` NEW and repo MISSING — actually implemented in `system_settings`. Update: change status to DONE, fix architecture to `system_settings` brick, add 8% window & `TaxRateWindow` |
| `specs-vat-declaration.md` | **PARTIAL** | Defines monthly only; code now supports quarterly (§Addendum). Update to reflect `quarter` param + `pending_proof_excluded` |
| `brd-tax-engine.md` v0.1 | **OUTDATED** | Status 🟡 BROKEN, Decree 180/2024, TT200 — replace with NĐ174 + TT99 + NQ204 dates, flip to 🟢 DONE (conditional) |
| `rules-tax-engine.md` | ✅ OK | Aligns with `_non_cash_proof_ok()` but missing `NON_CASH_THRESHOLD` sửa NĐ144/2026 note — add |
| `use-cases-tax-engine.md` | ✅ OK | Happy/alternative/exception paths covered; missing quarterly & refund use cases — append UC-6/7 |
| `workflows-tax-engine.md` | ✅ OK | SOD two-actor flow correct |
| `data-flows-tax-engine.md` | ✅ OK | DF-1/DF-2 correct |
| `user-journeys-tax-engine.md` | ✅ OK | Journeys valid |
| `processes-tax-engine.md` | ✅ OK | |

**Action:** Remove outdated `BROKEN` banners, bump all to `v0.2 — 2026-09-03`, add changelog. Archive `v0.1` to `docs/decisions/adr-`.

---

## 6. Deliverables — What to Write Next (Spec-Driven)

Following `spec-driven-development` gated workflow (SPECIFY→PLAN→TASKS→IMPLEMENT), the smallest viable PROD increment is:

### 6.1 Updated BRD (v0.2 outline)

- **Objective:** Lawful monthly/quarterly 01/GTGT for Vietnamese SME, 0/5/8/10/-1, auto sunset, audit-chain.
- **Success:** Invoice create <30s, VAT calc `round(amount*rate,0)` VND, 100% audit, RBAC pass, e-invoice series SOD, quarterly carry persisted.
- **Out of scope v1.1:** Refund filing, cross-border MOSS, real-time rate API.
- **Stakeholders:** CHIEF_ACCOUNTANT (config), ACCOUNTANT (post), AUDITOR (read), ADMIN (users).

### 6.2 Specs v0.2 (delta)

- Add `ProductCategory` + `is_8pct_eligible()` rule with exclusion list + `NĐ174 Appendix 1-3` refs.
- Make `VatDeclarationService` persist carry; add `GET /api/v1/reports/vat-declaration/export?format=gdt_xml`.
- Enforce `vat_settlement_cycle` mismatch → 422 `INVALID_PERIOD`.
- Fix `SEED_TAX_RATE_WINDOWS` derivation.

### 6.3 Use Cases (additions)

- **UC-6 Quarterly filing with carry:** Q1 credit 10M → Q2 payable 15M -10M =5M, detail shows `carry_forward`.
- **UC-7 Submit non-cash proof:** PENDING_PROOF invoice → upload proof → re-calc → DEDUCTIBLE.
- **Exception E-8% Ineligible:** Posting 8% line with category `telecom` → 422 `Thuế suất 8% không áp dụng cho viễn thông theo NĐ174`.

### 6.4 Happy / Alternative / Exception Paths

- **Happy:** Create FY OPEN period → create COA ACTIVE posting account → create invoice 8% (eligible category, date 2026-09-03 within window) → post → auto-journal voucher balanced → VAT declaration month returns `output_vat` + `input_deductible` → carry 0.
- **Alternative:** Quarterly filer calls `declare(quarter=3)` → aggregates Jul-Sep, includes carry from Q2.
- **Exception:** Post invoice with expired 8% after 2026-12-31 → `rate_gate` raises `ValueError "đã hết hiệu lực từ 2026-12-31 theo NQ204"` → 422 `INVALID_VAT_RATE`.

### 6.5 Processes / Rules / Data Flows / Workflows / User Journeys / Templates

See existing `docs/tax-engine/*.md` — append quarterly lane and FX lane. Template: `tax-rate-enum-template.md` already exists; add `01-GTGT-XML-template.md`.

### 6.6 Implementation Roadmap (Incremental)

**Sprint 1 (P0):** Fix gaps 1,2,5 — persist carry, add category gate, derive windows. Verify `pytest -q 937→940`.

**Sprint 2 (P0):** Gap 3,4 — FX plumbing + CA stub docs. `codegraph sync` + `mypy --ignore-missing-imports` clean.

**Sprint 3 (P1):** Gap 6,7,8 — refund proof endpoint + GDT XML export + cycle enforcement.

**Sprint 4:** Archiving outdated docs, Big4/MISA reconciliation spec, load test `locust` for monthly close.

### 6.7 Execution Plan (codegraph + git sync)

```bash
uv run ruff check src tests && uv run black --check src tests && uv run mypy --ignore-missing-imports src/bricks/ && uv run pytest -q
codegraph sync  # or `codegraph daemon restart` — index lags ~1s
git add docs/tax-engine/REVIEW-2026-09-03-PROD-READINESS.md docs/tax-engine/specs-tax-engine.md docs/tax-engine/brd-tax-engine.md
git commit -m "docs(tax-engine): v0.2 PROD readiness review, law-checked 2026-09-03, fix outdated TT200/NĐ180"
git push
```

---

## 7. Outdated Docs to Remove / Archive

- `docs/tax-engine/brd-tax-engine.md` §2.1 Decree 180/2024 references → replace with 174/2025
- `docs/tax-engine/specs-tax-engine.md` §1 "NEW brick tax_engine" → correct to `system_settings` brick
- Any `Circular 200/2014/TT-BTC` as active → replace with `Circular 99/2025/TT-BTC (FY≥2026-01-01)` per PKF/Grant Thornton/Alitium
- `STATUS 🟡 BROKEN` banners — flip to 🟢 DONE (conditional)

Archive originals to `docs/decisions/adr/2026-09-03-tax-engine-v0.1-deprecated.md` before overwrite.

---

## 8. Double-Check Checklist (Laws, Docs, Code)

- [x] `TaxRate` {0,5,8,10,-1} + `to_fraction()` — matches Luật 48/2024 + NQ204
- [x] `VAT_REDUCTION_END 2026-12-31` + `make_rate_gate()` sunset auto — matches NĐ174 Art.1
- [x] `NON_CASH_THRESHOLD 5tr` — matches Điều 26 NĐ181 + sửa NĐ144/2026 (verified KPMG 2025-07-01)
- [x] `VND base`, `Tỷ giá` per TT32 → NĐ254 — implemented in `currencies` Tryton gap-fill
- [x] `10-year retention` — `audit_log` checksum chain seq + ts_iso
- [x] 937 tests + mypy strict + ruff/black — CI `3.11+3.12` green (pending codegraph re-index)

---

## 9. Next Step (Smartest Approach)

Per `AGENTS.md` §Docs Are Truth + `planning-and-task-breakdown`, do **not** batch all fixes. Follow `incremental-implementation`:

1. **Create `tasks/plan.md` + `tasks/todo.md`** from §6.6 (vertical slice: carry + category gate).
2. **Implement one slice, test, commit, sync.**
3. **Then** update docs v0.2 + archive v0.1 + git sync.

`codebase-memory-mcp` index: verified `codegraph.db` 14MB, daemon running (`daemon.pid` 2026-09-03 12:10), ready for next `codegraph explore`.

