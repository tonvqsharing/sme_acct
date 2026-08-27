# Workflows — Tools & Equipment (CCDC) Module

## WF-001: CCDC Registration Workflow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Start   │───►│  Create │───►│  Assign │───►│  Set    │───►│  End    │
│          │    │  Record │    │  Dept   │    │  Alloc  │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Steps:**
1. **Create Record:** ACCOUNTANT enters CCDC details
2. **Assign Department:** Link to cost center / dimension
3. **Set Allocation:** Configure allocation parameters (period, expense account)

---

## WF-002: Monthly Allocation Workflow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Start   │───►│  Select │───►│  Calc   │───►│  Review │───►│  Post   │
│  Month   │    │  Period │    │  Allocations│ │  & Edit │    │  Entry  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Steps:**
1. **Select Period:** ACCOUNTANT chooses month/year
2. **Calculate:** System computes allocations for all ACTIVE CCDC
3. **Review:** ACCOUNTANT reviews allocation table
4. **Post:** System creates journal entries

---

## WF-003: CCDC Write-Off Workflow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Start   │───►│  Select │───►│  Choose │───►│  Create │───►│  End    │
│  (CHIEF) │    │  CCDC   │    │  Reason │    │  Entry  │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Steps:**
1. **Select CCDC:** CHIEF_ACCOUNTANT picks CCDC to write off
2. **Choose Reason:** Select THANH_LY / MAT / HU_HONG
3. **Create Entry:** System creates write-off journal entry

---

## WF-004: CCDC Transfer Workflow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Start   │───►│  Select │───►│  Choose │───►│  Update │
│          │    │  CCDC   │    │  New Dept│   │  Record │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Steps:**
1. **Select CCDC:** ACCOUNTANT picks CCDC to transfer
2. **Choose New Dept:** Select new cost_center / dimension_value
3. **Update Record:** System updates assignment (no journal entry)

---

## Workflow State Diagram

```
                    ┌─────────────────┐
                    │   (No CCDC)     │
                    └────────┬────────┘
                             │ Create
                             ▼
                    ┌─────────────────┐
           ┌───────│     ACTIVE      │◄──────────┐
           │       │ (Phân bổ)       │           │
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
