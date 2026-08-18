# Currencies & Exchange Rates Module — README

## Status: 📋 DESIGNED — NOT IMPLEMENTED — NOT PROD-READY

**Verdict: Module does not exist in codebase. Cannot operate in PROD ENV.**

Current codebase (Flask + Clean Architecture, src/):
- No `Currency` entity, no `ExchangeRate` entity, no FX service.
- No currency fields on `InvoiceModel`, `VoucherModel`, `PartnerModel`, `BankAccountModel`.
- `CompanyConfig` has no currency-related flags.
- Money handled as `Decimal` (VND-only, no currency context).

This module must be **built from scratch**. This doc set is the complete
business + technical specification for that build.

## Why now (2026 regulatory drivers)

| Driver | Legal basis | Effective |
|---|---|---|
| New enterprise accounting regime (replaces TT 200/2014) | **TT 99/2025/TT-BTC** | 01/01/2026 |
| New e-invoice / e-document regime (replaces ND 123/2020) | **ND 254/2026/NĐ-CP** | 01/07/2026 |
| New Tax Administration Law | **Luật 108/2025/QH15** | 01/07/2026 |
| FX use restrictions still governed by | Pháp lệnh ngoại hối 2005 (sửa đổi 2013) + ND 70/2014/NĐ-CP + TT 32/2013/TT-NHNN | in force |
| Sanctions for monetary/banking violations | **ND 340/2025/NĐ-CP** | 2025+ |

> ⚠️ Any existing docs referencing TT 200/2014 as *current* accounting regime are
> OUTDATED. TT 99/2025 applies from 01/01/2026. See `rules-currencies.md`.

## Doc index

| Doc | Purpose |
|---|---|
| [BRD](brd-currencies.md) | Business requirements, scope, stakeholders |
| [Specs](specs-currencies.md) | Technical/functional spec, data model, API |
| [Use cases](use-cases-currencies.md) | UC-01..UC-12 with happy/alt/exception paths |
| [Processes](processes-currencies.md) | End-to-end business processes |
| [Rules](rules-currencies.md) | Legal rules + domain rules (hard-coded) |
| [Data flows](data-flows-currencies.md) | DF diagrams + flows |
| [Workflows](workflows-currencies.md) | State machines, approvals, statuses |
| [User journeys](user-journeys-currencies.md) | Role-based journeys |
| [Prod-readiness audit](production-readiness-audit-currencies.md) | Gap analysis, verdict NOT PROD-ready |
| [SIGN-OFF](SIGN-OFF.md) | Sign-off ledger |
| [Templates](templates/) | Test plan, rate import, revaluation worksheet |

## Core concepts (summary)

- **Base currency (VND)** — reporting currency per TT 99/2025 (kế toán bằng Đồng Việt Nam).
- **Foreign currency** — USD, EUR, JPY, GBP, SGD, CNY, KRW, AUD, THB, ... (ISO 4217).
- **Tỷ giá ghi sổ (booking rate)** — rate used to record transaction in VND.
  - Nợ (receivable/expense): tỷ giá giao dịch thực tế.
  - Có (payable/revenue): tỷ giá ghi sổ bình quân gia quyền hoặc giao dịch thực tế.
  - (per TT 99/2025, mirroring TT 133/2016 Điều 52-53 for SMEs)
- **Tỷ giá quy đổi cuối kỳ (closing rate)** — tỷ giá mua bán chuyển khoản trung bình
  của NHTM nơi doanh nghiệp thường xuyên giao dịch, at period end.
- **Chênh lệch tỷ giá (FX difference)** — post to 515 (lãi) / 635 (lỗ).
- **TK 413 Chênh lệch tỷ giá** — for certain revaluation/translation cases (TT 99/2025 Điều 60).

## References (primary sources, verified 2026-08-18)

- Thông tư 99/2025/TT-BTC — chế độ kế toán doanh nghiệp mới (thay TT 200/2014), hiệu lực 01/01/2026.
- Nghị định 254/2026/NĐ-CP — hóa đơn, chứng từ điện tử, hiệu lực 01/07/2026.
- Luật Quản lý thuế 108/2025/QH15 — hiệu lực 01/07/2026.
- VAS 10 (QĐ 165/2002/QĐ-BTC) — Ảnh hưởng của việc thay đổi tỷ giá hối đoái.
- TT 200/2014/TT-BTC Điều 69 (TK 413) — legacy reference only.
- TT 133/2016/TT-BTC Điều 52-53 — SME regime reference (mirrored in TT 99/2025).
- IAS 21 — The Effects of Changes in Foreign Exchange Rates (functional currency).
- Pháp lệnh ngoại hối 28/2005/PL-UBTVQH11 + Pháp lệnh 06/2013/UBTVQH13; ND 70/2014/NĐ-CP; TT 32/2013/TT-NHNN; ND 340/2025/NĐ-CP.
- ERP benchmarks: Tryton currency module (rate per date, base currency rate=1, ECB source), Odoo currency_rate_update (provider pattern), MISA/Fast/Bravo/est-invoice (NHNN rate source).
- Official portals verified ACTIVE (2026-08-18, playwright): thuedientu.gdt.gov.vn (eTax v3.1.3), gdt.gov.vn, sbv.gov.vn.

## Related docs / modules

- `docs/system-settings/` — CompanyConfig, period locks (FX revaluation needs period lock).
- `docs/company-module/` — Company entity, BankAccountModel (needs currency field).
- `docs/multi-company/` — tenant isolation (currencies are per-company).
- `docs/decisions/ADR-003-currencies-exchange.md` — ADR for this module.