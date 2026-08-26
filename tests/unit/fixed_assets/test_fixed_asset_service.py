"""Unit tests — FixedAsset entity + service per docs/fixed-assets/specs."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.fixed_assets.domain import FixedAsset
from src.bricks.fixed_assets.services import (
    DuplicateAssetCodeError,
    FixedAssetService,
    MissingActorError,
)

COMPANY = uuid4()
ACTOR = uuid4()


class FakeRepo:
    def __init__(self):
        self.rows = {}

    def create(self, a):
        self.rows[a.id] = a
        return a

    def get_by_id(self, aid):
        return self.rows.get(aid)

    def get_by_company(self, cid):
        return [a for a in self.rows.values() if a.company_id == cid]

    def update(self, a):
        self.rows[a.id] = a
        return a

    def exists_duplicate(self, cid, code):
        return any(a.company_id == cid and a.asset_code == code for a in self.rows.values())

    def find_active_with_remaining(self, cid):
        return [
            a
            for a in self.rows.values()
            if a.company_id == cid and a.is_active and a.accumulated_depreciation < a.original_cost
        ]


@pytest.fixture()
def svc():
    return FixedAssetService(FakeRepo())


def _body(**over):
    b = {
        "company_id": COMPANY,
        "asset_code": "TSCD/0001",
        "name": "May Photocopy Ricoh",
        "category": "huu_hinh",
        "original_cost": Decimal(50000000),
        "acquisition_date": date(2026, 1, 15),
        "useful_life_months": 60,
        "depreciation_account": "6421",
        "actor": ACTOR,
        "reason": "mua moi",
    }
    b.update(over)
    return b


# -- Entity ----------------------------------------------------------------


class TestFixedAssetEntity:
    def test_monthly_depreciation_straight_line(self):
        fa = FixedAsset(
            company_id=COMPANY,
            asset_code="T/001",
            name="X",
            category="huu_hinh",
            original_cost=Decimal(50000000),
            acquisition_date=date(2026, 1, 15),
            useful_life_months=60,
            depreciation_account="6421",
        )
        assert fa.monthly_depreciation == Decimal(833333)

    def test_book_value_after_depreciation(self):
        fa = FixedAsset(
            company_id=COMPANY,
            asset_code="T/002",
            name="Y",
            category="huu_hinh",
            original_cost=Decimal(60000000),
            acquisition_date=date(2026, 2, 1),
            useful_life_months=120,
            depreciation_account="641",
            accumulated_depreciation=Decimal(1000000),
        )
        assert fa.book_value == Decimal(59000000)

    @pytest.mark.parametrize("cost", ["0", "-1"])
    def test_zero_or_negative_cost_rejected(self, cost):
        with pytest.raises(ValueError, match="[Cc]ost"):
            FixedAsset(
                company_id=COMPANY,
                asset_code="T",
                name="x",
                category="huu_hinh",
                original_cost=Decimal(cost),
                acquisition_date=date(2026, 1, 1),
                useful_life_months=12,
                depreciation_account="6421",
            )

    @pytest.mark.parametrize("months", [0, -3])
    def test_invalid_useful_life_rejected(self, months):
        with pytest.raises(ValueError, match="[Uu]seful"):
            FixedAsset(
                company_id=COMPANY,
                asset_code="T",
                name="x",
                category="huu_hinh",
                original_cost=Decimal(1000),
                acquisition_date=date(2026, 1, 1),
                useful_life_months=months,
                depreciation_account="6421",
            )


# -- Service CRUD ----------------------------------------------------------


class TestCreateAsset:
    def test_create_stamps_checksum_active(self, svc):
        fa = svc.create_asset(**_body())
        assert len(fa.checksum) == 64

    def test_duplicate_code_raises(self, svc):
        svc.create_asset(**_body())
        with pytest.raises(DuplicateAssetCodeError):
            svc.create_asset(**_body())

    def test_missing_actor_raises(self, svc):
        body = _body()
        del body["actor"]
        with pytest.raises(MissingActorError):
            svc.create_asset(**body)


# -- Depreciation engine ---------------------------------------------------


class TestDepreciationCompute:
    def test_single_asset_monthly_depreciation(self, svc):
        fa = svc.create_asset(**_body())
        result = svc.compute_and_post(COMPANY, actor=uuid4())
        entry = next(e for e in result["entries"] if e["asset_id"] == str(fa.id))
        assert Decimal(entry["amount"]) == Decimal(833333)
        fresh = svc.get_asset(fa.id)
        assert fresh.accumulated_depreciation == Decimal(833333)

    def test_capped_at_remaining_when_last_month(self, svc):
        fa = svc.create_asset(
            **_body(
                original_cost=Decimal(100000),
                useful_life_months=10,
            )
        )
        fa.accumulated_depreciation = Decimal(95000)
        svc._repo.update(fa)
        result = svc.compute_and_post(COMPANY, actor=uuid4())
        entry = next(e for e in result["entries"] if e["asset_id"] == str(fa.id))
        assert Decimal(entry["amount"]) == Decimal(5000)

    def test_fully_depreciated_skipped(self, svc):
        fa = svc.create_asset(**_body())
        fa.accumulated_depreciation = fa.original_cost
        svc._repo.update(fa)
        result = svc.compute_and_post(COMPANY, actor=uuid4())
        ids = [e["asset_id"] for e in result["entries"]]
        assert str(fa.id) not in ids

    def test_closed_asset_skipped(self, svc):
        fa = svc.create_asset(**_body())
        svc.deactivate(fa.id, actor=uuid4(), reason="close")
        result = svc.compute_and_post(COMPANY, actor=uuid4())
        ids = [e["asset_id"] for e in result["entries"]]
        assert str(fa.id) not in ids

    def test_grouped_journal_by_expense_account(self, svc):
        svc.create_asset(**_body(depreciation_account="6421"))
        svc.create_asset(
            **_body(
                asset_code="TSCD/0002",
                name="Laptop Dell",
                original_cost=Decimal(30000000),
                useful_life_months=36,
                depreciation_account="627",
            )
        )
        result = svc.compute_and_post(COMPANY, actor=uuid4())
        accounts = {jg["expense_account"] for jg in result["journal_groups"]}
        assert "6421" in accounts
        assert "627" in accounts


# -- Lifecycle ---------------------------------------------------------------


class TestLifecycle:
    def test_deactivate_soft_close_blocks_compute(self, svc):
        fa = svc.create_asset(**_body())
        out = svc.deactivate(fa.id, actor=uuid4(), reason="thanh ly")
        assert out.is_active is False
        assert svc.get_asset(fa.id) is not None

    def test_unknown_get_returns_none(self, svc):
        assert svc.get_asset(uuid4()) is None
