"""Party web adapter — Tryton party parity."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.party.services import DuplicateCodeError, DuplicateMstError

party_bp = Blueprint("party", __name__)

_party_service: Any = None


def init_party_service(svc: Any) -> None:
    global _party_service
    _party_service = svc


def _svc() -> Any:
    s = _party_service
    if s is None:
        abort(500, description="PartyService not initialized")
    return s


def _require_write() -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    if role not in ("ADMIN", "ACCOUNTANT", "CHIEF_ACCOUNTANT", "DIRECTOR"):
        abort(403)


@party_bp.post("/api/v1/parties")
@login_required  # type: ignore[untyped-decorator]
def create_party() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        p = _svc().create_party(
            company_id=UUID(body["company_id"]),
            code=body["code"],
            name=body["name"],
            mst=body.get("mst"),
            address=body.get("address"),
            phone=body.get("phone"),
            email=body.get("email"),
            is_customer=bool(body.get("is_customer", False)),
            is_supplier=bool(body.get("is_supplier", False)),
            is_employee=bool(body.get("is_employee", False)),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create party",
        )
    except DuplicateCodeError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_CODE"}), 409
    except DuplicateMstError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_MST"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_PARTY"}), 422
    return (
        jsonify(
            {
                "data": {
                    "id": str(p.id),
                    "code": p.code,
                    "name": p.name,
                    "mst": p.mst,
                    "is_customer": p.is_customer,
                    "is_supplier": p.is_supplier,
                    "is_employee": p.is_employee,
                }
            }
        ),
        201,
    )


@party_bp.get("/api/v1/parties")
@login_required  # type: ignore[untyped-decorator]
def list_parties() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    role = request.args.get("role")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    rows = _svc().list_parties(cid, role)
    return (
        jsonify(
            {
                "data": [
                    {
                        "id": str(r.id),
                        "code": r.code,
                        "name": r.name,
                        "mst": r.mst,
                        "is_customer": r.is_customer,
                        "is_supplier": r.is_supplier,
                        "is_employee": r.is_employee,
                    }
                    for r in rows
                ]
            }
        ),
        200,
    )


@party_bp.post("/api/v1/departments")
@login_required  # type: ignore[untyped-decorator]
def create_department() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        d = _svc().create_department(
            company_id=UUID(body["company_id"]),
            code=body["code"],
            name=body["name"],
            parent_id=UUID(body["parent_id"]) if body.get("parent_id") else None,
            manager_id=UUID(body["manager_id"]) if body.get("manager_id") else None,
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create department",
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_DEPARTMENT"}), 422
    return jsonify({"data": {"id": str(d.id), "code": d.code, "name": d.name}}), 201


@party_bp.get("/api/v1/departments")
@login_required  # type: ignore[untyped-decorator]
def list_departments() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    rows = _svc().list_departments(cid)
    return (
        jsonify(
            {
                "data": [
                    {
                        "id": str(r.id),
                        "code": r.code,
                        "name": r.name,
                        "parent_id": str(r.parent_id) if r.parent_id else None,
                    }
                    for r in rows
                ]
            }
        ),
        200,
    )
