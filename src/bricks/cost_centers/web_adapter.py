"""Cost centers & dimensions web adapter."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.cost_centers.domain import DimensionType
from src.bricks.cost_centers.services import (
    DuplicateCodeError,
    InvalidTransitionError,
    NotFoundError,
)

cost_centers_bp = Blueprint("cost_centers", __name__)

_cc_service: Any = None
_dim_service: Any = None
_dv_service: Any = None


def init_cost_center_service(svc: Any) -> None:
    global _cc_service
    _cc_service = svc


def init_dimension_service(svc: Any) -> None:
    global _dim_service
    _dim_service = svc


def init_dimension_value_service(svc: Any) -> None:
    global _dv_service
    _dv_service = svc


def _svc() -> Any:
    s = _cc_service
    if s is None:
        abort(500, description="CostCenterService not initialized")
    return s


def _dim_svc() -> Any:
    s = _dim_service
    if s is None:
        abort(500, description="DimensionService not initialized")
    return s


def _dv_svc() -> Any:
    s = _dv_service
    if s is None:
        abort(500, description="DimensionValueService not initialized")
    return s


WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN")
CLOSE_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN")
AUTO_SEED_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")
FY_ADMIN_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")


def _write(close: bool = False) -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    allowed = CLOSE_ROLES if close else WRITE_ROLES
    if role not in allowed:
        abort(403)


def _require_roles(roles: tuple[str, ...]) -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    if role not in roles:
        abort(403)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------


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


def ser_dim(d: Any) -> dict[str, Any]:
    return {
        "id": str(d.id),
        "code": d.code,
        "name": d.name,
        "type": d.type.value,
        "is_system": d.is_system,
        "description": d.description or "",
        "checksum": d.audit_checksum,
    }


def ser_dv(dv: Any) -> dict[str, Any]:
    return {
        "id": str(dv.id),
        "code": dv.code,
        "name": dv.name,
        "status": dv.status.value,
        "is_active": dv.is_active,
        "dimension_id": str(dv.dimension_id),
        "description": dv.description or "",
        "checksum": dv.audit_checksum,
    }


# ---------------------------------------------------------------------------
# Cost Center endpoints
# ---------------------------------------------------------------------------


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
            actor=UUID(str(current_user.id)),
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
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "close",
        )
    except (InvalidTransitionError, NotFoundError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_TRANSITION"}), 409
    except ValueError as exc:
        abort(422, description=str(exc))
    return jsonify({"data": ser_cc(out)}), 200


# ---------------------------------------------------------------------------
# Dimension endpoints
# ---------------------------------------------------------------------------


@cost_centers_bp.get("/api/v1/dimensions")
@login_required  # type: ignore[untyped-decorator]
def list_dimensions() -> tuple[Any, int]:
    try:
        cid = UUID(request.args.get("company_id", ""))
    except ValueError:
        abort(422, description="company_id required")
    dim_type = request.args.get("type")
    is_system_raw = request.args.get("is_system")
    is_system = None
    if is_system_raw is not None:
        is_system = is_system_raw.lower() in ("true", "1", "yes")
    rows = _dim_svc().list_by_company(cid, dimension_type=dim_type, is_system=is_system)
    return jsonify({"data": [ser_dim(x) for x in rows]}), 200


@cost_centers_bp.post("/api/v1/dimensions")
@login_required  # type: ignore[untyped-decorator]
def create_dimension() -> tuple[Any, int]:
    _require_roles(AUTO_SEED_ROLES)
    body = request.get_json(silent=True) or {}
    try:
        dim = _dim_svc().create(
            company_id=UUID(body["company_id"]),
            code=body["code"],
            name=body.get("name", ""),
            dimension_type=DimensionType(body["dimension_type"]),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create",
            description=body.get("description"),
            is_system=body.get("is_system", False),
        )
    except DuplicateCodeError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_DIMENSION"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_DIMENSION"}), 422
    return jsonify({"data": ser_dim(dim)}), 201


@cost_centers_bp.patch("/api/v1/dimensions/<did>")
@login_required  # type: ignore[untyped-decorator]
def modify_dimension(did: str) -> tuple[Any, int]:
    _require_roles(FY_ADMIN_ROLES)
    body = request.get_json(silent=True) or {}
    try:
        dim = _dim_svc().modify(
            UUID(did),
            new_name=body.get("name", ""),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "modify",
        )
    except (InvalidTransitionError, NotFoundError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_TRANSITION"}), 409
    except ValueError as exc:
        abort(422, description=str(exc))
    return jsonify({"data": ser_dim(dim)}), 200


@cost_centers_bp.post("/api/v1/dimensions/<did>/set-system")
@login_required  # type: ignore[untyped-decorator]
def set_system_dimension(did: str) -> tuple[Any, int]:
    _write(close=True)
    body = request.get_json(silent=True) or {}
    try:
        dim = _dim_svc().set_system(
            UUID(did),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "set_system",
        )
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except ValueError as exc:
        abort(422, description=str(exc))
    return jsonify({"data": ser_dim(dim)}), 200


# ---------------------------------------------------------------------------
# Dimension Value endpoints
# ---------------------------------------------------------------------------


@cost_centers_bp.get("/api/v1/dimension-values")
@login_required  # type: ignore[untyped-decorator]
def list_dimension_values() -> tuple[Any, int]:
    try:
        cid = UUID(request.args.get("company_id", ""))
    except ValueError:
        abort(422, description="company_id required")
    dim_id_raw = request.args.get("dimension_id")
    dim_id = UUID(dim_id_raw) if dim_id_raw else None
    status = request.args.get("status")
    rows = _dv_svc().list_by_company(cid, dimension_id=dim_id, status=status)
    return jsonify({"data": [ser_dv(x) for x in rows]}), 200


@cost_centers_bp.post("/api/v1/dimension-values")
@login_required  # type: ignore[untyped-decorator]
def create_dimension_value() -> tuple[Any, int]:
    _require_roles(AUTO_SEED_ROLES)
    body = request.get_json(silent=True) or {}
    try:
        dv = _dv_svc().create(
            company_id=UUID(body["company_id"]),
            dimension_id=UUID(body["dimension_id"]),
            code=body["code"],
            name=body.get("name", ""),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create",
            description=body.get("description"),
        )
    except DuplicateCodeError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_DIMENSION_VALUE"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_DIMENSION_VALUE"}), 422
    return jsonify({"data": ser_dv(dv)}), 201


@cost_centers_bp.patch("/api/v1/dimension-values/<dvid>")
@login_required  # type: ignore[untyped-decorator]
def modify_dimension_value(dvid: str) -> tuple[Any, int]:
    _require_roles(FY_ADMIN_ROLES)
    body = request.get_json(silent=True) or {}
    try:
        dv = _dv_svc().modify(
            UUID(dvid),
            new_name=body.get("name", ""),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "modify",
        )
    except (InvalidTransitionError, NotFoundError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_TRANSITION"}), 409
    except ValueError as exc:
        abort(422, description=str(exc))
    return jsonify({"data": ser_dv(dv)}), 200


@cost_centers_bp.post("/api/v1/dimension-values/<dvid>/deactivate")
@login_required  # type: ignore[untyped-decorator]
def deactivate_dimension_value(dvid: str) -> tuple[Any, int]:
    _require_roles(CLOSE_ROLES)
    body = request.get_json(silent=True) or {}
    try:
        dv = _dv_svc().deactivate(
            UUID(dvid),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "deactivate",
        )
    except (InvalidTransitionError, NotFoundError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_TRANSITION"}), 409
    except ValueError as exc:
        abort(422, description=str(exc))
    return jsonify({"data": ser_dv(dv)}), 200


@cost_centers_bp.post("/api/v1/dimension-values/<dvid>/reactivate")
@login_required  # type: ignore[untyped-decorator]
def reactivate_dimension_value(dvid: str) -> tuple[Any, int]:
    _require_roles(CLOSE_ROLES)
    body = request.get_json(silent=True) or {}
    try:
        dv = _dv_svc().reactivate(
            UUID(dvid),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "reactivate",
        )
    except (InvalidTransitionError, NotFoundError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_TRANSITION"}), 409
    except ValueError as exc:
        abort(422, description=str(exc))
    return jsonify({"data": ser_dv(dv)}), 200
