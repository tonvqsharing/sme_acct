# Use Cases — Purchase Invoices

## UC-P1 Nhập hóa đơn mua trong nước (kèm thuế GTGT)
**Actor:** ACCOUNTANT · **Pre:** kỳ mở, COA có tài khoản chi phí chi tiết
1. POST /purchase-invoices {supplier, mst, số/ký hiệu/ngày HĐ, entry_date, lines[{expense_account, amount_pre_vat, vat_rate, deductible}], payment_method}
2. Hệ thống kiểm tra: trùng (mst+số+ký hiệu) → 409 P02 nếu trùng; kỳ mở → 409 P03; tài khoản hợp lệ → 422 P04; tổng khớp → 422 P05
3. Lưu DRAFT + checksum genesis
4. POST …/post → POSTED, sinh bút toán gợi ý: Dr expense + Dr 1331(và/hoặc vốn hóa) / Cr 331·111·112
**Post-condition:** hóa đơn nằm trong bảng kê đầu vào kỳ tương ứng.

## UC-P2 Khấu trừ chờ bằng chứng thanh toán
**Actor:** ACCOUNTANT · Hóa đơn ≥5 triệu, payment_method≠cash, payment_proof=false
- Hệ thống đặt deductibility=PENDING_PROOF (R-4), vẫn cho POSTED
- Khi đính kèm chứng từ: PATCH proof=true → tự chuyển DEDUCTIBLE + checksum event `PROOF_ATTACHED`

## UC-P3 Hủy hóa đơn đã ghi sổ
**Actor:** CHIEF_ACCOUNTANT
1. POST …/cancel reason bắt buộc
2. Kiểm tra POSTED → CANCELLED, checksum chain, audit event `CANCEL`
3. Bảng kê đầu vào loại khỏi kỳ hiện hành; không xóa dòng (retention)

## UC-P4 Tra cứu & xuất bảng kê đầu vào
**Actor:** bất kỳ authenticated (AUDITOR OK)
GET list filter status/deductibility/kỳ → phục vụ 01/GTGT giai đoạn sau.

# Happy paths
| ID | Kịch bản |
|---|---|
| HP-P1 | Mua văn phòng phẩm 2.2tr (gồm VAT 10%) trả chuyển khoản → DEDUCTIBLE ngay |
| HP-P2 | Mua nguyên liệu 50tr chuyển khoản 30 ngày → Cr 331, DEDUCTIBLE |
| HP-P3 | Mua dịch vụ <5tr tiền mặt → DEDUCTIBLE, không cần chứng từ |

# Alternative paths
| ID | Độ lệch | Xử lý |
|---|---|---|
| AP-P1 | Hàng về trước, hóa đơn sau | v1: nhập khi có hóa đơn (ghi chú); v2 nhận-hóa-đơn riêng |
| AP-P2 | VAT không khấu trừ được (không chịu thuế) | deductible=false → VAT vốn hóa vào chi phí |
| AP-P3 | Trả chậm/trả góp ≥5tr chưa đến hạn | vẫn DEDUCTIBLE, ghi chú hợp đồng (NĐ 181 Đ.26) |

# Exception paths
| ID | Tình huống | Code |
|---|---|---|
| EX-P01 | Thiếu actor/reason | 400 MISSING_ACTOR |
| EX-P02 | Trùng mst+số+ký hiệu | 409 DUPLICATE_INVOICE |
| EX-P03 | Kỳ đã khóa | 409 PERIOD_CLOSED |
| EX-P04 | Sai/tài khoản aggregate | 422 INVALID_ACCOUNT |
| EX-P05 | subtotal/vat không khớp payload | 422 TOTAL_MISMATCH |
| EX-P06 | post lần 2 | 409 ALREADY_POSTED |
| EX-P07 | cancel khi chưa POSTED | 422 NOT_POSTED_ON_CANCEL |
| EX-P08 | AUDITOR ghi | 403 AUDITOR_READ_ONLY |
