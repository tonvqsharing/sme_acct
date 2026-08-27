"""Cost centers domain. Pure Python. Per docs/cost-centers-dimensions/specs §1."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

CODE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,9}$")
GENESIS_CHECKSUM = "0" * 64


class CostCenterStatus(Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    CLOSED = "Closed"


@dataclass
class CostCenter:
    company_id: UUID
    code: str
    name: str
    status: CostCenterStatus = CostCenterStatus.ACTIVE
    parent_id: UUID | None = None
    description: str | None = None
    created_by: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    audit_checksum: str = ""

    def __post_init__(self) -> None:
        if not CODE_RE.match(self.code or ""):
            raise ValueError(f"code must match {CODE_RE.pattern}, got '{self.code}'")
        if not self.name.strip():
            raise ValueError("name is required")

    @property
    def is_active(self) -> bool:
        return self.status == CostCenterStatus.ACTIVE

    @property
    def can_modify(self) -> bool:
        return self.status == CostCenterStatus.ACTIVE

    def compute_checksum(self, prev: str, actor: UUID, action: str, reason: str) -> str:
        payload = f"{prev}{self.id}{actor}{action}{reason}"
        return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Dimension entities — per specs §1.1.2, §1.3.2, §1.3.3
# ---------------------------------------------------------------------------

DIMENSION_CODE_RE = re.compile(r"^[A-Z0-9-]{2,50}$")


class DimensionType(str, Enum):
    PROJECT = "Project"
    LOCATION = "Location"
    PRODUCT = "Product"
    CUSTOMER = "Customer"
    EMPLOYEE = "Employee"
    DEPARTMENT = "Department"
    CUSTOM = "Custom"


class DimensionValueStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


@dataclass
class Dimension:
    company_id: UUID
    code: str
    name: str
    type: DimensionType
    is_system: bool = False
    description: str | None = None
    created_by: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    audit_checksum: str = ""

    def __post_init__(self) -> None:
        if not DIMENSION_CODE_RE.match(self.code or ""):
            raise ValueError(f"code must match {DIMENSION_CODE_RE.pattern}, got '{self.code}'")
        if not self.name.strip():
            raise ValueError("name is required")

    @property
    def can_modify(self) -> bool:
        return not self.is_system

    def compute_checksum(
        self, prev: str, actor: UUID, action: str, reason: str, ts: datetime | None = None
    ) -> str:
        stamp = ts or datetime.now(UTC)
        payload = f"{prev}|{self.id}|{action}|{actor}|{reason}|{stamp.isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class DimensionValue:
    company_id: UUID
    dimension_id: UUID
    code: str
    name: str
    status: DimensionValueStatus = DimensionValueStatus.ACTIVE
    description: str | None = None
    created_by: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    audit_checksum: str = ""

    def __post_init__(self) -> None:
        if not DIMENSION_CODE_RE.match(self.code or ""):
            raise ValueError(f"code must match {DIMENSION_CODE_RE.pattern}, got '{self.code}'")
        if not self.name.strip():
            raise ValueError("name is required")

    @property
    def is_active(self) -> bool:
        return self.status == DimensionValueStatus.ACTIVE

    @property
    def can_modify(self) -> bool:
        return self.status == DimensionValueStatus.ACTIVE

    def compute_checksum(
        self, prev: str, actor: UUID, action: str, reason: str, ts: datetime | None = None
    ) -> str:
        stamp = ts or datetime.now(UTC)
        payload = f"{prev}|{self.id}|{action}|{actor}|{reason}|{stamp.isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()
