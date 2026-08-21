"""Company contract interface.

Public interface for cross-brick communication.
Only primitive types in/out: str, int, float, dict, Decimal, UUID.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.company.domain import Company


class CompanyRepositoryPort(ABC):
    """Repository port for Company entities."""

    @abstractmethod
    def create(self, company: Company) -> Company:
        """Create new company."""
        ...

    @abstractmethod
    def get_by_id(self, company_id: UUID) -> Company | None:
        """Get company by ID."""
        ...

    @abstractmethod
    def get_by_mst(self, mst: str) -> Company | None:
        """Get company by MST (tax ID)."""
        ...

    @abstractmethod
    def list_active(self) -> list[Company]:
        """List all active companies."""
        ...

    @abstractmethod
    def update(self, company: Company, actor: UUID) -> Company:
        """Update company."""
        ...

    @abstractmethod
    def deactivate(self, company_id: UUID, actor: UUID) -> Company:
        """Deactivate company."""
        ...

    @abstractmethod
    def list_subsidiaries(self, parent_id: UUID) -> list[Company]:
        """List subsidiary companies."""
        ...
