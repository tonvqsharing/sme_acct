"""Port — opening balance."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.opening_balance.domain import BankOpening, GLBalance, OpeningBatch


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
