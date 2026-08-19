"""Serialize domain entities to JSON dicts for API responses."""

from datetime import datetime


def serialize_account(account) -> dict:
    """Serialize an Account entity to a dict."""
    return {
        "id": str(account.id),
        "code": account.code,
        "name": account.name,
        "category": account.category.value,
        "status": account.status.value,
        "vat_rate": account.vat_rate,
        "report_line": account.report_line,
        "tags": [t.value for t in account.account_tags],
        "created_by": str(account.created_by) if account.created_by else None,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
    }


def serialize_account_category(cat) -> dict:
    """Serialize an AccountCategory entity to a dict."""
    return {"id": None, "name": cat.value, "code_prefix": None, "is_system": True}


def serialize_account_tag(tag) -> dict:
def serialize_cost_center(cc) -> dict:
    """Serialize a CostCenter entity to a dict."""
    return {
        "id": str(cc.id),
        "code": cc.code,
        "name": cc.name,
        "status": cc.status.value,
        "description": cc.description or "",
        "created_by": str(cc.created_by) if cc.created_by else None,
        "created_at": cc.created_at.isoformat() if cc.created_at else None,
        "updated_at": cc.updated_at.isoformat() if cc.updated_at else None,
        "audit_checksum": cc.audit_checksum,
    }


def serialize_dimension(d) -> dict:
    """Serialize a Dimension entity to a dict."""
    return {
        "id": str(d.id),
        "code": d.code,
        "name": d.name,
        "type": d.type.value,
        "is_system": d.is_system,
        "description": d.description or "",
        "created_by": str(d.created_by) if d.created_by else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        "audit_checksum": d.audit_checksum,
    }


def serialize_dimension_value(dv) -> dict:
    """Serialize a DimensionValue entity to a dict."""
    return {
        "id": str(dv.id),
        "code": dv.code,
        "name": dv.name,
        "status": dv.status.value,
        "description": dv.description or "",
        "dimension_id": str(dv.dimension_id) if dv.dimension_id else None,
        "created_by": str(dv.created_by) if dv.created_by else None,
        "created_at": dv.created_at.isoformat() if dv.created_at else None,
        "updated_at": dv.updated_at.isoformat() if dv.updated_at else None,
        "audit_checksum": dv.audit_checksum,
    }    """Serialize an AccountTag entity to a dict."""
    return {"id": None, "name": tag.value, "code": tag.code, "is_mandatory": True}


def serialize_currency(currency) -> dict:
    """Serialize a Currency entity."""
    return {
        "code": currency.code,
        "name": currency.name,
        "is_base": currency.is_base,
    }


def serialize_exchange_rate(rate) -> dict:
    """Serialize an ExchangeRate entity."""
    return {
        "id": str(rate.id),
        "from_code": rate.from_currency.code,
        "to_code": rate.to_currency.code,
        "rate": float(rate.rate),
        "rate_type": rate.rate_type.value,
        "rate_date": rate.rate_date.isoformat(),
    }


def serialize_fiscal_year(fy) -> dict:
    """Serialize a FiscalYear entity."""
    return {
        "id": str(fy.id),
        "name": fy.name,
        "start_date": fy.start_date.isoformat(),
        "end_date": fy.end_date.isoformat(),
        "status": fy.status.value,
    }


def serialize_accounting_period(period) -> dict:
    """Serialize an AccountingPeriod entity."""
    return {
        "id": str(period.id),
        "name": period.name,
        "entry_date": period.entry_date.isoformat(),
        "status": period.status.value,
        "is_locked": period.is_locked,
    }


def serialize_period_lock_event(event) -> dict:
    """Serialize a PeriodLockEvent entity."""
    return {
        "id": str(event.id),
        "entity_type": event.entity_type,
        "entity_id": str(event.entity_id),
        "action": event.action.value,
        "requested_by": str(event.requested_by),
        "approved_by": str(event.approved_by) if event.approved_by else None,
        "requested_at": event.requested_at.isoformat(),
        "approved_at": event.approved_at.isoformat() if event.approved_by else None,
        "reason": event.reason,
        "prev_checksum": event.prev_checksum,
        "checksum": event.checksum,
    }
