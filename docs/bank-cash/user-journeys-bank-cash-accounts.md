# User Journeys — Bank & Cash Accounts Module

## 1. Overview

User Journeys describe the end-to-end experience of each user role interacting with the Bank & Cash Accounts module. Each journey maps the complete sequence of steps from login to task completion, including all UI interactions, validations, and system responses.

Follows the format of user-journeys-*.md in this codebase (e.g., user-journeys-currencies.md, user-journeys-fiscal-year-period.md).

---

## 2. Actor Personas

| Actor | Role | Typical Profile | Access Level |
|-------|------|-----------------|--------------|
| **Accountant** | ACCOUNTANT | Daily accounting operations, data entry, voucher posting | Read + Write (own company) |
| **Chief Accountant** | CHIEF_ACCOUNTANT | Financial closing, SOD approvals, system configuration | Read + Write + SOD authority |
| **Auditor** | AUDITOR | Internal audit, retention verification, compliance checks | Read-only |
| **Administrator** | ADMIN | System configuration, user management, SOD policy | Full access (company-level) |
| **Director** | DIRECTOR | Executive oversight, emergency overrides, company summary | Read + limited write (emergency) |

---

## 3. User Journeys

### 3.1 J-01: Accountant — Daily Cash Transaction Recording

**Goal:** Record a cash (tiêu hối) transaction for the day  
**Preconditions:** User is logged in as ACCOUNTANT, has access to company, cash account exists and is ACTIVE

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | User logs into the SME Accounting App | Dashboard displayed with company selector |
| 2 | User navigates to **Cash Accounts** menu → selects target cash account | Cash account detail page displayed: code, name, current_balance, opening_balance |
| 3 | User clicks **"Record Transaction"** button | Transaction modal/form appears: amount, reason, date (default: today) |
| 4 | User enters: amount = -500,000 (withdrawal), reason = "Mua vật tư làm việc" | Amount field shows -500,000, reason field shows "Mua vật tư làm việc" |
| 5 | User clicks **"Confirm Transaction"** | System validates: <br>• Actor UUID (D11) present in session ✓<br>• Cash account status = ACTIVE ✓<br>• Not a system account ✓<br>• New balance = current + amount =  current - 500,000 ≥ 0 ✓ |
| 6 | System updates: current_balance ← current_balance + (-500,000) | Balance updated in DB<br>• New balance displayed: e.g., "Số dư hiện tại: 3,500,000 VND" |
| 7 | SHA-256 checksum appended to audit log | Event logged: actor=UUID, action="TRANSACTION", reason="Mua vật tư làm việc", new_balance, timestamp |
| 8 | Success modal: "Giao dịch ghi nhận thành công. Số dư mới: 3.500.000 VND" | User clicks "OK", returns to cash account detail page |
| 9 | Audit event visible in logs (AUDITOR role only) | Full chain: actor, reason, old_balance, new_balance, checksum |

**Happy Path Outcome:** Cash transaction recorded, balance updated, audit trail complete.

**Exception Outcomes:**
- If amount would make balance negative: Error "Số dư không đủ giao dịch" (422 INSUFFICIENT_BALANCE)
- If cash account is CLOSED: Error "Tài khoản đã đóng" (409 ACCOUNT_CLOSED)
- If cash account is system: Error "Tài khoản hệ thống" (403 SYSTEM_ACCOUNT_ERROR)
- If actor UUID missing: Error "actor là bắt buộc" (400 MISSING_ACTOR)

---

### 3.2 J-02: Chief Accountant — Set Bank Account as Primary (SOD Workflow)

