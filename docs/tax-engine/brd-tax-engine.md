# BRD — Tax Engine Config / Tax Rates Module

| | |
|---|---|
| Module | Tax Engine Config / Tax Rates |
| Status | 🟡 BROKEN — REST API 500, blueprint not registered; domain layer OK |
| Version | 0.1 |
| Date | 2026-08-19 |
| Author | BA Lead + Chief Accountant research team |
| Related | System Settings, CompanyConfig, Invoice, VAT Law 48/2024/QH15, Circular 99/2025/TT-BTC |

## 1. Background

Vietnamese SME accounting requires VAT (Thuế GTGT) rate configuration per enterprise.
All businesses must apply correct VAT rates (0%, 5%, 10%, and temporary 8%) to taxable
transactions, issue compliant e-invoices per ND 123/2020/NĐ-CP (replaced by ND 254/2026/NĐ-CP
from 01/07/2026), and maintain audit trails per Luật Quản lý thuế 108/2025/QH15.

The application has **domain-layer tax support** (TaxRate enum, VAT validation, Invoice
VAT calculation) but the **REST API is broken** — all `/api/v1/system_settings/*` routes
return 500 because `SQLAlchemySystemSettingsRepository` does not exist. The blueprint
is also not registered in `app.py`. This module must be fixed before any PROD operation.

## 2. Regulatory drivers (verified 2026-08-19)

### 2.1 VAT rate regime

- **VAT Law No. 13/2008/QH12** (modified by Law No. 31/2013/QH13, Law No. 71/2014/QH13)
- **VAT Law No. 48/2024/QH15** — effective **01/07/2025**, new VAT framework, three main
  rates: 0%, 5%, 10%; temporary 8% reduction from 01/07/2025 to 31/12/2026 per Decree
  180/2024/ND-CP for many 10%-rated supplies.
- **Decree 180/2024/ND-CP** — VAT rate adjustment, 2% reduction from 10% to 8% for
  eligible supplies, extended through 31/12/2026.
- **Circular 219/2013/TT-BTC** — VAT implementation guidance, rates, invoicing.
- **Circular 99/2025/TT-BTC** — effective **01/01/2026**, replaces Circular 200/2014/TT-BTC,
  focuses on accounting regime (chart of accounts, financial statements), does NOT regulate
  tax obligations (those governed separately by tax law).
- **ND 123/2020/NĐ-CP** — e-invoice regime, replaced by **ND 254/2026/NĐ-CP** from
  **01/07/2026**; invoices must state tỷ giá quy đổi ra VND for FX invoices.
- **Luật Quản lý thuế 108/2025/QH15** — effective 01/07/2025, Tax Administration Law.

### 2.2 Tax rates (current, verified 2026-08-19)

| Rate | Applicable objects | Legal basis |
|---|---|---|
| **0%** | Export goods, international services, non-taxable exports | Law on VAT Art. 9; Circular 219/2013/TT-BTC |
| **5%** | Essential goods: clean water, medicine, medical equipment, textbooks, fertilizers | Law on VAT Art. 10; Circular 219/2013/TT-BTC |
| **10%** | Standard rate — most goods and services | Law on VAT General rate |
| **8%** (temporary) | Many supplies normally 10%, reduced by 2% from 01/07/2025 to 31/12/2026 | Decree 180/2024/ND-CP; VAT Law 48/2024/QH15 |

**Sectors excluded from 8% reduction:** telecommunications, IT/software, banking/finance/insurance,
real estate, metals/mining/petroleum, goods subject to special consumption tax.

### 2.3 E-invoice regime

- **ND 254/2026/NĐ-CP** — effective 01/07/2026, replaces ND 123/2020
- All businesses must use e-invoices (declaration method)
- Invoices in FX must state tỷ giá quy đổi ra VND (per TT 32/2013/TT-NHNN)
- Tax: revenue → tỷ giá mua (buy rate) commercial bank; expense → tỷ giá bán (sell rate)

