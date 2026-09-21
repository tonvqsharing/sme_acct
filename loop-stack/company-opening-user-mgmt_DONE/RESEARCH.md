# Research Log
## Context & Prior Work
**Global context**
- Loop-stack global memory confirms .NET 10 SDK, Clean Architecture enforced by 22 NetArchTest rules, VAS/Circular 99 compliance, FK to Company pattern with `OnDelete(DeleteBehavior.Restrict)`, snake-case naming, xmin concurrency, domain events minimalism.
- Tools: dotnet SDK 10.0.401, EF Core 10.0.4, Npgsql 10.0.3, MediatR 14.2.0, FluentValidation 12.1.0, PostgreSQL host 172.21.208.1.

**Source structure**
- Solution: `SmeAccounting.sln` with projects `SmeAccounting.Domain`, `SmeAccounting.Application`, `SmeAccounting.Infrastructure`, `SmeAccounting.Api`.
- Dependency direction: Api → Application → Domain; Infrastructure → Application + Domain; Domain zero NuGet refs.
- `Directory.Build.props` sets net10.0, C# 13, nullable enabled, implicit usings, TreatWarningsAsErrors true.

**Package files**
- Domain: no PackageReference, pure library.
- Application: MediatR 14.2.0, FluentValidation 12.1.0, FluentValidation.DependencyInjectionExtensions 12.1.0; references Domain.
- Infrastructure: EF Core 10.0.4, Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3, Microsoft.Extensions.DependencyInjection 10.0.12, EFCore.NamingConventions 10.0.*; references Application + Domain.
- Api: references Application + Infrastructure; FluentValidation 12.1.0, MediatR 14.2.0, EF Core.Design 10.0.12, Swashbuckle 10.2.3.

**Existing tests**
- `tests/SmeAccounting.ArchitectureTests/` with 22 NetArchTest rules.
- Tests enforce Domain purity, layer coupling, naming conventions, posting rule isolation.
- No unit tests for domain logic found; architecture tests only.

**Existing Company**
- Entity `SmeAccounting.Domain.Entities.Company` extends BaseEntity. Properties: Name, TaxCode, Address, Phone?, Email?, FiscalYearStartMonth, FiscalYearStartDay, FunctionalCurrencyCode, IsActive.
- Constructor validates month 1-12, day 1-28, raises `CompanyCreated(Id, DateTimeOffset.UtcNow)`.
- EF config `CompanyConfiguration`: table `companies`, unique index on TaxCode, snake-case columns, xmin row version.
- Port `ICompanyRepository` with GetByIdAsync, GetByTaxCodeAsync, GetAllAsync, AddAsync. Implementation `EfCompanyRepository`.
- No Application commands/queries for Company creation found; entity exists with domain event but no MediatR use case currently.

**OpeningBalanceMapping**
- Entity `OpeningBalanceMapping` with CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId, IsActive, Description? Constructor validates >0 and debit != credit, throws DomainException.
- EF config `OpeningBalanceMappingConfiguration`: table `opening_balance_mappings`, unique index on (CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId), FKs Restrict to Company, VoucherType, Account x2, xmin.
- Port `IOpeningBalanceMappingRepository` with GetByIdAsync, GetAllByCompanyAsync, AddAsync. Implementation `EfOpeningBalanceMappingRepository`.
- Application layer present: `CreateOpeningBalanceMappingCommand`, `DeactivateOpeningBalanceMappingCommand`, validators, handlers, DTO `OpeningBalanceMappingDto`, queries `GetOpeningBalanceMappingQuery`, `GetOpeningBalanceMappingsByCompanyQuery`. Thin MediatR pipeline with FluentValidation.

**User/Role/Identity presence**
- No `User`, `Role`, identity entities, or ASP.NET Identity references found in Domain/Entities, Application, Infrastructure, or Api.
- Glob searches for `*User*.cs`, `*Role*.cs`, `*Identity*.cs` returned no results. Grep for `User` in Domain yields none.
- Existing people-related entities: `Employee`, `Customer`, `Supplier`. No authentication/authorization domain model present.
- Controllers have no user management endpoints.

**Patterns observed**
- Domain entities: private parameterless ctor for EF, public ctor with required params, domain events via BaseEntity.AddDomainEvent, exceptions via DomainException hierarchy.
- Value objects/enums stored as string via `HasConversion<string>()`.
- FK to Company pattern universal: `HasOne<Company>().WithMany().HasForeignKey(...).OnDelete(Restrict)`.
- Composite unique indexes for per-company uniqueness.
- Repositories: async CRUD, `AsNoTracking()` for reads, `AddAsync` delegates to DbSet, no UpdateAsync (change tracking).
- Application: MediatR commands/queries as records, FluentValidation auto-pipeline, DTOs as records without domain refs.
- Infrastructure: EF Core with EFCore.NamingConventions, snake_case tables/columns, xmin concurrency token.

## External Knowledge & Resources

**Global data**
- loop-stack/.global/MEMORY.md: .NET 10 SDK defaults, Npgsql 10.0.3 requires EF Core >=10.0.4, Directory.Build.props eliminates boilerplate, Domain layer patterns: Domain events use entity ID consistently, Money currency-mismatch guards, DomainException hierarchy, private parameterless ctors for EF, JournalEntry.Post() atomic, Account.Deprecate() soft-delete, ports zero NuGet deps.
- Vietnamese Accounting Domain: 26 VAS standards mapped, Circular 99 Art.28 maps to domain posting rules/infrastructure audit/application reports, e-invoice XML legally binding via TVAN providers, Chart of Accounts 9 categories 4-digit Level1, IFRS transition via IAccountingPolicy, NormalBalance enum in ValueObjects, FK to Company pattern HasOne...OnDelete(Restrict) across FiscalYear, ExchangeRate, Account, AccountGroup.
- Cross-project: Solution layout Domain/Application/Infrastructure/Api/ArchitectureTests, ADR format Michael Nygard, traceability matrices, private parameterless ctors + public ctors.
- Application patterns: AddValidatorsFromAssembly requires FluentValidation.DependencyInjectionExtensions, commands/queries as record IRequest<T> MediatR 14.x, ValidationBehavior IPipelineBehavior, DTOs plain records, IAccountingReportService port, CreateJournalEntryCommand carries IReadOnlyList<JournalEntryLineInput>.
- T5 Dimensions: Department/CostCenter/Project follow ExchangeRate pattern with CompanyId FK Restrict, Code unique per company composite index, IsActive soft-delete, domain events, JournalEntryLine optional FKs SetNull.
- T1 Currency/Company: Money uses string Currency not VO record, Company ctor validates fiscal year start month/day, Currency entity Code 3 uppercase ISO 4217, port interfaces GetByTaxCodeAsync/GetByCodeAsync, unique indexes.
- G2 patterns: FK to Company universal, composite unique indexes, enums stored as string via HasConversion<string>(), string over FK for currency codes, backwards-compatible method expansion, event minimalism.
- G3 batch: Single migration AccountingFoundation covers G1/G2, migration naming descriptive, build must succeed before EF migration generation, backfill defaultValue 0L on company_id, final schema 13 tables.
- Tax legislation: VAT Law 48/2024/QH15 effective 2025-07-01 rates 10%/8%/5%/0%, CIT Law 67/2025/QH15 effective 2025-10-01, PIT Law 109/2025/QH15 effective 2026-07-01, Circular 99/2025/TT-BTC effective 2026-01-01, Decree 70/2025/NĐ-CP e-invoice XML mandatory.

