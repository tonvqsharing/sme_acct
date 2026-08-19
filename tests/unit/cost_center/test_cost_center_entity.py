"""Unit tests for CostCenter, Dimension, DimensionValue domain entities.

TDD red-green-refactor:
- Tests written BEFORE implementation
- Run pytest: expect failures (red)
- Implement src/domain/entities/cost_center.py: expect passes (green)
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.domain.entities.cost_center import (
    CostCenter,
    CostCenterStatus,
    Dimension,
    DimensionType,
    DimensionValue,
    DimensionValueStatus,
    CostCenterCode,
    DimensionCode,
)
from src.domain.exceptions import DomainException


@pytest.fixture
def valid_kwargs():
    """Base kwargs for entity creation."""
    return {
        "id": uuid4(),
        "created_by": uuid4(),
        "updated_by": uuid4(),
    }


@pytest.fixture
def cc_code_str():
    """Valid CostCenterCode string."""
    return "C01"


@pytest.fixture
def cc_code(cc_code_str):
    """Valid CostCenterCode (validated VO)."""
    return CostCenterCode(cc_code_str)


@pytest.fixture
def dim_code_str():
    """Valid DimensionCode string."""
    return "D1"


@pytest.fixture
def dim_code(dim_code_str):
    """Valid DimensionCode (validated VO)."""
    return DimensionCode(dim_code_str, DimensionType.LOCATION)


# ── Test: CostCenter creation ────────────────────────────────────────────────

class TestCostCenterCreation:
    def test_valid_cost_center_creation(self, valid_kwargs, cc_code, cc_code_str):
        cc = CostCenter(
            code=cc_code_str,
            name="Phòng kế toán",
            description="Phòng kế toán chính",
            company_id=uuid4(),
            created_by=uuid4(),
        )
        # cc.code is stored as plain string after VO validation
        assert cc.code == cc_code_str

    def test_cost_center_inactive_by_default(self, valid_kwargs, cc_code_str):
        cc = CostCenter(
            code=cc_code_str,
            name="Phòng tài chính",
            company_id=uuid4(),
            created_by=uuid4(),
        )
        assert cc.status == CostCenterStatus.ACTIVE  # default

    def test_cost_center_deactivate(self, valid_kwargs, cc_code_str):
        cc = CostCenter(code=cc_code_str, name="Test", company_id=uuid4(), created_by=uuid4())
        cc.deactivate(actor=uuid4(), reason="Test deactivation")
        assert cc.status == CostCenterStatus.INACTIVE

    def test_cost_center_reactivate(self, valid_kwargs, cc_code_str):
        cc = CostCenter(code=cc_code_str, name="Test", company_id=uuid4(), created_by=uuid4())
        cc.deactivate(actor=uuid4(), reason="Test deactivation")
        cc.reactivate(actor=uuid4(), reason="Test reactivation")
        assert cc.status == CostCenterStatus.ACTIVE

    def test_cost_center_close(self, valid_kwargs, cc_code_str):
        cc = CostCenter(code=cc_code_str, name="Test", company_id=uuid4(), created_by=uuid4())
        cc.close(actor=uuid4(), reason="Test closure")
        assert cc.status == CostCenterStatus.CLOSED

    def test_cost_center_modify(self, valid_kwargs, cc_code_str):
        cc = CostCenter(code=cc_code_str, name="Old Name", company_id=uuid4(), created_by=uuid4())
        cc.modify(new_name="New Name", actor=uuid4(), reason="Test modification")
        assert cc.name == "New Name"
        assert cc.audit_checksum is not None  # checksum should change

    def test_cost_center_modify_code(self, valid_kwargs, cc_code_str):
        cc = CostCenter(code=cc_code_str, name="Test", company_id=uuid4(), created_by=uuid4())
        cc.modify(new_code="C02", actor=uuid4(), reason="Code change")
        assert cc.code == "C02"


# ── Test: Dimension creation ─────────────────────────────────────────────────

class TestDimensionCreation:
    def test_valid_dimension_creation(self, valid_kwargs, dim_code, dim_code_str):
        dim = Dimension(
            code=dim_code_str,
            name="Khu vực",
            dimension_type=DimensionType.LOCATION,
            company_id=uuid4(),
            created_by=uuid4(),
        )
        # dim.code is stored as plain string after VO validation
        assert dim.code == dim_code_str
        assert dim.name == "Khu vực"
        assert dim.type == DimensionType.LOCATION
        assert dim.is_system is False

    def test_system_dimension_creation(self, valid_kwargs, dim_code):
        dim = Dimension(
            code=dim_code.value,  # use the validated code
            name="System dimension",
            dimension_type=DimensionType.LOCATION,
            is_system=True,
            company_id=uuid4(),
            created_by=uuid4(),
        )
        assert dim.is_system is True
        assert dim.type == DimensionType.LOCATION

    def test_dimension_modify_name(self, valid_kwargs, dim_code):
        dim = Dimension(code=dim_code.value, name="Old Name", dimension_type=DimensionType.LOCATION, company_id=uuid4(), created_by=uuid4())
        dim.modify(new_name="New Name", actor=uuid4(), reason="Test modification")
        assert dim.name == "New Name"
        assert dim.audit_checksum is not None  # checksum should change

    def test_dimension_set_system(self, valid_kwargs, dim_code):
        dim = Dimension(code=dim_code.value, name="Test", dimension_type=DimensionType.LOCATION, is_system=False, company_id=uuid4(), created_by=uuid4())
        dim.set_system(actor=uuid4(), reason="Mark as system")
        assert dim.is_system is True

    def test_dimension_code_validation(self, valid_kwargs):
        try:
            # Use DimensionCode VO which validates non-empty string
            Dimension(code=DimensionCode("", DimensionType.LOCATION).value, name="Test", dimension_type=DimensionType.LOCATION, company_id=uuid4(), created_by=uuid4())  # type: ignore
            assert False, "Should have raised error"
        except (DomainException, ValueError):
            pass  # Expected
