"""Voucher web adapter."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.bank_cash.services import (
    NegativeBalanceError as CashNegativeBalanceError,
)
from src.bricks.coa.services import (
    AccountNotFoundError,
    AggregateAccountError,
    InactiveAccountError,
)
from src.bricks.voucher.services import (
    AlreadyPostedError,
    NoOpeningLockError,
    NoOpenPeriodError,
    UnbalancedVoucherError,
    VoucherNotFoundError,
)

voucher_bp = Blueprint("voucher", __name__)

_voucher_service: Any = None


def init_voucher_service(svc: Any) -> None:
    global _voucher_service
    _voucher_service = svc


def _svc() -> Any:
    s = _voucher_service
    if s is None:
        abort(500, description="VoucherService not initialized")
    return s


def serialize(v: Any) -> dict[str, Any]:
    return {
        "id": str(v.id),
        "company_id": str(v.company_id),
        "number": v.number,
        "entry_date": v.entry_date.isoformat(),
        "description": v.description,
        "total_debit": float(v.total_debit),
        "total_credit": float(v.total_credit),
        "status": v.status.value,
        "checksum": v.checksum,
    }


@voucher_bp.post("/api/v1/vouchers")
@login_required  # type: ignore[untyped-decorator]
def create_voucher() -> tuple[Any, int]:
    body = request.get_json(silent=True) or {}
    try:
        company_id = UUID(body["company_id"])
        entry_date = date.fromisoformat(body["entry_date"])
    except (KeyError, ValueError) as exc:
        abort(422, description=f"invalid field: {exc}")
    try:
        v = _svc().create_voucher(
            company_id=company_id,
            entry_date=entry_date,
            description=body.get("description", ""),
            lines=body.get("lines", []),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create voucher",
        )
    except NoOpenPeriodError:
        return jsonify({"error": "Kỳ sổ chưa mở", "code": "NO_OPEN_PERIOD"}), 409
    except NoOpeningLockError as exc:
        return jsonify({"error": str(exc), "code": "NO_OPENING_LOCK"}), 409
    except UnbalancedVoucherError as exc:
        return jsonify({"error": str(exc), "code": "UNBALANCED_VOUCHER"}), 422
    except (
        AccountNotFoundError,
        AggregateAccountError,
        InactiveAccountError,
        ValueError,
    ) as exc:
        code = (
            "INVALID_ACCOUNT"
            if isinstance(exc, (AccountNotFoundError, AggregateAccountError, InactiveAccountError))
            else "INVALID_VOUCHER"
        )
        return jsonify({"error": str(exc), "code": code}), 422
    return jsonify({"data": serialize(v)}), 201


@voucher_bp.get("/api/v1/vouchers/<vid>")
@login_required  # type: ignore[untyped-decorator]
def get_voucher(vid: str) -> tuple[Any, int]:
    try:
        v = _svc().get_voucher(UUID(vid))
    except ValueError:
        abort(422, description="Invalid UUID")
    if v is None:
        abort(404, description="Voucher not found")
    return jsonify({"data": serialize(v)}), 200


@voucher_bp.post("/api/v1/vouchers/<vid>/post")
@login_required  # type: ignore[untyped-decorator]
def post_voucher(vid: str) -> tuple[Any, int]:
    body = request.get_json(silent=True) or {}
    try:
        uuid_vid = UUID(vid)
    except ValueError:
        abort(422, description="Invalid UUID")
    role = getattr(current_user, "role", "")
    try:
        posted = _svc().post_voucher(
            uuid_vid,
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "post voucher",
            chief_approved=(role == "CHIEF_ACCOUNTANT"),
        )
    except CashNegativeBalanceError as exc:
        return jsonify({"error": str(exc), "code": "NEGATIVE_BALANCE"}), 409
    except AlreadyPostedError as exc:
        return jsonify({"error": str(exc), "code": "ALREADY_POSTED"}), 409
    except VoucherNotFoundError:
        abort(404, description="Voucher not found")
    return jsonify({"data": serialize(posted)}), 200


@voucher_bp.get("/api/v1/vouchers")
@login_required  # type: ignore[untyped-decorator]
def list_vouchers() -> tuple[Any, int]:
    raw = request.args.get("company_id", "")
    try:
        cid = UUID(raw)
    except ValueError:
        abort(422, description="company_id required")
    return jsonify({"data": [serialize(x) for x in _svc().list_vouchers(cid)]}), 200