### 2.4 Stakeholders

| Stakeholder | Role |
|---|---|
| Chief Accountant (Kế toán trưởng) | Configures VAT rates, approves e-invoice series |
| Accountant (Kế toán viên) | Enters invoices, validates VAT rates, generates e-invoices |
| Auditor (AUDITOR) | Read-only review of rates, invoices, audit log |
| Admin | System configuration, user management |

## 3. Scope

### In scope (v1)

1. **TaxRate enum** — VAT_0 (0%), VAT_5 (5%), VAT_10 (10%), NOT_TAXED (−1) —
   domain entity, pure Python, no SQLAlchemy/Flask imports.
2. **CompanyConfig vat_rates** — frozenset[int] = {0, 5, 10} — LAW-type flag, immutable
   without migration (FlagLockedError pattern, per system-settings).
3. **VAT validation service** — `validate_vat_rate(rate)` — rejects rates outside {0, 5, 10};
   raises InvalidRegimeError.
4. **Invoice VAT calculation** — `InvoiceItem.vat_rate` × `line_total` → `vat_amount`; auto-
   recalc on item add/edit; rounding tol implied.
5. **E-invoice series management** — `add_e_invoice_series()` — max 15 active series per
   company; requires CA signer; audit-logged; CONFIG-type with 2nd-approval pattern.
6. **RBAC** — `@casbin_required` on all API routes; AUDITOR read-only everywhere.
7. **Audit trail** — every VAT rate change, e-invoice series add, config update logged
   (actor, timestamp, old/new, reason).

### Out of scope (v1)

- VAT rate 8% temporary reduction — CONFIG-type flag could be added later;
  not in current `vat_rates` frozenset.
- Multi-currency VAT (code has `currency` + `exchange_rate` on Invoice but VAT always
  calculated in VND per Vietnamese law).
- Real-time GST/VAT rate fetching from external APIs — manual config only.
- Input VAT credit/refund workflow — out of scope v1.
- Cross-border VAT MOSS/One-Stop Shop — v2.

## 4. Stakeholder journeys (high-level)

- **Chief Accountant configures VAT rates**: Sets CompanyConfig `vat_rates` frozenset via
  API PATCH /api/v1/system_settings/config; requires 2nd approval (CHIEF_ACCOUNTANT);
  LAW-type immutable without migration.
- **Accountant enters invoice**: Creates Invoice with items, each with `vat_rate` from
  TaxRate enum {0, 5, 10}; system auto-calculates `vat_amount`; posts e-invoice series.
- **Auditor reviews tax treatment**: GET /api/v1/system_settings/config; views rate
  history, config changes with actor + timestamp; read-only, no mutation possible.

## 5. Success criteria

- Accountant creates invoice with VAT in < 30 s including rate selection.
- VAT amount calculated correctly: `round(line_total × rate / 100, 2)`.
- 100% of VAT rate changes and e-invoice series adds audit-logged.
- All API routes RBAC-enforced; AUDITOR cannot mutate.
- Domain tests pass; repository adapter implemented; blueprint registered.

## 6. Open questions / assumptions

| # | Question | Assumption for v1 | Owner |
|---|---|---|---|
| 1 | VAT rate 8% temporary support? | No — rates {0, 5, 10} only; 8% flag can be added v2 | BA |
| 2 | E-invoice series max 15? | Yes — per ND 254/2026/NĐ-CP, enforced by service | Chief Acct |
| 3 | VAT rate change requires migration? | LAW-type flags immutable without migration (FlagLockedError) | BA |
| 4 | RBAC roles for VAT config? | ADMIN + CHIEF_ACCOUNTANT for CONFIG-type; AUDITOR read-only | RBAC |

## 7. Version history

| Ver | Date | Change |
|---|---|---|
| 0.1 | 2026-08-18 | Initial draft after legal + ERP research |