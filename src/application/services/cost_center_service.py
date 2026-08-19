"""Cost Centers and Dimensions application service.

Vietnamese SME Accounting Application — Cost Centers & Dimensions Module
Legal basis: Law on Accounting 2015 (Chap IX); Circular 99/2025/TT-BTC;
enterprise analytical accounting requirements.

Follows CurrencyService pattern: NO Flask/SQLAlchemy imports in service.
Actor UUID required on mutations (D11). Audit checksum chaining (SHA-256).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.application.ports import (
    CostCenterRepositoryPort,
    DimensionRepositoryPort,
    DimensionValueRepositoryPort,
)
from src.domain.entities.cost_center import (
    CostCenter,
    Dimension,
    DimensionType,
    DimensionValue,
    CostCenterStatus,
    DimensionValueStatus,
)
from src.domain.exceptions import (
    DomainException,
    DuplicateMSTError,
    SystemAccountModificationError,
)
from src.infrastructure.database import db


class CoaCostCenterService:
    """Enforces Cost Center business rules; no Flask/SQLAlchemy imports."""

    def __init__(
        self,
        cost_center_repo: CostCenterRepositoryPort,
    ) -> None:
        self._cc_repo = cost_center_repo

    # ── Creation ──────────────────────────────────────────────────

    def create_cost_center(
        self,
        code: str,
        name: str,
        company_id: UUID,
        actor: UUID,  # must be CHIEF_ACCOUNTANT or admin
        description: str | None = None,
    ) -> CostCenter:
        """Create new cost center with full invariant validation."""
        if actor is None:
            raise DomainException("Actor UUID required on mutations (D11)")

        # Validate code format (CostCenterCode VO)
        try:
            from src.domain.entities.cost_center import CostCenterCode  # local import
            CostCenterCode(code)  # raises DomainException if bad
        except DomainException as e:
            raise DomainException(f"Invalid cost center code: {e}") from e

        # Check code uniqueness per company
        existing = self._cc_repo.get_by_code(code, company_id)
        if existing is not None:
            raise DuplicateMSTError(
                f"Cost Center code {code} already exists for company {company_id}"
            )

        # Build domain entity
        cost_center = CostCenter(
            code=code,
            name=name,
            company_id=company_id,
            created_by=actor,
            description=description,
        )

        # Persist via repo (repo handles DB session; service just orchestrates)
        created = self._cc_repo.create(cost_center)
        db.session.flush()  # ensure persistence; caller commits per pattern
        return created

    # ── Modification ──────────────────────────────────────────────

    def update_cost_center(
        self,
        cost_center_id: UUID,
        *,
        new_code: str | None = None,
        new_name: str | None = None,
        actor: UUID,
        reason: str,
    ) -> CostCenter:
        """Modify cost center; requires actor and reason; audit logged.

        Code change: system checks uniqueness per company; if duplicate → error.
        """
        if actor is None:
            raise DomainException("Actor UUID required")

        # Fetch current cost center
        cost_center = self._cc_repo.get_by_id(cost_center_id)
        if cost_center is None:
            raise ValueError(f"Cost Center {cost_center_id} not found")

        # Apply allowed modifications via domain method
        try:
            cost_center.modify(
                new_code=new_code,
                new_name=new_name,
                actor=actor,
                reason=reason,
            )
        except DomainException as e:
            raise e

        # Persist
        updated = self._cc_repo.update(cost_center)
        db.session.flush()
        return updated

    # ── Deactivation/Reactivation ──────────────────────────────────

    def deactivate_cost_center(self, cost_center_id: UUID, actor: UUID, reason: str) -> CostCenter:
        """Deactivate cost center: ACTIVE → INACTIVE."""
        if actor is None:
            raise DomainException("Actor UUID required")

        cost_center = self._cc_repo.get_by_id(cost_center_id)
        if cost_center is None:
            raise ValueError(f"Cost Center {cost_center_id} not found")

        # Check if can deactivate (must be ACTIVE)
        if cost_center.status != CostCenterStatus.ACTIVE:
            raise ValueError(
                f"Cannot deactivate cost center {cost_center.code}: current status is {cost_center.status.value}"
            )

        # Soft-delete via repo (sets status=INACTIVE)
        self._cc_repo.soft_delete(cost_center_id, actor=actor, reason=reason)
        db.session.flush()

        # Fetch and return the updated cost center
        updated = self._cc_repo.get_by_id(cost_center_id)
        return updated

    def reactivate_cost_center(self, cost_center_id: UUID, actor: UUID, reason: str) -> CostCenter:
        """Reactivate cost center: INACTIVE → ACTIVE."""
        if actor is None:
            raise DomainException("Actor UUID required")

        cost_center = self._cc_repo.get_by_id(cost_center_id)
        if cost_center is None:
            raise ValueError(f"Cost Center {cost_center_id} not found")

        # Use domain method to set status back to ACTIVE
        cost_center.reactivate(actor=actor, reason=reason)
        updated = self._cc_repo.update(cost_center)
        db.session.flush()
        return updated

    # ── Closing ───────────────────────────────────────────────────

    def close_cost_center(self, cost_center_id: UUID, actor: UUID, reason: str) -> CostCenter:
        """Close cost center: ACTIVE → CLOSED."""
        if actor is None:
            raise DomainException("Actor UUID required")

        cost_center = self._cc_repo.get_by_id(cost_center_id)
        if cost_center is None:
            raise ValueError(f"Cost Center {cost_center_id} not found")

        # Check if can close (must be ACTIVE)
        if cost_center.status != CostCenterStatus.ACTIVE:
            raise ValueError(
                f"Cannot close cost center {cost_center.code}: current status is {cost_center.status.value}"
            )

        # Soft-close via repo (sets status=CLOSED)
        self._cc_repo.soft_delete(cost_center_id, actor=actor, reason=reason)
        db.session.flush()

        # Fetch and return the updated cost center
        updated = self._cc_repo.get_by_id(cost_center_id)
        return updated

    # ── Listing & Search ──────────────────────────────────────────

    def list_by_company(
        self,
        company_id: UUID,
        *,
        status: CostCenterStatus | None = None,
    ) -> list[CostCenter]:
        return self._cc_repo.list_by_company(company_id, status=status)

    # ── System dimensions integration ─────────────────────────────

    def can_modify_cost_center(self, cost_center_id: UUID, actor: UUID) -> bool:
        """Check if actor can modify a cost center (defense-in-depth)."""
        if actor is None:
            return False
        cost_center = self._cc_repo.get_by_id(cost_center_id)
        if cost_center is None:
            return False
        # CLOSED cost centers cannot be modified; ACTIVE can be
        return cost_center.status == CostCenterStatus.ACTIVE.value


class CoaDimensionService:
    """Enforces Dimension business rules; no Flask/SQLAlchemy imports."""

    def __init__(
        self,
        dimension_repo: DimensionRepositoryPort,
    ) -> None:
        self._dim_repo = dimension_repo

    # ── Creation ──────────────────────────────────────────────────

    def create_dimension(
        self,
        code: str,
        name: str,
        dimension_type: DimensionType,
        company_id: UUID,
        actor: UUID,  # must be CHIEF_ACCOUNTANT or admin
        is_system: bool = False,
        description: str | None = None,
    ) -> Dimension:
        """Create new dimension with full invariant validation."""
        if actor is None:
            raise DomainException("Actor UUID required on mutations (D11)")

        # Validate code format (DimensionCode VO)
        try:
            from src.domain.entities.cost_center import DimensionCode  # local import
            DimensionCode(code, DimensionType.CUSTOM)  # may raise
        except DomainException as e:
            raise DomainException(f"Invalid dimension code: {e}") from e

        # Check code uniqueness per company
        existing = self._dim_repo.get_by_code(code, company_id)
        if existing is not None:
            raise DuplicateMSTError(
                f"Dimension code {code} already exists for company {company_id}"
            )

        # Build domain entity
        dimension = Dimension(
            code=code,
            name=name,
            dimension_type=dimension_type,
            company_id=company_id,
            created_by=actor,
            is_system=is_system,
            description=description,
        )

        # Persist via repo
        created = self._dim_repo.create(dimension)
        db.session.flush()
        return created

    # ── Modification ──────────────────────────────────────────────

    def update_dimension(
        self,
        dimension_id: UUID,
        *,
        new_name: str | None = None,
        actor: UUID,
        reason: str,
    ) -> Dimension:
        """Modify dimension name; system dimensions require migration."""
        if actor is None:
            raise DomainException("Actor UUID required")

        # Fetch current dimension
        dimension = self._dim_repo.get_by_id(dimension_id)
        if dimension is None:
            raise ValueError(f"Dimension {dimension_id} not found")

        # Prohibit modification of system dimensions at domain level
        if dimension.is_system:
            raise SystemAccountModificationError(
                "System dimension modification requires migration module; contact admin"
            )

        # Apply modification via domain method
        try:
            dimension.modify(new_name=new_name, actor=actor, reason=reason)
        except (DomainException, SystemAccountModificationError) as e:
            raise e

        # Persist
        updated = self._dim_repo.update(dimension)
        db.session.flush()
        return updated

    # ── Listing & Search ──────────────────────────────────────────

    def list_by_company(
        self,
        company_id: UUID,
        *,
        dimension_type: DimensionType | None = None,
        is_system: bool | None = None,
    ) -> list[Dimension]:
        return self._dim_repo.list_by_company(
            company_id, dimension_type=dimension_type, is_system=is_system
        )

    def can_modify_dimension(self, dimension_id: UUID, actor: UUID) -> bool:
        """Check if actor can modify a dimension (defense-in-depth)."""
        if actor is None:
            return False
        dimension = self._dim_repo.get_by_id(dimension_id)
        if dimension is None:
            return False
        # System dimensions require migration module
        if dimension.is_system:
            return False
        return True


class CoaDimensionValueService:
    """Enforces Dimension Value business rules; no Flask/SQLAlchemy imports."""

    def __init__(
        self,
        dimension_value_repo: DimensionValueRepositoryPort,
    ) -> None:
        self._dv_repo = dimension_value_repo

    # ── Creation ──────────────────────────────────────────────────

    def create_dimension_value(
        self,
        code: str,
        name: str,
        dimension_id: UUID,
        company_id: UUID,
        actor: UUID,  # must be CHIEF_ACCOUNTANT or admin
        description: str | None = None,
    ) -> DimensionValue:
        """Create new dimension value with full invariant validation."""
        if actor is None:
            raise DomainException("Actor UUID required on mutations (D11)")

        # Validate code format (DimensionCode VO)
        try:
            from src.domain.entities.cost_center import DimensionCode  # local import
            DimensionCode(code, DimensionType.CUSTOM)  # may raise
        except DomainException as e:
            raise DomainException(f"Invalid dimension value code: {e}") from e

        # Check code uniqueness per (dimension_id, company)
        existing = self._dv_repo.get_by_code(code, company_id)
        if existing is not None:
            raise DuplicateMSTError(
                f"Dimension Value code {code} already exists for dimension {dimension_id}"
            )

        # Build domain entity
        dimension_value = DimensionValue(
            code=code,
            name=name,
            dimension_id=dimension_id,
            company_id=company_id,
            created_by=actor,
            description=description,
        )

        # Persist via repo
        created = self._dv_repo.create(dimension_value)
        db.session.flush()
        return created

    # ── Modification ──────────────────────────────────────────────

    def update_dimension_value(
        self,
        dv_id: UUID,
        *,
        new_name: str | None = None,
        actor: UUID,
        reason: str,
    ) -> DimensionValue:
        """Modify dimension value name; requires actor and reason; audit logged."""
        if actor is None:
            raise DomainException("Actor UUID required")

        # Fetch current dimension value
        dimension_value = self._dv_repo.get_by_id(dv_id)
        if dimension_value is None:
            raise ValueError(f"Dimension Value {dv_id} not found")

        # Apply modification via domain method
        try:
            dimension_value.modify(new_name=new_name, actor=actor, reason=reason)
        except DomainException as e:
            raise e

        # Persist
        updated = self._dv_repo.update(dimension_value)
        db.session.flush()
        return updated

    # ── Deactivation/Reactivation ──────────────────────────────────

    def deactivate_dimension_value(self, dv_id: UUID, actor: UUID, reason: str) -> DimensionValue:
        """Deactivate dimension value: ACTIVE → INACTIVE."""
        if actor is None:
            raise DomainException("Actor UUID required")

        dimension_value = self._dv_repo.get_by_id(dv_id)
        if dimension_value is None:
            raise ValueError(f"Dimension Value {dv_id} not found")

        if dimension_value.status != DimensionValueStatus.ACTIVE:
            raise ValueError(
                f"Cannot deactivate dimension value {dimension_value.code}: current status is {dimension_value.status.value}"
            )

        # Set status to INACTIVE via update
        dimension_value.status = DimensionValueStatus.INACTIVE
        updated = self._dv_repo.update(dimension_value)
        db.session.flush()
        return updated

    def reactivate_dimension_value(self, dv_id: UUID, actor: UUID, reason: str) -> DimensionValue:
        """Reactivate dimension value: INACTIVE → ACTIVE."""
        if actor is None:
            raise DomainException("Actor UUID required")

        dimension_value = self._dv_repo.get_by_id(dv_id)
        if dimension_value is None:
            raise ValueError(f"Dimension Value {dv_id} not found")

        if dimension_value.status != DimensionValueStatus.INACTIVE:
            raise ValueError(
                f"Cannot reactivate dimension value {dimension_value.code}: current status is {dimension_value.status.value}"
            )

        dimension_value.reactivate(actor=actor, reason=reason)
        updated = self._dv_repo.update(dimension_value)
        db.session.flush()
        return updated

    # ── Listing & Search ──────────────────────────────────────────

    def list_by_company(
        self,
        company_id: UUID,
        *,
        dimension_id: UUID | None = None,
        status: DimensionValueStatus | None = None,
    ) -> list[DimensionValue]:
        return self._dv_repo.list_by_company(
            company_id, dimension_id=dimension_id, status=status
        )

    def can_modify_dimension_value(self, dv_id: UUID, actor: UUID) -> bool:
        """Check if actor can modify a dimension value (defense-in-depth)."""
        if actor is None:
            return False
        dimension_value = self._dv_repo.get_by_id(dv_id)
        if dimension_value is None:
            return False
        return True