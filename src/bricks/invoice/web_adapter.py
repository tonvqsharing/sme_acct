"""Invoice web adapter."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.invoice.services import (
    AlreadyIssuedError,
    AlreadyPostedError,
    EInvoiceDisabledError,
    InvoiceNotFoundError,
    NoOpenPeriodError,
    NotPostedError,
)

invoice_bp = Blueprint("invoice", __name__)

_invoice_service: Any = None
_on_posted: Any = None  # optional callback(invoice)->dict, wired by app factory
_voucher_service: Any = None


def init_invoice_service(
    svc: Any, on_posted: Any | None = None, voucher_service: Any | None = None
) -> None:
    global _invoice_service, _on_posted, _voucher_service
    _invoice_service = svc
    _on_posted = on_posted
    _voucher_service = voucher_service


def _svc() -> Any:
    s = _invoice_service
    if s is None:
        abort(500, description="InvoiceService not initialized")
    return s


def serialize(inv: Any) -> dict[str, Any]:
    breakdown: dict[str, float] = {}
    try:
        bd = inv.vat_breakdown
        breakdown = {k: float(v) for k, v in bd.items()}
    except Exception:  # noqa: BLE001
        breakdown = {}
    einv = getattr(inv, "einvoice_status", None)
    einv_val = einv.value if einv is not None and hasattr(einv, "value") else "NOT_ISSUED"
    return {
        "id": str(inv.id),
        "company_id": str(inv.company_id),
        "number": inv.number,
        "issue_date": inv.issue_date.isoformat(),
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "customer_name": inv.customer_name,
        "customer_mst": getattr(inv, "customer_mst", None),
        "template_code": getattr(inv, "template_code", ""),
        "invoice_symbol": getattr(inv, "invoice_symbol", ""),
        "currency_code": getattr(inv, "currency_code", "VND"),
        "fx_rate": float(inv.fx_rate) if getattr(inv, "fx_rate", None) is not None else None,
        "einvoice_status": einv_val,
        "deferred_amount": float(getattr(inv, "deferred_amount", 0)),
        "subtotal": float(inv.subtotal),
        "vat_rate": float(inv.vat_rate),
        "vat_breakdown": breakdown,
        "vat_amount": float(inv.vat_amount),
        "grand_total": float(inv.grand_total),
        "status": inv.status.value,
        "checksum": inv.checksum,
        "items": [
            {
                "account_code": it.account_code,
                "description": it.description,
                "amount": float(it.amount),
                "vat_rate": float(it.vat_rate) if it.vat_rate is not None else None,
                "category": it.category,
            }
            for it in inv.items
        ],
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
        # AUDITOR cannot create (SOD)
        role = getattr(current_user, "role", "")
        if role == "AUDITOR":
            return jsonify({"error": "AUDITOR cannot create invoice", "code": "SOD_VIOLATION"}), 403
        inv = svc.create_invoice(
            company_id=UUID(body["company_id"]),
            customer_name=body.get("customer_name", ""),
            customer_mst=body.get("customer_mst"),
            template_code=body.get("template_code"),
            invoice_symbol=body.get("invoice_symbol"),
            issue_date=date.fromisoformat(body["issue_date"]),
            vat_rate=(
                Decimal(str(body.get("vat_rate", "0.1")))
                if body.get("vat_rate") is not None
                else Decimal("0.1")
            ),
            items=body.get("items", []),
            product_category=body.get("product_category"),
            currency_code=body.get("currency_code"),
            fx_rate=body.get("fx_rate"),
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
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        return jsonify({"error": "AUDITOR cannot post", "code": "SOD_VIOLATION"}), 403
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


@invoice_bp.post("/api/v1/invoices/<invoice_id>/deduction")
@login_required  # type: ignore[untyped-decorator]
def create_deduction(invoice_id: str) -> tuple[Any, int]:
    body = request.get_json(silent=True) or {}
    try:
        iid = UUID(invoice_id)
    except ValueError:
        abort(422, description="Invalid UUID")
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        return jsonify({"error": "AUDITOR cannot deduct", "code": "SOD_VIOLATION"}), 403
    try:
        svc = _svc()
        voucher = svc.create_deduction(
            iid,
            deduction_type=body.get("deduction_type", "RETURN"),
            amount=body.get("amount", "0"),
            vat_rate=body.get("vat_rate"),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "deduction",
            voucher_service=_voucher_service,
        )
    except InvoiceNotFoundError:
        abort(404, description="Invoice not found")
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "INVALID_DEDUCTION"}), 422
    except RuntimeError as exc:
        return jsonify({"error": str(exc), "code": "NOT_WIRED"}), 500
    from src.bricks.voucher.web_adapter import serialize as v_serialize

    return jsonify({"data": v_serialize(voucher)}), 201


@invoice_bp.post("/api/v1/invoices/<invoice_id>/einvoice/issue")
@login_required  # type: ignore[untyped-decorator]
def issue_einvoice(invoice_id: str) -> tuple[Any, int]:
    body = request.get_json(silent=True) or {}
    try:
        iid = UUID(invoice_id)
    except ValueError:
        abort(422, description="Invalid UUID")
    role = getattr(current_user, "role", "")
    if role not in ("CHIEF_ACCOUNTANT", "ADMIN"):
        return (
            jsonify(
                {
                    "error": "Only CHIEF_ACCOUNTANT/ADMIN can issue e-invoice",
                    "code": "SOD_VIOLATION",
                }
            ),
            403,
        )
    try:
        inv = _svc().issue_einvoice(
            iid,
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "issue einvoice",
            seller=body.get("seller"),
        )
        return jsonify({"data": serialize(inv)}), 200
    except InvoiceNotFoundError:
        abort(404, description="Invoice not found")
    except EInvoiceDisabledError as exc:
        return jsonify({"error": str(exc), "code": "E_INVOICE_DISABLED"}), 403
    except NotPostedError as exc:
        return jsonify({"error": str(exc), "code": "NOT_POSTED"}), 422
    except AlreadyIssuedError as exc:
        return jsonify({"error": str(exc), "code": "ALREADY_ISSUED"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_EINVOICE"}), 422
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc), "code": "EINVOICE_ERROR"}), 422
