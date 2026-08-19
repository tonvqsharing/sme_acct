"""Integration tests for CostCenter, Dimension, DimensionValue repositories.

Plain SQLAlchemy, no Flask app context (matching test_company_repository.py pattern).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker

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
from src.infrastructure.repositories import SQLAlchemyCostCenterRepository
from src.infrastructure.repositories import SQLAlchemyDimensionRepository
from src.infrastructure.repositories import SQLAlchemyDimensionValueRepository


@pytest.fixture(scope="function")
def engine():
    """Create a fresh in-memory SQLite engine for each test."""
    return create_engine("sqlite://")


@pytest.fixture(scope="function")
def session(engine):
    """Create a session bound to the in-memory engine."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    close_all_sessions()


@pytest.fixture(scope="function")
def cc_repo(session):
    """CostCenter repository bound to test session."""
    return SQLAlchemyCostCenterRepository(session)


@pytest.fixture(scope="function")
def dim_repo(session):
    """Dimension repository bound to test session."""
    return SQLAlchemyDimensionRepository(session)


@pytest.fixture(scope="function")
def dv_repo(session):
    """DimensionValue repository bound to test session."""
    return SQLAlchemyDimensionValueRepository(session)


# Fixture with valid kwargs (matching company test pattern)
@pytest.fixture
def valid_kwargs():
    """Base kwargs for entity creation."""
    return {
        "id": uuid4(),
        "created_by": uuid4(),
        "updated_by": uuid4(),
    }


# ── Test: CostCenter repository ─────────────────────────────────────────────

