"""Port — party."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.party.domain import Department, Party


class PartyRepositoryPort(ABC):
    @abstractmethod
    def create_party(self, p: Party) -> Party: ...

    @abstractmethod
    def get_party(self, pid: UUID) -> Party | None: ...

    @abstractmethod
    def get_by_code(self, company_id: UUID, code: str) -> Party | None: ...

    @abstractmethod
    def get_by_mst(self, company_id: UUID, mst: str) -> Party | None: ...

    @abstractmethod
    def list_parties(self, company_id: UUID, role: str | None = None) -> list[Party]: ...

    @abstractmethod
    def create_department(self, d: Department) -> Department: ...

    @abstractmethod
    def get_department(self, did: UUID) -> Department | None: ...

    @abstractmethod
    def list_departments(self, company_id: UUID) -> list[Department]: ...
