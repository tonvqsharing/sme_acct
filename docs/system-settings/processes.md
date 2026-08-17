# Processes: System Settings Module

---

## P-01: Company Setup Process

**Actor:** CA (Chief Accountant), A (Admin), External: GDT Tax Authority, PKI Provider
**Trigger:** New company onboarded — MST registered at GDT

```
[External] GDT issues MST certificate
  → MST entered + validated (LAW flag: tax_id_pattern enforced)
  → [A/CA] Select accounting regime (one-shot decision; BCTC format derived)
      ├─ SELECT TT200 → standard COA derived
      ├─ SELECT TT99 → new COA (effective 2026+)
      ├─ SELECT TT58_MICRO → simplified BCTC
      └─ SELECT TT133 → SME alternative (check legal continuity)
  → CA selects e-invoice mode
      ├─ SOFTWARE_CERT → no external integration; transitional
      └─ CA_SIGNED → integrate CA PKI; populate ca_list from GDT list
  → [A] Configure fiscal year (one-shot; BCTC periods derived)
  → [A] Configure settlement cycle (MONTHLY default; QUARTERLY optional ≤ VND 1B revenue)
  → CA optionally configures:
      ├─ invoice series (max 15; each declared to GDT)
      ├─ default_currency (multi-currency if foreign trading)
      ├─ cost_center structure (optional for most SMEs)
      └─ print/email templates
  → CA confirms legal review (legal_reviewed_at stamp)
  → System: emits CONFIG_CREATED audit event
  → System: sets config_version=1
  → [A] Authorizes PROD use for CA team
```

**Exit criteria:** config_version ≥ 1; legal_reviewed_at not null; period lock [current period] active; smoke test (3 invoices/vouchers) passes

---

## P-02: Accounting Period Close Process

**Trigger:** CA determines a period is ready to close (typically month-end or year-end)

```
[CA] Verifies period complete:
  ├─ All entries posted (DRAFT count = 0)
  ├─ Bank reconciliation balanced
  ├─ Tax provision calculated
  └─ Trial balance zero-mismatch < tolerance (0.01)
  → [System] Checks: entry_date NOT in LOCKED or FYEAR_CLOSED period
  → [System] Validates period integrity (no orphaned JEs, no missing cross-refs)
  → [CA] POST period lock
  → [System] Creates PeriodLock record (lock_type=PERIOD)
  → [System] Emits PERIOD_LOCKED audit event
  → [System] Invalidates period cache; all app instances acknowledge within 1s
  → Any subsequent POST/issue attempts with date in locked period → 403 PERIOD_LOCKED
```

### Fiscal Year Close (variant)
Additional checkpoints:
- Annual tax return filed and accepted by GDT
- BCTC audited (if required by law for company type)
- Audit adjustments posted
- CHIEF_ACCOUNTANT (not just ACCOUNTANT) authenticated
- lock_type changed to FYEAR_CLOSED (irreversible without data migration)

---

## P-03: Config Change Management Process

**Trigger:** A or CA requests change to CONFIG-type flag

```
[A] Identify flag name + new value
  → [A] GET current config_version
  → [System] Validate: flag type is CONFIG (not LAW); actor has ADMIN role
  → IF flag.requires_2nd_approval:
      → [System] Creates approval request; notifies CA
      → [CA] Reviews; APPROVES or REJECTS
      → IF REJECTED → ABORT; audit log records rejection
  → [System] BEGIN transaction
      ├─ Write CONFIG_CHANGED to config_changes (before/after JSON)
      ├─ Emit CONFIG_CHANGED to audit_log (actor, before, after)
      ├─ Update company_configs SET new value, config_version = config_version + 1
      └─ Invalidate cache key "config:{company_id}"
  → [System] COMMIT
  → [System] Propagate config to all app instances (within 1s)
  → [System] Apply any derived rule changes
```

**Special rules:**
- `accounting_regime` change is LEGISLATIVE event: requires tax authority filing + CA legal review before approval
- `vat_method` change is BINDING once applied; system must prevent mid-period switches

---

## P-04: E-Invoice Issuance Process

**Trigger:** CA approves draft invoice or SA auto-generates from posting

