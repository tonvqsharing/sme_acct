# Research Notes — Fixed Assets Module (Tài sản cố định)
_Compiled 2026-08-25 · All claims cite primary sources below._

## Legal base (verified current)

| Document | Status | Role |
|---|---|---|
| **TT99/2025/TT-BTC** | eff 01/01/2026, replaced TT200/2014 | Chart of accounts (211 TSCĐ HH, 212 TSCĐ TC, 213 TSCĐ VH, 214 Hao mòn), depreciation journal templates |
| Luật Thuế TNDN + TT45/2013 (sửa bởi TT147/2016) | In force | Depreciation framework: methods, useful-life ranges, non-depreciation exclusions |
| NQ 204/2025/QH15 + NĐ 174/2025/NĐ-CP | eff →31/12/2026 | VAT 8% on qualifying FA acquisitions |

## Key rules verified from TT99/2025

1. **Depreciation start:** by DAY of month asset increases; stop by day of decrease
2. **3 methods:** straight-line (đường thẳng) · declining balance adjusted (số dư giảm dần có điều chỉnh) · production output (sản lượng). Method must be consistent per asset; changes require significant-use-change justification
3. **Useful life:** per MOF framework; override requires MOF/DoF approval + tax-office notification within 20 days; only ONE change per asset
4. **Exclusions from depreciation:** fully depreciated but still in use · lost · not owned (except finance lease) · welfare assets (trừ nhà để xe, y tế, đưa đón, đào tạo) · land-use-rights long-term · aid-funded research
5. **TSCĐ ngừng sử dụng >9 months** → depreciation not tax-deductible
6. **XDCB temporary value:** adjust at settlement, no retroactive depreciation adjustment
7. **Journal — monthly depreciation:** Dr 623/627/641/642 / Cr 214
8. **Journal — disposal:** Dr 211·214 / Cr 111·112·331·711·811 (multiple steps)
9. **Mẫu 06-TSCĐ:** monthly allocation table — prior month + increases − decreases = this month
10. **TSCĐ hết khấu hao vẫn dùng:** track but don't depreciate

## Vendor feature parity (MISA AMIS Kế toán, Fast Accounting, Bravo ERP)

- **Ghi tăng:** asset code auto-gen · cost breakdown by source documents · depreciation tab (NG, useful life, method) · allocation setup (department/cost center/product) · source-origin tracking · attachments (biên bản giao nhận)
- **Tính khấu hao:** monthly batch compute → allocation to cost centers → auto-journal Dr expense/Cr 214
- **Ghi giảm:** liquidation/sale/damage paths with multi-step journals
- **Điều chuyển:** transfer between departments (v2 in MISA HKD — "tính năng đang phát triển")
- **Sổ TSCĐ:** ledger with NG/hao mòn lũy kế/giá trị còn lại at any date
- **Kiểm kê:** physical count vs book records
- **Multi-VAT invoices per acquisition document**

## Sources

- thuvienphapluat.vn: TT99 depreciation principles, Mẫu 06-TSCĐ format, account 214 rules
- congbao.chinhphu.vn: TT99 official record
- helpact.misa.vn: Ghi tăng, Khấu hao, Ghi giảm, Sổ TSCĐ workflows
- fast.com.vn: purchase-payables module FA features
- bravo.com.vn: FA module capabilities incl. multi-currency FX differences

## Not independently verified this pass

- Full TT99 Phụ lục 2 chart-of-accounts detail for 211/212/213 sub-accounts (needed for COA seeding)
- Exact useful-life range table per MOF circular (referenced but full text not fetched)
