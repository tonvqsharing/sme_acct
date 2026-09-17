# Research Log
## Environment & Integration
**Build & SDK**
- .NET SDK 10.0.401, ASP.NET Core Runtime 10.0.12, .NET Runtime 10.0.12 per TOOLS.md
- Solution `SmeAccounting.sln` classic format, Visual Studio 17, projects: SmeAccounting.Domain, SmeAccounting.Application, SmeAccounting.Infrastructure, SmeAccounting.Api, SmeAccounting.ArchitectureTests
- `Directory.Build.props` at repo root:
  - `<TargetFramework>net10.0</TargetFramework>`
  - `<Nullable>enable</Nullable>`
  - `<ImplicitUsings>enable</ImplicitUsings>`
  - `<LangVersion>13</LangVersion>`
  - `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`
- `.editorconfig` at repo root:
  - `[*]` indent_style space, indent_size 4, end_of_line lf, charset utf-8, trim_trailing_whitespace true, insert_final_newline true
  - `*.{csproj,props,targets,config,nuspec}` indent_size 2
  - `*.{json,yml,yaml}` indent_size 2
  - `*.md` trim_trailing_whitespace false
  - C# rules: qualification false warning, prefer auto-properties, var suggestions, expression-bodied members, Allman braces, private fields `_camelCase` naming rule
- `SmeAccounting.Domain.csproj` empty SDK project, zero NuGet refs
- `SmeAccounting.Application.csproj` references Domain; packages MediatR 14.2.0, FluentValidation 12.1.0, FluentValidation.DependencyInjectionExtensions 12.1.0
- `SmeAccounting.Infrastructure.csproj` references Application + Domain; packages Microsoft.EntityFrameworkCore 10.0.4, Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3, Microsoft.Extensions.DependencyInjection 10.0.12, EFCore.NamingConventions 10.0.*
- `SmeAccounting.Api.csproj` SDK Web; references Application + Infrastructure; packages FluentValidation 12.1.0, MediatR 14.2.0, Microsoft.EntityFrameworkCore.Design 10.0.12, Swashbuckle.AspNetCore 10.2.3

**CI/CD & Infrastructure**
- No `.github/workflows/` directory found
- No `Dockerfile`, `docker-compose*` files found
- No build scripts `*.sh` found
- Docker not installed per TOOLS.md: `docker` — not installed
- No `.env.example` found

**Database & Connection**
- `src/SmeAccounting.Api/appsettings.json`:
  - `ConnectionStrings.DefaultConnection` = `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`
- PostgreSQL 16.14 via EF Core on Windows host `172.21.208.1`
- EF Core naming conventions: snake_case tables/columns, `xmin` concurrency tokens
- `appsettings.Development.json` adds `DetailedErrors:true`

