# Use Cases — Payment Terms & Document Numbering Module

## 1. Overview

This document captures all Use Cases (UC) for the Payment Terms & Document Numbering module, covering happy paths, alternative paths, and exception paths. Each use case follows the format:
- **UC-ID**: Unique identifier
- **Title**: Brief description
- **Actor**: Primary user role
- **Preconditions**: State before use case starts
- **Basic Flow**: Step-by-step execution (happy path)
- **Alternative Flows**: Divergences from basic flow
- **Exception Guarantees**: Error handling outcomes
- **Postconditions**: State after use case completes

---

## 2. Payment Term Use Cases

### UC-001: Create Payment Term

| Field | Value |
|-------|-------|
| **UC-ID** | UC-001 |
| **Title** | Create new payment term |
| **Actor** | ACCOUNTANT, CHIEF_ACCOUNTANT |
| **Preconditions** | User authenticated, has ACCOUNTANT or CHIEF_ACCOUNTANT role; company exists |
| **Basic Flow** | 1. User navigates to payment terms creation page<br>2. User fills form: company_id, name="Net 30", due_days=30, interest_rate=0.00<br>3. User submits form<br>4. API POST /api/v1/payment-terms processes request<br>5. Service layer validates: name unique per company, due_days >= 1<br>6. PaymentTerm entity created with checksum initialized<br>7. SQLAlchemyRepository.create() persists to DB<br>8. AuditLogService.append_event() logs CREATE event with SHA-256 checksum<br>9. HTTP 201 returned with created payment term JSON<br>10. Use case completes |
| **Alternative Flows** | **AP-001**: Name already exists for company → Return 409 DUPLICATE_PAYMENT_TERM<br>**AP-002**: due_days < 1 → Return 422 INVALID_DUE_DAYS<br>**AP-003**: Missing actor UUID → Return 400 MISSING_ACTOR<br>**AP-004**: Missing reason → Return 400 MISSING_REASON |
| **Exception Guarantees** | Name uniqueness enforced per company; due_days validated >= 1; actor UUID required |
| **Postconditions** | Payment term stored in DB with is_default=FALSE; SHA-256 checksum in audit_log; company now has new payment term option |

---

### UC-002: Set Default Payment Term (SOD)

| Field | Value |
|-------|-------|
| **UC-ID** | UC-002 |
| **Title** | Set payment term as default (Separation of Duties) |
| **Actor** | CHIEF_ACCOUNTANT (requests), ACCOUNTANT (approves) |
| **Preconditions** | User authenticated, has CHIEF_ACCOUNTANT role; payment term exists and is ACTIVE; company has no current default |
| **Basic Flow** | 1. CHIEF_ACCOUNTANT submits request to set payment term as default<br>2. System records "DEFAULT_REQUEST" event with Checksum 1: SHA-256(prev + chief_actor_uuid + now + "DEFAULT_REQUEST" + reason + term_id)<br>3. System queues pending approval for ACCOUNTANT<br>4. ACCOUNTANT logs in, sees pending approval in dashboard<br>5. ACCOUNTANT reviews and clicks "Approve"<br>6. System records "DEFAULT_APPROVE" event with Checksum 2: SHA-256(prev + accountant_actor_uuid + now + "DEFAULT_APPROVE" + reason + term_id)<br>7. PaymentTerm.is_default set to TRUE in DB<br>8. All other payment terms for company is_default set to FALSE<br>9. HTTP 200 returned with success message<br>10. Use case completes |
| **Alternative Flows** | **AP-001**: Company already has default payment term → Return 409 DEFAULT_ALREADY_EXISTS, use case ends without change<br>**AP-002**: ACCOUNTANT rejects approval → Return 409 DEFAULT_REJECTED, is_default remains unchanged; Checksum 2 appended for "DEFAULT_REJECT"<br>**AP-003**: CHIEF_ACCOUNTANT sets default when another already default → System blocks at validation, 409 returned |
| **Exception Guarantees** | SOD enforced: 2 actors required; only 1 default per company; both actors logged in audit chain |
| **Postconditions** | Payment term marked as default; dual checksum chain in audit_log (request + approval); all other terms for company now is_default=FALSE |

