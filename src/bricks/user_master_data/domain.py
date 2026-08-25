"""User master data domain — per docs/user-master-data/specs §2.

Deviation from spec: password hashing uses werkzeug pbkdf2/scrypt
instead of spec's SHA-256 placeholder — SHA-256 is unsalted and too
fast for passwords; werkzeug is already in the stack. Spec notes
bcrypt as the future direction; pbkdf2 satisfies that intent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from werkzeug.security import check_password_hash, generate_password_hash

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 8


class UserRole(Enum):
    """Roles per quy định nội bộ hệ thống SME accounting."""

    # Values are UPPERCASE to match the house RBAC gate convention
    # used across all bricks (current_user.role == "ADMIN" etc.)
    ACCOUNTANT = "ACCOUNTANT"
    CHIEF_ACCOUNTANT = "CHIEF_ACCOUNTANT"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"
    DIRECTOR = "DIRECTOR"


class InvalidEmailError(ValueError):
    code = "INVALID_EMAIL"


@dataclass
class User:
    email: str
    role: UserRole
    full_name: str
    password: str = ""  # hashed at service layer via set_password()
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    last_login: datetime | None = None

    def __post_init__(self) -> None:
        if not EMAIL_RE.match(self.email or ""):
            raise InvalidEmailError(f"Invalid email: '{self.email}'")
        if not isinstance(self.role, UserRole):
            raise TypeError("role must be a UserRole")

    def set_password(self, plaintext: str) -> None:
        if len(plaintext) < MIN_PASSWORD_LEN:
            raise ValueError(f"Password must be >= {MIN_PASSWORD_LEN} chars")
        self.password = generate_password_hash(plaintext)

    def verify_password(self, plaintext: str) -> bool:
        if not self.password:
            return False
        return check_password_hash(self.password, plaintext)

    def get_id(self) -> str:
        """Flask-Login contract."""
        return str(self.id)

    @property
    def is_authenticated(self) -> bool:
        return self.is_active

    @property
    def is_anonymous(self) -> bool:
        return False

    def touch_login(self) -> None:
        self.last_login = datetime.now(UTC)
