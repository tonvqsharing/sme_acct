# Data Flow Diagrams: System Settings Module

---

## DFD-01: Config Read (Primary Path)

```
User Request
  GET /api/v1/companies/{id}/settings/config/flags
  [JWT Auth → RBAC Check: ACCOUNTANT|ADMIN]
  ↓
API Handler
  → SystemSettingsService.get_flags(company_id)
    → SystemSettingsRepository.get_company_config(company_id)
      → SQL: SELECT * FROM company_configs WHERE company_id = ?
    ← CompanyConfig (or SystemSettingsError if not found)
  → FlagMapper: transforms DB row → JSON response
    (flag_type included; LAW flags marked non-editable)
  ↓
HTTP 200
{
  "company_id": "uuid",
  "config_version": 3,
  "flags": [ {name, value, type, editable, category, legal_basis}, ... ]
}
```

**Data mapping:**
- DB `company_configs.vat_settlement_cycle` (VARCHAR) → JSON `"MONTHLY"` (enum display)
- DB `accounting_regime` (VARCHAR) → JSON with description: `{"id": "tt200", "label": "Thông tư 200/2014/TT-BTC"}`
- LAW flags: `editable=false`; CONFIG flags: `editable=true`, `requires_2nd_approval` if applicable

---

## DFD-02: Config Update Flow (CONFIG Flag)

```
A (Admin)
  PATCH /api/v1/companies/{id}/settings/flags/{flag_name}
  Headers: X-Config-Version: 3
  Body: { "value": "quarterly" }
  ↓
API Handler
  → Auth: ADMIN role ✓
  → SystemSettingsService.update_flag(company_id, flag_name, value, actor, v=3)
    → Repository.get_company_config(company_id) + check version = 3
    → FlagDefinition.lookup(flag_name) → type = CONFIG
      found: vat_settlement_cycle, requires_2nd_approval = True
    → If requires_2nd_approval AND not pre-approved:
        → Create approval request; notify CA (async email)
        → Return 202 Accepted with approval_id
        [CA reviews → approves via /approvals/{id}/approve]
        → ApprovalService.approve(approval_id, ca_actor)
          → FlagApproval state = APPROVED
          → Returns to caller
    → [Service] EMIT config_changes INTO config_changes (before, after, actor, flag_type, version)
    → [Service] EMIT audit_log INTO audit_log (before, after, actor, action=CONFIG_UPDATED)
    → [Repository] UPDATE company_configs SET vat_settlement_cycle='quarterly', config_version=4
      WHERE company_id=id AND config_version=3
    → IF 0 rows affected → 409 CONFIG_VERSION_CONFLICT
    → Cache.invalidate("config:{company_id}")
  ↓
HTTP 200
{ "company_id": "uuid", "config_version": 4, "flag_name": "vat_settlement_cycle", "value": "quarterly" }
```

**Data mapping:**
- `config_version` in DB: INT, incremented atomically in UPDATE WHERE clause
- `before_value`: JSONB serialization of CompanyConfig keyword snapshot for changed flag
- `after_value`: JSONB of new value
- `change_reason`: captured from PATCH body or approval request

---

## DFD-03: Period Lock Enforcement (at Invoice Creation)

```
SA creates invoice with issue_date = 2026-03-15
  → InvoiceService.create(invoice)
    → SystemSettingsService.is_period_locked(company_id, issue_date)
      → PeriodLockRepository.is_locked(company_id, "2026-03")
        → SQL: SELECT 1 FROM period_locks
                WHERE company_id=? AND fiscal_year=2026
                  AND accounting_period = MONTH(issue_date)
                  AND (lock_type='PERIOD' OR lock_type='FYEAR_CLOSED')
      → EXISTS → return True
    → IF locked → raise AccountingPeriodLockedError
      → API returns 403 PERIOD_LOCKED
    → IF not locked → continue CREATE
      → SQLAlchemyInvoiceRepository.create(invoice)  [existing path]
      → InvoiceService.emit_audit_event(invoice)
  ↓
HTTP 201 Created (if unlocked) or 403 (if locked)
```

**Data mapping:**
- `invoice.issue_date` (DATE) → mapped to `fiscal_year` + `accounting_period` using CompanyConfig.fiscal_year_start_*
- fiscal year derivation logic:
  ```
  if period_start_month=4, period_start_day=1:
    fiscal_year = issue_date.year if issue_date.month >= 4 else issue_date.year - 1
    accounting_period = (issue_date.month - 4 + 12) % 12 + 1
  ```

---

## DFD-04: E-Invoice Number Sequence (Atomic Advance)

```
SA requests invoice issuance for series "AA/2026"
  ├─ Thread A                              ├─ Thread B (concurrent)
  → SystemSettingsService
      .advance_e_invoice_sequence(...)
      → SQL (transaction):
          SELECT next_sequence
          FROM e_invoice_series
          WHERE company_id=? AND prefix='AA/2026'
            AND active=true
          FOR UPDATE        ← row lock
      → old_seq = 42
      → UPDATE e_invoice_series
          SET next_sequence = 43
          WHERE id = series_id
      → INSERT INTO invoice_series_log (series_id, seq_used, actor)
          VALUES (series_id, 42, sa_user_id)
      COMMIT
  ← Returns 42                           ← Would block on SELECT FOR UPDATE
 arrives first                          → Returns 43
```

