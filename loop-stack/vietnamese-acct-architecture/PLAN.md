# Loop Plan
## Mode
build
## Goal
Design the initial project architecture for a Vietnamese enterprise accounting web application using ASP.NET MVC and C#. Architecture only — no business module implementation. Covers domain boundaries, application boundaries, infrastructure boundaries, presentation boundary, accounting core boundary, future module boundaries, testing structure, regulatory documentation, and traceability. Must comply with VAS and Circular 99/2025/TT-BTC.
## Stop Condition
all tasks in loop-stack/vietnamese-acct-architecture/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks

- [x] ### [G1] Solution Structure and Shared Kernel
Create the .NET solution, all class library and web projects, and directory layout enforcing Clean Architecture dependency direction.

**Deliverables:**
- `SmeAccounting.sln` at project root
- `src/SmeAccounting.Domain/` — classlib, no NuGet refs beyond `net10.0`
- `src/SmeAccounting.Application/` — classlib, refs Domain only
- `src/SmeAccounting.Infrastructure/` — classlib, refs Application + Domain
- `src/SmeAccounting.Api/` — webapp (ASP.NET MVC), refs Application only
- `Directory.Build.props` — common properties (TargetFramework, Nullable, ImplicitUsings, LangVersion=13)
- `Directory.Build.targets` — shared targets if needed
- `.editorconfig` — C# style rules
- `.gitignore` — .NET standard ignores

**Acceptance Criteria:**
- `dotnet build` succeeds with zero errors
- Solution contains 5 projects (Domain, Application, Infrastructure, Api + 1 test project placeholder)
- Domain project has zero NuGet PackageReference elements
- Api project does NOT reference Infrastructure or Domain directly

**Verification:**
- `dotnet build SmeAccounting.sln` exits 0
- `dotnet list src/SmeAccounting.Domain/SmeAccounting.Domain.csproj package` shows no packages
- `dotnet list src/SmeAccounting.Api/SmeAccounting.Api.csproj reference` shows only Application

---

- [x] ### [G1] Domain Layer — Core Entities, Value Objects, and Port Interfaces
Create the pure domain layer with all Accounting Core entities, value objects, domain events, domain exceptions, and port interfaces. Zero infrastructure dependencies.

**Deliverables:**
- **Entities:**
  - `Account` (id, code, name, level, parent_id, account_type, is_active) — aggregate root
  - `AccountGroup` (id, code, name, account_type) — COA grouping
  - `JournalEntry` (id, entry_number, date, period_id, description, source_type, source_id, posted_by, posted_at) — aggregate root
  - `JournalEntryLine` (id, entry_id, account_id, debit, credit, currency, exchange_rate, description)
  - `FiscalYear` (id, year, status)
  - `FiscalPeriod` (id, year_id, month, status, opened_at, closed_at)
  - `PostingReference` (id, journal_entry_id, source_type, source_id)
- **Value Objects:**
  - `Money` (amount, currency) — equality by value
  - `AccountCode` (value) — 4-digit Level 1, extensible
  - `Currency` (code, name, is_default)
  - `PeriodStatus` (enum: Open, Closing, Closed)
  - `AccountType` (enum: Asset, Liability, Equity, Revenue, Expense)
- **Domain Events:**
  - `JournalEntryPosted` (entry_id, posted_at)
  - `PeriodClosed` (period_id, closed_at)
  - `AccountCreated`, `AccountDeprecated`
- **Domain Exceptions:**
  - `InvalidPostingRule` (debit != credit)
  - `PeriodClosedException`
  - `AccountNotLeafException`
- **Port Interfaces:**
  - `IAccountRepository` — CRUD for Account
  - `IJournalEntryRepository` — persistence for JournalEntry
  - `IUnitOfWork` — transaction boundary
  - `IForeignExchangeRateProvider` — bank rates
  - `IAuditLogger` — immutable audit trail
  - `IClock` — deterministic time for tests
  - `IPostingService` — accounting posting orchestration (domain service interface)

**Acceptance Criteria:**
- All entities inherit from `BaseEntity` (shared kernel) or are standalone
- Value objects implement `Equals`, `GetHashCode`, `operator ==`
- Port interfaces have no infrastructure NuGet references
- `IPostingService` defines `Post(JournalEntry entry)` method
- Domain events are plain records (no MediatR dependency)

**Verification:**
- `dotnet build src/SmeAccounting.Domain/SmeAccounting.Domain.csproj` exits 0
- No `Microsoft.*`, `Npgsql.*`, `Serilog.*` references in csproj
- All value object equality tests would pass (manual inspection)

---

- [x] ### [G1] Regulatory Documentation Structure
Create the documentation skeleton for VAS compliance, Circular 99 mapping, and regulatory traceability. This is architecture documentation — not business logic implementation.

