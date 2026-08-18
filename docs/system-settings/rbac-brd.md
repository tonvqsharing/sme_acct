# RBAC BRD — Role-Based Access Control for Vietnamese SME Accounting System

## 1. Overview

This BRD defines the minimum role-based access control (RBAC) system required for a **PRODUCTION-READY** Vietnamese SME accounting application. It addresses the critical gap where `pycasbin 2.8.0` is installed but **not implemented** in the codebase, and where **P0-10** production-readiness audit marks "No RBAC enforcement at backend — only UI/Flask-Login auth" as ❌ Not implemented.

## 2. Legal & Compliance Foundations

| Law/Decree | Requirement | RBAC Implication |
|---|---|---|
| **Luật Kế toán 2015** Art. 28-30 | System must enforce chart of accounts, retention ≥10y, immutability of audit logs | RBAC ensures only authorized roles can perform critical accounting actions; SoD prevents single-person control |
| **Nghị định 123/2020/NĐ-CP** | Audit log WORM (Write Once Read Many) enforcement | RBAC restricts who can create/modify/delete audit records |
| **Nghị định 13/2023/NĐ-CP** | Electronic invoice/e-voucher issuance rules | RBAC controls who can create, post, cancel invoices/vouchers by role |
| **Big4 ITGC (ISA 315, AS 2201)** | Audit trail, immutability, Segregation of Duties (SoD) — all **system-enforced**, not UI-only | RBAC must enforce SoD at backend; UI-only checks insufficient for audit |
| **Flask-Security-Too 5.8.2** + **Flask-Principal 0.4.0** + **pycasbin 2.8.0** | Authentication + authorization framework | Integration pattern: Flask-Login/SSO → pycasbin enforcer for authorization decisions |

## 3. Business Actors (Roles)

| Role | Code | Typical User | Primary Responsibilities | SoD Constraints |
|---|---|---|---|---|
| **ACCOUNTANT** | ACCT | Staff accountant | Data entry, posting invoices/vouchers, bank entries | Cannot approve own entries; cannot config system settings |
| **CHIEF_ACCOUNTANT** | CHA | Chief accountant | Approve invoices, validate VAT, period close, config changes | Cannot create entries; can approve/deny ACCOUNTANT entries |
| **ADMIN** | ADM | System administrator | User management, company config, CA list management | Full system access; 2nd approval required for LAW-type flags |
| **AUDITOR** | AUD | External/internal auditor | Read-only audit log access, retention compliance, SoD verification | Read-only; no write/modify/delete permissions |
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

### 4.3 Resource-Action Matrix

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

## 5. Policy Configuration (pycasbin CONF/CSV)

### 5.1 Model Template (`casbin_model.conf`)

```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[role_definition]
g = _, _

[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act

[eft]
e = some(where (p.sub == r.sub && p.obj == r.obj && p.act == r.act))
```

### 5.2 Initial Policy CSV (`rbac_policy.csv`)

```csv
; Resource,Action,Role
; Company
p, /api/v1/companies/*, ACCOUNTANT
p, /api/v1/companies/{id}, CHIEF_ACCOUNTANT
p, /api/v1/companies/{id}/suspend, CHIEF_ACCOUNTANT|ADMIN
p, /api/v1/companies/{id}/dissolve, ADMIN|DIRECTOR
p, /api/v1/companies, DIRECTOR

; Invoice
p, /api/v1/invoices, ACCOUNTANT
p, /api/v1/invoices, CHIEF_ACCOUNTANT
p, /api/v1/invoices/{id}/post, CHIEF_ACCOUNTANT
p, /api/v1/invoices/{id}/cancel, ADMIN

; Voucher
p, /api/v1/vouchers, ACCOUNTANT
p, /api/v1/vouchers/{id}/post, CHIEF_ACCOUNTANT|ACCOUNTANT
p, /api/v1/vouchers/{id}/lock, CHIEF_ACCOUNTANT|ADMIN

; System Config
p, /api/v1/system-config, ADMIN
p, /api/v1/system-config/vat-rates, ADMIN
p, /api/v1/system-config/period-locks, ADMIN|CHIEF_ACCOUNTANT

; Audit Log
p, /api/v1/audit-log, AUDITOR
p, /api/v1/audit-log, CHIEF_ACCOUNTANT
; No write/delete policies for AUDITOR

; Role hierarchy
g, ACCOUNTANT, CHIEF_ACCOUNTANT
g, CHIEF_ACCOUNTANT, ADMIN
; AUDITOR has no hierarchy; read-access via separate policy
```

