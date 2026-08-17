# Data Flows: System Settings Module

## DF-01: Config Initialization Data Flow
**Trigger**: Chief Accountant first-time system setup  
**Data Origin**: Domain defaults + Chief Accountant input  
**Data Path**:  
1. Domain layer provides default values for CompanyConfig fields (from base.py enums/constants)  
2. Chief Accountant input via UI form → validated at boundary → stored in temp session  
3. "Initialize System Settings" click → SystemSettingsService.initialize() called  
4. Service creates CompanyConfig record with domain-derived defaults  
5. AuditLogService emits CREATE event: {entity_type=CompanyConfig, entity_id=<id>, action=CREATE, new_value=<full config>, before_value=null, actor_id=<admin_id>, timestamp=now}  
6. Record persisted to `company_configs` table via SQLAlchemy adapter  
7. Response: confirmation + legal_reviewed_at=null notice  

**Data Transformation**:  
- Enum values (AccountingRegime, CompanyType) → stored as string in DB; domain layer converts back on read  
- Frozen sets (vat_rates, ca_list) → stored as JSON string in DB; domain layer converts back on read  
- Boolean flags (is_active, data_deletable) → stored as tinyint(1) in DB  

---

## DF-02: Period Lock Data Flow
**Trigger**: Chief Accountant locking/unlocking a period  
**Data Origin**: Chief Accountant input + PeriodLockService validation  
**Data Path**:  
1. Chief Accountant inputs period_start, period_end via UI → validated (date format, not future of company existence)  
2. PeriodLockService.is_locked(company_id, period_start, period_end) checked against `period_locks` table  
3. If not locked: New PeriodLock record data prepared: {company_id, period_start, period_end, is_locked=True, locked_by_id=admin_id, reason=optional, created_at=now}  
4. Record persisted to `period_locks` table via SQLAlchemy adapter  
5. AuditLogService emits CREATE event: {entity_type=PeriodLock, entity_id=<id>, action=CREATE, new_value=<lock details>, before_value=null, actor_id=<admin_id>, timestamp=now}  
6. Response: confirmation + period now locked at service layer  

**If locking fails** (period has vouchers):  
- Error data: {period_start, period_end, existing_voucher_count, existing_invoice_count}  
- Error raised to UI with actionable message  

**If unlocking**:  
- Similar data path with is_locked=False + audit LOG DELETE event  

---

## DF-03: Config Update Data Flow
**Trigger**: Admin modifying a system configuration flag  
**Data Origin**: Current CompanyConfig value + Admin new value  
**Data Path**:  
1. System reads current CompanyConfig value from `company_configs` table via SQLAlchemy adapter  
2. Admin inputs new value via UI → validated against flag_type (LAW vs CONFIG)  
3. If LAW: System raises FlagLockedError; no data mutation  
4. If CONFIG:  
   a. System emits AuditLogService event BEFORE mutation:  
      {flag_name, old_value=<current DB value>, new_value=<admin input>, actor_id=<admin_id>, timestamp=now, table_name=CompanyConfig}  
   b. System updates CompanyConfig record: UPDATE company_configs SET <field>=<new_value>, config_version=config_version+1 WHERE id=<id>  
   c. System emits AuditLogService event AFTER mutation: {flag_name, new_value=<admin input>, actor_id=<admin_id>, timestamp=now, table_name=CompanyConfig, config_version=<new_version>}  
5. Response: confirmation + new config_version displayed  

**Data Transformation**:  
- config_version: integer incremented by 1 each change  
- LAW-type flags: mutation blocked; error raised instead  
- CONFIG-type flags: mutation permitted with audit trail  

---

## DF-04: VAT Rate Validation Data Flow
**Trigger**: User creating/editing invoice/voucher VAT rate  
**Data Origin**: User input + CompanyConfig.vat_rates frozenset  
**Data Path**:  
1. User inputs VAT rate via invoice/voucher form  
2. System reads CompanyConfig.vat_rates from `company_configs` table  
3. System validates: rate ∈ vat_rates (i.e., rate ∈ {0, 5, 10})  
4. If valid: Proceed with invoice/voucher creation; Invoice._recalculate() or Voucher post() computes totals  
5. If invalid: System raises InvalidVATRateError; form field marked error; user must correct  

**Data Transformation**:  
- vat_rates stored as JSON string "[0,5,10]" in DB  
- Domain layer converts to frozenset{int} on read  
- Validation error message: "Thuế GTGT {rate} không hợp lệ. Các mức được phép: {0, 5, 10}"

---

## DF-05: E-Invoice Series Data Flow
**Trigger**: Chief Accountant managing e-invoice series  
**Data Origin**: Chief Accountant input + GDT constraints  
**Data Path**:  
1. Chief Accountant inputs series prefix via UI  
2. System reads current series count from `e_invoice_series` table  
3. If count < 15: New EInvoiceSeries record prepared: {series_prefix, next_sequence=1, is_active=True, ca_signer=<optional>, company_id=<current>, created_at=now}  
4. Record persisted to `e_invoice_series` table via SQLAlchemy adapter  
5. AuditLogService emits CREATE event: {entity_type=EInvoiceSeries, entity_id=<id>, action=CREATE, new_value=<series details>, before_value=null, actor_id=<admin_id>, timestamp=now}  
6. Response: series added confirmation + current count + max limit warning  

**If at limit** (count ≥ 15):  
- Error: "Đã đạt giới hạn 15 series số hóa đơn điện tử.active"  
- No data mutation  

**Data Transformation**:  
- series_prefix: string (e.g., "AA/2026")  
- next_sequence: integer, auto-incremented on each invoice within the series  
- is_active: boolean; only one series typically active per prefix, but up to 15 total active series permitted  
- ca_signer: optional string referencing GDT-approved CA identifier  

---

## DF-06: Config Change Audit Data Flow
**Trigger**: Any CompanyConfig modification  
**Data Origin**: System internal (SystemSettingsService)  
**Data Path**:  
1. SystemSettingsService.update_config() called  
2. BEFORE mutation: AuditLogService.create({entity_type=CompanyConfig, entity_id=<id>, action=CREATE/UPDATE, field_name=<field>, old_value=<current>, new_value=<new>, actor_id=<admin_id>, timestamp=now})  
3. CompanyConfig record updated: field=new_value, config_version=config_version+1  
4. AuditLogService.create({entity_type=CompanyConfig, entity_id=<id>, action=UPDATE, field_name=<field>, old_value=<current>, new_value=<new>, actor_id=<admin_id>, timestamp=now, config_version=<new_version>})  
5. Both events persisted to `audit_log` table via SQLAlchemy adapter  

**Data Fields in audit_log**:  
- id: UUID primary key  
- entity_type: "CompanyConfig"  
- entity_id: CompanyConfig UUID  
- action: "CREATE" or "UPDATE"  
- field_name: e.g., "vat_method", "vat_rates", "e_invoice_mode"  
- old_value: previous value (JSON-stringified where needed)  
- new_value: new value (JSON-stringified where needed)  
- actor_id: admin UUID who made the change  
- changed_at: timestamp of change  
- config_version: CompanyConfig config_version after change  

**Postconditions**: Full audit trail of all config changes; auditors can export audit_log table without UI assistance