**Deliverables:**
- `docs/regulatory/` directory
- `docs/regulatory/VAS-compliance.md` — map of 26 VAS standards to domain modules
- `docs/regulatory/Circular99-mapping.md` — Circular 99 articles to architecture enforcement points
- `docs/regulatory/ChartOfAccounts-structure.md` — account code hierarchy (Level 1-3), groups, Circular 99 revisions
- `docs/regulatory/EInvoice-integration.md` — Decree 123/2020 requirements, port interfaces, TVAN provider adapters
- `docs/regulatory/IFRS-transition-roadmap.md` — Decision 345/QĐ-BTC phases, abstraction layer design
- `docs/architecture/ADR-001-clean-architecture.md` — why Clean Architecture, dependency rules
- `docs/architecture/ADR-002-cqrs-mediatr.md` — CQRS pattern choice
- `docs/architecture/ADR-003-posting-seam.md` — where accounting posting happens (domain service)

**Acceptance Criteria:**
- Each VAS standard maps to at least one domain module or notes "not applicable"
- Circular 99 Art. 28 software requirements map to specific architecture layers
- ADRs follow standard format (Status, Context, Decision, Consequences)
- E-Invoice document defines the `IEInvoiceProvider` port interface contract

**Verification:**
- All markdown files exist and are non-empty
- VAS-compliance.md lists all 26 standards
- Circular99-mapping.md references Art. 28(a), (c), (d), (dd), (e)

---

- [x] - [x] ### [G2] Application Layer — CQRS Contracts, DTOs, and Validators
Create the application layer with MediatR command/query contracts, DTOs, validators, and the application-level posting service interface. Depends only on Domain.

**Deliverables:**
- **NuGet refs:** MediatR, FluentValidation, FluentValidation.DependencyInjectionExtensions
- **Command Contracts:**
  - `CreateAccountCommand` / `CreateAccountResult`
  - `CreateJournalEntryCommand` / `CreateJournalEntryResult`
  - `PostJournalEntryCommand` / `PostJournalEntryResult`
  - `OpenFiscalPeriodCommand`, `CloseFiscalPeriodCommand`
  - `DeprecateAccountCommand`
- **Query Contracts:**
  - `GetAccountQuery` / `AccountDto`
  - `GetAccountsByGroupQuery` / `List<AccountDto>`
  - `GetJournalEntryQuery` / `JournalEntryDto`
  - `GetFiscalPeriodsQuery` / `List<FiscalPeriodDto>`
  - `GetBalanceSheetQuery` / `BalanceSheetDto`
  - `GetIncomeStatementQuery` / `IncomeStatementDto`
- **DTOs:**
  - `AccountDto`, `JournalEntryDto`, `JournalEntryLineDto`
  - `FiscalPeriodDto`, `FiscalYearDto`
  - `BalanceSheetDto`, `IncomeStatementDto`
  - `MoneyDto` (amount, currency)
- **Validators (FluentValidation):**
  - `CreateAccountCommandValidator` — code format, required fields
  - `CreateJournalEntryCommandValidator` — period open, lines exist
  - `PostJournalEntryCommandValidator` — balance check
- **Application Service Interfaces:**
  - `IPostingService` (already in Domain) — handler will implement orchestration
  - `IAccountingReportService` — report generation port

**Acceptance Criteria:**
- All command/query records implement `IRequest<T>` from MediatR
- All validators inherit from `AbstractValidator<T>`
- DTOs are plain records with no domain entity references
- No `Infrastructure` or `Api` references in csproj

**Verification:**
- `dotnet build src/SmeAccounting.Application/SmeAccounting.Application.csproj` exits 0
- `dotnet list src/SmeAccounting.Application/SmeAccounting.Application.csproj package` shows MediatR, FluentValidation only
- No `Microsoft.EntityFrameworkCore` in package list

---

- [x] ### [G2] Infrastructure Layer — Persistence, EF Core, and External Adapters
Create the infrastructure layer implementing all port interfaces from Domain/Application. EF Core for persistence, external service adapters as stubs.

**Deliverables:**
- **NuGet refs:** Microsoft.EntityFrameworkCore, Npgsql.EntityFrameworkCore.PostgreSQL, Microsoft.Extensions.DependencyInjection
- **EF Core Setup:**
  - `SmeAccountingDbContext` — inherits `DbContext`
  - Entity configurations: `AccountConfiguration`, `JournalEntryConfiguration`, `JournalEntryLineConfiguration`, `FiscalYearConfiguration`, `FiscalPeriodConfiguration`
  - Snake-case naming convention (PostgreSQL)
  - bigint PKs, xmin concurrency tokens
- **Repository Implementations:**
  - `EfAccountRepository : IAccountRepository`
  - `EfJournalEntryRepository : IJournalEntryRepository`
  - `EfUnitOfWork : IUnitOfWork`
- **External Adapters (stubs):**
  - `BankExchangeRateProvider : IForeignExchangeRateProvider` — returns mock rates
  - `EInvoiceProviderAdapter : IEInvoiceProvider` — throws `NotImplementedException` (stub)
  - `DigitalSignatureAdapter : IDigitalSignatureService` — throws `NotImplementedException` (stub)
- **Audit Trail:**
  - `AuditLogger : IAuditLogger` — append-only log implementation
- **Time Provider:**
  - `SystemClock : IClock` — returns `DateTimeOffset.UtcNow`
