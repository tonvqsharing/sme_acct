"""Currency master service — §2.1 + FX config flags (§2.3)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.currencies.domain import (
    DEFAULT_BASE_CURRENCY,
    BookingRateSide,
    Currency,
    FxCompanyConfig,
    InvalidCurrencyCodeError,
    InvalidRateError,
    RateType,
)


class ActorRequiredError(Exception):
    code = "MISSING_ACTOR"


class DuplicateCurrencyError(Exception):
    code = "DUPLICATE_CURRENCY"


class BaseCurrencyImmutableError(Exception):
    code = "BASE_CURRENCY_LOCKED"


class NotFoundError(Exception):
    code = "NOT_FOUND"


def _d(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


def _require(actor: UUID | None) -> UUID:
    if actor is None:
        raise ActorRequiredError("actor là bắt buộc")
    return actor


class CurrencyService:
    def __init__(self, repo: Any, config_repo: Any | None = None) -> None:
        self._repo = repo
        self._config_repo = config_repo

    # ── master ──────────────────────────────────────────────────────────
    def ensure_base_currency(self) -> Currency:
        if self._repo.get_by_code(DEFAULT_BASE_CURRENCY) is None:
            vnd = Currency(
                code="VND",
                name="Việt Nam Đồng",
                symbol="₫",
                decimal_places=0,
                is_base=True,
            )
            created: Currency = self._repo.create(vnd)
            return created
        existing: Currency | None = self._repo.get_by_code(DEFAULT_BASE_CURRENCY)
        assert existing is not None
        return existing

    def create(
        self, *, code: str, name: str, symbol: str, decimal_places: int, actor: UUID | None = None
    ) -> Currency:
        _require(actor)
        if self._repo.get_by_code(code) is not None:
            raise DuplicateCurrencyError(f"Đã tồn tại {code}")
        cur = Currency(code=code, name=name.strip(), symbol=symbol, decimal_places=decimal_places)
        created: Currency = self._repo.create(cur)
        return created

    def get(self, code: str) -> Currency | None:
        found: Currency | None = self._repo.get_by_code(code)
        return found

    def all(self) -> list[Currency]:
        rows: list[Currency] = self._repo.all()
        return rows

    def deactivate(self, code: str, *, actor: UUID) -> Currency:
        _require(actor)
        cur = self._repo.get_by_code(code)
        if cur is None:
            raise NotFoundError(f"Không tìm thấy {code}")
        deactivated: Currency = cur.deactivate()
        if hasattr(self._repo, "update"):
            updated: Currency = self._repo.update(deactivated)
            return updated
        return deactivated

    # ── FX config (LAW flags) ───────────────────────────────────────────
    def get_fx_config(self, company_id: UUID) -> FxCompanyConfig:
        assert self._config_repo is not None
        cfg: FxCompanyConfig | None = self._config_repo.get(company_id)
        if cfg is None:
            cfg = FxCompanyConfig(company_id=company_id)
            self._config_repo.save(cfg)
        return cfg

    def set_base_currency(self, company_id: UUID, new_base: str) -> None:
        """LAW-type: immutable after first use (FlagLocked semantics)."""
        raise BaseCurrencyImmutableError("base_currency là LAW-type; thay đổi chỉ qua migration")


# ═══ Exchange rates + booking resolution (§2.2, §3) ═══════════════════════


class ExchangeRateService:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    def add_rate(
        self,
        *,
        currency_code: str,
        rate_type: Any,
        rate_date: date,
        rate: Decimal,
        source: Any,
        actor: UUID,
        note: str | None = None,
    ) -> Any:
        _require(actor)
        from src.bricks.currencies.domain import ExchangeRate

        try:
            er = ExchangeRate(
                currency_code=currency_code,
                rate_type=rate_type,
                rate_date=rate_date,
                rate=_d(rate),
                source=source,
                actor=actor,
            )
        except InvalidCurrencyCodeError as exc:
            raise InvalidRateError(str(exc)) from exc
        return self._repo.add(er)

    def latest(self, code: str, rate_type: Any, on_date: date) -> Any:
        found: Any = self._repo.latest_on_or_before(code, rate_type, on_date)
        if found is None:
            raise InvalidRateError(f"Không có tỷ giá {code}/{rate_type.value} trước {on_date}")
        return found

    def resolve_booking_rate(
        self,
        *,
        entry_side: BookingRateSide,
        currency: str,
        rate_date: date,
        actual_rate: Decimal | None = None,
        open_balance_provider: Any | None = None,
        company_id: UUID | None = None,
    ) -> Decimal:
        """§3 booking-rate resolution.

        VND is the base — identity rate. Nợ side prefers the actual
        transaction rate; Có side uses weighted average over the open FX
        balance, falling back to last known market rate.
        """
        if currency == DEFAULT_BASE_CURRENCY:
            return Decimal(1)

        if entry_side is BookingRateSide.ACTUAL and actual_rate is not None:
            r = _d(actual_rate)
            if r <= 0:
                raise InvalidRateError("actual_rate must be > 0")
            return r

        if (
            entry_side is BookingRateSide.WEIGHTED_AVG
            and open_balance_provider is not None
            and company_id is not None
        ):
            items = open_balance_provider(company_id, currency)
            tot_orig = sum((o for o, _ in items), Decimal(0))
            if tot_orig > 0:
                wavg = sum((o * rt for o, rt in items), Decimal(0)) / tot_orig
                return wavg.quantize(Decimal("0.0001"))

        return _d(self.latest(currency, RateType.TRANSFER, rate_date).rate)
