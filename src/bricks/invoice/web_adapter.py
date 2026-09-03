"""Invoice web adapter."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.invoice.services import (
    AlreadyPostedError,
    InvoiceNotFoundError,
    NoOpenPeriodError,
)

invoice_bp = Blueprint("invoice", __name__)

_invoice_service: Any = None
_on_posted: Any = None  # optional callback(invoice)->dict, wired by app factory


def init_invoice_service(svc: Any, on_posted: Any | None = None) -> None:
    global _invoice_service, _on_posted
    _invoice_service = svc
    _on_posted = on_posted


def _svc() -> Any:
    s = _invoice_service
    if s is None:
        abort(500, description="InvoiceService not initialized")
    return s


def serialize(inv: Any) -> dict[str, Any]:
    return {
        "id": str(inv.id),
        "company_id": str(inv.company_id),
        "number": inv.number,
        "issue_date": inv.issue_date.isoformat(),
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "customer_name": inv.customer_name,
        "subtotal": float(inv.subtotal),
        "vat_rate": float(inv.vat_rate),
        "vat_amount": float(inv.vat_amount),
        "grand_total": float(inv.grand_total),
        "status": inv.status.value,
        "checksum": inv.checksum,
    }


@invoice_bp.get("/api/v1/invoices")
@login_required  # type: ignore[untyped-decorator]
def list_invoices() -> tuple[Any, int]:
    cid = request.args.get("company_id", "")
    try:
        company_id = UUID(cid)
    except ValueError:
        abort(422, description="company_id required")
    return jsonify({"data": [serialize(i) for i in _svc().list_invoices(company_id)]}), 200


@invoice_bp.post("/api/v1/invoices")
@login_required  # type: ignore[untyped-decorator]
def create_invoice() -> tuple[Any, int]:
    body = request.get_json(silent=True) or {}
    svc = _svc()
    from src.bricks.coa.services import (
        AccountNotFoundError,
        AggregateAccountError,
        InactiveAccountError,
    )

    try:
        inv = svc.create_invoice(
            company_id=UUID(body["company_id"]),
            customer_name=body.get("customer_name", ""),
            issue_date=date.fromisoformat(body["issue_date"]),
            vat_rate=Decimal(str(body.get("vat_rate", "0.1"))),
            items=body.get("items", []),
            product_category=body.get("product_category"),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create invoice",
        )
        import logging

        logging.getLogger(__name__).info("Invoice created", extra={"number": inv.number})
        return jsonify({"data": serialize(inv)}), 201
    except NoOpenPeriodError:
        return jsonify({"error": "Kỳ sổ chưa mở", "code": "NO_OPEN_PERIOD"}), 409
    except KeyError as exc:
        abort(422, description=f"missing {exc}")
    except (
        AccountNotFoundError,
        AggregateAccountError,
        InactiveAccountError,
        AlreadyPostedError,
        ValueError,
    ) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_ACCOUNT"}), 422


@invoice_bp.get("/api/v1/invoices/<invoice_id>")
@login_required  # type: ignore[untyped-decorator]
def get_invoice(invoice_id: str) -> tuple[Any, int]:
    try:
        iid = UUID(invoice_id)
    except ValueError:
        abort(422, description="Invalid UUID")
    inv = _svc().get_invoice(iid)
    if inv is None:
        abort(404, description="Invoice not found")
    return jsonify({"data": serialize(inv)}), 200


@invoice_bp.post("/api/v1/invoices/<invoice_id>/post")
@login_required  # type: ignore[untyped-decorator]
def post_invoice(invoice_id: str) -> tuple[Any, int]:
    body = request.get_json(silent=True) or {}
    try:
        iid = UUID(invoice_id)
    except ValueError:
        abort(422, description="Invalid UUID")
    try:
        posted = _svc().post_invoice(
            iid,
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "post invoice",
        )
    except AlreadyPostedError as exc:
        return jsonify({"error": str(exc), "code": "ALREADY_POSTED"}), 409
    except InvoiceNotFoundError:
        abort(404, description="Invoice not found")

    payload = serialize(posted)
    if _on_posted is not None:
        journal = _on_posted(posted)
        payload["voucher_id"] = journal["id"]
        payload["voucher_number"] = journal["number"]
    return jsonify({"data": payload}), 200
