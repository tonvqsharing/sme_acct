# User Journeys — Payment Terms & Document Numbering Module

## 1. Overview

This document captures User Journeys (UJ) for the Payment Terms & Document Numbering module. Each user journey describes a complete end-to-end scenario from the perspective of a specific user role, using the application's UI (HTMX + Bulma frontend) and API endpoints. Journeys include all steps from login to task completion, including SOD approvals, error handling, and audit trail verification.

---

## 2. User Journey Definitions

### UJ-001: Accountant Creates Payment Terms

**Primary Role:** ACCOUNTANT  
**Preconditions:** User authenticated as ACCOUNTANT; company exists in DB  
**Goal:** Create a new payment term for the company  

| Step | Action | UI/API | Expected Result |
|------|--------|--------|-----------------|
| 1 | User logs into system | `POST /login` (existing auth) | Session established; redirected to dashboard |
| 2 | User navigates to "Payment Terms" menu | HTMX `GET /api/v1/payment-terms?company_id={company_id}` | List of existing payment terms displayed (may be empty) |
| 3 | User clicks "Create New Payment Term" button | Modal/form appears: company_id auto-filled, fields: name, due_days, interest_rate | Form ready for input |
| 4 | User fills form: name="Net 30", due_days=30, interest_rate=0.00 | Form fields populated | Values saved in form state |
| 5 | User adds reason: "Setup payment terms for Q4 2026" | Reason field filled | Reason stored in form state |
| 6 | User clicks "Create" button | `POST /api/v1/payment-terms` with body: `{company_id, name, due_days, interest_rate, actor: uuid, reason}` | **Success**: HTTP 201 + JSON payment term<br>**Or Error**: 400 (missing actor/reason), 409 (duplicate name), 422 (invalid due_days) |
| 7 | On success: payment term appears in list | List refreshes automatically | New term "Net 30" visible in company's payment terms |
| 8 | Audit log verified: CREATE event with checksum | Check `audit_log` table | SHA-256 checksum appended; actor_uuid=uuid; reason="Setup payment terms for Q4 2026" |

**Postconditions:** Company now has payment term "Net 30" (due 30 days); audit trail created; user can now select this term when creating invoices.

---

### UJ-002: Chief Accountant Sets Default Payment Term (SOD)

**Primary Role:** CHIEF_ACCOUNTANT (requests) + ACCOUNTANT (approves)  
**Preconditions:** User authenticated as CHIEF_ACCOUNTANT; company has no current default payment term; at least one payment term exists  
**Goal:** Set a payment term as the default for the company (requires 2-actor SOD)  

| Step | Action | UI/API | Expected Result |
|------|--------|--------|-----------------|
| 1 | User logs into system as CHIEF_ACCOUNTANT | `POST /login` (role=CHIEF_ACCOUNTANT) | Session established with CHIEF_ACCOUNTANT role |
| 2 | User navigates to "Payment Terms" menu | `GET /api/v1/payment-terms?company_id={company_id}` | List of company's payment terms displayed |
| 3 | User selects a payment term to set as default | Click "Set as Default" button on term row | Modal/confirmation appears |
| 4 | User confirms: set term "Net 30" as default; reason="Make Net 30 default for Q4" | Form: reason field filled | Confirmation sent to system |
| 5 | System validates: term ACTIVE, no current default, actor+reason present | Service layer validation | If valid → Queue pending ACCOUNTANT approval; if invalid → 409/400 error |
| 6 | Checksum 1 appended to audit_log: SHA-256(0*64 + chief_uuid + now + "DR" + reason + term_id) | Background: audit_log INSERT | Event: "DEFAULT_REQUEST" with checksum |
| 7 | System notifies ACCOUNTANT: pending approval for "Set Default" | In-app notification / dashboard badge | ACCOUNTANT sees pending approval count = 1 |
| 8 | ACCOUNTANT logs in (or stays logged) | ACCOUNTANT session | ACCOUNTANT can see pending approvals |
| 9 | ACCOUNTANT navigates to "Pending Approvals" | `GET /api/v1/approvals/pending` | Sees: "Set Default payment term - Net 30" by Chief Accountant |
| 10 | ACCOUNTANT reviews and clicks "Approve" | `POST /api/v1/approvals/{id}/approve` with actor=accountant-uuid, reason="Approved" | **If APPROVE**:<br>• Checksum 2: SHA-256(prev + accountant_uuid + now + "DA" + reason + term_id)<br>• PaymentTerm.is_default = TRUE<br>• Other terms: is_default = FALSE<br>• HTTP 200 + "Default set success"<br>• Both checksums in audit_log<br><br>**If REJECT**:<br>• Checksum 2: SHA-256(prev + accountant_uuid + now + "DR" + reason + term_id)<br>• No state changes<br>• HTTP 409 + "Rejected, default unchanged"<br>• Checksum in audit_log for rejection |
| 11 | On approval: default term now applied company-wide | Invoice creation auto-uses this term | All new invoices default to "Net 30" due date calculation |
| 12 | User verifies: term now shows is_default=TRUE | UI displays is_default indicator | Visual confirmation in payment terms list |

