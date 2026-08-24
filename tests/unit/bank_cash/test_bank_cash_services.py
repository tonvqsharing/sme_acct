"""Unit tests for BankAccountService & CashAccountService (fake repos)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.bank_cash.domain import (
    BankAccountStatus,
    CashAccountStatus,
)
from src.bricks.bank_cash.services import (
    AccountClosedError,
    BankAccountService,
    CashAccountService,
    DuplicateBankAccountError,
    DuplicateCashCodeError,
    NegativeBalanceError,
    SystemAccountProtectedError,
)

COMPANY = uuid4()
ACTOR = uuid4()


class FakeBankRepo:
    def __init__(self):
        self.rows = {}

    def create(self, acc):
        self.rows[acc.id] = acc
        return acc

    def get_by_id(self, aid):
        return self.rows.get(aid)

    def get_by_company(self, cid):
        return [a for a in self.rows.values() if a.company_id == cid]

    def update(self, acc):
        self.rows[acc.id] = acc
        return acc

    def find_primary(self, cid):
        for a in self.rows.values():
            if a.company_id == cid and a.is_primary:
                return a
        return None

    def validate_account_number_unique(self, cid, number):
        return not any(
            a.company_id == cid and a.account_number == number for a in self.rows.values()
        )


class FakeCashRepo:
    MAX_ACTIVE = None

    def __init__(self):
        self.rows = {}

    def create(self, acc):
        self.rows[acc.id] = acc
        return acc

    def get_by_id(self, aid):
        return self.rows.get(aid)

    def get_by_company(self, cid):
        return [a for a in self.rows.values() if a.company_id == cid]

    def update(self, acc):
        self.rows[acc.id] = acc
        return acc

    def validate_code_unique(self, cid, code):
        return not any(a.company_id == cid and a.code == code for a in self.rows.values())

    def last_checksum_for(self, aid):
        return None


@pytest.fixture()
def bank_svc():
    return BankAccountService(FakeBankRepo())


@pytest.fixture()
def cash_svc():
    return CashAccountService(FakeCashRepo())


BANK_BODY = {
    "company_id": COMPANY,
    "bank_name": "VietinBank",
    "account_number": "1020100001234",
    "account_holder": "Công ty TNHH ABC",
    "branch": "Hà Nội",
}


class TestBankAccounts:
    def test_create_stamps_checksum_and_active(self, bank_svc):
        acc = bank_svc.create_bank_account(
            **BANK_BODY, is_primary=False, actor=ACTOR, reason="open"
        )
        assert len(acc.checksum) == 64
        assert acc.status == BankAccountStatus.ACTIVE

    def test_duplicate_account_number_rejected(self, bank_svc):
        bank_svc.create_bank_account(**BANK_BODY, is_primary=False, actor=ACTOR, reason="a")
        with pytest.raises(DuplicateBankAccountError):
            bank_svc.create_bank_account(
                **{**BANK_BODY, "bank_name": "VTB"},
                is_primary=False,
                actor=ACTOR,
                reason="b",
            )

    def test_set_primary_swaps_previous(self, bank_svc):
        a = bank_svc.create_bank_account(**BANK_BODY, is_primary=True, actor=ACTOR, reason="a")
        b = bank_svc.create_bank_account(
            **{**BANK_BODY, "account_number": "999"},
            is_primary=False,
            actor=ACTOR,
            reason="b",
        )
        bank_svc.set_primary(b.id, ACTOR, "switch")
        assert bank_svc.get_account(b.id).is_primary is True
        assert bank_svc.get_account(a.id).is_primary is False

    def test_closed_blocks_entry_validation(self, bank_svc):
        acc = bank_svc.create_bank_account(**BANK_BODY, is_primary=False, actor=ACTOR, reason="a")
        bank_svc.close_account(acc.id, ACTOR, "shut")
        with pytest.raises(AccountClosedError):
            bank_svc.validate_before_entry(COMPANY, acc.id)

    def test_close_is_soft_retention(self, bank_svc):
        acc = bank_svc.create_bank_account(**BANK_BODY, is_primary=False, actor=ACTOR, reason="a")
        out = bank_svc.close_account(acc.id, ACTOR, "bye")
        assert out.status == BankAccountStatus.CLOSED
        assert bank_svc.get_account(acc.id) is not None


CASH_BODY = {"company_id": COMPANY, "name": "Quỹ tiền mặt tổng"}


class TestCashAccounts:
    def test_create_with_opening_balance_sets_current(self, cash_svc):
        c = cash_svc.create_cash_account(
            code="111",
            opening_balance=Decimal(5000000),
            actor=ACTOR,
            reason="init",
            **CASH_BODY,
        )
        assert c.current_balance == Decimal(5000000)
        assert c.status == CashAccountStatus.ACTIVE

    @pytest.mark.parametrize("bad", ["11", "11111", "0111", "AB1"])
    def test_code_must_match_tt_format(self, cash_svc, bad):
        with pytest.raises(ValueError, match="quỹ không hợp lệ|code must match"):
            cash_svc.create_cash_account(
                code=bad,
                opening_balance=Decimal(0),
                actor=ACTOR,
                reason="r",
                **CASH_BODY,
            )

    def test_duplicate_code_rejected(self, cash_svc):
        cash_svc.create_cash_account(
            code="111", opening_balance=Decimal(0), actor=ACTOR, reason="a", **CASH_BODY
        )
        with pytest.raises(DuplicateCashCodeError):
            cash_svc.create_cash_account(
                code="111",
                opening_balance=Decimal(0),
                actor=ACTOR,
                reason="b",
                **{**CASH_BODY, "name": "Q2"},
            )

    def test_deposit_increases_balance_and_chains_checksum(self, cash_svc):
        c = cash_svc.create_cash_account(
            code="111", opening_balance=Decimal(1000), actor=ACTOR, reason="i", **CASH_BODY
        )
        old = c.checksum
        out = cash_svc.update_balance(c.id, Decimal(500), actor=ACTOR, reason="thu")
        assert out.current_balance == Decimal(1500)
        assert out.checksum != old

    def test_withdraw_ok_within_balance(self, cash_svc):
        c = cash_svc.create_cash_account(
            code="111", opening_balance=Decimal(1000), actor=ACTOR, reason="i", **CASH_BODY
        )
        out = cash_svc.update_balance(c.id, Decimal(-400), actor=ACTOR, reason="chi")
        assert out.current_balance == Decimal(600)

    def test_negative_requires_chief_approval(self, cash_svc):
        """Rule: cannot go negative without chief accountant approval."""
        c = cash_svc.create_cash_account(
            code="111", opening_balance=Decimal(100), actor=ACTOR, reason="i", **CASH_BODY
        )
        with pytest.raises(NegativeBalanceError):
            cash_svc.update_balance(c.id, Decimal(-500), actor=ACTOR, reason="chi")
        ok = cash_svc.update_balance(
            c.id,
            Decimal(-500),
            actor=ACTOR,
            reason="chief ok",
            chief_approved=True,
        )
        assert ok.current_balance == Decimal(-400)

    def test_system_account_protected_from_close(self, cash_svc):
        c = cash_svc.create_cash_account(
            code="111",
            opening_balance=Decimal(0),
            actor=ACTOR,
            reason="seed",
            is_system=True,
            **CASH_BODY,
        )
        with pytest.raises(SystemAccountProtectedError):
            cash_svc.close_cash_account(c.id, ACTOR, "no")

    def test_closed_cash_blocks_entry(self, cash_svc):
        c = cash_svc.create_cash_account(
            code="111", opening_balance=Decimal(0), actor=ACTOR, reason="i", **CASH_BODY
        )
        cash_svc.close_cash_account(c.id, ACTOR, "retire")
        with pytest.raises(AccountClosedError):
            cash_svc.validate_before_entry(c.id)
