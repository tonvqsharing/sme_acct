"""SQLAlchemy repository adapters for Currencies & Exchange Rates.

Implements the repository ports from application/ports/__init__.py.
Follows SQLAlchemyCompanyRepository pattern (db.session-based, _to_domain
mappers). Rate history is append-only (D3): create inserts, never updates.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select

from src.application.ports import (
    CurrencyRepositoryPort,
    ExchangeRateRepositoryPort,
    RevaluationRepositoryPort,
)
from src.domain.entities.base import RateType, RevaluationStatus
from src.domain.entities.currency import (
    Currency,
    ExchangeRate,
    FXDifference,
    RevaluationEntry,
    RevaluationRun,
)
from src.domain.exceptions import NotFoundError
from src.infrastructure.database import db
from src.infrastructure.database.models import (
    CurrencyModel,
    ExchangeRateModel,
    FXDifferenceModel,
    PostingSideEnum,
    RateTypeEnum,
    RevaluationEntryModel,
    RevaluationRunModel,
    RevaluationStatusEnum,
)


class SQLAlchemyCurrencyRepository(CurrencyRepositoryPort):
    """Maps domain Currency <-> CurrencyModel."""

    def get(self, code: str) -> Currency | None:
        model = db.session.get(CurrencyModel, code)
        return self._to_domain(model) if model else None

    def list_active(self) -> list[Currency]:
        stmt = (
            select(CurrencyModel)
            .where(CurrencyModel.is_active.is_(True))
            .order_by(CurrencyModel.code)
        )
        return [self._to_domain(m) for m in db.session.scalars(stmt).all()]

    def save(self, currency: Currency) -> Currency:
        model = db.session.get(CurrencyModel, currency.code)
        if model is None:
            model = CurrencyModel(code=currency.code)
            db.session.add(model)
        model.name = currency.name
        model.symbol = currency.symbol
        model.decimal_places = currency.decimal_places
        model.is_base = currency.is_base
        model.is_active = currency.is_active
        model.display_format = currency.display_format
        db.session.commit()
        return currency

    def exists(self, code: str) -> bool:
        return db.session.get(CurrencyModel, code) is not None

    @staticmethod
    def _to_domain(model: CurrencyModel) -> Currency:
        return Currency(
            code=model.code,
            name=model.name,
            symbol=model.symbol,
            decimal_places=model.decimal_places,
            is_base=model.is_base,
            is_active=model.is_active,
            display_format=model.display_format,
        )


class SQLAlchemyExchangeRateRepository(ExchangeRateRepositoryPort):
    """Maps domain ExchangeRate <-> ExchangeRateModel (append-only)."""

    def create(self, rate: ExchangeRate) -> ExchangeRate:
        model = ExchangeRateModel(
            currency_code=rate.currency_code,
            rate_date=rate.rate_date,
            rate_type=RateTypeEnum(rate.rate_type.value),
            rate=rate.rate,
            source=rate.source,
            actor_id=rate.actor,
            note=rate.note,
        )
        db.session.add(model)
        db.session.commit()
        return rate

    def get_latest(
        self, currency_code: str, rate_type: RateType, rate_date: date
    ) -> ExchangeRate | None:
        stmt = (
            select(ExchangeRateModel)
            .where(ExchangeRateModel.currency_code == currency_code)
            .where(ExchangeRateModel.rate_type == RateTypeEnum(rate_type.value))
            .where(ExchangeRateModel.rate_date <= rate_date)
            .order_by(ExchangeRateModel.rate_date.desc(), ExchangeRateModel.created_at.desc())
            .limit(1)
        )
        model = db.session.scalars(stmt).first()
        return self._to_domain(model) if model else None

    def list_history(
        self,
        currency_code: str | None,
        rate_type: RateType | None,
        from_date: date | None,
        to_date: date | None,
    ) -> list[ExchangeRate]:
        stmt = select(ExchangeRateModel)
        if currency_code:
            stmt = stmt.where(ExchangeRateModel.currency_code == currency_code)
        if rate_type:
            stmt = stmt.where(ExchangeRateModel.rate_type == RateTypeEnum(rate_type.value))
        if from_date:
            stmt = stmt.where(ExchangeRateModel.rate_date >= from_date)
        if to_date:
            stmt = stmt.where(ExchangeRateModel.rate_date <= to_date)
        stmt = stmt.order_by(
            ExchangeRateModel.rate_date.desc(), ExchangeRateModel.created_at.desc()
        )
        return [self._to_domain(m) for m in db.session.scalars(stmt).all()]

    def rate_is_referenced(self, rate_id: UUID) -> bool:
        # v1: revaluation entries reference rate_applied (denormalized),
        # so a rate row cannot be "un-referenced"; source-level immutability
        # (D3) is guaranteed by append-only design. Reserved for future
        # transaction-level references (voucher lines).
        return False

    @staticmethod
    def _to_domain(model: ExchangeRateModel) -> ExchangeRate:
        return ExchangeRate(
            currency_code=model.currency_code,
            rate_date=model.rate_date,
            rate_type=RateType(model.rate_type.value),
            rate=model.rate,
            source=model.source,
            actor=model.actor_id,
            created_at=model.created_at,
            note=model.note,
        )


class SQLAlchemyRevaluationRepository(RevaluationRepositoryPort):
    """Maps domain RevaluationRun/Entry/FXDifference <-> models."""

    def create_run(self, run: RevaluationRun) -> RevaluationRun:
        model = self._to_model(run)
        db.session.add(model)
        db.session.commit()
        run.id = model.id
        return run

    def save_run(self, run: RevaluationRun) -> RevaluationRun:
        model = db.session.get(RevaluationRunModel, run.id)
        if model is None:
            raise NotFoundError(f"Revaluation run {run.id} not found")
        model.status = RevaluationStatusEnum(run.status.value)
        model.approver_id = run.approver
        model.posted_at = run.posted_at
        # Replace entries (cascade delete-orphan)
        model.entries.clear()
        for entry in run.entries:
            model.entries.append(self._entry_to_model(entry))
        db.session.commit()
        return run

    def get_run(self, run_id: UUID) -> RevaluationRun | None:
        model = db.session.get(RevaluationRunModel, run_id)
        return self._to_domain(model) if model else None

    def get_posted_run(
        self, company_id: UUID, period_start: date, period_end: date
    ) -> RevaluationRun | None:
        stmt = (
            select(RevaluationRunModel)
            .where(RevaluationRunModel.company_id == company_id)
            .where(RevaluationRunModel.period_start == period_start)
            .where(RevaluationRunModel.period_end == period_end)
            .where(RevaluationRunModel.status == RevaluationStatusEnum.POSTED)
            .order_by(RevaluationRunModel.created_at.desc())
            .limit(1)
        )
        model = db.session.scalars(stmt).first()
        return self._to_domain(model) if model else None

    def period_is_locked(self, company_id: UUID, period_start: date, period_end: date) -> bool:
        from src.infrastructure.database.models import PeriodLockModel

        stmt = (
            select(PeriodLockModel)
            .where(PeriodLockModel.company_id == company_id)
            .where(PeriodLockModel.is_locked.is_(True))
            .where(PeriodLockModel.period_start <= period_end)
            .where(PeriodLockModel.period_end >= period_start)
        )
        return db.session.scalars(stmt).first() is not None

    def list_fx_differences(
        self, company_id: UUID, period_start: date, period_end: date
    ) -> list[FXDifference]:
        stmt = (
            select(FXDifferenceModel)
            .where(FXDifferenceModel.company_id == company_id)
            .where(FXDifferenceModel.period_start == period_start)
            .where(FXDifferenceModel.period_end == period_end)
            .order_by(FXDifferenceModel.account_code, FXDifferenceModel.currency_code)
        )
        return [self._fx_to_domain(m) for m in db.session.scalars(stmt).all()]

    # ── Mappers ───────────────────────────────────────────────────────────

    def _to_model(self, run: RevaluationRun) -> RevaluationRunModel:
        model = RevaluationRunModel(
            company_id=run.company_id,
            period_start=run.period_start,
            period_end=run.period_end,
            rate_date=run.rate_date,
            status=RevaluationStatusEnum(run.status.value),
            actor_id=run.actor,
            approver_id=run.approver,
            posted_at=run.posted_at,
        )
        for entry in run.entries:
            model.entries.append(self._entry_to_model(entry))
        return model

    @staticmethod
    def _entry_to_model(entry: RevaluationEntry) -> RevaluationEntryModel:
        return RevaluationEntryModel(
            account_code=entry.account_code,
            currency_code=entry.currency_code,
            balance_original=entry.balance_original,
            rate_applied=entry.rate_applied,
            old_vnd=entry.old_vnd,
            new_vnd=entry.new_vnd,
            difference=entry.difference,
            posting_side=PostingSideEnum(entry.posting_side.value) if entry.posting_side else None,
        )

    def _to_domain(self, model: RevaluationRunModel) -> RevaluationRun | None:
        if model is None:
            return None
        from src.domain.entities.base import PostingSide

        entries = []
        for em in model.entries:
            entries.append(
                RevaluationEntry(
                    account_code=em.account_code,
                    currency_code=em.currency_code,
                    balance_original=em.balance_original,
                    rate_applied=em.rate_applied,
                    old_vnd=em.old_vnd,
                    new_vnd=em.new_vnd,
                    difference=em.difference,
                    posting_side=PostingSide(em.posting_side.value) if em.posting_side else None,
                )
            )
        return RevaluationRun(
            id=model.id,
            company_id=model.company_id,
            period_start=model.period_start,
            period_end=model.period_end,
            rate_date=model.rate_date,
            status=RevaluationStatus(model.status.value),
            entries=entries,
            actor=model.actor_id,
            approver=model.approver_id,
            created_at=model.created_at,
            posted_at=model.posted_at,
        )

    @staticmethod
    def _fx_to_domain(model: FXDifferenceModel) -> FXDifference:
        return FXDifference(
            company_id=model.company_id,
            account_code=model.account_code,
            currency_code=model.currency_code,
            period_start=model.period_start,
            period_end=model.period_end,
            opening_original=model.opening_original,
            opening_vnd=model.opening_vnd,
            movements_original=model.movements_original,
            movements_vnd=model.movements_vnd,
            closing_original=model.closing_original,
            closing_vnd=model.closing_vnd,
            revaluation_adjustment=model.revaluation_adjustment,
            cumulative_difference=model.cumulative_difference,
        )
