"""Fixed Assets domain — per docs/fixed-assets/specs. Pure Python."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64


@dataclass
class FixedAsset:
    """TSCĐ aggregate root per TT99/2025 Phụ lục 2."""

    company_id: UUID
    asset_code: str
    name: str
    category: str  # huu_hinh / tai_chinh / vu_hinh
    original_cost: Decimal
    acquisition_date: date
    useful_life_months: int
    depreciation_account: str
    is_active: bool = True
    accumulated_depreciation: Decimal = field(default_factory=lambda: Decimal(0))
    id: UUID = field(default_factory=uuid4)
    checksum: str = ""

    def __post_init__(self) -> None:
        if self.original_cost <= 0:
            raise ValueError(f"original_cost must be > 0, got {self.original_cost}")
        if self.useful_life_months < 1:
            raise ValueError(f"useful_life_months must be >= 1, got {self.useful_life_months}")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.asset_code.strip():
            raise ValueError("asset_code is required")

    @property
    def monthly_depreciation(self) -> Decimal:
        """Straight-line: NG / useful_life_months."""
        return (self.original_cost / self.useful_life_months).quantize(Decimal(1))

    @property
    def book_value(self) -> Decimal:
        return self.original_cost - self.accumulated_depreciation

    def compute_checksum(self, prev: str, actor: UUID, action: str) -> str:
        payload = f"{prev}{self.id}{actor}{action}{self.accumulated_depreciation}"
        return hashlib.sha256(payload.encode()).hexdigest()
