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


class FlagType(Enum):
    """Loại cờ hệ thống per quy định Luật Kế toán 2015."""

    LAW = "law"          # Luôn không thay đổi без migration patch
    CONFIG = "config"    # Thay đổi có thể bởi admin có役 2nd approval


class FlagScope(Enum):
    """ Phạm vi cờ hệ thống."""

    COMPANY = "company"  # Một giá trị cho mỗi công ty
    SYSTEM = "system"    # Giá trị đơn nhất cho tất cả công ty (hiếm trong sản xuất)


class FlagCategory(Enum):
    """Danh mục cờ hệ thống."""

    LEGAL = "legal"
    TAX = "tax"
    ACCOUNTING = "accounting"
    E_INVOICE = "e_invoice"
    INTEGRATION = "integration"
    SECURITY = "security"
    UI = "ui"


class AccountingPeriodType(Enum):
    """Loại năm tài chính."""

    CALENDAR = "calendar"         # Jan 1 – Dec 31
    FISCAL_APR = "fiscal_apr"     # Apr 1 – Mar 31 (thường cho doanh nghiệp kế thừa)
    FISCAL_15 = "fiscal_15"       # Jul 15 – Jul 14 (khiếm nhiëu; phải khai báo)


class UserRole(Enum):
    """Vai trò người dùng hệ thống kế toán SME."""

    ACCOUNTANT = "accountant"          # Kế toán viên: tạo/post hóa đơn, chứng từ
    CHIEF_ACCOUNTANT = "chief_accountant"  # Kế toán trưởng: quản lý tài chính công ty
    ADMIN = "admin"                    # Admin: thiết lập hệ thống, quản lý user
    AUDITOR = "auditor"                # Kiểm toán viên: chỉ đọc, review audit log
    DIRECTOR = "director"              # Giám đốc: toàn quyền hệ thống


class UserRoleError(ValueError):
    """Lỗi khi vai trò người dùng không hợp lệ."""
    pass


@dataclass
class EInvoiceSeries:
    """Serie số hóa đơn điện tử."""
    prefix: str                   # e.g., "AA/2026"
    next_sequence: int            # số nguyên tiếp theo phát hành; không thể reset
    active: bool                  # tối đa 15 series active
    ca_signer: str | None         # Identifier of CA for this series


class VATMethod(Enum):
    """Thuế suất VAT theo quy định Việt Nam."""

    DEDUCTION = "deduction"       # Khấu trừ — chuẩn mực
    OUTPUT_ONLY = "output_only"   # Đầu ra — thuế cả bộ (doanh thu nhỏ/KKDV)


class EInvoiceMode(Enum):
    """Chế độ ký hóa đơn điện tử."""

    SOFTWARE_CERT = "software_cert"   # Self-signed cert; giai đoạn chuyển dịch
    CA_SIGNED = "ca_signed"          # GDT-approved CA; bắt buộc sau 2026


class RateType(Enum):
    """Loại tỷ giá (specs-currencies.md §2.2)."""

    BUY = "buy"            # Tỷ giá mua (NHTM)
    SELL = "sell"          # Tỷ giá bán (NHTM)
    TRANSFER = "transfer"  # Tỷ giá chuyển khoản (mua bán trung bình — cuối kỳ)
    CENTRAL = "central"    # Tỷ giá trung tâm / NHNN
    BOOKING = "booking"    # Tỷ giá ghi sổ


class RevaluationStatus(Enum):
    """Trạng thái đợt đánh giá lại cuối kỳ (specs-currencies.md §2.5)."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    REVERSED = "reversed"


class PostingSide(Enum):
    """Bên ghi sổ cho bút toán chênh lệch tỷ giá."""

    DEBIT = "debit"
    CREDIT = "credit"


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