**Goal:** Change the primary bank account for the company (requires 2-actor SOD)  
**Preconditions:** User is logged in as CHIEF_ACCOUNTANT, company has existing bank accounts, target account is ACTIVE

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | CHIEF_ACCOUNTANT logs in, navigates to **Bank Accounts** menu | Bank account list displayed for company |
| 2 | CHIEF_ACCOUNTANT selects target bank account and clicks **"Set as Primary"** | Primary change request form/screen appears |
| 3 | System sends approval request to 2nd actor (ACCOUNTANT) via: <br>• In-system notification: "1 pending approval: Set as Primary"<br>• Email notification (if configured) | Pending approval badge displayed on nav bar: "1 approval pending" |
| 4 | ACCOUNTANT (2nd actor) logs in (separate session) | Dashboard shows notification: "Có 1 yêu cầu chờ phê chuẩn: Thiết làm tài khoản chính" |
| 5 | ACCOUNTANT clicks the notification → sees: "Set [Bank Account Name] as Primary" | Details shown: current primary account, target account info, reason field |
| 6 | ACCOUNTANT verifies the change is correct, enters reason if needed, clicks **"Approve"** | System performs: <br>• Validate: 2nd actor ≠ 1st actor (SOD check) ✓<br>• Update: bank_account.is_primary = TRUE<br>• Checksum 1: SHA-256(prev + chief_actor + now + "PRIMARY_REQUEST" + reason + bank_id)<br>• Checksum 2: SHA-256(prev + accountant_actor + now + "PRIMARY_APPROVE" + reason + bank_id)<br>• Both checksums appended to audit_log<br>• Bank account updated in DB<br>• Success notification: "Tài khoản chính đã được phê chuẩn" |
| 7 | If ACCOUNTANT clicks **"Reject"** instead: | status remains unchanged (is_primary = previous value)<br>• Checksum 2 appended for "PRIMARY_REJECT"<br>• Notification: "Yêu cầu đã bị từ chối"<br>• Chief Accountant notified: "Đề xuất bị từ chối" |

**Happy Path Outcome:** Primary bank account changed, both actors logged in audit chain, SOD compliance verified.

**Exception Outcomes:**
- If both actors are the same user: Error "SOD violation: cùng một diễn viên không thể là 1st và 2nd actor" (403 SOD_VIOLATION)
- If CHIEF_ACCOUNTANT closes the modal without approval: request expires, no changes
- If ACCOUNTANT approves but chief accountant had already changed primary elsewhere: DB constraint prevents, 409 PRIMARY_ALREADY_EXISTS

---

### 3.3 J-03: Auditor — Verify Audit Trail & Retention Status

**Goal:** Verify the integrity of the audit trail and check retention readiness  
**Preconditions:** User is logged in as AUDITOR, has VIEW_AUDIT_LOG permission

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | AUDITOR logs in, navigates to **Audit Log** menu | Audit log dashboard displayed with filters |
| 2 | AUDITOR sets filter: Entity Type = "bank_account", Date Range = "last 30 days" | List of bank account audit events for past 30 days displayed |
| 3 | AUDITOR verifies checksum chain integrity | System displays: <br>• Event list with: actor UUID, action, reason, timestamp<br>• Checksum value for each event<br>• "Chain valid: YES" if all checksums link correctly<br>• "Chain valid: NO" with broken event numbers if broken |
| 4 | AUDITOR clicks **"Check Retention Status"** | System queries: <br>• Count of bank_account events older than 10 years<br>• Count of complete checksum chains<br>• Count of events with gaps/missing predecessors<br>• Result: "Ready for destruction: 127 events" or "Issues found: 3 broken checksums, 5 gaps" |
| 5 | AUDITOR reviews issues (if any) | Details shown: which events have broken chains, recommended action |
| 6 | AUDITOR generates destruction request (if ready) | Calls: POST /api/audit-log/destroy with retention criteria<br>• Destruction event logged<br>• Entities marked as destroyed (soft delete, row preserved)<br>• Certificate of Destruction generated (PDF) |

**Happy Path Outcome:** Audit trail verified, retention status checked, any issues identified and resolved, destruction process initiated if ready.

**Exception Outcomes:**
- If checksum chain broken: Error details shown, must repair chain before destruction
- If entities past 10-year retention but still in use: Warning displayed, cannot destroy until SOD check passed
- If AUDITOR tries to modify audit log entries: Blocked (read-only), 403 AUDITOR_READ_ONLY

