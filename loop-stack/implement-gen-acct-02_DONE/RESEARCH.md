# Research Log
## Context & Prior Work
**Repository structure**
- Solution: SmeAccounting.sln (classic .sln)
- Projects: SmeAccounting.Domain, SmeAccounting.Application, SmeAccounting.Infrastructure, SmeAccounting.Api, SmeAccounting.ArchitectureTests
- Target framework: net10.0 (Directory.Build.props), C# 13, nullable enabled, implicit usings, TreatWarningsAsErrors true
- Clean Architecture enforced by 22 NetArchTest rules

**Domain layer**
- Zero NuGet refs, pure library
- Entities: Account, AccountGroup, JournalEntry, JournalEntryLine, FiscalYear, FiscalPeriod, PostingReference, Company, Currency, ExchangeRate, Department, CostCenter, Project, VoucherType, DocumentNumberingSeries, TransactionReason, PostingConfiguration, OpeningBalanceMapping, TaxType, TaxTreatment, TaxAuthority, TaxRate, TaxRule, TaxExemptionReason, TaxAccountingMapping, TaxPeriod, Uom, ItemCategory, Warehouse, UomConversion, Item, ServiceItem, InventoryValuationPolicy, InventoryAdjustmentReason, InventoryAccountingConfiguration, CompanySetting, OpeningBalancePeriod, OpeningBalanceEntry, User, Role, UserRole, CompanyMembership, Customer, Supplier, Employee, PaymentTerm, etc.
- ValueObjects: AccountCode, AccountType, Currency, ExchangeRateType, FilingFrequency, FiscalYearStatus, Money, NormalBalance, PaymentTermType, PeriodStatus, PeriodType, TaxAccountingMappingType, TaxAuthorityLevel, TaxCategory, TaxPeriodStatus, TaxTreatmentType, VoucherCategory
- Ports: IAccountRepository, IJournalEntryRepository, IUnitOfWork, IForeignExchangeRateProvider, IAuditLogger, IPostingService, IClock, plus repositories for Company, Currency, Department, CostCenter, Project, Tax*, User*, etc.
- BaseEntity with domain events, private parameterless ctor for EF, public ctor with DomainException validation

**Application layer**
- MediatR 14.2.0, FluentValidation 12.1.0
- Commands/Queries as records implementing IRequest<T>
- ValidationBehavior pipeline
- DTOs as records, no domain references
- Services: IAccountingReportService port

**Infrastructure layer**
- EF Core 10.0.4, Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3, EFCore.NamingConventions
- PostgreSQL connection: Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456
- Snake-case table/column naming, xmin concurrency tokens
- DbContext SmeAccountingDbContext implements IUnitOfWork, DbSets for all entities, ignores domain events
- Configurations: one *Configuration per entity, HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict), composite unique indexes on (CompanyId, Code), enums stored as string via HasConversion<string>()
- Repositories: Ef*Repository per entity, async CRUD, AsNoTracking for reads
- Migrations: 20260916051341_InitialCreate, 20260916051520_FixAccountNameColumn, 20260916083803_AccountingFoundation, 20260917013843_Phase2AccountingControlConfig, 20260917045015_Phase3TaxFoundation, 20260917092428_BusinessPartnerFoundation, 20260917111153_AddUom, 20260921020615_AddItemCategory, 20260921020956_AddWarehouse, 20260921021609_AddUomConversion, 20260921022726_AddItemAndServiceItem, 20260921024242_AddInventoryValuationPolicyAndAdjustmentReason, 20260921025725_AddInventoryAccountingConfiguration, 20260921052333_CompanyOpeningUserMgmt

**API layer**
- ASP.NET MVC controllers thin, MediatR dispatch only
- Swagger, FluentValidation, MediatR

**Existing concepts found**
- Account, AccountGroup, CostCenter, Department, Project, Currency, ExchangeRate, FiscalYear, FiscalPeriod, Tax, VAT via TaxType/TaxTreatment/TaxRate/TaxRule/TaxExemptionReason/TaxAuthority/TaxPeriod, Posting via JournalEntry/JournalEntryLine/PostingReference/PostingConfiguration, PaymentTerm exists, Bank/BankAccount/BankBranch not found
- Company scope: CompanyId FK on most entities with DeleteBehavior.Restrict, composite unique (CompanyId, Code)
- Audit: domain events, xmin concurrency, IAuditLogger port
- Soft delete: IsActive flag pattern, Account.Deprecate() sets IsActive=false
- Tests: ArchitectureTests with 22 NetArchTest rules
- Seed data: SystemSecuritySeed present

**Patterns**
- FK to Company pattern universal
- Enum storage as string
- String over FK for currency codes (Money uses string Currency)
- Backwards-compatible method expansion
- Domain event minimalism: entity ID + company ID + occurredOn
- Private parameterless ctor + public ctor with validation
## External Knowledge & Resources
**Documentation**
- README.md missing at repo root
- Docs present:
  - docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md — Circular 99/2025/TT-BTC, Law 48/2024/QH15 VAT, Law 67/2025/QH15 CIT, Law 109/2025/QH15 PIT
  - docs/discovery-phase0.md
  - docs/company-company-setting-design-summary.md
  - docs/document-numbering-voucher-transaction-reason-design-summary.md
  - docs/system-security-review-2026-09-21.md
  - docs/seed-system-security-defaults.md
- No .env.example found

**Configuration**
- appsettings.json: ConnectionStrings.DefaultConnection = Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456
- appsettings.Development.json exists
- Directory.Build.props: net10.0, C#13, TreatWarningsAsErrors true

**External APIs / Integrations**
- IForeignExchangeRateProvider port exists with stub BankExchangeRateProvider returning mock rates
- No external HTTP clients configured
- Regulatory references tracked via ADRs, not external services

**Regulatory traceability**
- VAS and Circular 99/2025/TT-BTC compliance core design constraint
- Legal sources documented in ADR-010 with article mapping to domain entities
## Requirements & Constraints
**DB Schema & Data Models — SME Accounting**

**Global patterns**
- Company isolation: FK `CompanyId` → `companies.id` with `DeleteBehavior.Restrict` on all company-scoped entities. Configured via `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(Restrict)`.
- Composite unique indexes per company: `(CompanyId, Code)` for AccountGroup, CostCenter, Department, Project, TaxType, TaxRule, PaymentTerm, VoucherType, TransactionReason, etc. Enforced at DB level.
- Effective dating: `DateOnly EffectiveFrom` + nullable `DateOnly? EffectiveTo` on TaxRate, TaxRule, ExchangeRate, Project.StartDate/EndDate. Query pattern: `EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive`.
- Soft delete: `IsActive` boolean flag. Domain `Deprecate()` sets `IsActive=false`, no hard delete. Account.Deprecate() raises `AccountDeprecated`.
- Audit / concurrency: All entities extend `BaseEntity` with `xmin` row version `IsRowVersion()` → PostgreSQL `xid`. Domain events raised on construction/state change, minimal payload `EntityId + CompanyId + OccurredOn`.
- Enum storage: all enums stored as string via `HasConversion<string>()` — `AccountType`, `NormalBalance`, `PeriodType`, `PeriodStatus`, `FiscalYearStatus`, `ExchangeRateType`, `TaxCategory`, `PaymentTermType`.
- Currency handling: `Money` VO uses `string Currency` code, not FK. Currency entity has unique index on `Code` (ISO 4217 3 uppercase chars). `FunctionalCurrencyCode` on Company is string.
- Snake-case naming: `EFCore.NamingConventions` → tables/columns snake_case. `ToTable("accounts")`, `HasColumnName("company_id")`.
- FK delete behaviors: Company → Restrict; JournalEntryLine → Department/CostCenter/Project → `SetNull` (dimensions optional, retain line data).

