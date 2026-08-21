# Specs — Payment Terms & Document Numbering Module

## 1. Module Overview

**Module:** Payment Terms & Document Numbering  
**Version:** 1.0.0  
**Status:** PARTIALLY IMPLEMENTED (document numbering exists, payment terms need implementation)  
**Base Framework:** Flask + SQLAlchemy 2.0 + Flask-Login (Flask built-in RBAC — no pycasbin)
**Architecture:** Lego Brick (`src/bricks/payment_terms/`) with pure Python domain, port interfaces, SQLAlchemy storage adapters, and Flask blueprint adapters
**Integration:** Invoice module (add payment_terms_id FK), System Settings (e-invoice series extension)

---

# Payment Terms & Document Numbering Module (Lego Brick)
_Brick: `src/bricks/payment_terms/`. Pure Python domain. Flask built-in RBAC. SQLite3 default DB._

## 1.1 Brick Position

```
src/bricks/
  payment_terms/               ← 🧱 NEW brick
    contract.py                ← 🔌 Public interface (PaymentTermCode, DocumentNumberingCode, primitive IDs only)
    domain.py                  ← 🎯 PaymentTerm, DocumentNumberingSeries entities (pure Python)
    services.py                ← ⚙️ PaymentTermService, DocumentNumberingSeriesService
    storage.py                 ← 💾 SQLAlchemy models + repository adapters
    web_adapter.py             ← 🌐 Flask blueprint + REST endpoints (payment_terms_bp)
```

**Brick boundaries:**
- `domain.py` — pure Python; NO Flask, NO SQLAlchemy, NO flask_login imports
- `contract.py` — public interface; accepts/returns only `str`, `int`, `float`, `dict`, `Decimal`, `UUID`
- `storage.py` — SQLAlchemy models + repo adapters (the ONLY file with SQLAlchemy imports)
- `services.py` — orchestration with injected port; no Flask/SQLAlchemy imports
- `web_adapter.py` — Flask blueprint; `@login_required` + `current_user.role` checks (no Casbin)

---

## 2. Data Model

### 2.1 PaymentTerm Model (Database: `payment_terms`)

| Field | Type | Nullable | Index | Description |
|-------|------|----------|-------|-------------|
| `id` | UUID | NO | PK | Primary key |
| `company_id` | UUID (FK → companies.id) | NO | INDEX | Tenant isolation |
| `name` | VARCHAR(200) | NO | — | Payment term name (e.g., "Net 30", "Thanh toán 15 ngày") |
| `due_days` | INTEGER | NO | DEFAULT 30 | Number of days for payment (e.g., 30 for Net 30) |
| `interest_rate` | NUMERIC(18,6) | NO | DEFAULT 0.00 | Interest rate for overdue payment (VND) |
| `is_default` | BOOLEAN | NO | DEFAULT FALSE | Default payment term per company |
| `status` | ENUM (ACTIVE/INACTIVE) | NO | DEFAULT ACTIVE | Status |
| `checksum` | VARCHAR(64) | NO | SHA-256 | Audit checksum chaining |
| `created_at` | DATE | NO | DEFAULT date.today | Creation date |

**Unique Constraints:**
- `(company_id, is_default) WHERE is_default=TRUE` — only one default per company
- `(company_id, name)` — payment term name must be unique per company

### 2.2 DocumentNumberingSeries Model (Database: `document_numbering_series`)

| Field | Type | Nullable | Index | Description |
|-------|------|----------|-------|-------------|
| `id` | UUID | NO | PK | Primary key |
| `company_id` | UUID (FK → companies.id) | NO | INDEX | Tenant isolation |
| `prefix` | VARCHAR(20) | NO | — | Series prefix (e.g., "HD/", "PK/") per GDT format |
| `next_sequence` | INTEGER | NO | DEFAULT 1 | Auto-incremented number for next document |
| `is_active` | BOOLEAN | NO | DEFAULT TRUE | Whether series is active |
| `max_sequences` | INTEGER | NO | DEFAULT 999999 | Max sequences before reset/alert |
| `status` | ENUM (ACTIVE/INACTIVE) | NO | DEFAULT ACTIVE | Series status |
| `checksum` | VARCHAR(64) | NO | SHA-256 | Audit checksum chaining |
| `created_at` | DATE | NO | DEFAULT date.today | Creation date |