**Global tools**
- TOOLS.md: dotnet SDK 10.0.401, ASP.NET Core Runtime 10.0.12, .NET Runtime 10.0.12, dotnet-ef 10.0.12, git 2.51.0, Node v26.5.0, npm 11.17.0, psql 18.4, curl 8.20.0, python3 3.13.9, OpenSSL 3.5.4. No nuget CLI, make, gcc, jq, docker.
- NuGet org enabled. Directory.Build.props net10.0 C#13 nullable implicit usings warnings-as-errors. .editorconfig present.
- Packages: Domain none, Application MediatR 14.2.0 FluentValidation 12.1.0, Infrastructure EF Core 10.0.4 Npgsql 10.0.3 EFCore.NamingConventions, Api EF Core.Design 10.0.12 Swashbuckle 10.2.3.
- Architecture constraints: Clean Architecture, 22 NetArchTest, Controllers must NOT reference Domain.Entities/Repositories, CQRS MediatR, FluentValidation auto-pipeline, PostgreSQL snake-case xmin.
- Regulatory: VAS, Circular 99, ADRs in loop-stack/vietnamese-acct-architecture_DONE/docs/architecture/
- Existing domain entities 19 files, ports IAccountRepository etc., EF configs pattern, repositories pattern, 4+ migrations listed.
- Commands: dotnet build SmeAccounting.sln, dotnet test tests/SmeAccounting.ArchitectureTests/, dotnet run --project src/SmeAccounting.Api/, EF migrations add/update/list, psql connection.
- Skills relevant listed.

**Repo README / docs**
- No README.md found at repo root or loop directory.
- Repo docs/: docs/discovery-phase0.md, docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md
- docs/discovery-phase0.md: project identity, Clean Architecture CQRS, current state: Company entity exists but Legal Representative/Chief Accountant/CompanySetting missing, OpeningBalanceMapping exists but engine missing, User/Role/Permission missing, ASP.NET Core Identity not present, Authentication/Authorization missing, UI missing.
- loop-stack/vietnamese-acct-architecture_DONE/docs/regulatory/: ChartOfAccounts-structure.md, Circular99-mapping.md, EInvoice-integration.md, IFRS-transition-roadmap.md, VAS-compliance.md
- ADRs use Michael Nygard format.

**Configuration**
- Directory.Build.props: TargetFramework net10.0, Nullable enable, ImplicitUsings enable, LangVersion 13, TreatWarningsAsErrors true
- .editorconfig: indent_style space, indent_size 4, end_of_line lf, charset utf-8, trim_trailing_whitespace true, insert_final_newline true, csproj indent_size 2, private fields camel_case_underscore_prefix
- src/SmeAccounting.Api/appsettings.json: ConnectionStrings.DefaultConnection Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456, Logging LogLevel Default Information, AllowedHosts *
- src/SmeAccounting.Api/appsettings.Development.json: DetailedErrors true
- No .env.example, no .env files found via glob
- No docker-compose.yml, no Kubernetes manifests found

**External APIs**
- Grep src/**/*.cs for HttpClient/IHttpClientFactory/external/api/webhook → no results
- No external API configuration in appsettings
- Domain ports: IForeignExchangeRateProvider, IAuditLogger, IPostingService, IClock present as internal ports, no external HTTP adapters implemented
- Global TOOLS.md lists external knowledge sources unconfirmed local: congbao.chinhphu.vn, thuvienphapluat.vn, luatvietnam.vn, vanban123.vn; PwC Worldwide Tax Summaries, Vietnam Briefing, EY Tax Updates, MISA SME Accounting

**Migration tooling**
- EF Core Migrations folder: src/SmeAccounting.Infrastructure/Migrations/
- Migrations found: 20260916051341_InitialCreate, 20260916051520_FixAccountNameColumn, 20260916083803_AccountingFoundation, 20260917013843_Phase2AccountingControlConfig, 20260917045015_Phase3TaxFoundation, 20260917092428_BusinessPartnerFoundation, 20260917111153_AddUom, 20260921020615_AddItemCategory, 20260921020956_AddWarehouse, 20260921021609_AddUomConversion, 20260921022726_AddItemAndServiceItem, 20260921024242_AddInventoryValuationPolicyAndAdjustmentReason, 20260921025725_AddInventoryAccountingConfiguration, plus Designer snapshots
- Model snapshot: SmeAccountingDbContextModelSnapshot.cs
- Commands documented in TOOLS.md and AGENTS.md: dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api; dotnet ef database update; dotnet ef migrations list
- Pre-requisite: build must succeed before migration generation
- Migration naming convention descriptive feature name
## Requirements & Constraints

