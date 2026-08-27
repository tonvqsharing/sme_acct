# Use Cases — Tools & Equipment (CCDC) Module

## UC-001: Create CCDC Record

**Actor:** ACCOUNTANT  
**Precondition:** User is authenticated, COA has valid expense accounts  
**Trigger:** User needs to register a new tool/equipment

**Happy Path:**
1. User navigates to CCDC management screen
2. User clicks "Thêm CCDC" (Add CCDC)
3. System displays creation form
4. User fills in: code, name, category, purchase_date, purchase_price, useful_life_months, expense_account_code
5. User optionally fills: salvage_value, assigned_to, cost_center_id, dimension_value_id, description
6. User clicks "Lưu" (Save)
7. System validates all fields (VR-001 to VR-010)
8. System generates audit_checksum
9. System saves CCDC with status ACTIVE
10. System returns success response with CCDC data

**Alternative Paths:**
- 4a. User selects category from dropdown → system auto-suggests expense_account_code
- 6a. User clicks "Lưu và thêm mới" (Save and add new) → system saves and resets form
- 7a. Validation fails → system highlights errors, user corrects

**Exception Paths:**
- 7b. Duplicate code → system shows error "Trùng mã CCDC"
- 7c. Invalid expense account → system shows error "Tài khoản chi phí không hợp lệ"
- 7d. purchase_price ≤ 0 → system shows error "Giá trị phải lớn hơn 0"

**Postcondition:** CCDC record created, audit trail recorded

---

## UC-002: List and Filter CCDC

**Actor:** Any authenticated user  
**Precondition:** User is authenticated  
**Trigger:** User needs to view CCDC list

**Happy Path:**
1. User navigates to CCDC list screen
2. System displays all CCDC for user's company
3. User can filter by: category, status, cost_center, date range
4. User can sort by: code, name, purchase_date, purchase_price
5. System returns filtered results

**Alternative Paths:**
- 3a. User applies multiple filters → system applies AND logic
- 3b. User clears filters → system shows all records

---

## UC-003: Modify CCDC

**Actor:** ACCOUNTANT  
**Precondition:** CCDC exists, user has permission  
**Trigger:** User needs to update CCDC information

**Happy Path:**
1. User selects CCDC from list
2. User clicks "Sửa" (Edit)
3. System displays edit form with current values
4. User modifies allowed fields (name, category, assigned_to, cost_center_id, dimension_value_id, description)
5. User clicks "Cập nhật" (Update)
6. System validates changes
7. System updates CCDC
8. System updates audit_checksum
9. System returns success

**Exception Paths:**
- 4a. User tries to modify code → field is read-only
- 4b. User tries to modify status → must use lifecycle endpoints

---

## UC-004: Deactivate CCDC

**Actor:** CHIEF_ACCOUNTANT  
**Precondition:** CCDC exists with status ACTIVE  
**Trigger:** CCDC temporarily not in use

**Happy Path:**
1. User selects ACTIVE CCDC
2. User clicks "Ngừng phân bổ" (Deactivate)
3. System confirms: "Bạn có chắc muốn ngừng phân bổ CCDC này?"
4. User confirms
5. System stops pending allocations
6. System sets status = INACTIVE
7. System updates audit_checksum
8. System returns success

**Exception Paths:**
- 2a. CCDC has pending allocations for current month → system processes current month first
- 4a. User cancels → no change

---

## UC-005: Reactivate CCDC

**Actor:** CHIEF_ACCOUNTANT  
**Precondition:** CCDC exists with status INACTIVE  
**Trigger:** CCDC returns to use

**Happy Path:**
1. User selects INACTIVE CCDC
2. User clicks "Kích hoạt lại" (Reactivate)
3. System confirms
4. User confirms
5. System sets status = ACTIVE
6. System resumes allocations from next month
7. System updates audit_checksum
8. System returns success

---

## UC-006: Write Off CCDC

**Actor:** CHIEF_ACCOUNTANT  
**Precondition:** CCDC exists, all allocations completed  
**Trigger:** CCDC is no longer usable

**Happy Path:**
1. User selects CCDC
2. User clicks "Thanh lý" (Write off)
3. System displays write-off form
4. User selects reason: THANH_LY (disposal), MAT (lost), HU_HONG (damaged)
5. User enters write_off_date and notes
6. System calculates remaining value
7. System creates write-off journal entry
8. System sets status = WRITTEN_OFF
9. System updates audit_checksum
10. System returns success

**Exception Paths:**
- 7a. Remaining value > 0 → system creates expense entry for remaining
- 7b. Reason = MAT → system creates loss entry

---

## UC-007: Run Monthly Allocation

**Actor:** ACCOUNTANT  
**Precondition:** CCDC records exist with status ACTIVE and remaining allocations  
**Trigger:** Monthly allocation process

**Happy Path:**
1. User navigates to Allocation screen
2. User selects month/year
3. System calculates allocations for all ACTIVE CCDC
4. System displays allocation table:
   - CCDC code, name
   - Remaining value
   - Amount to allocate this month
   - Expense account
   - Cost center / dimension
5. User reviews and confirms
6. System creates allocation records
7. System creates journal entries: Dr 623/627/641/642, Cr 242
8. System updates remaining values
9. System returns success

**Alternative Paths:**
- 5a. User modifies allocation amounts → system recalculates
- 5b. User excludes specific CCDC → system skips

**Exception Paths:**
- 3a. No CCDC to allocate → system shows "Không có CCDC cần phân bổ"
- 7a. Journal entry fails → system rolls back

---

## UC-008: View Allocation Report

**Actor:** Any authenticated user  
**Precondition:** Allocations exist  
**Trigger:** User needs allocation report

**Happy Path:**
1. User navigates to Reports
2. User selects "Bảng phân bổ CCDC"
3. User selects year
4. System displays monthly allocation schedule for all CCDC
5. User can export to Excel

---

## UC-009: View CCDC Ledger

**Actor:** Any authenticated user  
**Precondition:** CCDC records exist  
**Trigger:** User needs CCDC ledger

**Happy Path:**
1. User navigates to Reports
2. User selects "Sổ theo dõi CCDC"
3. User selects filters (date range, category, status)
4. System displays ledger with:
   - Opening balance
   - Increases (purchases)
   - Decreases (write-offs)
   - Closing balance
5. User can export to Excel

---

## UC-010: Transfer CCDC Between Departments

**Actor:** ACCOUNTANT  
**Precondition:** CCDC exists with status ACTIVE  
**Trigger:** CCDC moves to different department

**Happy Path:**
1. User selects CCDC
2. User clicks "Điều chuyển" (Transfer)
3. User selects new cost_center_id and/or dimension_value_id
4. User enters transfer date and reason
5. System updates CCDC assignment
6. System updates audit_checksum
7. System returns success

**Note:** Transfer does NOT create journal entry — only updates assignment for future allocations.
