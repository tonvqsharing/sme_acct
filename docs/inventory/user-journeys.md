# User Journeys — Inventory

## J-I01 Manager sets up master (Day 1)

```
1. Opens FY 2026 MONTHLY OPEN + COA 152/156/632 + PN/PX/CK series.
2. Creates warehouses Kho A (Hà Nội), Kho B (HCM) → locations A-01, B-02 shelves.
3. Creates products: Bút bi (WAVG), Vở (FIFO), Bàn ghế (STANDARD 500k).
4. Documents Internal Accounting Policy per TT99 for COA custom.
```

## J-I02 Warehouse keeper nhập mua (happy)

```
1. Purchase invoice 100 Bút bi @10k arrived → auto supplier shipment PN/000001 in DRAFT (or manual).
2. Keeper checks qty + cost → posts → stock A-01 =100, value 1M, 152 +1M, turnover report shows in 100.
```

## J-I03 Accountant xuất bán (FIFO vs WAVG)

```
1. Customer buys 30 Bút bi. Keeper picks PX/000002 CUSTOMER_OUT 30.
2. System per SKU method: WAVG → 300k COGS, remaining 70@10k. FIFO same after one lot; after second lot 50@12k, FIFO picks 10k lot first, WAVG blends to ~10.58k.
3. Voucher auto: Nợ 632 300k / Có 152 300k. B02 632 up.
```

## J-I04 Internal transfer (happy)

```
1. Need move 10 Bút bi A-01→B-02 for sale in HCM. Shipment INTERNAL 10, cost preserved, no GL, stock A 60 B 10.
```

## J-I05 Count & adjust (happy)

```
1. Month-end keeper counts A-01: expect 60, count 58 shortage 2 lost. System move to VIRTUAL_LOST 2 → Nợ 632 20k / Có 152 20k.
```

## J-I06 Oversell frustrated

```
1. Tries PX 100 but stock 58 → 409 INSUFFICIENT_STOCK. Must wait import or adjust count.
```

## J-I07 Period lock — accountant error

```
1. Tries PN effective 2026-08-10 but stock period 2026-08 CLOSED by Chief → 409 PERIOD_CLOSED. Must reopen via Chief+reason.
```

## J-I08 Auditor view

```
1. Auditor logs → GET /inventory/stock?as_of=2026-08-31 → sees quantity/value per warehouse.
2. GET /reports/inventory/nxt + turnover → verifies vs B01 tồn kho, vs trial-balance 152.
```

## Journey map ASCII

```
[Setup] Product/Warehouse → [In] PN DRAFT→DONE → stock +152 → [Out] PX per method → 632 → [Transfer] internal → [Count] adjust → [Lock] period → [Audit] NXT/turnover
       │ FY+period gates           │ wavg/fifo/standard       │ location          │ VIRTUAL    │ 409         │ reconciles B01
```
