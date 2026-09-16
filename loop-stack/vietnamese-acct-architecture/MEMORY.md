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

### Architecture Enforcement
- csproj refs + `NetArchTest.Rules` tests enforce dependency direction
- Verified: Api → Application only, Application → Domain only, Infrastructure → Application + Domain

## Patterns to Follow

1. **Atomic domain methods**: validate → mutate → raise event (e.g., `JournalEntry.Post()`)
2. **Soft-delete for audit**: `IsActive = false`, never hard delete
3. **Port interfaces in Domain**: zero framework dependencies, implement in Infrastructure
4. **Value objects with invariants**: constructor validation throws `DomainException`
5. **Domain events carry long IDs**: match `BaseEntity.Id` type — no cross-type casting
6. **Private parameterless constructors**: EF Core materialization without exposing invalid state
7. **ADR format**: Michael Nygard (Status/Context/Decision/Consequences)
8. **Traceability matrices**: regulations → architecture components → tests

## Pitfalls to Avoid

- Don't use `dotnet new webapp` when you need MVC — it creates Razor Pages
- Don't mix `long` and `Guid` entity IDs — causes casting at event raise sites
- Don't let Domain layer reference any NuGet packages — port interfaces only
- Don't hard-delete entities with audit requirements — use soft-delete pattern
- Don't assume `TreatWarningsAsErrors` catches all warnings — NuGet locale warnings slip through
