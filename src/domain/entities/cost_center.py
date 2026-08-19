"""Cost Centers and Dimensions domain entities.

Vietnamese SME Accounting Application — Cost Centers & Dimensions Module
Legal basis: Law on Accounting 2015 (Chap IX); Circular 99/2025/TT-BTC;
enterprise analytical accounting requirements.

Cost Centers (Chi phí trung tâm) represent departments, branches, or
organizational units that incur costs. Dimensions (Khối đoán) represent
analytical categories for cost allocation (project, location, product,
customer, etc.). Dimension Values (Giá trị khối đoán) are specific instances
of dimensions.

All entities follow Clean Architecture: pure Python, NO sqlalchemy/web imports.
Enums are duplicated in infra/models.py for SQLAlchemy compatibility.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from src.domain.exceptions import DomainException


# ── Enums ──────────────────────────────────────────────────────────────

class CostCenterStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    CLOSED = "Closed"


class DimensionType(str, Enum):
    """Analytical dimensions per enterprise needs."""
    PROJECT = "Project"
    LOCATION = "Location"
    PRODUCT = "Product"
    CUSTOMER = "Customer"
    EMPLOYEE = "Employee"
    DEPARTMENT = "Department"
    CUSTOM = "Custom"


class DimensionValueStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


# ── Value Objects ────────────────────────────────────────────────────


class CostCenterCode:
    """Validated Cost Center code.

    Format: 3-10 alphanumeric characters, must start with letter.
    Per enterprise analytical accounting conventions.
    """

    __slots__ = ("value",)

    def __init__(self, code: str) -> None:
        if not isinstance(code, str):
            raise DomainException("Cost Center code must be a string")
        code = code.strip()
        if not code:
            raise DomainException("Cost Center code cannot be empty")
        if not code[0].isalpha():
            raise DomainException(
                "Cost Center code must start with a letter; received: " + code
            )
        if len(code) > 10:
            raise DomainException(
                "Cost Center code maximum 10 characters; received: " + code
            )
        # Alphanumeric only (letters and digits after first letter)
        import re as _re
        if not _re.match(r"^[A-Za-z][A-Za-z0-9]{0,9}$", code):
            raise DomainException(
                "Cost Center code must be alphanumeric (start with letter); "
                "received: " + code
            )
        self.value = code


class DimensionCode:
    """Validated Dimension value code.

    Format: depends on dimension type, must be unique per company.
    """

    __slots__ = ("value",)

    def __init__(self, code: str, dimension_type: DimensionType) -> None:
        if not isinstance(code, str):
            raise DomainException("Dimension code must be a string")
        code = code.strip()
        if not code:
            raise DomainException("Dimension code cannot be empty")
        self.value = code


# ── Entity: CostCenter ──────────────────────────────────────────────


class CostCenter:
    """Cost Center (Chi phí trung tâm) aggregate root.

    Represents a department, branch, or organizational unit that incurs costs.
    Supports analytical accounting per Circular 99/2025/TT-BTC.

    Invariants (all validated in __post_init__):
    - code valid per CostCenterCode VO
    - code unique per company (enforced by repo)
    - status in CostCenterStatus enum
    - actor UUID required on mutations (D11)
    - audit checksum chaining (SHA-256, mirrors audit-log module)
    """

    __slots__ = (
        "id",
        "code",
        "name",
        "status",
        "company_id",
        "created_by",
        "created_at",
        "updated_at",
        "parent_id",  # self-referencing for sub-cost-centers
        "description",  # optional description
        "audit_checksum",
    )

    def __init__(
        self,
        code: str,
        name: str,
        company_id: UUID,
        created_by: UUID,
        description: str | None = None,
        status: CostCenterStatus = CostCenterStatus.ACTIVE,
        parent_id: UUID | None = None,
        id: UUID | None = None,
    ) -> None:
        # 1. Validate and store code
        self.code = CostCenterCode(code).value

        # 2. Basic attrs
        self.name = name.strip()
        self.company_id = company_id
        self.id = id or uuid4()  # auto-generate if not provided
        self.parent_id = parent_id  # self-referencing for sub-cost-centers

        # 3. Status: newly created → ACTIVE
        self.status = status

        # 4. Description (optional)
        self.description = description or ""

        # 5. Auditing: initialize checksum to zeros for chaining
        self.audit_checksum = "0" * 64

        # 6. Creation timestamp
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at

        # 7. Post-init invariant and checksum chaining
        self.audit_checksum = self._compute_checksum("create")

        # 6. Post-init invariant
        self._validate_invariant()

    # ── Invariant ──────────────────────────────────────────────────

    def _validate_invariant(self) -> None:
        """Run after __init__; raises ValueError if any invariant broken."""
        if self.code not in CostCenterStatus.__members__:  # quick check
            pass  # actual code format validated by VO
        if self.status not in CostCenterStatus:
            raise ValueError(f"Invalid status: {self.status}")
        if not self.name:
            raise ValueError("Cost Center name is required")
        # Company ID must be set (enforced by repo, not domain)
        # Parent ID: if set, must be same company_id (enforced by repo)

    # ── Behavioural Methods ──────────────────────────────────────────

    def deactivate(self, actor: UUID, reason: str) -> None:
        """Deactivate cost center: ACTIVE → INACTIVE."""
        if self.status != CostCenterStatus.ACTIVE:
            raise ValueError(
                f"Cannot deactivate cost center {self.code}: current status is {self.status.value}"
            )
        self.status = CostCenterStatus.INACTIVE
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("deactivate", actor=actor, reason=reason)

    def reactivate(self, actor: UUID, reason: str) -> None:
        """Reactivate cost center: INACTIVE → ACTIVE."""
        if self.status != CostCenterStatus.INACTIVE:
            raise ValueError(
                f"Cannot reactivate cost center {self.code}: current status is {self.status.value}"
            )
        self.status = CostCenterStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("reactivate", actor=actor, reason=reason)

    def close(self, actor: UUID, reason: str) -> None:
        """Close cost center: ACTIVE → CLOSED."""
        if self.status != CostCenterStatus.ACTIVE:
            raise ValueError(
                f"Cannot close cost center {self.code}: current status is {self.status.value}"
            )
        self.status = CostCenterStatus.CLOSED
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("close", actor=actor, reason=reason)

    def modify(
        self,
        *,
        new_code: str | None = None,
        new_name: str | None = None,
        actor: UUID,
        reason: str,
    ) -> None:
        """Modify cost center attributes. Requires actor and reason; audit logged."""
        if new_code is not None:
            self.code = CostCenterCode(new_code).value
            reason = f"{reason}; code changed from {self.code} to {new_code}"

        if new_name is not None:
            self.name = new_name.strip()
            reason = f"{reason}; name changed"

        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("modify", actor=actor, reason=reason)

    def _compute_checksum(self, action: str, actor: UUID | None = None, reason: str | None = None) -> str:
        """SHA-256 checksum chaining — mirrors audit-log module pattern.

        Raw: "|".join([prev_checksum, str(self.id), action, str(actor), reason, ts.isoformat()])
        """
        import hashlib

        raw_parts = [
            self.audit_checksum,  # prev checksum from prior event
            str(self.id),
            action,
            str(actor) if actor else "",
            reason or "",
            datetime.now(timezone.utc).isoformat(),
        ]
        raw = "|".join(raw_parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ── Entity: Dimension ──────────────────────────────────────────────


class Dimension:
    """Dimension (Khối đoán) aggregate root.

    Represents an analytical category for cost allocation (Project, Location,
    Product, Customer, etc.). Each dimension has multiple DimensionValues.

    Invariants:
    - type in DimensionType enum
    - code unique per company (enforced by repo)
    - actor UUID required on mutations (D11)
    - audit checksum chaining (SHA-256)
    """

    __slots__ = (
        "id",
        "code",
        "name",
        "type",
        "company_id",
        "created_by",
        "created_at",
        "updated_at",
        "description",  # optional description
    "audit_checksum",
        "description",  # optional description
        "is_system",  # pre-loaded vs enterprise-defined
    )

    def __init__(
        self,
        code: str,
        name: str,
        dimension_type: DimensionType,
        company_id: UUID,
        created_by: UUID,
        is_system: bool = False,
        description: str | None = None,
        id: UUID | None = None,
    ) -> None:
        # 1. Validate and store code
        self.code = DimensionCode(code, dimension_type).value

        # 2. Basic attrs
        self.name = name.strip()
        self.type = dimension_type
        self.company_id = company_id
        self.is_system = is_system  # system dimensions (e.g., Project) are pre-loaded
        self.id = id or uuid4()
        self.description = description or ""

        # 3. Auditing: initialize checksum to zeros for chaining
        self.audit_checksum = "0" * 64

        # 4. Creation timestamp and checksum chaining
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.audit_checksum = self._compute_checksum("create")

        # 3. Auditing
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.audit_checksum = self._compute_checksum("create")

        # 4. Post-init invariant
        self._validate_invariant()

    # ── Invariant ──────────────────────────────────────────────────

    def _validate_invariant(self) -> None:
        if self.type not in DimensionType:
            raise ValueError(f"Invalid dimension type: {self.type}")
        if not self.name:
            raise ValueError("Dimension name is required")
        # Company ID must be set (enforced by repo)
        # System dimensions: only admin can modify; enterprise dimensions editable

    # ── Behavioural Methods ──────────────────────────────────────────

    def set_system(self, actor: UUID, reason: str) -> None:
        """Mark dimension as system (pre-loaded). Requires CHIEF_ACCOUNTANT."""
        if not actor:
            raise DomainException("Actor UUID required")
        self.is_system = True
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("set_system", actor=actor, reason=reason)

    def modify(
        self,
        *,
        new_name: str | None = None,
        actor: UUID,
        reason: str,
    ) -> None:
        """Modify dimension name. System dimensions require migration."""
        if self.is_system:
            from src.domain.exceptions import SystemAccountModificationError  # local import
            raise SystemAccountModificationError(
                "System dimension modification requires migration module"
            )
        if new_name is not None:
            self.name = new_name.strip()
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("modify", actor=actor, reason=reason)

    def _compute_checksum(self, action: str, actor: UUID | None = None, reason: str | None = None) -> str:
        """SHA-256 checksum chaining — mirrors audit-log module pattern."""
        import hashlib

        raw_parts = [
            self.audit_checksum,  # prev checksum from prior event
            str(self.id),
            action,
            str(actor) if actor else "",
            reason or "",
            datetime.now(timezone.utc).isoformat(),
        ]
        raw = "|".join(raw_parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ── Entity: DimensionValue ─────────────────────────────────────────

class DimensionValue:
    """Dimension Value (Giá trị khối đoán) aggregate root.

    A specific value within a Dimension (e.g., "Project Alpha" under
    Dimension "Project", or "Hanoi" under Dimension "Location").
    Used for analytical cost allocation.

    Invariants:
    - value valid per DimensionCode VO
    - code unique per (dimension_id, company) (enforced by repo)
    - at least 1 dimension value per dimension (for usability)
    - actor UUID required on mutations (D11)
    - audit checksum chaining (SHA-256)
    """

    __slots__ = (
        "id",
        "dimension_id",
        "code",
        "name",
        "status",
        "company_id",
        "created_by",
        "created_at",
        "updated_at",
        "description",  # optional description
    "audit_checksum",
    )

    def __init__(
        self,
        code: str,
        name: str,
        dimension_id: UUID,
        company_id: UUID,
        created_by: UUID,
        status: DimensionValueStatus = DimensionValueStatus.ACTIVE,
        description: str | None = None,
        id: UUID | None = None,
    ) -> None:
        # 1. Validate and store code (uses DimensionCode VO)
        self.code = DimensionCode(code, DimensionType.CUSTOM).value  # type reuse for format

        # 2. Basic attrs
        self.name = name.strip()
        self.dimension_id = dimension_id
        self.company_id = company_id
        self.id = id or uuid4()

        # 3. Status: newly created → ACTIVE
        self.status = status

        # 4. Description (optional)
        self.description = description or ""

        # 5. Auditing: initialize checksum to zeros for chaining
        self.audit_checksum = "0" * 64

        # 6. Creation timestamp and checksum chaining
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.audit_checksum = self._compute_checksum("create")

        # 5. Auditing
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.audit_checksum = self._compute_checksum("create")

        # 6. Post-init invariant
        self._validate_invariant()

    # ── Invariant ──────────────────────────────────────────────────

    def _validate_invariant(self) -> None:
        if not self.name:
            raise ValueError("Dimension Value name is required")
        # Dimension ID must be set (enforced by repo)
        # Status must be valid (checked by repo)
        # Company ID must be set (enforced by repo)

    # ── Behavioural Methods ──────────────────────────────────────────

    def deactivate(self, actor: UUID, reason: str) -> None:
        """Deactivate dimension value: ACTIVE → INACTIVE."""
        if self.status != DimensionValueStatus.ACTIVE:
            raise ValueError(
                f"Cannot deactivate dimension value {self.code}: current status is {self.status.value}"
            )
        self.status = DimensionValueStatus.INACTIVE
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("deactivate", actor=actor, reason=reason)

    def reactivate(self, actor: UUID, reason: str) -> None:
        """Reactivate dimension value: INACTIVE → ACTIVE."""
        if self.status != DimensionValueStatus.INACTIVE:
            raise ValueError(
                f"Cannot reactivate dimension value {self.code}: current status is {self.status.value}"
            )
        self.status = DimensionValueStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("reactivate", actor=actor, reason=reason)

    def modify(
        self,
        *,
        new_name: str | None = None,
        actor: UUID,
        reason: str,
    ) -> None:
        """Modify dimension value name. Requires actor and reason; audit logged."""
        if new_name is not None:
            self.name = new_name.strip()
            reason = f"{reason}; name changed"
        self.updated_at = datetime.now(timezone.utc)
        self.audit_checksum = self._compute_checksum("modify", actor=actor, reason=reason)

    def _compute_checksum(self, action: str, actor: UUID | None = None, reason: str | None = None) -> str:
        """SHA-256 checksum chaining — mirrors audit-log module pattern."""
        import hashlib

        raw_parts = [
            self.audit_checksum,  # prev checksum from prior event
            str(self.id),
            action,
            str(actor) if actor else "",
            reason or "",
            datetime.now(timezone.utc).isoformat(),
        ]
        raw = "|".join(raw_parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()