# Processes, Rules, Data Flows, Workflows — Bank & Cash Accounts Module

## 1. Business Processes

### 1.1 Bank Account Lifecycle Process

```
┌──────────────────────────────────────────────────────────────┐
│                    BANK ACCOUNT LIFECYCLE                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ACTIVE  ───────────────────────▶  SUSPENDED  ─────────────▶ CLOSED  │
│      ▲                                       │                   │
│      └─────────────────────(SOD closure)───────────────────────┘
│                                              │
│                           (reactivate from SUSPENDED)     │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Legend:
- Arrow = allowed state transition
- SOD = Separation of Duties (requires 2-actor approval for closure)
- Reactivation: SUSPENDED → ACTIVE (1-actor approval, no SOD required)
```

**State Transition Rules:**
| From → To | Condition | Actor Requirement |
|-----------|-----------|-------------------|
| ACTIVE → SUSPENDED | Requested by CHIEF_ACCOUNTANT/ADMIN | 1st actor only |
| SUSPENDED → ACTIVE | Approved by CHIEF_ACCOUNTANT/ADMIN | 2nd actor (but NOT SOD, since not closure) |
| ACTIVE → CLOSED | SOD workflow: 1st actor requests, 2nd approves | 2 DIFFERENT actors (SOD) |
| CLOSED → (never) | — | — — system-immutable after close |
| SUSPENDED → CLOSED | Direct closure (bypasses SOD — admin only) | ADMIN only, with full audit |

### 1.2 Cash Account Lifecycle Process

```
┌─────────────────────────────────────────────┐
│              CASH ACCOUNT LIFECYCLE        │
├─────────────────────────────────────────────┤
│  ACTIVE  ─────────────────────▶  LOCKED ────┤
│      ▲                                    │
│      └────────(balance=0 closure)───────────┘
│                                              │
│            (reactivate from LOCKED)          │
│                                              │
└─────────────────────────────────────────────┘
```

**State Transition Rules:**
| From → To | Condition | Actor Requirement |
|-----------|-----------|-------------------|
| ACTIVE → LOCKED | Balance zeroed or transferred, CHIEF_ACCOUNTANT requests | 1st actor |
| LOCKED → ACTIVE | CHIEF_ACCOUNTANT approves reactivation | 1st actor (no SOD) |
| ACTIVE → CLOSED | Balance = 0, no transactions pending | 1 actor (CHIEF_ACCOUNTANT or ADMIN) |
| CLOSED → (never) | — | — — immutable |

### 1.3 Bank Reconciliation Process

```
┌─────────────────────────────────────────────────────────┐
│               BANK RECONCILIATION LIFECYCLE              │
├─────────────────────────────────────────────────────────┤
│  UNRESOLVED  ────────────────────▶  PARTIALLY_RESOLVED  ─┤
│      │                                   │               │
│      ▼                                   ▼               │
│  RESOLVED (1st actor) ──────▶ RESOLVED (2nd actor, SOD) │
│      │                                   │               │
│      └──────────────── no 2nd actor ───────────────────────┘
│                                                              │
│  If difference > 0.01 and 2nd actor rejects → remains      │
│  UNRESOLVED, flagged for investigation                     │
│                                                              │
│  Unresolved older than 365 days → escalated to CHIEF_ACCT   │
│                                                              │
└─────────────────────────────────────────────────────────┘
```

**Reconciliation Resolution Rules:**
| Condition | Outcome |
|-----------|---------|
| difference ≤ 0.01, 2nd actor approves | Reconciliation marked RESOLVED, both checksums logged |
| difference ≤ 0.01, 2nd actor rejects | Remains UNRESOLVED, investigation flag raised |
| difference > 0.01, 2nd actor approves | FORCED resolution, difference noted as "accepted discrepancy", both checksums logged |
| difference > 0.01, 2nd actor rejects | Remains UNRESOLVED, mandatory investigation, escalation to CHIEF_ACCOUNTANT |
| Reconciliation age > 365 days, still UNRESOLVED | Escalated to CHIEF_ACCOUNTANT via notification, audit report generated |

### 1.4 Cash Transaction Process

```
┌───────────────────────┐
│   CASH TRANSACTION     │
├───────────────────────┤
│  User enters amount    │
│  System validates:    │
│    • Account ACTIVE   │
│    • Not system acct  │
│    • Balance sufficiency │
│  Amount added to     │
│  current_balance     │
│  Checksum appended   │
│  Audit event logged  │
│  Return updated bal  │
│                       │
└───────────────────────┘
```

---

## 2. Business Rules (R-001 through R-015)

