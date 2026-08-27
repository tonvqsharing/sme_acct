# Specifications — Tools & Equipment (CCDC) Module

**Last updated:** 2026-08-27  
**Status:** Draft (specs only, not yet implemented)  
**Regulatory basis:** TT99/2025/TT-BTC (effective 01/01/2026), TT133/2016/TT-BTC

---

## 1. Overview

Tools & Equipment (CCDC — Công cụ, Dụng cụ) brick manages assets that don't meet fixed asset (TSCĐ) recognition criteria per Vietnamese accounting standards.

**Key distinction from TSCĐ:**
- TSCĐ: value ≥ VND 5,000,000 AND useful life ≥ 12 months (TK 211)
- CCDC: value < VND 5,000,000 OR useful life < 12 months (TK 153)

---

## 2. Account Structure (TT99/2025)

```
TK 153 — Công cụ, dụng cụ (Hàng tồn kho)
├── 1531 — Công cụ, dụng cụ
├── 1532 — Bao bì luân chuyển
├── 1533 — Đồ dùng cho thuê
└── 1534 — Thiết bị, phụ tùng thay thế

TK 242 — Chi phí trả trước (CCDC phân bổ nhiều kỳ)

TK chi phí phân bổ:
├── 623 — Chi phí nhân công
├── 627 — Chi phí khấu hao TSCĐ (dùng cho CCDC nếu có)
├── 641 — Chi phí bán hàng
└── 642 — Chi phí quản lý doanh nghiệp
```

---

## 3. Entity Model

### 3.1 ToolEquipment (CCDC)

```python
@dataclass
class ToolEquipment:
    company_id: UUID
    code: str                    # [A-Z0-9-]{2,50}, unique per company
    name: str
    category: CCDCCategory
    purchase_date: date
    purchase_price: Decimal      # Nguyên giá (VND)
    useful_life_months: int      # 1–36
    salvage_value: Decimal = Decimal("0")
    expense_account_code: str    # TK chi phí (623/627/641/642)
    prepaid_account_code: str | None = None  # TK 242 (nếu phân bổ > 1 kỳ)
    assigned_to: UUID | None = None
    cost_center_id: UUID | None = None
    dimension_value_id: UUID | None = None
    description: str | None = None
    status: ToolEquipmentStatus = ToolEquipmentStatus.ACTIVE
    id: UUID = field(default_factory=uuid4)
    created_by: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    audit_checksum: str = ""
```

### 3.2 Enums

```python
class CCDCCategory(str, Enum):
    LABOR_TOOL = "Công cụ lao động"
    OFFICE_EQUIP = "Thiết bị văn phòng"
    MEASURING = "Thiết bị đo lường"
    SAFETY = "Thiết bị an toàn"
    OTHER = "Khác"

class ToolEquipmentStatus(str, Enum):
    ACTIVE = "Active"           # Đang sử dụng
    INACTIVE = "Inactive"       # Ngừng phân bổ tạm thời
    WRITTEN_OFF = "WrittenOff"  # Đã thanh lý
```

### 3.3 ToolEquipmentAllocation (Bảng phân bổ)

```python
@dataclass
class ToolEquipmentAllocation:
    tool_equipment_id: UUID
    period_year: int
    period_month: int
    allocated_amount: Decimal
    expense_account_code: str
    cost_center_id: UUID | None = None
    dimension_value_id: UUID | None = None
    voucher_id: UUID | None = None
    status: AllocationStatus = AllocationStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
```

---

## 4. Allocation Rules (Điều 26 TT200/2014, áp dụng qua TT99/2025)

### 4.1 Method 1: Small value, single period
- CCDC có giá trị nhỏ, sử dụng trong 1 kỳ kế toán
- Hạch toán toàn bộ vào chi phí ngay khi xuất dùng
- **Không cần TK 242**

