# Loop Memory
Updated continuously by all agents as they discover things.

---

## Entity Patterns

### Company Entity (`Domain/Entities/Company.cs`)
- Public constructor validates: `fiscalYearStartMonth` (1–12), `fiscalYearStartDay` (1–28)
- Day capped at 28 for February safety — prevents invalid dates
- TaxCode regex validation DEFERRED to FluentValidation layer (not constructor)
- `FunctionalCurrencyCode` is `string` — NOT a FK to Currency entity. Matches Money VO pattern
- Domain event: `CompanyCreated` raised in constructor

### Currency Entity (`Domain/Entities/Currency.cs`)
- Code validated as exactly 3 uppercase chars (ISO 4217)
- Properties: `Symbol`, `DecimalPlaces`, `IsDefault`, `IsActive`
- Domain event: `CurrencyCreated` raised in constructor
- Namespace: `SmeAccounting.Domain.Entities.Currency` (separate from `SmeAccounting.Domain.ValueObjects.Currency`)

### Value Objects
- Currency VO record in `ValueObjects/Currency.cs` is NOT referenced anywhere — Money uses `string Currency` not the VO
- Safe to have both VO record and entity with different namespaces

---

## Configuration Patterns

### EF Core Configurations
- Both `CompanyConfiguration` and `CurrencyConfiguration` use unique indexes:
  - `companies.tax_code` (unique)
  - `currencies.code` (unique)
- Snake-case table/column naming via `EFCore.NamingConventions`
- `xmin` concurrency tokens on all entities

### Project Structure
- `Directory.Build.props` eliminates per-project boilerplate (TargetFramework, Nullable, etc.)
- TreatWarningsAsErrors enabled — NuGet warnings NOT promoted to errors

---

## Repository Patterns

### Port Interfaces
- `ICompanyRepository` adds `GetByTaxCodeAsync` — unique constraint in DB
- `ICurrencyRepository` adds `GetByCodeAsync` — unique constraint in DB
- Port interfaces live in `Domain/Ports/` — zero NuGet dependencies

### FK Relationships (Deferred)
- `CompanyId` FK needed on: `FiscalYear`, `FiscalPeriod`, `Account`, `AccountGroup`, `JournalEntry`
- Implementation deferred to T2/T4/T5

---

## Port Interface Patterns
- Port interfaces in `Domain/Ports/` include: repositories, UoW, external providers, clock, audit, posting service
- Zero NuGet deps in Domain layer
- Domain exceptions hierarchy: `DomainException` base → specific exceptions (not directly inheriting `Exception`)

---

## Technical Discoveries

### .NET 10 SDK
- `dotnet new sln` defaults to `.slnx` format — use `-f sln` for classic `.sln`
- Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3 requires EF Core >= 10.0.4
- `dotnet new webapp` = Razor Pages (not MVC); `dotnet new webapi` = Web API

### Entity Patterns
- Private parameterless constructors on entities enable EF Core materialization without exposing invalid state
- All entities: private parameterless constructors + public constructors with required params
- Domain events raised in constructors (CompanyCreated, CurrencyCreated, AccountCreated)

### Vietnamese Accounting Domain
- 26 VAS standards mapped to domain modules with applicability levels
- Circular 99 Art. 28 maps to: Domain posting rules, Infrastructure audit, Application reports
- E-invoice XML is legally binding (not PDF) — TVAN providers as adapter implementations
- Chart of Accounts: 9 categories, 4-digit Level 1 hierarchy, 25+ key account codes
- IFRS transition via Decision 345 — `IAccountingPolicy` interface abstraction

---

## Patterns to Follow

1. **Constructor validation** — validate invariants in entity constructors (fiscal year month/day, currency code format)
2. **Domain events** — raise in constructors (e.g., `CompanyCreated`, `CurrencyCreated`, `AccountCreated`)
3. **Unique constraints** — port interface methods map to DB unique indexes (e.g., `GetByTaxCodeAsync` → `tax_code` unique)
4. **String for currency** — use `string` for currency codes, not FK to entity. Matches Money VO pattern
5. **Deferred FK** — defer CompanyId FKs on related entities to later tasks (T2/T4/T5)
6. **FluentValidation** — regex validation deferred to validators, not constructors
7. **Port interfaces** — repositories in Domain/Ports/, zero NuGet deps
8. **EF Core materialization** — private parameterless constructors + public constructors with required params

