# Financial Statements — Report Templates

**Module:** Financial Statements
**Date:** 2026-08-28
**Regulatory basis:** TT99/2025/TT-BTC

---

## 1. Template Engine Design

### 1.1 Architecture

```python
class ReportTemplate(Base):
    """Template definition for a financial statement."""
    __tablename__ = "report_template"
    
    id: Mapped[UUID]
    code: Mapped[str]           # e.g., "B01-DN", "B02-DN"
    name: Mapped[str]           # Vietnamese name
    description: Mapped[str | None]
    fiscal_year_id: Mapped[UUID | None]  # NULL = global template
    is_active: Mapped[bool]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]


class ReportTemplateLine(Base):
    """One row in a report template."""
    __tablename__ = "report_template_line"
    
    id: Mapped[UUID]
    template_id: Mapped[UUID] = mapped_column(ForeignKey("report_template.id"))
    line_code: Mapped[str]     # e.g., "110", "280", "A"
    line_name: Mapped[str]     # Vietnamese label
    line_type: Mapped[str]     # "HEADER", "ACCOUNT_AGGREGATE", "FORMULA", "TOTAL"
    account_codes: Mapped[JSON] = mapped_column(JSON, default=list)  # ["111", "112", "113"]
    formula: Mapped[str | None]  # e.g., "line_110 - line_120"
    parent_code: Mapped[str | None]  # For hierarchy
    level: Mapped[int]          # Indentation level (0=main, 1=sub, 2=detail)
    sort_order: Mapped[int]
    sign: Mapped[int]           # 1 or -1 (for contra accounts)


class ReportInstance(Base):
    """Calculated snapshot of a report."""
    __tablename__ = "report_instance"
    
    id: Mapped[UUID]
    template_id: Mapped[UUID] = mapped_column(ForeignKey("report_template.id"))
    company_id: Mapped[UUID]
    period_from: Mapped[date]
    period_to: Mapped[date]
    computed_at: Mapped[datetime]
    status: Mapped[str]         # "DRAFT", "FINAL", "SUPERSEDED"
    created_by: Mapped[UUID]


class ReportInstanceLine(Base):
    """Calculated value for one line."""
    __tablename__ = "report_instance_line"
    
    id: Mapped[UUID]
    instance_id: Mapped[UUID] = mapped_column(ForeignKey("report_instance.id"))
    line_code: Mapped[str]
    line_name: Mapped[str]
    value_current: Mapped[Decimal]   # Current period
    value_prior: Mapped[Decimal | None]  # Prior period (for comparatives)
    value_current_month: Mapped[Decimal | None]  # For monthly breakdown
```

---

## 2. B01-DN Template (Balance Sheet)