### 4.2 Method 2: Large value, multiple periods
- CCDC có giá trị lớn, sử dụng nhiều kỳ kế toán
- Ghi nhận vào TK 242, phân bổ dần vào chi phí
- Thời gian phân bổ: tối đa 3 năm (theo quy định thuế)
- Phân bổ đều hàng tháng: `amount_per_month = (purchase_price - salvage_value) / useful_life_months`

### 4.3 Allocation Start Date
- Ngày bắt đầu phân bổ = ngày ghi tăng CCDC
- Tháng đầu tiên: phân bổ theo ngày thực tế (nếu không tròn tháng)

### 4.4 Allocation Object
- Phân bổ đến cost_center và/hoặc dimension_value
- Cho phép nhiều đối tượng phân bổ theo tỷ lệ (%)

---

## 5. Lifecycle State Machine

```
                    ┌─────────────────┐
                    │   (Tạo mới)     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
           ┌───────│     ACTIVE      │◄──────────┐
           │       │ (Đang sử dụng)  │           │
           │       └────────┬────────┘           │
           │                │                     │
           │   deactivate   │    reactivate       │
           │                ▼                     │
           │       ┌─────────────────┐           │
           │       │    INACTIVE     │───────────┘
           │       │ (Ngừng phân bổ)  │
           │       └────────┬────────┘
           │                │
           │   write_off    │
           │                ▼
           │       ┌─────────────────┐
           └──────►│  WRITTEN_OFF    │
                   │ (Đã thanh lý)   │
                   └─────────────────┘
```

---

## 6. Journal Entries

### 6.1 Mua CCDC nhập kho (giá trị nhỏ, 1 kỳ)
```
Nợ TK 1531 — Công cụ, dụng cụ     XXX
Nợ TK 1333 — GTGT được khấu trừ    XXX (nếu có HĐGTGT)
   Có TK 1111 — Tiền mặt           XXX
   Hoặc  Có TK 3311 — Phải trả người bán  XXX
```

### 6.2 Mua CCDC nhập kho (giá trị lớn, phân bổ nhiều kỳ)
```
Nợ TK 1531 — Công cụ, dụng cụ     XXX
Nợ TK 1333 — GTGT được khấu trừ    XXX
   Có TK 1111 — Tiền mặt           XXX
   Hoặc  Có TK 3311 — Phải trả người bán  XXX
```

### 6.3 Xuất CCDC sử dụng (1 kỳ)
```
Nợ TK 623/627/641/642 — Chi phí    XXX
   Có TK 1531 — Công cụ, dụng cụ  XXX
```

### 6.4 Xuất CCDC sử dụng (nhiều kỳ — ghi nhận vào TK 242)
```
Nợ TK 242 — Chi phí trả trước      XXX
   Có TK 1531 — Công cụ, dụng cụ  XXX
```

### 6.5 Phân bổ chi phí CCDC hàng tháng
```
Nợ TK 623/627/641/642 — Chi phí    XXX
   Có TK 242 — Chi phí trả trước   XXX
```

### 6.6 Thanh lý CCDC (còn giá trị)
```
Nợ TK 1111 — Tiền mặt              XXX (nếu bán)
Nợ TK 623/627/641/642 — Chi phí    XXX (lỗ)
Nợ TK 214 — Hao mòn TSCĐ           XXX (nếu có hao mòn)
   Có TK 1531 — Công cụ, dụng cụ  XXX (nguyên giá)
   Có TK 623/627/641/642 — Chi phí XXX (lãi)
```

### 6.7 CCDC mất/hư hỏng
```
Nợ TK 623/627/641/642 — Chi phí    XXX (giá trị còn lại)
Nợ TK 214 — Hao mòn TSCĐ           XXX
   Có TK 1531 — Công cụ, dụng cụ  XXX
```

---

## 7. RBAC Matrix

