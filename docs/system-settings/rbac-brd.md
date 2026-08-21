# RBAC BRD — Role-Based Access Control for Vietnamese SME Accounting System
_Flask built-in only. No pycasbin, no casbin_model.conf, no rbac_policy.csv._

## 1. Overview

This BRB defines the role-based access control system using **Flask-Login built-in only** for the Vietnamese SME accounting application. RBAC enforcement is via `current_user.role` checks and `@login_required` — no Casbin, no pycasbin, no model/CSV files.

**Critical**: The casbin model (`casbin_model.conf`), policy CSV (`rbac_policy.csv`), and `pycasbin` import are **deleted**. Do not import `pycasbin` or `casbin`. RBAC gaps marked ❌ in prior production-readiness audit are now resolved by Flask built-in checks.

## 2. Legal & Compliance Foundations

| Law/Decree | Requirement | RBAC Implication |
|---|---|---|
| **Luật Kế toán 2015** Art. 28-30 | System must enforce chart of accounts, retention ≥10y, immutability of audit logs | RBAC ensures only authorized roles can perform critical accounting actions; SoD prevents single-person control |
| **Nghị định 123/2020/NĐ-CP** | Audit log WORM (Write Once Read Many) enforcement | RBAC restricts who can create/modify/delete audit records |
| **Nghị định 13/2023/NĐ-CP** | Electronic invoice/e-voucher issuance rules | RBAC controls who can create, post, cancel invoices/vouchers by role |
| **Big4 ITGC (ISA 315, AS 2201)** | Audit trail, immutability, Segregation of Duties (SoD) — all **system-enforced**, not UI-only | RBAC must enforce SoD at backend; UI-only checks insufficient for audit |
| **Flask-Login** | Authentication + authorization framework | `@login_required` + `current_user.role` — no third-party RBAC library needed |

## 3. Business Actors (Roles)

| Role | Code | Typical User | Primary Responsibilities | SoD Constraints |
|---|---|---|---|---|
| **ACCOUNTANT** | ACCT | Staff accountant | Data entry, posting invoices/vouchers, bank entries | Cannot approve own entries; cannot config system settings |
| **CHIEF_ACCOUNTANT** | CHA | Chief accountant | Approve invoices, validate VAT, period close, config changes | Cannot create entries; can approve/deny ACCOUNTANT entries |
| **ADMIN** | ADM | System administrator | User management, company config, CA list management | Full system access; 2nd approval required for LAW-type flags |
| **AUDITOR** | AUD | External/internal auditor | Read-only audit log access, retention compliance, SoD verification | **Read-only**; no write/modify/delete permissions |
| **DIRECTOR** | DIR | Company director | Strategic decisions, dissolve company, authorize large transactions | Highest privilege; must not overlap with CHA on same transaction |

## 4. Core RBAC Requirements

### 4.1 Segregation of Duties (SoD) — Critical

| SoD Rule | Violation | Legal/Standard Reference |
|---|---|---|
| **S-01**: CREATOR ≠ APPROVER | Same user creates and approves an invoice | Luật Kế toán 2015 Art. 29; Big4 ISA 315 |
| **S-02**: POSTER ≠ CREATOR | Same user creates and posts a voucher | Luật Kế toán 2015 Art. 30; Big4 AS 2201 |
| **S-03**: CONFIG_MODIFIER ≠ AUDITOR | Same user modifies system config and audits it | Nghị định 123/2020/NĐ-CP; Big4 auditor independence |
| **S-04**: MST_CHANGER ≠ COMPANY_OWNER | Same user changes MST without owner approval | Luật Doanh nghiệp 2020; tax compliance |

### 4.2 Role Hierarchy

```
DIRECTOR > ADMIN > CHIEF_ACCOUNTANT > ACCOUNTANT
AUDITOR (independent; no hierarchy; read-only all)
```

### 4.3 Resource-Action Matrix (Flask-built role checks)

