"""Fiscal year / accounting period domain entities (specs-fiscal-year-period.md §2.2).

Pure Python — no sqlalchemy / web imports (domain rule).
Legal basis: Luật Kế toán 88/2015 Điều 12 (quarter-aligned start, 12-month
fiscal year, ≤15-month first period), rules R-01..R-03, R-08, R-10.
"""

from __future__ import annotations

import calendar as _cal
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from src.domain.entities.base import AccountingPeriodType, PeriodLockAction, PeriodStatus
from src.domain.exceptions import InvalidFiscalYearError, PeriodTransitionError

# ── Legal anchors (Luật 88/2015 Đ12 — R-01) ────────────────────────────────
_ANCHOR_START: dict[AccountingPeriodType, tuple[int, int]] = {
    AccountingPeriodType.CALENDAR: (1, 1),
    AccountingPeriodType.FISCAL_APR: (4, 1),
    AccountingPeriodType.FISCAL_JUL: (7, 1),
    AccountingPeriodType.FISCAL_OCT: (10, 1),
}

_ANCHOR_END: dict[AccountingPeriodType, tuple[int, int]] = {
    AccountingPeriodType.CALENDAR: (12, 31),
    AccountingPeriodType.FISCAL_APR: (3, 31),
    AccountingPeriodType.FISCAL_JUL: (6, 30),
    AccountingPeriodType.FISCAL_OCT: (9, 30),
}

MAX_FIRST_PERIOD_MONTHS = 15  # Luật 88/2015 Đ12


