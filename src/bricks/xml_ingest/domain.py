"""XML invoice ingest domain — TT91/2026 parser. Pure Python, no Flask/SQLAlchemy."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum

# ─── Invoice symbol system (Phụ lục I, TT91/2026) ─────────────────────

TEMPLATE_CODES = {
    "1": "VAT invoice",
    "2": "Sales invoice",
    "3": "Public asset sale",
    "4": "National reserve sale",
    "5": "Other e-invoice (token/ticket/card/receipt)",
    "6": "Internal transfer / agency consignment",
    "7": "E-commerce invoice",
    "8": "VAT integrated with tax receipt",
    "9": "Sales integrated with tax receipt",
}

INVOICE_TYPE_CODES = {
    "T": "registered with tax authority",
    "D": "public asset / special / national reserve",
    "L": "tax-authority-issued per transaction",
    "M": "POS (point of sale)",
    "N": "internal warehouse transfer",
    "B": "agency consignment",
    "G": "VAT token/ticket",
    "H": "sales token/ticket",
    "X": "e-commerce",
    "F": "VAT + refund declaration",
}


class InvoiceCoding(Enum):
    CODED = "C"  # has tax authority code
    UNCODED = "K"  # no tax authority code


@dataclass(frozen=True)
class InvoiceSymbol:
    """Parsed TT91/2026 invoice symbol (6-char group)."""

    raw: str
    template_code: str  # 1-9 (displayed before the 6-char group)
    coding: InvoiceCoding
    year: int  # 2-digit year
    type_code: str  # T/D/L/M/N/B/G/H/X/F
    internal_code: str  # 2-letter seller-defined (default YY)

    @property
    def full_year(self) -> int:
        return 2000 + self.year

    @property
    def type_description(self) -> str:
        return INVOICE_TYPE_CODES.get(self.type_code, "unknown")

    @property
    def template_description(self) -> str:
        return TEMPLATE_CODES.get(self.template_code, "unknown")


def parse_symbol(template_code: str, symbol: str) -> InvoiceSymbol:
    """Parse a TT91/2026 invoice symbol.

    Args:
        template_code: 1-digit template code (1-9)
        symbol: 6-char invoice symbol (e.g. '1C26TAA')

    Returns:
        InvoiceSymbol with parsed components

    Raises:
        ValueError: if format is invalid
    """
    template_code = template_code.strip()
    if template_code not in TEMPLATE_CODES:
        raise ValueError(f"Invalid template code: {template_code!r} (must be 1-9)")

    symbol = symbol.strip().upper()
    if len(symbol) != 6:
        raise ValueError(f"Symbol must be 6 characters, got {len(symbol)}: {symbol!r}")

    coding_char = symbol[0]
    if coding_char not in ("C", "K"):
        raise ValueError(f"First character must be C or K, got {coding_char!r}")

    year_str = symbol[1:3]
    if not year_str.isdigit():
        raise ValueError(f"Characters 2-3 must be digits (year), got {year_str!r}")

    type_char = symbol[3]
    if type_char not in INVOICE_TYPE_CODES:
        raise ValueError(f"Character 4 must be one of {set(INVOICE_TYPE_CODES)}, got {type_char!r}")

    internal = symbol[4:6]
    if not internal.isalpha():
        raise ValueError(f"Characters 5-6 must be letters, got {internal!r}")

    return InvoiceSymbol(
        raw=f"{template_code}{symbol}",
        template_code=template_code,
        coding=InvoiceCoding(coding_char),
        year=int(year_str),
        type_code=type_char,
        internal_code=internal,
    )


# ─── XML field mapping (TT91/2026 Appendix III) ───────────────────────

# Namespace handling — Vietnamese e-invoice XML may or may not use namespaces
_NS = "{http://hoadon.gdt.gov.vn/xml/schemas/common}"


def _tag(local: str) -> str:
    """Return namespaced or plain tag."""
    return f"{_NS}{local}"


# XPath-like selectors for common TT91 XML fields
# These cover the standard structure from NĐ 254/2026 Appendix 9
XML_PATHS = {
    # Seller (người bán)
    "seller_name": [".//DLHDon/HDon/NBan/Ten", ".//seller/name", ".//NBan/Ten"],
    "seller_mst": [".//DLHDon/HDon/NBan/MST", ".//seller/taxCode", ".//NBan/MST"],
    "seller_address": [".//DLHDon/HDon/NBan/DChi", ".//seller/address", ".//NBan/DChi"],
    "seller_phone": [".//DLHDon/HDon/NBan/DienThoai", ".//seller/phone", ".//NBan/DienThoai"],
    "seller_email": [".//DLHDon/HDon/NBan/Email", ".//seller/email", ".//NBan/Email"],
    # Buyer (người mua)
    "buyer_name": [".//DLHDon/HDon/NMua/Ten", ".//buyer/name", ".//NMua/Ten"],
    "buyer_mst": [".//DLHDon/HDon/NMua/MST", ".//buyer/taxCode", ".//NMua/MST"],
    "buyer_address": [".//DLHDon/HDon/NMua/DChi", ".//buyer/address", ".//NMua/DChi"],
    "buyer_phone": [".//DLHDon/HDon/NMua/DienThoai", ".//buyer/phone", ".//NMua/DienThoai"],
    "buyer_email": [".//DLHDon/HDon/NMua/Email", ".//buyer/email", ".//NMua/Email"],
    # Invoice header
    "invoice_number": [
        ".//DLHDon/HDon/SHDon",
        ".//invoice/invoiceNumber",
        ".//HDon/SHDon",
        ".//header/invoiceNo",
    ],
    "invoice_symbol": [
        ".//DLHDon/HDon/KHMSHDon",
        ".//invoice/invoiceSymbol",
        ".//HDon/KHMSHDon",
        ".//header/invoiceSymbol",
    ],
    "invoice_date": [
        ".//DLHDon/HDon/NLap",
        ".//invoice/invoiceDate",
        ".//HDon/NLap",
        ".//header/invoiceDate",
    ],
    "template_code": [
        ".//DLHDon/HDon/KMHHDON",
        ".//invoice/templateCode",
        ".//HDon/KMHHDON",
        ".//header/templateCode",
    ],
    # Invoice lines (hàng hóa/dịch vụ)
    "lines_container": [
        ".//DLHDon/HDon/HHDVu",
        ".//invoice/lineItems",
        ".//HDon/HHDVu",
        ".//items",
    ],
    "line_name": ["./Ten", "./name", "./itemName"],
    "line_unit": ["./DVTinh", "./unit", "./unitName"],
    "line_quantity": ["./SLuong", "./quantity", "./soLuong"],
    "line_unit_price": ["./DGia", "./unitPrice", "./donGia"],
    "line_amount": ["./ThTien", "./amount", "./thanhTien"],
    "line_vat_rate": ["./TSuat", "./vatRate", "./thueSuat"],
    "line_vat_amount": ["./TSuatTien", "./vatAmount", "./tienThue"],
    # Totals
    "total_before_vat": [
        ".//DLHDon/HDon/THTTLTE",
        ".//invoice/totalBeforeVAT",
        ".//HDon/THTTLTE",
    ],
    "total_vat": [
        ".//DLHDon/HDon/TTCKTM",
        ".//invoice/totalVAT",
        ".//HDon/TTCKTM",
    ],
    "total_after_vat": [
        ".//DLHDon/HDon/TongCong",
        ".//invoice/totalAmount",
        ".//HDon/TongCong",
    ],
    # Currency
    "currency": [
        ".//DLHDon/HDon/DVTTe",
        ".//invoice/currency",
        ".//HDon/DVTTe",
    ],
    "exchange_rate": [
        ".//DLHDon/HDon/TSHTNT",
        ".//invoice/exchangeRate",
        ".//HDon/TSHTNT",
    ],
}


def _ns_wildcard(path: str) -> str:
    """Convert a plain XPath to one using ``{*}`` namespace wildcard.

    Inserts ``{*}`` before each tag-name segment, preserving ``//`` and leading ``./``.
    Example: ``.//DLHDon/HDon/SHDon`` → ``.//{*}DLHDon/{*}HDon/{*}SHDon``
    """

    return re.sub(r"(?<=/)(\w)", r"{*}\1", path)


def _find_text(root: ET.Element, paths: list[str], default: str = "") -> str:
    """Find text using multiple XPath candidates.

    Tries each path as-is (non-namespaced), then with wildcard namespace
    ``{*}Tag`` for XML that declares ``xmlns=...`` on the root.
    """
    for path in paths:
        el = root.find(path)
        if el is not None and el.text:
            return el.text.strip()
        # Retry with wildcard namespace for namespaced XML
        ns_path = _ns_wildcard(path)
        if ns_path != path:
            el = root.find(ns_path)
            if el is not None and el.text:
                return el.text.strip()
    return default


def _find_decimal(root: ET.Element, paths: list[str]) -> Decimal | None:
    """Find and parse a decimal value."""
    text = _find_text(root, paths)
    if not text:
        return None
    try:
        # Vietnamese XML often uses comma as decimal separator
        text = text.replace(",", "")
        return Decimal(text)
    except InvalidOperation:
        return None


def _find_date(root: ET.Element, paths: list[str]) -> date | None:
    """Find and parse a date value."""
    text = _find_text(root, paths)
    if not text:
        return None
    # Try common date formats
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()  # noqa: DTZ007 — invoice dates are naive
        except ValueError:
            continue
    return None


# ─── Parsed invoice data ──────────────────────────────────────────────


@dataclass
class ParsedInvoiceLine:
    """A single line item from a parsed XML invoice."""

    name: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal


@dataclass
class ParsedInvoice:
    """Parsed Vietnamese e-invoice from XML."""

    # Seller
    seller_name: str
    seller_mst: str
    seller_address: str
    seller_phone: str = ""
    seller_email: str = ""

    # Buyer
    buyer_name: str = ""
    buyer_mst: str = ""
    buyer_address: str = ""
    buyer_phone: str = ""
    buyer_email: str = ""

    # Invoice header
    invoice_number: str = ""
    invoice_symbol: str = ""
    template_code: str = ""
    invoice_date: date | None = None
    parsed_symbol: InvoiceSymbol | None = None

    # Line items
    lines: list[ParsedInvoiceLine] = field(default_factory=list)

    # Totals
    total_before_vat: Decimal | None = None
    total_vat: Decimal | None = None
    total_after_vat: Decimal | None = None

    # Currency
    currency: str = "VND"
    exchange_rate: Decimal = Decimal(1)

    # Raw XML reference
    raw_xml: bytes = b""


# ─── XML parser ───────────────────────────────────────────────────────


def parse_xml_invoice(xml_bytes: bytes) -> ParsedInvoice:
    """Parse a TT91/2026-format e-invoice XML file.

    Args:
        xml_bytes: Raw XML content (UTF-8)

    Returns:
        ParsedInvoice with extracted fields

    Raises:
        ET.ParseError: if XML is malformed
        ValueError: if required fields are missing
    """
    root = ET.fromstring(xml_bytes)

    # Extract invoice number
    invoice_number = _find_text(root, XML_PATHS["invoice_number"])
    if not invoice_number:
        raise ValueError("Missing invoice number (SHDon)")

    # Extract and parse invoice symbol
    raw_symbol = _find_text(root, XML_PATHS["invoice_symbol"])
    template_code = _find_text(root, XML_PATHS["template_code"])

    parsed_symbol = None
    if template_code and raw_symbol:
        try:
            parsed_symbol = parse_symbol(template_code, raw_symbol)
        except ValueError:
            pass  # Symbol parsing is best-effort; raw values still captured

    # Extract lines
    lines = []
    container_paths = XML_PATHS["lines_container"]
    container = None
    for container_path in container_paths:
        container = root.find(container_path)
        if container is not None:
            break
        # Try with wildcard namespace
        ns_path = _ns_wildcard(container_path)
        if ns_path != container_path:
            container = root.find(ns_path)
            if container is not None:
                break
    if container is not None:
        for item in container:
            name = _find_text(item, XML_PATHS["line_name"])
            if not name:
                continue  # skip empty items

            quantity = _find_decimal(item, XML_PATHS["line_quantity"]) or Decimal(0)
            unit_price = _find_decimal(item, XML_PATHS["line_unit_price"]) or Decimal(0)
            amount = _find_decimal(item, XML_PATHS["line_amount"]) or Decimal(0)
            vat_rate_raw = _find_decimal(item, XML_PATHS["line_vat_rate"]) or Decimal(0)
            vat_amount = _find_decimal(item, XML_PATHS["line_vat_amount"])

            # Normalize VAT rate: XML may express as percentage (10) or decimal (0.1)
            if vat_rate_raw > 1:
                vat_rate = vat_rate_raw / 100
            else:
                vat_rate = vat_rate_raw

            # Calculate VAT amount if not provided
            if vat_amount is None:
                vat_amount = (amount * vat_rate).quantize(Decimal(1))

            lines.append(
                ParsedInvoiceLine(
                    name=name,
                    unit=_find_text(item, XML_PATHS["line_unit"]),
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount,
                    vat_rate=vat_rate,
                    vat_amount=vat_amount,
                )
            )

    # Build result
    return ParsedInvoice(
        seller_name=_find_text(root, XML_PATHS["seller_name"]),
        seller_mst=_find_text(root, XML_PATHS["seller_mst"]),
        seller_address=_find_text(root, XML_PATHS["seller_address"]),
        seller_phone=_find_text(root, XML_PATHS["seller_phone"]),
        seller_email=_find_text(root, XML_PATHS["seller_email"]),
        buyer_name=_find_text(root, XML_PATHS["buyer_name"]),
        buyer_mst=_find_text(root, XML_PATHS["buyer_mst"]),
        buyer_address=_find_text(root, XML_PATHS["buyer_address"]),
        buyer_phone=_find_text(root, XML_PATHS["buyer_phone"]),
        buyer_email=_find_text(root, XML_PATHS["buyer_email"]),
        invoice_number=invoice_number,
        invoice_symbol=raw_symbol,
        template_code=template_code,
        invoice_date=_find_date(root, XML_PATHS["invoice_date"]),
        parsed_symbol=parsed_symbol,
        lines=lines,
        total_before_vat=_find_decimal(root, XML_PATHS["total_before_vat"]),
        total_vat=_find_decimal(root, XML_PATHS["total_vat"]),
        total_after_vat=_find_decimal(root, XML_PATHS["total_after_vat"]),
        currency=_find_text(root, XML_PATHS["currency"], "VND"),
        exchange_rate=_find_decimal(root, XML_PATHS["exchange_rate"]) or Decimal(1),
        raw_xml=xml_bytes,
    )
