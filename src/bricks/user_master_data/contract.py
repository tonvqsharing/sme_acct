"""Port — user master data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.user_master_data.domain import User


class UserRepositoryPort(ABC):
    @abstractmethod
    def create(self, user: User) -> User: ...
    @abstractmethod
    def get_by_id(self, uid: UUID) -> User | None: ...
    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...
    @abstractmethod
    def update(self, user: User) -> User: ...
    @abstractmethod
    def email_exists(self, email: str) -> bool: ...
