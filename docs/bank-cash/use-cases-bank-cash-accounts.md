# Use Cases — Bank & Cash Accounts Module

## 1. Overview

This document describes all use cases for the Bank & Cash Accounts module, organized by actor role and operation type. Follows the same format as other module use cases in this codebase (currencies, COA, fiscal years).

---

## 2. Use Case Catalog

### Actant: ACCOUNTANT (Kế toán viên)

| UC ID | Use Case Title | Preconditions | Postconditions | Main Flow |
|-------|---------------|---------------|----------------|-----------|
| UC-01 | List bank accounts | User logged in as ACCOUNTANT | Bank account list displayed | 1. User navigates to Bank Accounts page<br>2. Clicks "List Bank Accounts"<br>3. System shows list with filters (company, status, primary)<br>4. Pagination applied (default 20 per page) |
| UC-02 | Create bank account | - User logged in as ACCOUNTANT<br>- Company exists in system | Bank account created with checksum in audit log | 1. User clicks "Create Bank Account"<br>2. Fills form: bank_name, account_number, account_holder, branch, is_primary (optional)<br>3. Clicks "Save"<br>4. System validates: actor UUID, code uniqueness, company exists<br>5. Bank account saved to DB<br>6. SHA-256 checksum appended to audit log<br>7. Success message shown |
| UC-03 | Update bank account | - Bank account is ACTIVE<br>- User has WRITE role | Bank account updated, checksum appended | 1. User selects bank account to update<br>2. Edits fields: bank_name, branch, is_primary (SOD required)<br>3. Clicks "Update"<br>4. System validates: account not CLOSED, SOD rules, actor has permission<br>5. Updates DB record<br>6. Appends checksum to audit log<br>7. Success message shown |
| UC-04 | Record cash transaction | - Cash account is ACTIVE<br>- User has ACCOUNTANT role | Cash balance updated, audit logged | 1. User navigates to Cash Account<br>2. Clicks "Record Transaction"<br>3. Enter: amount (positive=in, negative=out), reason, date<br>4. System validates: balance sufficiency, account not system, not CLOSED<br>5. Updates current_balance = current_balance + amount<br>6. Appends checksum to audit log<br>7. Shows updated balance |
| UC-05 | List cash accounts | User logged in as ACCOUNTANT | Cash account list displayed | 1. User navigates to Cash Accounts page<br>2. System lists all cash accounts by company<br>3. Shows: code, name, opening_balance, current_balance, status |
| UC-06 | List unresolved reconciliations | User logged in as AUDITOR or CHIEF_ACCOUNTANT | List of unresolved reconciliation items displayed | 1. User navigates to Reconciliations page<br>2. System shows all unresolvable reconciliations by company<br>3. Filters: by company, by date range, by bank account |
| UC-07 | View bank account detail | User logged in (any valid role) | Bank account detail page displayed | 1. User selects bank account from list<br>2. System shows detail: all fields, checksum chain, audit events, related reconciliations |

---

### Actant: CHIEF_ACCOUNTANT (Kế toán trưởng)

