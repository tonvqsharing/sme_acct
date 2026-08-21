# Processes, Rules, Data Flows & Workflows — Payment Terms & Document Numbering Module

---

## 1. Processes

### 1.1 Payment Term Lifecycle Process

```
┌──────────────────┐     CREATE     ┌─────────────────────┐
│   INACTIVE        │ ────────────▶ │   ACTIVE            │
│   (Soft Delete)   │              │   Payment Term     │
└──────────────────┘              └─────────────────────┘
        ▲                               │
        │                               │ DEACTIVATE
        │                               ▼
        │                      ┌─────────────────────┐
        │                      │   INACTIVE          │
        │                      │   (Soft Delete)     │
        │                      └─────────────────────┘
        │
        │ CREATE (new)
        ▼
┌─────────────────────┐
│   ACTIVE            │
│   Payment Term     │
└─────────────────────┘
```

**States:**
- **ACTIVE**: Payment term is active and can be selected for invoices; is_default=TRUE or FALSE
- **INACTIVE**: Payment term soft-deactivated; row preserved in DB for 10-year retention; cannot be selected for new invoices

**Transitions:**
- **CREATE**: New payment term starts as ACTIVE, is_default=FALSE
- **ACTIVATE**: (N/A — new terms start ACTIVE)
- **DEACTIVATE**: ACTIVE → INACTIVE (soft delete); blocked if term is default
- **SET DEFAULT**: Changes is_default=TRUE; SOD enforced (2-actor approval)

---

### 1.2 Document Numbering Series Lifecycle Process

```
┌──────────────────┐     CREATE     ┌─────────────────────┐
│   INACTIVE        │ ────────────▶ │   ACTIVE            │
│   (Soft Delete)   │              │   Series            │
└──────────────────┘              └─────────────────────┘
        ▲                               │
        │                               │ DEACTIVATE
        │                               ▼
        │                      ┌─────────────────────┐
        │                      │   INACTIVE          │
        │                      │   (Soft Delete)     │
        │                      └─────────────────────┘
        │
        │ CREATE (new)
        ▼
┌─────────────────────┐
│   ACTIVE            │
│   Series            │
└─────────────────────┘
```

**States:**
- **ACTIVE**: Series is active; next_sequence can be incrementated; available for document creation
- **INACTIVE**: Series soft-deactivated; row preserved for 10-year retention; cannot increment sequence

**Transitions:**
- **CREATE**: New series starts as ACTIVE, next_sequence=1
- **ACTIVATE**: INACTIVE → ACTIVE (SOD: 2-actor approval required)
- **DEACTIVATE**: ACTIVE → INACTIVE (soft delete); blocked if only active series for company
- **INCREMENT**: next_sequence += 1; only possible when series is ACTIVE and next_sequence < max_sequences

---

### 1.3 Sequence Increment Process (Per Document Creation)

```
┌─────────────────────┐     INCREMENT     ┌─────────────────────┐
│  series: ACTIVE     │ ────────────────▶ │ next_sequence+1     │
│  next_sequence=N    │                 │ (atomic increment)  │
└─────────────────────┘                 └─────────────────────┘
                                              │
                                              ▼
                                       ┌─────────────────────┐
                                       │ Document Number:    │
                                       │ {{prefix}}{{N+1}}   │
                                       │ e.g., HD/000001     │
                                       └─────────────────────┘
```

**Constraints:**
- Series MUST be ACTIVE to increment
- next_sequence must be < max_sequences (default 999999)
- Any failure rolls back the entire transaction (atomic all-or-nothing)
- SHA-256 checksum appended to audit_log for the increment event

---

### 1.4 SOD (Separation of Duties) Approval Process

```
┌─────────────────────┐
│   Request Phase     │
│   (Actor 1: Chief  │
│    Accountant)     │
└─────────────────────┘
        │ (Wait for 2nd actor)
        ▼
┌─────────────────────┐
│   Approval Phase    │
│   (Actor 2:       │
│    Accountant)    │
└─────────────────────┘
```

**Operations requiring SOD:**
- Setting default payment term (UC-002)
- Activating document numbering series (UC-009)

**SOD Flow:**
1. **Request Phase**: Primary actor (CHIEF_ACCOUNTANT) submits request
   - Checksum 1 appended: SHA-256(prev + chief_actor + now + "ACTION_REQUEST" + reason + entity_id)
   - System queues pending approval
   
