"""Purchases web adapter — REST per docs/purchases/specs §6."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.purchases.services import (
    AlreadyPostedError,
    DuplicateInvoiceError,
    InvalidAccountError,
    NotFoundError,
    NotPostedError,
    PeriodClosedError,
    TotalMismatchError,
)

purchases_bp = Blueprint("purchases", __name__)

_purchase_service: Any = None


def init_purchases_service(svc: Any) -> None:
    global _purchase_service
    _purchase_service = svc


def _svc() -> Any:
    s = _purchase_service
    if s is None:
        abort(500, description="PurchaseService not initialized")
    return s


WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")
CANCEL_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN")


def _roles(allowed: tuple[str, ...]) -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    if role not in allowed:
        abort(403)


def ser_inv(inv: Any) -> dict[str, Any]:
    return {
        "id": str(inv.id),
        "supplier_name": inv.supplier_name,
        "supplier_mst": inv.supplier_mst,
        "invoice_number": inv.invoice_number,
        "invoice_symbol": inv.invoice_symbol,
        "invoice_date": inv.invoice_date.isoformat(),
        "entry_date": inv.entry_date.isoformat(),
        "subtotal": float(inv.subtotal),
        "vat_deductible": float(inv.vat_deductible),
        "vat_non_deductible": float(inv.vat_non_deductible),
        "total_payment": float(inv.total_payment),
        "deductibility": inv.deductibility.value,
        "status": inv.status.value,
        "checksum": inv.checksum,
    }


@purchases_bp.errorhandler(PeriodClosedError)
def _period(e: PeriodClosedError) -> tuple[Any, int]:
    return jsonify({"error": str(e), "code": "PERIOD_CLOSED"}), 409


@purchases_bp.get("/api/v1/purchase-invoices")
@login_required  # type: ignore[untyped-decorator]
def list_purchase_invoices() -> tuple[Any, int]:
    try:
        cid = UUID(request.args.get("company_id", ""))
    except ValueError:
        abort(422, description="company_id required")
    status = request.args.get("status")
    ded = request.args.get("deductibility")
    rows = _svc().list_by_company(cid, status=status, deductibility=ded)
    return jsonify({"data": [ser_inv(x) for x in rows]}), 200


@purchases_bp.post("/api/v1/purchase-invoices")
@login_required  # type: ignore[untyped-decorator]
def create_purchase_invoice() -> tuple[Any, int]:
    _roles(WRITE_ROLES)
    body = request.get_json(silent=True) or {}
    kwargs: dict[str, Any] = {}
    if body.get("expected_total_payment") is not None:
        kwargs["expected_total_payment"] = str(body["expected_total_payment"])
    try:
        inv = _svc().create_invoice(
            company_id=UUID(body["company_id"]),
            supplier_name=body.get("supplier_name", ""),
            supplier_mst=body.get("supplier_mst", ""),
            invoice_number=body.get("invoice_number", ""),
            invoice_symbol=body.get("invoice_symbol", ""),
            invoice_date=date.fromisoformat(body["invoice_date"]),
            entry_date=date.fromisoformat(body["entry_date"]),
            payment_method=body.get("payment_method", "none"),
            payment_proof=bool(body.get("payment_proof", False)),
            lines=body.get("lines", []),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create purchase invoice",
            **kwargs,
        )
    except DuplicateInvoiceError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_INVOICE"}), 409
    except InvalidAccountError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_ACCOUNT"}), 422
    except PeriodClosedError:
        raise  # handled by blueprint errorhandler → 409
    except TotalMismatchError as exc:
        return jsonify({"error": str(exc), "code": "TOTAL_MISMATCH"}), 422
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_INVOICE"}), 422
    return jsonify({"data": ser_inv(inv)}), 201


@purchases_bp.post("/api/v1/purchase-invoices/<iid>/post")
@login_required  # type: ignore[untyped-decorator]
def post_purchase_invoice(iid: str) -> tuple[Any, int]:
    _roles(WRITE_ROLES)
    body = request.get_json(silent=True) or {}
    try:
        out = _svc().post(
            UUID(iid),
            UUID(str(current_user.id)),
            body.get("reason") or "post",
        )
    except AlreadyPostedError as exc:
        return jsonify({"error": str(exc), "code": "ALREADY_POSTED"}), 409
    except NotFoundError:
        abort(404)
    return jsonify({"data": ser_inv(out)}), 200


@purchases_bp.post("/api/v1/purchase-invoices/<iid>/cancel")
@login_required  # type: ignore[untyped-decorator]
def cancel_purchase_invoice(iid: str) -> tuple[Any, int]:
    _roles(CANCEL_ROLES)
    body = request.get_json(silent=True) or {}
    try:
        out = _svc().cancel(
            UUID(iid),
            UUID(str(current_user.id)),
            body.get("reason") or "cancel",
        )
    except NotPostedError as exc:
        return jsonify({"error": str(exc), "code": "NOT_POSTED_ON_CANCEL"}), 422
    except NotFoundError:
        abort(404)
    return jsonify({"data": ser_inv(out)}), 200


@purchases_bp.get("/api/v1/purchase-invoices/<iid>")
@login_required  # type: ignore[untyped-decorator]
def get_purchase_invoice(iid: str) -> tuple[Any, int]:
    try:
        iid_u = UUID(iid)
    except ValueError:
        abort(422, description="Invalid UUID")
    inv = _svc().get(iid_u)
    if inv is None:
        abort(404)
    return jsonify({"data": ser_inv(inv)}), 200
