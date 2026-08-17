# Workflows: System Settings Module

---

## WF-01: Company Initialization Workflow

```
States: (pre-init) → INFO_ENTERED → LEGAL_VALIDATED → DEFAULTS_APPLIED → REVIEWED → ACTIVE

  [pre-init]
    └── CA inputs company legal info (name, MST, address, company type)
          ↓ [validates] MST format, company type enum
    [INFO_ENTERED]
    └── CA selects accounting regime (TT200/TT99/TT58/TT133)
          ↓ [validates] regime allows company type (SME vs enterprise rules)
    └── CA selects chart of accounts type (derived from regime)
          ↓ [validates] COA version matches regime
    [LEGAL_VALIDATED]
    └── System derives fiscal year boundaries from fiscal_year_start_*
    └── System applies default invoice series (1 default series, prefix=YEAR)
    └── System applies default VAT rate table {0, 5, 10}
    └── System applies default retention (10 years)
    [DEFAULTS_APPLIED]
    └── CA overrides optional configs: currency, cost_center_required, print template
    [REVIEWED]
    └── CA stamps legal review (LEGAL_REVIEW_STAMPED event)
    └── System sets PRODUCTION_READY flag
    [ACTIVE]
      └── InvoiceService, VoucherService can use this company_id
      └── SAFE to enter transactions
```

**Transition guards:**
- Cannot reach LEGAL_VALIDATED with invalid MST (L-01 enforced in domain)
- Cannot reach ACTIVE without legal_reviewed_at stamp (OBJ-02)

**Versioning:** config_version = 1 on ACTIVATION; increments on each subsequent CONFIG change.

---

## WF-02: Config Change Request Workflow

```
States: PENDING → AWAITING_APPROVAL (if required) → APPROVED → APPLIED → AUDITED

  User (any ACTIVE user)
    └── Submits PATCH flag_name=value, X-Config-Version
          ↓ [validates]
          ├─ Role = ADMIN? → NO → REJECTED
          ├─ Flag type = LAW? → YES → REJECTED (FLAG_LOCKED)
          ├─ Requires 2nd approval? → NO → APPROVED
          └─ Requires 2nd approval? → YES → AWAITING_APPROVAL
                [CA notified async]
                    ↓
                  CA reviews
                    ├─ APPROVE → APPROVED
                    └─ REJECT → REJECTED (audit log records rejection + reason)
    [APPROVED]
      └── BEGIN atomic transaction
            ├─ CONFIG_CHANGED written to config_changes (before JSON, after JSON, version)
            ├─ AUDIT event written to audit_log
            ├─ company_configs UPDATED: value = new_value, config_version++
            └── Cache.invalidate("config:{company_id}")
      └── COMMIT
    [APPLIED]
      └── System propagates config to all app instances (< 1s)
      └── Derived rule changes take effect
    [AUDITED]
      └── [Background] Config change added to quarterly review queue
      └── [On next legal_review] Stamp includes this change
```

**Time SLA:**
- Approval notification to CA: <5 minutes (async email)
- Cache propagation: <1 second
- Full flow (including approval): depends on CA response SLA (typical: same business day)

---

## WF-03: Period Lock / Fiscal Year Close Workflow

```
States: OPEN → LOCK_REQUESTED → VALIDATING → LOCKED | FYEAR_CLOSED

  CA requests period lock (month: 3, year: 2026)
    [OPEN]
    └── System checks: period not yet locked
    └── System checks: all entries in period are POSTED (no DRAFT)
    └── System optionally checks: trial balance zero
    └── System checks CA role: ACCOUNTANT+
          ↓
    [VALIDATING]
          ↓ (all checks pass)
    [LOCKED]
      └── period_locks record created (lock_type=PERIOD)
      └── audit_log entry: PERIOD_LOCKED
      └── [On next invoice/voucher POST] is_period_locked() → raise AccountingPeriodLockedError
    [FYEAR_CLOSED] (variant, requires CHIEF_ACCOUNTANT role)
      └── Additional checks: BCTC submitted, audit done, tax return filed
      └── lock_type = FYEAR_CLOSED (has higher precedence than PERIOD_LOCKED)
      └── Cannot be reversed without data migration (hard flag)
```

**Lock lock_type precedence (highest to lowest):**
1. FYEAR_CLOSED (irreversible for closed year)
2. PERIOD_LOCKED (reversible only via administrator with logged justification)
3. OPEN (default)

---

## WF-04: E-Invoice Issuance Workflow

