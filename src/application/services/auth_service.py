"""Authentication and authorization service for user/role management.

Provides:
- User model with email, role, is_active, last_login
- Admin creation (first user becomes ADMIN)
- Password reset
- Role assignment
- Account enable/disable
- User listing

Uses Flask application context via current_app to access the db.
Follows clean architecture — domain layer has zero Flask/SQLAlchemy imports.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from flask import current_app
from sqlalchemy import text


def _get_db() -> object:
    """Get the Flask-SQLAlchemy db instance from the current app.

    Returns the `db` object initialized via `db.init_app(app)` in the
    application factory (app.py). Safe to call only within an app context.
    """
    migrate = current_app.extensions["migrate"]  # type: ignore[attr-defined]
    return migrate.db  # type: ignore[return-value]


def _ensure_users_table() -> None:
    """Ensure the 'users' table exists in the database.

    Creates the table if it doesn't exist. Idempotent — safe to call
    on every request within an app context.
    """
    _db = _get_db()

    # Check if users table exists by trying a simple query
    try:
        result = _db.session.execute(text("SELECT 1 FROM users LIMIT 1"))
        result.fetchone()  # table exists
    except Exception:
        # Table doesn't exist — create it
        _db.session.execute(
            text(
                """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'ACCOUNTANT',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                last_login DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
            )
        )
        _db.session.commit()


