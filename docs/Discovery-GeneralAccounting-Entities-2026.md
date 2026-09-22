# Discovery – General Accounting Entities 2026

**Date:** 2026-09-22  
**Loop:** implement-gen-acct-02 / G1  
**Scope:** Existing General Accounting entities, ports, EF configurations and architecture constraints

## Summary

Discovery of existing General Accounting domain model in SME Accounting project. Clean Architecture with CQRS, MediatR, FluentValidation, EF Core PostgreSQL, snake_case naming, xmin concurrency, company isolation.

## Existing General Accounting Domain Entities

Discovered via `src/SmeAccounting.Domain/Entities/*.cs`:

### Core accounting
- `Account`
- `AccountGroup`
- `JournalEntry`
- `JournalEntryLine`
- `PostingReference`
- `PostingConfiguration`

### Period & fiscal
- `FiscalYear`
- `FiscalPeriod`

### Dimensions
- `Department`
- `CostCenter`
- `Project`

### Currency & exchange
- `Currency`
- `ExchangeRate`

### Tax foundation
- `TaxType`
- `TaxTreatment`
- `TaxAuthority`
- `TaxRate`
- `TaxRule`
- `TaxExemptionReason`
- `TaxAccountingMapping`
- `TaxPeriod`

### Payment
- `PaymentTerm`

### Company & settings
- `Company`
- `CompanySetting`

### Voucher & transaction control
- `VoucherType`
- `DocumentNumberingSeries`
- `TransactionReason`

### Opening balances
- `OpeningBalanceMapping`
- `OpeningBalancePeriod`
- `OpeningBalanceEntry`

### Base
- `BaseEntity`

Additional entities present but outside General Accounting scope:
`User`, `Role`, `UserRole`, `CompanyMembership`, `Customer`, `Supplier`, `Employee`, `Uom`, `ItemCategory`, `Warehouse`, `UomConversion`, `Item`, `ServiceItem`, `InventoryValuationPolicy`, `InventoryAdjustmentReason`, `InventoryAccountingConfiguration`

## Domain Ports / Repository Interfaces

Discovered via `src/SmeAccounting.Domain/Ports/*.cs`:

Core ports:
- `IAccountRepository`
- `IJournalEntryRepository`
- `IUnitOfWork`
- `IForeignExchangeRateProvider`
- `IAuditLogger`
- `IPostingService`
- `IClock`

Company-scoped ports:
- `ICompanyRepository`
- `ICurrencyRepository`
- `IExchangeRateRepository`
- `IDepartmentRepository`
- `ICostCenterRepository`
- `IProjectRepository`
- `IPostingConfigurationRepository`
- `IVoucherTypeRepository`
- `IDocumentNumberingSeriesRepository`
- `ITransactionReasonRepository`

Tax ports:
- `ITaxTypeRepository`
- `ITaxTreatmentRepository`
- `ITaxAuthorityRepository`
- `ITaxRateRepository`
- `ITaxRuleRepository`
- `ITaxExemptionReasonRepository`
- `ITaxAccountingMappingRepository`
- `ITaxPeriodRepository`

Other:
- `IPaymentTermRepository`
- `ICompanySettingRepository`
- `IOpeningBalancePeriodRepository`
- `IOpeningBalanceEntryRepository`
- `IOpeningBalanceMappingRepository`

## EF Core Configurations

Discovered via `src/SmeAccounting.Infrastructure/Persistence/Configurations/*.cs`:

Pattern: `IEntityTypeConfiguration<T>` with snake_case table names, `HasColumnName`, `HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict)`, composite unique index `(CompanyId, Code)`, enum `HasConversion<string>()`, `IsRowVersion()` on `xmin`.

Configurations present:
- `AccountConfiguration`
- `AccountGroupConfiguration`
- `JournalEntryConfiguration`
- `JournalEntryLineConfiguration`
- `PostingReferenceConfiguration`
- `PostingConfigurationConfiguration`
- `FiscalYearConfiguration`
- `FiscalPeriodConfiguration`
- `DepartmentConfiguration`
- `CostCenterConfiguration`
- `ProjectConfiguration`
- `CurrencyConfiguration`
- `ExchangeRateConfiguration`
- `TaxTypeConfiguration`
- `TaxTreatmentConfiguration`
- `TaxAuthorityConfiguration`
- `TaxRateConfiguration`
- `TaxRuleConfiguration`
- `TaxExemptionReasonConfiguration`
- `TaxAccountingMappingConfiguration`
- `TaxPeriodConfiguration`
- `PaymentTermConfiguration`
- `CompanyConfiguration`
- `CompanySettingConfiguration`
- `VoucherTypeConfiguration`
- `DocumentNumberingSeriesConfiguration`
- `TransactionReasonConfiguration`
- `OpeningBalanceMappingConfiguration`
- `OpeningBalancePeriodConfiguration`
- `OpeningBalanceEntryConfiguration`

