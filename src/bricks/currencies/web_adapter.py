"""Currencies web adapter — currency master, exchange rates, revaluation."""

from __future__ import annotations

from datetime import UTC, date
from decimal import Decimal
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.currencies.domain import (
    InvalidCurrencyCodeError,
    InvalidRateError,
    RateType,
)
from src.bricks.currencies.services import (
    DuplicateCurrencyError,
    EmptyRunError,
    PeriodLockedError,
    SodViolationError,
    UnknownRateError,
)
from src.bricks.currencies.services import (
    NotFoundError as CurNotFoundError,
)

currencies_bp = Blueprint("currencies", __name__)

_currency_service: Any = None
_rate_service: Any = None
_reval_service: Any = None


def init_currencies_services(
    currency_svc: Any, rate_svc: Any, reval_svc: Any | None = None
) -> None:
    global _currency_service, _rate_service, _reval_service
    _currency_service = currency_svc
    _rate_service = rate_svc
    _reval_service = reval_svc


def _cur() -> Any:
    s = _currency_service
    if s is None:
        abort(500, description="CurrencyService not initialized")
    return s


def _rates() -> Any:
    s = _rate_service
    if s is None:
        abort(500, description="ExchangeRateService not initialized")
    return s


def _revals() -> Any:
    s = _reval_service
    if s is None:
        abort(500, description="RevaluationService not initialized")
    return s


WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN")


def _require_fx_write() -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    if role not in WRITE_ROLES:
        abort(403)


# ─── Currency master ───────────────────────────────────────────────────────


def ser_cur(c: Any) -> dict[str, Any]:
    return {
        "code": c.code,
        "name": c.name,
        "symbol": c.symbol,
        "decimal_places": c.decimal_places,
        "is_base": c.is_base,
        "is_active": c.is_active,
    }


@currencies_bp.get("/api/v1/currencies")
@login_required  # type: ignore[untyped-decorator]
def list_currencies() -> tuple[Any, int]:
    rows = _cur().all()
    return jsonify({"data": [ser_cur(c) for c in rows]}), 200


