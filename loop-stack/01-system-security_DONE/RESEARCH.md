# Research Log
## Context & Prior Work
### Global Data
- MEMORY.md learnings: .NET 10 SDK defaults, Domain layer patterns (events use entity ID type consistently, Money currency guards, DomainException hierarchy, private parameterless ctor for EF, JournalEntry.Post validation pattern, soft delete), Vietnamese Accounting Domain (VAS standards, Circular 99, e-invoice XML, chart of accounts, IFRS transition via IAccountingPolicy, architecture enforcement, NormalBalance enum location, FK to Company pattern with DeleteBehavior.Restrict)
- TOOLS.md: dotnet SDK 10.0.401, ASP.NET Core 10.0.12, psql 18.4, PostgreSQL host 172.21.208.1, Directory.Build.props net10.0 C#13 nullable implicit usings warnings-as-errors, Domain zero NuGet refs, Application MediatR 14.2.0 FluentValidation 12.1.0, Infrastructure EF Core 10.0.4 Npgsql 10.0.3 EFCore.NamingConventions, Clean Architecture 22 NetArchTest rules, snake-case naming xmin concurrency

### Source Structure
src/
  SmeAccounting.Domain/ Entities, ValueObjects, Events, Ports, Exceptions
  SmeAccounting.Application/ Commands/Queries/Handlers, Validators, DTOs, Pipeline
  SmeAccounting.Infrastructure/ Persistence/Configurations, Repositories, Adapters, Migrations
  SmeAccounting.Api/ Controllers (thin MediatR dispatch)

Solution: SmeAccounting.sln, Directory.Build.props enforces net10.0, C#13, nullable, implicit usings, TreatWarningsAsErrors

### Package Files
Domain: <Project Sdk="Microsoft.NET.Sdk"></Project> — zero NuGet refs
Application: MediatR 14.2.0, FluentValidation 12.1.0
Infrastructure: EF Core 10.0.4, Npgsql 10.0.3, EFCore.NamingConventions
Api: EF Core Design 10.0.12, Swashbuckle 10.2.3

### Code Style
.editorconfig: 4-space indent, LF, UTF-8, private fields _camelCase, var preferred, 2-space for csproj/json

### Existing Tests
tests/SmeAccounting.ArchitectureTests/
- DependencyRulesTests: Domain no Application/Infrastructure/Api deps; Application no Infrastructure/Api; Infrastructure no Api; Api controllers no Infrastructure
- DomainPurityTests, NamingConventionsTests, LayerCouplingTests, PostingRuleIsolationTests
22 NetArchTest rules enforced

### Existing Entities Relevant to Loop
#### Company
Domain/Entities/Company.cs: Name, TaxCode, Address, Phone, Email, FiscalYearStartMonth/Day, FunctionalCurrencyCode, IsActive. Private parameterless ctor, public ctor validates month 1-12 day 1-28, raises CompanyCreated(Id, DateTimeOffset.UtcNow)
EF Config CompanyConfiguration: table companies, snake_case columns, unique index TaxCode, xmin row version

#### User
Domain/Entities/User.cs: ExternalId, Email, DisplayName, UserName?, IsActive. Global user (no CompanyId). Constructor validates ExternalId/Email/DisplayName non-empty, trims ExternalId, lowercases Email, raises UserCreated(Id,...). Deactivate()
EF Config UserConfiguration: table users, unique indexes ExternalId, Email, xmin
Port IUsersRepository: GetByIdAsync, GetByExternalIdAsync, GetByEmailAsync, GetAllAsync, AddAsync
Repo EfUsersRepository implements port with AsNoTracking for list
Event UserCreated carries UserId only (minimalism)

#### Role
Domain/Entities/Role.cs: CompanyId, Code, Name, Description?, IsActive. Company-scoped. Constructor validates CompanyId>0, Code/Name required, raises RoleCreated(Id,CompanyId,...). Deactivate()
EF Config RoleConfiguration: table roles, HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(Restrict), unique index (CompanyId,Code), xmin
Port IRoleRepository: GetByIdAsync, GetByCompanyAndCodeAsync, GetAllByCompanyAsync, AddAsync

#### CompanyMembership
Domain/Entities/CompanyMembership.cs: UserId, CompanyId, IsActive, JoinedAt. Constructor validates ids>0, sets JoinedAt UtcNow, raises CompanyMembershipCreated(Id,CompanyId,...)
Pattern: explicit linking aggregate for global User + company scope

#### DocumentNumberingSeries
Domain/Entities/DocumentNumberingSeries.cs: VoucherTypeId, CompanyId, Prefix, NextNumber=1, PaddingLength=6, IsDefault, IsActive, Description?. Validates ids>0, prefix required, padding 1-10. Methods Increment(), Reset(), Deactivate()
EF Config DocumentNumberingSeriesConfiguration: table document_numbering_series, unique index (VoucherTypeId,CompanyId,Prefix), FK Restrict to Company and VoucherType, xmin

#### VoucherType
Domain/Entities/VoucherType.cs: Code, Name, VoucherCategory enum, CompanyId, IsActive, Description?. Constructor validates CompanyId>0, Code/Name required, raises VoucherTypeCreated(Id,CompanyId,...). Deactivate()
EF Config VoucherTypeConfiguration: table voucher_types, VoucherCategory stored as string via HasConversion, unique index (CompanyId,Code), FK Restrict to Company, xmin
Port IVoucherTypeRepository: GetByIdAsync, GetByCodeAsync(code,companyId), GetAllAsync, AddAsync
Event VoucherTypeCreated carries VoucherTypeId, CompanyId

#### TransactionReason
Domain/Entities/TransactionReason.cs: Code, Name, VoucherTypeId, CompanyId, IsActive, Description?. Constructor validates ids>0, Code/Name required, raises TransactionReasonCreated(Id,CompanyId,...)
EF Config TransactionReasonConfiguration: table transaction_reasons, unique index (CompanyId,Code), FK Restrict to Company and VoucherType, xmin
Port ITransactionReasonRepository: GetByIdAsync, GetByCodeAsync(code,companyId), GetAllByVoucherTypeAsync(voucherTypeId), AddAsync
Event TransactionReasonCreated carries TransactionReasonId, CompanyId (minimal)

### Patterns Observed
- FK to Company: HasOne<Company>().WithMany().HasForeignKey(...).OnDelete(DeleteBehavior.Restrict) universal
- Composite unique indexes for per-company uniqueness: (CompanyId, Code)
- Enum storage as string via HasConversion<string>()
- String over FK for currency codes (Money VO uses string)
- Events minimalism: entity ID + company ID + occurredOn, no payload duplication
- DomainException hierarchy for validation, private parameterless ctor for EF
- Repositories async, GetAll AsNoTracking, AddAsync only
- Identity placeholder: Infrastructure/Adapters/IdentityUserAdapter maps User ↔ IdentityUserModel, MicrosoftSignInProvider stub

### Prior Work Notes
- User redesign to global with ExternalId mandatory for Microsoft Entra, Email globally unique, CompanyMembership for company linkage
- CompanyMembershipCreated, UserRoleAssigned events follow minimalism
- DocumentNumberingSeries, VoucherType, TransactionReason follow same entity pattern as Department/CostCenter/Project: CompanyId + Code + Name + IsActive + Description, composite unique index, EF config snake_case, xmin

