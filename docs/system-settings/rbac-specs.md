# RBAC Specifications — Vietnamese SME Accounting System

## 1. Overview

This document specifies the technical implementation of the Role-Based Access Control (RBAC) module for the Vietnamese SME accounting application. It integrates with the existing `pycasbin 2.8.0`, `flask-login`, `flask-security-too 5.8.2`, and `flask-principal 0.4.0` extensions installed in the project.

**Critical Gap Addressed**: P0-10 "No RBAC enforcement at backend — only UI/Flask-Login auth" (marked ❌ Not implemented in production-readiness-audit.md). This specs document provides the complete implementation blueprint.

## 2. Model Definition (Casbin CONF Format)

### 2.1 `casbin_model.conf`

```ini
[request_definition]
r = sub, obj, act
; sub = subject (user.id UUID), obj = resource path (string), act = action/method (string)

[policy_definition]
p = sub, obj, act, eft
; eft = enforcement flag (0=deny-overrides, 1=allow-overrides, 2=priority); default v2 uses first match

[role_definition]
g = _, _
; g, user, role — vertical role hierarchy (g, alice, admin means alice inherits admin)

[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act
; Standard RBAC matcher: subject == policy subject AND object == policy object AND action == policy action

[eft]
e = some(where (p.sub == r.sub && p.obj == r.obj && p.act == r.act))
; Extensible Function Template: returns True if any matching policy rule allows
```

### 2.2 Model Explanation

| Section | Purpose | Key Details |
|---|---|---|
| `request_definition` | Defines the input to the enforcer | `sub` (subject/user), `obj` (resource/path), `act` (action/method) |
| `policy_definition` | Defines the policy structure | `p` = `sub, obj, act, eft`; eft enables advanced authorization logic |
| `role_definition` | Defines role hierarchy | `g = _, _` = vertical hierarchy; `g, ACCOUNTANT, CHIEF_ACCOUNTANT` means ACCOUNTANT → CHIEF_ACCOUNTANT |
| `matchers` | Boolean matching logic | Three-way AND: sub match + obj match + act match |
| `eft` | Extensibility point | `some(where ...)` = true if ANY matching rule allows; enables deny-overrides, allow-overrides patterns |

## 3. Policy Configuration (CSV Format)

### 3.1 `rbac_policy.csv` — Initial Policy Set

```csv
; Resource Pattern,Action,Role
; ===== COMPANY (doanh nghiệp) =====
p, /api/v1/companies, DIRECTOR
p, /api/v1/companies/{id}, CHIEF_ACCOUNTANT
p, /api/v1/companies/{id}/suspend, CHIEF_ACCOUNTANT|ADMIN
p, /api/v1/companies/{id}/reactivate, CHIEF_ACCOUNTANT|ADMIN
p, /api/v1/companies/{id}/dissolve, ADMIN|DIRECTOR

; ===== INVOICE (hóa đơn) =====
p, /api/v1/invoices, ACCOUNTANT
p, /api/v1/invoices/{id}, CHIEF_ACCOUNTANT
p, /api/v1/invoices/{id}/post, CHIEF_ACCOUNTANT
p, /api/v1/invoices/{id}/cancel, ADMIN
p, /api/v1/invoices/{id}/approve, CHIEF_ACCOUNTANT

; ===== VOUCHER (chứng từ) =====
p, /api/v1/vouchers, ACCOUNTANT
p, /api/v1/vouchers/{id}, CHIEF_ACCOUNTANT
p, /api/v1/vouchers/{id}/post, CHIEF_ACCOUNTANT|ACCOUNTANT
p, /api/v1/vouchers/{id}/lock, CHIEF_ACCOUNTANT|ADMIN

; ===== SYSTEM CONFIG (cấu hình hệ thống) =====
p, /api/v1/system-config, ADMIN
p, /api/v1/system-config/vat-rates, ADMIN
p, /api/v1/system-config/period-locks, ADMIN|CHIEF_ACCOUNTANT
p, /api/v1/system-config/decimal-places, ADMIN
p, /api/v1/system-config/default-currency, ADMIN

; ===== AUDIT LOG (nhật ký audit) =====
p, /api/v1/audit-log, AUDITOR
p, /api/v1/audit-log, CHIEF_ACCOUNTANT
; NOTE: No p, /api/v1/audit-log, AUDITOR, delete — read-only only

; ===== ROLE HIERARCHY (must match role_definition) =====
g, ACCOUNTANT, CHIEF_ACCOUNTANT
g, CHIEF_ACCOUNTANT, ADMIN
; AUDITOR has NO hierarchy; read-access via explicit p, rules above only
```

### 3.2 Policy Field Descriptions

