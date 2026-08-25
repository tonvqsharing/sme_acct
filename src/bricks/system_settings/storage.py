"""System settings storage — one config row per company, series as JSON."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal  # noqa: F401
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String
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
        self._session.commit()
        return cfg
