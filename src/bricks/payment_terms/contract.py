"""Public interface for the payment_terms brick.

Ports only. Primitives in/out per brick boundary rules.
Cross-brick consumers depend on THIS file, never on services/storage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.payment_terms.domain import (
    DocumentNumberingSeries,
    PaymentTerm,
)


class PaymentTermRepositoryPort(ABC):
    """Repository port for PaymentTerm entities."""

    @abstractmethod
    def get_by_id(self, payment_term_id: UUID) -> PaymentTerm | None:
        """Get payment term by ID."""
        ...

    @abstractmethod
    def get_by_company(self, company_id: UUID) -> list[PaymentTerm]:
        """List all payment terms for a company (incl. inactive — 10-yr retention)."""
        ...

    @abstractmethod
    def get_default_by_company(self, company_id: UUID) -> PaymentTerm | None:
        """Return the company's default payment term, or None."""
        ...

    @abstractmethod
    def create(self, term: PaymentTerm) -> PaymentTerm:
        """Persist a new payment term."""
        ...

    @abstractmethod
    def update(self, term: PaymentTerm) -> PaymentTerm:
        """Persist changes to an existing payment term."""
        ...

    @abstractmethod
    def set_default(self, payment_term_id: UUID, actor: UUID, reason: str) -> PaymentTerm | None:
        """Mark term as company default; clear previous default atomically."""
        ...

    @abstractmethod
    def soft_delete(self, payment_term_id: UUID, actor: UUID, reason: str) -> None:
        """Soft-deactivate (R-006: never hard-delete)."""
        ...

    @abstractmethod
    def validate_name_unique(self, company_id: UUID, name: str) -> bool:
        """True if name unused within company."""
        ...


class DocumentNumberingSeriesRepositoryPort(ABC):
    """Repository port for DocumentNumberingSeries entities."""

    @abstractmethod
    def get_by_id(self, series_id: UUID) -> DocumentNumberingSeries | None:
        """Get series by ID."""
        ...

    @abstractmethod
    def get_by_company(self, company_id: UUID) -> list[DocumentNumberingSeries]:
        """List all series for a company."""
        ...

    @abstractmethod
    def get_active_by_company(self, company_id: UUID) -> list[DocumentNumberingSeries]:
        """List active series only."""
        ...

    @abstractmethod
    def create(self, series: DocumentNumberingSeries) -> DocumentNumberingSeries:
        """Persist a new numbering series."""
        ...

    @abstractmethod
    def update(self, series: DocumentNumberingSeries) -> DocumentNumberingSeries:
        """Persist changes to an existing series."""
        ...

    @abstractmethod
    def activate(self, series_id: UUID, actor: UUID, reason: str) -> DocumentNumberingSeries | None:
        """Mark series active (SOD-gated at service layer)."""
        ...

    @abstractmethod
    def deactivate(
        self, series_id: UUID, actor: UUID, reason: str
    ) -> DocumentNumberingSeries | None:
        """Mark series inactive (soft — R-011)."""
        ...

    @abstractmethod
    def validate_prefix_unique(self, company_id: UUID, prefix: str) -> bool:
        """True if prefix unused within company (R-009)."""
        ...

    @abstractmethod
    def check_max_series_limit(self, company_id: UUID) -> bool:
        """True if company has reached max active series (R-008: 15)."""
        ...
