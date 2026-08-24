"""Bank & Cash web adapters."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required

from src.bricks.bank_cash.services import (
    AccountClosedError,
    DuplicateBankAccountError,
    DuplicateCashCodeError,
    NegativeBalanceError,
    NotFoundError,
    SystemAccountProtectedError,
)

bank_cash_bp = Blueprint("bank_cash", __name__)

_bank_service: Any = None
_cash_service: Any = None


def init_bank_cash_services(bank_svc: Any, cash_svc: Any) -> None:
    global _bank_service, _cash_service
    _bank_service = bank_svc
    _cash_service = cash_svc


def _banks() -> Any:
    s = _bank_service
    if s is None:
        abort(500, description="BankAccountService not initialized")
    return s


def _cash() -> Any:
    s = _cash_service
    if s is None:
        abort(500, description="CashAccountService not initialized")
    return s


def _company_id() -> UUID:
    try:
        return UUID(request.args.get("company_id", ""))
    except ValueError:
        abort(422, description="company_id required")


WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")
PRIMARY_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")


def _require_write() -> None:
    role = getattr(current_user, "role", "")
    if role == "AUDITOR":
        abort(403, description="AUDITOR chỉ đọc")
    if role not in WRITE_ROLES:
        abort(403)


def ser_bank(a: Any) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "bank_name": a.bank_name,
        "account_number": a.account_number,
        "account_holder": a.account_holder,
        "branch": a.branch,
        "is_primary": a.is_primary,
        "status": a.status.value,
        "checksum": a.checksum,
    }


def ser_cash(c: Any) -> dict[str, Any]:
    return {
        "id": str(c.id),
        "code": c.code,
        "name": c.name,
        "opening_balance": float(c.opening_balance),
        "current_balance": float(c.current_balance),
        "is_system": c.is_system,
        "status": c.status.value,
        "checksum": c.checksum,
    }


@bank_cash_bp.get("/api/v1/bank-accounts")
@login_required  # type: ignore[untyped-decorator]
def list_bank_accounts() -> tuple[Any, int]:
    rows = _banks().list_by_company(_company_id())
    return jsonify({"data": [ser_bank(a) for a in rows]}), 200


@bank_cash_bp.post("/api/v1/bank-accounts")
@login_required  # type: ignore[untyped-decorator]
def create_bank_account() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        acc = _banks().create_bank_account(
            company_id=UUID(body["company_id"]),
            bank_name=body.get("bank_name", ""),
            account_number=body.get("account_number", ""),
            account_holder=body.get("account_holder", ""),
            branch=body.get("branch", ""),
            is_primary=bool(body.get("is_primary", False)),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create bank account",
        )
    except DuplicateBankAccountError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_BANK_ACCOUNT"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_BANK_ACCOUNT"}), 422
    return jsonify({"data": ser_bank(acc)}), 201


@bank_cash_bp.post("/api/v1/bank-accounts/<aid>/set-primary")
@login_required  # type: ignore[untyped-decorator]
def set_primary(aid: str) -> tuple[Any, int]:
    role = getattr(current_user, "role", "")
    if role not in PRIMARY_ROLES:
        abort(403)
    body = request.get_json(silent=True) or {}
    try:
        acc = _banks().set_primary(
            UUID(aid),
            UUID(str(current_user.id)),
            body.get("reason") or "set primary",
        )
    except NotFoundError:
        abort(404)
    return jsonify({"data": ser_bank(acc)}), 200


@bank_cash_bp.get("/api/v1/cash-accounts")
@login_required  # type: ignore[untyped-decorator]
def list_cash_accounts() -> tuple[Any, int]:
    rows = _cash().list_by_company(_company_id())
    return jsonify({"data": [ser_cash(c) for c in rows]}), 200


@bank_cash_bp.post("/api/v1/cash-accounts")
@login_required  # type: ignore[untyped-decorator]
def create_cash_account() -> tuple[Any, int]:
    _require_write()
    body = request.get_json(silent=True) or {}
    try:
        acc = _cash().create_cash_account(
            company_id=UUID(body["company_id"]),
            code=body["code"],
            name=body.get("name", ""),
            opening_balance=Decimal(str(body.get("opening_balance", "0"))),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "create cash",
        )
    except DuplicateCashCodeError as exc:
        return jsonify({"error": str(exc), "code": "DUPLICATE_CASH_CODE"}), 409
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "code": "INVALID_CASH_ACCOUNT"}), 422
    return jsonify({"data": ser_cash(acc)}), 201


@bank_cash_bp.post("/api/v1/cash-accounts/<aid>/adjust")
@login_required  # type: ignore[untyped-decorator]
def adjust_cash(aid: str) -> tuple[Any, int]:
    """Delta adjust; negative result needs CHIEF_ACCOUNTANT session."""
    role = getattr(current_user, "role", "")
    chief_ok = role == "CHIEF_ACCOUNTANT"
    if role not in WRITE_ROLES:
        abort(403)
    body = request.get_json(silent=True) or {}
    try:
        acc = _cash().update_balance(
            UUID(aid),
            Decimal(str(body.get("amount", "0"))),
            actor=UUID(str(current_user.id)),
            reason=body.get("reason") or "adjust",
            chief_approved=chief_ok,
        )
    except NegativeBalanceError as exc:
        return jsonify({"error": str(exc), "code": "NEGATIVE_BALANCE"}), 409
    except NotFoundError:
        abort(404)
    return jsonify({"data": ser_cash(acc)}), 200


@bank_cash_bp.errorhandler(AccountClosedError)
def _closed(e: AccountClosedError) -> tuple[Any, int]:
    return jsonify({"error": str(e), "code": "ACCOUNT_CLOSED"}), 409


@bank_cash_bp.errorhandler(SystemAccountProtectedError)
def _protected(e: SystemAccountProtectedError) -> tuple[Any, int]:
    return jsonify({"error": str(e), "code": "SYSTEM_ACCOUNT_PROTECTED"}), 403
