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

### G3 TaxRule & TaxExemptionReason — Cross-Loop Reference (Sep 2026)
- **TaxRule is the "glue entity"** linking TaxType + TaxRate (nullable FK for exempt) + TaxTreatment + Company — 4 FKs all Restrict
- **Nullable TaxRateId:** exempt/non-taxable rules have no rate; 0% rate (ZeroRate) has TaxRateId present
- **LegalReference (TaxRule) and LegalBasis (TaxExemptionReason) required** — audit trail non-negotiable
- **TaxExemptionReason follows TaxTreatment two-FK pattern** (Company + TaxType), unique index on (CompanyId, Code)
- **Conditions stored as text** — no JSON type needed; PostgreSQL maps string to text
- **GetActiveRulesForDateAsync:** EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive
- **No new enums** — uses existing entity FKs
- **DbContext after G3:** 24 DbSets, 20 ignored events. DI: 19 registrations.
- **All 22 architecture tests pass** — Domain.csproj zero NuGet refs preserved

### G1 Tax Foundation — Cross-Loop Reference (Sep 2026)
- **Enum naming rule:** When entity and enum share semantic name, enum gets suffix (TaxCategory, TaxTreatmentType, TaxAuthorityLevel) to avoid C# namespace collision — same as VoucherCategory/VoucherType
- **All G1 entities follow VoucherType pattern exactly:** CompanyId + Code + Name + [Enum] + IsActive + optional Description
- **Company-scoped repos use GetAllByCompanyAsync** (not GetAllAsync) — applies to TaxType, TaxTreatment, TaxAuthority
- **TaxTreatment follows TransactionReason pattern:** two FKs (Company + parent entity) both Restrict, unique index on (CompanyId, Code) NOT composite with parent FK
- **TaxAuthority is standalone** — no FK dependencies beyond CompanyId (unlike TaxTreatment → TaxType)
- **InputCreditAllowed bool** captures Vietnamese VAT 0%-vs-exempt distinction — critical regulatory requirement
- **DbContext after G1:** 21 DbSets, 17 ignored events, 16 DI registrations
- **All 22 architecture tests pass** — Domain.csproj zero NuGet refs preserved

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

### G2 TaxRate — Cross-Loop Reference (Sep 2026)
- **Effective-date pattern:** `DateOnly EffectiveFrom` (required) + `DateOnly? EffectiveTo` (nullable = indefinite) — same nullable DateOnly pattern as Project.StartDate/EndDate
- **Unique index:** `(CompanyId, TaxTypeId, RateValue, EffectiveFrom)` — composite 4-column uniqueness for per-type rate versioning
- **RateValue decimal(5,2):** Supports up to 999.99% — Vietnamese max is 50%
- **Date range filter:** `EffectiveFrom <= date AND (EffectiveTo IS NULL OR EffectiveTo >= date) AND IsActive` — standard effective-date query
- **No Code property:** TaxRate uses RateName (string) instead of Code — different from G1 entity pattern
- **DbContext after G2:** 22 DbSets, 18 ignored events, 17 DI registrations

