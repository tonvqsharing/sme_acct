"""Invoice storage — SQLAlchemy adapter (items as JSON rows)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON

from src.bricks.invoice.domain import Invoice, InvoiceItem, InvoiceStatus


class Base(DeclarativeBase):
    pass


class InvoiceModel(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    number: Mapped[str] = mapped_column(String(30), index=True)
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    customer_name: Mapped[str] = mapped_column(String(200))
    items: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    vat_rate: Mapped[str] = mapped_column(String(20))
    payment_term_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="DRAFT")
    checksum: Mapped[str] = mapped_column(String(64), default="")


class SQLAlchemyInvoiceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, inv: Invoice) -> Invoice:
        existing = self._session.get(InvoiceModel, str(inv.id))
        payload = {
            "company_id": str(inv.company_id),
            "number": inv.number,
            "issue_date": inv.issue_date,
            "due_date": inv.due_date,
            "customer_name": inv.customer_name,
            "items": [
                {
                    "account_code": i.account_code,
                    "description": i.description,
                    "amount": str(i.amount),
                }
                for i in inv.items
            ],
            "vat_rate": str(inv.vat_rate),
            "payment_term_id": str(inv.payment_term_id) if inv.payment_term_id else None,
            "status": inv.status.value,
            "checksum": inv.checksum,
        }
        if existing is None:
            self._session.add(InvoiceModel(id=str(inv.id), **payload))
        else:
            for k, v in payload.items():
                setattr(existing, k, v)
        self._session.commit()
        return inv

    @staticmethod
    def _to_domain(m: InvoiceModel) -> Invoice:
        return Invoice(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            number=m.number,
            issue_date=m.issue_date,
            due_date=m.due_date,
            customer_name=m.customer_name,
            items=[
                InvoiceItem(
                    account_code=i["account_code"],
                    description=i["description"],
                    amount=Decimal(i["amount"]),
                )
                for i in m.items
            ],
            vat_rate=Decimal(m.vat_rate),
            payment_term_id=UUID(m.payment_term_id) if m.payment_term_id else None,
            status=InvoiceStatus(m.status),
        )

    def get_by_id(self, iid: UUID) -> Invoice | None:
        m = self._session.get(InvoiceModel, str(iid))
        return self._to_domain(m) if m else None

    def get_by_company(self, cid: UUID) -> list[Invoice]:
        rows = (
            self._session.query(InvoiceModel)
            .filter(InvoiceModel.company_id == str(cid))
            .order_by(InvoiceModel.number.asc())
            .all()
        )
        return [self._to_domain(r) for r in rows]
