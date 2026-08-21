"""Tests for Company domain entity."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from src.bricks.company.domain import (
    AccountingRegime,
    BankAccount,
    Company,
    CompanyStatus,
    CompanyType,
    TaxId,
)


class TestBankAccount:
    """BankAccount value object tests."""

    def test_create_bank_account(self):
        account = BankAccount(
            bank_name="VietinBank",
            account_number="1234567890",
            account_holder="Công ty TNHH ABC",
            branch="Chi nhánh Hà Nội",
            is_primary=True,
        )
        assert account.bank_name == "VietinBank"
        assert account.account_number == "1234567890"
        assert account.is_primary is True

    def test_bank_account_default_not_primary(self):
        account = BankAccount(
            bank_name="Sacombank",
            account_number="0987654321",
            account_holder="Công ty TNHH ABC",
            branch="Chi nhánh HCM",
        )
        assert account.is_primary is False


class TestCompany:
    """Company entity tests per Luật Doanh nghiệp 2020."""

    def test_create_company_minimal(self):
        company = Company(
            id=uuid4(),
            legal_name="Công ty TNHH ABC",
            mst=TaxId("0123456789"),
        )
        assert company.legal_name == "Công ty TNHH ABC"
        assert company.mst.value == "0123456789"
        assert company.status == CompanyStatus.ACTIVE
        assert company.is_active is True

    def test_create_company_full_fields(self):
        company = Company(
            id=uuid4(),
            legal_name="Công ty TNHH ABC",
            mst=TaxId("0123456789"),
            headquarters_address="123 Đường Lê Lợi, Hà Nội",
            legal_representative="Nguyễn Văn A",
            business_reg_number="0123456789",
            business_reg_date=date(2020, 1, 15),
            business_fields=["6201", "6202"],
            company_type=CompanyType.MULTI_LLC,
            accounting_regime=AccountingRegime.TT99,
            fiscal_year_start_month=1,
            fiscal_year_start_day=1,
            responsible_accountant_name="Trần Văn B",
            responsible_accountant_license="MSKHMN-001",
            tax_agency="Chi cục Thuế quận Hoàn Kiếm",
            controlling_tax_office="Cục Thuế Hà Nội",
            bhxh_code="BHXH-001",
            bhxh_agency="BHXH Hà Nội",
            authorized_capital=Decimal(1000000000),
            phone="024-12345678",
            email="info@abc.vn",
            website="https://abc.vn",
            short_name="ABC",
            bank_accounts=[
                BankAccount(
                    bank_name="VietinBank",
                    account_number="1234567890",
                    account_holder="Công ty TNHH ABC",
                    branch="Chi nhánh Hà Nội",
                    is_primary=True,
                )
            ],
            created_by=uuid4(),
            updated_by=uuid4(),
        )
        assert company.company_type == CompanyType.MULTI_LLC
        assert company.accounting_regime == AccountingRegime.TT99
        assert len(company.bank_accounts) == 1
        assert company.bank_accounts[0].is_primary is True

    def test_company_config_version_default(self):
        company = Company(
            id=uuid4(),
            legal_name="Công ty TNHH ABC",
            mst=TaxId("0123456789"),
        )
        assert company.config_version == 0

    def test_company_fiscal_year_defaults(self):
        company = Company(
            id=uuid4(),
            legal_name="Công ty TNHH ABC",
            mst=TaxId("0123456789"),
        )
        assert company.fiscal_year_start_month == 1
        assert company.fiscal_year_start_day == 1

    def test_company_status_lifecycle(self):
        company = Company(
            id=uuid4(),
            legal_name="Công ty TNHH ABC",
            mst=TaxId("0123456789"),
        )
        assert company.status == CompanyStatus.ACTIVE

        company.status = CompanyStatus.SUSPENDED
        assert company.status == CompanyStatus.SUSPENDED

        company.status = CompanyStatus.DISSOLVED
        assert company.status == CompanyStatus.DISSOLVED

    def test_company_bank_accounts_empty_default(self):
        company = Company(
            id=uuid4(),
            legal_name="Công ty TNHH ABC",
            mst=TaxId("0123456789"),
        )
        assert company.bank_accounts == []

    def test_company_business_fields_empty_default(self):
        company = Company(
            id=uuid4(),
            legal_name="Công ty TNHH ABC",
            mst=TaxId("0123456789"),
        )
        assert company.business_fields == []
