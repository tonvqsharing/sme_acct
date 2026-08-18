"""SQLAlchemy models."""

from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    MetaData,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    metadata = MetaData()


class CompanyTypeEnum(enum.Enum):
    SINGLE_LLC = "single_llc"
    MULTI_LLC = "multi_llc"
    JSC = "jsc"
    LISTED_JSC = "listed_jsc"
    SOLE_PROP = "sole_prop"
    PARTNERSHIP = "partnership"
    HOUSEHOLD = "household"
    COOP = "coop"


class CompanyStatusEnum(enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISSOLVED = "dissolved"


class AccountingRegimeEnum(enum.Enum):
    TT200 = "tt200"
    TT99 = "tt99"
    TT58_MICRO = "tt58_micro"
    TT133 = "tt133"


class CompanyModel(Base):
    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mst: Mapped[str] = mapped_column(String(13), unique=True, nullable=False, index=True)
    headquarters_address: Mapped[str] = mapped_column(String(500), nullable=False)
    legal_representative: Mapped[str] = mapped_column(String(255), nullable=False)
    business_reg_number: Mapped[str] = mapped_column(String(20), nullable=False)
    business_reg_date: Mapped[date] = mapped_column(Date, nullable=False)
    business_fields: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    company_type: Mapped[CompanyTypeEnum] = mapped_column(SQLEnum(CompanyTypeEnum), nullable=False)
    accounting_regime: Mapped[AccountingRegimeEnum] = mapped_column(
        SQLEnum(AccountingRegimeEnum), nullable=False
    )
    fiscal_year_start_month: Mapped[int] = mapped_column(nullable=False, default=1)
    fiscal_year_start_day: Mapped[int] = mapped_column(nullable=False, default=1)
    responsible_accountant_name: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    responsible_accountant_license: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )
    tax_agency: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    controlling_tax_office: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    bhxh_code: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    bhxh_agency: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    authorized_capital: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    phone: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    website: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    short_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    status: Mapped[CompanyStatusEnum] = mapped_column(
        SQLEnum(CompanyStatusEnum), nullable=False, default=CompanyStatusEnum.ACTIVE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    updated_at: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today, onupdate=date.today
    )
    created_by: Mapped[UUID] = mapped_column(nullable=False, default=uuid4)
    updated_by: Mapped[UUID] = mapped_column(nullable=False, default=uuid4)
    config_version: Mapped[int] = mapped_column(nullable=False, default=1)
    legal_reviewed_at: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    legal_reviewed_by: Mapped[UUID | None] = mapped_column(nullable=True, default=None)
    mst_changed_at: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)

    partners: Mapped[list[PartnerModel]] = relationship(back_populates="company", lazy="selectin")
    invoices: Mapped[list[InvoiceModel]] = relationship(back_populates="company", lazy="selectin")
    vouchers: Mapped[list[VoucherModel]] = relationship(back_populates="company", lazy="selectin")
    bank_account_models: Mapped[list[BankAccountModel]] = relationship(
        back_populates="company", lazy="selectin", cascade="all, delete-orphan"
    )

    __table_args__ = ({"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},)


class EntityTypeEnum(enum.Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    EMPLOYEE = "employee"


class InvoiceTypeEnum(enum.Enum):
    SALES_INVOICE = "sales_invoice"
    PURCHASE_INVOICE = "purchase_invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"


class InvoiceStatusEnum(enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    SIGNED = "signed"
    SENT_TO_CUSTOMER = "sent_to_customer"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    REPLACED = "replaced"


class DocumentTypeEnum(enum.Enum):
    RECEIPT = "receipt"
    PAYMENT = "payment"
    JOURNAL_ENTRY = "journal_entry"
    TRANSFER_SLIP = "transfer_slip"


class VoucherStatusEnum(enum.Enum):
    DRAFT = "draft"
    POSTED = "posted"
    LOCKED = "locked"


class PartnerModel(Base):
    __tablename__ = "partners"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    entity_type: Mapped[EntityTypeEnum] = mapped_column(SQLEnum(EntityTypeEnum), nullable=False)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    tax_agency: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    updated_at: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today, onupdate=date.today
    )

    company: Mapped[CompanyModel] = relationship(back_populates="partners", lazy="selectin")
    invoices: Mapped[list[InvoiceModel]] = relationship(back_populates="partner", lazy="selectin")


class InvoiceModel(Base):
    __tablename__ = "invoices"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    serial: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    invoice_type: Mapped[InvoiceTypeEnum] = mapped_column(SQLEnum(InvoiceTypeEnum), nullable=False)
    status: Mapped[InvoiceStatusEnum] = mapped_column(
        SQLEnum(InvoiceStatusEnum), nullable=False, default=InvoiceStatusEnum.DRAFT
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    partner_id: Mapped[UUID | None] = mapped_column(ForeignKey("partners.id"), nullable=True)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_tax_id: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="VND")
    exchange_rate: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=1.0)
    subtotal: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    vat_total: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    grand_total: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    notes: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    replaced_by_id: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    updated_at: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today, onupdate=date.today
    )

    partner: Mapped[PartnerModel | None] = relationship(back_populates="invoices")
    company: Mapped[CompanyModel] = relationship(back_populates="invoices", lazy="selectin")
    items: Mapped[list[InvoiceItemModel]] = relationship(back_populates="invoice", lazy="selectin")


class InvoiceItemModel(Base):
    __tablename__ = "invoice_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="Cái")
    quantity: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    vat_rate: Mapped[int] = mapped_column(nullable=False, default=10)
    vat_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    line_total: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)

    invoice: Mapped[InvoiceModel] = relationship(back_populates="items")


