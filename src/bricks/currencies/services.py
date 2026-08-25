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
    RevaluationEntry,
    RevaluationRun,
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


# ═══ Revaluation engine (§4) ══════════════════════════════════════════════


class PeriodLockedError(Exception):
    pass


class SodViolationError(Exception):
    pass


class UnknownRateError(Exception):
    pass


class EmptyRunError(Exception):
    code = "EMPTY_RUN"


class _ClosingRates:
    def __init__(self, rate_svc: Any, on_date: date) -> None:
        self._svc = rate_svc
        self._on = on_date
        self._cache: dict[str, Decimal] = {}

    def get(self, code: str) -> Decimal:
        if code not in self._cache:
            r = self._svc.latest(code, RateType.TRANSFER, self._on)
            self._cache[code] = r.rate
        return self._cache[code]


class RevaluationService:
    def __init__(
        self,
        *,
        rates: Any,
        repo: Any,
        monetary_items: Any,
        period_locked: Any,
        audit: Any | None = None,
    ) -> None:
        self._rates = rates
        self._repo = repo
        self._items = monetary_items
        self._locked = period_locked
        self._audit = audit

    def _get(self, rid: UUID) -> Any:
        getter = getattr(self._repo, "get_by_id", None) or self._repo.rows_get
        return getter(rid)

    def create_run(
        self,
        company_id: UUID,
        period_start: date,
        period_end: date,
        rate_date: date,
        *,
        actor: UUID,
    ) -> Any:
        if self._locked(company_id):
            raise PeriodLockedError("Kỳ đã khóa")
        closing = _ClosingRates(self._rates, rate_date)
        entries: list[RevaluationEntry] = []
        for item in self._items(company_id):
            code = item["currency_code"]
            orig = Decimal(str(item["balance_original"]))
            old = Decimal(str(item["old_vnd"]))
            try:
                applied = closing.get(code)
            except InvalidRateError as exc:
                raise UnknownRateError(code) from exc
            new_vnd = (orig * applied).quantize(Decimal(1))
            entries.append(
                RevaluationEntry(
                    account_code=item["account_code"],
                    currency_code=code,
                    balance_original=orig,
                    rate_applied=applied,
                    old_vnd=old,
                    new_vnd=new_vnd,
                )
            )
        if not entries:
            raise EmptyRunError("Không có khoản mục ngoại tệ")

        # idempotent re-run: reverse prior POSTED overlap first
        prior = self._repo.find_posted_overlap(company_id, period_start, period_end)
        reversal_entries: list[Any] = []
        if prior is not None:
            reversal_entries = prior.reverse()
            self._repo.update(prior)

        run = RevaluationRun(
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            rate_date=rate_date,
            entries=entries,
            reversal_entries=reversal_entries,
            actor=actor,
        )
        run.stamp(run.checksum or "0" * 64, actor, "CREATE")
        return self._repo.create(run)

    def get(self, rid: UUID) -> Any:
        return self._repo.get_by_id(rid) if hasattr(self._repo, "get_by_id") else None

    def submit_for_approval(self, rid: UUID, actor: UUID) -> Any:
        run = self._get(rid)
        run.submit()
        run.stamp(run.checksum, actor, "SUBMIT")
        return self._repo.update(run)

    def approve(self, rid: UUID, approver: UUID) -> Any:
        run = self._get(rid)
        if approver == run.actor:
            raise SodViolationError("Người lập không được tự phê duyệt")
        run.approve(approver)
        run.stamp(run.checksum, approver, "APPROVE")
        return self._repo.update(run)

    def post(self, rid: UUID, actor: UUID) -> Any:
        run = self._get(rid)
        run.post(actor)
        run.stamp(run.checksum, actor, "POST")
        saved = self._repo.update(run)
        if self._audit is not None:
            pass
        return saved