```python
B01_DN_TEMPLATE = [
    {"code": "A", "name": "TÀI SẢN NGẮN HẠN", "type": "HEADER", "level": 0},
    {"code": "100", "name": "Tài sản ngắn hạn", "type": "HEADER", "level": 1},
    {"code": "110", "name": "Tiền và các khoản tiền tương đương", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["111", "112", "113"], "level": 2},
    {"code": "120", "name": "Đầu tư tài chính ngắn hạn", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["121", "128"], "level": 2},
    {"code": "130", "name": "Phải thu ngắn hạn", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["131", "132", "133", "138"], "level": 2},
    {"code": "150", "name": "Hàng tồn kho", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["151", "152", "154", "155", "156"], "level": 2},
    {"code": "180", "name": "Tài sản ngắn hạn khác", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["180"], "level": 2},
    {"code": "200", "name": "TỔNG TÀI SẢN NGẮN HẠN", "type": "TOTAL",
     "formula": "sum(110, 120, 130, 150, 180)", "level": 1},
    
    {"code": "B", "name": "TÀI SẢN DÀI HẠN", "type": "HEADER", "level": 0},
    {"code": "210", "name": "Đầu tư tài chính dài hạn", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["211", "212", "219"], "level": 1},
    {"code": "220", "name": "Tài sản cố định", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["211x", "214", "213", "217", "215"], "level": 1},
    {"code": "230", "name": "Bất động sản đầu tư", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["230"], "level": 1},
    {"code": "240", "name": "Chi phí trả trước dài hạn", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["240"], "level": 1},
    {"code": "250", "name": "Thuế thu nhập hoãn lại phải nộp", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["250"], "level": 1},
    {"code": "260", "name": "Tài sản dài hạn khác", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["260"], "level": 1},
    {"code": "270", "name": "TỔNG TÀI SẢN DÀI HẠN", "type": "TOTAL",
     "formula": "sum(210, 220, 230, 240, 250, 260)", "level": 0},
    
    {"code": "280", "name": "TỔNG CỘNG TÀI SẢN (200 + 270)", "type": "TOTAL",
     "formula": "line_200 + line_270", "level": 0},
    
    {"code": "C", "name": "NỢ PHẢI TRẢ", "type": "HEADER", "level": 0},
    {"code": "300", "name": "Nợ ngắn hạn", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["341", "331", "332", "333", "338"], "level": 1},
    {"code": "310", "name": "Nợ dài hạn", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["341x", "343x", "336"], "level": 1},
    {"code": "320", "name": "TỔNG NỢ PHẢI TRẢ (300 + 310)", "type": "TOTAL",
     "formula": "line_300 + line_310", "level": 0},
    
    {"code": "D", "name": "VỐN CHỦ SỞ HỮU", "type": "HEADER", "level": 0},
    {"code": "410", "name": "Vốn đầu tư của chủ sở hữu", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["411"], "level": 1},
    {"code": "420", "name": "Thặng dư vốn", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["412"], "level": 1},
    {"code": "430", "name": "Vốn bổ sung", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["413"], "level": 1},
    {"code": "440", "name": "Lợi nhuận chưa phân phối", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["421"], "level": 1},
    {"code": "450", "name": "TỔNG VỐN CHỦ SỞ HỮU (410+420+430+440)", "type": "TOTAL",
     "formula": "line_410 + line_420 + line_430 + line_440", "level": 0},
    
    {"code": "460", "name": "TỔNG CỘNG NỢ + VỐN (320 + 450)", "type": "TOTAL",
     "formula": "line_320 + line_450", "level": 0},
]
```

---

## 3. B02-DN Template (Income Statement)

```python
B02_DN_TEMPLATE = [
    {"code": "A", "name": "DOANH THU", "type": "HEADER", "level": 0},
    {"code": "510", "name": "Doanh thu bán hàng và cung cấp dịch vụ", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["511"], "sign": 1, "level": 1},
    {"code": "520", "name": "Các khoản giảm trừ doanh thu", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["521"], "sign": -1, "level": 1},
    {"code": "530", "name": "Doanh thu thuần", "type": "TOTAL",
     "formula": "line_510 - line_520", "level": 0},
    
    {"code": "B", "name": "GIÁ VỐN HÀNG BÁN", "type": "HEADER", "level": 0},
    {"code": "632", "name": "Giá vốn hàng bán", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["632"], "level": 1},
    
    {"code": "640", "name": "LỢI NHUẬN GỘP (530 - 632)", "type": "TOTAL",
     "formula": "line_530 - line_632", "level": 0},
    
    {"code": "C", "name": "CHI PHÍ HOẠT ĐỘNG", "type": "HEADER", "level": 0},
    {"code": "641", "name": "Chi phí bán hàng", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["641"], "level": 1},
    {"code": "642", "name": "Chi phí quản lý doanh nghiệp", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["642"], "level": 1},
    {"code": "650", "name": "Tổng chi phí hoạt động", "type": "TOTAL",
     "formula": "line_641 + line_642", "level": 0},
    
    {"code": "660", "name": "LỢI NHUẬN HOẠT ĐỘNG KINH DOANH (640 - 650)", "type": "TOTAL",
     "formula": "line_640 - line_650", "level": 0},
    
    {"code": "D", "name": "THU NHẬP TÀI CHÍNH", "type": "HEADER", "level": 0},
    {"code": "515", "name": "Thu nhập tài chính", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["515"], "level": 1},
    {"code": "635", "name": "Chi phí tài chính", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["635"], "sign": -1, "level": 1},
    {"code": "670", "name": "Thu nhập tài chính ròng", "type": "TOTAL",
     "formula": "line_515 + line_635", "level": 0},
    
    {"code": "E", "name": "KẾT QUẢ HOẠT ĐỘNG KINH DOANH (660 + 670)", "type": "TOTAL",
     "formula": "line_660 + line_670", "level": 0},
    
    {"code": "F", "name": "KẾT QUẢ HOẠT ĐỘNG KHÁC", "type": "HEADER", "level": 0},
    {"code": "711", "name": "Thu nhập khác", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["711"], "level": 1},
    {"code": "811", "name": "Chi phí khác", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["811"], "sign": -1, "level": 1},
    {"code": "680", "name": "Kết quả hoạt động khác", "type": "TOTAL",
     "formula": "line_711 + line_811", "level": 0},
    
    {"code": "690", "name": "LỢI NHUẬN TRƯỚC THUẾ (660 + 670 + 680)", "type": "TOTAL",
     "formula": "line_660 + line_670 + line_680", "level": 0},
    
    {"code": "G", "name": "CHI PHÍ THUẾ", "type": "HEADER", "level": 0},
    {"code": "821", "name": "Chi phí thuế thu nhập doanh nghiệp", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["821"], "sign": -1, "level": 1},
    
    {"code": "700", "name": "LỢI NHUẬN SAU THUẾ (690 + 821)", "type": "TOTAL",
     "formula": "line_690 + line_821", "level": 0},
]
```