---

## T2 Discoveries (Sep 2026)

- `PeriodType` enum in `ValueObjects/` follows same pattern as existing enums (FiscalYearStatus, PeriodStatus) — all in ValueObjects namespace, not a separate Enums/ directory
- FiscalYearCreated domain event does NOT duplicate `OccurredOn` — inherited from `DomainEvent` base. CS0108 if re-declared
- `FiscalYear.AddPeriod(int month)` signature changed to `AddPeriod(int month, DateOnly startDate, DateOnly endDate, PeriodType periodType)` — FiscalPeriod constructor now requires these params
- FiscalYear entity raises `FiscalYearCreated` in constructor (same pattern as CompanyCreated, CurrencyCreated)
- FiscalYear config adds `HasOne<Company>().WithMany().HasForeignKey("CompanyId").OnDelete(DeleteBehavior.Restrict)` — prevents cascade delete
- FiscalPeriod `PeriodType` stored as string via `HasConversion<string>()` — same pattern as Status enums
- DTOs updated with new fields — FiscalYearDto adds CompanyId, StartDate, EndDate, Description; FiscalPeriodDto adds StartDate, EndDate, PeriodType

---

## T3 Discoveries (Sep 2026)

- ExchangeRateType enum goes in ValueObjects/ (not Enums/) — consistent with PeriodType, PeriodStatus, FiscalYearStatus pattern
- ExchangeRate entity stores FromCurrencyCode/ToCurrencyCode as string (not FK) — matches Money VO string Currency pattern
- DomainException thrown directly for invariants (From!=To, Rate>0) — no custom subclass needed
- ExchangeRateRecorded event is simpler than FiscalYearCreated — only ExchangeRateId + CompanyId (no currency pair/rate fields, just ID reference)
- Composite unique index: (CompanyId, FromCurrencyCode, ToCurrencyCode, RateType, EffectiveDate) — DB-level enforcement
- FK to Company with Restrict delete — same pattern as FiscalYear
- GetByCurrencyPairAsync normalizes to uppercase via ToUpperInvariant() — entity constructor already does this but explicit in repo
- No Rate property on event — avoids storing rate value twice (entity has it). Event is for notification, not data transfer

---

## Pitfalls to Avoid

1. **Namespace collision** — `SmeAccounting.Domain.Entities.Currency` vs `SmeAccounting.Domain.ValueObjects.Currency` — different namespaces, safe to coexist
2. **Currency as FK** — Don't use FK to Currency entity for money fields — use `string` to match Money VO pattern
3. **Day validation** — Don't allow day > 28 — February safety. Cap at 28
4. **Constructor regex** — Don't put regex validation in constructors — defer to FluentValidation layer
5. **Warnings-as-errors** — TreatWarningsAsErrors does NOT promote NuGet package locale warnings to errors
6. **Solution format** — `dotnet new sln` defaults to `.slnx` — use `-f sln` for classic `.sln`

---

## T4 Discoveries (Sep 2026)

