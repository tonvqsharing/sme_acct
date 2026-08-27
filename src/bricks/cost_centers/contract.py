"""Port — cost centers & dimensions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.cost_centers.domain import (
    CostCenter,
    Dimension,
    DimensionValue,
)


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


class DimensionRepositoryPort(ABC):
    @abstractmethod
    def create(self, dim: Dimension) -> Dimension: ...
    @abstractmethod
    def get_by_id(self, did: UUID) -> Dimension | None: ...
    @abstractmethod
    def get_by_company(
        self, cid: UUID, *, dimension_type: str | None = None, is_system: bool | None = None
    ) -> list[Dimension]: ...
    @abstractmethod
    def update(self, dim: Dimension) -> Dimension: ...
    @abstractmethod
    def exists_duplicate(self, cid: UUID, code: str) -> bool: ...


class DimensionValueRepositoryPort(ABC):
    @abstractmethod
    def create(self, dv: DimensionValue) -> DimensionValue: ...
    @abstractmethod
    def get_by_id(self, dvid: UUID) -> DimensionValue | None: ...
    @abstractmethod
    def get_by_company(
        self, cid: UUID, *, dimension_id: UUID | None = None, status: str | None = None
    ) -> list[DimensionValue]: ...
    @abstractmethod
    def update(self, dv: DimensionValue) -> DimensionValue: ...
    @abstractmethod
    def exists_duplicate(self, dim_id: UUID, cid: UUID, code: str) -> bool: ...