### 5.2.1 Subject Mapping (Flask-Login → pycasbin)

```
subject = current_user.id (UUID)
role = current_user.role (from Flask-Security-Too or custom)
```

The enforcer is initialized per-request:
```python
enforcer = CasbinEnforcer("casbin_model.conf", "rbac_policy.csv")
allowed = enforcer.enforce(subject, resource_path, action)
```

## 6. User Journeys (Happy Paths)

### UJ-01: Accountant Creates Invoice → Chief Approves

1. ACCOUNTANT logs in → session establishes `user.role = "ACCOUNTANT"`
2. ACCOUNTANT navigates to "Create Invoice" → UI enables invoice fields
3. ACCOUNTANT fills invoice, submits → Flask route calls `casbin_enforcer.enforce("ACCOUNTANT", "/api/v1/invoices", "create")` → **ALLOWED**
4. Invoice created in DB with `partner_id`, `company_id`
5. ACCOUNTANT clicks "Submit for Approval" → route checks `enforce("ACCOUNTANT", "/api/v1/invoices/{id}/approve", "post")` → **ALLOWED**
6. CHIEF_ACCOUNTANT logs in → reviews invoice → clicks "Approve" → route checks `enforce("CHIEF_ACCOUNTANT", "/api/v1/invoices/{id}/approve", "post")` → **ALLOWED**
7. Invoice status changes to APPROVED; audit log entry created with `actor_id = CHIEF_ACCOUNTANT.id`

### UJ-02: Chief Accountant Period Lock

1. CHIEF_ACCOUNTANT logs in → `user.role = "CHIEF_ACCOUNTANT"`
2. Navigates to "Close Accounting Period" → UI shows period lock form
3. Selects period, submits → route checks `enforce("CHIEF_ACCOUNTANT", "/api/v1/period-locks", "lock")` → **ALLOWED**
4. Period locked in `period_locks` table; `InvoiceService.validate_active_for_transaction()` checks lock → blocks new entries
5. Audit log entry created; Chief Accountant ID recorded as actor

### UJ-03: Auditor Views Audit Log (Read-Only)

1. AUDITOR logs in → `user.role = "AUDITOR"`
2. Navigates to "Audit Log" → route checks `enforce("AUDITOR", "/api/v1/audit-log", "read")` → **ALLOWED**
3. Lists audit records with pagination, filtering by entity_type, action, date range
4. Exports report → all actions are read-only; no download of raw DB data permitted
5. No "Delete" or "Destroy" buttons visible in UI

## 7. Alternative Paths (Error Handling)

### UA-01: Accountant Attempts to Approve Own Invoice

1. ACCOUNTANT submits invoice for approval
2. Route calls `enforce("ACCOUNTANT", "/api/v1/invoices/{id}/approve", "post")` → **DENIED** (SoD rule S-01)
3. Flask returns `403 Forbidden` with JSON: `{"error": "RBAC denied: ACCOUNTANT cannot approve own invoice", "code": "RBAC_DENIED"}`
4. UI displays: "Bạn không có quyền thực hiện thao tác này. Vui lòng yêu cầu CHIEF_ACCOUNTANT duyệt."
5. Audit log entry created: `action = "RBAC_DENIED"`, `entity_type = "Company"`, `after_value = "attempted_approval_by_ACCOUNTANT"`

### UA-02: Accountant Attempts to Modify LAW-Type System Flag

1. ACCOUNTANT attempts to POST `/api/v1/system-config` with `vat_method = "output_only"`
2. Route checks `enforce("ACCOUNTANT", "/api/v1/system-config/edit-law", "edit")` → **DENIED**
3. Additionally, `CompanyConfig` domain rule: LAW-type flags immutable without migration
4. Flask returns `403 Forbidden` with: `{"error": "RBAC + LAW-flag immutable without migration", "code": "LAW_IMMUTABLE"}`
5. UI shows: "Các cờ hệ thống loại LAW không thể thay đổi mà không có migration patch."

