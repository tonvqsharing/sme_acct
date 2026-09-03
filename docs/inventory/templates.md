# Templates — Inventory

## T-I01 Product create payload

```json
{
  "company_id": "22222222-2222-2222-2222-222222222222",
  "code": "SKU-001",
  "name": "Bút bi Thiên Long",
  "uom": "Cái",
  "cost_method": "wavg",
  "standard_cost": null,
  "reason": "tạo VTHH mới"
}
```

## T-I02 Shipment SUPPLIER_IN (PN)

```json
{
  "company_id": "...",
  "type": "SUPPLIER_IN",
  "moves": [
    {"product_id": "uuid-sku1", "qty": "100", "unit_cost": "10000", "to_loc": "uuid-A-01"}
  ],
  "effective_date": "2026-08-10",
  "reason": "nhập mua PO-001"
}
```
Response 201: `{number:"PN/000001", state:"DRAFT", moves:[...]}`

## T-I03 Shipment CUSTOMER_OUT (PX) + COGS

```json
{
  "company_id": "...",
  "type": "CUSTOMER_OUT",
  "moves": [
    {"product_id": "uuid-sku1", "qty": "30", "from_loc": "uuid-A-01"}
  ],
  "reason": "xuất bán SO-001"
}
```
On POST → computes COGS per method: `{"cogs":300000, "remaining_qty":70, "remaining_value":700000}`

## T-I04 Error envelope

```json
{"error":"Tồn kho không đủ: need 100 have 70","code":"INSUFFICIENT_STOCK"}
{"error":"Kỳ kho đã khóa","code":"PERIOD_CLOSED"}
{"error":"Phương pháp chuẩn yêu cầu standard_cost","code":"INVALID_PRODUCT"}
```

## T-I05 COA seed for HTK (TT99/TT58)

```
152  NVL (aggregate)
1521 NVL chi tiết (detail) → stock in value
153  CCDC in stock detail
154  Chi phí SX dở dang detail
155  Thành phẩm detail
156  Hàng hóa detail
158  (optional provision)
632  Giá vốn hàng bán detail (per method)
229  Dự phòng giảm giá HTK
```

## T-I06 Stock reports

NXT:
```
product, beginning_qty, beginning_value, in_qty, in_value, out_qty, out_value (632), ending_qty, ending_value
SKU-001, 0,0, 100,1000000, 30,300000, 70,700000
```

Thẻ kho (ledger per product/location):
```
date, doc, qty_in, value_in, qty_out, value_out, qty_onhand, value_onhand
2026-08-10, PN/000001, 100,1000000, 0,0, 100,1000000
2026-08-12, PX/000001, 0,0, 30,300000, 70,700000
```

## T-I07 Test seeding helper

```python
def _seed_inventory(app, company_id):
    fy.create_year(company_id,"2026", date(2026,1,1), date(2026,12,31),"MONTHLY", actor=..., reason="fy")
    for code,name,parent in [("152","NVL",None),("1521","NVL ct","152"),("632","GVHB",None),("6321","GVHB ct","632")]:
        coa.create_account(company_id, code, name, parent_code=parent, actor=..., reason="c")
    for pfx in ("PN/","PX/","CK/"): series.create_series(company_id=company_id, prefix=pfx, actor=..., reason="s")
    product = inv_service.create_product(company_id, code="SKU-001", name="Bút", uom="Cái", cost_method="wavg", actor=..., reason="init")
    loc = inv_service.create_location(company_id, warehouse=warehouse_id, code="A-01", name="Kệ A", type="SHELF")
```