---

### UC-003: Update Payment Term

| Field | Value |
|-------|-------|
| **UC-ID** | UC-003 |
| **Title** | Update payment term details |
| **Actor** | ACCOUNTANT, CHIEF_ACCOUNTANT |
| **Preconditions** | User authenticated, has ACCOUNTANT or CHIEF_ACCOUNTANT role; payment term exists and is ACTIVE |
| **Basic Flow** | 1. User navigates to payment term update page<br>2. User modifies fields: name, due_days, interest_rate<br>3. User submits form<br>4. API PATCH /api/v1/payment-terms/<id> processes request<br>5. Service layer validates: term exists, ACTIVE status, name unique if changed, due_days >= 1 if changed<br>6. PaymentTerm entity updated with new values<br>7. SQLAlchemyRepository.update() persists changes to DB<br>8. AuditLogService.append_event() logs UPDATE event with SHA-256 checksum (prev + actor + now + "UPDATE" + reason + term_id + new_values_hash)<br>9. HTTP 200 returned with updated payment term JSON<br>10. Use case completes |
| **Alternative Flows** | **AP-001**: Name already exists for different term → Return 409 DUPLICATE_PAYMENT_TERM<br>**AP-002**: due_days < 1 → Return 422 INVALID_DUE_DAYS<br>**AP-003**: Payment term is INACTIVE → Return 409 INACTIVE_TERM, cannot update |
| **Exception Guarantees** | Name uniqueness enforced; due_days validated; only ACTIVE terms can be updated |
| **Postconditions** | Payment term updated in DB; checksum in audit_log reflecting new values; company now has updated payment term configuration |

---

### UC-004: Deactivate Payment Term (Soft Delete)

| Field | Value |
|-------|-------|
| **UC-ID** | UC-004 |
| **Title** | Deactivate payment term (soft delete) |
| **Actor** | ACCOUNTANT, CHIEF_ACCOUNTANT |
| **Preconditions** | User authenticated, has ACCOUNTANT or CHIEF_ACCOUNTANT role; payment term exists |
| **Basic Flow** | 1. User submits deactivation request for payment term<br>2. Service layer validates: term exists, term is ACTIVE<br>3. If term is default → Block or reassign (depends on business rule)<br>4. PaymentTerm.status set to INACTIVE (soft delete)<br>5. SQLAlchemyRepository.update() persists status change<br>6. AuditLogService.append_event() logs DEACTIVATE event with SHA-256 checksum<br>7. HTTP 200 returned with success message<br>8. Use case completes |
| **Alternative Flows** | **AP-001**: Term is default → Return 409 CANNOT_DEACTIVATE_DEFAULT, must unset default first<br>**AP-002**: Term has associated invoices → Return 409 HAS_ASSOCIATED_INVOICES, must reassign or delete invoices first<br>**AP-003**: Term INACTIVE already → Return 409 ALREADY_INACTIVE |
| **Exception Guarantees** | Soft-delete only (row preserved, status=Inactive); 10-year retention enforced; no automatic deletion |
| **Postconditions** | Payment term marked INACTIVE in DB; checksum in audit_log; term no longer selectable for new invoices; audit trail preserved for 10 years |

---

### UC-005: List Payment Terms by Company

