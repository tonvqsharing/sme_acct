# Research Log
## Context & Prior Work
### Global Environment & Tools
- .NET SDK 10.0.401, ASP.NET Core Runtime 10.0.12, .NET Runtime 10.0.12
- dotnet-ef 10.0.12, PostgreSQL 18.4, git 2.51.0
- Directory.Build.props enforces net10.0, C#13, nullable enabled, implicit usings, TreatWarningsAsErrors=true
- NuGet sources: nuget.org enabled
- Project packages: Domain zero NuGet, Application MediatR 14.2.0 + FluentValidation 12.1.0, Infrastructure EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions, Api Swashbuckle 10.2.3

### Codebase Structure — Clean Architecture
Solution: SmeAccounting.sln
Layers:
- Domain (src/SmeAccounting.Domain) — pure library, zero NuGet refs, entities, value objects, events, exceptions, ports
- Application (src/SmeAccounting.Application) — MediatR commands/queries, FluentValidation, DTOs, references Domain only
- Infrastructure (src/SmeAccounting.Infrastructure) — EF Core PostgreSQL, repositories, adapters, references Application + Domain
- Api (src/SmeAccounting.Api) — ASP.NET MVC controllers thin MediatR dispatch, references Application + Infrastructure
- ArchitectureTests (tests/SmeAccounting.ArchitectureTests) — 22 NetArchTest rules enforcing dependency direction

Dependency direction enforced: Api → Application → Domain; Infrastructure → Application + Domain; Domain has zero NuGet refs. Controllers must not reference Domain.Entities or Domain.Repositories.

### Domain Layer Patterns
- BaseEntity with long Id, xmin concurrency token
- Private parameterless constructor for EF Core materialization + public constructor with required params and invariant validation via DomainException hierarchy
- Domain events raised in constructors: {Entity}Created(EntityId, CompanyId, OccurredOn). Event minimalism: ID + CompanyId only
- Port interfaces in Domain/Ports/: IAccountRepository, IJournalEntryRepository, IUnitOfWork, IForeignExchangeRateProvider, IAuditLogger, IPostingService, IClock, plus company-scoped repos
- Value objects in Domain/ValueObjects/: Money, AccountCode, NormalBalance, AccountType, PeriodStatus, FiscalYearStatus, PeriodType, ExchangeRateType, FilingFrequency, TaxPeriodStatus, TaxTreatmentType, TaxCategory, TaxAuthorityLevel, TaxAccountingMappingType, VoucherCategory, PaymentTermType, Currency (VO record not used as type)
- Enums stored as string via HasConversion<string>() in EF configs
- Soft delete via IsActive=false, never hard delete
- FK to Company pattern universal: HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)
- Composite unique indexes for per-company uniqueness: (CompanyId, Code) for dimensions, (CompanyId, FromCurrencyCode, ToCurrencyCode, RateType, EffectiveDate) for exchange rates
- String over FK for currency codes: Money uses string Currency, entities store FromCurrencyCode/ToCurrencyCode as string

### Existing Domain Entities (post P1-P4)
Entities/:
Account, AccountGroup, BaseEntity, Company, CostCenter, Currency, Customer, Department, DocumentNumberingSeries, Employee, ExchangeRate, FiscalPeriod, FiscalYear, JournalEntry, JournalEntryLine, OpeningBalanceMapping, PaymentTerm, PostingConfiguration, PostingReference, Project, Supplier, TaxAccountingMapping, TaxAuthority, TaxExemptionReason, TaxPeriod, TaxRate, TaxRule, TaxTreatment, TaxType, TransactionReason, VoucherType

ValueObjects/:
NormalBalance, PeriodType, FilingFrequency, TaxTreatmentType, AccountCode, VoucherCategory, AccountType, PeriodStatus, TaxAccountingMappingType, TaxCategory, Currency, TaxAuthorityLevel, ExchangeRateType, FiscalYearStatus, Money, TaxPeriodStatus, PaymentTermType

Events/:
DomainEvent base, AccountCreated, AccountDeprecated, CompanyCreated, CurrencyCreated, DepartmentCreated, CostCenterCreated, ProjectCreated, ExchangeRateRecorded, FiscalYearCreated, JournalEntryPosted, PeriodClosed, TaxPeriodCreated, TaxPeriodClosed, TaxRateCreated, TaxRuleCreated, TaxExemptionReasonCreated, TaxAuthorityCreated, TaxTreatmentCreated, TaxTypeCreated, TransactionReasonCreated, VoucherTypeCreated, CustomerCreated, SupplierCreated, EmployeeCreated, PaymentTermCreated, etc.