## External Knowledge & Resources

### Global Loop Memory & Tools
- MEMORY.md learnings: .NET 10 SDK defaults, Domain layer patterns, Vietnamese Accounting Domain (VAS, Circular 99, e-invoice XML, chart of accounts), Cross-Project patterns, Application layer patterns, T5 Dimensions, T1 discoveries, G2/G3 batch learnings, tax legislation.
- TOOLS.md: dotnet SDK 10.0.401, ASP.NET Core 10.0.12, psql 18.4, Node v26.5.0, PostgreSQL host 172.21.208.1, Directory.Build.props net10.0 C#13 nullable implicit usings warnings-as-errors, Domain zero NuGet refs, Application MediatR 14.2.0 FluentValidation 12.1.0, Infrastructure EF Core 10.0.4 Npgsql 10.0.3 EFCore.NamingConventions, Clean Architecture 22 NetArchTest rules. Vietnamese Legal Databases listed: congbao.chinhphu.vn, thuvienphapluat.vn, luatvietnam.vn, vanban123.vn. Tax reference: PwC, Vietnam Briefing, EY, MISA SME Accounting.

### Repository Docs
- /home/projects/sme_acct/docs/discovery-phase0.md: Phase 0 discovery, project identity, architecture, current state classification for Company/Accounting/Security/UI, conflicts/risks, next steps.
- /home/projects/sme_acct/docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md: ADR accepted 2026-09-17, Phase 3 Tax Foundation regulatory scope Circular 99/2025/TT-BTC, Law 48/2024/QH15 VAT, Law 67/2025/QH15 CIT, Law 109/2025/QH15 PIT, domain model TaxType/TaxTreatment/TaxAuthority/TaxRate/TaxRule/TaxExemptionReason/TaxAccountingMapping/TaxPeriod, architecture compliance, traceability matrix.

### README / docs in loop
- loop-stack/01-system-security/ contains no README.md, no docs/ folder, no .env.example.
- Loop specific files: AGENTS.md, MEMORY.md, PLAN.md, RESEARCH.md, STATUS.md, TOOLS.md. MEMORY.md empty learnings.

### Configuration files
- src/SmeAccounting.Api/appsettings.json: ConnectionStrings.DefaultConnection = Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456. Logging LogLevel Default Information, Microsoft.AspNetCore Warning. AllowedHosts *.
- src/SmeAccounting.Api/appsettings.Development.json: DetailedErrors true, Logging same as base.
- src/SmeAccounting.Api/Properties/launchSettings.json: http profile localhost:5085, https localhost:7026, ASPNETCORE_ENVIRONMENT Development.
- No .env.example discovered in repo root or loop directory.

### External APIs & Adapters
Infrastructure/Adapters present, architecture placeholders:
- BankExchangeRateProvider : IForeignExchangeRateProvider – mock conversion VND/USD/EUR hard-coded rates (25000, 27000). No external HTTP call.
- EInvoiceProviderAdapter – stub throws NotImplementedException with note “E-invoice TVAN provider integration — architecture placeholder.”
- DigitalSignatureAdapter – stub throws NotImplementedException “Digital signature HSM/USB token integration — architecture placeholder.”
- IdentityUserAdapter – record IdentityUserModel and static mapping ToIdentityUser / ToDomainUser between Domain User entity and Identity model. No ASP.NET Core Identity package dependency in Domain.
- MicrosoftSignInProvider : IMicrosoftSignInProvider – interface ValidateTokenAsync, GetExternalIdAsync. Implementation returns dummy validation, TODO integrate Microsoft.Identity.Web.
No external API configuration files, secrets, or service URLs found. Connection string hard-coded in appsettings.

### Migration Tooling
- EF Core migrations under src/SmeAccounting.Infrastructure/Migrations/ (29 files listed). Examples: 20260916051341_InitialCreate, 20260916051520_FixAccountNameColumn, 20260916083803_AccountingFoundation, 20260917013843_Phase2AccountingControlConfig, 20260917045015_Phase3TaxFoundation, 20260917092428_BusinessPartnerFoundation, 20260917111153_AddUom, 20260921022726_AddItemAndServiceItem, etc. SmeAccountingDbContextModelSnapshot present.
- Commands per TOOLS.md/MEMORY.md: dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api; dotnet ef database update; dotnet ef migrations list.
Build must succeed before migration generation. TreatWarningsAsErrors=true.

## Requirements & Constraints

### DB Schema & Data Models

**Database**
- PostgreSQL 16.14 via EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions
- Snake-case tables/columns, `xmin` row version concurrency token on all entities
- Connection string in `src/SmeAccounting.Api/appsettings.json`: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`
- FK to Company pattern universal: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`

**System Security tables**
- `companies` – id, name varchar(200), tax_code varchar(13) unique, address varchar(500), phone varchar(20), email varchar(200), fiscal_year_start_month, fiscal_year_start_day, functional_currency_code varchar(3), is_active, xmin
- `users` – id, external_id varchar(200) unique, email varchar(200) unique, display_name varchar(200), user_name varchar(100), is_active, xmin. User is global, no CompanyId
- `company_memberships` – id, user_id, company_id, is_active, joined_at, unique(user_id,company_id). FK Restrict to Company and User
- `roles` – id, company_id, code varchar(50), name varchar(200), description varchar(500), is_active. Unique(company_id,code). FK Restrict to Company
- `user_roles` – id, user_id, role_id, company_id, is_active. Unique(user_id,role_id,company_id). FK Restrict to Company/User/Role
- `company_settings` – id, company_id unique, legal_representative_name varchar(200), legal_representative_tax_id varchar(50), chief_accountant_name varchar(200), chief_accountant_tax_id varchar(50), fiscal_year_start_month, currency varchar(3), reporting_settings_json jsonb, xmin. 1:1 per company
- `document_numbering_series` – id, voucher_type_id, company_id, prefix varchar(20), next_number, padding_length, is_default, is_active, description varchar(500). Unique(voucher_type_id,company_id,prefix)
- `voucher_types` – id, company_id, code varchar(20), name varchar(200), voucher_category (string conversion), is_active, description varchar(500). Unique(company_id,code)
- `transaction_reasons` – id, company_id, voucher_type_id, code varchar(20), name varchar(200), is_active, description varchar(500). Unique(company_id,code)

**Domain model constraints**
- All entities extend `BaseEntity` with private parameterless ctor for EF, public ctor with required params, `DomainException` validation
- Domain events minimalism: events carry EntityId + CompanyId + OccurredOn only, e.g. `CompanyCreated(Id, DateTimeOffset.UtcNow)`, `UserCreated(Id,…)`, `RoleCreated(Id,CompanyId,…)`, `CompanyMembershipCreated(Id,CompanyId,…)`, `UserRoleAssigned(Id,CompanyId,…)`, `CompanySettingCreated(Id,companyId,…)`
- Soft delete via `IsActive=false`; no hard delete for audit trail
- Value objects/enums stored as string via `HasConversion<string>()`; `NormalBalance`, `AccountType`, `PeriodStatus` etc in `Domain/ValueObjects/`