| Field | Value |
|-------|-------|
| **UC-ID** | UC-005 |
| **Title** | List payment terms for a company |
| **Actor** | ACCOUNTANT, AUDITOR, DIRECTOR |
| **Preconditions** | User authenticated, has READ role; company exists |
| **Basic Flow** | 1. User requests list of payment terms for company_id<br>2. API GET /api/v1/payment-terms?company_id={id} processes request<br>3. PaymentTermRepository.get_by_company(company_id) queries DB<br>4. Results serialized and returned in JSON array<br>5. HTTP 200 returned with payment terms list<br>6. Use case completes |
| **Alternative Flows** | **AP-001**: Company not found → Return 404 COMPANY_NOT_FOUND<br>**AP-002**: No payment terms exist for company → Return 200 empty array `[]` |
| **Exception Guarantees** | Data scoped by company_id (tenant isolation); AUDITOR can read only |
| **Postconditions** | User sees all payment terms for the company; audit_log may have QUERY event (if configured) |

---

### UC-006: Get Payment Term by ID

| Field | Value |
|-------|-------|
| **UC-ID** | UC-006 |
| **Title** | Get payment term details by ID |
| **Actor** | ACCOUNTANT, AUDITOR, DIRECTOR |
| **Preconditions** | User authenticated, has READ role; payment term ID exists |
| **Basic Flow** | 1. User provides payment term UUID<br>2. API GET /api/v1/payment-terms/{id} processes request<br>3. PaymentTermRepository.get_by_id(id) queries DB<br>4. Entity serialized and returned in JSON<br>5. HTTP 200 returned with payment term details<br>6. Use case completes |
| **Alternative Flows** | **AP-001**: Payment term not found → Return 404 PAYMENT_TERM_NOT_FOUND<br>**AP-002**: User accesses another company's term → Return 403 ACCESS_DENIED (company_id check) |
| **Exception Guarantees** | Company isolation enforced; only accessible by authorized roles |
| **Postconditions** | User sees payment term details; audit trail preserved |

---

## 3. Document Numbering Series Use Cases

### UC-007: Create Document Numbering Series

| Field | Value |
|-------|-------|
| **UC-ID** | UC-007 |
| **Title** | Create new document numbering series |
| **Actor** | ACCOUNTANT, CHIEF_ACCOUNTANT |
| **Preconditions** | User authenticated, has WRITE role; company exists |
| **Basic Flow** | 1. User navigates to series creation page<br>2. User fills form: company_id, prefix="HD/" (GDT format), name="Hóa đơn", max_sequences=999999<br>3. User submits form<br>4. API POST /api/v1/document-numbering processes request<br>5. Service layer validates: prefix matches ^[A-Z]{2,}/$ (TT163), prefix unique per company, active series count < 15<br>6. DocumentNumberingSeries entity created with next_sequence=1, is_active=TRUE<br>7. SQLAlchemyRepository.create() persists to DB<br>8. AuditLogService.append_event() logs CREATE event with SHA-256 checksum<br>9. HTTP 201 returned with created series JSON<br>10. Use case completes |
| **Alternative Flows** | **AP-001**: Prefix doesn't match GDT format → Return 422 INVALID_SERIES_PREFIX<br>**AP-002**: Prefix already exists for company → Return 409 PREFIX_ALREADY_EXISTS<br>**AP-003**: Company already has 15 active series → Return 409 MAX_SERIES_EXCEEDED<br>**AP-004**: Missing actor UUID → Return 400 MISSING_ACTOR<br>**AP-005**: Missing reason → Return 400 MISSING_REASON |
| **Exception Guarantees** | Prefix format validated per GDT TT163; max 15 active series enforced; prefix unique per company; actor UUID required |
| **Postconditions** | New series stored in DB with next_sequence=1, is_active=TRUE; SHA-256 checksum in audit_log; company now has new document numbering capability |

---

### UC-008: Increment Document Numbering Sequence

