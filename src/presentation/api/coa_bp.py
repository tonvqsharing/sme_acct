"""COA API blueprint — Chart of Accounts endpoints.

REST-ish per docs/fiscal-year-period specs §5. Follows currencies_bp
pattern: test-engine hook, service-per-request, @casbin_required, actor
UUID required on mutations (D11). AUDITOR read-only.

Routes:
- GET   /api/v1/coa/accounts          list accounts
- POST  /api/v1/coa/accounts          create account (CHIEF_ACCOUNTANT)
- GET   /api/v1/coa/accounts/{id}     account detail
- PATCH /api/v1/coa/accounts/{id}     update account (CHIEF_ACCOUNTANT)
- DELETE/POST close → soft-delete (CHIEF_ACCOUNTANT)
- GET   /api/v1/coa/categories        list 9 system categories
- GET   /api/v1/coa/tags/mandatory    list 7 mandatory tags
- POST  /api/v1/coa/import             import COA from template (CHIEF_ACCOUNTANT)
- GET   /api/v1/coa/export              export COA snapshot (READ_ROLES)
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify, request
from src.application.services.coa_service import CoaService
from src.application.ports import (
    AccountRepositoryPort,
    AccountCategoryRepositoryPort,
    AccountTagRepositoryPort,
)
from src.infrastructure.database import db
from src.infrastructure.repositories.coa_repo import (
    SQLAlchemyAccountRepository,
    SQLAlchemyAccountCategoryRepository,
    SQLAlchemyAccountTagRepository,
)
from src.presentation.rbac import casbin_required
from src.presentation.serializers import (
    serialize_account,
    serialize_account_category,
    serialize_account_tag,
)
from src.presentation.rbac import READ_ROLES, LOCK_WRITE_ROLES, FY_ADMIN_ROLES, AUTO_SEED_ROLES

coa_bp = Blueprint("coa", __name__)
logger = logging.getLogger(__name__)

READ_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR")
LOCK_WRITE_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT")
FY_ADMIN_ROLES = ("CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")
AUTO_SEED_ROLES = ("ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "DIRECTOR")

# Service per-request factory (currencies pattern)
_service = None


def _service() -> CoaService:
    global _service
    if _service is None:
        acc_repo = SQLAlchemyAccountRepository()
        cat_repo = SQLAlchemyAccountCategoryRepository()
        tag_repo = SQLAlchemyAccountTagRepository()
        _service = CoaService(acc_repo, cat_repo, tag_repo)
    return _service


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


# ── Accounts ──────────────────────────────────────────────────────────

@coa_bp.get("/v1/coa/accounts")
@casbin_required(*READ_ROLES)
def list_accounts():
    company_id = request.args.get("company_id")
    if not company_id:
        return jsonify({"error": "company_id là bắt buộc", "code": "MISSING_COMPANY"}), 400
    try:
        accounts = _service().list_by_company(UUID(company_id))
        return jsonify({"accounts": [serialize_account(a) for a in accounts]})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("list_accounts failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.post("/v1/coa/accounts")
@casbin_required(*AUTO_SEED_ROLES)  # no AUDITOR; write operation
def create_account():
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        assert actor is not None
        account = _service().create_account(
            code=data.get("code", ""),
            name=data.get("name", ""),
            category=AccountCategory(data.get("category")),  # enum validation
            company_id=UUID(data["company_id"]),
            actor=actor,
            vat_rate=float(data.get("vat_rate", 0)),
            report_line=data.get("report_line"),
            account_tags=[AccountTag(t) for t in data.get("tags", [])],
        )
        return jsonify({"account": serialize_account(account)}), 201
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except InvalidAccountCodeError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except (AccountCodeAlreadyExistsError, SystemAccountModificationError) as e:
        return jsonify({"error": str(e), "code": "COA_ERROR"}), 409
    except Exception as exc:
        logger.exception("create_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.get("/v1/coa/accounts/<uuid:account_id>")
@casbin_required(*READ_ROLES)
def get_account(account_id: UUID):
    try:
        acct = _service().get_by_id(account_id)
        if acct is None:
            return jsonify({"error": "Account not found", "code": "NOT_FOUND"}), 404
        return jsonify({"account": serialize_account(acct)})
    except Exception as exc:
        logger.exception("get_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.patch("/v1/coa/accounts/<uuid:account_id>")
@casbin_required(*FY_ADMIN_ROLES)  # CHIEF_ACCOUNTANT/ADMIN/DIRECTOR only
def update_account(account_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        acct = _service().update_account(
            account_id=account_id,
            new_code=data.get("code"),
            new_name=data.get("name"),
            new_category=data.get("category"),
            new_vat_rate=float(data.get("vat_rate", 0)) if data.get("vat_rate") else None,
            new_report_line=data.get("report_line"),
            actor=actor,
            reason=data.get("reason", ""),  # mandatory for any COA change
        )
        return jsonify({"account": serialize_account(acct)})
    except (InvalidAccountCodeError, SystemAccountModificationError, AccountCodeAlreadyExistsError) as e:
        code = "COA_ERROR" if isinstance(e, AccountCodeAlreadyExistsError) else "VALIDATION_ERROR"
        status = 409 if isinstance(e, AccountCodeAlreadyExistsError) else 422
        return jsonify({"error": str(e), "code": code}), status
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("update_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.post("/v1/coa/accounts/<uuid:account_id>/close")
@casbin_required("CHIEF_ACCOUNTANT")
def close_account(account_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        acct = _service().close_account(account_id, actor=actor, reason=data.get("reason", ""))
        return jsonify({"account": serialize_account(acct)})
    except ValueError as e:
        return jsonify({"error": str(e), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:
        logger.exception("close_account failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── System categories & tags ────────────────────────────────────────

@coa_bp.get("/v1/coa/categories")
@casbin_required(*READ_ROLES)
def list_categories():
    cats = _service().list_system_categories()
    return jsonify({"categories": [c.value for c in cats]})


@coa_bp.get("/v1/coa/tags/mandatory")
@casbin_required(*READ_ROLES)
def list_mandatory_tags():
    tags = _service().list_mandatory_tags()
    return jsonify({"tags": [t.value for t in tags]})


# ── Import/Export ──────────────────────────────────────────────────

@coa_bp.post("/v1/coa/import")
@casbin_required(*FY_ADMIN_ROLES)
def import_coa():
    try:
        data = request.get_json(silent=True) or {}
        actor, err = _require_actor(data)
        if err:
            return err
        summary = _service().import_coa_from_template(data.get("template_rows", []), actor)
        return jsonify({"import_summary": summary})
    except Exception as exc:
        logger.exception("import_coa failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@coa_bp.get("/v1/coa/export")
@casbin_required(*READ_ROLES)
def export_coa():
    try:
        snapshot = _service().export_coa_snapshot()
        return jsonify(snapshot)
    except Exception as exc:
        logger.exception("export_coa failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500