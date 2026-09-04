"""Port — UOM."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.uom.domain import UOM


class UOMRepositoryPort(ABC):
    @abstractmethod
    def create_uom(self, u: UOM) -> UOM: ...

    @abstractmethod
    def get_uom(self, uid: UUID) -> UOM | None: ...

    @abstractmethod
    def get_by_code(self, company_id: UUID, code: str) -> UOM | None: ...

    @abstractmethod
    def list_uoms(self, company_id: UUID) -> list[UOM]: ...
