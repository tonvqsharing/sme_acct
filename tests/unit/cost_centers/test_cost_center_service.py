"""Unit tests — CostCenter per docs/cost-centers-dimensions/specs §1."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.cost_centers.domain import (
    CostCenterStatus,
)
from src.bricks.cost_centers.services import (
    CostCenterService,
    DuplicateCodeError,
)

C = uuid4()
ACTOR = uuid4()


class FakeRepo:
    def __init__(self):
        self.rows = {}

    def create(self, cc):
        self.rows[cc.id] = cc
        return cc

    def get_by_id(self, cid):
        return self.rows.get(cid)

    def get_by_company(self, c):
        return [x for x in self.rows.values() if x.company_id == c]

    def update(self, cc):
        self.rows[cc.id] = cc
        return cc

    def exists_duplicate(self, cid, code):
        return any(x.company_id == cid and x.code == code for x in self.rows.values())


@pytest.fixture()
def svc():
    return CostCenterService(FakeRepo())


def _body(**over):
    b = {
        "company_id": C,
        "code": "KT",
        "name": "Kế toán",
        "actor": ACTOR,
        "reason": "init",
    }
    b.update(over)
    return b


class TestCreate:
    def test_create_active_with_checksum(self, svc):
        cc = svc.create(**_body())
        assert cc.status.value == "Active"
        assert len(cc.audit_checksum) == 64

    def test_duplicate_code_raises(self, svc):
        svc.create(**_body())
        with pytest.raises(DuplicateCodeError):
            svc.create(**_body(code="KT", name="Dup"))

    @pytest.mark.parametrize("bad", ["", "1ABC", "TOOLONGCODE123", None])
    def test_invalid_code_rejected(self, svc, bad):
        with pytest.raises(ValueError):
            svc.create(**_body(code=bad))

    def test_empty_name_rejected(self, svc):
        with pytest.raises(ValueError, match="[Nn]ame"):
            svc.create(**_body(name=""))

    def test_missing_actor_raises(self, svc):
        body = _body()
        del body["actor"]
        with pytest.raises(ValueError, match="[Aa]ctor"):
            svc.create(**body)


class TestLifecycle:
    def _seed(self, svc):
        return svc.create(**_body())

    def test_deactivate_reactivate(self, svc):
        cc = self._seed(svc)
        off = svc.deactivate(cc.id, actor=ACTOR, reason="pause")
        assert off.status == CostCenterStatus.INACTIVE
        on = svc.reactivate(cc.id, actor=ACTOR, reason="resume")
        assert on.status == CostCenterStatus.ACTIVE

    def test_close_terminal(self, svc):
        cc = self._seed(svc)
        out = svc.close(cc.id, actor=ACTOR, reason="done")
        assert out.status == CostCenterStatus.CLOSED
        with pytest.raises(ValueError):
            svc.reactivate(out.id, actor=ACTOR, reason="reopen")

    def test_modify_changes_name_and_checksum(self, svc):
        cc = self._seed(svc)
        old = cc.audit_checksum
        mod = svc.modify(cc.id, new_name="Tài chính", actor=ACTOR, reason="rename")
        assert mod.name == "Tài chính"
        assert mod.audit_checksum != old


class TestQueries:
    def test_list_by_company(self, svc):
        svc.create(**_body())
        svc.create(**_body(code="KD", name="Kinh doanh"))
        assert len(svc.list_by_company(C)) == 2
