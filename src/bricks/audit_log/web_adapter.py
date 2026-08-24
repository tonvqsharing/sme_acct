from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import login_required

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


@audit_log_bp.get("/api/v1/audit-log")
@login_required  # type: ignore[untyped-decorator]
def query_audit_log() -> tuple[Any, int]:
    """FR-2.1 minimal filter set: entity_type + entity_id."""
    etype = request.args.get("entity_type", "")
    raw_id = request.args.get("entity_id", "")
    if not etype or not raw_id:
        abort(422, description="entity_type and entity_id required")
    try:
        eid = UUID(raw_id)
    except ValueError:
        abort(422, description="Invalid entity_id")
    events = _aud().get_by_entity(etype, eid)
    return (
        jsonify(
            {
                "data": [
                    {
                        "action": e.action,
                        "actor_id": str(e.actor_id),
                        "reason": e.reason,
                        "changed_at": e.changed_at.isoformat(),
                        "prev_checksum": e.prev_checksum[:16],
                        "checksum": e.checksum,
                    }
                    for e in events
                ]
            }
        ),
        200,
    )