Ports/:
IAccountRepository, IJournalEntryRepository, IUnitOfWork, IForeignExchangeRateProvider, IAuditLogger, IPostingService, IClock, ICompanyRepository, ICurrencyRepository, IExchangeRateRepository, IDepartmentRepository, ICostCenterRepository, IProjectRepository, IVoucherTypeRepository, ITransactionReasonRepository, ITaxTypeRepository, ITaxTreatmentRepository, ITaxAuthorityRepository, ITaxRateRepository, ITaxRuleRepository, ITaxExemptionReasonRepository, ITaxPeriodRepository, ITaxAccountingMappingRepository, ICustomerRepository, ISupplierRepository, IEmployeeRepository, IPaymentTermRepository, IDocumentNumberingSeriesRepository, IOpeningBalanceMappingRepository, IPostingConfigurationRepository

### P1-P4 Implementation Summary
P1-P4 correspond to completed loops:
- accounting-foundation-build_DONE: Company, Currency entities; FiscalYear/FiscalPeriod extensions; ExchangeRate; Department/CostCenter/Project dimensions; JournalEntryLine dimension FKs; FK to Company pattern; composite unique indexes; AccountingFoundation migration
- accounting-control-config_DONE: PostingConfiguration, OpeningBalanceMapping, DocumentNumberingSeries, TransactionReason, VoucherType extensions
- phase3-tax-foundation_DONE: TaxType, TaxTreatment, TaxAuthority, TaxRate, TaxRule, TaxExemptionReason, TaxPeriod, TaxAccountingMapping; enums TaxCategory, TaxTreatmentType, TaxAuthorityLevel, FilingFrequency, TaxPeriodStatus; effective-date patterns; legal reference requirements
- phase4-business-partner_DONE: Customer, Supplier, Employee, PaymentTerm; PaymentTermType enum; optional PaymentTermId/DefaultTaxTypeId on Supplier; EmployeeNumber/HireDate; GetAllByCompanyAsync pattern; repositories implemented with AsNoTracking; Application CQRS with Create/Deactivate commands, FluentValidation, DTOs; API controllers thin MediatR dispatch; ViewModels with DataAnnotations; DI registration; BusinessPartnerFoundation migration pending

### EF Core & Infrastructure Patterns
- Naming conventions: EFCore.NamingConventions, snake_case tables/columns
- Configurations: one *Configuration.cs per entity in Infrastructure/Persistence/Configurations/, IEntityTypeConfiguration<T>, ToTable(snake_plural), HasKey, HasColumnName, HasConversion<string>() for enums, HasOne<Company> Restrict, composite unique indexes, xmin row version last
- DbContext: DbSet<T> per entity, modelBuilder.Ignore<Event>() for all domain events
- Repositories: Ef*Repository per entity, constructor-injected DbContext, async CRUD, AsNoTracking for reads, AddAsync delegates to DbSet, no UpdateAsync (change tracking)
- Migrations: InitialCreate, FixAccountNameColumn, AccountingFoundation, Phase2AccountingControlConfig, Phase3TaxFoundation, BusinessPartnerFoundation (pending). Single migration per cohesive feature
- Backfill note: defaultValue:0L on non-nullable company_id columns for existing rows

### Application Layer Patterns
- Commands/queries as record types implementing IRequest<T>, MediatR 14.x
- ValidationBehavior<TRequest,TResponse> as IPipelineBehavior runs all IValidator<T> before handler, throws ValidationException
- AddValidatorsFromAssembly requires using FluentValidation.DependencyInjectionExtensions
- DTOs as plain records, no domain entity references, enums mapped via .ToString()
- BalanceSheetDto/IncomeStatementDto use AccountGroupTotal(GroupName, Total, Currency)
- IAccountingReportService port in Application, Infrastructure implements
- CreateJournalEntryCommand carries IReadOnlyList<JournalEntryLineInput>, domain creates Money from inputs
- DI registration via AddApplication() extension: MediatR assembly scan + open validation behavior + validators

### Test Patterns
- ArchitectureTests: 22 NetArchTest rules
  - Domain purity: no NuGet PackageReference, no Microsoft./Npgsql./Serilog./EFCore. packages, no EF Core assembly dependency
  - Layer coupling: Api cannot reference Domain.Entities/Repositories, Application cannot reference Infrastructure, Domain cannot reference Application/Infrastructure
  - Naming conventions, posting rule isolation