| Field | Value |
|-------|-------|
| **UC-ID** | UC-008 |
| **Title** | Increment sequence for document creation |
| **Actor** | ACCOUNTANT (primary), CHIEF_ACCOUNTANT |
| **Preconditions** | User authenticated, has INCREMENT role; series exists and is ACTIVE; next_sequence < max_sequences |
| **Basic Flow** | 1. User triggers sequence increment (e.g., creating new invoice)<br>2. API POST /api/v1/document-numbering/{id}/increment processes request<br>3. Service layer validates: series exists, series is ACTIVE, next_sequence < max_sequences<br>4. DocumentNumberingSeries.next_sequence incremented by 1 (atomic)<br>5. Generated document number: {{prefix}}{{next_sequence}} (e.g., "HD/000001")<br>6. SQLAlchemyRepository.update() persists increment to DB<br>7. AuditLogService.append_event() logs INCREMENT event with SHA-256 checksum<br>8. HTTP 200 returned with generated document number<br>9. Use case completes |
| **Alternative Flows** | **AP-001**: Series is INACTIVE → Return 409 SERIES_INACTIVE, cannot increment<br>**AP-002**: next_sequence at max_sequences → Return 409 SEQUENCE_AT_MAX, must deactivate or create new series<br>**AP-003**: Series not found → Return 404 SERIES_NOT_FOUND<br>**AP-004**: Missing actor UUID → Return 400 MISSING_ACTOR<br>**AP-005**: Missing reason → Return 400 MISSING_REASON |
| **Exception Guarantees** | Only ACTIVE series can be incrementated; sequence cannot exceed max_sequences; atomic increment (any failure rolls back) |
| **Postconditions** | next_sequence incremented by 1; document number generated and returned; audit_log has INCREMENT event with checksum; invoice can be created with this document number |

---

### UC-009: Activate Document Numbering Series (SOD)

| Field | Value |
|-------|-------|
| **UC-ID** | UC-009 |
| **Title** | Activate numbering series (Separation of Duties) |
| **Actor** | CHIEF_ACCOUNTANT (requests), ACCOUNTANT (approves) |
| **Preconditions** | User authenticated, has CHIEF_ACCOUNTANT role; series exists and is INACTIVE; company has < 15 active series |
| **Basic Flow** | 1. CHIEF_ACCOUNTANT submits request to activate series<br>2. System validates: series exists, company active series count < 15<br>3. System records "ACTIVATE_REQUEST" event with Checksum 1: SHA-256(prev + chief_actor_uuid + now + "ACTIVATE_REQUEST" + reason + series_id)<br>4. System queues pending approval for ACCOUNTANT<br>5. ACCOUNTANT logs in, sees pending approval<br>6. ACCOUNTANT reviews and clicks "Approve"<br>7. System records "ACTIVATE_APPROVE" event with Checksum 2: SHA-256(prev + accountant_actor_uuid + now + "ACTIVATE_APPROVE" + reason + series_id)<br>8. Series.is_active set to TRUE in DB<br>9. HTTP 200 returned with success message<br>10. Use case completes |
| **Alternative Flows** | **AP-001**: Company already has 15 active series → Return 409 MAX_SERIES_EXCEEDED, must deactivate existing first<br>**AP-002**: ACCOUNTANT rejects → Return 409 ACTIVATE_REJECTED, series remains INACTIVE; Checksum 2 appended for "ACTIVATE_REJECT"<br>**AP-003**: Series already ACTIVE → Return 409 ALREADY_ACTIVE |
| **Exception Guarantees** | SOD enforced: 2 actors required for activation; max 15 active series enforced; both actors logged in audit chain |
| **Postconditions** | Series marked ACTIVE; dual checksum chain in audit_log (request + approval); company now has one more active series; audit trail preserved 10 years |

---

### UC-010: Deactivate Document Numbering Series

