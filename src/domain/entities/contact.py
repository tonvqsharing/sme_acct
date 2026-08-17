"""Partner aggregate root: customers, suppliers."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from src.domain.entities.base import EntityType, TaxId


class Partner:
    """Đối tượng kế toán: khách hàng / nhà cung cấp."""

    __slots__ = (
        "id",
        "code",
        "name",
        "tax_id",
        "entity_type",
        "address",
        "phone",
        "email",
        "tax_agency",
        "is_active",
        "created_at",
        "updated_at",
    )

    def __init__(
        self,
        code: str,
        name: str,
        entity_type: EntityType,
        tax_id: TaxId | str | None = None,
        address: str = "",
        phone: str = "",
        email: str = "",
        tax_agency: str = "",
    ) -> None:
        from uuid import uuid4

        self.id: UUID = uuid4()
        self.code = code.strip()
        self.name = name.strip()
        self.tax_id: TaxId | None = TaxId(tax_id) if isinstance(tax_id, str) else tax_id
        self.entity_type = entity_type
        self.address = address.strip()
        self.phone = phone.strip()
        self.email = email.strip().lower()
        self.tax_agency = tax_agency.strip()
        self.is_active: bool = True
        self.created_at: date = date.today()
        self.updated_at: date = date.today()

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = date.today()

    def __repr__(self) -> str:
        return f"Partner({self.code!r}, {self.name!r}, {self.entity_type.value})"
