# Processes · Rules · Data Flows · Workflows — Purchase Invoices

## 1. Quy trình tổng thể (To-be)

```
Nhà cung cấp ──HĐĐT──▶ Kế toán mua hàng
                         │ 1. Nhập (UC-P1) — check trùng tức thời
                         ▼
                    DRAFT (checksum genesis)
                         │ 2. Kiểm tra: kỳ mở → COA chi tiết → tổng khớp
                         ▼
                       POSTED ──── sinh bút toán gợi ý + bảng kê đầu vào
                         │
              ┌──────────┴───────────┐
        ≥5tr & có CK-chứng từ   ≥5tr thiếu chứng từ
              DEDUCTIBLE            PENDING_PROOF ──đính kèm──▶ DEDUCTIBLE
                         │
                  CUỐI KỲ: bảng kê 1331 ─▶ (tương lai) tờ khai 01/GTGT
```

## 2. Rules Summary

| ID | Rule | Enforced by |
|---|---|---|
| R-P1 | Trùng (company, mst, số, ký hiệu) bị chặn | repo exists_duplicate + service |
| R-P2 | entry_date phải nằm trong kỳ OPEN | FY gate |
| R-P3 | expense_account ACTIVE + posting-level theo regime | COA gate |
| R-P4 | Phân loại khấu trừ: VAT invoice ∧ deductible ∧ (<5tr ∨ proof) | deductibility engine |
| R-P5 | ≥5tr tiền mặt ⇒ không được khấu trừ (chỉ PENDING/NON) | R-4 engine |
| R-P6 | Cộng nhiều hóa đơn <5tr trong cùng ngày ≥5tr ⇒ cần CK (v2: aggregate checker) | out-of-scope v1, ghi chú |
| R-P7 | Hủy chỉ POSTED, chỉ CHIEF+, soft-cancel | service + API roles |
| R-P8 | Mọi mutation gắn checksum SHA-256 chain | _stamp pattern |
| R-P9 | Không xóa cứng — lưu trữ 10 năm | Luật Kế toán Art.11 |

## 3. Data flow (DFD level 1)

```
[Supplier] →(HĐĐT PDF/XML tay)→ (Purchases UI)
(UI) → svc.create → repo.supplier_invoices
repo → checksum chain → audit_events (CREATE/POST/CANCEL/PROOF_ATTACHED)
svc.post → gợi ý bút toán → (tương lai) voucher brick link
GET list/deductibility → Bảng kê đầu vào → TaxEngine (future 01/GTGT)
```

## 4. Workflow — trạng thái

```
        create            post             cancel
  ●──────────────▶ DRAFT ───────▶ POSTED ───────▶ CANCELLED
                     ▲  (P06 nếu    (P07 nếu chưa
                     └── re-post)    chưa POSTED)
```

Hủy sau POSTED **không** hoàn trạng thái; điều chỉnh bằng hóa đơn điều chỉnh của NCC (v2 import).

## 5. Tích hợp chéo-brick (contract primitives)

| Brick | Chiều | Nội dung |
|---|---|---|
| fiscal_year_period | reads | find_open_period(entry_date) |
| coa | reads | validate_posting_account(expense_account, regime) |
| audit_log | writes | CREATE / POST / CANCEL / PROOF_ATTACHED events |
| company | reads | accounting_regime (pattern-aware validation) |
