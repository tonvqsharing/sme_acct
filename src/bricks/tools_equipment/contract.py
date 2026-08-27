"""Contract — Tools & Equipment (CCDC) port interfaces.

Ports define the public interface for external adapters.
Only primitives in/out. No Flask/SQLAlchemy imports.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.bricks.tools_equipment.domain import (
    CCDCCategory,
    ToolEquipment,
    ToolEquipmentAllocation,
    ToolEquipmentStatus,
)

# ---------------------------------------------------------------------------
# Repository ports
# ---------------------------------------------------------------------------


class ToolEquipmentRepositoryPort(ABC):
    """Repository for ToolEquipment entities."""

    @abstractmethod
    def create(self, entity: ToolEquipment) -> ToolEquipment:
        """Persist a new CCDC record."""

    @abstractmethod
    def get_by_id(self, id: UUID) -> ToolEquipment | None:
        """Retrieve CCDC by ID."""

    @abstractmethod
    def get_by_id_and_company(self, id: UUID, company_id: UUID) -> ToolEquipment | None:
        """Retrieve CCDC by ID within a company."""

    @abstractmethod
    def find_by_code_and_company(self, code: str, company_id: UUID) -> ToolEquipment | None:
        """Find CCDC by code + company (duplicate guard)."""

    @abstractmethod
    def update(self, entity: ToolEquipment) -> ToolEquipment:
        """Update an existing CCDC record."""

    @abstractmethod
    def delete(self, id: UUID) -> None:
        """Soft-delete a CCDC record."""

    @abstractmethod
    def list_by_company(
        self,
        company_id: UUID,
        status: ToolEquipmentStatus | None = None,
        category: CCDCCategory | None = None,
    ) -> list[ToolEquipment]:
        """List CCDC for a company with optional filters."""

    @abstractmethod
    def list_active_by_company(self, company_id: UUID) -> list[ToolEquipment]:
        """List all ACTIVE CCDC for allocation engine."""


class ToolEquipmentAllocationRepositoryPort(ABC):
    """Repository for ToolEquipmentAllocation entities."""

    @abstractmethod
    def create(self, entity: ToolEquipmentAllocation) -> ToolEquipmentAllocation:
        """Persist a new allocation record."""

    @abstractmethod
    def create_many(self, entities: list[ToolEquipmentAllocation]) -> list[ToolEquipmentAllocation]:
        """Batch create allocation records."""

    @abstractmethod
    def get_by_id(self, id: UUID) -> ToolEquipmentAllocation | None:
        """Retrieve allocation by ID."""

    @abstractmethod
    def list_by_tool(
        self,
        tool_equipment_id: UUID,
        year: int | None = None,
    ) -> list[ToolEquipmentAllocation]:
        """List allocations for a CCDC item, optionally filtered by year."""

    @abstractmethod
    def list_by_period(
        self,
        company_id: UUID,
        year: int,
        month: int,
    ) -> list[ToolEquipmentAllocation]:
        """List all allocations for a company in a given period."""

    @abstractmethod
    def find_existing_allocation(
        self,
        tool_equipment_id: UUID,
        year: int,
        month: int,
    ) -> ToolEquipmentAllocation | None:
        """Check if allocation already exists (idempotent guard)."""

    @abstractmethod
    def update(self, entity: ToolEquipmentAllocation) -> ToolEquipmentAllocation:
        """Update an allocation record."""

    @abstractmethod
    def sum_allocated_by_tool(self, tool_equipment_id: UUID) -> Decimal:
        """Sum of all allocated amounts for a CCDC item."""

    @abstractmethod
    def sum_allocated_by_tools(self, tool_equipment_ids: list[UUID]) -> dict[UUID, Decimal]:
        """Batch sum of allocated amounts for multiple CCDC items.

        Returns a mapping of tool_equipment_id → total allocated amount.
        """


# ---------------------------------------------------------------------------
# Service ports (external dependencies)
# ---------------------------------------------------------------------------


class FiscalPeriodServicePort(ABC):
    """Port for fiscal period validation."""

    @abstractmethod
    def is_period_open(self, year: int, month: int) -> bool:
        """Check if a fiscal period is open for posting."""

    @abstractmethod
    def get_period_id(self, year: int, month: int) -> UUID | None:
        """Get the period ID for a given year/month."""


class COAServicePort(ABC):
    """Port for Chart of Accounts validation."""

    @abstractmethod
    def is_account_active(self, account_code: str) -> bool:
        """Check if an account exists and is ACTIVE."""

    @abstractmethod
    def is_account_detail(self, account_code: str) -> bool:
        """Check if an account is a detail (posting) account."""

    @abstractmethod
    def get_account(self, account_code: str) -> dict[str, Any] | None:
        """Get account details by code."""