2. **Approval Phase**: Secondary actor (ACCOUNTANT) reviews and approves/rejects
   - If APPROVE: Checksum 2 appended: SHA-256(prev + accountant_actor + now + "APPROVE" + reason + entity_id)
     - Entity state changed (is_default=TRUE or is_active=TRUE)
     - Return success
   - If REJECT: Checksum 2 appended: SHA-256(prev + accountant_actor + now + "REJECT" + reason + entity_id)
     - Entity state unchanged
     - Return rejection

3. **Both checksums stored in audit_log** for immutable audit trail

---

## 2. Rules

### 2.1 Payment Term Rules (R-001 to R-012)

| Rule ID | Rule Description | Enforcement Level |
|---------|-----------------|-------------------|
| **R-001** | Every company can have only ONE default payment term | DB unique constraint + service layer validation |
| **R-002** | Payment term due_days must be ≥ 1 day | Entity validation on create/update |
| **R-003** | All mutations require actor UUID (D11) in request body | API decorator + service layer entry check |
| **R-004** | All mutations require non-empty reason string | API decorator + service layer validation |
| **R-005** | AUDITOR role is read-only; cannot create/update/delete payment terms | @login_required + current_user.role + service layer role check |
| **R-006** | 10-year retention: no automatic deletion, soft-deactivate only | Service layer policy + audit log configuration |
| **R-007** | Series prefix must match GDT format: ^[A-Z]{2,}/$ (TT163 compliance) | Entity validation on create |
| **R-008** | Maximum 15 active document numbering series per company (GDT Circular 163/2020/TT-BTC) | Service layer + DB constraint |
| **R-009** | Series prefix must be unique per company | DB unique constraint + service validation |
| **R-010** | SHA-256 checksum chaining on all payment term/series events | Service layer append_checksum() |
| **R-011** | SOD (Separation of Duties): setting default/activating series requires 2 actors | Service layer + @login_required + current_user.role |
| **R-012** | Due date calculation: issue_date + due_days (business days optional) | PaymentTermService.calculate_due_date() |

---

### 2.2 Document Numbering Series Rules (R-007 to R-012, continued)

| Rule ID | Rule Description | Enforcement Level |
|---------|-----------------|-------------------|
| **R-007** | Series prefix must match GDT format: ^[A-Z]{2,}/$ (TT163 compliance) | Entity validation on create |
| **R-008** | Maximum 15 active series per company (GDT Circular 163/2020/TT-BTC) | Service layer + DB constraint |
| **R-009** | Series prefix must be unique per company | DB unique constraint + service validation |
| **R-010** | SHA-256 checksum chaining on all payment term/series events | Service layer append_checksum() |
| **R-011** | SOD (Separation of Duties): setting default/activating series requires 2 actors | Service layer + @login_required + current_user.role |
| **R-012** | Due date calculation: issue_date + due_days (business days optional) | PaymentTermService.calculate_due_date() |

---

### 2.3 Cross-Module Rules

| Rule ID | Rule Description | Enforcement Level |
|---------|-----------------|-------------------|
| **R-013** | When creating invoice, apply payment terms due date auto-calculation | Invoice module integration (add payment_terms_id FK) |
| **R-014** | Document numbering series atomic: all-or-nothing (any failure → no partial save) | Service layer transaction management |
| **R-015** | Company data isolation: all payment term/series data scoped by company_id | Repository layer FK filtering + CASRBAC enforcement |
| **R-016** | Audit log required on every mutation: CREATE/UPDATE/DEACTIVATE/ACTIVATE/INCREMENT | Service layer mandatory append_checksum() |
| **R-017** | System account protection: no system accounts in this module | Domain layer design (N/A for this module) |
| **R-018** | Invoice-period enforcement: invoice issue_date must be within active fiscal year/period | Integration with fiscal year module (if period is locked, prompt user) |

---

## 3. Data Flows

### 3.1 Payment Term Creation Data Flow

