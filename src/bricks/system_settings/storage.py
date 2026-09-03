"""System settings storage — one config row per company, series as JSON."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON

from src.bricks.system_settings.contract import SystemSettingsRepositoryPort
from src.bricks.system_settings.domain import (
    DEFAULT_VAT_RATES,
    CompanyConfig,
    EInvoiceSeries,
)


class Base(DeclarativeBase):
    pass


def _ser_series(s: EInvoiceSeries) -> dict[str, str]:
    return {
        "id": str(s.id),
        "prefix": s.prefix,
        "next_sequence": str(s.next_sequence),
        "active": str(s.active),
        "ca_signer": s.ca_signer or "",
    }


def _des_series(d: dict[str, str]) -> EInvoiceSeries:
    return EInvoiceSeries(
        id=UUID(d["id"]),
        prefix=d["prefix"],
        next_sequence=int(d["next_sequence"]),
        active=d["active"] == "True",
        ca_signer=d.get("ca_signer") or None,
    )


class SystemSettingsModel(Base):
    __tablename__ = "system_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    vat_rates: Mapped[list[int]] = mapped_column(JSON)
    e_invoice_series: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    config_version: Mapped[int] = mapped_column(Integer, default=0)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    # ── CONFIG flags ──────────────────────────────────────────────────
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1)
    fiscal_year_start_day: Mapped[int] = mapped_column(Integer, default=1)
    vat_settlement_cycle: Mapped[str] = mapped_column(String(20), default="monthly")
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
    default_currency: Mapped[str] = mapped_column(String(3), default="VND")
    cost_center_required: Mapped[bool] = mapped_column(default=False)
    # ── Legal review ──────────────────────────────────────────────────
    legal_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    legal_reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class SQLAlchemySystemSettingsRepository(SystemSettingsRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_config(self, cid: UUID) -> CompanyConfig:
        m = self._get_or_init(cid)
        return self._to_domain(m)

    def _get_or_init(self, cid: UUID) -> SystemSettingsModel:
        m = (
            self._session.query(SystemSettingsModel)
            .filter(SystemSettingsModel.company_id == str(cid))
            .first()
        )
        if m is None:
            m = SystemSettingsModel(
                id=str(uuid4()),
                company_id=str(cid),
                vat_rates=sorted(DEFAULT_VAT_RATES),
                e_invoice_series=[],
                config_version=0,
            )
            self._session.add(m)
            self._session.commit()
        return m

    @staticmethod
    def _to_domain(m: SystemSettingsModel) -> CompanyConfig:
        return CompanyConfig(
            company_id=UUID(m.company_id),
            vat_rates=frozenset(m.vat_rates),
            e_invoice_series=frozenset(_des_series(d) for d in m.e_invoice_series),
            config_version=m.config_version,
            updated_by=UUID(m.updated_by) if m.updated_by else None,
            fiscal_year_start_month=m.fiscal_year_start_month,
            fiscal_year_start_day=m.fiscal_year_start_day,
            vat_settlement_cycle=m.vat_settlement_cycle,
            decimal_places=m.decimal_places,
            default_currency=m.default_currency,
            cost_center_required=m.cost_center_required,
            legal_reviewed_at=m.legal_reviewed_at,
            legal_reviewed_by=UUID(m.legal_reviewed_by) if m.legal_reviewed_by else None,
        )

    def update_config(self, cfg: CompanyConfig) -> CompanyConfig:
        m = self._get_or_init(cfg.company_id)
        m.vat_rates = sorted(cfg.vat_rates)
        m.e_invoice_series = sorted(
            (_ser_series(x) for x in cfg.e_invoice_series),
            key=lambda d: d["prefix"],
        )
        m.config_version = cfg.config_version
        m.updated_by = str(cfg.updated_by) if cfg.updated_by else None
        m.updated_at = datetime.now(UTC)
        m.fiscal_year_start_month = cfg.fiscal_year_start_month
        m.fiscal_year_start_day = cfg.fiscal_year_start_day
        m.vat_settlement_cycle = cfg.vat_settlement_cycle
        m.decimal_places = cfg.decimal_places
        m.default_currency = cfg.default_currency
        m.cost_center_required = cfg.cost_center_required
        m.legal_reviewed_at = cfg.legal_reviewed_at
        m.legal_reviewed_by = str(cfg.legal_reviewed_by) if cfg.legal_reviewed_by else None
        self._session.commit()
        return cfg


class PeriodLockModel(Base):
    """Period lock — prevents posting in closed fiscal periods."""

    __tablename__ = "period_locks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer)
    accounting_period: Mapped[int] = mapped_column(Integer)  # 1-12
    lock_type: Mapped[str] = mapped_column(String(20))  # PERIOD | FYEAR_CLOSED
    locked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    locked_by: Mapped[str] = mapped_column(String(36))
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "company_id", "fiscal_year", "accounting_period", name="uq_period_lock"
        ),
    )


class SQLAlchemyPeriodLockRepository:
    """Repository for period lock operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def is_locked(self, company_id: UUID, fiscal_year: int, period: int) -> bool:
        """Check if a period is locked."""
        m = (
            self._session.query(PeriodLockModel)
            .filter(
                PeriodLockModel.company_id == str(company_id),
                PeriodLockModel.fiscal_year == fiscal_year,
                PeriodLockModel.accounting_period == period,
            )
            .first()
        )
        return m is not None

    def lock(
        self,
        company_id: UUID,
        fiscal_year: int,
        period: int,
        actor: UUID,
        lock_type: str = "PERIOD",
        notes: str | None = None,
    ) -> None:
        """Lock a period."""
        existing = (
            self._session.query(PeriodLockModel)
            .filter(
                PeriodLockModel.company_id == str(company_id),
                PeriodLockModel.fiscal_year == fiscal_year,
                PeriodLockModel.accounting_period == period,
            )
            .first()
        )
        if existing is not None:
            return  # Already locked
        self._session.add(
            PeriodLockModel(
                id=str(uuid4()),
                company_id=str(company_id),
                fiscal_year=fiscal_year,
                accounting_period=period,
                lock_type=lock_type,
                locked_by=str(actor),
                notes=notes,
            )
        )
        self._session.commit()

    def unlock(self, company_id: UUID, fiscal_year: int, period: int) -> bool:
        """Unlock a period. Returns True if was locked."""
        m = (
            self._session.query(PeriodLockModel)
            .filter(
                PeriodLockModel.company_id == str(company_id),
                PeriodLockModel.fiscal_year == fiscal_year,
                PeriodLockModel.accounting_period == period,
            )
            .first()
        )
        if m is None:
            return False
        self._session.delete(m)
        self._session.commit()
        return True

    def list_locked(self, company_id: UUID, fiscal_year: int | None = None) -> list[dict[str, Any]]:
        """List all locked periods for a company."""
        q = self._session.query(PeriodLockModel).filter(
            PeriodLockModel.company_id == str(company_id)
        )
        if fiscal_year is not None:
            q = q.filter(PeriodLockModel.fiscal_year == fiscal_year)
        rows = q.all()
        return [
            {
                "fiscal_year": r.fiscal_year,
                "accounting_period": r.accounting_period,
                "lock_type": r.lock_type,
                "locked_at": r.locked_at.isoformat(),
                "locked_by": r.locked_by,
                "notes": r.notes,
            }
            for r in rows
        ]


