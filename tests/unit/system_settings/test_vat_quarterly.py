"""Quarterly VAT wrapper — sums three monthly declarations."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.system_settings.services import (
    InvalidPeriodError,
    VatDeclarationService,
)

COMPANY = uuid4()

# Monthly raw data simulating three months of activity
MONTHLY_DATA = {
    1: {"output": Decimal(1000000), "input": Decimal(300000)},
    2: {"output": Decimal(2000000), "input": Decimal(500000)},
    3: {"output": Decimal(1500000), "input": Decimal(400000)},
}


def _svc():
    def output_src(cid, s, e):
        # Return synthetic lines based on which month the window covers
        from datetime import date

        total = Decimal(0)
        for m, v in MONTHLY_DATA.items():
            ms = date(2026, m, 1)
            me = date(2026, m, 28)
            if s <= me and e >= ms:
                total += v["output"]
        return (
            [
                {
                    "account_code": "3331",
                    "debit": "0",
                    "credit": str(total),
                    "entry_date": s.isoformat(),
                }
            ]
            if total
            else []
        )

    def input_src(cid, s, e):
        from datetime import date

        total = Decimal(0)
        rows = []
        for m, v in MONTHLY_DATA.items():
            ms = date(2026, m, 1)
            me = date(2026, m, 28)
            if s <= me and e >= ms:
                total += v["input"]
        if total:
            rows.append(
                {
                    "invoice_number": "x",
                    "status": "POSTED",
                    "deductibility": "DEDUCTIBLE",
                    "vat_deductible": str(total),
                }
            )
        return rows

    return VatDeclarationService(output_source=output_src, input_source=input_src)


class TestQuarterlyWrapper:
    def test_q1_sums_three_months(self):
        d = _svc().declare(COMPANY, year=2026, quarter=1)
        assert d["output_vat"] == Decimal(4500000)
        assert d["input_vat_deductible"] == Decimal(1200000)
        assert d["vat_payable"] == Decimal(3300000)

    @pytest.mark.parametrize("q", [1, 2, 3, 4])
    def test_valid_quarters_accepted(self, q):
        _svc().declare(COMPANY, year=2026, quarter=q)

    @pytest.mark.parametrize("bad_q", [0, 5])
    def test_invalid_quarter_raises(self, bad_q):
        with pytest.raises(InvalidPeriodError):
            _svc().declare(COMPANY, year=2026, quarter=bad_q)

    def test_month_and_quarter_mutually_exclusive(self):
        with pytest.raises(InvalidPeriodError):
            _svc().declare(COMPANY, year=2026, month=3, quarter=1)

    def test_neither_month_nor_quarter_raises(self):
        with pytest.raises(InvalidPeriodError):
            _svc().declare(COMPANY, year=2026)
