"""API blueprint — Audit Log Configuration Module endpoints.

Provides full CRUD and query functionality for the immutable audit trail,
integrated with Vietnamese accounting law compliance (Luật Kế toán 2015,
Nghị định 123/2020/NĐ-CP, Nghị định 13/2023/NĐ-CP) and international
standards (ISO 27001, SOC 2, IFRS S2).

Follows Clean Architecture: service layer, NO Flask/SQLAlchemy imports.
"""

from __future__ import annotations

import logging

from flask import Blueprint

from src.application.services.audit_log_service import AuditLogService
from src.infrastructure.database import db

api_bp = Blueprint("audit", __name__, url_prefix="/api/audit")

logger = logging.getLogger(__name__)

# ── Test engine hook (set by tests before making requests) ─────────────────
_test_engine = None


def init_test_engine(engine):
    """Set a shared in-memory SQLite engine for tests."""
    global _test_engine
    _test_engine = engine


def clear_test_engine():
    """Reset test engine after tests."""
    global _test_engine
    _test_engine = None


def _req_session():
    """Get a session tied to the test engine when set, else fall back to app db."""
    if _test_engine is not None:
        return db.Session(bind=_test_engine)
    return db.session


def _service() -> AuditLogService:
    """Build AuditLogService using the current request-bound session."""
    from src.infrastructure.repositories import SQLAlchemyAuditLogRepository
    repo = SQLAlchemyAuditLogRepository()
    return AuditLogService(audit_log_repo=repo)
@api_bp.post("/retention-status")
def retention_status():
    """Get certificate of destruction retention status per Luật Kế toán 2015.

    Returns current retention years, next archival/deletion dates,
    and compliance status for the 10-year minimum retention requirement.
    """
    try:
        service = _service()
        status = service.get_retention_status()
        return {"data": status}, 200
    except Exception as exc:  # noqa: BLE001
        import traceback; traceback.print_exc()
        logger.exception("retention_status failed")
        return {"error": str(exc), "code": "SERVER_ERROR"}, 500


@api_bp.post("/verify-destruction/<uuid:record_id>")
def verify_destruction(record_id):  # noqa: F811
    """Verify if a specific audit record is eligible for destruction.

    Per Luật Kế toán 2015, records must be at least 10 years old
    before destruction is permitted.

    Returns eligibility status and years elapsed since record change.
    """
    try:
        data = request.get_json(silent=True) or {}
        changed_at = data.get("changed_at")

        service = _service()
        result = service.verify_destruction_eligibility(record_id, changed_at or "")
        return {"data": result}, 200
    except Exception as exc:  # noqa: BLE001
        import traceback; traceback.print_exc()
        logger.exception("verify_destruction failed")
        return {"error": str(exc), "code": "SERVER_ERROR"}, 500


@api_bp.post("/destroy", endpoint="destroy_records")
def destroy_records_endpoint():  # noqa: F811
    """Destroy (mark as destroyed) audit records meeting retention requirements.

    Per Luật Kế toán 2015 minimum 10-year retention.
    True physical deletion must occur after the retention period.
    Application-level SoD: SA role cannot perform destruction.
    """
    try:
        data = request.get_json(silent=True) or {}
        record_ids = data.get("record_ids", [])
        actor = data.get("actor", "00000000-0000-0000-0000-000000000000")

        service = _service()
        result = service.destroy_records(record_ids, UUID(actor))
        return {"data": result}, 200
    except Exception as exc:  # noqa: BLE001
        import traceback; traceback.print_exc()
        logger.exception("destroy_records failed")
        return {"error": str(exc), "code": "SERVER_ERROR"}, 500

@api_bp.post("/retention-status")