| Rule ID | Rule Description | Enforcement Level | Error on Violation |
|---------|-----------------|-------------------|---------------------|
| **R-001** | Every company can have only ONE primary bank account | DB unique constraint + service layer | 409 PRIMARY_ALREADY_EXISTS |
| **R-002** | Cash code must match TT99 format: ^[1-9]\d{2}$ or ^[1-9]\d{3}$ | Entity validation on create | 422 INVALID_CASH_CODE |
| **R-003** | Bank account account_number must be unique per company | DB unique constraint + service validation | 409 DUPLICATE_ACCOUNT_NUMBER |
| **R-004** | All mutations require actor UUID (D11) in request body | API decorator + service layer entry check | 400 MISSING_ACTOR |
| **R-005** | All mutations require non-empty reason string | API decorator + service layer validation | 400 MISSING_REASON |
| **R-006** | AUDITOR role is read-only; cannot create/update/delete bank/cash | @login_required + current_user.role + service layer role check | 403 AUDITOR_READ_ONLY |
| **R-007** | System accounts (is_system=TRUE) cannot be modified or deleted | CompanyConfig.check_system_account() | 403 SYSTEM_ACCOUNT_MODIFICATION_ERROR |
| **R-008** | Bank reconciliation must balance within tolerance 0.01 | BankReconciliation.is_balanced(tolerance=0.01) | 409 RECONCILIATION_IMBALANCED |
| **R-009** | 10-year retention: no automatic deletion, soft-close only | Service layer + audit log policy | N/A (retention policy) |
| **R-010** | SHA-256 checksum chaining on all bank/cash/reconciliation events | Service layer append_checksum() | N/A (audit integrity) |
| **R-011** | SOD (Separation of Duties): closure/primary change requires 2 actors | Service layer + @login_required + current_user.role | 403 SOD_VIOLATION (same actor both roles) |
| **R-012** | Currency on bank account must be valid ISO 4217 code ^[A-Z]{3}$ | Service layer validation | 422 INVALID_CURRENCY_CODE |
| **R-013** | Period locked prevents new reconciliations (FY integration) | PeriodLockService.check_fiscal_year_lock() | 409 PERIOD_LOCKED_ERROR |
| **R-014** | Cash balance cannot go negative without chief accountant approval | CashAccountService.validate_negative_balance() | 422 INSUFFICIENT_BALANCE |
| **R-015** | Bank account closure requires no related invoices/vouchers | Service layer FK check (CompanyModel.relatives) | 409 HAS_RELATED_DOCUMENTS |

---

## 3. Data Flows

### 3.1 Bank Account Creation Data Flow

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
                                 │  Business Rules │
                                 │  (R-001 to R-005)│
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │  BankAccountSrv │
                                 │  (create method)│
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
                                 │    bank_accounts│
                                 │    table in DB  │
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

### 3.2 Cash Transaction Data Flow

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
                                 │ (cash entity)   │
                                 │ - validate code │
                                 │ - check balance │
                                 │ - check system  │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ CashAccountSrv  │
                                 │  (update_balance)│
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
                                 │   cash_accounts │
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

### 3.3 Bank Reconciliation Resolve (SOD) Data Flow

```
┌──────────────────┐     POST     ┌─────────────────────┐
│  User Interface  │ ───────────▶ │  Flask API Layer    │
│  (HTMX + Bulma)    │            │  @login_required    │
└──────────────────┘            │  current_user.role  │
                              └─────────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │ SOD Check: 2nd   │
                                 │ actor ≠ 1st actor│
                                 │  (SOD_VIOLATION) │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │  1st Actor Event │
                                 │  (checksum 1)    │
                                 │  appended        │
                                 │  to audit_log    │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │  2nd Actor Valid │
                                 │  (difference ≤ 0.01)│
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │  2nd Actor Event │
                                 │  (checksum 2)    │
                                 │  appended        │
                                 │  to audit_log    │
                                 └─────────────────┘
                                        │
                                        ▼
                                 ┌─────────────────┐
                                 │   HTTP Response │
                                 │   200 + JSON    │
                                 └─────────────────┘
```

---

## 4. Workflows

### 4.1 Bank Account Creation Workflow (Condensed)

```
START
│
├─→ User fills Create Bank Account form
│   │
│├─→ Validate: actor UUID (D11) present?
││   │   └─ No → 400 MISSING_ACTOR, END
││   └─ Yes → continue
│
├─→ Validate: account_number unique per company?
││   │   └─ No → 409 DUPLICATE_ACCOUNT_NUMBER, END
││   └─ Yes → continue
│
├─→ Validate: if is_primary, check no other primary exists?
││   │   └─ No → 409 PRIMARY_ALREADY_EXISTS, END
││   └─ Yes → continue
│
├─→ Create BankAccount entity
││
├─→ Save to DB (SQLAlchemy repo add + flush)
││
├─→ Append SHA-256 checksum: SHA-256(prev + actor + now + "CREATE" + reason + id)
││
├─→ Log audit event via audit_log_service.append_event()
││
├─→ Return 201 + serialized bank account
│
└─→ END
```

### 4.2 Bank Account Closure Workflow (SOD — 2-Actor)