**GDT Compliance (Circular 163/2020/TT-BTC Art. 10):**
- Prefix format: Must follow GDT prescribed format (e.g., "HD/" for invoices, "PN/" for receipts)
- Maximum 15 active series per company
- Sequence must be continuous (no gaps)

**Unique Constraints:**
- `(company_id, prefix)` — one series per prefix per company
- `(company_id, is_active) WHERE is_active=TRUE` — max 1 active per type (configurable)

### 2.3 Integration with Invoice Model

**Existing Invoice Model Enhancement:**
- Add `payment_term_id` FK → `payment_terms.id` (nullable)
- When `payment_term_id` set, auto-calculate `due_date = issue_date + due_days`
- Default payment term from company config applied automatically

---

## 3. Domain Entities

### 3.1 PaymentTerm (src/bricks/payment_terms/domain.py)

```python
@dataclass
class PaymentTerm:
    """Payment term aggregate root with invariants per Circular 99/2025/TT-BTC."""
    
    id: UUID
    company_id: UUID
    name: str
    due_days: int  # Số ngày trả nợ (ví dụ: 30 cho Net 30)
    interest_rate: Decimal  # Lãi suất trễ thanh toán (VND)
    is_default: bool = False
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: date = field(default_factory=date.today)
    checksum: str = ""  # SHA-256 for audit trail
    
    def calculate_due_date(self, issue_date: date) -> date:
        """Calculate due date = issue_date + due_days (business days)."""
        # Simple implementation: add due_days to issue_date
        # Advanced: skip weekends/holidays per business rule
        return issue_date + timedelta(days=self.due_days)
    
    def can_set_as_default(self) -> bool:
        """Check if this term can be set as default (R-005)."""
        # Business rule: only one default per company
        return True  # Enforced in service/repo
```

### 3.2 DocumentNumberingSeries (src/bricks/payment_terms/domain.py)

```python
@dataclass
class DocumentNumberingSeries:
    """Document numbering series aggregate root per GDT Circular 163/2020/TT-BTC."""
    
    TT163_PREFIX_PATTERN = r"^[A-Z]{2,}/$"  # e.g., "HD/", "PN/", "CV/"
    
    id: UUID
    company_id: UUID
    prefix: str  # Must match TT163_PREFIX_PATTERN
    next_sequence: int  # Số tự động tăng
    is_active: bool = True
    max_sequences: int = 999999
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: date = field(default_factory=date.today)
    checksum: str = ""  # SHA-256 for audit trail
    
    def validate_prefix(self) -> bool:
        """Validate prefix format per GDT Circular 163/2020/TT-BTC Art. 10."""
        return bool(_re.match(self.TT163_PREFIX_PATTERN, self.prefix))
    
    def can_increment(self) -> bool:
        """Check if next_sequence can be incrementated (under max_sequences)."""
        return self.next_sequence < self.max_sequences
    
    def increment_sequence(self) -> int:
        """Atomically increment next_sequence by 1."""
        self.next_sequence += 1
        return self.next_sequence
```

---

## 4. Contract Interface

### 4.1 PaymentTermRepositoryPort (src/bricks/payment_terms/contract.py)