### DB Schema
- PostgreSQL 16.14 via EF Core 10.0.4 + Npgsql 10.0.3, snake_case table/column naming via EFCore.NamingConventions, xmin row-version concurrency on all entities.
- Tables present: accounts, account_groups, companies, cost_centers, currencies, customers, departments, document_numbering_series, employees, exchange_rates, fiscal_periods, fiscal_years, inventory_accounting_configurations, inventory_adjustment_reasons, inventory_valuation_policies, items, item_categories, journal_entries, journal_entry_lines, opening_balance_mappings, payment_terms, posting_configurations, posting_references, projects, service_items, suppliers, tax_accounting_mappings, tax_authorities, tax_exemption_reasons, tax_periods, tax_rates, tax_rules, tax_treatments, tax_types, transaction_reasons, uoms, uom_conversions, voucher_types, warehouses.
- FK pattern to Company: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` universal. Composite unique indexes for per-company uniqueness (CompanyId, Code) and mapping uniqueness e.g. opening_balance_mappings (CompanyId,VoucherTypeId,DebitAccountId,CreditAccountId).
- Enums stored as string via `HasConversion<string>()` — PeriodType, NormalBalance, ExchangeRateType, AccountType, PeriodStatus, FilingFrequency, TaxPeriodStatus.

### Data Models
- Company: Id, Name max200, TaxCode max13 unique, Address max500, Phone max20?, Email max200?, FiscalYearStartMonth 1-12, FiscalYearStartDay 1-28, FunctionalCurrencyCode max3 default VND, IsActive. Constructor validates month/day, raises CompanyCreated(Id,OccurredOn). No Legal Representative/Chief Accountant/CompanySetting yet.
- OpeningBalanceMapping: CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId, IsActive, Description max500. Private ctor + public ctor validates >0 and Debit != Credit via DomainException. Deactivate() soft-delete. EF config unique index on 4 columns, FK Restrict.
- JournalEntry: EntryNumber max50, Date, PeriodId, Description max500, SourceType/SourceId, PostedBy max100, PostedAt?, IsPosted. Aggregate root with private List<JournalEntryLine>. AddLine validates not posted, Post() validates balance then sets IsPosted true + event.
- FiscalPeriod: YearId, Month, StartDate, EndDate, PeriodType, Status default Open, OpenedAt?, ClosedAt?. Open/Close methods change Status and raise PeriodClosed.
- TaxPeriod: CompanyId, FiscalPeriodId, TaxTypeId, FilingFrequency, Status, Effective dates. Workflow Open → Filed → Closed with DomainException guards, events TaxPeriodCreated/TaxPeriodClosed.

### State Management
- FiscalPeriod lifecycle: Open → Closed via Close(date) sets ClosedAt and raises event. Closed periods must reject new postings per Circular 99.
- TaxPeriod lifecycle: Open → Filed → Closed with validation in MarkFiled/Close methods.
- JournalEntry: Draft → Posted irreversible. IsPosted flag prevents AddLine/Modify. Posting creates JournalEntryPosted domain event.
- Account lifecycle: Deprecate() sets IsActive false, soft-delete only for audit trail.

### Accounting Invariants
- Debit = Credit balance enforced in JournalEntry.ValidateBalance() before Post, throws InvalidPostingRuleException if mismatch. Posted entries immutable.
- OpeningBalanceMapping requires DebitAccountId != CreditAccountId and all IDs >0.
- Domain events minimalism: carry entity Id + CompanyId + occurredOn only.
- Money value object uses string Currency with currency-mismatch guards at operator level.
- AccountCode numeric check via constructor validation.
- Posting rules per Circular 99 Art 28(a): PostingService enforces debit=credit, period-open rules, Account entity enforces COA structure.

### VAS / Circular 99 Compliance
- Circular 99/2025/TT-BTC effective 2026-01-01 replaces 200/2014. Art 28 software requirements mapped to layers: Domain posting rules, Domain+Infrastructure immutability/audit, Application reporting, Infrastructure e-invoice/digital signature ports, extensibility.
- Chart of Accounts extensibility: accounts eliminated/renamed/new per Circular 99; Account entity supports lifecycle.
- E-invoice XML legally binding, TVAN provider adapters, digital signature mandatory.
- VAS core standards mapped: VAS 01 COA/reporting, VAS 02 Inventory, VAS 03/04 Fixed Assets, VAS 06 Lease, VAS 10 FX, VAS 14 Revenue, VAS 17 Tax, VAS 21/24 Reporting, VAS 29 Policy changes.
- Single-company scope confirmed by Circular 99 Art 2; no consolidation required.

### Single-Company Model
- All company-scoped entities carry CompanyId FK with Restrict delete. Repositories offer GetAllByCompanyAsync, GetByCodeAsync(code, companyId).
- Composite unique indexes enforce per-company uniqueness: (CompanyId, Code) for dimensions, (CompanyId, TaxTypeId, RateValue, EffectiveFrom) for TaxRate, etc.
- FunctionalCurrencyCode stored as string on Company, Money uses string Currency, no FK to Currency entity.
- No multi-tenant isolation beyond CompanyId filtering; schema assumes single-company database per instance.

### Validation Rules
- Domain constructors: Company fiscal year month 1-12 day 1-28; CompanyId >0; Code required non-empty; debit/credit >0 and distinct; ExchangeRate From != To, Rate >0; PaymentTerm Days >=0; TaxRate RateValue >=0; Item stock/service invariant.
- EF config max lengths: Code 20, Name 200, Description 500, TaxCode 13, etc.
- Unique DB constraints: Company TaxCode unique; per-company Code composite indexes; mapping uniqueness.
- Application layer: FluentValidation AbstractValidator for commands, ValidationBehavior IPipelineBehavior runs validators before handler and throws ValidationException.
- Enum values stored as string, conversion enforced.

### Transaction Boundaries
- IUnitOfWork.SaveChangesAsync is unit of work boundary. MediatR handlers perform domain operations then call SaveChanges.
- Posting is atomic aggregate method: ValidateBalance → set Posted flags → raise domain event, no partial state.
- EF Core change tracking handles updates; repositories have no UpdateAsync.
- Concurrency via xmin row version for optimistic concurrency.
- Domain events added to BaseEntity and dispatched after successful SaveChanges.

## Environment & Integration

**CI/CD**
- No CI/CD configuration discovered. No `.github/workflows/`, no `azure-pipelines*.yml`, no `*.yml` / `*.yaml` pipeline files in repo root or subdirectories.
- Build commands documented in AGENTS.md / TOOLS.md: `dotnet build SmeAccounting.sln`, `dotnet test tests/SmeAccounting.ArchitectureTests/`, `dotnet run --project src/SmeAccounting.Api/`.
- No automated pipeline artifacts, no linting, no codegen steps.

**Infrastructure / Runtime**
- .NET SDK 10.0.401, ASP.NET Core Runtime 10.0.12, .NET Runtime 10.0.12 per global TOOLS.md.
- PostgreSQL 16.14 host 172.21.208.1, database `sme_acct_dev`, user `dev`, password `123456`. Connection string in `src/SmeAccounting.Api/appsettings.json` under `ConnectionStrings:DefaultConnection`.
- EF Core 10.0.4 + Npgsql 10.0.3 with EFCore.NamingConventions for snake_case, xmin concurrency tokens.
- No Docker files: `Dockerfile*` not found, `docker-compose*.yml` not found. Docker not installed per global TOOLS.md.
- No Kubernetes manifests, no `.env` / `.env.example` files.

**Build**
- `Directory.Build.props` sets `net10.0`, C# 13, nullable enabled, implicit usings, `TreatWarningsAsErrors true`.
- Solution `SmeAccounting.sln` with 5 projects: Domain, Application, Infrastructure, Api, ArchitectureTests.
- Build prerequisite for EF migrations: build must succeed before `dotnet ef migrations add`.
- No `make`, `nuget` CLI, `jq`, `gcc` per global TOOLS.md.

**Runtime config**
- `src/SmeAccounting.Api/appsettings.json`: ConnectionStrings.DefaultConnection, Logging LogLevel Default Information / Microsoft.AspNetCore Warning, AllowedHosts "*".
- `appsettings.Development.json`: DetailedErrors true.
- `Program.cs`: `AddControllersWithViews`, `AddApplication`, `AddInfrastructure(configuration)`, `AddEndpointsApiExplorer`, `AddSwaggerGen`, `UseExceptionHandler`, `UseHsts` in non-dev, `UseHttpsRedirection`, `UseStaticFiles`, `UseRouting`, `UseAuthorization`, Swagger UI in dev, default MVC route `{controller=Home}/{action=Index}/{id?}`.
- No environment variables, no secrets management discovered.

**Authentication pipeline**
- No authentication configured. `Program.cs` calls `app.UseAuthorization()` but no `AddAuthentication`, `AddIdentity`, JWT Bearer, or ASP.NET Identity setup.
- No `User`, `Role`, `Identity` entities in Domain/Entities; glob for `*User*.cs`, `*Role*.cs`, `*Identity*.cs` returned no results.
- Existing people entities: Employee, Customer, Supplier only. No auth domain model, no login endpoints, no authentication middleware.
- Microsoft-first user management is planned per PLAN.md goal but not implemented.

**Reporting controller**
- `src/SmeAccounting.Api/Controllers/ReportingController.cs` exists.
- Constructor injects `IMediator`.
- `GET BalanceSheet(long? periodId)` → sends `GetBalanceSheetQuery(id)` via MediatR, returns View.
- `GET IncomeStatement(long? periodId)` → sends `GetIncomeStatementQuery(id)` via MediatR, returns View.
- Default periodId = 1 if null.
- Queries defined in Application: `GetBalanceSheetQuery` record implements `IRequest<BalanceSheetDto>`, `GetIncomeStatementQuery` similarly.
- No authorization attributes, no input validation beyond null-coalescing.

## Task-Specific Research
## Task-Specific Research — [G1] Design CompanySettings domain model

### Context & Prior Work
- BaseEntity in `src/SmeAccounting.Domain/Entities/BaseEntity.cs`: abstract class with long Id, private List<DomainEvent>, AddDomainEvent/RemoveDomainEvent/ClearDomainEvents. Private parameterless ctor + protected ctor(long id). Domain events pattern used across entities.
- DomainEvent base in `src/SmeAccounting.Domain/Events/DomainEvent.cs`: abstract with DateTimeOffset OccurredOn, Guid EventId.
- Example event `CompanyCreated`: carries long CompanyId + occurredOn. Event minimalism pattern: entity ID + company ID + occurredOn only.
- Company entity pattern: private parameterless ctor for EF, public ctor validates fiscalYearStartMonth 1-12, day 1-28, raises CompanyCreated(Id, DateTimeOffset.UtcNow). Properties private set, IsActive default true.
- EF configuration pattern from `CompanyConfiguration` and `DepartmentConfiguration`:
  - `ToTable("snake_case_plural")`
  - `HasKey(e => e.Id)`, Id column `id` ValueGeneratedOnAdd
  - Properties mapped with `HasColumnName("snake_case")`, `IsRequired()`, `HasMaxLength()`
  - FK to Company: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
  - Composite unique index for per-company uniqueness: `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()`
  - Row version: `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`
  - Enums stored as string via `HasConversion<string>()` per global memory.
- DomainException hierarchy: `SmeAccounting.Domain.Exceptions.DomainException` base for validation.
- Existing entities follow pattern: CompanyId + Code + Name + IsActive + optional Description, unique (CompanyId, Code). Department, CostCenter, Project, VoucherType examples.
- No existing CompanySetting entity found. Discovery doc confirms Legal Representative/Chief Accountant/CompanySetting missing.
- JSON extension: EF Core 7+ supports JSON columns via `OwnsOne(...).ToJson()` for owned aggregates. Npgsql provider supports jsonb. No existing JSON usage in codebase. Pattern would be owned value object mapped to jsonb column with snake_case naming. Alternative: store as `string` with value converter to/from JSON, or use `OwnsOne` with `ToJson()`.

### Existing Tools & Resources
- EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions already in Infrastructure.
- Domain zero NuGet refs, Application MediatR 14.2.0 + FluentValidation 12.1.0.
- Architecture tests enforce 22 NetArchTest rules, dependency direction, controllers cannot reference Domain.Entities.
- Existing EF configs scaffold per entity in `Infrastructure/Persistence/Configurations/`.
- Repositories pattern: `Ef*Repository` with async CRUD, AsNoTracking for reads.

### Requirements & Constraints
- CompanySetting entity must extend BaseEntity, use private parameterless ctor + public ctor with validation.
- Must include LegalRepresentative, ChiefAccountant, fiscal settings, JSON extension for arbitrary settings.
- Domain events required: e.g., CompanySettingCreated / CompanySettingUpdated.
- EF configuration scaffold per snake_case/xmin pattern, table name `company_settings` likely.
- FK to Company with Restrict delete. If singleton per company, unique index on CompanyId.
- JSON extension column: PostgreSQL jsonb, mapped via EF Core JSON column or owned type with ToJson(). Column name `extension_data` snake_case.
- Validation via DomainException in constructor, max lengths enforced in EF config.
- Clean Architecture constraints: Domain pure, no infrastructure refs, ports for repository.
- VAS/Circular 99 compliance not directly applicable but naming conventions must match.

### Suggested Approach
Design CompanySetting as aggregate root per Company with 1:1 relationship. Use BaseEntity, private setters, domain events. Map LegalRepresentative and ChiefAccountant as value objects or simple string fields. Fiscal settings as scalar properties. Extension data as owned type mapped to jsonb via `OwnsOne(...).ToJson()` or string JSON column with converter. EF config follows DepartmentConfiguration pattern with xmin row version and unique index on CompanyId.

### Verification Criteria
- Entity compiles with BaseEntity, domain events added in constructor.
- EF configuration produces table `company_settings` with snake_case columns, xmin row version, unique index on company_id.
- JSON extension column exists and maps to .NET type.
- Domain events minimalism: event carries CompanyId + SettingId + occurredOn.
- Architecture tests pass, no Domain NuGet refs, no controller references to Domain entities.

### Quality Standards
- Follow existing naming: private fields _camelCase, 4-space indent, records for DTOs.
- Constructor validation using DomainException, not ArgumentNullException.
- Private parameterless ctor for EF.
- EF config internal sealed class, IEntityTypeConfiguration<T>.
- No navigation property to Company entity? Existing pattern uses HasOne<Company>().WithMany() without navigation property on entity. Keep consistent.
- Event pattern matches DepartmentCreated: (EntityId, CompanyId, occurredOn).

### Prior Attempt Analysis
- No prior attempts; task is design phase. Ensure JSON mapping aligns with EF Core 10 + Npgsql capabilities; avoid premature use of ToJson if provider support uncertain; fallback to string column with System.Text.Json converter.

## Task-Specific Research — [G1] Design Opening Balances domain engine

### Context & Prior Work
- Existing `OpeningBalanceMapping` entity in `Domain/Entities/OpeningBalanceMapping.cs` maps Company + VoucherType → DebitAccountId + CreditAccountId. Constructor validates CompanyId>0, VoucherTypeId>0, Debit/Credit >0, Debit != Credit via DomainException. EF config `OpeningBalanceMappingConfiguration` maps to `opening_balance_mappings`, unique index on (CompanyId,VoucherTypeId,DebitAccountId,CreditAccountId), FKs Restrict to Company/VoucherType/Account x2, xmin row version.
- No `OpeningBalanceEntry` or `OpeningBalancePeriod` entities exist yet. Glob for `OpeningBalance*.cs` returns only Mapping entity, DTO, config, repository.
- `JournalEntry` aggregate in `Domain/Entities/JournalEntry.cs` extends BaseEntity, holds private List<JournalEntryLine>, AddLine validates not posted, Post() validates balance via `ValidateBalance()` throwing `InvalidPostingRuleException`, sets IsPosted true, raises `JournalEntryPosted(Id, occurredOn)`. EntryNumber max50, PeriodId FK, SourceType/SourceId optional.
- `JournalEntryLine` holds EntryId, AccountId, Money Debit/Credit, optional Department/CostCenter/Project FKs nullable with SetNull delete behavior per T5 pattern.
- `Money` value object record with Amount decimal, Currency string, Zero factory, currency-mismatch guards on +/− operators.
- `BaseEntity` provides Id, DomainEvents list, AddDomainEvent/Remove/Clear. Private parameterless ctor for EF, protected ctor(long id).
- `DomainEvent` base with OccurredOn DateTimeOffset, EventId Guid.
- Event minimalism pattern observed: `DepartmentCreated(DepartmentId, CompanyId, occurredOn)`, `FiscalYearCreated(FiscalYearId, CompanyId, Year, occurredOn)`, `CompanyCreated(CompanyId, occurredOn)`. Events carry entity ID + CompanyId + occurredOn only.
- `FiscalYear` entity with CompanyId, Year, StartDate, EndDate, Status, raises `FiscalYearCreated`. `FiscalPeriod` with YearId, Month, Start/End Date, PeriodType, Status Open/Closed, Close() raises `PeriodClosed`.
- `Account` entity with CompanyId FK Restrict, AccountCode value object owned, NormalBalance enum stored as string via HasConversion<string>(), Deprecate() soft-delete.
- EF configuration pattern: `internal sealed class XxxConfiguration : IEntityTypeConfiguration<T>` → `ToTable(snake_case)`, `HasKey`, Id column `id` ValueGeneratedOnAdd, properties `HasColumnName(snake_case)`, `HasConversion<string>()` for enums, `HasOne<Company>().WithMany().HasForeignKey(...).OnDelete(DeleteBehavior.Restrict)`, composite unique indexes, `Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`.
- `CompanySettingConfiguration` shows unique index on CompanyId for 1:1 per-company entity, FK Restrict, jsonb column mapping via `HasColumnType("jsonb")`.
- Domain exceptions hierarchy: `DomainException` base, `InvalidPostingRuleException`, `PeriodClosedException`, `AccountNotLeafException`.
- Ports: `IPostingService` with `Task PostAsync(JournalEntry entry)`, `IUnitOfWork.SaveChangesAsync`, `IJournalEntryRepository`, `IAccountRepository`.
- Clean Architecture constraints: Domain zero NuGet refs, controllers must not reference Domain.Entities, 22 NetArchTest rules, snake_case naming, xmin concurrency, FK to Company Restrict universal.

### Existing Tools & Resources
- EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions available in Infrastructure.
- MediatR 14.2.0 + FluentValidation 12.1.0 in Application for commands/queries.
- Existing repositories pattern: `Ef*Repository` with async CRUD, AsNoTracking for reads, AddAsync delegates to DbSet.
- `OpeningBalanceMapping` Application layer already exists: commands Create/Deactivate, validators, handlers, DTO, queries GetById/GetAllByCompany.
- `JournalEntry` posting integration already uses `ValidateBalance()` and `JournalEntryPosted` event.
- No existing domain events for opening balances; pattern to follow DepartmentCreated / FiscalYearCreated.

### Requirements & Constraints
- Design `OpeningBalanceEntry` aggregate root extending BaseEntity with CompanyId, AccountId, PeriodId/FiscalYearId? OpeningBalancePeriod reference, Debit Money, Credit Money, Description?, IsPosted? Validation rules: CompanyId>0, AccountId>0, Period must be opening period for company, Debit and Credit cannot both be zero, Debit/Credit currency must match company functional currency, one entry per Account per OpeningBalancePeriod enforced via unique index.
- `OpeningBalancePeriod` entity likely per Company per FiscalYear start period, with CompanyId, FiscalYearId/PeriodId, Status Open/Closed, maybe OpeningDate. FK Restrict to Company and FiscalPeriod/FiscalYear. Unique index on (CompanyId, FiscalYearId) or (CompanyId, PeriodId).
- Validation rules: cannot create opening balance entries after period closed; cannot modify posted entries; total debits must equal total credits per period; account must be active and belong to company; period must be first period of fiscal year or designated opening period per VAS/Circular 99.
- Posting integration with JournalEntry: OpeningBalanceEntry aggregate should be able to generate balanced JournalEntry lines via `IPostingService` or domain method `PostOpeningBalances()` that creates JournalEntry with SourceType="OpeningBalance", SourceId=OpeningBalancePeriodId, validates balance, raises `OpeningBalancePosted` domain event.
- Domain events: `OpeningBalanceEntryCreated(EntryId, CompanyId, AccountId, occurredOn)`, `OpeningBalancePeriodCreated(PeriodId, CompanyId, occurredOn)`, `OpeningBalancePeriodClosed(PeriodId, CompanyId, occurredOn)`, `OpeningBalancesPosted(PeriodId, CompanyId, JournalEntryId, occurredOn)`. Follow minimalism.
- EF configurations with FK Restrict to Company: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` for both OpeningBalanceEntry and OpeningBalancePeriod. Additional FKs to Account, FiscalPeriod/FiscalYear with Restrict.
- Snake_case table names: `opening_balance_entries`, `opening_balance_periods`. Columns snake_case, xmin row version, enums stored as string via HasConversion<string>().
- DomainException for validation failures, not ArgumentNullException.
- Private parameterless ctor for EF, public ctor with required params and validation.
- No navigation properties to Company per existing pattern; FK only in config.
- Backwards compatible with existing OpeningBalanceMapping; mapping may be used to auto-generate entries.

