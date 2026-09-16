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

---

## T6 Discoveries (Sep 2026)

### EF Core Migration
- Single migration `AccountingFoundation` covers all T1-T5 changes (6 new tables, 5 altered tables)
- Migration naming: `AccountingFoundation` (not per-task) — appropriate since all G1/G2 work is one cohesive feature
- Snake_case naming applied correctly via `EFCore.NamingConventions` — all tables/columns lowercase with underscores
- `xmin` concurrency tokens on new tables (companies, currencies, exchange_rates, departments, cost_centers, projects) — row versioning
- FK delete behavior: `Restrict` for company-scoped entities, `SetNull` for optional dimension FKs on journal_entry_lines
- Down migration correctly reverses all changes (drops FKs, drops tables, drops columns, drops indexes)
- `defaultValue: 0L` for non-nullable `company_id` columns on altered tables (existing rows get 0 — must be backfilled in production)

### Build Environment
- Memory-constrained environment (3.8GB) — zombie MSBuild processes from prior runs cause OOM
- `pkill MSBuild` frees memory when build hangs
- `--maxcpucount:1` helps but not sufficient alone — must kill zombies first
- Build time: ~90s with clean memory, >10min with zombie processes

### Migration SQL Correctness
- All new table PKs use `NpgsqlValueGenerationStrategy.IdentityByDefaultColumn` (PostgreSQL SERIAL)
- `rate` column: `numeric(10,6)` — matches ExchangeRate configuration
- Unique indexes: composite for per-company uniqueness, single-column for companies.tax_code and currencies.code
- JournalEntryLine dimension FKs: nullable long, SetNull delete — line data preserved if dimension deleted

---

## G3 Batch Consolidated Learnings (Sep 2026)

