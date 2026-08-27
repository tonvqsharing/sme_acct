"""Unit tests for xml_ingest domain — symbol parser + XML parser."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from decimal import Decimal

import pytest

from src.bricks.xml_ingest.domain import (
    InvoiceCoding,
    parse_symbol,
    parse_xml_invoice,
)

# ─── Invoice symbol parser tests ──────────────────────────────────────


class TestParseSymbol:
    def test_vat_coded_2026(self):
        sym = parse_symbol("1", "C26TAA")
        assert sym.template_code == "1"
        assert sym.coding == InvoiceCoding.CODED
        assert sym.year == 26
        assert sym.full_year == 2026
        assert sym.type_code == "T"
        assert sym.internal_code == "AA"
        assert sym.raw == "1C26TAA"

    def test_sales_coded(self):
        sym = parse_symbol("2", "C26TBB")
        assert sym.template_code == "2"
        assert sym.type_code == "T"
        assert sym.template_description == "Sales invoice"

    def test_vat_uncoded(self):
        sym = parse_symbol("1", "K26TYY")
        assert sym.coding == InvoiceCoding.UNCODED
        assert sym.year == 26
        assert sym.internal_code == "YY"

    def test_internal_transfer(self):
        sym = parse_symbol("6", "K26NAB")
        assert sym.template_code == "6"
        assert sym.type_code == "N"
        assert sym.type_description == "internal warehouse transfer"

    def test_ecommerce(self):
        sym = parse_symbol("7", "K26XAB")
        assert sym.type_code == "X"
        assert sym.type_description == "e-commerce"

    def test_vat_refund(self):
        sym = parse_symbol("1", "C26FYY")
        assert sym.type_code == "F"
        assert sym.type_description == "VAT + refund declaration"

    def test_pos(self):
        sym = parse_symbol("1", "C26MYY")
        assert sym.type_code == "M"
        assert sym.type_description == "POS (point of sale)"

    def test_all_template_codes(self):
        for code in "123456789":
            sym = parse_symbol(code, "C26TYY")
            assert sym.template_code == code
            assert sym.template_description != "unknown"

    def test_all_type_codes(self):
        for code in ["T", "D", "L", "M", "N", "B", "G", "H", "X", "F"]:
            sym = parse_symbol("1", f"C26{code}YY")
            assert sym.type_code == code
            assert sym.type_description != "unknown"

    def test_invalid_template_code(self):
        with pytest.raises(ValueError, match="Invalid template code"):
            parse_symbol("0", "C26TYY")

    def test_invalid_template_code_alpha(self):
        with pytest.raises(ValueError, match="Invalid template code"):
            parse_symbol("A", "C26TYY")

    def test_symbol_too_short(self):
        with pytest.raises(ValueError, match="6 characters"):
            parse_symbol("1", "C26T")

    def test_symbol_too_long(self):
        with pytest.raises(ValueError, match="6 characters"):
            parse_symbol("1", "C26TAAZ")

    def test_invalid_coding_char(self):
        with pytest.raises(ValueError, match="First character"):
            parse_symbol("1", "A26TYY")

    def test_invalid_year_chars(self):
        with pytest.raises(ValueError, match="digits"):
            parse_symbol("1", "CXXTYY")

    def test_invalid_type_char(self):
        with pytest.raises(ValueError, match="Character 4"):
            parse_symbol("1", "C26ZYY")

    def test_invalid_internal_chars(self):
        with pytest.raises(ValueError, match="Characters 5-6"):
            parse_symbol("1", "C26T1Y")

    def test_whitespace_stripped(self):
        sym = parse_symbol(" 1 ", " C26TAA ")
        assert sym.raw == "1C26TAA"


# ─── XML parser tests ─────────────────────────────────────────────────

SAMPLE_VAT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<DLHDon xmlns="http://hoadon.gdt.gov.vn/xml/schemas/common">
  <HDon>
    <SHDon>00001234</SHDon>
    <KHMSHDon>AA</KHMSHDon>
    <KMHHDON>1</KMHHDON>
    <NLap>2026-08-15</NLap>
    <NBan>
      <Ten>ABC Company Ltd</Ten>
      <MST>0123456789</MST>
      <DChi>123 Le Loi, Q1, HCMC</DChi>
      <DienThoai>028-1234567</DienThoai>
      <Email>sales@abc.vn</Email>
    </NBan>
    <NMua>
      <Ten>XYZ Trading</Ten>
      <MST>9876543210</MST>
      <DChi>456 Nguyen Hue, Q1, HCMC</DChi>
    </NMua>
    <HHDVu>
      <HH>
        <Ten>Văn phòng phẩm T8</Ten>
        <DVTinh>cái</DVTinh>
        <SLuong>100</SLuong>
        <DGia>20000</DGia>
        <ThTien>2000000</ThTien>
        <TSuat>10</TSuat>
      </HH>
      <HH>
        <Ten>Mực in</Ten>
        <DVTinh>hộp</DVTinh>
        <SLuong>50</SLuong>
        <DGia>80000</DGia>
        <ThTien>4000000</ThTien>
        <TSuat>10</TSuat>
      </HH>
    </HHDVu>
    <THTTLTE>6000000</THTTLTE>
    <TTCKTM>600000</TTCKTM>
    <TongCong>6600000</TongCong>
    <DVTTe>VND</DVTTe>
  </HDon>
</DLHDon>
"""