```python
class PaymentTermRepositoryPort(Protocol):
    """Repository port for PaymentTerm entities."""
    
    def get_by_id(self, payment_term_id: UUID) -> PaymentTerm | None: ...
    def get_by_company(self, company_id: UUID) -> list[PaymentTerm]: ...
    def get_default_by_company(self, company_id: UUID) -> PaymentTerm | None: ...
    def create(self, term: PaymentTerm) -> PaymentTerm: ...
    def update(self, term: PaymentTerm) -> PaymentTerm: ...
    def set_default(self, payment_term_id: UUID, actor: UUID, reason: str) -> PaymentTerm: ...
    def soft_delete(self, payment_term_id: UUID, actor: UUID, reason: str) -> None: ...
    def validate_name_unique(self, company_id: UUID, name: str) -> bool: ...
```

### 4.2 DocumentNumberingSeriesRepositoryPort (src/bricks/payment_terms/contract.py)

```python
class DocumentNumberingSeriesRepositoryPort(Protocol):
    """Repository port for DocumentNumberingSeries entities."""
    
    def get_by_id(self, series_id: UUID) -> DocumentNumberingSeries | None: ...
    def get_by_company(self, company_id: UUID) -> list[DocumentNumberingSeries]: ...
    def get_active_by_company(self, company_id: UUID) -> list[DocumentNumberingSeries]: ...
    def create(self, series: DocumentNumberingSeries) -> DocumentNumberingSeries: ...
    def update(self, series: DocumentNumberingSeries) -> DocumentNumberingSeries: ...
    def activate(self, series_id: UUID, actor: UUID, reason: str) -> DocumentNumberingSeries: ...
    def deactivate(self, series_id: UUID, actor: UUID, reason: str) -> None: ...
    def validate_prefix_unique(self, company_id: UUID, prefix: str) -> bool: ...
    def check_max_series_limit(self, company_id: UUID) -> bool: ...
```

---

## 5. Services Layer

### 5.1 PaymentTermService (src/bricks/payment_terms/services.py)

**Pure Python — NO Flask/SQLAlchemy imports.**

