# DocumentNumberingSeries / VoucherType / TransactionReason Design Summary

**Date:** 2026-09-21  
**Loop:** 01-system-security  
**Task:** [G1] Design DocumentNumberingSeries/VoucherType/TransactionReason domain entities, events, and concurrency-safe numbering logic

## Overview

Domain entities for system security numbering and voucher classification follow Clean Architecture constraints: Domain pure, BaseEntity pattern, DomainException validation, minimal domain events, EF Core configurations with snake_case naming, `xmin` row version concurrency tokens, and FK Restrict to Company.

## Entities

### DocumentNumberingSeries

**File:** `src/SmeAccounting.Domain/Entities/DocumentNumberingSeries.cs`

- Extends `BaseEntity`
- Private parameterless ctor for EF
- Public ctor validates:
  - `CompanyId > 0`
  - `VoucherTypeId > 0`
  - `Prefix` non-empty
  - `PaddingLength` between 1 and 10
- Properties: `VoucherTypeId`, `CompanyId`, `Prefix`, `NextNumber` default 1, `PaddingLength` default 6, `IsDefault`, `IsActive` default true, `Description?`
- Domain methods:
  - `Increment()` → `NextNumber++`
  - `Reset(startFrom)` → validates `startFrom > 0`
  - `Deactivate()` → `IsActive = false`
- **Domain event:** None on creation. Recommendation: add `DocumentNumberingSeriesCreated(Id, CompanyId)` for consistency with VoucherType/TransactionReason.
- **Concurrency safety:** Relies on optimistic concurrency via `xmin`. Numbering must be performed within a single EF transaction loading the series with row version, incrementing in memory, saving; `DbUpdateConcurrencyException` will be thrown on conflict. No explicit locking in domain model.

**EF Config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DocumentNumberingSeriesConfiguration.cs`
- Table: `document_numbering_series`
- Snake_case columns: `id`, `voucher_type_id`, `company_id`, `prefix`, `next_number`, `padding_length`, `is_default`, `is_active`, `description`
- Unique index: `(voucher_type_id, company_id, prefix)`
- FK Restrict:
  - `CompanyId` → `Company`
  - `VoucherTypeId` → `VoucherType`
- Row version: `xmin` as `IsRowVersion()`

### VoucherType

**File:** `src/SmeAccounting.Domain/Entities/VoucherType.cs`

- Extends `BaseEntity`
- Private parameterless ctor
- Public ctor validates:
  - `CompanyId > 0`
  - `Code` non-empty
  - `Name` non-empty
- Properties: `Code`, `Name`, `VoucherCategory`, `CompanyId`, `IsActive` default true, `Description?`
- Domain method: `Deactivate()`
- **Domain event:** `VoucherTypeCreated(Id, CompanyId, DateTimeOffset.UtcNow)` raised in ctor
- Event minimalism: `VoucherTypeId` + `CompanyId` + `OccurredOn` only

**EF Config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/VoucherTypeConfiguration.cs`
- Table: `voucher_types`
- Snake_case columns: `id`, `company_id`, `code`, `name`, `voucher_category`, `is_active`, `description`
- `VoucherCategory` stored as string via `HasConversion<string>()`
- Unique index: `(company_id, code)`
- FK Restrict: `CompanyId` → `Company`
- Row version: `xmin`

### TransactionReason

**File:** `src/SmeAccounting.Domain/Entities/TransactionReason.cs`

- Extends `BaseEntity`
- Private parameterless ctor
- Public ctor validates:
  - `CompanyId > 0`
  - `VoucherTypeId > 0`
  - `Code` non-empty
  - `Name` non-empty
- Properties: `Code`, `Name`, `VoucherTypeId`, `CompanyId`, `IsActive` default true, `Description?`
- Domain method: `Deactivate()`
- **Domain event:** `TransactionReasonCreated(Id, CompanyId, DateTimeOffset.UtcNow)` raised in ctor
- Event minimalism: `TransactionReasonId` + `CompanyId` + `OccurredOn` only

**EF Config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/TransactionReasonConfiguration.cs`
- Table: `transaction_reasons`
- Snake_case columns: `id`, `company_id`, `voucher_type_id`, `code`, `name`, `is_active`, `description`
- Unique index: `(company_id, code)`
- FK Restrict:
  - `CompanyId` → `Company`
  - `VoucherTypeId` → `VoucherType`
- Row version: `xmin`

## Compliance Checklist

- **BaseEntity pattern:** All three entities extend `BaseEntity`, private parameterless ctor present, public validating ctor present.
- **Validation DomainException:** All constructors throw `DomainException` for invariants.
- **Domain events minimalism:** VoucherType and TransactionReason raise creation events with EntityId + CompanyId + OccurredOn. DocumentNumberingSeries lacks creation event.
- **EF snake_case / xmin / FK Restrict:** All configurations use snake_case table/column names, `xmin` row version, `DeleteBehavior.Restrict` on Company and VoucherType FKs.
- **Clean Architecture:** Domain has zero NuGet refs, no EF references, ports in `Domain/Ports/`, events in `Domain/Events/`.

## Concurrency-Safe Numbering Logic

Current implementation:
- `DocumentNumberingSeries.Increment()` increments `NextNumber` in memory.
- Persistence uses EF Core optimistic concurrency via `xmin`.
- Recommended usage pattern:
  1. Load series with `AsTracking()` within a transaction.
  2. Call `Increment()` / `Reset()`.
  3. Save changes; EF checks `xmin`.
  4. On `DbUpdateConcurrencyException`, retry load-increment-save loop.

No database-level sequence per series is implemented; numbering is application-controlled.

## Findings & Recommendations

- Entities comply with BaseEntity, DomainException validation, EF naming/concurrency/FK Restrict.
- Domain events minimalism confirmed for VoucherType and TransactionReason.
- DocumentNumberingSeries missing creation domain event; consider adding for audit consistency.
- Concurrency safety depends on caller using EF optimistic concurrency; document retry policy in Application layer handlers.

## References

- Domain entities: `src/SmeAccounting.Domain/Entities/DocumentNumberingSeries.cs`, `VoucherType.cs`, `TransactionReason.cs`
- EF configs: `src/SmeAccounting.Infrastructure/Persistence/Configurations/DocumentNumberingSeriesConfiguration.cs`, `VoucherTypeConfiguration.cs`, `TransactionReasonConfiguration.cs`
- Events: `src/SmeAccounting.Domain/Events/VoucherTypeCreated.cs`, `TransactionReasonCreated.cs`
- Loop memory: `loop-stack/01-system-security/MEMORY.md`