### UA-03: Unauthenticated Access to Protected Route

1. User not logged in → `current_user.is_authenticated = False`
2. Route checks authentication first (Flask-Login/LDAP)
3. If unauthenticated, returns `401 Unauthorized` → redirect to login
4. If authenticated but insufficient role, returns `403 RBAC_DENIED` (as above)

### UA-04: Invalid Resource Pattern in Policy

1. Policy CSV has malformed entry (e.g., missing comma, wrong field count)
2. Casbin enforcer fails to load policy at app startup
3. Application logs error: `"Failed to load RBAC policy: <error details>"`
4. App starts with **open access** (no RBAC enforcement) — **SAFE DEFAULT**: 
   - Falls back to Flask-Login role checks only
   - Admin notified via error log + Sentry
   - Policy reload required to enable full RBAC

## 8. Exception Paths

### UE-01: Emergency Override (Director Only)

| Situation | Exception Process |
|---|---|
| CHIEF_ACCOUNTANT accidentally locks period preventing all posting | Director can unlock via special endpoint `/api/v1/period-locks/emergency-unlock` — requires `DIRECTOR` role + MFA + audit log of override |
| MST critical error needs immediate fix | Director bypasses RBAC with `X-Emergency-Override: true` header + 2-factor — every override logged immutably |

### UE-02: Role Assignment Without Admin

| Situation | Process |
|---|---|
| New employee needs ACCOUNTANT role | HR submits request → CHIEF_ACCOUNTANT approves → ADMIN assigns role in `auth_user_roles` table → pycasbin policy CSV updated → enforcer reloads |

### UE-03: Policy Reload Without Downtime

| Situation | Process |
|---|---|
| Role hierarchy or policy needs update | ADMIN triggers `/api/v1/rbac/reload` → enforcer reloads `rbac_policy.csv` from disk → all in-flight requests use old policy; new requests use updated policy — zero downtime |

## 9. Data Flows

```
User Auth (Flask-Login/SSO)
        |
        v
Role Assignment (auth_user_roles table / Flask-Security-Too)
        |
        v
Subject = user.id, Role = user.role
        |
        v
Casbin Enforcer (per-request)
      /     \
     /       \
    /         \ enforce(sub, obj, act)
   / Yes        \ No
  /             \
 v               v
API Route → Validation → Business Logic → DB Operation
  \             /
   \           /
    Yes       No
     \       /
      Return 403 RBAC_DENIED
```

### 9.1 Audit Trail Flow (Every RBAC Decision)

```
RBAC Decision Point
        |
        v
[Allowed/Denied] → AuditLogService.create()
        |
        v
entity_type = "RBAC"
action = "ALLOW" or "DENY"
entity_id = <resource_path>
before_value = <user_role>
after_value = <resource_path>:<action>
actor_id = <current_user.id>
checksum = SHA-256(policy_csv_hash + user_id + resource + action)
changed_at = now()
Stored in audit_log (WORM: INSERT-only, REVOKE DELETE via DB role)
```

## 10. Templates

### T-01: RBAC Policy CSV Template

```csv
; Resource Pattern,Action,Role
; ===== Company =====
p, /api/v1/companies, DIRECTOR
p, /api/v1/companies/{id}, CHIEF_ACCOUNTANT
p, /api/v1/companies/{id}/suspend, CHIEF_ACCOUNTANT|ADMIN
p, /api/v1/companies/{id}/dissolve, ADMIN|DIRECTOR

; ===== Invoice =====
p, /api/v1/invoices, ACCOUNTANT
p, /api/v1/invoices/{id}/post, CHIEF_ACCOUNTANT
p, /api/v1/invoices/{id}/cancel, ADMIN

; ===== Voucher =====
p, /api/v1/vouchers, ACCOUNTANT
p, /api/v1/vouchers/{id}/post, CHIEF_ACCOUNTANT|ACCOUNTANT
p, /api/v1/vouchers/{id}/lock, CHIEF_ACCOUNTANT|ADMIN

; ===== System Config =====
p, /api/v1/system-config, ADMIN
p, /api/v1/system-config/vat-rates, ADMIN
p, /api/v1/system-config/period-locks, ADMIN|CHIEF_ACCOUNTANT

; ===== Audit Log =====
p, /api/v1/audit-log, AUDITOR
p, /api/v1/audit-log, CHIEF_ACCOUNTANT

; ===== Role Hierarchy =====
g, ACCOUNTANT, CHIEF_ACCOUNTANT
g, CHIEF_ACCOUNTANT, ADMIN
```

