# User Journeys: System Settings Module

## J-01: Chief Accountant First-Time Setup Journey
**Profile**: Chief Accountant, newly assigned to company; no prior system settings configured  
**Precondition**: Company entity exists in system; database migration applied; user has admin role  
**Step Count**: 14 steps  

**Step 1**: Log in to system with admin credentials → redirected to dashboard  
**Step 2**: Click "Hệ thống Cấu hình" main menu item → System Settings page loads  
**Step 3**: Page displays "Chưa có cấu hình hệ thống" banner + initialization form  
**Step 4**: Form shows legal constants from domain defaults:  
  - Hệ thống kế toán: TT200 (default)  
  - Kỳ tài chính: Jan 1 - Dec 31 (default)  
  - Thuế GTGT: {0, 5, 10} (default)  
  - Chế độ VAT: Deduction (default)  
  - Chế độ e-invoice: Software Cert (default)  
**Step 5**: Chief Accountant reviews each field against Vietnamese law knowledge  
**Step 6**: Clicks "Kiểm tra Tuân thủ Pháp lý" → System validates all LAW-type flags  
  - If passes: "Kiểm tra thành công" banner appears  
  - If fails: Error lists non-compliant fields + legal basis references  
**Step 7**: Clicks "Khởi tạo Cấu hình Hệ thống" → Progress spinner shown  
**Step 8**: SystemSettingsService.initialize() executed internally  
**Step 9**: CompanyConfig record created; config_version=1; audit log CREATE event persisted  
**Step 10**: Banner: "Cấu hình hệ thống đã được khởi tạo" + notice: "Chief Accountant cần đánh giá lại trước khi dùng PROD"  
**Step 11**: Clicks "Đánh giá lại" → legal_reviewed_at set to now; banner: "Đã đánh giá pháp lý"  
**Step 12**: Clicks "Điều hướng đến Bảng điều khiển" → redirected to main dashboard  
**Step 13**: System settings now active; all subsequent operations validate against CompanyConfig  
**Step 14**: Journey completes; Chief Accountant can now configure period locks, e-invoice series, etc.  

**Alternative Paths**:  
- A-01: Step 6 fails → Error modal lists non-compliant fields + "Lỗi tuân thủ pháp lý - không thể khởi tạo"; journey ends  
- A-02: Step 9 fails (database constraint error) → Error modal + retry option  
- A-03: Step 10 clicked without Step 6 passing → Warning: "Chưa qua kiểm tra tuân thủ"; still allows proceed but logs non-compliance  

**Postconditions**: CompanyConfig exists; all subsequent system operations validate against it; audit trail complete for initialization  

---

## J-02: Period Lock Management Journey
**Profile**: Chief Accountant / Kế toán trưởng; managing accounting period locks  
**Precondition**: CompanyConfig exists; at least one fiscal year defined  
**Step Count**: 9 steps  

**Step 1**: Log in → navigate to "Ky khóa Kì kế toán" submenu under Hệ thống Cấu hình  
**Step 2**: "Thêm Ky khóa Kì kế toán" form loads; inputs: Ký hiệu kì (optional), Ngày bắt đầu, Ngày kết thúc  
**Step 3**: Chief Accountant inputs dates (e.g., 2026-07-01 to 2026-09-30 for Q3)  
**Step 4**: Clicks "Khóa Kì kệ toán" → System checks PeriodLockService.is_locked()  
**Step 5**: If period already locked → Error: "Ky khóa kì kế toán [dates] đã được khóa bởi user X vào [date]" + audit log link  
**Step 6**: If period not locked → System creates PeriodLock record; disables posting at service layer  
**Step 6**: Success: "Ky khóa kì kế toán [dates] đã được khóa thành công" + count of disabled postings shown  
**Step 7**: Period now appears in "Danh sách Ky khóa" list  
**Step 8**: Clicks "Mở khóa" on existing lock →  
  - If vouchers/invoices exist in period → Error: "Không thể mở khóa: còn [N] chứng từ/posting"; shows count + detail link  
  - If no vouchers/invoices → System sets is_locked=False; emits audit LOG DELETE; Success: "Ky khóa kì kế toán [dates] đã được mở khóa thành công"  
**Step 9**: Journey completes; period status updated in UI  

**Alternative Paths**:  
- A-01: Step 5 → Error shown + option to view existing vouchers/invoices in that period  
- A-02: Step 8 → Error shown + option to void/post existing vouchers/invoices first  

**Postconditions**: PeriodLock record reflects correct lock state; audit trail complete; service layer correctly blocks/enables posting  

---

## J-03: Config Update Journey
**Profile**: Chief Accountant / Admin; modifying a system flag  
**Precondition**: CompanyConfig exists; admin authenticated  
**Step Count**: 7 steps  

**Step 1**: Log in → navigate to "Cấu hình Hệ thống" submenu  
**Step 2**: List of current config flags displayed with current values + config_version  
**Step 2**: Clicks "Sửa đổi" on target flag (e.g., VAT method) → edit form loads  
**Step 2**: Form shows: Current value + flag_type badge (LAW/CONFIG) + read-only note if LAW  
**Step 3**: Chief Accountant inputs new value + clicks "Cập nhật"  
**Step 4**: System checks flag_type:  
  - If LAW → FlagLockedError + "Cờ hệ thống LAW không thể thay đổi mà không có migration patch" + legal basis reference  
  - If CONFIG → proceeds to step 5  
**Step 5**: System emits AuditLogService event BEFORE mutation  
**Step 5**: System updates CompanyConfig field + config_version increments  
**Step 5**: System emits AuditLogService event AFTER mutation  
**Step 6**: Success: "Cấu hình '{field}' đã được cập nhật"; new config_version displayed  
**Step 6**: Clicks "Xem Nhật ký thay đổi" → navigates to audit log view for this config  

**Alternative Paths**:  
- A-01: Step 4 → FlagLockedError shown + "Để thay đổi cờ LAW, cần tạo migration patch"; link to documentation  
- A-02: Concurrent edit → ConfigVersionConflict + "Phiên bản hiện tại: X, phiên bản bạn gửi: Y"; forces re-read + retry  

**Postconditions**: CompanyConfig updated; config_version incremented; two audit events (before/after); audit trail complete  
