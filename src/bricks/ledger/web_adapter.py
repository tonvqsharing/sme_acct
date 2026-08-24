"""Ledger report endpoints — read-only, any authenticated role."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import login_required

ledger_bp = Blueprint("ledger", __name__)

_ledger_service: Any = None


def init_ledger_service(svc: Any) -> None:
    global _ledger_service
    _ledger_service = svc


def _svc() -> Any:
    s = _ledger_service
    if s is None:
        abort(500, description="LedgerService not initialized")
    return s


def _params() -> tuple[UUID, date, date]:
    args = request.args
    try:
        cid = UUID(args.get("company_id", ""))
        start = date.fromisoformat(args.get("from", ""))
        end = date.fromisoformat(args.get("to", ""))
    except ValueError as exc:
        abort(422, description=f"invalid param: {exc}")
    return cid, start, end


def _dec(v: Any) -> float:
    return float(v)


@ledger_bp.get("/api/v1/reports/general-journal")
@login_required  # type: ignore[untyped-decorator]
def general_journal() -> tuple[Any, int]:
    cid, start, end = _params()
    entries = _svc().general_journal(cid, start, end)
    for e in entries:
        e["total_debit"] = _dec(e["total_debit"])
        for line in e["lines"]:
            line["debit"] = _dec(line["debit"])
            line["credit"] = _dec(line["credit"])
    return jsonify({"data": entries}), 200


@ledger_bp.get("/api/v1/reports/trial-balance")
@login_required  # type: ignore[untyped-decorator]
def trial_balance() -> tuple[Any, int]:
    cid, start, end = _params()
    rows = _svc().trial_balance(cid, start, end)
    for r in rows:
        r["debit"] = _dec(r["debit"])
        r["credit"] = _dec(r["credit"])
        r["net_debit"] = _dec(r["net_debit"])
    total_dr = sum(r["debit"] for r in rows)
    total_cr = sum(r["credit"] for r in rows)
    return (
        jsonify(
            {
                "data": rows,
                "totals": {"debit": total_dr, "credit": total_cr},
            }
        ),
        200,
    )
