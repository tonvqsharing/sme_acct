"""Public port — purchases brick."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.bricks.purchases.domain import SupplierInvoice


class SupplierInvoiceRepositoryPort(ABC):
    @abstractmethod
    def create(self, inv: SupplierInvoice) -> SupplierInvoice: ...
    @abstractmethod
    def get_by_id(self, iid: UUID) -> SupplierInvoice | None: ...
    @abstractmethod
    def get_by_company(self, cid: UUID) -> list[SupplierInvoice]: ...
    @abstractmethod
    def update(self, inv: SupplierInvoice) -> SupplierInvoice: ...
    @abstractmethod
    def exists_duplicate(self, cid: UUID, mst: str, number: str, symbol: str) -> bool: ...
