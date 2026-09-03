"""Financial Statements web adapter — report endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.financial_statements.services import (
    PeriodAlreadyClosedError,
)

reports_bp = Blueprint("reports", __name__)

_period_close_service: Any = None


def init_period_close_service(svc: Any) -> None:
    global _period_close_service
    _period_close_service = svc


def _close_svc() -> Any:
    s = _period_close_service
    if s is None:
        abort(500, description="PeriodCloseService not initialized")
    return s


@reports_bp.post("/api/v1/reports/close-month")
@login_required  # type: ignore[untyped-decorator]
def close_month() -> tuple[Any, int]:
    """Execute month-end close procedure.

    Request body:
        company_id: str (UUID)
        fiscal_year: int
        period: int (1-12)
        trial_balance: list of {account_code, debit, credit}
        cit_rate: float (optional, default 0.20)

    Returns:
        200: {data: {success, net_income, closing_entries_count, ...}}
        409: Period already closed
        422: Invalid input
    """
    role = getattr(current_user, "role", "")
    if role not in ("ACCOUNTANT", "ADMIN", "CHIEF_ACCOUNTANT"):
        abort(403)

    body = request.get_json(silent=True) or {}
    try:
        company_id = UUID(body["company_id"])
        fiscal_year = int(body["fiscal_year"])
        period = int(body["period"])
    except (KeyError, TypeError, ValueError) as exc:
        abort(422, description=f"Missing or invalid: {exc}")

    if not 1 <= period <= 12:
        abort(422, description="period must be 1-12")
    if fiscal_year < 1:
        abort(422, description="fiscal_year must be positive")

    trial_balance = body.get("trial_balance", [])
    if not isinstance(trial_balance, list):
        abort(422, description="trial_balance must be a list")

    cit_rate = body.get("cit_rate", 0.20)
    try:
        cit_rate_dec = __import__("decimal").Decimal(str(cit_rate))
    except (TypeError, ValueError):
        abort(422, description="cit_rate must be a number")

    try:
        result = _close_svc().close_period(
            company_id=company_id,
            fiscal_year=fiscal_year,
            period=period,
            trial_balance=trial_balance,
            actor=UUID(str(current_user.id)),
            cit_rate=cit_rate_dec,
        )
    except PeriodAlreadyClosedError as exc:
        return jsonify({"error": str(exc), "code": "PERIOD_ALREADY_CLOSED"}), 409

    return (
        jsonify(
            {
                "data": {
                    "success": result.success,
                    "company_id": str(result.company_id),
                    "fiscal_year": result.fiscal_year,
                    "period": result.period,
                    "net_income": float(result.net_income),
                    "closing_entries_count": len(result.closing_entries),
                    "closing_entries": [
                        {
                            "entry_type": e.entry_type.value,
                            "description": e.description,
                            "amount": float(e.amount),
                            "lines_count": len(e.lines),
                        }
                        for e in result.closing_entries
                    ],
                }
            }
        ),
        200,
    )
