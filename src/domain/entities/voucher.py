"""Chứng từ kế toán: phiếu thu, phiếu chi, bút toán, ủy nhiệm chi."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from src.domain.entities.base import AccountCode, DocumentType, VoucherStatus


class VoucherLine:
    """Dòng chứng từ: debit / credit."""

    __slots__ = ("account_code", "description", "debit", "credit", "cost_center", "department")

    def __init__(
        self,
        account_code: AccountCode | str,
        description: str = "",
        debit: float = 0.0,
        credit: float = 0.0,
        cost_center: str = "",
        department: str = "",
    ) -> None:
        self.account_code = (
            AccountCode(account_code) if isinstance(account_code, str) else account_code
        )
        self.description = description.strip()
        self.debit = round(debit, 2)
        self.credit = round(credit, 2)
        self.cost_center = cost_center.strip()
        self.department = department.strip()

    def is_balanced(self) -> bool:
        return self.debit + self.credit > 0 and abs(self.debit - self.credit) > 0


class Voucher:
    """Chứng từ kế toán cơ sở."""

    __slots__ = (
        "id",
        "voucher_number",
        "voucher_type",
        "status",
        "voucher_date",
        "accounting_date",
        "lines",
        "created_by",
        "approved_by",
        "notes",
        "is_imported",
        "created_at",
        "updated_at",
    )

    def __init__(
        self,
        voucher_number: str,
        voucher_type: DocumentType,
        voucher_date: date | None = None,
        accounting_date: date | None = None,
        notes: str = "",
    ) -> None:
        from uuid import uuid4

        self.id: UUID = uuid4()
        self.voucher_number = voucher_number.strip()
        self.voucher_type = voucher_type
        self.status = VoucherStatus.DRAFT
        self.voucher_date = voucher_date or date.today()
        self.accounting_date = accounting_date or date.today()
        self.lines: list[VoucherLine] = []
        self.created_by: UUID | None = None
        self.approved_by: UUID | None = None
        self.notes = notes.strip()
        self.is_imported: bool = False
        self.created_at: date = date.today()
        self.updated_at: date = date.today()

    def add_line(self, line: VoucherLine) -> None:
        self.lines.append(line)
        self.updated_at = date.today()

    def total_debit(self) -> float:
        return round(sum(l.debit for l in self.lines), 2)

    def total_credit(self) -> float:
        return round(sum(l.credit for l in self.lines), 2)

    def is_balanced(self) -> bool:
        return abs(self.total_debit() - self.total_credit()) < 0.01

    def post(self, approved_by: UUID) -> None:
        if not self.is_balanced():
            raise ValueError(
                f"Chứng từ không cân bằng: Nợ={self.total_debit()}, Có={self.total_credit()}"
            )
        if self.status != VoucherStatus.DRAFT:
            raise ValueError(f"Không thể đăng chứng từ ở trạng thái {self.status.value}")
        self.status = VoucherStatus.POSTED
        self.approved_by = approved_by
        self.updated_at = date.today()

    def lock(self) -> None:
        if self.status != VoucherStatus.POSTED:
            raise ValueError("Chỉ khóa được chứng từ đã đăng sổ")
        self.status = VoucherStatus.LOCKED
        self.updated_at = date.today()

    def __repr__(self) -> str:
        return f"Voucher({self.voucher_number!r}, {self.voucher_type.value}, {self.status.value})"