- No unit tests for domain entities yet; architecture tests enforce Clean Architecture constraints
- Build verification: dotnet build SmeAccounting.sln succeeds 0 warnings 0 errors
- Architecture tests pass 22/22 after each loop

### Regulatory & Domain Context
- VAS Vietnamese Accounting Standards, Circular 99/2025/TT-BTC compliance
- Chart of Accounts: 9 categories, 4-digit Level 1 hierarchy, 25+ key account codes
- E-invoice XML legally binding, TVAN providers as adapters
- IFRS transition via Decision 345, IAccountingPolicy abstraction
- Tax legislation: VAT Law 48/2024/QH15, CIT Law 67/2025/QH15, PIT Law 109/2025/QH15, Circular 99/2025/TT-BTC effective 2026-01-01
- Key distinction: 0% VAT rate deductible vs VAT-exempt non-deductible

### Patterns to Reuse for Product & Inventory Foundation
- Entity pattern: CompanyId + Code + Name + IsActive + optional Description, private parameterless ctor, public ctor validates CompanyId>0, Code/Name non-whitespace, DomainException, AddDomainEvent with Id 0 at construction
- EF config pattern: internal sealed class XxxConfiguration : IEntityTypeConfiguration<T>, ToTable(snake_plural), HasKey, column mappings, HasConversion<string>() for enums, HasOne<Company> Restrict, composite unique index (CompanyId, Code), xmin row version
- Repository pattern: EfXxxRepository implements IXxxRepository, GetById/GetByCode tracked, GetAllByCompanyAsync AsNoTracking, AddAsync delegates to DbSet
- Event pattern: XxxCreated(EntityId, CompanyId, OccurredOn) minimal
- Port interface: GetByCodeAsync(code, companyId), GetAllByCompanyAsync
- Backwards-compatible expansion: add params at end with defaults
- Soft delete via Deactivate() no event initially
- Max lengths: Code=20, Name=200, Description=500 enforced in EF config

## External Knowledge & Resources

### Documentation & Architecture Decisions
- **No README.md** found in repo root. Project documentation lives in `docs/` and loop-stack archives.
- `docs/architecture/ADR-010-tax-foundation-regulatory-traceability.md` — Phase 3 tax foundation ADR with regulatory traceability matrix, domain model, architecture compliance. Date 2026-09-17, Status Accepted.
- `loop-stack/vietnamese-acct-architecture_DONE/docs/architecture/`:
  - `ADR-001-clean-architecture.md` — Clean Architecture with dependency inversion, Domain zero NuGet, Api→Application→Domain, enforced by NetArchTest.
  - `ADR-002-cqrs-mediatr.md` — CQRS with MediatR 14.2.0, commands/queries, FluentValidation pipeline, handlers.
  - `ADR-003-posting-seam.md` — Accounting posting as domain service `IPostingService`, business modules raise events → handler invokes posting, validates debit=credit, period open, immutable after post.
- `loop-stack/vietnamese-acct-architecture_DONE/docs/regulatory/`:
  - `VAS-compliance.md` — Mapping of all 26 VAS standards to domain modules, applicability Core/Medium/Low, traceability matrix, IFRS transition gaps.
  - `Circular99-mapping.md` — Circular 99/2025/TT-BTC Art.28 software requirements → Architecture layers, Chart of Accounts changes, posting rules, fiscal period requirements, e-invoice integration, traceability matrix.
  - `ChartOfAccounts-structure.md` — 9 main categories, 4-digit Level1 hierarchy, key account codes 111,112,133,156,333,82112 etc., extensibility rules Art.25, Account entity design.
  - `EInvoice-integration.md` — Decree 123/2020 & Decree 70/2025 requirements, XML legally binding, TVAN provider adapter pattern, `IEInvoiceProvider` and `IDigitalSignatureService` port interfaces, request/response models, provider list Viettel/MISA/BKAV/VNPT/FPT/M-Invoice.
  - `IFRS-transition-roadmap.md` — exists, referenced for abstraction design.

### Configuration Examples
- `src/SmeAccounting.Api/appsettings.json`:
  ```json
  {
    "ConnectionStrings": {
      "DefaultConnection": "Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456"
    },
    "Logging": { "LogLevel": { "Default": "Information", "Microsoft.AspNetCore": "Warning" } },
    "AllowedHosts": "*"
  }
  ```