**Build & Test Execution**
- Build: `dotnet build SmeAccounting.sln` — TreatWarningsAsErrors=true enforced
- Tests: `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22 NetArchTest rules
- Run: `dotnet run --project src/SmeAccounting.Api/` — Swagger at `/swagger` in dev
- EF Core migrations:
  - `dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
  - `dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- `psql` access: `PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev`

**Observations**
- CI/CD pipeline not present; build relies on local `dotnet` commands
- No containerization artifacts; infrastructure is host PostgreSQL
- Nullable enabled, warnings-as-errors, C# 13 enforced globally via Directory.Build.props
- Architecture constraints enforced by NetArchTest, not by CI

## Context & Prior Work
**Project structure**
- Solution: `SmeAccounting.sln` with projects:
  - `src/SmeAccounting.Domain` (pure library, zero NuGet refs)
  - `src/SmeAccounting.Application` (MediatR 14.2.0, FluentValidation 12.1.0)
  - `src/SmeAccounting.Infrastructure` (EF Core 10.0.4, Npgsql 10.0.3, EFCore.NamingConventions)
  - `src/SmeAccounting.Api` (ASP.NET MVC, Swashbuckle 10.2.3)
  - `tests/SmeAccounting.ArchitectureTests` (NetArchTest.Rules 1.3.2)

**Clean Architecture enforcement**
- Dependency direction: Api → Application → Domain; Infrastructure → Application + Domain; Domain zero NuGet.
- 22 NetArchTest rules enforce constraints.
- Controllers must not reference Domain.Entities or Domain.Repositories.
- CQRS with MediatR, FluentValidation pipeline behavior, DTOs as records.

**Domain layer layout**
- `Domain/Entities/`: BaseEntity, Account, AccountGroup, JournalEntry, JournalEntryLine, FiscalYear, FiscalPeriod, PostingReference, Company, Currency, ExchangeRate, Department, CostCenter, Project, VoucherType, DocumentNumberingSeries, TransactionReason, OpeningBalanceMapping, PostingConfiguration, TaxType, TaxTreatment, TaxAuthority, TaxRate, TaxRule, TaxExemptionReason, TaxPeriod, TaxAccountingMapping
- `Domain/ValueObjects/`: Money, AccountCode, AccountType, NormalBalance, PeriodType, PeriodStatus, FiscalYearStatus, ExchangeRateType, Currency, FilingFrequency, TaxPeriodStatus, TaxCategory, TaxTreatmentType, TaxAuthorityLevel, TaxAccountingMappingType, VoucherCategory
- `Domain/Ports/`: IAccountRepository, IJournalEntryRepository, IUnitOfWork, IForeignExchangeRateProvider, IAuditLogger, IPostingService, IClock, ICompanyRepository, ICurrencyRepository, IDepartmentRepository, ICostCenterRepository, IProjectRepository, IVoucherTypeRepository, IDocumentNumberingSeriesRepository, ITransactionReasonRepository, ITaxTypeRepository, ITaxTreatmentRepository, ITaxAuthorityRepository, ITaxRateRepository, ITaxRuleRepository, ITaxExemptionReasonRepository, ITaxPeriodRepository, ITaxAccountingMappingRepository, IOpeningBalanceMappingRepository, IPostingConfigurationRepository
- `Domain/Events/`: DomainEvent base, entity-specific Created/Posted/Closed events
- `Domain/Exceptions/`: DomainException hierarchy

**Infrastructure layout**
- `Persistence/Configurations/`: one `*Configuration.cs` per entity, snake-case tables, xmin concurrency, enum string conversion, FK to Company with DeleteBehavior.Restrict, composite unique indexes on (CompanyId, Code)
- `Repositories/`: Ef*Repository per entity, async CRUD
- `Migrations/`: 5 migrations
  - 20260916051341_InitialCreate
  - 20260916051520_FixAccountNameColumn
  - 20260916083803_AccountingFoundation
  - 20260917013843_Phase2AccountingControlConfig
  - 20260917045015_Phase3TaxFoundation
- `Adapters/`, `Services/`

**Application layout**
- `Commands/`, `Queries/`, `Handlers/`, `DTOs/`, `Validators/`, `Behaviors/ValidationBehavior`, `Services/`

**Api layout**
- `Controllers/`, `Views/`, `ViewModels/`, `wwwroot/`

**Package files**
- Domain.csproj empty SDK project
- Application.csproj references Domain, MediatR 14.2.0, FluentValidation 12.1.0, FluentValidation.DependencyInjectionExtensions 12.1.0
- Infrastructure.csproj references Application + Domain, EF Core 10.0.4, Npgsql 10.0.3, Microsoft.Extensions.DependencyInjection 10.0.12, EFCore.NamingConventions 10.0.*
- Api.csproj references Application + Infrastructure, FluentValidation 12.1.0, MediatR 14.2.0, EF Core Design 10.0.12, Swashbuckle.AspNetCore 10.2.3

**Existing tests**
- ArchitectureTests only: DependencyRulesTests, LayerCouplingTests, DomainPurityTests, NamingConventionsTests, PostingRuleIsolationTests
- No unit/integration tests for business logic yet.

**Business Partner related code**
- No existing Customer/Supplier/Employee/BusinessPartner entities, ports, repositories, commands, or configurations found in src/.
- Phase 4 plan references building master-data domain contracts for customers, suppliers, employees, payment/credit terms with accounting/tax integration.
- Global memory indicates Phase 1-3 covered accounting foundation, control config, tax foundation. No Business Partner models present.

**Patterns to follow**
- Entity pattern: CompanyId + Code + Name + IsActive + optional Description, private parameterless ctor for EF, public ctor with validation, DomainException hierarchy
- EF config pattern: ToTable(snake_plural), HasKey, HasColumnName, HasConversion<string>() for enums, HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict), composite unique index (CompanyId, Code), xmin row version
- Repository pattern: tracked GetById/GetByCode, AsNoTracking for GetAll, AddAsync delegates to DbSet
- Event pattern: {Entity}Created(EntityId, CompanyId, occurredOn)
- FK to Company pattern universal across entities
- Enum storage as string
- String over FK for currency codes

## External Knowledge & Resources
**Project documentation**
- No `README.md` at repo root. Project documentation lives under `docs/architecture/` and loop-stack historical docs.
- `src/SmeAccounting.Api/appsettings.json`:
  - ConnectionStrings.DefaultConnection = `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`
  - Logging LogLevel Default Information, Microsoft.AspNetCore Warning
  - AllowedHosts *
- `.editorconfig` at repo root:
  - `[*]` indent_style space, indent_size 4, end_of_line lf, charset utf-8, trim_trailing_whitespace true, insert_final_newline true
  - `*.{csproj,props,targets,config,nuspec}` indent_size 2
  - `*.{json,yml,yaml}` indent_size 2
  - `*.md` trim_trailing_whitespace false
  - C# style rules: qualification false warning, prefer auto-properties, var suggestions, expression-bodied members, Allman braces, private fields `_camelCase` naming rule
- No `.env.example` found in repo.

**Architecture & regulatory docs**
- `docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md` — Phase 3 tax foundation traceability to Circular 99/2025/TT-BTC, Law 48/2024/QH15 VAT, Law 67/2025/QH15 CIT, Law 109/2025/QH15 PIT. Maps TaxAccountingMapping to COA per Circular 99 Art 28: accounts 1331/1332 input VAT, 33311 output VAT, 33312 import VAT, 3331 VAT payable, 3334 CIT payable, 3335 PIT payable.
- Historical architecture docs in `loop-stack/vietnamese-acct-architecture_DONE/docs/regulatory/`:
  - `Circular99-mapping.md` — Circular 99/2025/TT-BTC issued 27 Oct 2025 effective 01 Jan 2026, replaces Circular 200/2014/TT-BTC. Article 28 software requirements mapped to Domain/Application/Infrastructure layers: Art 28(a) posting compliance → PostingService; Art 28(c) immutability/audit → JournalEntry.IsPosted + IAuditLogger; Art 28(d) reporting → IAccountingReportService; Art 28(dd) e-invoice integration → IEInvoiceProvider; Art 28(e) extensibility → Account lifecycle. Chart of Accounts changes: eliminated 161,441,611,631; added 215 Biological Assets, 332 Dividends Payable, 82112 GMT Top-Up Tax, 246 Long-term prepaid expenses, 351 Provision for obligations, 137 Accrued revenue; renamed 112 to Demand deposits.
  - `ChartOfAccounts-structure.md` — Circular 99 Appendix II defines COA. 9 categories, 4-digit Level 1 hierarchy, enterprise may supplement/modify per Art 25 with internal accounting policy. Software implications: dynamic account creation, deprecation not deletion, code validation, parent-child hierarchy.
  - `VAS-compliance.md` — 26 VAS issued 2001-2005. Mapping table with IAS/IFRS equivalents, applicability Core/Medium/Low/N/A, domain modules. Core standards: VAS 01 Framework & presentation, VAS 02 Inventories, VAS 03 Tangible Fixed Assets, VAS 04 Intangible Fixed Assets, VAS 06 Leases, VAS 10 FX, VAS 14 Revenue, VAS 17 Income Taxes, VAS 21 Presentation, VAS 24 Cash Flow, VAS 29 Policy changes. Traceability matrix to architecture components.
  - `EInvoice-integration.md`, `IFRS-transition-roadmap.md` also present.

**Regulatory identification**
- **Circular 99/2025/TT-BTC** — Thông tư số 99/2025/TT-BTC hướng dẫn Chế độ kế toán doanh nghiệp. Effective 01/01/2026. Primary enterprise accounting regime. Art 28 software requirements, Art 11 Chart of Accounts, Art 25 account modification, Art 4-6 currency, Art 12 books, Art 17 financial statements.
- **Vietnamese Accounting Standards (VAS)** — 26 standards, rules-based, prescribed COA, historical cost. Core for SME accounting. Documented in VAS-compliance.md with traceability to domain.
- **Tax legislation referenced**: Law 48/2024/QH15 VAT effective 01/07/2025, Law 67/2025/QH15 CIT effective 01/10/2025, Law 109/2025/QH15 PIT effective 01/07/2026. Circular 99 Art 28 maps to tax accounts.
- **External legal sources noted in TOOLS.md**: congbao.chinhphu.vn, thuvienphapluat.vn, luatvietnam.vn, vanban123.vn. Tax reference sources: PwC, Vietnam Briefing, EY, MISA SME Accounting.
- No external API configs or `.env.example` discovered; connection string hard-coded in appsettings.json.
## Requirements & Constraints

### DB Schema & Naming Conventions
- **PostgreSQL with EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions**
- Table names: snake_case plural, e.g. `accounts`, `account_groups`, `journal_entries`, `journal_entry_lines`, `fiscal_years`, `fiscal_periods`, `posting_references`, `companies`, `currencies`, `cost_centers`, `departments`, `projects`, `exchange_rates`, `tax_types`, `tax_treatments`, `tax_authorities`, `tax_rates`, `tax_rules`, `tax_exemption_reasons`, `tax_periods`, `tax_accounting_mappings`
- Column names: snake_case, e.g. `id`, `code`, `name`, `is_active`, `company_id`, `account_group_id`, `parent_id`, `normal_balance`, `entry_number`, `period_id`, `posted_by`, `posted_at`, `is_posted`, `debit_amount`, `debit_currency`, `credit_amount`, `credit_currency`, `xmin`
- Primary keys: `id` bigint identity by default
- Foreign keys: snake_case `<table>_id`, e.g. `company_id`, `account_id`, `journal_entry_id`, `tax_type_id`
- Indexes: snake_case `IX_<table>_<columns>`, composite unique indexes for per-company uniqueness, e.g. `IX_accounts_company_id`, `IX_cost_centers_company_id_code`, `IX_tax_types_company_id_code`
- Enum storage: `HasConversion<string>()` → stored as text, e.g. `account_type`, `normal_balance`, `tax_category`, `tax_treatment_type`, `authority_level`, `period_type`, `filing_frequency`, `status`

### Concurrency & Audit
- **xmin concurrency token**: every entity has `xmin` column `uint` with `rowVersion: true`, configured via `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`
- No `CreatedAt/UpdatedAt/CreatedBy/UpdatedBy` columns in current migrations or entity models; audit is via domain events and `xmin` optimistic concurrency
- Domain events pattern: entities expose `DomainEvents` collection, raise events on state changes e.g. `AccountDeprecated`, `JournalEntryPosted`, `TaxTypeCreated`, `TaxRuleCreated`
- Soft delete pattern: `IsActive` bool flag, e.g. `Account.Deprecate()` sets `IsActive=false` and raises event; no hard delete

### Data Models – Phase 1-3 Core Entities
**BaseEntity**
- `long Id`, `IReadOnlyCollection<DomainEvent> DomainEvents`, private parameterless ctor for EF, protected ctor for id

**Accounting Core**
- `Account`: `AccountCode Code`, `string Name`, `int Level`, `long? ParentId`, `AccountType AccountType`, `bool IsActive`, `long? AccountGroupId`, `long CompanyId`, `string? Description`, `NormalBalance NormalBalance`. Owns `Code` value object. Children collection. `Deprecate()`, `AddChild()`
- `AccountGroup`: `code`, `name`, `account_type`, `company_id`, `display_order`, `is_active`
- `JournalEntry`: `EntryNumber`, `Date`, `PeriodId`, `Description`, `SourceType`, `SourceId`, `PostedBy`, `PostedAt`, `IsPosted`. `AddLine(accountId, Money debit, Money credit, ... departmentId?, costCenterId?, projectId?)`, `Post(postedBy, postedAt)` validates balance, raises `JournalEntryPosted`
- `JournalEntryLine`: `entry_id`, `account_id`, `debit_amount`, `debit_currency`, `credit_amount`, `credit_currency`, `description`, `department_id?`, `cost_center_id?`, `project_id?` with `SetNull` delete behavior
- `FiscalYear`: `year`, `status`, `company_id`, `start_date`, `end_date`, `description`
- `FiscalPeriod`: `year_id`, `month`, `status`, `opened_at`, `closed_at`, `FiscalYearId?`, `company_id?`, `start_date`, `end_date`, `period_type`
- `PostingReference`: `journal_entry_id`, `source_type`, `source_id`

**Company & Dimensions**
- `Company`: `name`, `tax_code` unique, `address`, `phone`, `email`, `fiscal_year_start_month`, `fiscal_year_start_day`, `functional_currency_code`, `is_active`
- `Currency`: `code` unique, `name`, `symbol`, `decimal_places`, `is_default`, `is_active`
- `ExchangeRate`: `company_id`, `from_currency_code`, `to_currency_code`, `rate`, `rate_type`, `effective_date`, `source`. Unique index on `(company_id, from_currency_code, to_currency_code, rate_type, effective_date)`
- `Department`, `CostCenter`, `Project`: `company_id`, `code`, `name`, `is_active`, `start_date?`, `end_date?`. Composite unique index `(company_id, code)`. FK to Company `Restrict`. Optional FKs from `JournalEntryLine` with `SetNull`

**Tax Foundation Phase 3**
- `TaxType`: `company_id`, `code`, `name`, `tax_category`, `is_active`, `description`. Unique `(company_id, code)`
- `TaxTreatment`: `company_id`, `tax_type_id`, `code`, `name`, `tax_treatment_type`, `input_credit_allowed`, `is_active`, `description`. Unique `(company_id, code)`
- `TaxAuthority`: `company_id`, `code`, `name`, `authority_level`, `is_active`, `address`, `phone`, `description`. Unique `(company_id, code)`
- `TaxRate`: `company_id`, `tax_type_id`, `rate_value numeric(5,2)`, `rate_name`, `effective_from`, `effective_to?`, `is_active`, `description`. Unique `(company_id, tax_type_id, rate_value, effective_from)`
- `TaxRule`: `company_id`, `tax_type_id`, `tax_rate_id?`, `tax_treatment_id`, `code`, `name`, `conditions?`, `legal_reference` required, `effective_from`, `effective_to?`, `is_active`, `description`. Unique `(company_id, code)`. Nullable `TaxRateId` for exempt rules
- `TaxExemptionReason`: `company_id`, `tax_type_id`, `code`, `name`, `legal_basis` required, `description`, `is_active`. Unique `(company_id, code)`
- `TaxPeriod`: `company_id`, `fiscal_period_id`, `tax_type_id`, `filing_deadline`, `filing_frequency`, `status`, `is_active`, `description`. Unique `(company_id, fiscal_period_id, tax_type_id)`
- `TaxAccountingMapping`: `company_id`, `tax_type_id`, `tax_treatment_id`, `account_id`, `mapping_type`, `is_active`, `description`. FKs to Account, TaxType, TaxTreatment, Company all `Restrict`

**Value Objects**
- `Money` with `Amount` decimal + `Currency` string (string not FK)
- `AccountCode` owned type
- Enums in `Domain/ValueObjects/`: `AccountType`, `NormalBalance`, `PeriodType`, `PeriodStatus`, `FiscalYearStatus`, `ExchangeRateType`, `TaxCategory`, `TaxTreatmentType`, `TaxAuthorityLevel`, `TaxPeriodStatus`, `FilingFrequency`, `TaxAccountingMappingType`, `VoucherCategory`

### State Management
- Aggregate roots: `JournalEntry` owns `JournalEntryLine` collection; `Account` has children hierarchy
- Domain events for state transitions: `JournalEntryPosted`, `AccountDeprecated`, `TaxTypeCreated`, `TaxRuleCreated`, `TaxPeriodCreated`, `TaxPeriodClosed`
- Posting workflow: `JournalEntry.Post()` → `ValidateBalance()` → set `IsPosted=true`, `PostedBy/PostedAt`, raise event
- Soft delete via `IsActive` flag, no physical delete
- Concurrency via PostgreSQL `xmin` row version
- FK delete behaviors: Company-scoped entities `Restrict`; dimension FKs on `JournalEntryLine` `SetNull`

### Integration Points for Business Partner Foundation
- **Company-scoped master data**: All new Business Partner entities must follow `CompanyId` FK with `DeleteBehavior.Restrict`, composite unique index `(CompanyId, Code)`, `IsActive` soft delete, `xmin` concurrency, snake_case table/columns
- **JournalEntry integration**: `JournalEntryLine` currently supports optional `DepartmentId`, `CostCenterId`, `ProjectId`. Business Partner entities (Customer/Supplier/Employee) should be linkable to journal lines for source tracking, e.g., `customer_id`, `supplier_id` on lines or via `PostingReference` `source_type/source_id`
- **Tax integration**: Business Partner tax attributes (TaxCode, TaxType, TaxTreatment) must align with existing `TaxType`, `TaxTreatment`, `TaxRule`, `TaxExemptionReason`. Potential FKs from Partner to `TaxType`/`TaxTreatment` for default tax handling
- **Account integration**: Partners map to receivable/payable accounts via `TaxAccountingMapping` pattern; may need `BusinessPartnerAccountMapping` similar to `TaxAccountingMapping`
- **PostingReference**: Existing `source_type/source_id` pattern allows linking journal entries to Business Partner aggregates without schema changes
- **Domain ports**: New repositories `IBusinessPartnerRepository`, `ICustomerRepository`, `ISupplierRepository`, `IEmployeeRepository`, `IPaymentTermRepository` should follow existing port pattern in `Domain/Ports/`
- **EF Configurations**: Follow `*Configuration.cs` pattern: `ToTable(snake_plural)`, `HasKey`, column mappings, `HasConversion<string>()` for enums, `HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict)`, composite unique index, `xmin` row version
- **Events**: Create `{Entity}Created` events with `(EntityId, CompanyId, occurredOn)` minimal pattern
- **Naming**: Entity files in `Domain/Entities/`, enums/value objects in `Domain/ValueObjects/`, events in `Domain/Events/`, ports in `Domain/Ports/`, EF configs in `Infrastructure/Persistence/Configurations/`, repositories in `Infrastructure/Repositories/`
- **Migrations**: Generate via `dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`; ensure `defaultValue: 0L` on new non-nullable `company_id` columns requires backfill strategy
- **Architecture constraints**: Domain zero NuGet refs, Application references Domain only, Infrastructure references Application+Domain, Api references Application+Infrastructure; 22 NetArchTest rules enforced; controllers must not reference Domain.Entities/Repositories

### Constraints Summary
- Snake_case DB naming mandatory via EFCore.NamingConventions
- `xmin` concurrency token mandatory on all entities
- `CompanyId` required on all master data, FK Restrict
- Composite unique `(CompanyId, Code)` for per-company code uniqueness
- Enums stored as string
- Currency codes stored as string, not FK
- Soft delete via `IsActive`
- Domain events for audit trail, no Created/Updated timestamps in schema
- Clean Architecture dependency direction enforced

## Task-Specific Research — [G1] Implement Domain layer contracts for Business Partner master data

### Existing Domain Patterns Inspected

**BaseEntity**
- `long Id`, `IReadOnlyCollection<DomainEvent> DomainEvents`
- Private parameterless ctor for EF, protected ctor for id
- `AddDomainEvent`, `RemoveDomainEvent`, `ClearDomainEvents`

**Entity pattern (Account, TaxType, Department, VoucherType)**
- Private parameterless ctor for EF materialization
- Public ctor validates invariants with `DomainException`
- Properties: `long CompanyId`, `string Code`, `string Name`, `bool IsActive = true`, `string? Description`
- `CompanyId` validated >0, `Code`/`Name` required non-whitespace
- Domain event raised in ctor: `AddDomainEvent(new XxxCreated(Id, companyId, DateTimeOffset.UtcNow))`
- Soft delete via `IsActive` flag, `Deactivate()` method without event (matches Department/TaxType)
- No navigation property to Company; FK configured in EF only

**DomainException**
- `public class DomainException : Exception` with message ctor
- Used for all invariant violations (replaces ArgumentNull/OutOfRange)

**DomainEvent**
- Abstract base with `DateTimeOffset OccurredOn`, `Guid EventId`
- Entity-specific events carry `EntityId`, `CompanyId`, `OccurredOn` only (minimalism)
- Examples: `DepartmentCreated`, `TaxTypeCreated`, `VoucherTypeCreated`

**Port interfaces**
- `IDepartmentRepository`: `GetByIdAsync`, `GetByCodeAsync(code, companyId)`, `GetAllAsync`, `AddAsync`
- `ITaxTypeRepository`: `GetByIdAsync`, `GetByCodeAsync`, `GetAllByCompanyAsync(companyId)`, `AddAsync`
- Pattern: async CRUD, no UpdateAsync (change tracking), GetByCode scoped to company

**ValueObjects**
- Enums live in `Domain/ValueObjects/` (e.g., `TaxCategory`, `VoucherCategory`)
- Records for value objects with validation via `DomainException` (e.g., `AccountCode`)
- Enums stored as string via `HasConversion<string>()` in EF config

**EF Configuration pattern**
- `internal sealed class XxxConfiguration : IEntityTypeConfiguration<T>`
- `ToTable("snake_plural")`, `HasKey`, column mappings with `HasColumnName`
- `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
- Composite unique index `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()`
- `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`
- Max lengths: Code 20-50, Name 200, Description 500

