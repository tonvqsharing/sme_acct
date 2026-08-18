"""RBAC enforcement module - pycasbin 2.8.0 integration for Vietnamese SME accounting.

Provides:
- CasbinEnforcer initialized per-request (Flask 'g')
- @casbin_required decorator for route-level RBAC enforcement
- Audit logging of every RBAC decision (entity_type="RBAC")
- Role hierarchy from CSV: g, ACCOUNTANT, CHIEF_ACCOUNTANT, g, CHIEF_ACCOUNTANT, ADMIN

Integrates with:
- Flask-Login: current_user.id (UUID), current_user.role (str)
- Flask-Security-Too: authentication layer
- Flask-Principal: optional fine-grained permissions (future)

Critical: RBAC enforcement is at the API boundary only.
Domain layer (src/domain/) MUST NOT import casbin or this module.
Presentation layer (src/presentation/) uses @casbin_required decorator.
"""
from __future__ import annotations

import hashlib
import logging
import os
from functools import wraps
from uuid import UUID

from flask import g, current_app, request, jsonify
from flask_login import current_user

from src.application.services.audit_log_service import AuditLogService
from src.infrastructure.database import db

logger = logging.getLogger(__name__)


def _casbin_hash(policy_path: str) -> str:
    try:
        with open(policy_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        return "0000000000000000"


def _get_enforcer():
    from functions import CasbinEnforcer
    if not hasattr(g, "casbin"):
        model_path = os.path.join(current_app.root_path, "casbin_model.conf")
        policy_path = os.path.join(current_app.root_path, "rbac_policy.csv")
        g.casbin = CasbinEnforcer(
            model_path=model_path,
            policy_path=policy_path,
        )
        logger.info(
            "Casbin enforcer initialized",
            extra={
                "model": model_path,
                "policy": policy_path,
                "policy_hash": _casbin_hash(policy_path),
            },
        )
    return g.casbin


def _log_rbac_decision(allowed: bool, resource: str, action: str) -> None:
    entity_type = "RBAC"
    action_label = "ALLOW" if allowed else "DENY"
    entity_id = resource
    before_value = f"role={g.casbin.role};resource={resource};action={action}"
    after_value = None
    actor_id = str(current_user.id) if current_user.is_authenticated else "anonymous"
    checksum = hashlib.sha256(
        f"{actor_id}:{resource}:{action}:{g.casbin.role}".encode()
    ).hexdigest()
    from src.application.services.audit_log_service import AuditLogService as _ALS
    from src.infrastructure.database import db as _db
    _als = _ALS(_db.session if _db.session else None)
    _als.create(
        entity_type="RBAC",
        entity_id=resource,
        action=action_label,
        before_value=before_value,
        after_value=after_value,
        actor_id=UUID(actor_id) if actor_id != "anonymous" else None,
        checksum=checksum,
    )


def casbin_required(*allowed_roles: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            enforcer = _get_enforcer()
            if current_user.is_authenticated:
                enforcer.subject(str(current_user.id))
                enforcer.role(str(current_user.role))
            else:
                enforcer.subject("anonymous")
                enforcer.role("NONE")
            if allowed_roles:
                if enforcer.role not in allowed_roles:
                    return jsonify({
                        "error": f"RBAC denied: role '{enforcer.role}' required, "
                                 f"'{', '.join(allowed_roles)}' allowed",
                        "code": "RBAC_INSUFFICIENT_ROLE"
                    }), 403
            resource = request.path
            action = request.method.lower()
            allowed = enforcer.enforce(enforcer.subject, resource, action)
            _log_rbac_decision(allowed, resource, action)
            if not allowed:
                return jsonify({
                    "error": f"RBAC denied: '{enforcer.subject}' cannot '{action}' '{resource}'",
                    "code": "RBAC_DENIED"
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def reload_casbin_policy():
    if hasattr(g, "casbin"):
        g.casbin.load_policy()
        logger.info("Casbin policy reloaded without restart")
        return True
    return False