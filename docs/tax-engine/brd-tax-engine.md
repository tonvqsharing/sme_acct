# BRD — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Module | Tax Engine Config / Tax Rates (System Settings brick) |
| Status | 🟢 DONE — conditional PROD (P0+P1 shipped, 951 tests, gate green) |
| Version | 0.2 |
| Date | 2026-09-03 |
| Author | BA Lead + Chief Accountant (20y, VACPA) + Research (137 docs) |
| Related | System Settings, CompanyConfig, Invoice, Purchases, VAT 48/2024, NQ204/ND174, TT99/2025 |

## 1. Background

Vietnamese SME accounting requires VAT (Thuế GTGT) rate configuration per enterprise.
All businesses must apply correct VAT rates (0%, 5%, 8% temporary, 10%, NOT_TAXED) to taxable
transactions, issue compliant e-invoices per NĐ 254/2026/NĐ-CP (replaced NĐ 123/2020 from 01/07/2026),
and maintain audit trails per Luật Quản lý thuế 108/2025/QH15.

**Implementation is DONE:** `src/bricks/system_settings` (TaxRate, rate windows, VatDeclaration + carry persist, GDT XML),
`invoice`/`purchases` gates (FY period → COA → catalog → 8% category + rate window by document date),
`voucher`/`ledger` gates, all blueprints registered in `src/app.py`, 951 tests. See `REVIEW-2026-09-03-PROD-READINESS.md`.

## 2. Regulatory drivers (verified 2026-09-03 via mof/vbpl/gdt/thuvienphapluat/luatvietnam + Big4)

### 2.1 VAT rate regime

- **VAT Law 48/2024/QH15** — effective 01/07/2025, base rates 0%, 5%, 10%, Art.9 Clause 3 defines 10% bucket subject to reduction
- **NQ 204/2025/QH15 (17/06/2025) + NĐ 174/2025/NĐ-CP (30/06/2025)** — 10%→8% reduction 01/07/2025→31/12/2026, sunset auto via `VAT_REDUCTION_END`
- **NĐ 181/2025/NĐ-CP + Sửa NĐ 144/2026 + TT 69/2025/TT-BTC** — non-cash proof for input VAT ≥5tr (incl. VAT), Điều 14 Luật GTGT 2024 + Điều 26 NĐ181
- **TT 99/2025/TT-BTC (27/10/2025)** — effective FY ≥01/01/2026, replaces TT200/2014, flexible chart (not VAT law)
- **NĐ 254/2026 + TT91/2026 (01/07/2026)** — replaces NĐ123/2020+TT32 e-invoice, ký hiệu mẫu số
- **Luật Quản lý thuế 108/2025/QH15** — effective 01/07/2025

### 2.2 Tax rates (current)

| Rate | Applicable objects | Legal basis |
|---|---|---|
| **0%** | Export goods, international services | VAT 48/2024 Art.9 |
| **5%** | Essential: clean water, medicine, textbooks, fertilizers | VAT 48/2024 Art.10 |
| **10%** | Standard — most goods/services | VAT 48/2024 general |
| **8%** (temporary) | Many 10% supplies reduced 2% 01/07/2025→31/12/2026 | NQ204 + NĐ174 |
| **-1 NOT_TAXED** | Exempt per Điều 5 | VAT 48/2024 Art.5 |

**Excluded from 8% while active (NĐ174 Art.1):** viễn thông, tài chính/NH/CK/bảo hiểm, BĐS, kim loại & đúc sẵn, khai khoáng (trừ than), TTĐB (trừ xăng), `EXCLUDED_FROM_8PCT` + `is_8pct_eligible()`.

### 2.3 E-invoice regime

- **NĐ 254/2026/NĐ-CP** — effective 01/07/2026, replaces NĐ 123/2020; FX invoices state tỷ giá VND per TT 32/2013/TT-NHNN → NĐ254

### 2.4 Stakeholders

| Stakeholder | Role |
|---|---|
| Chief Accountant (Kế toán trưởng) | Configures VAT rates, approves e-invoice series, reviews 01/GTGT |
| Accountant (Kế toán viên) | Enters invoices, validates VAT rates, submits proof, exports GDT XML |
| Auditor (AUDITOR) | Read-only review of rates, invoices, audit log |
| Admin | System configuration, user management |