**Entity constraints**

*Account*
- Table `accounts`. PK `id`. Owned value object `Code` → column `code` varchar(20). Columns: `level`, `name`, `parent_id`, `account_type` string, `is_active`, `account_group_id`, `company_id`, `description` varchar(500), `normal_balance` string.
- FK `company_id` Restrict to companies. Self FK `parent_id` Restrict. Index on `parent_id`, `company_id`.
- Domain: `AccountCode` validated numeric? Constructor requires `AccountCode`, `name`, `AccountType`, `companyId>0`, `NormalBalance`. `Deprecate()` sets `IsActive=false`.

*AccountGroup*
- Table `account_groups`. PK `id`. Columns: `code` varchar(20) required, `name` varchar(200) required, `account_type` string, `company_id`, `display_order`.
- FK `company_id` Restrict. No composite unique index defined in config (unique per company enforced via application? Memory notes composite unique for dimensions only). `xmin` concurrency.

*CostCenter / Department / Project*
- Tables `cost_centers`, `departments`, `projects`. PK `id`. Columns: `company_id`, `code` varchar(50) required, `name` varchar(200) required, `is_active`, `start_date`/`end_date` for Project.
- Composite unique index `(company_id, code)` IsUnique.
- FK `company_id` Restrict.
- Domain validation: `companyId>0`, code/name non-empty. Domain events `CostCenterCreated`, `DepartmentCreated`, `ProjectCreated` with `Id, CompanyId, OccurredOn`.
- JournalEntryLine optional FKs to these with `SetNull` on delete.

*Currency*
- Table `currencies`. PK `id`. Columns: `code` varchar(3) required unique, `name` varchar(100), `symbol` varchar(10), `decimal_places`, `is_default`, `is_active`.
- Unique index on `code`. No CompanyId — global master data.
- Domain: code must be 3 uppercase ISO 4217. Event `CurrencyCreated`.

*ExchangeRate*
- Table `exchange_rates`. PK `id`. Columns: `company_id`, `from_currency_code` varchar(3), `to_currency_code` varchar(3), `rate` numeric(10,6), `rate_type` string, `effective_date` date, `source` varchar(200).
- Composite unique index `(company_id, from_currency_code, to_currency_code, rate_type, effective_date)`.
- FK `company_id` Restrict.
- Domain validation: companyId>0, codes non-empty, from≠to, rate>0. Event `ExchangeRateRecorded`.

*FiscalYear*
- Table `fiscal_years`. PK `id`. Columns: `company_id`, `year`, `start_date` date, `end_date` date, `description`, `status` string.
- FK `company_id` Restrict. Index on `company_id`.
- Domain: companyId>0, startDate<endDate. Event `FiscalYearCreated`.

*FiscalPeriod*
- Table `fiscal_periods`. PK `id`. Columns: `year_id`, `month`, `start_date` date, `end_date` date, `period_type` string, `status` string, `opened_at`, `closed_at`.
- Index on `year_id`. No direct CompanyId FK (via Year). Domain `Open`/`Close` changes status and raises `PeriodClosed`.

*Tax*
- TaxType: table `tax_types`. Columns `company_id`, `code` varchar(20), `name` varchar(200), `tax_category` string, `is_active`, `description`. Unique `(company_id, code)`. FK Restrict.
- TaxRate: table `tax_rates`. Columns `company_id`, `tax_type_id`, `rate_value` decimal(5,2), `rate_name` varchar(200), `effective_from` date, `effective_to` date nullable, `is_active`, `description`. Unique `(company_id, tax_type_id, rate_value, effective_from)`. FKs Restrict to Company & TaxType.
- TaxRule: table `tax_rules`. Columns `company_id`, `tax_type_id`, `tax_rate_id` nullable, `tax_treatment_id`, `code` varchar(20), `name` varchar(200), `conditions`, `legal_reference` varchar(500) required, `effective_from`, `effective_to` nullable, `is_active`, `description`. Unique `(company_id, code)`. FKs Restrict to Company/TaxType/TaxRate/TaxTreatment. Domain requires `LegalReference` for audit.
- TaxExemptionReason follows TaxTreatment two-FK pattern with unique `(company_id, code)`.
- Effective-date query standard for TaxRate/TaxRule.

*Posting*
- JournalEntry: table `journal_entries`. PK `id`. Columns `entry_number` varchar(50), `date` timestamptz, `period_id`, `description` varchar(500), `source_type` varchar(100), `source_id`, `posted_by` varchar(100), `posted_at`, `is_posted`. Indexes on `period_id`, `entry_number`. No CompanyId directly (via Period→Year→Company).
- JournalEntryLine: table `journal_entry_lines`. PK `id`. Columns `entry_id`, `account_id`, `debit_amount` numeric, `debit_currency` varchar(3), `credit_amount` numeric, `credit_currency` varchar(3), `description`, `department_id` nullable, `cost_center_id` nullable, `project_id` nullable. Indexes on entry/account/dimensions. FKs to Department/CostCenter/Project `SetNull`.
- PostingReference: table `posting_references`. PK `id`. Columns `journal_entry_id`, `source_type` varchar(100), `source_id`. Index on `(source_type, source_id)`.

*Payment / Bank*
- PaymentTerm exists: table `payment_terms`. Columns `company_id`, `code` varchar(20), `name` varchar(200), `payment_term_type` string, `days`, `is_active`, `description`. Unique `(company_id, code)`. FK Restrict.
- Bank/BankAccount entities not present in current schema.

**State management**
- BaseEntity provides `DomainEvents` collection, `AddDomainEvent`.
- Private parameterless ctor for EF, public ctor with `DomainException` validation.
- Concurrency via `xmin` row version.
- Authorization patterns: company-scoped repositories `GetByCodeAsync(code, companyId)`, `GetAllByCompanyAsync`. No explicit ASP.NET authorization in domain; application layer handles.

**Migrations**
- InitialCreate: accounts, account_groups, fiscal_years, journal_entries, posting_references, fiscal_periods, journal_entry_lines.
- AccountingFoundation: adds Company, Currencies, CostCenters, Departments, Projects, ExchangeRates; adds company_id to fiscal_years/accounts/account_groups; adds dimension FKs to journal_entry_lines with SetNull; composite unique indexes.
- Phase2AccountingControlConfig, Phase3TaxFoundation, BusinessPartnerFoundation, etc. extend schema.

**Constraints summary**
- Company isolation mandatory via FK Restrict + composite unique indexes.
- Soft delete via IsActive, never hard delete.
- Effective dating for rates/rules/rates with nullable EffectiveTo.
- Concurrency via xmin.
- Audit via domain events + LegalReference on TaxRule.
- Enum as string, currency as string code.
- Snake-case DB naming.

## Environment & Integration
**CI/CD**
- No CI configuration found: no `.github/workflows/`, no `azure-pipelines.yml`, no CI files discovered in repo.
- No automated pipeline config present.

**Docker / Infrastructure**
- No Dockerfile found.
- No docker-compose.yml found.
- Docker not installed per TOOLS.md (Not Available).
- Build and run performed locally via dotnet CLI.

**Build**
- dotnet SDK version: 10.0.401 (TOOLS.md, `dotnet --version` confirms)
- Target framework: net10.0 per Directory.Build.props
- C# 13, nullable enabled, implicit usings, TreatWarningsAsErrors=true
- Build command: `dotnet build SmeAccounting.sln` — primary verification, warnings-as-errors enforced
- Build succeeds with 0 warnings 0 errors required