### Suggested Approach
- Model `OpeningBalancePeriod` as aggregate root per company per fiscal year start, with CompanyId, FiscalYearId, PeriodId?, Status, OpeningDate. Enforce unique (CompanyId, FiscalYearId). Provide `AddEntry(AccountId, Money debit, Money credit)` method that validates account belongs to company, period open, currency matches, and creates `OpeningBalanceEntry` child entity in aggregate collection.
- Model `OpeningBalanceEntry` as entity within aggregate with CompanyId, AccountId, PeriodId, Debit Money, Credit Money, Description, IsPosted flag. Enforce one entry per account per period via composite unique index (CompanyId, PeriodId, AccountId).
- Validation rules in constructors and domain methods: CompanyId>0, AccountId>0, Period open, Debit/Credit >=0, not both zero, currency matches company functional currency, account active.
- Posting integration: `OpeningBalancePeriod.PostOpeningBalances(postedBy, postedAt)` validates total debit == total credit, creates JournalEntry via factory or via IPostingService, sets SourceType="OpeningBalance", SourceId=PeriodId, adds lines for each entry, calls JournalEntry.Post(), raises OpeningBalancesPosted event.
- EF configs: OpeningBalancePeriodConfiguration with FK Restrict to Company and FiscalYear, unique index on CompanyId+FiscalYearId, xmin. OpeningBalanceEntryConfiguration with FK Restrict to Company, Account, OpeningBalancePeriod, unique index on CompanyId+PeriodId+AccountId, xmin.
- Follow existing patterns for domain events, EF config, repository ports.

