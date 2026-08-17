"""Core domain entities for Vietnamese accounting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EntityType(Enum):
    """Loại đối tượng kế toán."""

    CUSTOMER = "customer"
    SUPPLIER = "supplier"


class InvoiceType(Enum):
    """Loại hóa đơn theo quy định kế toán Việt Nam."""

    SALES_INVOICE = "sales_invoice"  # Hóa đơn bán hàng
    PURCHASE_INVOICE = "purchase_invoice"  # Hóa đơn mua vào
    CREDIT_NOTE = (
        "credit_note"  # Hóa đơn điều chỉnh (giảm công nợ người bán / tăng công nợ người mua)
    )
    DEBIT_NOTE = (
        "debit_note"  # Hóa đơn điều chỉnh (tăng công nợ người bán / giảm công nợ người mua)
    )


class InvoiceStatus(Enum):
    """Trạng thái hóa đơn."""

    DRAFT = "draft"
    ISSUED = "issued"  # Đã phát hành, chưa gửi
    SIGNED = "signed"  # Đã có chữ ký số
    SENT_TO_CUSTOMER = "sent_to_customer"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    REPLACED = "replaced"  # Đã thay thế bởi hóa đơn khác


class DocumentType(Enum):
    """Loại chứng từ kế toán."""

    RECEIPT = "receipt"  # Phiếu thu
    PAYMENT = "payment"  # Phiếu chi
    JOURNAL_ENTRY = "journal_entry"  # Bút toán kế toán
    TRANSFER_SLIP = "transfer_slip"  # Ủy nhiệm chi


class VoucherStatus(Enum):
    """Trạng thái chứng từ."""

    DRAFT = "draft"
    POSTED = "posted"
    LOCKED = "locked"  # Đã khóa kỳ kế toán


class TaxRate(Enum):
    """Thuế suất theo quy định Việt Nam."""

    VAT_0 = 0
    VAT_5 = 5
    VAT_10 = 10
    NOT_TAXED = -1


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
    """Trạng thái hoạt động của đơn vị kế toán."""

    ACTIVE = "active"
    SUSPENDED = "suspended"  # Tạm ngừng hoạt động
    DISSOLVED = "dissolved"  # Giải thể


class AccountingRegime(Enum):
    """Chế độ kế toán theo Thông tư Bộ Tài chính."""

    TT200 = "tt200"  # Thông tư 200/2014/TT-BTC (legacy enterprise)
    TT99 = "tt99"  # Thông tư 99/2025/TT-BTC (current enterprise)
    TT58_MICRO = "tt58_micro"  # Thông tư 58/2026/TT-BTC (super-micro)
    TT133 = "tt133"  # Thông tư 133/2016/TT-BTC (SME alternative)


@dataclass
class TaxId:
    """Mã số thuế (MST) value object."""

    value: str

    def __post_init__(self):
        import re

        cleaned = self.value.replace("-", "").strip()
        if not re.match(r"^\d{10}(-\d{3})?$", self.value) and not re.match(r"^\d{10}$", cleaned):
            raise ValueError("Mã số thuế không hợp lệ. Định dạng: 10 chữ số hoặc XXXXXXXXXX-XXX")
        object.__setattr__(self, "value", cleaned if "-" not in self.value else self.value)

    def __str__(self) -> str:
        return self.value


@dataclass
class AccountCode:
    """Mã tài khoản value object theo thông tư 200/2014/TT-BTC."""

    value: str

    def __post_init__(self):
        import re

        v = self.value.strip()
        if not re.match(r"^[1-9]\d{2}$|^[1-9]\d{3}$", v):
            raise ValueError(f"Mã tài khoản '{v}' không hợp lệ. VD: 111, 511, 6111...")
        object.__setattr__(self, "value", v)

    def __str__(self) -> str:
        return self.value


@dataclass
class BankAccount:
    """Tài khoản ngân hàng của doanh nghiệp."""

    bank_name: str
    account_number: str
    account_holder: str
    branch: str
    is_primary: bool = False

    def __post_init__(self):
        self.bank_name = self.bank_name.strip()
        self.account_number = self.account_number.strip()
        self.account_holder = self.account_holder.strip()
        self.branch = self.branch.strip()
