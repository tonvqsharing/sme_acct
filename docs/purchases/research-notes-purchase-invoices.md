# Research Notes — Purchase Invoice Module
_Compiled: 2026-08-24 · All claims cite primary sources below._

## Legal base (verified current)

| Document | Status / Effect | Role |
|---|---|---|
| Luật Quản lý thuế 108/2025/QH15 | In force | Parent tax-administration law |
| **NĐ 254/2026/NĐ-CP** | Issued 30/06/2026, **eff 01/07/2026** | E-invoice & e-document framework — **replaces NĐ 123/2020 (+70/2025)** |
| **TT 91/2026/TT-BTC** | Eff 01/07/2026 | Guides NĐ 254 + Luật QLT — **replaces TT 32/2025**; owns invoice formats, registration, adjustment/replacement procedures |
| Luật Thuế GTGT 2024 (Điều 14 khoản 2) | In force | Input-VAT deduction conditions |
| NĐ 181/2025/NĐ-CP Điều 26 (sửa bởi **NĐ 144/2026**) | In force | Non-cash payment proof: mandatory ≥ **5 triệu VND** (incl. VAT); same-day aggregation; installment grace; cash-paid-to-seller-account excluded |
| TT99/2025 · TT58/2026 · TT133/2016 | Verified 2026-08 | Accounting regimes (see company domain enum) |

**Outdated citations removed:** NĐ 123/2020, NĐ 70/2025, TT 78/2021, TT 32/2025, the old 20-million non-cash threshold.

## Vendor feature parity (market leaders, live product docs)

- **MISA AMIS Kế toán** (`helpact.misa.vn`): Đơn mua hàng · Hợp đồng mua hàng · Chứng từ mua hàng (nhập kho / không qua kho / nhập khẩu) · **Nhận hóa đơn** (hàng về trước, hóa đơn sau) · **Xử lý hóa đơn đầu vào** (XML từ cơ quan thuế / email; duplicate-MST & duplicate-invoice detection) · Trả lại hàng mua · Giảm giá hàng mua · Trả tiền theo hóa đơn · Thanh toán ngay → auto phiếu chi/giấy báo nợ · many-VAT-per-voucher · công nợ theo điều khoản.
- **Fast Accounting/Business Online** (`fast.com.vn`): XML ingest per TT-era format → auto-create hóa đơn mua / phiếu nhập / phiếu chi; vendor & item auto-matching by MST; buyer-MST validation; reconciliation of input list vs posted tax ledger.
- **Bravo ERP** (`bravo.com.vn`): multiple VAT invoices per document, ứng-before cấn trừ, hạn-thanh-toan alerts, 3-party công-nợ bù trừ, FX difference handling per regime circular.

## Standard journal entries (all vendors agree; TT99/TT133 chart)

1. Goods into stock: Dr 152/156/611 (pre-VAT) · Dr 1331 (deductible VAT) / Cr 111·112·331 (total)
2. Immediate use: Dr 621/623/641/642 · Dr 1331 / Cr 111·112·331
3. Fixed asset/CCDC purchases analogous (211/153).

## Sources

- congbao.chinhphu.vn: NĐ 254/2026, NĐ 123/2020 records
- thuvienphapluat.vn: NĐ 70/2025 analysis; Luật GTGT 2024 Đ.14; NĐ 181/2025 Đ.26 as amended by NĐ 144/2026; "dưới 20 triệu 2026" advisory (superseded threshold note)
- EY Vietnam technical alert PDF: Decree 254 on e-invoices (replaces 123/70; TT 91 replaces TT 32; both eff 01/07/2026)
- help.amis.vn / helpact.misa.vn / helpasp.misa.vn: purchase & input-invoice processing KB
- fast.com.vn: input-invoice management features
- bravo.com.vn: purchase-payables module capabilities

## Not independently verified this pass

- Full text of TT 91 annexes (invoice XML field list) — implementation must pull official annex from thuvienphapluat/vbpl before building the XML importer.
- gdt.gov.vn API availability for automated đầu-vào sync (vendor docs indicate it exists via TCT portal; direct-API contract unconfirmed).
