"""Port — fixed assets."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.fixed_assets.domain import FixedAsset


class FixedAssetRepositoryPort(ABC):
    @abstractmethod
    def create(self, asset: FixedAsset) -> FixedAsset: ...
    @abstractmethod
    def get_by_id(self, aid: UUID) -> FixedAsset | None: ...
    @abstractmethod
    def get_by_company(self, cid: UUID) -> list[FixedAsset]: ...
    @abstractmethod
    def update(self, asset: FixedAsset) -> FixedAsset: ...
    @abstractmethod
    def exists_duplicate(self, cid: UUID, code: str) -> bool: ...
    @abstractmethod
    def find_active_with_remaining(self, cid: UUID) -> list[FixedAsset]: ...