| Field | Value |
|-------|-------|
| **UC-ID** | UC-010 |
| **Title** | Deactivate numbering series |
| **Actor** | ACCOUNTANT, CHIEF_ACCOUNTANT |
| **Preconditions** | User authenticated, has ACTIVATE or DEACTIVATE role; series exists and is ACTIVE |
| **Basic Flow** | 1. User submits deactivation request for series<br>2. Service layer validates: series exists, series is ACTIVE<br>3. Series.is_active set to FALSE in DB (soft delete)<br>4. SQLAlchemyRepository.update() persists status change<br>5. AuditLogService.append_event() logs DEACTIVATE event with SHA-256 checksum<br>6. HTTP 200 returned with success message<br>7. Use case completes |
| **Alternative Flows** | **AP-001**: Series is only active one for company → Return 409 CANNOT_DEACTIVATE_LAST_ACTIVE, must keep at least one active series<br>**AP-002**: Series has documents already issued → Return 409 HAS_ISSUED_DOCUMENTS, cannot deactivate series with existing document numbers<br>**AP-003**: Series already INACTIVE → Return 409 ALREADY_INACTIVE |
| **Exception Guarantees** | Soft-delete only (row preserved); 10-year retention; no automatic deletion; must keep at least one active series per company |
| **Postconditions** | Series marked INACTIVE; checksum in audit_log; series no longer available for new document numbering; audit trail preserved for 10 years |

---

### UC-011: List Document Numbering Series by Company

| Field | Value |
|-------|-------|
| **UC-ID** | UC-011 |
| **Title** | List numbering series for a company |
| **Actor** | ACCOUNTANT, AUDITOR, DIRECTOR |
| **Preconditions** | User authenticated, has READ role; company exists |
| **Basic Flow** | 1. User requests list of series for company_id<br>2. API GET /api/v1/document-numbering?company_id={id} processes request<br>3. DocumentNumberingSeriesRepository.get_by_company(company_id) queries DB<br>4. Results serialized and returned in JSON array<br>5. HTTP 200 returned with series list<br>6. Use case completes |
| **Alternative Flows** | **AP-001**: Company not found → Return 404 COMPANY_NOT_FOUND<br>**AP-002**: No series exist for company → Return 200 empty array `[]` |
| **Exception Guarantees** | Data scoped by company_id (tenant isolation); AUDITOR can read only |
| **Postconditions** | User sees all series for the company; audit trail preserved |

---

### UC-012: Get Series by ID

| Field | Value |
|-------|-------|
| **UC-ID** | UC-012 |
| **Title** | Get numbering series details by ID |
| **Actor** | ACCOUNTANT, AUDITOR, DIRECTOR |
| **Preconditions** | User authenticated, has READ role; series ID exists |
| **Basic Flow** | 1. User provides series UUID<br>2. API GET /api/v1/document-numbering/{id} processes request<br>3. DocumentNumberingSeriesRepository.get_by_id(id) queries DB<br>4. Entity serialized and returned in JSON<br>5. HTTP 200 returned with series details<br>6. Use case completes |
| **Alternative Flows** | **AP-001**: Series not found → Return 404 SERIES_NOT_FOUND<br>**AP-002**: User accesses another company's series → Return 403 ACCESS_DENIED |
| **Exception Guarantees** | Company isolation enforced; only accessible by authorized roles |
| **Postconditions** | User sees series details; audit trail preserved |

---

## 4. Exception Use Cases

### UC-EX-001: Missing Actor UUID

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-001 |
| **Title** | Actor UUID missing from request |
| **Actor** | System (error handler) |
| **Preconditions** | User submits API request without actor field |
| **Basic Flow** | 1. API endpoint receives POST/PATCH/DELETE request<br>2. @require_actor() decorator checks for actor in request body<br>3. Actor missing → Return 400 MISSING_ACTOR<br>4. Response: `{"error": "actor là bắt buộc", "code": "MISSING_ACTOR"}`<br>5. Use case ends; no further processing |
| **Alternative Flows** | N/A |
| **Exception Guarantees** | All mutation endpoints require actor UUID; never proceed without it |
| **Postconditions** | Error response returned; original request not processed; audit_log may have ENTRY_ERROR event |

---

