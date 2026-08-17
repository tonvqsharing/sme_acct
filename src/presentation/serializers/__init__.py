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