---

### 3.4 J-04: Administrator — Configure SOD Thresholds & System Settings

**Goal:** Configure Separation of Duties thresholds and system-wide bank/cash settings  
**Preconditions:** User is logged in as ADMIN, has ADMIN role for company

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | ADMIN logs in, navigates to **System Settings** → **Bank & Cash Configuration** | Configuration form displayed with current SOD settings |
| 2 | ADMIN modifies: <br>• SOD threshold amount (e.g., transactions > 10,000,000 VND require 2-actor approval)<br>• Retention period (default 10 years, per law)<br>• Approval workflow actors per role | Settings saved to company_config table, checksum appended to audit_log |
| 3 | ADMIN clicks **"Save Configuration"** | System validates: <br>• SOD threshold ≥ 0<br>• Retention period ≥ 1 year (per Luật Kế toán 2015)<br>• At least 2 role groups defined for SOD<br>• If valid: Settings saved, success message: "Cấu hình đã được cập nhật" |
| 4 | If invalid: Error messages displayed for each field | e.g., "Ngưỡng SOD phải lớn hơn 0", " Kỳ 유지 tối thiểu 1 năm" |
| 4 | ADMIN views audit log for configuration changes | Shows: which admin made changes, when, reason, checksum of the config event |

**Happy Path Outcome:** System settings updated, full audit trail, SOD policy enforced going forward.

**Exception Outcomes:**
- If ADMIN saves with SOD threshold = 0: Error shown, must set positive value
- If retention period < 1 year: Error shown, must comply with Law on Accounting Art. 11
- If ADMIN changes SOD rules without 2-actor approval (if configured): Blocked, 403

---

### 3.5 J-05: Director — Emergency Bank Account Override

**Goal:** Emergency override of bank account restrictions (e.g., urgent cash need)  
**Preconditions:** User is logged in as DIRECTOR, requires Chief Accountant co-signature

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | DIRECTOR logs in, navigates to **Bank Accounts** → selects target account | Bank account detail page displayed |
| 2 | DIRECTOR clicks **"Emergency Override"** button | Override request form appears: reason, estimated amount, duration |
| 3 | DIRECTOR enters: reason = "Cấp phép lương cấp bách", amount = 50,000,000 VND | Form validated: reason ≠ empty, amount > 0 |
| 4 | System requests Chief Accountant co-signature | • Notification sent to CHIEF_ACCOUNTANT: "Giám đốc yêu cầu khẩn cấp: Override tài khoản ngân hàng"<br>• DIRECTOR sees: "Chờ phê chuẩn của Kế toán trưởng" |
| 5 | CHIEF_ACCOUNTANT logs in (separate session) | Sees pending override request in dashboard |
| 6 | CHIEF_ACCOUNTANT reviews the emergency request | • Reviews reason, amount, duration<br>• Verifies this is truly emergency<br>• Clicks **"Approve"** or **"Reject"** |
| 7 | If APPROVED: <br>• System applies override with status: "EMERGENCY_OVERRIDE"<br>• Both UUIDs (DIRECTOR + CHIEF_ACCOUNTANT) logged in audit chain<br>• Checksum: SHA-256(prev + director_actor + now + "EMERGENCY_APPROVE" + reason + override_id)<br>• UI shows: "Override khẩn cấp đã được phê chuẩn<br>• Notification to DIRECTOR: "Override đã phê chuẩn" |
| 8 | If REJECTED: <br>• Override request cancelled<br>• Audit event logged for rejection<br>• UI shows: "Yêu cầu override bị từ chối"<br>• Notification to DIRECTOR: "Override bị từ chối" |

**Happy Path Outcome:** Emergency override applied, full audit trail with both actors, business need met.

**Exception Outcomes:**
- If CHIEF_ACCOUNTANT rejects: No override applied, business process continues normally
- If DIRECTOR and CHIEF_ACCOUNTANT are the same user (impossible in practice): Blocked by SOD check
- If override amount exceeds company's SOD threshold: Additional approval required from ADMIN level

---