### Vietnamese Tax Legislation (Sep 2026)
- **VAT Law 48/2024/QH15** effective July 1, 2025 — rates: 10% standard, 8% temporary (until Dec 31, 2026), 5% essential, 0% exports
- **CIT Law 67/2025/QH15** effective October 1, 2025 — rates: 20% standard, 15% small enterprise (≤VND 3B), 17% medium (VND 3-50B)
- **PIT Law 109/2025/QH15** effective July 1, 2026 — 5 brackets: 5%, 10%, 20%, 30%, 35% (reduced from 7 brackets)
- **Circular 99/2025/TT-BTC** effective January 1, 2026 — tax accounts: 1331 (VAT deductible goods), 1332 (VAT deductible fixed assets), 3331 (VAT payable), 33311 (output VAT), 33312 (import VAT), 3334 (CIT), 3335 (PIT)
- **Decree 70/2025/NĐ-CP** effective June 1, 2025 — e-invoice requirements, XML format mandatory
- **Key distinction:** 0% VAT rate (deductible input credit) vs. VAT-exempt (non-deductible input credit)
- **Temporary 8% VAT reduction** via Resolution 204/2025/QH15 — excludes telecom, finance, real estate, etc.
- **Non-cash payment evidence** required for input VAT credit on purchases ≥ VND 5 million
- [product-inventory-foundation, task 1] UOM master-data pattern reusable for Product & Inventory Foundation: Company-scoped entity with Code/Name/Symbol/IsActive/Description, unique (CompanyId,Code) index, UomCreated domain event, IUomRepository port, EfUomRepository, snake_case EF config with xmin concurrency, DI registration, CQRS Create/Deactivate/Get with FluentValidation, thin MediatR API controller, migration AddUom succeeds, build 0 warnings, architecture tests 22/22 pass.

### CompanySettings design & verification — company-opening-user-mgmt, 2026-09-21
- Loop company-opening-user-mgmt G1 design verified VERIFIED_PASS: build succeeds, 22 NetArchTest rules pass.
- What was built: domain scaffolding only — CompanySetting entity extending BaseEntity with CompanyId, LegalRepresentativeName, LegalRepresentativeTaxId, ChiefAccountantName, ChiefAccountantTaxId, FiscalYearStartMonth, Currency, ReportingSettingsJson; CompanySettingCreated domain event; ICompanySettingRepository port; CompanySettingConfiguration EF scaffold.
- Design decisions confirmed:
  - 1:1 per-company setting via unique index on CompanyId, FK to Company with DeleteBehavior.Restrict, no navigation property.
  - Scalar fields for Legal Representative/Chief Accountant; FiscalYearStartMonth 1-12 validation; Currency as string code matching Money VO pattern.
  - Extension data as jsonb column reporting_settings_json via HasColumnType("jsonb").
  - Private parameterless ctor for EF, public ctor with DomainException validation, domain events via AddDomainEvent.
- Patterns confirmed cross-loop:
  - BaseEntity domain events minimalism: event carries SettingId, CompanyId, OccurredOn — matches DepartmentCreated pattern.
  - EF configuration pattern: snake_case table company_settings, snake_case columns, xmin row version, unique index, HasOne<Company>().WithMany().HasForeignKey().OnDelete(Restrict).
  - Clean Architecture purity: Domain zero NuGet refs, no ASP.NET Identity coupling.
  - Validation via DomainException hierarchy, not ArgumentNullException.
  - Event Id=0 at construction consistent with existing Company/Department pattern.
- No Application/Infrastructure implementation yet per scope; design scaffolding only.

### Opening Balances domain engine fix & audit — company-opening-user-mgmt, 2026-09-21
- Source: loop-stack/company-opening-user-mgmt G1 Opening Balances fix executor and audit/verify.
- What changed:
  - OpeningBalanceEntry constructor no longer validates OpeningBalancePeriodId >0; transient aggregate Id=0 allowed, matching JournalEntryLine pattern where parent Id is 0 at construction time and EF populates FK on save.
  - Domain events minimized to EntityId + CompanyId + OccurredOn:
    - OpeningBalancePeriodCreated: PeriodId, CompanyId
    - OpeningBalanceEntryCreated: EntryId, CompanyId (AccountId removed)
    - OpeningBalancesPosted: PeriodId, CompanyId (JournalEntryId removed)
  - Entry number generation removed from domain: no `OP-{Id}-{PeriodDate}` using Id=0; JournalEntry creation uses `"OP-{PeriodDate:yyyyMMdd}"` without Id; final numbering deferred to Application handler after Id assigned.
  - FiscalPeriodId validation retained; no FiscalYearId confusion.