**Tests**
- Architecture tests: `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22 NetArchTest rules enforce Clean Architecture dependency direction
- No unit/integration test commands documented beyond architecture tests

**EF Core Migrations**
- `dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- `dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- `dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- dotnet-ef global tool version 10.0.12

**Database / PostgreSQL**
- PostgreSQL 16.14 via EF Core on Windows host 172.21.208.1
- Connection string in appsettings.json: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`
- Connect via psql: `PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev`
- Snake-case naming via EFCore.NamingConventions, xmin concurrency tokens

**Run**
- `dotnet run --project src/SmeAccounting.Api/` — Swagger at /swagger in dev

**Build Scripts**
- No build scripts (.sh, Makefile) found

## Task-Specific Research — [G1] Discover existing General Accounting entities, ports, EF configurations and architecture constraints via code exploration

### Existing General Accounting Domain Entities
Discovered via `src/SmeAccounting.Domain/Entities/*.cs`:
- Core accounting: `Account`, `AccountGroup`, `JournalEntry`, `JournalEntryLine`, `PostingReference`, `PostingConfiguration`
- Period & fiscal: `FiscalYear`, `FiscalPeriod`
- Dimensions: `Department`, `CostCenter`, `Project`
- Currency & exchange: `Currency`, `ExchangeRate`
- Tax foundation: `TaxType`, `TaxTreatment`, `TaxAuthority`, `TaxRate`, `TaxRule`, `TaxExemptionReason`, `TaxAccountingMapping`, `TaxPeriod`
- Payment: `PaymentTerm`
- Company & settings: `Company`, `CompanySetting`
- Voucher & transaction control: `VoucherType`, `DocumentNumberingSeries`, `TransactionReason`
- Opening balances: `OpeningBalanceMapping`, `OpeningBalancePeriod`, `OpeningBalanceEntry`
- Base: `BaseEntity`

Additional entities present in Domain (non-General Accounting scope):
`User`, `Role`, `UserRole`, `CompanyMembership`, `Customer`, `Supplier`, `Employee`, `Uom`, `ItemCategory`, `Warehouse`, `UomConversion`, `Item`, `ServiceItem`, `InventoryValuationPolicy`, `InventoryAdjustmentReason`, `InventoryAccountingConfiguration`

### Domain Ports / Repository Interfaces
Discovered via `src/SmeAccounting.Domain/Ports/*.cs`:
`IAccountRepository`, `IJournalEntryRepository`, `IUnitOfWork`, `IForeignExchangeRateProvider`, `IAuditLogger`, `IPostingService`, `IClock`,
`ICompanyRepository`, `ICurrencyRepository`, `IExchangeRateRepository`, `IDepartmentRepository`, `ICostCenterRepository`, `IProjectRepository`,
`IPostingConfigurationRepository`, `IVoucherTypeRepository`, `IDocumentNumberingSeriesRepository`, `ITransactionReasonRepository`,
`ITaxTypeRepository`, `ITaxTreatmentRepository`, `ITaxAuthorityRepository`, `ITaxRateRepository`, `ITaxRuleRepository`, `ITaxExemptionReasonRepository`, `ITaxAccountingMappingRepository`, `ITaxPeriodRepository`,
`IPaymentTermRepository`,
`ICompanySettingRepository`, `IOpeningBalancePeriodRepository`, `IOpeningBalanceEntryRepository`, `IOpeningBalanceMappingRepository`,
`IUsersRepository`, `IRoleRepository`, `IUserRoleRepository`, `ICompanyMembershipRepository`,
`ICustomerRepository`, `ISupplierRepository`, `IEmployeeRepository`,
`IUomRepository`, `IUomConversionRepository`, `IItemCategoryRepository`, `IWarehouseRepository`, `IItemRepository`, `IServiceItemRepository`, `IInventoryValuationPolicyRepository`, `IInventoryAdjustmentReasonRepository`, `IInventoryAccountingConfigurationRepository`

### EF Core Configurations
Discovered via `src/SmeAccounting.Infrastructure/Persistence/Configurations/*.cs`:
`AccountConfiguration`, `AccountGroupConfiguration`, `JournalEntryConfiguration`, `JournalEntryLineConfiguration`, `PostingReferenceConfiguration`, `PostingConfigurationConfiguration`,
`FiscalYearConfiguration`, `FiscalPeriodConfiguration`,
`DepartmentConfiguration`, `CostCenterConfiguration`, `ProjectConfiguration`,
`CurrencyConfiguration`, `ExchangeRateConfiguration`,
`TaxTypeConfiguration`, `TaxTreatmentConfiguration`, `TaxAuthorityConfiguration`, `TaxRateConfiguration`, `TaxRuleConfiguration`, `TaxExemptionReasonConfiguration`, `TaxAccountingMappingConfiguration`, `TaxPeriodConfiguration`,
`PaymentTermConfiguration`,
`CompanyConfiguration`, `CompanySettingConfiguration`,
`VoucherTypeConfiguration`, `DocumentNumberingSeriesConfiguration`, `TransactionReasonConfiguration`,
`OpeningBalanceMappingConfiguration`, `OpeningBalancePeriodConfiguration`, `OpeningBalanceEntryConfiguration`,
`UserConfiguration`, `RoleConfiguration`, `UserRoleConfiguration`, `CompanyMembershipConfiguration`,
`CustomerConfiguration`, `SupplierConfiguration`, `EmployeeConfiguration`,
`UomConfiguration`, `UomConversionConfiguration`, `ItemCategoryConfiguration`, `WarehouseConfiguration`, `ItemConfiguration`, `ServiceItemConfiguration`, `InventoryValuationPolicyConfiguration`, `InventoryAdjustmentReasonConfiguration`, `InventoryAccountingConfigurationConfiguration`

Pattern: `IEntityTypeConfiguration<T>` with snake_case table names, `HasColumnName`, `HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict)`, composite unique index `(CompanyId, Code)`, enum `HasConversion<string>()`, `IsRowVersion()` on `xmin`.

### Architecture Constraints — NetArchTest Rules
22 tests in `tests/SmeAccounting.ArchitectureTests/`:

DependencyRulesTests (7):
- Domain should not depend on Application
- Domain should not depend on Infrastructure
- Domain should not depend on Api
- Application should not depend on Infrastructure
- Application should not depend on Api
- Infrastructure should not depend on Api
- Api Controllers should not depend on Infrastructure

DomainPurityTests (3):
- Domain should have no NuGet PackageReferences
- Domain should not reference Microsoft./Npgsql./Serilog./EFCore. packages
- Domain should not depend on Microsoft.EntityFrameworkCore

LayerCouplingTests (4):
- Controllers should not reference Domain.Entities namespace
- Controllers should not reference Domain.Ports namespace
- Application handlers should not reference Infrastructure namespace
- Infrastructure should not reference Api namespace

NamingConventionsTests (6):
- Entities inheriting BaseEntity should reside in Domain.Entities namespace
- Repository interfaces should start with I
- Commands in Commands namespace should end with Command
- Queries in Queries namespace should end with Query
- DTOs should end with Dto
- Controllers should end with Controller

PostingRuleIsolationTests (2):
- IPostingService should reside in Domain assembly
- JournalEntry balance rule enforceable in Domain

Additional constraints from project config:
- Clean Architecture dependency direction: Api → Application → Domain; Infrastructure → Application + Domain; Domain zero NuGet refs
- Controllers must never reference `SmeAccounting.Domain.Entities` or `SmeAccounting.Domain.Repositories`
- CQRS with MediatR, FluentValidation pipeline
- PostgreSQL snake-case naming, xmin concurrency tokens
- Company isolation via `CompanyId` FK Restrict + composite unique `(CompanyId, Code)`
- Enum storage as string, currency codes as string, soft delete via `IsActive`, effective dating `EffectiveFrom`/`EffectiveTo`

### Gaps for General Accounting
- Bank/BankBranch/BankAccount entities not present
- PostingReference implementation exists but Bank linkage missing
- PaymentTerm exists, no Bank integration

## Task-Specific Research — [G1] Discover missing Bank/BankBranch/BankAccount entities and verify PostingReference implementation gaps

**Bank/BankBranch/BankAccount absence**
- No domain entity found for Bank, BankBranch, BankAccount under src/SmeAccounting.Domain/Entities
- No EF Configuration found for Bank/BankBranch/BankAccount
- No repository port or implementation found
- No Application commands/queries/validators for Bank concepts
- Only BankExchangeRateProvider adapter exists under Infrastructure, no entity model
- Grep returns zero results for `BankAccount` / `BankBranch` entity definitions

**PostingReference implementation gaps**
- Entity exists at SmeAccounting.Domain/Entities/PostingReference.cs with Id, JournalEntryId, SourceType, SourceId. Private ctor + public ctor validates SourceType not null/empty.
- EF config PostingReferenceConfiguration maps to posting_references table, indexes on journal_entry_id and (source_type, source_id), xmin row version. No FK constraint to journal_entries, no CompanyId, no navigation.
- Migration 20260916051341_InitialCreate creates posting_references with columns id, journal_entry_id, source_type, source_id, xmin – no FK constraint to journal_entries.
- DbContext exposes DbSet<PostingReference> PostingReferences
- No repository interface/implementation for PostingReference
- No Application commands/queries/validators for PostingReference
- No domain events related to PostingReference
- JournalEntry has SourceType/SourceId properties and SetSource method but does not create/manage PostingReference
- No Company isolation, no soft-delete, no effective dating, SourceType as free string, no validation enum

**Naming collision risk**
- BankExchangeRateProvider name uses Bank prefix but is service provider, not entity.

## Task-Specific Research — [G1] Extract company isolation, effective dating, soft delete, enum storage patterns for implementation reference

### CompanyId FK Restrict pattern
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs`
  ```csharp
  builder.HasOne<Company>()
      .WithMany()
      .HasForeignKey(e => e.CompanyId)
      .OnDelete(DeleteBehavior.Restrict);
  ```
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` lines 64-67
  ```csharp
  builder.HasOne<Company>()
      .WithMany()
      .HasForeignKey(e => e.CompanyId)
      .OnDelete(DeleteBehavior.Restrict);
  ```
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/ExchangeRateConfiguration.cs` lines 49-52
  ```csharp
  builder.HasOne<Company>()
      .WithMany()
      .HasForeignKey(e => e.CompanyId)
      .OnDelete(DeleteBehavior.Restrict);
  ```
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRateConfiguration.cs` lines 49-52
  ```csharp
  builder.HasOne<Company>()
      .WithMany()
      .HasForeignKey(e => e.CompanyId)
      .OnDelete(DeleteBehavior.Restrict);
  ```
- Pattern universal across all company-scoped entities. Domain entities expose `public long CompanyId { get; private set; }` with validation `companyId <= 0` throws `DomainException`.

### Composite unique indexes (CompanyId, Code)
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs` lines 34-35
  ```csharp
  builder.HasIndex(e => new { e.CompanyId, e.Code })
      .IsUnique();
  ```
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/CostCenterConfiguration.cs` — same pattern
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/ProjectConfiguration.cs` — same pattern
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRateConfiguration.cs` lines 46-47
  ```csharp
  builder.HasIndex(e => new { e.CompanyId, e.TaxTypeId, e.RateValue, e.EffectiveFrom })
      .IsUnique();
  ```
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/ExchangeRateConfiguration.cs` lines 46-47
  ```csharp
  builder.HasIndex(e => new { e.CompanyId, e.FromCurrencyCode, e.ToCurrencyCode, e.RateType, e.EffectiveDate })
      .IsUnique();
  ```
- Enforces per-company uniqueness at DB level beyond application validation.

### Effective dating with EffectiveFrom/EffectiveTo
- **Domain entity:** `src/SmeAccounting.Domain/Entities/TaxRate.cs`
  ```csharp
  public DateOnly EffectiveFrom { get; private set; }
  public DateOnly? EffectiveTo { get; private set; }
  ```
- **Domain entity:** `src/SmeAccounting.Domain/Entities/TaxRule.cs` lines 16-17
  ```csharp
  public DateOnly EffectiveFrom { get; private set; }
  public DateOnly? EffectiveTo { get; private set; }
  ```
- **EF config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/TaxRateConfiguration.cs` lines 33-37
  ```csharp
  builder.Property(e => e.EffectiveFrom).HasColumnName("effective_from");
  builder.Property(e => e.EffectiveTo).HasColumnName("effective_to");
  ```
- Query pattern documented in MEMORY.md: `EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive`
- Nullable `EffectiveTo` means indefinite validity.

### IsActive soft delete pattern
- **Domain entity:** `src/SmeAccounting.Domain/Entities/Department.cs` lines 11, 15-29
  ```csharp
  public bool IsActive { get; private set; } = true;
  ```
- **Domain entity:** `src/SmeAccounting.Domain/Entities/TaxRate.cs` line 14
  ```csharp
  public bool IsActive { get; private set; } = true;
  public void Deactivate() { IsActive = false; }
  ```
- **EF config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs` lines 31-32
  ```csharp
  builder.Property(e => e.IsActive).HasColumnName("is_active");
  ```
- Soft delete only — `Account.Deprecate()` sets `IsActive=false`, never hard delete. Domain events raised on deactivation where applicable.

### Enum storage with HasConversion<string>()
- **Value object:** `src/SmeAccounting.Domain/ValueObjects/NormalBalance.cs`
  ```csharp
  public enum NormalBalance { Debit, Credit }
  ```
- **EF config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` lines 29-30, 45-47
  ```csharp
  builder.Property(e => e.AccountType).HasColumnName("account_type").HasConversion<string>();
  builder.Property(e => e.NormalBalance).HasColumnName("normal_balance").HasConversion<string>();
  ```
- **EF config:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/ExchangeRateConfiguration.cs` lines 35-37
  ```csharp
  builder.Property(e => e.RateType).HasColumnName("rate_type").HasConversion<string>();
  ```
- All enums stored as string via `HasConversion<string>()` — `AccountType`, `NormalBalance`, `PeriodType`, `PeriodStatus`, `ExchangeRateType`, `TaxCategory`, etc.

### xmin concurrency token
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs` lines 42-44
  ```csharp
  builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
  ```
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` lines 69-71
  ```csharp
  builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
  ```
- Present on all entities extending `BaseEntity`. PostgreSQL `xid` row version for optimistic concurrency.

### Snake_case naming
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs` lines 11, 18-19
  ```csharp
  builder.ToTable("departments");
  builder.Property(e => e.CompanyId).HasColumnName("company_id");
  ```
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/AccountConfiguration.cs` lines 12, 38-39
  ```csharp
  builder.ToTable("accounts");
  builder.Property(e => e.CompanyId).HasColumnName("company_id");
  ```
- `EFCore.NamingConventions` package enforces snake_case for tables/columns. All configurations use `ToTable(snake_plural)` and `HasColumnName(snake_case)`.

### SetNull for dimensions
- **File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/JournalEntryLineConfiguration.cs` lines 57-70
  ```csharp
  builder.HasOne<Department>()
      .WithMany()
      .HasForeignKey(e => e.DepartmentId)
      .OnDelete(DeleteBehavior.SetNull);
  builder.HasOne<CostCenter>()
      .WithMany()
      .HasForeignKey(e => e.CostCenterId)
      .OnDelete(DeleteBehavior.SetNull);
  builder.HasOne<Project>()
      .WithMany()
      .HasForeignKey(e => e.ProjectId)
      .OnDelete(DeleteBehavior.SetNull);
  ```
- Dimensions are optional on `JournalEntryLine`. Deleting dimension nulls FK, retains line data for audit.

### Domain validation patterns
- **File:** `src/SmeAccounting.Domain/Entities/Department.cs` lines 15-29
  ```csharp
  public Department(long companyId, string code, string name)
  {
      if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
      if (string.IsNullOrWhiteSpace(code)) throw new DomainException("Code is required.");
      if (string.IsNullOrWhiteSpace(name)) throw new DomainException("Name is required.");
      CompanyId = companyId;
      Code = code;
      Name = name;
      AddDomainEvent(new DepartmentCreated(Id, companyId, DateTimeOffset.UtcNow));
  }
  ```
- **File:** `src/SmeAccounting.Domain/Entities/TaxRate.cs` lines 19-46
  ```csharp
  if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");
  if (taxTypeId <= 0) throw new DomainException("TaxTypeId must be greater than zero.");
  if (rateValue < 0) throw new DomainException("RateValue must be greater than or equal to zero.");
  if (string.IsNullOrWhiteSpace(rateName)) throw new DomainException("RateName is required.");
  ```
- Private parameterless ctor for EF, public ctor with `DomainException` validation, domain events added on construction. No `ArgumentNullException` — domain exception hierarchy used.

## Task-Specific Research — [G2] Implement Bank aggregate with Domain entity, EF configuration, repository, Application commands/queries and FluentValidation using TDD

### Domain entity patterns
- **BaseEntity**: `src/SmeAccounting.Domain/Entities/BaseEntity.cs` — abstract class with `long Id`, `DomainEvents` collection, `AddDomainEvent`, private parameterless ctor for EF.
- **DomainException**: `src/SmeAccounting.Domain/Exceptions/DomainException.cs` — base exception for domain validation.
- **DomainEvent**: `src/SmeAccounting.Domain/Events/DomainEvent.cs` — abstract with `OccurredOn` and `EventId`.
- **Entity pattern example — Department**:
  - File: `src/SmeAccounting.Domain/Entities/Department.cs`
  - Properties: `long CompanyId { get; private set; }`, `string Code`, `string Name`, `bool IsActive = true`
  - Private parameterless ctor for EF
  - Public ctor validates `companyId <=0`, `code` non-empty, `name` non-empty → throws `DomainException`
  - Raises domain event `DepartmentCreated(Id, companyId, DateTimeOffset.UtcNow)` via `AddDomainEvent`
- **Domain event minimalism**: `DepartmentCreated` carries `DepartmentId`, `CompanyId`, `OccurredOn` only. Same pattern for `CostCenterCreated`, `ProjectCreated`, `VoucherTypeCreated`.
- **CompanyId validation**: `if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.");` universal.
- **IsActive soft delete**: `public bool IsActive { get; private set; } = true;` with `Deactivate()` method setting false. No hard delete.
- **Code uniqueness per company**: enforced via EF composite unique index `(CompanyId, Code)` and repository `GetByCodeAsync(code, companyId)`.
- **Constructors with DomainException**: all entities use private parameterless ctor + public ctor with validation, no `ArgumentNullException`.

### EF configuration patterns for company-scoped entities
- **Pattern file**: `src/SmeAccounting.Infrastructure/Persistence/Configurations/DepartmentConfiguration.cs`
- `builder.ToTable("departments")`
- `builder.HasKey(e => e.Id)`
- Properties mapped with `HasColumnName("company_id")`, `HasColumnName("code")`, `HasMaxLength(50/200)`, `IsRequired()`
- `builder.Property(e => e.IsActive).HasColumnName("is_active")`
- Composite unique index: `builder.HasIndex(e => new { e.CompanyId, e.Code }).IsUnique();`
- Company FK: `builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);`
- Concurrency token: `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");`
- Enum storage: `HasConversion<string>()` for enums.
- Snake-case naming via `EFCore.NamingConventions`.

### Repository pattern
- **Port interface example**: `src/SmeAccounting.Domain/Ports/IDepartmentRepository.cs`
  - `Task<Department?> GetByIdAsync(long id)`
  - `Task<Department?> GetByCodeAsync(string code, long companyId)`
  - `Task<IReadOnlyList<Department>> GetAllAsync()`
  - `Task AddAsync(Department department)`
- **Implementation example**: `src/SmeAccounting.Infrastructure/Repositories/EfDepartmentRepository.cs`
  - Inject `SmeAccountingDbContext`
  - `GetByIdAsync` uses `FirstOrDefaultAsync`
  - `GetByCodeAsync` filters by `Code` + `CompanyId`
  - `GetAllAsync` uses `AsNoTracking().OrderBy(...)`
  - `AddAsync` delegates to `_context.Departments.AddAsync`
- **DI registration**: `services.AddScoped<IDepartmentRepository, EfDepartmentRepository>();` in `Infrastructure/DependencyInjection.cs`

### Application command/query patterns
- **Command record**: `src/SmeAccounting.Application/Commands/CreateVoucherTypeCommand.cs`
  - `public record CreateVoucherTypeCommand(string Code, string Name, VoucherCategory VoucherCategory, long CompanyId, string? Description = null) : IRequest<CreateVoucherTypeResult>;`
  - Result record `CreateVoucherTypeResult(long Id)`
- **Handler**: `src/SmeAccounting.Application/Handlers/CreateVoucherTypeHandler.cs`
  - Primary constructor injection of repository + `IUnitOfWork`
  - Implements `IRequestHandler<CreateVoucherTypeCommand, CreateVoucherTypeResult>`
  - Creates domain entity via public ctor, `repository.AddAsync`, `unitOfWork.SaveChangesAsync`, returns Id
- **Query example**: `GetVoucherTypeQuery(long VoucherTypeId) : IRequest<VoucherTypeDto?>`
- **DTO**: records, no domain references, manual mapping in handler

### FluentValidation patterns
- **Validator example**: `src/SmeAccounting.Application/Validators/CreateVoucherTypeCommandValidator.cs`
  - `public class CreateVoucherTypeCommandValidator : AbstractValidator<CreateVoucherTypeCommand>`
  - Rules: `RuleFor(x => x.Code).NotEmpty().MaximumLength(20)`, `RuleFor(x => x.Name).NotEmpty().MaximumLength(200)`, `RuleFor(x => x.CompanyId).GreaterThan(0)`, `RuleFor(x => x.VoucherCategory).IsInEnum()`
- **Pipeline**: `ValidationBehavior<TRequest,TResponse>` runs validators before handler, throws `ValidationException`
- **Registration**: `AddValidatorsFromAssembly` in `AddApplication()` extension

### TDD notes for Bank aggregate
- Bank entity expected to follow same patterns as Department/VoucherType: CompanyId + Code + Name + IsActive, composite unique `(CompanyId, Code)`, domain event `BankCreated`, private parameterless ctor, public ctor with DomainException validation.
- EF config: table `banks`, columns `company_id`, `code`, `name`, `is_active`, `description`, xmin, unique index, FK Restrict.
- Repository port `IBankRepository` with `GetByIdAsync`, `GetByCodeAsync`, `GetAllByCompanyAsync`, `AddAsync`.
- Application: `CreateBankCommand`, `CreateBankCommandValidator`, `CreateBankHandler`, `GetBankQuery`, `GetBanksByCompanyQuery`, DTOs.
- Tests: domain unit tests for constructor validation, domain event raising, EF config tests, repository tests, handler tests with in-memory DB, validator tests.

## Task-Specific Research — [G2] Implement BankBranch and BankAccount domain entities with EF configurations, repositories and Application layer with TDD

### Existing Bank aggregate implementation
- **Domain entity**: `src/SmeAccounting.Domain/Entities/Bank.cs`
  - Extends `BaseEntity`, properties: `CompanyId`, `Code`, `Name`, `IsActive` default true, `Description?`
  - Private parameterless ctor for EF, public ctor validates `companyId>0`, `code` non-empty, `name` non-empty via `DomainException`
  - Raises `BankCreated(Id, companyId, DateTimeOffset.UtcNow)` via `AddDomainEvent`
  - `Deactivate()` sets `IsActive=false`
- **Domain event**: `src/SmeAccounting.Domain/Events/BankCreated.cs` carries `BankId`, `CompanyId`, `OccurredOn` — minimalism pattern
- **EF configuration**: `src/SmeAccounting.Infrastructure/Persistence/Configurations/BankConfiguration.cs`
  - `ToTable("banks")`, `HasKey(Id)`, snake_case columns `company_id`, `code` max 50, `name` max 200, `is_active`, `description` max 500
  - Composite unique index `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()`
  - FK `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
  - Concurrency `Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`
- **Repository port**: `src/SmeAccounting.Domain/Ports/IBankRepository.cs`
  - `GetByIdAsync`, `GetByCodeAsync(code, companyId)`, `GetAllByCompanyAsync(companyId)`, `AddAsync`
- **Repository impl**: `src/SmeAccounting.Infrastructure/Repositories/EfBankRepository.cs` uses `SmeAccountingDbContext`, `FirstOrDefaultAsync`, `AsNoTracking().Where(...).OrderBy(Code)`
- **DbContext**: `DbSet<Bank> Banks` registered
- **Application patterns already used**: CreateBankCommand + validator + handler, GetBank/GetBanksByCompany queries + DTOs, FluentValidation pipeline, MediatR handlers

### Hierarchical relationship patterns in codebase
- **Self-referencing hierarchy**: `Account` entity
  - `ParentId` nullable long, `Level` int, `Children` collection
  - EF config `AccountConfiguration.cs`:
    - `HasOne<Account>().WithMany(a => a.Children).HasForeignKey(e => e.ParentId).OnDelete(DeleteBehavior.Restrict)`
    - Index on `ParentId`
  - `AddChild` method creates child with `Level+1` and `ParentId = Id`
  - DeleteBehavior.Restrict prevents cascade delete loops and circular cascade paths
- **Parent-child via FK**: `TransactionReason`
  - Properties `CompanyId`, `VoucherTypeId`, `Code`, `Name`, `IsActive`, `Description`
  - EF config `TransactionReasonConfiguration.cs`:
    - FK to Company `OnDelete(Restrict)`
    - FK to VoucherType `OnDelete(Restrict)`
    - Unique index `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()` — uniqueness scoped per company, not per parent
  - Domain event `TransactionReasonCreated(Id, companyId, ...)` minimal
- **Optional dimension FKs with SetNull**: `JournalEntryLineConfiguration.cs`
  - `DepartmentId`, `CostCenterId`, `ProjectId` nullable
  - `HasOne<Department>().WithMany().HasForeignKey(e => e.DepartmentId).OnDelete(DeleteBehavior.SetNull)`
  - Same for CostCenter/Project — deleting dimension nulls FK, retains line for audit
- **Circular reference prevention**
  - Self-referencing FK uses `Restrict` not `Cascade`
  - No navigation back from parent to children in domain entities except `Account.Children` read-only collection
  - Domain events minimal, no bidirectional event propagation

### Department / CostCenter / Project patterns for reference
- **Entity shape**: `Department`, `CostCenter`, `Project` all follow same template
  - `CompanyId`, `Code` max 50, `Name` max 200, `IsActive` default true
  - `Project` adds `StartDate`/`EndDate` nullable `DateOnly` for effective dating
  - Private parameterless ctor, public ctor validates `companyId>0`, code/name non-empty via `DomainException`
  - Domain event `DepartmentCreated(Id, companyId, OccurredOn)` etc.
  - `Deactivate()` sets `IsActive=false`
- **EF configuration**: `DepartmentConfiguration.cs`, `CostCenterConfiguration.cs`, `ProjectConfiguration.cs`
  - `ToTable("departments"/"cost_centers"/"projects")`
  - Columns snake_case, `HasMaxLength(50/200)`, `IsRequired`
  - Composite unique `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()`
  - FK `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(Restrict)`
  - `xmin` row version
- **Repository ports**: `IDepartmentRepository`, `ICostCenterRepository`, `IProjectRepository`
  - `GetByIdAsync`, `GetByCodeAsync(code, companyId)`, `GetAllAsync` / `GetAllByCompanyAsync`, `AddAsync`
- **Application**: Commands/queries with FluentValidation, DTOs, MediatR handlers

### Company isolation, composite unique indexes, effective dating, soft delete
- **Company isolation**
  - Universal pattern: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
  - Domain validation `if (companyId <= 0) throw new DomainException("CompanyId must be greater than zero.")`
  - No navigation property to Company on entity — FK only
- **Composite unique indexes**
  - `(CompanyId, Code)` for Bank, Department, CostCenter, Project, VoucherType, TransactionReason, PaymentTerm, TaxType, etc.
  - `(CompanyId, BankId, Code)` expected for BankBranch to ensure code uniqueness per bank per company
  - `(CompanyId, BankBranchId, Code)` or `(CompanyId, BankId, BranchCode, AccountCode)` for BankAccount
  - Examples: `TaxRateConfiguration` `HasIndex(e => new { e.CompanyId, e.TaxTypeId, e.RateValue, e.EffectiveFrom }).IsUnique()`
  - `ExchangeRateConfiguration` `HasIndex(e => new { e.CompanyId, e.FromCurrencyCode, e.ToCurrencyCode, e.RateType, e.EffectiveDate }).IsUnique()`
- **Effective dating**
  - Pattern: `DateOnly EffectiveFrom` required, `DateOnly? EffectiveTo` nullable = indefinite
  - Entities: `TaxRate`, `TaxRule`, `ExchangeRate`, `Project.StartDate/EndDate`
  - Query pattern documented: `EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive`
  - EF mapping: `builder.Property(e => e.EffectiveFrom).HasColumnName("effective_from")`, same for `EffectiveTo`
- **Soft delete**
  - `bool IsActive { get; private set; } = true`
  - `Deactivate()` method sets false, no hard delete
  - EF column `is_active`
  - Account uses `Deprecate()` naming variant
- **Enum storage**
  - All enums stored as string via `HasConversion<string>()`
  - Enums live in `Domain/ValueObjects/`
- **Concurrency & naming**
  - `Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")` on all entities
  - Snake_case table/column via `EFCore.NamingConventions`
  - Private parameterless ctor for EF, public ctor with `DomainException`

### Implications for BankBranch and BankAccount
- **BankBranch** expected shape:
  - `CompanyId`, `BankId`, `Code`, `Name`, `IsActive`, `Description?`, optional `BranchNumber`, `Address`
  - FK to Company Restrict, FK to Bank Restrict
  - Composite unique `(CompanyId, BankId, Code)` — code unique per bank per company
  - Domain event `BankBranchCreated(BranchId, CompanyId, OccurredOn)`
  - Repository `IBankBranchRepository` with `GetByIdAsync`, `GetByCodeAsync(code, bankId, companyId)`, `GetAllByBankAsync(bankId)`, `AddAsync`
- **BankAccount** expected shape:
  - `CompanyId`, `BankId`, `BankBranchId?`, `Code`, `AccountNumber`, `AccountName`, `IsActive`, `Description?`, optional `CurrencyCode` string
  - FK to Company Restrict, FK to Bank Restrict, FK to BankBranch Restrict (nullable or required)
  - Composite unique `(CompanyId, BankId, BankBranchId, Code)` or `(CompanyId, AccountNumber)` depending on business rule
  - Domain event `BankAccountCreated(AccountId, CompanyId, OccurredOn)`
  - Repository `IBankAccountRepository` with similar methods
- **Hierarchical delete behavior**
  - Bank → BankBranch → BankAccount chain should use `DeleteBehavior.Restrict` to prevent accidental cascade delete of financial data
  - Optional SetNull for BankBranchId if branch deletion allowed but accounts retained
- **TDD approach**
  - Follow existing Bank aggregate TDD: domain unit tests for constructor validation, domain event raising, Deactivate
  - EF configuration tests for table/columns/indexes/FKs
  - Repository tests with in-memory DB
  - Application command/query tests with FluentValidation
  - Architecture tests must remain 22/22 passing

## Task-Specific Research — [G3] verification and architecture compliance

All findings verified from local source files (no web search needed — task fully answerable from repo).

### Exact verification commands
- Build: `dotnet build SmeAccounting.sln` from repo root. `Directory.Build.props` sets `TreatWarningsAsErrors=true`, net10.0, C#13, nullable+implicit usings. Bar: 0 warnings 0 errors (warnings fail build).
- Architecture tests: `dotnet test tests/SmeAccounting.ArchitectureTests/` (xunit 2.9.3 + NetArchTest.Rules 1.3.2). Bar: 22/22 pass.
- 22 rule breakdown (verified from test sources):
  - `DependencyRulesTests.cs` (7): Domain→not→Application/Infrastructure/Api; Application→not→Infrastructure/Api; Infrastructure→not→Api; Api Controllers→not→Infrastructure.
  - `DomainPurityTests.cs` (3): Domain csproj has zero `PackageReference` (verified: `src/SmeAccounting.Domain/SmeAccounting.Domain.csproj` is empty SDK project); no Microsoft./Npgsql./Serilog./EFCore. package prefixes; no `Microsoft.EntityFrameworkCore` assembly dependency.
  - `LayerCouplingTests.cs` (4): Controllers→not→`Domain.Entities`; Controllers→not→`Domain.Ports`; Application `IRequestHandler<,>`→not→Infrastructure; Infrastructure→not→Api.
  - `NamingConventionsTests.cs` (6): BaseEntity heirs reside in `Domain.Entities`; `*Repository` interfaces start with `I`; `Application.Commands` IRequest types end `Command`; `Application.Queries` classes end `Query`; `Application.DTOs` types end `Dto`; `Api.Controllers` classes end `Controller`.
  - `PostingRuleIsolationTests.cs` (2): `IPostingService` in Domain assembly; JournalEntry/Money/IPostingService all in Domain assembly.

### Bank wiring — already present, executor only verifies (no edits expected)
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` lines 46-48: `DbSet<Bank> Banks`, `DbSet<BankBranch> BankBranches`, `DbSet<BankAccount> BankAccounts`; lines 105-107: `modelBuilder.Ignore<BankCreated/BankBranchCreated/BankAccountCreated>()`.
- `src/SmeAccounting.Infrastructure/DependencyInjection.cs` lines 65-67: `AddScoped<IBankRepository, EfBankRepository>`, `IBankBranchRepository`, `IBankAccountRepository`.
- Application DI (`src/SmeAccounting.Application/DependencyInjection.cs`): assembly-wide MediatR scan + open `ValidationBehavior<,>` + `AddValidatorsFromAssembly` — Bank handlers/validators auto-registered, nothing Bank-specific to add.
- Application files exist: `Application/Banks|BankBranches|BankAccounts/{Commands,Queries,DTOs}/` — Create*Command/Handler/Validator, Get*ById + Get*ByCompany/Bank queries+handlers, *Dto records.
- No Bank controller in Api (grep `Bank` under `src/SmeAccounting.Api` returns zero hits) — controller-thinness rule trivially satisfied for Bank; do NOT create a controller in G3 (out of scope).

### Controller-thinness rule detail
- Banned: `SmeAccounting.Domain.Entities`, `SmeAccounting.Domain.Ports` (LayerCouplingTests). Allowed precedent: `PaymentTermController.cs` imports `SmeAccounting.Domain.ValueObjects` (enum parse) + `Application.Commands/Queries` + ViewModels, dispatches via `IMediator` only. Bank verification: confirm no `using SmeAccounting.Domain.Entities|Ports` in any controller.

### Naming-rule nuance for Bank files
- Bank commands live in `SmeAccounting.Application.Banks.Commands` (nested), while the arch rule scopes `ResideInNamespace("SmeAccounting.Application.Commands")` — nested Bank namespaces fall outside that selector, so rule does not directly assert on them (consistent with 22/22 passing today). Executor still follows convention: `CreateBankCommand`/`CreateBankResult`, `*Query`, `*Dto`, ports named `I*Repository`.

### Integration-test landscape for executor
- Only test project in repo: `tests/SmeAccounting.ArchitectureTests` (xunit, refs all 4 src projects). No integration/unit test project exists.
- `Microsoft.EntityFrameworkCore.InMemory` is NOT referenced anywhere — options: (a) add xunit test classes inside ArchitectureTests project (zero new projects, but mixes concerns), (b) create new `tests/SmeAccounting.BankTests/` xunit project referencing Application+Infrastructure (cleaner; copy csproj pattern from ArchitectureTests + add `Microsoft.EntityFrameworkCore.InMemory` matching EF Core 10.0.4). Prefer (b); adding InMemory to a *test* project does not affect Domain purity rules.
- Minimal test scope (keep small, deterministic, no live Postgres needed): domain ctor validation (DomainException on bad CompanyId/empty Code/Name), `Deactivate()` sets IsActive=false, `BankCreated` event raised with CompanyId; validator rejects empty Code; handler round-trip via InMemory DbContext (create Bank → GetById returns DTO); unique-index smoke test optional (InMemory does not enforce indexes — note as limitation, do not assert uniqueness on InMemory).
- Gotchas: `TreatWarningsAsErrors` applies to new test project too — no unused vars (CS0219), no missing usings; xunit `Fact` attribute via `Using Include="Xunit"` in csproj pattern; EF InMemory version must match EF Core 10.0.4 major.

## Task-Specific Research — [G3] minimal integration tests

All findings verified from local source files 2026-09-22 (no web search needed — repo sources decisive).

### Does a Bank test project exist? No
- `tests/` contains exactly one project: `tests/SmeAccounting.ArchitectureTests/` (xunit only). No `*BankTests*`, `*DomainTests*`, `*IntegrationTests*` anywhere (glob + grep zero hits).
- Only test framework in repo: **xunit 2.9.3** (+ `xunit.runner.visualstudio` 3.1.4, `Microsoft.NET.Test.Sdk` 17.14.1, `coverlet.collector` 6.0.4). No MSTest/NUnit refs anywhere.
- EF test strategy in repo: **none established**. `Microsoft.EntityFrameworkCore.InMemory`, Testcontainers, WebApplicationFactory: zero references in any csproj/src/tests. (Testcontainers appears only as an unimplemented proposal in `loop-stack/vietnamese-acct-architecture_DONE/RESEARCH.md` — not adopted.)
- Live PostgreSQL exists (`Host=172.21.208.1`) but no test uses it; Bank tests must NOT need live Postgres (deterministic, offline).

### ArchitectureTests csproj pattern (exact template to copy)
- File `tests/SmeAccounting.ArchitectureTests/SmeAccounting.ArchitectureTests.csproj`: SDK `Microsoft.NET.Sdk`, `<IsPackable>false</IsPackable>`, framework/lang/nullability/warnings inherited from root `Directory.Build.props` (net10.0, C#13, nullable+implicit usings, `TreatWarningsAsErrors=true`).
- Package refs: coverlet.collector 6.0.4, Microsoft.NET.Test.Sdk 17.14.1, xunit 2.9.3, xunit.runner.visualstudio 3.1.4, NetArchTest.Rules 1.3.2 (BankTests copies all except NetArchTest — not needed).
- `<Using Include="Xunit" />` gives global `Fact`/`Assert` without per-file usings.
- ProjectRefs use `GeneratePathProperty="true"` (needed only for DomainPurityTests csproj-path checks — BankTests does NOT need it; plain ProjectReference suffices).
- Solution `SmeAccounting.sln` nests test projects under `tests` solution folder — executor must `dotnet sln add tests/SmeAccounting.BankTests/` (else build/test still works per-project but solution-wide `dotnet build`/`test` skips it).

### Why a new test project is arch-safe
- All 22 arch rules scan **src assemblies by type** (`typeof(Account).Assembly`, etc.), never the tests folder — a new test project is invisible to them. Verified in `NamingConventionsTests.cs`: command/query/DTO rules scope to `SmeAccounting.Application.Commands/Queries/DTOs` namespaces (Bank commands live in nested `Application.Banks.Commands` etc., outside those selectors).
- `DomainPurityTests` asserts on `SmeAccounting.Domain.csproj` (verified: empty SDK project, zero `PackageReference`) — adding packages to a *test* project cannot break it. Rule: NEVER add a PackageReference to Domain.
- New test project may reference Domain+Application (+Infrastructure only if doing InMemory EF round-trip); that direction (tests→src) is unrestricted.

### Testability hooks already present (no src edits needed)
- `SmeAccountingDbContext(DbContextOptions<SmeAccountingDbContext> options)` (line 56) — options-ctor, so `UseInMemoryDatabase` works if chosen. Implements `IUnitOfWork` (`SaveChangesAsync` via base DbContext).
- `BaseEntity.DomainEvents` is `IReadOnlyCollection<DomainEvent>` — assert via `bank.DomainEvents.OfType<BankCreated>().Single()`.
- `IBankRepository` (and Branch/Account equivalents): 4-method shape `GetByIdAsync / GetByCodeAsync(code, companyId) / GetAllByCompanyAsync / AddAsync` — trivial to hand-fake with a `List<T>`.
- Handlers are `internal sealed` with primary-ctor `(IBankRepository, IUnitOfWork)` — reachable from tests via `InternalsVisibleTo` ONLY if needed; simpler: test handlers through hand fakes in same assembly? No — handlers internal means external test project CANNOT instantiate directly. Options: (a) test via public API only (domain ctors + validators, no handler test), (b) add `InternalsVisibleTo("SmeAccounting.BankTests")` to Application csproj, (c) full MediatR `Send()` via service collection (needs DI wiring). Recommend (b): one-line `AssemblyAttribute` in Application (`[assembly: InternalsVisibleTo("SmeAccounting.BankTests")]` in e.g. `Properties/AssemblyInfo.cs` or csproj `<InternalsVisibleTo>`), minimal and precedented. If executor wants zero src edits, fall back to (a).
- Exact ctor signatures: `Bank(companyId, code, name, description?)`; `BankBranch(companyId, bankId, code, name, description?)`; `BankAccount(companyId, bankId, code, accountNumber, accountName, bankBranchId?, description?, currencyCode?)`. All throw `DomainException` on `companyId<=0` / empty code/name (+`bankId<=0`, empty accountNumber/accountName for leaf). `Deactivate()` sets `IsActive=false` (no event). Events `BankCreated(BankId, CompanyId, OccurredOn)` (+Branch/Account variants) with provisional `Id=0` at construction — assert `CompanyId`, NOT `Id>0`.
- Validators: `CreateBankCommandValidator` etc. (`AbstractValidator<T>`) — test via `validator.Validate(cmd).IsValid` / `ValidateAndThrow`; pass case `(1, "VCB", "Vietcombank")`, fail cases empty Code, empty Name, `CompanyId=0`, Code>50 chars, Name>200 chars.

### Recommendation: hand fakes first, InMemory optional (do NOT invent infra)
- Preferred minimal: new `tests/SmeAccounting.BankTests/` xunit project copying ArchitectureTests csproj (minus NetArchTest), refs to Domain + Application only, **zero new NuGet packages**. Handler happy path via hand-fake `FakeBankRepository : IBankRepository` (List-backed) + `FakeUnitOfWork : IUnitOfWork` (SavedChanges counter). Covers: domain ctor validation + Deactivate + event, validator pass/fail, handler round-trip (Send command via handler instance → fake repo contains entity, SaveChanges called once, returned Id matches).
- Add `Microsoft.EntityFrameworkCore.InMemory` **10.0.4** (must match `Microsoft.EntityFrameworkCore` 10.0.4 in Infrastructure.csproj) ONLY if executor wants true EF round-trip (real `EfBankRepository` + `SmeAccountingDbContext` on InMemory). Cost: new package download (nuget.org enabled), project must then also ref Infrastructure. InMemory limitations to document in test comments, never assert: unique indexes NOT enforced, FK Restrict NOT enforced, `xmin` row-version NOT enforced, snake_case naming NOT verifiable. EF config aspects (tables `banks`/`bank_branches`/`bank_accounts`, composite uniques, Restrict, xmin) are verified by build + code review, not by InMemory asserts.
- Minimal viable surface (~10 Facts, one file per aggregate or single `BankAggregateTests.cs`): Bank ctor valid + event CompanyId; Bank ctor throws on `companyId=0` / empty code / empty name; `Deactivate()` flips IsActive; same 3 for Branch (plus `bankId=0` throws) and Account (plus empty accountNumber/accountName throws); validator valid + invalid; handler happy path with fakes (1 test on Bank suffices, replicate only if cheap).
- Gotchas: `TreatWarningsAsErrors` inherits — no unused vars, no nullable warnings (use `string.Empty` not null where non-nullable); xunit `Assert.Throws<DomainException>` needs `using SmeAccounting.Domain.Exceptions`; collection file-scoped namespaces match src style; `dotnet test tests/SmeAccounting.BankTests/` is the verify command; arch tests must stay 22/22 after (`dotnet test tests/SmeAccounting.ArchitectureTests/`).


