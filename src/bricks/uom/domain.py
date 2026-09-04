"""UOM domain — pure Python. Hộp→Cái convert, Tryton UOM parity."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64


@dataclass
class UOM:
    company_id: UUID
    code: str
    name: str
    factor: Decimal = Decimal(1)  # how many base units = 1 of this UOM
    base_uom_id: UUID | None = None
    active: bool = True
    id: UUID = field(default_factory=uuid4)
    checksum: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code required")
        if not self.name.strip():
            raise ValueError("name required")
        if self.factor <= 0:
            raise ValueError("factor must be >0")
        if self.base_uom_id is not None and self.base_uom_id == self.id:
            raise ValueError("base cycle: self reference")

    def compute_checksum(self, prev: str, actor: UUID, action: str) -> str:
        payload = f"{prev}{self.id}{actor}{action}{self.code}{self.factor}"
        return hashlib.sha256(payload.encode()).hexdigest()
