"""Unit tests for Invoice threshold checking and approval workflows."""

from uuid import UUID, uuid4

import pytest

from src.domain.entities.invoice import Invoice, InvoiceItem
from src.domain.entities.base import InvoiceStatus, InvoiceType, TaxRate


class TestInvoiceThresholdChecking:
    """Tests for invoice threshold-based approval workflow."""

    def test_invoice_auto_approved_under_threshold_with_po(self):
        """Invoice with amount ≤ T1 ($500) and valid PO should be auto-approved."""
        invoice = Invoice(
            serial="INV-001",
            invoice_number="INV-2026-001",
            invoice_type=InvoiceType.SALES_INVOICE,
            partner_name="Test Vendor",
            partner_tax_id="123456789011",
            notes="",
        )
        invoice.add_item(
            InvoiceItem(
                product_name="Test Product",
                quantity=1,
                unit_price=350,
                vat_rate=TaxRate.VAT_10,
            )
        )

        # Threshold check: $350 ≤ $500 → T1 band → auto-approved if PO matched
        # Simulate auto-approval with PO match
        invoice.approve(po_matched=True)
        assert invoice.status == InvoiceStatus.APPROVED
        assert invoice.updated_at is not None

    def test_invoice_routes_to_manager_above_t1_but_under_t2(self):
        """Invoice with T1 < amount ≤ T2 should route to manager for approval."""
        invoice = Invoice(
            serial="INV-002",
            invoice_number="INV-2026-002",
            invoice_type=InvoiceType.SALES_INVOICE,
            partner_name="Test Vendor",
            partner_tax_id="123456789011",
            notes="",
        )
        invoice.add_item(
            InvoiceItem(
                product_name="Test Product",
                quantity=1,
                unit_price=3000,
                vat_rate=TaxRate.VAT_10,
            )
        )

        # Amount $3,000 is in T2 band ($500-$5,000)
        # Should require manager approval, not auto-approved
        # Without PO match, stays DRAFT for manager review
        invoice.approve(po_matched=False)
        assert invoice.status == InvoiceStatus.DRAFT

    def test_invoice_routes_to_chief_accountant_above_t2_but_under_t3(self):
        """Invoice with T2 < amount ≤ T3 should route to chief accountant."""
        invoice = Invoice(
            serial="INV-003",
            invoice_number="INV-2026-003",
            invoice_type=InvoiceType.SALES_INVOICE,
            partner_name="Test Vendor",
            partner_tax_id="123456789011",
            notes="",
        )
        invoice.add_item(
            InvoiceItem(
                product_name="Test Product",
                quantity=1,
                unit_price=15000,
                vat_rate=TaxRate.VAT_10,
            )
        )

        # Amount $15,000 is in T3 band ($5,000-$25,000)
        # Chief accountant approval required
        invoice.approve(po_matched=False)
        assert invoice.status == InvoiceStatus.DRAFT

    def test_invoice_approval_prerequisite_status_draft(self):
        """Invoice can only be approved if status = DRAFT; non-DRAFT raises ValueError."""
        invoice = Invoice(
            serial="INV-004",
            invoice_number="INV-2026-004",
            invoice_type=InvoiceType.SALES_INVOICE,
            partner_name="Test Vendor",
            partner_tax_id="123456789011",
            notes="",
        )
        invoice.add_item(
            InvoiceItem(
                product_name="Test Product",
                quantity=1,
                unit_price=100,
                vat_rate=TaxRate.VAT_10,
            )
        )

        # First approval from DRAFT should succeed
        invoice.approve(po_matched=True)
        assert invoice.status == InvoiceStatus.APPROVED

        # Second approval attempt on already-APPROVED invoice should raise ValueError
        with pytest.raises(ValueError, match="Không thể duyệt hóa đơn ở trạng thái"):
            invoice.approve(po_matched=True)

    def test_invoice_rejects_approval_when_not_draft(self):
        """Invoice in non-DRAFT status cannot be approved."""
        invoice = Invoice(
            serial="INV-005",
            invoice_number="INV-2026-005",
            invoice_type=InvoiceType.SALES_INVOICE,
            partner_name="Test Vendor",
            partner_tax_id="123456789011",
            notes="",
        )
        invoice.add_item(
            InvoiceItem(
                product_name="Test Product",
                quantity=1,
                unit_price=100,
                vat_rate=TaxRate.VAT_10,
            )
        )

        # Manually set status to APPROVED (simulating prior approval)
        invoice.status = InvoiceStatus.APPROVED
        with pytest.raises(ValueError, match="Không thể duyệt hóa đơn ở trạng thái"):
            invoice.approve(po_matched=True)

    def test_invoice_with_no_po_routes_to_manager_even_under_t1(self):
        """Invoice under T1 but without PO reference should route to manager."""
        invoice = Invoice(
            serial="INV-005",
            invoice_number="INV-2026-005",
            invoice_type=InvoiceType.SALES_INVOICE,
            partner_name="Test Vendor",
            partner_tax_id="123456789011",
            notes="",
        )
        invoice.add_item(
            InvoiceItem(
                product_name="Test Product",
                quantity=1,
                unit_price=400,
                vat_rate=TaxRate.VAT_10,
            )
        )

        # Amount $400 is under T1 ($500), but no PO reference
        # Should NOT auto-approve, should route to manager (stays DRAFT)
        invoice.approve(po_matched=False)
        assert invoice.status == InvoiceStatus.DRAFT