### UC-EX-002: Missing Reason

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-002 |
| **Title** | Reason string missing from request |
| **Actor** | System (error handler) |
| **Preconditions** | User submits mutation request without reason field |
| **Basic Flow** | 1. API endpoint receives mutation request<br>2. @require_reason() decorator checks for reason in request body<br>3. Reason missing → Return 400 MISSING_REASON<br>4. Response: `{"error": "Lý do là bắt buộc", "code": "MISSING_REASON"}`<br>5. Use case ends; no further processing |
| **Alternative Flows** | N/A |
| **Exception Guarantees** | All mutations require non-empty reason; enforced at API decorator + service layer |
| **Postconditions** | Error response returned; original request not processed |

---

### UC-EX-003: AUDITOR Attempting Mutation

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-003 |
| **Title** | AUDITOR role attempting mutation operation |
| **Actor** | AUDITOR user |
| **Preconditions** | AUDITOR- authenticated user tries to create/update payment term or series |
| **Basic Flow** | 1. AUDITOR sends POST/PATCH request to mutation endpoint<br>2. @login_required + current_user.role check: if role == 'AUDITOR' → deny<br>3. AUDITOR not in allowed roles → Access denied<br>4. Return 403 AUDITOR_READ_ONLY<br>5. Response: `{"error": "AUDITOR chỉ đọc", "code": "AUDITOR_READ_ONLY"}`<br>6. Use case ends; mutation blocked |
| **Alternative Flows** | N/A |
| **Exception Guarantees** | AUDITOR role strictly read-only; cannot mutate any payment terms or numbering series |
| **Postconditions** | 403 returned; mutation blocked; attempt logged in audit_log with AUDITOR_ACCESS_DENIED event |

---

### UC-EX-004: Duplicate Payment Term Name

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-004 |
| **Title** | Attempt to create payment term with name already exists |
| **Actor** | ACCOUNTANT or CHIEF_ACCOUNTANT |
| **Preconditions** | User tries to create payment term with name already used by another term in same company |
| **Basic Flow** | 1. User submits POST /api/v1/payment-terms with name="Net 30"<br>2. Service layer validates: name must be unique per company<br>3. Duplicate detected → Return 409 DUPLICATE_PAYMENT_TERM<br>4. Response: `{"error": "Tên đã tồn tại cho doanh nghiệp này", "code": "DUPLICATE_PAYMENT_TERM"}`<br>5. Use case ends; payment term not created |
| **Alternative Flows** | N/A |
| **Exception Guarantees** | Name uniqueness enforced per company; cannot have two terms with same name |
| **Postconditions** | Error returned; original payment term not created; user must choose different name |

---

### UC-EX-005: Maximum Series Exceeded

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-005 |
| **Title** | Company already at 15 active series limit |
| **Actor** | ACCOUNTANT or CHIEF_ACCOUNTANT |
| **Preconditions** | User tries to create new series when company already has 15 active series |
| **Basic Flow** | 1. User submits POST /api/v1/document-numbering with prefix="PN/"<br>2. Service layer validates: active series count per company<br>3. Count >= 15 → Return 409 MAX_SERIES_EXCEEDED<br>4. Response: `{"error": "Đã đạt giới hạn 15 series active cho doanh nghiệp này", "code": "MAX_SERIES_EXCEEDED"}`<br>5. Use case ends; new series not created |
| **Alternative Flows** | **Solution**: User must deactivate existing series first (UC-010), then create new series<br>**AP**: Deactivate an existing series, then retry creation |
| **Exception Guarantees** | Maximum 15 active series per company (GDT Circular 163/2020/TT-BTC); enforced at service layer |
| **Postconditions** | Error returned; new series not created; user must deactivate existing series first |

---