### T-02: Casbin Model CONF Template

```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[role_definition]
g = _, _

[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act

[eft]
e = some(where (p.sub == r.sub && p.obj == r.obj && p.act == r.act))
```

### T-03: RBAC Enforcer Initialization (Python)

```python
from flask_casbin import CasbinEnforcer
from flask import g, request, jsonify, current_user

# Per-request initializer (in before_request or route wrapper)
def init_casbin_enforcer():
    """Initialize casbin enforcer with current user context."""
    g.casbin = CasbinEnforcer(
        model_path="casbin_model.conf",
        policy_path="rbac_policy.csv"
    )
    # Map Flask-Login user to casbin subject
    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        g.casbin.subject(str(current_user.id))
        g.casbin.role(str(current_user.role))

def casbin_required(*allowed_roles):
    """Decorator to enforce RBAC on Flask routes."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Initialize enforcer if not already done
            if not hasattr(g, 'casbin'):
                init_casbin_enforcer()
            
            # Check role membership
            if g.casbin.role not in allowed_roles:
                return jsonify({
                    "error": f"RBAC denied: role '{g.casbin.role}' required, '{', '.join(allowed_roles)}' allowed",
                    "code": "RBAC_INSUFFICIENT_ROLE"
                }), 403
            
            # Check action permission
            resource = request.path
            action = request.method.lower()  # get, post, patch, delete
            allowed = g.casbin.enforce(g.casbin.subject, resource, action)
            
            if not allowed:
                return jsonify({
                    "error": f"RBAC denied: '{g.casbin.subject}' cannot '{action}' '{resource}'",
                    "code": "RBAC_DENIED"
                }), 403
            
            return f(*args, **kwargs)
        return wrapper
    return decorator
```

## 11. Production Readiness Checklist

| Item | Status | Owner | Notes |
|---|---|---|---|
| P0-10: RBAC backend enforcement ❌ → ⬜ | Not implemented | Lead Dev + BA | Must implement before PROD launch |
| P0-10a: pycasbin policy CSV loaded ✅ → ⬜ | Config files ready | Dev | `casbin_model.conf` + `rbac_policy.csv` |
| P0-10b: Casbin enforcer per-request ✅ → ⬜ | Middleware built | Dev | `before_request` + `casbin_required` decorator |
| P0-10c: SoD rules enforced ✅ → ⬜ | 4 critical SoD rules | BA + Chief Acct | S-01 through S-04 |
| P0-10d: Audit log of RBAC decisions ✅ → ⬜ | Every decision logged | Dev | AuditLogService.create() with entity_type="RBAC" |
| P0-10e: Role hierarchy working ✅ → ⬜ | g, ACCOUNTANT, CHIEF_ACCOUNTANT etc. | Dev | Casbin role_definition |
| P0-10f: LAW-type flag immutability ✅ → ⬜ | Migration required for LAW flags | Chief Acct + Dev | Art. 28 Luật Kế toán 2015 |
| P0-10g: AUDITOR read-only ✅ → ⬜ | No write/delete policies | Dev | Policy CSV has no `p, /audit-log, AUDITOR, delete` |
| P1-02: MFA on privileged roles ❌ → ⬜ | Not yet enabled | Security Lead | Flask-Security-Too MFA config |
| P2-06: Password policy ❌ → ⬜ | Not implemented | Security Lead | Password complexity, rotation |

**PRODUCTION GATE**: All P0 items must be ✅ (green) before any staging deploy. P1/P2 can be β (beta) with documented risk acceptance.

## 12. Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-18 | BA Lead + Chief Accountant | Initial BRD; RBAC gap analysis from production audit |
| 1.1 | — | — | — |