## Architecture Constraints

### Clean Architecture
- Dependency direction: Api → Application → Domain; Infrastructure → Application + Domain; Domain zero NuGet refs
- 22 NetArchTest rules enforce constraints
- Controllers must NOT reference `SmeAccounting.Domain.Entities` or `SmeAccounting.Domain.Repositories`

### Domain purity
- Domain has no NuGet PackageReferences
- Domain should not reference Microsoft./Npgsql./Serilog./EFCore. packages
- Domain should not depend on Microsoft.EntityFrameworkCore

### Layer coupling
- Controllers should not reference Domain.Entities namespace
- Controllers should not reference Domain.Ports namespace
- Application handlers should not reference Infrastructure namespace
- Infrastructure should not reference Api namespace

### Naming conventions
- Entities inheriting BaseEntity reside in Domain.Entities namespace
- Repository interfaces start with I
- Commands end with Command, Queries end with Query
- DTOs end with Dto
- Controllers end with Controller

### Technical constraints
- Target framework net10.0, C# 13, nullable enabled, implicit usings, TreatWarningsAsErrors true
- PostgreSQL with snake_case naming via EFCore.NamingConventions
- xmin concurrency tokens on all entities
- CQRS with MediatR 14.2.0, FluentValidation 12.1.0 pipeline
- Company isolation via CompanyId FK Restrict + composite unique (CompanyId, Code)
- Enum storage as string via HasConversion<string>()
- Currency codes as string, not FK
- Soft delete via IsActive flag
- Effective dating EffectiveFrom/EffectiveTo nullable

## Key Patterns Discovered

### CompanyId FK Restrict
```csharp
builder.HasOne<Company>()
    .WithMany()
    .HasForeignKey(e => e.CompanyId)
    .OnDelete(DeleteBehavior.Restrict);
```
Universal across company-scoped entities. Domain validation `companyId <= 0` throws DomainException.

### Composite unique indexes
```csharp
builder.HasIndex(e => new { e.CompanyId, e.Code }).IsUnique();
```
Used for AccountGroup, CostCenter, Department, Project, TaxType, PaymentTerm, VoucherType, TransactionReason, etc.

### Effective dating
`DateOnly EffectiveFrom` + `DateOnly? EffectiveTo`
Query pattern: `EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive`
Used on TaxRate, TaxRule, ExchangeRate, Project.

### Soft delete
`public bool IsActive { get; private set; } = true;`
`Deactivate()` sets IsActive=false. Account.Deprecate() raises AccountDeprecated.

### Enum storage
`builder.Property(e => e.AccountType).HasConversion<string>();`
All enums stored as string.

### xmin concurrency
`builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");`
Present on all BaseEntity descendants.

### Snake_case naming
`builder.ToTable("accounts");`
`builder.Property(e => e.CompanyId).HasColumnName("company_id");`

### SetNull for dimensions
JournalEntryLine optional FKs to Department/CostCenter/Project with `OnDelete(DeleteBehavior.SetNull)`.

### Domain validation
Private parameterless ctor for EF, public ctor with DomainException validation, domain events added on construction.

## Gaps for General Accounting

- Bank/BankBranch/BankAccount entities not present
- PostingReference exists but no FK to JournalEntry, no CompanyId, no repository, no application layer
- PaymentTerm exists, no Bank integration
- BankExchangeRateProvider adapter exists, no entity model

## Migrations

Existing migrations:
- 20260916051341_InitialCreate
- 20260916051520_FixAccountNameColumn
- 20260916083803_AccountingFoundation
- 20260917013843_Phase2AccountingControlConfig
- 20260917045015_Phase3TaxFoundation
- 20260917092428_BusinessPartnerFoundation
- 20260917111153_AddUom
- 20260921020615_AddItemCategory
- 20260921020956_AddWarehouse
- 20260921021609_AddUomConversion
- 20260921022726_AddItemAndServiceItem
- 20260921024242_AddInventoryValuationPolicyAndAdjustmentReason
- 20260921025725_AddInventoryAccountingConfiguration
- 20260921052333_CompanyOpeningUserMgmt

## Regulatory Context

- VAS Vietnamese Accounting Standards
- Circular 99/2025/TT-BTC compliance
- ADRs in loop-stack/vietnamese-acct-architecture_DONE/docs/architecture/

## Conclusion

General Accounting core is present with Account, JournalEntry, FiscalYear/Period, Dimensions, Currency/ExchangeRate, Tax foundation, PaymentTerm. Architecture constraints enforced via NetArchTest. Missing Bank entities and PostingReference gaps identified for next tasks.
