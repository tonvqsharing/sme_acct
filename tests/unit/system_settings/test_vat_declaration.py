"""Unit tests — VatDeclarationService per specs-vat-declaration.md."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.system_settings.services import (
    InvalidPeriodError,
    VatDeclarationService,
)

COMPANY = uuid4()


def _out_lines():
    return [
        {
            "account_code": "3331100001",
            "debit": "0",
            "credit": "5500000",
            "entry_date": "2026-08-05",
        },
        {
            "account_code": "1121",
            "debit": "60500000",
            "credit": "0",
            "entry_date": "2026-08-05",
        },  # non-VAT line ignored
    ]


def _in_invoices(ded=Decimal(200000), pending=Decimal(0)):
    rows = [
        {
            "invoice_number": "0001234",
            "status": "POSTED",
            "deductibility": "DEDUCTIBLE",
            "vat_deductible": str(ded),
        }
    ]
    if pending:
        rows.append(
            {
                "invoice_number": "0009999",
                "status": "POSTED",
                "deductibility": "PENDING_PROOF",
                "vat_deductible": str(pending),
            }
        )
    return rows


def _svc(output=None, invoices=None):
    return VatDeclarationService(
        output_source=lambda cid, s, e: output or [],
        input_source=lambda cid, s, e: invoices or [],
    )


class TestFormula:
    def test_payable_when_output_exceeds_input(self):
        svc = _svc(output=_out_lines(), invoices=_in_invoices())
        d = svc.declare(COMPANY, 2026, 8)
        assert d["output_vat"] == Decimal(5500000)
        assert d["input_vat_deductible"] == Decimal(200000)
        assert d["vat_payable"] == Decimal(5300000)
        assert d["carry_forward"] == Decimal(0)

    def test_carry_forward_when_input_exceeds(self):
        svc = _svc(
            output=[
                {
                    "account_code": "3331",
                    "debit": "100000",
                    "credit": "0",
                    "entry_date": "2026-08-01",
                }
            ],
            invoices=_in_invoices(ded=Decimal(900000)),
        )
        d = svc.declare(COMPANY, 2026, 8)
        assert d["vat_payable"] == Decimal(0)
        assert d["carry_forward"] == Decimal(1000000)  # 900k−100k output

    def test_pending_proof_excluded_from_input_R_V2(self):
        svc = _svc(output=_out_lines(), invoices=_in_invoices(pending=Decimal(777777)))
        d = svc.declare(COMPANY, 2026, 8)
        assert d["input_vat_deductible"] == Decimal(200000)  # pending ignored
        assert d["detail"]["pending_proof_excluded"] == 1

    def test_empty_period_zeroes(self):
        d = _svc().declare(COMPANY, 2026, 8)
        assert (d["output_vat"], d["input_vat_deductible"], d["vat_payable"]) == (Decimal(0),) * 3

    @pytest.mark.parametrize("bad", [(2026, 13), (2026, 0)])
    def test_invalid_month_raises(self, bad):
        with pytest.raises(InvalidPeriodError):
            _svc().declare(COMPANY, bad[0], bad[1])

    def test_period_window_passed_to_sources(self):
        seen = {}

        def out_src(cid, s, e):
            seen["s"], seen["e"] = s, e
            return []

        def in_src(cid, s, e):
            return []

        VatDeclarationService(output_source=out_src, input_source=in_src).declare(COMPANY, 2026, 2)
        from datetime import date

        assert (seen["s"], seen["e"]) == (date(2026, 2, 1), date(2026, 2, 28))