@currencies_bp.post("/api/v1/currencies")
@login_required  # type: ignore[untyped-decorator]
def create_currency() -> tuple[Any, int]:
    _require_fx_write()
    body = request.get_json(silent=True) or {}
    try:
        cur = _cur().create(
            code=body["code"],
            name=body.get("name", ""),
            symbol=body.get("symbol", ""),
            decimal_places=int(body.get("decimal_places", 2)),
            actor=UUID(str(current_user.id)),
        )
    except DuplicateCurrencyError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_CURRENCY"}), 409
    except (KeyError, InvalidCurrencyCodeError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_CURRENCY"}), 422
    return jsonify({"data": ser_cur(cur)}), 201


# ─── Exchange rates ────────────────────────────────────────────────────────


def ser_rate(r: Any) -> dict[str, Any]:
    return {
        "currency_code": r.currency_code,
        "rate_type": r.rate_type.value,
        "rate_date": r.rate_date.isoformat(),
        "rate": float(r.rate),
        "source": r.source.value,
    }


@currencies_bp.get("/api/v1/exchange-rates")
@login_required  # type: ignore[untyped-decorator]
def latest_rate() -> tuple[Any, int]:
    args = request.args
    code = args.get("currency_code", "")
    rt_raw = args.get("rate_type", "TRANSFER")
    from datetime import datetime as _dt

    on_raw = args.get("on") or _dt.now(UTC).date().isoformat()  # noqa: DTZ — default today UTC
    try:
        rt = RateType(rt_raw)
        on = date.fromisoformat(on_raw)
    except ValueError as exc:
        abort(422, description=f"invalid param: {exc}")
    try:
        found = _rates().latest(code, rt, on)
    except InvalidRateError as exc:
        return jsonify({"error": str(exc), "code": "NO_RATE"}), 404
    return jsonify({"data": ser_rate(found)}), 200


@currencies_bp.post("/api/v1/exchange-rates")
@login_required  # type: ignore[untyped-decorator]
def add_exchange_rate() -> tuple[Any, int]:
    _require_fx_write()
    body = request.get_json(silent=True) or {}
    try:
        r = _rates().add_rate(
            currency_code=body["currency_code"],
            rate_type=RateType(body.get("rate_type", "TRANSFER")),
            rate_date=date.fromisoformat(body["rate_date"]),
            rate=Decimal(str(body["rate"])),
            source=body.get("source", "MANUAL"),
            actor=UUID(str(current_user.id)),
            note=body.get("note"),
        )
    except InvalidRateError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_RATE"}), 422
    except InvalidCurrencyCodeError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_CURRENCY"}), 422
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_RATE"}), 422
    return jsonify({"data": ser_rate(r)}), 201


# ─── Revaluation runs ──────────────────────────────────────────────────────


def ser_run(run: Any) -> dict[str, Any]:
    total_gain = sum((e.difference for e in run.entries if e.difference > 0), Decimal(0))
    total_loss = sum((-e.difference for e in run.entries if e.difference < 0), Decimal(0))
    return {
        "id": str(run.id),
        "period_start": run.period_start.isoformat(),
        "period_end": run.period_end.isoformat(),
        "rate_date": run.rate_date.isoformat(),
        "status": run.status.value,
        "entries_count": len(run.entries),
        "total_gain": float(total_gain),
        "total_loss": float(total_loss),
        "checksum": run.checksum,
    }


@currencies_bp.post("/api/v1/revaluation-runs")
@login_required  # type: ignore[untyped-decorator]
def create_reval_run() -> tuple[Any, int]:
    """§4: compute entries; auto-reverses prior POSTED overlap."""
    _require_fx_write()
    body = request.get_json(silent=True) or {}
    try:
        run = _revals().create_run(
            UUID(body["company_id"]),
            date.fromisoformat(body["period_start"]),
            date.fromisoformat(body["period_end"]),
            date.fromisoformat(body["rate_date"]),
            actor=UUID(str(current_user.id)),
        )
    except PeriodLockedError:
        return jsonify({"error": "Kỳ đã khóa", "code": "PERIOD_LOCKED"}), 409
    except EmptyRunError:
        return jsonify({"error": "Không có khoản mục ngoại tệ", "code": "EMPTY_RUN"}), 422
    except UnknownRateError as exc:
        return (
            jsonify(
                {
                    "error": f"Thiếu tỷ giá closing cho {exc}",
                    "code": "UNKNOWN_RATE",
                }
            ),
            422,
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_RUN"}), 422
    return jsonify({"data": ser_run(run)}), 201


@currencies_bp.post("/api/v1/revaluation-runs/<rid>/submit")
@login_required  # type: ignore[untyped-decorator]
def submit_reval(rid: str) -> tuple[Any, int]:
    _require_fx_write()
    body = request.get_json(silent=True) or {}
    try:
        run = _revals().submit_for_approval(UUID(rid), UUID(str(current_user.id)))
    except CurNotFoundError:
        abort(404)
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_STATE"}), 409
    del body
    return jsonify({"data": ser_run(run)}), 200


@currencies_bp.post("/api/v1/revaluation-runs/<rid>/approve")
@login_required  # type: ignore[untyped-decorator]
def approve_reval(rid: str) -> tuple[Any, int]:
    role = getattr(current_user, "role", "")
    if role not in ("CHIEF_ACCOUNTANT", "ADMIN"):
        abort(403)
    body = request.get_json(silent=True) or {}
    try:
        run = _revals().approve(UUID(rid), UUID(str(current_user.id)))
    except SodViolationError as exc:
        return jsonify({"error": str(exc), "code": "SOD_VIOLATION"}), 403
    except CurNotFoundError:
        abort(404)
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_STATE"}), 409
    del body
    return jsonify({"data": ser_run(run)}), 200


@currencies_bp.post("/api/v1/revaluation-runs/<rid>/post")
@login_required  # type: ignore[untyped-decorator]
def post_reval(rid: str) -> tuple[Any, int]:
    role = getattr(current_user, "role", "")
    if role not in ("CHIEF_ACCOUNTANT", "ADMIN"):
        abort(403)
    try:
        run = _revals().post(UUID(rid), UUID(str(current_user.id)))
    except ValueError as exc:
        msg = str(exc)
        code = "ALREADY_POSTED" if "POSTED" in msg else "NOT_APPROVED"
        return jsonify({"error": msg, "code": code}), 409
    except CurNotFoundError:
        abort(404)
    return jsonify({"data": ser_run(run)}), 200
