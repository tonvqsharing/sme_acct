"""TDD RED — Slice 2b: 8% exclusion categories as data (panel-managed)."""

from __future__ import annotations

from uuid import uuid4

from src.bricks.system_settings.exclusions import CategoryExclusionService

COMPANY = uuid4()


class FakeRepo:
    def __init__(self):
        self.rows: dict = {}  # company_id -> set(category)

    def list_categories(self, cid):
        return sorted(self.rows.get(cid, set()))

    def add(self, cid, category):
        self.rows.setdefault(cid, set()).add(category.lower())
        return category

    def remove(self, cid, category):
        self.rows.get(cid, set()).discard(category.lower())


def _svc():
    return CategoryExclusionService(repo=FakeRepo(), audit=None)


def test_seeded_defaults_exclude_telecom():
    svc = _svc()
    assert svc.is_eligible(COMPANY, "telecom") is False
    assert svc.is_eligible(COMPANY, "manufacturing") is True
    assert svc.is_eligible(COMPANY, None) is True


def test_admin_can_remove_and_readd_category():
    svc = _svc()
    svc.remove_category(COMPANY, "telecom", actor=uuid4(), reason="law change")
    assert svc.is_eligible(COMPANY, "telecom") is True
    svc.add_category(COMPANY, "telecom", actor=uuid4(), reason="re-include")
    assert svc.is_eligible(COMPANY, "telecom") is False


def test_categories_are_company_isolated():
    svc = _svc()
    other = uuid4()
    svc.remove_category(COMPANY, "telecom", actor=uuid4(), reason="x")
    assert svc.is_eligible(other, "telecom") is False
