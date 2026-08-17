"""Application layer: use cases coordinate domain."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

from src.domain.entities.company import Company
from src.domain.entities.contact import Partner
from src.domain.entities.invoice import Invoice, InvoiceItem, InvoiceStatus, InvoiceType
from src.domain.entities.voucher import DocumentType, Voucher, VoucherLine, VoucherStatus


class CompanyRepositoryPort(ABC):
    @abstractmethod
    def create(self, company: Company) -> Company:
        pass

    @abstractmethod
    def update(self, company: Company) -> Company:
        """Persist changes to an existing company (matched by MST)."""
        pass

    @abstractmethod
    def get_by_id(self, company_id: UUID) -> Company | None:
        pass

    @abstractmethod
    def get_by_mst(self, mst: str) -> Company | None:
        pass

    @abstractmethod
    def get_active(self) -> Company | None:
        pass

    @abstractmethod
    def list_active(self, page: int = 1, page_size: int = 20) -> list[Company]:
        pass


class PartnerRepositoryPort(ABC):
    @abstractmethod
    def create(self, partner: Partner) -> Partner:
        pass

    @abstractmethod
    def get_by_id(self, partner_id: UUID) -> Partner | None:
        pass

    @abstractmethod
    def get_by_code(self, code: str) -> Partner | None:
        pass

    @abstractmethod
    def list_active(self, page: int = 1, page_size: int = 20) -> list[Partner]:
        pass


class InvoiceRepositoryPort(ABC):
    @abstractmethod
    def create(self, invoice: Invoice) -> Invoice:
        pass

    @abstractmethod
    def get_by_id(self, invoice_id: UUID) -> Invoice | None:
        pass

    @abstractmethod
    def get_by_serial_number(self, serial: str, invoice_number: str) -> Invoice | None:
        pass

    @abstractmethod
    def list_by_partner(
        self,
        partner_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Invoice]:
        pass


class VoucherRepositoryPort(ABC):
    @abstractmethod
    def create(self, voucher: Voucher) -> Voucher:
        pass

    @abstractmethod
    def get_by_id(self, voucher_id: UUID) -> Voucher | None:
        pass

    @abstractmethod
    def get_by_number(self, voucher_number: str) -> Voucher | None:
        pass

    @abstractmethod
    def lock(self, voucher_id: UUID) -> Voucher:
        pass


class AccountChartRepositoryPort(ABC):
    @abstractmethod
    def get_balance(self, account_code: str, from_date: date, to_date: date) -> dict:
        pass