**Postconditions:** Payment term "Net 30" is now the default for the company; SOD audit chain complete (2 checksums in audit_log for 10-year retention); all new invoices use this default; previous default (if any) now is_default=FALSE.

---

### UJ-003: Accountant Creates Document Numbering Series

**Primary Role:** ACCOUNTANT  
**Preconditions:** User authenticated as ACCOUNTANT; company exists  
**Goal:** Create a new document numbering series (e.g., for invoices)  

| Step | Action | UI/API | Expected Result |
|------|--------|--------|-----------------|
| 1 | User logs into system | `POST /login` (role=ACCOUNTANT) | Session established |
| 2 | User navigates to "Document Numbering" menu | `GET /api/v1/document-numbering?company_id={company_id}` | List of existing series displayed (may be empty) |
| 3 | User clicks "Create New Series" button | Modal/form appears: fields: prefix, name, max_sequences (default 999999) | Form ready for input |
| 4 | User fills form: prefix="HD/", name="Hóa đơn", max_sequences=999999 | Form fields populated | Values saved in form state |
| 5 | User adds reason: "Setup invoice series for 2026" | Reason field filled | Reason stored in form state |
| 6 | User validates prefix format (implicit: must be ^[A-Z]{2,}/$) | Prefix input validated as typing | If invalid format → inline error: "Prefix must follow GDT format: HD/" |
| 7 | User clicks "Create" button | `POST /api/v1/document-numbering` with body: `{company_id, prefix, name, max_sequences, actor, reason}` | **Success**: HTTP 201 + JSON series<br>**Or Error**: 400 (missing actor/reason), 409 (prefix exists), 409 (max 15 series), 422 (invalid prefix) |
| 8 | On success: new series appears in list | List refreshes automatically | New series "HD/" visible with next_sequence=1, is_active=TRUE |
| 9 | Audit log verified: CREATE event with checksum | Check `audit_log` table | SHA-256 checksum appended; actor_uuid; reason="Setup invoice series for 2026" |

**Postconditions:** Company now has document numbering series "HD/" starting at sequence 1; user can create invoices with document numbers "HD/000001", "HD/000002", etc.; audit trail created.

---

### UJ-004: Accountant Creates Invoice with Auto-Numbering

**Primary Role:** ACCOUNTANT  
**Preconditions:** User authenticated as ACCOUNTANT; company has active document numbering series; payment terms optionally set  
**Goal:** Create a new invoice with auto-generated document number  

| Step | Action | UI/API | Expected Result |
|------|--------|--------|-----------------|
| 1 | User logs into system | `POST /login` (role=ACCOUNTANT) | Session established |
| 2 | User navigates to "Invoices" menu | `GET /api/v1/invoices` (existing) | Invoice list displayed (empty or previous invoices) |
| 3 | User clicks "Create New Invoice" button | Modal/form appears: fields: customer, amount, vat_rate, issue_date, payment_term_id (optional) | Form ready; payment terms listed if exist |
| 4 | User fills invoice details: customer="Công ty A", amount=1000000, vat_rate=0.1, issue_date=2026-08-20 | Form fields populated | Invoice data saved in form state |
| 5 | If payment terms exist: User optionally selects "Net 30" from dropdown | payment_term_id dropdown populated | If selected: due_date auto-calculated = 2026-08-30 |
| 6 | User clicks "Create Invoice" button | System auto-triggers: <br>• `POST /api/v1/document-numbering/{series_id}/increment` <br>• `POST /api/v1/invoices` (with document_number, due_date) | **Auto-increment flow**:<br>1. System gets company's active series (e.g., "HD/")<br>2. Increments next_sequence: 1→2 (or 1→1 if first ever)<br>3. Generates document number: "HD/000002"<br>4. Creates invoice with: document_number="HD/000002", due_date=2026-08-30 (if Net 30 set)<br>5. HTTP 201 + invoice details with document_number |
| 7 | On success: invoice created with document number | Invoice appears in list with document_number column | Invoice visible: "HD/000002" as document_number, customer="Công ty A", total=1100000 |
| 8 | Audit log verified: INCREMENT + Invoice CREATE events | Check `audit_log` table | Two events: <br>• INCREMENT: checksum for series increment <br>• CREATE: invoice details with actor, reason |
| 9 | User verifies: next invoice will use sequence 3 | Create another invoice | document_number="HD/000003" (auto-incremented) |