SAMPLE_SALES_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<DLHDon>
  <HDon>
    <SHDon>INV-001</SHDon>
    <KHMSHDon>BB</KHMSHDon>
    <KMHHDON>2</KMHHDON>
    <NLap>15/08/2026</NLap>
    <NBan>
      <Ten>Seller Corp</Ten>
      <MST>1112223334</MST>
      <DChi>789 Dien Bien Phu, Binh Thanh</DChi>
    </NBan>
    <NMua>
      <Ten>Buyer Inc</Ten>
      <MST>4445556667</MST>
    </NMua>
    <HHDVu>
      <Item>
        <Ten>Hàng hóa A</Ten>
        <DVTinh>chiếc</DVTinh>
        <SLuong>10</SLuong>
        <DGia>500000</DGia>
        <ThTien>5000000</ThTien>
        <TSuat>8</TSuat>
      </Item>
    </HHDVu>
    <TongCong>5400000</TongCong>
  </HDon>
</DLHDon>
"""

SAMPLE_MINIMAL_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<invoice>
  <header>
    <invoiceNo>MIN-001</invoiceNo>
    <invoiceSymbol>CC26TYY</invoiceSymbol>
    <templateCode>1</templateCode>
    <invoiceDate>2026-08-20</invoiceDate>
  </header>
  <seller>
    <name>Minimal Seller</name>
    <taxCode>1234567890</taxCode>
    <address>Ha Noi</address>
  </seller>
  <buyer>
    <name>Minimal Buyer</name>
    <taxCode>0987654321</taxCode>
  </buyer>
  <items>
    <item>
      <itemName>Dịch vụ tư vấn</itemName>
      <unit>lần</unit>
      <quantity>1</quantity>
      <unitPrice>10000000</unitPrice>
      <amount>10000000</amount>
      <vatRate>10</vatRate>
    </item>
  </items>
  <totalAmount>11000000</totalAmount>
</invoice>
"""


class TestParseXmlInvoice:
    def test_vat_invoice_with_namespace(self):
        inv = parse_xml_invoice(SAMPLE_VAT_XML.encode())
        assert inv.invoice_number == "00001234"
        assert inv.seller_name == "ABC Company Ltd"
        assert inv.seller_mst == "0123456789"
        assert inv.buyer_name == "XYZ Trading"
        assert inv.buyer_mst == "9876543210"
        assert inv.invoice_date is not None
        assert inv.invoice_date.year == 2026
        assert inv.invoice_date.month == 8
        assert inv.invoice_date.day == 15
        assert len(inv.lines) == 2
        assert inv.lines[0].name == "Văn phòng phẩm T8"
        assert inv.lines[0].quantity == Decimal(100)
        assert inv.lines[0].unit_price == Decimal(20000)
        assert inv.lines[0].amount == Decimal(2000000)
        assert inv.lines[0].vat_rate == Decimal("0.10")
        assert inv.total_before_vat == Decimal(6000000)
        assert inv.total_vat == Decimal(600000)
        assert inv.total_after_vat == Decimal(6600000)

    def test_sales_invoice_no_namespace(self):
        inv = parse_xml_invoice(SAMPLE_SALES_XML.encode())
        assert inv.invoice_number == "INV-001"
        assert inv.seller_name == "Seller Corp"
        assert inv.buyer_name == "Buyer Inc"
        assert len(inv.lines) == 1
        assert inv.lines[0].vat_rate == Decimal("0.08")

    def test_minimal_invoice(self):
        inv = parse_xml_invoice(SAMPLE_MINIMAL_XML.encode())
        assert inv.invoice_number == "MIN-001"
        assert inv.seller_name == "Minimal Seller"
        assert inv.buyer_name == "Minimal Buyer"
        assert len(inv.lines) == 1
        assert inv.lines[0].name == "Dịch vụ tư vấn"

    def test_vat_rate_normalization(self):
        """VAT rate 10 (percentage) should normalize to 0.10 (decimal)."""
        inv = parse_xml_invoice(SAMPLE_VAT_XML.encode())
        assert inv.lines[0].vat_rate == Decimal("0.10")

    def test_vat_amount_calculated_when_missing(self):
        """VAT amount should be calculated from amount * rate when not in XML."""
        xml = SAMPLE_VAT_XML.encode()
        inv = parse_xml_invoice(xml)
        # First line: amount=2000000, rate=0.10 → vat=200000
        assert inv.lines[0].vat_amount == Decimal(200000)

    def test_missing_invoice_number_raises(self):
        xml = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<DLHDon>
  <HDon>
    <NBan><MST>123</MST></NBan>
  </HDon>