```
START
│
├─→ CHIEF_ACCOUNTANT requests closure on bank account
│   │
│├─→ Validate: account is ACTIVE, no related invoices/vouchers?
││   │   └─ No → 409 HAS_RELATED_DOCUMENTS, END
││   └─ Yes → continue (status → SUSPENDED, checksum 1 appended)
│
├─→ System waits for 2nd actor approval
│   │
│├─→ ACCOUNTANT (2nd actor) logs in, sees pending approval
││   │
│├─→ ACCOUNTANT reviews and Approves or Rejects
││   │   ├─ APPROVED:
││   │   │   ├─ status → CLOSED
││   │   │─ checksum 2: SHA-256(prev + accountant + now + "CLOSE_APPROVE" + reason + id)
││   │   │   ├─ Both checksums in audit_log
││   │   │   └─ Return 200 + "Closed success"
││   │   │
││   │   └─ REJECTED:
││   │       ├─ status → ACTIVE (restored)
││   │       ├─ checksum 2: SHA-256(prev + accountant + now + "CLOSE_REJECT" + reason + id)
││   │       └─ Return 409 + "Rejected, account restored"
││   │
││   └─ END (either outcome)
│
└─→ END
```

### 4.3 Cash Transaction Workflow

```
START
│
├─→ User enters transaction on Cash Account
│   │
├─→ Validate: actor UUID (D11) present?
│   │   └─ No → 400 MISSING_ACTOR, END
│
├─→ Validate: Cash Account is ACTIVE, not system, not CLOSED?
│   │   └─ No → 409 ACCOUNT_CLOSED or SYSTEM_ACCOUNT_ERROR, END
│
├─→ Validate: new balance ≥ 0 (or chief accountant approval if negative)?
│   │   └─ No → 422 INSUFFICIENT_BALANCE, END
│
├─→ Update: current_balance = current_balance + amount
│   │
├─→ Append SHA-256 checksum: SHA-256(prev + actor + now + "TRANSACTION" + reason + id + amount)
│   │
├─→ Log audit event via audit_log_service.append_event()
│   │
├─→ Return 200 + updated cash account JSON
│
└─→ END
```

### 4.4 Bank Reconciliation Resolution Workflow (SOD)

```
START
│
├─→ User (1st actor) initiates reconciliation resolve
│   │
├─→ Validate: actor UUID present, reconciliation exists and UNRESOLVED?
│   │   └─ No → 404/409, END
│
├─→ Mark as "1st actor approved", append checksum 1:
│   │  SHA-256(prev + 1st_actor + now + "RECON_RESOLVE_1ST" + reason + reconciliation_id)
│
├─→ System waits for 2nd actor (CHIEF_ACCOUNTANT/ADMIN)
│   │
├─→ 2nd actor logs in, sees pending resolution
│   │
├─→ 2nd actor reviews difference (statement_balance - internal_balance)
│   │
├─→ 2nd actor Approves or Rejects
│   │
│  ├─ APPROVED (difference ≤ 0.01):
│  │   │  status → RESOLVED
│  │   │  checksum 2: SHA-256(prev + 2nd_actor + now + "RECON_RESOLVE_2ND" + reason + reconciliation_id)
│  │   │  Both checksums 1 & 2 in audit_log
│  │   │  Return 200 + "Reconciliation resolved"
│  │   │
│  │  └─ difference > 0.01 but 2nd actor forces:
│  │     │  status → RESOLVED_WITH_DISCREPANCY
│  │     │  reason forced to include "FORCED_DISCREPANCY"
│  │     │  Both checksums logged
│  │     │  Return 200 + "Resolved with noted discrepancy"
│  │
│  └─ REJECTED:
│      │  status → UNRESOLVED (remains)
│      │  checksum 2: SHA-256(prev + 2nd_actor + now + "RECON_REJECT" + reason + reconciliation_id)
│      │  Return 409 + "Unresolved, investigation needed"
│
└─→ END
```

---

## 5. Data Flow Diagrams (DFD Level 0-2)

### DFD Level 0: System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                        BANK & CASH MODULE                        │
│                                                                 │
│  Actors:  ACCOUNTANT, CHIEF_ACCOUNTANT, AUDITOR, ADMIN, DIRECTOR│
│                                                                 │
│  External Interfaces:                                           │
│  ├─ POST /api/v1/bank-accounts          │ GET /api/v1/bank-accounts     │
│  ├─ POST /api/v1/cash-accounts          │ GET /api/v1/cash-accounts     │
│  ├─ POST /api/v1/reconciliations         │ GET /api/v1/reconciliations   │
│  ├─ POST /api/v1/cash-accounts/{id}/transact   │ GET /api/v1/cash-accounts/{id}│
│  └─ ... (full API surface)                                          │
│                                                                 │
│  Database: bank_accounts, cash_accounts, bank_reconciliations, │
│           audit_log, companies, users                             │
│                                                                 │
│  Integrations:                                                    │
│  ├─ AuditLogService (append_event, get_retention_status)         │
│  ├─ RBAC ( @login_required + current_user.role )                 │
│  ├─ PeriodLockService (period status checks)                     │
│  ├─ CurrencyService (ISO 4217 validation)                        │
│  └─ CompanyService (company existence FK checks)                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### DFD Level 1: Bank Account Create ( explosion of Create Bank Account process )

(See detailed data flow diagram in section 3.1 above)

### DFD Level 1: Cash Transaction (explosion of Cash Transaction process )

(See detailed data flow diagram in section 3.2 above)

### DFD Level 1: Reconciliation Resolve with SOD (explosion of Reconciliation Resolve workflow)

(See detailed data flow diagram in section 4.4 above)

---