# Data Flows — Tools & Equipment (CCDC) Module

## DF-001: CCDC Creation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User Input  │────►│  Validation  │────►│  Domain      │────►│  Storage     │
│  (Web/API)   │     │  Layer       │     │  Entity      │     │  (SQLAlchemy)│
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  COA Check   │
                     │  (expense    │
                     │  account)    │
                     └──────────────┘
```

**Data transformation:**
1. Request JSON → ToolEquipment domain entity
2. Domain entity → SQLAlchemy model
3. Audit checksum computed and stored
4. Response: domain entity → JSON

---

## DF-002: Monthly Allocation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Period      │────►│  Query ACTIVE│────►│  Calculate   │────►│  Create      │
│  Selection   │     │  CCDC        │     │  Amounts     │     │  Allocations │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                    │
                                                    ▼
                                             ┌──────────────┐
                                             │  Create      │
                                             │  Journal     │
                                             │  Entries     │
                                             └──────────────┘
                                                    │
                                                    ▼
                                             ┌──────────────┐
                                             │  Update      │
                                             │  Remaining   │
                                             │  Values      │
                                             └──────────────┘
```

**Data transformation:**
1. Period (year, month) → Query filter
2. ACTIVE CCDC records → Calculation input
3. Calculation result → ToolEquipmentAllocation entities
4. Allocation entities → Journal entries (via voucher brick)

---

## DF-003: Write-Off Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Select      │────►│  Calculate   │────►│  Create      │────►│  Update      │
│  CCDC +      │     │  Remaining   │     │  Journal     │     │  Status      │
│  Reason      │     │  Value       │     │  Entry       │     │  = WRITTEN   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**Data transformation:**
1. CCDC ID + reason → Remaining value calculation
2. Remaining value → Journal entry amount
3. Journal entry → Voucher creation
4. Status update → Audit trail

---

## DF-004: Report Generation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Report      │────►│  Query       │────►│  Aggregate   │────►│  Format      │
│  Request     │     │  Data        │     │  Data        │     │  Output      │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**Report types:**
1. **Sổ theo dõi CCDC:** Group by CCDC, show opening/increases/decreases/closing
2. **Bảng phân bổ CCDC:** Group by CCDC, show monthly allocation schedule
3. **Bảng cân đối phát sinh:** Summary of all CCDC movements

---

## Integration Data Flows

### With Purchases Brick
```
Purchase Invoice (CCDC items)
    │
    ├──► Create CCDC record
    ├──► Link to purchase voucher
    └──► Set allocation parameters
```

### With Cost Centers Brick
```
CCDC Record
    │
    ├──► cost_center_id → Cost Center master
    └──► Allocation → Cost Center expense
```

### With Dimensions Brick
```
CCDC Record
    │
    ├──► dimension_value_id → Dimension Value master
    └──► Allocation → Dimension expense
```

### With COA Brick
```
CCDC Transactions
    │
    ├──► TK 1531 (CCDC asset)
    ├──► TK 242 (prepaid expense)
    └──► TK 623/627/641/642 (expense)
```