class TestCostCenterRepository:
    def test_create_and_get_cost_center(self, cc_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import CostCenterCode
        cc = CostCenter(
            code=CostCenterCode("001"),
            name="Phòng kế toán",
            **valid_kwargs,
        )
        cc_repo.create(cc)
        session.flush()

        retrieved = cc_repo.get_by_id(UUID(str(cc.id)))
        assert retrieved is not None
        assert retrieved.code == CostCenterCode("001")
        assert retrieved.name == "Phòng kế toán"
        assert retrieved.status == CostCenterStatus.ACTIVE

    def test_get_by_code(self, cc_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import CostCenterCode
        cc = CostCenter(
            code=CostCenterCode("002"),
            name="Phòng tài chính",
            **valid_kwargs,
        )
        cc_repo.create(cc)
        session.flush()

        retrieved = cc_repo.get_by_code(CostCenterCode("002"))
        assert retrieved is not None
        assert retrieved.name == "Phòng tài chính"

    def test_update_cost_center(self, cc_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import CostCenterCode
        cc = CostCenter(
            code=CostCenterCode("003"),
            name="Phòng cũ",
            **valid_kwargs,
        )
        cc_repo.create(cc)
        session.flush()

        cc.name = "Phòng mới"
        updated = cc_repo.update(cc)
        assert updated.name == "Phòng mới"

    def test_soft_delete_cost_center(self, cc_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import CostCenterCode
        cc = CostCenter(
            code=CostCenterCode("004"),
            name="Phòng sẽ xóa",
            **valid_kwargs,
        )
        cc_repo.create(cc)
        session.flush()

        # Soft delete via status change
        cc.status = CostCenterStatus.INACTIVE
        updated = cc_repo.update(cc)
        assert updated.status == CostCenterStatus.INACTIVE
        assert updated.is_active is False

    def test_list_by_company(self, cc_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import CostCenterCode
        # Create costs for two "companies"
        cc1 = CostCenter(code=CostCenterCode("010"), name="Cty A", **valid_kwargs)
        cc2 = CostCenter(code=CostCenterCode("020"), name="Cty B", **valid_kwargs)
        # Change company_id for second
        cc2_id = uuid4()
        cc2 = CostCenter(code=CostCenterCode("020"), name="Cty B", company_id=cc2_id, **valid_kwargs)
        cc_repo.create(cc1)
        cc_repo.create(cc2)
        session.flush()

        # List for cc1's company
        results = cc_repo.list_by_company(cc1.company_id if hasattr(cc1, 'company_id') else cc1.id)
        assert len(results) >= 1
        names = [c.name for c in results]
        assert "Cty A" in names


# ── Test: Dimension repository ──────────────────────────────────────────────

class TestDimensionRepository:
    def test_create_and_get_dimension(self, dim_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import DimensionCode
        dim = Dimension(
            code=DimensionCode("D1"),
            name="Khu vực",
            dimension_type=DimensionType.LOCATION,
            is_system=False,
            **valid_kwargs,
        )
        dim_repo.create(dim)
        session.flush()

        retrieved = dim_repo.get_by_id(UUID(str(dim.id)))
        assert retrieved is not None
        assert retrieved.code == DimensionCode("D1")
        assert retrieved.name == "Khu vực"
        assert retrieved.type == DimensionType.LOCATION
        assert retrieved.is_system is False

    def test_list_by_company(self, dim_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import DimensionCode
        dim1 = Dimension(
            code=DimensionCode("D2"),
            name="Nhóm hàng",
            dimension_type=DimensionType.PRODUCT,
            is_system=False,
            **valid_kwargs,
        )
        dim2 = Dimension(
            code=DimensionCode("D3"),
            name="Khu vực",
            dimension_type=DimensionType.LOCATION,
            is_system=False,
            **valid_kwargs,
        )
        dim2_id = uuid4()
        dim2 = Dimension(code=DimensionCode("D3"), name="Khu vực", dimension_type=DimensionType.LOCATION, is_system=False, company_id=dim2_id, **valid_kwargs)
        dim_repo.create(dim1)
        dim_repo.create(dim2)
        session.flush()

        results = dim_repo.list_by_company(dim1.company_id if hasattr(dim1, 'company_id') else dim1.id)
        names = [d.name for d in results]
        assert "Nhóm hàng" in names
        assert "Khu vực" not in names

    def test_get_by_type(self, dim_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import DimensionCode, DimensionType
        dim1 = Dimension(
            code=DimensionCode("D4"),
            name="Product A",
            dimension_type=DimensionType.PRODUCT,
            is_system=False,
            **valid_kwargs,
        )
        dim2 = Dimension(
            code=DimensionCode("D5"),
            name="LOC-001",
            dimension_type=DimensionType.LOCATION,
            is_system=False,
            **valid_kwargs,
        )
        dim_repo.create(dim1)
        dim_repo.create(dim2)
        session.flush()

        location_dims = dim_repo.list_by_type(DimensionType.LOCATION)
        loc_names = [d.name for d in location_dims]
        assert "LOC-001" in loc_names
        assert "Product A" not in loc_names


# ── Test: DimensionValue repository ─────────────────────────────────────────

class TestDimensionValueRepository:
    def test_create_and_get_dimension_value(self, dv_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import DimensionCode
        dv = DimensionValue(
            code=DimensionCode("DV001"),
            name="Khu vực TP.HCM",
            status=DimensionValueStatus.ACTIVE,
            dimension_id=uuid4(),
            **valid_kwargs,
        )
        dv_repo.create(dv)
        session.flush()

        retrieved = dv_repo.get_by_id(UUID(str(dv.id)))
        assert retrieved is not None
        assert retrieved.code == DimensionCode("DV001")
        assert retrieved.name == "Khu vực TP.HCM"
        assert retrieved.status == DimensionValueStatus.ACTIVE
        assert retrieved.is_active is True

    def test_list_by_company_and_dimension(self, dv_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import DimensionCode
        # Create DV for two different dimensions
        dv1 = DimensionValue(
            code=DimensionCode("DV001"),
            name="TP.HCM",
            dimension_id=uuid4(),
            **valid_kwargs,
        )
        dv2 = DimensionValue(
            code=DimensionCode("DV001"),
            name="Hà Nội",
            dimension_id=uuid4(),  # Different dimension
            **valid_kwargs,
        )
        dv_repo.create(dv1)
        dv_repo.create(dv2)
        session.flush()

        # List for dv1's dimension
        results = dv_repo.list_by_company_and_dimension(dv1.company_id if hasattr(dv1, 'company_id') else dv1.id, dv1.dimension_id)
        names = [d.name for d in results]
        assert "TP.HCM" in names

    def test_soft_delete_dimension_value(self, dv_repo, session, valid_kwargs):
        from src.domain.entities.cost_center import DimensionCode, DimensionValueStatus
        dv = DimensionValue(
            code=DimensionCode("DV001"),
            name="Test DV",
            status=DimensionValueStatus.ACTIVE,
            dimension_id=uuid4(),
            **valid_kwargs,
        )
        dv_repo.create(dv)
        session.flush()

        dv.status = DimensionValueStatus.INACTIVE
        updated = dv_repo.update(dv)
        assert updated.status == DimensionValueStatus.INACTIVE
        assert updated.is_active is False