### Required Fields Inference

No existing Customer/Supplier/Employee/PaymentTerm entities found. Based on Phase 4 goal and existing patterns:

**Customer**
- `CompanyId` (long, required, FK Restrict)
- `Code` (string, required, unique per company)
- `Name` (string, required)
- `TaxCode` (string?, optional for Vietnamese VAT)
- `Address` (string?, optional)
- `Phone` (string?, optional)
- `Email` (string?, optional)
- `IsActive` (bool, default true)
- `Description` (string?, optional)
- Domain event: `CustomerCreated(CustomerId, CompanyId, occurredOn)`
- Port: `ICustomerRepository` with `GetByIdAsync`, `GetByCodeAsync(code, companyId)`, `GetAllByCompanyAsync`, `AddAsync`

**Supplier**
- Same base fields as Customer
- Additional optional: `PaymentTermId` (long?) referencing PaymentTerm, `DefaultTaxTypeId` (long?) for tax handling
- Domain event: `SupplierCreated`
- Port: `ISupplierRepository` same pattern

**Employee**
- `CompanyId`, `Code`, `Name`, `IsActive`, `Description`
- Additional: `EmployeeNumber` (string?, unique per company), `TaxCode` (string?), `Phone`, `Email`, `Address`, `HireDate` (DateOnly?), `IsActive`
- Domain event: `EmployeeCreated`
- Port: `IEmployeeRepository` with `GetByCodeAsync`, `GetByEmployeeNumberAsync`

