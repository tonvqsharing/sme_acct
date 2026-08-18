"""API blueprint — Fiscal Years & Accounting Periods endpoints.

REST-ish per docs/fiscal-year-period specs §5. Follows currencies_bp
pattern: test-engine hook, service-per-request, @casbin_required, actor
UUID required on mutations (D11). AUDITOR read-only.

Routes:
- GET   /v1/fiscal-years?company_id=          list years
- POST  /v1/fiscal-years                      create year (CHIEF_ACCOUNTANT/ADMIN/DIRECTOR)
- GET   /v1/fiscal-years/<uuid:id>            year detail incl. periods
- POST  /v1/fiscal-years/ensure               idempotent auto-seed for a date
- POST  /v1/fiscal-years/<uuid:id>/close      close year (CHIEF_ACCOUNTANT)
- POST  /v1/periods/<uuid:id>/lock            close period (ACCOUNTANT/CHIEF_ACCOUNTANT)
- POST  /v1/periods/<uuid:id>/unlock          reopen period (CHIEF_ACCOUNTANT)
- GET   /v1/periods/lock-status?company_id=&date=   lock state for a date
- GET   /v1/periods/<uuid:id>/history         lock event chain
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import sessionmaker

from src.application.services.period_lock_service import PeriodLockService
from src.domain.exceptions import (
    FiscalYearError,
    NotFoundError,
)
from src.infrastructure.database import db
from src.infrastructure.repositories.fiscal_year_repo import (
    SQLAlchemyFiscalYearRepository,
    SQLAlchemyPeriodLockRepository,
)
from src.presentation.rbac import casbin_required
from src.presentation.serializers import (
    serialize_accounting_period,
    serialize_fiscal_year,
    serialize_period_lock_event,
)

api_bp = Blueprint("fiscal_year", __name__)

logger = logging.getLogger(__name__)

READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")
LOCK_WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT")
FY_ADMIN_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")
# ensure auto-seeds a fiscal year (write); AUDITOR stays read-only.
AUTO_SEED_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")

# ── Test engine hook (set by tests before making requests) ─────────────────
_test_engine = None
_ORIGINAL_SESSION = db.session


def init_test_engine(engine):
    """Set a shared in-memory SQLite engine for tests."""
    global _test_engine
    _test_engine = engine


def clear_test_engine():
    """Reset test engine after tests."""
    global _test_engine
    _test_engine = None


def _req_session():
    if _test_engine is not None:
        return sessionmaker(bind=_test_engine)()
    return db.session


@api_bp.teardown_request
def _restore_db_session(exc=None):  # noqa: ARG001
    """Restore the real db.session after each request (currencies pattern)."""
    db.session = _ORIGINAL_SESSION  # type: ignore[assignment]


def _service() -> PeriodLockService:
    db.session = _req_session()  # type: ignore[assignment]
    return PeriodLockService(
        fy_repo=SQLAlchemyFiscalYearRepository(),
        lock_repo=SQLAlchemyPeriodLockRepository(),
    )


def _actor(data: dict) -> UUID | None:
    try:
        return UUID(data["actor"]) if data.get("actor") else None
    except (ValueError, TypeError):
        return None


def _require_actor(data: dict):
    actor = _actor(data)
    if actor is None:
        return None, (jsonify({"error": "actor là bắt buộc", "code": "MISSING_ACTOR"}), 400)
    return actor, None


def _as_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


# ── Fiscal years ────────────────────────────────────────────────────────────


@api_bp.get("/v1/fiscal-years")
@casbin_required(*READ_ROLES)
def list_fiscal_years():
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "company_id là bắt buộc", "code": "MISSING_COMPANY"}), 400
    try:
        years = _service()._fy_repo.list_by_company(UUID(company_id))
        return jsonify({"fiscal_years": [serialize_fiscal_year(fy) for fy in years]})
    except (ValueError, TypeError):
        return jsonify({"error": "company_id không hợp lệ", "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("list_fiscal_years failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/fiscal-years")
@casbin_required(*FY_ADMIN_ROLES)
def create_fiscal_year():
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        period_type = data.get("period_type")
        start_date = _as_date(data.get("start_date", ""))
        if start_date is None:
            return (
                jsonify({"error": "start_date (YYYY-MM-DD) bắt buộc", "code": "VALIDATION_ERROR"}),
                422,
            )
        from src.domain.entities.base import AccountingPeriodType

        fy = _service().create_fiscal_year(
            company_id=UUID(data["company_id"]),
            period_type=AccountingPeriodType(period_type),
            start_date=start_date,
            actor=actor,
        )
        return jsonify({"fiscal_year": serialize_fiscal_year(fy)}), 201
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except FiscalYearError as exc:
        return jsonify({"error": str(exc), "code": "FISCAL_YEAR_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("create_fiscal_year failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.get("/v1/fiscal-years/<uuid:fy_id>")
@casbin_required(*READ_ROLES)
def get_fiscal_year(fy_id: UUID):
    try:
        fy = _service()._fy_repo.get_by_id(fy_id)
        if fy is None:
            return jsonify({"error": "Năm tài chính không tồn tại", "code": "NOT_FOUND"}), 404
        return jsonify({"fiscal_year": serialize_fiscal_year(fy)})
    except Exception as exc:  # noqa: BLE001
        logger.exception("get_fiscal_year failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/fiscal-years/ensure")
@casbin_required(*AUTO_SEED_ROLES)
def ensure_fiscal_year():
    try:
        data = request.get_json(silent=True) or {}
        entry_date = _as_date(data.get("entry_date", ""))
        if entry_date is None:
            return (
                jsonify(
                    {"error": "entry_date (YYYY-MM-DD) là bắt buộc", "code": "VALIDATION_ERROR"}
                ),
                422,
            )
        fy = _service().ensure_fiscal_year(
            company_id=UUID(data["company_id"]),
            entry_date=entry_date,
        )
        return jsonify({"fiscal_year": serialize_fiscal_year(fy)})
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("ensure_fiscal_year failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/fiscal-years/<uuid:fy_id>/close")
@casbin_required("CHIEF_ACCOUNTANT")
def close_fiscal_year(fy_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        fy = _service().close_fiscal_year(
            company_id=UUID(data["company_id"]),
            fy_id=fy_id,
            actor=actor,
        )
        return jsonify({"fiscal_year": serialize_fiscal_year(fy)})
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except FiscalYearError as exc:
        return jsonify({"error": str(exc), "code": "FISCAL_YEAR_ERROR"}), 422
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("close_fiscal_year failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── Periods ─────────────────────────────────────────────────────────────────


@api_bp.get("/v1/periods/lock-status")
@casbin_required(*READ_ROLES)
def period_lock_status():
    company_id = request.args.get("company_id")
    entry_date = _as_date(request.args.get("date", ""))
    if not company_id or entry_date is None:
        return (
            jsonify(
                {"error": "company_id + date (YYYY-MM-DD) bắt buộc", "code": "VALIDATION_ERROR"}
            ),
            422,
        )
    try:
        svc = _service()
        period = svc._lock_repo.find_period(UUID(company_id), entry_date)
        locked = svc.is_locked(UUID(company_id), entry_date)
        return jsonify(
            {
                "locked": locked,
                "period": serialize_accounting_period(period) if period else None,
            }
        )
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("period_lock_status failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/periods/<uuid:period_id>/lock")
@casbin_required(*LOCK_WRITE_ROLES)
def lock_period(period_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        event = _service().close_period(
            period_id=period_id,
            actor=actor,
            reason=data.get("reason", ""),
        )
        return jsonify({"event": serialize_period_lock_event(event)}), 201
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except FiscalYearError as exc:
        return jsonify({"error": str(exc), "code": "FISCAL_YEAR_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("lock_period failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/periods/<uuid:period_id>/unlock")
@casbin_required("CHIEF_ACCOUNTANT")
def unlock_period(period_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        event = _service().reopen_period(
            period_id=period_id,
            actor=actor,
            reason=data.get("reason", ""),
        )
        return jsonify({"event": serialize_period_lock_event(event)})
    except NotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except FiscalYearError as exc:
        return jsonify({"error": str(exc), "code": "FISCAL_YEAR_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("unlock_period failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.get("/v1/periods/<uuid:period_id>/history")
@casbin_required(*READ_ROLES)
def period_history(period_id: UUID):
    try:
        events = _service()._lock_repo.history(period_id)
        return jsonify({"events": [serialize_period_lock_event(e) for e in events]})
    except Exception as exc:  # noqa: BLE001
        logger.exception("period_history failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500
