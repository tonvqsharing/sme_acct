# BRD — Công cụ, Dụng cụ (Tools & Equipment / CCDC)

## 1. Business Context

### 1.1 Problem Statement
Doanh nghiệp SME Việt Nam cần quản lý công cụ dụng cụ (CCDC) — tư liệu lao động không đủ tiêu chuẩn ghi nhận TSCĐ. Hiện tại, hệ thống chưa có brick CCDC,导致 TK 153 (Công cụ, dụng cụ) không có nguồn giao dịch, báo cáo tài chính không đầy đủ.

### 1.2 Regulatory Framework
| Văn bản | Nội dung | Trạng thái |
|---------|----------|------------|
| **TT 99/2025/TT-BTC** | Chế độ kế toán doanh nghiệp (thay thế TT200/2014) | Có hiệu lực 01/01/2026 |
| **TT 133/2016/TT-BTC** | Chế độ kế toán DNNVV | Còn hiệu lực |
| **Luật Kế toán 2015** | Art. 11 — lưu trữ 10 năm | Còn hiệu lực |
| **NĐ 174/2025/NĐ-CP** | VAT 8% giảm (NQ 204/2025/QH15) | Đến 31/12/2026 |

### 1.3 Definition of CCDC
Theo Điều 26 TT200/2014/TT-BTC (vẫn áp dụng qua TT99/2025):
- **CCDC** = tư liệu lao động **không** đủ tiêu chuẩn ghi nhận TSCĐ
- Tiêu chuẩn TSCĐ: nguyên giá ≥ 5.000.000 VND **và** thời gian sử dụng ≥ 12 tháng
- → CCDC: nguyên giá < 5.000.000 VND **hoặc** thời gian sử dụng < 12 tháng

**Lưu ý:** Một số nguồn đề cập ngưỡng 30.000.000 VND — đây là ngưỡng cũ từ QĐ 15/2006, đã được thay thế bởi Luật Kế toán 2015 (ngưỡng 5.000.000 VND).

### 1.4 Scope

**In Scope (MVP):**
- CRUD CCDC (master data)
- Phân loại CCDC (category)
- Theo dõi CCDC theo bộ phận sử dụng (cost center / dimension)
- Ghi tăng CCDC (từ chứng từ mua hàng)
- Phân bổ chi phí CCDC (theo tháng/năm)
- Ghi giảm CCDC (thanh lý, mất, hư hỏng)
- Báo cáo Sổ theo dõi CCDC
- Báo cáo Bảng phân bổ CCDC

**Out of Scope (Future):**
- Barcode/QR tracking
- Tích hợp với hệ thống kho vật tư
- Đánh giá lại CCDC (revaluation)
- CCDC cho thuê (rental)
- CCDC nhập khẩu (import duties)

## 2. Functional Requirements

### 2.1 Master Data Management

#### FR-001: CCDC Master Record
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | auto | Primary key |
| company_id | UUID | yes | FK → companies |
| code | String(50) | yes | Unique per company, format `[A-Z0-9-]{2,50}` |
| name | String(200) | yes | |
| category | Enum | yes | LABOR_TOOL, OFFICE_EQUIP, MEASURING, SAFETY, OTHER |
| purchase_date | Date | yes | |
| purchase_price | Decimal(18,2) | yes | Nguyên giá (VND) |
| useful_life_months | Integer | yes | Số kỳ phân bổ (1–36) |
| salvage_value | Decimal(18,2) | no | Giá trị còn lại cuối kỳ |
| status | Enum | auto | ACTIVE → INACTIVE → WRITTEN_OFF |
| assigned_to | UUID | no | FK → users (người phụ trách) |
| cost_center_id | UUID | no | FK → cost_centers |
| dimension_value_id | UUID | no | FK → dimension_values |
| expense_account_code | String(10) | yes | TK chi phí phân bổ (VD: 623, 627, 641) |
| prepaid_account_code | String(10) | no | TK 242 (nếu phân bổ nhiều kỳ) |
| description | String(500) | no | |
| audit_checksum | String(64) | auto | Chain checksum |
| created_by | UUID | no | |
| created_at | DateTime | auto | |
| updated_at | DateTime | auto | |

#### FR-002: CCDC Category
```python
class CCDCCategory(str, Enum):
    LABOR_TOOL = "Công cụ lao động"        # Dao, kéo, búa, tuýp...
    OFFICE_EQUIP = "Thiết bị văn phòng"     # Laptop, máy in, bàn ghế...
    MEASURING = "Thiết bị đo lường"          # Thước, cân, đồng hồ...
    SAFETY = "Thiết bị an toàn"              # Mũ bảo hộ, giày bảo hộ...
    OTHER = "Khác"
```

### 2.2 Lifecycle Operations

#### FR-003: Ghi tăng CCDC
- Tạo CCDC từ dữ liệu đầu vào
- Nếu giá trị nhỏ (≤ 1.000.000 VND): hạch toán thẳng vào chi phí (TK 623/627/641)
- Nếu giá trị lớn và phân bổ nhiều kỳ: ghi nhận vào TK 242, phân bổ dần

#### FR-004: Phân bổ chi phí CCDC
- Tính phân bổ hàng tháng: `giá_trị / số_kỳ_phân_bổ`
- Ngày bắt đầu phân bổ = ngày ghi tăng CCDC
- Tạo chứng từ phân bổ tự động mỗi tháng
- Ghi nhận: Nợ TK chi phí, Có TK 242

#### FR-005: Ghi giảm CCDC
- Thanh lý: CCDC hết giá trị hoặc không cần dùng
- Mất/hư hỏng: CCDC bị tổn thất
- Chuyển đổi: CCDC → TSCĐ (nếu nâng cấp)