- `src/SmeAccounting.Api/appsettings.Development.json`: `DetailedErrors: true`, logging levels.
- `Directory.Build.props` at repo root:
  - TargetFramework net10.0, Nullable enable, ImplicitUsings enable, LangVersion 13, TreatWarningsAsErrors true
- `.editorconfig`:
  - 4-space indent, LF line endings, UTF-8, trim trailing whitespace
  - csproj/props indent 2, json/yaml indent 2
  - Private fields `_camelCase` enforced, var preferred, expression-bodied members suggestions
- No `.env.example` found in repo.

### External APIs & Integrations
- **E-Invoice TVAN providers** — port/adapter pattern:
  - `IEInvoiceProvider.SubmitAsync`, `GetStatusAsync`
  - Providers: Viettel ~40%, MISA ~25%, BKAV ~10%, VNPT ~10%, FPT ~8%, M-Invoice ~5%
  - XML format mandatory, digital signature mandatory, 10-year retention
- **Digital Signature**: `IDigitalSignatureService.SignAsync`, `VerifyAsync` — GDT-approved certificate USB token/cloud HSM
- **Regulatory data sources** referenced in global TOOLS.md:
  - congbao.chinhphu.vn, thuvienphapluat.vn, luatvietnam.vn, vanban123.vn
  - PwC Worldwide Tax Summaries, Vietnam Briefing, EY Tax Updates, MISA SME Accounting

### Regulatory Requirements
- **Circular 99/2025/TT-BTC** effective 01/01/2026 — software requirements Art.28(a)-(e), COA changes, posting rules, fiscal period lifecycle
- **VAS** 26 standards mapped, Core standards: VAS 01,02,03,04,10,14,17,21,24,29
- **Tax Laws**:
  - VAT Law 48/2024/QH15 effective 01/07/2025 — 10%/8%/5%/0% rates, 0% vs exempt distinction
  - CIT Law 67/2025/QH15 effective 01/10/2025 — 20%/15%/17%
  - PIT Law 109/2025/QH15 effective 01/07/2026 — 5/10/20/30/35% brackets
- **Decree 123/2020** e-invoice mandatory, Decree 70/2025 updates
- Traceability matrices link legal source → article → domain entity → test

### P1-P4 Documentation References
- P1 Accounting Foundation, P2 Accounting Control Config, P3 Tax Foundation, P4 Business Partner — documented in global MEMORY.md and RESEARCH.md Context & Prior Work
- Existing entities post P1-P4: Account, AccountGroup, JournalEntry, JournalEntryLine, FiscalYear, FiscalPeriod, PostingReference, Company, Currency, ExchangeRate, Department, CostCenter, Project, VoucherType, DocumentNumberingSeries, TransactionReason, TaxType, TaxTreatment, TaxAuthority, TaxRate, TaxRule, TaxExemptionReason, TaxPeriod, TaxAccountingMapping, Customer, Supplier, Employee, PaymentTerm
- Architecture tests 22/22 pass, Clean Architecture enforced

### Skill Documentation
Global TOOLS.md lists relevant skills for Phase 3: domain-modeling, ubiquitous-language, source-driven-development, test-driven-development, implement, incremental-implementation, code-review-and-quality, doubt-driven-development, documentation-and-adrs, planning-and-task-breakdown, security-and-hardening.
## Requirements & Constraints

### DB Schema Patterns from P1-P4

**Base entity & audit**
- All entities inherit `BaseEntity` with `long Id` and domain event collection.
- EF Core concurrency token: `xmin` row version (`Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")`) on every table.
- Private parameterless constructor for EF materialization; public constructor validates invariants and throws `DomainException`.
- No hard delete: soft delete via `IsActive` boolean, `Deactivate()` sets `IsActive=false`. No delete events initially.