**PaymentTerm**
- `CompanyId`, `Code`, `Name`, `IsActive`, `Description`
- Value object/enum: `PaymentTermType` (e.g., Net, DueOnReceipt, DaysAfterInvoice) stored as string
- `Days` (int?, number of days for net terms)
- Unique `(CompanyId, Code)`
- Domain event: `PaymentTermCreated`
- Port: `IPaymentTermRepository` with `GetByCodeAsync`

**Value Objects**
- `PaymentTermType` enum in `Domain/ValueObjects/` (Net, DueOnReceipt, DaysAfterInvoice, etc.)
- Possibly `PartnerType` enum if shared, but separate entities preferred per goal

### Constraints to Follow
- CompanyId FK Restrict, composite unique (CompanyId, Code)
- IsActive soft delete, xmin concurrency token
- DomainException validation in constructors
- Private parameterless ctor for EF
- Events minimal: EntityId + CompanyId + occurredOn
- No NuGet refs in Domain
- Naming: entities in `Domain/Entities/`, events in `Domain/Events/`, ports in `Domain/Ports/`, value objects/enums in `Domain/ValueObjects/`

### Verification Criteria for Executor
- Entities extend BaseEntity, have private parameterless ctor + public validated ctor
- Constructors throw DomainException for invalid CompanyId/Code/Name
- Domain event added in constructor
- Port interfaces follow async pattern with GetByCode scoped to company
- No navigation properties to Company
- All properties private set