- Design decisions confirmed:
  - Transient aggregate pattern is canonical: child entities accept parent Id=0; EF Core sets relationships on persistence; events may carry provisional Id=0 at construction, as with Company/Department/JournalEntryLine.
  - Domain event minimalism is enforced cross-loop: events should carry entity ID + company ID + timestamp only, never duplicate entity payload.
  - Identifier formatting belongs to Application layer: domain should not format strings using transient IDs.
  - Posting remains domain responsibility: OpeningBalancePeriod.PostOpeningBalances validates open status, debit=credit, creates JournalEntry via domain, calls JournalEntry.Post, raises minimal OpeningBalancesPosted event.
- Patterns confirmed by audit:
  - Build succeeds with 0 warnings, 22/22 NetArchTest rules pass.
  - Transient aggregate works: OpeningBalanceEntry ctor accepts OpeningBalancePeriodId=0.
  - Events minimal: OpeningBalanceEntryCreated contains no AccountId; OpeningBalancesPosted contains no JournalEntryId.
  - EF configs: opening_balance_periods and opening_balance_entries tables with snake_case columns, xmin row version, FK Restrict to Company/FiscalPeriod/Account/OpeningBalancePeriod, unique indexes on (CompanyId,FiscalPeriodId) and (CompanyId,OpeningBalancePeriodId,AccountId).
  - Clean Architecture maintained: Domain zero NuGet refs, private parameterless ctor for EF, public ctor with DomainException, BaseEntity events, no navigation properties, FK to Company with DeleteBehavior.Restrict.
- Cross-loop impact:
  - Reinforces transient Id=0 pattern for all aggregates with children.
  - Reinforces domain event minimalism as global standard.
  - Confirms separation of domain validation from identifier formatting.

### User Management domain redesign — Microsoft-first — company-opening-user-mgmt, 2026-09-21
- Redesign context:
  - Initial Microsoft-first User Management domain model designed with User company-scoped (CompanyId on User), Email unique per company, UserCreated event carried CompanyId.
  - Audit/research identified identity-agnostic requirement: User must be global for Microsoft Entra sign-in, not per-company.
- Redesign applied:
  - User entity global: CompanyId removed, mandatory ExternalId added for Microsoft ObjectId mapping, Email unique globally, DomainException if ExternalId empty.
  - UserCreated domain event simplified to carry UserId only (no CompanyId).
  - CompanyMembershipCreated event added and raised on CompanyMembership construction with MembershipId + CompanyId + OccurredOn.
  - IUsersRepository updated to global queries: GetByExternalIdAsync, GetByEmailAsync, GetAllAsync (no company filter).
  - UserConfiguration updated: table users with columns external_id, email, display_name, user_name, is_active, xmin; unique indexes on external_id and email separately; CompanyId FK removed.
  - CompanyMembershipConfiguration: FK Restrict to User and Company, unique index (user_id, company_id).
  - UserRoleConfiguration: FK Restrict to Company/User/Role, unique index (user_id, role_id, company_id) — per-company role assignment.
  - Role remains company-scoped with CompanyId, Code, Name, unique index (company_id, code).
- Patterns reinforced:
  - Domain purity: Domain zero NuGet refs, no ASP.NET Identity coupling, no EF Core refs, authentication adapter lives in Infrastructure.
  - Entity pattern: private parameterless ctor for EF, public ctor with DomainException validation, BaseEntity domain events, no navigation properties.
  - FK Restrict to Company universal, snake_case naming, xmin concurrency, composite unique indexes for per-company uniqueness.
  - Domain event minimalism: UserCreated(UserId only), RoleCreated(RoleId+CompanyId), CompanyMembershipCreated(MembershipId+CompanyId), UserRoleAssigned(UserRoleId+CompanyId).
  - Separation of concerns: passwords/credentials not stored in Domain; Microsoft sign-in handled by Infrastructure adapter; Domain stores only identity-agnostic data (ExternalId, Email, DisplayName, IsActive).
