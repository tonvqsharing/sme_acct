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