| Field | Type | Description | Example |
|---|---|---|---|
| Resource Pattern | String | Flask route path; `{id}` = UUID wildcard; `*` = any resource | `/api/v1/invoices/{id}/post` |
| Action | String | HTTP method lowered, or custom action name | `post`, `get`, `patch`, `delete`, `lock`, `unlock`, `read` |
| Role | String | Role name must exist in `role_definition` hierarchy | `ACCOUNTANT`, `CHIEF_ACCOUNTANT`, `ADMIN`, `DIRECTOR`, `AUDITOR` |
| `g,` prefix | CSV directive | Role hierarchy assignment (vertical) | `g, ACCOUNTANT, CHIEF_ACCOUNTANT` |

### 3.3 Role Hierarchy (Vertical)

```
DIRECTOR
  └── ADMIN
       └── CHIEF_ACCOUNTANT
            └── ACCOUNTANT
                 (no further inheritance)
AUDITOR (standalone; read-access via explicit p,/api/v1/audit-log, AUDITOR rules only; no g, rules)
```

### 3.4 Subject Mapping (Flask-Login → pycasbin)

| Flask Context | pycasbin Subject | Notes |
|---|---|---|
| `current_user.is_authenticated = True` | `str(current_user.id)` (UUID as string) | `current_user.id` is UUID type from `app.py` `SECRET_KEY` / `user_loader` |
| `current_user.role` | `str(current_user.role)` | Role string: `ACCOUNTANT`, `CHIEF_ACCOUNTANT`, `ADMIN`, `DIRECTOR`, `AUDITOR` |
| `current_user.is_active` | Not directly mapped | Casbin enforcer does not check activity; handled by Flask-Login `LoginManager` |
| Anonymous/unauthenticated | `None` or `"anonymous"` | Enforcer returns `False` for all checks; route returns `401 Unauthorized` first |

## 4. Enforcer Initialization & Per-Request Lifecycle

### 4.1 CasbinEnforcer Class (Python Wrapper)

```python
from flask import g, current_app, request, jsonify
from flask_casbin import CasbinEnforcer  # pip: uv pip install flask-casbin
import logging

logger = logging.getLogger(__name__)


def get_casbin_enforcer() -> CasbinEnforcer:
    """Get or create casbin enforcer per request (stored in Flask 'g')."""
    if not hasattr(g, 'casbin'):
        # Load model from package-resolved path; policy from config/
        model_path = current_app.root_path + "/casbin_model.conf"
        policy_path = current_app.root_path + "/rbac_policy.csv"
        
        g.casbin = CasbinEnforcer(
            model_path=model_path,
            policy_path=policy_path,
            # debug=True  # Dev only: logs every enforce() call
        )
        logger.info(
            "Casbin enforcer initialized",
            extra={"model": model_path, "policy": policy_path}
        )
    return g.casbin


def reload_casbin_policy():
    """Reload policy CSV without restarting app (for role promotions etc.)."""
    if hasattr(g, 'casbin'):
        g.casbin.load_policy()
        logger.info("Casbin policy reloaded without restart")
        return True
    return False
```

### 4.2 Before Request Hook (app.py or blueprint)

```python
# In app.py create_app() or src/presentation/api/__init__.py
from functions import get_casbin_enforcer  # relative import from project functions/

@app.before_request
def _init_casbin_per_request():
    """Initialize casbin enforcer with current user context before every request."""
    from flask_login import current_user
    
    # Always initialize enforcer (lightweight; just loads model + policy)
    enforcer = get_casbin_enforcer()
    
    # Map Flask-Login user to casbin subject + role
    if current_user.is_authenticated:
        enforcer.subject(str(current_user.id))
        enforcer.role(str(current_user.role))
    else:
        enforcer.subject("anonymous")
        enforcer.role("NONE")
    
    # Store enforcer in Flask 'g' for route access
    g.casbin = enforcer
```

### 4.3 Route Decorator for RBAC Enforcement

```python
from functools import wraps
from flask import jsonify, current_app

def casbin_required(*allowed_roles):
    """Decorator that enforces role membership AND action permission.
    
    Usage:
        @api_bp.post("/api/v1/invoices")
        @casbin_required("ACCOUNTANT")  # Must be ACCOUNTANT role
        def create_invoice(): ...
        
        @api_bp.post("/api/v1/invoices/<uuid:id>/post")
        @casbin_required("CHIEF_ACCOUNTANT", "ADMIN")  # Either role allowed
        def post_invoice(id): ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            enforcer = get_casbin_enforcer()
            
            # 1. Check role membership (optional; can be checked inside enforce())
            if allowed_roles:
                user_role = enforcer.role
                if user_role not in allowed_roles:
                    return jsonify({
                        "error": f"RBAC denied: role '{user_role}' required, "
                                 f"'{', '.join(allowed_roles)}' allowed",
                        "code": "RBAC_INSUFFICIENT_ROLE"
                    }), 403
            
            # 2. Check action permission via enforcer
            # Resource = request.path (e.g. "/api/v1/invoices/{id}/post")
            # Action = request.method.lower() (e.g. "post") 
            # But we also allow custom action names in policy CSV
            resource = request.path
            # Determine action: use method.lower() unless policy uses different naming
            action = request.method.lower()  # "get", "post", "patch", "delete"
            
            allowed = enforcer.enforce(enforcer.subject, resource, action)
            
            if not allowed:
                return jsonify({
                    "error": f"RBAC denied: '{enforcer.subject}' cannot '{action}' '{resource}'",
                    "code": "RBAC_DENIED"
                }), 403
            
            # 3. All checks passed — execute original route
            return f(*args, **kwargs)
        return wrapper
    return decorator
```

