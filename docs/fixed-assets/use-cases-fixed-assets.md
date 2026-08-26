# Use Cases — Fixed Assets

## UC-FA1 Ghi tăng TSCĐ
**Actor:** ACCOUNTANT · **Pre:** kỳ mở, TK chi phí chi tiết ACTIVE
1. POST /fixed-assets {asset_code?, name, category, original_cost, acquisition_date, useful_life_months, depreciation_account}
2. Hệ thống: R-FA3 unique check → genesis checksum → status ACTIVE
3. Response 201 + monthly_depreciation computed

## UC-FA2 Tính khấu hao hàng tháng
**Actor:** ACCOUNTANT · **Pre:** có ≥1 TSCĐ ACTIVE còn remaining
1. POST /depreciation-runs/compute {company_id, year, month}
2. Hệ thống: FY gate → per-asset straight-line compute (capped at remaining) → sinh voucher Dr expense/Cr 214 → update accumulated_depreciation → stamp checksum
3. Response 200 + summary {assets_depreciated, total_depreciation}

## UC-FA3 Thanh lý / nhượng bán TSCĐ
**Actor:** CHIEF_ACCOUNTANT
1. POST …/deactivate {reason}
2. Status → CLOSED (soft); blocks future depreciation runs
3. Actual disposal journals handled via generic voucher module (NĐ 254 rules)

# Happy paths

| ID | Scenario | Expected |
|---|---|---|
| HP-FA1 | Mua máy Photocopy 50tr, khấu hao 5 năm → monthly = 833,333đ | Dr 6421 833,333 / Cr 214 833,333 |
| HP-FA2 | Mua laptop 30tr, khấu hao 3 năm → monthly = 833,333đ | Same pattern |
| HP-FA3 | Compute tháng có 2 TSCĐ → tổng khấu hao = Σ monthly | Balanced journal |

# Alternative paths

| ID | Độ lệch | Xử lý |
|---|---|---|
| AP-FA1 | accumulated ≥ NG (fully depreciated but still in use) | Skip in compute run; still listed in sổ TSCĐ |
| AP-FA2 | TSCĐ ngừng sử dụng >9 tháng | Status SUSPENDED; depreciation not tax-deductible (tracked flag for tax adj.) |

# Exception paths

| ID | Code | HTTP |
|---|---|---|
| EX-FA01 MISSING_ACTOR | 400 |
| FA02 DUPLICATE_ASSET_CODE | 409 |
| FA03 PERIOD_CLOSED | 409 |
| FA04 INVALID_ACCOUNT | 422 |
| FA05 ASSET_CLOSED — deactivate/depreciate on CLOSED asset | 409 |
| FA06 NO_REMAINING_DEPRECIATION | 409 |
