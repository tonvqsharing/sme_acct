"""Period lock service — accounting period enforcement (specs §3, R-01..R-10).

Ports injected (no Flask/SQLAlchemy). Handles: lazy fiscal-year auto-seed,
quarter-aligned FY creation, period close/reopen with SOD, year-end close.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from src.application.ports import FiscalYearRepositoryPort, PeriodLockRepositoryPort
from src.domain.entities.base import AccountingPeriodType, PeriodStatus
from src.domain.entities.fiscal_year import (
    _ANCHOR_START,
    FiscalYear,
    PeriodLockEvent,
)
from src.domain.exceptions import (
    FiscalYearExistsError,
    InvalidFiscalYearError,
    NotFoundError,
    PeriodLockedError,
    PeriodTransitionError,
    SelfApprovalError,
    YearEndPreconditionsError,
)


class PeriodLockService:
    """Enforces period lock + fiscal year lifecycle rules.

    Replaces the v1 stub (is_locked always False). Now backed by
    accounting_periods.status (dual-written to legacy period_locks by the
    adapter so the currencies D8 path keeps working).
    """

    def __init__(
        self,
        fy_repo: FiscalYearRepositoryPort,
        lock_repo: PeriodLockRepositoryPort,
    ) -> None:
        self._fy_repo = fy_repo
        self._lock_repo = lock_repo

    # ── Fiscal year lifecycle ───────────────────────────────────────────────

    def ensure_fiscal_year(self, company_id: UUID, entry_date: date) -> FiscalYear:
        """Idempotent auto-seed: return FY containing entry_date, create a
        default calendar FY (starting 01/01) if none exists."""
        existing = self._fy_repo.get_active(company_id, entry_date)
        if existing is not None:
            return existing
        fy = FiscalYear(
            company_id=company_id,
            period_type=AccountingPeriodType.CALENDAR,
            start_date=date(entry_date.year, 1, 1),
        )
        return self._fy_repo.save(fy)

    def create_fiscal_year(
        self,
        company_id: UUID,
        period_type: AccountingPeriodType,
        start_date: date,
        actor: UUID,
    ) -> FiscalYear:
        """Create a new fiscal year — quarter-aligned start (R-01), no
        overlap with existing years (R-03)."""
        anchor_month = _ANCHOR_START[period_type][0]
        if start_date.day != 1 or start_date.month != anchor_month:
            raise InvalidFiscalYearError(
                f"Năm tài chính phải bắt đầu {anchor_month:02d}/01 (Luật 88/2015 Đ12)"
            )

        fy = FiscalYear(
            company_id=company_id,
            period_type=period_type,
            start_date=start_date,
        )
        for existing in self._fy_repo.list_by_company(company_id):
            if not (fy.end_date < existing.start_date or fy.start_date > existing.end_date):
                raise FiscalYearExistsError(
                    f"Năm tài chính {fy.year_code} trùng khoảng thời gian với năm tài chính hiện có"
                )
        return self._fy_repo.save(fy)

    def close_fiscal_year(self, company_id: UUID, fy_id: UUID, actor: UUID) -> FiscalYear:
        """Close fiscal year: all periods must be LOCKED (R-10). Marks
        YEAR_CLOSED, posts opening-balance flag for the next year."""
        fy = self._fy_repo.get_by_id(fy_id)
        if fy is None or fy.company_id != company_id:
            raise NotFoundError(f"Năm tài chính {fy_id} không tồn tại")
        if fy.status == PeriodStatus.YEAR_CLOSED:
            raise PeriodTransitionError(f"Năm tài chính {fy.year_code} đã đóng sổ")
        if not fy.all_periods_locked():
            open_periods = [p.label for p in fy.periods if p.status == PeriodStatus.OPEN]
            raise YearEndPreconditionsError(
                f"Không thể đóng năm: các kỳ còn mở {open_periods}; khóa toàn bộ kỳ trước"
            )

        for p in fy.periods:
            p.close_fiscal_year()
        fy.status = PeriodStatus.YEAR_CLOSED
        fy.opening_balance_posted = True
        fy.closed_by = actor
        fy.closed_at = datetime.now(UTC)
        return self._fy_repo.save(fy)

    # ── Period lock enforcement ─────────────────────────────────────────────

    def is_locked(self, company_id: UUID, entry_date: date) -> bool:
        return self._lock_repo.is_locked(company_id, entry_date)

    def validate_before_entry(self, company_id: UUID, entry_date: date) -> None:
        """Raise PeriodLockedError when posting into a locked period (D8)."""
        if self._lock_repo.is_locked(company_id, entry_date):
            raise PeriodLockedError(f"Kỳ kế toán chứa {entry_date} đang khóa; không thể ghi sổ")

    def close_period(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent:
        """OPEN → LOCKED (R-06).

        State guard via domain transition first (rejects double-lock and any
        attempt to re-lock a YEAR_CLOSED period — the latter would silently
        downgrade a closed year), then delegate persistence.
        """
        period = self._lock_repo.get_period(period_id)
        if period is None:
            raise NotFoundError(f"Kỳ kế toán {period_id} không tồn tại")
        period.close(actor=actor, reason=reason)
        return self._lock_repo.lock(period_id, actor=actor, reason=reason)

    def reopen_period(self, period_id: UUID, actor: UUID, reason: str) -> PeriodLockEvent:
        """LOCKED → OPEN (R-06, UC-06): reason required, self-approval blocked.

        State guard via domain transition first (rejects re-open of an OPEN or
        YEAR_CLOSED period), then delegate persistence.
        """
        period = self._lock_repo.get_period(period_id)
        if period is None:
            raise NotFoundError(f"Kỳ kế toán {period_id} không tồn tại")
        if not reason or not reason.strip():
            raise PeriodTransitionError("Lý do mở khóa kỳ kế toán là bắt buộc")
        if period.locked_by == actor:
            raise SelfApprovalError("Người khóa kỳ không được tự mở khóa; cần người khác duyệt")
        period.reopen(actor=actor, reason=reason)
        return self._lock_repo.reopen(period_id, actor=actor, reason=reason)