**Data mapping:**
- `e_invoice_series.next_sequence` (INT, NOT NULL, ≥1)
- `invoice_series_log` (proposed log table): id, series_id, seq_used, actor, created_at
- Lock granularity: row-level on e_invoice_series; no table lock required

---

## DFD-05: Audit Log Append (WORM)

```
System event (e.g., CONFIG_CHANGED)
  → AuditLogService.emit(company_id, actor, action, entity_type, entity_id, before, after, ip, ua)
    → [Non-blocking] Write to async queue
    → [DB Writer - dedicated role with INSERT-only]
        INSERT INTO audit_log (
            company_id, actor_user_id, action, entity_type, entity_id,
            before_value, after_value, ip_address, user_agent, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, now())
    → INSERT succeeds (REVOKE DELETE prevents removal)
  → [Background Worker - hourly]
      ├─ Archive rows older than 2 years to cold storage (WORM)
      └─ Mark archived in hot DB (still queryable, large blobs moved)

  [DB constraint]
  REVOKE DELETE, UPDATE ON audit_log FROM app_role;
  GRANT INSERT, SELECT ON audit_log TO app_role;
```

**Data mapping:**
- `before_value`, `after_value`: JSONB with full flag snapshot for CONFIG changes; minimal payload for high-volume events
- `created_at`: set at DB level via `now()` NOT application; guarantees WORM

---

## DFD-06: Company Setup (Init Flow)

```
[External] GDT issues MST
  ↓
[CA] POST /api/v1/companies/{new_id}/settings/init
  Body: {
    company_name, mst, address, legal_rep, company_type,
    accounting_regime: "tt200",
    fiscal_year_start: { month: 1, day: 1 },
    vat_method: "deduction",
    vat_cycle: "monthly",
    e_invoice_mode: "software_cert"
  }
  ↓
API Handler
  → SystemSettingsService.init_company(company_id, company_info)
    → Validate: MST format (TaxId value object)
    → Validate: company_type in enum (ENTERPRISE, COMPANY, BRANCH, HQ)
    → Validate: accounting_regime in enum
    → Validate: fiscal_year_start {1,1} or valid Apr-1
    → Validate: vat_method matches declared tax registration (TODO: reconcile with external source)
    → Build CompanyConfig with all mandatory fields; config_version=1
    → Repository.create_company_config(config)
      → INSERT INTO company_configs (...) VALUES (...)
    → Repository.append_audit_log(company_id, actor, 'CONFIG_CREATED', ..., before=null, after=config_json)
  ↓
HTTP 201 Created
{ company_id, config_version: 1, legal_review_required: true }
```

**Data mapping:**
- `company_info.company_type` → maps to DB `company_configs.company_type` + FK to future `companies` table
- `accounting_regime` → maps to COA template; derived `coa_version` should match

---

## DFD-07: Legal Review Stamp Flow

```
[System] Periodic task: identifies configs needing legal review
  OR [CA] triggers: POST /config/legal-review
  ↓
API Handler
  → SystemSettingsService.stamp_legal_review(company_id, ca_actor)
    → Check: ca_actor role = CHIEF_ACCOUNTANT
    → Build review_summary JSONB:
        {
          "config_version": 5,
          "flags_since_last_review": [ ... ],
          "changes": [ flag_name, before, after, actor, timestamp ],
          "regime_matches_registration": true,
          "retention_adequate": true,
          "vat_method_declared_match": true
        }
    → Repository.update(
        legal_reviewed_at=now(),
        legal_reviewed_by=ca_actor.id,
        ...
      )
    → Repository.append_audit_log(action=LEGAL_REVIEW_STAMPED,
        after_value=review_summary)
    → Repository.append_audit_log(action=AUDIT_LOG_EXPORT, ...)
  ↓
HTTP 200
{ company_id, legal_reviewed_at, legal_reviewed_by, config_version }
```

**Data mapping:**
- `review_summary` stored in audit_log only (not in company_configs — audit trail is primary record); compact JSONB
- Reviewed flags snapshot extracted from config_changes WHERE config_version > last_review_version

---

## Data Dictionary (Key Tables)

| Table | Primary Key | Key Columns | Growth Rate | Retention |
|-------|------------|-------------|-------------|-----------|
| company_configs | id | company_id, config_version, accounting_regime, vat_rates | ~1 row/company | Immutable once set; updates rare |
| audit_log | id | company_id, action, entity_type, created_at | ~100-1000 rows/day per active company | ≥10 years hot; archive after 2y |
| period_locks | id | company_id, fiscal_year, accounting_period, lock_type | ~12 (periods) + 1 (fyear) per year per company | Retention = company lifetime |
| e_invoice_series | id | company_id, prefix, next_sequence | ~2-15 per company | Retention = company lifetime |
| config_changes | id | company_id, config_version, flag_name, actor | ~few per quarter per company | ≥10 years |