---

## 4. B03-DN Template (Cash Flow)

```python
B03_DN_TEMPLATE = [
    {"code": "A", "name": "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG SẢN XUẤT KINH DOANH", "type": "HEADER", "level": 0},
    {"code": "A1", "name": "Tiền thu từ bán hàng, cung cấp dịch vụ", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "IN", "level": 1},
    {"code": "A2", "name": "Tiền thu lãi, cổ tức", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "IN", "level": 1},
    {"code": "A3", "name": "Tiền trả cho nhà cung cấp", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "OUT", "level": 1},
    {"code": "A4", "name": "Tiền trả cho người lao động", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "OUT", "level": 1},
    {"code": "A5", "name": "Tiền trả lãi vay", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "OUT", "level": 1},
    {"code": "A6", "name": "Tiền nộp thuế thu nhập doanh nghiệp", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "OUT", "level": 1},
    {"code": "A7", "name": "Các khoản tiền thu khác", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "IN", "level": 1},
    {"code": "A8", "name": "Các khoản tiền trả khác", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "OUT", "level": 1},
    {"code": "A9", "name": "Tiền nộp thuế GTGT", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "OUT", "level": 1},
    {"code": "A10", "name": "Tiền thuế khác", "type": "CASH_FLOW_ITEM",
     "activity": "OPERATING", "direction": "OUT", "level": 1},
    {"code": "A_TONG", "name": "Lưu chuyển tiền ròng từ HĐSXKD", "type": "TOTAL",
     "formula": "sum(A1..A10)", "level": 0},
    
    {"code": "B", "name": "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ", "type": "HEADER", "level": 0},
    {"code": "B1", "name": "Tiền mua sắm tài sản cố định", "type": "CASH_FLOW_ITEM",
     "activity": "INVESTING", "direction": "OUT", "level": 1},
    {"code": "B2", "name": "Tiền bán tài sản cố định", "type": "CASH_FLOW_ITEM",
     "activity": "INVESTING", "direction": "IN", "level": 1},
    {"code": "B_TONG", "name": "Lưu chuyển tiền ròng từ HĐĐT", "type": "TOTAL",
     "formula": "sum(B1, B2)", "level": 0},
    
    {"code": "C", "name": "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH", "type": "HEADER", "level": 0},
    {"code": "C1", "name": "Tiền vay ngân hàng", "type": "CASH_FLOW_ITEM",
     "activity": "FINANCING", "direction": "IN", "level": 1},
    {"code": "C2", "name": "Tiền trả nợ vay", "type": "CASH_FLOW_ITEM",
     "activity": "FINANCING", "direction": "OUT", "level": 1},
    {"code": "C3", "name": "Đóng góp vốn chủ sở hữu", "type": "CASH_FLOW_ITEM",
     "activity": "FINANCING", "direction": "IN", "level": 1},
    {"code": "C4", "name": "Chi trả cổ tức", "type": "CASH_FLOW_ITEM",
     "activity": "FINANCING", "direction": "OUT", "level": 1},
    {"code": "C_TONG", "name": "Lưu chuyển tiền ròng từ HĐTC", "type": "TOTAL",
     "formula": "sum(C1..C4)", "level": 0},
    
    {"code": "D", "name": "TĂNG GIẢM TIỀN GỬI NGÂN HÀNG (A_TONG + B_TONG + C_TONG)", "type": "TOTAL",
     "formula": "line_A_TONG + line_B_TONG + line_C_TONG", "level": 0},
    
    {"code": "E", "name": "TỶ GIÁ QUY ĐỔI", "type": "HEADER", "level": 0},
    {"code": "E1", "name": "Tiền gửi ngân hàng đầu kỳ", "type": "ACCOUNT_AGGREGATE",
     "accounts": ["112"], "level": 1},
    {"code": "E2", "name": "Ảnh hưởng tỷ giá quy đổi", "type": "FORMULA",
     "formula": "fx_impact", "level": 1},
    
    {"code": "700", "name": "TIỀN GỬI NGÂN HÀNG CUỐI KỲ = E1 + D + E2", "type": "TOTAL",
     "formula": "line_E1 + line_D + line_E2", "level": 0},
]
```