class TaxRateWindowModel(Base):
    __tablename__ = "tax_rate_windows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rate_pct: Mapped[int] = mapped_column(Integer)
    fraction: Mapped[str] = mapped_column(String(10))
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    decree_ref: Mapped[str] = mapped_column(String(200))


class VatCarryModel(Base):
    """Persisted VAT carry-forward per company+period (01/GTGT)."""

    __tablename__ = "vat_carry_forwards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    carry_amount: Mapped[Decimal] = mapped_column(sa.Numeric(18, 2), default=Decimal(0))
    __table_args__ = (
        sa.UniqueConstraint("company_id", "year", "month", "quarter", name="uq_vat_carry"),
    )


class SQLAlchemyVatCarryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_carry(
        self, company_id: UUID, year: int, month: int | None, quarter: int | None
    ) -> Decimal:
        m = (
            self._session.query(VatCarryModel)
            .filter(
                VatCarryModel.company_id == str(company_id),
                VatCarryModel.year == year,
                VatCarryModel.month == month,
                VatCarryModel.quarter == quarter,
            )
            .first()
        )
        return Decimal(m.carry_amount) if m else Decimal(0)

    def get_previous_carry(
        self, company_id: UUID, year: int, month: int | None, quarter: int | None
    ) -> Decimal:
        # Monthly: previous month; Quarterly: previous quarter
        if quarter is not None:
            if quarter == 1:
                return self.get_carry(company_id, year - 1, None, 4)
            return self.get_carry(company_id, year, None, quarter - 1)
        if month is not None:
            if month == 1:
                return self.get_carry(company_id, year - 1, 12, None)
            return self.get_carry(company_id, year, month - 1, None)
        return Decimal(0)

    def save_carry(
        self, company_id: UUID, year: int, month: int | None, quarter: int | None, amount: Decimal
    ) -> None:
        m = (
            self._session.query(VatCarryModel)
            .filter(
                VatCarryModel.company_id == str(company_id),
                VatCarryModel.year == year,
                VatCarryModel.month == month,
                VatCarryModel.quarter == quarter,
            )
            .first()
        )
        if m is None:
            m = VatCarryModel(
                company_id=str(company_id),
                year=year,
                month=month,
                quarter=quarter,
                carry_amount=amount,
            )
            self._session.add(m)
        else:
            m.carry_amount = amount
        self._session.commit()


class SQLAlchemyTaxRateWindowRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def all(self) -> list[Any]:
        rows = (
            self._session.query(TaxRateWindowModel)
            .order_by(TaxRateWindowModel.rate_pct.asc())
            .all()
        )
        return [
            __import__(
                "src.bricks.system_settings.rate_windows",
                fromlist=["TaxRateWindow"],
            ).TaxRateWindow(
                rate_pct=r.rate_pct,
                fraction=r.fraction,
                valid_from=r.valid_from,
                valid_to=r.valid_to,
                decree_ref=r.decree_ref,
            )
            for r in rows
        ]

    def add(self, w: Any) -> Any:
        self._session.add(
            TaxRateWindowModel(
                id=str(uuid4()),
                rate_pct=w.rate_pct,
                fraction=w.fraction,
                valid_from=w.valid_from,
                valid_to=w.valid_to,
                decree_ref=w.decree_ref,
            )
        )
        self._session.commit()
        return w

    def remove(self, w: Any) -> Any:
        m = (
            self._session.query(TaxRateWindowModel)
            .filter(
                TaxRateWindowModel.fraction == w.fraction,
                TaxRateWindowModel.decree_ref == w.decree_ref,
            )
            .first()
        )
        if m is not None:
            self._session.delete(m)
            self._session.commit()
        return w

    def count(self) -> int:
        return self._session.query(TaxRateWindowModel).count()