- Decisions:
  - User global, CompanyMembership as explicit linking aggregate.
  - Role company-scoped.
  - ExternalId mandatory for Microsoft-first integration.
  - Email globally unique.
  - Build verified: 0 warnings, 22/22 NetArchTest rules pass.
- Cross-loop impact:
  - Establishes global User pattern for future multi-company SaaS scenarios.
  - Reinforces domain event minimalism and FK Restrict patterns.
  - Provides reference for authentication/authorization separation in Clean Architecture.

### CompanySettings Application + Infrastructure consolidated learnings — company-opening-user-mgmt, 2026-09-21
- Loop company-opening-user-mgmt G2 implementation complete and verified.
- DbContext: DbSet<CompanySetting> CompanySettings added, CompanySettingCreated ignored in OnModelCreating to prevent EF mapping.
- Infrastructure: EfCompanySettingRepository implements ICompanySettingRepository with async GetByIdAsync, GetByCompanyIdAsync, AddAsync using DbSet. No UpdateAsync; change tracking used.
- DI: ICompanySettingRepository -> EfCompanySettingRepository registered scoped in Infrastructure DependencyInjection.
- Application layer: CreateCompanySettingCommand record implements IRequest<CreateCompanySettingResult>. Handler CreateCompanySettingHandler constructs domain CompanySetting via public ctor, calls repository.AddAsync, unitOfWork.SaveChangesAsync, returns Id. DomainException validation runs in entity ctor.
- Validation: CreateCompanySettingCommandValidator uses FluentValidation: CompanyId >0, LegalRepresentativeName required max200, LegalRepresentativeTaxId required max50, ChiefAccountant fields max length, FiscalYearStartMonth 1-12 when present, Currency max3 when present.
- Queries: GetCompanySettingByIdQuery and GetCompanySettingByCompanyIdQuery with handlers returning CompanySettingDto. Manual mapping, no AutoMapper.
- DTO: CompanySettingDto record mirrors entity properties, no domain entity reference.
- Patterns reinforced: MediatR IRequest handlers, ValidationBehavior pipeline, DTO records, async EF Core repository, Unit of Work, domain events raised on construction, Clean Architecture maintained, build 0 warnings, 22/22 NetArchTest pass.
- Cross-loop reference: CompanySettings now full CQRS stack example — domain scaffolding → application commands/queries + validation + DTO → infrastructure repository + DbContext + DI. Reusable pattern for future company-scoped configuration entities.

### Bank Hierarchy — Cross-Loop Reference (Sep 2026)
- [implement-gen-acct-02, G2] Bank→BankBranch→BankAccount hierarchy: all Restrict FKs (never Cascade/SetNull for financial data), composite uniques (CompanyId,Code) / (CompanyId,BankId,Code) / (CompanyId,BankId,BankBranchId,Code)+(CompanyId,AccountNumber), snake_case tables banks/bank_branches/bank_accounts with xmin, BankCreated/BankBranchCreated/BankAccountCreated minimal events, MediatR+FluentValidation CQRS with manual DTO mapping, DbSet+Ignore<Event>+DI per aggregate, build 0 warn 0 err + 22/22 arch tests; fixes: single DTO file avoids CS8955, explicit usings avoid CS0246, remove unused vars avoids CS0219.
- [implement-gen-acct-02, task 6] BankTests minimal-test pattern: copy ArchitectureTests csproj (IsPackable false, xunit 2.9.3 + runner + TestSdk + coverlet, Using Xunit), reference Domain+Application only, dotnet sln add, hand List-backed fakes over new EF InMemory packages (InMemory ignores unique/FK/xmin), InternalsVisibleTo for internal handlers, ~13 Facts domain+validator+handler happy path, arch stays 22/22 since rules scan src assemblies only.

