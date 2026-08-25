"""Unit tests — Currency master + FX config flags (specs §2.1, §2.3)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.bricks.currencies.domain import (
    BookingRateSide,
    Currency,
    InvalidCurrencyCodeError,
)
from src.bricks.currencies.services import (
    BaseCurrencyImmutableError,
    CurrencyService,
    DuplicateCurrencyError,
)


class _FakeConfigRepo:
    def __init__(self):
        self.rows = {}

    def get(self, cid):
        return self.rows.get(cid)

    def save(self, cfg):
        self.rows[cfg.company_id] = cfg
        return cfg


class FakeRepo:
    def __init__(self):
        self.rows = {}

    def create(self, c):
        self.rows[c.code] = c
        return c

    def get_by_code(self, code):
        return self.rows.get(code)

    def all(self):
        return list(self.rows.values())

    def count_transactions_for(self, code):
        return 0


@pytest.fixture()
def svc():
    return CurrencyService(FakeRepo(), config_repo=_FakeConfigRepo())


class TestCurrencyVO:
    @pytest.mark.parametrize("code", ["USD", "EUR", "JPY", "VND"])
    def test_valid_iso_codes(self, code):
        c = Currency(code=code, name="x", symbol="x", decimal_places=2)
        assert len(c.code) == 3

    @pytest.mark.parametrize("bad", ["usd", "US", "USDX", "U D", ""])
    def test_invalid_code_rejected(self, bad):
        with pytest.raises(InvalidCurrencyCodeError):
            Currency(code=bad, name="x", symbol="x", decimal_places=2)

    def test_negative_decimal_places_rejected(self):
        with pytest.raises(ValueError, match="decimal_places"):
            Currency(code="USD", name="x", symbol="$", decimal_places=-1)

    def test_jpy_zero_places_ok(self):
        Currency(code="JPY", name="Yen", symbol="¥", decimal_places=0)


class TestCurrencyMaster:
    def test_vnd_seeded_as_base_zero_places(self, svc):
        svc.ensure_base_currency()
        vnd = svc.get("VND")
        assert vnd is not None
        assert vnd.decimal_places == 0

    def test_duplicate_code_rejected(self, svc):
        svc.create(code="USD", name="Dollar", symbol="$", decimal_places=2, actor=uuid4())
        with pytest.raises(DuplicateCurrencyError):
            svc.create(code="USD", name="Dup", symbol="$", decimal_places=2, actor=uuid4())

    def test_deactivate_soft_only(self, svc):
        svc.ensure_base_currency()
        out = svc.deactivate("VND", actor=uuid4()) if False else None
        usd = svc.create(code="USD", name="D", symbol="$", decimal_places=2, actor=uuid4())
        out = svc.deactivate(usd.code, actor=uuid4())
        assert out.is_active is False


class TestFxConfig:
    """§2.3: LAW-type flags immutable after first use."""

    def test_default_config_vnd_base(self, svc):
        cfg = svc.get_fx_config(uuid4())
        assert cfg.base_currency == "VND"
        assert cfg.fx_revaluation_approval_required is True
        assert cfg.booking_rate_debit == BookingRateSide.ACTUAL
        assert cfg.booking_rate_credit == BookingRateSide.WEIGHTED_AVG

    def test_change_base_currency_locked(self, svc):
        cid = uuid4()
        svc.get_fx_config(cid)
        cid = uuid4()
        svc.get_fx_config(cid)  # first use initializes
        with pytest.raises(BaseCurrencyImmutableError):
            svc.set_base_currency(cid, "USD")
