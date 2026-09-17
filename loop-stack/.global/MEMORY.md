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
- NormalBalance enum in ValueObjects/ (Debit, Credit) — same location as all other enums (AccountType, PeriodStatus, etc.)
- FK to Company pattern: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — consistent across FiscalYear, ExchangeRate, Account, AccountGroup

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

### T5 Dimensions Discoveries (Sep 2026)
- Department, CostCenter, Project follow same pattern as ExchangeRate: CompanyId FK (required, Restrict), Code unique per company (composite index), IsActive soft-delete
- Domain events: DepartmentCreated, CostCenterCreated, ProjectCreated — entity ID + CompanyId + occurredOn (same as ExchangeRateRecorded)
- JournalEntryLine gets 3 optional nullable FKs (DepartmentId, CostCenterId, ProjectId) with SetNull delete behavior — if dimension deleted, line keeps data but loses reference
- JournalEntry.AddLine updated with passthrough optional params — backwards compatible with existing callers
- Configurations: composite unique index on (CompanyId, Code) for all 3 dimensions — prevents duplicate codes per company per dimension type at DB level
- All 3 dimension port interfaces include GetByCodeAsync(code, companyId) for application-level duplicate check
- All new params backwards compatible — no breaking changes to existing method signatures

### T1 Discoveries (Sep 2026)
- Currency VO record in ValueObjects/ is NOT referenced anywhere as a type — Money uses `string Currency` not the VO record. Safe to add entity alongside it without namespace conflicts
- Company constructor validates fiscal year start month (1–12) and day (1–28). Day capped at 28 for February safety. TaxCode regex validation deferred to FluentValidation
- CompanyCreated/CurrencyCreated events raised in constructors (same pattern as AccountCreated)
- Currency entity: Code validated as 3 uppercase chars (ISO 4217). Entity has IsDefault, IsActive, Symbol, DecimalPlaces
- Port interfaces: ICompanyRepository adds GetByTaxCodeAsync (unique constraint); ICurrencyRepository adds GetByCodeAsync (unique constraint)
- Both configurations: unique indexes on TaxCode (companies) and Code (currencies)
- FK note: CompanyId FK needed on FiscalYear, FiscalPeriod, Account, AccountGroup, JournalEntry — deferred to T2/T4/T5
- Company FunctionalCurrencyCode is a `string` (not FK to Currency entity) — matches Money VO pattern

### G2 Cross-Cutting Patterns (Sep 2026)
- **FK to Company pattern**: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — universal across all company-scoped entities
- **Composite unique indexes**: Used for per-company uniqueness (dimensions, exchange rates) — DB-level enforcement beyond application validation
- **Enum storage**: All enums stored as string via `HasConversion<string>()` — PeriodType, NormalBalance, ExchangeRateType, AccountType, PeriodStatus
- **String over FK for currency codes**: Money VO uses `string Currency` — entities store currency codes as string, not FK to Currency entity
- **Backwards-compatible method expansion**: Expand constructors/methods by adding new params at end with defaults — no existing callers broken
- **Event minimalism**: Domain events carry entity ID + company ID only — avoid duplicating entity data in events

### G3 Batch Learnings (Sep 2026)
- **Single migration for cohesive feature**: `AccountingFoundation` migration covers all G1/G2 work — 6 new tables, 5 altered tables
- **Migration naming**: Use descriptive feature name, not per-task numbering
- **Pre-requisite**: Build must succeed before EF Core migration generation (EF Core reads compiled assemblies)
- **Memory-constrained environments**: Zombie MSBuild processes cause OOM — `pkill MSBuild` frees memory
- **Migration SQL correctness**: Verify PKs, indexes, FK relationships, down migration reversal
- **Backfill note**: `defaultValue: 0L` on non-nullable company_id columns — existing rows get 0, must be backfilled in production
- **Final schema**: 13 tables total (7 original + 6 new), 14 entities (7 original + 6 new + BaseEntity)
- **Architecture tests**: 22/22 pass post-migration — no test changes needed for new entities following established patterns

### T1 VoucherType — Cross-Loop Reference (Sep 2026)
- **New entity file checklist:** Entity(`Domain/Entities/`), Enum(`Domain/ValueObjects/`), Event(`Domain/Events/`), Port(`Domain/Ports/`), EF Config(`Infrastructure/Persistence/Configurations/`), Repository(`Infrastructure/Repositories/`)
- **DbContext edits:** `DbSet<T>` property + `modelBuilder.Ignore<Event>()` — always both
- **DI edit:** `AddScoped<IXxx, EfXxx>()` — one line in DependencyInjection.cs
- **Enum location:** `Domain/ValueObjects/` — NOT `Domain/Enums/` (no such directory; all 7 enums live in ValueObjects/)
- **Invariant pattern:** `DomainException` for all new entities (replaces legacy `ArgumentNullException`/`ArgumentOutOfRangeException`)
- **Entity pattern:** CompanyId + Code + Name + IsActive + optional Description — copy from Department/CostCenter/Project
- **EF config pattern:** `internal sealed class XxxConfiguration : IEntityTypeConfiguration<T>` — `ToTable(snake_plural)`, `HasKey`, `HasColumnName` per property, `HasConversion<string>()` for enums, `HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict)`, composite unique index on `(CompanyId, Code)`, xmin row version last
- **Repository pattern:** tracked for GetById/GetByCode, `AsNoTracking()` for GetAll, `AddAsync` delegates to DbSet — no `UpdateAsync` (change tracking handles it)
- **Event pattern:** `{Entity}Created(EntityId, CompanyId, occurredOn)` — matches Department/CostCenter/Project events exactly
- **FK nav-free:** No `Company` navigation property on entity — `HasOne<Company>().WithMany()` in EF config only
- **Id=0 in constructor:** Known — real ID assigned by EF Core after SaveChanges; events carry provisional 0
- **Deactivate() no event:** Matches plan; can add `XxxDeactivated` event later if needed
- **Max lengths:** Code=20, Name=200, Description=500 — enforced in EF config, not domain
- **Architecture tests:** 22/22 pass — entity in `Domain.Entities`, port starts with `I`, zero new NuGet refs

### T3 TransactionReason — Cross-Loop Reference (Sep 2026)
- **5 new files, 2 modified files:** Domain: entity, event, port; Infrastructure: EF config, repository; DbContext + DI edits
- **Entity pattern:** VoucherType with added VoucherTypeId FK — CompanyId + VoucherTypeId + Code + Name + IsActive + Description
- **Domain event:** TransactionReasonCreated(TransactionReasonId, CompanyId, occurredOn) — event minimalism (no VoucherTypeId)
- **Port:** GetByCodeAsync(code, companyId) + GetAllByVoucherTypeAsync(voucherTypeId) — not GetAllAsync
- **EF config:** Unique index on (CompanyId, Code) — NOT composite with VoucherTypeId. Same scope as VoucherType/Department
- **EF config:** Two FKs both Restrict: Company + VoucherType
- **DbContext:** 16 DbSets, 14 ignored events after T3
- **Deactivate() no event:** Matches VoucherType pattern
