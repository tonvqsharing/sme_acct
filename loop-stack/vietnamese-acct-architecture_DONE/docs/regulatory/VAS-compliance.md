# Vietnamese Accounting Standards (VAS) Compliance

## Overview

All 26 VAS issued by the Ministry of Finance (2001–2005), based on older IAS/IFRS. VAS use rules-based approach with prescribed COA and financial statement templates. This document maps each standard to domain modules.

## VAS Standards Mapping

| # | Standard | Vietnamese Name | IAS/IFRS Equivalent | Applicability | Domain Module(s) | Key Requirements |
|---|----------|-----------------|---------------------|---------------|------------------|------------------|
| 1 | VAS 01 | Chuẩn mực kế toán số 01 — Khung thuyết minh và trình bày BCTC | IAS 1 | **Core** | ChartOfAccounts, Reporting | Prescribes COA structure, VND currency, financial statement format (B01-DN, B02-DN, B03-DN) |
| 2 | VAS 02 | Chuẩn mực kế toán số 02 — Hàng tồn kho | IAS 2 | **Core** | Inventory | FIFO/weighted avg valuation; Account 156 |
| 3 | VAS 03 | Chuẩn mực kế toán số 03 — Tài sản cố định hữu hình | IAS 16 | **Core** | FixedAssets | Cost model only, no revaluation; Accounts 153, 21x |
| 4 | VAS 04 | Chuẩn mực kế toán số 04 — Tài sản cố định vô hình | IAS 38 | **Core** | FixedAssets | Recognition/amortization; Accounts 154, 24x |
| 5 | VAS 05 | Chuẩn mực kế toán số 05 — Bất động sản đầu tư | IAS 40 | Low | FixedAssets | Investment property; SMEs rarely applicable |
| 6 | VAS 06 | Chuẩn mực kế toán số 06 — Lease (Cho thuê) | IAS 17 | **Core** | FixedAssets | Operating lease only, periodic expense recording |
| 7 | VAS 07 | Chuẩn mực kế toán số 07 — Đầu tư vào liên doanh | IAS 28 | Low | — | Equity method for associates |
| 8 | VAS 08 | Chuẩn mực kế toán số 08 — Báo cáo tài chính cho liên doanh | IAS 31 | Low | — | BCC/joint venture reporting |
| 9 | VAS 10 | Chuẩn mực kế toán số 10 — Tác động của biến động tỷ giá | IAS 21 | **Core** | GeneralLedger | Multi-currency, exchange differences; Accounts 413, 811/711 |
| 10 | VAS 11 | Chuẩn mực kế toán số 11 — Sáp nhập kinh doanh | IFRS 3 | Low | — | M&A accounting |
| 11 | VAS 14 | Chuẩn mực kế toán số 14 — Doanh thu và thu nhập khác | IAS 18 | **Core** | Sales | Revenue recognition; Accounts 511, 515, 711 |
| 12 | VAS 15 | Chuẩn mực kế toán số 15 — Hợp đồng xây dựng | IAS 11 | Medium | Sales | Percentage-of-completion for construction |
| 13 | VAS 16 | Chuẩn mực kế toán số 16 — Chi phí đi vay | IAS 23 | Medium | GeneralLedger | Capitalization of borrowing costs |
| 14 | VAS 17 | Chuẩn mực kế toán số 17 — Thuế thu nhập doanh nghiệp | IAS 12 | **Core** | Tax | Deferred tax, CIT; Accounts 333, 82112 GMT |
| 15 | VAS 18 | Chuẩn mực kế toán số 18 — Dự phòng, nợ tiềm tàng và tài sản tiềm tàng | IAS 37 | **Core** | GeneralLedger | Provisions; Account 351 |
| 16 | VAS 19 | Chuẩn mực kế toán số 19 — Hợp đồng bảo hiểm | IFRS 4 | Low | — | Insurance-specific |
| 17 | VAS 21 | Chuẩn mực kế toán số 21 — Trình bày BCTC | IAS 1 (revised) | **Core** | Reporting | Balance Sheet (B01-DN), P&L (B02-DN), Cash Flow (B03-DN), Notes |
| 18 | VAS 22 | Chuẩn mực kế toán số 22 — BCTC bổ sung cho tổ chức tín dụng | IAS 30 | N/A | — | Credit institutions excluded from Circular 99 scope |
| 19 | VAS 23 | Chuẩn mực kế toán số 23 — Sự kiện sau ngày lập BCTC | IAS 10 | Medium | Reporting | Adjusting/non-adjusting events |
| 20 | VAS 24 | Chuẩn mực kế toán số 24 — Báo cáo lưu chuyển tiền tệ | IAS 7 | **Core** | Reporting | B03-DN cash flow statement |
| 21 | VAS 25 | Chuẩn mực kế toán số 25 — BCTC hợp nhất | IAS 27 | Low | — | Single-company scope, no consolidation |
| 22 | VAS 26 | Chuẩn mực kế toán số 26 —披露 liên quan đến bên liên quan | IAS 24 | Medium | Reporting | Related party note disclosures |
| 23 | VAS 27 | Chuẩn mực kế toán số 27 — BCTC giữa kỳ | IAS 34 | Low | Reporting | Optional interim reports |
| 24 | VAS 28 | Chuẩn mực kế toán số 28 — Báo cáo theo phân khúc | IAS 14 | Low | Reporting | Optional segment reporting |
| 25 | VAS 29 | Chuẩn mực kế toán số 29 — Thay đổi chính sách, ước tính và sai sót | IAS 8 | **Core** | GeneralLedger | Transitional guidance for Circular 99 adoption |
| 26 | VAS 30 | Chuẩn mực kế toán số 30 — Lợi nhuận trên cổ phiếu | IAS 33 | Low | — | SMEs rarely issue shares |

