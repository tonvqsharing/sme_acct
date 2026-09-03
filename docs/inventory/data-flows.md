# Data Flows — Inventory

## DF-I01 Supplier In (PN)

```
POST /shipments SUPPLIER_IN
  {company_id, moves:[{product_id, qty, unit_cost, to_loc}], reason, actor}
       │
       ▼
InventoryService.create_shipment
  ├─ actor+reason? → 422
  ├─ fy.find_open_period(company, effective_date) → 409 if None
  ├─ stock_period.is_locked? → 409
  ├─ product active? location company match?
  ├─ qty>0 cost>=0 standard_cost? → 422
  ├─ shipment number PN/000001 (DocumentNumbering)
  └─ repo.save DRAFT + moves DRAFT → audit CREATE

POST /shipments/<id>/post
  ├─ exists? → 404 if miss, 409 if already DONE
  ├─ re-check FY+period
  ├─ for each move: state→DONE, effective_date now
  ├─ wavg recompute per product: new_avg = (prev_qty*prev_avg + qty*cost)/(prev_qty+qty)
  │  fifo queue push lot, specific pick lot, standard variance = actual - standard
  ├─ GL: Nợ 152/156 value / Có ... (supplier 331 handled by purchases brick)
  └─ audit POST + checksum(prev|id|actor|DONE|qty|cost|reason)
```

## DF-I02 Customer Out (PX) + 632

```
POST /shipments CUSTOMER_OUT qty 30
  ├─ check stock available per product (sum DONE moves in loc)
  │   if insufficient → 409 INSUFFICIENT_STOCK
  ├─ pick lots per method → compute COGS
  └─ GL: Nợ 632 / Có 152 (or 155/156) amount = COGS
```

ASCII pipeline:

```
[Product/Warehouse master] ──┐
FY/COA/Period gates ──────────┼──► Shipment DRAFT ──► post → Move DONE ──► cost revision ──► GL 152/632
Numbering PN/PX/CK ───────────┘                                         └─► audit_log
                                                                               │
                                                                        ┌──────┴──────┐
                                                                        ▼             ▼
                                                                  stock report   trial-balance 152
                                                                   NXT/turnover   (reconciles)
```

## DF-I03 Reports (read-model, posted-only)

```
GET /inventory/stock?company_id&warehouse&as_of
  Ledger: SELECT SUM(qty) FILTER(state=DONE, effective_date ≤ as_of) GROUP BY product,warehouse

GET /reports/inventory/nxt
  window from→to: in sum, out sum (COGS), tồn = begin + in - out

GET /reports/inventory/turnover
  turnover = out qty / avg stock qty in window
```

## DF-I04 Persistence contracts (primitives across seams)

```
InventoryService ◄──► fy: {find_open_period(UUID,date)→Period|None}
                 ◄──► period_lock: {is_locked(UUID,year,month)→bool}
                 ◄──► coa: {validate_posting_account(UUID,str,regime)} for 152/632
                 ◄──► numbering: {issue(UUID,prefix)→str}
                 ◄──► audit: {append(entity_type, entity_id, action, actor_id, reason)}
                 ◄──► voucher: {create_voucher(...)} for COGS
No cross-brick SQLA joins — all via contract primitives.
```