class AuthService:
    """Authentication and authorization service.

    Uses Flask application context to access the database.
    All methods must be called within a Flask app context.
    """

    def __init__(self) -> None:
        _ensure_users_table()
        self.db = _get_db()

    # ── Creation ──────────────────────────────────────────────────────────

    def create_admin(self) -> object:
        """Create the first admin user.

        Only callable once — if a user with role=ADMIN already exists,
        raises ValueError. The admin's password is set to a random
        16-char string (hashed); return value includes the temp password
        for the initial login.
        """
        # Check if any admin exists
        stmt = text("SELECT COUNT(*) FROM users WHERE role = 'ADMIN'")
        result = self.db.session.execute(stmt).fetchone()
        if result and result[0] > 0:
            raise ValueError("Admin user already exists — use reset-password instead.")

        # Generate temporary password
        temp_password = secrets.token_urlsafe(16)

        # Hash password
        password_hash = hashlib.sha256(temp_password.encode()).hexdigest()

        # Create admin user
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.session.execute(
            text(
                """
            INSERT INTO users (email, password, role, is_active, last_login, created_at, updated_at)
            VALUES (:email, :password, 'ADMIN', 1, :last_login, :now, :now)
            """
            ),
            {
                "email": "admin@sme-acct.local",
                "password": password_hash,
                "last_login": now,
                "now": now,
            },
        )
        self.db.session.commit()

        # Return a simple object with the needed attributes
        class _Admin:
            id = 1
            email = "admin@sme-acct.local"
            role = "ADMIN"
            is_active = True
            last_login = datetime.now(timezone.utc)

        return _Admin()

    def create_user(self, email: str, role: str = "ACCOUNTANT", password: str | None = None) -> object:
        """Create a new user with the given role.

        Args:
            email: User email (must be unique)
            role: One of: ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, AUDITOR, DIRECTOR
            password: Plain-text password. If None, generates a random 16-char password.

        Returns:
            User object with id, email, role, is_active attributes.

        Raises:
            ValueError: If role is invalid or user already exists.
        """
        valid_roles = {"ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR"}
        if role not in valid_roles:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of: {', '.join(sorted(valid_roles))}"
            )

        # Check if user already exists
        stmt = text("SELECT COUNT(*) FROM users WHERE email = :email")
        result = self.db.session.execute(stmt, {"email": email}).fetchone()
        if result and result[0] > 0:
            raise ValueError(f"User with email '{email}' already exists.")

        # Generate password if not provided
        if password is None:
            password = secrets.token_urlsafe(16)

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Create user
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.session.execute(
            text(
                """
            INSERT INTO users (email, password, role, is_active, last_login, created_at, updated_at)
            VALUES (:email, :password, :role, 1, :last_login, :now, :now)
            """
            ),
            {
                "email": email,
                "password": password_hash,
                "role": role,
                "last_login": now,
                "now": now,
            },
        )
        self.db.session.commit()

        # Return a simple object with the needed attributes
        class _User:
            id = 1  # Will be set properly below
            email_val = email
            role_val = role
            is_active_val = True
            last_login_val = datetime.now(timezone.utc)

        # Fetch the actual ID
        stmt2 = text("SELECT id FROM users WHERE email = :email")
        result2 = self.db.session.execute(stmt2, {"email": email}).fetchone()
        if result2:
            _User.id = result2[0]
            _User.email_val = email
            _User.role_val = role
            _User.is_active_val = True
            _User.last_login_val = datetime.now(timezone.utc)

        return _User()

    # ── Password ──────────────────────────────────────────────────────────

    def reset_password(self, user_identifier: str, new_password: str) -> None:
        """Reset a user's password.

        Args:
            user_identifier: Username (email) or user ID
            new_password: New plain-text password
        """
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()

        # Try by email first
        stmt = text("UPDATE users SET password = :pw WHERE email = :email")
        result = self.db.session.execute(stmt, {"pw": password_hash, "email": user_identifier})
        if result.rowcount == 0:
            # Try by ID
            stmt2 = text("UPDATE users SET password = :pw WHERE id = :uid")
            result2 = self.db.session.execute(stmt2, {"pw": password_hash, "uid": int(user_identifier)})
            if result2.rowcount == 0:
                raise LookupError(f"User '{user_identifier}' not found")
        self.db.session.commit()

    # ── Role ──────────────────────────────────────────────────────────────

    def assign_role(self, user_identifier: str, role: str) -> None:
        """Assign a role to a user.

        Args:
            user_identifier: Username (email) or user ID
            role: One of: ACCOUNTANT, CHIEF_ACCOUNTANT, ADMIN, AUDITOR, DIRECTOR
        """
        valid_roles = {"ACCOUNTANT", "CHIEF_ACCOUNTANT", "ADMIN", "AUDITOR", "DIRECTOR"}
        if role not in valid_roles:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of: {', '.join(sorted(valid_roles))}"
            )

        # Try by email first
        stmt = text("UPDATE users SET role = :role WHERE email = :email")
        result = self.db.session.execute(stmt, {"role": role, "email": user_identifier})
        if result.rowcount == 0:
            # Try by ID
            stmt2 = text("UPDATE users SET role = :role WHERE id = :uid")
            result2 = self.db.session.execute(stmt2, {"role": role, "uid": int(user_identifier)})
            if result2.rowcount == 0:
                raise LookupError(f"User '{user_identifier}' not found")
        self.db.session.commit()

    # ── Account status ────────────────────────────────────────────────────

    def enable_user(self, user_identifier: str) -> None:
        """Enable a user account."""
        # Try by email first
        stmt = text("UPDATE users SET is_active = 1 WHERE email = :email")
        result = self.db.session.execute(stmt, {"email": user_identifier})
        if result.rowcount == 0:
            # Try by ID
            stmt2 = text("UPDATE users SET is_active = 1 WHERE id = :uid")
            result2 = self.db.session.execute(stmt2, {"uid": int(user_identifier)})
            if result2.rowcount == 0:
                raise LookupError(f"User '{user_identifier}' not found")
        self.db.session.commit()

    def disable_user(self, user_identifier: str) -> None:
        """Disable a user account."""
        # Try by email first
        stmt = text("UPDATE users SET is_active = 0 WHERE email = :email")
        result = self.db.session.execute(stmt, {"email": user_identifier})
        if result.rowcount == 0:
            # Try by ID
            stmt2 = text("UPDATE users SET is_active = 0 WHERE id = :uid")
            result2 = self.db.session.execute(stmt2, {"uid": int(user_identifier)})
            if result2.rowcount == 0:
                raise LookupError(f"User '{user_identifier}' not found")
        self.db.session.commit()

    # ── Listing ───────────────────────────────────────────────────────────

    def list_users(self) -> list:
        """List all users with their attributes."""
        stmt = text("SELECT id, email, role, is_active, last_login FROM users")
        result = self.db.session.execute(stmt).fetchall()

        users_list = []
        for row in result:
            users_list.append(
                {
                    "id": row[0],
                    "email": row[1],
                    "role": row[2],
                    "is_active": bool(row[3]),
                    "last_login": row[4],
                }
            )
        return users_list