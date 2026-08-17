"""Fixtures for company module unit tests."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.domain.entities.base import (
    AccountingRegime,
    CompanyType,
)


@pytest.fixture
def valid_company_kwargs():
    return {
        "legal_name": "Công ty TNHH ABC Việt Nam",
        "mst": "0123456789",
        "headquarters_address": "123 Nguyễn Văn Linh, P. Tân Phong, Q.7, TP.HCM",
        "legal_representative": "Nguyễn Văn A",
        "business_reg_number": "0312345678",
        "business_reg_date": "2020-01-15",
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
        "bank_accounts": [],
        "created_by": uuid4(),
        "updated_by": uuid4(),
    }


@pytest.fixture
def household_company_kwargs():
    return {
        "legal_name": "Hộ kinh doanh An Bình",
        "mst": "0123456798",
        "headquarters_address": "45 Lê Lợi, Q.1, TP.HCM",
        "legal_representative": "Lê Văn C",
        "company_type": CompanyType.HOUSEHOLD,
        "accounting_regime": AccountingRegime.TT58_MICRO,
        "fiscal_year_start_month": 1,
        "fiscal_year_start_day": 1,
        "responsible_accountant_name": "",
        "responsible_accountant_license": "",
        "tax_agency": "Chi cục Thuế Q.1",
        "controlling_tax_office": "Cục Thuế TP.HCM",
        "bhxh_code": "",
        "bhxh_agency": "",
        "authorized_capital": 0,
        "phone": "0909123456",
        "email": "anbinh@gmail.com",
        "website": "",
        "short_name": "An Bình",
        "bank_accounts": [],
        "created_by": uuid4(),
        "updated_by": uuid4(),
    }
