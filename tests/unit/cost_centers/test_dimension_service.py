"""Unit tests — Dimension & DimensionValue per docs/cost-centers-dimensions/specs §1."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.cost_centers.domain import (
    DimensionType,
    DimensionValueStatus,
)
from src.bricks.cost_centers.services import (
    DimensionService,
    DimensionValueService,
    DuplicateCodeError,
    InvalidTransitionError,
    NotFoundError,
)

C = uuid4()
ACTOR = uuid4()


# ---------------------------------------------------------------------------
# Fake repos
# ---------------------------------------------------------------------------


class FakeDimRepo:
    def __init__(self) -> None:
        self.rows: dict = {}

    def create(self, dim):
        self.rows[dim.id] = dim
        return dim

    def get_by_id(self, did):
        return self.rows.get(did)

    def get_by_company(self, cid, *, dimension_type=None, is_system=None):
        return [
            x
            for x in self.rows.values()
            if x.company_id == cid
            and (dimension_type is None or x.type.value == dimension_type)
            and (is_system is None or x.is_system == is_system)
        ]

    def update(self, dim):
        self.rows[dim.id] = dim
        return dim

    def exists_duplicate(self, cid, code):
        return any(x.company_id == cid and x.code == code for x in self.rows.values())


class FakeDVRepo:
    def __init__(self) -> None:
        self.rows: dict = {}

    def create(self, dv):
        self.rows[dv.id] = dv
        return dv

    def get_by_id(self, dvid):
        return self.rows.get(dvid)

    def get_by_company(self, cid, *, dimension_id=None, status=None):
        return [
            x
            for x in self.rows.values()
            if x.company_id == cid
            and (dimension_id is None or x.dimension_id == dimension_id)
            and (status is None or x.status.value == status)
        ]

    def update(self, dv):
        self.rows[dv.id] = dv
        return dv

    def exists_duplicate(self, dim_id, cid, code):
        return any(
            x.dimension_id == dim_id and x.company_id == cid and x.code == code
            for x in self.rows.values()
        )


@pytest.fixture()
def dim_svc():
    return DimensionService(FakeDimRepo())


@pytest.fixture()
def dv_svc():
    return DimensionValueService(FakeDVRepo())


# ---------------------------------------------------------------------------
# Dimension tests
# ---------------------------------------------------------------------------


def _dim_body(**over):
    b = {
        "company_id": C,
        "code": "PROJ-01",
        "name": "Project Alpha",
        "dimension_type": DimensionType.PROJECT,
        "actor": ACTOR,
        "reason": "init",
    }
    b.update(over)
    return b


class TestDimensionCreate:
    def test_create_active_with_checksum(self, dim_svc):
        dim = dim_svc.create(**_dim_body())
        assert dim.type == DimensionType.PROJECT
        assert len(dim.audit_checksum) == 64

    def test_duplicate_code_raises(self, dim_svc):
        dim_svc.create(**_dim_body())
        with pytest.raises(DuplicateCodeError):
            dim_svc.create(**_dim_body(code="PROJ-01", name="Dup"))

    @pytest.mark.parametrize("bad", ["", "1ABC", "X" * 51, None])
    def test_invalid_code_rejected(self, dim_svc, bad):
        with pytest.raises(ValueError):
            dim_svc.create(**_dim_body(code=bad))

    def test_empty_name_rejected(self, dim_svc):
        with pytest.raises(ValueError, match="[Nn]ame"):
            dim_svc.create(**_dim_body(name=""))

    def test_missing_actor_raises(self, dim_svc):
        body = _dim_body()
        del body["actor"]
        with pytest.raises(ValueError, match="[Aa]ctor"):
            dim_svc.create(**body)

    def test_system_dimension(self, dim_svc):
        dim = dim_svc.create(**_dim_body(is_system=True))
        assert dim.is_system is True


class TestDimensionLifecycle:
    def _seed(self, dim_svc):
        return dim_svc.create(**_dim_body())

    def test_modify_name(self, dim_svc):
        dim = self._seed(dim_svc)
        old = dim.audit_checksum
        mod = dim_svc.modify(dim.id, new_name="Project Beta", actor=ACTOR, reason="rename")
        assert mod.name == "Project Beta"
        assert mod.audit_checksum != old

    def test_system_dimension_cannot_modify(self, dim_svc):
        dim = dim_svc.create(**_dim_body(is_system=True))
        with pytest.raises(InvalidTransitionError):
            dim_svc.modify(dim.id, new_name="X", actor=ACTOR, reason="rename")

    def test_set_system(self, dim_svc):
        dim = self._seed(dim_svc)
        assert dim.is_system is False
        out = dim_svc.set_system(dim.id, actor=ACTOR, reason="promote")
        assert out.is_system is True

    def test_not_found_raises(self, dim_svc):
        with pytest.raises(NotFoundError):
            dim_svc.modify(uuid4(), new_name="X", actor=ACTOR, reason="nope")


class TestDimensionQueries:
    def test_list_by_company(self, dim_svc):
        dim_svc.create(**_dim_body())
        dim_svc.create(
            **_dim_body(code="LOC-01", name="Hanoi", dimension_type=DimensionType.LOCATION)
        )
        assert len(dim_svc.list_by_company(C)) == 2

    def test_list_by_type(self, dim_svc):
        dim_svc.create(**_dim_body())
        dim_svc.create(
            **_dim_body(code="LOC-01", name="Hanoi", dimension_type=DimensionType.LOCATION)
        )
        proj = dim_svc.list_by_company(C, dimension_type="Project")
        assert len(proj) == 1
        assert proj[0].type == DimensionType.PROJECT

    def test_list_by_system(self, dim_svc):
        dim_svc.create(**_dim_body())
        dim_svc.create(**_dim_body(code="SYS-01", name="System", is_system=True))
        sys_dims = dim_svc.list_by_company(C, is_system=True)
        assert len(sys_dims) == 1
        assert sys_dims[0].is_system is True


# ---------------------------------------------------------------------------
# DimensionValue tests
# ---------------------------------------------------------------------------


def _dv_body(**over):
    dim_id = uuid4()
    b = {
        "company_id": C,
        "dimension_id": dim_id,
        "code": "PRJ-A",
        "name": "Alpha Project",
        "actor": ACTOR,
        "reason": "init",
    }
    b.update(over)
    return b


class TestDimensionValueCreate:
    def test_create_active_with_checksum(self, dv_svc):
        dv = dv_svc.create(**_dv_body())
        assert dv.status.value == "Active"
        assert len(dv.audit_checksum) == 64

    def test_duplicate_code_raises(self, dv_svc):
        dim_id = uuid4()
        dv_svc.create(**_dv_body(dimension_id=dim_id))
        with pytest.raises(DuplicateCodeError):
            dv_svc.create(**_dv_body(dimension_id=dim_id, code="PRJ-A", name="Dup"))

    @pytest.mark.parametrize("bad", ["", "1ABC", None])
    def test_invalid_code_rejected(self, dv_svc, bad):
        with pytest.raises(ValueError):
            dv_svc.create(**_dv_body(code=bad))

    def test_empty_name_rejected(self, dv_svc):
        with pytest.raises(ValueError, match="[Nn]ame"):
            dv_svc.create(**_dv_body(name=""))

    def test_missing_actor_raises(self, dv_svc):
        body = _dv_body()
        del body["actor"]
        with pytest.raises(ValueError, match="[Aa]ctor"):
            dv_svc.create(**body)


class TestDimensionValueLifecycle:
    def _seed(self, dv_svc):
        return dv_svc.create(**_dv_body())

    def test_deactivate_reactivate(self, dv_svc):
        dv = self._seed(dv_svc)
        off = dv_svc.deactivate(dv.id, actor=ACTOR, reason="pause")
        assert off.status == DimensionValueStatus.INACTIVE
        on = dv_svc.reactivate(dv.id, actor=ACTOR, reason="resume")
        assert on.status == DimensionValueStatus.ACTIVE

    def test_deactivate_already_inactive_raises(self, dv_svc):
        dv = self._seed(dv_svc)
        dv_svc.deactivate(dv.id, actor=ACTOR, reason="pause")
        with pytest.raises(InvalidTransitionError):
            dv_svc.deactivate(dv.id, actor=ACTOR, reason="pause again")

    def test_reactivate_already_active_raises(self, dv_svc):
        dv = self._seed(dv_svc)
        with pytest.raises(InvalidTransitionError):
            dv_svc.reactivate(dv.id, actor=ACTOR, reason="already active")

    def test_modify_changes_name_and_checksum(self, dv_svc):
        dv = self._seed(dv_svc)
        old = dv.audit_checksum
        mod = dv_svc.modify(dv.id, new_name="Beta", actor=ACTOR, reason="rename")
        assert mod.name == "Beta"
        assert mod.audit_checksum != old

    def test_modify_inactive_raises(self, dv_svc):
        dv = self._seed(dv_svc)
        dv_svc.deactivate(dv.id, actor=ACTOR, reason="pause")
        with pytest.raises(InvalidTransitionError):
            dv_svc.modify(dv.id, new_name="X", actor=ACTOR, reason="rename")

    def test_not_found_raises(self, dv_svc):
        with pytest.raises(NotFoundError):
            dv_svc.deactivate(uuid4(), actor=ACTOR, reason="nope")


class TestDimensionValueQueries:
    def test_list_by_company(self, dv_svc):
        dv_svc.create(**_dv_body())
        dv_svc.create(**_dv_body(code="PRJ-B", name="Beta"))
        assert len(dv_svc.list_by_company(C)) == 2

    def test_list_by_dimension(self, dv_svc):
        dim_id = uuid4()
        dv_svc.create(**_dv_body(dimension_id=dim_id))
        dv_svc.create(**_dv_body(dimension_id=uuid4(), code="PRJ-B", name="Other"))
        result = dv_svc.list_by_company(C, dimension_id=dim_id)
        assert len(result) == 1

    def test_list_by_status(self, dv_svc):
        dv = dv_svc.create(**_dv_body())
        dv_svc.deactivate(dv.id, actor=ACTOR, reason="pause")
        inactive = dv_svc.list_by_company(C, status="Inactive")
        assert len(inactive) == 1
        active = dv_svc.list_by_company(C, status="Active")
        assert len(active) == 0
