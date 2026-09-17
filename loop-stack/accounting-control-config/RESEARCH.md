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