### PaymentMethod Slice — Cross-Loop Reference (Sep 2026)
- [payment-method-slice, G1] PaymentMethod design locks: enum `PaymentMethodCategory` (Cash/BankTransfer/Card/EWallet/Other) in Domain/ValueObjects string-stored, `RequiresBankAccount bool default false` scalar over nullable BankAccountId FK (one method spans many accounts mis-models as FK), category column locked to `category`, lengths 20/200/500, composite unique (CompanyId,Code) + Company FK Restrict + xmin, Ignore-only DbContext wiring (no DbSet, matches PaymentTerm/Customer/Supplier/Employee via Set<T>).
- [payment-method-slice, task G2] Enum-master vertical slice accepted CLEAN with validator-only enum guard: DTO stores enum as string via .ToString() and thin controller uses Enum.Parse<Category> (Domain.ValueObjects using passes arch, Domain.Entities using fails), invalid (Enum)999 rejected at FluentValidation IsInEnum with no domain Enum.IsDefined guard (PaymentTerm-faithful); flat Application layout (Commands/Handlers/Queries/Validators/DTOs) over Bank feature-folders; Deactivate handler beyond design minimum is safe extra; Ignore-only DbContext (1 Ignore line) + 1 AddScoped DI suffices; BankTests extended with List-backed fake reusing FakeUnitOfWork, zero csproj/sln edits (27/27, arch 22/22, build 0/0).
- [payment-method-slice, task G3] Check-only EF migration pattern: scaffold `dotnet ef migrations add <Name>` only after build+arch+tests green, verify Up()=single CreateTable + single unique CreateIndex with Restrict/no-CASCADE + snake_case + xmin and Down()=DropTable only with R1-R7 per-item verdicts quoted, never run `database update` without explicit approval (scaffold/script render offline, update needs live DB).
- [posting-reference-harden, task G1] Free-text trace columns keep InitialCreate width (source_type varchar100, NOT master-data Code-20); canonical-table vs cache-columns split (posting_references canonical with unique(CompanyId,SourceType,SourceId) + dual Restrict FKs, JE SourceType/SourceId read-model cache, same-UoW atomic write, direct CompanyId when chain hops lack HasOne); design-doc path must match PLAN or auditor WARNs.
- [posting-reference-harden, task G2] Don't add >0/posted guards to entity setters with live transient-Id=0 callers (JournalEntry.SetSource <- OpeningBalancePeriod.cs:78 passes pre-save Id 0); defer guard until caller fixed — zero-diff with reason passes audit/verify, reconcile ownership before next task.
- [posting-reference-harden, task G3] Thin MediatR Create POST must redirect on Send-result Id (`var result = await Mediator.Send(...); RedirectToAction Details(result.Id)`), never on an input-model FK (model.JournalEntryId is the wrong entity's id) — auditor WARN → verifier fix; PaymentTerm Index-redirect precedent masks this slip on Detail-redirect controllers.
- [posting-reference-harden, task G4] ALTER-only hardening migration pattern + defaultValue-0 backfill risk rule: scaffold renders Up=DropIndex old pair + AddColumn company_id bigint NOT NULL defaultValue 0L + CreateIndex UNIQUE(company_id,source_type,source_id) + 2xAddForeignKey Restrict with Down exact reversal (R1-R7 quoted PASS, no CreateTable/Cascade/SetNull, source_type varchar100 + xmin preserved); defaultValue 0L + same-Up Company FK FAILS at apply on any DB with existing rows (0 matches no companies.id) — state risk explicitly, leave scaffold unedited, defer backfill per design, never run database update without approval (check-only).
- [setsource-caller-fix, task 1] Harden-setter + transient-Id caller reconciliation: before adding a >0 guard whose live caller passes transient Id=0, check whether the caller's Id is real in the production handler path (loaded via GetByIdAsync) — if yes, land a domain-only caller fail-fast pre-condition (throw before building children, e.g. `if (Id <= 0) throw new DomainException(...)` inserted before JE construction) + full guard set in the same change; guard then holds unconditionally with zero handler/DI/EF churn; never relax the guard or absorb a separate out-of-scope persist bug to unblock (completes posting-reference-harden G2 lesson at :246).
- [setsource-caller-fix, task 2] TDD RED-first guard-fact split proves new-code coverage: write all Facts first, confirm guard-dependent subset fails RED (4/9: b,c,d,f) while unchanged-behavior subset passes (5/9), then GREEN with guards; test enablers: BaseEntity.Id has PUBLIC setter (tests set persisted Id directly, e.g. period.Id = 5 — no reflection/subclass needed) and InternalsVisibleTo("SmeAccounting.BankTests") already in Application.csproj (internal handler Facts testable with zero csproj edits; explicit using SmeAccounting.Application.Handlers required else CS0246).
- [setsource-caller-fix, task 3] No-migration evidence pattern for domain-only guard/caller changes: prove zero schema surface via Migrations-dir file count + latest migration timestamp predating loop commits + grep -i <feature> over Migrations = 0 hits; runtime in-memory guards (entity-method checks) touch no table/column/index/FK/DbContext so the no-migration statement passes audit/verify without scaffolding anything.
- [opening-balance-persist, G1] No-migration grep-evidence trap: `grep -i <feature>` over Migrations returns hits for pre-existing entity property names from prior loops (134 hits for 'openingbalance' — OpeningBalancePeriod/Entry/Mapping entities) — NOT valid zero-evidence; use Migrations-dir count + latest-migration timestamp + zero NEW migration files (diff/commit-tail) instead; grep only valid when feature has zero prior schema surface.
- [opening-balance-persist, G2] Design-doc line-level return placement can be wrong: literal "return after Post() :88 before flags :90-91" makes IsPosted/Status/event unreachable → CS0162 under TreatWarningsAsErrors; correct = end-of-method after event (:95); documented deviation + auditor CLEAN + verifier VERIFIED_PASS — compiler is arbiter over design-doc literals, verify reachability before locking placement.
- [opening-balance-persist, G3] Compile-error RED error-code prediction can be wrong: RESEARCH predicted CS7036 ("no argument given for required parameter") for 3-arg ctor call against stale 2-param primary ctor — actual is CS1729 "does not contain a constructor that takes 3 arguments" (CS7036 needs a 3-param ctor missing one arg). Same deterministic compile-error RED mechanism; record actual error code + lines, don't force the predicted one. Also: FakeJournalEntryRepository MUST implement GetAllAsync (port IJournalEntryRepository has it) — copying FakePostingReferenceRepository shape verbatim would CS0535; check port members, not just the copy source.
- [opening-balance-persist, G3] Verifier RED-reconstruction canon: revert the GREEN commit's changed file(s) (`git checkout <commit>~1 -- <file>`) and rebuild — compile-error RED reproduces deterministically (CS1729 at :176/:202; G2 CS0815 revert-domain-diff same), proving the recorded RED was real; restore file after. Independent of executor's recorded evidence; used twice in this loop.
- [opening-balance-persist, G4] No-touch audit canon: `git show --stat` per loop commit = exact file list per commit — cross-check each commit's files against the no-touch list (zero code changes ⇒ state-files-only commits, e.g. MEMORY/STATUS); pairs with Migrations count + latest-migration timestamp + zero NEW for closed-loop evidence; grep over Migrations stays invalid (G1 trap).
- [opening-balance-pr-link, G1] Don't replicate a precedent handler's duplicate pre-check when the target flow already has a domain guard: CreatePostingReferenceHandler's GetBySourceAsync+InvalidOperationException exists only because that handler lacks a domain guard; PostOpeningBalancesHandler's IsPosted guard (sequential dupes, pre-persistence) + xmin on the mutated period row (concurrent race, caught at save 1 before JE persists) + unique index (last resort) already layer the protection — the pre-check adds a DB round-trip, is TOCTOU-ineffective, and if placed post-save-1 leaves a dangling JE (committed JE, no PR row). Precedent patterns must be justified by target context, not by the precedent's existence.
