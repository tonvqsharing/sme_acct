# Global Loop Memory
Shared across all loops in this project.

## Learnings

### .NET 10 SDK (Sep 2026)
- `dotnet new sln` defaults to `.slnx` format — use `-f sln` for classic `.sln`
- Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3 requires EF Core >= 10.0.4
- Directory.Build.props eliminates per-project boilerplate (TargetFramework, Nullable, etc.)
- `dotnet new webapp` = Razor Pages (not MVC); `dotnet new webapi` = Web API
- TreatWarningsAsErrors does not promote NuGet package locale warnings to errors

### Domain Layer Patterns (Sep 2026)
- Domain events must use entity ID type consistently (`long` for `BaseEntity.Id`) — avoid cross-type casting
- C# records work well for value objects but need constructor validation for invariants (AccountCode numeric check)
- `Money` arithmetic operators need currency-mismatch guards at operator level
- Domain exceptions should form hierarchy: `DomainException` base → specific exceptions — not directly inheriting `Exception`
- Private parameterless constructors on entities enable EF Core materialization without exposing invalid state
- `JournalEntry.Post()` pattern: validate balance → set state → raise event — all in one atomic method
- `Account.Deprecate()` is soft-delete only (IsActive=false) — never hard delete for audit trail
- Port interfaces in Domain layer: repositories, UoW, external providers, clock, audit, posting service — zero NuGet deps

### Vietnamese Accounting Domain (Sep 2026)
- 26 VAS standards mapped to domain modules with applicability levels
- Circular 99 Art. 28 maps to: Domain posting rules, Infrastructure audit, Application reports, extensible architecture
- E-invoice XML is legally binding (not PDF) — TVAN providers (Viettel/MISA/BKAV) as adapter implementations
- Chart of Accounts: 9 categories, 4-digit Level 1 hierarchy, 25+ key account codes
- IFRS transition via Decision 345 — `IAccountingPolicy` interface abstraction for VAS vs IFRS
- Architecture enforcement: csproj refs + NetArchTest.Rules tests
- Dependency direction: Api→Application→Domain; Infrastructure→Application+Domain; Domain has zero NuGet refs

### Cross-Project Patterns (Sep 2026)
- Solution layout: Domain (entities, value objects, events, exceptions, ports), Application (use cases, DTOs, validators), Infrastructure (EF Core, adapters), Api (controllers), ArchitectureTests (enforcement)
- ADR format: Michael Nygard (Status/Context/Decision/Consequences)
- Traceability matrices in docs link regulations → architecture components → tests
- All entities: private parameterless constructors (EF Core) + public constructors with required params

### Application Layer Patterns (Sep 2026)
- `AddValidatorsFromAssembly` requires `using FluentValidation.DependencyInjectionExtensions;` — not auto-imported
- Commands/queries as `record` types implementing `IRequest<T>` — MediatR 14.x
- `ValidationBehavior<TRequest, TResponse>` as `IPipelineBehavior` — runs all `IValidator<T>` before handler, throws `ValidationException`
- DTOs as plain records — no domain entity references, enums mapped via `.ToString()`
- `BalanceSheetDto` / `IncomeStatementDto` use `AccountGroupTotal(GroupName, Total, Currency)` for grouped totals
- `IAccountingReportService` in Application layer — report generation port (Infrastructure implements)
- `CreateJournalEntryCommand` carries `IReadOnlyList<JournalEntryLineInput>` — domain creates Money from inputs
- DI registration: `AddApplication()` extension method — MediatR assembly scan + open validation behavior + validators
