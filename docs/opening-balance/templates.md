# Templates — Opening Balance

## T-O01 GL lines payload (POST /batches/<id>/gl)

```json
{
  "reason": "opening FY2026 per prior-year BCTC",
  "lines": [
    {"account_code": "1111", "debit": "500000000", "credit": "0"},
    {"account_code": "1521", "debit": "2100000000", "credit": "0"},
    {"account_code": "1311", "debit": "800000000", "credit": "0"},
    {"account_code": "3311", "debit": "0", "credit": "600000000"},
    {"account_code": "4111", "debit": "0", "credit": "2800000000"}
  ]
}
```

Response 201: `{batch_id, lines_accepted: 5}` (balance checked at lock, not entry).

## T-O02 Counterparty rows

```json
{
  "rows": [
    {"account_code": "1311", "party_id": "uuid-KH-001", "side": "debit", "amount": "200000000"},
    {"account_code": "3311", "party_id": "uuid-NCC-01", "side": "credit", "amount": "150000000", "proof": true}
  ]
}
```

## T-O03 Stock rows (incl. FIFO lot detail)

```json
{
  "rows": [
    {"product_id": "uuid-SKU-001", "warehouse_id": "uuid-KHO-A",
     "qty": "100", "total_value": "1000000"},
    {"product_id": "uuid-SKU-002", "warehouse_id": "uuid-KHO-A",
     "qty": "50", "total_value": "600000",
     "lot_code": "LOT-25A", "receipt_date": "2025-12-20",
     "receipt_doc": "PN-881", "unit_cost": "12000"}
  ]
}
```

## T-O04 Asset rows

```json
{
  "rows": [
    {"kind": "fixed_asset", "code": "TSCD-01", "name": "Máy CNC",
     "original_cost": "1200000000", "remaining_value": "800000000",
     "months_left": 80, "expense_account": "6421"},
    {"kind": "ccdc", "code": "CCDC-07", "name": "Khuôn ép",
     "original_cost": "120000000", "remaining_value": "40000000",
     "months_left": 8, "expense_account": "6421"}
  ]
}
```

## T-O05 Bank rows

```json
{
  "rows": [
    {"bank_account_id": "uuid-VCB-001", "amount": "750000000"}
  ]
}
```

## T-O06 Error envelope

```json
{"error": "Nợ 5000000000 ≠ Có 4800000000", "code": "UNBALANCED_OPENING"}
{"error": "Batch is LOCKED", "code": "BATCH_LOCKED"}
{"error": "No locked opening batch — complete setup first", "code": "NO_OPENING_LOCK"}
```

## T-O07 Excel sheets (headers, * required)

```
gl:            account_code* | debit | credit | currency
counterparty:  account_code* | party_code* | side* | amount* | proof
stock:         product_code* | warehouse_code* | qty* | total_value* | lot_code | expiry_date | receipt_date | receipt_doc | unit_cost
assets:        kind* | code* | name* | original_cost* | remaining_value* | months_left* | expense_account*
bank:          bank_account_no* | amount*
```

Rules: no rename sheets/cols; numeric plain (no thousand separators); dates ISO.

## T-O08 Reconcile report

```json
{"balanced": false, "checks": [
  {"rule": "R-O01 trial", "expected": "0", "actual": "200000000", "ok": false},
  {"rule": "R-O02 SKU=152", "expected": "2100000000", "actual": "2000000000", "ok": false}
]}
```

## T-O09 Test seeding helper (integration)

```python
def _setup_opening(app, company_id, fy_id):
    batch = opening_svc.create_batch(company_id, fy_id, source="MANUAL", actor=..., reason="init")
    opening_svc.post_gl(batch.id, lines=[...balanced...], actor=..., reason="gl")
    opening_svc.post_stock(batch.id, rows=[...], actor=..., reason="stock")
    opening_svc.lock(batch.id, actor=chief, reason="go-live")
    return batch
```