**Company scoping & FKs**
- Every master data entity is company-scoped: non-nullable `long CompanyId`.
- FK pattern universal: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`. No navigation property on entity.
- Multi-FK entities use Restrict for all references, e.g., `TaxRule` links Company + TaxType + TaxRate + TaxTreatment all Restrict.
- Optional dimension FKs on transactional lines use `SetNull` (JournalEntryLine Department/CostCenter/Project).

**Naming & conventions**
- Tables/columns snake_case via `EFCore.NamingConventions`. `ToTable("snake_plural")`, `HasColumnName("snake_case")`.
- Enums stored as string: `HasConversion<string>()`. Enums live in `Domain/ValueObjects/`.
- Currency codes stored as string, not FK to Currency entity. `Money` VO uses `string Currency`.

**Uniqueness & constraints**
- Per-company unique code: composite unique index `(CompanyId, Code)` on all master entities. Example: Department, Customer, TaxRule.
- Composite unique indexes also used for natural keys: `(CompanyId, FromCurrencyCode, ToCurrencyCode, RateType, EffectiveDate)` for ExchangeRate; `(CompanyId, TaxTypeId, RateValue, EffectiveFrom)` for TaxRate.
- Max lengths enforced in EF config, not domain: `Code` typically 20, `Name` 200, `Description` 500. Department Code 50 in early pattern.
- Required fields: `CompanyId > 0`, `Code` non-whitespace, `Name` non-whitespace validated in constructor.

**Domain model invariants**
- Entity pattern: `CompanyId + Code + Name + IsActive + optional Description`. Some entities add extra required fields e.g., `TaxRule` adds `LegalReference` required, `EffectiveFrom`.
- Domain events minimal: `{Entity}Created(EntityId, CompanyId, OccurredOn)`. Event raised in constructor with provisional Id=0.
- Backwards-compatible expansion: add optional params at end with defaults, no breaking changes.
- Repository pattern: `GetById`, `GetByCodeAsync(code, companyId)`, `GetAllByCompanyAsync` with `AsNoTracking()`. No `UpdateAsync`; change tracking handles updates.

**Application & infrastructure patterns**
- CQRS with MediatR 14.x, commands/queries as records, `ValidationBehavior` pipeline runs FluentValidation before handler.
- DTOs plain records, no domain references, enums via `.ToString()`.
- DI: `AddApplication()` scans MediatR + validators; repositories registered `AddScoped<IXxx, EfXxx>()`.
- Migrations: one per cohesive feature, descriptive name, build must succeed before `dotnet ef migrations add`.

### Product & Inventory Foundation Specific Constraints

Components: UOM, UOM Conversion, Item Category, Item/Product, Service Item, Warehouse, Inventory Valuation Policy, Inventory Adjustment Reason, Inventory Accounting Configuration.

**Common master data invariants**
- All master entities must have `CompanyId`, `Code`, `Name`, `IsActive`, optional `Description`.
- `Code` unique per company via DB unique index `(CompanyId, Code)`. Application-level duplicate check via `GetByCodeAsync`.
- Soft delete only; never hard delete for audit trail.
- DomainException for invariant violations: CompanyId>0, Code/Name non-whitespace.
- Private parameterless ctor + public ctor with validation + `AddDomainEvent(new XxxCreated(Id, CompanyId, DateTimeOffset.UtcNow))`.

**UOM**
- Code unique per company. Name required. IsActive soft delete.
- Optional attributes: Symbol, Description. No FKs.

**UOM Conversion**
- Links two UOMs within same company. FKs: `CompanyId`, `FromUomId`, `ToUomId`. Both UOM FKs Restrict.
- Conversion factor decimal >0. Unique index per company: `(CompanyId, FromUomId, ToUomId)`.
- Invariant: FromUomId != ToUomId, factor >0.

**Item Category**
- Hierarchical category tree. Fields: `CompanyId`, `Code`, `Name`, `ParentCategoryId` nullable self-reference Restrict, `IsActive`.
- Unique `(CompanyId, Code)`. Optional `Description`.
- Invariant: no circular parent reference; parent must belong to same company if present.

**Item/Product**
- Master item for inventory. Fields: `CompanyId`, `Code`, `Name`, `ItemCategoryId` nullable FK Restrict, `UomId` FK Restrict, `IsStockItem` bool, `IsServiceItem` bool mutually exclusive? Service Item separate entity.
- Unique `(CompanyId, Code)`. Optional `Description`, `TaxTypeId`, `DefaultWarehouseId`.
- Invariant: if `IsStockItem` true then `UomId` required; `IsServiceItem` true implies non-stock.

**Service Item**
- Non-inventory service offering. Fields: `CompanyId`, `Code`, `Name`, `UomId` optional, `IsActive`, `Description`.
- Unique `(CompanyId, Code)`. May share code space with Item? Separate table.

**Warehouse**
- Physical location. Fields: `CompanyId`, `Code`, `Name`, `Address` optional, `IsActive`, `Description`.
- Unique `(CompanyId, Code)`. Invariant: Code non-whitespace.

**Inventory Valuation Policy**
- Company-scoped policy selection. Fields: `CompanyId`, `Code`, `Name`, `ValuationMethod` enum (FIFO/LIFO/WeightedAverage), `IsActive`, `Description`.
- Unique `(CompanyId, Code)`. Enum stored as string.

**Inventory Adjustment Reason**
- Reason codes for inventory adjustments. Fields: `CompanyId`, `Code`, `Name`, `IsActive`, `Description`.
- Unique `(CompanyId, Code)`. Legal/audit reference optional.

**Inventory Accounting Configuration**
- Links inventory movements to accounting. Fields: `CompanyId`, `Code`, `Name`, `InventoryAssetAccountId` FK to Account Restrict, `COGSAccountId` FK to Account Restrict, `ValuationPolicyId` FK Restrict, `IsActive`, `Description`.
- Unique `(CompanyId, Code)`. Invariant: both account FKs must belong to same company; accounts must be active.

**State management**
- All entities use `IsActive` flag for soft delete. No status workflow beyond active/inactive unless domain requires (e.g., Valuation Policy may be default).
- Audit via domain events and `xmin` concurrency. No explicit CreatedAt/UpdatedAt columns in current patterns.
- FK to Company mandatory for all; DeleteBehavior.Restrict prevents orphaning.

**Quality standards**
- Follow existing entity checklist: Entity file, Enum in ValueObjects, Event, Port, EF Configuration, Repository.
- EF config: `ToTable`, `HasKey`, column mappings, `HasConversion<string>()` for enums, `HasOne<Company>` Restrict, composite unique index, `xmin`.
- Repository: tracked reads for GetById/GetByCode, AsNoTracking for lists.
- Max lengths: Code 20, Name 200, Description 500 unless domain requires longer.
- Architecture tests must remain 22/22 passing; Domain zero NuGet refs; Controllers must not reference Domain.Entities.

## Environment & Integration

### Build & Toolchain
- .NET SDK 10.0.401, ASP.NET Core Runtime 10.0.12, .NET Runtime 10.0.12
- dotnet-ef 10.0.12, roslyn-language-server 5.12.0-1.26426.8
- Directory.Build.props: TargetFramework net10.0, C# 13, Nullable enable, ImplicitUsings enable, TreatWarningsAsErrors true
- Build command: `dotnet build SmeAccounting.sln` — primary verification, warnings-as-errors enforced
- No linting, codegen, or migration steps defined; build is primary verification
- Project packages: Domain zero NuGet, Application MediatR 14.2.0 + FluentValidation 12.1.0, Infrastructure EF Core 10.0.4 + Npgsql 10.0.3 + EFCore.NamingConventions, Api Swashbuckle 10.2.3

### Test Commands
- Architecture constraint tests: `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22 NetArchTest rules
- No unit/integration test commands documented; architecture tests are the enforced quality gate
- Build must succeed before EF Core migration generation