### Verification Criteria
- OpeningBalanceEntry entity compiles, extends BaseEntity, private parameterless ctor, public ctor validates via DomainException, adds domain event on creation.
- OpeningBalancePeriod entity compiles, validates CompanyId>0, FiscalYearId>0, unique index enforced.
- EF configurations produce tables `opening_balance_periods` and `opening_balance_entries` with snake_case columns, xmin row version, FK Restrict to Company, Account, FiscalYear/Period.
- Unique indexes exist for per-company per-period per-account uniqueness and per-company per-fiscal-year period uniqueness.
- Domain events carry EntityId + CompanyId + occurredOn only, matching DepartmentCreated pattern.
- Posting integration creates balanced JournalEntry with SourceType OpeningBalance, validates balance before post, raises JournalEntryPosted and OpeningBalancesPosted events.
- Architecture tests pass: Domain zero NuGet refs, no controller references to Domain entities, dependency direction preserved.

### Quality Standards
- Follow existing naming: private fields _camelCase, 4-space indent, records for DTOs, internal sealed EF configs.
- Constructor validation uses DomainException hierarchy.
- Private parameterless ctor for EF materialization.
- EF config uses HasConversion<string>() for enums, HasColumnName snake_case, HasMaxLength for strings, Property<uint>("xmin").IsRowVersion().
- Domain events minimalism: no entity data duplication.
- FK to Company pattern with DeleteBehavior.Restrict, no navigation property on entity.
- Validation rules enforced in domain, not only in FluentValidation.
- Posting atomic: ValidateBalance → set flags → raise events in one method.
- Soft-delete not required for opening balances; period closure prevents modifications.

### Prior Attempt Analysis
- No prior OpeningBalanceEntry/Period implementation found. Existing OpeningBalanceMapping is mapping only, not entry engine. Ensure design does not conflict with Mapping entity; Mapping can remain for voucher type defaults, Entry engine handles actual balances.
- Avoid creating navigation properties to Company; keep FK only in EF config per existing pattern.
- Ensure Money currency matches Company FunctionalCurrencyCode; avoid string currency mismatch.
- Ensure period open/closed checks align with FiscalPeriod.Status and Circular 99 posting rules.

## Task-Specific Research — [G1] Design Opening Balances domain engine — Fix

### Context & Prior Work
- Current implementation files:
  - `src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs` — aggregate root with CompanyId, FiscalPeriodId, PeriodDate, Status, IsPosted, private List<OpeningBalanceEntry> _entries. Constructor validates CompanyId>0, FiscalPeriodId>0, raises OpeningBalancePeriodCreated(Id, companyId, UtcNow). AddEntry creates `new OpeningBalanceEntry(Id, CompanyId, accountId, debit, credit, description)` where Id is 0 for transient aggregate. PostOpeningBalances builds entryNumber `OP-{Id}-{PeriodDate:yyyyMMdd}` using Id=0, creates JournalEntry, calls JournalEntry.Post, raises OpeningBalancesPosted(Id, CompanyId, 0, UtcNow).
  - `src/SmeAccounting.Domain/Entities/OpeningBalanceEntry.cs` — constructor validates OpeningBalancePeriodId <=0 throws DomainException, CompanyId>0, AccountId>0, debit/credit non-negative, currency match, raises OpeningBalanceEntryCreated(Id, companyId, accountId, UtcNow).
  - Events:
    - OpeningBalancePeriodCreated: PeriodId, CompanyId
    - OpeningBalanceEntryCreated: EntryId, CompanyId, AccountId
    - OpeningBalancesPosted: PeriodId, CompanyId, JournalEntryId
- Existing patterns observed:
  - `JournalEntry.AddLine` creates `new JournalEntryLine(Id, accountId, ...)` where Id is 0 for transient JournalEntry; JournalEntryLine constructor does NOT validate EntryId >0.
  - `DepartmentCreated`, `CompanyCreated`, `FiscalYearCreated` events carry EntityId + CompanyId + occurredOn only. No extra payload.
  - `JournalEntryPosted` event carries EntryId only, no PostedBy/PostedAt duplication.
  - Domain events raised in constructors use `Id` which is 0 at construction time — consistent across Company, Department, VoucherType, etc. Id is assigned by EF after SaveChanges.
  - FK to Company pattern: `HasOne<Company>().WithMany().HasForeignKey(...).OnDelete(DeleteBehavior.Restrict)` with no navigation property on entity.
  - EF configurations use snake_case, xmin row version, `HasConversion<string>()` for enums, composite unique indexes.
  - Validation uses DomainException, private parameterless ctor for EF, public ctor with required params.

