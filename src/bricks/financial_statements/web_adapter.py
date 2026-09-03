"""Financial Statements web adapter — report endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.financial_statements.services import (
    PeriodAlreadyClosedError,
    ReportEngine,
)
from src.bricks.financial_statements.templates import (
    b01_dn_template,
    b02_dn_template,
    b03_dn_template,
)

reports_bp = Blueprint("reports", __name__)

_period_close_service: Any = None
_ledger_source: Any = None


def init_period_close_service(svc: Any) -> None:
    global _period_close_service
    _period_close_service = svc


def init_reports_ledger(source: Any) -> None:
    global _ledger_source
    _ledger_source = source


def _close_svc() -> Any:
    s = _period_close_service
    if s is None:
        abort(500, description="PeriodCloseService not initialized")
    return s


def _ledger() -> Any:
    if _ledger_source is None:
        abort(500, description="Ledger source not initialized")
    return _ledger_source


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


def _compute_report(code: str) -> list[dict[str, Any]]:
    import calendar
    from datetime import date
    from decimal import Decimal

    from flask import request as _req

    args = _req.args
    try:
        company_id = UUID(args.get("company_id", ""))
    except ValueError:
        abort(422, description="company_id required")
    try:
        y = int(args.get("year", "2026"))
        m = int(args.get("month", "12"))
    except ValueError:
        abort(422, description="invalid year/month")
    start = date(y, 1, 1)
    end = date(y, m, calendar.monthrange(y, m)[1])
    # Use ledger source to build account_balances
    ledger = _ledger()
    try:
        account_balances: dict[str, Any] = {}
        for r in (
            ledger.get_posted_lines(company_id, start, end)
            if hasattr(ledger, "get_posted_lines")
            else []
        ):
            acct = r["account_code"]
            slot = account_balances.setdefault(
                acct,
                {
                    "debit": Decimal(0),
                    "credit": Decimal(0),
                },
            )
            slot["debit"] += Decimal(str(r["debit"]))
            slot["credit"] += Decimal(str(r["credit"]))
    except Exception:  # noqa: BLE001 — ledger empty is non-fatal
        account_balances = {}
    template = {"B01-DN": b01_dn_template, "B02-DN": b02_dn_template, "B03-DN": b03_dn_template}[
        code
    ]()
    engine = ReportEngine()
    lines = engine.compute(template, account_balances)
    return [
        {"line_code": l.line_code, "line_name": l.line_name, "value": float(l.value_current)}
        for l in lines
    ]


@reports_bp.get("/api/v1/reports/b01")
@login_required  # type: ignore[untyped-decorator]
def report_b01() -> tuple[Any, int]:
    return jsonify({"data": _compute_report("B01-DN")}), 200


@reports_bp.get("/api/v1/reports/b02")
@login_required  # type: ignore[untyped-decorator]
def report_b02() -> tuple[Any, int]:
    return jsonify({"data": _compute_report("B02-DN")}), 200


@reports_bp.get("/api/v1/reports/b03")
@login_required  # type: ignore[untyped-decorator]
def report_b03() -> tuple[Any, int]:
    return jsonify({"data": _compute_report("B03-DN")}), 200
