"""Multi-currency voucher lines + bank balance linkage."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from src.bricks.voucher.domain import JournalLine
from src.bricks.voucher.services import (
    VoucherService,
)

COMPANY = uuid4()
BANK_ID = uuid4()


class OpenFY:
    def find_open_period(self, cid, d):
        return object()


class OkCOA:
    def validate_posting_account(self, cid, code, regime="tt133"):
        pass


class FakeNumbering:
    def issue(self, cid):
        return "PT/000001"


class FakeBankRepo:
    def __init__(self):
        self.rows: dict[str, Decimal] = {}

    def get_balance(self, bid):
        return self.rows.get(str(bid), Decimal(0))

    def adjust(self, bid, delta):
        self.rows[str(bid)] = self.get_balance(bid) + delta


def _svc(bank_repo=None):
    return VoucherService(
        fy=OpenFY(),
        coa=OkCOA(),
        numbering=FakeNumbering(),
        audit=None,
        bank_repo=bank_repo,
    )


ACTOR = uuid4()


def _body(lines):
    return {
        "company_id": COMPANY,
        "entry_date": date(2026, 8, 10),
        "description": "test",
        "actor": ACTOR,
        "reason": "test",
        "lines": [dict(l) for l in lines],
    }


class TestMultiCurrencyLines:
    """§2.4: lines carry original currency context alongside VND."""

    def test_line_accepts_currency_metadata(self):
        ln = JournalLine(
            account_code="1121",
            debit=Decimal(25400000),
            currency_code="USD",
            fx_rate=Decimal(25400),
            amount_original=Decimal(1000),
        )
        assert ln.currency_code == "USD"
        assert ln.amount_original == Decimal(1000)

    def test_default_is_base_currency(self):
        ln = JournalLine(account_code="111", debit=Decimal(100))
        assert ln.currency_code is None
        assert ln.fx_rate is None


class TestBankBalanceLinkage:
    """#2: voucher lines tagged with bank_account_id move bank balances."""

    def test_post_adjusts_bank_internal_balance(self):
        br = FakeBankRepo()
        svc = _svc(bank_repo=br)
        v = svc.create_voucher(
            **_body(
                [
                    {
                        "account_code": "1121",
                        "debit": "5000000",
                        "credit": "0",
                        "bank_account_id": str(BANK_ID),
                    },
                    {"account_code": "5111", "debit": "0", "credit": "5000000"},
                ]
            )
        )
        assert br.get_balance(BANK_ID) == Decimal(0)  # not yet posted
        svc.post_voucher(v.id, actor=uuid4(), reason="ok")
        assert br.get_balance(BANK_ID) == Decimal(5000000)

    def test_credit_reduces_bank_balance(self):
        br = FakeBankRepo()
        br.adjust(BANK_ID, Decimal(3000000))
        svc = _svc(bank_repo=br)
        v = svc.create_voucher(
            **_body(
                [
                    {
                        "account_code": "1121",
                        "debit": "0",
                        "credit": "2000000",
                        "bank_account_id": str(BANK_ID),
                    },
                    {"account_code": "6421", "debit": "2000000", "credit": "0"},
                ]
            )
        )
        svc.post_voucher(v.id, actor=uuid4(), reason="chi")
        assert br.get_balance(BANK_ID) == Decimal(1000000)

    def test_untagged_lines_dont_touch_bank(self):
        br = FakeBankRepo()
        svc = _svc(bank_repo=br)
        v = svc.create_voucher(
            **_body(
                [
                    {"account_code": "1111", "debit": "100", "credit": "0"},  # cash not bank
                    {"account_code": "5111", "debit": "0", "credit": "100"},
                ]
            )
        )
        svc.post_voucher(v.id, actor=uuid4(), reason="r")
        assert br.get_balance(BANK_ID) == Decimal(0)


class TestRevalProviderIntegration:
    """Revaluation's monetary_items provider reads posted voucher lines."""

    def test_provider_sees_currency_tagged_lines_after_post(self):
        br = FakeBankRepo()
        svc = _svc(bank_repo=br)
        v = svc.create_voucher(
            **_body(
                [
                    {
                        "account_code": "1121",
                        "debit": "25400000",
                        "credit": "0",
                        "currency_code": "USD",
                        "fx_rate": "25400",
                        "amount_original": "1000",
                        "bank_account_id": str(BANK_ID),
                    },
                    {"account_code": "5111", "debit": "0", "credit": "25400000"},
                ]
            )
        )
        svc.post_voucher(v.id, actor=uuid4(), reason="r")

        # Simulate revaluation provider scanning posted vouchers
        stored = svc._repo.get_by_company(COMPANY)
        fx_lines = [
            l for v2 in stored for l in v2.lines if l.currency_code and l.currency_code != "VND"
        ]
        assert len(fx_lines) == 1
        assert fx_lines[0].currency_code == "USD"
        assert fx_lines[0].amount_original == Decimal(1000)
