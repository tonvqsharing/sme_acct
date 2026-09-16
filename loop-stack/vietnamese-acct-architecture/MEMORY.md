# Loop Memory
Updated continuously by all agents as they discover things.

## Project Structure Decisions

### Solution Layout
- 5 projects: Domain, Application, Infrastructure, Api, ArchitectureTests
- Dependency direction: Api → Application → Domain; Infrastructure → Application + Domain
- Domain has **zero** NuGet PackageReference — port interfaces live here
- `Directory.Build.props` eliminates per-project TargetFramework/Nullable/ImplicitUsings duplication
- `dotnet new sln` defaults to `.slnx` in .NET 10 — use `-f sln` for classic `.sln`

### Api Layer
- `dotnet new webapp` creates Razor Pages (not MVC) — use `AddControllersWithViews()` + Controllers/Views folders for MVC

## Domain Modeling Decisions

### Entities & Value Objects
- `BaseEntity.Id` is `long` (not Guid) — matches PostgreSQL bigint PK convention
- `AccountCode` value object validates numeric-only, 4+ digits in constructor — throws `DomainException`
- `Money` record: static `Zero`, `operator +`/`operator -` with currency mismatch guard
- `Account.Deprecate()` = soft-delete only (`IsActive = false`) — never hard delete (audit trail)
- All entities have private parameterless constructors (EF Core) + public constructors with required params

### Domain Events
- Events use `long` for entity IDs (matching `BaseEntity.Id`) — avoids casting at raise sites
- `JournalEntry.Post()`: validate balance → set state → raise `JournalEntryPosted` — atomic method
- `FiscalPeriod.Close()` raises `PeriodClosed` — closes period permanently
- Domain exceptions form hierarchy: `DomainException` base → specific exceptions (not `System.Exception` directly)

### Port Interfaces (in Domain layer)
- `IAccountRepository`, `IJournalEntryRepository`, `IUnitOfWork`
- `IForeignExchangeRateProvider`, `IAuditLogger`, `IClock`, `IPostingService`
- Zero NuGet dependencies — pure interface definitions

## Regulatory Findings

### Vietnamese Accounting Standards (VAS)
- 26 VAS standards mapped to domain modules with applicability levels (Core/Medium/Low/N/A)
- VAS compliance documented in `docs/VAS-compliance.md`

### Circular 99 (Decree 2017)
- Art. 28 requirements mapped to architecture layers:
  - (a) Domain posting rules
  - (c) Domain immutability + Infrastructure audit
  - (d) Application report generation
  - (dd) Infrastructure port interfaces (`IEInvoiceProvider`)
  - (e) Extensible architecture
- Traceability matrices link regulations → architecture components → tests

### Chart of Accounts
- 9 categories, 4-digit Level 1 hierarchy
- 25+ key account codes documented
- Enterprises may add/modify accounts per Art. 25
- Structure documented in `docs/ChartOfAccounts-structure.md`

### E-Invoice Integration
- E-invoice XML is legally binding format (not PDF)
- TVAN providers (Viettel/MISA/BKAV) as adapter implementations via `IEInvoiceProvider` port
- Decree 123 XML format structure documented in `docs/EInvoice-integration.md`

### IFRS Transition
- Decision 345 phases documented
- `IAccountingPolicy` interface abstraction for VAS vs IFRS
- Roadmap in `docs/IFRS-transition-roadmap.md`

## Technical Discoveries

### .NET 10 / EF Core
- EF Core 10.0.0 (LTS until Nov 2028), Npgsql provider 10.0.3
- Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3 requires `Microsoft.EntityFrameworkCore >= 10.0.4` — NU1605 version downgrade error if mismatched
- `TreatWarningsAsErrors` does NOT promote NuGet package locale warnings (NETSDK1188) — build succeeds with warnings

### NuGet Packages
- MediatR 14.2.0 (latest stable, netstandard2.0 — works with net10.0)
- FluentValidation 12.1.0 supports .NET 10; deprecated AspNetCore package — use `DependencyInjectionExtensions` instead
- EFCore.NamingConventions 10.0.1 for snake_case — required dependency not in original PLAN

### Architecture Enforcement
- csproj refs + `NetArchTest.Rules` tests enforce dependency direction
- Verified: Api → Application only, Application → Domain only, Infrastructure → Application + Domain
- Domain has zero NuGet PackageReference elements (csproj purity test)
- No Microsoft.EntityFrameworkCore, Npgsql, Serilog, MediatR in Domain assembly

## Architecture Tests (G4 — Sep 2026)

### Test Project Setup
- `tests/SmeAccounting.ArchitectureTests/` — xUnit + NetArchTest.Rules 1.3.2
- 4 ProjectReferences with `GeneratePathProperty="true"` for csproj path resolution
- 22 tests total, all passing in < 6 seconds

