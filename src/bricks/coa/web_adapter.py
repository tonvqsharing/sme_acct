"""COA read API — any authenticated role (AUDITOR included)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user

coa_bp = Blueprint("coa", __name__)

_coa_service: Any = None


def init_coa_service(svc: Any) -> None:
    global _coa_service
    _coa_service = svc


def _svc() -> Any:
    s = _coa_service
    if s is None:
        abort(500, description="AccountService not initialized")
    return s


def _ser(a: Any) -> dict[str, Any]:
    return {
        "code": a.code,
        "name": a.name,
        "parent_code": a.parent_code,
        "normal_balance": a.normal_balance.value,
        "status": a.status.value,
        "is_detail": a.is_detail,
    }


def _company() -> UUID:
    try:
        return UUID(request.args.get("company_id", ""))
    except ValueError:
        abort(422, description="company_id required")


@coa_bp.get("/api/v1/accounts")
# login_required added at registration via app-level? keep explicit below
def list_accounts() -> tuple[Any, int]:
    from flask_login import current_user

    if not current_user.is_authenticated:
        abort(401)
    rows = _svc().list_accounts(_company())
    return jsonify({"data": [_ser(a) for a in rows]}), 200


@coa_bp.get("/api/v1/accounts/<code>")
def get_account(code: str) -> tuple[Any, int]:
    from flask_login import current_user

    if not current_user.is_authenticated:
        abort(401)
    acc = _svc().get_account(_company(), code)
    if acc is None:
        abort(404, description="Account not found")
    return jsonify({"data": _ser(acc)}), 200


# ─── Write endpoints (onboarding) ──────────────────────────────────────────

from src.bricks.coa.services import (
    AccountNotFoundError,
    AggregateAccountError,
    DuplicateAccountError,
    HasActiveChildrenError,
    InactiveAccountError,
    ParentNotAggregateError,
    ParentNotFoundError,
)

WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN")
CLOSE_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN")


def _require_write(close: bool = False) -> None:
    from flask_login import current_user

    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    allowed = CLOSE_ROLES if close else WRITE_ROLES
    if role not in allowed:
        abort(403)


@coa_bp.post("/api/v1/accounts")
def create_account() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        acc = _svc().create_account(
            UUID(body["company_id"]),
            code=body["code"],
            name=body.get("name", ""),
            normal_balance=body.get("normal_balance", "debit"),
            parent_code=body.get("parent_code"),
            actor=str(current_user.id),
            reason=body.get("reason") or "create account",
            regime=body.get("regime", "tt133"),
        )
    except DuplicateAccountError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_ACCOUNT"}), 409
    except ParentNotFoundError as exc:
        return jsonify({"error": str(exc), "code": "PARENT_NOT_FOUND"}), 422
    except ParentNotAggregateError as exc:
        return jsonify({"error": str(exc), "code": "PARENT_NOT_AGGREGATE"}), 422
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_ACCOUNT"}), 422
    return jsonify({"data": _ser(acc)}), 201


@coa_bp.post("/api/v1/accounts/<code>/deactivate")
def deactivate_account(code: str) -> tuple[Any, int]:
    _require_write(close=True)
    body = request.get_json(silent=True) or {}
    company_raw = body.get("company_id") or request.args.get("company_id", "")
    try:
        company_id = UUID(str(company_raw))
    except ValueError:
        abort(422, description="company_id required")
    try:
        acc = _svc().deactivate_account(
            company_id,
            code,
            actor=str(current_user.id),
            reason=body.get("reason") or "deactivate",
        )
    except HasActiveChildrenError as exc:
        return jsonify({"error": str(exc), "code": "HAS_ACTIVE_CHILDREN"}), 409
    except (AggregateAccountError, AccountNotFoundError, InactiveAccountError) as exc:
        return jsonify({"error": str(exc), "code": "ACCOUNT_STATE_ERROR"}), 409
    return jsonify({"data": _ser(acc)}), 200