| UC ID | Use Case Title | Preconditions | Postconditions | Main Flow |
|-------|---------------|---------------|----------------|-----------|
| UC-08 | Set bank account as primary (SOD) | - User logged in as CHIEF_ACCOUNTANT or ADMIN<br>- Target bank account is ACTIVE | Primary changed, both actors logged in audit | 1. Chief Accountant requests primary change via UI<br>2. System sends approval request to 2nd actor (ACCOUNTANT)<br>3. 2nd actor logs in, reviews request<br>4. 2nd actor approves or rejects<br>5. If approved: status updated, is_primary=TRUE, checksums appended for both actors<br>6. If rejected: request cancelled, original state preserved |
| UC-09 | Close bank account (SOD) | - Bank account is ACTIVE<br>- No related invoices/vouchers<br>- User logged in as CHIEF_ACCOUNTANT | Account status → SUSPENDED → CLOSED after 2nd approval | 1. CHIEF_ACCOUNTANT requests closure<br>2. System checks: no related invoices/vouchers (FK check)<br>3. If OK: status → SUSPENDED, 1st checksum appended<br>4. System waits for 2nd actor approval<br>5. 2nd actor reviews, approves → status → CLOSED, 2nd checksum appended<br>6. If 2nd actor rejects: status reverts to ACTIVE |
| UC-10 | Close cash account | - Cash account is ACTIVE<br>- Current balance = 0 (or transferred)<br>- User logged in as CHIEF_ACCOUNTANT | Cash account status → CLOSED | 1. User selects cash account to close<br>2. System validates: balance = 0 (or transferred)<br>3. If valid: status → CLOSED, checksum appended<br>4. If balance ≠ 0: error shown, must zero balance first |
| UC-11 | Create cash account | - User logged in as CHIEF_ACCOUNTANT or ADMIN<br>- Code must be unique per company | Cash account created, current_balance = opening_balance | 1. User fills form: code (TT99 format), name, opening_balance (VND)<br>2. System validates: code format ^[1-9]\d{2}$ or ^[1-9]\d{3}$, uniqueness per company<br>3. Creates cash account with current_balance = opening_balance<br>4. Appends checksum to audit log<br>5. Success message shown |
| UC-12 | Resolve bank reconciliation (SOD) | - Unresolved reconciliation exists<br>- User is 2nd actor (CHIEF_ACCOUNTANT/ADMIN) | Reconciliation marked resolved, both actors logged | 1. 1st actor (requester) starts resolution process<br>2. System marks as "1st actor approved", appends checksum<br>3. 2nd actor (CHIEF_ACCOUNTANT/ADMIN) reviews difference<br>3. 2nd actor approves → reconciliation marked "resolved", 2nd checksum appended<br>4. If difference > 0.01 and 2nd actor rejects → remains unresolved, investigation needed |

---

### Actant: ADMIN (Quản trị hệ thống)

| UC ID | Use Case Title | Preconditions | Postconditions | Main Flow |
|-------|---------------|---------------|----------------|-----------|
| UC-13 | System configuration | - User logged in as ADMIN | System-wide bank/cash settings configured | 1. ADMIN accesses System Settings<br>2. Configures: SOD thresholds, retention policies, approval workflows<br>3. Settings saved to company config, audit logged |
| UC-14 | Bank statement import (CAMT) | - User logged in as CHIEF_ACCOUNTANT or ADMIN<br>- CAMT.053/CAMT.054 file uploaded | Bank transactions imported atomically (all-or-nothing) | 1. User uploads CAMT XML file<br>2. System parses all bank transactions<br>3. For each transaction: create cash account transaction or bank reconciliation line<br>4. If ANY row fails: entire import rolled back, no data saved<br>5. If all succeed: success message with count of transactions imported<br>6. All events logged with checksums |
| UC-15 | Generate bank reconciliation report | - User logged in as AUDITOR or CHIEF_ACCOUNTANT | Report generated in PDF/CSV format | 1. User selects date range and company<br>2. System queries all reconciliations for that period<br>3. Generates report: statement_balance, internal_balance, difference, resolution status<br>4. Exports to PDF/CSV, stored in audit log retention period |

---

### Actant: AUDITOR (Kiểm toán viên)

| UC ID | Use Case Title | Preconditions | Postconditions | Main Flow |
|-------|---------------|---------------|----------------|-----------|
| UC-16 | View bank/cash audit trail | User logged in as AUDITOR | Audit trail displayed, read-only | 1. User navigates to Audit Log section<br>2. Filters: by entity type (bank_account/cash_account/reconciliation), date range, actor<br>3. System shows: checksum chain, actor UUID, reason, timestamp for each event<br>4. No modify capability available (disabled UI) |
| UC-17 | Verify destruction readiness | User logged in as AUDITOR | Destruction status shown | 1. User requests destruction verification for entities older than 10 years<br>2. System checks: all checksums intact, no gaps in chain<br>3. Reports: "Ready for destruction" or "Issues found: X broken checksums"<br>4. If ready: auditor can initiate destruction process via /api/audit-log/destroy |
| UC-18 | Check retention status | User logged in as AUDITOR | Retention status displayed | 1. User calls GET /api/audit-log/retention-status<br>2. System returns: count of entities by age, how many past 10-year retention period, how many ready for destruction |

---