## 3. Scope

### In scope (v0.2 DONE)

1. **TaxRate enum** — VAT_0(0), VAT_5(5), VAT_8(8 temporary), VAT_10(10), NOT_TAXED(-1) — pure Python
2. **CompanyConfig** — `vat_rates` LAW-type immutable, `vat_settlement_cycle` monthly/quarterly enforce, `CONFIG_FLAGS` allowlist
3. **Rate windows** — `TaxRateWindow` date-effective `SEED_TAX_RATE_WINDOWS` derived from `TaxRate.to_fraction()`, `make_rate_gate()` sunset auto, `is_8pct_eligible()`
4. **VAT validation** — catalog + window by document date + 8% category gate (all invoice lines checked)
5. **Invoice/VAT calc** — `InvoiceItem.vat_rate` × `line_total` → `vat_amount` VND, `quantize(Decimal(1))`
6. **Purchases deductibility** — `Deductibility {DEDUCTIBLE/PENDING_PROOF/NON_DEDUCTIBLE}` + `NON_CASH_THRESHOLD=5tr` + `PENDING_PROOF→DEDUCTIBLE` via `submit_proof` + `POST /purchase-invoices/<iid>/proof`
7. **E-invoice series** — `add_e_invoice_series()` max 15, CA signer, SOD actor≠approver
8. **VAT declaration** — `VatDeclarationService` monthly/quarterly, `vat_payable`/`carry_forward` persist via `vat_carry_forwards` table, cycle enforce, `export_gdt_xml()` `?format=gdt_xml` → `01/GTGT` XML, `pending_proof_excluded` count
9. **RBAC** — `@login_required + role` all routes; AUDITOR read-only
10. **Audit trail** — every config/series/proof change logged with `actor, timestamp, old/new, reason, was:cash`

### Out of scope (v0.2)

- VAT refund cash `hoàn thuế` workflow beyond carry-forward persist
- Real-time VAT rate API — manual catalog only
- Cross-border MOSS

## 4. Stakeholder journeys (high-level)

- **Chief Accountant configures VAT rates**: PATCH `/system_settings/config` LAW-type locked → migration only; cycle monthly/quarterly via `with_flag_update`
- **Accountant enters invoice 8%**: Creates invoice 8% with `category=manufacturing` + date within window → auto calc 8%; `telecom`→422 `không áp dụng cho nhóm telecom`
- **Accountant fixes proof**: `POST /purchase-invoices/<iid>/proof` on PENDING_PROOF → DEDUCTIBLE
- **Accountant files 01/GTGT**: `GET /reports/vat-declaration?month=8` → `payable/carry` + `?format=gdt_xml` → upload `thuedientu.gdt.gov.vn`
- **Auditor reviews**: GET config/rate windows/invoices — read-only

## 5. Success criteria

- Invoice create <30s, VAT calc `round(amount*rate,0)` VND correct
- 8% gate blocks all 9 excluded categories on every line
- 100% config/series/proof audit-logged with `was:` trail
- Quarterly carry Q1→Q2 persists, cycle mismatch →422
- GDT XML valid for `thuedientu`
- 951 tests, gate green 3.11+3.12

## 6. Open questions / assumptions

| # | Question | Answer v0.2 | Owner |
|---|---|---|---|
| 1 | VAT 8% support? | Yes — derived windows + category gate, sunset 31/12/2026 auto | BA |
| 2 | E-invoice max 15? | Yes — per NĐ254, enforce | Chief Acct |
| 3 | VAT rate change? | LAW-type migration only | BA |
| 4 | RBAC? | ADMIN+CHIEF for CONFIG, AUDITOR read-only | RBAC |
| 5 | Carry persist? | Yes — `vat_carry_forwards` table, monthly/quarterly | BA |

## 7. Version history

| Ver | Date | Change |
|---|---|---|
| 0.1 | 2026-08-18 | Initial draft after legal+ERP research (BROKEN) |
| 0.2 | 2026-09-03 | P0+P1 shipped: 8% windows+gate, carry persist, GDT XML, proof workflow, 951 tests, gate green — law re-checked via 137 primary sources |
