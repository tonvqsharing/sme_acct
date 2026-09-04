"""Port — opening balance."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.opening_balance.domain import (
    AssetOpening,
    BankOpening,
    CounterpartyBalance,
    GLBalance,
    OpeningBatch,
    StockOpening,
)


class OpeningBalanceRepositoryPort(ABC):
    @abstractmethod
    def create_batch(self, b: OpeningBatch) -> OpeningBatch: ...

    @abstractmethod
    def get_batch(self, bid: UUID) -> OpeningBatch | None: ...

    @abstractmethod
    def update_batch(self, b: OpeningBatch) -> OpeningBatch: ...

    @abstractmethod
    def list_batches(self, company_id: UUID) -> list[OpeningBatch]: ...

    @abstractmethod
    def add_gl(self, row: GLBalance) -> GLBalance: ...

    @abstractmethod
    def list_gl(self, batch_id: UUID) -> list[GLBalance]: ...

    @abstractmethod
    def add_bank(self, row: BankOpening) -> BankOpening: ...

    @abstractmethod
    def list_bank(self, batch_id: UUID) -> list[BankOpening]: ...

    @abstractmethod
    def add_counterparty(self, row: CounterpartyBalance) -> CounterpartyBalance: ...

    @abstractmethod
    def list_counterparty(self, batch_id: UUID) -> list[CounterpartyBalance]: ...

    @abstractmethod
    def add_stock(self, row: StockOpening) -> StockOpening: ...

    @abstractmethod
    def list_stock(self, batch_id: UUID) -> list[StockOpening]: ...

    @abstractmethod
    def add_asset(self, row: AssetOpening) -> AssetOpening: ...

    @abstractmethod
    def list_assets(self, batch_id: UUID) -> list[AssetOpening]: ...
