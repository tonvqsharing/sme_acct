# RBAC Specifications — Vietnamese SME Accounting System
_Flask built-in only. No pycasbin, no casbin_model.conf, no rbac_policy.csv._

## 1. Overview

This document specifies the technical implementation of the Role-Based Access Control (RBAC) module for the Vietnamese SME accounting application using **Flask-Login built-in only**. No `pycasbin`, no `casbin_model.conf`, no `rbac_policy.csv`. RBAC enforcement via `current_user.role` checks and `@login_required`.

**Critical Gap Addressed**: P0-10 "No RBAC enforcement at backend — only UI/Flask-Login auth" is now resolved by Flask built-in checks. All role authorization uses `current_user.role` from Flask-Login.

## 2. Model Definition

RBAC is flat — no Casbin model, no policy CSV, no role hierarchy via `g,` directives. Roles are simple string values on `current_user.role`:

| Role String | Description |
|---|---|
| `ACCOUNTANT` | Staff accountant — create own-company invoices/vouchers, read-only access |
| `CHIEF_ACCOUNTANT` | Chief accountant — approve invoices, period lock/unlock, system config edits |
| `ADMIN` | System administrator — full access, user management, company config |
| `AUDITOR` | External/internal auditor — **read-only**; no write/modify/delete permissions |
| `DIRECTOR` | Company director — strategic decisions, dissolve company, authorize large transactions |

**Role Hierarchy** (advisory only; enforcement is flat-check via `current_user.role`):

```
DIRECTOR > ADMIN > CHIEF_ACCOUNTANT > ACCOUNTANT
AUDITOR (standalone; read-access via explicit role check; no hierarchy inheritance)
```

## 3. Subject Mapping (Flask-Login)

| Flask Context | `current_user` Attribute | RBAC Role String |
|---|---|---|
| `is_authenticated = True` | `current_user.role` | `str(current_user.role)` |
| `is_authenticated = True` | `current_user.id` | UUID — used for audit logging only |
| `is_authenticated = False` | unauthenticated | No role — `@login_required` redirects to login |

**No pycasbin subject/role mapping needed.** The enforcer, model, and CSV are deleted.

## 4. Enforcer Initialization — N/A

No casbin enforcer, no model loading, no per-request initialization. Flask-Login handles authentication and `current_user` proxy is available after `@login_required`.

**No `before_request` hook initializes casbin.** No `get_casbin_enforcer()` function needed. No `casbin_required` decorator.

## 5. RBAC Enforcement Pattern (Flask Built-in)

All role checks use `current_user.role` from Flask-Login:

```python
from flask import current_user, abort
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
        # Read-only mode: allow GET, prohibit write methods
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            abort(403, description="RBAC denied: AUDITOR read-only")
    # ... proceed with read access
```

## 6. API Blueprint RBAC Requirements

All endpoints must have `@login_required`. RBAC role checks via `current_user.role`:

| Blueprint | Endpoint | Required Role Check |
|---|---|---|
| `api_bp` (Company) | `POST /api/v1/companies` | `current_user.role == "ADMIN"` |
| | `GET /api/v1/companies` | `current_user.role in ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` |
| | `GET /api/v1/companies/<id>` | `current_user.role in ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` for read |
| | `PATCH /api/v1/companies/<id>` | `current_user.role in ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` |
| | `POST /api/v1/companies/<id>/suspend` | `current_user.role in ("CHIEF_ACCOUNTANT", "ADMIN")` |
| | `POST /api/v1/companies/<id>/dissolve` | `current_user.role in ("ADMIN", "DIRECTOR")` |
| | `POST /api/v1/companies/<id>/reactivate` | `current_user.role in ("CHIEF_ACCOUNTANT", "ADMIN")` |
| `audit_bp` (Audit Log) | `GET /api/v1/audit-log` | `current_user.role in ("AUDITOR", "CHIEF_ACCOUNTANT", "ADMIN", "ACCOUNTANT")` read-only |
| | `POST /api/v1/audit-log/export` | `current_user.role in ("AUDITOR", "CHIEF_ACCOUNTANT", "ADMIN")` |
| `system_settings_bp` | `GET /config` | `current_user.role in ("ACCOUNTANT", "ADMIN")` limited |
| | `PATCH /config/flags/{flag_name}` | `current_user.role == "ADMIN"` for CONFIG; LAW-type requires migration |
| `health` | `GET /health` | Public (no auth) — monitoring endpoint must be open |

**Service layer calls** assume RBAC is already enforced at the API decorator boundary (per Lego Brick Architecture: "Presentation translate HTTP"). Internal trusted calls bypass role checks.

## 7. Audit Trail for RBAC Decisions

Every RBAC decision must be logged via `AuditLogService.create()`:

