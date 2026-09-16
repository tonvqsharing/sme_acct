# Loop Plan
## Mode
build
## Goal
Build the Accounting Foundation of the Vietnamese accounting web application. Implement Company, Fiscal Year, Accounting Period, Currency, Exchange Rate, Chart of Accounts, and Accounting Dimensions (Department, Cost Center, Project) as production-grade accounting core. Follow Circular 99/2025/TT-BTC. TDD. Clean Architecture. Single company. No multi-tenancy.
## Stop Condition
all tasks in loop-stack/accounting-foundation-build/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks

- [x] ### [G1] T1 — Company Entity + Currency Promotion
**Parallel Group:** G1 (independent — foundation, no deps)
**Depends On:** none

**Deliverables:**
- `Company` entity in `src/SmeAccounting.Domain/Entities/Company.cs` with fields: Id (long), Name, TaxCode, Address, Phone, Email, FiscalYearStartMonth (int, 1–12, default 1), FiscalYearStartDay (int, 1–28, default 1), FunctionalCurrencyCode (string, default "VND"), IsActive (bool)
- `Currency` promoted from record VO to entity in `src/SmeAccounting.Domain/Entities/Currency.cs` with new fields: Id (long), Symbol, DecimalPlaces (int), IsActive (bool). Keep existing Code, Name, IsDefault. Add private parameterless constructor.
- `CompanyCreated` and `CurrencyPromoted` domain events in `src/SmeAccounting.Domain/Events/`
- `ICompanyRepository` and `ICurrencyRepository` port interfaces in `src/SmeAccounting.Domain/Ports/`
- EF Core configurations: `CompanyConfiguration` and `CurrencyConfiguration` in `src/SmeAccounting.Infrastructure/Persistence/Configurations/`
- Repository implementations: `EfCompanyRepository` and `EfCurrencyRepository` in `src/SmeAccounting.Infrastructure/Repositories/`
- DbSet properties added to `SmeAccountingDbContext`
- Domain events ignored in `OnModelCreating`
- DI registration in `Infrastructure/DependencyInjection.cs`
- Validation: Company.TaxCode regex `\d{10}(\d{3})?`, Currency.Code must be ISO 4217 3-char
- Preserve existing `Money` VO — it still references currency code strings, no change needed

**Acceptance Criteria:**
- `dotnet build SmeAccounting.sln` compiles with 0 warnings/errors
- 22 architecture tests pass
- Company entity has all required fields with correct types and defaults
- Currency entity has Id, Symbol, DecimalPlaces, IsActive alongside existing Code/Name/IsDefault
- Both configurations follow snake-case + xmin pattern
- Money VO unchanged (still a record with string Currency)

**Verification:** `dotnet build SmeAccounting.sln && dotnet test tests/SmeAccounting.ArchitectureTests/`

**Scope:** Domain/Entities, Domain/Ports, Domain/Events, Infrastructure/Configurations, Infrastructure/Repositories, Infrastructure/DependencyInjection.cs, Infrastructure/Persistence/SmeAccountingDbContext.cs

---

### [G2] T2 — FiscalYear + FiscalPeriod Extensions
**Parallel Group:** G2 (depends on T1; parallel with T3, T4, T5)
**Depends On:** T1 (CompanyId FK)

**Deliverables:**
- Extend `FiscalYear` entity: add CompanyId (long, required FK → Company), StartDate (DateOnly), EndDate (DateOnly), Description (string?)
- Extend `FiscalPeriod` entity: add StartDate (DateOnly), EndDate (DateOnly), PeriodType (new enum: Monthly, Quarterly)
- New domain invariant: FiscalYear.StartDate < EndDate, no overlapping FY per company
- Update existing `FiscalYearConfiguration` and `FiscalPeriodConfiguration` to add new columns with snake_case naming
- Update `FiscalPeriod` — existing Month field stays (for backwards compat), new StartDate/EndDate provide precision
- Domain event `FiscalYearCreated` (CompanyId, Year, StartDate, EndDate)

**Acceptance Criteria:**
- FiscalYear has CompanyId, StartDate, EndDate, Description columns
- FiscalPeriod has StartDate, EndDate, PeriodType columns
- New columns snake_case in DB
- xmin concurrency preserved on both entities
- All existing FiscalYear/FiscalPeriod commands/queries still compile (no breaking changes to existing method signatures)
- `dotnet build` passes, 22 arch tests pass

**Verification:** `dotnet build SmeAccounting.sln && dotnet test tests/SmeAccounting.ArchitectureTests/`

**Scope:** Domain/Entities (FiscalYear.cs, FiscalPeriod.cs), Infrastructure/Configurations (FiscalYearConfiguration.cs, FiscalPeriodConfiguration.cs), Domain/Events/

---

### [G2] T3 — ExchangeRate Entity + Repository
**Parallel Group:** G2 (depends on T1; parallel with T2, T4, T5)
**Depends On:** T1

**Deliverables:**
- `ExchangeRate` entity in `src/SmeAccounting.Domain/Entities/ExchangeRate.cs`: Id, CompanyId (long FK), FromCurrencyCode (string), ToCurrencyCode (string), Rate (decimal, precision 10,6, >0), RateType (enum: Average, Actual, Book, Contract), EffectiveDate (DateOnly), Source (string?)
- `ExchangeRateType` enum in `src/SmeAccounting.Domain/Enums/` (or inline in entity file)
- `ExchangeRateRecorded` domain event
- `IExchangeRateRepository` port interface: GetByIdAsync, GetByCurrencyPairAsync(from, to, rateType, date), GetAllAsync, AddAsync
- Domain invariant: FromCurrencyCode != ToCurrencyCode, Rate > 0
- EF Core `ExchangeRateConfiguration` following standard pattern
- `EfExchangeRateRepository` implementation
- DbSet + Ignore events + DI registration

