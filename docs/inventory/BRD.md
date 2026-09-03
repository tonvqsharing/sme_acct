# BRD — Inventory Module (HTK — Hàng Tồn Kho)

| | |
|---|---|
| Module | Inventory — VAS 02, TT99/TT58, stock moves + cost |
| Version | 1.0 — Inventory PROD Gap Review |
| Date | 2026-09-03 |
| Authors | BA Lead 20y + Chief Acc VACPA 20y |
| Depends | Company, COA (152/153/154/155/156/158), FY/Period, Purchases, Sales, Voucher/Ledger, System Settings |
| Status | BRD approved — S1-S5 required before PROD |

## 1. Background & Goal

SME phải quản lý HTK theo VAS 02 (giá gốc + NRV) và TT99 (mới). Mục tiêu TT99: linh hoạt phương pháp tính giá per product (WAVG/FIFO/đích danh/chuẩn), bỏ 611 và bỏ đối ngẫu perpetual/periodic — mọi nhập/xuất là stock move định lượng + giá vốn.

Goal: `Product → Move in/out/internal → Cost recompute (method per product) → 632 COGS → 152/156 balance → B01 tồn kho → audit 10y`.

## 2. Regulatory drivers (active only)

```
ACTIVE (2026-09-03)                           OUTDATED — DO NOT USE
─────────────────────────────────────────    ────────────────────────────
VAS 02 QĐ149/2001 31/12/2001 (HTK)            TT200/2014 §22-30 (HTK cũ)
TT99/2025 27/10/2025 FY≥01/01/2026             TT133/2016 (SME cũ)
TT58/2026 SME HTK                            QĐ 15/2006
Luật Kế toán 88/2015 Art.11 (10y)             TK 611 Purchase (abolished)
TT99 + TT58: 4 methods + per-item method     Old: 1 method global
```

## 3. Scope v1.0

In:
1. Product master `code, name, uom, cost_method {specific|wavg|fifo|standard}, warehouse default`
2. Warehouse/Location hierarchy `Warehouse → Location (shelf/bin)`, virtual locations (lost/missing)
3. Stock Move `product, qty, uom, unit_cost, from_loc→to_loc, effective_date, company`
4. Shipment `Supplier (in), Customer (out), Internal (transfer)` grouping moves, state DRAFT→DONE
5. Cost recompute per product method → `cost price revision` + update 152/156 + COGS 632 on out
6. Period + lock (stock period) + inventory count reconciliation
7. Reports: tồn kho (quantity/value), NXT, thẻ kho, turnover

Out (v1):
- Lot/serial/expiry, barcode, BOM, MRP
- Consignment, branch transfer pricing, external WMS 3P (next version)

## 4. Roles & Permissions

| Action | ADMIN | CHIEF | ACCOUNTANT | AUDITOR |
|---|---|---:|---:|---:|
| Product/Warehouse master | ✓ | ✓ | ✓ | - |
| Create shipment DRAFT | - | - | ✓ | - |
| Post shipment (increase/decrease stock) | - | ✓ | ✓* | - |
| Cost method change | - | ✓ | - | - |
| Inventory count | - | ✓ | ✓ | - |
| Read stock/report | ✓ | ✓ | ✓ | ✓ |

`* ACCOUNTANT posts if under threshold, else CHIEF per config*`

## 5. Success criteria

| # | Criterion | Measure |
|---|---|---|
| SC-01 | Import 100 units @10k → stock 100, value 1M, 152 balance 1M | UT+integration |
| SC-02 | Export 30 @ FIFO vs WAVG vs Standard produce TT99-correct 632 diff tracked | UT method |
| SC-03 | Per-product method (SKU A FIFO, SKU B WAVG) | UT |
| SC-04 | No 611 account used; direct 152/156 via moves | grep audit |
| SC-05 | Period lock blocks move | 409 |
| SC-06 | NXT + turnover reports correct vs voucher ledger | integration |
| SC-07 | mypy strict + ruff/black + pytest | CI |

## 6. Ubiquitous Language

| Term | VN | Meaning |
|---|---|---|
| HTK | Hàng tồn kho | VAS 02 §03: hàng mua để bán, dở dang, NVL/CCDC |
| Stock Move | Phiếu nhập/xuất/kho | Transfer qty between locations with cost |
| Shipment | Phiếu | Group moves (NCC, KH, nội bộ) |
| Cost method | Phương pháp tính giá xuất | specific, wavg, fifo, standard (TT99) |
| NRV | Giá trị thuần có thể thực hiện | original vs NRV lower → provision 229 |
| Period | Kỳ kho | stock.period, lock per month |
