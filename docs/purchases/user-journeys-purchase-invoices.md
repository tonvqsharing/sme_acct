# User Journeys — Purchase Invoices

## Journey 1 — Kế toán viên nhập hóa đơn cuối tháng
1. 08:00 nhận 12 hóa đơn PDF từ Zalo/email NCC.
2. Mở `POST /purchase-invoices`, dán MST → hệ thống gợi ý supplier (v2), nhập số/ký hiệu/ngày.
3. Thêm dòng: chọn tài khoản 6421, gõ 2.000.000, VAT 10% tự nhân.
4. Bấm Lưu — popup đỏ "Trùng hóa đơn" với HĐ tuần trước (R-P1 cứu 1 lần nhầm).
5. Sửa ký hiệu, Lưu DRAFT; POST — thấy bút toán Dr 6421/Dr 1331/Cr 331 hiện preview.
⏱ 4 phút/hóa đơn sau khi quen; zero Excel.

## Journey 2 — Kế toán trưởng duyệt kỳ
1. Ngày 3 tháng sau: GET list ?deductibility=PENDING_PROOF → 3 hóa đơn chờ chứng từ.
2. Nhờ kế toán đuổi CK-báo nợ; attach proof → 3 dòng chuyển DEDUCTIBLE.
3. GET bảng kê đầu vào kỳ 8 → tổng khớp số dư 1331 trên Trial Balance ✓.

## Journey 3 — Kiểm toán viên truy vết
1. Chọn ngẫu nhiên 1 hóa đơn POSTED → GET detail: checksum + audit chain đầy đủ CREATE→POST.
2. Đối chiếu PDF gốc lưu ngoài: số tiền/ký hiệu khớp. Không phát hiện can thiệp.

## Journey 4 — Giám đốc nhìn con số
GET ?deductibility=DEDUCTIBLE&period=8 → "Thuế được khấu trừ kỳ 8: 47.350.000đ" — quyết định mua sắm Q4 dựa trên dòng tiền thuế.