### EF Core Migrations Workflow
- Add migration: `dotnet ef migrations add <Name> --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- Update database: `dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- List migrations: `dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- Pre-requisite: build must succeed before migration generation
- Naming: descriptive feature name, single migration per cohesive feature
- Existing migrations: 20260916051341_InitialCreate, 20260916051520_FixAccountNameColumn, 20260916083803_AccountingFoundation, 20260917013843_Phase2AccountingControlConfig

### PostgreSQL Connection & Infrastructure
- PostgreSQL 16.14 via EF Core on Windows host `172.21.208.1`
- Connection string in `src/SmeAccounting.Api/appsettings.json`:
  `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`
- Connect from Kali: `PGPASSWORD=123456 psql -h 172.21.208.1 -U dev -d sme_acct_dev`
- Naming: EFCore.NamingConventions snake_case tables/columns
- Concurrency: `xmin` row version on all entities
- No Docker setup found in repo; `docker` CLI not installed per global TOOLS.md

### Docker Setup
- No Dockerfile, docker-compose.yml, or container configuration discovered in repo
- Global TOOLS.md lists `docker` as Not Available
- Infrastructure currently relies on external PostgreSQL host 172.21.208.1; no containerized database or app defined

### CI/CD Pipeline Constraints
- No `.github/workflows`, Azure Pipelines, or CI configuration files found in repo
- No CI pipeline constraints documented
- Build verification is local: `dotnet build SmeAccounting.sln` + `dotnet test tests/SmeAccounting.ArchitectureTests/`
- Run app locally: `dotnet run --project src/SmeAccounting.Api/` — Swagger at `/swagger` in dev
- TreatWarningsAsErrors=true enforces clean build as quality gate
- Architecture tests enforce dependency direction; violations break build

## Task-Specific Research
(pending)
