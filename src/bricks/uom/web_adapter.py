"""UOM web adapter."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.uom.services import DuplicateCodeError

uom_bp = Blueprint("uom", __name__)

_uom_service: Any = None


def init_uom_service(svc: Any) -> None:
    global _uom_service
    _uom_service = svc


def _svc() -> Any:
    s = _uom_service
    if s is None:
        abort(500, description="UOMService not initialized")
    return s


def _require_write() -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    if role not in ("ADMIN", "ACCOUNTANT", "CHIEF_ACCOUNTANT", "DIRECTOR"):
        abort(403)


@uom_bp.post("/api/v1/uoms")
@login_required  # type: ignore[untyped-decorator]
def create_uom() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        u = _svc().create_uom(
            company_id=UUID(body["company_id"]),
            code=body["code"],
            name=body.get("name", ""),
            factor=Decimal(str(body.get("factor", "1"))),
            base_uom_id=UUID(body["base_uom_id"]) if body.get("base_uom_id") else None,
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create uom",
        )
    except DuplicateCodeError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_CODE"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_UOM"}), 422
    return (
        jsonify(
            {"data": {"id": str(u.id), "code": u.code, "name": u.name, "factor": str(u.factor)}}
        ),
        201,
    )


@uom_bp.get("/api/v1/uoms")
@login_required  # type: ignore[untyped-decorator]
def list_uoms() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    rows = _svc().list_uoms(cid)
    return (
        jsonify(
            {
                "data": [
                    {
                        "id": str(r.id),
                        "code": r.code,
                        "name": r.name,
                        "factor": str(r.factor),
                        "base_uom_id": str(r.base_uom_id) if r.base_uom_id else None,
                    }
                    for r in rows
                ]
            }
        ),
        200,
    )
