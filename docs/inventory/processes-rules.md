# Processes & Rules — Inventory

## Processes

### P-I01 Supplier In (PN)

```
Accountant            InventoryService            FY/COA/StockPeriod        Voucher/Ledger
  │ POST /shipments SUPPLIER_IN ──►│                              │                │
  │ moves [{sku,qty,cost,to}]      ├─ fy OPEN? period OPEN? ───►│                │
  │                                ├─ product active? loc match?  │                │
  │                                ├─ qty>0 cost>=0 standard?    │                │
  │                                ├─ shipment PN/ DRAFT ───────►│ audit CREATE   │
  │◄── 201 PN/000001 ──────────────┤                              │                │
  │ POST /shipments/<id>/post ────►│ state→DONE moves→DONE       │                │
  │                                ├─ wavg recompute: avg ──────►│ Nợ 152 / Có 111/331*│
  │                                │ (no 611)                     │                │
```

`* purchase integration: use supplier shipment to auto-create 152 entry`

### P-I02 Customer Out (PX) + COGS

```
Post CUSTOMER_OUT qty 30 → method wavg/fifo/standard → pick lots → COGS 632
If insufficient → 409
Journal: Nợ 632 / Có 152 (or 156 if finished goods)
```

### P-I03 Internal Transfer

```
From A-01 → B-02, no GL, only qty moves, cost preserved.
```

### P-I04 Inventory Count

```
Keeper posts count {expected 70, counted 68} → shortage 2 → move to VIRTUAL_LOST → Nợ 632/811 / Có 152
Audit COUNT + checksum.
```

### P-I05 Period Lock

```
Before any DONE: stock_period.is_locked(company,year,month)? → 409.
Lock via POST /periods/close (CHIEF).
```

## Rules R-Ixx (testable)

| ID | Rule | Test |
|---|---|---|
| R-I01 | FY OPEN on effective_date | `test_closed_period_blocked` |
| R-I02 | Period OPEN | `test_period_closed_409` |
| R-I03 | Product active, location same company | `test_wrong_company_404` |
| R-I04 | qty>0, cost>=0, standard_cost required if method=standard | `test_invalid_move_422` |
| R-I05 | No negative stock (except consumable) | `test_oversell_409` |
| R-I06 | Per-product cost method (SKU diff) | `test_mixed_method` |
| R-I07 | No 611 usage; direct 152/156 | `grep 611 → 0` |
| R-I08 | Checksum = sha256(prev|id|actor|state|qty|cost|reason) | `test_checksum_changes` |
| R-I09 | WAVG moving: `(prev_val+in_val)/(prev_qty+in_qty)` | `test_wavg_recompute` |
| R-I10 | FIFO oldest lots first | `test_fifo_picks_oldest` |
| R-I11 | Standard variance → adjust 632 | `test_standard_variance` |
| R-I12 | AUDITOR read-only | `test_auditor_403` |

## ASCII workflow

```
[Product/Location master] → [DRAFT shipment + moves] → FY+period gates → cost recompute → [DONE]
          │                          │  oversell? lock?          │ wavg/fifo/standard
          └──────► 152 balance ──────┴──────► 632 COGS ──────────┴──────► NXT/turnover reports
                                                                      │
                                                                Audit 10y chain
```
