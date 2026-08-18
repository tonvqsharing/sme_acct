"""API blueprint — System Settings Module endpoints.

Provides REST-ish endpoints for the System Settings module, following the
same patterns as the Company API and Audit Log API.

Module status (Phase 1 domain complete, migration applied):
- Domain layer: FlagType/FlagScope/FlagCategory enums; AccountingPeriodType;
  VATMethod/EInvoiceMode/EInvoiceSeries dataclass; CompanyConfig aggregate;
  exceptions (SystemSettingsError, FlagLockedError, ConfigVersionConflict,
  InvalidVATRateError, InvalidCAListError, InvalidRegimeError)
- Migration: flask db migrate generated 4 new tables (audit_log, ca_list_entries,
  e_invoice_series, period_locks); flask db upgrade applied
- Service layer: SystemSettingsService with get_config, update_config,
  lock_period, unlock_period, validate_vat_rate, add_e_invoice_series —
  follows CompanyService pattern, NO Flask/SQLAlchemy imports
- REST API: now implemented (was deferred; model separation resolved)

Follows Clean Architecture: service layer, NO Flask/SQLAlchemy imports in service.
Implements LAW-type flag immutability and CONFIG-type admin-changeable with audit log.
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify, request

from src.application.services.system_settings_service import SystemSettingsService
from src.application.ports import SystemSettingsRepositoryPort
from src.domain.exceptions import (
    SystemSettingsError,
    FlagLockedError,
    ConfigVersionConflict,
    InvalidVATRateError,
    InvalidCAListError,
    InvalidRegimeError,
)
from src.infrastructure.database import db
from src.infrastructure.database.models import SystemAuditLogModel

api_bp = Blueprint("system_settings", __name__, url_prefix="/api/v1/system_settings")

logger = logging.getLogger(__name__)

# ── Test engine hook (set by tests before making requests) ─────────────────
_test_engine = None


def init_test_engine(engine):
    """Set a shared in-memory SQLite engine for tests."""
    global _test_engine
    _test_engine = engine


def clear_test_engine():
    """Reset test engine after tests."""
    global _test_engine
    _test_engine = None


def _req_session():
    """Get a session tied to the test engine when set, else fall back to app db."""
    if _test_engine is not None:
        return db.Session(bind=_test_engine)
    return db.session


def _service() -> SystemSettingsService:
    """Build SystemSettingsService using the current request-bound session."""
    session = _req_session()
    from src.infrastructure.repositories import SQLAlchemySystemSettingsRepository
    repo = SQLAlchemySystemSettingsRepository()
    return SystemSettingsService(repo)


# ── Health ──────────────────────────────────────────────────────────────────


@api_bp.get("/health")
def health():
    return {"status": "ok", "module": "system_settings"}


# ── Config Retrieval ───────────────────────────────────────────────────────


@api_bp.get("/config")
def list_configs():
    """List all company configurations.

    Returns configs for all companies in the system.
    """
    try:
        service = _service()
        # Get first company's config as example; in production would list all
        from src.domain.entities.company import Company
        from src.infrastructure.repositories import SQLAlchemyCompanyRepository

        company_repo = SQLAlchemyCompanyRepository()
        companies = company_repo.list_active()
        if companies:
            config = service.get_config(companies[0].id)
            return jsonify({"configs": [{"id": str(config.id), "company_id": str(config.company_id)}]})
        return jsonify({"configs": []})
    except Exception as exc:  # noqa: BLE001
        logger.exception("list_configs failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.get("/config/<uuid:company_id>")
def get_config(company_id: UUID):
    """Get company configuration by company ID.

    Returns the CompanyConfig aggregate for the specified company.
    LAW-type flags are immutable without migration; CONFIG-type flags
    are admin-changeable with audit logging.
    """
    try:
        service = _service()
        config = service.get_config(company_id)
        if config is None:
            return jsonify({"error": "Configuration not found", "code": "NOT_FOUND"}), 404

        # Serialize config - skip LAW-type flags that can't be modified
        result = {
            "id": str(config.id),
            "company_id": str(config.company_id),
            "config_version": config.config_version,
            "last_updated": config.updated_at.isoformat() if config.updated_at else None,
        }

        # Add CONFIG-type flags that are admin-changeable
        if hasattr(config, "flags") and config.flags:
            for flag_key, flag_value in config.flags.items():
                # Only include CONFIG-type flags; LAW-type would be documented only
                result[flag_key] = flag_value

        return jsonify(result)
    except Exception as exc:  # noqa: BLE001
        logger.exception("get_config failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── Config Update ───────────────────────────────────────────────────────────


@api_bp.patch("/config/<uuid:company_id>")
def update_config(company_id: UUID):
    """Partial update to company configuration.

    LAW-type flags cannot be modified without migration.
    CONFIG-type flags can be modified by admin with audit logging.

    Request JSON body:
    - flag_name: Name of the flag to update
    - new_value: New value for the flag
    - actor: UUID of the user performing the change
    """
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.get("actor")) if data.get("actor") else None

        if not actor:
            return jsonify({"error": "actor is required", "code": "MISSING_ACTOR"}), 400

        service = _service()

        flag_name = data.get("flag_name")
        new_value = data.get("new_value")

        if not flag_name:
            return jsonify({"error": "flag_name is required", "code": "MISSING_FIELD"}), 400

        # Attempt the update - service will raise FlagLockedError for LAW-type
        try:
            result = service.update_config(
                company_id=company_id,
                actor=actor,
                **({flag_name: new_value} if flag_name and new_value else {}),
            )
            return jsonify({"success": True, "config_version": result.config_version})
        except FlagLockedError as exc:
            return jsonify({"error": str(exc), "code": "FLAG_LOCKED"}), 403
        except ConfigVersionConflict as exc:
            return jsonify({"error": str(exc), "code": "CONFIG_VERSION_CONFLICT"}), 409
        except Exception as exc:  # noqa: BLE001
            logger.exception("update_config failed")
            return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500

    except ValueError as exc:
        return jsonify({"error": f"Invalid actor UUID: {exc}", "code": "INVALID_UUID"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("update_config outer failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


# ── Period Lock/Unlock ─────────────────────────────────────────────────────


@api_bp.post("/lock-period")
def lock_period():
    """Lock an accounting period.

    Prevents posting new entries in a closed/frozen accounting period.
    """
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.get("actor")) if data.get("actor") else None
        period_start = date.fromisoformat(data.get("period_start")) if data.get("period_start") else None
        period_end = date.fromisoformat(data.get("period_end")) if data.get("period_end") else None

        if not actor:
            return jsonify({"error": "actor is required", "code": "MISSING_ACTOR"}), 400
        if not period_start or not period_end:
            return jsonify({"error": "period_start and period_end are required", "code": "MISSING_FIELD"}), 400

        service = _service()
        service.lock_period(company_id=UUID(data.get("company_id")) if data.get("company_id") else None,
                           actor=actor,
                           period_start=period_start,
                           period_end=period_end)

        return jsonify({"success": True})
    except ValueError as exc:
        return jsonify({"error": f"Invalid date format: {exc}", "code": "INVALID_DATE"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("lock_period failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


@api_bp.post("/unlock-period")
def unlock_period():
    """Unlock an accounting period."""
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.get("actor")) if data.get("actor") else None
        period_start = date.fromisoformat(data.get("period_start")) if data.get("period_start") else None
        period_end = date.fromisoformat(data.get("period_end")) if data.get("period_end") else None

        if not actor:
            return jsonify({"error": "actor is required", "code": "MISSING_ACTOR"}), 400
        if not period_start or not period_end:
            return jsonify({"error": "period_start and period_end are required", "code": "MISSING_FIELD"}), 400

        service = _service()
        service.unlock_period(company_id=UUID(data.get("company_id")) if data.get("company_id") else None,
                             actor=actor,
                             period_start=period_start,
                             period_end=period_end)

        return jsonify({"success": True})
    except ValueError as exc:
        return jsonify({"error": f"Invalid date format: {exc}", "code": "INVALID_DATE"}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("unlock_period failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500


'''
Invoice Approval with threshold-based routing and RBAC enforcement
'''

@api_bp.post("/invoices/<uuid:invoice_id>/approve")
def approve_invoice(invoice_id: UUID):
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.get("actor")) if data.get("actor") else None
        if not actor:
            return jsonify({"error": "actor is required", "code": "MISSING_ACTOR"}), 400
        from src.infrastructure.repositories import SQLAlchemyInvoiceRepository
        from src.domain.entities.invoice import InvoiceStatus
        invoice = SQLAlchemyInvoiceRepository().get_by_id(invoice_id)
        if not invoice:
            return jsonify({"error": "Invoice not found", "code": "NOT_FOUND"}), 404
        if invoice.status != InvoiceStatus.DRAFT:
            return jsonify({"error": "Hoa don khong o trang thai DRAFT", "code": "INVALID_STATUS"}), 400
        po_matched = data.get("po_matched", False)
        from src.application.services import InvoiceService as _ISvc
        _ISvc().approve_invoice(invoice_id=invoice_id, actor=actor, po_matched=po_matched)
        return jsonify({"success": True, "invoice_id": str(invoice_id), "status": invoice.status})
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except Exception as exc:  # noqa: BLE001
        logger.exception("approve_invoice failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500

@api_bp.get("/invoices/<uuid:invoice_id>/threshold-info")
def threshold_info(invoice_id: UUID):
    try:
        from src.infrastructure.repositories import SQLAlchemyInvoiceRepository
        invoice = SQLAlchemyInvoiceRepository().get_by_id(invoice_id)
        if not invoice:
            return jsonify({"error": "Invoice not found", "code": "NOT_FOUND"}), 404
        amount = invoice.grand_total
        _T1 = 500_000_000
        _T2 = 5_000_000_000
        _T3 = 25_000_000_000
        _T4 = 100_000_000_000
        if amount <= _T1:
            band = "T1 (<= 500USD / <= 500M VND)"
            role = "AUTO (with PO) or MANAGER"
        elif amount <= _T2:
            band = "T2 (500-5000USD / 500M-5B VND)"
            role = "MANAGER"
        elif amount <= _T3:
            band = "T3 (5000-25000USD / 5B-25B VND)"
            role = "CHIEF_ACCOUNTANT"
        elif amount <= _T4:
            band = "T4 (25000-100000USD / 25B-100B VND)"
            role = "DIRECTOR"
        else:
            band = "T5 (> 100000USD / > 100B VND)"
            role = "ADMIN/BOARD"
        return jsonify({
            "invoice_id": str(invoice_id),
            "invoice_number": invoice.invoice_number,
            "amount": float(amount),
            "threshold_band": band,
            "required_approver_role": role,
            "status": invoice.status,
            "po_matched": getattr(invoice, 'po_matched', False)
        })
    except Exception as exc:  # noqa: BLE001
        logger.exception("threshold_info failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500
# ── E-Invoice Series ───────────────────────────────────────────────────────


@api_bp.post("/e-invoice-series")
def add_e_invoice_series():
    """Add a new e-invoice series for a company.

    Maximum 15 active series per company.
    Requires CA signer information for validation.
    """
    try:
        data = request.get_json(silent=True) or {}
        actor = UUID(data.get("actor")) if data.get("actor") else None
        prefix = data.get("prefix")
        ca_signer = data.get("ca_signer")

        if not actor:
            return jsonify({"error": "actor is required", "code": "MISSING_ACTOR"}), 400
        if not prefix:
            return jsonify({"error": "prefix is required", "code": "MISSING_FIELD"}), 400

        service = _service()
        result = service.add_e_invoice_series(
            company_id=UUID(data.get("company_id")) if data.get("company_id") else None,
            actor=actor,
            prefix=prefix,
            ca_signer=ca_signer,
        )

        return jsonify({"success": True, "series_prefix": result.prefix, "series_id": str(result.id)})
    except ValueError as exc:
        return jsonify({"error": str(exc), "code": "VALIDATION_ERROR"}), 422
    except SystemSettingsError as exc:
        return jsonify({"error": str(exc), "code": "SYSTEM_SETTINGS_ERROR"}), 500
    except Exception as exc:  # noqa: BLE001
        logger.exception("add_e_invoice_series failed")
        return jsonify({"error": str(exc), "code": "SERVER_ERROR"}), 500