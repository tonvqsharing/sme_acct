"""Company storage layer — SQLAlchemy models + repository adapters.

Only file with SQLAlchemy imports in the brick.
"""

from typing import Any, List, Dict

import json
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    Integer,
    Numeric,
    String,
    Text,
    TypeDecorator,
    func,
)
from sqlalchemy.orm import Mapped, Session, mapped_column


class JSONType(TypeDecorator[str]):
    """Store Python lists/dicts as JSON strings in Text columns."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any | None, dialect: Any) -> str:
        if value is not None:
            return json.dumps(value)
        return ""

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            return json.loads(value)
        return ""


from src.bricks.company.contract import CompanyRepositoryPort
from src.bricks.company.domain import (
    AccountingRegime,
    BankAccount,
    Company,
    CompanyStatus,
    CompanyType,
    TaxId,
)

# ─── Base ────────────────────────────────────────────────────────────────

try:
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

except ImportError:
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()  # type: ignore[misc]


# ─── Models ──────────────────────────────────────────────────────────────


class CompanyModel(Base):
    """SQLAlchemy model for companies table."""

    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Legal mandatory
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    mst: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    headquarters_address: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    legal_representative: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    business_reg_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    business_reg_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    business_fields: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True, default="[]")

    # Classification
    company_type: Mapped[str] = mapped_column(String(30), nullable=False, default="multi_llc")
    accounting_regime: Mapped[str] = mapped_column(String(30), nullable=False, default="tt99")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Accounting
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    fiscal_year_start_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    responsible_accountant_name: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    responsible_accountant_license: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Tax / BHXH
    tax_agency: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    controlling_tax_office: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    bhxh_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bhxh_agency: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Operational
    authorized_capital: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    phone: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    website: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    short_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bank_accounts: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True, default="[]")

    # Audit
    created_at: Mapped[date | None] = mapped_column(
        Date, nullable=True, server_default=func.current_date()
    )
    updated_at: Mapped[date | None] = mapped_column(
        Date, nullable=True, onupdate=func.current_date()
    )
    created_by: Mapped[UUID | None] = mapped_column(nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(nullable=True)
    config_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    legal_reviewed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    legal_reviewed_by: Mapped[UUID | None] = mapped_column(nullable=True)
    mst_changed_at: Mapped[date | None] = mapped_column(Date, nullable=True)


# ─── Repository ──────────────────────────────────────────────────────────


class SQLAlchemyCompanyRepository(CompanyRepositoryPort):
    """SQLAlchemy implementation of CompanyRepositoryPort."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, company: Company) -> Company:
        model = CompanyModel(
            id=company.id,
            legal_name=company.legal_name,
            mst=company.mst.value,
            headquarters_address=company.headquarters_address,
            legal_representative=company.legal_representative,
            business_reg_number=company.business_reg_number,
            business_reg_date=company.business_reg_date,
            business_fields=company.business_fields,
            company_type=company.company_type.value,
            accounting_regime=company.accounting_regime.value,
            status=company.status.value,
            is_active=company.is_active,
            fiscal_year_start_month=company.fiscal_year_start_month,
            fiscal_year_start_day=company.fiscal_year_start_day,
            responsible_accountant_name=company.responsible_accountant_name,
            responsible_accountant_license=company.responsible_accountant_license,
            tax_agency=company.tax_agency,
            controlling_tax_office=company.controlling_tax_office,
            bhxh_code=company.bhxh_code,
            bhxh_agency=company.bhxh_agency,
            authorized_capital=company.authorized_capital,
            phone=company.phone,
            email=company.email,
            website=company.website,
            short_name=company.short_name,
            bank_accounts=[vars(b) for b in company.bank_accounts],
            created_by=company.created_by,
            updated_by=company.updated_by,
            config_version=company.config_version,
        )
        self._session.add(model)
        self._session.commit()
        return company

    def get_by_id(self, company_id: UUID) -> Company | None:
        model = self._session.get(CompanyModel, company_id)
        if model is None:
            return None
        return self._to_domain(model)

    def get_by_mst(self, mst: str) -> Company | None:
        model = self._session.query(CompanyModel).filter(CompanyModel.mst == mst).first()
        if model is None:
            return None
        return self._to_domain(model)

    def list_active(self) -> list[Company]:
        models = self._session.query(CompanyModel).filter(CompanyModel.is_active == True).all()
        return [self._to_domain(m) for m in models]

    def update(self, company: Company, actor: UUID) -> Company:
        model = self._session.get(CompanyModel, company.id)
        if model is None:
            raise ValueError(f"Company {company.id} not found")

        model.legal_name = company.legal_name
        model.headquarters_address = company.headquarters_address
        model.legal_representative = company.legal_representative
        model.business_reg_number = company.business_reg_number
        model.business_reg_date = company.business_reg_date
        model.business_fields = company.business_fields
        model.company_type = company.company_type.value
        model.accounting_regime = company.accounting_regime.value
        model.status = company.status.value
        model.is_active = company.is_active
        model.fiscal_year_start_month = company.fiscal_year_start_month
        model.fiscal_year_start_day = company.fiscal_year_start_day
        model.responsible_accountant_name = company.responsible_accountant_name
        model.responsible_accountant_license = company.responsible_accountant_license
        model.tax_agency = company.tax_agency
        model.controlling_tax_office = company.controlling_tax_office
        model.bhxh_code = company.bhxh_code
        model.bhxh_agency = company.bhxh_agency
        model.authorized_capital = company.authorized_capital
        model.phone = company.phone
        model.email = company.email
        model.website = company.website
        model.short_name = company.short_name
        model.bank_accounts = [vars(b) for b in company.bank_accounts]
        model.updated_by = actor
        model.config_version = company.config_version + 1
        model.updated_at = date.today()  # noqa: DTZ011 — SQLite date column, no timezone needed

        self._session.commit()
        company.config_version = model.config_version
        return company

    def deactivate(self, company_id: UUID, actor: UUID) -> Company:
        model = self._session.get(CompanyModel, company_id)
        if model is None:
            raise ValueError(f"Company {company_id} not found")

        model.status = CompanyStatus.SUSPENDED.value
        model.is_active = False
        model.updated_by = actor
        model.config_version += 1
        model.updated_at = date.today()  # noqa: DTZ011 — SQLite date column, no timezone needed

        self._session.commit()
        return self._to_domain(model)

    def list_subsidiaries(self, parent_id: UUID) -> list[Company]:
        # Placeholder — will be implemented when parent_company_id is added
        return []

    def _to_domain(self, model: CompanyModel) -> Company:
        """Convert CompanyModel to Company domain entity."""
        bank_accounts = []
        if model.bank_accounts:
            for ba_data in model.bank_accounts:
                bank_accounts.append(
                    BankAccount(
                        bank_name=ba_data.get("bank_name", ""),
                        account_number=ba_data.get("account_number", ""),
                        account_holder=ba_data.get("account_holder", ""),
                        branch=ba_data.get("branch", ""),
                        is_primary=ba_data.get("is_primary", False),
                    )
                )

        return Company(
            id=model.id,
            legal_name=model.legal_name,
            mst=TaxId(model.mst),
            headquarters_address=model.headquarters_address,
            legal_representative=model.legal_representative,
            business_reg_number=model.business_reg_number or "",
            business_reg_date=model.business_reg_date,
            business_fields=model.business_fields if model.business_fields else [],
            company_type=CompanyType(model.company_type),
            accounting_regime=AccountingRegime(model.accounting_regime),
            fiscal_year_start_month=model.fiscal_year_start_month,
            fiscal_year_start_day=model.fiscal_year_start_day,
            responsible_accountant_name=model.responsible_accountant_name,
            responsible_accountant_license=model.responsible_accountant_license or "",
            tax_agency=model.tax_agency,
            controlling_tax_office=model.controlling_tax_office,
            bhxh_code=model.bhxh_code or "",
            bhxh_agency=model.bhxh_agency or "",
            authorized_capital=model.authorized_capital,
            phone=model.phone,
            email=model.email,
            website=model.website,
            short_name=model.short_name or "",
            bank_accounts=bank_accounts,
            status=CompanyStatus(model.status),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            config_version=model.config_version,
            legal_reviewed_at=model.legal_reviewed_at,
            legal_reviewed_by=model.legal_reviewed_by,
            mst_changed_at=model.mst_changed_at,
        )