```
INPUT:  POST /api/v1/payment-terms
Body:   {
    "company_id": "c123...",
    "name": "Net 30",
    "due_days": 30,
    "interest_rate": 0.00,
    "actor": "uuid-chief-accountant",
    "reason": "Setup default payment terms for new company"
}

│
├─→ Validation Layer:
│   1. company_id exists in companies table
│   2. name unique per company (check DB)
│   3. due_days >= 1
│   4. actor UUID not empty
│   5. reason not empty
│
├─→ PaymentTermService.create():
│   1. Create PaymentTerm entity
│   2. Set is_default=FALSE
│   3. checksum = SHA-256("0"*64 + actor + now + "CREATE" + reason + term_id)
│   4. entity.checksum = checksum
│
├─→ SQLAlchemyRepository.create():
│   1. INSERT INTO payment_terms (company_id, name, due_days, interest_rate, is_default, status, checksum, created_at)
│   2. RETURNING id, company_id, name, due_days, interest_rate, is_default, status, checksum, created_at
│
├─→ AuditLogService.append_event():
│   1. Append CREATE event to audit_log table
│   2. Event fields: entity_type="payment_term", entity_id=<new_id>, action="CREATE", checksum=<computed>
│   3. Also store: actor_uuid, reason, timestamp, old_values="N/A", new_values=<entity_json>
│
├─→ HTTP Response:
│   1. Status 201 Created
│   2. Body: serialize_payment_term(new_term)
│
└─→ POSTCONDITIONS:
    • Payment term stored in DB with all fields
    • SHA-256 checksum in audit_log
    • Company now has new payment term option
```

---

### 3.2 Document Numbering Series Creation Data Flow

```
INPUT:  POST /api/v1/document-numbering
Body:   {
    "company_id": "c123...",
    "prefix": "HD/",
    "name": "Hóa đơn",
    "max_sequences": 999999,
    "actor": "uuid-chief-accountant",
    "reason": "Setup invoice series for company"
}

│
├─→ Validation Layer:
│   1. company_id exists in companies table
│   2. prefix matches ^[A-Z]{2,}/$ (TT163 GDT format)
│   3. prefix unique per company (check DB)
│   4. active series count < 15 (GDT limit)
│   5. actor UUID not empty
│   6. reason not empty
│
├─→ DocumentNumberingSeriesService.create():
│   1. Create DocumentNumberingSeries entity
│   2. Set next_sequence=1
│   3. Set is_active=TRUE
│   4. Set status=ACTIVE
│   5. Validate prefix.validate_prefix() → must return True
│   6. checksum = SHA-256("0"*64 + actor + now + "CREATE" + reason + series_id)
│   7. entity.checksum = checksum
│
├─→ SQLAlchemyRepository.create():
│   1. INSERT INTO document_numbering_series (company_id, prefix, next_sequence, is_active, max_sequences, status, checksum, created_at)
│   2. RETURNING all fields
│
├─→ AuditLogService.append_event():
│   1. Append CREATE event to audit_log table
│   2. Event fields: entity_type="document_numbering_series", entity_id=<new_id>, action="CREATE", checksum=<computed>
│   3. Also store: actor_uuid, reason, timestamp, old_values="N/A", new_values=<entity_json>
│
├─→ HTTP Response:
│   1. Status 201 Created
│   2. Body: serialize_document_numbering_series(new_series)
│
└─→ POSTCONDITIONS:
    • New series stored in DB with next_sequence=1, is_active=TRUE
    • SHA-256 checksum in audit_log
    • Company now has new document numbering capability
```

---

### 3.3 Sequence Increment Data Flow (Document Creation)