## Task-Specific Research — [G2] Implement Infrastructure EF Core configurations and repositories

### Existing Configuration Patterns Inspected

**DepartmentConfiguration.cs**
- `internal sealed class DepartmentConfiguration : IEntityTypeConfiguration<Department>`
- `ToTable("departments")`
- `HasKey(e => e.Id)`; `Id` column `id`, `ValueGeneratedOnAdd`
- Properties mapped with `HasColumnName` snake_case: `company_id`, `code`, `name`, `is_active`
- `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()`
- `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
- `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`
- No enum conversion needed

**VoucherTypeConfiguration.cs**
- Same pattern as Department
- Additional enum property: `VoucherCategory` mapped with `HasColumnName("voucher_category").HasConversion<string>()`
- `code` max length 20, `name` 200, `description` 500
- Composite unique index `(CompanyId, Code)`

**TaxTypeConfiguration.cs**
- Enum `TaxCategory` with `HasConversion<string>()`
- `code` max 20, `name` 200, `description` 500
- Composite unique index `(CompanyId, Code)`
- Company FK Restrict

**TransactionReasonConfiguration.cs**
- Two FKs: `CompanyId` and `VoucherTypeId`
- Both configured with `HasOne<...>().WithMany().HasForeignKey(...).OnDelete(DeleteBehavior.Restrict)`
- Composite unique index `(CompanyId, Code)` — not composite with VoucherTypeId
- No enum conversion

**JournalEntryLineConfiguration.cs**
- Optional FKs with `OnDelete(DeleteBehavior.SetNull)` for Department/CostCenter/Project
- `OwnsOne` for Money value objects
- Indexes on FK columns

### Existing Repository Patterns Inspected

**EfDepartmentRepository.cs**
- `public class EfDepartmentRepository : IDepartmentRepository`
- Constructor injection `SmeAccountingDbContext`
- `GetByIdAsync`: `_context.Departments.FirstOrDefaultAsync(e => e.Id == id)`
- `GetByCodeAsync`: filter by `Code` + `CompanyId`
- `GetAllAsync`: `AsNoTracking().OrderBy(e => e.Code).ToListAsync()`
- `AddAsync`: `_context.Departments.AddAsync(department)`

**EfVoucherTypeRepository.cs**
- Same pattern as Department
- `GetAllAsync` uses `AsNoTracking()`

**EfTaxTypeRepository.cs**
- `GetAllByCompanyAsync(long companyId)`: `AsNoTracking().Where(e => e.CompanyId == companyId).OrderBy(e => e.Code).ToListAsync()`
- Ports with `GetAllByCompanyAsync` use company filter, not global GetAll

### Entity Field Mapping for Configurations

**Customer**
- Table: `customers`
- Columns: `id`, `company_id`, `code`, `name`, `tax_code`, `address`, `phone`, `email`, `is_active`, `description`
- Max lengths: `code` 20, `name` 200, `tax_code` 20, `address` 500, `phone` 50, `email` 200, `description` 500
- Composite unique index `(company_id, code)`
- Company FK Restrict
- xmin row version

**Supplier**
- Table: `suppliers`
- Columns: `id`, `company_id`, `code`, `name`, `tax_code`, `address`, `phone`, `email`, `payment_term_id`, `default_tax_type_id`, `is_active`, `description`
- Max lengths same as Customer
- Composite unique index `(company_id, code)`
- Company FK Restrict
- Optional FKs: `PaymentTermId` → PaymentTerm, `DefaultTaxTypeId` → TaxType, both `OnDelete(DeleteBehavior.Restrict)`
- xmin row version

**Employee**
- Table: `employees`
- Columns: `id`, `company_id`, `code`, `name`, `employee_number`, `tax_code`, `address`, `phone`, `email`, `hire_date`, `is_active`, `description`
- Max lengths: `code` 20, `name` 200, `employee_number` 50, `tax_code` 20, `address` 500, `phone` 50, `email` 200, `description` 500
- Composite unique index `(company_id, code)`
- Company FK Restrict
- `hire_date` maps to `DateOnly?` → column type `date`
- xmin row version

**PaymentTerm**
- Table: `payment_terms`
- Columns: `id`, `company_id`, `code`, `name`, `payment_term_type`, `days`, `is_active`, `description`
- Max lengths: `code` 20, `name` 200, `description` 500
- Enum `PaymentTermType` → `HasConversion<string>()`, column `payment_term_type`
- `days` nullable int
- Composite unique index `(company_id, code)`
- Company FK Restrict
- xmin row version

### Repository Method Requirements

**ICustomerRepository**
- `GetByIdAsync(long id)` → tracked
- `GetByCodeAsync(string code, long companyId)` → tracked
- `GetAllByCompanyAsync(long companyId)` → `AsNoTracking().Where(e => e.CompanyId == companyId).OrderBy(e => e.Code)`
- `AddAsync(Customer customer)`

**ISupplierRepository**
- Same as Customer
- `GetAllByCompanyAsync` with company filter

**IEmployeeRepository**
- `GetByIdAsync`
- `GetByCodeAsync`
- `GetByEmployeeNumberAsync(string employeeNumber, long companyId)` → filter by `EmployeeNumber` + `CompanyId`
- `GetAllByCompanyAsync`
- `AddAsync`

**IPaymentTermRepository**
- `GetByIdAsync`
- `GetByCodeAsync`
- `GetAllByCompanyAsync`
- `AddAsync`

### Naming & Conventions to Follow

- Configuration class `internal sealed class XxxConfiguration : IEntityTypeConfiguration<Xxx>`
- `ToTable("snake_plural")`
- Column names snake_case via `HasColumnName`
- `Id` → `id`, `ValueGeneratedOnAdd`
- `CompanyId` → `company_id`
- `Code` → `code`, `IsRequired()`, `HasMaxLength(20)`
- `Name` → `name`, `IsRequired()`, `HasMaxLength(200)`
- `IsActive` → `is_active`
- `Description` → `description`, `HasMaxLength(500)`
- Enum properties → `HasConversion<string>()`
- `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()`
- `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
- `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`
- Repositories: `public class EfXxxRepository : IXxxRepository`, inject `SmeAccountingDbContext`, async methods, `AsNoTracking()` for list queries, no `UpdateAsync` needed

