# Templates — Purchase Invoices

## 1. JSON payload — tạo hóa đơn mua

```json
{
  "company_id": "uuid",
  "supplier_name": "Công ty CP Văn phòng phẩm Hòa Bình",
  "supplier_mst": "0101234567",
  "invoice_number": "0001234",
  "invoice_symbol": "1C26TYY",
  "invoice_date": "2026-08-20",
  "entry_date": "2026-08-21",
  "payment_method": "bank",
  "payment_proof": true,
  "reason": "mua VP tháng 8",
  "actor": "uuid-accountant",
  "lines": [
    {
      "expense_account": "6421000001",
      "description": "Giấy A4 20 gói",
      "amount_pre_vat": "2000000",
      "vat_rate": "0.1",
      "deductible": true
    },
    {
      "expense_account": "6421000002",
      "description": "Trà, cà phê",
      "amount_pre_vat": "300000",
      "vat_rate": "0.08",
      "deductible": false
    }
  ]
}
```

## 2. Response 201 (data)

```json
{
  "id": "uuid",
  "status": "DRAFT",
  "subtotal": 2300000.0,
  "vat_deductible": 200000.0,
  "vat_non_deductible": 24000.0,
  "total_payment": 2524000.0,
  "deductibility_summary": {"DEDUCTIBLE_LINES": 1, "NON_DEDUCTIBLE_LINES": 1},
  "checksum": "<64 hex>"
}
```

## 3. Bút toán gợi ý khi POST (hiển thị cho kế toán)

| Định khoản | Tài khoản | Số tiền |
|---|---|---|
| Nợ chi phí | 6421… | 2,300,000 |
| Nợ thuế GTGT được khấu trừ | 1331 | 200,000 |
| Có phải trả người bán | 331 | 2,524,000 |

*(dòng deductible=false: VAT 24,000 vốn hóa vào 6421 — không đưa 1331)*

## 4. Error envelope

```json
{"error": "Trùng số/ký hiệu với HĐ đã nhập", "code": "DUPLICATE_INVOICE"}
```

## 5. Mẫu bảng kê đầu vào (GET ?format=declaration-preview)

| STT | Ký hiệu | Số | Ngày | MST NCC | Tên NCC | Giá chưa thuế | Thuế suất | Tiền thuế | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1C26TYY | 0001234 | 20/08/2026 | 0101234567 | Hòa Bình | 2,000,000 | 10% | 200,000 | |

*(Ghi chú: PENDING_PROOF hiện "chờ chứng từ"; NON_DEDUCTIBLE loại khỏi kê khai khấu trừ.)*