### Test Categories (22 tests)
- **DependencyRulesTests** (7): Domain/Application/Infrastructure dependency direction enforcement
- **LayerCouplingTests** (4): Controller→Domain.Entities, Controller→Domain.Ports, Handler→Infrastructure, Infrastructure→Api
- **NamingConventionsTests** (6): Entities in correct namespace, repo interfaces start with I, commands/queries/DTOs/controllers naming
- **DomainPurityTests** (3): No NuGet packages in Domain csproj, no forbidden packages, no EF Core assembly dependency
- **PostingRuleIsolationTests** (2): IPostingService in Domain assembly, JournalEntry+Money enforceable without HTTP/DB

### Key NetArchTest Patterns
- `Types.InAssembly(typeof(Account).Assembly)` — load types from Domain assembly
- `ShouldNot().HaveDependencyOn("SmeAccounting.Application")` — namespace prefix matched
- `That().ResideInNamespace("SmeAccounting.Api.Controllers")` — namespace filter
- `Should().HaveNameEndingWith("Command")` — naming convention assertion
- `MeetCustomRule()` — for complex custom rules (not used, `HaveNameMatching` regex used instead)
- `FailingTypes` is null when test passes — always use `?.Select() ?? []` pattern
- `HaveNameContaining` does NOT exist in NetArchTest.Rules 1.3.2 — use `HaveNameMatching` with regex or namespace filtering

### Known Deviations
- `ChartOfAccountsController.cs:38` uses fully-qualified `Enum.Parse<SmeAccounting.Domain.ValueObjects.AccountType>(...)` — not caught by Entities/Ports namespace tests but would be caught by root Domain dependency test
- Api csproj references Infrastructure for DI wiring (`AddInfrastructure` in Program.cs) — composition root exception
- Commands namespace contains Result records and Input types — IRequest filter used to scope command naming tests
- `AccountGroupTotal` in DTOs namespace doesn't end with "Dto" — excluded by filtering types that already end with "Dto"

### Csproj Path Resolution
- Use `typeof(TestClass).Assembly.Location` (test assembly, always in test output dir)
- Navigate up 5 levels from `bin/Debug/net10.0/` to reach solution root
- `Path.GetFullPath(Path.Combine(dir, "..", "..", "..", "..", "..", "src", ...))`

## Application Layer Patterns (G2 — Sep 2026)

### MediatR CQRS Contracts
- Commands/queries as `record` types implementing `IRequest<T>` — MediatR 14.x
- 6 commands: CreateAccount, CreateJournalEntry, PostJournalEntry, DeprecateAccount, OpenFiscalPeriod, CloseFiscalPeriod
- 6 queries: GetAccount, GetAccountsByGroup, GetJournalEntry, GetFiscalPeriods, GetBalanceSheet, GetIncomeStatement
- `CreateJournalEntryCommand` carries `IReadOnlyList<JournalEntryLineInput>` — domain creates Money from inputs

### FluentValidation
- `AddValidatorsFromAssembly` requires `using FluentValidation.DependencyInjectionExtensions;` — not auto-imported
- `ValidationBehavior<TRequest, TResponse>` as `IPipelineBehavior` — runs all `IValidator<T>` before handler, throws `ValidationException`
- 3 validators: CreateAccountCommandValidator, CreateJournalEntryCommandValidator, PostJournalEntryCommandValidator

### DTOs
- DTOs as plain records — no domain entity references, enums mapped via `.ToString()`
- 8 DTOs: AccountDto, JournalEntryDto, JournalEntryLineDto, FiscalPeriodDto, FiscalYearDto, BalanceSheetDto, IncomeStatementDto, MoneyDto
- `BalanceSheetDto` / `IncomeStatementDto` use `AccountGroupTotal(GroupName, Total, Currency)` for grouped totals

### Service Ports
- `IAccountingReportService` in Application layer — report generation port (Infrastructure implements)

### DI Registration
- `AddApplication()` extension method — MediatR assembly scan + open validation behavior + validators

## Infrastructure Layer Patterns (G2 — Sep 2026)

### EF Core Configuration
- EFCore.NamingConventions 10.0.1 provides `UseSnakeCaseNamingConvention()` — requires Npgsql provider
- `SmeAccountingDbContext` implements `IUnitOfWork` directly — no separate class needed
- `xmin` concurrency token via `IsRowVersion()` — PostgreSQL system column for optimistic concurrency
- Domain events dispatched in `SaveChangesAsync` override — collect events before save, publish after
- Money value objects as EF Core owned types — `OwnsOne(e => e.Debit)` with separate `HasColumnName` for amount/currency
- `AccountCode` as owned type on Account — `OwnsOne(e => e.Code)` with `HasColumnName("code")`
- 7 DbSets: Accounts, AccountGroups, JournalEntries, JournalEntryLines, FiscalYears, FiscalPeriods, PostingReferences
- 7 entity configurations: Account, AccountGroup, JournalEntry, JournalEntryLine, FiscalYear, FiscalPeriod, PostingReference

