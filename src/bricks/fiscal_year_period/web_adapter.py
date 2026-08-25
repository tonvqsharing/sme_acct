"""Fiscal year read API."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user

fiscal_year_bp = Blueprint("fiscal_year", __name__)

_fy_service: Any = None


def init_fy_service(svc: Any) -> None:
    global _fy_service
    _fy_service = svc


def _svc() -> Any:
    s = _fy_service
    if s is None:
        abort(500, description="FiscalYearService not initialized")
    return s


def _authed() -> None:
    from flask_login import current_user

    if not current_user.is_authenticated:
        abort(401)


@fiscal_year_bp.get("/api/v1/fiscal-years")
def list_years() -> tuple[Any, int]:
    _authed()
    try:
        cid = UUID(request.args.get("company_id", ""))
    except ValueError:
        abort(422, description="company_id required")
    years = _svc()._fy.get_by_company(cid)
    return (
        jsonify(
            {
                "data": [
                    {
                        "id": str(y.id),
                        "name": y.name,
                        "start_date": y.start_date.isoformat(),
                        "end_date": y.end_date.isoformat(),
                        "status": y.status.value,
                    }
                    for y in years
                ]
            }
        ),
        200,
    )


@fiscal_year_bp.get("/api/v1/fiscal-years/<year_id>/periods")
def list_periods(year_id: str) -> tuple[Any, int]:
    _authed()
    try:
        yid = UUID(year_id)
    except ValueError:
        abort(422, description="Invalid UUID")
    periods = _svc()._periods.get_by_year(yid)
    return (
        jsonify(
            {
                "data": [
                    {
                        "sequence": p.sequence,
                        "start_date": p.start_date.isoformat(),
                        "end_date": p.end_date.isoformat(),
                        "status": p.status.value,
                    }
                    for p in periods
                ]
            }
        ),
        200,
    )


# ─── Write endpoints (onboarding) ──────────────────────────────────────────


class OverlapHTTP(Exception):
    code = "OVERLAPPING_YEAR"


@fiscal_year_bp.post("/api/v1/fiscal-years")
def create_fiscal_year() -> tuple[Any, int]:
    _authed()
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403)
    if role not in ("ADMIN", "CHIEF_ACCOUNTANT"):
        abort(403, description="ADMIN/CHIEF_ACCOUNTANT required")
    body = request.get_json(silent=True) or {}
    from datetime import date as _d

    from src.bricks.fiscal_year_period.services import OverlappingYearError as _OYE

    try:
        fy, periods = _svc().create_year(
            UUID(body["company_id"]),
            name=body.get("name", ""),
            start_date=_d.fromisoformat(body["start_date"]),
            end_date=_d.fromisoformat(body["end_date"]),
            period_frequency=body.get("period_frequency", "MONTHLY"),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create fiscal year",
        )
    except _OYE:
        return jsonify({"error": "Năm tài chính chồng lấn", "code": "OVERLAPPING_YEAR"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_FY"}), 422
    return (
        jsonify(
            {
                "data": {
                    "id": str(fy.id),
                    "name": fy.name,
                    "periods_count": len(periods),
                    "status": fy.status.value,
                }
            }
        ),
        201,
    )


@fiscal_year_bp.errorhandler(OverlapHTTP)
def _overlap_http(e: OverlapHTTP) -> tuple[Any, int]:
    return jsonify({"error": str(e), "code": e.code}), 409