### Existing Tools & Resources
- EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions already configured.
- BaseEntity provides Id, DomainEvents, AddDomainEvent.
- Money value object with currency-mismatch guards.
- DomainException hierarchy used for validation.
- OpeningBalancePeriodConfiguration maps to opening_balance_periods with FK Restrict to Company and FiscalPeriod, unique index (CompanyId, FiscalPeriodId).
- OpeningBalanceEntryConfiguration maps to opening_balance_entries with FK Restrict to Company/Account/OpeningBalancePeriod, unique index (CompanyId, OpeningBalancePeriodId, AccountId), owned Money mapping.

### Requirements & Constraints
- Allow transient aggregate Id=0: child entity constructors must not require parent Id >0. Pattern matches JournalEntryLine which accepts EntryId=0.
- Set PeriodId via navigation / EF relationship after aggregate persisted; do not enforce >0 in domain constructor for OpeningBalancePeriodId.
- Minimal domain events: EntityId + CompanyId + OccurredOn only. Remove AccountId from OpeningBalanceEntryCreated, remove JournalEntryId from OpeningBalancesPosted.
- JournalEntry Id unknown at domain event time: do not include JournalEntryId in OpeningBalancesPosted; event should be PeriodId + CompanyId only.
- Entry number generation defer to handler/application: do not generate `OP-{Id}-{PeriodDate}` in domain with Id=0; generate after Id assigned by EF, e.g., in Application handler after SaveChanges or via domain method that accepts number from application.
- Validation on FiscalPeriodId not FiscalYearId: OpeningBalancePeriod uses FiscalPeriodId, matches configuration and existing FK. Keep FiscalPeriodId validation.
- Keep FK Restrict to Company, no navigation properties.
- Keep snake_case, xmin, unique indexes.
- Keep DomainException validation for business invariants, not for transient Id.

### Suggested Approach
- Remove `openingBalancePeriodId <=0` validation from OpeningBalanceEntry constructor; allow 0 for transient aggregate. EF will populate FK on save via aggregate relationship.
- Change OpeningBalancePeriod.AddEntry to create entry with OpeningBalancePeriodId = 0 (or omit) and rely on EF to set FK when period is saved with entries collection. Alternatively, keep constructor signature but pass 0 and remove validation.
- Remove AccountId from OpeningBalanceEntryCreated event; event payload becomes EntryId, CompanyId, occurredOn.
- Remove JournalEntryId from OpeningBalancesPosted event; event payload becomes PeriodId, CompanyId, occurredOn.
- Remove entry number generation from PostOpeningBalances domain method; either accept entryNumber as parameter from application or defer numbering to Application handler after Id is known. Domain method should focus on validation and state transition, not formatting.
- Keep PostOpeningBalances validation: period open, entries exist, total debit == total credit, then create JournalEntry via domain factory, call JournalEntry.Post, set IsPosted=true, Status=Closed, raise OpeningBalancesPosted with minimal payload.
- Ensure OpeningBalancePeriodCreated event remains minimal: PeriodId, CompanyId, occurredOn.

### Verification Criteria
- OpeningBalanceEntry constructor does not throw for OpeningBalancePeriodId =0.
- OpeningBalancePeriod.AddEntry works on transient aggregate with Id=0 without DomainException.
- OpeningBalanceEntryCreated event contains only EntryId, CompanyId, occurredOn — no AccountId.
- OpeningBalancesPosted event contains only PeriodId, CompanyId, occurredOn — no JournalEntryId.
- PostOpeningBalances does not generate entry number using Id=0; entry number generation is absent from domain or deferred.
- Domain events minimalism matches DepartmentCreated pattern.
- EF configurations unchanged: tables opening_balance_periods / opening_balance_entries, snake_case, xmin, FK Restrict, unique indexes.
- Build succeeds, 22 NetArchTest rules pass.

### Quality Standards
- Follow existing transient Id pattern: child entities accept parent Id=0, EF sets FK on save.
- Domain events minimalism: EntityId + CompanyId + OccurredOn only.
- No domain logic for formatting identifiers; identifiers generated in Application layer after persistence.
- Validation remains in domain for business invariants: CompanyId>0, FiscalPeriodId>0, account uniqueness per period, debit/credit balance, period open status.
- Keep private parameterless ctor for EF, public ctor with validation via DomainException.
- Keep FK Restrict to Company, no navigation properties.
- Keep snake_case naming, xmin concurrency, HasConversion<string>() for enums.

### Prior Attempt Analysis
- Failure root causes:
  - OpeningBalanceEntry ctor requires OpeningBalancePeriodId>0, but AddEntry passes Id=0 for transient aggregate → DomainException.
  - OpeningBalancesPosted raised with JournalEntryId placeholder 0 → JournalEntry Id not known at domain event time.
  - Entry number uses Id=0 → formatting before persistence.
  - Domain events exceed minimalism → AccountId and JournalEntryId extra payload.
  - FiscalYearId vs FiscalPeriodId mismatch → implementation correctly uses FiscalPeriodId; research criteria should align.
- Corrective actions:
  - Allow transient Id=0 for child entities, matching JournalEntryLine pattern.
  - Set PeriodId via EF relationship, not constructor validation.
  - Minimal events: EntityId + CompanyId + OccurredOn.
  - Do not include JournalEntryId in domain event; JournalEntry Id unknown at raise time.
  - Defer entry number generation to Application handler after Id assigned.
  - Keep FiscalPeriodId validation as implemented.

## Task-Specific Research — [G1] Design Microsoft-first User Management domain model

### Context & Prior Work
- No User, Role, UserRole, CompanyMembership entities exist in src/SmeAccounting.Domain/Entities. Glob for *User*.cs / *Role*.cs returns zero results. Grep for User in Domain yields none.
- Existing people-related entities: Employee, Customer, Supplier. No authentication/authorization domain model present.
- Existing domain patterns observed:
  - BaseEntity with long Id, private List<DomainEvent>, AddDomainEvent/Remove/Clear, private parameterless ctor + protected ctor(long id).
  - DomainEvent base with DateTimeOffset OccurredOn, Guid EventId.
  - Entities: private parameterless ctor for EF, public ctor with required params, validation via DomainException, AddDomainEvent in ctor.
  - Example Department: CompanyId, Code, Name, IsActive. Constructor validates companyId>0, code/name non-empty, throws DomainException. Event DepartmentCreated(Id, companyId, occurredOn).
  - Company entity validates fiscal year month/day, raises CompanyCreated(Id, occurredOn).
  - DomainException hierarchy: DomainException base, no ArgumentNullException.
  - FK to Company pattern universal: HasOne<Company>().WithMany().HasForeignKey(e=>e.CompanyId).OnDelete(DeleteBehavior.Restrict), no navigation property on entity.
  - EF Configuration pattern: internal sealed class *Configuration : IEntityTypeConfiguration<T>, ToTable(snake_case), HasKey, Id column id ValueGeneratedOnAdd, properties HasColumnName(snake_case), HasMaxLength, HasIndex unique composite, Property<uint>("xmin").IsRowVersion().HasColumnName("xmin"), enums HasConversion<string>().
  - Domain events minimalism: EntityId + CompanyId + OccurredOn only. Examples: DepartmentCreated, CompanyCreated, FiscalYearCreated, OpeningBalancePeriodCreated.
  - Ports: ICompanyRepository, IAccountRepository etc. Methods: GetByIdAsync, GetByCodeAsync(code,companyId), GetAllByCompanyAsync, AddAsync. No UpdateAsync.
  - Clean Architecture: Domain zero NuGet refs, no Microsoft.EntityFrameworkCore dependency, 22 NetArchTest rules enforce dependency direction, controllers must not reference Domain.Entities.
  - Application layer uses MediatR commands/queries as records, FluentValidation AbstractValidator, ValidationBehavior pipeline.
  - Existing Company-scoped entities use CompanyId FK Restrict, composite unique index (CompanyId, Code) for per-company uniqueness.
  - Money VO uses string Currency, not FK to Currency entity.
  - Authentication pipeline absent: Program.cs has UseAuthorization but no AddAuthentication/AddIdentity/JWT. No ASP.NET Identity references in solution.

