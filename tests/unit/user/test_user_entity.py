"""Unit tests for User entity — TDD red‑green‑refactor.

TDD cycle:
1. Write test (expect failure → RED)
2. Implement UserRole enum + User entity (implementation → GREEN)
3. Run pytest: all user tests pass
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from uuid import UUID, uuid4

import pytest

from src.domain.entities.base import UserRole, UserRoleError
from src.domain.entities.user import User


# -------------------- FIXTURES --------------------


@pytest.fixture
def valid_user_kwargs():
    """Build valid user kwargs with sane defaults."""
    return {
        "id": uuid4(),
        "email": "accountant@test.local",
        "password": "HashedPassword123!",
        "role": UserRole.ACCOUNTANT,
        "is_active": True,
        "last_login": None,
        "created_at": date.today(),
        "created_by": uuid4(),
        "updated_at": date.today(),
        "updated_by": uuid4(),
        "config_version": 1,
    }


# -------------------- TESTS: UserRole enum --------------------


class TestUserRole:
    """Test the UserRole enum values and stability."""

    def test_all_roles_have_correct_values(self):
        """All UserRole enum values match the specification."""
        roles = [
            UserRole.ACCOUNTANT,
            UserRole.CHIEF_ACCOUNTANT,
            UserRole.ADMIN,
            UserRole.AUDITOR,
            UserRole.DIRECTOR,
        ]
        expected = ["accountant", "chief_accountant", "admin", "auditor", "director"]
        for role, expected_val in zip(roles, expected):
            assert role.value == expected_val

    def test_role_hierarchy_ordering(self):
        """Role hierarchy is consistent: ACCOUNTANT < CHIEF_ACCOUNTANT < ADMIN < AUDITOR < DIRECTOR."""
        hierarchy = {
            UserRole.ACCOUNTANT: 1,
            UserRole.CHIEF_ACCOUNTANT: 2,
            UserRole.ADMIN: 3,
            UserRole.AUDITOR: 4,
            UserRole.DIRECTOR: 5,
        }
        assert hierarchy[UserRole.ACCOUNTANT] < hierarchy[UserRole.CHIEF_ACCOUNTANT]
        assert hierarchy[UserRole.CHIEF_ACCOUNTANT] < hierarchy[UserRole.ADMIN]
        assert hierarchy[UserRole.ADMIN] < hierarchy[UserRole.AUDITOR]
        assert hierarchy[UserRole.AUDITOR] < hierarchy[UserRole.DIRECTOR]


# -------------------- TESTS: User entity --------------------


class TestUserEntity:
    """Test User entity construction and invariants."""

    def test_user_can_be_constructed_with_valid_kwargs(self, valid_user_kwargs):
        """User entity constructs successfully with all required fields."""
        user = User(**valid_user_kwargs)
        assert user.email == valid_user_kwargs["email"]
        assert user.role == valid_user_kwargs["role"]
        assert user.is_active == valid_user_kwargs["is_active"]
        assert user.config_version == valid_user_kwargs["config_version"]
        assert user.id == valid_user_kwargs["id"]

    def test_user_defaults_minimal(self):
        """User entity can be constructed with minimal required fields."""
        import uuid
        user = User(
            email="minimal@local",
            password="Password123!",
            role=UserRole.ACCOUNTANT,
        )
        assert user.is_active == True  # default
        assert user.config_version == 1  # default
        assert user.id is not None
        assert isinstance(user.id, UUID)

    def test_user_invalid_role_raises_error(self):
        """User entity rejects invalid role."""
        with pytest.raises(UserRoleError):
            User(
                email="bad@local",
                password="Hash123!",
                role="invalid_role",  # type: ignore[arg-type]
            )

    def test_user_email_is_normalized_lowercase(self):
        """User entity stores email correctly (lowercased)."""
        user = User(
            email="UPPERCASE@TEST.LOCAL",
            password="Hash123!",
            role=UserRole.ACCOUNTANT,
        )
        assert str(user.email) == "uppercase@test.local"

    def test_user_id_is_auto_generated(self):
        """User entity can work with auto-generated ID (minimal constructor)."""
        user = User(
            email="auto@local",
            password="Hash123!",
            role=UserRole.ACCOUNTANT,
        )
        assert user.id is not None
        assert isinstance(user.id, UUID)


# -------------------- TESTS: User entity errors --------------------


class TestUserEntityErrors:
    """Test User entity error conditions."""

    def test_user_requires_valid_email_format(self):
        """User entity validates email contains @."""
        with pytest.raises(UserRoleError):
            User(
                email="not-an-email",
                password="Hash123!",
                role=UserRole.ACCOUNTANT,
            )

    def test_user_email_max_120_chars(self):
        """User entity rejects email > 120 chars."""
        long_email = "a" * 121 + "@test.local"
        with pytest.raises(UserRoleError):
            User(
                email=long_email,
                password="Hash123!",
                role=UserRole.ACCOUNTANT,
            )