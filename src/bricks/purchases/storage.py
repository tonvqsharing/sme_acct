"""Purchases storage adapter — supplier_invoices table."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON

from src.bricks.purchases.contract import SupplierInvoiceRepositoryPort
from src.bricks.purchases.domain import (
    NON_CASH_THRESHOLD,
    PaymentMethod,
    PurchaseStatus,
    SupplierInvoice,
    SupplierLine,
)


class Base(DeclarativeBase):
    pass


class SupplierInvoiceModel(Base):
    __tablename__ = "supplier_invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), index=True)
    supplier_name: Mapped[str] = mapped_column(String(255))
    supplier_mst: Mapped[str] = mapped_column(String(14), index=True)
    invoice_number: Mapped[str] = mapped_column(String(30))
    invoice_symbol: Mapped[str] = mapped_column(String(30))
    invoice_date: Mapped[date] = mapped_column(Date)
    entry_date: Mapped[date] = mapped_column(Date)
    lines: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    vat_deductible: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    vat_non_deductible: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total_payment: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    payment_method: Mapped[str] = mapped_column(String(10), default="none")
    payment_proof: Mapped[bool] = mapped_column(Boolean, default=False)
    non_cash_threshold: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=5000000)
    deductibility: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(12), default="DRAFT")
    checksum: Mapped[str] = mapped_column(String(64), default="")


def _to_domain(m: SupplierInvoiceModel) -> SupplierInvoice:
    return SupplierInvoice(
        id=UUID(m.id),
        company_id=UUID(m.company_id),
        supplier_name=m.supplier_name,
        supplier_mst=m.supplier_mst,
        invoice_number=m.invoice_number,
        invoice_symbol=m.invoice_symbol,
        invoice_date=m.invoice_date,
        entry_date=m.entry_date,
        lines=[
            SupplierLine(
                expense_account=l["expense_account"],
                description=l.get("description", ""),
                amount_pre_vat=Decimal(l["amount_pre_vat"]),
                vat_rate=Decimal(l["vat_rate"]),
                deductible=bool(l.get("deductible", True)),
            )
            for l in m.lines
        ],
        payment_method=PaymentMethod(m.payment_method),
        payment_proof=bool(m.payment_proof),
        non_cash_threshold=(
            Decimal(m.non_cash_threshold)
            if m.non_cash_threshold is not None
            else NON_CASH_THRESHOLD
        ),
        status=PurchaseStatus(m.status),
    )


class SQLAlchemySupplierInvoiceRepository(SupplierInvoiceRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, inv: SupplierInvoice) -> SupplierInvoice:
        self._session.add(
            SupplierInvoiceModel(
                id=str(inv.id),
                company_id=str(inv.company_id),
                supplier_name=inv.supplier_name,
                supplier_mst=inv.supplier_mst,
                invoice_number=inv.invoice_number,
                invoice_symbol=inv.invoice_symbol,
                invoice_date=inv.invoice_date,
                entry_date=inv.entry_date,
                lines=self._lines_json(inv),
                subtotal=inv.subtotal,
                vat_deductible=inv.vat_deductible,
                vat_non_deductible=inv.vat_non_deductible,
                total_payment=inv.total_payment,
                payment_method=inv.payment_method.value,
                payment_proof=inv.payment_proof,
                non_cash_threshold=inv.non_cash_threshold,
                deductibility=inv.deductibility.value,
                status=inv.status.value,
                checksum=inv.checksum,
            )
        )
        self._session.commit()
        return inv

    @staticmethod
    def _lines_json(inv: SupplierInvoice) -> list[dict[str, str]]:
        return [
            {
                "expense_account": l.expense_account,
                "description": l.description,
                "amount_pre_vat": str(l.amount_pre_vat),
                "vat_rate": str(l.vat_rate),
                "deductible": str(l.deductible),
            }
            for l in inv.lines
        ]

    def get_by_id(self, iid: UUID) -> SupplierInvoice | None:
        m = self._session.get(SupplierInvoiceModel, str(iid))
        return _to_domain(m) if m else None

    def get_by_company(self, cid: UUID) -> list[SupplierInvoice]:
        rows = (
            self._session.query(SupplierInvoiceModel)
            .filter(SupplierInvoiceModel.company_id == str(cid))
            .order_by(SupplierInvoiceModel.entry_date.desc())
            .all()
        )
        return [_to_domain(r) for r in rows]

    def update(self, inv: SupplierInvoice) -> SupplierInvoice:
        m = self._session.get(SupplierInvoiceModel, str(inv.id))
        if m is None:
            raise ValueError("not found")
        m.status = inv.status.value
        m.checksum = inv.checksum
        self._session.commit()
        return inv

    def get_posted_between(self, cid: UUID, start: date, end: date) -> list[SupplierInvoice]:
        """POSTED invoices whose entry_date falls in [start, end]."""
        rows = (
            self._session.query(SupplierInvoiceModel)
            .filter(
                SupplierInvoiceModel.company_id == str(cid),
                SupplierInvoiceModel.status == PurchaseStatus.POSTED.value,
                SupplierInvoiceModel.entry_date >= start,
                SupplierInvoiceModel.entry_date <= end,
            )
            .order_by(SupplierInvoiceModel.entry_date.asc())
            .all()
        )
        return [_to_domain(r) for r in rows]

    def exists_duplicate(self, cid: UUID, mst: str, number: str, symbol: str) -> bool:
        row = (
            self._session.query(SupplierInvoiceModel.id)
            .filter(
                SupplierInvoiceModel.company_id == str(cid),
                SupplierInvoiceModel.supplier_mst == mst,
                SupplierInvoiceModel.invoice_number == number,
                SupplierInvoiceModel.invoice_symbol == symbol,
            )
            .first()
        )
        return row is not None