- NormalBalance enum goes in ValueObjects/ (not Enums/) — consistent with all other enums (AccountType, PeriodStatus, FiscalYearStatus, PeriodType, ExchangeRateType)
- Account constructor now requires CompanyId (long) and NormalBalance (enum) as required params —CompanyId > 0 validated
- AccountGroup constructor now requires CompanyId (long) as required param —CompanyId > 0 validated, DisplayOrder defaults to 0
- FK to Company pattern identical across FiscalYear, ExchangeRate, Account, AccountGroup — `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
- NormalBalance stored as string via `HasConversion<string>()` in DB — same pattern as AccountType, PeriodStatus, etc.
- Controller (ChartOfAccountsController) needed updating since it calls CreateAccountCommand directly — ViewModel also needed new fields (CompanyId, NormalBalance, Description)
- No new DbSets, no new events, no DbContext changes, no DI changes, no port interface changes — Account/AccountGroup already existed
- No breaking changes to existing entity methods (Deprecate stays same) — only constructors changed which have no callers yet

---

## G2 Batch Consolidated Learnings (Sep 2026)

### FiscalYear/FiscalPeriod Extensions (T2)
- `CompanyId` FK added to FiscalYear — required, Restrict delete, same pattern as other entities
- FiscalYear: `StartDate`, `EndDate`, `Description` properties added
- FiscalPeriod: `StartDate`, `EndDate`, `PeriodType` added — PeriodType stored as string via `HasConversion<string>()`
- `FiscalYear.AddPeriod` signature expanded: `(int month, DateOnly startDate, DateOnly endDate, PeriodType periodType)` — backwards compatible if no callers exist yet
- Domain event: `FiscalYearCreated` — no `OccurredOn` redeclaration (inherited from `DomainEvent` base, CS0108 trap)

### ExchangeRate Entity (T3)
- `FromCurrencyCode` / `ToCurrencyCode` stored as string (not FK) — matches Money VO `string Currency` pattern
- Invariants: `From != To`, `Rate > 0` — enforced in constructor via `DomainException`
- Domain event: `ExchangeRateRecorded` — carries `ExchangeRateId` + `CompanyId` only (no rate value, avoids duplication)
- Composite unique index: `(CompanyId, FromCurrencyCode, ToCurrencyCode, RateType, EffectiveDate)` — DB-level enforcement
- `ExchangeRateType` enum in ValueObjects/ — consistent with PeriodType, PeriodStatus, FiscalYearStatus
- Repo method: `GetByCurrencyPairAsync` normalizes to uppercase via `ToUpperInvariant()`

### COA Extensions (T4)
- `NormalBalance` enum added to `ValueObjects/` — Debit/Credit
- Account constructor expanded: now requires `CompanyId` (long) and `NormalBalance` (enum) —CompanyId > 0 validated
- AccountGroup constructor expanded: now requires `CompanyId` (long) —CompanyId > 0 validated, DisplayOrder defaults to 0
- NormalBalance stored as string via `HasConversion<string>()` in DB — same pattern as AccountType, PeriodStatus
- FK to Company: identical config across FiscalYear, ExchangeRate, Account, AccountGroup — `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)`
- Controller (ChartOfAccountsController) updated — ViewModel needed new fields (CompanyId, NormalBalance, Description)
- No new DbSets, events, DbContext changes, DI changes, or port interface changes — only constructors changed

### Dimensions (T5)
- Department, CostCenter, Project — all follow same pattern as ExchangeRate: CompanyId FK (required, Restrict), Code unique per company (composite index), IsActive soft-delete
- Domain events: `DepartmentCreated`, `CostCenterCreated`, `ProjectCreated` — entity ID + CompanyId + occurredOn (same shape as `ExchangeRateRecorded`)
- JournalEntryLine gets 3 optional nullable FKs: `DepartmentId`, `CostCenterId`, `ProjectId` — SetNull delete behavior (line keeps data, loses reference if dimension deleted)
- `JournalEntry.AddLine` updated with passthrough optional params — backwards compatible with existing callers
- Configurations: composite unique index on `(CompanyId, Code)` per dimension type — prevents duplicate codes per company at DB level
- All 3 dimension port interfaces include `GetByCodeAsync(code, companyId)` for application-level duplicate check
- No breaking changes — all new params backwards compatible

### Cross-Cutting G2 Patterns
- **FK to Company pattern**: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — universal across all entities that need company scoping
- **Composite unique indexes**: Used for per-company uniqueness (dimensions, exchange rates) — DB-level enforcement
- **Enum storage**: All enums stored as string via `HasConversion<string>()` — PeriodType, NormalBalance, ExchangeRateType, AccountType, PeriodStatus
- **String over FK for currency codes**: Money VO uses `string Currency` — entity stores FromCurrencyCode/ToCurrencyCode as string, not FK to Currency entity
- **Backwards-compatible method expansion**: When expanding constructors/methods, keep existing params in same order, add new params at end with defaults — no callers broken
- **Event minimalism**: Domain events carry entity ID + company ID only — avoid duplicating entity data in events