**Postconditions:** New invoice created with auto-generated document number; series sequence incremented; due date calculated from payment term if set; audit trail with 2 events; company numbering continues sequentially.

---

### UJ-005: Chief Accountant Activates Inactive Series (SOD)

**Primary Role:** CHIEF_ACCOUNTANT (requests) + ACCOUNTANT (approves)  
**Preconditions:** User authenticated as CHIEF_ACCOUNTANT; company has inactive series; company has < 15 active series  
**Goal:** Activate an inactive document numbering series (requires 2-actor SOD)  

| Step | Action | UI/API | Expected Result |
|------|--------|--------|-----------------|
| 1 | User logs into system as CHIEF_ACCOUNTANT | `POST /login` (role=CHIEF_ACCOUNTANT) | Session established |
| 2 | User navigates to "Document Numbering" menu | `GET /api/v1/document-numbering?company_id={company_id}` | List displayed; inactive series marked (e.g., grayed out or "Inactive" label) |
| 3 | User selects inactive series to activate | Click "Activate" button on inactive series row | Confirmation modal appears |
| 4 | User confirms: activate series "PN/"; reason="Reactivate receipt series for Q3" | Reason field filled | Confirmation sent |
| 5 | System validates: series exists, is INACTIVE, company < 15 active, actor+reason present | Service layer validation | If valid → Queue pending ACCOUNTANT approval; if invalid → 409/400 error |
| 6 | Checksum 1 appended to audit_log: SHA-256(0*64 + chief_uuid + now + "ASR" + reason + series_id) | Background: audit_log INSERT | Event: "ACTIVATE_REQUEST" with checksum |
| 7 | System notifies ACCOUNTANT: pending approval for "Activate Series" | In-app notification | ACCOUNTANT sees pending approval count = 1 |
| 8 | ACCOUNTANT logs in / sees pending approvals | ACCOUNTANT session + `GET /api/v1/approvals/pending` | Sees: "Activate series PN/ by Chief Accountant" |
| 9 | ACCOUNTANT reviews and clicks "Approve" | `POST /api/v1/approvals/{id}/approve` with actor=accountant-uuid, reason="Approved" | **If APPROVE**:<br>• Checksum 2: SHA-256(prev + accountant_uuid + now + "AA" + reason + series_id)<br>• Series.is_active = TRUE<br>• SQLAlchemyRepository.update() persists<br>• HTTP 200 + "Series activated success"<br>• Both checksums in audit_log<br><br>**If REJECT**:<br>• Checksum 2: SHA-256(prev + accountant_uuid + now + "AR" + reason + series_id)<br>• No state changes<br>• HTTP 409 + "Reactivated denied"<br>• Checksum in audit_log for rejection |
| 10 | On approval: series now ACTIVE and available for increment | Series appears in active list | Series "PN/" now shown as active; can be used for new receipt numbering |
| 11 | User verifies: can now increment sequence on series | Try creating new receipt | Sequence increments; document number generated with "PN/" prefix |

**Postconditions:** Inactive series "PN/" now ACTIVE; SOD audit chain complete (2 checksums); company now has one more active series (must still ≤ 15); series available for new document numbering.

---

### UJ-006: Accountant Deactivates Payment Term

**Primary Role:** ACCOUNTANT  
**Preconditions:** User authenticated as ACCOUNTANT; payment term exists and is ACTIVE  
**Goal:** Soft-deactivate (retention) a payment term  

