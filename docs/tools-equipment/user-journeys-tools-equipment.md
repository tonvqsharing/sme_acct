# User Journeys — Tools & Equipment (CCDC) Module

## UJ-001: ACCOUNTANT — Register New CCDC

**Persona:** Kế toán viên, 3–5 năm kinh nghiệm  
**Goal:** Đăng ký CCDC mới mua  
**Device:** Desktop (web browser)

### Journey:
1. **Login** → System shows dashboard
2. **Navigate** → Click "Công cụ dụng cụ" in sidebar
3. **Click** "Thêm CCDC mới"
4. **Fill form:**
   - Mã CCDC: `LPT-001` (auto-suggest or manual)
   - Tên: `Laptop Dell Inspiron 15`
   - Loại: `Thiết bị văn phòng` (dropdown)
   - Ngày mua: `2026-08-15` (date picker)
   - Nguyên giá: `15,000,000` (VND input)
   - Số kỳ phân bổ: `12` (months, auto-calculated or manual)
   - TK chi phí: `642` (dropdown from COA)
   - Bộ phận sử dụng: `Phòng Kế toán` (dropdown from cost centers)
5. **System validates:**
   - ✅ Code unique
   - ✅ Price > 0
   - ✅ Useful life 1–36 months
   - ✅ Valid expense account
6. **System calculates:**
   - Phân bổ hàng tháng: `15,000,000 / 12 = 1,250,000`
   - Ghi nhận vào TK 242
7. **Click** "Lưu"
8. **System confirms:** "Đã tạo CCDC LPT-001 thành công"
9. **System shows** CCDC detail page with allocation schedule

**Pain points:**
- Phải nhớ đúngTK chi phí (623/627/641/642)
- Phải biết số kỳ phân bổ phù hợp (≤ 36 tháng)

---

## UJ-002: ACCOUNTANT — Run Monthly Allocation

**Persona:** Kế toán viên  
**Goal:** Phân bổ chi phí CCDC hàng tháng  
**Device:** Desktop

### Journey:
1. **Login** → Navigate to "Phân bổ CCDC"
2. **Select period:** Tháng 08/2026
3. **System displays:** Bảng phân bổ CCDC
   ```
   Mã     | Tên                    | Còn lại   | Phân bổ tháng 8
   LPT-001| Laptop Dell Inspiron 15 | 13,750,000| 1,250,000
   MK-001 | Máy photocopy Ricoh     | 2,400,000 | 400,000
   ```
4. **Review:** Check amounts are correct
5. **Click** "Xác nhận phân bổ"
6. **System creates:** 2 journal entries
   - Dr 642 1,250,000 / Cr 242 1,250,000 (Laptop)
   - Dr 623 400,000 / Cr 242 400,000 (Máy photocopy)
7. **System confirms:** "Đã phân bổ CCDC tháng 8/2026"

**Pain points:**
- Phải kiểm tra kỹ số tiền phân bổ
- Nếu có CCDC mới trong tháng, phải thêm vào danh sách

---

## UJ-003: CHIEF_ACCOUNTANT — Write Off Damaged CCDC

**Persona:** Kế toán trưởng, 10+ năm kinh nghiệm  
**Goal:** Thanh lý CCDC bị hư hỏng  
**Device:** Desktop

### Journey:
1. **Login** → Navigate to "Công cụ dụng cụ"
2. **Find CCDC:** Search `MK-001` (Máy photocopy)
3. **Click** "Thanh lý"
4. **System shows:** Write-off form
   - CCDC: MK-001 - Máy photocopy Ricoh
   - Nguyên giá: 3,600,000
   - Giá trị còn lại: 1,200,000
5. **Select reason:** `Hư hỏng` (damaged)
6. **Enter date:** `2026-08-20`
7. **System calculates:** Remaining value = 1,200,000
8. **System shows journal entry:**
   - Dr 642 1,200,000 (chi phí)
   - Cr 1531 1,200,000 (giảm CCDC)
9. **Click** "Xác nhận thanh lý"
10. **System confirms:** "Đã thanh lý CCDC MK-001"
11. **System updates:** Status = WRITTEN_OFF

**Pain points:**
- Phải kiểm tra CCDC đã phân bổ hết chưa
- Nếu CCDC đang phân bổ dở, phải ngừng phân bổ trước

---

## UJ-004: AUDITOR — View CCDC Report

**Persona:** Kiểm toán viên  
**Goal:** Kiểm tra sổ CCDC  
**Device:** Desktop

### Journey:
1. **Login** → Navigate to "Báo cáo"
2. **Select:** "Sổ theo dõi CCDC"
3. **Set filters:** Năm 2026, Tất cả loại
4. **System displays:** Bảng sổ CCDC
   ```
   Mã     | Tên                    | Nguyên giá | Đã PB   | Còn lại | Trạng thái
   LPT-001| Laptop Dell Inspiron 15 | 15,000,000 | 5,000,000| 10,000,000| Active
   MK-001 | Máy photocopy Ricoh     | 3,600,000  | 2,400,000| 1,200,000| Active
   ```
5. **Click** "Xuất Excel" → Download report
6. **Verify:** Check allocation amounts match journal entries

**Pain points:**
- Cần export để so sánh với sổ cái
- Cần kiểm tra tính nhất quán giữa sổ CCDC và sổ cái TK 153
