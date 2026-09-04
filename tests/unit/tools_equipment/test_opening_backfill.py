"""TDD RED — Opening S4b: CCDC opening via elapsed-allocation backfill."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.tools_equipment.domain import CCDCCategory
from src.bricks.tools_equipment.services import ToolEquipmentService

COMPANY = uuid4()
ACTOR = uuid4()


class FakeRepo:
    def __init__(self):
        self.items: dict = {}

    def find_by_code_and_company(self, code, cid):
        return None

    def create(self, entity):
        self.items[entity.id] = entity
        return entity

    def list_active_by_company(self, cid):
        return []


class FakeAllocRepo:
    def __init__(self):
        self.rows: list = []

    def sum_allocated_by_tools(self, ids):
        return {}

    def find_existing_allocation(self, tid, year, month):
        return None

    def create_many(self, entities):
        self.rows.extend(entities)
        return entities


class FakeFY:
    def is_period_open(self, year, month):
        return True


class FakeCOA:
    def is_account_active(self, cid, code):
        return True


def _svc():
    return ToolEquipmentService(
        repo=FakeRepo(),
        alloc_repo=FakeAllocRepo(),
        fy_service=FakeFY(),
        coa_service=FakeCOA(),
    )


def test_open_with_history_backfills_elapsed_months():
    svc = _svc()
    # price 12M, life 12, 7 months left → 5 elapsed × 1M = 5M allocated
    item = svc.open_ccdc_with_history(
        company_id=COMPANY,
        code="CCDC-OP",
        name="Máy khoan",
        category=CCDCCategory.LABOR_TOOL,
        purchase_date=date(2026, 1, 15),
        purchase_price=Decimal(12000000),
        useful_life_months=12,
        expense_account_code="627",
        actor_id=ACTOR,
        remaining_value=Decimal(7000000),
        months_left=7,
    )
    assert len(svc._alloc_repo.rows) == 5
    total = sum((r.allocated_amount for r in svc._alloc_repo.rows), Decimal(0))
    assert total == Decimal(12000000) - Decimal(7000000)
    assert all(r.status.value == "Posted" for r in svc._alloc_repo.rows)
    assert item.code == "CCDC-OP"


def test_open_with_history_remaining_guard():
    svc = _svc()
    with pytest.raises(ValueError, match="remaining"):
        svc.open_ccdc_with_history(
            company_id=COMPANY,
            code="CCDC-BAD",
            name="X",
            category=CCDCCategory.OTHER,
            purchase_date=date(2026, 1, 15),
            purchase_price=Decimal(12000000),
            useful_life_months=12,
            expense_account_code="627",
            actor_id=ACTOR,
            remaining_value=Decimal(20000000),
            months_left=7,
        )


def test_open_with_history_full_remaining_no_rows():
    svc = _svc()
    svc.open_ccdc_with_history(
        company_id=COMPANY,
        code="CCDC-NEW",
        name="Mới",
        category=CCDCCategory.OTHER,
        purchase_date=date(2026, 1, 15),
        purchase_price=Decimal(12000000),
        useful_life_months=12,
        expense_account_code="627",
        actor_id=ACTOR,
        remaining_value=Decimal(12000000),
        months_left=12,
    )
    assert svc._alloc_repo.rows == []
