# Specs — Bank & Cash Accounts Module

## 1. Module Overview

**Module:** Bank & Cash Accounts  
**Version:** 1.0.0  
**Status:** PRODUCTION READY  
**Base Framework:** Flask + SQLAlchemy 2.0 + Flask-Login (Flask built-in RBAC — no pycasbin)
**Architecture:** Lego Brick (`src/bricks/bank_cash/`) with pure Python domain, port interfaces, SQLAlchemy storage adapters, and Flask blueprint adapters

---

# Bank & Cash Accounts Module (Lego Brick)
_Brick: `src/bricks/bank_cash/`. Pure Python domain. Flask built-in RBAC. SQLite3 default DB._

## 1.1 Brick Position

```
src/bricks/
  bank_cash/                   ← 🧱 NEW brick
    contract.py                ← 🔌 Public interface (BankAccountCode, CashAccountCode, primitive IDs only)
    domain.py                  ← 🎯 BankAccount, CashAccount, BankReconciliation entities (pure Python)
    services.py                ← ⚙️ BankAccountService, CashAccountService, BankReconciliationService
    storage.py                 ← 💾 SQLAlchemy models + repository adapters
    web_adapter.py             ← 🌐 Flask blueprint + REST endpoints (bank_cash_bp)
```

**Brick boundaries:**
- `domain.py` — pure Python; NO Flask, NO SQLAlchemy, NO flask_login imports
- `contract.py` — public interface; accepts/returns only `str`, `int`, `float`, `dict`, `Decimal`, `UUID`
- `storage.py` — SQLAlchemy models + repo adapters (the ONLY file with SQLAlchemy imports)
- `services.py` — orchestration with injected port; no Flask/SQLAlchemy imports
- `web_adapter.py` — Flask blueprint; `@login_required` + `current_user.role` checks (no Casbin)

---

## 2. Data Model

### 2.1 BankAccount Model (Database: `bank_accounts`)