---

## 5. S06-DN Template (Trial Balance)

```python
S06_DN_TEMPLATE = [
    {"code": "I", "name": "TÀI SẢN (1xx)", "type": "HEADER", "level": 0,
     "account_type": "ASSET"},
    {"code": "II", "name": "NỢ PHẢI TRẢ (2xx)", "type": "HEADER", "level": 0,
     "account_type": "LIABILITY"},
    {"code": "III", "name": "VỐN CHỦ SỞ HỮU (3xx)", "type": "HEADER", "level": 0,
     "account_type": "EQUITY"},
    {"code": "IV", "name": "DOANH THU (4xx)", "type": "HEADER", "level": 0,
     "account_type": "REVENUE"},
    {"code": "V", "name": "CHI PHÍ (5xx)", "type": "HEADER", "level": 0,
     "account_type": "EXPENSE"},
]
```

---

## 6. Template Seeding Strategy

Templates are seeded on first company creation via `seed_report_templates()`:

```python
def seed_report_templates(company_id: UUID) -> None:
    """Create default TT99 report templates for a company."""
    templates = [
        ("B01-DN", "Bảng cân đối kế toán", B01_DN_TEMPLATE),
        ("B02-DN", "Báo cáo kết quả kinh doanh", B02_DN_TEMPLATE),
        ("B03-DN", "Báo cáo lưu chuyển tiền tệ", B03_DN_TEMPLATE),
        ("S06-DN", "Bảng cân đối phát sinh", S06_DN_TEMPLATE),
    ]
    for code, name, lines in templates:
        template = ReportTemplate(code=code, name=name, ...)
        db.session.add(template)
        for line in lines:
            db.session.add(ReportTemplateLine(template_id=template.id, ...))
    db.session.commit()
```

---

## 7. API Response Format

### GET /api/v1/reports/balance-sheet?period_to=2026-08-31

```json
{
  "template": "B01-DN",
  "name": "Bảng cân đối kế toán",
  "period_to": "2026-08-31",
  "status": "DRAFT",
  "lines": [
    {"code": "A", "name": "TÀI SẢN NGẮN HẠN", "value_current": null, "level": 0},
    {"code": "110", "name": "Tiền và các khoản tiền tương đương", "value_current": 150000000, "level": 2},
    {"code": "120", "name": "Đầu tư tài chính ngắn hạn", "value_current": 0, "level": 2},
    {"code": "130", "name": "Phải thu ngắn hạn", "value_current": 230000000, "level": 2},
    {"code": "150", "name": "Hàng tồn kho", "value_current": 85000000, "level": 2},
    {"code": "180", "name": "Tài sản ngắn hạn khác", "value_current": 15000000, "level": 2},
    {"code": "200", "name": "TỔNG TÀI SẢN NGẮN HẠN", "value_current": 480000000, "level": 1},
    {"code": "280", "name": "TỔNG CỘNG TÀI SẢN", "value_current": 830000000, "level": 0},
    {"code": "320", "name": "TỔNG NỢ PHẢI TRẢ", "value_current": 330000000, "level": 0},
    {"code": "450", "name": "TỔNG VỐN CHỦ SỞ HỮU", "value_current": 500000000, "level": 0},
    {"code": "460", "name": "TỔNG CỘNG NỢ + VỐN", "value_current": 830000000, "level": 0}
  ],
  "checks": {
    "balance_ok": true,
    "assets": 830000000,
    "liabilities_equity": 830000000
  }
}
```