| Resource | Actions | ACCOUNTANT | CHIEF_ACCOUNTANT | ADMIN | AUDITOR | DIRECTOR |
|---|---|---|---|---|---|---|
| **Company** | create | ✗ | ✗ | ✓ | ✓ (read) | ✓ |
| | update | ✗ | ✓ (own) | ✓ | ✗ | ✓ |
| | suspend/reactivate | ✗ | ✓ | ✓ | ✗ | ✓ |
| | dissolve | ✗ | ✗ | ✓ | ✗ | ✓ |
| **Invoice** | create | ✓ (own company) | ✗ | ✗ | ✓ (read) | ✓ |
| | post | ✓ | ✓ (approve) | ✗ | ✗ | ✓ |
| | cancel | ✗ | ✓ | ✓ | ✗ | ✓ |
| **Voucher** | create | ✓ (own company) | ✗ | ✗ | ✓ (read) | ✓ |
| | post | ✓ (self-post within tol) | ✓ (approve) | ✗ | ✗ | ✓ |
| | lock/unlock | ✗ | ✓ | ✓ | ✗ | ✓ |
| **Tax/MST** | validate | ✓ (domain VO) | ✓ | ✓ | ✓ | ✓ |
| | modify | ✗ | ✗ | ✓ (with 2nd approval) | ✗ | ✗ |
| **System Config** | view | ✓ (limited) | ✓ (limited) | ✓ | ✓ (read-only) | ✓ |
| | edit CONFIG-type | ✗ | ✗ | ✓ (with audit log + 2nd approval) | ✗ | ✗ |
| | edit LAW-type | ✗ | ✗ | ✗ (migration required) | ✗ | ✗ (migration) |
| **Audit Log** | read | ✓ (all roles) | ✓ (all roles) | ✓ | ✓ | ✓ |
| | destroy/delete | ✗ | ✗ | ✗ (migration) | ✗ | ✗ (10-yr retention only) |
| **Period Lock** | lock/unlock | ✗ | ✓ | ✓ | ✗ | ✓ |

## 5. Flask Built-in RBAC Enforcement Pattern

All role checks use Flask-Login built-in only:

```python
from flask import current_user, abort, redirect, url_for
from flask_login import login_required

# Pattern 1: Basic auth + role check
@bp.route("/api/v1/companies", methods=["POST"])
@login_required
def create_company():
    if current_user.role != "ADMIN":
        abort(403, description="RBAC denied: ADMIN role required")
    # ... proceed

# Pattern 2: Role check with OR logic
@bp.route("/api/v1/period-locks/lock", methods=["POST"])
@login_required
def lock_period():
    if current_user.role not in ("CHIEF_ACCOUNTANT", "ADMIN"):
        abort(403, description="RBAC denied: CHIEF_ACCOUNTANT or ADMIN role required")
    # ... proceed

# Pattern 3: AUDITOR read-only
@bp.route("/api/v1/audit-log", methods=["GET"])
@login_required
def audit_log():
    if current_user.role == "AUDITOR":
        # Read-only: allow listing/export
        pass
    elif current_user.role in ("ADMIN", "CHIEF_ACCOUNTANT", "ACCOUNTANT"):
        # Full access
        pass
    else:
        abort(403, description="RBAC denied: insufficient role")
    # ... proceed
```

## 6. User Journeys (Happy Paths)

### UJ-01: Accountant Creates Invoice → Chief Approves

1. ACCOUNTANT logs in → Flask-Login establishes `session.user.role = "ACCOUNTANT"`
2. ACCOUNTANT navigates to "Create Invoice" → UI may enable/disable fields based on role
3. ACCOUNTANT fills invoice, submits → Flask route checks `current_user.role != "ACCOUNTANT"` → **ALLOWED** (own-company create)
4. Invoice created in DB with `partner_id`, `company_id`
5. ACCOUNTANT clicks "Submit for Approval" → route checks `current_user.role != "CHIEF_ACCOUNTANT"` → **ALLOWED** (approval)
6. CHIEF_ACCOUNTANT logs in → reviews invoice → clicks "Approve" → route checks `current_user.role != "CHIEF_ACCOUNTANT"` → **ALLOWED**
7. Invoice status changes to APPROVED; audit log entry created with `actor_id = CHIEF_ACCOUNTANT.id`

### UJ-02: Chief Accountant Period Lock

1. CHIEF_ACCOUNTANT logs in → `user.role = "CHIEF_ACCOUNTANT"`
2. Navigates to "Close Accounting Period" → UI shows period lock form
3. Selects period, submits → route checks `current_user.role not in ("CHIEF_ACCOUNTANT", "ADMIN")` → **ALLOWED**
4. Period locked in `period_locks` table; `InvoiceService.validate_active_for_transaction()` checks lock → blocks new entries
5. Audit log entry created; Chief Accountant ID recorded as actor

