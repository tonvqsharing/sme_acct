"""Payment Terms & Document Numbering domain entities.

Pure Python. ZERO Flask/SQLAlchemy imports.
Per docs/payment-terms/specs-payment-terms.md §3.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from uuid import UUID

# ─── Constants ─────────────────────────────────────────────────────────────

GENESIS_CHECKSUM = "0" * 64  # First event in a checksum chain

# GDT Circular 163/2020/TT-BTC Art. 10: e.g., "HD/", "PN/", "CV/"
TT163_PREFIX_PATTERN = r"^[A-Z]{2,}/$"

MAX_NAME_LENGTH = 200


class PaymentTermStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SeriesStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


def compute_checksum(
    *,
    prev: str,
    actor: UUID,
    timestamp: str,
    action: str,
    reason: str,
    entity_id: UUID,
) -> str:
    """SHA-256 checksum chain event per spec §9.1.

    checksum = SHA-256(prev_checksum + actor_uuid + timestamp + action + reason + entity_id)
    """
    payload = f"{prev}{actor}{timestamp}{action}{reason}{entity_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ─── PaymentTerm ───────────────────────────────────────────────────────────


@dataclass
class PaymentTerm:
    """Payment term aggregate root with invariants per Circular 99/2025/TT-BTC."""

    id: UUID
    company_id: UUID
    name: str
    due_days: int  # Số ngày trả nợ (ví dụ: 30 cho Net 30)
    interest_rate: Decimal  # Lãi suất trễ thanh toán
    is_default: bool = False
    status: PaymentTermStatus = PaymentTermStatus.ACTIVE
    created_at: date = field(default_factory=date.today)
    checksum: str = ""

    def __post_init__(self) -> None:
        if self.due_days < 1:
            raise ValueError(f"due_days must be >= 1, got {self.due_days}")
        if not self.name or not self.name.strip():
            raise ValueError("name must be non-empty")
        if len(self.name) > MAX_NAME_LENGTH:
            raise ValueError(f"name must be <= {MAX_NAME_LENGTH} chars")
        if self.interest_rate < Decimal(0):
            raise ValueError(f"interest_rate must be >= 0, got {self.interest_rate}")

    def calculate_due_date(self, issue_date: date) -> date:
        """R-012: due date = issue_date + due_days."""
        return issue_date + timedelta(days=self.due_days)

    def can_set_as_default(self) -> bool:
        """R-001 enforced at service/repo layer; entity is always eligible."""
        return self.status == PaymentTermStatus.ACTIVE


# ─── DocumentNumberingSeries ───────────────────────────────────────────────


@dataclass
class DocumentNumberingSeries:
    """Document numbering series aggregate root per GDT Circular 163/2020/TT-BTC."""

    id: UUID
    company_id: UUID
    prefix: str  # Must match TT163_PREFIX_PATTERN, e.g., "HD/"
    next_sequence: int  # Số tự động tăng
    is_active: bool = True
    max_sequences: int = 999999
    status: SeriesStatus = SeriesStatus.ACTIVE
    created_at: date = field(default_factory=date.today)
    checksum: str = ""

    def __post_init__(self) -> None:
        if self.next_sequence < 1:
            raise ValueError(f"next_sequence must be >= 1, got {self.next_sequence}")
        if self.max_sequences < 1:
            raise ValueError(f"max_sequences must be >= 1, got {self.max_sequences}")

    def validate_prefix(self) -> bool:
        """R-007: prefix format per GDT Circular 163 Art. 10."""
        return bool(TT163_RE.match(self.prefix))

    def can_increment(self) -> bool:
        """EX-006 guard: may still issue a document at max_sequences."""
        return self.next_sequence <= self.max_sequences

    def increment_sequence(self) -> int:
        """Advance next_sequence by 1; returns the NEW value."""
        if not self.can_increment():
            raise ValueError("SEQUENCE_AT_MAX")
        self.next_sequence += 1
        return self.next_sequence


TT163_RE = re.compile(TT163_PREFIX_PATTERN)


# ─── Domain exceptions ─────────────────────────────────────────────────────
# Codes map 1:1 to spec §12 Exception Paths (EX-001..EX-010).
# Web adapter translates these to HTTP responses.


class PaymentTermsDomainError(Exception):
    """Base for payment_terms brick errors. Carries API error code."""

    code = "PAYMENT_TERMS_ERROR"
    http_status = 400

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)


class ActorRequiredError(PaymentTermsDomainError):
    """EX-001: actor UUID missing from mutation."""

    code = "MISSING_ACTOR"
    http_status = 400


class ReasonRequiredError(PaymentTermsDomainError):
    """R-004: non-empty reason required on mutations."""

    code = "REASON_REQUIRED"
    http_status = 400


class DuplicatePaymentTermError(PaymentTermsDomainError):
    """EX-002: term name already exists for company."""

    code = "DUPLICATE_PAYMENT_TERM"
    http_status = 409


class DefaultAlreadyExistsError(PaymentTermsDomainError):
    """EX-003: company already has a default payment term."""

    code = "DEFAULT_ALREADY_EXISTS"
    http_status = 409


class InvalidSeriesPrefixError(PaymentTermsDomainError):
    """EX-004: prefix fails GDT format ^[A-Z]{2,}/$."""

    code = "INVALID_SERIES_PREFIX"
    http_status = 422


class MaxSeriesExceededError(PaymentTermsDomainError):
    """EX-005: more than 15 active series per company."""

    code = "MAX_SERIES_EXCEEDED"
    http_status = 409


class SequenceAtMaxError(PaymentTermsDomainError):
    """EX-006: sequence reached 999999."""

    code = "SEQUENCE_AT_MAX"
    http_status = 409


class AuditorReadOnlyError(PaymentTermsDomainError):
    """EX-007: AUDITOR attempted a mutation."""

    code = "AUDITOR_READ_ONLY"
    http_status = 403


class SeriesInactiveError(PaymentTermsDomainError):
    """EX-008: cannot increment on inactive series."""

    code = "SERIES_INACTIVE"
    http_status = 409


class PrefixAlreadyExistsError(PaymentTermsDomainError):
    """AP-002: series prefix already used within company."""

    code = "PREFIX_ALREADY_EXISTS"
    http_status = 409


class PaymentTermNotFoundError(PaymentTermsDomainError):
    """EX-010 family: entity not found."""

    code = "NOT_FOUND"
    http_status = 404


class SeriesNotFoundError(PaymentTermNotFoundError):
    """Series variant of NOT_FOUND."""
