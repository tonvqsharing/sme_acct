"""Unit tests — Tools & Equipment (CCDC) domain layer.

Tests for domain entities and validation rules.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.tools_equipment.domain import (
    PREPAID_ACCOUNT,
    AllocationStatus,
    CCDCCategory,
    InvalidPriceError,
    InvalidStatusTransitionError,
    InvalidUsefulLifeError,
    ToolEquipment,
    ToolEquipmentAllocation,
    ToolEquipmentStatus,
    ValidationError,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

COMPANY_ID = uuid4()
ACTOR_ID = uuid4()


def _make_ccdc(
    code: str = "LPT-001",
    useful_life_months: int = 12,
    purchase_price: Decimal = Decimal(15000000),
    **overrides: object,
) -> ToolEquipment:
    """Helper to create a CCDC entity with sensible defaults."""
    defaults = {
        "company_id": COMPANY_ID,
        "code": code,
        "name": "Laptop Dell Inspiron 15",
        "category": CCDCCategory.OFFICE_EQUIP,
        "purchase_date": date(2026, 8, 15),
        "purchase_price": purchase_price,
        "useful_life_months": useful_life_months,
        "expense_account_code": "642",
        "salvage_value": Decimal(0),
        "prepaid_account_code": PREPAID_ACCOUNT if useful_life_months > 1 else None,
    }
    defaults.update(overrides)
    return ToolEquipment(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestToolEquipmentValidation:
    """Test domain validation rules."""

    def test_create_valid_ccdc(self) -> None:
        """VR-001/002/003/004/005: Valid CCDC creation."""
        entity = _make_ccdc()
        assert entity.code == "LPT-001"
        assert entity.status == ToolEquipmentStatus.ACTIVE

    def test_code_too_short(self) -> None:
        """VR-001: Code must be 2+ chars."""
        with pytest.raises(ValidationError, match="2,50"):
            _make_ccdc(code="A")

    def test_code_too_long(self) -> None:
        """VR-001: Code max 50 chars."""
        with pytest.raises(ValidationError, match="2,50"):
            _make_ccdc(code="A" * 51)

    def test_code_invalid_chars(self) -> None:
        """VR-001: Code must be uppercase alphanumeric + hyphens."""
        with pytest.raises(ValidationError, match="2,50"):
            _make_ccdc(code="lpt-001")

    def test_price_zero(self) -> None:
        """VR-002: Price must be > 0."""
        with pytest.raises(InvalidPriceError):
            _make_ccdc(purchase_price=Decimal(0))

    def test_price_negative(self) -> None:
        """VR-002: Price must be > 0."""
        with pytest.raises(InvalidPriceError):
            _make_ccdc(purchase_price=Decimal(-1000))

    def test_useful_life_zero(self) -> None:
        """VR-003: Useful life must be 1–36 months."""
        with pytest.raises(InvalidUsefulLifeError):
            _make_ccdc(useful_life_months=0)

    def test_useful_life_over_36(self) -> None:
        """VR-003: Useful life must be 1–36 months."""
        with pytest.raises(InvalidUsefulLifeError):
            _make_ccdc(useful_life_months=37)

    def test_salvage_exceeds_price(self) -> None:
        """VR-004: Salvage value must be < purchase price."""
        with pytest.raises(ValidationError, match="Salvage value"):
            _make_ccdc(
                purchase_price=Decimal(10000000),
                salvage_value=Decimal(10000000),
            )

    def test_invalid_expense_account(self) -> None:
        """VR-005: Expense account must be valid."""
        with pytest.raises(ValidationError, match="Expense account"):
            _make_ccdc(expense_account_code="999")

    def test_multi_period_requires_prepaid(self) -> None:
        """VR-006: Multi-period allocation requires TK 242."""
        with pytest.raises(ValidationError, match="prepaid account"):
            _make_ccdc(
                useful_life_months=12,
                prepaid_account_code=None,
            )

    def test_single_period_no_prepaid(self) -> None:
        """VR-006: Single-period allocation does not need TK 242."""
        entity = _make_ccdc(
            useful_life_months=1,
            prepaid_account_code=None,
        )
        assert entity.prepaid_account_code is None

    def test_single_period_with_prepaid_fails(self) -> None:
        """VR-006: Single-period allocation should not have TK 242."""
        with pytest.raises(ValidationError, match="Single-period"):
            _make_ccdc(
                useful_life_months=1,
                prepaid_account_code=PREPAID_ACCOUNT,
            )


# ---------------------------------------------------------------------------
# Lifecycle tests
# ---------------------------------------------------------------------------


class TestToolEquipmentLifecycle:
    """Test status state machine."""

    def test_deactivate_active(self) -> None:
        """ACTIVE → INACTIVE."""
        entity = _make_ccdc()
        entity.deactivate(ACTOR_ID)
        assert entity.status == ToolEquipmentStatus.INACTIVE

    def test_deactivate_inactive_fails(self) -> None:
        """INACTIVE → INACTIVE (invalid)."""
        entity = _make_ccdc()
        entity.deactivate(ACTOR_ID)
        with pytest.raises(InvalidStatusTransitionError):
            entity.deactivate(ACTOR_ID)

    def test_reactivate_inactive(self) -> None:
        """INACTIVE → ACTIVE."""
        entity = _make_ccdc()
        entity.deactivate(ACTOR_ID)
        entity.reactivate(ACTOR_ID)
        assert entity.status == ToolEquipmentStatus.ACTIVE

    def test_reactivate_active_fails(self) -> None:
        """ACTIVE → ACTIVE (invalid)."""
        entity = _make_ccdc()
        with pytest.raises(InvalidStatusTransitionError):
            entity.reactivate(ACTOR_ID)

    def test_write_off_active(self) -> None:
        """ACTIVE → WRITTEN_OFF."""
        entity = _make_ccdc()
        entity.write_off(ACTOR_ID)
        assert entity.status == ToolEquipmentStatus.WRITTEN_OFF

    def test_write_off_inactive(self) -> None:
        """INACTIVE → WRITTEN_OFF."""
        entity = _make_ccdc()
        entity.deactivate(ACTOR_ID)
        entity.write_off(ACTOR_ID)
        assert entity.status == ToolEquipmentStatus.WRITTEN_OFF

    def test_write_off_already_written(self) -> None:
        """WRITTEN_OFF → WRITTEN_OFF (invalid)."""
        entity = _make_ccdc()
        entity.write_off(ACTOR_ID)
        with pytest.raises(InvalidStatusTransitionError, match="already written"):
            entity.write_off(ACTOR_ID)


# ---------------------------------------------------------------------------
# Computed properties tests
# ---------------------------------------------------------------------------


class TestToolEquipmentComputedProperties:
    """Test computed properties."""

    def test_monthly_allocation(self) -> None:
        """Monthly allocation = (price - salvage) / useful_life_months."""
        entity = _make_ccdc(
            purchase_price=Decimal(15000000),
            useful_life_months=12,
            salvage_value=Decimal(0),
        )
        assert entity.monthly_allocation == Decimal(1250000)

    def test_monthly_allocation_with_salvage(self) -> None:
        """Monthly allocation accounts for salvage value."""
        entity = _make_ccdc(
            purchase_price=Decimal(15000000),
            useful_life_months=12,
            salvage_value=Decimal(3000000),
        )
        assert entity.monthly_allocation == Decimal(1000000)


# ---------------------------------------------------------------------------
# ToolEquipmentAllocation tests
# ---------------------------------------------------------------------------


class TestToolEquipmentAllocation:
    """Test allocation entity validation."""

    def test_create_valid_allocation(self) -> None:
        """Valid allocation creation."""
        alloc = ToolEquipmentAllocation(
            tool_equipment_id=uuid4(),
            period_year=2026,
            period_month=8,
            allocated_amount=Decimal(1250000),
            expense_account_code="642",
        )
        assert alloc.period_month == 8
        assert alloc.status == AllocationStatus.PENDING

    def test_invalid_month(self) -> None:
        """Period month must be 1–12."""
        with pytest.raises(ValidationError, match="1–12"):
            ToolEquipmentAllocation(
                tool_equipment_id=uuid4(),
                period_year=2026,
                period_month=13,
                allocated_amount=Decimal(1000),
                expense_account_code="642",
            )

    def test_negative_amount(self) -> None:
        """Allocated amount must be ≥ 0."""
        with pytest.raises(ValidationError, match="≥ 0"):
            ToolEquipmentAllocation(
                tool_equipment_id=uuid4(),
                period_year=2026,
                period_month=8,
                allocated_amount=Decimal(-1000),
                expense_account_code="642",
            )

    def test_invalid_expense_account(self) -> None:
        """Expense account must be valid."""
        with pytest.raises(ValidationError, match="Expense account"):
            ToolEquipmentAllocation(
                tool_equipment_id=uuid4(),
                period_year=2026,
                period_month=8,
                allocated_amount=Decimal(1000),
                expense_account_code="999",
            )
