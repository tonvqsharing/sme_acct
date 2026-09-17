# Phase 1 Domain Model Research — SME Accounting App

## 1. Project Structure Overview

```
SmeAccounting/
├── src/
│   ├── SmeAccounting.Domain/          — Pure domain: entities, VOs, ports, events, exceptions
│   ├── SmeAccounting.Application/     — CQRS: commands, queries, DTOs, validators, behaviors
│   ├── SmeAccounting.Infrastructure/  — EF Core, repos, adapters, services
│   └── SmeAccounting.Api/             — ASP.NET MVC controllers, Program.cs
└── tests/
    └── SmeAccounting.ArchitectureTests/ — 22 NetArchTest constraint tests
```

---

## 2. Domain Layer (`SmeAccounting.Domain`)

### 2.1 BaseEntity Contract

**File:** `src/SmeAccounting.Domain/Entities/BaseEntity.cs`

```csharp
public abstract class BaseEntity
{
    public long Id { get; set; }
    private readonly List<DomainEvent> _domainEvents = [];
    public IReadOnlyCollection<DomainEvent> DomainEvents => _domainEvents.AsReadOnly();
    protected BaseEntity() { }
    protected BaseEntity(long id) => Id = id;
    public void AddDomainEvent(DomainEvent domainEvent) => _domainEvents.Add(domainEvent);
    public void RemoveDomainEvent(DomainEvent domainEvent) => _domainEvents.Remove(domainEvent);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

Key points:
- **Identity:** `long Id` (sequence-generated via EF Core `ValueGeneratedOnAdd`)
- **Concurrency token:** `xmin` (PostgreSQL row version) — configured on EVERY entity via EF Core configurations, NOT on BaseEntity itself. Each `IEntityTypeConfiguration<T>` adds: `builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");`
- **Audit fields:** NONE on BaseEntity. Audit is via domain events and `IAuditLogger` port
- **Domain events:** In-memory collection with add/remove/clear. Events are collected pre-save and dispatched post-save in `SaveChangesAsync`

### 2.2 Domain Events Base

**File:** `src/SmeAccounting.Domain/Events/DomainEvent.cs`

```csharp
public abstract class DomainEvent
{
    public DateTimeOffset OccurredOn { get; }
    public Guid EventId { get; }
    protected DomainEvent(DateTimeOffset occurredOn)
    {
        OccurredOn = occurredOn;
        EventId = Guid.NewGuid();
    }
}
```

Events are ignored by EF Core (all explicitly `modelBuilder.Ignore<>` in DbContext).

---

## 3. All Entities — Properties, Relationships, Invariants

### 3.1 Account

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| Code | AccountCode | Value object, owned, numeric >= 4 digits |
| Name | string | |
| Level | int | Hierarchy depth |
| ParentId | long? | Self-referencing FK, nullable for root accounts |
| AccountType | AccountType | Enum: Asset/Liability/Equity/Revenue/Expense |
| IsActive | bool | Default true, soft-disable via Deprecate() |
| AccountGroupId | long? | FK to AccountGroup |
| CompanyId | long | FK to Company, required |
| Description | string? | Max 500 |
| NormalBalance | NormalBalance | Enum: Debit/Credit |
| Children | IReadOnlyCollection<Account> | Navigation, self-referencing tree |

**Invariants:**
- `Code` cannot be null/empty (ArgumentNullException)
- `CompanyId` must be > 0 (ArgumentOutOfRangeException)
- `Deprecate()` sets IsActive=false, raises `AccountDeprecated` event
- `AddChild()` creates child with Level+1, sets ParentId
- Tree structure: parent-child via self-referencing FK with `DeleteBehavior.Restrict`

### 3.2 AccountGroup

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| Code | string | Max 20, required |
| Name | string | Max 200, required |
| AccountType | AccountType | Enum |
| CompanyId | long | FK to Company |
| DisplayOrder | int | Default 0 |

### 3.3 Company

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| Name | string | Max 200, required |
| TaxCode | string | Max 13, UNIQUE index, required |
| Address | string | Max 500, required |
| Phone | string? | Max 20 |
| Email | string? | Max 200 |
| FiscalYearStartMonth | int | 1-12, default 1 |
| FiscalYearStartDay | int | 1-28, default 1 |
| FunctionalCurrencyCode | string | 3 chars, default "VND" |
| IsActive | bool | Default true |

**Invariants:**
- FiscalYearStartMonth must be 1-12
- FiscalYearStartDay must be 1-28 (safe for all months)
- Raises `CompanyCreated` on construction

### 3.4 FiscalYear

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| CompanyId | long | FK to Company |
| Year | int | |
| StartDate | DateOnly | |
| EndDate | DateOnly | |
| Description | string? | |
| Status | FiscalYearStatus | Enum: Open/Closed |
| Periods | IReadOnlyCollection<FiscalPeriod> | Navigation |

**Invariants:**
- CompanyId must be > 0
- StartDate must be before EndDate
- Raises `FiscalYearCreated` event
- `AddPeriod()` creates child FiscalPeriod

### 3.5 FiscalPeriod

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| YearId | long | FK to FiscalYear |
| Month | int | |
| StartDate | DateOnly | |
| EndDate | DateOnly | |
| PeriodType | PeriodType | Enum: Monthly/Quarterly |
| Status | PeriodStatus | Enum: Open/Closing/Closed |
| OpenedAt | DateTimeOffset? | |
| ClosedAt | DateTimeOffset? | |

**Invariants:**
- `Open()` sets Status=Open, records timestamp
- `Close()` sets Status=Closed, records timestamp, raises `PeriodClosed` event

### 3.6 Currency (Entity)

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| Code | string | 3 uppercase chars (ISO 4217), UNIQUE index |
| Name | string | Max 100, required |
| Symbol | string | Max 10, required |
| DecimalPlaces | int | Default 2 |
| IsDefault | bool | |
| IsActive | bool | Default true |

**Invariants:**
- Code must be exactly 3 uppercase characters
- Raises `CurrencyCreated` event

### 3.7 Department

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| CompanyId | long | FK to Company |
| Code | string | Max 50, required |
| Name | string | Max 200, required |
| IsActive | bool | Default true |

**Invariants:**
- Unique index on (CompanyId, Code)
- CompanyId must be > 0
- Raises `DepartmentCreated` event

### 3.8 CostCenter

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| CompanyId | long | FK to Company |
| Code | string | Max 50, required |
| Name | string | Max 200, required |
| IsActive | bool | Default true |

**Invariants:**
- Unique index on (CompanyId, Code)
- CompanyId must be > 0
- Raises `CostCenterCreated` event

### 3.9 Project

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| CompanyId | long | FK to Company |
| Code | string | Max 50, required |
| Name | string | Max 200, required |
| StartDate | DateOnly? | Optional |
| EndDate | DateOnly? | Optional |
| IsActive | bool | Default true |

**Invariants:**
- Unique index on (CompanyId, Code)
- CompanyId must be > 0
- Raises `ProjectCreated` event

### 3.10 JournalEntry

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| EntryNumber | string | Max 50, required, indexed |
| Date | DateTimeOffset | |
| PeriodId | long | FK to FiscalPeriod, indexed |
| Description | string? | Max 500 |
| SourceType | string? | Max 100 — polymorphic source reference |
| SourceId | long? | Polymorphic source reference |
| PostedBy | string? | Max 100 |
| PostedAt | DateTimeOffset? | |
| IsPosted | bool | Immutable once posted |
| Lines | IReadOnlyCollection<JournalEntryLine> | Navigation |

**Invariants:**
- `AddLine()` blocked if IsPosted
- `Post()` blocked if already posted; validates balance; raises `JournalEntryPosted`
- `ValidateBalance()` sums Debit/Credit amounts; throws `InvalidPostingRuleException` if unbalanced
- `SetSource()` links to external entity (polymorphic association)

### 3.11 JournalEntryLine

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| EntryId | long | FK to JournalEntry, indexed |
| AccountId | long | FK to Account, indexed |
| Debit | Money | Value object, owned |
| Credit | Money | Value object, owned |
| Description | string? | Max 500 |
| DepartmentId | long? | FK to Department, SetNull on delete, indexed |
| CostCenterId | long? | FK to CostCenter, SetNull on delete, indexed |
| ProjectId | long? | FK to Project, SetNull on delete, indexed |

**Key:** Money value objects are owned via `OwnsOne()` and stored as:
- `debit_amount` (decimal)
- `debit_currency` (string, max 3)
- `credit_amount` (decimal)
- `credit_currency` (string, max 3)

### 3.12 PostingReference

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| JournalEntryId | long | FK to JournalEntry, indexed |
| SourceType | string | Max 100, required, composite index |
| SourceId | long | Composite index with SourceType |

### 3.13 ExchangeRate

| Property | Type | Notes |
|----------|------|-------|
| Id | long | BaseEntity |
| CompanyId | long | FK to Company |
| FromCurrencyCode | string | 3 chars, uppercase, required |
| ToCurrencyCode | string | 3 chars, uppercase, required |
| Rate | decimal | decimal(10,6) |
| RateType | ExchangeRateType | Enum: Average/Actual/Book/Contract |
| EffectiveDate | DateOnly | |
| Source | string? | Max 200 |

**Invariants:**
- Unique index on (CompanyId, FromCurrencyCode, ToCurrencyCode, RateType, EffectiveDate)
- FromCurrencyCode and ToCurrencyCode must differ
- Rate must be > 0
- Currency codes normalized to uppercase on construction
- Raises `ExchangeRateRecorded` event

---

## 4. Value Objects

### 4.1 AccountCode (record)

```csharp
public record AccountCode
{
    public string Value { get; }
    public AccountCode(string value) { ... }
}
```
- Must be numeric (all digits)
- Must be at least 4 characters
- Throws `DomainException` on invalid input
- Owned by Account via `OwnsOne()`, stored as `code` column (max 20)

### 4.2 Money (record)

```csharp
public record Money
{
    public decimal Amount { get; }
    public string Currency { get; }
    public static Money Zero => new(0m, "VND");
    // operator+ and operator- with same-currency enforcement
}
```
- Arithmetic operators enforce same currency
- Used by JournalEntryLine (Debit/Credit)
- Default zero: `Money.Zero` = 0 VND

### 4.3 Currency VO (record)

```csharp
public record Currency(string Code, string Name, bool IsDefault);
```
- Distinct from `Currency` entity. This is a lightweight read-only VO

### 4.4 Enums

| Enum | Values | Used By |
|------|--------|---------|
| AccountType | Asset, Liability, Equity, Revenue, Expense | Account, AccountGroup |
| NormalBalance | Debit, Credit | Account |
| PeriodType | Monthly, Quarterly | FiscalPeriod |
| PeriodStatus | Open, Closing, Closed | FiscalPeriod |
| FiscalYearStatus | Open, Closed | FiscalYear |
| ExchangeRateType | Average, Actual, Book, Contract | ExchangeRate |

All enums stored as strings in DB via `HasConversion<string>()`.

---

## 5. Port Interfaces

### 5.1 Repository Ports (Domain/Ports/)

| Interface | Methods | Notes |
|-----------|---------|-------|
| IAccountRepository | GetByIdAsync, GetAllAsync, AddAsync, UpdateAsync | Includes Children via Include |
| IJournalEntryRepository | GetByIdAsync, GetAllAsync, AddAsync | Lines via Include |
| ICompanyRepository | GetByIdAsync, GetByTaxCodeAsync, GetAllAsync, AddAsync | TaxCode lookup |
| ICurrencyRepository | GetByIdAsync, GetByCodeAsync, GetAllAsync, AddAsync | Code lookup |
| IDepartmentRepository | GetByIdAsync, GetByCodeAsync(code, companyId), GetAllAsync, AddAsync | Composite code lookup |
| ICostCenterRepository | GetByIdAsync, GetByCodeAsync(code, companyId), GetAllAsync, AddAsync | Composite code lookup |
| IProjectRepository | GetByIdAsync, GetByCodeAsync(code, companyId), GetAllAsync, AddAsync | Composite code lookup |
| IExchangeRateRepository | GetByIdAsync, GetByCurrencyPairAsync(from, to, rateType, date), GetAllAsync, AddAsync | Complex lookup |

### 5.2 Infrastructure Ports

| Interface | Contract | Notes |
|-----------|----------|-------|
| IUnitOfWork | `Task<int> SaveChangesAsync(CancellationToken)` | Implemented by DbContext |
| IClock | `DateTimeOffset Now { get; }` | Testability seam |
| IAuditLogger | `Task LogAsync(action, entity, entityId, details)` | Console impl |
| IPostingService | `Task PostAsync(JournalEntry entry)` | Posting orchestration |
| IForeignExchangeRateProvider | `Task<Money> ConvertAsync(Money amount, string targetCurrency, DateTimeOffset date)` | Mock bank provider |

---

## 6. Domain Events (12 events)

