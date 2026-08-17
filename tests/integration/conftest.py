"""Integration test infrastructure — plain SQLAlchemy, no Flask."""

from __future__ import annotations

import os
import sys
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.infrastructure.database import db  # flask-sqlalchemy instance
from src.infrastructure.database.models import Base  # DeclarativeBase


@pytest.fixture()
def repo():
    """SQLAlchemyCompanyRepository backed by an in-memory SQLite session.

    Replaces Flask-SQLAlchemy's scoped ``db.session`` with a plain
    SQLAlchemy session so tests don't need a live Flask app context.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    plain_session = sessionmaker(bind=engine)()

    # Swap Flask-SQLAlchemy's scoped session for our plain session
    # (type: ignore is intentional — substituting a plain Session for
    #    scoped_session[Session] is the standard testing pattern here)
    original = db.session
    db.session = plain_session  # type: ignore[assignment]
    try:
        from src.infrastructure.repositories import SQLAlchemyCompanyRepository

        yield SQLAlchemyCompanyRepository()
    finally:
        db.session = original
        close_all_sessions()
        engine.dispose()


# ── Domain helpers ───────────────────────────────────────────────

FIXED_ID = UUID("11111111-1111-1111-1111-111111111111")
FIXED_CREATOR = UUID("22222222-2222-2222-2222-222222222222")


def valid_company_kwargs(**overrides):
    from datetime import date

    from src.domain.entities.base import TaxId
    from src.domain.entities.company import (
        AccountingRegime,
        BankAccount,
        CompanyStatus,
        CompanyType,
    )

    base = {
        "id": FIXED_ID,
        "legal_name": "Công ty TNHH ABC Việt Nam",
        "mst": TaxId("0123456789"),
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
        "created_by": FIXED_CREATOR,
        "updated_by": FIXED_CREATOR,
        "config_version": 1,
        "legal_reviewed_at": None,
        "legal_reviewed_by": None,
        "mst_changed_at": None,
        "created_at": date(2024, 1, 1),
        "updated_at": date(2024, 1, 1),
    }
    base.update(overrides)
    return base