### UC-EX-006: Series at Maximum Sequence

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-006 |
| **Title** | Series next_sequence at maximum (999999) |
| **Actor** | ACCOUNTANT creating invoice |
| **Preconditions** | User tries to increment sequence when next_sequence >= max_sequences |
| **Basic Flow** | 1. User triggers sequence increment (invoice creation)<br>2. Service layer validates: next_sequence < max_sequences<br>3. next_sequence >= max_sequences → Return 409 SEQUENCE_AT_MAX<br>4. Response: `{"error": "Số tiếp theo đã đạt giới hạn 999999", "code": "SEQUENCE_AT_MAX"}`<br>5. Use case ends; sequence not incremented; invoice creation blocked |
| **Alternative Flows** | **Solution**: User must deactivate current series and create new series with fresh sequence, or increase max_sequences (admin only)<br>**AP**: Deactivate series, create new series with prefix variant, resume numbering |
| **Exception Guarantees** | Sequence cannot exceed max_sequences (default 999999); enforced at service layer |
| **Postconditions** | Error returned; sequence not incremented; invoice creation blocked until series reset |

---

### UC-EX-007: Cannot Deactivate Default Payment Term

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-007 |
| **Title** | User attempts to deactivate default payment term |
| **Actor** | ACCOUNTANT or CHIEF_ACCOUNTANT |
| **Preconditions** | User tries to deactivate a payment term that is set as default |
| **Basic Flow** | 1. User submits deactivation request for default payment term<br>2. Service layer validates: term.is_default = TRUE<br>3. Block deactivation → Return 409 CANNOT_DEACTIVATE_DEFAULT<br>4. Response: `{"error": "Không thể vô hiệu hóa default payment term", "code": "CANNOT_DEACTIVATE_DEFAULT"}`<br>5. Use case ends; term remains ACTIVE but default |
| **Alternative Flows** | **Solution**: First unset default (set another term as default or remove default), then deactivate<br>**AP**: Set a different payment term as default first, then deactivate the original |
| **Exception Guarantees** | Cannot soft-delete default payment term; must reassign default first |
| **Postconditions** | Error returned; default payment term remains active; user must follow alternative path |

---

### UC-EX-008: Cannot Deactivate Series with Issued Documents

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-008 |
| **Title** | User attempts to deactivate series with existing issued documents |
| **Actor** | ACCOUNTANT or CHIEF_ACCOUNTANT |
| **Preconditions** | User tries to deactivate a series that has documents already issued (with document numbers) |
| **Basic Flow** | 1. User submits deactivation request for series<br>2. Service layer validates: series has issued documents (check invoice table for documents with this series prefix)<br>3. Has issued documents → Return 409 HAS_ISSUED_DOCUMENTS<br>4. Response: `{"error": "Không thể vô hiệu hóa series có tài liệu đã xuất bản", "code": "HAS_ISSUED_DOCUMENTS"}`<br>5. Use case ends; series remains ACTIVE |
| **Alternative Flows** | **Solution**: Create new series for future documents; existing documents keep their original series numbers (preserved for 10-year retention)<br>**AP**: Leave series active; create new series with different prefix for new documents |
| **Exception Guarantees** | Cannot soft-delete series with existing issued documents; preservation of issued document numbers for audit/retention |
| **Postconditions** | Error returned; series remains ACTIVE; existing document numbers preserved; new documents use new series |

---

### UC-EX-009: Company Not Found

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-009 |
| **Title** | Company ID not found in database |
| **Actor** | System (all endpoints) |
| **Preconditions** | User provides company_id that doesn't exist in companies table |
| **Basic Flow** | 1. API endpoint receives request with company_id={uuid}<br>2. Repository.query() returns no results or raises NoResultFound<br>3. Exception caught → Return 404 COMPANY_NOT_FOUND<br>4. Response: `{"error": "Doanh nghiệp không tồn tại", "code": "COMPANY_NOT_FOUND"}`<br>5. Use case ends; no further processing |
| **Alternative Flows** | N/A |
| **Exception Guarantees** | All payment term/series data scoped to existing companies only |
| **Postconditions** | 404 returned; request not processed; user must provide valid company_id |

---