</DLHDon>
"""
        with pytest.raises(ValueError, match="Missing invoice number"):
            parse_xml_invoice(xml)

    def test_malformed_xml_raises(self):
        with pytest.raises(ET.ParseError):
            parse_xml_invoice(b"<not valid xml")

    def test_empty_xml_raises(self):
        with pytest.raises(ET.ParseError):
            parse_xml_invoice(b"")

    def test_symbol_parsed_when_full_format(self):
        """Symbol is parsed when KHMSHDon contains full 6-char format."""
        # Real GDT XML has just the series code (e.g. AA), not full 6-char symbol.
        # So parsed_symbol is None for typical real-world XML.
        xml = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<DLHDon xmlns="http://hoadon.gdt.gov.vn/xml/schemas/common">
  <HDon>
    <SHDon>00009999</SHDon>
    <KHMSHDon>C26TAA</KHMSHDon>
    <KMHHDON>1</KMHHDON>
    <NLap>2026-08-15</NLap>
    <NBan><MST>0123456789</MST></NBan>
    <NMua><MST>9876543210</MST></NMua>
    <HHDVu>
      <HH><Ten>X</Ten><ThTien>100</ThTien><TSuat>10</TSuat></HH>
    </HHDVu>
  </HDon>
</DLHDon>
"""
        inv = parse_xml_invoice(xml)
        assert inv.parsed_symbol is not None
        assert inv.parsed_symbol.template_code == "1"
        assert inv.parsed_symbol.coding == InvoiceCoding.CODED
        assert inv.parsed_symbol.type_code == "T"

    def test_symbol_none_for_series_code_only(self):
        """Typical real-world XML: KHMSHDon is just series (e.g. AA), not full symbol."""
        inv = parse_xml_invoice(SAMPLE_VAT_XML.encode())
        assert inv.invoice_symbol == "AA"
        assert inv.parsed_symbol is None  # 2-char series, not 6-char format

    def test_symbol_optional_when_invalid(self):
        """Symbol parsing is best-effort; invalid format should not crash."""
        xml = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<invoice>
  <header>
    <invoiceNo>INV-002</invoiceNo>
    <invoiceSymbol>INVALID</invoiceSymbol>
    <templateCode>1</templateCode>
    <invoiceDate>2026-08-20</invoiceDate>
  </header>
  <seller><name>S</name><taxCode>123</taxCode></seller>
  <buyer><name>B</name><taxCode>456</taxCode></buyer>
  <items>
    <item><itemName>X</itemName><amount>100</amount></item>
  </items>
</invoice>
"""
        inv = parse_xml_invoice(xml)
        assert inv.invoice_number == "INV-002"
        assert inv.invoice_symbol == "INVALID"
        assert inv.parsed_symbol is None  # invalid symbol → None

    def test_symbol_optional_when_missing(self):
        """No template_code in XML → parsed_symbol is None."""
        xml = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<invoice>
  <header>
    <invoiceNo>INV-003</invoiceNo>
  </header>
  <seller><name>S</name><taxCode>123</taxCode></seller>
  <buyer><name>B</name><taxCode>456</taxCode></buyer>
  <items>
    <item><itemName>X</itemName><amount>100</amount></item>
  </items>
</invoice>
"""
        inv = parse_xml_invoice(xml)
        assert inv.parsed_symbol is None

    def test_currency_defaults_to_vnd(self):
        inv = parse_xml_invoice(SAMPLE_MINIMAL_XML.encode())
        assert inv.currency == "VND"

    def test_raw_xml_preserved(self):
        xml = SAMPLE_VAT_XML.encode()
        inv = parse_xml_invoice(xml)
        assert inv.raw_xml == xml
