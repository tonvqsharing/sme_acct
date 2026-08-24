"""Fiscal year read API."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request

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