```
States: DRAFT → APPROVED → SERIES_RESERVED → SIGNED → SENT → CANCELLED | REPLACED

  SA creates Invoice(DRAFT)
    [DRAFT]
    └── SA fills invoice
    └── EInvoiceMode check: if CA_SIGNED → cert must be in ca_list
    └── InvoiceService checks period NOT locked
    └── CA approves Invoice(Approve)
      [APPROVED]
      └── System: advance_e_invoice_sequence(prefix) atomically
            ├─ SELECT next_sequence FROM e_invoice_series ... FOR UPDATE
            ├─ UPDATE e_invoice_series SET next_sequence = next + 1
            └─ INSERT INTO invoice_series_log(seq_used)
      └── Series sequence assigned
      [SERIES_RESERVED] (sequence claimed but not yet signed)
      └── System generates XML per GDT schema
      └── EInvoiceMode branch:
            ├─ SOFTWARE_CERT → sign with internal cert (signed immediately)
            └─ CA_SIGNED → CA cert signing (async if HSM)
      └── Signature embedded
      [SIGNED]
      └── System: assign invoice_number = prefix + padded_seq
      └── System: emit INVOICE_ISSUED audit event
      └── System: archive signed XML to retention storage (≥10y)
      [SENT]
      └── SA sends to customer (email/print/portal)

  Exception transitions:
    Issuance rejected → CANCELLED state; sequence is NOT returned (non-resettable)
    Cancellation with replacement → REPLACED (original invoice still stored; replaced_by_id set)
```

---

## WF-05: Legal Review Stamp Cycle

```
States: STAMP_READY → PENDING_REVIEW → STAMPED → (until next_change) → STAMP_READY

  After config_version changes
    [STAMP_READY]
    └── System: generates review_summary JSONB:
          ├─ all flag values
          ├─ all changes since last review (from config_changes)
          ├─ legal compliance checklist: MST format, retention years, VAT rates
          └─ Suggests next review date (Quarterly recommended)
    └── CA reviews summary
          ├─ PASS → STAMPED
          │       └── sets legal_reviewed_at, legal_reviewed_by
          │       └── emits LEGAL_REVIEW_STAMPED audit event
          └─ FAIL → PENDING_REVIEW (CA flags violations; reverts/updates config)
                  └── Remediation loop back to CONFIG change workflow
  [STAMPED]
    └── All flag changes since last stamp are cleared from "unreviewed" queue
    └── Config considered legally reviewed until next flag change
```

---

## WF-06: Auditor Data Extraction Workflow

```
States: REQUESTED → VALIDATING → PREPARING → DELIVERED | REJECTED

  AU (auditor) with auditor role + MFA
    → POST /config/audit-log/export with { from_date, to_date, format }
    [REQUESTED]
    └── System: validates AU role is AUDITOR or ADMIN
    └── System: validates date range ≤ 10 years (max export window)
    └── System: checks company_id in auditor's scope (if multi-company in future)
    [VALIDATING]
    └── System: runs SQL queries:
          ├─ SELECT * FROM audit_log WHERE company_id=? AND created_at BETWEEN ? AND ?
          ├─ SELECT * FROM config_changes WHERE company_id=? AND ...
          ├─ SELECT * FROM company_configs WHERE company_id=?
          └─ SELECT * FROM period_locks WHERE company_id=? AND ...
    └── System: formats as ZIP:
          ├─ audit_log.csv (flat export)
          ├─ config_changes.json
          ├─ company_config.json (current snapshot)
          └─ period_locks.json
    [PREPARING]
    └── System: emits AUDITOR_EXPORT audit event
    └── System: stores export hash (integrity check)
    [DELIVERED]
    └── AU receives signed URL (short expiry, 1 hour)
    └── AU downloads
```

---

## WF-07: VAT Rate Hot-Patch Workflow

```
States: LEGAL_CHANGE_DETECTED → SCOPE_REVIEWED → MIGRATION_READY → PATCHED → VERIFIED

  Legal team detects new VAT Circular (e.g., adding 8% rate)
    [LEGAL_CHANGE_DETECTED]
    └── Legal team publishes circular summary (Circular #, effective date, changes)
    └── Chief Accountant + Technical Lead review scope
    [SCOPE_REVIEWED]
    └── Dev writes migration: UPDATE vat_rates SET = '{0,5,8,10}' WHERE ...
    └── Migration tagged with decree_citation, effective_date, legal_signature
    └── Backward compatibility check: existing invoices with old rates → VALID
    [MIGRATION_READY]
    └── Migration applied (during maintenance window if production)
    └── System: updates company_configs.config_version += 1
    └── System: emits LEGAL_CONSTANT_UPDATE audit event (decreed_citation)
    └── System: cache invalidation
    [PATCHED]
    └── QA: verifies 8% accepted; 0/5/10 still accepted; 7% rejected
    └── QA: verifies existing invoices with rate still valid (read-only preserved)
    └── Quarterly review: CA includes in next LEGAL_REVIEW_STAMPED
    [VERIFIED]
    └── Deployment complete; tag release with vat-rate-{effective_date}
```

**Irreversibility note:** Changes to LAW-flagged constants like vat_rates require migration patches (not PATCH API). This path is explicit; no admin UI path exists.