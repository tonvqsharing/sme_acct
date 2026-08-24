"""Public port for the coa brick."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.coa.domain import Account


class AccountRepositoryPort(ABC):
    @abstractmethod
    def create(self, account: Account) -> Account: ...

    @abstractmethod
    def get_by_code(self, company_id: UUID, code: str) -> Account | None: ...

    @abstractmethod
    def get_by_company(self, company_id: UUID) -> list[Account]: ...

    @abstractmethod
    def update(self, account: Account) -> Account: ...

    @abstractmethod
    def validate_code_unique(self, company_id: UUID, code: str) -> bool: ...
