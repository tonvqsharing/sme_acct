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
    customer_mst: Mapped[str | None] = mapped_column(String(14), nullable=True)
    template_code: Mapped[str] = mapped_column(String(20), default="")
    invoice_symbol: Mapped[str] = mapped_column(String(20), default="")
    currency_code: Mapped[str] = mapped_column(String(3), default="VND")
    fx_rate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    einvoice_status: Mapped[str] = mapped_column(String(20), default="NOT_ISSUED")
    deferred_amount: Mapped[str] = mapped_column(String(20), default="0")
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
            "customer_mst": inv.customer_mst,
            "template_code": inv.template_code,
            "invoice_symbol": inv.invoice_symbol,
            "currency_code": inv.currency_code,
            "fx_rate": str(inv.fx_rate) if inv.fx_rate is not None else None,
            "einvoice_status": inv.einvoice_status.value,
            "deferred_amount": str(inv.deferred_amount),
            "items": [
                {
                    "account_code": i.account_code,
                    "description": i.description,
                    "amount": str(i.amount),
                    "vat_rate": str(i.vat_rate) if i.vat_rate is not None else None,
                    "category": i.category,
                    "quantity": str(i.quantity) if i.quantity is not None else None,
                    "unit_price": str(i.unit_price) if i.unit_price is not None else None,
                    "po_id": i.po_id,
                    "is_agent": i.is_agent,
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
        from src.bricks.invoice.domain import EInvoiceStatus

        def _dec(v: str | None) -> Decimal | None:
            return Decimal(v) if v is not None else None

        return Invoice(
            id=UUID(m.id),
            company_id=UUID(m.company_id),
            number=m.number,
            issue_date=m.issue_date,
            due_date=m.due_date,
            customer_name=m.customer_name,
            customer_mst=getattr(m, "customer_mst", None),
            template_code=getattr(m, "template_code", "") or "",
            invoice_symbol=getattr(m, "invoice_symbol", "") or "",
            currency_code=getattr(m, "currency_code", "VND") or "VND",
            fx_rate=_dec(getattr(m, "fx_rate", None)),
            einvoice_status=EInvoiceStatus(getattr(m, "einvoice_status", "NOT_ISSUED")),
            deferred_amount=Decimal(getattr(m, "deferred_amount", "0") or "0"),
            items=[
                InvoiceItem(
                    account_code=i["account_code"],
                    description=i["description"],
                    amount=Decimal(i["amount"]),
                    vat_rate=Decimal(i["vat_rate"]) if i.get("vat_rate") is not None else None,
                    category=i.get("category"),
                    quantity=Decimal(i["quantity"]) if i.get("quantity") is not None else None,
                    unit_price=(
                        Decimal(i["unit_price"]) if i.get("unit_price") is not None else None
                    ),
                    po_id=i.get("po_id"),
                    is_agent=bool(i.get("is_agent", False)),
                )
                for i in m.items
            ],
            vat_rate=Decimal(m.vat_rate),
            payment_term_id=UUID(m.payment_term_id) if m.payment_term_id else None,
            status=InvoiceStatus(m.status),
            checksum=m.checksum,
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