#### FR-006: Sổ theo dõi CCDC
- Báo cáo chi tiết từng CCDC
- Theo dõi nguyên giá, giá trị còn lại, chi phí đã phân bổ

### 2.3 Integration Points

#### FR-007: Tích hợp với Brick Purchase
- Khi tạo purchase invoice có CCDC items → tự động ghi tăng CCDC
- Liên kết chứng từ mua hàng với CCDC

#### FR-008: Tích hợp với Brick Cost Centers
- CCDC gắn với cost_center_id để phân bổ chi phí theo TT

#### FR-009: Tích hợp với Brick Dimensions
- CCDC gắn với dimension_value_id để phân bổ theo dự án/bộ phận

#### FR-010: Tích hợp với Brick COA
- TK 1531: Công cụ, dụng cụ
- TK 242: Chi phí trả trước
- TK 623/627/641: Chi phí sản xuất kinh doanh

## 3. Non-Functional Requirements

### NFR-001: Performance
- Phân bổ CCDC cho 1000 items: < 5 giây
- Báo cáo Sổ theo dõi: < 3 giây

### NFR-002: Data Integrity
- Audit checksum chain (giống cost_centers brick)
- Tất cả thay đổi phải có audit trail

### NFR-003: RBAC
| Action | Roles |
|--------|-------|
| Create CCDC | ADMIN, ACCOUNTANT |
| Modify CCDC | ADMIN, ACCOUNTANT |
| Delete/Deactivate CCDC | CHIEF_ACCOUNTANT |
| Phân bổ CCDC | ADMIN, ACCOUNTANT |
| Thanh lý CCDC | CHIEF_ACCOUNTANT |
| Read CCDC | Any authenticated user |

### NFR-004: Compliance
- Tuân thủ TT99/2025/TT-BTC
- Tuân thủ TT133/2016/TT-BTC
- Lưu trữ 10 năm (Luật Kế toán 2015 Art. 11)

## 4. Data Model

### 4.1 ER Diagram (textual)
```
companies ──1:N── tools_equipment
cost_centers ──1:N── tools_equipment
dimension_values ──1:N── tools_equipment
users ──1:N── tools_equipment (assigned_to)
users ──1:N── tools_equipment (created_by)
tools_equipment ──1:N── tools_equipment_allocations
```

### 4.2 Tables
```sql
-- tools_equipment (sổ CCDC)
CREATE TABLE tools_equipment (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    purchase_date DATE NOT NULL,
    purchase_price NUMERIC(18,2) NOT NULL,
    useful_life_months INTEGER NOT NULL,
    salvage_value NUMERIC(18,2) DEFAULT 0,
    status TEXT DEFAULT 'ACTIVE',
    assigned_to TEXT,
    cost_center_id TEXT,
    dimension_value_id TEXT,
    expense_account_code TEXT NOT NULL,
    prepaid_account_code TEXT,
    description TEXT,
    audit_checksum TEXT DEFAULT '',
    created_by TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE(code, company_id)
);

-- tools_equipment_allocations (bảng phân bổ chi phí)
CREATE TABLE tools_equipment_allocations (
    id TEXT PRIMARY KEY,
    tool_equipment_id TEXT NOT NULL,
    period_year INTEGER NOT NULL,
    period_month INTEGER NOT NULL,
    allocated_amount NUMERIC(18,2) NOT NULL,
    expense_account_code TEXT NOT NULL,
    cost_center_id TEXT,
    dimension_value_id TEXT,
    voucher_id TEXT,
    status TEXT DEFAULT 'PENDING',
    created_at DATETIME,
    UNIQUE(tool_equipment_id, period_year, period_month)
);
```

## 5. Acceptance Criteria

### AC-001: Create CCDC
```gherkin
Given user is ACCOUNTANT
When user creates CCDC with valid data
Then CCDC is created with status ACTIVE
And audit_checksum is generated
And CCDC appears in Sổ theo dõi

Given CCDC has purchase_price = 800,000 VND
And useful_life_months = 1
When CCDC is created
Then full amount is expensed immediately (no TK242)

Given CCDC has purchase_price = 2,400,000 VND
And useful_life_months = 6
When CCDC is created
Then 400,000 VND is allocated monthly
And TK242 is debited with 2,400,000
```

### AC-002: Phân bổ CCDC
```gherkin
Given CCDC with purchase_price = 2,400,000 VND
And useful_life_months = 6
And allocation started on 2026-01-15
When monthly allocation runs for 2026-02
Then allocated_amount = 400,000 VND
And journal entry: Dr 623/627/641 400,000 / Cr 242 400,000
```

### AC-003: Ghi giảm CCDC
```gherkin
Given CCDC with remaining_value = 800,000 VND
When user writes off CCDC
Then status changes to WRITTEN_OFF
And remaining value is expensed
And audit trail is recorded
```

## 6. Open Questions

| # | Question | Answer |
|---|----------|--------|
| 1 | CCDC có cần quy trình DOD 2-actor như payment_terms không? | **No** — CCDC lifecycle đơn giản hơn TSCĐ |
| 2 | Có cần phân bổ theo tỷ lệ (%). không chia đều? | **Yes** — cho phép phân bổ theo tỷ lệ cho nhiều đối tượng |
| 3 | CCDC có cần barcode/QR không? | **No** — MVP không cần |
| 4 | CCDC nhập khẩu có cần tính thuế nhập khẩu không? | **No** — out of scope MVP |
| 5 | CCDC cho thuê có cần module riêng không? | **Yes** — future scope (TK 1533) |

## 7. Sign-off

| Role | Name | Date |
|------|------|------|
| BA Lead | — | — |
| Chief Accountant | — | — |
| Tech Lead | — | — |