### UJ-03: Auditor Views Audit Log (Read-Only)

1. AUDITOR logs in → `user.role = "AUDITOR"`
2. Navigates to "Audit Log" → route checks `current_user.role == "AUDITOR"` → **ALLOWED** (read-only)
3. Lists audit records with pagination, filtering by entity_type, action, date range
4. Exports report → all actions are read-only; no download of raw DB data permitted
5. No "Delete" or "Destroy" buttons visible in UI

## 7. Alternative Paths (Error Handling)

### UA-01: Accountant Attempts to Approve Own Invoice

1. ACCOUNTANT submits invoice for approval
2. Route checks `current_user.role not in ("CHIEF_ACCOUNTANT",)` → **DENIED** (SoD rule S-01)
3. Flask returns `403 Forbidden` with JSON: `{"error": "RBAC denied: ACCOUNTANT cannot approve own invoice", "code": "RBAC_DENIED"}`
4. UI displays: "Bạn không có quyền thực hiện thao tác này. Vui lòng yêu cầu CHIEF_ACCOUNTANT duyệt."
5. Audit log entry created: `action = "RBAC_DENIED"`, `entity_type = "Company"`, `after_value = "attempted_approval_by_ACCOUNTANT"`

### UA-02: Accountant Attempts to Modify LAW-Type System Flag

1. ACCOUNTANT attempts to POST `/api/v1/system-config` with `vat_method = "output_only"`
2. Route checks `current_user.role not in ("ADMIN",)` → **DENIED** (admin-only for LAW-type)
3. Additionally, `CompanyConfig` domain rule: LAW-type flags immutable without migration
4. Flask returns `403 Forbidden` with: `{"error": "RBAC denied: ADMIN role required to modify LAW flags", "code": "RBAC_DENIED"}`
5. UI shows: "Các cờ hệ thống loại LAW không thể thay đổi mà không có migration patch."

### UA-03: Unauthenticated Access to Protected Route

1. User not logged in → `current_user.is_authenticated = False`
2. Route checks authentication first (Flask-Login) via `@login_required`
3. If unauthenticated, returns `401 Unauthorized` → redirect to login
4. If authenticated but insufficient role, returns `403 RBAC_DENIED` (as above)

## 8. Data Flows

```
User Auth (Flask-Login)
        |
        v
Role: current_user.role
        |
        v
Flask Role Check (current_user.role)
        |
        v
Allowed → Business Logic → DB Operation
Denied → 403 Forbidden + audit log
```

### 8.1 Audit Trail Flow (Every RBAC Decision)

```
RBAC Decision Point
        |
        v
[Allowed/Denied] → AuditLogService.create(entity_type="RBAC", ...)
        |
        v
entity_type = "RBAC"
action = "ALLOW" or "DENY"
entity_id = <resource_path>
before_value = <user_role>
after_value = <resource_path>:<action>
actor_id = <current_user.id>
checksum = SHA-256(...)
changed_at = now()
Stored in audit_log (WORM: INSERT-only, REVOKE DELETE via DB role)
```

## 9. Templates (Flask RBAC)

### T-01: Flask RBAC Role Check Template

```python
# In each Flask route:
from flask import current_user, abort
from flask_login import login_required

@bp.route("/api/v1/companies", methods=["POST"])
@login_required
def create_company():
    # RBAC: only ADMIN can create
    if current_user.role != "ADMIN":
        abort(403, description="RBAC denied: ADMIN role required")
    # ... route logic
```

### T-02: AUDITOR Read-only Template

```python
@bp.route("/api/v1/audit-log", methods=["GET"])
@login_required
def audit_log():
    if current_user.role == "AUDITOR":
        # Read-only: allow listing, prohibit write
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            abort(403, description="RBAC denied: AUDITOR read-only")
    # ... proceed with read access
```

## 10. Production Readiness

RBAC is now enforced at the backend via Flask-Login `current_user.role` — no Casbin, no pycasbin, no model/CSV files needed. All P0-10 RBAC gap items are resolved by the patterns above.

---