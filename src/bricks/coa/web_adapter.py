"""COA read API — any authenticated role (AUDITOR included)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request

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
