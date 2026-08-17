"""Unit tests for CompanyService — business logic layer."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest
from unittest.mock import MagicMock

from src.domain.entities.base import AccountingRegime, CompanyType, TaxId
from src.domain.entities.company import BankAccount, Company, CompanyStatus
from src.domain.exceptions import (
    CompanyLockedError,
    CompanyNotFoundError,
    DuplicateMSTError,
    NotFoundError,
)
from src.application.services.company_service import CompanyService

FIXED_ID = UUID("11111111-1111-1111-1111-111111111111")
FIXED_ACTOR = UUID("22222222-2222-2222-2222-222222222222")


def _valid_kwargs(**overrides):
    """Build valid company kwargs with sane defaults."""
    base = {
        "id": FIXED_ID,
        "legal_name": "Công ty TNHH ABC Việt Nam",
        "mst": TaxId("0123456789"),
        "headquarters_address": "123 Nguyễn Văn Linh, Q.7, TP.HCM",
        "legal_representative": "Nguyễn Văn A",
        "business_reg_number": "0312345678",
        "business_reg_date": date(2020, 1, 15),
        "business_fields": ["6202", "4791"],
        "company_type": CompanyType.MULTI_LLC,
        "accounting_regime": AccountingRegime.TT99,
        "fiscal_year_start_month": 1,
        "fiscal_year_start_day": 1,
        "responsible_accountant_name": "Trần Thị B",
        "responsible_accountant_license": "KHMN-01234",
        "tax_agency": "Chi cục Thuế Q.7",
        "controlling_tax_office": "Cục Thuế TP.HCM",
        "bhxh_code": "0070123456",
        "bhxh_agency": "BHXH Quận 7",
        "authorized_capital": 1_000_000_000,
        "phone": "0281234567",
        "email": "info@abc.com",
        "website": "https://abc.com",
        "short_name": "ABC Co.",
        "bank_accounts": [
            BankAccount("VCB", "0071234567890", "Cty ABC", "PGD Q.7", is_primary=True),
        ],
        "status": CompanyStatus.ACTIVE,
        "is_active": True,
        "created_by": FIXED_ACTOR,
        "updated_by": FIXED_ACTOR,
        "config_version": 1,
        "legal_reviewed_at": None,
        "legal_reviewed_by": None,
        "mst_changed_at": None,
        "created_at": date(2024, 1, 1),
        "updated_at": date(2024, 1, 1),
    }
    base.update(overrides)
    return base


@pytest.fixture
def company_repo():
    return MagicMock()


@pytest.fixture
def service(company_repo):
    return CompanyService(company_repo=company_repo)


class TestCreateCompany:
    """CompanyService.create_company()"""

    def test_create_company_persists(self, service, company_repo):
        company = Company(**_valid_kwargs())
        company_repo.create.return_value = company

        result = service.create_company(**_valid_kwargs(), actor=FIXED_ACTOR)

        company_repo.create.assert_called_once()
        assert result is company

    def test_create_company_sets_created_by(self, service, company_repo):
        company = Company(**_valid_kwargs())
        company_repo.create.return_value = company

        service.create_company(**_valid_kwargs(), actor=FIXED_ACTOR)

        created = company_repo.create.call_args[0][0]
        assert created.created_by == FIXED_ACTOR

    def test_create_company_duplicate_mst_propagates(self, service, company_repo):
        company_repo.create.side_effect = DuplicateMSTError("đã được sử dụng")

        with pytest.raises(DuplicateMSTError, match="đã được sử dụng"):
            service.create_company(**_valid_kwargs(), actor=FIXED_ACTOR)

    def test_create_company_invalid_mst_propagates(self, service, company_repo):
        with pytest.raises(ValueError, match="Mã số thuế không hợp lệ"):
            service.create_company(**_valid_kwargs(mst="invalid"), actor=FIXED_ACTOR)


class TestGetCompany:
    """CompanyService.get_company()"""

    def test_get_company_found(self, service, company_repo):
        company = Company(**_valid_kwargs())
        company_repo.get_by_id.return_value = company

        result = service.get_company(FIXED_ID)

        company_repo.get_by_id.assert_called_once_with(FIXED_ID)
        assert result is company

    def test_get_company_not_found_raises(self, service, company_repo):
        company_repo.get_by_id.return_value = None
        with pytest.raises(CompanyNotFoundError, match="Không tìm thấy"):
            service.get_company(FIXED_ID)


class TestUpdateCompany:
    """CompanyService.update_company()"""

    def test_update_company_active(self, service, company_repo):
        # Arrange
        company = Company(**_valid_kwargs())
        company_repo.get_by_id.return_value = company
        company_repo.update.return_value = company

        # Act
        result = service.update_company(
            FIXED_ID, legal_name="Công ty TNHH XYZ", actor=FIXED_ACTOR
        )

        # Assert
        company_repo.get_by_id.assert_called_once_with(FIXED_ID)
        company_repo.update.assert_called_once()
        assert result is company

    def test_update_company_suspended_raises(self, service, company_repo):
        company = Company(**_valid_kwargs(status=CompanyStatus.SUSPENDED))
        company_repo.get_by_id.return_value = company

        with pytest.raises(CompanyLockedError, match="Không thể chỉnh sửa"):
            service.update_company(FIXED_ID, legal_name="XYZ", actor=FIXED_ACTOR)

    def test_update_company_dissolved_raises(self, service, company_repo):
        company = Company(**_valid_kwargs(status=CompanyStatus.DISSOLVED))
        company_repo.get_by_id.return_value = company

        with pytest.raises(CompanyLockedError, match="Không thể chỉnh sửa"):
            service.update_company(FIXED_ID, legal_name="XYZ", actor=FIXED_ACTOR)

    def test_update_company_not_found_raises(self, service, company_repo):
        company_repo.get_by_id.return_value = None
        with pytest.raises(CompanyNotFoundError):
            service.update_company(FIXED_ID, legal_name="XYZ", actor=FIXED_ACTOR)

    def test_update_company_sets_updated_by(self, service, company_repo):
        company = Company(**_valid_kwargs())
        company_repo.get_by_id.return_value = company
        company_repo.update.return_value = company

        service.update_company(
            FIXED_ID, legal_name="New Name", actor=FIXED_ACTOR
        )

        assert company.updated_by == FIXED_ACTOR


class TestDeactivateCompany:
    """CompanyService.deactivate_company()"""

    def test_deactivate_company(self, service, company_repo):
        company = Company(**_valid_kwargs())
        company_repo.get_by_id.return_value = company
        company_repo.update.return_value = company

        result = service.deactivate_company(FIXED_ID, actor=FIXED_ACTOR)

        assert company.status == CompanyStatus.SUSPENDED
        assert company.is_active is False
        company_repo.update.assert_called_once_with(company)

    def test_deactivate_dissolved_raises(self, service, company_repo):
        company = Company(**_valid_kwargs(status=CompanyStatus.DISSOLVED))
        company_repo.get_by_id.return_value = company
        with pytest.raises(CompanyLockedError, match="đã giải thể"):
            service.deactivate_company(FIXED_ID, actor=FIXED_ACTOR)


class TestDissolveCompany:
    """CompanyService.dissolve_company()"""

    def test_dissolve_company(self, service, company_repo):
        company = Company(**_valid_kwargs())
        company_repo.get_by_id.return_value = company
        company_repo.update.return_value = company

        result = service.dissolve_company(FIXED_ID, actor=FIXED_ACTOR)

        assert company.status == CompanyStatus.DISSOLVED
        assert company.is_active is False
        company_repo.update.assert_called_once_with(company)

    def test_dissolve_company_not_found(self, service, company_repo):
        company_repo.get_by_id.return_value = None
        with pytest.raises(CompanyNotFoundError):
            service.dissolve_company(FIXED_ID, actor=FIXED_ACTOR)


class TestCompanyStatusGuards:
    """CompanyService.validate_active_for_transaction() integration."""

    def test_active_company_passes_validation(self, service, company_repo):
        company = Company(**_valid_kwargs(status=CompanyStatus.ACTIVE))
        company_repo.get_by_id.return_value = company
        # Should not raise
        service.validate_active_for_transaction(FIXED_ID)

    def test_suspended_company_raises(self, service, company_repo):
        company = Company(**_valid_kwargs(status=CompanyStatus.SUSPENDED))
        company_repo.get_by_id.return_value = company
        with pytest.raises(CompanyLockedError, match="đã tạm ngừng"):
            service.validate_active_for_transaction(FIXED_ID)

    def test_dissolved_company_raises(self, service, company_repo):
        company = Company(**_valid_kwargs(status=CompanyStatus.DISSOLVED))
        company_repo.get_by_id.return_value = company
        with pytest.raises(CompanyLockedError, match="đã giải thể"):
            service.validate_active_for_transaction(FIXED_ID)