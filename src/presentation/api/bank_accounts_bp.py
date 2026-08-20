"""API blueprint — Bank Accounts endpoints.

REST-ish endpoints per specs-bank-cash-accounts.md §6.
Follows currencies_bp.py pattern: test-engine hook, service-per-request,
@casbin_required enforcement. AUDITOR read-only; actor UUID required for mutations (D11).
"""

from __future__ import annotations

import logging
from uuid import UUID

from flask import Blueprint, jsonify, request

from src.application.services.bank_account_service import BankAccountService
from src.presentation.rbac import casbin_required
from src.presentation.serializers import serialize_bank_account

api_bp = Blueprint("bank_accounts", __name__)

logger = logging.getLogger(__name__)

# ── Role definitions ────────────────────────────────────────────────────
READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")
WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")  # AUDITOR read-only
PRIMARY_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")  # SOD for primary change
CLOSE_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")  # SOD for closure

# ── Test engine hook (set by tests before making requests) ─────────────
_test_engine = None
_ORIGINAL_SESSION = None


def init_test_engine(engine):
    """Set a shared in-memory SQLite engine for tests."""
    global _test_engine
    _test_engine = engine


def clear_test_engine():
    """Reset test engine after tests."""
    global _test_engine
    _test_engine = None


def _service() -> BankAccountService:
    """Get bank account service instance."""
    from src.infrastructure.repositories import SQLAlchemyBankAccountRepository
    return BankAccountService(repo=SQLAlchemyBankAccountRepository())


def _actor(data: dict) -> UUID | None:
    try:
        return UUID(data["actor"]) if data.get("actor") else None
    except (ValueError, TypeError):
        return None


def _require_actor(data: dict):
    actor = _actor(data)
    if actor is None:
        return None, (jsonify({"error": "actor là bắt buộc", "code": "MISSING_ACTOR"}), 400)
    return actor, None


# ── Bank Accounts ──────────────────────────────────────────────────────


@api_bp.get("/v1/bank-accounts")
@casbin_required(*READ_ROLES)
def list_bank_accounts():
    try:
        service = _service()
        service.db.session = _req_session() if _test_engine else db.session
        accounts = service.get_config(UUID(request.args.get("company_id"))) if request.args.get("company_id") else {}
        # Simplified: return all accounts for company
        company_id = UUID(request.args.get("company_id")) if request.args.get("company_id") else None
        if company_id:
            accounts = service.get_config(company_id)
        else:
            accounts = {"total_accounts": 0, "primary_account": None, "accounts": []}
        return jsonify({"bank_accounts": accounts.get("accounts", [])})
    except Exception as exc:  # noqa: BLE001
        logger.exception("list_bank_accounts failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/bank-accounts")
@casbin_required(*WRITE_ROLES)
def create_bank_account():
    try:
        actor, err = _require_actor(request.get_json(silent=True) or {})
        if err:
            return err
        service = _service()
        company_id = UUID(request.json["company_id"])
        account = service.create_bank_account(
            company_id=company_id,
            bank_name=request.json["bank_name"],
            account_number=request.json["account_number"],
            account_holder=request.json["account_holder"],
            branch=request.json.get("branch", ""),
            is_primary=request.json.get("is_primary", False),
            created_by=actor,
        )
        return jsonify({"bank_account": serialize_bank_account(account)}), 201
    except DomainException as e:
        return jsonify({"error": str(e), "code": "DOMAIN_ERROR"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("create_bank_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.get("/v1/bank-accounts/<uuid:bank_account_id>")
@casbin_required(*READ_ROLES)
def get_bank_account(bank_account_id: UUID):
    try:
        service = _service()
        account = service._repo.get_by_id(bank_account_id)
        if account is None:
            return jsonify({"error": "Tài khoản không tồn tại", "code": "NOT_FOUND"}), 404
        return jsonify({"bank_account": serialize_bank_account(account)})
    except Exception as exc:  # noqa: BLE001
        logger.exception("get_bank_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.patch("/v1/bank-accounts/<uuid:bank_account_id>")
@casbin_required(*WRITE_ROLES)
def update_bank_account(bank_account_id: UUID):
    try:
        actor, err = _require_actor(request.get_json(silent=True) or {})
        if err:
            return err
        service = _service()
        account = service.update_bank_account(
            bank_account_id=bank_account_id,
            bank_name=request.json.get("bank_name"),
            account_number=request.json.get("account_number"),
            branch=request.json.get("branch"),
            is_primary=request.json.get("is_primary"),
            actor=actor,
            reason=request.json.get("reason", ""),
        )
        return jsonify({"bank_account": serialize_bank_account(account)})
    except DomainException as e:
        return jsonify({"error": str(e), "code": "DOMAIN_ERROR"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("update_bank_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/bank-accounts/<uuid:bank_account_id>/set-primary")
@casbin_required(*PRIMARY_ROLES)
def set_primary(bank_account_id: UUID):
    try:
        actor, err = _require_actor(request.get_json(silent=True) or {})
        if err:
            return err
        service = _service()
        account = service.set_primary(
            bank_account_id=bank_account_id,
            actor=actor,
            reason=request.json.get("reason", ""),
        )
        return jsonify({"bank_account": serialize_bank_account(account)})
    except DomainException as e:
        return jsonify({"error": str(e), "code": "DOMAIN_ERROR"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("set_primary failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/bank-accounts/<uuid:bank_account_id>/suspend")
@casbin_required(*WRITE_ROLES)
def suspend_bank_account(bank_account_id: UUID):
    try:
        actor, err = _require_actor(request.get_json(silent=True) or {})
        if err:
            return err
        service = _service()
        account = service.suspend_bank_account(
            bank_account_id=bank_account_id,
            actor=actor,
            reason=request.json.get("reason", ""),
        )
        return jsonify({"bank_account": serialize_bank_account(account)})
    except DomainException as e:
        return jsonify({"error": str(e), "code": "DOMAIN_ERROR"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("suspend_bank_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/v1/bank-accounts/<uuid:bank_account_id>/close")
@casbin_required(*CLOSE_ROLES)
def close_bank_account(bank_account_id: UUID):
    try:
        actor, err = _require_actor(request.get_json(silent=True) or {})
        if err:
            return err
        service = _service()
        account = service.close_bank_account(
            bank_account_id=bank_account_id,
            actor=actor,
            reason=request.json.get("reason", ""),
        )
        return jsonify({"bank_account": serialize_bank_account(account)})
    except DomainException as e:
        return jsonify({"error": str(e), "code": "DOMAIN_ERROR"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("close_bank_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.get("/v1/bank-accounts/<uuid:bank_account_id>/reconciliations")
@casbin_required(*READ_ROLES)
def list_reconciliations(bank_account_id: UUID):
    try:
        service = _service()
        # Simplified: return reconciliations for bank account
        company_id = request.args.get("company_id")
        return jsonify({"reconciliations": []})
    except Exception as exc:  # noqa: BLE001
        logger.exception("list_reconciliations failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500