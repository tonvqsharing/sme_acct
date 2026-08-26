# BRD — Fixed Assets Module (Tài sản cố định)

## 1. Vấn đề
TSCĐ được theo dõi thủ công qua Excel; khấu hao tính tay hàng tháng; không có sổ TSCĐ tự động; rủi ro sai/khấu hao thiếu/thừa không phát hiện kịp.

## 2. Mục tiêu
1. Quản lý danh mục TSCĐ: nguyên giá, thời gian khấu hao, phương pháp, bộ phận sử dụng
2. Tự động tính khấu hao hàng tháng theo TT99/2025 (3 phương pháp)
3. Sinh bút toán khấu hao tự động: Dr chi phí / Cr 214
4. Theo dõi ghi tăng/ghi giảm/điều chuyển/đánh giá lại với checksum chain
5. Báo cáo Mẫu 06-TSCĐ

## 3. Phạm vi v1
**Trong phạm vi:** Ghi tăng · Tính khấu hao (đường thẳng) · Ghi giảm (thanh lý/nhượng bán) · Sổ TSCĐ · API REST
**Ngoài phạm vi v1:** Điều chuyển bộ phận (v2) · Đánh giá lại (v2) · Kiểm kê TSCĐ (v2) · Khấu hao số dư giảm dần/sản lượng (v2)

## 4. Ràng buộc pháp lý
- Trích khấu hao từ NGÀAY tăng/giảm trong tháng (theo số ngày)
- 3 loại không trích: đã khấu hao hết vẫn dùng · mất · không sở hữu (trừ thuê TC)
- Thay đổi thời gian khấu hao: 1 lần/tài sản + phê duyệt MOF/Sở TC
- Lưu trữ 10 năm sau thanh lý — Luật Kế toán Art. 11

## 5. Tiêu chí thành công
- Khấu hao hàng tháng = Σ(NG / số tháng khấu hao), chính xác đến từng tài sản
- Bút toán Dr 627·641·642 / Cr 214 tự động sinh và cân đối
- Sổ TSCĐ tại bất kỳ ngày nào phản ánh đúng nguyên giá/hao mòn lũy kế/giá trị còn lại
