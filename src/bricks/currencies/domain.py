"""Currencies domain — Currency master + FX config flags. Pure Python."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

ISO4217_RE = re.compile(r"^[A-Z]{3}$")


class InvalidCurrencyCodeError(ValueError):
    pass


class InvalidRateError(ValueError):
    code = "INVALID_RATE"


class BookingRateSide(Enum):
    """§3: Nợ = actual transaction rate; Có = weighted average."""

    ACTUAL = "ACTUAL"
    WEIGHTED_AVG = "WEIGHTED_AVG"


class FxRateSource(Enum):
    MANUAL = "MANUAL"
    CSV_IMPORT = "CSV_IMPORT"
    NHNN = "NHNN"
    BANK = "BANK"


@dataclass(frozen=True)
class Currency:
    """§2.1 — ISO 4217 master entry."""

    code: str
    name: str
    symbol: str
    decimal_places: int
    is_base: bool = False
    is_active: bool = True

    def __post_init__(self) -> None:
        if not ISO4217_RE.match(self.code or ""):
            raise InvalidCurrencyCodeError(
                f"code must match {ISO4217_RE.pattern} (ISO 4217), got '{self.code}'"
            )
        if self.decimal_places < 0:
            raise ValueError("decimal_places must be >= 0")
        if not self.name.strip():
            raise ValueError("name is required")

    def deactivate(self) -> Currency:
        return replace(self, is_active=False)


DEFAULT_BASE_CURRENCY = "VND"


@dataclass(frozen=True)
class FxCompanyConfig:
    """§2.3 flags. LAW-type fields immutable after first use."""

    company_id: UUID
    base_currency: str = DEFAULT_BASE_CURRENCY
    booking_rate_debit: BookingRateSide = BookingRateSide.ACTUAL
    booking_rate_credit: BookingRateSide = BookingRateSide.WEIGHTED_AVG
    fx_gain_account: str = "515"
    fx_loss_account: str = "635"
    fx_revaluation_approval_required: bool = True


class RateType(Enum):
    """§2.2 rate_type per TT99 tỷ giá vocabulary."""

    BUY = "BUY"
    SELL = "SELL"
    TRANSFER = "TRANSFER"
    CENTRAL = "CENTRAL"
    BOOKING = "BOOKING"


@dataclass(frozen=True)
class ExchangeRate:
    """§2.2 — VND per 1 unit of currency_code; valid from rate_date onward."""

    currency_code: str
    rate_type: RateType
    rate_date: date
    rate: Decimal
    source: FxRateSource
    actor: UUID

    def __post_init__(self) -> None:
        if not ISO4217_RE.match(self.currency_code or ""):
            raise InvalidCurrencyCodeError(f"Invalid currency: {self.currency_code}")
        if self.rate <= 0:
            raise InvalidRateError("rate phải > 0")


class RevaluationStatus(Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


@dataclass
class RevaluationEntry:
    account_code: str
    currency_code: str
    balance_original: Decimal
    rate_applied: Decimal
    old_vnd: Decimal
    new_vnd: Decimal

    @property
    def difference(self) -> Decimal:
        return self.new_vnd - self.old_vnd

    @property
    def posting_side(self) -> str:
        return "GAIN" if self.difference >= 0 else "LOSS"


import hashlib


@dataclass
class RevaluationRun:
    company_id: UUID
    period_start: date
    period_end: date
    rate_date: date
    entries: list[RevaluationEntry]
    reversal_entries: list[RevaluationEntry] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    status: RevaluationStatus = RevaluationStatus.DRAFT
    actor: UUID | None = None
    approver: UUID | None = None
    checksum: str = ""

    def _hash(self, prev: str, actor: UUID, action: str) -> str:
        payload = f"{prev}{self.id}{actor}{self.status.value}{action}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def stamp(self, prev: str, actor: UUID, action: str) -> None:
        self.checksum = self._hash(prev, actor, action)

    def submit(self) -> None:
        if self.status != RevaluationStatus.DRAFT:
            raise ValueError("NOT_DRAFT")
        self.status = RevaluationStatus.PENDING_APPROVAL

    def approve(self, approver: UUID) -> None:
        if self.status != RevaluationStatus.PENDING_APPROVAL:
            raise ValueError("NOT_PENDING")
        self.approver = approver
        self.status = RevaluationStatus.APPROVED

    def post(self, actor: UUID) -> None:
        if self.status != RevaluationStatus.APPROVED:
            raise ValueError("NOT_APPROVED")
        self.actor = actor
        self.status = RevaluationStatus.POSTED

    def reverse(self) -> list[RevaluationEntry]:
        """Flip each entry's economics; mark run REVERSED."""
        rev: list[RevaluationEntry] = []
        for e in self.entries:
            rev.append(
                RevaluationEntry(
                    account_code=e.account_code,
                    currency_code=e.currency_code,
                    balance_original=e.balance_original,
                    rate_applied=e.rate_applied,
                    old_vnd=e.new_vnd,
                    new_vnd=e.old_vnd,
                )
            )
        self.reversal_entries = rev
        self.status = RevaluationStatus.REVERSED
        return rev