def _add_months(d: date, months: int) -> date:
    """Add months, clamping day to month length (31/01 + 1mo = 28 or 29/02)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, _cal.monthrange(year, month)[1])
    return date(year, month, day)


def _month_end(d: date) -> date:
    return date(d.year, d.month, _cal.monthrange(d.year, d.month)[1])


def _anchor_end_date(period_type: AccountingPeriodType, year: int) -> date:
    month, day = _ANCHOR_END[period_type]
    return date(year, month, day)


@dataclass
class AccountingPeriod:
    """Một kỳ kế toán (tháng) trong năm tài chính."""

    fiscal_year_id: UUID
    period_number: int
    label: str
    start_date: date
    end_date: date
    status: PeriodStatus = PeriodStatus.OPEN
    locked_by: UUID | None = None
    locked_at: datetime | None = None
    lock_reason: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise PeriodTransitionError(f"Kỳ kế toán {self.label} kết thúc trước khi bắt đầu")

    def contains(self, d: date) -> bool:
        """Boundary dates inclusive (U-16)."""
        return self.start_date <= d <= self.end_date

    def close(self, actor: UUID, reason: str) -> None:
        """OPEN → LOCKED (R-06)."""
        if self.status != PeriodStatus.OPEN:
            raise PeriodTransitionError(
                f"Kỳ {self.label} trạng thái {self.status.value}; chỉ kỳ OPEN mới khóa được"
            )
        self.status = PeriodStatus.LOCKED
        self.locked_by = actor
        self.locked_at = datetime.now(UTC)
        self.lock_reason = reason

    def reopen(self, actor: UUID, reason: str) -> None:
        """LOCKED → OPEN; requires justification (R-06, UC-06)."""
        if self.status != PeriodStatus.LOCKED:
            raise PeriodTransitionError(
                f"Kỳ {self.label} trạng thái {self.status.value}; chỉ kỳ LOCKED mở lại được"
            )
        if not reason or not reason.strip():
            raise PeriodTransitionError("Lý do mở khóa kỳ kế toán là bắt buộc")
        self.status = PeriodStatus.OPEN
        self.locked_by = None
        self.locked_at = None
        self.lock_reason = reason

    def close_fiscal_year(self) -> None:
        """LOCKED → YEAR_CLOSED (workflows §1: OPEN→YEAR_CLOSED bị chặn)."""
        if self.status != PeriodStatus.LOCKED:
            raise PeriodTransitionError(
                f"Kỳ {self.label} phải LOCKED trước khi đóng năm (trạng thái {self.status.value})"
            )
        self.status = PeriodStatus.YEAR_CLOSED


@dataclass
class FiscalYear:
    """Năm tài chính — aggregate root (specs §2.2).

    Normal fiscal year: exactly 12 months, quarter-aligned start (R-01/R-02).
    First period of a new company: ≤ 15 months, end at anchor (R-02, FR-02).
    """

    company_id: UUID
    period_type: AccountingPeriodType
    start_date: date
    is_first_period: bool = False
    end_date: date | None = None  # required for first period
    year_code: str | None = None
    status: PeriodStatus = PeriodStatus.OPEN
    opening_balance_posted: bool = False
    closed_by: UUID | None = None
    closed_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)
    periods: list[AccountingPeriod] = field(default_factory=list)

    def __post_init__(self) -> None:
        start, end = self._resolve_bounds()
        self.start_date, self.end_date = start, end
        if self.year_code is None:
            self.year_code = str(self.start_date.year)
        if not self.periods:
            self._build_periods(start, end)

    @property
    def label(self) -> str:
        return (
            "Kỳ kế toán đầu tiên"
            if self.is_first_period
            else f"Năm tài chính {self.start_date} – {self.end_date}"
        )

    # ── Validation (R-01, R-02) ──────────────────────────────────────────

    def _resolve_bounds(self) -> tuple[date, date]:
        if self.is_first_period:
            if self.end_date is None:
                raise InvalidFiscalYearError(
                    "Kỳ kế toán đầu tiên phải khai end_date (kết thúc tại mốc cuối năm tài chính)"
                )
            anchor_end = _anchor_end_date(self.period_type, self.end_date.year)
            if self.end_date != anchor_end:
                raise InvalidFiscalYearError(
                    f"Kỳ kế toán đầu tiên phải kết thúc {anchor_end} (mốc cuối của loại năm {self.period_type.value})"
                )
            max_end = _add_months(self.start_date, MAX_FIRST_PERIOD_MONTHS)
            if self.end_date > max_end:
                raise InvalidFiscalYearError(
                    f"Kỳ kế toán đầu tiên tối đa {MAX_FIRST_PERIOD_MONTHS} tháng "
                    f"(Luật 88/2015 Đ12); từ {self.start_date} chỉ đến {max_end}"
                )
            return self.start_date, self.end_date
        expected_start = _ANCHOR_START[self.period_type]
        if (self.start_date.month, self.start_date.day) != expected_start:
            raise InvalidFiscalYearError(
                f"Năm tài chính phải bắt đầu từ đầu tháng đầu quý: "
                f"{expected_start[0]:02d}/{expected_start[1]:02d} (Luật Kế toán 88/2015 Điều 12, R-01)"
            )
        end = _add_months(self.start_date, 12) - timedelta(days=1)
        return self.start_date, end

    # ── Period generation (R-03: contiguous, non-overlapping) ────────────

    def _build_periods(self, start: date, end: date) -> None:
        periods: list[AccountingPeriod] = []
        number = 1
        cursor = start

        if cursor.day != 1:
            # Partial first month (registration mid-month)
            periods.append(
                AccountingPeriod(
                    fiscal_year_id=self.id,
                    period_number=number,
                    label=f"Tháng {cursor.month:02d}/{cursor.year}",
                    start_date=cursor,
                    end_date=_month_end(cursor),
                )
            )
            number += 1
            cursor = _add_months(_month_end(cursor), 1)

        while cursor <= end:
            period_end = _month_end(cursor)
            if period_end > end:
                period_end = end
            periods.append(
                AccountingPeriod(
                    fiscal_year_id=self.id,
                    period_number=number,
                    label=f"Tháng {cursor.month:02d}/{cursor.year}",
                    start_date=cursor,
                    end_date=period_end,
                )
            )
            number += 1
            cursor = _add_months(cursor, 1)

        self.periods = periods

    # ── Queries ──────────────────────────────────────────────────────────

    def period_for_date(self, d: date) -> AccountingPeriod | None:
        return next((p for p in self.periods if p.contains(d)), None)

    def is_locked(self, d: date) -> bool:
        """R-04: entry_date inside non-OPEN period → locked."""
        period = self.period_for_date(d)
        return period is not None and period.status != PeriodStatus.OPEN

    def all_periods_locked(self) -> bool:
        return len(self.periods) > 0 and all(p.status != PeriodStatus.OPEN for p in self.periods)


@dataclass
class PeriodLockEvent:
    """Append-only khóa/mở khóa event (period_lock_events, R-08/F-08).

    Checksum chain (SHA-256) mirrors audit-log module — tamper-evident.
    """

    period_id: UUID
    action: PeriodLockAction
    requested_by: UUID
    reason: str
    requested_at: datetime
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    prev_checksum: str | None = None
    checksum: str | None = None
    id: UUID = field(default_factory=uuid4)