```
TRIGGER: User creates invoice OR manually increments sequence

│
├─→ Service Layer Validation:
│   1. Get series by ID (from invoice or request)
│   2. Validate series is ACTIVE
│   3. Validate next_sequence < max_sequences
│
├─→ DocumentNumberingSeriesService.increment():
│   1. next_sequence = series.next_sequence + 1 (atomic operation)
│   2. series.next_sequence = next_sequence
│   3. generated_number = "{{series.prefix}}{{next_sequence}}" (e.g., "HD/000001")
│   4. checksum = SHA-256(prev_checksum + actor + now + "INCREMENT" + reason + series_id + old_next_seq + new_next_seq)
│   5. entity.checksum = checksum
│
├─→ SQLAlchemyRepository.update():
│   1. UPDATE document_numbering_series SET next_sequence=<new_val> WHERE id=<series_id>
│   2. RETURNING new next_sequence value
│
├─→ Invoice Creation (if applicable):
│   1. Create Invoice with document_number=generated_number
│   2. If payment_term_id set: calculate due_date = issue_date + due_days
│   3. Save invoice to DB
│
├─→ AuditLogService.append_event():
│   1. Append INCREMENT event to audit_log table
│   2. Event fields: entity_type="document_numbering_series", entity_id=<series_id>, action="INCREMENT", checksum=<computed>
│   3. Also store: actor_uuid, reason, timestamp, old_next_sequence=<old_val>, new_next_sequence=<new_val>, generated_document_number=<generated_num>
│
├─→ HTTP Response:
│   1. Status 200 OK
│   2. Body: {"document_number": "HD/000001", "next_sequence": 1, "series_id": "<id>"}
│
└─→ POSTCONDITIONS:
    • next_sequence incremented by 1 in DB
    • Document number generated and returned
    • Invoice (if created) has document_number set
    • SHA-256 checksum in audit_log reflecting the increment
```

---

### 3.4 SOD Approval Data Flow (Set Default/Activate Series)

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Request (Primary Actor: CHIEF_ACCOUNTANT)            │
│  ────────────────────────────────────────────────────────────── │
│  1. Submit request: set default / activate series              │
│  2. Validation: entity exists, valid state, company checks     │
│  3. Checksum 1: SHA-256(prev + chief_actor + now + "ACTION_REQ"│
│     + reason + entity_id)                                      │
│  4. Queue pending approval in system                           │
│  ────────────────────────────────────────────────────────────── │
│                                                                  │
│  Phase 2: Approval (Secondary Actor: ACCOUNTANT)               │
│  ────────────────────────────────────────────────────────────── │
│  1. ACCOUNTANT logs in, sees pending approval                    │
│  2. Reviews and clicks: APPROVE or REJECT                       │
│  3. If APPROVE:                                                │
│     • Checksum 2: SHA-256(prev + accountant_actor + now + "AP" │
│       + reason + entity_id)                                    │
│     • Execute state change: is_default=TRUE or is_active=TRUE   │
│     • If SET DEFAULT: unset other terms' is_default=FALSE       │
│     • Return 200 success                                       │
│  4. If REJECT:                                                 │
│     • Checksum 2: SHA-256(prev + accountant_actor + now + "RE" │
│       + reason + entity_id)                                    │
│     • No state change                                          │
│     • Return 409 rejection message                             │
│  ────────────────────────────────────────────────────────────── │
│                                                                  │
│  FINAL: Both checksums stored in audit_log (immutable chain)   │
│  ────────────────────────────────────────────────────────────── │
└─────────────────────────────────────────────────────────────────┘
```

**Checksum Details:**
- **Checksum 1 (Request)**: SHA-256("0"*64 + chief_actor_uuid + timestamp_1 + "DEFAULT_REQUEST" + reason + term_id)
- **Checksum 2 (Approval)**: SHA-256(checksum_1 + accountant_actor_uuid + timestamp_2 + "DEFAULT_APPROVE" + reason + term_id)
- **Immutable**: Both checksums stored in audit_log; cannot be altered without detection

---

## 4. Workflows

### 4.1 Payment Term Setting as Default Workflow (SOD) — Detailed

```
┌─────────────────────────────────────────────────────────────────┐
│                        SET DEFAULT PAYMENT TERM                 │
│  (Separation of Duties: 2-actor approval)                       │
├─────────────────────────────────────────────────────────────────┤
│  STEP 1: CHIEF_ACCOUNTANT requests set as default              │
│  │                                                               │
│  │  Action: POST /api/v1/payment-terms/{id}/set-default         │
│  │  Body: { "actor": "chief-uuid", "reason": "Make default" }   │
│  │                                                               │
│  │  Validation:                                                  │
│  │  • Term exists and is ACTIVE                                  │
│  │  • Company has NO current default                             │
│  │  • Actor UUID present                                         │
│  │  • Reason present                                             │
│  │                                                               │
│  │  Outcome: If valid → Queue pending ACCOUNTANT approval        │
│  │           If invalid → 409 DEFAULT_ALREADY_EXISTS or 400      │
│  │                                                               │
│  │  Checksum 1: SHA-256(0*64 + chief_uuid + now + "DR" + reason│
│  │           + term_id)                                          │
│  │  Append to audit_log: "DEFAULT_REQUEST" event                │
│  └───────────────────────────────────────────────────────────────┘
│                                                                  │
│  STEP 2: Wait for ACCOUNTANT approval                           │
│  │                                                               │
│  │  ACCOUNTANT logs in, sees pending approval in dashboard       │
│  │  Reviews the request details                                  │
│  │                                                               │
│  │  Action: ACCOUNTANT clicks "Approve" or "Reject"             │
│  │                                                               │
│  │  If APPROVE:                                                  │
│  │    • Checksum 2: SHA-256(prev + accountant_uuid + now + "DA"│
│  │      + reason + term_id)                                      │
│  │    • PaymentTerm.is_default = TRUE                          │
│  │    • All other terms for company: is_default = FALSE          │
│  │    • SQLAlchemyRepository.update() persists changes           │
│  │    • Append Checksum 2 to audit_log: "DEFAULT_APPROVE" event  │
│  │    • Return 200 + "Default set success"                      │
│  │                                                               │
│  │  If REJECT:                                                   │
│  │    • Checksum 2: SHA-256(prev + accountant_uuid + now + "DR"│
│  │      + reason + term_id)                                      │
│  │    • No state changes                                         │
│  │    • Append Checksum 2 to audit_log: "DEFAULT_REJECT" event   │
│  │    • Return 409 + "Rejected, default unchanged"              │
│  │                                                               │
│  └───────────────────────────────────────────────────────────────┘
│                                                                  │
│  STEP 3: Final state                                              │
│  │                                                               │
│  │  • If APPROVED: Payment term now is_default=TRUE              │
│  │  • Dual checksum chain in audit_log (immutable)               │
│  │  • Company now has 1 default payment term                     │
│  │                                                               │
│  └───────────────────────────────────────────────────────────────┘
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **SOD Enforced**: Both CHIEF_ACCOUNTANT and ACCOUNTANT must participate
- **Checksum Chain**: 2 SHA-256 hashes form immutable audit trail
- **Default Unsetting**: When new default set, all other terms' is_default set to FALSE atomically
- **Audit Trail**: Both events stored in audit_log for 10-year retention

