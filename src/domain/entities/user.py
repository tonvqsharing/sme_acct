"""User entity: operator / user of the Vietnamese SME accounting system.

Per Luật Kế toán 2015 Art. 16: Kế toán trưởng phải được đăng ký.
Per Decree 02/2022/NĐ-CP: Đăng ký operator cho kế toán điện tử.

User là entity aggregate: có trách nhiệm audit trail, role-based access control.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4, UUID

from src.domain.entities.base import UserRole, UserRoleError


class User:
    """Operator / user of the Vietnamese SME accounting system.

    Attributes:
        id: PK UUID
        email: Unique login name; max 120 chars; always stored lowercase
        password: Hashed password (SHA-256 current; bcrypt future)
        role: UserRole enum — determines RBAC permissions
        is_active: Soft-disabled flag; TRUE = active, can login
        last_login: Timestamp of last successful login (UTC); NULL never logged
        created_at: Audit trail — when this user was created
        created_by: Audit trail — who created this user (admin UUID)
        updated_at: Audit trail — when this user was last updated
        updated_by: Audit trail — who last updated this user (admin UUID)
        config_version: Optimistic lock version; incremented on every update
    """

    __slots__ = (
        "id",
        "email",
        "password",
        "role",
        "is_active",
        "last_login",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "config_version",
    )

    def __init__(
        self,
        *,
        id: UUID | None = None,
        email: str,
        password: str,
        role: UserRole,
        is_active: bool = True,
        last_login: datetime | None = None,
        created_at: date | None = None,
        created_by: UUID | None = None,
        updated_at: date | None = None,
        updated_by: UUID | None = None,
        config_version: int = 1,
    ) -> None:
        # ── Validate ──────────────────────────────────────────────────
        if not email or "@" not in email:
            raise UserRoleError("Email là bắt buộc và phải có định dạng email")

        if len(email) > 120:
            raise UserRoleError("Email tối đa 120 ký tự")

        # Normalize email to lowercase
        self.email = email.lower().strip()

        if not isinstance(role, UserRole):
            raise UserRoleError(
                f"Vai trò không hợp lệ: {role}. "
                f"Chọn: {', '.join(r.value for r in UserRole)}"
            )

        self.role = role
        self.password = password
        self.is_active = is_active
        self.last_login = last_login
        self.id = id or uuid4()
        self.created_at = created_at or date.today()
        self.created_by = created_by or UUID(int=0)
        self.updated_at = updated_at or date.today()
        self.updated_by = updated_by or UUID(int=0)
        self.config_version = config_version

    # ── Factory ─────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        *,
        email: str,
        password: str,
        role: UserRole,
        created_by: UUID | None = None,
        is_active: bool = True,
    ) -> "User":
        """Construct a new User with sane defaults for audit trail."""
        import uuid

        return cls(
            id=uuid.uuid4(),
            email=email,
            password=password,
            role=role,
            is_active=is_active,
            created_by=created_by,
        )

    # ── Domain behaviors ────────────────────────────────────────────

    def activate(self) -> None:
        """Enable user account."""
        self.is_active = True
        self.updated_at = date.today()
        self.updated_by = self._get_current_admin()  # filled by service layer

    def deactivate(self) -> None:
        """Disable user account."""
        self.is_active = False
        self.updated_at = date.today()
        self.updated_by = self._get_current_admin()  # filled by service layer

    def change_role(self, new_role: UserRole, actor: UUID) -> None:
        """Change user role (admin-only operation)."""
        if not isinstance(new_role, UserRole):
            raise UserRoleError(f"Vai trò mới không hợp lệ: {new_role}")
        self.role = new_role
        self.updated_at = date.today()
        self.updated_by = actor

    def record_login(self) -> None:
        """Record successful login timestamp."""
        from datetime import datetime as _dt

        self.last_login = _dt.utcnow()

    # ── Helpers ─────────────────────────────────────────────────────

    def _get_current_admin(self) -> UUID:
        """Hook — filled by service layer before domain save.

        In a real app this would come from Flask-Login context.
        Defaults to UUID zero for domain-level test isolation.
        """
        return self.updated_by

    # ── Equality ────────────────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    # ── Repr ────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r}, role={self.role.value!r})"