"""Voucher storage — SQLAlchemy adapter (lines as JSON)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON

from src.bricks.voucher.domain import JournalLine, Voucher, VoucherStatus


class Base(DeclarativeBase):
    pass


class VoucherModel(Base):
    __tablename__ = "vouchers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    number: Mapped[str] = mapped_column(String(30), index=True)
    entry_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(500))
    lines: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(10), default="DRAFT")
    checksum: Mapped[str] = mapped_column(String(64), default="")


class SQLAlchemyVoucherRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, v: Voucher) -> Voucher:
        payload = {
            "company_id": str(v.company_id),
            "number": v.number,
            "entry_date": v.entry_date,
            "description": v.description,
            "lines": [
                {
                    "account_code": l.account_code,
                    "debit": str(l.debit),
                    "credit": str(l.credit),
                    **(
                        {"bank_account_id": str(l.bank_account_id)}
                        if getattr(l, "bank_account_id", None)
                        else {}
                    ),
                }
                for l in v.lines
            ],
            "status": v.status.value,
            "checksum": v.checksum,
        }
        existing = self._session.get(VoucherModel, str(v.id))
        if existing is None:
            self._session.add(VoucherModel(id=str(v.id), **payload))
        else:
            for k, val in payload.items():
                setattr(existing, k, val)
        self._session.commit()
        return v

    @staticmethod
    def _to_domain(m: VoucherModel) -> Voucher:
        return Voucher(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            number=m.number,
            entry_date=m.entry_date,
            description=m.description,
            lines=[
                JournalLine(
                    account_code=l["account_code"],
                    debit=Decimal(l["debit"]),
                    credit=Decimal(l["credit"]),
                    bank_account_id=(
                        UUID(l["bank_account_id"]) if l.get("bank_account_id") else None
                    ),
                )
                for l in m.lines
            ],
            status=VoucherStatus(m.status),
        )

    def get_by_id(self, vid: UUID) -> Voucher | None:
        m = self._session.get(VoucherModel, str(vid))
        return self._to_domain(m) if m else None

    def get_by_company(self, cid: UUID) -> list[Voucher]:
        rows = (
            self._session.query(VoucherModel)
            .filter(VoucherModel.company_id == str(cid))
            .order_by(VoucherModel.number.asc())
            .all()
        )
        return [self._to_domain(r) for r in rows]