### Verification Criteria for Executor

- Four configuration files created under `src/SmeAccounting.Infrastructure/Persistence/Configurations/`:
  - `CustomerConfiguration.cs`, `SupplierConfiguration.cs`, `EmployeeConfiguration.cs`, `PaymentTermConfiguration.cs`
- Each config implements `IEntityTypeConfiguration<T>` with snake_case table/columns, enum conversion for PaymentTermType, Company FK Restrict, composite unique index `(CompanyId, Code)`, xmin row version
- Supplier config includes FKs to PaymentTerm and TaxType with Restrict
- Four repository files created under `src/SmeAccounting.Infrastructure/Repositories/`:
  - `EfCustomerRepository.cs`, `EfSupplierRepository.cs`, `EfEmployeeRepository.cs`, `EfPaymentTermRepository.cs`
- Repositories implement respective port interfaces with async CRUD: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, AddAsync; Employee repo also implements GetByEmployeeNumberAsync
- Build succeeds with 0 warnings 0 errors, ArchitectureTests pass

## Task-Specific Research — [G2] Implement Application layer CQRS for Business Partner

### Existing Application Patterns Inspected

**ValidationBehavior pipeline**
- `SmeAccounting.Application.Behaviors.ValidationBehavior<TRequest,TResponse>` implements `IPipelineBehavior<TRequest,TResponse>`
- Validates all `IValidator<TRequest>` via `ValidateAsync`, throws `ValidationException` on failures
- Registered via `AddOpenBehavior(typeof(ValidationBehavior<,>))` in `DependencyInjection.AddApplication()`
- Validators registered via `AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly)`

**Command pattern**
- Commands are `record` types implementing `IRequest<TResponse>`
- Example: `CreateVoucherTypeCommand(string Code, string Name, VoucherCategory VoucherCategory, long CompanyId, string? Description = null) : IRequest<CreateVoucherTypeResult>`
- Result is simple record: `CreateVoucherTypeResult(long Id)`
- No Update commands exist in codebase; only Create and Deactivate commands observed

**Handler pattern**
- Handlers are `internal sealed class XxxHandler(...) : IRequestHandler<Command, Result>`
- Constructor injection of repository + `IUnitOfWork` for commands requiring SaveChanges
- Example `CreateVoucherTypeHandler`: creates domain entity via public ctor, `repository.AddAsync`, `unitOfWork.SaveChangesAsync`, returns Id
- Deactivate handler loads entity, calls `entity.Deactivate()`, saves