### State Management

- State transitions encapsulated in domain methods: `Deactivate()`, `Post()` pattern validates balance → set state → raise event atomically
- `DocumentNumberingSeries.Increment()`, `Reset()` for concurrency-safe numbering
- Domain events added via `AddDomainEvent` in constructors/methods, dispatched after successful `IUnitOfWork.SaveChangesAsync`
- EF Core change tracking used; repositories expose `AddAsync`, `GetByIdAsync`, `GetByCodeAsync(code,companyId)`, `GetAllByCompanyAsync` with `AsNoTracking()` for reads, no `UpdateAsync`
- Optimistic concurrency via `xmin` row version

### VAS / Circular 99 Compliance

- Circular 99/2025/TT-BTC effective 2026-01-01 replaces 200/2014. Art 28 software requirements mapped to:
  - Domain posting rules
  - Infrastructure audit immutability
  - Application reporting
  - Infrastructure e-invoice/digital signature ports
  - Extensible architecture
- E-invoice XML is legally binding; adapters for TVAN providers (Viettel/MISA/BKAV) as stubs in Infrastructure
- Digital signature HSM/USB token integration stubbed
- VAS standards core to SME scope: VAS 01 COA/reporting, VAS 02 Inventory, VAS 03/04 Fixed Assets, VAS 06 Lease, VAS 10 FX, VAS 14 Revenue, VAS 17 Tax, VAS 21/24 Reporting, VAS 29 Policy changes
- Single-company scope per Circular 99 Art 2; no consolidation required
- Chart of Accounts extensibility for accounts eliminated/renamed/new per Circular 99

### Single-Company Model

- Schema assumes single-company database per instance; no multi-tenant row-level isolation beyond `CompanyId` filtering
- All company-scoped entities carry `CompanyId` FK Restrict, composite unique indexes enforce per-company uniqueness e.g. `(CompanyId,Code)`, `(VoucherTypeId,CompanyId,Prefix)`, `(UserId,CompanyId)`
- Repositories expose `GetAllByCompanyAsync`, `GetByCodeAsync(code,companyId)`; commands/queries require `CompanyId >0`
- FunctionalCurrencyCode stored as string on Company; `Money` VO uses `string Currency`, no FK to Currency entity
- `User` is global for Microsoft Entra sign-in; company linkage via `CompanyMembership` and `UserRole` per company

### Validation Rules

**Domain**
- `Company` constructor: `FiscalYearStartMonth` 1-12, `FiscalYearStartDay` 1-28, TaxCode/Name/Address required, raises `CompanyCreated`
- `User` constructor: `ExternalId` required, `Email` required trimmed lowercased, `DisplayName` required, raises `UserCreated`
- `Role`/`VoucherType`/`TransactionReason`/`DocumentNumberingSeries`/`CompanySetting`: `CompanyId>0`, Code/Name required non-empty, `DomainException` on violation
- `CompanyMembership`/`UserRole`: ids >0
- `CompanySetting`: `LegalRepresentativeName`/`TaxId` required, `FiscalYearStartMonth` 1-12 if present, `Currency` max 3 chars
- Max lengths enforced in EF config: Code 20/50, Name 200, Description 500, TaxCode 13, ExternalId 200, Email 200

**Application**
- FluentValidation `AbstractValidator<T>` per command, `ValidationBehavior<TRequest,TResponse>` IPipelineBehavior runs all validators before handler, throws `ValidationException`
- Command validation examples: `CompanyId >0`, `LegalRepresentativeName` required max 200, `FiscalYearStartMonth` 1-12, `Currency` max 3
- Unique constraints enforced at DB level via unique indexes; application-level duplicate checks via `GetByCodeAsync(code,companyId)`

### Transaction Boundaries

- Unit of work boundary: `IUnitOfWork.SaveChangesAsync` called by MediatR handlers after domain operations
- Handlers: construct domain entity via public ctor → `repository.AddAsync` → `unitOfWork.SaveChangesAsync` → return result
- Domain aggregate methods are atomic: e.g. `JournalEntry.Post()` validates balance, sets posted state, raises event in one method
- EF Core change tracking handles updates; no explicit `UpdateAsync` in repositories
- Domain events dispatched after successful commit; events carry provisional Id=0 at construction, EF assigns Id on save
- Concurrency-safe numbering via `DocumentNumberingSeries.NextNumber` incremented within same transaction

### Authorization Boundaries

- Authentication Microsoft-first: `User.ExternalId` mandatory for Microsoft ObjectId mapping, password/credentials not stored in Domain
- `IdentityUserAdapter` in Infrastructure maps Domain `User` ↔ Identity model; `MicrosoftSignInProvider` interface stubbed
- Authorization model:
  - Global `User` entity
  - Company membership via `CompanyMembership` (UserId+CompanyId unique, IsActive)
  - Company-scoped `Role` (CompanyId+Code unique)
  - Per-company role assignment via `UserRole` (UserId+RoleId+CompanyId unique, IsActive)
- Company isolation enforced by `CompanyId` FK Restrict and repository queries filtered by companyId; no cross-company access in domain operations
- Domain has zero NuGet refs and no ASP.NET Identity coupling; adapters live in Infrastructure
- Clean Architecture enforcement: 22 NetArchTest rules, Api controllers thin MediatR dispatch only, no direct Domain.Entity references

## Environment & Integration

### CI/CD
- No CI/CD configuration discovered in repository. No `.github/`, no `*.yml`/`*.yaml` pipeline files, no GitLab CI, no Azure Pipelines, no `docker-compose` or Dockerfile.
- Build commands documented in TOOLS.md/MEMORY.md: `dotnet build SmeAccounting.sln`, `dotnet test tests/SmeAccounting.ArchitectureTests/`, `dotnet run --project src/SmeAccounting.Api/`. No automated quality gates found.
- Git present v2.51.0 per TOOLS.md; repository is git repo but no workflow automation configured.

### Infrastructure & Build
- .NET SDK 10.0.401, ASP.NET Core Runtime 10.0.12, .NET Runtime 10.0.12 per TOOLS.md.
- Solution enforces `net10.0`, C# 13, nullable enabled, implicit usings, `TreatWarningsAsErrors=true` via `Directory.Build.props`.
- Package references:
  - Domain: zero NuGet refs (pure)
  - Application: MediatR 14.2.0, FluentValidation 12.1.0
  - Infrastructure: EF Core 10.0.4, Npgsql 10.0.3, EFCore.NamingConventions
  - Api: Microsoft.EntityFrameworkCore.Design 10.0.12, Swashbuckle.AspNetCore 10.2.3
- Build verification: `dotnet build SmeAccounting.sln` is primary verification per AGENTS.md.
- EF Core tooling `dotnet-ef 10.0.12` available. Migrations live under `src/SmeAccounting.Infrastructure/Migrations/`. Migrations require successful build first.
- No Docker files, no containerization, no `docker` CLI available per TOOLS.md.