| Step | Action | UI/API | Expected Result |
|------|--------|--------|-----------------|
| 1 | User logs into system | `POST /login` (role=ACCOUNTANT) | Session established |
| 2 | User navigates to "Payment Terms" menu | `GET /api/v1/payment-terms?company_id={company_id}` | List displayed; term to deactivate shown |
| 3 | User selects term to deactivate | Click "Deactivate" button on term row | Confirmation modal appears with warnings |
| 4 | Warning displayed: "Cannot deactivate default term"; "Cannot deactivate term with associated invoices" | Validation warnings shown | User reads warnings |
| 5 | User confirms deactivation; reason="Term no longer used, replacing with Net 60" | Reason field filled | Confirmation sent |
| 6 | System validates: term exists, is ACTIVE, NOT default, NO associated active invoices | Service layer validation | If any fail → appropriate error: 409 CANNOT_DEACTIVATE_DEFAULT, 409 HAS_ASSOCIATED_INVOICES, 409 ALREADY_INACTIVE |
| 7 | If valid → Proceed with deactivation | `PATCH /api/v1/payment-terms/{id}` with: `{status: "inactive", actor, reason}` | Service sets PaymentTerm.status = INACTIVE (soft delete) |
| 8 | SQLAlchemyRepository.update() persists status change | DB: payment_terms table, status=INACTIVE | Row preserved; is_default may be affected if this was the default |
| 9 | AuditLogService.append_event(): DEACTIVATE event with SHA-256 checksum | audit_log table INSERT | Event: "DEACTIVATE" with: actor_uuid, reason, old_status="ACTIVE", new_status="INACTIVE", has_associated_invoices="FALSE" |
| 10 | HTTP 200 + "Payment term deactivated" returned | API response | User sees success message |
| 11 | User verifies: term now marked INACTIVE in list | UI shows is_default=False, status indicator | Term appears inactive/ grayed out in list |
| 12 | Audit verification: term preserved in DB for 10-year retention | Check DB directly | Row still exists with status=INACTIVE; no automatic deletion |

**Postconditions:** Payment term soft-deactivated; row preserved in DB for 10-year retention per Luật Kế toán 2015; term no longer selectable for new invoices; audit trail created; user must create new term or reassign invoices if needed.

---

### UJ-007: Accountant Lists Payment Terms and Series

**Primary Role:** AUDITOR (read-only) or ACCOUNTANT  
**Preconditions:** User authenticated with READ role (AUDITOR or ACCOUNTANT)  
**Goal:** View all payment terms and document numbering series for company (audit/overview purposes)  

| Step | Action | UI/API | Expected Result |
|------|--------|--------|-----------------|
| 1 | User logs into system | `POST /login` (role=AUDITOR or ACCOUNTANT) | Session established with appropriate role |
| 2 | User navigates to "Payment Terms" menu | `GET /api/v1/payment-terms?company_id={company_id}` | List of all payment terms for company displayed |
| 3 | User observes: terms with is_default highlighted; INACTIVE terms grayed out | UI displays is_default indicator, status badges | User can see which term is default, which are active/inactive |
| 4 | User navigates to "Document Numbering" menu | `GET /api/v1/document-numbering?company_id={company_id}` | List of all series for company displayed |
| 5 | User observes: active series count vs. GDT limit (max 15) | Series list shows is_active=True/False; count shown if configured | User can see how many active series vs. GDT limit |
| 6 | User verifies data isolation: only own company's terms/series visible | company_id filter applied | No cross-company data visible (enforced by FK + CASRBAC) |
| 7 | User can export/list for audit purposes | Optional: CSV/JSON export feature | Data exported if needed for audit/retention reporting |
| 8 | Audit log check: QUERY events (if configured) | Check audit_log for QUERY-type events | Optional: audit trail of who viewed/listed data |

**Postconditions:** User has complete view of company's payment term and numbering series configuration; data properly isolated by company_id; audit trail may include query events; compliant with 10-year retention (data preserved, no deletion).

---

## 3. Journey Summary Table

