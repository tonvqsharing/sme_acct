# Use Cases — Inventory

## Actors
Accountant (KT), Chief Acc, Warehouse keeper, Auditor, System

## UC-I01 Create Product + Location (happy)

```
Pre: company exists, FY 2026 OPEN
1. KT POST /inventory/products {company_id, code: SKU-001, name: Bút bi, uom: Cái, cost_method: wavg}
2. System: code unique per company → save ACTIVE
3. KT POST /inventory/locations {warehouse: Kho A, code: A-01, type: SHELF, parent: Warehouse}
```

## UC-I02 Supplier In — nhập mua (happy)

```
1. KT POST /shipments {type: SUPPLIER_IN, moves:[{product: SKU-001, qty:100, unit_cost:10000, to: A-01}]}
2. System: FY OPEN + product active + loc company match → shipment PN/000001 DRAFT, moves DRAFT
3. Chief POST /shipments/<id>/post
4. System: state→DONE, move effective_date now, recompute WAVG: avg=10k, stock 100, value 1M, 152 +1M (no 611), audit POST
```

## UC-I03 Customer Out — xuất bán FIFO/WAVG/Standard (happy)

```
Pre: stock 100@10k
1. KT creates shipment CUSTOMER_OUT qty 30
2. Post → per method:
   wavg: COGS 30*10k=300k → Nợ 632 300k / Có 152 300k, remaining 70@10k
   fifo: pick oldest lot 30@10k =300k (same here, later lots diff)
   standard (8k): COGS 240k + variance 60k → Nợ 632
```

## UC-I04 Mixed methods per SKU (happy — TT99)

```
SKU-001 wavg, SKU-002 fifo in same shipment INTERNAL transfer
System recomputes each SKU independently per its method
```

## UC-I05 Internal Transfer (happy)

```
Move from A-01 → B-02 within company, qty 10, cost preserved (no GL entry, only location)
```

## UC-I06 Oversell blocked (exception)

```
Stock 70, order 100 → 422 INSUFFICIENT_STOCK "Tồn kho không đủ: need 100 have 70"
No negative stock unless config allows (consumable).
```

## UC-I07 Inventory Count + Reconciliation (happy)

```
1. Keeper POST /inventory/count {location: A-01, counts:[{SKU-001, qty:68}]}
2. System finds 70 expected → shortage 2 → create adjustment move to VIRTUAL_LOST → Nợ 632 / Có 152 (or 138 if awaiting)
```

## UC-I08 Period Lock (exception)

```
Stock period 2026-08 CLOSED → POST shipment effective 2026-08-10 → 409 PERIOD_CLOSED
```

## UC-I09 Reports (happy)

```
GET /inventory/stock?warehouse=KhoA&as_of=2026-08-31 → [{SKU-001 qty:70 value:700k}]
GET /reports/inventory/nxt → nhập/xuất/tồn per product
GET /reports/inventory/turnover → qty out / avg stock
GET /reports/trial-balance → 152/156 vs stock value reconciles
```

## UC-I10 NRV Provision (alternative)

```
At period end, NRV 9k < cost 10k → create provision 229: Nợ 632 / Có 229 70k (70*1k)
```

## State machines

```
Shipment: DRAFT → DONE (or CANCELLED before DONE)
Move:     DRAFT → ASSIGNED → DONE
Period:   OPEN → CLOSED (no reopen without CHIEF+reason)
```

## Exceptions matrix

| Condition | Code | HTTP |
|---|---|---|
| qty ≤0 / cost <0 | INVALID_MOVE | 422 |
| FY closed | NO_OPEN_PERIOD | 409 |
| period closed | PERIOD_CLOSED | 409 |
| insufficient stock | INSUFFICIENT_STOCK | 409 |
| duplicate SKU | DUPLICATE_SKU | 409 |
| unknown product/loc | NOT_FOUND | 404 |
| AUDITOR write | SOD_VIOLATION | 403 |
