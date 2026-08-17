"""Unit tests for Company domain entity.

TDD red-green-refactor:
- Tests written BEFORE implementation
- Run pytest: expect failures (red)
- Implement src/domain/entities/company.py: expect passes (green)
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from src.domain.entities.company import (
    AccountingRegime,
    BankAccount,
    Company,
    CompanyLockedError,
    CompanyStatus,
    CompanyType,
    CompanyValidationError,
    InvalidCompanyTypeError,
)

# -------------------- FIXTURES --------------------


@pytest.fixture
def valid_kwargs():
    return {
        "legal_name": "Công ty TNHH ABC Việt Nam",
        "mst": "0123456789",
        "headquarters_address": "123 Nguyễn Văn Linh, P. Tân Phong, Q.7, TP.HCM",
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
        "tax_agency": "Chi cục Thuế Quận 7",
        "controlling_tax_office": "Cục Thuế TP.HCM",
        "bhxh_code": "0070123456",
        "bhxh_agency": "BHXH Quận 7",
        "authorized_capital": 1_000_000_000,
        "phone": "0281234567",
        "email": "info@abc.com",
        "website": "https://abc.com",
        "short_name": "ABC Co.",
        "bank_accounts": [
            BankAccount(
                bank_name="VCB",
                account_number="0071234567890",
                account_holder="Công ty TNHH ABC",
                branch="PGD Quận 7",
                is_primary=True,
            )
        ],
        "created_by": uuid4(),
        "updated_by": uuid4(),
    }


# -------------------- TESTS: Company Creation --------------------


class TestCompanyCreation:
    def test_valid_company_creation(self, valid_kwargs):
        company = Company(**valid_kwargs)
        assert company.legal_name == "Công ty TNHH ABC Việt Nam"
        assert str(company.mst) == "0123456789"
        assert company.company_type == CompanyType.MULTI_LLC
        assert company.status == CompanyStatus.ACTIVE
        assert company.is_active is True
        assert company.config_version == 1
        assert len(company.bank_accounts) == 1

    def test_mst_format_invalid_too_short(self, valid_kwargs):
        valid_kwargs["mst"] = "012345678"
        with pytest.raises(ValueError, match="Mã số thuế không hợp lệ"):
            Company(**valid_kwargs)

    def test_mst_format_invalid_alphanumeric(self, valid_kwargs):
        valid_kwargs["mst"] = "01234ABC89"
        with pytest.raises(ValueError, match="Mã số thuế không hợp lệ"):
            Company(**valid_kwargs)

    def test_mst_format_valid_branch_suffix(self, valid_kwargs):
        valid_kwargs["mst"] = "0123456789-001"
        company = Company(**valid_kwargs)
        assert str(company.mst) == "0123456789-001"

    def test_legal_name_empty_raises(self, valid_kwargs):
        valid_kwargs["legal_name"] = ""
        valid_kwargs["headquarters_address"] = ""
        with pytest.raises(CompanyValidationError, match="Địa chỉ trụ sở chính"):
            Company(**valid_kwargs)

    def test_legal_name_whitespace_only_raises(self, valid_kwargs):
        valid_kwargs["legal_name"] = "   "
        valid_kwargs["headquarters_address"] = ""
        with pytest.raises(CompanyValidationError, match="Địa chỉ trụ sở chính"):
            Company(**valid_kwargs)

    def test_headquarters_address_empty_raises(self, valid_kwargs):
        valid_kwargs["headquarters_address"] = ""
        with pytest.raises(CompanyValidationError, match="Địa chỉ"):
            Company(**valid_kwargs)

    def test_legal_representative_empty_raises(self, valid_kwargs):
        valid_kwargs["legal_representative"] = ""
        with pytest.raises(CompanyValidationError, match="Người đại diện"):
            Company(**valid_kwargs)

    def test_company_type_invalid_raises(self, valid_kwargs):
        # Simulate invalid type via constructor bypass
        valid_kwargs["company_type"] = "invalid_type"
        with pytest.raises(InvalidCompanyTypeError):
            Company(**valid_kwargs)

    def test_fiscal_year_month_out_of_range_raises(self, valid_kwargs):
        valid_kwargs["fiscal_year_start_month"] = 13
        with pytest.raises(ValueError, match="Tháng bắt đầu năm tài chính"):
            Company(**valid_kwargs)

    def test_fiscal_year_day_out_of_range_raises(self, valid_kwargs):
        valid_kwargs["fiscal_year_start_month"] = 1
        valid_kwargs["fiscal_year_start_day"] = 32
        with pytest.raises(ValueError, match="Ngày bắt đầu năm tài chính"):
            Company(**valid_kwargs)

    def test_fiscal_year_february_day_29_allowed(self, valid_kwargs):
        valid_kwargs["fiscal_year_start_month"] = 2
        valid_kwargs["fiscal_year_start_day"] = 29
        # Should not raise for leap year consideration
        Company(**valid_kwargs)

    def test_fiscal_year_february_day_30_raises(self, valid_kwargs):
        valid_kwargs["fiscal_year_start_month"] = 2
        valid_kwargs["fiscal_year_start_day"] = 30
        with pytest.raises(ValueError, match="Ngày bắt đầu năm tài chính"):
            Company(**valid_kwargs)

    def test_household_skips_bhxh(self, valid_kwargs):
        valid_kwargs.update(
            {
                "company_type": CompanyType.HOUSEHOLD,
                "accounting_regime": AccountingRegime.TT58_MICRO,
                "bhxh_code": "",
                "bhxh_agency": "",
                "responsible_accountant_name": "",
                "responsible_accountant_license": "",
                "authorized_capital": 0,
            }
        )
        company = Company(**valid_kwargs)
        assert company.company_type == CompanyType.HOUSEHOLD
        assert company.bhxh_code == ""

    def test_llc_requires_bhxh(self, valid_kwargs):
        valid_kwargs["bhxh_code"] = ""
        with pytest.raises(CompanyValidationError, match="BHXH"):
            Company(**valid_kwargs)

    def test_llc_requires_accountant_license(self, valid_kwargs):
        valid_kwargs["responsible_accountant_license"] = ""
        with pytest.raises(CompanyValidationError, match="MSKHMN"):
            Company(**valid_kwargs)

    def test_accounting_regime_auto_set_for_household(self, valid_kwargs):
        valid_kwargs.update(
            {
                "company_type": CompanyType.HOUSEHOLD,
                "bhxh_code": "",
                "bhxh_agency": "",
                "responsible_accountant_name": "",
                "responsible_accountant_license": "",
                "authorized_capital": 0,
            }
        )
        company = Company(**valid_kwargs)
        assert company.accounting_regime == AccountingRegime.TT58_MICRO

    def test_default_status_is_active(self, valid_kwargs):
        company = Company(**valid_kwargs)
        assert company.status == CompanyStatus.ACTIVE
        assert company.is_active is True

    def test_bank_accounts_stored(self, valid_kwargs):
        accounts = [
            BankAccount(
                bank_name="VCB",
                account_number="0071234567890",
                account_holder="Công ty TNHH ABC",
                branch="PGD Quận 7",
                is_primary=True,
            ),
            BankAccount(
                bank_name="TCB",
                account_number="19033123456789",
                account_holder="Công ty TNHH ABC",
                branch="PGD Q.3",
                is_primary=False,
            ),
        ]
        valid_kwargs["bank_accounts"] = accounts
        company = Company(**valid_kwargs)
        assert len(company.bank_accounts) == 2
        assert company.bank_accounts[0].bank_name == "VCB"
        assert company.bank_accounts[1].is_primary is False


# -------------------- TESTS: Company Status Lifecycle --------------------


class TestCompanyStatusLifecycle:
    def test_suspend_company(self, valid_kwargs):
        company = Company(**valid_kwargs)
        company.suspend()
        assert company.status == CompanyStatus.SUSPENDED
        assert company.is_active is False

    def test_reactivate_suspended_company(self, valid_kwargs):
        company = Company(**valid_kwargs)
        company.suspend()
        company.reactivate()
        assert company.status == CompanyStatus.ACTIVE
        assert company.is_active is True

    def test_dissolve_company(self, valid_kwargs):
        company = Company(**valid_kwargs)
        company.dissolve()
        assert company.status == CompanyStatus.DISSOLVED
        assert company.is_active is False

    def test_cannot_create_invoice_when_dissolved(self, valid_kwargs):
        company = Company(**valid_kwargs)
        company.dissolve()
        with pytest.raises(CompanyLockedError, match="giải thể"):
            company.validate_active_for_transaction()


# -------------------- TESTS: Fiscal Year Derivation --------------------


class TestFiscalYearDerivation:
    def test_calendar_year_jan_date(self, valid_kwargs):
        company = Company(**valid_kwargs)
        test_date = date(2026, 3, 15)
        fy, period = company.get_fiscal_year_and_period(test_date)
        assert fy == 2026
        assert period == 3

    def test_apr_start_fy_jan_belongs_to_prev_year(self, valid_kwargs):
        valid_kwargs["fiscal_year_start_month"] = 4
        valid_kwargs["fiscal_year_start_day"] = 1
        company = Company(**valid_kwargs)
        test_date = date(2026, 3, 31)
        fy, period = company.get_fiscal_year_and_period(test_date)
        assert fy == 2025
        assert period == 12

    def test_apr_start_fy_april_belongs_to_new_year(self, valid_kwargs):
        valid_kwargs["fiscal_year_start_month"] = 4
        valid_kwargs["fiscal_year_start_day"] = 1
        company = Company(**valid_kwargs)
        test_date = date(2026, 4, 1)
        fy, period = company.get_fiscal_year_and_period(test_date)
        assert fy == 2026
        assert period == 1


# -------------------- TESTS: MST Handling --------------------


class TestMSTHandling:
    def test_mst_stored_as_string(self, valid_kwargs):
        company = Company(**valid_kwargs)
        assert str(company.mst) == "0123456789"

    def test_mst_branch_suffix_preserved(self, valid_kwargs):
        valid_kwargs["mst"] = "0123456789-123"
        company = Company(**valid_kwargs)
        assert str(company.mst) == "0123456789-123"

    def test_mst_normalized_no_dash(self, valid_kwargs):
        # TaxId normalizes by removing dash if no branch suffix needed
        valid_kwargs["mst"] = "0123456789"
        company = Company(**valid_kwargs)
        assert "-" not in str(company.mst)


# -------------------- TESTS: Display Helpers --------------------


class TestDisplayHelpers:
    def test_get_display_name_returns_legal_name(self, valid_kwargs):
        company = Company(**valid_kwargs)
        assert company.get_display_name() == "Công ty TNHH ABC Việt Nam"

    def test_get_display_name_falls_back_to_name(self, valid_kwargs):
        valid_kwargs["legal_name"] = ""
        valid_kwargs["short_name"] = "ABC Co."
        company = Company(**valid_kwargs)
        assert company.get_display_name() == "ABC Co."


# -------------------- TESTS: DEACTIVATE/DISSOLVE Guards --------------------


class TestDeactivateGuards:
    def test_deactivate_company(self, valid_kwargs):
        company = Company(**valid_kwargs)
        company.deactivate()
        assert company.is_active is False
        assert company.status == CompanyStatus.SUSPENDED
