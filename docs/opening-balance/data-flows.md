# Data Flows — Opening Balance

## DF-O01 Create draft batch

```
HTTP POST /api/v1/opening-batches
  {company_id, fiscal_year_id, source: MANUAL|EXCEL|YEAR_ROLL, reason, actor}
       │
       ▼
OpeningService.create_batch
  ├─ require actor+reason
  ├─ FY belongs to company? ──► 404/422
  ├─ Batch(DRAFT) + checksum(GENESIS, actor, reason)
  └─ repo.save → 201 {id, state: DRAFT}
       │
       └──► audit.append(entity_type=batch, action=CREATE)
```

## DF-O02 Post rows (per group, same pattern ×5)

```
POST /batches/<id>/stock
  {rows:[{product_id, warehouse_id, qty, total_value, lot?...}], reason}
       │
       ▼
  ├─ batch DRAFT? ──► 409 BATCH_LOCKED
  ├─ product/warehouse active + same company? ──► 404/422
  ├─ qty>0, value≥0, FIFO needs receipt_*? ──► 422
  ├─ persist rows + materialize DONE StockMove(from None, unit=value/qty or receipt price)
  ├─ checksum(prev, actor, reason) → save
  └─ audit APPEND (never update-in-place history)
```

## DF-O03 Reconcile (read-only)

```
GET /batches/<id>/reconcile
  ├─ ΣNợ vs ΣCó GL → balanced?
  ├─ Σ stock.total_value by account vs GL 152/153/155/156/157/158
  ├─ Σ counterparty by account vs GL 131/331/141/138/338
  ├─ Σ bank vs GL 112x; Σ FA remaining vs 211−214; CCDC vs 242
  └─ 200 {balanced: bool, checks:[{rule, expected, actual, ok}]}
```

ASCII pipeline:

```
[FY+COA+Party/UOM/Product/Warehouse/Bank masters] ──┐
     Batch DRAFT ───────────────────────────────────┼──► rows per group ──► materialize ──► audit_log
                                                    │                              │
                                             ┌──────┴──────┐                       ▼
                                             ▼             ▼                reconcile report
                                                    trial Nợ=Có gate ──► LOCKED ──► live vouchers
```

## DF-O04 Excel import

```
POST /batches/<id>/excel (multipart, ≤10 .xlsx)
  ├─ header match template? ──► 422 + expected list
  ├─ per row: master exists? numeric? single side? ──► collect errors
  ├─ valid rows persist (same as DF-O02 gates)
  └─ 200 {imported: n, errors:[{row, reason}]} + error sheet
      all-invalid → 422, nothing persisted
```

## DF-O05 Lock / reopen / year-roll

```
POST /batches/<id>/lock (CHIEF/ADMIN)
  ├─ reconcile balanced? else 409 UNBALANCED_OPENING + diff
  └─ state→LOCKED + audit LOCK

POST /batches/<id>/reopen (CHIEF only) → DRAFT + audit REOPEN(reason)

POST /roll-year {from_year, to_year}
  ├─ from closed? to OPEN? ──► 409/422
  └─ copy rows → new DRAFT batch (source=YEAR_ROLL); supersede audit link
```

## Persistence contract (primitives across seams)

```
OpeningService ◄──► fy: {get_year(UUID), belongs_to(UUID,UUID)}
               ◄──► coa: {validate_posting_account(UUID,str,regime)}
               ◄──► party/product/warehouse/bank: {get_by_id(UUID)} + company match
               ◄──► audit: {append(entity_type, entity_id, action, actor_id, reason)}
               ◄──► inventory: {materialize_opening_move(...)} (no join, via port)
No cross-brick SQLAlchemy joins — all via contract primitives.
```