| Action | ADMIN | ACCOUNTANT | CHIEF_ACCOUNTANT | AUDITOR |
|--------|-------|------------|------------------|---------|
| Create CCDC | ✅ | ✅ | ✅ | ❌ |
| Modify CCDC | ✅ | ✅ | ✅ | ❌ |
| Deactivate CCDC | ❌ | ❌ | ✅ | ❌ |
| Reactivate CCDC | ❌ | ❌ | ✅ | ❌ |
| Write-off CCDC | ❌ | ❌ | ✅ | ❌ |
| Run allocation | ✅ | ✅ | ✅ | ❌ |
| Read CCDC | ✅ | ✅ | ✅ | ✅ |
| Export reports | ✅ | ✅ | ✅ | ✅ |

---

## 8. API Endpoints

### 8.1 CCDC Master
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/tools-equipment` | Create CCDC | ADMIN, ACCOUNTANT |
| GET | `/api/v1/tools-equipment` | List CCDC (filterable) | Any |
| GET | `/api/v1/tools-equipment/{id}` | Get CCDC detail | Any |
| PATCH | `/api/v1/tools-equipment/{id}` | Modify CCDC | ADMIN, ACCOUNTANT |
| POST | `/api/v1/tools-equipment/{id}/deactivate` | Deactivate | CHIEF_ACCOUNTANT |
| POST | `/api/v1/tools-equipment/{id}/reactivate` | Reactivate | CHIEF_ACCOUNTANT |
| POST | `/api/v1/tools-equipment/{id}/write-off` | Write off | CHIEF_ACCOUNTANT |

### 8.2 Allocation
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/tools-equipment/allocate` | Run monthly allocation | ADMIN, ACCOUNTANT |
| GET | `/api/v1/tools-equipment/{id}/allocations` | List allocations for CCDC | Any |
| GET | `/api/v1/tools-equipment/allocations/report` | Allocation report | Any |

### 8.3 Reports
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/tools-equipment/ledger` | Sổ theo dõi CCDC | Any |
| GET | `/api/v1/tools-equipment/allocation-schedule` | Bảng phân bổ CCDC | Any |

---

## 9. Validation Rules

| Rule | Description |
|------|-------------|
| VR-001 | Code must match `^[A-Z0-9-]{2,50}$` |
| VR-002 | purchase_price > 0 |
| VR-003 | useful_life_months between 1 and 36 |
| VR-004 | salvage_value < purchase_price |
| VR-005 | expense_account_code must be valid COA account (623/627/641/642) |
| VR-006 | If useful_life_months > 1, prepaid_account_code must be 242 |
| VR-007 | Cannot modify code after creation |
| VR-008 | Cannot deactivate CCDC that has pending allocations |
| VR-009 | Write-off requires all allocations to be completed |
| VR-010 | Category must be valid CCDCCategory enum |

---

## 10. Report Templates

### 10.1 Sổ theo dõi CCDC (Tool Equipment Ledger)
| Stt | Mã | Tên CCDC | Loại | Ngày mua | Nguyên giá | Số kỳ PB | Đã PB | Còn lại | Trạng thái |
|-----|-----|---------|------|----------|-----------|---------|-------|---------|-----------|

### 10.2 Bảng phân bổ CCDC (Allocation Schedule)
| Stt | Mã | Tên CCDC | Nguyên giá | Số kỳ PB | Tháng 1 | Tháng 2 | ... | Tháng 12 | Tổng |
|-----|-----|---------|-----------|---------|---------|---------|-----|---------|------|

---

## 11. Dependencies

| Brick | Dependency | Type |
|-------|-----------|------|
| cost_centers | cost_center_id FK | Optional |
| dimensions | dimension_value_id FK | Optional |
| coa | expense_account_code, prepaid_account_code FK | Required |
| purchases | Source document for CCDC creation | Optional |
| fiscal_year_period | Period validation for allocations | Required |
| audit_log | Checksum chain | Required |

---

## 12. Migration Notes

- New tables: `tools_equipment`, `tools_equipment_allocations`
- Add to `alembic/env.py` `target_metadata`
- Wire in `app.py` composition root
- No changes to existing tables
