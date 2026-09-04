"""Party domain — pure Python. Tryton party parity, MST TT99."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64


@dataclass
class Party:
    company_id: UUID
    code: str
    name: str
    mst: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_customer: bool = False
    is_supplier: bool = False
    is_employee: bool = False
    active: bool = True
    id: UUID = field(default_factory=uuid4)
    checksum: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code required")
        if not self.name.strip():
            raise ValueError("name required")
        if not (self.is_customer or self.is_supplier or self.is_employee):
            raise ValueError("at least one role required")

    def compute_checksum(self, prev: str, actor: UUID, action: str) -> str:
        payload = f"{prev}{self.id}{actor}{action}{self.code}{self.mst or ''}"
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class Department:
    company_id: UUID
    code: str
    name: str
    parent_id: UUID | None = None
    manager_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code required")
        if not self.name.strip():
            raise ValueError("name required")