### Runtime Config
- ASP.NET Core MVC app `SmeAccounting.Api`.
- `appsettings.json` contains hard-coded connection string: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`. No secrets management, no environment-specific overrides beyond `appsettings.Development.json`.
- `appsettings.Development.json` sets `DetailedErrors: true` and logging levels.
- `Properties/launchSettings.json`: HTTP localhost:5085, HTTPS localhost:7026, `ASPNETCORE_ENVIRONMENT=Development`, `launchBrowser: true`.
- No `.env.example` or environment variable config discovered.
- Logging: `LogLevel Default Information`, `Microsoft.AspNetCore Warning`. Swagger enabled in Development only.

### Authentication Pipeline
- Program.cs registers `AddAuthentication("PlaceholderScheme")` and `AddAuthorization()`; `UseAuthentication()`/`UseAuthorization()` in pipeline.
- No ASP.NET Core Identity package referenced in Domain; authentication adapter in Infrastructure.
- `Infrastructure/Adapters/IdentityUserAdapter` provides mapping between Domain `User` and placeholder `IdentityUserModel` record.
- `Infrastructure/Adapters/MicrosoftSignInProvider` implements `IMicrosoftSignInProvider` with stub: `ValidateTokenAsync` returns `!string.IsNullOrWhiteSpace(token)`, `GetExternalIdAsync` returns `null`. TODO comment to integrate Microsoft.Identity.Web.
- Domain `User` entity is global with mandatory `ExternalId` for Microsoft Entra mapping, Email globally unique, no password stored in Domain.
- Authentication pipeline is placeholder; no JWT bearer, OpenID Connect, or cookie scheme configured. `MicrosoftSignInProvider` registered as scoped in `Infrastructure/DependencyInjection`.

### Reporting Controller
- `src/SmeAccounting.Api/Controllers/ReportingController.cs` thin MVC controller, depends on MediatR `IMediator`.
- Actions:
  - `GET BalanceSheet(long? periodId)` → sends `GetBalanceSheetQuery(id)` → returns View(model)
  - `GET IncomeStatement(long? periodId)` → sends `GetIncomeStatementQuery(id)` → returns View(model)
  - Defaults `periodId ?? 1`.
- Views: `Views/Reporting/BalanceSheet.cshtml` and `IncomeStatement.cshtml` render `BalanceSheetDto`/`IncomeStatementDto` with Assets/Liabilities/Equity groups.
- Application layer provides `IAccountingReportService` port for report generation; DTOs are records with `AccountGroupTotal(GroupName, Total, Currency)`.
- No API endpoints; reporting is MVC view-based, not JSON API.

## Task-Specific Research
## Task-Specific Research — [G1] Design Company/CompanySetting domain entities, value objects, events, ports, and EF configurations with company isolation and VAS compliance

### Context & Prior Work
- Existing `Company` entity at `src/SmeAccounting.Domain/Entities/Company.cs` extends `BaseEntity`. Properties: Name, TaxCode, Address, Phone?, Email?, FiscalYearStartMonth, FiscalYearStartDay, FunctionalCurrencyCode, IsActive. Private parameterless ctor for EF, public ctor validates month 1-12 day 1-28, throws `ArgumentNullException`/`ArgumentOutOfRangeException` (not `DomainException`). Raises `CompanyCreated(Id, DateTimeOffset.UtcNow)` on construction.
- Existing `CompanySetting` entity at `src/SmeAccounting.Domain/Entities/CompanySetting.cs` extends `BaseEntity`. Properties: CompanyId, LegalRepresentativeName, LegalRepresentativeTaxId, ChiefAccountantName?, ChiefAccountantTaxId?, FiscalYearStartMonth?, Currency?, ReportingSettingsJson?. Private parameterless ctor, public ctor validates CompanyId>0, required legal rep fields, month 1-12, throws `DomainException`. Raises `CompanySettingCreated(Id, companyId, DateTimeOffset.UtcNow)`.
- Events:
  - `CompanyCreated` at `Domain/Events/CompanyCreated.cs`: `CompanyId` + `OccurredOn` base.
  - `CompanySettingCreated` at `Domain/Events/CompanySettingCreated.cs`: `SettingId`, `CompanyId`, `OccurredOn`.
- Ports:
  - `ICompanyRepository` at `Domain/Ports/ICompanyRepository.cs`: GetByIdAsync, GetByTaxCodeAsync, GetAllAsync, AddAsync.
  - `ICompanySettingRepository` at `Domain/Ports/ICompanySettingRepository.cs`: GetByIdAsync, GetByCompanyIdAsync, AddAsync.
- EF Configurations:
  - `CompanyConfiguration` at `Infrastructure/Persistence/Configurations/CompanyConfiguration.cs`: table `companies`, snake_case columns, `HasKey`, `HasMaxLength`, unique index on `tax_code`, `xmin` row version. No FK to Company (root).
  - `CompanySettingConfiguration` at `Infrastructure/Persistence/Configurations/CompanySettingConfiguration.cs`: table `company_settings`, snake_case, `CompanyId` column, unique index on `CompanyId`, `HasOne<Company>().WithMany().HasForeignKey(e=>e.CompanyId).OnDelete(DeleteBehavior.Restrict)`, `ReportingSettingsJson` column type `jsonb`, `xmin` row version.
- Infrastructure repository `EfCompanySettingRepository` implements port with `FirstOrDefaultAsync` reads, `AddAsync` only. No `UpdateAsync`.
- DbContext `SmeAccountingDbContext` includes `DbSet<Company>`, `DbSet<CompanySetting>`, ignores `CompanyCreated` and `CompanySettingCreated` domain events in `OnModelCreating`.
- Base patterns confirmed from global memory: FK to Company pattern `HasOne<Company>().WithMany().HasForeignKey(...).OnDelete(Restrict)`, composite unique indexes per company, enum storage as string, domain events minimalism Id+CompanyId+OccurredOn, `DomainException` hierarchy, private parameterless ctor, `xmin` concurrency, snake_case naming, Clean Architecture 22 NetArchTest rules.

### Existing Tools & Resources
- Domain layer pure: zero NuGet refs, `BaseEntity` with `AddDomainEvent`, `DomainEvent` base with `OccurredOn`/`EventId`.
- EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions already configured.
- `Directory.Build.props` enforces net10.0, C#13, nullable, implicit usings, TreatWarningsAsErrors.
- Architecture tests enforce dependency direction; controllers must not reference Domain.Entities.
- Company-scoped entities already follow pattern: `Department`, `CostCenter`, `Project`, `VoucherType`, `TransactionReason`, `DocumentNumberingSeries` all use `CompanyId` FK Restrict + unique `(CompanyId,Code)` index.
- CompanySettings design verified in global memory 2026-09-21: 1:1 per company via unique index on CompanyId, FK Restrict, no navigation property, scalar fields for legal rep/chief accountant, FiscalYearStartMonth 1-12, Currency as string matching Money VO, ReportingSettingsJson jsonb, private parameterless ctor, public ctor with DomainException, domain events minimalism.

### Requirements & Constraints
- Company isolation: all company-scoped entities must carry `CompanyId` FK with `DeleteBehavior.Restrict`, composite unique indexes for per-company uniqueness, repository methods filter by companyId.
- VAS / Circular 99/2025/TT-BTC compliance: Company must capture TaxCode, Legal Representative, Chief Accountant, Fiscal year start, Functional currency. CompanySetting holds legal rep tax id, chief accountant tax id, reporting settings for VAS reporting.
- Domain purity: Domain zero NuGet refs, no ASP.NET Identity coupling, no EF Core refs. Ports in `Domain/Ports/`.
- Validation: `DomainException` for invariants, not `ArgumentNullException`. FiscalYearStartMonth 1-12, FiscalYearStartDay 1-28, TaxCode max13, Name max200, Address max500, Currency code max3.
- Events minimalism: events carry EntityId + CompanyId + OccurredOn only, no payload duplication. `CompanyCreated` currently carries only CompanyId; `CompanySettingCreated` carries SettingId+CompanyId.
- EF config pattern: `internal sealed class XxxConfiguration : IEntityTypeConfiguration<T>`, `ToTable(snake_plural)`, `HasKey`, `HasColumnName` per property, `HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict)`, unique index, `xmin` row version last.
- Value objects: No dedicated value objects for Company yet; `FunctionalCurrencyCode` is string matching Money VO pattern. Potential value object for `TaxCode` or `FiscalYearStart` but current design uses primitives.
- Soft delete: `IsActive` flag on Company, no hard delete.
- Backwards compatibility: Existing `Company` ctor uses `ArgumentNullException`/`ArgumentOutOfRangeException`; aligning to `DomainException` may be desired but not required for design task.

### Suggested Approach
- Keep existing `Company` entity as root aggregate; ensure constructor validation uses `DomainException` consistently with `CompanySetting`.
- Keep `CompanySetting` as 1:1 per-company aggregate with unique index on `CompanyId`, FK Restrict, jsonb reporting settings.
- Define ports `ICompanyRepository` and `ICompanySettingRepository` already exist; verify method signatures match pattern `GetByCodeAsync(code,companyId)` where applicable.
- Ensure EF configurations follow snake_case, `xmin` concurrency, FK Restrict, unique indexes.
- Document VAS compliance mapping: TaxCode, Legal Representative, Chief Accountant, Fiscal year start, Functional currency.
- No new value objects required for this design task; currency remains string per existing Money VO pattern.

### Verification Criteria
- Build succeeds with `dotnet build SmeAccounting.sln` zero warnings.
- 22 NetArchTest rules pass.
- `Company` and `CompanySetting` entities extend `BaseEntity`, have private parameterless ctor, public ctor with validation, raise domain events on construction.
- `CompanySettingConfiguration` has unique index on `CompanyId`, FK Restrict to Company, `reporting_settings_json` column type `jsonb`, `xmin` row version.
- `CompanyConfiguration` has unique index on `tax_code`, `xmin` row version, snake_case columns.
- Ports `ICompanyRepository` and `ICompanySettingRepository` exist in `Domain/Ports/`.
- Domain events `CompanyCreated` and `CompanySettingCreated` exist, minimal payload.
- No Domain entity references ASP.NET Identity or EF Core.

### Quality Standards
- Follow existing patterns: FK to Company Restrict, composite unique indexes, enum string conversion, domain event minimalism, `DomainException` hierarchy.
- Private fields `_camelCase` not applicable to entities; properties private set.
- Max lengths enforced in EF config, not domain.
- Events raised via `AddDomainEvent` in constructor.
- Repository reads use `AsNoTracking()` where appropriate; writes via `AddAsync`.
- Clean Architecture: Domain zero NuGet, Application references Domain only, Infrastructure references both.

### Prior Attempt Analysis
- No prior failures recorded for Company/CompanySetting design in this loop. Global memory notes CompanySettings design verified PASS 2026-09-21 with build success and 22 rules pass. Existing `Company` ctor uses `ArgumentNullException`/`ArgumentOutOfRangeException` instead of `DomainException` — inconsistency to note for future alignment but not blocking design.

## Task-Specific Research — [G1] Design CompanyMembership/User/Role domain entities, events, ports, and repository contracts for multi-company membership and role assignment

### Context & Prior Work
- Existing domain entities already implemented and compliant with patterns:
  - `User` at `src/SmeAccounting.Domain/Entities/User.cs`: global user, no CompanyId. Properties ExternalId, Email, DisplayName, UserName?, IsActive. Private parameterless ctor, public ctor validates ExternalId/Email/DisplayName non-empty, trims ExternalId, lowercases Email, raises `UserCreated(Id, DateTimeOffset.UtcNow)`. `Deactivate()` sets IsActive false.
  - `Role` at `src/SmeAccounting.Domain/Entities/Role.cs`: company-scoped. Properties CompanyId, Code, Name, Description?, IsActive. Validates CompanyId>0, Code/Name required, raises `RoleCreated(Id, CompanyId, DateTimeOffset.UtcNow)`.
  - `CompanyMembership` at `src/SmeAccounting.Domain/Entities/CompanyMembership.cs`: linking aggregate UserId+CompanyId. Properties UserId, CompanyId, IsActive, JoinedAt. Validates ids>0, sets JoinedAt UtcNow, raises `CompanyMembershipCreated(Id, CompanyId, DateTimeOffset.UtcNow)`.
  - `UserRole` at `src/SmeAccounting.Domain/Entities/UserRole.cs`: per-company role assignment. Properties UserId, RoleId, CompanyId, IsActive. Validates ids>0, raises `UserRoleAssigned(Id, CompanyId, DateTimeOffset.UtcNow)`.
- Domain events minimalism confirmed:
  - `UserCreated` carries UserId only.
  - `RoleCreated` carries RoleId + CompanyId.
  - `CompanyMembershipCreated` carries MembershipId + CompanyId.
  - `UserRoleAssigned` carries UserRoleId + CompanyId.
  All events extend `DomainEvent` with `OccurredOn`.
- Ports exist in `Domain/Ports/`:
  - `IUsersRepository`: GetByIdAsync, GetByExternalIdAsync, GetByEmailAsync, GetAllAsync, AddAsync.
  - `IRoleRepository`: GetByIdAsync, GetByCompanyAndCodeAsync, GetAllByCompanyAsync, AddAsync.
  - `ICompanyMembershipRepository`: AddAsync only.
  - `IUserRoleRepository`: AddAsync only.
- EF Configurations follow established patterns:
  - `UserConfiguration`: table `users`, snake_case columns, unique indexes on ExternalId and Email, `xmin` row version.
  - `RoleConfiguration`: table `roles`, CompanyId FK Restrict to Company, unique index (CompanyId,Code), `xmin`.
  - `CompanyMembershipConfiguration`: table `company_memberships`, unique index (UserId,CompanyId), FK Restrict to Company and User, `xmin`.
  - `UserRoleConfiguration`: table `user_roles`, unique index (UserId,RoleId,CompanyId), FK Restrict to Company/User/Role, `xmin`.
- Infrastructure repositories implemented:
  - `EfUsersRepository`: GetByIdAsync, GetByExternalIdAsync, GetByEmailAsync (lowercases), GetAllAsync AsNoTracking, AddAsync.
  - `EfRoleRepository`: GetByIdAsync, GetByCompanyAndCodeAsync, GetAllByCompanyAsync AsNoTracking ordered by Code, AddAsync.
  - `EfCompanyMembershipRepository`: AddAsync only.
  - `EfUserRoleRepository`: AddAsync only.
- DbContext includes DbSets for Users, Roles, CompanyMemberships, UserRoles and ignores domain events in OnModelCreating.
- Global memory 2026-09-21 confirms redesign to Microsoft-first: User global with mandatory ExternalId for Microsoft ObjectId mapping, Email globally unique, CompanyMembership explicit linking aggregate, Role company-scoped, UserRole per-company assignment, domain events minimalism, FK Restrict patterns, build verified 0 warnings 22/22 NetArchTest pass.

### Existing Tools & Resources
- Domain zero NuGet refs, BaseEntity with AddDomainEvent, DomainException hierarchy.
- EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions configured, snake_case naming, xmin concurrency.
- Directory.Build.props enforces net10.0 C#13 nullable implicit usings TreatWarningsAsErrors.
- Architecture tests enforce dependency direction, controllers thin MediatR dispatch.
- Identity adapter in Infrastructure: IdentityUserAdapter mapping, MicrosoftSignInProvider stub, no ASP.NET Identity coupling in Domain.
- Patterns from global memory: FK to Company Restrict universal, composite unique indexes per company, enum string conversion, domain event minimalism Id+CompanyId+OccurredOn, DomainException validation, private parameterless ctor for EF, repositories async AddAsync/GetById/GetByCode, AsNoTracking for reads.

### Requirements & Constraints
- Multi-company membership: User is global, CompanyMembership links User to Company with unique (UserId,CompanyId), IsActive flag, JoinedAt timestamp.
- Role assignment per company: Role is company-scoped with unique (CompanyId,Code). UserRole links User+Role+Company with unique (UserId,RoleId,CompanyId), IsActive flag.
- Microsoft-first integration: User.ExternalId mandatory for Microsoft Entra ObjectId mapping, Email globally unique, no password stored in Domain.
- Company isolation: all company-scoped entities carry CompanyId FK Restrict, composite unique indexes enforce per-company uniqueness, repository queries filter by companyId.
- Domain purity: Domain zero NuGet refs, no ASP.NET Identity coupling, ports in Domain/Ports/, events in Domain/Events/.
- Validation: DomainException for invariants, ExternalId/Email/DisplayName required for User, CompanyId>0 Code/Name required for Role, ids>0 for Membership/UserRole.
- Events minimalism: events carry EntityId + CompanyId + OccurredOn only, no payload duplication. UserCreated carries UserId only.
- EF config pattern: internal sealed class *Configuration : IEntityTypeConfiguration<T>, ToTable(snake_plural), HasKey, HasColumnName per property, HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict), unique indexes, xmin row version.
- Soft delete via IsActive=false, no hard delete.
- Max lengths enforced in EF config: ExternalId 200, Email 200, DisplayName 200, UserName 100, Role Code 50, Name 200, Description 500.
- Repository reads use AsNoTracking, writes via AddAsync, no UpdateAsync, change tracking handles updates.

### Suggested Approach
- Entities already exist and follow patterns; design is complete. Verify consistency with global memory redesign: User global, ExternalId mandatory, Email globally unique, CompanyMembership and UserRole as linking aggregates, Role company-scoped.
- Ensure ports provide sufficient query methods for application use cases: IUsersRepository needs GetByExternalIdAsync/GetByEmailAsync for sign-in; IRoleRepository needs GetByCompanyAndCodeAsync/GetAllByCompanyAsync; ICompanyMembershipRepository may need GetByUserAndCompanyAsync/GetAllByCompanyAsync for future queries; IUserRoleRepository may need GetByUserAndCompanyAsync.
- Keep domain events minimal as implemented.
- Maintain FK Restrict to Company/User/Role, unique indexes, xmin concurrency.
- No new value objects required; primitives sufficient.

### Verification Criteria
- Build succeeds `dotnet build SmeAccounting.sln` zero warnings.
- 22 NetArchTest rules pass.
- Entities extend BaseEntity, private parameterless ctor, public validating ctor with DomainException, raise domain events on construction.
- User has no CompanyId, ExternalId mandatory, Email lowercased, unique indexes on ExternalId and Email.
- Role has CompanyId FK Restrict, unique index (CompanyId,Code).
- CompanyMembership has unique index (UserId,CompanyId), FK Restrict to Company and User, JoinedAt set.
- UserRole has unique index (UserId,RoleId,CompanyId), FK Restrict to Company/User/Role.
- Ports exist with methods listed above.
- EF configurations snake_case, xmin row version, FK Restrict, unique indexes.
- Domain events minimal payload as described.
- No Domain entity references ASP.NET Identity or EF Core.

### Quality Standards
- Follow existing patterns: FK to Company Restrict, composite unique indexes, domain event minimalism, DomainException hierarchy.
- Private parameterless ctor for EF, public ctor with validation.
- Events raised via AddDomainEvent in constructor.
- Repository reads AsNoTracking, writes AddAsync.
- Clean Architecture maintained: Domain zero NuGet, Application references Domain only, Infrastructure references both.
- User global, CompanyMembership explicit linking, Role company-scoped, UserRole per-company assignment.
- No navigation properties exposed on entities; FKs configured in EF only.

### Prior Attempt Analysis
- Global memory 2026-09-21 notes initial design had User company-scoped with CompanyId on User, Email unique per company. Audit identified identity-agnostic requirement for Microsoft Entra sign-in. Redesign applied: User global, ExternalId mandatory, Email globally unique, CompanyMembership created, events simplified. Build verified 0 warnings 22/22 rules pass. Current implementation reflects redesign. No further changes needed for design task; executor can proceed to Application layer commands/queries.

## Application Layer Patterns Research — Company/CompanySetting/Membership/Role/VoucherType/TransactionReason/DocumentNumberingSeries

### Commands
- Record types implementing MediatR IRequest<T>. Example: CreateCompanySettingCommand(CompanyId, LegalRepresentativeName, ...) : IRequest<CreateCompanySettingResult>. Result is record with long Id.
- CreateRoleCommand(CompanyId, Code, Name, Description?) : IRequest<CreateRoleResult>.
- AddCompanyMembershipCommand(UserId, CompanyId) : IRequest<AddCompanyMembershipResult>.
- CreateVoucherTypeCommand(Code, Name, VoucherCategory, CompanyId, Description?) : IRequest<CreateVoucherTypeResult>.
- CreateTransactionReasonCommand(Code, Name, VoucherTypeId, CompanyId, Description?) : IRequest<CreateTransactionReasonResult>.
- CreateDocumentNumberingSeriesCommand(VoucherTypeId, CompanyId, Prefix, PaddingLength, IsDefault, Description?) : IRequest<CreateDocumentNumberingSeriesResult>.
- Company command not present in Application layer; only CompanySetting commands exist.

### Validators
- FluentValidation AbstractValidator<T> per command, namespace SmeAccounting.Application.Validators.
- Rules: RuleFor(x=>x.CompanyId).GreaterThan(0); RuleFor(x=>x.Code).NotEmpty().MaximumLength(20/50); RuleFor(x=>x.Name).NotEmpty().MaximumLength(200); RuleFor(x=>x.VoucherCategory).IsInEnum(); RuleFor(x=>x.PaddingLength).InclusiveBetween(1,10); conditional When for nullable fields.
- ValidationBehavior<TRequest,TResponse> implements IPipelineBehavior, runs all IValidator<T> before handler, throws ValidationException on failures.
- AddValidatorsFromAssembly called in Application DI.

### Handlers
- Internal sealed class with primary constructor injection: repository + IUnitOfWork.
- Implements IRequestHandler<Command, Result>.
- Handle: construct domain entity via public ctor with command values, repository.AddAsync(entity), unitOfWork.SaveChangesAsync(cancellationToken), return new Result(entity.Id).
- Examples: CreateCompanySettingHandler, CreateRoleHandler, AddCompanyMembershipHandler, CreateVoucherTypeHandler, CreateTransactionReasonHandler, CreateDocumentNumberingSeriesHandler.
- Query handlers: IRequestHandler<Query, Dto?>. Fetch via repository.GetByIdAsync / GetAllByCompanyAsync, map manually to DTO via new Dto(...). AsNoTracking used by repository for reads.
- GetRolesByCompanyHandler returns IReadOnlyList<RoleDto> via repository.GetAllByCompanyAsync and Select mapping.

### Queries
- Record types implementing IRequest<Dto> or IRequest<IReadOnlyList<Dto>>.
- CompanySetting: GetCompanySettingByIdQuery(long Id), GetCompanySettingByCompanyIdQuery(long CompanyId).
- Role: GetRolesByCompanyQuery(long CompanyId).
- VoucherType: GetVoucherTypeQuery(long VoucherTypeId), GetVoucherTypesByCompanyQuery(long CompanyId).
- TransactionReason: GetTransactionReasonsByVoucherTypeQuery, pattern similar.
- No Company query found; CompanySetting queries exist.

### DTOs
- Records in SmeAccounting.Application.DTOs, no domain references.
- CompanySettingDto(Id, CompanyId, LegalRepresentativeName, LegalRepresentativeTaxId, ChiefAccountantName?, ChiefAccountantTaxId?, FiscalYearStartMonth?, Currency?, ReportingSettingsJson?).
- RoleDto(Id, CompanyId, Code, Name, Description?, IsActive).
- VoucherTypeDto(Id, Code, Name, VoucherCategory as string, CompanyId, IsActive, Description?). Enum mapped via string.
- TransactionReasonDto(Id, Code, Name, VoucherTypeId, CompanyId, IsActive, Description?).
- DocumentNumberingSeriesDto(Id, VoucherTypeId, CompanyId, Prefix, NextNumber, PaddingLength, IsDefault, IsActive, Description?).
- Mapping is manual in handlers, no AutoMapper used.

### Cross-Entity Patterns
- All commands/validators/handlers follow same structure: command record → validator → handler constructs domain entity → repo Add → UoW Save.
- Company isolation enforced via CompanyId >0 validation and repository methods filtered by company.
- DTOs mirror entity properties, private set not exposed.
- No Application layer for Company creation yet; existing Company entity domain only.
- Membership query DTO not found; only command for AddCompanyMembership exists.
- Validation messages provided for user feedback, max lengths match EF config.
- Clean Architecture maintained: Application references Domain and MediatR/FluentValidation only, no EF Core.

## Infrastructure Identity Integration — Microsoft Entra Adapter Research
### Files Discovered
- `src/SmeAccounting.Infrastructure/Adapters/IdentityUserAdapter.cs`
- `src/SmeAccounting.Infrastructure/Adapters/MicrosoftSignInProvider.cs`
- `src/SmeAccounting.Infrastructure/DependencyInjection.cs`
- `src/SmeAccounting.Api/Program.cs`

### IdentityUserAdapter Mapping
- Static class `IdentityUserAdapter` provides bidirectional mapping between Domain `User` entity and placeholder `IdentityUserModel`.
- `IdentityUserModel` record: `string Id, string UserName, string Email, bool EmailConfirmed`.
- `ToIdentityUser(User user)` returns model with:
  - Id = `user.Id.ToString()`
  - UserName = `user.UserName ?? user.Email`
  - Email = `user.Email`
  - EmailConfirmed = `false`
- `ToDomainUser(IdentityUserModel identityUser)` constructs `new User(externalId: identityUser.Id, email: identityUser.Email, displayName: identityUser.UserName)`. Note mapping assumes Identity User Id → Domain User ExternalId; DisplayName populated from UserName fallback.
- No ASP.NET Core Identity package reference in Domain; adapter lives in Infrastructure, keeping Domain pure.
- Adapter is static; not registered in DI container.

### Microsoft Entra Adapter — IMicrosoftSignInProvider
- Interface defined in `MicrosoftSignInProvider.cs`:
  - `Task<bool> ValidateTokenAsync(string token, CancellationToken cancellationToken = default)`
  - `Task<string?> GetExternalIdAsync(string token, CancellationToken cancellationToken = default)`
- Implementation `MicrosoftSignInProvider` is placeholder stub:
  - `ValidateTokenAsync` returns `!string.IsNullOrWhiteSpace(token)` with TODO comment to integrate `Microsoft.Identity.Web` token validation.
  - `GetExternalIdAsync` returns `null` with TODO to extract object identifier from Microsoft token claims.
- Registered in Infrastructure DI:
  - `services.AddScoped<IMicrosoftSignInProvider, MicrosoftSignInProvider>();` at `DependencyInjection.cs:73`
- No configuration binding for Entra tenant/client ID, authority, scopes observed. No `Microsoft.Identity.Web` package reference found in solution.

### DI Registration Summary
- Infrastructure `AddInfrastructure` registers DbContext, UnitOfWork, repositories for all domain aggregates including `IUsersRepository`, `IRoleRepository`, `IUserRoleRepository`, `ICompanyMembershipRepository`, `ICompanySettingRepository`.
- Adapters registered:
  - `IClock` → `SystemClock`
  - `IAuditLogger` → `AuditLogger`
  - `IForeignExchangeRateProvider` → `BankExchangeRateProvider`
  - `IMicrosoftSignInProvider` → `MicrosoftSignInProvider` (stub)
- `IdentityUserAdapter` static, not registered.
- Application `AddApplication` registers MediatR, ValidationBehavior, FluentValidation validators.

### Authentication Pipeline Stubs
- `src/SmeAccounting.Api/Program.cs`:
  - `builder.Services.AddAuthentication("PlaceholderScheme");`
  - `builder.Services.AddAuthorization();`
  - Middleware pipeline includes `app.UseAuthentication();` `app.UseAuthorization();`
- No authentication scheme configured: no JWT Bearer, Cookie, OpenID Connect handlers registered.
- No `Microsoft.Identity.Web` or `AddMicrosoftIdentityWebApi` call.
- No authentication controller endpoints found; no usage of `IMicrosoftSignInProvider` in Api layer via grep.
- Domain `User` entity is global with mandatory `ExternalId` for Microsoft ObjectId mapping, Email globally unique, no password storage in Domain, consistent with Microsoft-first design.
- Clean Architecture maintained: Domain has zero NuGet refs, no ASP.NET Identity coupling; authentication concerns isolated to Infrastructure adapters.

### Gaps / TODOs
- Token validation not implemented; `ValidateTokenAsync` only checks non-empty string.
- ExternalId extraction not implemented; `GetExternalIdAsync` returns null.
- No mapping from Microsoft Entra claims to Domain User creation / sign-in flow.
- No DI registration for `IdentityUserAdapter` as service; static usage only.
- Authentication pipeline placeholder scheme will reject all requests; production requires OpenID Connect / JWT bearer configuration and Entra app registration.
- No secrets/configuration for Entra tenant/client ID; appsettings.json contains only DB connection string.
- No integration tests for sign-in flow.

### Verification Notes
- Build succeeds with current stubs; architecture tests pass.
- Domain purity preserved: no Identity package leakage to Domain.
- Adapter pattern aligns with existing Infrastructure adapters (`BankExchangeRateProvider`, `EInvoiceProviderAdapter`, `DigitalSignatureAdapter`) as architecture placeholders.

## Security Review & Test Gap Analysis — 2026-09-21

### Architecture Tests
- Present only in `tests/SmeAccounting.ArchitectureTests/` — 5 files, 22 NetArchTest facts:
  - `DependencyRulesTests.cs`: Domain→Application/Infrastructure/Api forbidden; Application→Infrastructure/Api forbidden; Infrastructure→Api forbidden; Api Controllers→Infrastructure forbidden.
  - `DomainPurityTests.cs`: Domain csproj has zero PackageReference; no Microsoft./Npgsql./Serilog./EFCore. packages; Domain assembly has no dependency on Microsoft.EntityFrameworkCore.
  - `LayerCouplingTests.cs`: Api.Controllers must not reference Domain.Entities or Domain.Ports; Application handlers must not reference Infrastructure; Infrastructure must not reference Api.
  - `NamingConventionsTests.cs`: BaseEntity inheritors in Domain.Entities; Repository interfaces start with I; Commands/Queries end with Command/Query; DTOs end with Dto; Controllers end with Controller.
  - `PostingRuleIsolationTests.cs`: IPostingService, JournalEntry, Money reside in Domain assembly.
- Security relevance: enforces Clean Architecture boundaries, prevents accidental leakage of EF/Identity into Domain. No tests for authorization, input validation, secret management, or controller security attributes.
- Gap: no automated tests for authentication/authorization enforcement, no tests ensuring controllers are decorated with [Authorize], no tests for secure coding patterns.

### Domain Validation Unit Tests
- Search of `tests/` shows only ArchitectureTests project. No `SmeAccounting.Domain.Tests` or similar.
- Domain entities `Company`, `User`, `Role`, `CompanyMembership`, `DocumentNumberingSeries`, `VoucherType`, `TransactionReason` implement constructors with `DomainException` validation.
- No unit tests verify:
  - Constructor invariants e.g., `Company` FiscalYearStartMonth 1-12, `DocumentNumberingSeries` PaddingLength 1-10, Prefix required.
  - Domain methods `Deactivate()`, `Reset()`, `Increment()` behavior and exception paths.
  - Event raising on construction.
- Security relevance: validation gaps allow malformed data to propagate if Application layer validation is bypassed. Lack of unit tests means invariants are not contractually verified.
- Finding: Domain validation is present in code but untested.

### Integration Tests for Repositories
- No integration test project discovered. `tests/` contains only ArchitectureTests.
- Repository implementations exist:
  - `EfDocumentNumberingSeriesRepository`: `GetByIdAsync`, `GetDefaultAsync`, `GetAllByCompanyAsync`, `AddAsync`.
  - Similar `EfUsersRepository`, `EfRoleRepository`, `EfCompanyMembershipRepository`, `EfUserRoleRepository`.
- No tests for:
  - EF Core mapping correctness (snake_case, xmin row version).
  - Unique constraints enforcement `(CompanyId,Code)`, `(VoucherTypeId,CompanyId,Prefix)`.
  - FK Restrict behavior on delete.
  - Query filtering by `CompanyId`.
- Security relevance: repository layer is trust boundary for data isolation. Without integration tests, company isolation regressions and data leakage risks are undetected.
- Finding: Zero repository integration tests.

### Concurrency Safety Verification for DocumentNumberingSeries
Entity: `src/SmeAccounting.Domain/Entities/DocumentNumberingSeries.cs`
- Properties: `VoucherTypeId`, `CompanyId`, `Prefix`, `NextNumber`, `PaddingLength`, `IsDefault`, `IsActive`, `Description`.
- Methods:
  - `Increment()`: `NextNumber++` — no concurrency control, no event.
  - `Reset(int startFrom)`: validates `startFrom >0`, sets `NextNumber`.
  - `Deactivate()`.
- EF Configuration: `DocumentNumberingSeriesConfiguration.cs`
  - Table `document_numbering_series`, unique index `(VoucherTypeId,CompanyId,Prefix)`, FK Restrict to Company/VoucherType, `xmin` row version concurrency token.
- Repository: `EfDocumentNumberingSeriesRepository` uses EF Core change tracking; `GetByIdAsync` returns tracked entity, `AddAsync` adds.
- Usage:
  - `CreateDocumentNumberingSeriesHandler` creates new series.
  - `ResetNumberingSeriesHandler` loads entity, calls `Reset`, `unitOfWork.SaveChangesAsync`.
  - `Increment()` is defined but never invoked in Application layer (`grep` finds 1 match, definition only).
- Concurrency analysis:
  - Optimistic concurrency via `xmin` exists at EF level; `SaveChangesAsync` will throw `DbUpdateConcurrencyException` on conflicting updates.
  - No explicit locking or transactional increment-and-read pattern for generating voucher numbers.
  - No handler demonstrates atomic "fetch next number, increment, persist, return formatted number" sequence.
  - No tests verifying concurrent increment scenarios, no retry logic, no `FOR UPDATE` pessimistic lock usage.
- Security/Integrity risk: Under concurrent voucher creation, two requests may read same `NextNumber`, both generate same document number before save, leading to duplicate numbers or lost increments. `xmin` will detect concurrent modification on save, causing exception but no recovery strategy.
- Recommendations:
  - Implement number generation in a dedicated domain service with pessimistic lock or serializable transaction.
  - Add integration tests simulating concurrent `Increment` calls.
  - Consider raising domain event on increment for audit trail.
  - Ensure repository method for "get and lock" series.

### Security Review Summary
- Hard-coded connection string in `appsettings.json`: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`.
- No secrets management, no user-secrets, no environment variable binding.
- Authentication placeholder: `AddAuthentication("PlaceholderScheme")` with no scheme configured; `MicrosoftSignInProvider` stub returns dummy validation.
- No authorization attributes on controllers observed; `HomeController` etc. thin MediatR dispatch without `[Authorize]`.
- No input sanitisation tests; FluentValidation present but not tested.
- No audit logging tests; `IAuditLogger` adapter exists but not verified.
- Domain events dispatch after `SaveChangesAsync` but no tests for event integrity.

