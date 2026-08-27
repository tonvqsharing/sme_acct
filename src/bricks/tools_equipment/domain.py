"""Domain layer — Tools & Equipment (CCDC) entities.

Pure Python. No Flask/SQLAlchemy imports.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class CCDCCategory(str, Enum):
    """CCDC categories per Vietnamese accounting standards."""

    LABOR_TOOL = "Công cụ lao động"
    OFFICE_EQUIP = "Thiết bị văn phòng"
    MEASURING = "Thiết bị đo lường"
    SAFETY = "Thiết bị an toàn"
    OTHER = "Khác"


class ToolEquipmentStatus(str, Enum):
    """CCDC lifecycle status."""

    ACTIVE = "Active"  # Đang sử dụng
    INACTIVE = "Inactive"  # Ngừng phân bổ tạm thời
    WRITTEN_OFF = "WrittenOff"  # Đã thanh lý


class AllocationStatus(str, Enum):
    """Allocation record status."""

    PENDING = "Pending"
    POSTED = "Posted"


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class ValidationError(Exception):
    """Base validation error."""


class DuplicateCodeError(ValidationError):
    """CCDC code already exists for this company."""


class InvalidPriceError(ValidationError):
    """Purchase price must be > 0."""


class InvalidUsefulLifeError(ValidationError):
    """Useful life must be 1–36 months."""


class InvalidCategoryError(ValidationError):
    """Invalid CCDC category."""


class InvalidStatusTransitionError(ValidationError):
    """Invalid status transition."""


class CodeImmutableError(ValidationError):
    """Cannot modify code after creation."""


# ---------------------------------------------------------------------------
# Domain entities
# ---------------------------------------------------------------------------

# CCDC code pattern: uppercase alphanumeric + hyphens, 2–50 chars
_CODE_RE = re.compile(r"^[A-Z0-9-]{2,50}$")

# Valid expense account codes
VALID_EXPENSE_ACCOUNTS = frozenset({"623", "627", "641", "642"})

# Prepaid account for multi-period allocation
PREPAID_ACCOUNT = "242"


def _validate_code(code: str) -> None:
    if not _CODE_RE.match(code):
        raise ValidationError(f"Code must match ^[A-Z0-9-]{{2,50}}$, got: {code!r}")


def _validate_price(price: Decimal) -> None:
    if price <= 0:
        raise InvalidPriceError(f"Price must be > 0, got: {price}")


def _validate_useful_life(months: int) -> None:
    if not 1 <= months <= 36:
        raise InvalidUsefulLifeError(f"Useful life must be 1–36 months, got: {months}")


def _validate_category(category: CCDCCategory) -> None:
    if not isinstance(category, CCDCCategory):
        raise InvalidCategoryError(f"Invalid category: {category}")


def _validate_expense_account(code: str) -> None:
    if code not in VALID_EXPENSE_ACCOUNTS:
        raise ValidationError(
            f"Expense account must be one of {VALID_EXPENSE_ACCOUNTS}, got: {code!r}"
        )


class ToolEquipment:
    """CCDC entity (Công cụ, Dụng cụ).

    Represents tools and equipment that don't meet fixed asset (TSCĐ)
    recognition criteria per Vietnamese accounting standards (TT99/2025).
    """

    def __init__(
        self,
        company_id: UUID,
        code: str,
        name: str,
        category: CCDCCategory,
        purchase_date: date,
        purchase_price: Decimal,
        useful_life_months: int,
        expense_account_code: str,
        id: UUID | None = None,
        salvage_value: Decimal = Decimal(0),
        prepaid_account_code: str | None = None,
        assigned_to: UUID | None = None,
        cost_center_id: UUID | None = None,
        dimension_value_id: UUID | None = None,
        description: str | None = None,
        status: ToolEquipmentStatus = ToolEquipmentStatus.ACTIVE,
        created_by: UUID | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        audit_checksum: str = "",
    ) -> None:
        # Validate
        _validate_code(code)
        _validate_price(purchase_price)
        _validate_useful_life(useful_life_months)
        _validate_category(category)
        _validate_expense_account(expense_account_code)

        if salvage_value >= purchase_price:
            raise ValidationError(
                f"Salvage value ({salvage_value}) must be < " f"purchase price ({purchase_price})"
            )

        # Multi-period allocation requires TK 242
        if useful_life_months > 1 and prepaid_account_code != PREPAID_ACCOUNT:
            raise ValidationError(
                f"Multi-period allocation requires prepaid account "
                f"{PREPAID_ACCOUNT}, got: {prepaid_account_code!r}"
            )

        # Single-period: no prepaid account needed
        if useful_life_months == 1 and prepaid_account_code is not None:
            raise ValidationError("Single-period allocation does not need prepaid account")

        self.id = id or uuid4()
        self.company_id = company_id
        self.code = code
        self.name = name
        self.category = category
        self.purchase_date = purchase_date
        self.purchase_price = purchase_price
        self.useful_life_months = useful_life_months
        self.salvage_value = salvage_value
        self.expense_account_code = expense_account_code
        self.prepaid_account_code = prepaid_account_code
        self.assigned_to = assigned_to
        self.cost_center_id = cost_center_id
        self.dimension_value_id = dimension_value_id
        self.description = description
        self.status = status
        self.created_by = created_by
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)
        self.audit_checksum = audit_checksum

    # -- Computed properties --------------------------------------------------

    @property
    def monthly_allocation(self) -> Decimal:
        """Monthly allocation amount (直线法)."""
        if self.useful_life_months == 0:
            return Decimal(0)
        return (self.purchase_price - self.salvage_value) / self.useful_life_months

    @property
    def allocated_value(self) -> Decimal:
        """Total value allocated so far (placeholder — needs allocation records)."""
        # This will be computed from allocation records in the service layer
        return Decimal(0)

    @property
    def remaining_value(self) -> Decimal:
        """Remaining value = original - allocated."""
        return self.purchase_price - self.allocated_value

    # -- Status transitions ---------------------------------------------------

    def deactivate(self, actor_id: UUID) -> None:
        """Transition ACTIVE → INACTIVE. Requires CHIEF_ACCOUNTANT."""
        if self.status != ToolEquipmentStatus.ACTIVE:
            raise InvalidStatusTransitionError(
                f"Can only deactivate ACTIVE CCDC, current: {self.status.value}"
            )
        self.status = ToolEquipmentStatus.INACTIVE
        self.updated_at = datetime.now(UTC)

    def reactivate(self, actor_id: UUID) -> None:
        """Transition INACTIVE → ACTIVE. Requires CHIEF_ACCOUNTANT."""
        if self.status != ToolEquipmentStatus.INACTIVE:
            raise InvalidStatusTransitionError(
                f"Can only reactivate INACTIVE CCDC, current: {self.status.value}"
            )
        self.status = ToolEquipmentStatus.ACTIVE
        self.updated_at = datetime.now(UTC)

    def write_off(self, actor_id: UUID) -> None:
        """Transition INACTIVE/ACTIVE → WRITTEN_OFF. Requires CHIEF_ACCOUNTANT."""
        if self.status == ToolEquipmentStatus.WRITTEN_OFF:
            raise InvalidStatusTransitionError("CCDC is already written off")
        self.status = ToolEquipmentStatus.WRITTEN_OFF
        self.updated_at = datetime.now(UTC)

    # -- Checksum -------------------------------------------------------------

    def compute_checksum(self, prev_checksum: str, actor_id: UUID) -> str:
        """Compute audit checksum (pipe-delimited format).

        Format: prev|id|action|actor|timestamp
        """
        stamp = self.updated_at.isoformat()
        payload = f"{prev_checksum}|{self.id}|status_change|{actor_id}|{stamp}"
        # In production, use hashlib.sha256(payload.encode()).hexdigest()
        # For now, return raw payload for testing
        return payload

    def __repr__(self) -> str:
        return f"<ToolEquipment {self.code!r} name={self.name!r} " f"status={self.status.value}>"


class ToolEquipmentAllocation:
    """Monthly allocation record for a CCDC item."""

    def __init__(
        self,
        tool_equipment_id: UUID,
        period_year: int,
        period_month: int,
        allocated_amount: Decimal,
        expense_account_code: str,
        id: UUID | None = None,
        cost_center_id: UUID | None = None,
        dimension_value_id: UUID | None = None,
        voucher_id: UUID | None = None,
        status: AllocationStatus = AllocationStatus.PENDING,
        created_at: datetime | None = None,
    ) -> None:
        if not 1 <= period_month <= 12:
            raise ValidationError(f"Period month must be 1–12, got: {period_month}")
        if allocated_amount < 0:
            raise ValidationError(f"Allocated amount must be ≥ 0, got: {allocated_amount}")
        _validate_expense_account(expense_account_code)

        self.id = id or uuid4()
        self.tool_equipment_id = tool_equipment_id
        self.period_year = period_year
        self.period_month = period_month
        self.allocated_amount = allocated_amount
        self.expense_account_code = expense_account_code
        self.cost_center_id = cost_center_id
        self.dimension_value_id = dimension_value_id
        self.voucher_id = voucher_id
        self.status = status
        self.created_at = created_at or datetime.now(UTC)

    def __repr__(self) -> str:
        return (
            f"<ToolEquipmentAllocation year={self.period_year} "
            f"month={self.period_month} amount={self.allocated_amount}>"
        )