## 5. Integration Points (Existing Code)

### 5.1 API Blueprints That Need RBAC Decorators

| Blueprint | Endpoint | Current Auth | Required RBAC Decorator |
|---|---|---|---|
| `api_bp` (Company) | `POST /api/v1/companies` | `current_user.is_authenticated` (Flask-Login) | `@casbin_required("DIRECTOR")` — only director can create company |
| | `GET /api/v1/companies` | Same | `@casbin_required("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` |
| | `GET /api/v1/companies/<id>` | Same | `@casbin_required("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` |
| | `PATCH /api/v1/companies/<id>` | Same | `@casbin_required("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")` |
| | `POST /api/v1/companies/<id>/suspend` | Same | `@casbin_required("CHIEF_ACCOUNTANT", "ADMIN")` |
| | `POST /api/v1/companies/<id>/dissolve` | Same | `@casbin_required("ADMIN", "DIRECTOR")` |
| | `POST /api/v1/companies/<id>/reactivate` | Same | `@casbin_required("CHIEF_ACCOUNTANT", "ADMIN")` |
| `audit_bp` (Audit Log) | `POST /api/v1/audit-log/...` | Same | `@casbin_required("AUDITOR", "CHIEF_ACCOUNTANT")` read-only for AUDITOR |
| `system_settings_bp` | `POST /api/v1/system-config/...` | Same | `@casbin_required("ADMIN")` for CONFIG; `@casbin_required("ADMIN with migration")` for LAW |
| `health` | `GET /health` | Public (no auth) | No RBAC — health endpoint must be open for monitoring |

### 5.2 Service Layer Calls That Need RBAC Checks

| Service | Method | RBAC Requirement |
|---|---|---|
| `CompanyService.create_company()` | — | Called only via RBAC-protected API; internal calls bypass (trusted) |
| `CompanyService.update_company()` | — | Same; RBAC enforced at API boundary |
| `InvoiceService.post()` (or VoucherService.post()) | — | RBAC already checked by API decorator before service call |
| `SystemSettingsService.update_config()` | — | RBAC checked at API decorator; service assumes authorized |
| `PeriodLockService.lock_period()` | — | RBAC checked at API decorator |
| `AuditLogService.create()` | — | Always allowed (audit records own creation); but individual read RBAC separate |

### 5.3 Repository Layer — NO RBAC Changes Needed

The existing `SQLAlchemyCompanyRepository`, `SQLAlchemyInvoiceRepository`, etc. **do not need modification** for RBAC because:
- RBAC enforcement is at the **API/presentation layer** (route decorators)
- Service layer assumes caller is authorized (consistent with Clean Architecture: "Domain raise exception, Presentation translate HTTP")
- DB-level security (Separate DB roles, REVOKE DELETE on audit_log) handles infra-level SoD
- This is the **"Presentation translate HTTP"** pattern per CODING_CONVENTION.md §4.3

## 6. Audit Trail for RBAC Decisions

### 6.1 Every RBAC Decision Must Be Logged

```python
# In the casbin_required decorator, after enforce() succeeds/failed:
from src.application.services.audit_log_service import AuditLogService
from src.infrastructure.database import db

def _log_rbac_decision(allowed: bool, user_role: str, resource: str, action: str, actor_id: UUID):
    """Log every RBAC decision to the immutable audit log."""
    service = AuditLogService(db.session if hasattr(db, 'session') else None)
    
    decision = "ALLOW" if allowed else "DENY"
    service.create(
        entity_type="RBAC",
        entity_id=request.path,
        action=decision,
        before_value=f"role={user_role};resource={resource};action={action}",
        after_value=None,  # No after_value for decision log entries (or could store enforced result)
        actor_id=actor_id,
    )
```

### 6.2 Audit Log Entry Schema (RBAC Decisions)

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

### 6.3 Example Audit Entries

