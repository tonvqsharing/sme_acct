# Templates — Tools & Equipment (CCDC) Module

## Template 1: CCDC Creation Form

```json
{
  "company_id": "uuid",
  "code": "LPT-001",
  "name": "Laptop Dell Inspiron 15",
  "category": "OFFICE_EQUIP",
  "purchase_date": "2026-08-15",
  "purchase_price": 15000000,
  "useful_life_months": 12,
  "salvage_value": 0,
  "expense_account_code": "642",
  "prepaid_account_code": "242",
  "assigned_to": "uuid | null",
  "cost_center_id": "uuid | null",
  "dimension_value_id": "uuid | null",
  "description": "Laptop Dell Inspiron 15, Core i7, 16GB RAM"
}
```

## Template 2: CCDC Response

```json
{
  "data": {
    "id": "uuid",
    "company_id": "uuid",
    "code": "LPT-001",
    "name": "Laptop Dell Inspiron 15",
    "category": "OFFICE_EQUIP",
    "category_label": "Thiết bị văn phòng",
    "purchase_date": "2026-08-15",
    "purchase_price": 15000000,
    "useful_life_months": 12,
    "salvage_value": 0,
    "monthly_allocation": 1250000,
    "remaining_value": 13750000,
    "allocated_months": 1,
    "remaining_months": 11,
    "status": "ACTIVE",
    "assigned_to": "uuid | null",
    "assigned_to_name": "Nguyen Van A",
    "cost_center_id": "uuid | null",
    "cost_center_code": "KTPP",
    "dimension_value_id": "uuid | null",
    "dimension_value_code": "PROJ-01",
    "expense_account_code": "642",
    "prepaid_account_code": "242",
    "description": "Laptop Dell Inspiron 15, Core i7, 16GB RAM",
    "audit_checksum": "sha256_hex_string",
    "created_by": "uuid",
    "created_at": "2026-08-15T10:30:00Z",
    "updated_at": "2026-08-15T10:30:00Z"
  }
}
```

## Template 3: Allocation Request

```json
{
  "period_year": 2026,
  "period_month": 8,
  "tool_equipment_ids": ["uuid1", "uuid2"],
  "allocation_date": "2026-08-31"
}
```

## Template 4: Allocation Response

```json
{
  "data": {
    "period_year": 2026,
    "period_month": 8,
    "allocations": [
      {
        "id": "uuid",
        "tool_equipment_id": "uuid",
        "tool_code": "LPT-001",
        "tool_name": "Laptop Dell Inspiron 15",
        "remaining_value": 13750000,
        "allocated_amount": 1250000,
        "expense_account_code": "642",
        "cost_center_id": "uuid | null",
        "dimension_value_id": "uuid | null",
        "status": "POSTED",
        "voucher_id": "uuid"
      }
    ],
    "total_allocated": 1650000,
    "journal_entries": [
      {
        "debit_account": "642",
        "credit_account": "242",
        "amount": 1250000,
        "description": "Phân bổ CCDC LPT-001 tháng 8/2026"
      }
    ]
  }
}
```

## Template 5: Write-Off Request

```json
{
  "tool_equipment_id": "uuid",
  "reason": "HU_HONG",
  "write_off_date": "2026-08-20",
  "notes": "Máy photocopy bị hỏng motor, không thể sửa chữa"
}
```

## Template 6: Write-Off Response

```json
{
  "data": {
    "id": "uuid",
    "tool_code": "MK-001",
    "tool_name": "Máy photocopy Ricoh",
    "original_price": 3600000,
    "remaining_value": 1200000,
    "reason": "HU_HONG",
    "status": "WRITTEN_OFF",
    "journal_entry": {
      "debit_account": "642",
      "credit_account": "1531",
      "amount": 1200000,
      "description": "Thanh lý CCDC MK-001 - Hư hỏng"
    },
    "audit_checksum": "sha256_hex_string"
  }
}
```

## Template 7: Sổ theo dõi CCDC (Ledger Report)

```json
{
  "report_name": "Sổ theo dõi CCDC",
  "period": "2026",
  "data": [
    {
      "code": "LPT-001",
      "name": "Laptop Dell Inspiron 15",
      "category": "Thiết bị văn phòng",
      "purchase_date": "2026-08-15",
      "opening_balance": 0,
      "increases": 15000000,
      "decreases": 0,
      "closing_balance": 15000000,
      "allocated_to_date": 1250000,
      "remaining_value": 13750000,
      "status": "Active"
    }
  ],
  "summary": {
    "total_original": 18600000,
    "total_allocated": 3650000,
    "total_remaining": 14950000,
    "count_active": 2,
    "count_written_off": 0
  }
}
```

## Template 8: Bảng phân bổ CCDC (Allocation Schedule)

```json
{
  "report_name": "Bảng phân bổ CCDC năm 2026",
  "year": 2026,
  "data": [
    {
      "code": "LPT-001",
      "name": "Laptop Dell Inspiron 15",
      "original_price": 15000000,
      "useful_life_months": 12,
      "monthly_amount": 1250000,
      "allocations": {
        "1": 1250000,
        "2": 1250000,
        "3": 1250000,
        "4": 1250000,
        "5": 1250000,
        "6": 1250000,
        "7": 1250000,
        "8": 1250000,
        "9": 0,
        "10": 0,
        "11": 0,
        "12": 0
      },
      "total_allocated": 10000000,
      "remaining": 5000000
    }
  ]
}
```
