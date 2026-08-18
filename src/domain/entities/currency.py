"""Currencies & Exchange Rates domain entities.

Pure Python — no SQLAlchemy, no Flask imports (lint-enforced, D10).
Follows specs-currencies.md §2 and rules-currencies.md (D1-D9).

Money values are Decimal everywhere (specs §8): rates Decimal(18,6),
VND amounts Decimal(18,2). Dates are business dates (rate_date),
timestamps UTC.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from src.domain.entities.base import PostingSide, RateType, RevaluationStatus
from src.domain.exceptions import (
    InvalidCurrencyError,
    InvalidRateError,
    RevaluationError,
)

_CURRENCY_CODE_RE = re.compile(r"^[A-Z]{3}$")

_RATE_TOL = Decimal("0.01")


def _validate_currency_code(code: str) -> str:
    if not _CURRENCY_CODE_RE.match(code):
        raise InvalidCurrencyError(
            f"Currency code '{code}' không hợp lệ. ISO 4217: 3 chữ hoa (VD: USD, EUR)"
        )
    return code


@dataclass(frozen=True)
class Currency:
    """Đơn vị tiền tệ (ISO 4217)."""

    code: str
    name: str
    symbol: str
    decimal_places: int = 2
    is_base: bool = False
    is_active: bool = True
    display_format: str = "{symbol} {amount:,.2f}"

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _validate_currency_code(self.code))
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "symbol", self.symbol.strip())


@dataclass(frozen=True)
class ExchangeRate:
    """Tỷ giá quy đổi ra VND cho 1 đơn vị ngoại tệ.

    Rate valid from rate_date until superseded by a later rate of the same
    (currency_code, rate_type); last available rate ≤ date used for gaps
    (Tryton semantics, specs §3).
    """

    currency_code: str
    rate_date: date
    rate_type: RateType
    rate: Decimal
    source: str  # MANUAL | CSV_IMPORT | NHNN | BANK
    actor: UUID
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "currency_code", _validate_currency_code(self.currency_code))
        if not isinstance(self.rate_type, RateType):
            raise InvalidRateError(f"rate_type '{self.rate_type}' không hợp lệ")
        rate = Decimal(self.rate)
        if rate <= 0:
            raise InvalidRateError("Tỷ giá phải > 0")
        object.__setattr__(self, "rate", rate)
        if not self.source:
            raise InvalidRateError("Thiếu nguồn tỷ giá (source)")
        if self.note:
            object.__setattr__(self, "note", self.note.strip())


@dataclass(frozen=True)
class RevaluationEntry:
    """Một khoản mục tiền tệ trong đợt đánh giá lại cuối kỳ."""

    account_code: str
    currency_code: str
    balance_original: Decimal
    rate_applied: Decimal
    old_vnd: Decimal
    new_vnd: Decimal
    difference: Decimal
    posting_side: PostingSide | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "currency_code", _validate_currency_code(self.currency_code))
        for name in ("balance_original", "rate_applied", "old_vnd", "new_vnd", "difference"):
            object.__setattr__(self, name, Decimal(getattr(self, name)))
        if self.posting_side is not None and not isinstance(self.posting_side, PostingSide):
            object.__setattr__(self, "posting_side", PostingSide(self.posting_side))

    @property
    def is_gain(self) -> bool:
        """Lãi tỷ giá → TK 515 (Có); lỗ → TK 635 (Nợ)."""
        return self.difference > 0


@dataclass
class RevaluationRun:
    """Đợt đánh giá lại cuối kỳ (specs §2.5).

    State machine: DRAFT → PENDING_APPROVAL → APPROVED → POSTED.
    REVERSED from POSTED (re-run reverses prior postings, D7).
    """

    company_id: UUID
    period_start: date
    period_end: date
    rate_date: date
    actor: UUID
    status: RevaluationStatus = RevaluationStatus.DRAFT
    entries: list[RevaluationEntry] = field(default_factory=list)
    id: UUID | None = None
    approver: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    posted_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.period_end < self.period_start:
            raise RevaluationError("period_end trước period_start")

    # ── State machine ────────────────────────────────────────────────────

    def submit_for_approval(self) -> None:
        if self.status != RevaluationStatus.DRAFT:
            raise RevaluationError(
                f"Chỉ DRAFT mới trình duyệt; trạng thái hiện tại {self.status.value}"
            )
        self.status = RevaluationStatus.PENDING_APPROVAL

    def approve(self, approver: UUID) -> None:
        if self.status != RevaluationStatus.PENDING_APPROVAL:
            raise RevaluationError(
                f"Chỉ PENDING_APPROVAL mới được duyệt; trạng thái {self.status.value}"
            )
        self.approver = approver
        self.status = RevaluationStatus.APPROVED

    def post(self) -> None:
        """Post journal entries. Requires APPROVED + balanced (D6, D9)."""
        if self.status != RevaluationStatus.APPROVED:
            raise RevaluationError(f"Chỉ APPROVED mới được đăng sổ; trạng thái {self.status.value}")
        if not self._is_balanced():
            raise RevaluationError(f"Bút toán đánh giá lại không cân bằng: {self._balance_delta()}")
        self.status = RevaluationStatus.POSTED
        self.posted_at = datetime.now(UTC)

    def reverse(self) -> None:
        """Reverse a POSTED run (idempotent re-run path, D7)."""
        if self.status != RevaluationStatus.POSTED:
            raise RevaluationError(f"Chỉ POSTED mới được đảo; trạng thái {self.status.value}")
        self.status = RevaluationStatus.REVERSED

    # ── Balance helpers (D6: tol 0.01) ────────────────────────────────────

    def _balance_delta(self) -> Decimal:
        return sum((e.difference for e in self.entries), Decimal("0"))

    def _is_balanced(self) -> bool:
        return abs(self._balance_delta()) < _RATE_TOL


@dataclass(frozen=True)
class FXDifference:
    """Dòng báo cáo chênh lệch tỷ giá theo tài khoản + ngoại tệ."""

    company_id: UUID
    account_code: str
    currency_code: str
    period_start: date
    period_end: date
    opening_original: Decimal
    opening_vnd: Decimal
    movements_original: Decimal
    movements_vnd: Decimal
    closing_original: Decimal
    closing_vnd: Decimal
    revaluation_adjustment: Decimal
    cumulative_difference: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "currency_code", _validate_currency_code(self.currency_code))
        for name in (
            "opening_original",
            "opening_vnd",
            "movements_original",
            "movements_vnd",
            "closing_original",
            "closing_vnd",
            "revaluation_adjustment",
            "cumulative_difference",
        ):
            object.__setattr__(self, name, Decimal(getattr(self, name)))