### Actant: DIRECTOR (Giám đốc)

| UC ID | Use Case Title | Preconditions | Postconditions | Main Flow |
|-------|---------------|---------------|----------------|-----------|
| UC-19 | Company-level bank overview | User logged in as DIRECTOR | Company bank summary displayed | 1. Director accesses dashboard<br>2. System shows: total bank accounts, primary account, total cash on hand, total reconciliations this period<br>3. Overview includes SOD approval status pending |
| UC-20 | Emergency bank account override | - Critical business need<br>- User logged in as DIRECTOR with CHIEF_ACCOUNTANT co-signature | Override approved, logged with full audit | 1. Director requests emergency override via formal channel<br>2. System requires co-signature from Chief Accountant<br>3. Both actors' UUIDs logged in audit chain<br>4. Override applied with reason "EMERGENCY_OVERRIDE", checksum appended<br>5. Full audit trail maintained, report generated |

---

## 2. Detailed Use Case Flows

### UC-02: Create Bank Account — Full Flow

```
PRECONDITIONS:
- User is authenticated and has ACCOUNTANT role
- Company ID known from session (company_id)
- Actor UUID (D11) available from login session

MAIN SUCCESS SUCCESS FLOW:
1. User navigates to "Create Bank Account" page
2. User fills form:
   - bank_name: "VietinBank" (required)
   - account_number: "123456789" (required, unique per company)
   - account_holder: "Công ty ABC" (required)
   - branch: "Cục Thành Phố" (optional, default "")
   - is_primary: false (optional, boolean)
3. User clicks "Save"
4. System performs:
   a. Validate actor UUID (D11) present → if missing, 400 MISSING_ACTOR
   b. Validate bank_name not empty → if empty, 422 validation error
   c. Validate account_number format (max 30 chars) → if invalid, 422
   d. Check uniqueness: (company_id, account_number) not exists → if exists, 409 DUPLICATE_ACCOUNT_NUMBER
   e. Check primary constraint: if is_primary=TRUE, check no other primary for this company → if exists, 409 PRIMARY_ALREADY_EXISTS
   f. Create BankAccount entity with all validated fields
   g. Save to DB via SQLAlchemyRepository (add + flush)
   h. Append SHA-256 checksum: SHA-256(prev_checksum + actor_uuid + now_iso + "CREATE" + reason + entity_id)
   i. Log audit event via audit_log_service.append_event()
   j. Return 201 + serialized bank account JSON

ALTERNATIVE FLOW (validation failure):
- At any step (a–e) fails: return appropriate error response, no DB write, no checksum

POSTCONDITIONS:
- Bank account record created in bank_accounts table
- SHA-256 checksum appended to audit_log table
- Actor UUID logged in audit event
- Success message: "Tài khoản ngân hàng đã được tạo thành công"
```

### UC-01: List Bank Accounts — Full Flow

```
PRECONDITIONS:
- User is authenticated with valid role (ACCOUNTANT or higher)
- Company context available

MAIN SUCCESS FLOW:
1. User navigates to Bank Accounts listing page
2. System queries: SELECT * FROM bank_accounts WHERE company_id = :company_id
3. Optionally filter by: status (ACTIVE/SUSPENDED/CLOSED), is_primary (true/false)
4. Apply pagination: LIMIT 20 OFFSET (:page-1)*20
5. Optionally sort by: created_at DESC, bank_name ASC
6. Return paginated list with:
   - Total count of records
   - Current page data (bank_name, account_number, is_primary, status, created_at)
   - Navigation controls (prev/next page)
7. Display in UI table with action buttons (edit, detail, reconcile)

FILTER PARAMETERS (via GET /api/v1/bank-accounts):
- status: "ACTIVE" | "SUSPENDED" | "CLOSED" (optional)
- is_primary: true|false (optional)
- company_id: UUID (optional, for multi-company views)
- search: free text search on bank_name or account_number (optional)
- page: integer (default 1)
- limit: integer (default 20, max 200)

POSTCONDITIONS:
- Bank account list displayed in UI
- Pagination controls functional
- Filter applied correctly
- No sensitive data exposed beyond user's role permissions
```

### UC-08: Set Bank Account as Primary (SOD Workflow)

