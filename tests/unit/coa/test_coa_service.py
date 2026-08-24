"""COA unit tests via fake repo."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.bricks.coa.domain import Account, AccountStatus
from src.bricks.coa.services import (
    AccountNotFoundError,
    AccountService,
    AggregateAccountError,
    CircularParentError,  # noqa: F401 - reserved for cycle guard
    DuplicateAccountError,
    HasActiveChildrenError,
    InactiveAccountError,
    ParentNotAggregateError,
    ParentNotFoundError,
)

COMPANY = uuid4()


class FakeRepo:
    def __init__(self):
        self.accounts: dict[str, Account] = {}

    def create(self, acc):
        self.accounts[(str(acc.company_id), acc.code)] = acc
        return acc

    def get_by_code(self, company_id, code):
        return self.accounts.get((str(company_id), code))

    def get_by_company(self, company_id):
        return [a for k, a in self.accounts.items() if k[0] == str(company_id)]

    def update(self, acc):
        self.accounts[(str(acc.company_id), acc.code)] = acc
        return acc

    def validate_code_unique(self, company_id, code):
        return (str(company_id), code) not in self.accounts


@pytest.fixture()
def svc():
    return AccountService(FakeRepo())


@pytest.fixture()
def repo(svc):
    return svc._repo


class TestCreateAccount:
    @pytest.mark.parametrize("code", ["111", "1311", "999", "990"])
    def test_valid_codes_accepted(self, svc, code):
        acc = svc.create_account(
            company_id=COMPANY,
            code=code,
            name="T",
            actor=uuid4(),
            reason="r",
        )
        assert acc.status == AccountStatus.ACTIVE

    @pytest.mark.parametrize("bad", ["", "01", "12", "12345", "ABC", "0111"])
    def test_invalid_codes_rejected(self, svc, bad):
        with pytest.raises(ValueError):
            svc.create_account(
                company_id=COMPANY,
                code=bad,
                name="T",
                actor=uuid4(),
                reason="r",
            )

    def test_duplicate_code_rejected(self, svc):
        svc.create_account(COMPANY, "111", "Tiền", actor=uuid4(), reason="r")
        with pytest.raises(DuplicateAccountError):
            svc.create_account(COMPANY, "111", "Dup", actor=uuid4(), reason="r")

    def test_same_code_ok_other_company(self, svc):
        svc.create_account(COMPANY, "111", "A", actor=uuid4(), reason="r")
        other = uuid4()
        acc = svc.create_account(other, "111", "B", actor=uuid4(), reason="r")
        assert isinstance(acc.company_id, UUID)

    def test_parent_must_exist(self, svc):
        with pytest.raises(ParentNotFoundError):
            svc.create_account(
                COMPANY,
                "1111",
                "TGNH VietinBank",
                parent_code="112",
                actor=uuid4(),
                reason="r",
            )

    def test_detail_under_aggregate_ok(self, svc, repo):
        repo.create(Account(company_id=COMPANY, code="112", name="Tiền gửi NH"))
        acc = svc.create_account(
            COMPANY,
            "1121",
            "VietinBank",
            parent_code="112",
            actor=uuid4(),
            reason="r",
        )
        assert acc.is_detail is True

    def test_detail_under_detail_rejected(self, svc, repo):
        repo.create(Account(company_id=COMPANY, code="1121", name="VTB"))
        with pytest.raises(ParentNotAggregateError):
            svc.create_account(
                COMPANY,
                "1122",
                "Sub",
                parent_code="1121",
                actor=uuid4(),
                reason="r",
            )


class TestPostingGate:
    def _setup(self, svc, repo):
        repo.create(Account(company_id=COMPANY, code="112", name="Agg"))
        repo.create(Account(company_id=COMPANY, code="1121", name="VTB"))
        repo.create(
            Account(
                company_id=COMPANY,
                code="1129",
                name="Old",
                status=AccountStatus.INACTIVE,
            )
        )

    def test_detail_active_passes(self, svc, repo):
        self._setup(svc, repo)
        svc.validate_posting_account(COMPANY, "1121")  # no raise

    def test_aggregate_rejected(self, svc, repo):
        self._setup(svc, repo)
        with pytest.raises(AggregateAccountError):
            svc.validate_posting_account(COMPANY, "112")

    def test_inactive_rejected(self, svc, repo):
        self._setup(svc, repo)
        with pytest.raises(InactiveAccountError):
            svc.validate_posting_account(COMPANY, "1129")

    def test_unknown_rejected(self, svc, repo):
        self._setup(svc, repo)
        with pytest.raises(AccountNotFoundError):
            svc.validate_posting_account(COMPANY, "999")


class TestDeactivate:
    def test_cannot_deactivate_with_active_children(self, svc, repo):
        agg = repo.create(Account(company_id=COMPANY, code="112", name="Agg"))
        repo.create(Account(company_id=COMPANY, code="1121", name="VTB", parent_code="112"))
        assert agg.is_detail is False
        with pytest.raises(HasActiveChildrenError):
            svc.deactivate_account(COMPANY, "112", actor=uuid4(), reason="r")

    def test_leaf_deactivates_soft(self, svc, repo):
        repo.create(Account(company_id=COMPANY, code="1121", name="Leaf"))
        out = svc.deactivate_account(COMPANY, "1121", actor=uuid4(), reason="retire")
        assert out.status == AccountStatus.INACTIVE
        assert svc.get_account(COMPANY, "1121") is not None
