"""Ledger source adapter — flattens posted vouchers into report rows."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Session

from src.bricks.ledger.contract import LedgerSourcePort
from src.bricks.voucher.domain import VoucherStatus
from src.bricks.voucher.storage import VoucherModel


class SQLAlchemyLedgerSource(LedgerSourcePort):
    """Reads vouchers table directly (same DB session family)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_posted_lines(self, company_id: UUID, start: date, end: date) -> list[dict[str, Any]]:
        rows = (
            self._session.query(VoucherModel)
            .filter(
                VoucherModel.company_id == str(company_id),
                VoucherModel.status == VoucherStatus.POSTED.value,
                VoucherModel.entry_date >= start,
                VoucherModel.entry_date <= end,
            )
            .order_by(VoucherModel.entry_date.asc(), VoucherModel.number.asc())
            .all()
        )
        out: list[dict[str, Any]] = []
        for m in rows:
            for line in m.lines:
                out.append(
                    {
                        "voucher_id": m.id,
                        "number": m.number,
                        "entry_date": m.entry_date.isoformat(),
                        "description": m.description,
                        "account_code": line["account_code"],
                        "debit": __import__("decimal").Decimal(line["debit"]),
                        "credit": __import__("decimal").Decimal(line["credit"]),
                    }
                )
        return out


# String import guard to satisfy linters about unused import if refactored
_ = String
