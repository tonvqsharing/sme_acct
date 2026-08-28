"""Financial Statement templates — TT99 Appendix IV predefined line structures.

Pure data: template line definitions for B01-DN, B02-DN, B03-DN, S06-DN.
No Flask/SQLAlchemy imports.
"""

from __future__ import annotations

from src.bricks.financial_statements.domain import (
    LineType,
    ReportTemplate,
    ReportTemplateLine,
)


def b01_dn_template() -> ReportTemplate:
    """B01-DN: Statement of Financial Position (Balance Sheet).

    TT99 Appendix IV structure:
    A. Short-term Assets (100-180)
    B. Long-term Assets (200-260)
    C. Liabilities (300-330)
    D. Owners' Equity (400)
    """
    lines = [
        # ── A. SHORT-TERM ASSETS ──────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A",
            line_name="Tài sản ngắn hạn",
            line_type=LineType.HEADER,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A1",
            line_name="Tiền và các khoản tiền equivalent",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["111", "112", "113"],
            parent_code="A_TONG",
            level=1,
            sort_order=1,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A2",
            line_name="Đầu tư tài chính ngắn hạn",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["121", "128"],
            parent_code="A_TONG",
            level=1,
            sort_order=2,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A3",
            line_name="Phải thu ngắn hạn",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["131", "132", "133", "138"],
            parent_code="A_TONG",
            level=1,
            sort_order=3,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A4",
            line_name="Hàng tồn kho",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["151", "152", "154", "155", "156"],
            parent_code="A_TONG",
            level=1,
            sort_order=4,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A5",
            line_name="Tài sản ngắn hạn khác",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["180"],
            parent_code="A_TONG",
            level=1,
            sort_order=5,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A_TONG",
            line_name="Tổng tài sản ngắn hạn",
            line_type=LineType.TOTAL,
            parent_code=None,
            level=0,
            sort_order=10,
        ),
        # ── B. LONG-TERM ASSETS ───────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="B",
            line_name="Tài sản dài hạn",
            line_type=LineType.HEADER,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="B1",
            line_name="Đầu tư tài chính dài hạn",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["211", "212", "219"],
            parent_code="B_TONG",
            level=1,
            sort_order=11,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="B2",
            line_name="Tài sản cố định ròng",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["213", "214", "215", "217"],
            parent_code="B_TONG",
            level=1,
            sort_order=12,
            # No sign flip needed — contra accounts (213) already have
            # negative net via debit-credit calculation.
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="B3",
            line_name="Bất động sản đầu tư",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["230"],
            parent_code="B_TONG",
            level=1,
            sort_order=13,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="B4",
            line_name="Chi phí trả trước dài hạn",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["240"],
            parent_code="B_TONG",
            level=1,
            sort_order=14,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="B5",
            line_name="Thuế thu nhập hoãn lại phải nộp",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["250"],
            parent_code="B_TONG",
            level=1,
            sort_order=15,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="B6",
            line_name="Tài sản dài hạn khác",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["260"],
            parent_code="B_TONG",
            level=1,
            sort_order=16,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="B_TONG",
            line_name="Tổng tài sản dài hạn",
            line_type=LineType.TOTAL,
            parent_code=None,
            level=0,
            sort_order=20,
        ),
        # ── TOTAL ASSETS ──────────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="TS_TONG",
            line_name="TỔNG CỘNG TÀI SẢN",
            line_type=LineType.FORMULA,
            formula="A_TONG+B_TONG",
            level=0,
            sort_order=25,
        ),
        # ── C. LIABILITIES ────────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="C",
            line_name="Nợ phải trả",
            line_type=LineType.HEADER,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="C1",
            line_name="Nợ ngắn hạn",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["331", "332", "333", "335", "336", "338", "340", "341"],
            parent_code="C_TONG",
            level=1,
            sort_order=30,
            sign=-1,  # Liability: credit balance → sign flip for positive display
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="C2",
            line_name="Nợ dài hạn",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["342", "343", "344", "351", "352", "353"],
            parent_code="C_TONG",
            level=1,
            sort_order=31,
            sign=-1,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="C_TONG",
            line_name="Tổng nợ phải trả",
            line_type=LineType.TOTAL,
            parent_code=None,
            level=0,
            sort_order=35,
        ),
        # ── D. OWNERS' EQUITY ─────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="D",
            line_name="Vốn chủ sở hữu",
            line_type=LineType.HEADER,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="D1",
            line_name="Vốn góp",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["411"],
            parent_code="D_TONG",
            level=1,
            sort_order=40,
            sign=-1,  # Equity: credit balance → sign flip
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="D2",
            line_name="Thặng dư vốn",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["412"],
            parent_code="D_TONG",
            level=1,
            sort_order=41,
            sign=-1,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="D3",
            line_name="Quỹ đánh giá lại",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["413"],
            parent_code="D_TONG",
            level=1,
            sort_order=42,
            sign=-1,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="D4",
            line_name="Lợi nhuận chưa phân phối",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["421"],
            parent_code="D_TONG",
            level=1,
            sort_order=43,
            sign=-1,
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="D_TONG",
            line_name="Tổng vốn chủ sở hữu",
            line_type=LineType.TOTAL,
            parent_code=None,
            level=0,
            sort_order=45,
        ),
        # ── TOTAL LIABILITIES + EQUITY ────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="NNC_TONG",
            line_name="TỔNG CỘNG NỢ PHẢI TRẢ VÀ VỐN CHỦ SỞ HỮU",
            line_type=LineType.FORMULA,
            formula="C_TONG+D_TONG",
            level=0,
            sort_order=50,
        ),
        # ── BALANCE CHECK ─────────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="CHECK",
            line_name="Kiểm tra cân đối",
            line_type=LineType.FORMULA,
            formula="TS_TONG-NNC_TONG",
            level=0,
            sort_order=99,
        ),
    ]

    return ReportTemplate(
        code="B01-DN",
        name="Bảng cân đối kế toán",
        description="Statement of Financial Position per TT99 Appendix IV",
        lines=lines,
    )


