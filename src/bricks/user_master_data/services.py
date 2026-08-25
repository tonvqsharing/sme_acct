"""UserService — create/authenticate/manage users (specs §3, §6)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.bricks.user_master_data.domain import (
    MIN_PASSWORD_LEN,
    User,
    UserRole,
)


class ActorRequiredError(Exception):
    code = "MISSING_ACTOR"


class DuplicateEmailError(Exception):
    code = "DUPLICATE_EMAIL"


class InvalidCredentialsError(Exception):
    code = "INVALID_CREDENTIALS"


class InactiveAccountError(Exception):
    code = "INACTIVE_ACCOUNT"


class NotFoundError(Exception):
    code = "NOT_FOUND"


def _require(actor: UUID | None) -> UUID:
    if actor is None:
        raise ActorRequiredError("actor là bắt buộc")
    return actor


class UserService:
    def __init__(self, repo: Any) -> None:
        self._repo = repo

    # ── create ──────────────────────────────────────────────────────────
    def create_user(
        self,
        *,
        email: str,
        password: str,
        role: UserRole,
        full_name: str,
        actor: UUID | None,
        is_active: bool = True,
    ) -> User:
        _require(actor)
        u = User(email=email.strip().lower(), role=role, full_name=full_name.strip())
        if len(password) < MIN_PASSWORD_LEN:
            raise ValueError(f"Password must be >= {MIN_PASSWORD_LEN} chars")
        u.set_password(password)
        if self._repo.email_exists(u.email):
            raise DuplicateEmailError("Email đã tồn tại")
        u.is_active = is_active
        created: User = self._repo.create(u)
        return created

    # ── authenticate ────────────────────────────────────────────────────
    def authenticate(self, email: str, password: str) -> User:
        user = self._repo.get_by_email(email.strip().lower())
        # Anti-enumeration: identical error for unknown vs wrong pw.
        if user is None or not user.verify_password(password):
            raise InvalidCredentialsError("Email hoặc mật khẩu không đúng")
        if not user.is_active:
            raise InactiveAccountError("Tài khoản đã bị vô hiệu hóa")
        user.touch_login()
        updated: User = self._repo.update(user)
        return updated

    # ── queries / lifecycle ─────────────────────────────────────────────
    def get_by_id(self, uid: UUID) -> User | None:
        found: User | None = self._repo.get_by_id(uid)
        return found

    def get_by_email(self, email: str) -> User | None:
        found: User | None = self._repo.get_by_email(email)
        return found

    def reset_password(self, uid: UUID, new_password: str, *, actor: UUID | None = None) -> User:
        _require(actor)
        user = self._get_or_404(uid)
        user.set_password(new_password)
        saved: User = self._repo.update(user)
        return saved

    def deactivate(self, uid: UUID, *, actor: UUID | None = None) -> User:
        _require(actor)
        user = self._get_or_404(uid)
        user.is_active = False
        deactivated: User = self._repo.update(user)
        return deactivated

    def _get_or_404(self, uid: UUID) -> User:
        user: User | None = self._repo.get_by_id(uid)
        if user is None:
            raise NotFoundError("Không tìm thấy người dùng")
        return user
