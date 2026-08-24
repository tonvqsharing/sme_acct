"""Payment Terms & Document Numbering storage layer.

SQLAlchemy models + repository adapters implementing contract ports.
Only file with SQLAlchemy imports in the brick.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.bricks.payment_terms.contract import (
    DocumentNumberingSeriesRepositoryPort,
    PaymentTermRepositoryPort,
)
from src.bricks.payment_terms.domain import (
    DocumentNumberingSeries,
    PaymentTerm,
    PaymentTermStatus,
    SeriesStatus,
)

# ─── Base ────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Brick-local metadata — no coupling to other bricks' tables."""


# ─── Models ──────────────────────────────────────────────────────────────


class PaymentTermModel(Base):
    """payment_terms table per spec §2.1."""

    __tablename__ = "payment_terms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # Plain indexed column, NOT a ForeignKey — cross-brick boundary rule.
    company_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    due_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False, default=Decimal(0)
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_at: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (UniqueConstraint("company_id", "name", name="uq_payment_term_company_name"),)


class DocumentNumberingSeriesModel(Base):
    """document_numbering_series table per spec §2.2."""

    __tablename__ = "document_numbering_series"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    next_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_sequences: Mapped[int] = mapped_column(Integer, nullable=False, default=999999)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_at: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (UniqueConstraint("company_id", "prefix", name="uq_series_company_prefix"),)


# ─── Adapters ────────────────────────────────────────────────────────────