**Validator pattern**
- `AbstractValidator<T>` with `RuleFor` fluent rules
- Example `CreateVoucherTypeCommandValidator`:
  - `Code` NotEmpty, MaxLength(20)
  - `Name` NotEmpty, MaxLength(200)
  - `VoucherCategory` IsInEnum
  - `CompanyId` GreaterThan(0)
- Messages are user-friendly strings

**DTO pattern**
- DTOs are plain `record` types, no domain references
- Enums mapped via `.ToString()`
- Example `VoucherTypeDto(Id, Code, Name, VoucherCategory, CompanyId, IsActive, Description)` where `VoucherCategory` is string

**Query pattern**
- Queries are `record` types implementing `IRequest<TResponse>`
- Get single: `GetVoucherTypeQuery(long VoucherTypeId) : IRequest<VoucherTypeDto?>`
- List by company: `GetVoucherTypesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<VoucherTypeDto>>`
- Handlers map entity → DTO, use `AsNoTracking` via repository

**Repository usage in handlers**
- `GetByIdAsync`, `GetByCodeAsync`, `GetAllByCompanyAsync` used
- No Update methods on repositories; change tracking handles updates

### Domain Entities for Business Partner

**Customer**
- Fields: CompanyId, Code, Name, TaxCode?, Address?, Phone?, Email?, IsActive, Description
- Ctor validates CompanyId>0, Code/Name non-whitespace, raises `CustomerCreated`
- `Deactivate()` sets IsActive=false

**Supplier**
- Fields: CompanyId, Code, Name, TaxCode?, Address?, Phone?, Email?, PaymentTermId?, DefaultTaxTypeId?, IsActive, Description
- Ctor validates, raises `SupplierCreated`
- `Deactivate()`

**Employee**
- Fields: CompanyId, Code, Name, EmployeeNumber?, TaxCode?, Address?, Phone?, Email?, HireDate?, IsActive, Description
- Ctor validates, raises `EmployeeCreated`
- `Deactivate()`

**PaymentTerm**
- Fields: CompanyId, Code, Name, PaymentTermType enum, Days?, IsActive, Description
- `PaymentTermType` enum: Net, DueOnReceipt, DaysAfterInvoice, EndOfMonth
- Ctor validates CompanyId>0, Code/Name non-whitespace, Days>=0
- Raises `PaymentTermCreated`
- `Deactivate()`

**Ports**
- `ICustomerRepository`: GetByIdAsync, GetByCodeAsync(code,companyId), GetAllByCompanyAsync(companyId), AddAsync
- `ISupplierRepository`: same
- `IEmployeeRepository`: GetByIdAsync, GetByCodeAsync, GetByEmployeeNumberAsync(employeeNumber,companyId), GetAllByCompanyAsync, AddAsync
- `IPaymentTermRepository`: GetByIdAsync, GetByCodeAsync, GetAllByCompanyAsync, AddAsync

### Requirements & Constraints for Application Layer

- Commands/Queries/Handlers/DTOs/Validators must reside in `src/SmeAccounting.Application/Commands/`, `Queries/`, `Handlers/`, `DTOs/`, `Validators/`
- Commands as records implementing `IRequest<T>`, results as records
- Handlers internal sealed, MediatR `IRequestHandler`
- Validators `AbstractValidator<T>` with FluentValidation rules matching domain invariants
- DTOs as records, enums as string via ToString()
- ValidationBehavior pipeline already registered, no extra wiring needed
- `IUnitOfWork.SaveChangesAsync` required for commands mutating state
- No domain entity references in DTOs
- CompanyId must be >0, Code/Name required, max lengths per EF config (Code 20, Name 200, Description 500)
- PaymentTermType must be valid enum value
- Days nullable int >=0 for PaymentTerm
- EmployeeNumber optional but unique per company (validated via repository)
- Supplier PaymentTermId/DefaultTaxTypeId optional FKs
- Get/List queries return DTOs, filter by CompanyId
- Update command pattern not present in existing codebase; domain entities lack update methods. Current entities only support Create and Deactivate. Executor should follow existing pattern: Create commands for creation, Deactivate commands for soft delete, Get/List queries for read. If Update required, domain update methods must be added first.

### Suggested Approach

- Create Create commands + results for Customer/Supplier/Employee/PaymentTerm with parameters matching domain ctors
- Create Deactivate commands + handlers for soft delete
- Create GetById and GetAllByCompany queries + handlers mapping to DTOs
- Create FluentValidation validators mirroring domain invariants and max lengths
- Create DTO records with properties matching entity fields, enums as string
- Follow naming conventions: `CreateCustomerCommand`, `CreateCustomerCommandValidator`, `CreateCustomerHandler`, `CustomerDto`, `GetCustomerQuery`, `GetCustomersByCompanyQuery`
- Use existing ValidationBehavior pipeline, no changes needed

### Verification Criteria

- All command/query/handler/validator/DTO files exist under correct folders
- Commands are records implementing IRequest<T>
- Handlers are internal sealed, inject correct repository and IUnitOfWork where needed
- Validators enforce NotEmpty, MaxLength, GreaterThan(0), IsInEnum
- DTOs contain Id, Code, Name, CompanyId, IsActive, optional fields, enum as string
- Queries return DTO or IReadOnlyList<DTO>
- Build succeeds with 0 warnings 0 errors
- ArchitectureTests pass, no Domain references in Application DTOs

### Quality Standards

- Follow existing naming and folder structure exactly
- Keep handlers thin: map command → domain entity → repository → unit of work
- No business logic in handlers beyond orchestration
- Validators provide clear messages
- DTOs avoid domain types
- Use `var` preferred, C#13 features, nullable enabled
- Private fields `_camelCase` not applicable here
- No direct EF Core references in Application layer

## Task-Specific Research — [G3] Implement API controllers and build verification

### Existing API Controller Patterns Inspected