class VoucherModel(Base):
    __tablename__ = "vouchers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    voucher_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    voucher_type: Mapped[DocumentTypeEnum] = mapped_column(
        SQLEnum(DocumentTypeEnum), nullable=False
    )
    status: Mapped[VoucherStatusEnum] = mapped_column(
        SQLEnum(VoucherStatusEnum), nullable=False, default=VoucherStatusEnum.DRAFT
    )
    voucher_date: Mapped[date] = mapped_column(Date, nullable=False)
    accounting_date: Mapped[date] = mapped_column(Date, nullable=False)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    notes: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    created_by_id: Mapped[UUID | None] = mapped_column(nullable=True)
    approved_by_id: Mapped[UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    updated_at: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today, onupdate=date.today
    )

    company: Mapped[CompanyModel] = relationship(back_populates="vouchers", lazy="selectin")
    lines: Mapped[list[VoucherLineModel]] = relationship(back_populates="voucher", lazy="selectin")


class VoucherLineModel(Base):
    __tablename__ = "voucher_lines"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    voucher_id: Mapped[UUID] = mapped_column(ForeignKey("vouchers.id"), nullable=False)
    account_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    debit: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    credit: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    cost_center: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    department: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    voucher: Mapped[VoucherModel] = relationship(back_populates="lines")


class BankAccountModel(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    account_holder: Mapped[str] = mapped_column(String(255), nullable=False)
    branch: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    company: Mapped[CompanyModel] = relationship(
        back_populates="bank_account_models", lazy="selectin"
    )


class FlagTypeEnum(enum.Enum):
    LAW = "law"
    CONFIG = "config"


class FlagScopeEnum(enum.Enum):
    COMPANY = "company"
    SYSTEM = "system"


class UserRoleEnum(enum.Enum):
    ACCOUNTANT = "accountant"
    CHIEF_ACCOUNTANT = "chief_accountant"
    ADMIN = "admin"
    AUDITOR = "auditor"
    DIRECTOR = "director"


class PeriodLockModel(Base):
    __tablename__ = "period_locks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    locked_at: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    locked_by_id: Mapped[UUID | None] = mapped_column(nullable=True, default=None)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)


class SystemAuditLogModel(Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=True)
    action: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # CREATE | UPDATE | DELETE | APPROVE | REJECT | SUSPEND | REACTIVATE | DISSOLVE
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    before_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    after_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    actor_id: Mapped[UUID] = mapped_column(nullable=False, default=uuid4)
    actor_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)  # Client IP (IPv4/IPv6)
    actor_user_agent: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Browser/APP version
    checksum: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # SHA-256 hash for integrity chain
    destroyed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # NULL = active, set when destroyed
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )


class EInvoiceSeriesModel(Base):
    __tablename__ = "e_invoice_series"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    series_prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    next_sequence: Mapped[int] = mapped_column(nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ca_signer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)


class CAListEntryModel(Base):
    __tablename__ = "ca_list_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ca_identifier: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    ca_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    cert_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expired_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # hashed
    role: Mapped[UserRoleEnum] = mapped_column(
        SQLEnum(UserRoleEnum), nullable=False, default=UserRoleEnum.ACCOUNTANT
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )
    created_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class RateTypeEnum(enum.Enum):
    BUY = "buy"
    SELL = "sell"
    TRANSFER = "transfer"
    CENTRAL = "central"
    BOOKING = "booking"


class RevaluationStatusEnum(enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    REVERSED = "reversed"


class PostingSideEnum(enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class CurrencyModel(Base):
    """Đơn vị tiền tệ (ISO 4217) — specs-currencies.md §2.1."""

    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    decimal_places: Mapped[int] = mapped_column(nullable=False, default=2)
    is_base: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_format: Mapped[str] = mapped_column(
        String(100), nullable=False, default="{symbol} {amount:,.2f}"
    )


class ExchangeRateModel(Base):
    """Tỷ giá quy đổi ra VND — specs §2.2. Lịch sử bất biến (D3)."""

    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint(
            "currency_code", "rate_date", "rate_type", name="uq_exchange_rate_currency_date_type"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    currency_code: Mapped[str] = mapped_column(
        ForeignKey("currencies.code"), nullable=False, index=True
    )
    rate_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    rate_type: Mapped[RateTypeEnum] = mapped_column(
        SQLEnum(RateTypeEnum), nullable=False, index=True
    )
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


class RevaluationRunModel(Base):
    """Đợt đánh giá lại cuối kỳ — specs §2.5."""

    __tablename__ = "revaluation_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[RevaluationStatusEnum] = mapped_column(
        SQLEnum(RevaluationStatusEnum), nullable=False, default=RevaluationStatusEnum.DRAFT
    )
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    approver_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    entries: Mapped[list[RevaluationEntryModel]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class RevaluationEntryModel(Base):
    """Khoản mục tiền tệ trong đợt đánh giá lại."""

    __tablename__ = "revaluation_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("revaluation_runs.id"), nullable=False, index=True
    )
    account_code: Mapped[str] = mapped_column(String(10), nullable=False)
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"), nullable=False)
    balance_original: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    rate_applied: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    old_vnd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    new_vnd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    difference: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    posting_side: Mapped[PostingSideEnum | None] = mapped_column(
        SQLEnum(PostingSideEnum), nullable=True
    )

    run: Mapped[RevaluationRunModel] = relationship(back_populates="entries")


class FXDifferenceModel(Base):
    """Dòng báo cáo chênh lệch tỷ giá — specs §5."""

    __tablename__ = "fx_differences"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    account_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    currency_code: Mapped[str] = mapped_column(
        ForeignKey("currencies.code"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    opening_original: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    opening_vnd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    movements_original: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    movements_vnd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    closing_original: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    closing_vnd: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    revaluation_adjustment: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0
    )
    cumulative_difference: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=0
    )
