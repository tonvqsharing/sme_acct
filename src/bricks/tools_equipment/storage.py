"""Storage — Tools & Equipment (CCDC) SQLAlchemy models + repository adapters.

SQLAlchemy models and repository implementations.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.bricks.tools_equipment.contract import (
    ToolEquipmentAllocationRepositoryPort,
    ToolEquipmentRepositoryPort,
)
from src.bricks.tools_equipment.domain import (
    AllocationStatus,
    CCDCCategory,
    ToolEquipment,
    ToolEquipmentAllocation,
    ToolEquipmentStatus,
)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# SQLAlchemy models
# ---------------------------------------------------------------------------

utc_now = sa.func.now()


class ToolEquipmentModel(Base):  # type: ignore[misc]
    """SQLAlchemy model for CCDC master data."""

    __tablename__ = "tools_equipment"

    id: Mapped[sa.Uuid] = mapped_column(  # type: ignore[type-arg]
        sa.Uuid(), primary_key=True, default=sa.text("gen_random_uuid()")
    )
    company_id: Mapped[sa.Uuid] = mapped_column(  # type: ignore[type-arg]
        sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    category: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    purchase_date: Mapped[sa.Date] = mapped_column(sa.Date(), nullable=False)
    purchase_price: Mapped[sa.Numeric] = mapped_column(sa.Numeric(18, 2), nullable=False)  # type: ignore[type-arg]
    useful_life_months: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    salvage_value: Mapped[sa.Numeric] = mapped_column(  # type: ignore[type-arg]
        sa.Numeric(18, 2), nullable=False, server_default="0"
    )
    expense_account_code: Mapped[str] = mapped_column(
        sa.String(20), sa.ForeignKey("accounts.code"), nullable=False
    )
    prepaid_account_code: Mapped[str | None] = mapped_column(
        sa.String(20), sa.ForeignKey("accounts.code"), nullable=True
    )
    assigned_to: Mapped[sa.Uuid | None] = mapped_column(  # type: ignore[type-arg]
        sa.Uuid(), sa.ForeignKey("users.id"), nullable=True
    )
    cost_center_id: Mapped[sa.Uuid | None] = mapped_column(  # type: ignore[type-arg]
        sa.Uuid(), sa.ForeignKey("cost_centers.id"), nullable=True
    )
    dimension_value_id: Mapped[sa.Uuid | None] = mapped_column(  # type: ignore[type-arg]
        sa.Uuid(), sa.ForeignKey("dimension_values.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default="Active")
    audit_checksum: Mapped[str] = mapped_column(sa.Text(), nullable=False, server_default="")

    # Audit columns
    created_by: Mapped[sa.Uuid | None] = mapped_column(
        sa.Uuid(), sa.ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=utc_now
    )
    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        sa.UniqueConstraint("code", "company_id", name="uq_tool_equipment_code_company"),
    )


class ToolEquipmentAllocationModel(Base):  # type: ignore[misc]
    """SQLAlchemy model for CCDC allocation records."""

    __tablename__ = "tools_equipment_allocations"

    id: Mapped[sa.Uuid] = mapped_column(  # type: ignore[type-arg]
        sa.Uuid(), primary_key=True, default=sa.text("gen_random_uuid()")
    )
    tool_equipment_id: Mapped[sa.Uuid] = mapped_column(
        sa.Uuid(),
        sa.ForeignKey("tools_equipment.id"),
        nullable=False,
        index=True,
    )
    period_year: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    period_month: Mapped[int] = mapped_column(sa.Integer(), nullable=False)
    allocated_amount: Mapped[sa.Numeric] = mapped_column(sa.Numeric(18, 2), nullable=False)  # type: ignore[type-arg]
    expense_account_code: Mapped[str] = mapped_column(
        sa.String(20), sa.ForeignKey("accounts.code"), nullable=False
    )
    cost_center_id: Mapped[sa.Uuid | None] = mapped_column(  # type: ignore[type-arg]
        sa.Uuid(), sa.ForeignKey("cost_centers.id"), nullable=True
    )
    dimension_value_id: Mapped[sa.Uuid | None] = mapped_column(  # type: ignore[type-arg]
        sa.Uuid(), sa.ForeignKey("dimension_values.id"), nullable=True
    )
    voucher_id: Mapped[sa.Uuid | None] = mapped_column(
        sa.Uuid(), sa.ForeignKey("vouchers.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default="Pending")
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=utc_now
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "tool_equipment_id",
            "period_year",
            "period_month",
            name="uq_allocation_tool_period",
        ),
    )


# ---------------------------------------------------------------------------
# Repository adapters
# ---------------------------------------------------------------------------


def _row_to_entity(row: ToolEquipmentModel) -> ToolEquipment:
    """Convert SQLAlchemy model to domain entity."""
    return ToolEquipment(
        id=row.id,  # type: ignore[arg-type]
        company_id=row.company_id,
        code=row.code,
        name=row.name,
        category=CCDCCategory(row.category),
        purchase_date=row.purchase_date,
        purchase_price=row.purchase_price,
        useful_life_months=row.useful_life_months,
        salvage_value=row.salvage_value,
        expense_account_code=row.expense_account_code,
        prepaid_account_code=row.prepaid_account_code,
        assigned_to=row.assigned_to,
        cost_center_id=row.cost_center_id,
        dimension_value_id=row.dimension_value_id,
        description=row.description,
        status=ToolEquipmentStatus(row.status),
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
        audit_checksum=row.audit_checksum,
    )


def _alloc_row_to_entity(
    row: ToolEquipmentAllocationModel,
) -> ToolEquipmentAllocation:
    """Convert SQLAlchemy model to domain entity."""
    return ToolEquipmentAllocation(
        id=row.id,
        tool_equipment_id=row.tool_equipment_id,
        period_year=row.period_year,
        period_month=row.period_month,
        allocated_amount=row.allocated_amount,
        expense_account_code=row.expense_account_code,
        cost_center_id=row.cost_center_id,
        dimension_value_id=row.dimension_value_id,
        voucher_id=row.voucher_id,
        status=AllocationStatus(row.status),
        created_at=row.created_at,
    )


class ToolEquipmentRepo(ToolEquipmentRepositoryPort):
    """SQLAlchemy repository for ToolEquipment."""

    def __init__(self, session: orm.Session) -> None:
        self._session = session

    def create(self, entity: ToolEquipment) -> ToolEquipment:
        model = ToolEquipmentModel(
            id=entity.id,
            company_id=entity.company_id,
            code=entity.code,
            name=entity.name,
            category=entity.category.value,
            purchase_date=entity.purchase_date,
            purchase_price=entity.purchase_price,
            useful_life_months=entity.useful_life_months,
            salvage_value=entity.salvage_value,
            expense_account_code=entity.expense_account_code,
            prepaid_account_code=entity.prepaid_account_code,
            assigned_to=entity.assigned_to,
            cost_center_id=entity.cost_center_id,
            dimension_value_id=entity.dimension_value_id,
            description=entity.description,
            status=entity.status.value,
            audit_checksum=entity.audit_checksum,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self._session.add(model)
        self._session.flush()
        return _row_to_entity(model)

    def get_by_id(self, id: sa.Uuid) -> ToolEquipment | None:
        model = self._session.get(ToolEquipmentModel, id)
        return _row_to_entity(model) if model else None

    def get_by_id_and_company(self, id: sa.Uuid, company_id: sa.Uuid) -> ToolEquipment | None:
        model = self._session.execute(
            sa.select(ToolEquipmentModel).where(
                ToolEquipmentModel.id == id,
                ToolEquipmentModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return _row_to_entity(model) if model else None

    def find_by_code_and_company(self, code: str, company_id: sa.Uuid) -> ToolEquipment | None:
        model = self._session.execute(
            sa.select(ToolEquipmentModel).where(
                ToolEquipmentModel.code == code,
                ToolEquipmentModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return _row_to_entity(model) if model else None

    def update(self, entity: ToolEquipment) -> ToolEquipment:
        model = self._session.get(ToolEquipmentModel, entity.id)
        if model is None:
            raise ValueError(f"ToolEquipment {entity.id} not found")

        model.code = entity.code
        model.name = entity.name
        model.category = entity.category.value
        model.purchase_date = entity.purchase_date
        model.purchase_price = entity.purchase_price
        model.useful_life_months = entity.useful_life_months
        model.salvage_value = entity.salvage_value
        model.expense_account_code = entity.expense_account_code
        model.prepaid_account_code = entity.prepaid_account_code
        model.assigned_to = entity.assigned_to
        model.cost_center_id = entity.cost_center_id
        model.dimension_value_id = entity.dimension_value_id
        model.description = entity.description
        model.status = entity.status.value
        model.audit_checksum = entity.audit_checksum
        model.updated_at = entity.updated_at

        self._session.flush()
        return _row_to_entity(model)

    def delete(self, id: sa.Uuid) -> None:
        model = self._session.get(ToolEquipmentModel, id)
        if model:
            self._session.delete(model)
            self._session.flush()

    def list_by_company(
        self,
        company_id: sa.Uuid,
        status: ToolEquipmentStatus | None = None,
        category: CCDCCategory | None = None,
    ) -> list[ToolEquipment]:
        stmt = sa.select(ToolEquipmentModel).where(ToolEquipmentModel.company_id == company_id)
        if status is not None:
            stmt = stmt.where(ToolEquipmentModel.status == status.value)
        if category is not None:
            stmt = stmt.where(ToolEquipmentModel.category == category.value)
        stmt = stmt.order_by(ToolEquipmentModel.code)
        rows = self._session.execute(stmt).scalars().all()
        return [_row_to_entity(r) for r in rows]

    def list_active_by_company(self, company_id: sa.Uuid) -> list[ToolEquipment]:
        return self.list_by_company(company_id, status=ToolEquipmentStatus.ACTIVE)


class ToolEquipmentAllocationRepo(ToolEquipmentAllocationRepositoryPort):
    """SQLAlchemy repository for ToolEquipmentAllocation."""

    def __init__(self, session: orm.Session) -> None:
        self._session = session

    def create(self, entity: ToolEquipmentAllocation) -> ToolEquipmentAllocation:
        model = ToolEquipmentAllocationModel(
            id=entity.id,
            tool_equipment_id=entity.tool_equipment_id,
            period_year=entity.period_year,
            period_month=entity.period_month,
            allocated_amount=entity.allocated_amount,
            expense_account_code=entity.expense_account_code,
            cost_center_id=entity.cost_center_id,
            dimension_value_id=entity.dimension_value_id,
            voucher_id=entity.voucher_id,
            status=entity.status.value,
            created_at=entity.created_at,
        )
        self._session.add(model)
        self._session.flush()
        return _alloc_row_to_entity(model)

    def create_many(self, entities: list[ToolEquipmentAllocation]) -> list[ToolEquipmentAllocation]:
        results: list[ToolEquipmentAllocation] = []
        for entity in entities:
            results.append(self.create(entity))
        return results

    def get_by_id(self, id: sa.Uuid) -> ToolEquipmentAllocation | None:
        model = self._session.get(ToolEquipmentAllocationModel, id)
        return _alloc_row_to_entity(model) if model else None

    def list_by_tool(
        self,
        tool_equipment_id: sa.Uuid,
        year: int | None = None,
    ) -> list[ToolEquipmentAllocation]:
        stmt = sa.select(ToolEquipmentAllocationModel).where(
            ToolEquipmentAllocationModel.tool_equipment_id == tool_equipment_id
        )
        if year is not None:
            stmt = stmt.where(ToolEquipmentAllocationModel.period_year == year)
        stmt = stmt.order_by(
            ToolEquipmentAllocationModel.period_year,
            ToolEquipmentAllocationModel.period_month,
        )
        rows = self._session.execute(stmt).scalars().all()
        return [_alloc_row_to_entity(r) for r in rows]

    def list_by_period(
        self,
        company_id: sa.Uuid,
        year: int,
        month: int,
    ) -> list[ToolEquipmentAllocation]:
        stmt = (
            sa.select(ToolEquipmentAllocationModel)
            .join(ToolEquipmentModel)
            .where(
                ToolEquipmentModel.company_id == company_id,
                ToolEquipmentAllocationModel.period_year == year,
                ToolEquipmentAllocationModel.period_month == month,
            )
        )
        rows = self._session.execute(stmt).scalars().all()
        return [_alloc_row_to_entity(r) for r in rows]

    def find_existing_allocation(
        self,
        tool_equipment_id: sa.Uuid,
        year: int,
        month: int,
    ) -> ToolEquipmentAllocation | None:
        model = self._session.execute(
            sa.select(ToolEquipmentAllocationModel).where(
                ToolEquipmentAllocationModel.tool_equipment_id == tool_equipment_id,
                ToolEquipmentAllocationModel.period_year == year,
                ToolEquipmentAllocationModel.period_month == month,
            )
        ).scalar_one_or_none()
        return _alloc_row_to_entity(model) if model else None

    def update(self, entity: ToolEquipmentAllocation) -> ToolEquipmentAllocation:
        model = self._session.get(ToolEquipmentAllocationModel, entity.id)
        if model is None:
            raise ValueError(f"Allocation {entity.id} not found")

        model.allocated_amount = entity.allocated_amount
        model.expense_account_code = entity.expense_account_code
        model.cost_center_id = entity.cost_center_id
        model.dimension_value_id = entity.dimension_value_id
        model.voucher_id = entity.voucher_id
        model.status = entity.status.value

        self._session.flush()
        return _alloc_row_to_entity(model)

    def sum_allocated_by_tool(self, tool_equipment_id: sa.Uuid) -> sa.Numeric:
        """Sum of all allocated amounts for a CCDC item."""
        from decimal import Decimal

        result = self._session.execute(
            sa.select(
                sa.func.coalesce(
                    sa.func.sum(ToolEquipmentAllocationModel.allocated_amount),
                    Decimal(0),
                )
            ).where(ToolEquipmentAllocationModel.tool_equipment_id == tool_equipment_id)
        ).scalar_one()
        return result or Decimal(0)

    def sum_allocated_by_tools(
        self, tool_equipment_ids: list[sa.Uuid]
    ) -> dict[sa.Uuid, sa.Numeric]:
        """Batch sum of allocated amounts for multiple CCDC items."""
        from decimal import Decimal

        if not tool_equipment_ids:
            return {}

        result = self._session.execute(
            sa.select(
                ToolEquipmentAllocationModel.tool_equipment_id,
                sa.func.coalesce(
                    sa.func.sum(ToolEquipmentAllocationModel.allocated_amount),
                    Decimal(0),
                ),
            )
            .where(ToolEquipmentAllocationModel.tool_equipment_id.in_(tool_equipment_ids))
            .group_by(ToolEquipmentAllocationModel.tool_equipment_id)
        ).all()

        return {row[0]: row[1] for row in result}
