"""Company domain entities.

Pure Python — no Flask, no SQLAlchemy imports.
Root aggregate for all accounting data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

# ─── Value Objects ───────────────────────────────────────────────────────


class TaxId:
    """Mã số thuế — validated format per Luật Quản lý thuế 2019.

    Format: 10 digits, optionally followed by '-' and 3 digits.
    Examples: 0123456789, 0123456789-001
    """

    _PATTERN = re.compile(r"^\d{10}(-\d{3})?$")

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        if not self._PATTERN.match(value):
            raise ValueError(
                f"Invalid MST format: {value!r}. Expected: 10 digits or 10 digits-3 digits"
            )
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"TaxId({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaxId):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)


# ─── Enums ───────────────────────────────────────────────────────────────


class CompanyType(Enum):
    """Loại hình doanh nghiệp per Luật Doanh nghiệp 2020 Art. 2."""

    SINGLE_LLC = "single_llc"  # Công ty TNHH 1 thành viên
    MULTI_LLC = "multi_llc"  # Công ty TNHH 2+ thành viên
    JSC = "jsc"  # Công ty cổ phần
    LISTED_JSC = "listed_jsc"  # Công ty cổ phần niêm yết
    SOLE_PROP = "sole_prop"  # Doanh nghiệp tư nhân
    PARTNERSHIP = "partnership"  # Công ty hợp danh
    HOUSEHOLD = "household"  # Hộ kinh doanh
    COOP = "coop"  # Hợp tác xã


class CompanyStatus(Enum):
    """Trạng thái doanh nghiệp."""

    ACTIVE = "active"
    SUSPENDED = "suspended"  # Tạm ngừng hoạt động
    DISSOLVED = "dissolved"  # Giải thể


class AccountingRegime(Enum):
    """Chế độ kế toán — verified against mof.gov.vn / vbpl.vn, Aug 2026.

    - TT99/2025: hiệu lực 01/01/2026, thay thế TT200/2014 (+75/2015,
      53/2016, 195/2012) per Điều 31(1); SMEs may adopt voluntarily
      per Điều 31(3).
    - TT58/2026: hiệu lực 01/07/2026, thay thế TT132/2018 (siêu nhỏ)
      per Điều 12; does NOT touch TT133.
    - TT133/2016: still in force for DN nhỏ và vừa; revision only on
      roadmap (QĐ 3389/QĐ-BTC, 2026–27) — not yet issued.
    """

    TT99 = "tt99"  # Thông tư 99/2025/TT-BTC (current enterprise)
    TT58_MICRO = "tt58_micro"  # Thông tư 58/2026/TT-BTC (siêu nhỏ)
    TT133 = "tt133"  # Thông tư 133/2016/TT-BTC (DN nhỏ và vừa — in force)


# ─── Exceptions ──────────────────────────────────────────────────────────


class CompanyError(Exception):
    """Base exception for Company domain errors."""


class DuplicateMSTError(CompanyError):
    """Raised when MST already exists in system."""


class CompanyNotFoundError(CompanyError):
    """Raised when company not found by ID or MST."""


class CompanyLockedError(CompanyError):
    """Raised when operation blocked by company state."""


class InvalidCompanyStateError(CompanyError):
    """Raised when invalid state transition attempted."""


# ─── Value Objects ───────────────────────────────────────────────────────


@dataclass
class BankAccount:
    """Thông tin tài khoản ngân hàng."""

    bank_name: str
    account_number: str
    account_holder: str
    branch: str = ""
    is_primary: bool = False


# ─── Entities ────────────────────────────────────────────────────────────


@dataclass
class Company:
    """Doanh nghiệp / Đơn vị kế toán — root aggregate for all accounting data."""

    # ── Identity ──
    id: UUID = field(default_factory=uuid4)

    # ── Mandatory legal (from Luật Doanh nghiệp 2020 Art. 31) ──
    legal_name: str = ""
    mst: TaxId = field(default_factory=lambda: TaxId("0000000000"))
    headquarters_address: str = ""
    legal_representative: str = ""

    # ── Registration (from Luật Doanh nghiệp 2020 Art. 37) ──
    business_reg_number: str = ""
    business_reg_date: date | None = None
    business_fields: list[str] = field(default_factory=list)

    # ── Classification (from Luật Doanh nghiệp 2020 Ch. II) ──
    company_type: CompanyType = CompanyType.MULTI_LLC
    accounting_regime: AccountingRegime = AccountingRegime.TT99

    # ── Accounting (from Luật Kế toán 2015 Art. 13) ──
    fiscal_year_start_month: int = 1
    fiscal_year_start_day: int = 1
    responsible_accountant_name: str = ""
    responsible_accountant_license: str = ""

    # ── Tax (from Luật Quản lý thuế 2019) ──
    tax_agency: str = ""
    controlling_tax_office: str = ""

    # ── BHXH (from Luật BHXH 2024) ──
    bhxh_code: str = ""
    bhxh_agency: str = ""

    # ── Operational ──
    authorized_capital: Decimal = Decimal(0)
    phone: str = ""
    email: str = ""
    website: str = ""
    short_name: str = ""
    bank_accounts: list[BankAccount] = field(default_factory=list)

    # ── Status ──
    status: CompanyStatus = CompanyStatus.ACTIVE
    is_active: bool = True

    # ── Audit ──
    created_at: date | None = None
    updated_at: date | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    config_version: int = 0
    legal_reviewed_at: date | None = None
    legal_reviewed_by: UUID | None = None
    mst_changed_at: date | None = None
