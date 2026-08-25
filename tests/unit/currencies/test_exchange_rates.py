"""Unit tests — ExchangeRate + resolve_booking_rate (specs §2.2, §3)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.bricks.currencies.domain import (
    BookingRateSide,
    FxRateSource,
    RateType,
)
from src.bricks.currencies.services import (
    ExchangeRateService,
    InvalidRateError,
)


class FakeRateRepo:
    def __init__(self):
        self.rows: list = []

    def add(self, r):
        self.rows.append(r)
        return r

    def latest_on_or_before(self, code, rate_type, on_date):
        cands = [
            x
            for x in self.rows
            if x.currency_code == code and x.rate_type == rate_type and x.rate_date <= on_date
        ]
        return max(cands, key=lambda x: x.rate_date) if cands else None


ACTOR = uuid4()
COMPANY = uuid4()


@pytest.fixture()
def svc():
    repo = FakeRateRepo()
    s = ExchangeRateService(repo)
    # seed USD TRANSFER rates (NHNN-style daily series)
    for d, r in [("2026-08-20", "25400"), ("2026-08-22", "25450")]:
        s.add_rate(
            currency_code="USD",
            rate_type=RateType.TRANSFER,
            rate_date=date.fromisoformat(d),
            rate=Decimal(r),
            source=FxRateSource.MANUAL,
            actor=ACTOR,
        )
    return s


class TestAddRate:
    def test_add_returns_entity(self, svc):
        r = svc.latest("USD", RateType.TRANSFER, date(2026, 8, 23))
        assert r.rate == Decimal(25450)  # gap-fill: last ≤ date

    def test_rate_must_be_positive(self):
        with pytest.raises(InvalidRateError):
            ExchangeRateService(FakeRateRepo()).add_rate(
                currency_code="USD",
                rate_type=RateType.BUY,
                rate_date=date(2026, 8, 1),
                rate=Decimal(0),
                source=FxRateSource.MANUAL,
                actor=ACTOR,
            )

    def test_unknown_currency_code_format(self):
        with pytest.raises(InvalidRateError):
            ExchangeRateService(FakeRateRepo()).add_rate(
                currency_code="usd",
                rate_type=RateType.BUY,
                rate_date=date(2026, 8, 1),
                rate=Decimal(25000),
                source=FxRateSource.MANUAL,
                actor=ACTOR,
            )


class TestResolveBooking:
    """§3: Nợ = actual (passed-in); Có = weighted avg of open FX balance."""

    def test_debit_uses_actual_rate_when_provided(self, svc):
        r = svc.resolve_booking_rate(
            entry_side=BookingRateSide.ACTUAL,
            currency="USD",
            rate_date=date(2026, 8, 23),
            actual_rate=Decimal(25500),
        )
        assert r == Decimal(25500)

    def test_debit_falls_back_to_latest_when_no_actual(self, svc):
        r = svc.resolve_booking_rate(
            entry_side=BookingRateSide.ACTUAL,
            currency="USD",
            rate_date=date(2026, 8, 23),
        )
        assert r == Decimal(25450)

    def test_credit_weighted_average_over_open_balance(self, svc):
        open_items = [
            (Decimal(1000), Decimal(25000)),  # orig, booked rate
            (Decimal(2000), Decimal(25600)),
        ]
        r = svc.resolve_booking_rate(
            entry_side=BookingRateSide.WEIGHTED_AVG,
            currency="USD",
            rate_date=date(2026, 8, 23),
            open_balance_provider=lambda cid, code: open_items,
            company_id=COMPANY,
        )
        expected = (1000 * 25000 + 2000 * 25600) / 3000
        assert abs(r - Decimal(str(expected))) < Decimal("0.01")

    def test_weighted_avg_empty_balance_falls_back_to_latest(self, svc):
        r = svc.resolve_booking_rate(
            entry_side=BookingRateSide.WEIGHTED_AVG,
            currency="USD",
            rate_date=date(2026, 8, 23),
            open_balance_provider=lambda cid, code: [],
            company_id=COMPANY,
        )
        assert r == Decimal(25450)

    def test_no_rate_history_at_all_raises(self):
        empty = ExchangeRateService(FakeRateRepo())
        with pytest.raises(InvalidRateError):
            empty.resolve_booking_rate(
                entry_side=BookingRateSide.WEIGHTED_AVG,
                currency="EUR",
                rate_date=date(2026, 8, 23),
            )

    def test_vnd_needs_no_rate(self, svc):
        assert svc.resolve_booking_rate(
            entry_side=BookingRateSide.WEIGHTED_AVG,
            currency="VND",
            rate_date=date(2026, 8, 23),
        ) == Decimal(1)