### Migration Generation Process
- **Command**: `dotnet ef migrations add AccountingFoundation --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- **Single migration** for entire G1/G2 scope — 6 new tables, 5 altered tables, all in one cohesive file
- **Migration file**: `src/SmeAccounting.Infrastructure/Migrations/20260916083803_AccountingFoundation.cs` (499 lines)
- **Pre-requisite**: Build must succeed before migration generation (EF Core reads compiled assemblies)
- **Naming**: Descriptive feature name (`AccountingFoundation`), not per-task numbering

### Final Project Summary — All Entities

#### New Entities (6)
| Entity | Table | Key Fields | Domain Event |
|--------|-------|------------|--------------|
| **Company** | `companies` | Name, TaxCode (unique), Address, FiscalYearStartMonth/Day, FunctionalCurrencyCode | CompanyCreated |
| **Currency** | `currencies` | Code (unique, 3-char ISO 4217), Name, Symbol, DecimalPlaces, IsDefault, IsActive | CurrencyCreated |
| **ExchangeRate** | `exchange_rates` | CompanyId FK, FromCurrencyCode, ToCurrencyCode, Rate (10,6), RateType, EffectiveDate, Source | ExchangeRateRecorded |
| **Department** | `departments` | CompanyId FK, Code (unique per company), Name, IsActive | DepartmentCreated |
| **CostCenter** | `cost_centers` | CompanyId FK, Code (unique per company), Name, IsActive | CostCenterCreated |
| **Project** | `projects` | CompanyId FK, Code (unique per company), Name, StartDate?, EndDate?, IsActive | ProjectCreated |

#### Extended Entities (5)
| Entity | New Columns Added |
|--------|-------------------|
| **FiscalYear** | CompanyId (FK), StartDate, EndDate, Description |
| **FiscalPeriod** | StartDate, EndDate, PeriodType (enum) |
| **Account** | CompanyId (FK), Description, NormalBalance (enum) |
| **AccountGroup** | CompanyId (FK), DisplayOrder |
| **JournalEntryLine** | DepartmentId?, CostCenterId?, ProjectId? (all nullable FKs) |

#### Unchanged Entities (3)
| Entity | Notes |
|--------|-------|
| **JournalEntry** | No schema changes |
| **PostingReference** | No schema changes |
| **BaseEntity** | Abstract base — no table |

### Final Database Schema — All Tables (13)

#### New Tables (6)
| Table | Columns | Indexes |
|-------|---------|---------|
| `companies` | id, name, tax_code (unique), address, phone, email, fiscal_year_start_month, fiscal_year_start_day, functional_currency_code, is_active, xmin | IX_companies_tax_code (unique) |
| `currencies` | id, code (unique), name, symbol, decimal_places, is_default, is_active, xmin | IX_currencies_code (unique) |
| `exchange_rates` | id, company_id FK, from_currency_code, to_currency_code, rate, rate_type, effective_date, source, xmin | IX_exchange_rates_company_id_from_currency_code_to_currency_co~ (composite unique) |
| `departments` | id, company_id FK, code, name, is_active, xmin | IX_departments_company_id_code (composite unique) |
| `cost_centers` | id, company_id FK, code, name, is_active, xmin | IX_cost_centers_company_id_code (composite unique) |
| `projects` | id, company_id FK, code, name, start_date, end_date, is_active, xmin | IX_projects_company_id_code (composite unique) |

#### Altered Tables (5)
| Table | New Columns Added |
|-------|-------------------|
| `fiscal_years` | company_id FK, start_date, end_date, description |
| `fiscal_periods` | start_date, end_date, period_type |
| `accounts` | company_id FK, description, normal_balance |
| `account_groups` | company_id FK, display_order |
| `journal_entry_lines` | department_id FK, cost_center_id FK, project_id FK |

#### Unchanged Tables (2)
| Table | Notes |
|-------|-------|
| `journal_entries` | No schema changes |
| `posting_references` | No schema changes |

### Key Architectural Decisions

1. **FK to Company pattern** — Universal: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — prevents cascade delete across all company-scoped entities
2. **Composite unique indexes** — Per-company uniqueness enforced at DB level (dimensions, exchange rates) — defense-in-depth beyond application validation
3. **Enum storage** — All enums stored as string via `HasConversion<string>()` — PeriodType, NormalBalance, ExchangeRateType, AccountType, PeriodStatus
4. **String over FK for currency codes** — Money VO uses `string Currency` — entities store currency codes as string, not FK to Currency entity
5. **Event minimalism** — Domain events carry entity ID + company ID only — no data duplication in events
6. **Backwards-compatible method expansion** — New params added at end with defaults — no existing callers broken
7. **Soft-delete only** — IsActive pattern everywhere (Company, Currency, Dimensions, Accounts) — no hard delete for audit trail
8. **Private parameterless constructors** — EF Core materialization without exposing invalid state
9. **Single migration for cohesive feature** — Not per-task migrations — appropriate for G1/G2 scope as one unit

### What Was Built vs What Existed

#### Built from Scratch (G1-G2)
- **Company entity** — Full domain entity with validation, events, repository
- **Currency entity** — Promoted from VO to entity with Symbol, DecimalPlaces, IsActive
- **ExchangeRate entity** — Full entity with invariants (From≠To, Rate>0), composite unique index
- **Department, CostCenter, Project** — All three dimension entities with same pattern
- **6 new EF Core configurations** — Following established snake-case + xmin pattern
- **6 new repository implementations** — Constructor-injected DbContext pattern
- **6 new port interfaces** — In Domain/Ports/, zero NuGet deps
- **6 new domain events** — Minimal: entity ID + company ID
- **EF Core migration** — Single `AccountingFoundation` migration covering all changes

#### Extended Existing (G2)
- **FiscalYear** — Added CompanyId FK, StartDate, EndDate, Description
- **FiscalPeriod** — Added StartDate, EndDate, PeriodType
- **Account** — Added CompanyId FK, Description, NormalBalance
- **AccountGroup** — Added CompanyId FK, DisplayOrder
- **JournalEntryLine** — Added 3 optional dimension FKs (DepartmentId, CostCenterId, ProjectId)

#### Already Existed (Pre-G1)
- Account, AccountGroup, FiscalYear, FiscalPeriod, JournalEntry, JournalEntryLine, PostingReference (7 entities)
- Money, AccountCode, Currency (VO), AccountType, PeriodStatus, FiscalYearStatus (6 VOs/enums)
- AccountCreated, AccountDeprecated, JournalEntryPosted, PeriodClosed (4 events)
- 4 domain exceptions, 7 port interfaces, 2 repository implementations
- 7 EF Core configurations, DbContext, DI registration
- Application layer: CQRS commands/queries, DTOs, validators
- Api layer: MVC controllers, ViewModels, Swagger
- Architecture tests: 22 tests enforcing Clean Architecture constraints

### Migration Verification Summary
- **Build**: 0 warnings, 0 errors ✅
- **Architecture tests**: 22/22 pass ✅
- **Migration list**: InitialCreate → FixAccountNameColumn → AccountingFoundation (Pending) ✅
- **Migration pending** — not applied to database (per plan requirement)
- **Backfill note**: `defaultValue: 0L` on non-nullable company_id columns — existing rows get 0, must be backfilled in production
