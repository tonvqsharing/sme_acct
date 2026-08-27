# Processes — Tools & Equipment (CCDC) Module

## Process 1: CCDC Procurement & Registration

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  Purchase    │────►│  Create CCDC │────►│  Assign to   │────►│  Start      │
│  Request     │     │  Record      │     │  Department  │     │  Allocation │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  If value    │
                    │  ≤ 1M VND:  │
                    │  Expense     │
                    │  immediately │
                    └──────────────┘
```

**Steps:**
1. User creates purchase invoice for CCDC item
2. System creates CCDC record (or user creates manually)
3. User assigns CCDC to cost center / dimension
4. System determines allocation method based on value and useful life
5. System starts allocation process

---

## Process 2: Monthly Allocation

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Select      │────►│  Calculate   │────►│  Review      │────►│  Post        │
│  Period      │     │  Allocations │     │  Allocations │     │  Journal     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  For each    │
                     │  ACTIVE CCDC │
                     │  with rem.   │
                     │  allocations │
                     └──────────────┘
```

**Steps:**
1. User selects month/year for allocation
2. System queries all ACTIVE CCDC with remaining allocations
3. For each CCDC:
   a. Calculate `amount = (purchase_price - salvage_value) / useful_life_months`
   b. Check if allocation period is within useful life
   c. Determine allocation objects (cost center, dimension)
4. System presents allocation table for review
5. User confirms
6. System creates allocation records
7. System posts journal entries:
   - Dr 623/627/641/642 (expense)
   - Cr 242 (prepaid)
8. System updates remaining values

---

## Process 3: CCDC Write-Off

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Select      │────►│  Calculate   │────►│  Create      │────►│  Update      │
│  CCDC        │     │  Remaining   │     │  Journal     │     │  Status      │
│              │     │  Value       │     │  Entry       │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Reason:     │
                     │  - Thanh lý  │
                     │  - Mất       │
                     │  - Hư hỏng   │
                     └──────────────┘
```

**Steps:**
1. CHIEF_ACCOUNTANT selects CCDC to write off
2. System calculates remaining value
3. User selects write-off reason
4. System creates journal entry based on reason:
   - **Thanh lý (disposal):** If sold, record cash received; record gain/loss
   - **Mất (lost):** Record full remaining value as expense
   - **Hư hỏng (damaged):** Record remaining value as expense
5. System sets status = WRITTEN_OFF
6. System stops all future allocations

---

## Process 4: CCDC Transfer Between Departments

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Select      │────►│  Choose New  │────►│  Update      │
│  CCDC        │     │  Department  │     │  Assignment  │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Steps:**
1. User selects ACTIVE CCDC
2. User selects new cost_center and/or dimension_value
3. System updates CCDC assignment
4. Future allocations will use new department
5. No journal entry created (only assignment changes)