| UJ-ID | Title | Primary Role | SOD Required | Key API Calls | Audit Events |
|-------|-------|-------------|--------------|---------------|--------------|
| UJ-001 | Create Payment Term | ACCOUNTANT | NO | POST /payment-terms | CREATE (1 checksum) |
| UJ-002 | Set Default Payment Term | CHIEF_ACCOUNTANT + ACCOUNTANT | YES (2-actor) | POST /set-default, GET /approvals/pending | 2 CHECKSUMS (request + approve/reject) |
| UJ-003 | Create Document Series | ACCOUNTANT | NO | POST /series | CREATE (1 checksum) |
| UJ-004 | Create Invoice with Numbering | ACCOUNTANT | NO | POST /increment + POST /invoices | INCREMENT + CREATE (2 checksums) |
| UJ-005 | Activate Inactive Series | CHIEF_ACCOUNTANT + ACCOUNTANT | YES (2-actor) | POST /activate, GET /approvals/pending | 2 CHECKSUMS (request + approve/reject) |
| UJ-006 | Deactivate Payment Term | ACCOUNTANT | NO | PATCH /{id} with status=inactive | DEACTIVATE (1 checksum) |
| UJ-007 | List/View Terms & Series | AUDITOR/ACCOUNTANT | NO | GET /payment-terms, GET /series | QUERY (optional) |

✓ = Can perform, SOD = Separation of Duties (2-actor approval required)

---

## 4. Cross-Journey Dependencies

| Journey | Depends On | Description |
|---------|-----------|-------------|
| UJ-001 → UJ-004 | Payment terms exist | Invoice creation auto-calculates due_date from payment_term_id |
| UJ-003 → UJ-004 | Series exist | Invoice creation auto-generates document_number from series |
| UJ-002 → UJ-001 | At least 1 payment term | Cannot set default if no terms exist; user must create first |
| UJ-005 → UJ-003 | At least 1 inactive series | Cannot activate if no inactive series exist; user must create first |
| UJ-006 → UJ-001 | Term not default | Cannot deactivate default; must set new default first (UJ-002) |
| UJ-007 → UJ-001, UJ-003 | Data exists | Lists depend on existing terms/series in company |

---

## 5. Error Handling in User Journeys

| Journey | Error Scenario | HTTP Status | User-Visible Message | Recovery |
|---------|---------------|-------------|---------------------|----------|
| UJ-001 | Duplicate payment term name | 409 | "Tên đã tồn tại cho doanh nghiệp này" | User must use different name |
| UJ-001 | due_days < 1 | 422 | "Số ngày phải lớn hơn 0" | User enters valid due_days >= 1 |
| UJ-001 | Missing actor UUID | 400 | "actor là bắt buộc" | User/login issue; re-authenticate |
| UJ-001 | Missing reason | 400 | "Lý do là bắt buộc" | User fills reason field |
| UJ-002 | Company already has default | 409 | "Doanh nghiệp đã có payment term default" | Must unset existing default first (set another term, or remove default) |
| UJ-002 | ACCOUNTANT rejects approval | 409 | "Được denied, default unchanged" | User can re-request approval or accept rejection |
| UJ-003 | Prefix doesn't match GDT format | 422 | "Định dạng prefix không hợp lệ theo GDT" (e.g., must be "HD/") | User corrects prefix format |
| UJ-003 | Prefix already exists for company | 409 | "Prefix đã tồn tại cho doanh nghiệp này" | User uses different prefix or deactivates existing |
| UJ-003 | Company at 15 active series limit | 409 | "Đã đạt giới hạn 15 series active" | Must deactivate existing series first (UJ-006) |
| UJ-004 | Series inactive when creating invoice | 409 | "Series không phải ACTIVE, kích hoạt series trước" | Activate series first (UJ-005) or create new series |
| UJ-004 | next_sequence at max (999999) | 409 | "Số tiếp theo đã đạt giới hạn 999999" | Deactivate series, create new series with fresh sequence |
| UJ-005 | Company already at 15 active series | 409 | "Đã đạt giới hạn 15 series active cho doanh nghiệp này" | Deactivate existing series first, then activate |
| UJ-005 | ACCOUNTANT rejects approval | 409 | "Kích hoạt series bị denied" | User can re-request approval |
| UJ-006 | Term is default | 409 | "Không thể vô hiệu hóa payment term mặc định" | Must set new default first (UJ-002) |
| UJ-006 | Term has associated invoices | 409 | "Term có tài liệu liên quan, phải giao dịch lại invoices" | Reassign invoices to other term, then deactivate |
| UJ-006 | Term already INACTIVE | 409 | "Term đã bị vô hiệu hóa" | No action needed or reactivate first |
| UJ-007 | Cross-company data access attempt | 403 | "Không có quyền truy cập doanh nghiệp này" | User must use own company context |

---