```
PRECONDITIONS:
- Chief Accountant initiates request
- Target bank account exists and is ACTIVE
- 2nd actor (Accountant) must separately approve

MAIN SUCCESS FLOW:
1. CHIEF_ACCOUNTANT logs in, navigates to bank account detail
2. Clicks "Set as Primary"
3. System sends approval request to 2nd actor (ACCOUNTANT) via:
   - In-system notification
   - Email notification
   - UI badge showing "1 pending approval"
4. ACCOUNTANT logs in (separate session)
5. System shows pending approval: "Set [Bank Account] as Primary"
6. ACCOUNTANT reviews: verifies this is the intended change
7. ACCOUNTANT clicks "Approve" or "Reject"
8. If APPROVED:
   a. Bank account status: is_primary = TRUE
   b. Checksum 1: SHA-256(prev + chief_actor + now + "PRIMARY_REQUEST" + reason + bank_id)
   c. Checksum 2: SHA-256(prev + accountant_actor + now + "PRIMARY_APPROVE" + reason + bank_id)
   d. Both checksums appended to audit_log
   e. UI shows: "Tài khoản chính đã được cập nhật thành công"
   f. Notification sent to Chief Accountant: "Đã được phê chuẩn"
9. If REJECTED:
   a. UI shows: "Đề xuất bị từ chối"
   b. Bank account remains in previous state (is_primary = previous value)
   c. Checksum appended for rejection event
   d. Notification sent: "Đề xuất đã bị từ chối"

SOD ENFORCEMENT:
- Both actor UUIDs MUST be different (CHIEF_ACCOUNTANT ≠ ACCOUNTANT)
- If same actor tries both roles: 403 SOD_VIOLATION
- Minimum 5-minute cooling period between 1st and 2nd approval (optional)
- All events logged with full audit trail

POSTCONDITIONS:
- Bank account is_primary updated to TRUE
- Two audit events logged (request + approval)
- Both actors' UUIDs in audit chain
- SOD violation prevented (different actors required)
```

### UC-14: Bank Statement Import (CAMT) — Full Flow

```
PRECONDITIONS:
- User logged in as CHIEF_ACCOUNTANT or ADMIN
- CAMT.053 or CAMT.054 XML file prepared
- Company context available

MAIN SUCCESS FLOW:
1. User navigates to "Import Bank Statements" page
2. User uploads CAMT XML file (max 10MB, configurable)
3. System performs:
   a. Parse XML: extract all bank transactions (date, amount, description, balance)
   b. For each transaction row:
      - Validate: amount ≠ 0, date valid, description not empty
      - Map to internal: create CashAccount transaction OR BankReconciliation line
      - Check: account exists, company_id matches, currency valid
   c. If ALL rows valid:
      - Begin DB transaction
      - Save all transactions atomically
      - Commit DB transaction
      - Append SHA-256 checksum for each transaction event
      - Log audit events for all imported rows
      - Return success: "Đã nhập thành công N giao dịch từ file CAMT"
   d. If ANY row invalid:
      - Rollback entire DB transaction (no partial save)
      - Return error: "Nhập thất bại: dòng thứ N có lỗi - lý do"
      - No checksums appended for failed rows (atomic all-or-nothing)
      - UI shows which rows failed with error details

ALTERNATIVE FLOW (file format error):
- If XML is malformed or not valid CAMT: 400 INVALID_FILE_FORMAT
- Error message: "Định dạng file không hợp lệ, phải là CAMT.053 hoặc CAMT.054"

ALTERNATIVE FLOW (company mismatch):
- If any transaction belongs to different company: 409 COMPANY_MISMATCH
- Error: "Giao dịch thuộc công ty khác, import không thể thực hiện"

SIZE LIMITS (configurable in system settings):
- Max file size: 10MB (default)
- Max transactions per file: 1000 (default)
- Max total imports per day: configurable (prevents abuse)

POSTCONDITIONS:
- All valid transactions saved to DB (cash transactions or reconciliation lines)
- No partial data saved (atomic all-or-nothing)
- SHA-256 checksums appended for each successful transaction event
- Audit log entries for all import activity
- Success/error message displayed to user
```

---