**Controller base pattern**
- Controllers inherit `Controller` (MVC) from `Microsoft.AspNetCore.Mvc`
- Constructor injects `IMediator _mediator` only
- No direct references to Domain.Entities or Domain.Repositories — Clean Architecture enforced
- Actions are thin: dispatch MediatR commands/queries, map to ViewModels, return `View()` or `RedirectToAction`
- Example `ChartOfAccountsController`:
  - `Index` GET sends `GetAccountsByGroupQuery(0)` via mediator, builds `ChartOfAccountsViewModel`, returns View
  - `Create` GET returns empty view model
  - `Create` POST validates `ModelState`, parses enums via `Enum.Parse`, builds `CreateAccountCommand`, sends via mediator, catches `ValidationException` to add ModelState errors, redirects on success
  - `Deprecate` POST sends `DeprecateAccountCommand(id)` and redirects
- Example `JournalEntryController`:
  - Similar pattern: mediator dispatch, `ValidateAntiForgeryToken`, `ValidationException` handling, redirect
- `HomeController` simple MVC with no MediatR

**ViewModels used**
- `SmeAccounting.Api.ViewModels` namespace
- ViewModels are separate from Application DTOs; controllers map DTO → ViewModel
- Example `CreateAccountViewModel`, `ChartOfAccountsViewModel`, `CreateJournalEntryViewModel`

**Anti-patterns avoided**
- Controllers never reference `SmeAccounting.Domain.Entities` or `SmeAccounting.Domain.Repositories`
- No business logic in controllers; only orchestration and validation mapping

### DI Composition Root Inspected

**Program.cs**
- `builder.Services.AddControllersWithViews()`
- `builder.Services.AddApplication()` — registers MediatR with assembly scan, `ValidationBehavior<,>` open behavior, `AddValidatorsFromAssembly`
- `builder.Services.AddInfrastructure(builder.Configuration)` — registers `SmeAccountingDbContext` with Npgsql connection string from `ConnectionStrings:DefaultConnection`, registers `IUnitOfWork` as DbContext, registers repositories `AddScoped<IAccountRepository, EfAccountRepository>` etc., registers `IClock`, `IAuditLogger`, `IForeignExchangeRateProvider`
- Swagger configured for dev
- MVC routing: `{controller=Home}/{action=Index}/{id?}`

**Application DependencyInjection**
- `AddApplication()`:
  - `services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly); cfg.AddOpenBehavior(typeof(ValidationBehavior<,>)))`
  - `services.AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly)`
- No manual service registrations needed for commands/handlers/validators

**Infrastructure DependencyInjection**
- `AddInfrastructure(IConfiguration)`:
  - `AddDbContext<SmeAccountingDbContext>` with Npgsql
  - `AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<SmeAccountingDbContext>())`
  - `AddScoped<IAccountRepository, EfAccountRepository>` etc. for all existing ports
  - Singletons/scoped for `IClock`, `IAuditLogger`, `IForeignExchangeRateProvider`
- Repositories for Business Partner entities not yet registered — must be added for G3

### Existing Application Commands/DTOs for Business Partner

**Commands**
- `CreateCustomerCommand(long CompanyId, string Code, string Name, string? TaxCode, string? Address, string? Phone, string? Email, string? Description) : IRequest<CreateCustomerResult>`
- `CreateCustomerResult(long Id)`
- `DeactivateCustomerCommand` exists
- Similar pattern for Supplier, Employee, PaymentTerm

**DTOs**
- `CustomerDto(long Id, long CompanyId, string Code, string Name, string? TaxCode, string? Address, string? Phone, string? Email, bool IsActive, string? Description)`
- Enums mapped as string in DTOs

**Queries**
- `GetCustomerQuery`, `GetCustomersByCompanyQuery` expected pattern

### Build & Verification Steps Required

**EF Migration**
- Pre-requisite: build succeeds before `dotnet ef migrations add`
- Command: `dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- Must generate migration for Customer/Supplier/Employee/PaymentTerm tables if not yet migrated
- Existing migrations: InitialCreate, FixAccountNameColumn, AccountingFoundation, Phase2AccountingControlConfig, Phase3TaxFoundation

**Build verification**
- `dotnet build SmeAccounting.sln` — TreatWarningsAsErrors=true enforced via Directory.Build.props
- Must succeed with 0 warnings 0 errors

**Architecture tests**
- `dotnet test tests/SmeAccounting.ArchitectureTests/`
- 22 NetArchTest rules enforce Clean Architecture dependency direction, controller purity, Domain zero NuGet refs
- Controllers must not reference Domain.Entities/Repositories

### Suggested Approach for G3

- Create thin MVC controllers in `src/SmeAccounting.Api/Controllers/` for Customer, Supplier, Employee, PaymentTerm
- Controllers inject `IMediator`, dispatch Create/Deactivate commands and Get/List queries, map to ViewModels
- Follow existing controller pattern: GET Index/Create, POST Create with ModelState validation, catch `ValidationException` to populate ModelState, redirect on success
- Register Business Partner repositories in `Infrastructure/DependencyInjection.cs`:
  - `services.AddScoped<ICustomerRepository, EfCustomerRepository>()`
  - `services.AddScoped<ISupplierRepository, EfSupplierRepository>()`
  - `services.AddScoped<IEmployeeRepository, EfEmployeeRepository>()`
  - `services.AddScoped<IPaymentTermRepository, EfPaymentTermRepository>()`
- Ensure `SmeAccountingDbContext` includes `DbSet<Customer>`, `DbSet<Supplier>`, `DbSet<Employee>`, `DbSet<PaymentTerm>` and ignores domain events
- Generate EF migration for new entities
- Run `dotnet build SmeAccounting.sln` and `dotnet test tests/SmeAccounting.ArchitectureTests/` to verify constraints

### Verification Criteria

- Controllers exist under `src/SmeAccounting.Api/Controllers/` with thin MediatR dispatch, no Domain references
- DI registration includes Business Partner repositories
- `dotnet build SmeAccounting.sln` succeeds with 0 warnings 0 errors
- `dotnet test tests/SmeAccounting.ArchitectureTests/` passes 22/22
- EF migration generated successfully for Business Partner entities
- Controllers follow existing pattern: IMediator injection, ValidateAntiForgeryToken, ValidationException handling, RedirectToAction

### Quality Standards

- Controllers must remain thin; no business logic
- Use existing ViewModels pattern; do not expose Application DTOs directly to views
- Keep enum parsing consistent with existing controllers (Enum.Parse with error handling)
- Maintain Clean Architecture constraints; no Domain references in Api project
- Follow C# style: var preferred, 4-space indent, private fields `_camelCase`