### Existing Tools & Resources
- .NET 10 SDK 10.0.401, C#13, nullable enabled, implicit usings, TreatWarningsAsErrors true.
- Domain: zero NuGet refs.
- Application: MediatR 14.2.0, FluentValidation 12.1.0.
- Infrastructure: EF Core 10.0.4, Npgsql 10.0.3, EFCore.NamingConventions 10.0.*.
- PostgreSQL host 172.21.208.1, database sme_acct_dev, user dev/123456.
- EF Core migrations pattern: dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api.
- Existing EF configs in Infrastructure/Persistence/Configurations/, repositories in Infrastructure/Repositories/.
- Architecture tests enforce Domain purity, layer coupling, naming conventions.

### Requirements & Constraints
- Design domain model Microsoft-first User Management with entities User, Role, UserRole, CompanyMembership.
- Port interfaces IUsersRepository / IRoleRepository required.
- Validation via DomainException in constructors, invariants enforced in domain.
- Clean Architecture constraints: Domain pure, no ASP.NET Identity domain coupling, no EF Core references in Domain, no Microsoft.Extensions.* in Domain.
- No password / credential storage in Domain; authentication handled by Infrastructure adapter to Microsoft Entra ID / ASP.NET Core Identity.
- Domain entities must follow existing patterns: BaseEntity, private parameterless ctor, public ctor with validation, domain events minimalism, FK to Company Restrict, snake_case EF mapping, xmin concurrency.
- User entity should be identity-agnostic: store ExternalId for Microsoft ObjectId, Email, DisplayName, UserName?, IsActive. No password hash in Domain.
- Role entity likely company-scoped: CompanyId, Code, Name, Description?, IsActive. Unique index (CompanyId, Code).
- CompanyMembership links User to Company: UserId, CompanyId, IsActive, JoinedAt?, maybe Role assignment at membership level or via UserRole.
- UserRole join entity: UserId, RoleId, CompanyId? Ensure per-company role assignment. Unique index on (UserId, RoleId, CompanyId) or (UserId, RoleId).
- Domain events: UserCreated(UserId, occurredOn), RoleCreated(RoleId, CompanyId, occurredOn), CompanyMembershipCreated(MembershipId, CompanyId, occurredOn), UserRoleAssigned(UserRoleId, CompanyId, occurredOn) – minimalism EntityId + CompanyId + OccurredOn.
- Ports should expose company-scoped queries: GetByIdAsync, GetByExternalIdAsync, GetByEmailAsync, GetAllByCompanyAsync, GetByCompanyAndCodeAsync.
- Validation rules: ExternalId required non-empty, Email required valid format? Domain validation minimal – format validation can be FluentValidation in Application. Domain ensures non-empty, CompanyId>0, Code non-empty, uniqueness enforced by DB index.
- No navigation properties to Company on entities; FK only in EF config per existing pattern.
- Enums stored as string via HasConversion<string>() if any enum introduced.
- Table names snake_case plural: users, roles, user_roles, company_memberships.
- Composite unique indexes for per-company uniqueness: roles (CompanyId, Code), company_memberships (UserId, CompanyId), user_roles (UserId, RoleId, CompanyId).
- Domain events carry provisional Id=0 at construction – consistent with existing pattern.

### Suggested Approach
- Model User as aggregate root with ExternalId string, Email string, DisplayName string, UserName? string, IsActive bool. Constructor validates ExternalId/Email non-empty, raises UserCreated(Id, occurredOn). No CompanyId on User – User is global, membership links to companies.
- Model Role as company-scoped entity with CompanyId, Code, Name, Description?, IsActive. Constructor validates CompanyId>0, Code/Name non-empty, raises RoleCreated(Id, CompanyId, occurredOn). Unique index (CompanyId, Code).
- Model CompanyMembership as link between User and Company with UserId, CompanyId, IsActive, JoinedAt DateTimeOffset. Constructor validates IDs>0, raises CompanyMembershipCreated(Id, CompanyId, occurredOn). Unique index (UserId, CompanyId).
- Model UserRole as assignment entity with UserId, RoleId, CompanyId, IsActive?, AssignedAt?. Constructor validates IDs>0, raises UserRoleAssigned(Id, CompanyId, occurredOn). Unique index (UserId, RoleId, CompanyId).
- Define ports IUsersRepository with GetByIdAsync, GetByExternalIdAsync, GetByEmailAsync, GetAllAsync, AddAsync. IRoleRepository with GetByIdAsync, GetByCompanyAndCodeAsync, GetAllByCompanyAsync, AddAsync. Optionally ICompanyMembershipRepository, IUserRoleRepository.
- EF Configurations follow DepartmentConfiguration pattern: ToTable, HasKey, column mappings snake_case, HasOne<Company>().WithMany().HasForeignKey(...).OnDelete(Restrict), xmin row version, unique indexes.
- Keep Domain free of ASP.NET Identity types; Infrastructure adapter will map Microsoft Entra ID claims to User.ExternalId and populate User entity via domain services.
- Validation via DomainException, not ArgumentNullException. Private parameterless ctor for EF.

### Verification Criteria
- User, Role, UserRole, CompanyMembership entities exist in src/SmeAccounting.Domain/Entities, extend BaseEntity, have private parameterless ctor and public ctor with DomainException validation.
- Domain events UserCreated, RoleCreated, CompanyMembershipCreated, UserRoleAssigned exist in src/SmeAccounting.Domain/Events with minimal payload EntityId + CompanyId + OccurredOn.
- Port interfaces IUsersRepository and IRoleRepository exist in src/SmeAccounting.Domain/Ports with async methods.
- No reference to Microsoft.AspNetCore.Identity or Microsoft.EntityFrameworkCore in Domain project.
- EF Configuration scaffolds exist in Infrastructure/Persistence/Configurations with snake_case table names, xmin row version, FK Restrict to Company, composite unique indexes.
- Build succeeds with dotnet build SmeAccounting.sln, 0 warnings.
- Architecture tests pass 22/22 NetArchTest rules.
- Domain events minimalism verified: events carry only Id + CompanyId + OccurredOn, no extra payload like Email or Role name.

### Quality Standards
- Follow existing naming: private fields _camelCase, 4-space indent, records for DTOs in Application, internal sealed EF configs.
- Constructor validation uses DomainException hierarchy.
- Private parameterless ctor for EF materialization.
- EF config uses HasColumnName snake_case, HasMaxLength for strings, Property<uint>("xmin").IsRowVersion().
- No navigation properties to Company on entities; FK only in EF config.
- Domain events minimalism enforced; Id=0 at construction acceptable.
- No ASP.NET Identity coupling in Domain; authentication concerns isolated to Infrastructure adapter.
- Repositories follow existing pattern: async CRUD, AsNoTracking for reads, AddAsync delegates to DbSet, no UpdateAsync.
- Unique indexes enforce per-company uniqueness at DB level.

### Prior Attempt Analysis
- No prior User Management domain implementation found. Task is design phase. Ensure design avoids coupling to ASP.NET Identity types in Domain, keeps User identity-agnostic with ExternalId, and follows existing FK to Company Restrict pattern for Role and membership entities.