### Repository Pattern
- Write repos track changes only, NO SaveChanges — UoW owns commit
- Read repos use `AsNoTracking()` for performance, write repos use tracked entries
- UoW registered as factory to same DbContext instance: `services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<SmeAccountingDbContext>())`
- 2 repositories: EfAccountRepository, EfJournalEntryRepository

### External Adapter Stubs
- `BankExchangeRateProvider` returns mock rates
- `EInvoiceProviderAdapter` / `DigitalSignatureAdapter` throw `NotImplementedException`
- Ports (`IEInvoiceProvider`, `IDigitalSignatureService`) not yet defined in Domain — stubs ready for implementation

### Services
- `SystemClock : IClock` — singleton, returns `DateTimeOffset.UtcNow`
- `AuditLogger : IAuditLogger` — append-only console log (stub for production)

### DI Registration
- `AddInfrastructure(Action<DbContextOptionsBuilder>?)` extension method — accepts optional DB configuration action
- Registers DbContext, UoW, repos, clock, audit, FX provider

## Presentation Layer Patterns (G3 — Sep 2026)

### MVC vs Razor Pages
- `dotnet new webapp` creates Razor Pages (`AddRazorPages()` + `Pages/` folder)
- MVC requires `AddControllersWithViews()` + `Controllers/` + `Views/` folders
- DELETE `Pages/` folder before creating MVC structure — Razor Pages and MVC cannot coexist
- Tag helpers: `asp-controller` + `asp-action` (MVC) vs `asp-page` (Razor Pages)

### Program.cs Configuration
- `AddControllersWithViews()` — NOT `AddRazorPages()`, NOT `AddControllers()`
- `AddApplication()` — MediatR assembly scan + FluentValidation + ValidationBehavior pipeline
- `AddInfrastructure(IConfiguration)` — DbContext + repos + adapters (reads connection string from config)
- `MapControllerRoute("default", "{controller=Home}/{action=Index}/{id?}")` — conventional routing
- Swashbuckle 10.x: `using Microsoft.OpenApi;` NOT `Microsoft.OpenApi.Models`
- `UseNpgsql()` is in Infrastructure assembly — Api should NOT reference Npgsql directly

### Controller Patterns (Thin Controllers)
- Inject `IMediator` via constructor — zero domain/infrastructure references
- `[ValidateAntiForgeryToken]` on all POST actions
- Pass `CancellationToken` through to `_mediator.Send()`
- Catch `FluentValidation.ValidationException` → map to `ModelState` errors
- Controllers reference only Application types (DTOs, commands, queries, ViewModels)
- `SmeAccounting.Domain.ValueObjects.AccountType` used via fully qualified name (no `using` statement) — avoids coupling

### Architecture Constraints Verified
- Api csproj references both Application AND Infrastructure (for DI wiring in Program.cs)
- Controllers only reference Application types — no `using SmeAccounting.Domain.Entities` in controllers
- `using SmeAccounting.Domain` constraint applies to using statements, not fully qualified names

### ViewModels
- ViewModels in `Api/ViewModels/` — reference Application DTOs and primitives only
- DataAnnotations on ViewModels for client-side validation
- ViewModels map directly to MediatR commands/queries — controller constructs command from VM

### Views
- `_ViewImports.cshtml` — `@using SmeAccounting.Application.DTOs` + tag helpers
- `_Layout.cshtml` — Bootstrap 5, Vietnamese labels, `asp-controller`/`asp-action` navigation
- Tables render empty state when no data — views work without database
- jQuery validation scripts via `_ValidationScriptsPartial`

## Patterns to Follow

1. **Atomic domain methods**: validate → mutate → raise event (e.g., `JournalEntry.Post()`)
2. **Soft-delete for audit**: `IsActive = false`, never hard delete
3. **Port interfaces in Domain**: zero framework dependencies, implement in Infrastructure
4. **Value objects with invariants**: constructor validation throws `DomainException`
5. **Domain events carry long IDs**: match `BaseEntity.Id` type — no cross-type casting
6. **Private parameterless constructors**: EF Core materialization without exposing invalid state
7. **ADR format**: Michael Nygard (Status/Context/Decision/Consequences)
8. **Traceability matrices**: regulations → architecture components → tests
9. **Thin controllers**: inject IMediator only, delegate all logic to Application layer
10. **ViewModels as boundary**: ViewModels reference DTOs/primitives only, controller maps to commands

## Pitfalls to Avoid

- Don't use `dotnet new webapp` when you need MVC — it creates Razor Pages
- Don't mix `long` and `Guid` entity IDs — causes casting at event raise sites
- Don't let Domain layer reference any NuGet packages — port interfaces only
- Don't hard-delete entities with audit requirements — use soft-delete pattern
- Don't assume `TreatWarningsAsErrors` catches all warnings — NuGet locale warnings slip through
- Don't use `AddControllers()` when you need views — use `AddControllersWithViews()`
- Don't reference Infrastructure types in controllers — only Application types
- Swashbuckle 10.x namespace changed: `Microsoft.OpenApi` not `Microsoft.OpenApi.Models`
