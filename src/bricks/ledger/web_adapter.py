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
    args = request.args
    try:
        page = int(args.get("page", "1"))
        page_size = int(args.get("page_size", "50"))
    except ValueError:
        abort(422, description="invalid pagination")
    entries = _svc().general_journal(cid, start, end, page=page, page_size=page_size)
    for e in entries:
        e["total_debit"] = _dec(e["total_debit"])
        for line in e["lines"]:
            line["debit"] = _dec(line["debit"])
            line["credit"] = _dec(line["credit"])
    return jsonify({"data": entries, "page": page, "page_size": page_size}), 200


@ledger_bp.get("/api/v1/reports/ar-aging")
@login_required  # type: ignore[untyped-decorator]
def ar_aging() -> tuple[Any, int]:
    args = request.args
    try:
        cid = UUID(args.get("company_id", ""))
        as_of = date.fromisoformat(args.get("as_of", date.today().isoformat()))  # noqa: DTZ011
    except ValueError as exc:
        abort(422, description=f"invalid param: {exc}")
    buckets = _svc().ar_aging(cid, as_of)
    for b in buckets:
        b["amount"] = float(b["amount"])
    return jsonify({"data": buckets}), 200


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
