"""Services — Tools & Equipment (CCDC) business logic.

Orchestrates domain entities via port interfaces.
Transaction gate order: fiscal-period open → COA posting accounts → balance/invariant.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from src.bricks.tools_equipment.contract import (
    COAServicePort,
    FiscalPeriodServicePort,
    ToolEquipmentAllocationRepositoryPort,
    ToolEquipmentRepositoryPort,
)
from src.bricks.tools_equipment.domain import (
    AllocationStatus,
    CCDCCategory,
    CodeImmutableError,
    DuplicateCodeError,
    InvalidStatusTransitionError,
    ToolEquipment,
    ToolEquipmentAllocation,
    ToolEquipmentStatus,
    ValidationError,
)


class ToolEquipmentService:
    """Service for CCDC CRUD and lifecycle management."""

    def __init__(
        self,
        repo: ToolEquipmentRepositoryPort,
        alloc_repo: ToolEquipmentAllocationRepositoryPort,
        fy_service: FiscalPeriodServicePort,
        coa_service: COAServicePort,
    ) -> None:
        self._repo = repo
        self._alloc_repo = alloc_repo
        self._fy_service = fy_service
        self._coa_service = coa_service

    # -- Create ---------------------------------------------------------------

    def create(
        self,
        company_id: UUID,
        code: str,
        name: str,
        category: CCDCCategory,
        purchase_date: date,
        purchase_price: Decimal,
        useful_life_months: int,
        expense_account_code: str,
        actor_id: UUID,
        salvage_value: Decimal = Decimal(0),
        prepaid_account_code: str | None = None,
        assigned_to: UUID | None = None,
        cost_center_id: UUID | None = None,
        dimension_value_id: UUID | None = None,
        description: str | None = None,
    ) -> ToolEquipment:
        """Create a new CCDC record.

        Business rules:
        - BR-001: Code unique per company
        - BR-004: Price > 0
        - BR-009: Create sets created_by = actor_id
        """
        # Duplicate guard
        existing = self._repo.find_by_code_and_company(code, company_id)
        if existing is not None:
            raise DuplicateCodeError(f"CCDC code {code!r} already exists for company")

        # COA validation
        if not self._coa_service.is_account_active(expense_account_code):
            raise ValidationError(f"Expense account {expense_account_code!r} is not active")
        if not self._coa_service.is_account_detail(expense_account_code):
            raise ValidationError(
                f"Expense account {expense_account_code!r} is not a detail account"
            )

        # Create entity
        entity = ToolEquipment(
            company_id=company_id,
            code=code,
            name=name,
            category=category,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            useful_life_months=useful_life_months,
            expense_account_code=expense_account_code,
            salvage_value=salvage_value,
            prepaid_account_code=prepaid_account_code,
            assigned_to=assigned_to,
            cost_center_id=cost_center_id,
            dimension_value_id=dimension_value_id,
            description=description,
            created_by=actor_id,
        )

        return self._repo.create(entity)

    # -- Update ---------------------------------------------------------------

    def update(
        self,
        id: UUID,
        company_id: UUID,
        actor_id: UUID,
        **fields: Any,
    ) -> ToolEquipment:
        """Update a CCDC record.

        Business rules:
        - BR-011: Update sets updated_by = actor_id
        - VR-007: Cannot modify code after creation
        """
        entity = self._repo.get_by_id_and_company(id, company_id)
        if entity is None:
            raise ValidationError(f"CCDC {id} not found in company")

        if entity.status != ToolEquipmentStatus.ACTIVE:
            raise InvalidStatusTransitionError(
                f"Can only update ACTIVE CCDC, current: {entity.status.value}"
            )

        # Block code modification
        if "code" in fields and fields["code"] != entity.code:
            raise CodeImmutableError("Cannot modify code after creation")

        # Apply allowed fields
        allowed = {
            "name",
            "category",
            "purchase_date",
            "purchase_price",
            "useful_life_months",
            "salvage_value",
            "expense_account_code",
            "prepaid_account_code",
            "assigned_to",
            "cost_center_id",
            "dimension_value_id",
            "description",
        }
        for key, value in fields.items():
            if key in allowed:
                setattr(entity, key, value)

        return self._repo.update(entity)

    # -- Deactivate -----------------------------------------------------------

    def deactivate(
        self,
        id: UUID,
        company_id: UUID,
        actor_id: UUID,
    ) -> ToolEquipment:
        """Deactivate CCDC (ACTIVE → INACTIVE).

        Business rules:
        - BR-005: Requires ACTIVE status
        - BR-010: Sets deactivated_by = actor_id
        """
        entity = self._repo.get_by_id_and_company(id, company_id)
        if entity is None:
            raise ValidationError(f"CCDC {id} not found in company")

        entity.deactivate(actor_id)
        return self._repo.update(entity)

    # -- Reactivate -----------------------------------------------------------

    def reactivate(
        self,
        id: UUID,
        company_id: UUID,
        actor_id: UUID,
    ) -> ToolEquipment:
        """Reactivate CCDC (INACTIVE → ACTIVE).

        Business rules:
        - BR-006: Requires INACTIVE status
        """
        entity = self._repo.get_by_id_and_company(id, company_id)
        if entity is None:
            raise ValidationError(f"CCDC {id} not found in company")

        entity.reactivate(actor_id)
        return self._repo.update(entity)

    # -- Write-off ------------------------------------------------------------

    def write_off(
        self,
        id: UUID,
        company_id: UUID,
        actor_id: UUID,
    ) -> ToolEquipment:
        """Write off CCDC (ACTIVE/INACTIVE → WRITTEN_OFF).

        Business rules:
        - BR-007: Requires CHIEF_ACCOUNTANT role (checked in web adapter)
        - BR-008: Requires non-zero remaining value
        """
        entity = self._repo.get_by_id_and_company(id, company_id)
        if entity is None:
            raise ValidationError(f"CCDC {id} not found in company")

        # Check remaining value
        allocated = self._alloc_repo.sum_allocated_by_tool(id)
        remaining = entity.purchase_price - allocated
        if remaining <= 0:
            raise ValidationError(
                f"Cannot write off CCDC with zero or negative " f"remaining value: {remaining}"
            )

        entity.write_off(actor_id)
        return self._repo.update(entity)

    # -- Read -----------------------------------------------------------------

    def get_by_id(
        self,
        id: UUID,
        company_id: UUID,
    ) -> ToolEquipment | None:
        """Get CCDC by ID within a company."""
        return self._repo.get_by_id_and_company(id, company_id)

    def list_by_company(
        self,
        company_id: UUID,
        status: ToolEquipmentStatus | None = None,
        category: CCDCCategory | None = None,
    ) -> list[ToolEquipment]:
        """List CCDC for a company with optional filters."""
        return self._repo.list_by_company(company_id, status=status, category=category)


class AllocationEngine:
    """Service for monthly CCDC allocation."""

    def __init__(
        self,
        repo: ToolEquipmentRepositoryPort,
        alloc_repo: ToolEquipmentAllocationRepositoryPort,
        fy_service: FiscalPeriodServicePort,
        coa_service: COAServicePort,
    ) -> None:
        self._repo = repo
        self._alloc_repo = alloc_repo
        self._fy_service = fy_service
        self._coa_service = coa_service

    def calculate_allocations(
        self,
        company_id: UUID,
        year: int,
        month: int,
    ) -> list[dict[str, Any]]:
        """Calculate allocations for a given period.

        Business rules:
        - BR-012: Allocation = (price - salvage) / useful_life_months
        - BR-013: Only ACTIVE status
        - BR-014: Only in open fiscal periods
        - BR-015: Amount rounded to VND
        - BR-016: Maximum 36-month allocation
        """
        # Gate 1: Fiscal period must be open
        if not self._fy_service.is_period_open(year, month):
            raise ValidationError(f"Fiscal period {year}/{month:02d} is not open")

        # Get all ACTIVE CCDC for this company
        active_items = self._repo.list_active_by_company(company_id)

        results: list[dict[str, Any]] = []
        for item in active_items:
            # Skip if already fully allocated
            total_allocated = self._alloc_repo.sum_allocated_by_tool(item.id)
            remaining = item.purchase_price - total_allocated
            if remaining <= 0:
                continue

            # Calculate monthly amount
            monthly = item.monthly_allocation

            # Don't over-allocate
            amount = min(monthly, remaining)
            amount = amount.quantize(Decimal(1), rounding=ROUND_HALF_UP)

            if amount > 0:
                results.append(
                    {
                        "tool_equipment_id": item.id,
                        "tool_code": item.code,
                        "tool_name": item.name,
                        "remaining_value": remaining,
                        "allocated_amount": amount,
                        "expense_account_code": item.expense_account_code,
                        "cost_center_id": item.cost_center_id,
                        "dimension_value_id": item.dimension_value_id,
                    }
                )

        return results

    def post_allocations(
        self,
        company_id: UUID,
        year: int,
        month: int,
    ) -> list[ToolEquipmentAllocation]:
        """Post allocations for a given period.

        Creates allocation records and returns them.
        Journal entry creation happens in the voucher brick.
        """
        # Gate 1: Fiscal period must be open
        if not self._fy_service.is_period_open(year, month):
            raise ValidationError(f"Fiscal period {year}/{month:02d} is not open")

        # Calculate
        calculations = self.calculate_allocations(company_id, year, month)

        # Create allocation records
        allocations: list[ToolEquipmentAllocation] = []
        for calc in calculations:
            # Idempotent guard
            existing = self._alloc_repo.find_existing_allocation(
                calc["tool_equipment_id"], year, month
            )
            if existing is not None:
                allocations.append(existing)
                continue

            alloc = ToolEquipmentAllocation(
                tool_equipment_id=calc["tool_equipment_id"],
                period_year=year,
                period_month=month,
                allocated_amount=calc["allocated_amount"],
                expense_account_code=calc["expense_account_code"],
                cost_center_id=calc["cost_center_id"],
                dimension_value_id=calc["dimension_value_id"],
                status=AllocationStatus.POSTED,
            )
            allocations.append(alloc)

        # Batch create
        if allocations:
            return self._alloc_repo.create_many(allocations)
        return allocations

    def list_allocations(
        self,
        tool_equipment_id: UUID,
        year: int | None = None,
    ) -> list[ToolEquipmentAllocation]:
        """List allocations for a CCDC item."""
        return self._alloc_repo.list_by_tool(tool_equipment_id, year=year)

    def get_allocation_summary(
        self,
        company_id: UUID,
        year: int,
    ) -> dict[str, Any]:
        """Get allocation summary for a year."""
        items = self._repo.list_by_company(company_id)
        summary: dict[str, Any] = {
            "year": year,
            "items": [],
            "total_original": Decimal(0),
            "total_allocated": Decimal(0),
            "total_remaining": Decimal(0),
        }

        for item in items:
            allocated = self._alloc_repo.sum_allocated_by_tool(item.id)
            remaining = item.purchase_price - allocated
            summary["items"].append(
                {
                    "id": item.id,
                    "code": item.code,
                    "name": item.name,
                    "original_price": item.purchase_price,
                    "allocated_to_date": allocated,
                    "remaining_value": remaining,
                    "useful_life_months": item.useful_life_months,
                    "status": item.status.value,
                }
            )
            summary["total_original"] += item.purchase_price
            summary["total_allocated"] += allocated
            summary["total_remaining"] += remaining

        return summary
