"""Serializers stubs."""

from __future__ import annotations

from src.domain.entities.contact import Partner
from src.domain.entities.invoice import Invoice
from src.domain.entities.voucher import Voucher


def serialize_partner(partner: Partner) -> dict:
    return {
        "id": str(partner.id),
        "code": partner.code,
        "name": partner.name,
        "tax_id": str(partner.tax_id) if partner.tax_id else None,
        "entity_type": partner.entity_type.value,
        "address": partner.address,
        "phone": partner.phone,
        "email": partner.email,
        "tax_agency": partner.tax_agency,
        "is_active": partner.is_active,
    }


def serialize_invoice(invoice: Invoice) -> dict:
    return {
        "id": str(invoice.id),
        "serial": invoice.serial,
        "invoice_number": invoice.invoice_number,
        "invoice_type": invoice.invoice_type.value,
        "status": invoice.status.value,
        "issue_date": invoice.issue_date.isoformat(),
        "partner_id": str(invoice.partner_id) if invoice.partner_id else None,
        "partner_name": invoice.partner_name,
        "partner_tax_id": invoice.partner_tax_id,
        "subtotal": invoice.subtotal,
        "vat_total": invoice.vat_total,
        "grand_total": invoice.grand_total,
        "currency": invoice.currency,
        "items": [
            {
                "product_name": i.product_name,
                "unit": i.unit,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "vat_rate": i.vat_rate.value,
                "vat_amount": i.vat_amount,
                "total_amount": i.total_amount,
            }
            for i in invoice.items
        ],
    }


def serialize_voucher(voucher: Voucher) -> dict:
    return {
        "id": str(voucher.id),
        "voucher_number": voucher.voucher_number,
        "voucher_type": voucher.voucher_type.value,
        "status": voucher.status.value,
        "voucher_date": voucher.voucher_date.isoformat(),
        "accounting_date": voucher.accounting_date.isoformat(),
        "lines": [
            {
                "account_code": str(line.account_code),
                "description": line.description,
                "debit": line.debit,
                "credit": line.credit,
            }
            for line in voucher.lines
        ],
    }


def serialize_currency(currency) -> dict:
    return {
        "code": currency.code,
        "name": currency.name,
        "symbol": currency.symbol,
        "decimal_places": currency.decimal_places,
        "is_base": currency.is_base,
        "is_active": currency.is_active,
        "display_format": currency.display_format,
    }


def serialize_exchange_rate(rate) -> dict:
    return {
        "currency_code": rate.currency_code,
        "rate_date": rate.rate_date.isoformat(),
        "rate_type": rate.rate_type.value,
        "rate": str(rate.rate),
        "source": rate.source,
        "actor_id": str(rate.actor),
        "created_at": rate.created_at.isoformat(),
        "note": rate.note,
    }


def serialize_revaluation_run(run) -> dict:
    return {
        "id": str(run.id),
        "company_id": str(run.company_id),
        "period_start": run.period_start.isoformat(),
        "period_end": run.period_end.isoformat(),
        "rate_date": run.rate_date.isoformat(),
        "status": run.status.value,
        "actor_id": str(run.actor),
        "approver_id": str(run.approver) if run.approver else None,
        "posted_at": run.posted_at.isoformat() if run.posted_at else None,
        "entries": [
            {
                "account_code": e.account_code,
                "currency_code": e.currency_code,
                "balance_original": str(e.balance_original),
                "rate_applied": str(e.rate_applied),
                "old_vnd": str(e.old_vnd),
                "new_vnd": str(e.new_vnd),
                "difference": str(e.difference),
                "posting_side": e.posting_side.value if e.posting_side else None,
            }
            for e in run.entries
        ],
    }


def serialize_fx_difference(fx) -> dict:
    return {
        "company_id": str(fx.company_id),
        "account_code": fx.account_code,
        "currency_code": fx.currency_code,
        "period_start": fx.period_start.isoformat(),
        "period_end": fx.period_end.isoformat(),
        "opening_original": str(fx.opening_original),
        "opening_vnd": str(fx.opening_vnd),
        "movements_original": str(fx.movements_original),
        "movements_vnd": str(fx.movements_vnd),
        "closing_original": str(fx.closing_original),
        "closing_vnd": str(fx.closing_vnd),
        "revaluation_adjustment": str(fx.revaluation_adjustment),
        "cumulative_difference": str(fx.cumulative_difference),
    }