---

### 4.2 Document Numbering Series Activation Workflow (SOD) — Detailed

```
┌─────────────────────────────────────────────────────────────────┐
│                        ACTIVATE SERIES                           │
│  (Separation of Duties: 2-actor approval)                       │
├─────────────────────────────────────────────────────────────────┤
│  STEP 1: CHIEF_ACCOUNTANT requests activate series               │
│  │                                                               │
│  │  Action: POST /api/v1/document-numbering/{id}/activate       │
│  │  Body: { "actor": "chief-uuid", "reason": "Activate series" }│
│  │                                                               │
│  │  Validation:                                                  │
│  │  • Series exists and is INACTIVE                              │
│  │  • Company has < 15 active series (GDT limit)                 │
│  │  • Actor UUID present                                         │
│  │  • Reason present                                             │
│  │                                                               │
│  │  Outcome: If valid → Queue pending ACCOUNTANT approval        │
│  │           If invalid → 409 MAX_SERIES_EXCEEDED or 400         │
│  │                                                               │
│  │  Checksum 1: SHA-256(0*64 + chief_uuid + now + "ASR" + reason│
│  │           + series_id)                                        │
│  │  Append to audit_log: "ACTIVATE_REQUEST" event                │
│  └───────────────────────────────────────────────────────────────┘
│                                                                  │
│  STEP 2: Wait for ACCOUNTANT approval                           │
│  │                                                               │
│  │  ACCOUNTANT logs in, sees pending approval in dashboard       │
│  │  Reviews the request details                                  │
│  │                                                               │
│  │  Action: ACCOUNTANT clicks "Approve" or "Reject"             │
│  │                                                               │
│  │  If APPROVE:                                                  │
│  │    • Checksum 2: SHA-256(prev + accountant_uuid + now + "AA"│
│  │      + reason + series_id)                                    │
│  │    • Series.is_active = TRUE                                  │
│  │    • SQLAlchemyRepository.update() persists changes           │
│  │    • Append Checksum 2 to audit_log: "ACTIVATE_APPROVE" event │
│  │    • Return 200 + "Series activated success"                 │
│  │                                                               │
│  │  If REJECT:                                                   │
│  │    • Checksum 2: SHA-256(prev + accountant_uuid + now + "AR"│
│  │      + reason + series_id)                                    │
│  │    • No state changes                                         │
│  │    • Append Checksum 2 to audit_log: "ACTIVATE_REJECT" event   │
│  │    • Return 409 + "Reactivated denied"                       │
│  │                                                               │
│  └───────────────────────────────────────────────────────────────┘
│                                                                  │
│  STEP 3: Final state                                              │
│  │                                                               │
│  │  • If APPROVED: Series now is_active=TRUE                      │
│  │  • Dual checksum chain in audit_log (immutable)               │
│  │  • Company now has one more active series (must still ≤ 15)   │
│  │                                                               │
│  └───────────────────────────────────────────────────────────────┘
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **SOD Enforced**: Both CHIEF_ACCOUNTANT and ACCOUNTANT must participate
- **GDT Limit Check**: Company must have < 15 active series before activation
- **Checksum Chain**: 2 SHA-256 hashes form immutable audit trail
- **Post-Activation**: Series immediately available for sequence increment

---

### 4.3 Document Creation with Numbering Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                       DOCUMENT CREATION                          │
│  (Auto-increment series sequence on invoice creation)            │
├─────────────────────────────────────────────────────────────────┤
│  TRIGGER: User clicks "Create Invoice" or API creates invoice      │
│  │                                                               │
│  │  1. Determine company_id from user context                    │
│  │  2. Get company's default payment term (if any)               │
│  │  3. Get company's active document numbering series            │
│  │                                                               │
│  │  Validation:                                                  │
│  │  • Company exists                                             │
│  │  • Series is ACTIVE                                           │
│  │  • next_sequence < max_sequences                              │
│  │                                                               │
│  │  4. Increment sequence: next_sequence += 1                    │
│  │  │                                                             │
│  │  │  Generated document number: {{prefix}}{{next_sequence}}      │
│  │  │  e.g., if prefix="HD/" and next_sequence=1 → "HD/000001"   │
│  │  │                                                             │
│  │  5. Create Invoice with:                                      │
│  │  │  • document_number = generated_number                      │
│  │  │  • payment_term_id = default_term_id (if set)              │
│  │  │  • due_date = issue_date + due_days (auto-calc)            │
│  │  │                                                             │
│  │  6. Save invoice to DB                                        │
│  │                                                               │
│  │  7. AuditLogService.append_event():                           │
│  │  │  • INCREMENT event with checksum                            │
│  │  │  • Invoice CREATE event with checksum                       │
│  │                                                               │
│  │  8. HTTP 201 + invoice details returned                       │
│  │                                                               │
│  └───────────────────────────────────────────────────────────────┘
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **Auto-increment**: Sequence auto-increments on every invoice creation
- **Document Number Format**: {{prefix}}{{sequence}} (GDT compliant)
- **Payment Term Integration**: due_date auto-calculated from payment terms
- **Audit Trail**: Both INCREMENT and Invoice CREATE events logged

---

### 4.4 Deactivate Payment Term Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEACTIVATE PAYMENT TERM                      │
│  (Soft Delete: row preserved, 10-year retention)                │
├─────────────────────────────────────────────────────────────────┤
│  TRIGGER: User selects "Deactivate" for payment term            │
│  │                                                               │
│  │  Validation:                                                  │
│  │  • Term exists in DB                                          │
│  │  • Term is ACTIVE (cannot deactivate already INACTIVE)        │
│  │  • Term is NOT default (cannot deactivate default)            │
│  │  • Term has NO associated active invoices                     │
│  │                                                               │
│  │  If ANY validation fails → Return appropriate error:          │
│  │  • 409 CANNOT_DEACTIVATE_DEFAULT if term is default           │
│  │  • 409 HAS_ASSOCIATED_INVOICES if invoices use this term       │
│  │  • 409 ALREADY_INACTIVE if already INACTIVE                   │
│  │                                                               │
│  │  If all pass → Proceed with deactivation                      │
│  │                                                               │
│  │  Action: PaymentTerm.status = INACTIVE                        │
│  │  │                                                             │
│  │  2. SQLAlchemyRepository.update() persists status change       │
│  │  3. AuditLogService.append_event():                           │
│  │     • DEACTIVATE event with SHA-256 checksum                  │
│  │     • Fields: actor, reason, old_status="ACTIVE",             │
│  │       new_status="INACTIVE"                                   │
│  │                                                               │
│  │  4. HTTP 200 + "Payment term deactivated" returned            │
│  │                                                               │
│  └───────────────────────────────────────────────────────────────┘
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **Soft Delete**: Row preserved in DB; status=INACTIVE; 10-year retention
- **Cannot Deactivate Default**: Must unset default first (set another term or remove default)
- **Cannot Deactivate with Invoices**: Must reassign invoices to other payment terms first
- **Audit Trail**: DEACTIVATE event with checksum in audit_log for 10 years

---

### 4.5 Deactivate Series with Issued Documents Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEACTIVATE SERIES WITH DOCUMENTS           │
│  (Preserve issued document numbers for audit/retention)         │
├─────────────────────────────────────────────────────────────────┤
│  TRIGGER: User selects "Deactivate" for numbering series        │
│  │                                                               │
│  │  Validation:                                                  │
│  │  • Series exists in DB                                        │
│  │  • Series is ACTIVE (cannot deactivate already INACTIVE)      │
│  │  • Series has NO issued documents (check invoice table)       │
│  │    - Query: SELECT COUNT(*) FROM invoices WHERE               │
│  │      document_number LIKE {{prefix}}%                         │
│  │    - If COUNT > 0 → Block deactivation                        │
│  │                                                               │
│  │  If validation fails → Return error:                          │
│  │  • 409 HAS_ISSUED_DOCUMENTS if series has issued documents    │
│  │  • 409 ALREADY_INACTIVE if already INACTIVE                   │
│  │                                                               │
│  │  If validation passes → Proceed with deactivation:             │
│  │                                                               │
│  │  Action: Series.is_active = FALSE                             │
│  │  │                                                             │
│  │  2. SQLAlchemyRepository.update() persists status change       │
│  │  3. AuditLogService.append_event():                           │
│  │     • DEACTIVATE event with SHA-256 checksum                  │
│  │     • Fields: actor, reason, old_status="ACTIVE",             │
│  │       new_status="INACTIVE", has_issued_docs=TRUE             │
│  │                                                               │
│  │  4. HTTP 200 + "Series deactivated (with existing docs)"      │
│  │                                                               │
│  └───────────────────────────────────────────────────────────────┘
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **Preservation**: Existing document numbers preserved for 10-year retention
- **Cannot Deactivate with Issued Docs**: Must keep series active; create new series for future documents
- **Audit Trail**: DEACTIVATE event with checksum and has_issued_docs flag in audit_log

---

## 5. Data Flow Summary Table

| Data Flow | Input | Key Validations | Output | Audit |
|-----------|-------|-----------------|--------|-------|
| PT Creation | POST /payment-terms | company_id exists, name unique, due_days>=1, actor+reason | 201 + term JSON | CREATE event + SHA-256 |
| Series Creation | POST /series | prefix GDT format, unique, <15 active, actor+reason | 201 + series JSON | CREATE event + SHA-256 |
| Sequence Increment | POST /series/{id}/increment | series ACTIVE, next_seq<max_seq | 200 + document_number | INCREMENT event + SHA-256 |
| Set Default (SOD) | POST /terms/{id}/set-default | term ACTIVE, no current default, 2-actor | 200 + updated term | 2 checksums in audit |
| Activate Series (SOD) | POST /series/{id}/activate | series INACTIVE, <15 active, 2-actor | 200 + activated series | 2 checksums in audit |
| PT Deactivate | POST /terms/{id}/deactivate | term ACTIVE, not default, no invoices | 200 + deactivated | DEACTIVATE event + SHA-256 |
| Series Deactivate | POST /series/{id}/deactivate | series ACTIVE, no issued docs | 200 + deactivated | DEACTIVATE event + SHA-256 |
| List PT | GET /payment-terms | company_id filter (optional) | 200 + array | QUERY event (if configured) |
| List Series | GET /series | company_id filter (optional) | 200 + array | QUERY event (if configured) |