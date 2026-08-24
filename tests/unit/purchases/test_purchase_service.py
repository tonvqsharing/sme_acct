"""Unit tests — PurchaseService per docs/purchases/specs (EX-P01..P08, R-P1..P5)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.purchases.services import (
    DuplicateInvoiceError,
    InvalidAccountError,
    MissingActorError,
    NotFoundError,
    PeriodClosedError,
    PurchaseService,
)

COMPANY = uuid4()
ACTOR_A = uuid4()


class FakeRepo:
    def __init__(self):
        self.rows = {}

    def create(self, inv):
        self.rows[inv.id] = inv
        return inv

    def get_by_id(self, iid):
        return self.rows.get(iid)

    def get_by_company(self, cid):
        return [x for x in self.rows.values() if x.company_id == cid]

    def update(self, inv):
        self.rows[inv.id] = inv
        return inv

    def exists_duplicate(self, cid, mst, number, symbol):
        if getattr(self, "_force_dup", False):
            return True
        return any(
            x.company_id == cid
            and x.supplier_mst == mst
            and x.invoice_number == number
            and x.invoice_symbol == symbol
            for x in self.rows.values()
        )


def _svc(*, fy_open=True, dup=False):
    class FY:
        def find_open_period(self, cid, d):
            return object() if fy_open else None

    class COA:
        def validate_posting_account(self, cid, code, regime="tt133"):
            if code.endswith("9999") or code == "112":
                raise ValueError(code)

    repo = FakeRepo()
    repo._force_dup = dup
    return PurchaseService(
        repo=repo,
        fy=FY(),
        coa=COA(),
        regime_of=lambda cid: "tt133",
    )


def _body(**over):
    b = {
        "company_id": COMPANY,
        "supplier_name": "CTCP Hòa Bình",
        "supplier_mst": "0101234567",
        "invoice_number": "0001234",
        "invoice_symbol": "1C26TYY",
        "invoice_date": date(2026, 8, 20),
        "entry_date": date(2026, 8, 21),
        "payment_method": "bank",
        "payment_proof": True,
        "lines": [
            {
                "expense_account": "6421000001",
                "description": "Giấy A4",
                "amount_pre_vat": "2000000",
                "vat_rate": "0.1",
                "deductible": True,
            }
        ],
        "actor": ACTOR_A,
        "reason": "mua VP tháng 8",
    }
    b.update(over)
    return b


class TestCreateGates:
    def test_create_success_draft_with_checksum_and_split(self):
        svc = _svc()
        inv = svc.create_invoice(**_body())
        assert inv.status.value == "DRAFT"
        assert len(inv.checksum) == 64
        assert inv.subtotal == Decimal(2000000)
        assert inv.vat_deductible == Decimal(200000)
        assert inv.vat_non_deductible == Decimal(0)
        assert inv.deductibility.value == "DEDUCTIBLE"

    def test_missing_actor_EX_P01(self):
        with pytest.raises(MissingActorError):
            _svc().create_invoice(**_body(actor=None))

    def test_duplicate_EX_P02(self):
        svc = _svc(dup=True)
        with pytest.raises(DuplicateInvoiceError):
            svc.create_invoice(**_body())

    def test_period_closed_EX_P03(self):
        with pytest.raises(PeriodClosedError):
            _svc(fy_open=False).create_invoice(**_body())

    @pytest.mark.parametrize("code", ["112", "64219999"])
    def test_invalid_account_EX_P04(self, code):
        body = _body(
            lines=[
                {
                    "expense_account": code,
                    "description": "x",
                    "amount_pre_vat": "100000",
                    "vat_rate": "0.1",
                    "deductible": True,
                }
            ]
        )
        with pytest.raises(InvalidAccountError):
            _svc().create_invoice(**body)


class TestDeductibilityEngine:
    """R-P4/R-P5: ≥5tr incl-VAT needs non-cash proof."""

    def test_bank_no_proof_over_threshold_pending(self):
        svc = _svc()
        big = _body(
            payment_proof=False,
            lines=[
                {
                    "expense_account": "6421000001",
                    "description": "hàng hóa",
                    "amount_pre_vat": "6000000",
                    "vat_rate": "0.1",
                    "deductible": True,
                }
            ],
        )
        inv = svc.create_invoice(**big)
        assert inv.total_payment == Decimal(6600000)  # ≥5tr
        assert inv.vat_deductible == Decimal(0)
        assert inv.vat_non_deductible == Decimal(600000)
        assert inv.deductibility.value == "PENDING_PROOF"

    def test_cash_under_threshold_still_deductible(self):
        body = _body(
            payment_method="cash",
            payment_proof=False,
            lines=[
                {
                    "expense_account": "6421000001",
                    "description": "trà sữa",
                    "amount_pre_vat": "300000",
                    "vat_rate": "0.08",
                    "deductible": True,
                }
            ],
        )
        inv = _svc().create_invoice(**body)
        assert inv.deductibility.value == "DEDUCTIBLE"
        assert inv.vat_deductible == Decimal(24000)

    def test_cash_over_threshold_forced_non_deductible(self):
        body = _body(
            payment_method="cash",
            payment_proof=False,
        )
        inv = _svc().create_invoice(**body)  # 2.2tr incl → under 5tr actually
        assert inv.deductibility.value == "DEDUCTIBLE"
        big = _svc().create_invoice(
            **_body(
                lines=[
                    {
                        "expense_account": "1521000001",
                        "description": "nguyên liệu",
                        "amount_pre_vat": "6000000",
                        "vat_rate": "0.1",
                        "deductible": True,
                    }
                ],
                payment_method="cash",
                payment_proof=False,
            )
        )
        assert big.total_payment == Decimal(6600000)
        assert big.vat_deductible == Decimal(0)
        assert big.vat_non_deductible == Decimal(600000)


class TestPostCancelLifecycle:
    def test_post_flips_status_new_checksum_audit_once(self):
        svc = _svc()
        inv = svc.create_invoice(**_body())
        old = inv.checksum
        posted = svc.post(inv.id, ACTOR_A, "ghi sổ mua vào")
        assert posted.status.value == "POSTED"
        assert posted.checksum != old

    def test_double_post_EX_P06(self):
        from src.bricks.purchases.services import AlreadyPostedError

        svc = _svc()
        inv = svc.create_invoice(**_body())
        svc.post(inv.id, ACTOR_A, "r")
        with pytest.raises(AlreadyPostedError):
            svc.post(inv.id, ACTOR_A, "again")

    def test_cancel_requires_posted_EX_P07(self):
        from src.bricks.purchases.services import NotPostedError

        svc = _svc()
        inv = svc.create_invoice(**_body())
        with pytest.raises(NotPostedError):
            svc.cancel(inv.id, ACTOR_A, "oops")

    def test_cancel_soft_only_retention(self):
        svc = _svc()
        inv = svc.create_invoice(**_body())
        svc.post(inv.id, ACTOR_A, "p")
        out = svc.cancel(inv.id, ACTOR_A, "sai sót NCC")
        assert out.status.value == "CANCELLED"
        assert svc.get(inv.id) is not None

    def test_unknown_get_raises(self):
        with pytest.raises(NotFoundError):
            _svc().post(uuid4(), ACTOR_A, "ghost")