```
[SA] Creates Invoice(DRAFT) with valid MST, account codes, items
  → [System] Validates period NOT locked (period_lock check on issue_date)
  → [CA] Approves Invoice
  → [System] Checks EInvoiceMode
      ├─ SOFTWARE_CERT → signs internally
      └─ CA_SIGNED →
          ├─ Looks up signing cert in PKI store
          ├─ Validates cert in ca_list
          ├─ Validates cert expiry (check cert_expiry < now + 30 days?)
          └─ Calls HSM/PKIS for signature
  → [System] Reads next sequence for series prefix atomically (advance)
  → [System] Constructs XML per GDT schema (NĐ 123)
  → [System] Signs / embeds signature
  → [System] Assigns issued sequence number
  → [System] Emits: INVOICE_ISSUED to audit_log (MST-visible for tax audit)
  → [System] Archives signed XML + metadata to retention storage
  → [SA] can print / send / store for customer
```

---

## P-05: Audit Trail Guarantee Process

**Trigger:** Any config change, period lock, special threshold event, failed validation attempt

```
[Any User Action] Attempts config write, period close, high-amount JE posting
  → [System] Appends to audit_log table (APPEND ONLY; NO UPDATE; NO DELETE)
      ├─ id (gen_random_uuid), company_id, actor_user_id (None for system)
      ├─ action (CONFIG_UPDATED | PERIOD_LOCKED | FLAG_VIOLATION | ...)
      ├─ entity_type, entity_id
      ├─ before_value (JSONB of previous config state)
      ├─ after_value (JSONB of new config state)
      ├─ ip_address, user_agent
      └─ created_at (= now() at DB level — NOT application time)
  → [DB] WRITE succeeds (REVOKE DELETE on audit_log from all application roles)
  → [System] Sends audit event to async queue (for dashboards, alerts)
  → [Background Worker] Archives audit_log row to WORM-compatible cold storage after → 2 years
  → [Background Worker] Purges from hot DB only after legal retention period (≥10y)
```

**Critical constraint:** `REVOKE DELETE ON audit_log FROM PUBLIC;` enforced via dedicated DB role with SELECT-only for application.

---

## P-06: Tax / Integration Sync Process

**Trigger:** VAT settlement due date; or on-demand sync request

```
[CA] Requests e-tax sync
  → [System] Reads: vat_method, settlement_cycle, fiscal_year
  → Determines: filing period boundaries from accounting_period_type
  → [System] Queries: all VAT-driven transactions in period
  → [System] Formats: CSV/XML per tax authority schema
  → [System] Flags: any transactions with period=LOCKED (no re-filing possible)
  → [CA] Reviews + signs export
  → [System] Emits TAX_EXPORT audit event
  → [System] Transmits via HTTPS to thuedientu.gdt.gov.vn (future API integration)
  → [System] Records: transmission ID, timestamp, response code
  → [System] Stores: submission history for tax audit trail (≥10y)
```

---

## P-07: Data Retention Enforcement Process

**Trigger:** Fiscal year close; or periodic cleanup job (daily)

```
  → [Background Job] Runs nightly
  → For each document type [voucher, invoice, BCTC]:
      ├─ Check: document.date + data_retention_years < today()?
      └─ AND: document is in ARCHIVED state (not soft-delete)
  → IF retention satisfied AND legal holds not flagged:
      → [System] Moves to cold storage (WORM S3/Glacier or equivalent)
      → [System] Removes from hot DB index (query-only via archive restore)
      → [System] Emits RETENTION_ARCHIVED audit event
  → IF retention NOT satisfied:
      → [System] BLOCKS any DELETE; guarantees data integrity
  → [System]同时对: NĐ 13/2023 personal data retention
      ├─ Employee records: retain per employment + 10y
      └─ Anonymize after retention if PDPA deletion request received
```

---

## P-08: Legal Constant Hot-Patch Process

**Trigger:** GDT issues new Circular changing VAT rates, CA list, or other constants

```
[Legal Team] Monitors: vbpl.vn, gdt.gov.vn for new Circulars
  → [Legal Team] Reviews impact; legal sign-off
  → [Chief Accountant] Approves patch scope
  → [Dev Team] Creates migration:
      ├─ Version bumps: config_version + 1
      ├─ Updates vat_rates from {0,5,10} to {0,5,8,10} (example)
      ├─ Populates ca_list from latest GDT-approved CA list
      └─ Runs BACKWARDS compatibility check: existing invoices with old rate = valid
  → [System] Validates: no inflight transactions depend on old constant
  → [System] Migrates: atomic write + audit log
  → [System] Emits LEGAL_CONSTANT_UPDATE with decree_citation
  → [System] Cache invalidation
  → [Quarterly Review] Chief Accountant reviews patch in legal review stamp cycle
```