**Acceptance Criteria:**
- ExchangeRate entity enforces From != To and Rate > 0 at domain level
- RateType stored as string conversion in DB
- Configuration uses snake_case, xmin row version
- No self-conversion (same currency codes) throws DomainException
- Build passes, arch tests pass

**Verification:** `dotnet build SmeAccounting.sln && dotnet test tests/SmeAccounting.ArchitectureTests/`

**Scope:** Domain/Entities/ExchangeRate.cs, Domain/Ports/IExchangeRateRepository.cs, Infrastructure/Configurations/ExchangeRateConfiguration.cs, Infrastructure/Repositories/EfExchangeRateRepository.cs, Infrastructure/DependencyInjection.cs, Infrastructure/Persistence/SmeAccountingDbContext.cs

---

### [G2] T4 — Chart of Accounts Extensions
**Parallel Group:** G2 (depends on T1; parallel with T2, T3, T5)
**Depends On:** T1

**Deliverables:**
- Extend `Account` entity: add CompanyId (long FK → Company), Description (string?), NormalBalance (enum: Debit, Credit)
- Extend `AccountGroup` entity: add CompanyId (long FK → Company), DisplayOrder (int)
- New `NormalBalance` enum in Domain/Enums/
- Update `AccountConfiguration` and `AccountGroupConfiguration` for new columns
- NormalBalance can be derived from AccountType (Asset/Expense→Debit, Liability/Equity/Revenue→Credit) but stored explicitly for posting clarity

**Acceptance Criteria:**
- Account has CompanyId, Description, NormalBalance columns
- AccountGroup has CompanyId, DisplayOrder columns
- NormalBalance enum stored as string in DB
- Existing CreateAccount/DeprecateAccount commands still compile
- Build passes, arch tests pass

**Verification:** `dotnet build SmeAccounting.sln && dotnet test tests/SmeAccounting.ArchitectureTests/`

**Scope:** Domain/Entities/Account.cs, Domain/Entities/AccountGroup.cs, Domain/Enums/, Infrastructure/Configurations/AccountConfiguration.cs, Infrastructure/Configurations/AccountGroupConfiguration.cs

---

### [G2] T5 — Accounting Dimensions (Department, CostCenter, Project)
**Parallel Group:** G2 (depends on T1; parallel with T2, T3, T4)
**Depends On:** T1

**Deliverables:**
- `Department` entity: Id, CompanyId (long FK), Code (string, unique per company), Name (string), IsActive (bool)
- `CostCenter` entity: Id, CompanyId (long FK), Code (string, unique per company), Name (string), IsActive (bool)
- `Project` entity: Id, CompanyId (long FK), Code (string, unique per company), Name (string), StartDate (DateOnly?), EndDate (DateOnly?), IsActive (bool)
- Port interfaces: `IDepartmentRepository`, `ICostCenterRepository`, `IProjectRepository`
- Domain events: `DepartmentCreated`, `CostCenterCreated`, `ProjectCreated`
- EF Core configurations for all three (snake_case, xmin)
- Repository implementations for all three
- DbSets + Ignore events + DI registration
- Extend `JournalEntryLine` — add optional FK columns: DepartmentId (long?), CostCenterId (long?), ProjectId (long?) with update to `JournalEntryLineConfiguration`

**Acceptance Criteria:**
- All three dimension entities exist with correct fields
- Code is unique per company per dimension (enforced at application level — composite index in config)
- JournalEntryLine has optional dimension FK columns
- Build passes, arch tests pass
- Soft-delete only (IsActive), no hard delete

**Verification:** `dotnet build SmeAccounting.sln && dotnet test tests/SmeAccounting.ArchitectureTests/`

**Scope:** Domain/Entities/ (Department.cs, CostCenter.cs, Project.cs), Domain/Ports/ (3 repo interfaces), Infrastructure/Configurations/ (3 new + JournalEntryLine update), Infrastructure/Repositories/ (3 new), Infrastructure/DependencyInjection.cs, Infrastructure/Persistence/SmeAccountingDbContext.cs

---

### [G3] T6 — EF Core Migration + Build Verification
**Parallel Group:** G3 (sequential — depends on T1–T5)
**Depends On:** T1, T2, T3, T4, T5

**Deliverables:**
- Single EF Core migration adding all new tables and altering existing tables:
  - New tables: companies, currencies, exchange_rates, departments, cost_centers, projects
  - Altered tables: fiscal_years (add company_id, start_date, end_date, description), fiscal_periods (add start_date, end_date, period_type), accounts (add company_id, description, normal_balance), account_groups (add company_id, display_order), journal_entry_lines (add department_id, cost_center_id, project_id)
- Migration generated via `dotnet ef migrations add AccountingFoundation --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`
- Full build verification: `dotnet build SmeAccounting.sln` — 0 warnings, 0 errors
- Full test verification: `dotnet test tests/SmeAccounting.ArchitectureTests/` — 22/22 pass
- Verify migration SQL is correct (review generated Up/Down methods)

**Acceptance Criteria:**
- Migration file generated with correct snake_case table/column names
- All new tables have xmin concurrency tokens
- All FK relationships correctly configured
- `dotnet build` clean (TreatWarningsAsErrors=true)
- All 22 architecture tests pass post-migration
- No changes to existing domain event handling

**Verification:** `dotnet build SmeAccounting.sln && dotnet test tests/SmeAccounting.ArchitectureTests/ && dotnet ef migrations list --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api`

**Scope:** src/SmeAccounting.Infrastructure/Migrations/, all Configuration files (final state), SmeAccountingDbContext.cs
