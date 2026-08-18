"""API blueprint — Currencies & Exchange Rates endpoints.

REST-ish endpoints per specs-currencies.md §6. Follows Company API pattern
(api/__init__.py): test-engine hook, service-per-request, @casbin_required
enforcement. AUDITOR read-only; actor UUID required for mutations (D11).

Routes:
- GET  /api/v1/currencies                       list currencies
- POST /api/v1/currencies                       create currency (ADMIN)
- PATCH /api/v1/currencies/<code>               update / deactivate (ADMIN)
- GET  /api/v1/exchange-rates                   rate history
- POST /api/v1/exchange-rates                   create rate
- POST /api/v1/exchange-rates/import            CSV batch import
- POST /api/v1/revaluations                     create DRAFT run
- GET  /api/v1/revaluations/<uuid:id>           run detail
- POST /api/v1/revaluations/<uuid:id>/approve   approve (CHIEF_ACCOUNTANT)
- POST /api/v1/revaluations/<uuid:id>/post      post journal (CHIEF_ACCOUNTANT)
- POST /api/v1/revaluations/<uuid:id>/reverse   reverse (CHIEF_ACCOUNTANT)
- GET  /api/v1/fx-differences                   FX difference report
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import sessionmaker

from src.application.services.currency_service import CurrencyService
from src.application.services.exchange_rate_service import ExchangeRateService
from src.application.services.revaluation_service import RevaluationService
from src.domain.entities.base import RateType
from src.domain.entities.currency import Currency
from src.domain.exceptions import (
    CurrencyError,
    CurrencyNotFoundError,
    FXImportError,
    InvalidCurrencyError,
    InvalidRateError,
    PeriodLockedError,
    RateNotFoundError,
    RevaluationError,
)
from src.infrastructure.database import db
from src.infrastructure.repositories.currency_repo import (
    SQLAlchemyCurrencyRepository,
    SQLAlchemyExchangeRateRepository,
    SQLAlchemyRevaluationRepository,
)
from src.presentation.rbac import casbin_required
from src.presentation.serializers import (
    serialize_currency,
    serialize_exchange_rate,
    serialize_fx_difference,
    serialize_revaluation_run,
)

api_bp = Blueprint("currencies", __name__)

logger = logging.getLogger(__name__)

READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")
RATE_WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT")
REVAL_APPROVE_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")

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
    """Get a session tied to the test engine when set, else fall back to app db."""
    if _test_engine is not None:
        return sessionmaker(bind=_test_engine)()
    return db.session


@api_bp.teardown_request
def _restore_db_session(exc=None):  # noqa: ARG001
    """Restore the real db.session after each request.

    Prevents the swapped plain session from leaking into Flask-SQLAlchemy's
    app-context teardown (AttributeError: 'Session' has no attribute 'remove').
    """
    db.session = _ORIGINAL_SESSION  # type: ignore[assignment]


def _service() -> CurrencyService:
    db.session = _req_session()  # type: ignore[assignment]
    return CurrencyService(currency_repo=SQLAlchemyCurrencyRepository())


def _rate_service() -> ExchangeRateService:
    db.session = _req_session()  # type: ignore[assignment]
    return ExchangeRateService(
        rate_repo=SQLAlchemyExchangeRateRepository(),
        currency_repo=SQLAlchemyCurrencyRepository(),
    )


def _reval_service() -> RevaluationService:
    db.session = _req_session()  # type: ignore[assignment]
    return RevaluationService(
        revaluation_repo=SQLAlchemyRevaluationRepository(),
        rate_repo=SQLAlchemyExchangeRateRepository(),
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


def _get_actor(data: dict) -> tuple[UUID | None, tuple | None]:
    return _require_actor(data)


# ── Currencies ──────────────────────────────────────────────────────────────


@api_bp.get("/v1/currencies")
@casbin_required(*READ_ROLES)
def list_currencies():
    try:
        currencies = _service().list_currencies()
        return jsonify({"currencies": [serialize_currency(c) for c in currencies]})
    except CurrencyError as exc:
        return jsonify({"error": str(exc), "code": "CURRENCY_ERROR"}), 404
    except Exception as exc:  # noqa: BLE001
        logger.exception("list_currencies failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/currencies")
@casbin_required("ADMIN", "DIRECTOR")
def create_currency():
    try:
        data = request.get_json(silent=True) or {}
        is_base = data.get("is_base", False)
        if not isinstance(is_base, bool):
            raise InvalidCurrencyError("is_base phải là boolean")
        currency = Currency(
            code=data.get("code", ""),
            name=data.get("name", ""),
            symbol=data.get("symbol", ""),
            decimal_places=int(data.get("decimal_places", 2)),
            is_base=is_base,
            display_format=data.get("display_format", "{symbol} {amount:,.2f}"),
        )
        saved = _service().create_currency(currency)
        return jsonify({"currency": serialize_currency(saved)}), 201
    except InvalidCurrencyError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_CURRENCY"}), 422
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("create_currency failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.patch("/v1/currencies/<code>")
@casbin_required("ADMIN", "DIRECTOR")
def update_currency(code: str):
    """Update currency metadata or deactivate (is_active=false)."""
    try:
        data = request.get_json(silent=True) or {}
        service = _service()
        existing = service.get_currency(code)
        if data.get("is_active") is False or data.get("deactivate"):
            saved = service.deactivate_currency(code, actor=_actor(data) or UUID(int=0))
        else:
            is_base = data.get("is_base", existing.is_base)
            if not isinstance(is_base, bool):
                raise InvalidCurrencyError("is_base phải là boolean")
            is_active = data.get("is_active", existing.is_active)
            if not isinstance(is_active, bool):
                raise InvalidCurrencyError("is_active phải là boolean")
            saved = service.update_currency(
                Currency(
                    code=code,
                    name=data.get("name", existing.name),
                    symbol=data.get("symbol", existing.symbol),
                    decimal_places=int(data.get("decimal_places", existing.decimal_places)),
                    is_base=is_base,
                    is_active=is_active,
                    display_format=data.get("display_format", existing.display_format),
                )
            )
        return jsonify({"currency": serialize_currency(saved)})
    except CurrencyNotFoundError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except InvalidCurrencyError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_CURRENCY"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("update_currency failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── Exchange rates ──────────────────────────────────────────────────────────


@api_bp.get("/v1/exchange-rates")
@casbin_required(*READ_ROLES)
def list_exchange_rates():
    try:
        args = request.args
        rates = _rate_service().list_history(
            currency_code=args.get("currency"),
            rate_type=RateType(args["type"].lower()) if args.get("type") else None,
            from_date=date.fromisoformat(args["from"]) if args.get("from") else None,
            to_date=date.fromisoformat(args["to"]) if args.get("to") else None,
        )
        return jsonify({"exchange_rates": [serialize_exchange_rate(r) for r in rates]})
    except ValueError as exc:
        return jsonify({"error": f"Tham số không hợp lệ: {exc}", "code": "INVALID_PARAM"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("list_exchange_rates failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/exchange-rates")
@casbin_required(*RATE_WRITE_ROLES)
def create_exchange_rate():
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _get_actor(data)
        if err:
            return err
        assert actor is not None
        rate = _rate_service().create_rate(
            currency_code=data["currency_code"],
            rate_date=date.fromisoformat(data["rate_date"]),
            rate_type=RateType(data["rate_type"].lower()),
            rate=data["rate"],
            source=data.get("source", "MANUAL"),
            actor=actor,
            note=data.get("note"),
        )
        return jsonify({"exchange_rate": serialize_exchange_rate(rate)}), 201
    except (CurrencyNotFoundError, RateNotFoundError) as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except (InvalidRateError, InvalidCurrencyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_RATE"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("create_exchange_rate failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/exchange-rates/import")
@casbin_required(*RATE_WRITE_ROLES)
def import_exchange_rates():
    """CSV batch import (specs §7). Atomic: all-or-nothing."""
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _get_actor(data)
        if err:
            return err
        assert actor is not None
        content = data.get("csv")
        if not content:
            return jsonify({"error": "csv là bắt buộc", "code": "MISSING_FIELD"}), 400
        result = _rate_service().import_csv(content, actor=actor)
        return jsonify({"success": True, **result}), 201
    except FXImportError as exc:
        return jsonify({"error": str(exc), "code": "IMPORT_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("import_exchange_rates failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── Revaluations ────────────────────────────────────────────────────────────


@api_bp.post("/v1/revaluations")
@casbin_required(*RATE_WRITE_ROLES)
def create_revaluation():
    """Create a DRAFT revaluation run (spec §4)."""
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _get_actor(data)
        if err:
            return err
        assert actor is not None
        run = _reval_service().create_run(
            company_id=UUID(data["company_id"]),
            period_start=date.fromisoformat(data["period_start"]),
            period_end=date.fromisoformat(data["period_end"]),
            rate_date=date.fromisoformat(data["rate_date"]),
            monetary_items=data.get("monetary_items", []),
            actor=actor,
        )
        return jsonify({"revaluation_run": serialize_revaluation_run(run)}), 201
    except (PeriodLockedError, RevaluationError) as exc:
        return jsonify({"error": str(exc), "code": "REVALUATION_ERROR"}), 409
    except RateNotFoundError as exc:
        return jsonify({"error": str(exc), "code": "RATE_NOT_FOUND"}), 404
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"Tham số không hợp lệ: {exc}", "code": "INVALID_PARAM"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("create_revaluation failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.get("/v1/revaluations/<uuid:run_id>")
@casbin_required(*READ_ROLES)
def get_revaluation(run_id: UUID):
    try:
        run = _reval_service().get_run(run_id)
        return jsonify({"revaluation_run": serialize_revaluation_run(run)})
    except RevaluationError as exc:
        return jsonify({"error": str(exc), "code": "NOT_FOUND"}), 404
    except Exception as exc:  # noqa: BLE001
        logger.exception("get_revaluation failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/revaluations/<uuid:run_id>/approve")
@casbin_required(*REVAL_APPROVE_ROLES)
def approve_revaluation(run_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _get_actor(data)
        if err:
            return err
        assert actor is not None
        run = _reval_service().approve_run(run_id, approver=actor)
        return jsonify({"success": True, "revaluation_run": serialize_revaluation_run(run)})
    except RevaluationError as exc:
        return jsonify({"error": str(exc), "code": "REVALUATION_ERROR"}), 409
    except Exception as exc:  # noqa: BLE001
        logger.exception("approve_revaluation failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/revaluations/<uuid:run_id>/post")
@casbin_required(*REVAL_APPROVE_ROLES)
def post_revaluation(run_id: UUID):
    try:
        run = _reval_service().post_run(run_id)
        return jsonify({"success": True, "revaluation_run": serialize_revaluation_run(run)})
    except RevaluationError as exc:
        return jsonify({"error": str(exc), "code": "REVALUATION_ERROR"}), 409
    except Exception as exc:  # noqa: BLE001
        logger.exception("post_revaluation failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/revaluations/<uuid:run_id>/reverse")
@casbin_required(*REVAL_APPROVE_ROLES)
def reverse_revaluation(run_id: UUID):
    try:
        run = _reval_service().reverse_run(run_id)
        return jsonify({"success": True, "revaluation_run": serialize_revaluation_run(run)})
    except RevaluationError as exc:
        return jsonify({"error": str(exc), "code": "REVALUATION_ERROR"}), 409
    except Exception as exc:  # noqa: BLE001
        logger.exception("reverse_revaluation failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── FX difference report ────────────────────────────────────────────────────


@api_bp.get("/v1/fx-differences")
@casbin_required(*READ_ROLES)
def list_fx_differences():
    try:
        args = request.args
        company_id = UUID(args["company_id"])
        period_start = date.fromisoformat(args["period_start"])
        period_end = date.fromisoformat(args["period_end"])
        rows = _reval_service().list_fx_differences(company_id, period_start, period_end)
        return jsonify({"fx_differences": [serialize_fx_difference(r) for r in rows]})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"Tham số không hợp lệ: {exc}", "code": "INVALID_PARAM"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("list_fx_differences failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500