## Task-Specific Research — [G1] Design Microsoft-first User Management domain model — Fix

### Context & Prior Work
- Current implementation: User entity has CompanyId, Email, DisplayName, UserName?, ExternalId?, IsActive. Constructor validates CompanyId>0, Email non-empty, DisplayName non-empty. ExternalId optional. UserCreated event carries UserId + CompanyId.
- Role entity company-scoped with CompanyId, Code, Name, IsActive. RoleCreated event carries RoleId + CompanyId.
- CompanyMembership entity links UserId + CompanyId + IsActive + JoinedAt. No domain event raised on creation.
- UserRole entity links UserId + RoleId + CompanyId + IsActive. UserRoleAssigned event carries UserRoleId + CompanyId.
- IUsersRepository methods: GetByIdAsync, GetByCompanyAndEmailAsync, GetAllByCompanyAsync, AddAsync. Missing GetByExternalIdAsync, GetByEmailAsync, GetAllAsync.
- EF configs: UserConfiguration maps CompanyId FK Restrict, unique index (CompanyId, Email). RoleConfiguration unique index (CompanyId, Code). CompanyMembershipConfiguration unique index (UserId, CompanyId) with FK Restrict to Company and User. UserRoleConfiguration unique index (UserId, RoleId, CompanyId) with FK Restrict to Company/User/Role.
- Verification failures: CompanyMembershipCreated event missing; User company-scoped conflicts with Microsoft-first global identity; User constructor does not enforce ExternalId required; repository methods differ from spec.

### Existing Tools & Resources
- Domain patterns: BaseEntity with Id, DomainEvents, private parameterless ctor + public ctor with DomainException validation, AddDomainEvent in ctor.
- Domain events minimalism: EntityId + CompanyId + OccurredOn only. Examples: DepartmentCreated, CompanyCreated, OpeningBalancePeriodCreated.
- FK to Company pattern: HasOne<Company>().WithMany().HasForeignKey(...).OnDelete(DeleteBehavior.Restrict), no navigation property on entity.
- EF config pattern: ToTable snake_case, HasKey, column mappings snake_case, HasMaxLength, HasIndex unique composite, Property<uint>("xmin").IsRowVersion().HasColumnName("xmin"), enums HasConversion<string>().
- Repositories: async CRUD, AsNoTracking for reads, AddAsync delegates to DbSet, no UpdateAsync.
- Clean Architecture: Domain zero NuGet refs, no ASP.NET Identity coupling, controllers must not reference Domain.Entities.
- Microsoft-first identity: ExternalId maps to Microsoft Entra ObjectId, global unique. Authentication handled by Infrastructure adapter, Domain stores identity-agnostic User.

### Requirements & Constraints
- User global identity-agnostic: no CompanyId on User. User identified by ExternalId mandatory, Email unique globally, DisplayName required, UserName optional, IsActive.
- ExternalId required non-empty in constructor, validated via DomainException. ExternalId max length 200, unique index on ExternalId.
- Email unique globally: unique index on Email, not per company. Email normalized to lower invariant.
- CompanyMembership links User to Company: UserId + CompanyId + IsActive + JoinedAt. Unique index (UserId, CompanyId). CompanyMembershipCreated event required with MembershipId + CompanyId + OccurredOn.
- Role company-scoped: CompanyId + Code + Name + IsActive. Unique index (CompanyId, Code). RoleCreated event unchanged.
- UserRole links User + Role within Company: UserId + RoleId + CompanyId + IsActive. Unique index (UserId, RoleId, CompanyId). UserRoleAssigned event unchanged.
- Repository methods: IUsersRepository must expose GetByIdAsync, GetByExternalIdAsync, GetByEmailAsync, GetAllAsync. No company-scoped queries on User.
- IRoleRepository methods: GetByIdAsync, GetByCompanyAndCodeAsync, GetAllByCompanyAsync, AddAsync. Company-scoped remains.
- Domain events minimalism: UserCreated should carry UserId + OccurredOn only? Current pattern includes CompanyId. For global User, event should carry UserId + OccurredOn only, no CompanyId. CompanyMembershipCreated carries MembershipId + CompanyId + OccurredOn.
- No password/credential storage in Domain. No ASP.NET Identity types in Domain.
- EF configs: User table users with columns id, external_id, email, display_name, user_name, is_active, xmin. No company_id. Unique indexes on external_id and email.
- CompanyMembership table company_memberships with user_id, company_id, is_active, joined_at, xmin. FK Restrict to Company and User.
- UserRole table user_roles with user_id, role_id, company_id, is_active, xmin. FK Restrict to Company/User/Role.
- Role table roles unchanged.

### Suggested Approach
- Redesign User entity: remove CompanyId property and FK. Add required ExternalId validation. Constructor params: externalId, email, displayName, userName? Validate ExternalId non-empty, Email non-empty, DisplayName non-empty. Raise UserCreated(UserId, OccurredOn) without CompanyId.
- Update UserCreated event: remove CompanyId property, keep UserId + OccurredOn.
- Update UserConfiguration: remove CompanyId mapping and FK, remove unique index (CompanyId, Email). Add unique index on ExternalId and Email separately. Keep xmin.
- Redesign CompanyMembership entity: add domain event on creation. Constructor validates UserId>0, CompanyId>0, sets JoinedAt, raises CompanyMembershipCreated(MembershipId, CompanyId, OccurredOn).
- Create CompanyMembershipCreated event class with MembershipId, CompanyId, OccurredOn.
- Update IUsersRepository: replace GetByCompanyAndEmailAsync and GetAllByCompanyAsync with GetByExternalIdAsync, GetByEmailAsync, GetAllAsync. Keep GetByIdAsync, AddAsync.
- Keep Role, UserRole unchanged except ensure UserRoleAssigned event minimalism.
- Ensure EF configs reflect new User schema, update CompanyMembershipConfiguration to keep FK Restrict.
- Keep Domain pure, no ASP.NET Identity coupling.

### Verification Criteria
- User entity has no CompanyId property. ExternalId property non-nullable string, validated required.
- User constructor throws DomainException if ExternalId empty.
- UserCreated event contains UserId and OccurredOn only, no CompanyId.
- CompanyMembershipCreated event exists with MembershipId, CompanyId, OccurredOn.
- CompanyMembership constructor raises CompanyMembershipCreated event.
- IUsersRepository interface defines GetByExternalIdAsync, GetByEmailAsync, GetAllAsync.
- UserConfiguration maps table users without company_id column, unique indexes on external_id and email.
- Build succeeds with dotnet build SmeAccounting.sln 0 warnings.
- Architecture tests 22/22 pass.
- No ASP.NET Identity references in Domain.

### Quality Standards
- Follow existing naming: private fields _camelCase, 4-space indent, records for DTOs.
- Constructor validation via DomainException, not ArgumentNullException.
- Private parameterless ctor for EF.
- EF config internal sealed, IEntityTypeConfiguration<T>, snake_case columns, xmin row version.
- Domain events minimalism: EntityId + CompanyId + OccurredOn where applicable; global User event has no CompanyId.
- No navigation properties to Company on entities; FK only in EF config.
- Unique indexes enforce global uniqueness for User ExternalId/Email, per-company uniqueness for Role Code and Membership.
- No ASP.NET Identity coupling in Domain; Infrastructure adapter maps Entra claims to ExternalId.

### Prior Attempt Analysis
- Failure root causes:
  - User entity company-scoped with CompanyId conflicts with Microsoft-first global identity requirement.
  - ExternalId optional, not enforced.
  - CompanyMembershipCreated event missing.
  - IUsersRepository methods company-scoped, not global.
- Corrective actions:
  - Remove CompanyId from User, make ExternalId mandatory.
  - Add CompanyMembershipCreated event and raise on creation.
  - Update IUsersRepository to global queries.
  - Update EF configs and events to match new design.
  - Keep Role company-scoped, CompanyMembership links User to Company.

