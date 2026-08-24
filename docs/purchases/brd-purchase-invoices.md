# BRD — Purchase Invoices Module (Mua hàng & hóa đơn mua vào)

## 1. Vấn đề
Doanh nghiệp SME hiện nhập hóa đơn mua vào thủ công; thuế GTGT đầu vào không được theo dõi hệ thống ⇒ rủi ro kê khai thiếu/khấu trừ sai, mất thời gian đối soát cuối kỳ, không truy vết được bộ chứng từ.

## 2. Mục tiêu kinh doanh
1. Ghi nhận mọi hóa đơn mua hàng/dịch vụ kèm thuế GTGT đầu vào trong 1 màn hình.
2. Tự động phân loại được-khấu-trừ / chờ-bằng-chứng / không-khấu-trừ theo Luật GTGT 2024 + NĐ 181/2025 (Đ.26, sửa NĐ 144/2026).
3. Cung cấp dữ liệu đầu vào chuẩn cho tờ khai 01/GTGT (module khai thuế giai đoạn sau).
4. Công nợ phải trả (TK 331) theo dõi theo hóa đơn — nền cho phân bổ thanh toán sau này.

## 3. Phạm vi
**Trong phạm vi v1:** nhập tay hóa đơn mua trong nước (đã có hóa đơn); kiểm tra trùng; hạch toán Nợ chi phí/TSCĐ + 1331 / Có 111·112·331; trạng thái DRAFT→POSTED→CANCELLED; checksum chain; API REST.
**Ngoài phạm vi v1:** import XML từ Tổng cục Thuế/email; danh mục nhà cung cấp; phiếu nhập kho; mua nhập khẩu; tạm tính thuế TNDN.

## 4. Stakeholders
| Vai trò | Quan tâm |
|---|---|
| Kế toán viên | nhập nhanh, cảnh báo trùng, đúng tài khoản |
| Kế toán trưởng | duyệt hủy, kiểm soát khấu-trừ/chờ-bằng-chứng |
| Kiểm toán viên | tra cứu, xuất bảng kê đầu vào |
| Giám đốc | tổng chi phí mua, thuế được khấu trừ kỳ này |

## 5. Ràng buộc pháp lý chính
- Thời điểm lập/ghi nhận theo NĐ 254/2026 (hàng: chuyển quyền sở hữu; dịch vụ: hoàn thành; đêm: ngày làm việc kế tiếp).
- Khấu trừ: hóa đơn hợp pháp + chứng từ không tiền mặt cho hóa đơn ≥5 triệu (gồm VAT) — Điều 26 NĐ 181/2025 (sửa NĐ 144/2026).
- Lưu trữ tối thiểu 10 năm — Luật Kế toán 2015 Art. 11.

## 6. Tiêu chí thành công
- 100% hóa đơn POSTED có checksum truy vết.
- Bảng kê đầu vào khớp sổ 1331 trên Trial Balance.
- Nhập 1 hóa đơn < 60 giây, cảnh báo trùng ngay khi lưu.
