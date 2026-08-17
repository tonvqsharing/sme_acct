"""Company aggregate root: doanh nghiệp / đơn vị kế toán."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from src.domain.entities.base import (
    AccountingRegime,
    BankAccount,
    CompanyStatus,
    CompanyType,
    TaxId,
)
from src.domain.exceptions import (
    CompanyLockedError,
    CompanyValidationError,
    InvalidCompanyTypeError,
)


@dataclass
class Company:
    """Doanh nghiệp / Đơn vị kế toán.

    Root aggregate for all accounting data.
    Per Luật Doanh nghiệp 2020 Art. 31 + Luật Kế toán 2015 Art. 6.
    """

    # ── Mandatory legal (Luật Doanh nghiệp 2020 Art. 31) ──
    legal_name: str
    mst: TaxId
    headquarters_address: str
    legal_representative: str

    # ── Registration (Luật Doanh nghiệp 2020 Art. 37) ──
    business_reg_number: str
    business_reg_date: date
    business_fields: list[str]

    # ── Classification (Luật Doanh nghiệp 2020 Ch. II) ──
    company_type: CompanyType
    accounting_regime: AccountingRegime

    # ── Accounting (Luật Kế toán 2015 Art. 13) ──
    fiscal_year_start_month: int = 1
    fiscal_year_start_day: int = 1
    responsible_accountant_name: str = ""
    responsible_accountant_license: str = ""

    # ── Tax / BHXH ──
    tax_agency: str = ""
    controlling_tax_office: str = ""
    bhxh_code: str = ""
    bhxh_agency: str = ""

    # ── Operational ──
    authorized_capital: float = 0.0
    phone: str = ""
    email: str = ""
    website: str = ""
    short_name: str = ""
    bank_accounts: list[BankAccount] = field(default_factory=list)

    # ── Status ──
    status: CompanyStatus = CompanyStatus.ACTIVE
    is_active: bool = True

    # ── Audit ──
    id: UUID = field(default_factory=uuid4)
    created_at: date = field(default_factory=date.today)
    updated_at: date = field(default_factory=date.today)
    created_by: UUID = field(default_factory=uuid4)
    updated_by: UUID = field(default_factory=uuid4)
    config_version: int = 1
    legal_reviewed_at: date | None = None
    legal_reviewed_by: UUID | None = None
    mst_changed_at: date | None = None

    def __post_init__(self) -> None:
        import calendar as _cal

        # ── Normalize ──────────────────────────────────────────
        # Ensure mst is a TaxId (test passes raw strings via kwargs)
        if isinstance(self.mst, str):
            self.mst = TaxId(self.mst)

        self.legal_name = self.legal_name.strip()
        self.headquarters_address = self.headquarters_address.strip()
        self.legal_representative = self.legal_representative.strip()
        self.phone = self.phone.strip()
        self.email = self.email.strip()
        self.website = self.website.strip()
        self.short_name = self.short_name.strip()
        self.tax_agency = self.tax_agency.strip()
        self.controlling_tax_office = self.controlling_tax_office.strip()
        self.bhxh_code = self.bhxh_code.strip()
        self.bhxh_agency = self.bhxh_agency.strip()

        if not self.headquarters_address or len(self.headquarters_address) < 5:
            raise CompanyValidationError("Địa chỉ trụ sở chính là bắt buộc (tối thiểu 5 ký tự)")
        if not self.legal_representative:
            raise CompanyValidationError("Người đại diện pháp luật là bắt buộc")

        if not isinstance(self.company_type, CompanyType):
            raise InvalidCompanyTypeError(
                f"Loại hình doanh nghiệp không hợp lệ: {self.company_type}"
            )

        if not isinstance(self.accounting_regime, AccountingRegime):
            raise CompanyValidationError(f"Chế độ kế toán không hợp lệ: {self.accounting_regime}")

        if self.company_type == CompanyType.HOUSEHOLD:
            self.accounting_regime = AccountingRegime.TT58_MICRO

        if not (1 <= self.fiscal_year_start_month <= 12):
            raise ValueError(
                f"Tháng bắt đầu năm tài chính không hợp lệ: {self.fiscal_year_start_month} (phải từ 1-12)"
            )
        if not (1 <= self.fiscal_year_start_day <= 31):
            raise ValueError(
                f"Ngày bắt đầu năm tài chính không hợp lệ: {self.fiscal_year_start_day} (phải từ 1-31)"
            )
        max_day = _cal.monthrange(2024, self.fiscal_year_start_month)[1]
        if self.fiscal_year_start_day > max_day:
            raise ValueError(
                f"Ngày bắt đầu năm tài chính không hợp lệ: {self.fiscal_year_start_month}/{self.fiscal_year_start_day}"
            )

        if self.company_type != CompanyType.HOUSEHOLD:
            if not self.bhxh_code:
                raise CompanyValidationError(
                    "Mã BHXH là bắt buộc cho đơn vị không phải Hộ kinh doanh"
                )
            if not self.responsible_accountant_license:
                raise CompanyValidationError("MSKHMN là bắt buộc cho đơn vị doanh nghiệp")

        for account in self.bank_accounts:
            if not isinstance(account, BankAccount):
                raise CompanyValidationError(f"Tài khoản ngân hàng không hợp lệ: {account}")

    # ── Lifecycle ────────────────────────────────────────────

    def suspend(self) -> None:
        """Tạm ngừng hoạt động."""
        if self.status == CompanyStatus.DISSOLVED:
            raise CompanyLockedError("Không thể tạm ngừng đơn vị đã giải thể")
        self.status = CompanyStatus.SUSPENDED
        self.is_active = False
        self.updated_at = date.today()

    def reactivate(self) -> None:
        """Kích hoạt lại từ trạng thái tạm ngừng."""
        if self.status == CompanyStatus.DISSOLVED:
            raise CompanyLockedError("Không thể kích hoạt lại đơn vị đã giải thể")
        self.status = CompanyStatus.ACTIVE
        self.is_active = True
        self.updated_at = date.today()

    def dissolve(self) -> None:
        """Giải thể — không thể hoàn tác."""
        self.status = CompanyStatus.DISSOLVED
        self.is_active = False
        self.updated_at = date.today()

    def deactivate(self) -> None:
        """Deactivate (alias for suspend — used in service layer)."""
        self.suspend()

    def validate_active_for_transaction(self) -> None:
        """Raise if company cannot create new transactions."""
        if self.status == CompanyStatus.SUSPENDED:
            raise CompanyLockedError(
                f"Đơn vị {self.legal_name} đã tạm ngừng hoạt động. Không thể tạo chứng từ."
            )
        if self.status == CompanyStatus.DISSOLVED:
            raise CompanyLockedError(
                f"Đơn vị {self.legal_name} đã giải thể. Không thể tạo chứng từ."
            )
        if not self.is_active:
            raise CompanyLockedError(
                f"Đơn vị {self.legal_name} không hoạt động. Không thể tạo chứng từ."
            )

    # ── Fiscal Year Helpers ──────────────────────────────────

    def get_fiscal_year_and_period(self, entry_date: date) -> tuple[int, int]:
        """Derive fiscal year and accounting period from entry date.

        Returns:
            (fiscal_year, accounting_period) where period is 1-based.
        """
        fym = self.fiscal_year_start_month
        fyd = self.fiscal_year_start_day

        fiscal_year = (
            entry_date.year
            if entry_date.month > fym or (entry_date.month == fym and entry_date.day >= fyd)
            else entry_date.year - 1
        )

        if entry_date.month > fym or (entry_date.month == fym and entry_date.day >= fyd):
            month_offset = entry_date.month - fym
        else:
            month_offset = entry_date.month + 12 - fym

        accounting_period = month_offset + 1
        return fiscal_year, accounting_period

    # ── Display Helpers ──────────────────────────────────────

    def get_display_name(self) -> str:
        """Tên hiển thị: legal_name > short_name."""
        return self.legal_name or self.short_name or ""

    # ── Repr ─────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Company({self.legal_name!r}, {self.mst}, {self.status.value})"