## Applicability Legend

- **Core**: Directly impacts accounting software domain model or reporting
- **Medium**: May apply depending on business type
- **Low**: Not applicable to single-company SME scope
- **N/A**: Excluded from Circular 99 scope

## Traceability Matrix

| Regulation | Article/Section | Architecture Component | Layer | Test | Status |
|-----------|-----------------|----------------------|-------|------|--------|
| VAS 01 | Para 22 | Account entity | Domain | AccountTests | Planned |
| VAS 02 | VAS 02 | Inventory valuation | Domain | InventoryTests | Planned |
| VAS 03 | VAS 03 | FixedAsset cost model | Domain | FixedAssetTests | Planned |
| VAS 10 | VAS 10 | Currency exchange | Domain | CurrencyTests | Planned |
| VAS 14 | VAS 14 | Revenue recognition | Domain | RevenueTests | Planned |
| VAS 17 | VAS 17 | Deferred tax | Domain | TaxTests | Planned |
| VAS 21 | VAS 21 | Financial statement format | Application | ReportingTests | Planned |
| VAS 24 | VAS 24 | Cash flow statement | Application | ReportingTests | Planned |
| VAS 29 | VAS 29 | Accounting policy changes | Domain | PolicyTests | Planned |

## IFRS Transition Readiness

VAS standards have not been updated since 2001–2005 while IFRS continues evolving. Key gaps:
- VAS rules-based vs IFRS principles-based
- VAS mandates prescribed COA; IFRS does not
- VAS uses historical cost; IFRS emphasizes fair value
- VAS 06: Operating leases record only periodic expense; IFRS 16: ROU asset + lease liability
- Multiple IFRS standards have no VAS equivalent: IAS 20, IAS 41, IFRS 5, IFRS 9, IFRS 13, IFRS 15, IFRS 16

See [IFRS-transition-roadmap.md](./IFRS-transition-roadmap.md) for architecture abstraction design.