### UC-EX-010: Payment Term Not Found

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-010 |
| **Title** | Payment term ID not found |
| **Actor** | System (all endpoints) |
| **Preconditions** | User provides payment_term_id that doesn't exist |
| **Basic Flow** | 1. API endpoint receives request with payment_term_id={uuid}<br>2. Repository.get_by_id() returns None<br>3. Exception caught → Return 404 PAYMENT_TERM_NOT_FOUND<br>4. Response: `{"error": "Payment term không tồn tại", "code": "PAYMENT_TERM_NOT_FOUND"}`<br>5. Use case ends; no further processing |
| **Alternative Flows** | N/A |
| **Exception Guarantees** | Payment term must exist for any operation |
| **Postconditions** | 404 returned; request not processed |

---

### UC-EX-011: Series Not Found

| Field | Value |
|-------|-------|
| **UC-ID** | UC-EX-011 |
| **Title** | Document numbering series ID not found |
| **Actor** | System (all endpoints) |
| **Preconditions** | User provides series_id that doesn't exist |
| **Basic Flow** | 1. API endpoint receives request with series_id={uuid}<br>2. Repository.get_by_id() returns None<br>3. Exception caught → Return 404 SERIES_NOT_FOUND<br>4. Response: `{"error": "Series không tồn tại", "code": "SERIES_NOT_FOUND"}`<br>5. Use case ends; no further processing |
| **Alternative Flows** | N/A |
| **Exception Guarantees** | Series must exist for any operation |
| **Postconditions** | 404 returned; request not processed |

---

## 5. Happy Path Summary

| UC-ID | Title | Success Status |
|-------|-------|----------------|
| UC-001 | Create Payment Term | ✓ 201 + JSON |
| UC-002 | Set Default Payment Term (SOD) | ✓ 200 + dual checksum |
| UC-003 | Update Payment Term | ✓ 200 + JSON |
| UC-004 | Deactivate Payment Term | ✓ 200 + audit trail |
| UC-005 | List Payment Terms | ✓ 200 + array |
| UC-006 | Get Payment Term by ID | ✓ 200 + JSON |
| UC-007 | Create Document Numbering Series | ✓ 201 + JSON |
| UC-008 | Increment Sequence | ✓ 200 + document number |
| UC-009 | Activate Series (SOD) | ✓ 200 + dual checksum |
| UC-010 | Deactivate Series | ✓ 200 + audit trail |
| UC-011 | List Series | ✓ 200 + array |
| UC-012 | Get Series by ID | ✓ 200 + JSON |

## 6. Use Case Matrix by Role

| Use Case | ACCOUNTANT | CHIEF_ACCOUNTANT | AUDITOR | ADMIN | DIRECTOR |
|----------|-----------|------------------|---------|-------|----------|
| UC-001 (Create PT) | ✓ | ✓ | ✗ | ✓ | ✓ |
| UC-002 (Set Default) | ✗ (approve only) | ✓ (request+approve) | ✗ | ✓ | ✓ |
| UC-003 (Update PT) | ✓ | ✓ | ✗ | ✓ | ✓ |
| UC-004 (Deactivate PT) | ✓ | ✓ | ✗ | ✓ | ✓ |
| UC-005 (List PT) | ✓ | ✓ | ✓ | ✓ | ✓ |
| UC-006 (Get PT by ID) | ✓ | ✓ | ✓ | ✓ | ✓ |
| UC-007 (Create Series) | ✓ | ✓ | ✗ | ✓ | ✓ |
| UC-008 (Increment Seq) | ✓ (on ACTIVE) | ✓ | ✗ | ✓ | ✓ |
| UC-009 (Activate Series) | ✗ (approve only) | ✓ (request+approve) | ✗ | ✓ | ✓ |
| UC-010 (Deactivate Series) | ✓ | ✓ | ✗ | ✓ | ✓ |
| UC-011 (List Series) | ✓ | ✓ | ✓ | ✓ | ✓ |
| UC-012 (Get Series by ID) | ✓ | ✓ | ✓ | ✓ | ✓ |

✓ = Can perform, ✗ = Cannot perform (read-only or role-restricted)