| Event | Properties | Raised By |
|-------|-----------|-----------|
| DomainEvent (base) | OccurredOn, EventId | — |
| AccountCreated | AccountId | (unused directly — Account constructor doesn't raise it) |
| AccountDeprecated | AccountId | Account.Deprecate() |
| CompanyCreated | CompanyId | Company constructor |
| CurrencyCreated | CurrencyId | Currency constructor |
| DepartmentCreated | DepartmentId, CompanyId | Department constructor |
| CostCenterCreated | CostCenterId, CompanyId | CostCenter constructor |
| ProjectCreated | ProjectId, CompanyId | Project constructor |
| FiscalYearCreated | FiscalYearId, CompanyId, Year | FiscalYear constructor |
| ExchangeRateRecorded | ExchangeRateId, CompanyId | ExchangeRate constructor |
| JournalEntryPosted | EntryId | JournalEntry.Post() |
| PeriodClosed | PeriodId | FiscalPeriod.Close() |

**Note:** `PublishDomainEventAsync()` in DbContext is currently a no-op (`await Task.CompletedTask`). Events are collected but not yet dispatched via MediatR `IPublisher`.

---

## 7. Domain Exceptions

| Exception | Message Pattern |
|-----------|----------------|
| DomainException | Base exception, custom message |
| AccountNotLeafException | "Account {id} has child accounts and cannot accept postings." |
| InvalidPostingRuleException | Custom message (used for unbalanced entries) |
| PeriodClosedException | "Period {id} is closed and cannot accept new postings." |

---

## 8. Naming Conventions

### 8.1 Database (snake_case)

All table and column names use snake_case via `EFCore.NamingConventions` package and explicit `HasColumnName()`:

| Entity | Table Name |
|--------|-----------|
| Account | accounts |
| AccountGroup | account_groups |
| Company | companies |
| FiscalYear | fiscal_years |
| FiscalPeriod | fiscal_periods |
| Currency | currencies |
| Department | departments |
| CostCenter | cost_centers |
| Project | projects |
| JournalEntry | journal_entries |
| JournalEntryLine | journal_entry_lines |
| PostingReference | posting_references |
| ExchangeRate | exchange_rates |

### 8.2 C# Code

- **Private fields:** `_camelCase` (enforced by .editorconfig)
- **Entities:** PascalCase properties, private setters
- **Value objects:** Records with PascalCase
- **Port interfaces:** `I` prefix + PascalCase (e.g., `IAccountRepository`)
- **Commands:** `VerbNounCommand` (e.g., `CreateAccountCommand`)
- **Queries:** `VerbNounQuery` (e.g., `GetAccountQuery`)
- **DTOs:** `NounDto` (e.g., `AccountDto`)
- **Validators:** `CommandNameValidator` (e.g., `CreateAccountCommandValidator`)
- **Controllers:** `NounController` (e.g., `ChartOfAccountsController`)

### 8.3 EF Core Concurrency

Every entity uses PostgreSQL `xmin` row version:
```csharp
builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
```

---

## 9. Application Layer (`SmeAccounting.Application`)

### 9.1 NuGet Dependencies

- `MediatR` 14.2.0
- `FluentValidation` 12.1.0
- `FluentValidation.DependencyInjectionExtensions` 12.1.0
- References only `SmeAccounting.Domain`

### 9.2 CQRS Commands

| Command | Result | Validation |
|---------|--------|-----------|
| CreateAccountCommand | CreateAccountResult(long Id) | Code (regex \d{4,}), Name (max 200), AccountType (enum) |
| DeprecateAccountCommand | DeprecateAccountResult(long AccountId) | None |
| CreateJournalEntryCommand | CreateJournalEntryResult(long Id, string EntryNumber) | PeriodId > 0, Lines not empty, each line AccountId > 0 |
| PostJournalEntryCommand | PostJournalEntryResult(long JournalEntryId, DateTimeOffset PostedAt) | JournalEntryId > 0 |
| CloseFiscalPeriodCommand | CloseFiscalPeriodResult(long PeriodId, DateTimeOffset ClosedAt) | None |
| OpenFiscalPeriodCommand | OpenFiscalPeriodResult(long PeriodId) | None |

**Input DTO:** `JournalEntryLineInput(AccountId, DebitAmount, CreditAmount, Description)`

### 9.3 CQRS Queries

| Query | Return Type |
|-------|------------|
| GetAccountQuery(AccountId) | AccountDto? |
| GetAccountsByGroupQuery(AccountGroupId) | IReadOnlyList<AccountDto> |
| GetJournalEntryQuery(JournalEntryId) | JournalEntryDto? |
| GetFiscalPeriodsQuery(YearId?) | IReadOnlyList<FiscalPeriodDto> |
| GetBalanceSheetQuery(PeriodId) | BalanceSheetDto |
| GetIncomeStatementQuery(PeriodId) | IncomeStatementDto |

### 9.4 DTOs (all records)

| DTO | Properties |
|-----|-----------|
| AccountDto | Id, Code, Name, Level, ParentId?, AccountType, IsActive, AccountGroupId?, CompanyId, Description?, NormalBalance |
| JournalEntryDto | Id, EntryNumber, Date, PeriodId, Description?, IsPosted, PostedAt?, Lines |
| JournalEntryLineDto | Id, AccountId, Debit(MoneyDto), Credit(MoneyDto), Description?, DepartmentId?, CostCenterId?, ProjectId? |
| MoneyDto | Amount, Currency |
| FiscalYearDto | Id, CompanyId, Year, StartDate, EndDate, Description?, Status |
| FiscalPeriodDto | Id, YearId, Month, StartDate, EndDate, PeriodType, Status, OpenedAt?, ClosedAt? |
| BalanceSheetDto | Assets, Liabilities, Equity (each IReadOnlyList<AccountGroupTotal>) |
| AccountGroupTotal | GroupName, Total, Currency |
| IncomeStatementDto | Revenue, Expenses (IReadOnlyList<AccountGroupTotal>), NetIncome, Currency |

### 9.5 ValidationBehavior (MediatR Pipeline)

```csharp
public class ValidationBehavior<TRequest, TResponse>(IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
```
- Runs all FluentValidation validators before handler
- Throws `ValidationException` with aggregated failures
- Skipped if no validators registered

### 9.6 IAccountingReportService

```csharp
public interface IAccountingReportService
{
    Task<BalanceSheetDto> GetBalanceSheetAsync(long periodId, CancellationToken ct);
    Task<IncomeStatementDto> GetIncomeStatementAsync(long periodId, CancellationToken ct);
}
```
- Defined in Application layer
- No implementation found yet (stub)

### 9.7 DI Registration

```csharp
services.AddMediatR(cfg => {
    cfg.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly);
    cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
});
services.AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly);
```

---

## 10. Infrastructure Layer (`SmeAccounting.Infrastructure`)

### 10.1 NuGet Dependencies

- `Microsoft.EntityFrameworkCore` 10.0.4
- `Npgsql.EntityFrameworkCore.PostgreSQL` 10.0.3
- `Microsoft.Extensions.DependencyInjection` 10.0.12
- `EFCore.NamingConventions` 10.0.*
- References: Application + Domain

### 10.2 DbContext

**File:** `SmeAccountingDbContext.cs`

- 13 DbSets (all entities)
- Implements `IUnitOfWork`
- `OnModelCreating`: ignores all 12 domain event types, applies configurations from assembly
- `SaveChangesAsync`: collects domain events pre-save, dispatches post-save (currently no-op)

### 10.3 Entity Configurations (14 files)

All in `Persistence/Configurations/`, all `internal sealed`, all `IEntityTypeConfiguration<T>`:

| Configuration | Table | Key Indexes | Special |
|--------------|-------|-------------|---------|
| AccountConfiguration | accounts | Id, ParentId | OwnsOne(AccountCode), self-referencing tree, Company FK Restrict |
| AccountGroupConfiguration | account_groups | Id | Company FK Restrict |
| CompanyConfiguration | companies | Id, TaxCode (UNIQUE) | — |
| FiscalYearConfiguration | fiscal_years | Id, YearId | Company FK Restrict |
| FiscalPeriodConfiguration | fiscal_periods | Id, YearId | — |
| CurrencyConfiguration | currencies | Id, Code (UNIQUE) | — |
| DepartmentConfiguration | departments | Id, (CompanyId, Code) UNIQUE | Company FK Restrict |
| CostCenterConfiguration | cost_centers | Id, (CompanyId, Code) UNIQUE | Company FK Restrict |
| ProjectConfiguration | projects | Id, (CompanyId, Code) UNIQUE | Company FK Restrict |
| JournalEntryConfiguration | journal_entries | Id, PeriodId, EntryNumber | — |
| JournalEntryLineConfiguration | journal_entry_lines | Id, EntryId, AccountId, DeptId, CostCenterId, ProjectId | OwnsOne(Money)x2, FKs SetNull |
| PostingReferenceConfiguration | posting_references | Id, JournalEntryId, (SourceType, SourceId) | — |
| ExchangeRateConfiguration | exchange_rates | Id, (Company, From, To, RateType, Date) UNIQUE | Rate decimal(10,6) |

### 10.4 Repositories (8 implementations)

All `Ef*Repository` classes:
- Take `SmeAccountingDbContext` via constructor injection
- `GetByIdAsync`: uses tracked queries with Includes where needed
- `GetAllAsync`: uses `AsNoTracking()` with `OrderBy`
- `AddAsync`: delegates to `DbSet.AddAsync`
- `UpdateAsync`: only on EfAccountRepository (others rely on change tracking)

### 10.5 Adapters

| Adapter | Port | Status |
|---------|------|--------|
| BankExchangeRateProvider | IForeignExchangeRateProvider | Mock implementation with hardcoded VND/USD/EUR rates |
| EInvoiceProviderAdapter | (none) | Placeholder — throws NotImplementedException |
| DigitalSignatureAdapter | (none) | Placeholder — throws NotImplementedException |

### 10.6 Services

| Service | Port | Implementation |
|---------|------|---------------|
| SystemClock | IClock | Returns `DateTimeOffset.UtcNow` |
| AuditLogger | IAuditLogger | Console.WriteLine stub |

### 10.7 DI Registration

```csharp
services.AddDbContext<SmeAccountingDbContext>(...UseNpgsql...)
services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<SmeAccountingDbContext>())
// 8 repository registrations (all Scoped)
services.AddSingleton<IClock, SystemClock>()
services.AddScoped<IAuditLogger, AuditLogger>()
services.AddScoped<IForeignExchangeRateProvider, BankExchangeRateProvider>()
```

---

## 11. Migration History

| Migration | Date | Description |
|-----------|------|-------------|
| 20260916051341_InitialCreate | Sep 16 2026 05:13 | Initial schema |
| 20260916051520_FixAccountNameColumn | Sep 16 2026 05:15 | Fix Account name column |
| 20260916083803_AccountingFoundation | Sep 16 2026 08:38 | Foundation accounting tables |

All migrations target PostgreSQL via Npgsql. Connection: `Host=172.21.208.1;Database=sme_acct_dev;Username=dev;Password=123456`.

---

## 12. Seed Data / Configuration

**No seed data found.** No `HasData()` calls in any configuration. No migration seed data. The domain starts empty.

---

## 13. Architecture Tests (5 test files, 22 tests)

### 13.1 DomainPurityTests (3 tests)
1. `Domain_Should_Have_No_NuGet_PackageReferences` — Parses Domain .csproj, asserts zero PackageReference elements
2. `Domain_Should_Not_Reference_Microsoft_Or_Npgsql_Packages` — Checks no Microsoft/Npgsql/Serilog/EFCore packages
3. `Domain_Should_Have_No_EntityFramework_Assembly_Dependency` — NetArchTest: no dependency on Microsoft.EntityFrameworkCore

### 13.2 NamingConventionsTests (6 tests)
1. Entities inheriting BaseEntity must reside in `SmeAccounting.Domain.Entities`
2. Repository interfaces must start with `I`
3. Commands in Commands namespace must end with `Command`
4. Queries in Queries namespace must end with `Query`
5. DTOs in DTOs namespace must end with `Dto`
6. Controllers must end with `Controller`

### 13.3 LayerCouplingTests (4 tests)
1. Controllers must NOT reference `Domain.Entities`
2. Controllers must NOT reference `Domain.Ports`
3. Application handlers must NOT reference `Infrastructure`
4. Infrastructure must NOT reference `Api`

### 13.4 DependencyRulesTests (7 tests)
1. Domain must NOT depend on Application
2. Domain must NOT depend on Infrastructure
3. Domain must NOT depend on Api
4. Application must NOT depend on Infrastructure
5. Application must NOT depend on Api
6. Infrastructure must NOT depend on Api
7. Api controllers must NOT depend on Infrastructure

### 13.5 PostingRuleIsolationTests (2 tests)
1. IPostingService must reside in Domain assembly
2. JournalEntry, Money, and IPostingService must all be in Domain assembly

---

## 14. API Layer (`SmeAccounting.Api`)

### 14.1 Program.cs

- ASP.NET MVC with Controllers + Views
- Swagger/Swashbuckle in development
- Conventional routing: `{controller=Home}/{action=Index}/{id?}`
- Calls `AddApplication()` and `AddInfrastructure()` for DI composition

### 14.2 Controllers (6)

| Controller | Actions | Dependencies |
|-----------|---------|-------------|
| HomeController | Index, About, Error | None |
| ChartOfAccountsController | Index, Create, Deprecate | IMediator |
| JournalEntryController | Index, Create, Post | IMediator |
| FiscalPeriodController | Index, Open, Close | IMediator |
| ReportingController | BalanceSheet, IncomeStatement | IMediator |
| SettingsController | Index | None |

All MediatR-dispatching controllers follow thin controller pattern. Use `[ValidateAntiForgeryToken]` on POST actions. Catch `ValidationException` to populate ModelState.

### 14.3 ViewModels (5)

| ViewModel | Type | Properties |
|-----------|------|-----------|
| ChartOfAccountsViewModel | record | Accounts, SelectedGroupFilter? |
| FiscalPeriodViewModel | record | Periods |
| JournalEntryViewModel | record | Entries |
| CreateAccountViewModel | class | Code, Name, AccountType, CompanyId, NormalBalance, ParentId?, AccountGroupId?, Description? |
| CreateJournalEntryViewModel | class | Date, PeriodId, Description?, Lines |

CreateAccountViewModel uses Vietnamese validation attributes (e.g., "Ma tai khoan la bat buoc").

---

## 15. Dependency Graph

```
Api ──→ Application ──→ Domain
 │                         ↑
 └──→ Infrastructure ──────┘
```

**Enforced by 22 architecture tests.** Clean Architecture: Domain is the innermost ring with zero external dependencies. Application depends only on Domain. Infrastructure implements Domain ports. Api is the composition root.

---

## 16. Notable Design Decisions

1. **No audit fields on BaseEntity** — Audit is via domain events + `IAuditLogger` port, not columns
2. **xmin concurrency** — PostgreSQL row-level optimistic concurrency on all 13 entities
3. **Domain events collected but not dispatched** — `PublishDomainEventAsync` is a no-op; events accumulate but are not processed
4. **No seed data** — Clean start, no HasData() in configurations
5. **Mock exchange rates** — `BankExchangeRateProvider` returns hardcoded VND/USD/EUR rates
6. **Placeholder adapters** — E-invoice and digital signature adapters throw NotImplementedException
7. **Account hierarchy** — Self-referencing tree with Level tracking, Restrict delete
8. **Money as owned value object** — Stored as separate columns (amount + currency), not JSON
9. **AccountCode as owned value object** — Stored as `code` column, validated for numeric >= 4 digits
10. **Multi-tenant ready** — CompanyId on most entities, unique indexes scoped per company

---

## Task-Specific Research — Task 1: Voucher Type

**Goal:** Create VoucherType entity, VoucherCategory enum, IVoucherTypeRepository port, EF configuration, repository implementation, and DI registration.

**File list (6 new files, 2 modified files):**

### New Files

| # | File Path | Layer |
|---|-----------|-------|
| 1 | `src/SmeAccounting.Domain/ValueObjects/VoucherCategory.cs` | Domain |
| 2 | `src/SmeAccounting.Domain/Entities/VoucherType.cs` | Domain |
| 3 | `src/SmeAccounting.Domain/Events/VoucherTypeCreated.cs` | Domain |
| 4 | `src/SmeAccounting.Domain/Ports/IVoucherTypeRepository.cs` | Domain |
| 5 | `src/SmeAccounting.Infrastructure/Persistence/Configurations/VoucherTypeConfiguration.cs` | Infrastructure |
| 6 | `src/SmeAccounting.Infrastructure/Repositories/EfVoucherTypeRepository.cs` | Infrastructure |

### Modified Files

| # | File Path | Change |
|---|-----------|--------|
| 7 | `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` | Add DbSet + Ignore event |
| 8 | `src/SmeAccounting.Infrastructure/DependencyInjection.cs` | Register repository |

**Total: 6 new files, 2 modified files.**

---

### 1. VoucherCategory Enum

**File:** `src/SmeAccounting.Domain/ValueObjects/VoucherCategory.cs`

**GOTCHA — Enum Location:** The PLAN.md specifies `Domain/Enums/VoucherCategory.cs` but NO `Domain/Enums/` directory exists. All 6 existing enums live in `Domain/ValueObjects/`. Creating `Domain/Enums/` is safe (no arch test constrains enum location), but following established convention (`Domain/ValueObjects/`) is better for consistency. Use `Domain/ValueObjects/`.

**Pattern (copy from existing):**

```csharp
namespace SmeAccounting.Domain.ValueObjects;

public enum VoucherCategory
{
    Receipt,
    Payment,
    Journal,
    Adjustment,
    Opening
}
```

**Exact pattern reference:** `src/SmeAccounting.Domain/ValueObjects/AccountType.cs` — same structure (enum, no attributes, PascalCase values).

**DB storage:** Will use `HasConversion<string>()` in EF configuration (same as AccountType, PeriodType, etc. per G2 global pattern).

---

### 2. VoucherType Entity

**File:** `src/SmeAccounting.Domain/Entities/VoucherType.cs`

**Closest pattern to copy:** `src/SmeAccounting.Domain/Entities/Department.cs` (or CostCenter/Project — all identical structure: CompanyId + Code + Name + IsActive + DomainException invariants + DomainCreated event).

**Exact entity pattern:**

```csharp
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Domain.Entities;

public class VoucherType : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public VoucherCategory VoucherCategory { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private VoucherType() { }

    public VoucherType(long companyId, string code, string name, VoucherCategory voucherCategory, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        Code = code;
        Name = name;
        VoucherCategory = voucherCategory;
        Description = description;

        AddDomainEvent(new VoucherTypeCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
```

**Key pattern observations (from Department/CostCenter/Project):**
- Invariant validation uses `DomainException`, NOT `ArgumentNullException` or `ArgumentOutOfRangeException` (those are older patterns from Account/Company)
- `DomainException` is the standard for all entities created in T5+ (Department, CostCenter, Project, ExchangeRate)
- Private parameterless constructor `private VoucherType() { }` — enables EF Core materialization without exposing invalid state
- `IsActive` default = `true`, no setter needed — only `Deactivate()` method changes it
- `Description` is nullable (optional), no max length constraint in domain (enforced in EF config)
- Domain event raised in constructor with `AddDomainEvent(new VoucherTypeCreated(Id, companyId, DateTimeOffset.UtcNow))`
- NOTE: `Id` is 0 at constructor time (set by EF Core after SaveChanges). Events carry `Id=0` until DB assigns the real ID. This matches existing pattern exactly.

**Domain event template** (`src/SmeAccounting.Domain/Events/VoucherTypeCreated.cs`):

```csharp
namespace SmeAccounting.Domain.Events;

public class VoucherTypeCreated : DomainEvent
{
    public long VoucherTypeId { get; }
    public long CompanyId { get; }

    public VoucherTypeCreated(
        long voucherTypeId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        VoucherTypeId = voucherTypeId;
        CompanyId = companyId;
    }
}
```

**Exact pattern reference:** `src/SmeAccounting.Domain/Events/DepartmentCreated.cs` — identical structure (entity ID + CompanyId + occurredOn).

---

### 3. IVoucherTypeRepository Port

**File:** `src/SmeAccounting.Domain/Ports/IVoucherTypeRepository.cs`

**Pattern (copy from IDepartmentRepository):**

```csharp
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IVoucherTypeRepository
{
    Task<VoucherType?> GetByIdAsync(long id);
    Task<VoucherType?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<VoucherType>> GetAllAsync();
    Task AddAsync(VoucherType voucherType);
}
```

**Exact pattern reference:** `src/SmeAccounting.Domain/Ports/IDepartmentRepository.cs` — identical method signatures (GetByIdAsync, GetByCodeAsync(code, companyId), GetAllAsync, AddAsync).

**Note:** `GetByCodeAsync(code, companyId)` — composite lookup scoped to company. This matches Department/CostCenter/Project pattern where code uniqueness is per-company.

---

### 4. VoucherType EF Configuration

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/VoucherTypeConfiguration.cs`

**Pattern (copy from DepartmentConfiguration):**

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class VoucherTypeConfiguration : IEntityTypeConfiguration<VoucherType>
{
    public void Configure(EntityTypeBuilder<VoucherType> builder)
    {
        builder.ToTable("voucher_types");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.Code)
            .HasColumnName("code")
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.VoucherCategory)
            .HasColumnName("voucher_category")
            .HasConversion<string>();

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.CompanyId, e.Code })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
```

**Critical configuration patterns (from all 13 existing configs):**
1. Class: `internal sealed class VoucherTypeConfiguration : IEntityTypeConfiguration<VoucherType>`
2. `ToTable("voucher_types")` — snake_case, plural
3. `HasKey(e => e.Id)`
4. `Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd()` — always present
5. Each property: `HasColumnName("snake_case_name")`
6. Strings: `.IsRequired().HasMaxLength(N)` — Code=20, Name=200, Description=500
7. Enums: `.HasConversion<string>()` — universal pattern for all enums (AccountType, PeriodType, PeriodStatus, etc.)
8. Company FK: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — universal
9. Composite unique index: `HasIndex(e => new { e.CompanyId, e.Code }).IsUnique()` — same as Department/CostCenter/Project
10. xmin: `Property<uint>("xmin").IsRowVersion().HasColumnName("xmin")` — always last, always present

---

### 5. EfVoucherTypeRepository

**File:** `src/SmeAccounting.Infrastructure/Repositories/EfVoucherTypeRepository.cs`

**Pattern (copy from EfDepartmentRepository):**

```csharp
using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfVoucherTypeRepository : IVoucherTypeRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfVoucherTypeRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<VoucherType?> GetByIdAsync(long id)
    {
        return await _context.VoucherTypes
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<VoucherType?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.VoucherTypes
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<VoucherType>> GetAllAsync()
    {
        return await _context.VoucherTypes
            .AsNoTracking()
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(VoucherType voucherType)
    {
        await _context.VoucherTypes.AddAsync(voucherType);
    }
}
```

**Key patterns from all 8 existing repos:**
- `public class EfXxxRepository : IXxxRepository` — public, not internal
- Constructor: `private readonly SmeAccountingDbContext _context;` + one-liner constructor
- `GetByIdAsync`: tracked query (no `AsNoTracking`) — for change tracking
- `GetByCodeAsync`: tracked query with composite filter `(e.Code == code && e.CompanyId == companyId)`
- `GetAllAsync`: `AsNoTracking()` + `OrderBy` — read-only, optimized
- `AddAsync`: `await _context.Xxx.AddAsync(entity)` — delegates to DbSet
- No `UpdateAsync` needed — relies on EF Core change tracking (only Account has UpdateAsync)
- Lambda param name: `e` (or `c` for Company/Currency) — consistent within each file
- Namespace: `SmeAccounting.Infrastructure.Repositories`

---

### 6. DbContext Modifications

**File:** `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`

**Changes needed:**

**Add DbSet (line ~22, after existing DbSets):**
```csharp
public DbSet<VoucherType> VoucherTypes => Set<VoucherType>();
```

**Add Ignore for new event (line ~40, after existing Ignores):**
```csharp
modelBuilder.Ignore<VoucherTypeCreated>();
```

**Current DbSet count:** 13 DbSets → will become 14.
**Current Ignore count:** 12 events → will become 13.

---

### 7. DI Registration

**File:** `src/SmeAccounting.Infrastructure/DependencyInjection.cs`

**Add (line ~35, after existing repository registrations):**
```csharp
services.AddScoped<IVoucherTypeRepository, EfVoucherTypeRepository>();
```

**Pattern:** All repository registrations are `AddScoped<IXxxRepository, EfXxxRepository>()`. This is the universal pattern across all 8 existing registrations.

---

### 8. Gotchas and Edge Cases

#### 8.1 Enum Location Decision
The PLAN.md says `Domain/Enums/VoucherCategory.cs` but no `Domain/Enums/` directory exists. ALL existing enums are in `Domain/ValueObjects/` (AccountType, NormalBalance, PeriodType, PeriodStatus, FiscalYearStatus, ExchangeRateType). 

**Decision:** Place in `Domain/ValueObjects/VoucherCategory.cs` to match existing convention. The architecture test `Entities_Inheriting_BaseEntity_Should_Reside_In_Entities_Namespace` only constrains entity location, not enum location. Either location passes all 22 tests. But consistency with existing codebase matters.

#### 8.2 No Domain Event Raise on Deactivate()
The `Deactivate()` method does NOT raise a domain event. This matches `Account.Deprecate()` which raises `AccountDeprecated`, but is inconsistent with Department/CostCenter/Project which have no deactivation method at all. 

**Note:** The plan does not mention a `VoucherTypeDeactivated` event. If the Application layer (Task 6) needs to react to deactivation, a `VoucherTypeDeactivated` event should be added. For now, follow the plan literally — no event on `Deactivate()`.

#### 8.3 Id = 0 During Constructor
When the constructor calls `AddDomainEvent(new VoucherTypeCreated(Id, ...))`, `Id` is still 0 (default for `long`). This is the EXACT same behavior as Department/CostCenter/Project. The real ID is assigned by EF Core after `SaveChangesAsync`. Events carry the provisional 0 ID. This is a known pattern in the codebase — no fix needed.

#### 8.4 Code/Name Max Length
Domain layer: no max length enforcement (string, no constraints). EF Configuration: `HasMaxLength(20)` for Code, `HasMaxLength(200)` for Name. The domain relies on the DB schema for length enforcement. Application layer (Task 6) will add FluentValidation rules for max length.

#### 8.5 No FK Navigation Property
The entity has `CompanyId` as `long` but NO `Company` navigation property. This is intentional — matches Department/CostCenter/Project/AccountGroup/ExchangeRate/FiscalYear pattern. FK is configured in EF via `HasOne<Company>().WithMany()` (no navigation on either side).

#### 8.6 Architecture Test Compliance
- Entity inherits `BaseEntity` → must be in `SmeAccounting.Domain.Entities` ✓ (test: `Entities_Inheriting_BaseEntity_Should_Reside_In_Entities_Namespace`)
- Port interface `IVoucherTypeRepository` starts with `I` and ends with `Repository` ✓ (test: `Repository_Interfaces_Should_Start_With_I`)
- Domain has zero NuGet refs → no new packages needed ✓
- Infrastructure references Domain only → correct ✓
- No Api references to Domain.Entities or Domain.Ports → correct ✓

#### 8.7 Migration Naming
The migration will be created in Task 7, named `Phase2AccountingControlConfig`. VoucherType is the first entity in this phase. The migration should cover all 5 entities (Tasks 1-5).

#### 8.8 Code Style Compliance
- 4-space indent (C#)
- LF line endings
- Allman braces (new line before `{`)
- `var` preferred
- Private fields `_camelCase`
- File-scoped namespaces (`namespace X;`)
- `string.Empty` default for strings
- `= null!` not used on simple properties (only on owned types like AccountCode)
- `= true` default for IsActive
- Nullable `string?` for optional description
- Expression-bodied members for simple getters/methods (constructor body uses block)

---

## Task-Specific Research — Task 2: Document Numbering Series

**Goal:** Create DocumentNumberingSeries entity, IDocumentNumberingSeriesRepository port, EF configuration, repository, and DI registration.

**Depends on:** Task 1 (VoucherType entity already exists).

### File List (4 new files, 2 modified files)

| # | File Path | Layer | Status |
|---|-----------|-------|--------|
| 1 | `src/SmeAccounting.Domain/Entities/DocumentNumberingSeries.cs` | Domain | New |
| 2 | `src/SmeAccounting.Domain/Ports/IDocumentNumberingSeriesRepository.cs` | Domain | New |
| 3 | `src/SmeAccounting.Infrastructure/Persistence/Configurations/DocumentNumberingSeriesConfiguration.cs` | Infrastructure | New |
| 4 | `src/SmeAccounting.Infrastructure/Repositories/EfDocumentNumberingSeriesRepository.cs` | Infrastructure | New |
| 5 | `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` | Infrastructure | Modify |
| 6 | `src/SmeAccounting.Infrastructure/DependencyInjection.cs` | Infrastructure | Modify |

**Total: 4 new files, 2 modified files.**

---

### 1. DocumentNumberingSeries Entity

**File:** `src/SmeAccounting.Domain/Entities/DocumentNumberingSeries.cs`

**Copy from:** `src/SmeAccounting.Domain/Entities/VoucherType.cs` (just created in T1 — same structure with dual FKs).

**Properties (from PLAN.md):**

| Property | Type | Default | Notes |
|----------|------|---------|-------|
| Id | long | BaseEntity | |
| VoucherTypeId | long | — | FK to VoucherType |
| CompanyId | long | — | FK to Company |
| Prefix | string | — | Max 20, required |
| NextNumber | int | 1 | Must be >= 1 |
| PaddingLength | int | 6 | Must be 1–10 |
| IsDefault | bool | false | One default series per voucher type per company |
| IsActive | bool | true | Soft-delete |
| Description | string? | null | Max 500 |

**Invariants (throw `DomainException`):**
- `CompanyId > 0` — same as VoucherType
- `VoucherTypeId > 0` — FK must reference valid VoucherType
- `NextNumber >= 1` — cannot start below 1
- `PaddingLength >= 1 && PaddingLength <= 10` — reasonable padding bounds

**Methods:**
- `Increment()` — advances NextNumber by 1 (used in optimistic concurrency flow with xmin)
- `Reset(int startFrom)` — resets NextNumber to startFrom (must be >= 1)

**Domain events:** None — no DocumentNumberingSeriesCreated event in plan. Constructor validates invariants but does NOT raise an event. This is an intentional deviation from VoucherType/Department pattern. The plan does not specify a domain event for this entity.

**Gotcha — No domain event:** Unlike VoucherType/Department/CostCenter/Project, the plan does NOT specify a domain event for DocumentNumberingSeries. Constructor should still validate invariants but skip `AddDomainEvent(...)`. This means no event file to create and no `modelBuilder.Ignore<>()` needed in DbContext.

**Gotcha — Two FKs in constructor:** VoucherType only had one FK (CompanyId). DocumentNumberingSeries has two (CompanyId + VoucherTypeId). Both must be validated in constructor.

**Pattern:**

```csharp
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class DocumentNumberingSeries : BaseEntity
{
    public long VoucherTypeId { get; private set; }
    public long CompanyId { get; private set; }
    public string Prefix { get; private set; } = string.Empty;
    public int NextNumber { get; private set; } = 1;
    public int PaddingLength { get; private set; } = 6;
    public bool IsDefault { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private DocumentNumberingSeries() { }

    public DocumentNumberingSeries(
        long companyId, long voucherTypeId, string prefix,
        int paddingLength = 6, bool isDefault = false, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (voucherTypeId <= 0)
            throw new DomainException("VoucherTypeId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(prefix))
            throw new DomainException("Prefix is required.");
        if (paddingLength < 1 || paddingLength > 10)
            throw new DomainException("PaddingLength must be between 1 and 10.");

        CompanyId = companyId;
        VoucherTypeId = voucherTypeId;
        Prefix = prefix;
        PaddingLength = paddingLength;
        IsDefault = isDefault;
        Description = description;
    }

    public void Increment()
    {
        NextNumber++;
    }

    public void Reset(int startFrom)
    {
        if (startFrom < 1)
            throw new DomainException("StartFrom must be greater than zero.");
        NextNumber = startFrom;
    }
}
```

---

### 2. IDocumentNumberingSeriesRepository Port

**File:** `src/SmeAccounting.Domain/Ports/IDocumentNumberingSeriesRepository.cs`

**Methods (from PLAN.md):**

```csharp
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IDocumentNumberingSeriesRepository
{
    Task<DocumentNumberingSeries?> GetByIdAsync(long id);
    Task<DocumentNumberingSeries?> GetDefaultAsync(long voucherTypeId, long companyId);
    Task<IReadOnlyList<DocumentNumberingSeries>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(DocumentNumberingSeries series);
}
```

**Gotcha — `GetDefaultAsync` not `GetByCodeAsync`:** Unlike VoucherType/Department which have `GetByCodeAsync(code, companyId)`, this repo uses `GetDefaultAsync(voucherTypeId, companyId)` — looks up the default series for a given voucher type + company. No `GetByCode` because there is no `Code` property on this entity.

**Gotcha — `GetAllByCompanyAsync` not `GetAllAsync`:** Unlike VoucherType's `GetAllAsync()`, this repo scopes queries by CompanyId. Makes sense — you never want to list numbering series across all companies.

**Gotcha — No `UpdateAsync`:** Matches all repos except EfAccountRepository. Change tracking handles it. The `Increment()` and `Reset()` methods modify tracked entity state; calling `SaveChangesAsync` via UoW persists it.

---

### 3. DocumentNumberingSeries EF Configuration

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/DocumentNumberingSeriesConfiguration.cs`

**Copy from:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/VoucherTypeConfiguration.cs` (just created in T1).

**Unique index (from PLAN.md):** `(VoucherTypeId, CompanyId, Prefix)` — three-column composite unique index. This is different from Department/VoucherType which use two-column `(CompanyId, Code)`.

**FK pattern:** Two FKs — both Restrict:
1. `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — universal
2. `HasOne<VoucherType>().WithMany().HasForeignKey(e => e.VoucherTypeId).OnDelete(DeleteBehavior.Restrict)` — new FK to VoucherType

**Gotcha — No VoucherType navigation property:** Same pattern as Company FK — `HasOne<VoucherType>().WithMany()` with no navigation on either side. Entity has `VoucherTypeId` (long) but no `VoucherType` property.

**Pattern:**

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class DocumentNumberingSeriesConfiguration : IEntityTypeConfiguration<DocumentNumberingSeries>
{
    public void Configure(EntityTypeBuilder<DocumentNumberingSeries> builder)
    {
        builder.ToTable("document_numbering_series");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.VoucherTypeId)
            .HasColumnName("voucher_type_id");

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.Prefix)
            .HasColumnName("prefix")
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(e => e.NextNumber)
            .HasColumnName("next_number");

        builder.Property(e => e.PaddingLength)
            .HasColumnName("padding_length");

        builder.Property(e => e.IsDefault)
            .HasColumnName("is_default");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.VoucherTypeId, e.CompanyId, e.Prefix })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<VoucherType>()
            .WithMany()
            .HasForeignKey(e => e.VoucherTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
```

**Gotcha — `NextNumber`/`PaddingLength`/`IsDefault`/`IsActive` no HasMaxLength:** They're int/bool, not strings. Just `HasColumnName()` — no `.HasMaxLength()` or `.IsRequired()` needed.

**Gotcha — Table name:** `document_numbering_series` — already snake_case plural from PLAN. No casing issues.

---

### 4. EfDocumentNumberingSeriesRepository

**File:** `src/SmeAccounting.Infrastructure/Repositories/EfDocumentNumberingSeriesRepository.cs`

**Copy from:** `src/SmeAccounting.Infrastructure/Repositories/EfVoucherTypeRepository.cs`.

**Pattern:**

```csharp
using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfDocumentNumberingSeriesRepository : IDocumentNumberingSeriesRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfDocumentNumberingSeriesRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<DocumentNumberingSeries?> GetByIdAsync(long id)
    {
        return await _context.DocumentNumberingSeries
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<DocumentNumberingSeries?> GetDefaultAsync(long voucherTypeId, long companyId)
    {
        return await _context.DocumentNumberingSeries
            .FirstOrDefaultAsync(e => e.VoucherTypeId == voucherTypeId
                && e.CompanyId == companyId && e.IsDefault);
    }

    public async Task<IReadOnlyList<DocumentNumberingSeries>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.DocumentNumberingSeries
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.Prefix)
            .ToListAsync();
    }

    public async Task AddAsync(DocumentNumberingSeries series)
    {
        await _context.DocumentNumberingSeries.AddAsync(series);
    }
}
```

**Gotcha — DbSet name:** `DocumentNumberingSeries` (singular) — matches DbSet property name. Confirm DbSet is named `DocumentNumberingSeries` in DbContext (not `DocumentNumberingSerieses`).

**Gotcha — `GetAllByCompanyAsync` ordering:** Order by `Prefix` (the closest equivalent to Code on this entity). No Code property exists.

---

### 5. DbContext Modifications

**File:** `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`

**Current state (after T1):** 14 DbSets, 13 ignored events.

**Add DbSet (after line 23):**
```csharp
public DbSet<DocumentNumberingSeries> DocumentNumberingSeries => Set<DocumentNumberingSeries>();
```

**No event to ignore** — DocumentNumberingSeries does NOT raise a domain event. No `modelBuilder.Ignore<>()` needed.

**New count:** 15 DbSets, 13 ignored events (unchanged).

---

### 6. DI Registration

**File:** `src/SmeAccounting.Infrastructure/DependencyInjection.cs`

**Add (after line 36):**
```csharp
services.AddScoped<IDocumentNumberingSeriesRepository, EfDocumentNumberingSeriesRepository>();
```

**Pattern:** Same `AddScoped<IXxxRepository, EfXxxRepository>()` as all 9 existing registrations.

---

### Gotchas and Edge Cases

#### 1. No Domain Event
Unlike VoucherType/Department/CostCenter/Project, the plan does NOT specify a domain event for DocumentNumberingSeries. This means:
- No event file to create in `Domain/Events/`
- No `modelBuilder.Ignore<>()` in DbContext
- Constructor does NOT call `AddDomainEvent(...)`

This is intentional per the plan. If needed later, a `DocumentNumberingSeriesCreated` event can be added.

#### 2. Dual FK Pattern
This entity has two FKs (CompanyId + VoucherTypeId). Both use the universal `HasOne<X>().WithMany().HasForeignKey().OnDelete(Restrict)` pattern. No navigation properties on entity — FKs configured only in EF.

#### 3. Three-Column Unique Index
`HasIndex(e => new { e.VoucherTypeId, e.CompanyId, e.Prefix }).IsUnique()` — three columns, not two. This prevents duplicate prefixes per voucher type per company. Different from Department/VoucherType two-column `(CompanyId, Code)` pattern.

#### 4. No Code Property
Unlike VoucherType/Department/CostCenter/Project, DocumentNumberingSeries has NO `Code` property. The `Prefix` serves a similar role but is not a code. The repository uses `GetDefaultAsync` instead of `GetByCodeAsync`.

#### 5. NextNumber Auto-Increment Behavior
`Increment()` method advances NextNumber by 1. This is NOT an auto-increment DB column — it's a domain method. The Application layer (Task 6) will call `Increment()` within a transaction, relying on xmin optimistic concurrency to prevent race conditions.

#### 6. Architecture Test Compliance
- Entity inherits `BaseEntity` → must be in `SmeAccounting.Domain.Entities` ✓
- Port interface `IDocumentNumberingSeriesRepository` starts with `I` ✓
- Domain has zero NuGet refs → no new packages ✓
- Infrastructure references Domain only → correct ✓
- No Api references to Domain.Entities or Domain.Ports → correct ✓

#### 7. Migration Timing
Migration created in Task 7. DocumentNumberingSeries table will be `document_numbering_series` in the `Phase2AccountingControlConfig` migration alongside the other 4 new tables.

#### 8. DbSet Naming
DbSet property: `DocumentNumberingSeries` (singular). Table: `document_numbering_series` (snake_case plural). EF Core handles the mapping via `ToTable()`. The DbSet expression-bodied property pattern: `public DbSet<DocumentNumberingSeries> DocumentNumberingSeries => Set<DocumentNumberingSeries>();`

#### 9. Default PaddingLength
`PaddingLength` defaults to 6 in the constructor (matching PLAN.md). This means a prefix like "HD" with NextNumber=1 produces "HD000001". Domain has no formatting logic — that's Application layer responsibility (Task 6).

---

## Task-Specific Research — Task 3: Transaction Reason

**Goal:** Create TransactionReason entity, ITransactionReasonRepository port, EF configuration, repository, and DI registration.

**Depends on:** Task 1 (VoucherType entity already exists).

### File List (4 new files, 2 modified files)

| # | File Path | Layer | Status |
|---|-----------|-------|--------|
| 1 | `src/SmeAccounting.Domain/Entities/TransactionReason.cs` | Domain | New |
| 2 | `src/SmeAccounting.Domain/Events/TransactionReasonCreated.cs` | Domain | New |
| 3 | `src/SmeAccounting.Domain/Ports/ITransactionReasonRepository.cs` | Domain | New |
| 4 | `src/SmeAccounting.Infrastructure/Persistence/Configurations/TransactionReasonConfiguration.cs` | Infrastructure | New |
| 5 | `src/SmeAccounting.Infrastructure/Repositories/EfTransactionReasonRepository.cs` | Infrastructure | New |
| 6 | `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` | Infrastructure | Modify |
| 7 | `src/SmeAccounting.Infrastructure/DependencyInjection.cs` | Infrastructure | Modify |

**Total: 5 new files, 2 modified files.**

---

### 1. TransactionReason Entity

**File:** `src/SmeAccounting.Domain/Entities/TransactionReason.cs`

**Closest pattern to copy:** `src/SmeAccounting.Domain/Entities/VoucherType.cs` — same structure: CompanyId + Code + Name + IsActive + DomainException invariants + DomainCreated event + Description.

**Key difference from VoucherType:** This entity has a `VoucherTypeId` FK (like DocumentNumberingSeries has two FKs). But unlike DocumentNumberingSeries, it DOES raise a domain event (per PLAN.md pattern from T1).

**Properties (from PLAN.md):**

| Property | Type | Default | Notes |
|----------|------|---------|-------|
| Id | long | BaseEntity | |
| Code | string | — | Max 20, required |
| Name | string | — | Max 200, required |
| VoucherTypeId | long | — | FK to VoucherType |
| CompanyId | long | — | FK to Company |
| IsActive | bool | true | Soft-delete |
| Description | string? | null | Max 500 |

**Invariants (throw `DomainException`):**
- `CompanyId > 0`
- `VoucherTypeId > 0`
- Code not empty
- Name not empty

**Domain event:** `TransactionReasonCreated(EntityId, CompanyId, occurredOn)` — same pattern as VoucherTypeCreated, DepartmentCreated, etc.

**Pattern:**

```csharp
using SmeAccounting.Domain.Events;
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class TransactionReason : BaseEntity
{
    public string Code { get; private set; } = string.Empty;
    public string Name { get; private set; } = string.Empty;
    public long VoucherTypeId { get; private set; }
    public long CompanyId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private TransactionReason() { }

    public TransactionReason(long companyId, long voucherTypeId, string code, string name, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (voucherTypeId <= 0)
            throw new DomainException("VoucherTypeId must be greater than zero.");
        if (string.IsNullOrWhiteSpace(code))
            throw new DomainException("Code is required.");
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Name is required.");

        CompanyId = companyId;
        VoucherTypeId = voucherTypeId;
        Code = code;
        Name = name;
        Description = description;

        AddDomainEvent(new TransactionReasonCreated(Id, companyId, DateTimeOffset.UtcNow));
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
```

**Gotcha — Dual FK with event:** Unlike DocumentNumberingSeries (two FKs, no event), TransactionReason has two FKs AND raises a domain event. Constructor takes both FK IDs and validates both.

**Gotcha — Constructor parameter order:** `(companyId, voucherTypeId, code, name, description?)` —CompanyId first, then VoucherTypeId, then Code/Name. Matches VoucherType pattern of CompanyId-first.

---

### 2. TransactionReasonCreated Event

**File:** `src/SmeAccounting.Domain/Events/TransactionReasonCreated.cs`

**Copy from:** `src/SmeAccounting.Domain/Events/VoucherTypeCreated.cs` — identical structure.

```csharp
namespace SmeAccounting.Domain.Events;

public class TransactionReasonCreated : DomainEvent
{
    public long TransactionReasonId { get; }
    public long CompanyId { get; }

    public TransactionReasonCreated(
        long transactionReasonId,
        long companyId,
        DateTimeOffset occurredOn)
        : base(occurredOn)
    {
        TransactionReasonId = transactionReasonId;
        CompanyId = companyId;
    }
}
```

**Gotcha — Event property name:** `TransactionReasonId` (not `Id` or `ReasonId`). Matches VoucherTypeCreated's `VoucherTypeId`, DepartmentCreated's `DepartmentId`, etc.

---

### 3. ITransactionReasonRepository Port

**File:** `src/SmeAccounting.Domain/Ports/ITransactionReasonRepository.cs`

**Methods (from PLAN.md):**

```csharp
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface ITransactionReasonRepository
{
    Task<TransactionReason?> GetByIdAsync(long id);
    Task<TransactionReason?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TransactionReason>> GetAllByVoucherTypeAsync(long voucherTypeId);
    Task AddAsync(TransactionReason transactionReason);
}
```

**Gotcha — `GetAllByVoucherTypeAsync` not `GetAllAsync`:** Unlike VoucherType's `GetAllAsync()`, this repo scopes by VoucherTypeId. Rationale: transaction reasons are meaningful within a voucher type context; listing all reasons across all voucher types is less useful.

**Gotcha — `GetByCodeAsync(code, companyId)` not `(code, voucherTypeId)`:** Code uniqueness is scoped to company (not voucher type). This means the unique index in EF config is `(CompanyId, Code)` — same as Department/VoucherType. A code like "Thu tien ban hang" can exist under multiple voucher types within the same company.

---

### 4. TransactionReason EF Configuration

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/TransactionReasonConfiguration.cs`

**Copy from:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/VoucherTypeConfiguration.cs` — add VoucherType FK.

**Unique index (from PLAN.md):** `(CompanyId, Code)` — same as VoucherType/Department/CostCenter/Project. NOT `(VoucherTypeId, CompanyId, Code)`.

**FK pattern:** Two FKs — both Restrict:
1. `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — universal
2. `HasOne<VoucherType>().WithMany().HasForeignKey(e => e.VoucherTypeId).OnDelete(DeleteBehavior.Restrict)` — same as DocumentNumberingSeries

**Pattern:**

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class TransactionReasonConfiguration : IEntityTypeConfiguration<TransactionReason>
{
    public void Configure(EntityTypeBuilder<TransactionReason> builder)
    {
        builder.ToTable("transaction_reasons");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.VoucherTypeId)
            .HasColumnName("voucher_type_id");

        builder.Property(e => e.Code)
            .HasColumnName("code")
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.CompanyId, e.Code })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<VoucherType>()
            .WithMany()
            .HasForeignKey(e => e.VoucherTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
```

**Gotcha — Table name:** `transaction_reasons` (snake_case plural). Verify: `ToTable("transaction_reasons")`.

**Gotcha — Property order:** CompanyId, VoucherTypeId, Code, Name, IsActive, Description — matches entity property declaration order. EF doesn't care about order, but consistency helps readability.

---

### 5. EfTransactionReasonRepository

**File:** `src/SmeAccounting.Infrastructure/Repositories/EfTransactionReasonRepository.cs`

**Copy from:** `src/SmeAccounting.Infrastructure/Repositories/EfVoucherTypeRepository.cs` — change GetAllAsync to GetAllByVoucherTypeAsync.

**Pattern:**

```csharp
using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfTransactionReasonRepository : ITransactionReasonRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfTransactionReasonRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<TransactionReason?> GetByIdAsync(long id)
    {
        return await _context.TransactionReasons
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<TransactionReason?> GetByCodeAsync(string code, long companyId)
    {
        return await _context.TransactionReasons
            .FirstOrDefaultAsync(e => e.Code == code && e.CompanyId == companyId);
    }

    public async Task<IReadOnlyList<TransactionReason>> GetAllByVoucherTypeAsync(long voucherTypeId)
    {
        return await _context.TransactionReasons
            .AsNoTracking()
            .Where(e => e.VoucherTypeId == voucherTypeId)
            .OrderBy(e => e.Code)
            .ToListAsync();
    }

    public async Task AddAsync(TransactionReason transactionReason)
    {
        await _context.TransactionReasons.AddAsync(transactionReason);
    }
}
```

**Gotcha — DbSet name:** `TransactionReasons` (plural) — matches DbSet property name pattern (`Departments`, `CostCenters`, `Projects`, `VoucherTypes`).

**Gotcha — `GetAllByVoucherTypeAsync` filtering:** Uses `.Where(e => e.VoucherTypeId == voucherTypeId)` before `.ToListAsync()`. Orders by Code (matching VoucherType/Department pattern).

---

### 6. DbContext Modifications

**File:** `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`

**Current state (after T2):** 15 DbSets, 13 ignored events.

**Add DbSet (after line 24):**
```csharp
public DbSet<TransactionReason> TransactionReasons => Set<TransactionReason>();
```

**Add Ignore for new event (after line 43):**
```csharp
modelBuilder.Ignore<TransactionReasonCreated>();
```

**New count:** 16 DbSets, 14 ignored events.

---

### 7. DI Registration

**File:** `src/SmeAccounting.Infrastructure/DependencyInjection.cs`

**Add (after line 37):**
```csharp
services.AddScoped<ITransactionReasonRepository, EfTransactionReasonRepository>();
```

**Pattern:** Same `AddScoped<IXxxRepository, EfXxxRepository>()` as all 10 existing registrations.

---

### Gotchas and Edge Cases

#### 1. Domain Event Present (Unlike DocumentNumberingSeries)
TransactionReason DOES raise a domain event (`TransactionReasonCreated`). This means:
- Create event file in `Domain/Events/TransactionReasonCreated.cs`
- Add `modelBuilder.Ignore<TransactionReasonCreated>()` in DbContext
- Constructor calls `AddDomainEvent(new TransactionReasonCreated(...))`

This is the same pattern as VoucherType, Department, CostCenter, Project. DocumentNumberingSeries was the exception (no event).

#### 2. Dual FK + Event Combination
TransactionReason has two FKs (CompanyId + VoucherTypeId) AND raises a domain event. This is a combination not seen in existing entities:
- VoucherType: one FK + event
- DocumentNumberingSeries: two FKs, no event
- Department/CostCenter/Project: one FK + event

The pattern is straightforward: validate both FK IDs in constructor, raise event with CompanyId (not VoucherTypeId). Event carries entity ID + CompanyId only (event minimalism pattern).

#### 3. Code Uniqueness Scope
Unique index is `(CompanyId, Code)` — NOT `(VoucherTypeId, CompanyId, Code)`. This means:
- Same code CAN exist under different voucher types within the same company
- Same code CANNOT exist twice under the same company regardless of voucher type
- Application layer (Task 6) must check for duplicates before insert

#### 4. GetAllByVoucherTypeAsync vs GetAllAsync
The repo method `GetAllByVoucherTypeAsync(long voucherTypeId)` replaces the generic `GetAllAsync()`. This is intentional — transaction reasons are queried in context of a voucher type. The Application layer (Task 6) query `GetTransactionReasonsByVoucherTypeQuery` will call this method.

#### 5. No VoucherType Navigation Property
Same pattern as all other FK relationships: entity has `VoucherTypeId` (long) but no `VoucherType` navigation property. FK configured in EF via `HasOne<VoucherType>().WithMany()` (no navigation on either side).

#### 6. Architecture Test Compliance
- Entity inherits `BaseEntity` → must be in `SmeAccounting.Domain.Entities` ✓
- Port interface `ITransactionReasonRepository` starts with `I` ✓
- Domain has zero NuGet refs → no new packages ✓
- Infrastructure references Domain only → correct ✓
- No Api references to Domain.Entities or Domain.Ports → correct ✓

#### 7. Migration Timing
Migration created in Task 7. TransactionReasons table will be `transaction_reasons` in the `Phase2AccountingControlConfig` migration alongside the other 4 new tables.

#### 8. DbSet Naming
DbSet property: `TransactionReasons` (plural). Table: `transaction_reasons` (snake_case plural). The DbSet expression-bodied property pattern: `public DbSet<TransactionReason> TransactionReasons => Set<TransactionReason>();`

#### 9. Event Minimalism
`TransactionReasonCreated` carries `TransactionReasonId` + `CompanyId` + `occurredOn`. Does NOT carry `VoucherTypeId`. This matches the event minimalism pattern: entity ID + company ID only. The Application layer can look up VoucherTypeId from the entity if needed.

---

## Task-Specific Research — Task 4: Posting Configuration

**Goal:** Create PostingConfiguration entity, IPostingConfigurationRepository port, EF configuration, repository, and DI registration.

**Depends on:** Task 1 (VoucherType), existing Account entity, Task 3 (TransactionReason — nullable FK).

### File List (4 new files, 2 modified files)

| # | File Path | Layer | Status |
|---|-----------|-------|--------|
| 1 | `src/SmeAccounting.Domain/Entities/PostingConfiguration.cs` | Domain | New |
| 2 | `src/SmeAccounting.Domain/Ports/IPostingConfigurationRepository.cs` | Domain | New |
| 3 | `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingConfigurationConfiguration.cs` | Infrastructure | New |
| 4 | `src/SmeAccounting.Infrastructure/Repositories/EfPostingConfigurationRepository.cs` | Infrastructure | New |
| 5 | `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` | Infrastructure | Modify |
| 6 | `src/SmeAccounting.Infrastructure/DependencyInjection.cs` | Infrastructure | Modify |

**Total: 4 new files, 2 modified files.**

**No domain event** — plan does not specify a PostingConfigurationCreated event. Same pattern as DocumentNumberingSeries (T2).

---

### 1. PostingConfiguration Entity

**File:** `src/SmeAccounting.Domain/Entities/PostingConfiguration.cs`

**Closest pattern:** `src/SmeAccounting.Domain/Entities/DocumentNumberingSeries.cs` — multiple FKs, no domain event, soft-delete via Deactivate().

**Properties (from PLAN.md):**

| Property | Type | Default | Notes |
|----------|------|---------|-------|
| Id | long | BaseEntity | |
| VoucherTypeId | long | — | FK to VoucherType |
| DebitAccountId | long | — | FK to Account |
| CreditAccountId | long | — | FK to Account |
| CompanyId | long | — | FK to Company |
| TransactionReasonId | long? | null | FK to TransactionReason, nullable for default posting rules |
| DisplayOrder | int | 0 | Ordering within voucher type |
| IsActive | bool | true | Soft-delete |
| Description | string? | null | Max 500 |

**Invariants (throw `DomainException`):**
- `CompanyId > 0`
- `VoucherTypeId > 0`
- `DebitAccountId > 0`
- `CreditAccountId > 0`
- `DebitAccountId != CreditAccountId` — core accounting invariant: debit and credit must be different accounts

**Key gotcha — "Both accounts must belong to same company":** This is an APPLICATION-LEVEL invariant, NOT a domain constructor invariant. The entity does not have access to Account entities or their CompanyId values. The constructor only checks `DebitAccountId != CreditAccountId`. The Application layer (Task 6) must validate that both accounts belong to the same company before calling the constructor. This matches the existing pattern where `ExchangeRate` validates `FromCurrencyCode != ToCurrencyCode` in the constructor but cannot validate the currencies exist.

**Key gotcha — TransactionReasonId is nullable:** Unlike all other FKs on this entity, `TransactionReasonId` is `long?`. A null value means "this is the default posting rule for this voucher type, not tied to a specific transaction reason." The constructor should NOT validate `TransactionReasonId > 0` because null is valid. Only validate non-null values: `if (transactionReasonId.HasValue && transactionReasonId <= 0) throw ...`.

**Key gotcha — No domain event:** Same pattern as DocumentNumberingSeries (T2). No event file, no `modelBuilder.Ignore<>()` in DbContext, no `AddDomainEvent()` in constructor.

**Key gotcha — Four/Five FKs:** This entity has the most FKs of any in the codebase:
1. CompanyId → Company (Restrict)
2. VoucherTypeId → VoucherType (Restrict)
3. DebitAccountId → Account (Restrict)
4. CreditAccountId → Account (Restrict)
5. TransactionReasonId → TransactionReason (nullable, Restrict)

**Key gotcha — Two Account FKs:** `DebitAccountId` and `CreditAccountId` both reference the Account entity. EF Core needs two separate `HasOne<Account>()` configurations with different foreign key properties. Use explicit FK configuration to avoid ambiguity:
```csharp
builder.HasOne<Account>()
    .WithMany()
    .HasForeignKey(e => e.DebitAccountId)
    .OnDelete(DeleteBehavior.Restrict);

builder.HasOne<Account>()
    .WithMany()
    .HasForeignKey(e => e.CreditAccountId)
    .OnDelete(DeleteBehavior.Restrict);
```

**Key gotcha — TransactionReason FK nullable delete behavior:** Since `TransactionReasonId` is nullable, the FK could use `DeleteBehavior.SetNull` or `DeleteBehavior.Restrict`. PLAN.md says "Company/Account/VoucherType FKs Restrict" — does not specify TransactionReason behavior. **Recommendation:** Use `Restrict` for consistency with all other FKs. If a TransactionReason is deleted, the PostingConfiguration referencing it should be deactivated first (soft-delete), not cascade-null. This matches the accounting domain where referential integrity matters.

**Pattern:**

```csharp
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class PostingConfiguration : BaseEntity
{
    public long VoucherTypeId { get; private set; }
    public long DebitAccountId { get; private set; }
    public long CreditAccountId { get; private set; }
    public long CompanyId { get; private set; }
    public long? TransactionReasonId { get; private set; }
    public int DisplayOrder { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private PostingConfiguration() { }

    public PostingConfiguration(
        long companyId, long voucherTypeId, long debitAccountId, long creditAccountId,
        long? transactionReasonId = null, int displayOrder = 0, string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (voucherTypeId <= 0)
            throw new DomainException("VoucherTypeId must be greater than zero.");
        if (debitAccountId <= 0)
            throw new DomainException("DebitAccountId must be greater than zero.");
        if (creditAccountId <= 0)
            throw new DomainException("CreditAccountId must be greater than zero.");
        if (debitAccountId == creditAccountId)
            throw new DomainException("DebitAccountId and CreditAccountId must be different.");
        if (transactionReasonId.HasValue && transactionReasonId <= 0)
            throw new DomainException("TransactionReasonId must be greater than zero when specified.");

        CompanyId = companyId;
        VoucherTypeId = voucherTypeId;
        DebitAccountId = debitAccountId;
        CreditAccountId = creditAccountId;
        TransactionReasonId = transactionReasonId;
        DisplayOrder = displayOrder;
        Description = description;
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
```

**Gotcha — Constructor parameter order:** `(companyId, voucherTypeId, debitAccountId, creditAccountId, transactionReasonId?, displayOrder, description?)` — CompanyId first (matching all other entities), then VoucherTypeId, then the two account FKs, then optional TransactionReasonId, then optional display/description params.

**Gotcha — No Id in constructor:** Id is 0 at constructor time. Real ID assigned by EF Core after SaveChanges. No domain event carries the provisional 0 (because there is no event).

---

### 2. IPostingConfigurationRepository Port

**File:** `src/SmeAccounting.Domain/Ports/IPostingConfigurationRepository.cs`

**Methods (from PLAN.md):**

```csharp
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IPostingConfigurationRepository
{
    Task<PostingConfiguration?> GetByIdAsync(long id);
    Task<IReadOnlyList<PostingConfiguration>> GetAllByVoucherTypeAsync(long voucherTypeId, long companyId);
    Task<IReadOnlyList<PostingConfiguration>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(PostingConfiguration postingConfiguration);
}
```

**Gotcha — `GetAllByVoucherTypeAsync` takes two params:** Unlike TransactionReason's `GetAllByVoucherTypeAsync(voucherTypeId)` which is company-scoped via the entity's unique index, PostingConfiguration needs `(voucherTypeId, companyId)` because posting configurations are per-company AND per-voucher-type. The query filters on both.

**Gotcha — No `GetByCodeAsync`:** PostingConfiguration has no `Code` property. No code-based lookup needed.

**Gotcha — No `UpdateAsync`:** Matches all repos except EfAccountRepository. Change tracking handles it.

---

### 3. PostingConfiguration EF Configuration

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingConfigurationConfiguration.cs`

**Copy from:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/TransactionReasonConfiguration.cs` — add Account FKs and nullable TransactionReason FK.

**Index (from PLAN.md):** `(VoucherTypeId, TransactionReasonId)` — composite index. This is a NON-UNIQUE index for query performance (find all posting configs for a voucher type + reason combination). Multiple posting configurations can share the same voucher type + reason (e.g., different debit/credit account pairs).

**Gotcha — No unique business key:** Unlike Department/VoucherType/TransactionReason which have `(CompanyId, Code)` unique indexes, PostingConfiguration has NO unique business key. The entity is identified by its auto-generated ID. The composite index on `(VoucherTypeId, TransactionReasonId)` is for query performance only.

**Gotcha — Five FK configurations including one nullable:**
1. Company FK: `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — universal
2. VoucherType FK: `HasOne<VoucherType>().WithMany().HasForeignKey(e => e.VoucherTypeId).OnDelete(DeleteBehavior.Restrict)` — same as T2/T3
3. DebitAccount FK: `HasOne<Account>().WithMany().HasForeignKey(e => e.DebitAccountId).OnDelete(DeleteBehavior.Restrict)` — first Account FK
4. CreditAccount FK: `HasOne<Account>().WithMany().HasForeignKey(e => e.CreditAccountId).OnDelete(DeleteBehavior.Restrict)` — second Account FK
5. TransactionReason FK (nullable): `HasOne<TransactionReason>().WithMany().HasForeignKey(e => e.TransactionReasonId).OnDelete(DeleteBehavior.Restrict)` — nullable FK, Restrict delete

**Pattern:**

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class PostingConfigurationConfiguration : IEntityTypeConfiguration<PostingConfiguration>
{
    public void Configure(EntityTypeBuilder<PostingConfiguration> builder)
    {
        builder.ToTable("posting_configurations");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.VoucherTypeId)
            .HasColumnName("voucher_type_id");

        builder.Property(e => e.DebitAccountId)
            .HasColumnName("debit_account_id");

        builder.Property(e => e.CreditAccountId)
            .HasColumnName("credit_account_id");

        builder.Property(e => e.TransactionReasonId)
            .HasColumnName("transaction_reason_id");

        builder.Property(e => e.DisplayOrder)
            .HasColumnName("display_order");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.VoucherTypeId, e.TransactionReasonId });

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<VoucherType>()
            .WithMany()
            .HasForeignKey(e => e.VoucherTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Account>()
            .WithMany()
            .HasForeignKey(e => e.DebitAccountId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Account>()
            .WithMany()
            .HasForeignKey(e => e.CreditAccountId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<TransactionReason>()
            .WithMany()
            .HasForeignKey(e => e.TransactionReasonId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
```

**Gotcha — Table name:** `posting_configurations` (snake_case plural). Verify: `ToTable("posting_configurations")`.

**Gotcha — Composite index NOT unique:** `HasIndex(e => new { e.VoucherTypeId, e.TransactionReasonId })` — no `.IsUnique()`. This is different from Department/VoucherType/TransactionReason which all have `.IsUnique()` on their composite indexes.

**Gotcha — Two Account FKs need explicit naming:** EF Core can infer the principal entity type from the property type, but when there are two FKs to the same principal entity, you MUST use `.HasForeignKey(e => e.DebitAccountId)` and `.HasForeignKey(e => e.CreditAccountId)` explicitly. Without explicit FK, EF Core throws ambiguous relationship error.

**Gotcha — Nullable FK column:** `TransactionReasonId` is `long?` so the column `transaction_reason_id` will be nullable in the database. EF Core handles this automatically from the C# nullable type.

---

### 4. EfPostingConfigurationRepository

**File:** `src/SmeAccounting.Infrastructure/Repositories/EfPostingConfigurationRepository.cs`

**Copy from:** `src/SmeAccounting.Infrastructure/Repositories/EfTransactionReasonRepository.cs` — adjust for dual-scoped GetAll methods.

**Pattern:**

```csharp
using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfPostingConfigurationRepository : IPostingConfigurationRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfPostingConfigurationRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<PostingConfiguration?> GetByIdAsync(long id)
    {
        return await _context.PostingConfigurations
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<PostingConfiguration>> GetAllByVoucherTypeAsync(
        long voucherTypeId, long companyId)
    {
        return await _context.PostingConfigurations
            .AsNoTracking()
            .Where(e => e.VoucherTypeId == voucherTypeId && e.CompanyId == companyId)
            .OrderBy(e => e.DisplayOrder)
            .ToListAsync();
    }

    public async Task<IReadOnlyList<PostingConfiguration>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.PostingConfigurations
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.DisplayOrder)
            .ToListAsync();
    }

    public async Task AddAsync(PostingConfiguration postingConfiguration)
    {
        await _context.PostingConfigurations.AddAsync(postingConfiguration);
    }
}
```

**Gotcha — DbSet name:** `PostingConfigurations` (plural) — matches DbSet property name pattern.

**Gotcha — OrderBy `DisplayOrder`:** Both GetAll methods order by `DisplayOrder` (the entity's natural ordering property). Different from VoucherType/Department which order by Code. PostingConfiguration has no Code — DisplayOrder is the logical sort key.

**Gotcha — `GetAllByVoucherTypeAsync` filters on two columns:** Both `VoucherTypeId` AND `CompanyId` are filtered. This ensures posting configs are scoped to a specific company even when querying by voucher type.

---

### 5. DbContext Modifications

**File:** `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`

**Current state (after T3):** 16 DbSets, 14 ignored events.

**Add DbSet (after line 25):**
```csharp
public DbSet<PostingConfiguration> PostingConfigurations => Set<PostingConfiguration>();
```

**No event to ignore** — PostingConfiguration does NOT raise a domain event. No `modelBuilder.Ignore<>()` needed.

**New count:** 17 DbSets, 14 ignored events (unchanged).

---

### 6. DI Registration

**File:** `src/SmeAccounting.Infrastructure/DependencyInjection.cs`

**Add (after line 38):**
```csharp
services.AddScoped<IPostingConfigurationRepository, EfPostingConfigurationRepository>();
```

**Pattern:** Same `AddScoped<IXxxRepository, EfXxxRepository>()` as all 11 existing registrations.

---

### Gotchas and Edge Cases

#### 1. No Domain Event
Same pattern as DocumentNumberingSeries (T2). No event file, no `modelBuilder.Ignore<>()` in DbContext, no `AddDomainEvent()` in constructor. This is the second entity (after DocumentNumberingSeries) without a domain event.

#### 2. Five FKs — Most in Codebase
PostingConfiguration has the most FK relationships of any entity:
- Company (required, Restrict)
- VoucherType (required, Restrict)
- Account as DebitAccount (required, Restrict)
- Account as CreditAccount (required, Restrict)
- TransactionReason (nullable, Restrict)

All use the universal `HasOne<X>().WithMany().HasForeignKey().OnDelete(Restrict)` pattern. No navigation properties on entity.

#### 3. Two Account FKs — Explicit Configuration Required
Both `DebitAccountId` and `CreditAccountId` reference the Account entity. EF Core requires explicit FK configuration for each:
```csharp
builder.HasOne<Account>().WithMany().HasForeignKey(e => e.DebitAccountId)...
builder.HasOne<Account>().WithMany().HasForeignKey(e => e.CreditAccountId)...
```
Without explicit FK names, EF Core throws: "The navigation 'Account' cannot be determined for the type 'PostingConfiguration'..."

#### 4. DebitAccountId != CreditAccountId — Domain Invariant
The constructor enforces this invariant with `DomainException`. This is a CORE accounting rule: you cannot debit and credit the same account in a single posting line. The Application layer (Task 6) validator will mirror this check with FluentValidation, but the domain invariant is the source of truth.

#### 5. "Both Accounts Belong to Same Company" — Application-Level Only
The plan says "both accounts must belong to same company" as an invariant. However, the entity constructor CANNOT enforce this — it only has account IDs (longs), not Account entities. The domain invariant is limited to `DebitAccountId != CreditAccountId`. The Application layer (Task 6) must:
1. Load both Account entities via IAccountRepository
2. Verify both have the same CompanyId
3. Verify both belong to the requesting company
4. THEN create the PostingConfiguration

This matches the existing pattern where `ExchangeRate` validates `FromCurrencyCode != ToCurrencyCode` in the constructor but cannot validate the currencies exist (that's Application layer responsibility).

#### 6. Nullable TransactionReasonId
`TransactionReasonId` is `long?` — null means "default posting rule for this voucher type." The constructor validates:
- If null: valid (no additional check needed)
- If has value: must be > 0

The EF configuration uses nullable FK column. Delete behavior is Restrict (not SetNull) — if a TransactionReason is referenced, it must be deactivated first, not cascade-deleted.

#### 7. No Unique Business Key
Unlike Department/VoucherType/TransactionReason which have `(CompanyId, Code)` unique indexes, PostingConfiguration has NO unique business key. The composite index on `(VoucherTypeId, TransactionReasonId)` is non-unique (query optimization only). Multiple posting configurations can exist for the same voucher type + reason combination with different account pairs.

#### 8. DisplayOrder for Sorting
`DisplayOrder` (int, default 0) controls the ordering of posting configurations within a voucher type. Repository sorts by `DisplayOrder` in both GetAll methods. This is the entity's natural sort key (replacing Code which doesn't exist on this entity).

#### 9. Architecture Test Compliance
- Entity inherits `BaseEntity` → must be in `SmeAccounting.Domain.Entities` ✓
- Port interface `IPostingConfigurationRepository` starts with `I` ✓
- Domain has zero NuGet refs → no new packages ✓
- Infrastructure references Domain only → correct ✓
- No Api references to Domain.Entities or Domain.Ports → correct ✓

#### 10. Migration Timing
Migration created in Task 7. PostingConfigurations table will be `posting_configurations` in the `Phase2AccountingControlConfig` migration alongside the other 4 new tables.

#### 11. DbSet Naming
DbSet property: `PostingConfigurations` (plural). Table: `posting_configurations` (snake_case plural). The DbSet expression-bodied property pattern: `public DbSet<PostingConfiguration> PostingConfigurations => Set<PostingConfiguration>();`

#### 12. Account Entity Reference Points
Key Account properties relevant to PostingConfiguration:
- `Account.Id` (long) — referenced by DebitAccountId/CreditAccountId
- `Account.CompanyId` (long) — used by Application layer to validate same-company constraint
- `Account.IsActive` (bool) — Application layer should validate both accounts are active before creating posting config
- `Account.NormalBalance` (NormalBalance enum: Debit/Credit) — Application layer could use this to validate posting rule consistency (optional, not enforced in domain)

---

## Task-Specific Research — Task 5: Opening Balance Mapping

**Goal:** Create OpeningBalanceMapping entity, IOpeningBalanceMappingRepository port, EF configuration, repository, and DI registration.

**Depends on:** Task 1 (VoucherType), existing Account entity, existing FiscalPeriod entity.

### File List (4 new files, 2 modified files)

| # | File Path | Layer | Status |
|---|-----------|-------|--------|
| 1 | `src/SmeAccounting.Domain/Entities/OpeningBalanceMapping.cs` | Domain | New |
| 2 | `src/SmeAccounting.Domain/Ports/IOpeningBalanceMappingRepository.cs` | Domain | New |
| 3 | `src/SmeAccounting.Infrastructure/Persistence/Configurations/OpeningBalanceMappingConfiguration.cs` | Infrastructure | New |
| 4 | `src/SmeAccounting.Infrastructure/Repositories/EfOpeningBalanceMappingRepository.cs` | Infrastructure | New |
| 5 | `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs` | Infrastructure | Modify |
| 6 | `src/SmeAccounting.Infrastructure/DependencyInjection.cs` | Infrastructure | Modify |

**Total: 4 new files, 2 modified files.**

**No domain event** — plan does not specify an OpeningBalanceMappingCreated event. Same pattern as DocumentNumberingSeries (T2) and PostingConfiguration (T4).

---

### 1. OpeningBalanceMapping Entity

**File:** `src/SmeAccounting.Domain/Entities/OpeningBalanceMapping.cs`

**Closest pattern:** `src/SmeAccounting.Domain/Entities/PostingConfiguration.cs` — dual Account FK pattern (DebitAccountId + CreditAccountId), same invariant (debit != credit), no domain event, soft-delete via Deactivate().

**Key differences from PostingConfiguration:**
- NO `DisplayOrder` property (PostingConfiguration has it)
- NO `TransactionReasonId` property (PostingConfiguration has nullable FK)
- SIMPLER: only 4 FKs (Company, VoucherType, DebitAccount, CreditAccount) vs PostingConfiguration's 5
- UNIQUE index on `(CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId)` (PostingConfiguration has non-unique `(VoucherTypeId, TransactionReasonId)`)

**Properties (from PLAN.md):**

| Property | Type | Default | Notes |
|----------|------|---------|-------|
| Id | long | BaseEntity | |
| CompanyId | long | — | FK to Company |
| VoucherTypeId | long | — | FK to VoucherType (opening balance voucher type) |
| DebitAccountId | long | — | FK to Account |
| CreditAccountId | long | — | FK to Account |
| IsActive | bool | true | Soft-delete |
| Description | string? | null | Max 500 |

**Invariants (throw `DomainException`):**
- `CompanyId > 0`
- `VoucherTypeId > 0`
- `DebitAccountId > 0`
- `CreditAccountId > 0`
- `DebitAccountId != CreditAccountId` — core accounting invariant (same as PostingConfiguration)

**Pattern:**

```csharp
using SmeAccounting.Domain.Exceptions;

namespace SmeAccounting.Domain.Entities;

public class OpeningBalanceMapping : BaseEntity
{
    public long CompanyId { get; private set; }
    public long VoucherTypeId { get; private set; }
    public long DebitAccountId { get; private set; }
    public long CreditAccountId { get; private set; }
    public bool IsActive { get; private set; } = true;
    public string? Description { get; private set; }

    private OpeningBalanceMapping() { }

    public OpeningBalanceMapping(
        long companyId, long voucherTypeId, long debitAccountId, long creditAccountId,
        string? description = null)
    {
        if (companyId <= 0)
            throw new DomainException("CompanyId must be greater than zero.");
        if (voucherTypeId <= 0)
            throw new DomainException("VoucherTypeId must be greater than zero.");
        if (debitAccountId <= 0)
            throw new DomainException("DebitAccountId must be greater than zero.");
        if (creditAccountId <= 0)
            throw new DomainException("CreditAccountId must be greater than zero.");
        if (debitAccountId == creditAccountId)
            throw new DomainException("Debit and credit accounts must be different.");

        CompanyId = companyId;
        VoucherTypeId = voucherTypeId;
        DebitAccountId = debitAccountId;
        CreditAccountId = creditAccountId;
        Description = description;
    }

    public void Deactivate()
    {
        IsActive = false;
    }
}
```

**Gotcha — Constructor parameter order:** `(companyId, voucherTypeId, debitAccountId, creditAccountId, description?)` — CompanyId first (matching all other entities), then VoucherTypeId, then the two account FKs, then optional description. Simpler than PostingConfiguration (no transactionReasonId, no displayOrder).

**Gotcha — No domain event:** Same as PostingConfiguration (T4) and DocumentNumberingSeries (T2). No event file, no `modelBuilder.Ignore<>()` in DbContext, no `AddDomainEvent()` in constructor.

**Gotcha — Two Account FKs:** Same dual-Account FK pattern as PostingConfiguration. Entity only has account IDs (longs), cannot validate account ownership. Application layer (Task 6) must load accounts and verify CompanyId match.

---

### 2. IOpeningBalanceMappingRepository Port

**File:** `src/SmeAccounting.Domain/Ports/IOpeningBalanceMappingRepository.cs`

**Methods (from PLAN.md):**

```csharp
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Domain.Ports;

public interface IOpeningBalanceMappingRepository
{
    Task<OpeningBalanceMapping?> GetByIdAsync(long id);
    Task<IReadOnlyList<OpeningBalanceMapping>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(OpeningBalanceMapping mapping);
}
```

**Gotcha — Only 3 methods:** Fewer than PostingConfiguration (which has 4 methods including `GetAllByVoucherTypeAsync`). OpeningBalanceMapping only needs company-scoped listing, not voucher-type-scoped. This is simpler — one mapping per voucher type per company is expected.

**Gotcha — No `GetByCodeAsync`:** OpeningBalanceMapping has no `Code` property. No code-based lookup needed.

**Gotcha — No `GetAllByVoucherTypeAsync`:** Unlike PostingConfiguration, the plan does not specify a voucher-type-scoped query. The Application layer can filter the company list by VoucherTypeId if needed.

---

### 3. OpeningBalanceMapping EF Configuration

**File:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/OpeningBalanceMappingConfiguration.cs`

**Copy from:** `src/SmeAccounting.Infrastructure/Persistence/Configurations/PostingConfigurationConfiguration.cs` — remove TransactionReason FK and DisplayOrder, simplify index to unique.

**Unique index (from PLAN.md):** `(CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId)` — four-column composite unique index. This prevents duplicate opening balance mappings for the same company + voucher type + account pair combination. Different from PostingConfiguration's non-unique `(VoucherTypeId, TransactionReasonId)`.

**FK pattern:** Four FKs — all Restrict:
1. `HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict)` — universal
2. `HasOne<VoucherType>().WithMany().HasForeignKey(e => e.VoucherTypeId).OnDelete(DeleteBehavior.Restrict)` — same as T2/T3/T4
3. `HasOne<Account>().WithMany().HasForeignKey(e => e.DebitAccountId).OnDelete(DeleteBehavior.Restrict)` — first Account FK
4. `HasOne<Account>().WithMany().HasForeignKey(e => e.CreditAccountId).OnDelete(DeleteBehavior.Restrict)` — second Account FK

**Pattern:**

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class OpeningBalanceMappingConfiguration : IEntityTypeConfiguration<OpeningBalanceMapping>
{
    public void Configure(EntityTypeBuilder<OpeningBalanceMapping> builder)
    {
        builder.ToTable("opening_balance_mappings");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.VoucherTypeId)
            .HasColumnName("voucher_type_id");

        builder.Property(e => e.DebitAccountId)
            .HasColumnName("debit_account_id");

        builder.Property(e => e.CreditAccountId)
            .HasColumnName("credit_account_id");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.CompanyId, e.VoucherTypeId, e.DebitAccountId, e.CreditAccountId })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<VoucherType>()
            .WithMany()
            .HasForeignKey(e => e.VoucherTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Account>()
            .WithMany()
            .HasForeignKey(e => e.DebitAccountId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Account>()
            .WithMany()
            .HasForeignKey(e => e.CreditAccountId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
```

**Gotcha — Table name:** `opening_balance_mappings` (snake_case plural). Verify: `ToTable("opening_balance_mappings")`.

**Gotcha — Four-column unique index:** `HasIndex(e => new { e.CompanyId, e.VoucherTypeId, e.DebitAccountId, e.CreditAccountId }).IsUnique()` — four columns. This is the widest unique index in the codebase (PostingConfiguration's is 2 columns, DocumentNumberingSeries is 3). The order matters for index efficiency: CompanyId first (most selective per query), then VoucherTypeId, then the two account FKs.

**Gotcha — Two Account FKs need explicit naming:** Same as PostingConfiguration. EF Core requires explicit FK configuration for each Account reference:
```csharp
builder.HasOne<Account>().WithMany().HasForeignKey(e => e.DebitAccountId)...
builder.HasOne<Account>().WithMany().HasForeignKey(e => e.CreditAccountId)...
```

**Gotcha — No TransactionReason FK:** Unlike PostingConfiguration, OpeningBalanceMapping has no TransactionReason FK. This simplifies the configuration — only 4 FKs instead of 5.

**Gotcha — No DisplayOrder:** Unlike PostingConfiguration, OpeningBalanceMapping has no DisplayOrder property. The repository will not have an OrderBy clause (or can order by VoucherTypeId, DebitAccountId).

---

### 4. EfOpeningBalanceMappingRepository

**File:** `src/SmeAccounting.Infrastructure/Repositories/EfOpeningBalanceMappingRepository.cs`

**Copy from:** `src/SmeAccounting.Infrastructure/Repositories/EfPostingConfigurationRepository.cs` — simplify to only 3 methods, remove DisplayOrder ordering.

**Pattern:**

```csharp
using Microsoft.EntityFrameworkCore;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;
using SmeAccounting.Infrastructure.Persistence;

namespace SmeAccounting.Infrastructure.Repositories;

public class EfOpeningBalanceMappingRepository : IOpeningBalanceMappingRepository
{
    private readonly SmeAccountingDbContext _context;

    public EfOpeningBalanceMappingRepository(SmeAccountingDbContext context) => _context = context;

    public async Task<OpeningBalanceMapping?> GetByIdAsync(long id)
    {
        return await _context.OpeningBalanceMappings
            .FirstOrDefaultAsync(e => e.Id == id);
    }

    public async Task<IReadOnlyList<OpeningBalanceMapping>> GetAllByCompanyAsync(long companyId)
    {
        return await _context.OpeningBalanceMappings
            .AsNoTracking()
            .Where(e => e.CompanyId == companyId)
            .OrderBy(e => e.VoucherTypeId)
            .ThenBy(e => e.DebitAccountId)
            .ToListAsync();
    }

    public async Task AddAsync(OpeningBalanceMapping mapping)
    {
        await _context.OpeningBalanceMappings.AddAsync(mapping);
    }
}
```

**Gotcha — DbSet name:** `OpeningBalanceMappings` (plural) — matches DbSet property name pattern.

**Gotcha — No DisplayOrder ordering:** Unlike PostingConfiguration (which orders by DisplayOrder), OpeningBalanceMapping has no DisplayOrder. Order by `VoucherTypeId` then `DebitAccountId` as natural sort key.

**Gotcha — Only 3 methods:** Simpler than PostingConfiguration's 4 methods. No `GetAllByVoucherTypeAsync` — the plan only specifies company-scoped listing.

---

### 5. DbContext Modifications

**File:** `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`

**Current state (after T4):** 17 DbSets, 14 ignored events.

**Add DbSet (after line 26):**
```csharp
public DbSet<OpeningBalanceMapping> OpeningBalanceMappings => Set<OpeningBalanceMapping>();
```

**No event to ignore** — OpeningBalanceMapping does NOT raise a domain event. No `modelBuilder.Ignore<>()` needed.

**New count:** 18 DbSets, 14 ignored events (unchanged).

---

### 6. DI Registration

**File:** `src/SmeAccounting.Infrastructure/DependencyInjection.cs`

**Add (after line 39):**
```csharp
services.AddScoped<IOpeningBalanceMappingRepository, EfOpeningBalanceMappingRepository>();
```

**Pattern:** Same `AddScoped<IXxxRepository, EfXxxRepository>()` as all 12 existing registrations.

---

### Gotchas and Edge Cases

#### 1. No Domain Event
Same pattern as DocumentNumberingSeries (T2) and PostingConfiguration (T4). No event file, no `modelBuilder.Ignore<>()` in DbContext, no `AddDomainEvent()` in constructor. This is the third entity without a domain event in Phase 2.

#### 2. Simplified PostingConfiguration
OpeningBalanceMapping is essentially a stripped-down PostingConfiguration:
- Same dual Account FK pattern (DebitAccountId, CreditAccountId)
- Same DebitAccountId != CreditAccountId invariant
- NO DisplayOrder (not needed for opening balance — order doesn't matter for a single mapping)
- NO TransactionReasonId (opening balance entries are not tied to specific transaction reasons)
- UNIQUE index instead of non-unique (one mapping per company + voucher type + account pair)

#### 3. Two Account FKs — Explicit Configuration Required
Same as PostingConfiguration. Both `DebitAccountId` and `CreditAccountId` reference the Account entity. EF Core requires explicit FK configuration:
```csharp
builder.HasOne<Account>().WithMany().HasForeignKey(e => e.DebitAccountId)...
builder.HasOne<Account>().WithMany().HasForeignKey(e => e.CreditAccountId)...
```

#### 4. DebitAccountId != CreditAccountId — Domain Invariant
Same core accounting rule as PostingConfiguration. Enforced in constructor via DomainException. Application layer (Task 6) mirrors with FluentValidation.

#### 5. "Both Accounts Belong to Same Company" — Application-Level Only
Same limitation as PostingConfiguration. Entity only has account IDs (longs), cannot validate account ownership. Application layer (Task 6) must load both Account entities via IAccountRepository and verify CompanyId match before creating the mapping.

#### 6. Unique Index vs Non-Unique
PostingConfiguration uses a non-unique composite index `(VoucherTypeId, TransactionReasonId)` for query performance. OpeningBalanceMapping uses a UNIQUE composite index `(CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId)` to enforce business rule: one mapping per company + voucher type + account pair. The unique index prevents duplicate configurations at the DB level.

#### 7. No DisplayOrder
Unlike PostingConfiguration, OpeningBalanceMapping has no DisplayOrder property. The repository sorts by `VoucherTypeId` then `DebitAccountId` as the natural ordering. The Application layer (Task 6) does not need to display these in a specific order — they are configuration entries, not user-facing lists.

#### 8. Architecture Test Compliance
- Entity inherits `BaseEntity` → must be in `SmeAccounting.Domain.Entities` ✓
- Port interface `IOpeningBalanceMappingRepository` starts with `I` ✓
- Domain has zero NuGet refs → no new packages ✓
- Infrastructure references Domain only → correct ✓
- No Api references to Domain.Entities or Domain.Ports → correct ✓

#### 9. Migration Timing
Migration created in Task 7. OpeningBalanceMappings table will be `opening_balance_mappings` in the `Phase2AccountingControlConfig` migration alongside the other 4 new tables.

#### 10. DbSet Naming
DbSet property: `OpeningBalanceMappings` (plural). Table: `opening_balance_mappings` (snake_case plural). The DbSet expression-bodied property pattern: `public DbSet<OpeningBalanceMapping> OpeningBalanceMappings => Set<OpeningBalanceMapping>();`

#### 11. Entity Is Smallest in Phase 2
OpeningBalanceMapping has only 6 properties (CompanyId, VoucherTypeId, DebitAccountId, CreditAccountId, IsActive, Description) — the simplest entity in Phase 2. This makes it a quick implementation with minimal edge cases.

#### 12. FiscalPeriod Reference
The plan mentions "existing Account/FiscalPeriod entities" as dependencies. However, OpeningBalanceMapping does NOT have a FiscalPeriodId FK. FiscalPeriod is an indirect dependency — the Application layer (Task 6) will use FiscalPeriod to determine when opening balance entries should be posted, but the mapping entity itself only references VoucherType and Account.

---

## Task-Specific Research — Task 6: Application Layer — Commands + Queries for All 5 Slices

**Goal:** Create MediatR commands, queries, DTOs, validators, and handlers for all 5 Phase 2 domains (VoucherType, DocumentNumberingSeries, TransactionReason, PostingConfiguration, OpeningBalanceMapping).

**Depends on:** Tasks 1-5 (all domain entities + infrastructure complete).

**CRITICAL DISCOVERY: No handler implementations exist anywhere in the codebase.** All 6 existing commands (CreateAccountCommand, DeprecateAccountCommand, CreateJournalEntryCommand, PostJournalEntryCommand, CloseFiscalPeriodCommand, OpenFiscalPeriodCommand) and 6 existing queries (GetAccountQuery, GetAccountsByGroupQuery, GetJournalEntryQuery, GetFiscalPeriodsQuery, GetBalanceSheetQuery, GetIncomeStatementQuery) are defined as records implementing `IRequest<T>`, but there are ZERO `IRequestHandler<TRequest, TResponse>` implementations anywhere in the solution. Controllers dispatch via MediatR but no handlers exist. Task 6 must create a new `Handlers/` directory and implement handlers for ALL commands/queries (both existing Phase 1 and new Phase 2).

### File List — Complete Task 6 Output

**Total: ~30 new files, 0 modified files.**

| # | File Path | Type | Slice |
|---|-----------|------|-------|
| 1 | `src/SmeAccounting.Application/DTOs/VoucherTypeDto.cs` | DTO | VoucherType |
| 2 | `src/SmeAccounting.Application/DTOs/DocumentNumberingSeriesDto.cs` | DTO | DocumentNumberingSeries |
| 3 | `src/SmeAccounting.Application/DTOs/TransactionReasonDto.cs` | DTO | TransactionReason |
| 4 | `src/SmeAccounting.Application/DTOs/PostingConfigurationDto.cs` | DTO | PostingConfiguration |
| 5 | `src/SmeAccounting.Application/DTOs/OpeningBalanceMappingDto.cs` | DTO | OpeningBalanceMapping |
| 6 | `src/SmeAccounting.Application/Commands/CreateVoucherTypeCommand.cs` | Command | VoucherType |
| 7 | `src/SmeAccounting.Application/Commands/DeactivateVoucherTypeCommand.cs` | Command | VoucherType |
| 8 | `src/SmeAccounting.Application/Commands/CreateDocumentNumberingSeriesCommand.cs` | Command | DocumentNumberingSeries |
| 9 | `src/SmeAccounting.Application/Commands/ResetNumberingSeriesCommand.cs` | Command | DocumentNumberingSeries |
| 10 | `src/SmeAccounting.Application/Commands/CreateTransactionReasonCommand.cs` | Command | TransactionReason |
| 11 | `src/SmeAccounting.Application/Commands/DeactivateTransactionReasonCommand.cs` | Command | TransactionReason |
| 12 | `src/SmeAccounting.Application/Commands/CreatePostingConfigurationCommand.cs` | Command | PostingConfiguration |
| 13 | `src/SmeAccounting.Application/Commands/DeactivatePostingConfigurationCommand.cs` | Command | PostingConfiguration |
| 14 | `src/SmeAccounting.Application/Commands/CreateOpeningBalanceMappingCommand.cs` | Command | OpeningBalanceMapping |
| 15 | `src/SmeAccounting.Application/Commands/DeactivateOpeningBalanceMappingCommand.cs` | Command | OpeningBalanceMapping |
| 16 | `src/SmeAccounting.Application/Queries/GetVoucherTypeQuery.cs` | Query | VoucherType |
| 17 | `src/SmeAccounting.Application/Queries/GetVoucherTypesByCompanyQuery.cs` | Query | VoucherType |
| 18 | `src/SmeAccounting.Application/Queries/GetNumberingSeriesQuery.cs` | Query | DocumentNumberingSeries |
| 19 | `src/SmeAccounting.Application/Queries/GetNumberingSeriesByCompanyQuery.cs` | Query | DocumentNumberingSeries |
| 20 | `src/SmeAccounting.Application/Queries/GetTransactionReasonQuery.cs` | Query | TransactionReason |
| 21 | `src/SmeAccounting.Application/Queries/GetTransactionReasonsByVoucherTypeQuery.cs` | Query | TransactionReason |
| 22 | `src/SmeAccounting.Application/Queries/GetPostingConfigurationQuery.cs` | Query | PostingConfiguration |
| 23 | `src/SmeAccounting.Application/Queries/GetPostingConfigurationsByCompanyQuery.cs` | Query | PostingConfiguration |
| 24 | `src/SmeAccounting.Application/Queries/GetOpeningBalanceMappingQuery.cs` | Query | OpeningBalanceMapping |
| 25 | `src/SmeAccounting.Application/Queries/GetOpeningBalanceMappingsByCompanyQuery.cs` | Query | OpeningBalanceMapping |
| 26 | `src/SmeAccounting.Application/Validators/CreateVoucherTypeCommandValidator.cs` | Validator | VoucherType |
| 27 | `src/SmeAccounting.Application/Validators/CreateDocumentNumberingSeriesCommandValidator.cs` | Validator | DocumentNumberingSeries |
| 28 | `src/SmeAccounting.Application/Validators/CreateTransactionReasonCommandValidator.cs` | Validator | TransactionReason |
| 29 | `src/SmeAccounting.Application/Validators/CreatePostingConfigurationCommandValidator.cs` | Validator | PostingConfiguration |
| 30 | `src/SmeAccounting.Application/Validators/CreateOpeningBalanceMappingCommandValidator.cs` | Validator | OpeningBalanceMapping |
| 31 | `src/SmeAccounting.Application/Handlers/` (directory) | Directory | All |
| 32-41 | `src/SmeAccounting.Application/Handlers/*.cs` (10 handler files) | Handlers | All |

---

### 1. Existing Application Layer Patterns (Exhaustive Reference)

#### 1.1 Command Pattern

**File pattern:** One file per command, command + result records in same file.
**Namespace:** `SmeAccounting.Application.Commands`
**File-scoped namespace:** Yes (`namespace SmeAccounting.Application.Commands;`)
**Type:** `record` implementing `IRequest<TResult>`

**Exact existing patterns:**

```csharp
// Simple command (from CreateAccountCommand.cs)
using MediatR;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Application.Commands;

public record CreateAccountCommand(
    string Code,
    string Name,
    AccountType AccountType,
    long CompanyId,
    NormalBalance NormalBalance,
    long? ParentId,
    long? AccountGroupId,
    string? Description = null) : IRequest<CreateAccountResult>;

public record CreateAccountResult(long Id);
```

```csharp
// Simple deprecation command (from DeprecateAccountCommand.cs)
using MediatR;

namespace SmeAccounting.Application.Commands;

public record DeprecateAccountCommand(long AccountId) : IRequest<DeprecateAccountResult>;

public record DeprecateAccountResult(long AccountId);
```

```csharp
// Command with nested input type (from CreateJournalEntryCommand.cs)
using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Commands;

public record CreateJournalEntryCommand(
    DateTimeOffset Date,
    long PeriodId,
    string? Description,
    string? SourceType,
    long? SourceId,
    IReadOnlyList<JournalEntryLineInput> Lines) : IRequest<CreateJournalEntryResult>;

public record JournalEntryLineInput(
    long AccountId,
    decimal DebitAmount,
    decimal CreditAmount,
    string? Description);

public record CreateJournalEntryResult(long Id, string EntryNumber);
```

**Key pattern observations:**
- Command record uses positional parameters (primary constructor syntax)
- Result record defined in same file, immediately after command
- Result record name follows: `{CommandNameWithoutCommand}Result` pattern (e.g., `CreateAccountResult`, `DeprecateAccountResult`)
- Optional parameters use `?` nullable + default value (e.g., `string? Description = null`)
- `long?` for nullable FK IDs
- `IReadOnlyList<T>` for collection inputs
- No validation in command constructors — validation is in FluentValidation validators

#### 1.2 Query Pattern

**File pattern:** One file per query.
**Namespace:** `SmeAccounting.Application.Queries`
**Type:** `record` implementing `IRequest<ResponseType>`

**Exact existing patterns:**

```csharp
// Single-item query (from GetAccountQuery.cs)
using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetAccountQuery(long AccountId) : IRequest<AccountDto?>;
```

```csharp
// Collection query (from GetAccountsByGroupQuery.cs)
using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetAccountsByGroupQuery(long AccountGroupId) : IRequest<IReadOnlyList<AccountDto>>;
```

```csharp
// Nullable parameter query (from GetFiscalPeriodsQuery.cs)
using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetFiscalPeriodsQuery(long? YearId) : IRequest<IReadOnlyList<FiscalPeriodDto>>;
```

```csharp
// Non-nullable return type query (from GetBalanceSheetQuery.cs)
using MediatR;
using SmeAccounting.Application.DTOs;

namespace SmeAccounting.Application.Queries;

public record GetBalanceSheetQuery(long PeriodId) : IRequest<BalanceSheetDto>;
```

**Key pattern observations:**
- Single-item queries return `DtoType?` (nullable)
- Collection queries return `IReadOnlyList<DtoType>`
- Non-nullable returns for aggregate queries (BalanceSheet, IncomeStatement)
- Query parameter names use entity-specific names (e.g., `AccountId`, `AccountGroupId`, `PeriodId`)
- No validators on queries (only commands have validators)

#### 1.3 DTO Pattern

**File pattern:** One file per DTO. Simple records with no methods.
**Namespace:** `SmeAccounting.Application.DTOs`
**Type:** `record` (positional parameters)

**Critical: Enums are stored as `string` in DTOs, NOT as enum types.** This is the established pattern.

**Exact existing patterns:**

```csharp
// Simple DTO (from AccountDto.cs)
namespace SmeAccounting.Application.DTOs;

public record AccountDto(
    long Id,
    string Code,
    string Name,
    int Level,
    long? ParentId,
    string AccountType,      // enum stored as string
    bool IsActive,
    long? AccountGroupId,
    long CompanyId,
    string? Description,
    string NormalBalance);   // enum stored as string
```

```csharp
// DTO with nested collection (from JournalEntryDto.cs)
namespace SmeAccounting.Application.DTOs;

public record JournalEntryDto(
    long Id,
    string EntryNumber,
    DateTimeOffset Date,
    long PeriodId,
    string? Description,
    bool IsPosted,
    DateTimeOffset? PostedAt,
    IReadOnlyList<JournalEntryLineDto> Lines);
```

```csharp
// Helper DTO (from MoneyDto.cs)
namespace SmeAccounting.Application.DTOs;

public record MoneyDto(decimal Amount, string Currency);
```

```csharp
// Aggregate DTO (from BalanceSheetDto.cs)
namespace SmeAccounting.Application.DTOs;

public record BalanceSheetDto(
    IReadOnlyList<AccountGroupTotal> Assets,
    IReadOnlyList<AccountGroupTotal> Liabilities,
    IReadOnlyList<AccountGroupTotal> Equity);

public record AccountGroupTotal(string GroupName, decimal Total, string Currency);
```

**Key pattern observations:**
- DTOs are pure records — no methods, no validation, no domain references
- Enums mapped as `string` (e.g., `string AccountType`, `string NormalBalance`, `string Status`)
- Nullable properties use `string?`, `long?`, `DateTimeOffset?`
- `IReadOnlyList<T>` for collection properties
- Each DTO in its own file (except AccountGroupTotal which is a helper in BalanceSheetDto.cs)
- All DTOs MUST end with `Dto` suffix (architecture test enforces this)
- No `using` statements needed for simple records (file-scoped namespace)

#### 1.4 Validator Pattern

**File pattern:** One file per validator.
**Namespace:** `SmeAccounting.Application.Validators`
**Type:** `class` inheriting `AbstractValidator<TCommand>`

**Exact existing patterns:**

```csharp
// Complex validator (from CreateAccountCommandValidator.cs)
using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateAccountCommandValidator : AbstractValidator<CreateAccountCommand>
{
    public CreateAccountCommandValidator()
    {
        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Account code is required.")
            .Matches(@"^\d{4,}$").WithMessage("Account code must be numeric, at least 4 digits.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Account name is required.")
            .MaximumLength(200).WithMessage("Account name cannot exceed 200 characters.");

        RuleFor(x => x.AccountType)
            .IsInEnum().WithMessage("Invalid account type.");
    }
}
```

```csharp
// Simple ID validator (from PostJournalEntryCommandValidator.cs)
using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class PostJournalEntryCommandValidator : AbstractValidator<PostJournalEntryCommand>
{
    public PostJournalEntryCommandValidator()
    {
        RuleFor(x => x.JournalEntryId)
            .GreaterThan(0).WithMessage("Journal entry ID is required.");
    }
}
```

```csharp
// Collection validator (from CreateJournalEntryCommandValidator.cs)
using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateJournalEntryCommandValidator : AbstractValidator<CreateJournalEntryCommand>
{
    public CreateJournalEntryCommandValidator()
    {
        RuleFor(x => x.PeriodId)
            .GreaterThan(0).WithMessage("Period ID is required.");

        RuleFor(x => x.Lines)
            .NotEmpty().WithMessage("Journal entry must have at least one line.");

        RuleForEach(x => x.Lines).ChildRules(line =>
        {
            line.RuleFor(l => l.AccountId)
                .GreaterThan(0).WithMessage("Line must have a valid account.");
        });
    }
}
```

**Key pattern observations:**
- Constructor-based rules (no `RuleLevelCascadeMode` or class-level settings)
- `RuleFor(x => x.Property)` fluent syntax
- `.NotEmpty()` for strings
- `.GreaterThan(0)` for long IDs
- `.IsInEnum()` for enum values
- `.MaximumLength(N)` for string length limits
- `.Matches("regex")` for pattern validation
- `.WithMessage("...")` on every rule
- `RuleForEach(...).ChildRules(...)` for collection validation
- Validators auto-discovered by `AddValidatorsFromAssembly` — no manual registration needed
- Namespace: `SmeAccounting.Application.Validators`

#### 1.5 Handler Pattern (CRITICAL — No Existing Handlers)

**NO HANDLERS EXIST.** This is the most important finding. The 6 existing commands and 6 existing queries have no `IRequestHandler<>` implementations. Task 6 must create ALL handlers from scratch.

**Handler directory:** New `src/SmeAccounting.Application/Handlers/` directory.
**Namespace:** `SmeAccounting.Application.Handlers`
**Type:** `class` implementing `IRequestHandler<TCommand, TResult>` or `IRequestHandler<TQuery, TResult>`

**Architecture constraint:** Handlers must NOT reference `SmeAccounting.Infrastructure` namespace (enforced by `Application_Handlers_Should_Not_Reference_Infrastructure_Namespace` test). Handlers use port interfaces (e.g., `IVoucherTypeRepository`) injected via constructor.

**DI auto-registration:** `AddMediatR(cfg => cfg.RegisterServicesFromAssembly(...))` scans the Application assembly and auto-registers all `IRequestHandler<>` implementations. No manual handler registration needed.

**Handler template (to be created):**

```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateVoucherTypeHandler(
    IVoucherTypeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateVoucherTypeCommand, CreateVoucherTypeResult>
{
    public async Task<CreateVoucherTypeResult> Handle(
        CreateVoucherTypeCommand request,
        CancellationToken cancellationToken)
    {
        var voucherType = new VoucherType(
            request.CompanyId, request.Code, request.Name,
            request.VoucherCategory, request.Description);

        await repository.AddAsync(voucherType);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateVoucherTypeResult(voucherType.Id);
    }
}
```

**Key handler pattern observations (derived from architecture + DI patterns):**
- `internal sealed class` — not public (matches Infrastructure pattern)
- Primary constructor with port interfaces injected
- Implements `IRequestHandler<TCommand, TResult>`
- Single `Handle` method with `(TCommand request, CancellationToken ct)`
- Create handlers: new entity -> repo.AddAsync -> unitOfWork.SaveChangesAsync -> return result
- Deactivate handlers: repo.GetByIdAsync -> entity.Deactivate() -> unitOfWork.SaveChangesAsync -> return result
- Query handlers: repo.GetByIdAsync -> map to DTO -> return DTO
- Collection query handlers: repo.GetAllByXAsync -> map to IReadOnlyList<DTO> -> return list
- Mapping: manual property-by-property (no AutoMapper)

#### 1.6 DI Registration Pattern

**File:** `src/SmeAccounting.Application/DependencyInjection.cs`

**Current code:**
```csharp
using FluentValidation;
using MediatR;
using Microsoft.Extensions.DependencyInjection;
using SmeAccounting.Application.Behaviors;

namespace SmeAccounting.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(typeof(DependencyInjection).Assembly);
            cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
        });

        services.AddValidatorsFromAssembly(typeof(DependencyInjection).Assembly);

        return services;
    }
}
```

**No changes needed.** The assembly scan (`RegisterServicesFromAssembly`) auto-discovers:
- All `IRequestHandler<>` implementations (new handlers in `Handlers/` directory)
- All `IValidator<>` implementations (new validators in `Validators/` directory)
- The `ValidationBehavior<>` pipeline behavior (already registered)

Adding new files to the Application assembly is sufficient. No manual DI registration required.

#### 1.7 ValidationBehavior Pipeline

**File:** `src/SmeAccounting.Application/Behaviors/ValidationBehavior.cs`

```csharp
public class ValidationBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
```

- Runs ALL validators for a command before the handler executes
- If any validation fails, throws `FluentValidation.ValidationException` with aggregated failures
- Skipped if no validators registered for the command type
- Controllers catch `ValidationException` and populate ModelState

#### 1.8 Application Project References

**File:** `src/SmeAccounting.Application/SmeAccounting.Application.csproj`

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <ProjectReference Include="..\SmeAccounting.Domain\SmeAccounting.Domain.csproj" />
  </ItemGroup>
  <ItemGroup>
    <PackageReference Include="MediatR" Version="14.2.0" />
    <PackageReference Include="FluentValidation" Version="12.1.0" />
    <PackageReference Include="FluentValidation.DependencyInjectionExtensions" Version="12.1.0" />
  </ItemGroup>
</Project>
```

Application references ONLY Domain. No Infrastructure reference. This is why handlers use port interfaces, not EF Core directly.

---

### 2. Phase 2 Domain Reference — Entity Constructors + Port Methods

Handlers need to create entities and call repo methods. Here are the exact constructor signatures and port interfaces for all 5 entities:

#### 2.1 VoucherType

**Entity constructor:**
```csharp
new VoucherType(long companyId, string code, string name, VoucherCategory voucherCategory, string? description = null)
```

**Port:**
```csharp
IVoucherTypeRepository {
    Task<VoucherType?> GetByIdAsync(long id);
    Task<VoucherType?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<VoucherType>> GetAllAsync();
    Task AddAsync(VoucherType voucherType);
}
```

**Domain method:** `Deactivate()` — sets `IsActive = false`

#### 2.2 DocumentNumberingSeries

**Entity constructor:**
```csharp
new DocumentNumberingSeries(
    long companyId, long voucherTypeId, string prefix,
    int paddingLength = 6, bool isDefault = false, string? description = null)
```

**Port:**
```csharp
IDocumentNumberingSeriesRepository {
    Task<DocumentNumberingSeries?> GetByIdAsync(long id);
    Task<DocumentNumberingSeries?> GetDefaultAsync(long voucherTypeId, long companyId);
    Task<IReadOnlyList<DocumentNumberingSeries>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(DocumentNumberingSeries series);
}
```

**Domain methods:** `Increment()`, `Reset(int startFrom)`, `Deactivate()`

#### 2.3 TransactionReason

**Entity constructor:**
```csharp
new TransactionReason(long companyId, long voucherTypeId, string code, string name, string? description = null)
```

**Port:**
```csharp
ITransactionReasonRepository {
    Task<TransactionReason?> GetByIdAsync(long id);
    Task<TransactionReason?> GetByCodeAsync(string code, long companyId);
    Task<IReadOnlyList<TransactionReason>> GetAllByVoucherTypeAsync(long voucherTypeId);
    Task AddAsync(TransactionReason transactionReason);
}
```

**Domain method:** `Deactivate()`

#### 2.4 PostingConfiguration

**Entity constructor:**
```csharp
new PostingConfiguration(
    long companyId, long voucherTypeId, long debitAccountId, long creditAccountId,
    long? transactionReasonId = null, int displayOrder = 0, string? description = null)
```

**Port:**
```csharp
IPostingConfigurationRepository {
    Task<PostingConfiguration?> GetByIdAsync(long id);
    Task<IReadOnlyList<PostingConfiguration>> GetAllByVoucherTypeAsync(long voucherTypeId, long companyId);
    Task<IReadOnlyList<PostingConfiguration>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(PostingConfiguration postingConfiguration);
}
```

**Domain method:** `Deactivate()`

#### 2.5 OpeningBalanceMapping

**Entity constructor:**
```csharp
new OpeningBalanceMapping(
    long companyId, long voucherTypeId, long debitAccountId, long creditAccountId,
    string? description = null)
```

**Port:**
```csharp
IOpeningBalanceMappingRepository {
    Task<OpeningBalanceMapping?> GetByIdAsync(long id);
    Task<IReadOnlyList<OpeningBalanceMapping>> GetAllByCompanyAsync(long companyId);
    Task AddAsync(OpeningBalanceMapping mapping);
}
```

**Domain method:** `Deactivate()`

#### 2.6 IUnitOfWork

```csharp
IUnitOfWork {
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}
```

Implemented by `SmeAccountingDbContext`. Every command handler must call `unitOfWork.SaveChangesAsync(cancellationToken)` after mutations.

---

### 3. Exact Command Definitions (from PLAN.md)

#### 3.1 VoucherType Commands

```csharp
// CreateVoucherTypeCommand
public record CreateVoucherTypeCommand(
    string Code,
    string Name,
    VoucherCategory VoucherCategory,
    long CompanyId,
    string? Description = null) : IRequest<CreateVoucherTypeResult>;

public record CreateVoucherTypeResult(long Id);
```

```csharp
// DeactivateVoucherTypeCommand
public record DeactivateVoucherTypeCommand(long VoucherTypeId) : IRequest<DeactivateVoucherTypeResult>;

public record DeactivateVoucherTypeResult;
```

**Gotcha — DeactivateVoucherTypeResult has NO properties:** Unlike DeprecateAccountResult(long AccountId) which echoes the ID back, the plan specifies `DeactivateVoucherTypeResult` with no parameters. Same pattern for all 4 deactivate commands. This is a parameterless result record.

#### 3.2 DocumentNumberingSeries Commands

```csharp
// CreateDocumentNumberingSeriesCommand
public record CreateDocumentNumberingSeriesCommand(
    long VoucherTypeId,
    long CompanyId,
    string Prefix,
    int PaddingLength,
    bool IsDefault,
    string? Description = null) : IRequest<CreateDocumentNumberingSeriesResult>;

public record CreateDocumentNumberingSeriesResult(long Id);
```

```csharp
// ResetNumberingSeriesCommand
public record ResetNumberingSeriesCommand(long SeriesId, int StartFrom) : IRequest<ResetNumberingSeriesResult>;

public record ResetNumberingSeriesResult;
```

**Gotcha — ResetNumberingSeriesResult has no properties:** Same as deactivate pattern. No echo of SeriesId.

#### 3.3 TransactionReason Commands

```csharp
// CreateTransactionReasonCommand
public record CreateTransactionReasonCommand(
    string Code,
    string Name,
    long VoucherTypeId,
    long CompanyId,
    string? Description = null) : IRequest<CreateTransactionReasonResult>;

public record CreateTransactionReasonResult(long Id);
```

```csharp
// DeactivateTransactionReasonCommand
public record DeactivateTransactionReasonCommand(long ReasonId) : IRequest<DeactivateTransactionReasonResult>;

public record DeactivateTransactionReasonResult;
```

**Gotcha — Parameter name is `ReasonId`, not `TransactionReasonId`:** The plan specifies `ReasonId` as the command parameter name. Follow this exactly.

#### 3.4 PostingConfiguration Commands

```csharp
// CreatePostingConfigurationCommand
public record CreatePostingConfigurationCommand(
    long VoucherTypeId,
    long DebitAccountId,
    long CreditAccountId,
    long CompanyId,
    long? TransactionReasonId,
    string? Description = null) : IRequest<CreatePostingConfigurationResult>;

public record CreatePostingConfigurationResult(long Id);
```

```csharp
// DeactivatePostingConfigurationCommand
public record DeactivatePostingConfigurationCommand(long ConfigId) : IRequest<DeactivatePostingConfigurationResult>;

public record DeactivatePostingConfigurationResult;
```

**Gotcha — Parameter name is `ConfigId`, not `PostingConfigurationId`:** Follow plan exactly.

#### 3.5 OpeningBalanceMapping Commands

```csharp
// CreateOpeningBalanceMappingCommand
public record CreateOpeningBalanceMappingCommand(
    long CompanyId,
    long VoucherTypeId,
    long DebitAccountId,
    long CreditAccountId,
    string? Description = null) : IRequest<CreateOpeningBalanceMappingResult>;

public record CreateOpeningBalanceMappingResult(long Id);
```

```csharp
// DeactivateOpeningBalanceMappingCommand
public record DeactivateOpeningBalanceMappingCommand(long MappingId) : IRequest<DeactivateOpeningBalanceMappingResult>;

public record DeactivateOpeningBalanceMappingResult;
```

**Gotcha — Parameter name is `MappingId`:** Follow plan exactly.

---

### 4. Exact Query Definitions (from PLAN.md)

#### 4.1 VoucherType Queries

```csharp
// GetVoucherTypeQuery
public record GetVoucherTypeQuery(long VoucherTypeId) : IRequest<VoucherTypeDto?>;
```

```csharp
// GetVoucherTypesByCompanyQuery
public record GetVoucherTypesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<VoucherTypeDto>>;
```

#### 4.2 DocumentNumberingSeries Queries

```csharp
// GetNumberingSeriesQuery
public record GetNumberingSeriesQuery(long SeriesId) : IRequest<DocumentNumberingSeriesDto?>;
```

```csharp
// GetNumberingSeriesByCompanyQuery
public record GetNumberingSeriesByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<DocumentNumberingSeriesDto>>;
```

#### 4.3 TransactionReason Queries

```csharp
// GetTransactionReasonQuery
public record GetTransactionReasonQuery(long ReasonId) : IRequest<TransactionReasonDto?>;
```

```csharp
// GetTransactionReasonsByVoucherTypeQuery
public record GetTransactionReasonsByVoucherTypeQuery(long VoucherTypeId) : IRequest<IReadOnlyList<TransactionReasonDto>>;
```

#### 4.4 PostingConfiguration Queries

```csharp
// GetPostingConfigurationQuery
public record GetPostingConfigurationQuery(long ConfigId) : IRequest<PostingConfigurationDto?>;
```

```csharp
// GetPostingConfigurationsByCompanyQuery
public record GetPostingConfigurationsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<PostingConfigurationDto>>;
```

#### 4.5 OpeningBalanceMapping Queries

```csharp
// GetOpeningBalanceMappingQuery
public record GetOpeningBalanceMappingQuery(long MappingId) : IRequest<OpeningBalanceMappingDto?>;
```

```csharp
// GetOpeningBalanceMappingsByCompanyQuery
public record GetOpeningBalanceMappingsByCompanyQuery(long CompanyId) : IRequest<IReadOnlyList<OpeningBalanceMappingDto>>;
```

**Query naming convention:** `Get{Entity}Query` for single item, `Get{EntityPlural}By{Scope}Query` for collection.

---

### 5. DTO Definitions

All DTOs are records in `SmeAccounting.Application.DTOs`. Enums stored as `string`.

```csharp
// VoucherTypeDto.cs
namespace SmeAccounting.Application.DTOs;

public record VoucherTypeDto(
    long Id,
    string Code,
    string Name,
    string VoucherCategory,  // enum as string
    long CompanyId,
    bool IsActive,
    string? Description);
```

```csharp
// DocumentNumberingSeriesDto.cs
namespace SmeAccounting.Application.DTOs;

public record DocumentNumberingSeriesDto(
    long Id,
    long VoucherTypeId,
    long CompanyId,
    string Prefix,
    int NextNumber,
    int PaddingLength,
    bool IsDefault,
    bool IsActive,
    string? Description);
```

```csharp
// TransactionReasonDto.cs
namespace SmeAccounting.Application.DTOs;

public record TransactionReasonDto(
    long Id,
    string Code,
    string Name,
    long VoucherTypeId,
    long CompanyId,
    bool IsActive,
    string? Description);
```

```csharp
// PostingConfigurationDto.cs
namespace SmeAccounting.Application.DTOs;

public record PostingConfigurationDto(
    long Id,
    long VoucherTypeId,
    long DebitAccountId,
    long CreditAccountId,
    long CompanyId,
    long? TransactionReasonId,
    int DisplayOrder,
    bool IsActive,
    string? Description);
```

```csharp
// OpeningBalanceMappingDto.cs
namespace SmeAccounting.Application.DTOs;

public record OpeningBalanceMappingDto(
    long Id,
    long CompanyId,
    long VoucherTypeId,
    long DebitAccountId,
    long CreditAccountId,
    bool IsActive,
    string? Description);
```

**DTO mapping in handlers (entity -> DTO):**

```csharp
// Example: VoucherType entity -> VoucherTypeDto
var dto = new VoucherTypeDto(
    entity.Id,
    entity.Code,
    entity.Name,
    entity.VoucherCategory.ToString(),  // enum -> string
    entity.CompanyId,
    entity.IsActive,
    entity.Description);
```

**Critical: `.ToString()` for enum-to-string mapping.** This matches the existing pattern where `AccountType` enum is mapped to `string AccountType` in `AccountDto` via `.ToString()`.

---

### 6. Validator Definitions

#### 6.1 CreateVoucherTypeCommandValidator

```csharp
using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateVoucherTypeCommandValidator : AbstractValidator<CreateVoucherTypeCommand>
{
    public CreateVoucherTypeCommandValidator()
    {
        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Voucher type code is required.")
            .MaximumLength(20).WithMessage("Voucher type code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Voucher type name is required.")
            .MaximumLength(200).WithMessage("Voucher type name cannot exceed 200 characters.");

        RuleFor(x => x.VoucherCategory)
            .IsInEnum().WithMessage("Invalid voucher category.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
```

#### 6.2 CreateDocumentNumberingSeriesCommandValidator

```csharp
using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateDocumentNumberingSeriesCommandValidator : AbstractValidator<CreateDocumentNumberingSeriesCommand>
{
    public CreateDocumentNumberingSeriesCommandValidator()
    {
        RuleFor(x => x.VoucherTypeId)
            .GreaterThan(0).WithMessage("Voucher type ID is required.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.Prefix)
            .NotEmpty().WithMessage("Prefix is required.")
            .MaximumLength(20).WithMessage("Prefix cannot exceed 20 characters.");

        RuleFor(x => x.PaddingLength)
            .InclusiveBetween(1, 10).WithMessage("Padding length must be between 1 and 10.");
    }
}
```

#### 6.3 CreateTransactionReasonCommandValidator

```csharp
using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateTransactionReasonCommandValidator : AbstractValidator<CreateTransactionReasonCommand>
{
    public CreateTransactionReasonCommandValidator()
    {
        RuleFor(x => x.Code)
            .NotEmpty().WithMessage("Transaction reason code is required.")
            .MaximumLength(20).WithMessage("Transaction reason code cannot exceed 20 characters.");

        RuleFor(x => x.Name)
            .NotEmpty().WithMessage("Transaction reason name is required.")
            .MaximumLength(200).WithMessage("Transaction reason name cannot exceed 200 characters.");

        RuleFor(x => x.VoucherTypeId)
            .GreaterThan(0).WithMessage("Voucher type ID is required.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");
    }
}
```

#### 6.4 CreatePostingConfigurationCommandValidator

```csharp
using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreatePostingConfigurationCommandValidator : AbstractValidator<CreatePostingConfigurationCommand>
{
    public CreatePostingConfigurationCommandValidator()
    {
        RuleFor(x => x.VoucherTypeId)
            .GreaterThan(0).WithMessage("Voucher type ID is required.");

        RuleFor(x => x.DebitAccountId)
            .GreaterThan(0).WithMessage("Debit account ID is required.");

        RuleFor(x => x.CreditAccountId)
            .GreaterThan(0).WithMessage("Credit account ID is required.");

        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x)
            .Must(x => x.DebitAccountId != x.CreditAccountId)
            .WithMessage("Debit and credit accounts must be different.");

        RuleFor(x => x.TransactionReasonId)
            .GreaterThan(0).When(x => x.TransactionReasonId.HasValue)
            .WithMessage("Transaction reason ID must be greater than zero when specified.");
    }
}
```

**Gotcha — Custom `Must` rule for debit != credit:** FluentValidation has no built-in "not equal" rule across two properties. Use `.Must(x => x.DebitAccountId != x.CreditAccountId)` with a lambda on the command object. This mirrors the domain invariant `DomainException("DebitAccountId and CreditAccountId must be different.")` on `PostingConfiguration`.

**Gotcha — Conditional TransactionReasonId validation:** `.GreaterThan(0).When(x => x.TransactionReasonId.HasValue)` — only validates when the nullable has a value. Null is valid (default posting rule).

#### 6.5 CreateOpeningBalanceMappingCommandValidator

```csharp
using FluentValidation;
using SmeAccounting.Application.Commands;

namespace SmeAccounting.Application.Validators;

public class CreateOpeningBalanceMappingCommandValidator : AbstractValidator<CreateOpeningBalanceMappingCommand>
{
    public CreateOpeningBalanceMappingCommandValidator()
    {
        RuleFor(x => x.CompanyId)
            .GreaterThan(0).WithMessage("Company ID is required.");

        RuleFor(x => x.VoucherTypeId)
            .GreaterThan(0).WithMessage("Voucher type ID is required.");

        RuleFor(x => x.DebitAccountId)
            .GreaterThan(0).WithMessage("Debit account ID is required.");

        RuleFor(x => x.CreditAccountId)
            .GreaterThan(0).WithMessage("Credit account ID is required.");

        RuleFor(x => x)
            .Must(x => x.DebitAccountId != x.CreditAccountId)
            .WithMessage("Debit and credit accounts must be different.");
    }
}
```

---

### 7. Handler Implementations — Complete Templates

All handlers go in `src/SmeAccounting.Application/Handlers/`. New directory — `internal sealed class`.

#### 7.1 VoucherType Handlers

**CreateVoucherTypeHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateVoucherTypeHandler(
    IVoucherTypeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateVoucherTypeCommand, CreateVoucherTypeResult>
{
    public async Task<CreateVoucherTypeResult> Handle(
        CreateVoucherTypeCommand request,
        CancellationToken cancellationToken)
    {
        var voucherType = new VoucherType(
            request.CompanyId, request.Code, request.Name,
            request.VoucherCategory, request.Description);

        await repository.AddAsync(voucherType);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateVoucherTypeResult(voucherType.Id);
    }
}
```

**DeactivateVoucherTypeHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateVoucherTypeHandler(
    IVoucherTypeRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateVoucherTypeCommand, DeactivateVoucherTypeResult>
{
    public async Task<DeactivateVoucherTypeResult> Handle(
        DeactivateVoucherTypeCommand request,
        CancellationToken cancellationToken)
    {
        var voucherType = await repository.GetByIdAsync(request.VoucherTypeId);
        if (voucherType is null)
            throw new InvalidOperationException($"Voucher type with ID {request.VoucherTypeId} not found.");

        voucherType.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateVoucherTypeResult();
    }
}
```

**GetVoucherTypeHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetVoucherTypeHandler(
    IVoucherTypeRepository repository)
    : IRequestHandler<GetVoucherTypeQuery, VoucherTypeDto?>
{
    public async Task<VoucherTypeDto?> Handle(
        GetVoucherTypeQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.VoucherTypeId);
        return entity is null ? null : new VoucherTypeDto(
            entity.Id, entity.Code, entity.Name,
            entity.VoucherCategory.ToString(),
            entity.CompanyId, entity.IsActive, entity.Description);
    }
}
```

**GetVoucherTypesByCompanyHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetVoucherTypesByCompanyHandler(
    IVoucherTypeRepository repository)
    : IRequestHandler<GetVoucherTypesByCompanyQuery, IReadOnlyList<VoucherTypeDto>>
{
    public async Task<IReadOnlyList<VoucherTypeDto>> Handle(
        GetVoucherTypesByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllAsync();
        return entities
            .Where(e => e.CompanyId == request.CompanyId)
            .Select(e => new VoucherTypeDto(
                e.Id, e.Code, e.Name,
                e.VoucherCategory.ToString(),
                e.CompanyId, e.IsActive, e.Description))
            .ToList();
    }
}
```

**Gotcha — GetAllAsync returns all companies, filter in handler:** `IVoucherTypeRepository.GetAllAsync()` has no companyId parameter (returns all voucher types). The handler must filter by CompanyId in memory. This is an existing limitation of the VoucherType repo (same as the `GetAllAsync()` pattern on Department/CostCenter/Project repos). A future improvement could add `GetAllByCompanyAsync(companyId)` to the port.

#### 7.2 DocumentNumberingSeries Handlers

**CreateDocumentNumberingSeriesHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateDocumentNumberingSeriesHandler(
    IDocumentNumberingSeriesRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateDocumentNumberingSeriesCommand, CreateDocumentNumberingSeriesResult>
{
    public async Task<CreateDocumentNumberingSeriesResult> Handle(
        CreateDocumentNumberingSeriesCommand request,
        CancellationToken cancellationToken)
    {
        var series = new DocumentNumberingSeries(
            request.CompanyId, request.VoucherTypeId, request.Prefix,
            request.PaddingLength, request.IsDefault, request.Description);

        await repository.AddAsync(series);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateDocumentNumberingSeriesResult(series.Id);
    }
}
```

**ResetNumberingSeriesHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class ResetNumberingSeriesHandler(
    IDocumentNumberingSeriesRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<ResetNumberingSeriesCommand, ResetNumberingSeriesResult>
{
    public async Task<ResetNumberingSeriesResult> Handle(
        ResetNumberingSeriesCommand request,
        CancellationToken cancellationToken)
    {
        var series = await repository.GetByIdAsync(request.SeriesId);
        if (series is null)
            throw new InvalidOperationException($"Numbering series with ID {request.SeriesId} not found.");

        series.Reset(request.StartFrom);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new ResetNumberingSeriesResult();
    }
}
```

**GetNumberingSeriesHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetNumberingSeriesHandler(
    IDocumentNumberingSeriesRepository repository)
    : IRequestHandler<GetNumberingSeriesQuery, DocumentNumberingSeriesDto?>
{
    public async Task<DocumentNumberingSeriesDto?> Handle(
        GetNumberingSeriesQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.SeriesId);
        return entity is null ? null : new DocumentNumberingSeriesDto(
            entity.Id, entity.VoucherTypeId, entity.CompanyId,
            entity.Prefix, entity.NextNumber, entity.PaddingLength,
            entity.IsDefault, entity.IsActive, entity.Description);
    }
}
```

**GetNumberingSeriesByCompanyHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetNumberingSeriesByCompanyHandler(
    IDocumentNumberingSeriesRepository repository)
    : IRequestHandler<GetNumberingSeriesByCompanyQuery, IReadOnlyList<DocumentNumberingSeriesDto>>
{
    public async Task<IReadOnlyList<DocumentNumberingSeriesDto>> Handle(
        GetNumberingSeriesByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new DocumentNumberingSeriesDto(
                e.Id, e.VoucherTypeId, e.CompanyId,
                e.Prefix, e.NextNumber, e.PaddingLength,
                e.IsDefault, e.IsActive, e.Description))
            .ToList();
    }
}
```

#### 7.3 TransactionReason Handlers

**CreateTransactionReasonHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateTransactionReasonHandler(
    ITransactionReasonRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateTransactionReasonCommand, CreateTransactionReasonResult>
{
    public async Task<CreateTransactionReasonResult> Handle(
        CreateTransactionReasonCommand request,
        CancellationToken cancellationToken)
    {
        var reason = new TransactionReason(
            request.CompanyId, request.VoucherTypeId,
            request.Code, request.Name, request.Description);

        await repository.AddAsync(reason);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateTransactionReasonResult(reason.Id);
    }
}
```

**DeactivateTransactionReasonHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateTransactionReasonHandler(
    ITransactionReasonRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateTransactionReasonCommand, DeactivateTransactionReasonResult>
{
    public async Task<DeactivateTransactionReasonResult> Handle(
        DeactivateTransactionReasonCommand request,
        CancellationToken cancellationToken)
    {
        var reason = await repository.GetByIdAsync(request.ReasonId);
        if (reason is null)
            throw new InvalidOperationException($"Transaction reason with ID {request.ReasonId} not found.");

        reason.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateTransactionReasonResult();
    }
}
```

**GetTransactionReasonHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTransactionReasonHandler(
    ITransactionReasonRepository repository)
    : IRequestHandler<GetTransactionReasonQuery, TransactionReasonDto?>
{
    public async Task<TransactionReasonDto?> Handle(
        GetTransactionReasonQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.ReasonId);
        return entity is null ? null : new TransactionReasonDto(
            entity.Id, entity.Code, entity.Name,
            entity.VoucherTypeId, entity.CompanyId,
            entity.IsActive, entity.Description);
    }
}
```

**GetTransactionReasonsByVoucherTypeHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetTransactionReasonsByVoucherTypeHandler(
    ITransactionReasonRepository repository)
    : IRequestHandler<GetTransactionReasonsByVoucherTypeQuery, IReadOnlyList<TransactionReasonDto>>
{
    public async Task<IReadOnlyList<TransactionReasonDto>> Handle(
        GetTransactionReasonsByVoucherTypeQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByVoucherTypeAsync(request.VoucherTypeId);
        return entities
            .Select(e => new TransactionReasonDto(
                e.Id, e.Code, e.Name,
                e.VoucherTypeId, e.CompanyId,
                e.IsActive, e.Description))
            .ToList();
    }
}
```

#### 7.4 PostingConfiguration Handlers

**CreatePostingConfigurationHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreatePostingConfigurationHandler(
    IPostingConfigurationRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreatePostingConfigurationCommand, CreatePostingConfigurationResult>
{
    public async Task<CreatePostingConfigurationResult> Handle(
        CreatePostingConfigurationCommand request,
        CancellationToken cancellationToken)
    {
        var config = new PostingConfiguration(
            request.CompanyId, request.VoucherTypeId,
            request.DebitAccountId, request.CreditAccountId,
            request.TransactionReasonId, description: request.Description);

        await repository.AddAsync(config);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreatePostingConfigurationResult(config.Id);
    }
}
```

**Gotcha — DisplayOrder not in command:** The `CreatePostingConfigurationCommand` does not include `DisplayOrder`. The entity constructor defaults `displayOrder` to 0. If DisplayOrder needs to be set, it should be added to the command. For now, follow the plan exactly — command has no DisplayOrder parameter.

**DeactivatePostingConfigurationHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivatePostingConfigurationHandler(
    IPostingConfigurationRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivatePostingConfigurationCommand, DeactivatePostingConfigurationResult>
{
    public async Task<DeactivatePostingConfigurationResult> Handle(
        DeactivatePostingConfigurationCommand request,
        CancellationToken cancellationToken)
    {
        var config = await repository.GetByIdAsync(request.ConfigId);
        if (config is null)
            throw new InvalidOperationException($"Posting configuration with ID {request.ConfigId} not found.");

        config.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivatePostingConfigurationResult();
    }
}
```

**GetPostingConfigurationHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPostingConfigurationHandler(
    IPostingConfigurationRepository repository)
    : IRequestHandler<GetPostingConfigurationQuery, PostingConfigurationDto?>
{
    public async Task<PostingConfigurationDto?> Handle(
        GetPostingConfigurationQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.ConfigId);
        return entity is null ? null : new PostingConfigurationDto(
            entity.Id, entity.VoucherTypeId, entity.DebitAccountId,
            entity.CreditAccountId, entity.CompanyId,
            entity.TransactionReasonId, entity.DisplayOrder,
            entity.IsActive, entity.Description);
    }
}
```

**GetPostingConfigurationsByCompanyHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetPostingConfigurationsByCompanyHandler(
    IPostingConfigurationRepository repository)
    : IRequestHandler<GetPostingConfigurationsByCompanyQuery, IReadOnlyList<PostingConfigurationDto>>
{
    public async Task<IReadOnlyList<PostingConfigurationDto>> Handle(
        GetPostingConfigurationsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new PostingConfigurationDto(
                e.Id, e.VoucherTypeId, e.DebitAccountId,
                e.CreditAccountId, e.CompanyId,
                e.TransactionReasonId, e.DisplayOrder,
                e.IsActive, e.Description))
            .ToList();
    }
}
```

#### 7.5 OpeningBalanceMapping Handlers

**CreateOpeningBalanceMappingHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class CreateOpeningBalanceMappingHandler(
    IOpeningBalanceMappingRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<CreateOpeningBalanceMappingCommand, CreateOpeningBalanceMappingResult>
{
    public async Task<CreateOpeningBalanceMappingResult> Handle(
        CreateOpeningBalanceMappingCommand request,
        CancellationToken cancellationToken)
    {
        var mapping = new OpeningBalanceMapping(
            request.CompanyId, request.VoucherTypeId,
            request.DebitAccountId, request.CreditAccountId,
            request.Description);

        await repository.AddAsync(mapping);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new CreateOpeningBalanceMappingResult(mapping.Id);
    }
}
```

**DeactivateOpeningBalanceMappingHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.Commands;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class DeactivateOpeningBalanceMappingHandler(
    IOpeningBalanceMappingRepository repository,
    IUnitOfWork unitOfWork)
    : IRequestHandler<DeactivateOpeningBalanceMappingCommand, DeactivateOpeningBalanceMappingResult>
{
    public async Task<DeactivateOpeningBalanceMappingResult> Handle(
        DeactivateOpeningBalanceMappingCommand request,
        CancellationToken cancellationToken)
    {
        var mapping = await repository.GetByIdAsync(request.MappingId);
        if (mapping is null)
            throw new InvalidOperationException($"Opening balance mapping with ID {request.MappingId} not found.");

        mapping.Deactivate();
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return new DeactivateOpeningBalanceMappingResult();
    }
}
```

**GetOpeningBalanceMappingHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetOpeningBalanceMappingHandler(
    IOpeningBalanceMappingRepository repository)
    : IRequestHandler<GetOpeningBalanceMappingQuery, OpeningBalanceMappingDto?>
{
    public async Task<OpeningBalanceMappingDto?> Handle(
        GetOpeningBalanceMappingQuery request,
        CancellationToken cancellationToken)
    {
        var entity = await repository.GetByIdAsync(request.MappingId);
        return entity is null ? null : new OpeningBalanceMappingDto(
            entity.Id, entity.CompanyId, entity.VoucherTypeId,
            entity.DebitAccountId, entity.CreditAccountId,
            entity.IsActive, entity.Description);
    }
}
```

**GetOpeningBalanceMappingsByCompanyHandler:**
```csharp
using MediatR;
using SmeAccounting.Application.DTOs;
using SmeAccounting.Application.Queries;
using SmeAccounting.Domain.Ports;

namespace SmeAccounting.Application.Handlers;

internal sealed class GetOpeningBalanceMappingsByCompanyHandler(
    IOpeningBalanceMappingRepository repository)
    : IRequestHandler<GetOpeningBalanceMappingsByCompanyQuery, IReadOnlyList<OpeningBalanceMappingDto>>
{
    public async Task<IReadOnlyList<OpeningBalanceMappingDto>> Handle(
        GetOpeningBalanceMappingsByCompanyQuery request,
        CancellationToken cancellationToken)
    {
        var entities = await repository.GetAllByCompanyAsync(request.CompanyId);
        return entities
            .Select(e => new OpeningBalanceMappingDto(
                e.Id, e.CompanyId, e.VoucherTypeId,
                e.DebitAccountId, e.CreditAccountId,
                e.IsActive, e.Description))
            .ToList();
    }
}
```

---

### 8. Architecture Test Compliance

**Tests that constrain Application layer (from architecture tests):**

| Test | Constraint | Task 6 Impact |
|------|-----------|---------------|
| `Commands_In_Commands_Namespace_Should_End_With_Command` | All `IRequest<>` types in `SmeAccounting.Application.Commands` namespace must end with `Command` | All new commands end with `Command` ✓ |
| `Queries_In_Queries_Namespace_Should_End_With_Query` | All classes in `SmeAccounting.Application.Queries` must end with `Query` | All new queries end with `Query` ✓ |
| `DTOs_Should_End_With_Dto` | All types in `SmeAccounting.Application.DTOs` ending with `Dto` must also end with `Dto` | All new DTOs end with `Dto` ✓ |
| `Application_Handlers_Should_Not_Reference_Infrastructure_Namespace` | `IRequestHandler<,>` implementations must not reference `SmeAccounting.Infrastructure` | Handlers only reference Domain.Ports, Domain.Entities, Application.Commands, Application.DTOs ✓ |
| `Application_Should_Not_Depend_On_Infrastructure` | Application assembly must not reference Infrastructure assembly | No Infrastructure references in any Application file ✓ |
| `Application_Should_Not_Depend_On_Api` | Application assembly must not reference Api assembly | No Api references in any Application file ✓ |

**Key constraint for handlers:** Handlers MUST use port interfaces (`IVoucherTypeRepository`, `IUnitOfWork`, etc.) — NEVER concrete implementations (`EfVoucherTypeRepository`, `SmeAccountingDbContext`). Port interfaces are in `SmeAccounting.Domain.Ports` which Application is allowed to reference.

**Handler namespace:** `SmeAccounting.Application.Handlers` — NOT in `Commands` or `Queries` namespace. The architecture tests do NOT constrain handler namespace, only handler dependency on Infrastructure.

---

### 9. Gotchas and Edge Cases

#### 9.1 No Existing Handlers — Must Create All From Scratch
The most critical finding. 6 existing commands + 6 existing queries have no handlers. Controllers dispatch via MediatR but will throw `InvalidOperationException("No service for type 'MediatR.IRequestHandler<...>'")` at runtime. Task 6 must create handlers for ALL commands/queries (both existing Phase 1 and new Phase 2). The plan only mentions Phase 2 handlers, but the executor should decide whether to also create Phase 1 handlers or defer them.

#### 9.2 Deactivate/Reset Result Records Have No Properties
`DeactivateVoucherTypeResult`, `DeactivateTransactionReasonResult`, `DeactivatePostingConfigurationResult`, `DeactivateOpeningBalanceMappingResult`, and `ResetNumberingSeriesResult` are all parameterless records. Unlike `DeprecateAccountResult(long AccountId)` which echoes the ID, these are empty. Follow the plan exactly.

#### 9.3 GetAllAsync vs GetAllByCompanyAsync
`IVoucherTypeRepository.GetAllAsync()` returns ALL voucher types across ALL companies. The `GetVoucherTypesByCompanyHandler` must filter in memory with `.Where(e => e.CompanyId == request.CompanyId)`. This is an existing limitation. Other repos (`IDocumentNumberingSeriesRepository`, `IPostingConfigurationRepository`, `IOpeningBalanceMappingRepository`) have company-scoped methods already. `ITransactionReasonRepository.GetAllByVoucherTypeAsync()` is scoped by voucher type, not company.

#### 9.4 Enum-to-String Mapping in DTOs
Entity enums (e.g., `VoucherCategory`) are mapped to DTO strings via `.ToString()`. This is the established pattern. Do NOT use `.ToString("G")` or any format specifier — default `.ToString()` produces the enum name (e.g., "Receipt", "Payment").

#### 9.5 Domain Exceptions in Create Handlers
If entity constructor throws `DomainException` (e.g., empty code, invalid company ID), the handler will propagate it unhandled. This is correct behavior — `DomainException` is not caught by `ValidationException` catch blocks in controllers. The FluentValidation pipeline catches bad input BEFORE the handler runs. Domain exceptions are a safety net for business rule violations that slip past validation.

#### 9.6 NotFound Handling in Deactivate/Reset Handlers
Handlers throw `InvalidOperationException` if the entity is not found. This is a runtime error, not a validation error. Controllers will see a 500 error. A more robust pattern would use `Result<T>` or custom exceptions, but the existing codebase does not use this pattern. Follow existing convention: `throw new InvalidOperationException($"... with ID {id} not found.")`.

#### 9.7 Command Parameter Names Must Match Plan
The plan specifies exact parameter names: `VoucherTypeId`, `ReasonId`, `ConfigId`, `MappingId`, `SeriesId`. These differ from entity property names (e.g., entity has `Id` but command uses `VoucherTypeId`/`ReasonId`/`ConfigId`/`MappingId`/`SeriesId`). Follow the plan exactly.

#### 9.8 No DisplayOrder in CreatePostingConfigurationCommand
The plan omits `DisplayOrder` from the create command. Entity defaults to 0. If ordering matters, add it later. Follow the plan as-is.

#### 9.9 File-Scoped Namespaces
All files use file-scoped namespace syntax (`namespace X;` not `namespace X { }`). This is the established pattern across all Application files.

#### 9.10 No `using` Needed for Implicit Usings
`Directory.Build.props` enables implicit usings. Standard namespaces like `System`, `System.Collections.Generic`, `System.Linq`, `System.Threading.Tasks` are auto-imported. Only need explicit `using` for:
- `MediatR` (for `IRequest<>`, `IRequestHandler<>`)
- `FluentValidation` (for `AbstractValidator<>`)
- `SmeAccounting.Application.Commands` (for command types)
- `SmeAccounting.Application.DTOs` (for DTO types)
- `SmeAccounting.Application.Queries` (for query types)
- `SmeAccounting.Domain.Entities` (for entity types)
- `SmeAccounting.Domain.Ports` (for port interfaces)

#### 9.11 Handler Count
Total handlers to create: 10 (for 10 new commands + 10 new queries = 20 new request types). Each handler file contains one handler class. Total handler files: 10 (or 20 if one file per request type — depends on executor preference). Existing 12 commands/queries (6 commands + 6 queries) have no handlers and can be deferred.

#### 9.12 No Modifying Existing Files
Task 6 creates new files only. No modifications to existing commands, queries, DTOs, validators, DependencyInjection.cs, or any other file. All new content goes into new files in the Application project.
