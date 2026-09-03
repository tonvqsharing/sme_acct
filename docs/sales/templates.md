# Templates — Sales

## T-S01 Invoice create payload (POST /api/v1/invoices)

```json
{
  "company_id": "22222222-2222-2222-2222-222222222222",
  "template_code": "1C26TAA",
  "invoice_symbol": "HD/",
  "customer_name": "Công ty TNHH Khách",
  "customer_mst": "0101234567",
  "issue_date": "2026-08-10",
  "currency_code": "VND",
  "fx_rate": null,
  "items": [
    {"account_code": "5111", "description": "Bán hàng A", "amount": "10000000", "vat_rate": "0.10", "category": "manufacturing"},
    {"account_code": "5111", "description": "Sách giáo khoa", "amount": "5000000", "vat_rate": "0.05", "category": "education"}
  ],
  "reason": "sale order SO-2026-001"
}
```

Response 201:
```json
{"data": {"id":"...","number":"HD/000001","issue_date":"2026-08-10","due_date":"2026-09-09",
 "subtotal":15000000,"vat_breakdown":{"0.1":1000000,"0.05":250000},"vat_amount":1250000,"grand_total":16250000,
 "status":"DRAFT","checksum":"..."}}
```

## T-S02 Error envelope

```json
{"error": "Thuế suất 8% không áp dụng cho nhóm telecom theo NĐ174/2025", "code": "VAT_CATEGORY_INELIGIBLE"}
{"error": "Kỳ sổ chưa mở cho ngày hạch toán", "code": "NO_OPEN_PERIOD"}
{"error": "Số HĐ đã đạt giới hạn 99,999,999/năm/ký hiệu", "code": "EINVOICE_SEQUENCE_EXHAUSTED"}
```

## T-S03 COA seed for sales (TT133/TT99-aware)

```
COA setup (call coa.create_account for each):
  131    Phải thu KH (aggregate)
  1311   Phải thu KH - chi tiết (detail) ← used in 131 debit
  511    Doanh thu (aggregate)
  5111   Doanh thu bán hàng (detail)    ← revenue credit
  333    Thuế phải nộp (aggregate)
  3331   Thuế GTGT đầu ra (detail)      ← vat credit
  521    Các khoản giảm trừ DT (TT99)
  5211/5212/5213 detail (hàng trả lại, giảm giá, chiết khấu)
  3387   Doanh thu chưa thực hiện (deferred, for multi-PO service)
```

## T-S04 E-invoice XML skeleton (NĐ254 Phụ lục, abridged)

```xml
<HDon>
  <TTChung>
    <PBan><MST>010...</MST><Ten>CTY BÁN</Ten><DChi>...</DChi></PBan>
    <PMua><MST>0101234567</MST><Ten>Cty Khách</Ten></PMua>
    <KHMSHDon>1C26TAA</KHMSHDon>
    <KHHDon>HD/</KHHDon>
    <SHDon>00000001</SHDon>
  </TTChung>
  <DSHHDVu>
    <HHDVu><Ten>Bán hàng A</Ten><SLuong>1</SLuong><DGia>10000000</DGia><ThueSuat>10%</ThueSuat><TienThue>1000000</TienThue></HHDVu>
  </DSHHDVu>
  <Tong><TgTCThue>15000000</TgTCThue><TgTThue>1250000</TgTThue><TgTTTBSo>16250000</TgTTTBSo></Tong>
</HDon>
```

## T-S05 Ledger export (CSV)

```
entry_date,number,description,account_code,debit,credit
2026-08-10,HD/000001,Bán hàng KH A,131,16250000,0
2026-08-10,HD/000001,Bán hàng KH A,5111,0,15000000
2026-08-10,HD/000001,Bán hàng KH A,3331,0,1250000
```

## T-S06 Test seeding helper (integration)

```python
def _setup_sales_company(app, company_id):
    fy.create_year(company_id, "2026", date(2026,1,1), date(2026,12,31), "MONTHLY", actor=..., reason="fy")
    for code, name, parent in [
        ("5111","DT",None), ("131","PTKH",None), ("1311","PTKH ct","131"),
        ("333","Thue",None), ("3331","GTGT ra","333"),
    ]: coa.create_account(company_id, code, name, parent_code=parent, actor=..., reason="coa")
    for pfx in ("HD/","PT/"): series.create_series(company_id=company_id, prefix=pfx, actor=..., reason="s")
    terms.create_payment_term(company_id=company_id, name="Net 30", due_days=30, actor=..., reason="terms", is_default=True)
```
