"""Port — inventory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from uuid import UUID

from src.bricks.inventory.domain import Location, Product, Shipment, StockMove


class InventoryRepositoryPort(ABC):
    @abstractmethod
    def create_product(self, p: Product) -> Product: ...

    @abstractmethod
    def get_product(self, pid: UUID) -> Product | None: ...

    @abstractmethod
    def get_product_by_code(self, company_id: UUID, code: str) -> Product | None: ...

    @abstractmethod
    def list_products(self, company_id: UUID) -> list[Product]: ...

    @abstractmethod
    def create_location(self, loc: Location) -> Location: ...

    @abstractmethod
    def get_location(self, lid: UUID) -> Location | None: ...

    @abstractmethod
    def list_locations(self, company_id: UUID) -> list[Location]: ...

    @abstractmethod
    def create_shipment(self, s: Shipment) -> Shipment: ...

    @abstractmethod
    def get_shipment(self, sid: UUID) -> Shipment | None: ...

    @abstractmethod
    def update_shipment(self, s: Shipment) -> Shipment: ...

    @abstractmethod
    def create_move(self, m: StockMove) -> StockMove: ...

    @abstractmethod
    def get_move(self, mid: UUID) -> StockMove | None: ...

    @abstractmethod
    def list_moves(
        self,
        company_id: UUID,
        product_id: UUID | None = None,
        location_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        state: str | None = None,
    ) -> list[StockMove]: ...

    @abstractmethod
    def update_move(self, m: StockMove) -> StockMove: ...

    @abstractmethod
    def get_stock_qty(
        self, company_id: UUID, product_id: UUID, location_id: UUID | None = None
    ) -> Decimal: ...

    @abstractmethod
    def get_stock_value(self, company_id: UUID, product_id: UUID) -> Decimal: ...

    # period
    @abstractmethod
    def is_period_closed(self, company_id: UUID, year: int, month: int) -> bool: ...

    @abstractmethod
    def close_period(self, company_id: UUID, year: int, month: int) -> None: ...
