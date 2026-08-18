"""SQLAlchemy adapters — fiscal years + period locks (specs §4.1, R-08).

Dual-write bridge: period locks write BOTH accounting_periods.status
(new truth) AND legacy period_locks rows (keeps currencies D8
RevaluationRepositoryPort.period_is_locked path green without touching
currency_repo.py).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import delete, select

from src.application.ports import (
    FiscalYearRepositoryPort,
    PeriodLockRepositoryPort,
)
from src.domain.entities.base import AccountingPeriodType, PeriodLockAction, PeriodStatus
from src.domain.entities.fiscal_year import AccountingPeriod, FiscalYear, PeriodLockEvent
from src.infrastructure.database import db
from src.infrastructure.database.models import (
    AccountingPeriodModel,
    AccountingPeriodTypeEnum,
    FiscalYearModel,
    PeriodLockActionEnum,
    PeriodLockEventModel,
    PeriodLockModel,
    PeriodStatusEnum,
)


def _to_domain_type(model_type) -> AccountingPeriodType:
    return AccountingPeriodType(model_type.value)


def _to_model_type(domain_type: AccountingPeriodType) -> AccountingPeriodTypeEnum:
    return AccountingPeriodTypeEnum(domain_type.value)


def _to_domain_status(model_status) -> PeriodStatus:
    return PeriodStatus(model_status.value)


def _to_model_status(domain_status: PeriodStatus) -> PeriodStatusEnum:
    return PeriodStatusEnum(domain_status.value)


def _period_model_to_domain(m: AccountingPeriodModel) -> AccountingPeriod:
    return AccountingPeriod(
        id=m.id,
        fiscal_year_id=m.fiscal_year_id,
        period_number=m.period_number,
        label=m.label,
        start_date=m.start_date,
        end_date=m.end_date,
        status=_to_domain_status(m.status),
        locked_by=m.locked_by,
        locked_at=m.locked_at,
        lock_reason=m.lock_reason,
    )


def _fy_model_to_domain(m: FiscalYearModel) -> FiscalYear:
    return FiscalYear(
        id=m.id,
        company_id=m.company_id,
        year_code=m.year_code,
        period_type=_to_domain_type(m.period_type),
        start_date=m.start_date,
        end_date=m.end_date,
        status=_to_domain_status(m.status),
        is_first_period=m.is_first_period,
        opening_balance_posted=m.opening_balance_posted,
        closed_at=m.closed_at,
        closed_by=m.closed_by,
        periods=[_period_model_to_domain(p) for p in sorted(m.periods, key=lambda p: p.period_number)],
    )


def _event_model_to_domain(m: PeriodLockEventModel) -> PeriodLockEvent:
    return PeriodLockEvent(
        id=m.id,
        period_id=m.period_id,
        action=PeriodLockAction(m.action.value),
        requested_by=m.requested_by,
        approved_by=m.approved_by,
        requested_at=m.requested_at,
        approved_at=m.approved_at,
        reason=m.reason,
        prev_checksum=m.prev_checksum,
        checksum=m.checksum,
    )


def _chain_checksum(
    prev: str | None,
    period_id: UUID,
    action: PeriodLockAction,
    actor: UUID,
    reason: str,
    ts: datetime,
) -> str:
    raw = "|".join(
        [prev or "", str(period_id), action.value, str(actor), reason, ts.isoformat()]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SQLAlchemyFiscalYearRepository(FiscalYearRepositoryPort):
    def save(self, fiscal_year: FiscalYear) -> FiscalYear:
        if fiscal_year.id is None:
            raise ValueError("FiscalYear.id must be set before save")
        model = db.session.get(FiscalYearModel, fiscal_year.id)
        if model is None:
            model = FiscalYearModel(id=fiscal_year.id)
            db.session.add(model)
        model.company_id = fiscal_year.company_id
        model.year_code = fiscal_year.year_code
        model.period_type = _to_model_type(fiscal_year.period_type)
        model.start_date = fiscal_year.start_date
        model.end_date = fiscal_year.end_date
        model.is_first_period = fiscal_year.is_first_period
        model.status = _to_model_status(fiscal_year.status)
        model.opening_balance_posted = fiscal_year.opening_balance_posted
        model.closed_at = fiscal_year.closed_at
        model.closed_by = fiscal_year.closed_by

        # Periods matched by period_number and updated in place — no
        # delete/reinsert (identity-map PK churn breaks relationships).
        existing = {p.period_number: p for p in model.periods}
        for dom in fiscal_year.periods:
            pm = existing.get(dom.period_number)
            if pm is None:
                pm = AccountingPeriodModel(
                    id=dom.id,
                    fiscal_year_id=model.id,
                    period_number=dom.period_number,
                )
                model.periods.append(pm)
            pm.label = dom.label
            pm.start_date = dom.start_date
            pm.end_date = dom.end_date
            pm.status = _to_model_status(dom.status)
            pm.locked_by = dom.locked_by
            pm.locked_at = dom.locked_at
            pm.lock_reason = dom.lock_reason

        db.session.flush()
        return _fy_model_to_domain(model)

    def get_active(self, company_id: UUID, entry_date: date) -> FiscalYear | None:
        stmt = (
            select(FiscalYearModel)
            .where(
                FiscalYearModel.company_id == company_id,
                FiscalYearModel.start_date <= entry_date,
                FiscalYearModel.end_date >= entry_date,
            )
            .order_by(FiscalYearModel.start_date.desc())
            .limit(1)
        )
        model = db.session.scalar(stmt)
        return _fy_model_to_domain(model) if model is not None else None

    def get_by_id(self, fiscal_year_id: UUID) -> FiscalYear | None:
        model = db.session.get(FiscalYearModel, fiscal_year_id)
        return _fy_model_to_domain(model) if model is not None else None

    def list_by_company(self, company_id: UUID) -> list[FiscalYear]:
        stmt = (
            select(FiscalYearModel)
            .where(FiscalYearModel.company_id == company_id)
            .order_by(FiscalYearModel.start_date)
        )
        return [_fy_model_to_domain(m) for m in db.session.scalars(stmt)]


class SQLAlchemyPeriodLockRepository(PeriodLockRepositoryPort):
    def get_period(self, period_id: UUID) -> AccountingPeriod | None:
        model = db.session.get(AccountingPeriodModel, period_id)
        return _period_model_to_domain(model) if model is not None else None

    def find_period(self, company_id: UUID, entry_date: date) -> AccountingPeriod | None:
        stmt = (
            select(AccountingPeriodModel)
            .join(FiscalYearModel, AccountingPeriodModel.fiscal_year_id == FiscalYearModel.id)
            .where(
                FiscalYearModel.company_id == company_id,
                AccountingPeriodModel.start_date <= entry_date,
                AccountingPeriodModel.end_date >= entry_date,
            )
            .order_by(AccountingPeriodModel.start_date.desc())
            .limit(1)
        )
        model = db.session.scalar(stmt)
        return _period_model_to_domain(model) if model is not None else None

    def is_locked(self, company_id: UUID, entry_date: date) -> bool:
        stmt = (
            select(AccountingPeriodModel.status)
            .join(FiscalYearModel, AccountingPeriodModel.fiscal_year_id == FiscalYearModel.id)
            .where(
                FiscalYearModel.company_id == company_id,
                AccountingPeriodModel.start_date <= entry_date,
                AccountingPeriodModel.end_date >= entry_date,
            )
        )
        status = db.session.scalar(stmt)
        return status is not None and status != PeriodStatusEnum.OPEN

    def lock(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent:
        period = db.session.get(AccountingPeriodModel, period_id)
        if period is None:
            raise KeyError(f"period not found: {period_id}")
        now = datetime.now(UTC)
        period.status = PeriodStatusEnum.LOCKED
        period.locked_by = actor
        period.locked_at = now
        period.lock_reason = reason

        event = self._append_event(period_id, PeriodLockAction.CLOSE, actor, reason, now)
        self._write_legacy_lock(period, actor, reason, now)
        db.session.flush()
        return event

    def reopen(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent:
        period = db.session.get(AccountingPeriodModel, period_id)
        if period is None:
            raise KeyError(f"period not found: {period_id}")
        if period.status == PeriodStatusEnum.YEAR_CLOSED:
            raise ValueError("year-closed period cannot be reopened")
        now = datetime.now(UTC)
        period.status = PeriodStatusEnum.OPEN
        period.locked_by = None
        period.locked_at = None
        period.lock_reason = None

        event = self._append_event(period_id, PeriodLockAction.REOPEN, actor, reason, now)
        self._clear_legacy_lock(period, now)
        db.session.flush()
        return event

    def history(self, period_id: UUID) -> list[PeriodLockEvent]:
        stmt = (
            select(PeriodLockEventModel)
            .where(PeriodLockEventModel.period_id == period_id)
            .order_by(PeriodLockEventModel.requested_at, PeriodLockEventModel.id)
        )
        return [_event_model_to_domain(m) for m in db.session.scalars(stmt)]

    # ── internals ──────────────────────────────────────────────────────────

    def _append_event(
        self,
        period_id: UUID,
        action: PeriodLockAction,
        actor: UUID,
        reason: str,
        now: datetime,
    ) -> PeriodLockEvent:
        last = db.session.scalar(
            select(PeriodLockEventModel)
            .where(PeriodLockEventModel.period_id == period_id)
            .order_by(PeriodLockEventModel.requested_at.desc(), PeriodLockEventModel.id.desc())
            .limit(1)
        )
        prev = last.checksum if last is not None else None
        checksum = _chain_checksum(prev, period_id, action, actor, reason, now)
        model = PeriodLockEventModel(
            period_id=period_id,
            action=PeriodLockActionEnum(action.value),
            requested_by=actor,
            requested_at=now,
            reason=reason,
            prev_checksum=prev,
            checksum=checksum,
        )
        db.session.add(model)
        return _event_model_to_domain(model)

    def _write_legacy_lock(
        self, period: AccountingPeriodModel, actor: UUID, reason: str, now: datetime
    ) -> None:
        fy = db.session.get(FiscalYearModel, period.fiscal_year_id)
        legacy = db.session.scalar(
            select(PeriodLockModel).where(
                PeriodLockModel.company_id == fy.company_id,
                PeriodLockModel.period_start == period.start_date,
                PeriodLockModel.period_end == period.end_date,
            )
        )
        if legacy is None:
            legacy = PeriodLockModel(
                company_id=fy.company_id,
                period_start=period.start_date,
                period_end=period.end_date,
            )
            db.session.add(legacy)
        legacy.is_locked = True
        legacy.locked_at = now.date()
        legacy.locked_by_id = actor
        legacy.reason = reason

    def _clear_legacy_lock(self, period: AccountingPeriodModel, now: datetime) -> None:
        fy = db.session.get(FiscalYearModel, period.fiscal_year_id)
        db.session.execute(
            delete(PeriodLockModel).where(
                PeriodLockModel.company_id == fy.company_id,
                PeriodLockModel.period_start >= period.start_date,
                PeriodLockModel.period_end <= period.end_date,
                PeriodLockModel.is_locked.is_(True),
            )
        )