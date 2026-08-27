"""Audit log web adapter — FR-1 (create), FR-2 (query/filter/export), FR-3 (verify)."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

audit_log_bp = Blueprint("audit_log", __name__)

_audit_service: Any = None


def init_audit_service(svc: Any) -> None:
    global _audit_service
    _audit_service = svc


def _aud() -> Any:
    s = _audit_service
    if s is None:
        abort(500, description="AuditLogService not initialized")
    return s


def _parse_uuid(raw: str, field: str) -> UUID:
    try:
        return UUID(raw)
    except ValueError:
        abort(422, description=f"Invalid {field}")
        raise  # unreachable, abort raises; satisfies mypy


def _parse_date(raw: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        pass
    try:
        return datetime.combine(date.fromisoformat(raw), time.min)
    except ValueError:
        abort(422, description=f"Invalid {field} (use ISO format)")
        raise  # unreachable, abort raises; satisfies mypy


def _serialize_event(ev: Any) -> dict[str, Any]:
    return {
        "id": str(ev.id),
        "entity_type": ev.entity_type,
        "entity_id": str(ev.entity_id),
        "action": ev.action,
        "actor_id": str(ev.actor_id),
        "reason": ev.reason,
        "field_name": ev.field_name,
        "before_value": ev.before_value,
        "after_value": ev.after_value,
        "changed_at": ev.changed_at.isoformat(),
        "checksum": ev.checksum,
    }


# ─── POST /api/v1/audit-log — create audit record (FR-1) ──────────────


@audit_log_bp.post("/api/v1/audit-log")
@login_required  # type: ignore[untyped-decorator]
def create_audit_log() -> tuple[Any, int]:
    """Create an audit record (FR-1.1 .. FR-1.5)."""
    body = request.get_json(silent=True) or {}
    required = ("entity_type", "entity_id", "action")
    for field in required:
        if field not in body:
            abort(422, description=f"Missing required field: {field}")
    entity_id = _parse_uuid(body["entity_id"], "entity_id")
    actor_id = (
        _parse_uuid(body["actor_id"], "actor_id")
        if "actor_id" in body
        else UUID(str(current_user.id))
    )
    ev = _aud().append(
        entity_type=body["entity_type"],
        entity_id=entity_id,
        action=body["action"],
        actor_id=actor_id,
        reason=body.get("reason", ""),
        field_name=body.get("field_name"),
        before_value=body.get("before_value"),
        after_value=body.get("after_value"),
    )
    return jsonify({"data": _serialize_event(ev)}), 201


# ─── GET /api/v1/audit-log — query with filters + pagination (FR-2) ────


@audit_log_bp.get("/api/v1/audit-log")
@login_required  # type: ignore[untyped-decorator]
def query_audit_log() -> tuple[Any, int]:
    """Query audit records with filters (FR-2.1) and pagination (FR-2.3)."""
    args = request.args
    entity_type = args.get("entity_type")
    entity_id_raw = args.get("entity_id")
    action = args.get("action")
    actor_id_raw = args.get("actor_id")
    field_name = args.get("field_name")
    start_date_raw = args.get("start_date")
    end_date_raw = args.get("end_date")

    entity_id = _parse_uuid(entity_id_raw, "entity_id") if entity_id_raw else None
    actor_id = _parse_uuid(actor_id_raw, "actor_id") if actor_id_raw else None
    start_date = _parse_date(start_date_raw, "start_date") if start_date_raw else None
    end_date = _parse_date(end_date_raw, "end_date") if end_date_raw else None

    try:
        page = max(1, int(args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(100, max(1, int(args.get("page_size", 50))))
    except (TypeError, ValueError):
        page_size = 50

    result = _aud().query(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        field_name=field_name,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return (
        jsonify(
            {
                "data": [_serialize_event(ev) for ev in result.items],
                "pagination": {
                    "page": result.page,
                    "page_size": result.page_size,
                    "total": result.total,
                },
            }
        ),
        200,
    )


# ─── GET /api/v1/audit-log/verify — integrity check (FR-3) ────────────


@audit_log_bp.get("/api/v1/audit-log/verify")
@login_required  # type: ignore[untyped-decorator]
def verify_audit_chain() -> tuple[Any, int]:
    """Verify checksum chain integrity for an entity (FR-3.1 .. FR-3.4)."""
    entity_type = request.args.get("entity_type", "")
    entity_id_raw = request.args.get("entity_id", "")
    if not entity_type or not entity_id_raw:
        abort(422, description="entity_type and entity_id required")
    entity_id = _parse_uuid(entity_id_raw, "entity_id")
    valid = _aud().verify_chain(entity_type, entity_id)
    events = _aud().get_by_entity(entity_type, entity_id)
    return (
        jsonify(
            {
                "data": {
                    "valid": valid,
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "checked_records": len(events),
                    "root_hash": events[0].prev_checksum if events else None,
                }
            }
        ),
        200,
    )