```python
from src.application.services.audit_log_service import AuditLogService
from src.infrastructure.database import db

def _log_rbac_decision(allowed: bool, user_role: str, resource: str, action: str, actor_id: UUID):
    service = AuditLogService(db.session if hasattr(db, 'session') else None)
    
    decision = "ALLOW" if allowed else "DENY"
    service.create(
        entity_type="RBAC",
        entity_id=request.path,
        action=decision,
        before_value=f"role={user_role};resource={resource};action={action}",
        after_value=None,
        actor_id=actor_id,
    )
```

### 7.1 Audit Log Entry Schema (RBAC Decisions)

| Field | Value (RBAC Decision) |
|---|---|
| `entity_type` | `"RBAC"` |
| `action` | `"ALLOW"` or `"DENY"` |
| `entity_id` | Request path, e.g. `"/api/v1/invoices/{id}/post"` |
| `before_value` | `f"role={user_role};resource={resource};action={action}"` |
| `after_value` | `None` (decisions are immutable; no "after" state) |
| `actor_id` | `current_user.id` (the user whose access was checked) |
| `checksum` | `SHA-256(f"{actor_id}:{request.path}:{action}:{policy_csv_hash}")` computed at policy load |
| `changed_at` | `now()` (INSERT-only; WORM enforcement via DB: `REVOKE DELETE ON audit_log FROM PUBLIC`) |
| `destroyed_at` | `NULL` (never destroyed before 10-year retention) |

### 7.2 Example Audit Entries

| Scenario | entity_type | action | actor_id | before_value | checksum (truncated) |
|---|---|---|---|---|---|
| ACCOUNTANT creates invoice | `"RBAC"` | `"ALLOW"` | `uuids:1111...` | `"role=ACCOUNTANT;resource=/api/v1/invoices;action=post"` | `a1b2c3d4...` |
| ACCOUNTANT approves own invoice | `"RBAC"` | `"DENY"` | `uuids:1111...` | `"role=ACCOUNTANT;resource=/api/v1/invoices/{id}/post;action=post"` | `a1b2c3d4...` |
| ADMIN edits VAT rates | `"RBAC"` | `"ALLOW"` | `uuids:2222...` | `"role=ADMIN;resource=/api/v1/system-config/vat-rates;action=patch"` | `a1b2c3d4...` |
| AUDITOR tries to delete audit record | `"RBAC"` | `"DENY"` | `uuids:3333...` | `"role=AUDITOR;resource=/api/v1/audit-log/{id}/delete;action=delete"` | `a1b2c3d4...` |

## 8. Production Readiness Gates

| Gate | Requirement | Status (post-implementation) | Owner | Done Definition |
|---|---|---|---|---|
| **P0-10** | RBAC backend enforcement (not just UI) | ✅ Resolved | Lead Dev | Every route uses `@login_required` + `current_user.role` check; 403 on deny |
| **P0-10a** | Flask-Login `@login_required` on ALL API routes | ✅ Done | Dev | `from flask_login import login_required` on every route |
| **P0-10b** | `current_user.role` role checks on all routes | ✅ Done | Dev | `if current_user.role != "ADMIN": abort(403)` pattern |
| **P0-10c** | SoD rules enforced (4 critical rules: S-01 through S-04) | ✅ Done | BA + Chief Acct | Role checks in routes prevent S-01 through S-04 violations |
| **P0-10d** | Audit log of every RBAC decision | ✅ Done | Dev | `AuditLogService.create(entity_type="RBAC", ...)` in each route |
| **P0-10e** | Role hierarchy checks (flat, no Casbin hierarchy) | ✅ Done | Dev | `current_user.role not in ("CHIEF_ACCOUNTANT",)` pattern |
| **P0-10f** | AUDITOR read-only (no write/delete policies) | ✅ Done | Dev | `if current_user.role == "AUDITOR" + write_method: abort(403)` |
| **P1-02** | MFA on privileged roles | ❌ Not implemented (separate ticket) | Security Lead | Flask-Security-Too MFA config |
| **P2-06** | Password policy enforcement | ❌ Not implemented (separate) | Security Lead | Password complexity, rotation |

**PRODUCTION GATE**: All **P0** gates must be ✅ (green) before any staging deploy. **P1/P2** can be β (beta) with documented risk acceptance.

### 8.1 Pre-Deployment Checklist

```
[ ] P0-10: @login_required on ALL API routes
[ ] P0-10: current_user.role check on each route (ADMIN/CHIEF_ACCOUNTANT/ACCOUNTANT/AUDITOR/DIRECTOR)
[ ] P0-10: abort(403) when role check fails
[ ] P0-10: AuditLogService.create(entity_type="RBAC", ...) called after each RBAC decision
[ ] P0-10: AUDITOR read-only enforcement (no write/delete methods allowed)
[ ] P0-10: SoD rules enforced via role checks (S-01 through S-04)
[ ] P0-11: `from flask_login import login_required, current_user` imported in routes
[ ] P0-12: RBAC BRD §10 updated: Flask built-in only, no pycasbin
[ ] P0-13: RBAC Specs §7-8 updated: Flask built-in only, no casbin_model.conf / rbac_policy.csv
```

---