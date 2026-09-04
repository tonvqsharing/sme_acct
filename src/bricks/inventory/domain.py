"""Inventory domain — pure Python. VAS 02, TT99/TT58, Tryton 8 parity."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

GENESIS_CHECKSUM = "0" * 64


class CostMethod(Enum):
    SPECIFIC = "specific"
    WAVG = "wavg"  # moving weighted average
    FIFO = "fifo"
    STANDARD = "standard"


class LocationType(Enum):
    WAREHOUSE = "warehouse"
    SHELF = "shelf"
    VIRTUAL = "virtual"


class ShipmentType(Enum):
    SUPPLIER_IN = "supplier_in"  # PN
    CUSTOMER_OUT = "customer_out"  # PX
    INTERNAL = "internal"  # CK


class MoveState(Enum):
    DRAFT = "DRAFT"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class ShipState(Enum):
    DRAFT = "DRAFT"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class PeriodState(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class Product:
    company_id: UUID
    code: str
    name: str
    uom: str
    cost_method: CostMethod
    standard_cost: Decimal | None = None
    id: UUID = field(default_factory=uuid4)
    active: bool = True
    checksum: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code required")
        if not self.name.strip():
            raise ValueError("name required")
        if not self.uom.strip():
            raise ValueError("uom required")
        if self.cost_method == CostMethod.STANDARD and self.standard_cost is None:
            raise ValueError("standard_cost required for STANDARD method")
        if self.standard_cost is not None and self.standard_cost < 0:
            raise ValueError("standard_cost must be >=0")

    def compute_checksum(self, prev: str, actor: UUID, action: str) -> str:
        payload = f"{prev}{self.id}{actor}{action}{self.code}{self.cost_method.value}"
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class Location:
    company_id: UUID
    warehouse_id: UUID | None
    code: str
    name: str
    type: LocationType = LocationType.SHELF
    parent_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code required")
        if not self.name.strip():
            raise ValueError("name required")


@dataclass
class StockMove:
    company_id: UUID
    product_id: UUID
    qty: Decimal  # always positive qty moved; direction via from_loc/to_loc
    unit_cost: Decimal
    from_loc: UUID | None
    to_loc: UUID | None
    effective_date: date
    shipment_id: UUID | None = None
    state: MoveState = MoveState.DRAFT
    id: UUID = field(default_factory=uuid4)
    checksum: str = ""

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise ValueError("qty must be >0")
        if self.unit_cost < 0:
            raise ValueError("unit_cost must be >=0")
        if self.from_loc is None and self.to_loc is None:
            raise ValueError("at least one location required")

    def compute_checksum(self, prev: str, actor: UUID, reason: str) -> str:
        payload = f"{prev}{self.id}{actor}{self.state.value}{self.qty}{self.unit_cost}{reason}"
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class Shipment:
    company_id: UUID
    type: ShipmentType
    number: str
    effective_date: date
    moves: list[UUID] = field(default_factory=list)
    state: ShipState = ShipState.DRAFT
    id: UUID = field(default_factory=uuid4)
    checksum: str = ""

    def compute_checksum(self, prev: str, actor: UUID, reason: str) -> str:
        payload = f"{prev}{self.id}{actor}{self.state.value}{self.number}{reason}"
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class StockPeriod:
    company_id: UUID
    year: int
    month: int
    state: PeriodState = PeriodState.OPEN
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError("month 1-12")


@dataclass
class ProductCategory:
    company_id: UUID
    code: str
    name: str
    parent_id: UUID | None = None
    cost_method: CostMethod | None = None  # default for products in category
    account_code: str | None = None  # 152/156 mapping
    tax_category: str | None = None  # for 8% eligibility
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code required")
        if not self.name.strip():
            raise ValueError("name required")


@dataclass
class Warehouse:
    company_id: UUID
    code: str
    name: str
    address: str | None = None
    manager_id: UUID | None = None
    account_code: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code required")
        if not self.name.strip():
            raise ValueError("name required")