| Scenario | entity_type | action | actor_id | before_value | checksum (truncated) |
|---|---|---|---|---|---|
| ACCOUNTANT creates invoice | `"RBAC"` | `"ALLOW"` | `uuids:1111...` | `"role=ACCOUNTANT;resource=/api/v1/invoices;action=post"` | `a1b2c3d4...` |
| ACCOUNTANT approves own invoice | `"RBAC"` | `"DENY"` | `uuids:1111...` | `"role=ACCOUNTANT;resource=/api/v1/invoices/{id}/post;action=post"` | `a1b2c3d4...` |
| ADMIN edits VAT rates | `"RBAC"` | `"ALLOW"` | `uuids:2222...` | `"role=ADMIN;resource=/api/v1/system-config/vat-rates;action=patch"` | `a1b2c3d4...` |
| AUDITOR tries to delete audit record | `"RBAC"` | `"DENY"` | `uuids:3333...` | `"role=AUDITOR;resource=/api/v1/audit-log/{id}/delete;action=delete"` | `a1b2c3d4...` |

## 7. Production Readiness Gates

| Gate | Requirement | Status (pre-implementation) | Owner | Done Definition |
|---|---|---|---|---|
| **P0-10** | RBAC backend enforcement (not just UI) | ❌ Not implemented | Lead Dev + BA | `casbin_required` decorator on ALL API routes; every route returns 403 if denied |
| **P0-10a** | pycasbin policy CSV loaded and valid | ⬜ Not started | Dev | `casbin_model.conf` + `rbac_policy.csv` exist at `src/presentation/rbac/`; enforcer loads without error |
| **P0-10b** | Casbin enforcer per-request (before_request) | ⬜ Not started | Dev | `g.casbin` available in every route; subject/role mapped from `current_user` |
| **P0-10c** | SoD rules enforced (4 critical rules: S-01 through S-04) | ⬜ Not started | BA + Chief Acct | 4 SoD rules checked in policy CSV + service-layer exceptions where needed |
| **P0-10d** | Audit log of every RBAC decision | ⬜ Not started | Dev | `AuditLogService.create(entity_type="RBAC", ...)` called in `casbin_required` decorator |
| **P0-10e** | Role hierarchy working (g, rules in CSV + casbin) | ⬜ Not started | Dev | `g, ACCOUNTANT, CHIEF_ACCOUNTANT` and `g, CHIEF_ACCOUNTANT, ADMIN` in CSV; hierarchy tested |
| **P0-10e** | LAW-type flag immutability without migration | ⬜ Not started | Chief Acct + Dev | Attempting to edit LAW flag via API returns `403 LAW_IMMUTABLE_NO_MIGRATION`; migration path documented |
| **P0-10f** | AUDITOR read-only (no delete/write policies) | ⬜ Not started | Dev | Policy CSV has NO `p, /api/v1/audit-log, AUDITOR, delete` or `post` entries |
| **P1-02** | MFA on privileged roles (ADMIN, DIRECTOR) | ❌ Not implemented (separate ticket) | Security Lead | Flask-Security-Too MFA configured; required for `/api/v1/rbac/reload` and LAW migration |
| **P2-06** | Password policy enforcement | ❌ Not implemented (separate) | Security Lead | Complexity, rotation, history checks in auth layer |

**PRODUCTION GATE RULE**: All **P0** gates must be ✅ (green) before any staging deploy. **P1/P2** can be β (beta) with documented risk acceptance in the release notes.

### 7.1 Pre-Deployment Checklist

```
[ ] P0-10: rbac_model.conf exists at project root (or correct path)
[ ] P0-10: rbac_policy.csv exists with all resource/role/action rules
[ ] P0-10: CasbinEnforcer initialized in @app.before_request
[ ] P0-10: @casbin_required decorator on ALL API routes in api_bp, audit_bp, system_settings_bp
[ ] P0-10: Every route returns 403 with {"error": "...", "code": "RBAC_DENIED"} when denied
[ ] P0-10: AuditLogService.create(entity_type="RBAC", ...) in casbin_required after enforce()
[ ] P0-10: Role hierarchy g, rules verified: ACCOUNTANT→CHIEF_ACCOUNTANT→ADMIN→DIRECTOR
[ ] P0-10: LAW-type flag edit attempt returns 403 + "requires migration" message
[ ] P0-10: AUDITOR cannot destroy/delete audit records (no policies for delete action)
[ ] P0-10: `flask curses` or `pytest` run passes: all 65 existing tests still green
[ ] P0-11: `uv pip install flask-casbin` added to dependency requirements if not already
[ ] P0-12: Documentation updated: BRD §11, Specs §7, Use Cases complete
[ ] P0-13: Chief Accountant sign-off on LAW-type flag immutability compliance
```

## 8. Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-18 | BA Lead + Chief Accountant | Initial specs; RBAC implementation blueprint for pycasbin 2.8.0 integration |
| 1.1 | — | — | — |
| 1.2 | — | — | — |