| Method | Required Roles | Description |
|--------|---------------|-------------|
| `get_config(company_id)` | ACCOUNTANT, CHIEF_ACCOUNTANT, AUDITOR, DIRECTOR | Get payment term configuration per company |
| `create_payment_term(name, due_days, interest_rate, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Create new payment term |
| `update_payment_term(term_id, **kwargs, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Update payment term |
| `set_default_payment_term(term_id, actor, reason)` | CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Set as default (SOD: requires 2-actor if changing default) |
| `list_by_company(company_id, status)` | ACCOUNTANT, AUDITOR, DIRECTOR | List payment terms with filters |
| `validate_before_invoice_entry(company_id, issue_date, actor, reason)` | — | Validate before creating invoice entry |

**Key Business Rules (enforced in service):**
- R-001: Only one default payment term per company
- R-002: due_days must be ≥ 1
- R-003: All mutations require actor UUID (D11)
- R-004: AUDITOR read-only (enforced at API layer)
- R-005: 10-year retention: no automatic deletion, soft-deactivate only
- R-006: SHA-256 checksum chaining on all payment term events
- R-012: Due date calculation = issue_date + due_days

### 5.2 DocumentNumberingSeriesService (src/bricks/payment_terms/services.py)

**Pure Python — NO Flask/SQLAlchemy imports.**

| Method | Required Roles | Description |
|--------|---------------|-------------|
| `get_config(company_id)` | ACCOUNTANT, CHIEF_ACCOUNTANT, AUDITOR, DIRECTOR | Get document numbering series configuration |
| `create_numbering_series(prefix, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Create new numbering series |
| `update_numbering_series(series_id, **kwargs, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Update numbering series |
| `activate_series(series_id, actor, reason)` | CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Activate series (SOD: 2-actor if changing active series) |
| `deactivate_series(series_id, actor, reason)` | CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Deactivate series |
| `increment_sequence(series_id, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, DIRECTOR | Increment sequence for document creation |
| `list_by_company(company_id, active)` | ACCOUNTANT, AUDITOR, DIRECTOR | List series with filters |

**Key Business Rules (enforced in service):**
- R-007: Prefix must match GDT format ^[A-Z]{2,}/$ (TT163 compliance)
- R-008: Maximum 15 active series per company (GDT Circular 163/2020/TT-BTC)
- R-009: Series prefix must be unique per company
- R-010: Sequence automation: atomic increment, any failure rolls back
- R-011: 10-year retention: no automatic deletion, soft-deactivate only
- R-012: SHA-256 checksum chaining on all series events

---

## 6. API Endpoints

### 6.1 Payment Terms (src/presentation/api/payment_terms_bp.py)

| Endpoint | Method | Roles | Description |
|----------|--------|-------|-------------|
| `GET /api/v1/payment-terms` | GET | READ_ROLES | List payment terms with filters |
| `POST /api/v1/payment-terms` | POST | WRITE_ROLES | Create payment term |
| `GET /api/v1/payment-terms/<id>` | GET | READ_ROLES | Get payment term by ID |
| `PATCH /api/v1/payment-terms/<id>` | PATCH | WRITE_ROLES | Update payment term |
| `POST /api/v1/payment-terms/<id>/set-default` | POST | DEFAULT_ROLES | Set as default (SOD) |
| `POST /api/v1/payment-terms/<id>/activate` | POST | ACTIVATE_ROLES | Activate payment term |
| `POST /api/v1/payment-terms/<id>/deactivate` | POST | DEACTIVATE_ROLES | Deactivate payment term |

**Role Definitions:**
- `READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")`
- `WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` — AUDITOR read-only
- `DEFAULT_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` — SOD for setting default
- `ACTIVATE_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` — SOD for activation

### 6.2 Document Numbering Series (src/presentation/api/document_numbering_bp.py)

| Endpoint | Method | Roles | Description |
|----------|--------|-------|-------------|
| `GET /api/v1/document-numbering` | GET | READ_ROLES | List numbering series |
| `POST /api/v1/document-numbering` | POST | WRITE_ROLES | Create numbering series |
| `GET /api/v1/document-numbering/<id>` | GET | READ_ROLES | Get series by ID |
| `PATCH /api/v1/document-numbering/<id>` | PATCH | WRITE_ROLES | Update numbering series |
| `POST /api/v1/document-numbering/<id>/activate` | POST | ACTIVATE_ROLES | Activate series (SOD) |
| `POST /api/v1/document-numbering/<id>/deactivate` | POST | DEACTIVATE_ROLES | Deactivate series |
| `POST /api/v1/document-numbering/<id>/increment` | POST | INCREMENT_ROLES | Increment sequence (for document creation) |

---

## 7. Serializers

### 7.1 serialize_payment_term(term) → dict

```python
{
    "id": str(term.id),
    "company_id": str(term.company_id),
    "name": term.name,
    "due_days": term.due_days,
    "interest_rate": float(term.interest_rate),
    "is_default": term.is_default,
    "status": term.status.value,
    "created_at": term.created_at.isoformat(),
    "checksum": term.checksum,
}
```

### 7.2 serialize_document_numbering_series(series) → dict

```python
{
    "id": str(series.id),
    "company_id": str(series.company_id),
    "prefix": series.prefix,
    "next_sequence": series.next_sequence,
    "is_active": series.is_active,
    "max_sequences": series.max_sequences,
    "status": series.status.value,
    "created_at": series.created_at.isoformat(),
    "checksum": series.checksum,
}
```

---

## 8. CASRBAC Role Mappings

| Role | Permissions | Notes |
|------|-------------|-------|
| `ACCOUNTANT` | Read all payment terms/document numbering; create/modify own company's | Full mutation rights (except AUDITOR restriction) |
| `CHIEF_ACCOUNTANT` | All ACCOUNTANT rights + SOD approval authority | Can approve 2nd actor |
| `ADMIN` | All CHIEF_ACCOUNTANT rights + system config | Company-level admin |
| `AUDITOR` | Read-only — cannot mutate any payment terms/document numbering | Read-only enforced by @login_required + service layer |
| `DIRECTOR` | All rights including system admin | Highest level |

**RBAC Enforcement:**
- `@login_required` + `current_user.role` checks on all API routes (Flask built-in)
- Service layer also checks actor permissions (defense in depth)
- AUDITOR role explicitly cannot call mutation APIs
- All mutations require actor UUID (D11) in request body

---

## 9. Audit & Retention

### 9.1 SHA-256 Checksum Chaining

Every mutation (create, update, activate, deactivate) appends a SHA-256 checksum event:

```
checksum = SHA-256(prev_checksum + actor_uuid + timestamp + action + reason + entity_id)
```

- **prev_checksum**: Previous event's checksum (genesis = "0"*64)
- **actor_uuid**: UUID of actor performing the action
- **timestamp**: ISO datetime of the action
- **action**: "CREATE"/"UPDATE"/"ACTIVATE"/"DEACTIVATE"
- **reason**: Free-text reason required on all mutations
- **entity_id**: UUID of the payment term or series entity

**Storage:** Audit log events stored in `audit_log` table (already exists in DB, per Circular 99/2025/TT-BTC).

### 9.2 10-Year Retention (Luật Kế toán 2015 Art. 11)

- All payment term and numbering configurations retained for minimum 10 years from creation date
- **No automatic deletion** — soft-deactivate only (status=Inactive, row preserved)
- Destruction request required via formal process
- Checksum chain ensures tamper-evident audit trail
- Quarterly audit reports generated for retention compliance

### 9.3 System Account Protection

- N/A (no system accounts in this module)

---

## 10. Data Flow Diagrams

### 10.1 Payment Term Creation Flow

```
┌──────────────────┐     POST     ┌─────────────────────┐
│  User Interface  │ ───────────▶ │  Flask API Layer    │
│  (HTMX + Bulma)    │            │  @login_required    │
└──────────────────┘            │  current_user.role  │
                              └─────────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ Validation Layer│
                                 │ (entity + service)│
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ PaymentTermSrv  │
                                 │ (create method) │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │   SQLAlchemy    │
                                 │   Repository    │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ payment_terms   │
                                 │   table in DB   │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ SHA-256 Checksum│
                                 │  append to audit │
                                 │  log (audit_log)│
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │   HTTP Response │
                                 │   201 + JSON    │
                                 └─────────────────┘
```

### 10.2 Document Numbering Series Increment Flow

```
┌──────────────────┐     POST     ┌─────────────────────┐
│  User Interface  │ ───────────▶ │  Flask API Layer    │
│  (HTMX + Bulma)    │            │  @login_required    │
└──────────────────┘            │  current_user.role  │
                              └─────────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ Validation Layer│
                                 │ (series entity) │
                                 │ - validate prefix│
                                 │ - check max seq │
                                 │ - check active  │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ SeriesSrv       │
                                 │ (increment)     │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │   SQLAlchemy    │
                                 │   Repository    │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ document_numbering_series │
                                 │   table in DB   │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ SHA-256 Checksum│
                                 │  audit event    │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │   HTTP Response │
                                 │   200 + JSON    │
                                 └─────────────────┘
```

---

## 11. Workflows

### 11.1 Payment Term Setting as Default Workflow (SOD)

```
START
│
├─→ CHIEF_ACCOUNTANT requests set as default
│   │
├─→ Validate: term is ACTIVE, company has no current default?
│   │   └─ No → 409 HasCurrentDefault, END
│   └─ Yes → continue (status → marked as default request)
│
├─→ System waits for 2nd actor (ACCOUNTANT) approval
│   │
├─→ ACCOUNTANT logs in, sees pending approval
│   │
├─→ ACCOUNTANT reviews and Approves or Rejects
│   │   ├─ APPROVED:
││   │   │   ├─ term.is_default = TRUE
││   │   │   ├─ Checksum 1: SHA-256(prev + chief_actor + now + "DEFAULT_REQUEST" + reason + term_id)
││   │   │   ├─ Checksum 2: SHA-256(prev + accountant_actor + now + "DEFAULT_APPROVE" + reason + term_id)
││   │   │   ├─ Both checksums in audit_log
││   │   │   └─ Return 200 + "Default set success"
││   │   │
││   │   └─ REJECTED:
││   │       ├─ term.is_default remains unchanged
││   │       ├─ Checksum 2: SHA-256(prev + accountant_actor + now + "DEFAULT_REJECT" + reason + term_id)
││   │       └─ Return 409 + "Rejected, default unchanged"
││   │
││   └─ END (either outcome)
│
└─→ END
```

### 11.2 Document Numbering Series Activation Workflow (SOD)

```
START
│
├─→ CHIEF_ACCOUNTANT requests activate series
│   │
├─→ Validate: series prefix valid, company has < 15 active series?
│   │   └─ No → 409 MaxSeriesExceeded, END
│   └─ Yes → continue (status → activated pending 2nd approval)
│
├─→ System waits for 2nd actor (ACCOUNTANT) approval
│   │
├─→ ACCOUNTANT logs in, sees pending approval
│   │
├─→ ACCOUNTANT reviews and Approves or Rejects
│   │   ├─ APPROVED:
││   │   │   ├─ series.is_active = TRUE
││   │   │   ├─ Checksum 1 + Checksum 2 appended
││   │   │   └─ Return 200 + "Series activated"
││   │   │
││   │   └─ REJECTED:
││   │       ├─ series.is_active remains unchanged
││   │       ├─ Checksum 2 appended for rejection
││   │       └─ Return 409 + "Reactivated denied"
││   │
││   └─ END (either outcome)
│
└─→ END
```

### 11.3 Document Creation with Numbering Flow

```
START
│
├─→ User creates invoice → System auto-increments series sequence
│   │
├─→ Validate: series is ACTIVE, next_sequence available?
│   │   └─ No → 409 NoAvailableSequence, END
│   └─ Yes → continue
│
├─→ Increment: next_sequence += 1 (atomic)
│   │
├─→ Generate document number: {{prefix}}{{next_sequence}} (e.g., "HD/000123")
│   │
├─→ Save invoice with: document_number = generated number, payment_term_id = ...
│   │
├─→ Append SHA-256 checksum for sequence increment event
│   │
├─→ Return document number to user
│   │
└─→ END
```

---

## 12. Exception Paths

| Exception ID | Scenario | Error Code | HTTP Status | Response |
|--------------|----------|------------|-------------|----------|
| EX-001 | Actor UUID (D11) missing from request | MISSING_ACTOR | 400 | `{"error": "actor là bắt buộc", "code": "MISSING_ACTOR"}` |
| EX-002 | Payment term name already exists for company | DUPLICATE_PAYMENT_TERM | 409 | `{"error": "Tên đã tồn tại", "code": "DUPLICATE_PAYMENT_TERM"}` |
| EX-003 | Cannot set default: company already has default payment term | DEFAULT_ALREADY_EXISTS | 409 | `{"error": "Doanh nghiệp đã códefault", "code": "DEFAULT_ALREADY_EXISTS"}` |
| EX-004 | Series prefix not matching GDT format | INVALID_SERIES_PREFIX | 422 | `{"error": "Định dạng prefix không hợp lệ", "code": "INVALID_SERIES_PREFIX"}` |
| EX-005 | Maximum 15 active series exceeded | MAX_SERIES_EXCEEDED | 409 | `{"error": "Đã đạt giới hạn 15 series active", "code": "MAX_SERIES_EXCEEDED"}` |
| EX-006 | Series sequence at maximum (999999) | SEQUENCE_AT_MAX | 409 | `{"error": "Số tiếp theo đã đạt giới hạn", "code": "SEQUENCE_AT_MAX"}` |
| EX-007 | AUDITOR attempting mutation operation | AUDITOR_READ_ONLY | 403 | `{"error": "AUDITOR chỉ đọc", "code": "AUDITOR_READ_ONLY"}` |
| EX-008 | Series not ACTIVE, cannot increment sequence | SERIES_INACTIVE | 409 | `{"error": "Series không phải ACTIVE", "code": "SERIES_INACTIVE"}` |
| EX-009 | Invoice creation fails: no payment term set | NO_PAYMENT_TERM | 400 | `{"error": "Chưa có payment term", "code": "NO_PAYMENT_TERM"}` |
| EX-010 | Company not found | COMPANY_NOT_FOUND | 404 | `{"error": "Doanh nghiệp không tồn tại", "code": "NOT_FOUND"}` |

---

## 13. Happy Paths

| ID | Scenario | Steps |
|----|----------|-------|
| HP-001 | Create payment term | 1. User logs in with ACCOUNTANT role<br>2. POST /api/v1/payment-terms with: company_id, name="Net 30", due_days=30, interest_rate=0<br>3. Response 201 with payment term details<br>4. SHA-256 checksum appended to audit log |
| HP-002 | Set default payment term (SOD) | 1. Chief Accountant requests set as default<br>2. ACCOUNTANT logs in as 2nd actor, approves<br>3. Response 200 with updated payment term is_default=TRUE<br>4. Both actors logged in audit chain |
| HP-003 | Create numbering series | 1. User logs in with CHIEF_ACCOUNTANT role<br>2. POST /api/v1/document-numbering with: prefix="HD/", name="Hóa đơn"<br>3. Response 201 with series details<br>4. next_sequence initialized to 1 |
| HP-004 | Increment sequence for invoice | 1. User creates invoice<br>2. System auto-increments series next_sequence from 0 to 1<br>3. Document number generated: "HD/0001"<br>4. Invoice saved with document_number="HD/0001"<br>5. Audit log entry with checksum |
| HP-004 | Set default payment term | 1. Chief Accountant requests set as default<br>2. ACCOUNTANT approves<br>3. All company's invoices now use this default payment term<br>4. Audit chain: both actors logged |

---

## 14. Alternative Paths

| ID | Scenario | Divergence | Resolution |
|----|----------|------------|------------|
| AP-001 | Create payment term with duplicate name | Validation fails at service layer | Return 409 DUPLICATE_PAYMENT_TERM, user must use different name |
| AP-002 | Create series with prefix already exist | Validation fails at repo layer | Return 409 PREFIX_ALREADY_EXISTS, user must use different prefix |
| AP-003 | Set default when company already has default | Service layer blocks | Return 409 DEFAULT_ALREADY_EXISTS, must replace existing first |
| AP-003 | Create series when company has 15 active series | Service layer blocks | Return 409 MAX_SERIES_EXCEEDED, must deactivate existing series first |
| AP-004 | Increment sequence when series at max | Service layer blocks | Return 409 SEQUENCE_AT_MAX, must deactivate/create new series |
| AP-005 | AUDITOR tries to create payment term | CASRBAC blocks at decorator + service layer | Return 403 AUDITOR_READ_ONLY |
| AP-006 | Activate series when company already at 15 active | Service layer blocks | Return 409 MAX_SERIES_EXCEEDED, must deactivate existing series |
| AP-007 | Increment sequence on inactive series | Service layer blocks | Return 409 SERIES_INACTIVE, must activate series first |
| AP-008 | Invoice creation with no payment term set | Optional flow | System applies company's default payment term auto, or prompts user to set one |

---

## 14. Rules Summary

| Rule ID | Rule Description | Enforced By |
|---------|-----------------|-------------|
| R-001 | Every company can have only ONE default payment term | Service layer + DB unique constraint (company_id + is_default) |
| R-002 | Payment term due_days must be ≥ 1 day | Entity validation on create |
| R-003 | All mutations require actor UUID (D11) in request body | API decorator + service layer entry check |
| R-004 | All mutations require non-empty reason string | API decorator + service layer validation |
| R-005 | AUDITOR role is read-only; cannot create/update/delete payment terms/document numbering | @login_required + current_user.role + service layer check |
| R-006 | 10-year retention: no automatic deletion, soft-deactivate only | Service layer + audit log policy |
| R-007 | Series prefix must match GDT format: ^[A-Z]{2,}/$ (TT163 compliance) | Entity validation on create |
| R-008 | Maximum 15 active document numbering series per company (GDT Circular 163/2020/TT-BTC) | Service layer + DB constraint |
| R-009 | Series prefix must be unique per company | DB unique constraint + service validation |
| R-010 | SHA-256 checksum chaining on all payment term/series events | Service layer append_checksum() |
| R-011 | SOD (Separation of Duties): setting default/activating series requires 2 actors | Service layer + @login_required + current_user.role |
| R-012 | Due date calculation: issue_date + due_days (business days optional) | PaymentTermService.calculate_due_date() |
| R-013 | When creating invoice, apply payment terms due date auto-calculation | Invoice module integration (add payment_terms_id FK) |

---

## 14. Dependencies

### 14.1 Internal Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `Invoice` | Must exist | Payment terms apply to invoices; add payment_terms_id FK |
| `User` / Actor UUID | Must exist | All mutations must include actor UUID (D11) |
| `Company` | Must exist | Payment terms/series belong to a company (company_id FK) |
| `AuditLogService` | Required | All events logged via audit_log_service.append_event() |
| `Flask-Login RBAC` | Required | @login_required + current_user.role on all API routes |
| `SQLAlchemyRepository` | Required | DB adapters for PaymentTerm, DocumentNumberingSeries |

### 14.2 External Dependencies

| Dependency | Version | Description |
|------------|---------|-------------|
| `flask` | >= 3.0 | Web framework |
| `flask-sqlalchemy` | >= 3.0 | ORM (SQLAlchemy 2.0) |
| `pycasbin` | ❌ Removed | RBAC via Flask built-in only |
| `sqlalchemy` | >= 2.0 | SQL toolkit |
| `python-dotenv` | >= 1.0 | Environment config |
| `flask-migrate` | >= 4.0 | Database migration management |

### 14.3 DB Migration (New: `a1b2c3d4e5f6_payment_terms_module.py`)

Creates 2 new tables:
1. `payment_terms` — payment term definitions
2. `document_numbering_series` — document numbering series (extends existing e-invoice series)

**Dependencies on existing schema:**
- `company` table (already exists, companies.id FK)
- `audit_log` table (already exists, applied in system settings migration)
- `invoice` table (already exists, add payment_term_id FK)

---

## 15. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Payment term list (100+ records) | < 2s | `pytest --bench` or manual timing |
| Payment term create | < 500ms | Unit test timing |
| Numbering series create | < 500ms | Unit test timing |
| Sequence increment | < 200ms | Unit test timing |
| API response time (P95) | < 500ms | Flask profiler |
| Database query count (list) | < 3 queries | SQLAlchemy count |

---

## 16. Security Requirements

| Requirement | Detail |
|-------------|--------|
| **Data isolation** | All payment term/series data scoped by company_id (tenant isolation) |
| **Actor audit** | Every mutation must include actor UUID (D11), logged in audit_log |
| **SOD enforcement** | Critical operations (setting default, activating series) require 2-actor approval |
| **AUDITOR read-only** | AUDITOR cannot call any mutation API endpoint |
| **Prefix validation** | All prefix values validated against GDT regex ^[A-Z]{2,}/$ |
| **Input validation** | All fields validated at entity layer (format, length, regex) |
| **XSS prevention** | Names, prefixes escaped in API responses |
| **CSRF protection** | Protected by Flask-WTF/HTMX pattern (existing in codebase) |
| **Rate limiting** | Configured at Flask level (existing pattern from other blueprints) |
| **HTTPS enforcement** | Flask-Talisman when DEBUG=False (existing pattern) |

---