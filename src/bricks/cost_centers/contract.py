"""Port — cost centers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.cost_centers.domain import CostCenter


class CostCenterRepositoryPort(ABC):
    @abstractmethod
    def create(self, cc: CostCenter) -> CostCenter: ...
    @abstractmethod
    def get_by_id(self, cid: UUID) -> CostCenter | None: ...
    @abstractmethod
    def get_by_company(self, cid: UUID) -> list[CostCenter]: ...
    @abstractmethod
    def update(self, cc: CostCenter) -> CostCenter: ...
    @abstractmethod
    def exists_duplicate(self, cid: UUID, code: str) -> bool: ...