def b02_dn_template() -> ReportTemplate:
    """B02-DN: Statement of Profit or Loss (Income Statement).

    TT99 Appendix IV structure:
    A. Net Revenue (511 - 521)
    B. Cost of Goods Sold (632)
    GROSS PROFIT (A - B)
    C. Sales Expenses (641)
    D. Admin Expenses (642)
    OPERATING PROFIT (A - B - C - D)
    E. Financial Income (515)
    F. Financial Expenses (635)
    NET FINANCIAL (E - F)
    G. Other Income (711)
    H. Other Expenses (811)
    PROFIT BEFORE TAX
    I. Income Tax Expense (821)
    NET PROFIT
    """
    lines = [
        # ── A. NET REVENUE ────────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A",
            line_name="Doanh thu bán hàng và cung cấp dịch vụ",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["511"],
            level=0,
            sort_order=1,
            sign=-1,  # Revenue: credit balance → sign flip
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A_DISC",
            line_name="Chiết khấu bán hàng",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["521"],
            level=0,
            sort_order=2,
            sign=1,  # Contra-revenue: debit balance → positive
        ),
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="A_NET",
            line_name="Doanh thu thuần",
            line_type=LineType.FORMULA,
            formula="A-A_DISC",
            level=0,
            sort_order=3,
        ),
        # ── B. COST OF GOODS SOLD ─────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="B",
            line_name="Giá vốn hàng bán",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["632"],
            level=0,
            sort_order=10,
        ),
        # ── GROSS PROFIT ──────────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="GROSS_PROFIT",
            line_name="Lợi nhuận gộp về bán hàng và cung cấp dịch vụ",
            line_type=LineType.FORMULA,
            formula="A_NET-B",
            level=0,
            sort_order=15,
        ),
        # ── C. SALES EXPENSES ─────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="C",
            line_name="Chi phí bán hàng",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["641"],
            level=0,
            sort_order=20,
        ),
        # ── D. ADMIN EXPENSES ─────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="D",
            line_name="Chi phí quản lý doanh nghiệp",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["642"],
            level=0,
            sort_order=25,
        ),
        # ── OPERATING PROFIT ──────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="OP_PROFIT",
            line_name="Lợi nhuận từ hoạt động kinh doanh",
            line_type=LineType.FORMULA,
            formula="GROSS_PROFIT-C-D",
            level=0,
            sort_order=30,
        ),
        # ── E. FINANCIAL INCOME ───────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="E",
            line_name="Thu nhập tài chính",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["515"],
            level=0,
            sort_order=40,
            sign=-1,  # Revenue: credit balance → sign flip
        ),
        # ── F. FINANCIAL EXPENSES ─────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="F",
            line_name="Chi phí tài chính",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["635"],
            level=0,
            sort_order=45,
        ),
        # ── NET FINANCIAL ─────────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="NET_FIN",
            line_name="Thu nhập (chi phí) tài chính thuần",
            line_type=LineType.FORMULA,
            formula="E-F",
            level=0,
            sort_order=50,
        ),
        # ── G. OTHER INCOME ───────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="G",
            line_name="Thu nhập khác",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["711"],
            level=0,
            sort_order=55,
            sign=-1,  # Revenue: credit balance → sign flip
        ),
        # ── H. OTHER EXPENSES ─────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="H",
            line_name="Chi phí khác",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["811"],
            level=0,
            sort_order=60,
        ),
        # ── PROFIT BEFORE TAX ─────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="PROFIT_BT",
            line_name="Lợi nhuận trước thuế thu nhập doanh nghiệp",
            line_type=LineType.FORMULA,
            formula="OP_PROFIT+NET_FIN+G-H",
            level=0,
            sort_order=65,
        ),
        # ── I. INCOME TAX ─────────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="I",
            line_name="Chi phí thuế thu nhập doanh nghiệp",
            line_type=LineType.ACCOUNT_AGGREGATE,
            account_codes=["821"],
            level=0,
            sort_order=70,
        ),
        # ── NET PROFIT ────────────────────────────────────────────────
        ReportTemplateLine(
            template_id=None,  # type: ignore[arg-type]
            line_code="NET_PROFIT",
            line_name="Lợi nhuận sau thuế thu nhập doanh nghiệp",
            line_type=LineType.FORMULA,
            formula="PROFIT_BT-I",
            level=0,
            sort_order=99,
        ),
    ]

    return ReportTemplate(
        code="B02-DN",
        name="Báo cáo kết quả hoạt động kinh doanh",
        description="Statement of Profit or Loss per TT99 Appendix IV",
        lines=lines,
    )
