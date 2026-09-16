# Loop Status
## State
IN_PROGRESS
## Current Task
T2 — FiscalYear + FiscalPeriod Extensions
## Task Progress
1 / 6 complete
## Attempts On Current Task
1
## Completed Tasks
- [x] [G1] T1 — Company Entity + Currency Promotion
## Skipped Tasks
(none)
## Last Researcher Result
T1 patterns mapped: BaseEntity (long Id, events), Account (private ctor, Deprecate pattern), Currency VO is minimal record (Code/Name/IsDefault) — promotion adds Id/Symbol/DecimalPlaces/IsActive. Config: internal sealed, snake_case, xmin, enums as strings. Repo: DbContext-injected, CRUD. Port: I{Name}Repository. Events: long Id + DateTimeOffset.UtcNow. TaxCode: `\d{10}(\d{3})?` regex. Money VO unchanged (uses string Currency). Namespace shift: ValueObjects.Currency → Entities.Currency.
## Last Executor Result
T1 complete. Files created/modified:
- Domain: Company.cs, Currency.cs (Entities), CompanyCreated.cs, CurrencyCreated.cs (Events), ICompanyRepository.cs, ICurrencyRepository.cs (Ports)
- Infrastructure: CompanyConfiguration.cs, CurrencyConfiguration.cs, EfCompanyRepository.cs, EfCurrencyRepository.cs, SmeAccountingDbContext.cs (DbSets + Ignore events), DependencyInjection.cs (DI registration)
- Build: 0 warnings, 0 errors. Arch tests: 22/22 pass.
## Last Verifier Result
**VERDICT: VERIFIED_PASS**

### Verification Results (6/6 criteria met)

| # | Criterion | Result | Detail |
|---|-----------|--------|--------|
| 1 | `dotnet build` exits 0 | ✅ | 0 warnings, 0 errors, 12.19s |
| 2 | Arch tests 22/22 | ✅ | Passed: 22, Failed: 0, Skipped: 0 |
| 3 | Company entity fields | ✅ | Id (long), Name, TaxCode, Address, Phone?, Email?, FiscalYearStartMonth (int, default 1, 1–12), FiscalYearStartDay (int, default 1, 1–28), FunctionalCurrencyCode (string, default "VND"), IsActive (bool, default true). Private ctor. |
| 4 | Currency entity (separate from VO) | ✅ | Entity in Entities/: Id (long), Code (3-char ISO 4217 validated), Name, Symbol, DecimalPlaces (default 2), IsDefault, IsActive (default true). Private ctor. Old VO in ValueObjects/ untouched. |
| 5 | Configs: snake-case + xmin | ✅ | CompanyConfiguration: `companies`, explicit HasColumnName all props, xmin row version, unique index on TaxCode. CurrencyConfiguration: `currencies`, explicit HasColumnName all props, xmin row version, unique index on Code. Both `internal sealed class`. |
| 6 | Money VO unchanged | ✅ | Money.cs in ValueObjects/ — still `record Money` with `decimal Amount` + `string Currency`. No changes. |
## Last Audit Result
**VERDICT: CLEAN**

### Audit Results (10/10 criteria met)

| # | Criterion | Result | Detail |
|---|-----------|--------|--------|
| 1 | `dotnet build` succeeds | ✅ | 0 warnings, 0 errors |
| 2 | Architecture tests pass | ✅ | 22/22 pass |
| 3 | Company entity fields | ✅ | Id, Name, TaxCode, Address, Phone?, Email?, FiscalYearStartMonth (1–12, default 1), FiscalYearStartDay (1–28, default 1), FunctionalCurrencyCode ("VND"), IsActive — all correct with private ctors, null checks, domain event |
| 4 | Currency entity (separate from VO) | ✅ | Entity in Entities/Currency.cs: Id, Code (ISO 4217 3-char validated), Name, Symbol, DecimalPlaces (default 2), IsDefault, IsActive — private ctor + CurrencyCreated event. Old VO record in ValueObjects/Currency.cs still exists but unused (no type references — only property name `Currency` on Money VO) |
| 5 | EF configs: snake-case + xmin | ✅ | Both configurations: `internal sealed class`, `ToTable("snake_case")`, explicit `HasColumnName` on every property, `xmin` row version, `ValueGeneratedOnAdd` on Id, unique indexes on TaxCode (Company) and Code (Currency) |
| 6 | Repositories implement interfaces | ✅ | EfCompanyRepository : ICompanyRepository — GetByIdAsync, GetByTaxCodeAsync, GetAllAsync (AsNoTracking), AddAsync. EfCurrencyRepository : ICurrencyRepository — GetByIdAsync, GetByCodeAsync, GetAllAsync (AsNoTracking), AddAsync. Both inject DbContext via constructor |
| 7 | DbContext: DbSets + Ignore events | ✅ | `DbSet<Company> Companies`, `DbSet<Currency> Currencies` added. `Ignore<CompanyCreated>()` and `Ignore<CurrencyCreated>()` in OnModelCreating. Existing DbSets and events unchanged |
| 8 | DI registration | ✅ | `AddScoped<ICompanyRepository, EfCompanyRepository>()` and `AddScoped<ICurrencyRepository, EfCurrencyRepository>()` in AddInfrastructure |
| 9 | No breaking changes | ✅ | Money VO unchanged (still `string Currency`). All existing commands/queries/validators/controllers compile. Old Currency VO record kept (unused but harmless — no namespace collision since no file imports both namespaces) |
| 10 | No unnecessary abstractions | ✅ | Entities are concrete classes (not interfaces), configurations follow existing pattern, repositories are direct implementations. No extra layers or abstractions added |
## Active Heartbeats
(none)
## Blocked Reason
(none)
