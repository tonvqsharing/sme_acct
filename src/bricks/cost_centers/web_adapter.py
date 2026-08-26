"""Cost centers web adapter."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.cost_centers.services import (
    DuplicateCodeError,
    InvalidTransitionError,
    NotFoundError,
)

cost_centers_bp = Blueprint("cost_centers", __name__)

_cc_service: Any = None


def init_cost_center_service(svc: Any) -> None:
    global _cc_service
    _cc_service = svc


def _svc() -> Any:
    s = _cc_service
    if s is None:
        abort(500, description="CostCenterService not initialized")
    return s


WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN")
CLOSE_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN")


def _write(close: bool = False) -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    allowed = CLOSE_ROLES if close else WRITE_ROLES
    if role not in allowed:
        abort(403)


def ser_cc(c: Any) -> dict[str, Any]:
    return {
        "id": str(c.id),
        "code": c.code,
        "name": c.name,
        "status": c.status.value,
        "is_active": c.is_active,
        "description": c.description,
        "checksum": c.audit_checksum,
    }


@cost_centers_bp.get("/api/v1/cost-centers")
@login_required  # type: ignore[untyped-decorator]
def list_cost_centers() -> tuple[Any, int]:
    try:
        cid = UUID(request.args.get("company_id", ""))
    except ValueError:
        abort(422, description="company_id required")
    rows = _svc().list_by_company(cid)
    return jsonify({"data": [ser_cc(x) for x in rows]}), 200


@cost_centers_bp.post("/api/v1/cost-centers")
@login_required  # type: ignore[untyped-decorator]
def create_cost_center() -> tuple[Any, int]:
    _write()
    body = request.get_json(silent=True) or {}
    try:
        cc = _svc().create(
            company_id=UUID(body["company_id"]),
            code=body["code"],
            name=body.get("name", ""),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create",
            description=body.get("description"),
            parent_id=UUID(body["parent_id"]) if body.get("parent_id") else None,
        )
    except DuplicateCodeError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_COST_CENTER"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_COST_CENTER"}), 422
    return jsonify({"data": ser_cc(cc)}), 201


@cost_centers_bp.post("/api/v1/cost-centers/<cid>/deactivate")
@login_required  # type: ignore[untyped-decorator]
def deactivate_cc(cid: str) -> tuple[Any, int]:
    _write()
    body = request.get_json(silent=True) or {}
    try:
        out = _svc().deactivate(
            UUID(cid),
            UUID(str(current_user.id)),
            reason=body.get("reason") or "deactivate",
        )
    except (InvalidTransitionError, NotFoundError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_TRANSITION"}), 409
    except ValueError as exc:
        abort(422, description=str(exc))
    return jsonify({"data": ser_cc(out)}), 200


@cost_centers_bp.post("/api/v1/cost-centers/<cid>/close")
@login_required  # type: ignore[untyped-decorator]
def close_cc(cid: str) -> tuple[Any, int]:
    _write(close=True)
    body = request.get_json(silent=True) or {}
    try:
        out = _svc().close(
            UUID(cid),
            UUID(str(current_user.id)),
            reason=body.get("reason") or "close",
        )
    except (InvalidTransitionError, NotFoundError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_TRANSITION"}), 409
    except ValueError as exc:
        abort(422, description=str(exc))
    return jsonify({"data": ser_cc(out)}), 200