- **Dependency Injection:**
  - `InfrastructureServiceCollectionExtensions.AddInfrastructure(...)` — registers all implementations

**Acceptance Criteria:**
- `SmeAccountingDbContext` has `DbSet<Account>`, `DbSet<JournalEntry>`, `DbSet<JournalEntryLine>`, `DbSet<FiscalYear>`, `DbSet<FiscalPeriod>`
- All repositories implement their Domain interfaces
- External adapters throw `NotImplementedException` (architecture placeholder)
- `AddInfrastructure` extension method compiles and registers all ports

**Verification:**
- `dotnet build src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj` exits 0
- `dotnet list src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj package` shows EF Core + Npgsql
- Repository classes implement correct interfaces (manual inspection)

---

- [x] ### [G3] Presentation Layer — ASP.NET MVC Controllers, Views, and MediatR Wiring
Create the ASP.NET MVC presentation layer with thin controllers that dispatch to MediatR, views for key pages, and application startup configuration.

**Deliverables:**
- **NuGet refs:** MediatR (for `AddMediatR`), Swashbuckle.AspNetCore (Swagger)
- **Startup/Program.cs:**
  - `builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(...))`
  - `builder.Services.AddInfrastructure(...)` (from Infrastructure extension)
  - `builder.Services.AddControllersWithViews()`
  - Swagger configured at `/swagger`
- **Controllers (thin — HTTP mapping only):**
  - `HomeController` — index, about pages
  - `ChartOfAccountsController` — list, create, edit, deprecate accounts
  - `JournalEntryController` — list, create, post entries
  - `FiscalPeriodController` — list, open, close periods
  - `ReportingController` — balance sheet, income statement views
  - `SettingsController` — accounting policy settings (placeholder)
- **Views (Razor):**
  - `Views/Shared/_Layout.cshtml` — navigation, Bootstrap
  - `Views/Home/Index.cshtml` — dashboard placeholder
  - `Views/ChartOfAccounts/Index.cshtml` — account list table
  - `Views/ChartOfAccounts/Create.cshtml` — account creation form
  - `Views/JournalEntry/Index.cshtml` — journal entry list
  - `Views/JournalEntry/Create.cshtml` — entry creation form
  - `Views/FiscalPeriod/Index.cshtml` — period list with open/close
  - `Views/Reporting/BalanceSheet.cshtml` — B01-DN placeholder
  - `Views/Reporting/IncomeStatement.cshtml` — B02-DN placeholder
- **ViewModels:**
  - `ChartOfAccountsViewModel`, `JournalEntryViewModel`, `FiscalPeriodViewModel`
  - `CreateAccountViewModel`, `CreateJournalEntryViewModel`

**Acceptance Criteria:**
- Controllers have zero `Domain.Entities` or `Domain.Repositories` using statements
- Controllers only: validate model state → create command/query → send via MediatR → map result to view/ViewBag
- `dotnet run` starts the app, Swagger accessible at `/swagger`
- All views render without errors (even with empty data)

**Verification:**
- `dotnet build src/SmeAccounting.Api/SmeAccounting.Api.csproj` exits 0
- No `using SmeAccounting.Domain.Entities` in any controller file
- `dotnet run --project src/SmeAccounting.Api/` starts without exception (manual)

---

### [G4] Architecture Tests and Verification
Create the architecture test project enforcing Clean Architecture constraints, layer coupling rules, and naming conventions using NetArchTest.

**Deliverables:**
- **Test project:** `tests/SmeAccounting.ArchitectureTests/` (xUnit + NetArchTest.Rules)
- **Dependency Rules Tests:**
  - Domain has no reference to Application, Infrastructure, or Api assemblies
  - Application has no reference to Infrastructure or Api assemblies
  - Infrastructure has no reference to Api assembly
  - Api has no reference to Infrastructure assembly (only Application)
- **Layer Coupling Tests:**
  - Controllers do not reference `SmeAccounting.Domain.Entities` namespace
  - Controllers do not reference `SmeAccounting.Domain.Repositories` namespace
  - Handlers (Application) do not reference `SmeAccounting.Infrastructure` namespace
- **Naming Convention Tests:**
  - Entities in Domain end with correct suffixes
  - Repository interfaces start with `I`
  - Commands/Queries follow naming pattern
- **Domain Purity Tests:**
  - Domain project has no NuGet PackageReference (only FrameworkReference)
  - No `Microsoft.*`, `Npgsql.*`, `Serilog.*` in Domain csproj
- **Posting Rule Isolation Tests:**
  - `IPostingService` interface is in Domain assembly (not Application)
  - Journal entry balance rule is enforceable without HTTP/DB

**Acceptance Criteria:**
- All architecture tests pass: `dotnet test tests/SmeAccounting.ArchitectureTests/`
- Zero architectural violations detected
- Tests are descriptive (test names explain what they enforce)
- NetArchTest.Rules NuGet package referenced

**Verification:**
- `dotnet test tests/SmeAccounting.ArchitectureTests/ --verbosity normal` exits 0
- All tests show "Passed" status
- No skipped or failed tests