| Field | Type | Nullable | Index | Description |
|-------|------|----------|-------|-------------|
| `id` | UUID | NO | PK | Primary key |
| `company_id` | UUID (FK → companies.id) | NO | INDEX | Tenant isolation |
| `bank_name` | VARCHAR(100) | NO | — | Bank name (e.g., "VietinBank", "Sacombank") |
| `account_number` | VARCHAR(30) | NO | INDEX | Account number (per bank's format) |
| `account_holder` | VARCHAR(255) | NO | — | Name of account holder |
| `branch` | VARCHAR(200) | NO | DEFAULT "" | Branch name/code |
| `is_primary` | BOOLEAN | NO | DEFAULT FALSE | Primary bank account per company |
| `created_at` | DATE | NO | DEFAULT date.today | Creation date |
| `checksum` | VARCHAR(64) | NO | SHA-256 | Audit checksum chaining |
| `status` | ENUM (ACTIVE/SUSPENDED/CLOSED) | NO | DEFAULT ACTIVE | Account status |

**Unique Constraints:**
- `(company_id, account_number)` — one account number per company
- `(company_id, is_primary)` where is_primary=TRUE — only one primary per company

### 2.2 CashAccount Model (Database: `cash_accounts`)

| Field | Type | Nullable | Index | Description |
|-------|------|----------|-------|-------------|
| `id` | UUID | NO | PK | Primary key |
| `company_id` | UUID (FK → companies.id) | NO | INDEX | Tenant isolation |
| `code` | VARCHAR(20) | NO | UNIQUE | Cash code (per TT99 format: ^[1-9]\d{2}$ or ^[1-9]\d{3}$) |
| `name` | VARCHAR(200) | NO | — | Cash account name (e.g., "Tiêu hối Tổng Kho") |
| `opening_balance` | NUMERIC(18,2) | NO | DEFAULT 0.00 | Opening balance at creation |
| `current_balance` | NUMERIC(18,2) | NO | DEFAULT 0.00 | Current balance (updated by transactions) |
| `is_system` | BOOLEAN | NO | DEFAULT FALSE | System cash account (protected) |
| `checksum` | VARCHAR(64) | NO | SHA-256 | Audit checksum chaining |
| `status` | ENUM (ACTIVE/LOCKED/CLOSED) | NO | DEFAULT ACTIVE | Account status |

**Unique Constraints:**
- `(company_id, code)` — one cash code per company

### 2.3 Bank Reconciliation Model (Database: `bank_reconciliations`)

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `company_id` | UUID (FK → companies.id) | NO | INDEX |
| `bank_account_id` | UUID (FK → bank_accounts.id) | NO | — |
| `reconciliation_date` | DATE | NO | — |
| `statement_balance` | NUMERIC(18,2) | NO | Balance per bank statement |
| `internal_balance` | NUMERIC(18,2) | NO | Balance per internal records |
| `difference` | NUMERIC(18,2) | NO | statement_balance - internal_balance |
| `is_resolved` | BOOLEAN | NO | DEFAULT FALSE |
| `resolved_at` | DATE | YES | Date resolved |
| `checksum` | VARCHAR(64) | NO | SHA-256 |
| `created_by` | UUID | NO | Actor UUID (D11) |
| `approved_by` | UUID | YES | 2nd actor for SOD approval |

---

## 3. Domain Entities

### 3.1 BankAccount (src/bricks/bank_cash/domain.py)

```python
@dataclass
class BankAccount:
    """Bank account entity with audit checksum chaining."""
    id: UUID
    company_id: UUID
    bank_name: str
    account_number: str
    account_holder: str
    branch: str = ""
    is_primary: bool = False
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: date = field(default_factory=date.today)
    checksum: str = ""  # SHA-256, chained from previous
    
    def validate_code(self) -> None:
        """Validate account number format per bank standards."""
        if not self.account_number.strip():
            raise BankAccountError("Số tài khoản không được rỗng")
        if len(self.account_number) > 30:
            raise BankAccountError("Số tài khoản vượt quá 30 ký tự")
    
    def set_primary(self, actor: UUID, reason: str) -> None:
        """Set this as primary bank account (requires SOD approval)."""
        # Business rule: only one primary per company
        if not CompanyRepository.is_primary_available(self.company_id):
            raise BankAccountError("Doanh nghiệp đã có tài khoản chính")
        # ... set primary logic
    
    def can_modify(self, actor: UUID) -> bool:
        """Check if actor can modify this account."""
        if CompanyConfig.is_system_account(self.company_id, self.id):
            return False  # System account protection
        if self.status == AccountStatus.CLOSED:
            return False
        return True
```

### 3.2 CashAccount (src/bricks/bank_cash/domain.py)

```python
@dataclass
class CashAccount:
    """Cash on hand entity with balance tracking."""
    id: UUID
    company_id: UUID
    code: AccountCode  # TT99 format validation
    name: str
    opening_balance: Decimal  # VND, 2 decimal places
    current_balance: Decimal  # VND, 2 decimal places, defaults to opening_balance
    is_system: bool = False
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: date = field(default_factory=date.today)
    checksum: str = ""  # SHA-256, chained from previous
    
    def validate_code(self) -> None:
        """Validate cash code per TT99 format."""
        # ^[1-9]\d{2}$ or ^[1-9]\d{3}$ (Vietnamese chart of accounts)
        pattern = r"^[1-9]\d{2}$|^[1-9]\d{3}$"
        if not re.match(pattern, self.code):
            raise CashAccountError(f"Mã số không hợp lệ: {self.code}. Định dạng: ^[1-9]\\d{{2}}$ hoặc ^[1-9]\\d{{3}}$")
    
    def update_balance(self, amount: Decimal, actor: UUID, reason: str) -> None:
        """Update cash balance with SOD-tracked mutation."""
        if self.status == AccountStatus.CLOSED:
            raise CashAccountError("Không thể cập nhật trên tài khoản đã đóng")
        if self.is_system and not actor_is_chief_accountant(actor):
            raise CashAccountError("Tài khoản hệ thống không được sửa đổi")
        self.current_balance = (self.current_balance or Decimal("0")) + amount
        # ... append audit event
```

### 3.3 BankReconciliation (src/bricks/bank_cash/domain.py)

```python
@dataclass
class BankReconciliation:
    """Bank reconciliation entity with SOD approval."""
    id: UUID
    company_id: UUID
    bank_account_id: UUID
    reconciliation_date: date
    statement_balance: Decimal  # From bank statement
    internal_balance: Decimal  # From internal records
    difference: Decimal  # statement_balance - internal_balance
    is_resolved: bool = False
    resolved_at: Optional[date] = None
    resolved_by: Optional[UUID] = None
    checksum: str = ""  # SHA-256 chaining
    
    def is_balanced(self, tolerance: Decimal = Decimal("0.01")) -> bool:
        """Check if reconciliation is balanced within tolerance."""
        return abs(self.difference) <= tolerance
```

---

## 4. Contract Interface

### 4.1 BankAccountRepositoryPort (src/bricks/bank_cash/contract.py)

```python
class BankAccountRepositoryPort(Protocol):
    """Repository port for BankAccount entities."""
    
    def get_by_id(self, bank_account_id: UUID) -> BankAccount | None: ...
    def get_by_company(self, company_id: UUID) -> list[BankAccount]: ...
    def get_primary_by_company(self, company_id: UUID) -> BankAccount | None: ...
    def create(self, account: BankAccount) -> BankAccount: ...
    def update(self, account: BankAccount) -> BankAccount: ...
    def soft_delete(self, bank_account_id: UUID, actor: UUID, reason: str) -> None: ...
    def validate_code_unique(self, company_id: UUID, account_number: str) -> bool: ...
```

### 4.2 CashAccountRepositoryPort (src/bricks/bank_cash/contract.py)

```python
class CashAccountRepositoryPort(Protocol):
    """Repository port for CashAccount entities."""
    
    def get_by_id(self, cash_account_id: UUID) -> CashAccount | None: ...
    def get_by_company(self, company_id: UUID) -> list[CashAccount]: ...
    def get_active_by_company(self, company_id: UUID) -> list[CashAccount]: ...
    def create(self, account: CashAccount) -> CashAccount: ...
    def update_balance(self, cash_account_id: UUID, amount: Decimal, actor: UUID, reason: str) -> CashAccount: ...
    def soft_close(self, cash_account_id: UUID, actor: UUID, reason: str) -> None: ...
    def validate_code_unique(self, company_id: UUID, code: str) -> bool: ...
```

### 4.3 BankReconciliationRepositoryPort (src/bricks/bank_cash/contract.py)

```python
class BankReconciliationRepositoryPort(Protocol):
    """Repository port for BankReconciliation entities."""
    
    def get_by_id(self, reconciliation_id: UUID) -> BankReconciliation | None: ...
    def get_unresolved_by_company(self, company_id: UUID) -> list[BankReconciliation]: ...
    def create(self, reconciliation: BankReconciliation) -> BankReconciliation: ...
    def update(self, reconciliation: BankReconciliation) -> BankReconciliation: ...
    def resolve(self, reconciliation_id: UUID, approver: UUID, reason: str) -> BankReconciliation: ...
```

---

## 5. Services Layer

### 5.1 BankAccountService (src/bricks/bank_cash/services.py)

**Pure Python — NO Flask/SQLAlchemy imports.**

| Method | Required Roles | Description |
|--------|---------------|-------------|
| `get_config(company_id)` | ACCOUNTANT, CHIEF_ACCOUNTANT, AUDITOR, DIRECTOR | Get bank account configuration per company |
| `create_bank_account(code, name, bank_name, account_number, account_holder, branch, is_primary, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Create new bank account |
| `update_bank_account(bank_account_id, **kwargs, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Update bank account |
| `set_primary(bank_account_id, actor, reason)` | CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Set as primary (SOD) |
| `suspend_bank_account(bank_account_id, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, DIRECTOR | Suspend account |
| `close_bank_account(bank_account_id, actor, reason)` | CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Close account (soft delete) |
| `list_by_company(company_id, status, skip, limit)` | ACCOUNTANT, AUDITOR, DIRECTOR | List bank accounts with filters |
| `validate_before_entry(company_id, bank_account_id, actor, reason)` | — | Validate before creating voucher entry |

**Key Business Rules (enforced in service):**
- Only one primary bank account per company (D11 actor validation)
- System accounts cannot be modified/deleted (CompanyConfig.check_system_account)
- CLOSED status prevents new transactions
- SOD approval required for primary changes and closures
- SHA-256 checksum appended on every mutation

### 5.2 CashAccountService (src/bricks/bank_cash/services.py)

**Pure Python — NO Flask/SQLAlchemy imports.**

| Method | Required Roles | Description |
|--------|---------------|-------------|
| `get_config(company_id)` | ACCOUNTANT, CHIEF_ACCOUNTANT, AUDITOR, DIRECTOR | Get cash account configuration |
| `create_cash_account(code, name, opening_balance, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Create new cash account |
| `update_balance(cash_account_id, amount, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, DIRECTOR | Update cash balance |
| `close_cash_account(cash_account_id, actor, reason)` | CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Close cash account |
| `list_by_company(company_id, status)` | ACCOUNTANT, AUDITOR, DIRECTOR | List cash accounts |
| `validate_before_entry(cash_account_id, actor, reason)` | — | Validate before voucher entry |

**Key Business Rules (enforced in service):**
- Code must match TT99 format ^[1-9]\d{2}$ or ^[1-9]\d{3}$
- System cash accounts protected from modification
- Balance cannot go negative without chief accountant approval
- SOD approval required for closure
- 10-year retention: no automatic deletion, soft-close only
- Current balance = opening_balance + sum of all transactions

### 5.3 BankReconciliationService (src/bricks/bank_cash/services.py)

**Pure Python — NO Flask/SQLAlchemy imports.**

| Method | Required Roles | Description |
|--------|---------------|-------------|
| `create_reconciliation(bank_account_id, statement_date, statement_balance, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, DIRECTOR | Create new reconciliation |
| `update_reconciliation(reconciliation_id, statement_balance, actor, reason)` | ACCOUNTANT, CHIEF_ACCOUNTANT, DIRECTOR | Update reconciliation |
| `resolve_reconciliation(reconciliation_id, resolver, reason)` | CHIEF_ACCOUNTANT, ADMIN, DIRECTOR | Resolve reconciliation (SOD) |
| `list_unresolved(company_id)` | AUDITOR, DIRECTOR | List unresolved reconciliations |
| `list_by_company(company_id, resolved)` | ACCOUNTANT, AUDITOR, DIRECTOR | List reconciliations with filters |

**Key Business Rules (enforced in service):**
- Reconciliation must balance within tolerance 0.01 (D11)
- Unresolved reconciliations older than 365 days flagged for review
- Resolution requires 2nd actor (SOD) for amounts > threshold
- SHA-256 checksum appended on resolve
- Locked periods prevent new reconciliations (Fiscal Year integration)

---

## 6. API Endpoints

### 6.1 Bank Accounts (src/presentation/api/bank_accounts_bp.py)

| Endpoint | Method | Roles | Description |
|----------|--------|-------|-------------|
| `GET /api/v1/bank-accounts` | GET | READ_ROLES | List bank accounts with filters |
| `POST /api/v1/bank-accounts` | POST | WRITE_ROLES | Create bank account |
| `GET /api/v1/bank-accounts/<id>` | GET | READ_ROLES | Get bank account by ID |
| `PATCH /api/v1/bank-accounts/<id>` | PATCH | WRITE_ROLES | Update bank account |
| `POST /api/v1/bank-accounts/<id>/set-primary` | POST | PRIMARY_ROLES | Set as primary (SOD) |
| `POST /api/v1/bank-accounts/<id>/suspend` | POST | SUSPEND_ROLES | Suspend account |
| `POST /api/v1/bank-accounts/<id>/close` | POST | CLOSE_ROLES | Close bank account |
| `GET /api/v1/bank-accounts/<id>/reconciliations` | GET | READ_ROLES | List reconciliations |

**Role Definitions:**
- `READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")`
- `WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` — AUDITOR read-only
- `PRIMARY_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` — SOD for primary change
- `CLOSE_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` — SOD for closure

### 6.2 Cash Accounts (src/presentation/api/cash_accounts_bp.py)

| Endpoint | Method | Roles | Description |
|----------|--------|-------|-------------|
| `GET /api/v1/cash-accounts` | GET | READ_ROLES | List cash accounts |
| `POST /api/v1/cash-accounts` | POST | WRITE_ROLES | Create cash account |
| `GET /api/v1/cash-accounts/<id>` | GET | READ_ROLES | Get cash account by ID |
| `PATCH /api/v1/cash-accounts/<id>` | PATCH | WRITE_ROLES | Update cash account |
| `POST /api/v1/cash-accounts/<id>/close` | POST | CLOSE_ROLES | Close cash account |
| `POST /api/v1/cash-accounts/<id>/transact` | POST | TRANSACT_ROLES | Record transaction |

### 6.3 Bank Reconciliations (src/presentation/api/bank_reconciliations_bp.py)

| Endpoint | Method | Roles | Description |
|----------|--------|-------|-------------|
| `GET /api/v1/reconciliations` | GET | READ_ROLES | List reconciliations |
| `POST /api/v1/reconciliations` | POST | WRITE_ROLES | Create reconciliation |
| `GET /api/v1/reconciliations/<id>` | GET | READ_ROLES | Get reconciliation by ID |
| `PATCH /api/v1/reconciliations/<id>` | PATCH | WRITE_ROLES | Update reconciliation |
| `POST /api/v1/reconciliations/<id>/resolve` | POST | RESOLVE_ROLES | Resolve reconciliation |

---

## 7. Serializers

### 7.1 serialize_bank_account(account) → dict

```python
{
    "id": str(account.id),
    "company_id": str(account.company_id),
    "bank_name": account.bank_name,
    "account_number": account.account_number,
    "account_holder": account.account_holder,
    "branch": account.branch,
    "is_primary": account.is_primary,
    "status": account.status.value,
    "created_at": account.created_at.isoformat(),
    "checksum": account.checksum,
}
```

### 7.2 serialize_cash_account(account) → dict

```python
{
    "id": str(account.id),
    "company_id": str(account.company_id),
    "code": account.code.value,
    "name": account.name,
    "opening_balance": float(account.opening_balance),
    "current_balance": float(account.current_balance),
    "is_system": account.is_system,
    "status": account.status.value,
    "created_at": account.created_at.isoformat(),
    "checksum": account.checksum,
}
```

### 7.3 serialize_reconciliation(reconciliation) → dict

```python
{
    "id": str(reconciliation.id),
    "company_id": str(reconciliation.company_id),
    "bank_account_id": str(reconciliation.bank_account_id),
    "reconciliation_date": reconciliation.reconciliation_date.isoformat(),
    "statement_balance": float(reconciliation.statement_balance),
    "internal_balance": float(reconciliation.internal_balance),
    "difference": float(reconciliation.difference),
    "is_resolved": reconciliation.is_resolved,
    "resolved_at": reconciliation.resolved_at.isoformat() if reconciliation.resolved_at else None,
    "resolved_by": str(reconciliation.resolved_by) if reconciliation.resolved_by else None,
    "checksum": reconciliation.checksum,
}
```

---

## 8. CASRBAC Role Mappings

| Role | Permissions | Notes |
|------|-------------|-------|
| `ACCOUNTANT` | Read all bank/cash; create/modify own company's accounts | Full mutation rights |
| `CHIEF_ACCOUNTANT` | All ACCOUNTANT rights + SOD approval authority | Can approve 2nd actor |
| `ADMIN` | All CHIEF_ACCOUNTANT rights + system config | Company-level admin |
| `AUDITOR` | Read-only — cannot mutate any bank/cash | Read-only enforced by @login_required + service layer |
| `DIRECTOR` | All rights including system admin | Highest level |

**RBAC Enforcement:**
- `@login_required` + `current_user.role` checks on all API routes (Flask built-in)
- Service layer also checks actor permissions (defense in depth)
- AUDITOR role explicitly cannot call mutation APIs
- All mutations require actor UUID (D11) in request body

---

## 9. Audit & Retention

### 9.1 SHA-256 Checksum Chaining

Every mutation (create, update, close, reconcile, resolve) appends a SHA-256 checksum event:

```
checksum = SHA-256(prev_checksum + actor_uuid + timestamp + action + reason + entity_id)
```

- **prev_checksum**: Previous event's checksum (genesis = "0"*64)
- **actor_uuid**: UUID of actor performing the action
- **timestamp**: ISO datetime of the action
- **action**: "CREATE"/"UPDATE"/"CLOSE"/"RESOLVE"
- **reason**: Free-text reason required on all mutations
- **entity_id**: UUID of the bank/cash/reconciliation entity

**Storage:** Audit log events stored in `audit_log` table (already exists in DB, per Circular 99/2025/TT-BTC).

### 9.2 10-Year Retention (Luật Kế toán 2015 Art. 11)

- All bank/cash documents retained for minimum 10 years from creation date
- **No automatic deletion** — soft-close only (status=Closed, row preserved)
- Destruction request required via `/api/audit-log/destroy` endpoint
- Checksum chain ensures tamper-evident audit trail
- Quarterly audit reports generated for retention compliance

### 9.3 System Account Protection

- System-identified bank/cash accounts (e.g., VND treasury, main operating account) marked `is_system=TRUE`
- System accounts cannot be modified or deleted via API
- Modification attempts logged as security events
- Only chief accountant can request system account changes via formal process

---

## 10. Data Flow Diagrams

### 10.1 Bank Account Creation Flow

```
┌─────────────┐     POST /api/v1/bank-accounts     ┌─────────────────────┐
│  User UI    │ ──────────────────────────────────▶ │  API Bank Account   │
└─────────────┘                                  │  Service Layer     │
                                              │ • Validate actor   │
                                              │ • Validate code    │
                                              │ • Check SOD rules  │
                                              │ • Create repo      │
                                              │ • Append checksum  │
                                              │ • Return response  │
                                              └─────────────────────┘
```

### 10.2 Bank Reconciliation Flow

```
┌─────────────┐     POST /api/v1/reconciliations     ┌─────────────────────┐
│  User UI    │ ──────────────────────────────────▶ │  API Reconciliation │
└─────────────┘                                  │  Service Layer     │
                                              │ • Validate period  │
                                              │ • Check balance    │
                                              │ • Append checksum  │
                                              │ • Create repo      │
                                              └─────────────────────┘
                                              │                       │
                                              ▼                       ▼
                               ┌────────────────────────────────┐
                               │  Bank Statement Import (CAMT)  │
                               └────────────────────────────────┘
```

### 10.3 Cash Transaction Flow

```
┌─────────────┐     POST /api/v1/cash-accounts/transact     ┌─────────────────────┐
│  User UI    │ ───────────────────────────────────────────────▶ │  Cash Account Service│
└─────────────┘                                          │ • Validate balance   │
                                                   │ • Check SOD rules    │
                                                   │ • Update current_Bal │
                                                   │ • Append checksum    │
                                                   │ • Return response    │
                                                   └─────────────────────┘
```

---

## 11. Workflows

### 11.1 Bank Account Creation Workflow

```
START → User fills bank account form → POST /api/v1/bank-accounts
     │
     ├──→ Validate actor UUID (D11) present → PASS/FAIL
     │        FAIL → 400 MISSING_ACTOR
     │
     ├──→ Validate business rules:
     │     • Account number unique per company
     │     • Company exists
     │     • If is_primary, check no other primary exists
     │     • SOD checks based on actor role
     │
     ├──→ PASS → Create BankAccount entity → SQLAlchemy repo → Save → Append SHA-256 checksum
     │        → Return 201 + serialized account
     │
     └──→ FAIL → Return error response (422 validation, 409 conflict)
```

### 11.2 Bank Account Closure Workflow (SOD)

```
START → User requests closure → POST /api/v1/bank-accounts/{id}/close
     │
     ├──→ Validate actor UUID (D11) → PASS/FAIL
     │        FAIL → 400 MISSING_ACTOR
     │
     ├──→ Check if account is CLOSED → PASS/FAIL
     │        → 409 Already closed
     │
     ├──→ Check if account has related transactions → PASS/FAIL
     │        → 409 Cannot close: has related invoices/vouchers
     │
     ├──→ 1st actor (requester) approves → status → SUSPENDED
     │        → Append checksum, log audit event
     │
     ├──→ 2nd actor (approver) reviews → PASS → status → CLOSED
     │        → Append checksum, log audit event
     │        → FAIL → Return to SUSPENDED
     │
     └──→ Complete → Return 200 + closed account
```

### 11.3 Cash Transaction Workflow

```
START → User records cash transaction → POST /api/v1/cash-accounts/{id}/transact
     │
     ├──→ Validate actor UUID (D11) → PASS/FAIL
     │
     ├──→ Check cash account status (must be ACTIVE) → PASS/FAIL
     │
     ├──→ Check system account protection → PASS/FAIL
     │
     ├──→ Update current_balance = current_balance + amount
     ├──→ Append SHA-256 checksum event
     ├──→ Log audit event (actor, amount, reason, new balance)
     └──→ Return 200 + updated cash account
```

### 11.4 Bank Reconciliation Resolution Workflow (SOD)

```
START → User resolves reconciliation → POST /api/v1/reconciliations/{id}/resolve
     │
     ├──→ Validate 1st actor (requester) UUID → PASS/FAIL
     │
     ├──→ Mark reconciliation as "partially resolved" by 1st actor
     │        → Append checksum (1st actor event)
     │
     ├──→ Validate 2nd actor (approver) UUID → PASS/FAIL
     │        → 400 MISSING_ACTOR if absent
     │
     ├──→ 2nd actor reviews difference → PASS → mark "resolved"
     │        → Append checksum (2nd actor event)
     │        → Log final audit event
     │        → Return 200 + resolved reconciliation
     │
     └──→ FAIL → Return error, reconciliation remains unresolved
```

---

## 12. Exception Paths

| Exception ID | Scenario | Error Code | HTTP Status | Response |
|--------------|----------|------------|-------------|----------|
| EX-001 | Actor UUID (D11) missing from request | MISSING_ACTOR | 400 | `{"error": "actor là bắt buộc", "code": "MISSING_ACTOR"}` |
| EX-002 | Account number already exists for company | DUPLICATE_ACCOUNT_NUMBER | 409 | `{"error": "Số tài khoản đã tồn tại", "code": "DUPLICATE_ACCOUNT_NUMBER"}` |
| EX-003 | Cannot set primary: company already has primary | PRIMARY_ALREADY_EXISTS | 409 | `{"error": "Doanh nghiệp đã có tài khoản chính", "code": "PRIMARY_ALREADY_EXISTS"}` |
| EX-004 | System account modification attempted | SYSTEM_ACCOUNT_MODIFICATION_ERROR | 403 | `{"error": "Tài khoản hệ thống không được sửa đổi", "code": "SYSTEM_ACCOUNT_ERROR"}` |
| EX-005 | Cash code not matching TT99 format | INVALID_CASH_CODE | 422 | `{"error": "Mã số không hợp lệ...", "code": "INVALID_CASH_CODE"}` |
| EX-006 | Cash balance would go negative | INSUFFICIENT_BALANCE | 422 | `{"error": "Số dư không đủ", "code": "INSUFFICIENT_BALANCE"}` |
| EX-007 | Bank account CLOSED, cannot perform operation | ACCOUNT_CLOSED | 409 | `{"error": "Tài khoản đã đóng", "code": "ACCOUNT_CLOSED"}` |
| EX-008 | Reconciliation difference exceeds tolerance 0.01 | RECONCILIATION_IMBALANCED | 409 | `{"error": "Phân kỳ không bằng", "code": "RECONCILIATION_IMBALANCED"}` |
| EX-009 | AUDITOR attempting mutation operation | AUDITOR_READ_ONLY | 403 | `{"error": "AUDITOR chỉ đọc", "code": "AUDITOR_READ_ONLY"}` |
| EX-010 | Period locked, cannot create reconciliation | PERIOD_LOCKED_ERROR | 409 | `{"error": "Kỳ đã khóa", "code": "PERIOD_LOCKED"}` |
| EX-011 | Invalid amount (zero or negative without cause) | INVALID_AMOUNT | 422 | `{"error": "Số tiền không hợp lệ", "code": "INVALID_AMOUNT"}` |
| EX-012 | Bank account not found | BANK_ACCOUNT_NOT_FOUND | 404 | `{"error": "Tài khoản không tồn tại", "code": "NOT_FOUND"}` |
| EX-013 | Cash account not found | CASH_ACCOUNT_NOT_FOUND | 404 | `{"error": "Tài khoản tiền mặt không tồn tại", "code": "NOT_FOUND"}` |
| EX-014 | Company not found | COMPANY_NOT_FOUND | 404 | `{"error": "Doanh nghiệp không tồn tại", "code": "NOT_FOUND"}` |
| EX-015 | Reconciliation already resolved | RECONCILIATION_ALREADY_RESOLVED | 409 | `{"error": "Phân kỳ đã giải quyết", "code": "RECONCILIATION_ALREADY_RESOLVED"}` |

---

## 13. Happy Paths

| ID | Scenario | Steps |
|----|----------|-------|
| HP-001 | Create bank account | 1. User logs in with ACCOUNTANT role<br>2. POST /api/v1/bank-accounts with: company_id, bank_name="VietinBank", account_number="123456789", account_holder="Công ty ABC", branch="HQ"<br>3. Response 201 with account details<br>4. SHA-256 checksum appended to audit log |
| HP-002 | Create cash account | 1. User logs in with CHIEF_ACCOUNTANT role<br>2. POST /api/v1/cash-accounts with: code="111", name="Tiêu hối Tổng Kho", opening_balance=50000000<br>3. Response 201 with cash account<br>4. current_balance initialized to opening_balance |
| HP-003 | Record cash transaction | 1. User logs in with ACCOUNTANT role<br>2. POST /api/v1/cash-accounts/{id}/transact with: amount=-1000000 (withdrawal), reason="Mua vật tư"<br>3. Response 200 with updated current_balance<br>4. Audit log entry with checksum |
| HP-004 | Create bank reconciliation | 1. User logs in with CHIEF_ACCOUNTANT role<br>2. POST /api/v1/reconciliations with: bank_account_id, reconciliation_date=2026-08-01, statement_balance=120000000, internal_balance=119500000<br>3. Response 201 with reconciliation<br>4. difference = 500000 (within 0.01 tolerance after rounding) |
| HP-005 | Set primary bank account (SOD) | 1. Chief Accountant logs in, requests primary change<br>2. ACCOUNTANT logs in as 2nd actor, approves the change<br>3. Response 200 with updated bank account is_primary=TRUE<br>4. Both actors logged in audit chain |

---

## 14. Alternative Paths

| ID | Scenario | Divergence | Resolution |
|----|----------|------------|------------|
| AP-001 | Create bank account with duplicate account number | Validation fails at service layer | Return 409 DUPLICATE_ACCOUNT_NUMBER, user must use different account number |
| AP-002 | Create cash account with invalid TT99 code | Validation fails at entity level | Return 422 INVALID_CASH_CODE, user must use valid code per TT99 format |
| AP-003 | Update bank account on system account | Service layer blocks modification | Return 403 SYSTEM_ACCOUNT_MODIFICATION_ERROR, only chief accountant can request change |
| AP-004 | Close cash account with transactions | Service layer prevents closure | Return 409, user must transfer/zero balance first, then close |
| AP-005 | Reconciliation with difference > 0.01 | Validation fails | Return 409 RECONCILIATION_IMBALANCED, user must investigate and adjust |
| AP-006 | AUDITOR tries to create bank account | CASRBAC blocks at decorator + service layer | Return 403 AUDITOR_READ_ONLY |
| AP-007 | Set primary without SOD approval | Service layer enforces 2-actor rule | Return 403, need 2nd actor approval |
| AP-008 | Import bank statements (CAMT) - partial failure | Import is atomic: all-or-nothing | If any row fails, entire import rejected, no partial data saved |

---

## 15. Rules Summary

| Rule ID | Rule Description | Enforced By |
|---------|-----------------|-------------|
| R-001 | Every company can have only ONE primary bank account | Service layer + DB unique constraint (company_id + is_primary) |
| R-002 | Cash code must match TT99 format: ^[1-9]\d{2}$ or ^[1-9]\d{3}$ | Entity validation on create |
| R-003 | Bank account account_number must be unique per company | DB unique constraint + service validation |
| R-004 | All mutations require actor UUID (D11) in request body | API decorator + service layer |
| R-005 | All mutations require non-empty reason string | API decorator + service layer validation |
| R-006 | AUDITOR role is read-only; cannot create/update/delete bank/cash | @login_required + current_user.role + service layer check |
| R-007 | System accounts (is_system=TRUE) cannot be modified or deleted | CompanyConfig.check_system_account() |
| R-008 | Bank reconciliation must balance within tolerance 0.01 | BankReconciliation.is_balanced(tolerance=0.01) |
| R-009 | 10-year retention: no automatic deletion, soft-close only | Service layer + audit log policy |
| R-010 | SHA-256 checksum chaining on all bank/cash/reconciliation events | Service layer append_checksum() |
| R-011 | SOD (Separation of Duties): closure/primary change requires 2 actors | Service layer + @login_required + current_user.role |
| R-012 | Currency on bank account must be valid ISO 4217 code ^[A-Z]{3}$ | Service layer validation |
| R-013 | Period locked prevents new reconciliations (FY integration) | PeriodLockService.check_fiscal_year_lock() |
| R-014 | Cash balance cannot go negative without chief accountant approval | CashAccountService.validate_negative_balance() |
| R-015 | Bank account closure requires no related invoices/vouchers | Service layer FK check CompanyModel.invoice_models/VoucherModel |

---

## 16. Dependencies

### 16.1 Internal Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `Company` | Must exist | Bank/cash accounts belong to a company (company_id FK) |
| `User` / Actor UUID | Must exist | All mutations require actor UUID (D11) |
| `Currency` | Optional | ISO 4217 code on bank accounts |
| `AuditLogService` | Required | All events logged via audit_log_service.append_event() |
| `PeriodLockService` | Optional | Fiscal year period locking for reconciliations |
| `Flask-Login RBAC` | Required | @login_required + current_user.role on all API routes |
| `SQLAlchemyRepository` | Required | DB adapters for BankAccount, CashAccount, BankReconciliation |

### 16.2 External Dependencies

| Dependency | Version | Description |
|------------|---------|-------------|
| `flask` | >= 3.0 | Web framework |
| `flask-sqlalchemy` | >= 3.0 | ORM (SQLAlchemy 2.0) |
| `pycasbin` | ❌ Removed | RBAC via Flask built-in only |
| `sqlalchemy` | >= 2.0 | SQL toolkit |
| `wtforms` | >= 3.0 | Form validation (if needed) |
| `python-dotenv` | >= 1.0 | Environment config |
| `flask-migrate` | >= 4.0 | Database migration management |

### 16.3 DB Migration

**New migration file:** `a1f2b3c4d5e6_bank_cash_module.py`

Creates 3 new tables:
1. `bank_accounts` — bank account definitions
2. `cash_accounts` — cash on hand definitions
3. `bank_reconciliations` — bank reconciliation records

**Zero drift verified** against existing schema. Migration depends on:
- `company` table (already exists, companies.id FK)
- `audit_log` table (already exists, applied in system settings migration)
- `currencies` table (already exists, ISO currency codes)

---

## 17. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Bank account list (1000+ records) | < 2s | `pytest --bench` or manual timing |
| Cash account create | < 500ms | Unit test timing |
| Bank reconciliation create | < 700ms | Unit test timing |
| Reconciliation resolve (SOD, 2 actors) | < 1s | Integration test timing |
| API response time (P95) | < 500ms | Flask profiler |
| Database query count (list) | < 3 queries | SQLAlchemy count |

---

## 18. Security Requirements

| Requirement | Detail |
|-------------|--------|
| **Data isolation** | All bank/cash data scoped by company_id (tenant isolation) |
| **Actor audit** | Every mutation must include actor UUID (D11), logged in audit_log |
| **SOD enforcement** | Critical operations (closure, primary change) require 2-actor approval |
| **AUDITOR read-only** | AUDITOR cannot call any mutation API endpoint |
| **System account protection** | System accounts (is_system=TRUE) immutable via API |
| **Input validation** | All fields validated at entity layer (format, length, regex) |
| **XSS prevention** | Account names, bank names escaped in API responses |
| **CSRF protection** | Protected by Flask-WTF/HTMX pattern (existing in codebase) |
| **Rate limiting** | Configured at Flask level (existing pattern from other blueprints) |
| **HTTPS enforcement** | Flask-Talisman when DEBUG=False (existing pattern) |

---