class SQLAlchemyPaymentTermRepository(PaymentTermRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: PaymentTermModel) -> PaymentTerm:
        return PaymentTerm(
            id=UUID(model.id),
            company_id=UUID(model.company_id),
            name=model.name,
            due_days=model.due_days,
            interest_rate=model.interest_rate,
            is_default=model.is_default,
            status=PaymentTermStatus(model.status),
            created_at=model.created_at,
            checksum=model.checksum,
        )

    def get_by_id(self, payment_term_id: UUID) -> PaymentTerm | None:
        model = self._session.get(PaymentTermModel, str(payment_term_id))
        return self._to_domain(model) if model else None

    def get_by_company(self, company_id: UUID) -> list[PaymentTerm]:
        rows = (
            self._session.query(PaymentTermModel)
            .filter(PaymentTermModel.company_id == str(company_id))
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def get_default_by_company(self, company_id: UUID) -> PaymentTerm | None:
        row = (
            self._session.query(PaymentTermModel)
            .filter(
                PaymentTermModel.company_id == str(company_id),
                PaymentTermModel.is_default.is_(True),
            )
            .first()
        )
        return self._to_domain(row) if row else None

    def create(self, term: PaymentTerm) -> PaymentTerm:
        model = PaymentTermModel(
            id=str(term.id),
            company_id=str(term.company_id),
            name=term.name,
            due_days=term.due_days,
            interest_rate=term.interest_rate,
            is_default=term.is_default,
            status=term.status.value,
            checksum=term.checksum,
            created_at=term.created_at,
        )
        self._session.add(model)
        self._session.commit()
        return term

    def update(self, term: PaymentTerm) -> PaymentTerm:
        model = self._session.get(PaymentTermModel, str(term.id))
        if model is None:
            raise ValueError(f"PaymentTerm {term.id} not found")
        model.name = term.name
        model.due_days = term.due_days
        model.interest_rate = term.interest_rate
        model.is_default = term.is_default
        model.status = term.status.value
        model.checksum = term.checksum
        self._session.commit()
        return term

    def set_default(self, payment_term_id: UUID, actor: UUID, reason: str) -> PaymentTerm | None:
        target = self._session.get(PaymentTermModel, str(payment_term_id))
        if target is None:
            return None
        # R-001: clear all siblings in same company, then flag target.
        siblings = (
            self._session.query(PaymentTermModel)
            .filter(
                PaymentTermModel.company_id == target.company_id,
                PaymentTermModel.is_default.is_(True),
            )
            .all()
        )
        for sibling in siblings:
            sibling.is_default = False
        target.is_default = True
        self._session.commit()
        return self._to_domain(target)

    def soft_delete(self, payment_term_id: UUID, actor: UUID, reason: str) -> None:
        model = self._session.get(PaymentTermModel, str(payment_term_id))
        if model is not None:
            model.status = PaymentTermStatus.INACTIVE.value
            self._session.commit()

    def validate_name_unique(self, company_id: UUID, name: str) -> bool:
        exists = (
            self._session.query(PaymentTermModel.id)
            .filter(
                PaymentTermModel.company_id == str(company_id),
                PaymentTermModel.name == name,
            )
            .first()
        )
        return exists is None


class SQLAlchemyDocumentNumberingSeriesRepository(DocumentNumberingSeriesRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: DocumentNumberingSeriesModel) -> DocumentNumberingSeries:
        return DocumentNumberingSeries(
            id=UUID(model.id),
            company_id=UUID(model.company_id),
            prefix=model.prefix,
            next_sequence=model.next_sequence,
            is_active=model.is_active,
            max_sequences=model.max_sequences,
            status=SeriesStatus(model.status),
            created_at=model.created_at,
            checksum=model.checksum,
        )

    def get_by_id(self, series_id: UUID) -> DocumentNumberingSeries | None:
        model = self._session.get(DocumentNumberingSeriesModel, str(series_id))
        return self._to_domain(model) if model else None

    def get_by_company(self, company_id: UUID) -> list[DocumentNumberingSeries]:
        rows = (
            self._session.query(DocumentNumberingSeriesModel)
            .filter(DocumentNumberingSeriesModel.company_id == str(company_id))
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def get_active_by_company(self, company_id: UUID) -> list[DocumentNumberingSeries]:
        rows = (
            self._session.query(DocumentNumberingSeriesModel)
            .filter(
                DocumentNumberingSeriesModel.company_id == str(company_id),
                DocumentNumberingSeriesModel.is_active.is_(True),
            )
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def create(self, series: DocumentNumberingSeries) -> DocumentNumberingSeries:
        model = DocumentNumberingSeriesModel(
            id=str(series.id),
            company_id=str(series.company_id),
            prefix=series.prefix,
            next_sequence=series.next_sequence,
            is_active=series.is_active,
            max_sequences=series.max_sequences,
            status=series.status.value,
            checksum=series.checksum,
            created_at=series.created_at,
        )
        self._session.add(model)
        self._session.commit()
        return series

    def update(self, series: DocumentNumberingSeries) -> DocumentNumberingSeries:
        model = self._session.get(DocumentNumberingSeriesModel, str(series.id))
        if model is None:
            raise ValueError(f"Series {series.id} not found")
        model.prefix = series.prefix
        model.next_sequence = series.next_sequence
        model.is_active = series.is_active
        model.max_sequences = series.max_sequences
        model.status = series.status.value
        model.checksum = series.checksum
        self._session.commit()
        return series

    def activate(self, series_id: UUID, actor: UUID, reason: str) -> DocumentNumberingSeries | None:
        model = self._session.get(DocumentNumberingSeriesModel, str(series_id))
        if model is None:
            return None
        model.is_active = True
        model.status = SeriesStatus.ACTIVE.value
        self._session.commit()
        return self._to_domain(model)

    def deactivate(
        self, series_id: UUID, actor: UUID, reason: str
    ) -> DocumentNumberingSeries | None:
        model = self._session.get(DocumentNumberingSeriesModel, str(series_id))
        if model is None:
            return None
        model.is_active = False
        model.status = SeriesStatus.INACTIVE.value
        self._session.commit()
        return self._to_domain(model)

    def validate_prefix_unique(self, company_id: UUID, prefix: str) -> bool:
        exists = (
            self._session.query(DocumentNumberingSeriesModel.id)
            .filter(
                DocumentNumberingSeriesModel.company_id == str(company_id),
                DocumentNumberingSeriesModel.prefix == prefix,
            )
            .first()
        )
        return exists is None

    def check_max_series_limit(self, company_id: UUID) -> bool:
        count = (
            self._session.query(DocumentNumberingSeriesModel)
            .filter(
                DocumentNumberingSeriesModel.company_id == str(company_id),
                DocumentNumberingSeriesModel.is_active.is_(True),
            )
            .count()
        )
        return count >= 15  # R-008
