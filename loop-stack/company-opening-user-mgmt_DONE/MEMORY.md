# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
### [G1] Microsoft-first User Management domain model design — 2026-09-21
### [G1] Microsoft-first User Management domain model design — 2026-09-21
- Entities created: User, Role, UserRole, CompanyMembership in src/SmeAccounting.Domain/Entities extending BaseEntity with CompanyId, Email, DisplayName, IsActive etc. Private parameterless ctor + public ctor with DomainException validation.
- Domain events created: UserCreated, RoleCreated, UserRoleAssigned in src/SmeAccounting.Domain/Events with minimal payload EntityId + CompanyId + OccurredOn.
- Ports created: IUsersRepository and IRoleRepository in src/SmeAccounting.Domain/Ports with company-scoped async methods.
- EF configurations created: UserConfiguration, RoleConfiguration, UserRoleConfiguration, CompanyMembershipConfiguration mapping to snake_case tables users, roles, user_roles, company_memberships, xmin row version, FK Restrict to Company, composite unique indexes (company_id,email) for users, (company_id,code) for roles, (user_id,role_id,company_id) for user_roles, (user_id,company_id) for company_memberships.
- Design follows Clean Architecture constraints: Domain zero NuGet refs, no ASP.NET Identity coupling, no navigation properties to Company, FK Restrict pattern, domain events minimalism, private parameterless ctor for EF.
- Build succeeds with 0 warnings, 22/22 NetArchTest rules pass. No Application/Infrastructure implementation per scope.

### [G1] Microsoft-first User Management domain model — Fix — 2026-09-21
- Redesigned User entity to be global: removed CompanyId, added mandatory ExternalId, Email unique globally, DomainException if ExternalId empty, UserCreated event now carries UserId only (no CompanyId).
- Added CompanyMembershipCreated event class and raise event on CompanyMembership construction with MembershipId + CompanyId + OccurredOn.
- Updated IUsersRepository to GetByExternalIdAsync, GetByEmailAsync, GetAllAsync (no company filter).
- Updated UserConfiguration: table users, columns external_id, email, display_name, user_name, is_active, xmin; unique indexes on external_id and email separately; removed CompanyId FK and index.
- CompanyMembershipConfiguration unchanged but confirms FK Restrict to User and Company, unique index (user_id, company_id).
- UserRoleConfiguration unchanged, FK Restrict to Company/User/Role, unique index (user_id, role_id, company_id).
- Role remains company-scoped with CompanyId, Code, Name.
- Build succeeds 0 warnings, 22/22 NetArchTest rules pass. Domain zero NuGet refs, no ASP.NET Identity coupling.

### [G1] Opening Balances domain engine fix — 2026-09-21
- Fixed OpeningBalanceEntry ctor to allow transient aggregate: removed OpeningBalancePeriodId >0 validation, matches JournalEntryLine pattern allowing Id=0, EF sets FK after persistence.
- Removed excess fields from domain events for minimalism: OpeningBalanceEntryCreated now carries EntryId, CompanyId, OccurredOn only (removed AccountId); OpeningBalancesPosted now carries PeriodId, CompanyId, OccurredOn only (removed JournalEntryId); OpeningBalancePeriodCreated already minimal.
- Removed JournalEntryId from OpeningBalancesPosted event and raised event after posting with PeriodId and CompanyId only.
- Deferred entry number generation: removed OP-{Id}-{PeriodDate} pattern using Id=0; changed JournalEntry creation to use entry number $"OP-{PeriodDate:yyyyMMdd}" without Id, avoiding transient Id usage. Entry number generation can be refined in Application handler after Id assigned.
- Kept FiscalPeriodId validation, not FiscalYearId.
- EF configurations unchanged; build succeeds with 0 warnings, 22/22 NetArchTest rules pass.
### [G1] Opening Balances domain engine design — 2026-09-21
- OpeningBalancePeriod entity created in src/SmeAccounting.Domain/Entities/OpeningBalancePeriod.cs extending BaseEntity with CompanyId, FiscalPeriodId, PeriodDate, PeriodStatus, IsPosted, private parameterless ctor + public ctor validating CompanyId>0 and FiscalPeriodId>0, AddEntry method validates open status, account uniqueness, debit/credit invariants, PostOpeningBalances validates debit=credit total, creates JournalEntry with SourceType OpeningBalance, calls JournalEntry.Post, raises OpeningBalancesPosted.
- OpeningBalanceEntry entity created in src/SmeAccounting.Domain/Entities/OpeningBalanceEntry.cs extending BaseEntity with OpeningBalancePeriodId, CompanyId, AccountId, Money Debit/Credit, Description, private parameterless ctor + public ctor validating IDs>0, non-negative amounts, currency match, domain event raised on creation.
- Domain events created: OpeningBalancePeriodCreated (PeriodId, CompanyId), OpeningBalanceEntryCreated (EntryId, CompanyId, AccountId), OpeningBalancesPosted (PeriodId, CompanyId, JournalEntryId) — minimalism pattern matching DepartmentCreated.
- Ports created: IOpeningBalancePeriodRepository with GetByIdAsync, GetByCompanyAndFiscalPeriodAsync, GetAllByCompanyAsync, AddAsync; IOpeningBalanceEntryRepository with GetByIdAsync, GetAllByPeriodAsync, GetAllByCompanyAsync, AddAsync.
- EF configurations created: OpeningBalancePeriodConfiguration maps to opening_balance_periods with snake_case columns company_id, fiscal_period_id, period_date, status (string conversion), is_posted, xmin row version, FK Restrict to Company and FiscalPeriod, unique index on (CompanyId, FiscalPeriodId). OpeningBalanceEntryConfiguration maps to opening_balance_entries with snake_case columns opening_balance_period_id, company_id, account_id, description, owned Money Debit/Credit mapped to debit_amount/debit_currency/credit_amount/credit_currency, FK Restrict to Company/Account/OpeningBalancePeriod, unique index on (CompanyId, OpeningBalancePeriodId, AccountId), xmin row version.
- Design follows existing patterns: BaseEntity domain events, DomainException validation, private EF ctor, snake_case naming, xmin concurrency, FK Restrict to Company, no navigation properties, Money owned type mapping.
- No Application/Infrastructure implementation added per scope — domain scaffolding only.

### [G1] CompanySettings domain model design — 2026-09-21
- CompanySetting entity created in src/SmeAccounting.Domain/Entities/CompanySetting.cs extending BaseEntity with CompanyId, LegalRepresentativeName, LegalRepresentativeTaxId, ChiefAccountantName, ChiefAccountantTaxId, FiscalYearStartMonth, Currency, ReportingSettingsJson. Private parameterless ctor + public ctor with DomainException validation.
- Domain event CompanySettingCreated created in src/SmeAccounting.Domain/Events/CompanySettingCreated.cs carrying SettingId, CompanyId, OccurredOn. Follows DepartmentCreated minimalism pattern.
- Port ICompanySettingRepository created in src/SmeAccounting.Domain/Ports/ICompanySettingRepository.cs with GetByIdAsync, GetByCompanyIdAsync, AddAsync.
- EF configuration CompanySettingConfiguration created in src/SmeAccounting.Infrastructure/Persistence/Configurations/CompanySettingConfiguration.cs mapping to company_settings table, snake_case columns, xmin row version, unique index on CompanyId, FK to Company with DeleteBehavior.Restrict, reporting_settings_json column mapped as jsonb.
- Design follows existing patterns: BaseEntity domain events, DomainException validation, private EF ctor, snake_case naming, xmin concurrency, FK Restrict to Company, no navigation property.
- No Application/Infrastructure implementation added yet per scope — design scaffolding only.

### [G1] CompanySettings verification — 2026-09-21
- Audit/verify result: VERIFIED_PASS 2026-09-21. Build succeeded, 22 NetArchTest rules passed.
- Patterns confirmed by audit:
  - BaseEntity: private parameterless ctor present, public ctor validates via DomainException, domain events added via AddDomainEvent.
  - Clean Architecture: Domain entities/ports/events zero NuGet refs, no Infrastructure/App references, no ASP.NET Identity coupling.
  - EF config: table company_settings, snake_case columns legal_representative_name/tax_id/chief_accountant_name/tax_id/fiscal_year_start_month/currency/reporting_settings_json, xmin row version, unique index on company_id, HasOne<Company>().WithMany().HasForeignKey(...).OnDelete(DeleteBehavior.Restrict).
  - Domain events minimalism: CompanySettingCreated carries SettingId, CompanyId, OccurredOn; matches DepartmentCreated pattern.
  - Validation uses DomainException for CompanyId>0, required LegalRepresentativeName/TaxId, FiscalYearStartMonth 1-12.
  - ReportingSettingsJson mapped as jsonb via HasColumnType("jsonb").
- Notes: Event created with Id at construction yields Id=0 (consistent with codebase pattern for Company, Department, etc.). No blocking violations.
- What was built: domain scaffolding only — entity, event, port, EF configuration. Application/Infrastructure handlers not implemented per scope.
- Design decisions confirmed: 1:1 CompanySetting per Company via unique CompanyId index, Legal Representative/Chief Accountant as scalar fields, FiscalYearStartMonth scalar, Currency string code, reporting extension as jsonb, no navigation property to Company, FK Restrict consistent with FK-to-Company pattern.

### [G1] Opening Balances fix — consolidated learnings & audit verification — 2026-09-21
- What changed:
  - OpeningBalanceEntry constructor validation removed for OpeningBalancePeriodId >0; transient aggregate Id=0 now allowed, matching JournalEntryLine pattern where EntryId=0 is accepted and EF populates FK on save.
  - Domain events minimized to EntityId + CompanyId + OccurredOn:
    - OpeningBalancePeriodCreated: PeriodId, CompanyId
    - OpeningBalanceEntryCreated: EntryId, CompanyId (AccountId removed)
    - OpeningBalancesPosted: PeriodId, CompanyId (JournalEntryId removed)
  - Entry number generation deferred from domain: removed `OP-{Id}-{PeriodDate:yyyyMMdd}` using Id=0; JournalEntry created with number `"OP-{PeriodDate:yyyyMMdd}"` without Id, final numbering to be refined in Application handler after Id assigned.
  - FiscalPeriodId validation retained; FiscalYearId not used.
- Design decisions confirmed:
  - Transient aggregate pattern: child entities accept parent Id=0, EF Core sets FK on persistence; consistent with codebase transient Id usage for Company, Department, JournalEntryLine.
  - Domain event minimalism: events carry only identifying IDs and timestamp, no duplicate entity data; matches DepartmentCreated/CompanyCreated pattern.
  - No domain-level identifier formatting: entry numbers generated after persistence in Application layer, avoiding Id=0 usage.
  - Posting integration remains in domain: OpeningBalancePeriod.PostOpeningBalances validates period open, debit=credit total, creates JournalEntry with SourceType OpeningBalance, calls JournalEntry.Post, raises OpeningBalancesPosted with minimal payload.
- Patterns confirmed by audit/verify:
  - Build: `dotnet build SmeAccounting.sln` succeeds with 0 warnings, 0 errors.
  - Architecture tests: 22/22 NetArchTest rules pass.
  - Transient aggregate: OpeningBalanceEntry constructor accepts OpeningBalancePeriodId=0 without DomainException.
  - Domain events minimalism verified: OpeningBalancePeriodCreated (PeriodId, CompanyId), OpeningBalanceEntryCreated (EntryId, CompanyId), OpeningBalancesPosted (PeriodId, CompanyId).
  - No JournalEntryId in OpeningBalancesPosted event.
  - Entry number generation does not use Id=0.
  - FiscalPeriodId validation retained.
  - EF configurations correct: tables opening_balance_periods / opening_balance_entries with snake_case columns, xmin row version, FK Restrict to Company/FiscalPeriod/Account/OpeningBalancePeriod, unique indexes (CompanyId, FiscalPeriodId) and (CompanyId, OpeningBalancePeriodId, AccountId).
  - Clean Architecture purity maintained: Domain zero NuGet refs, no Infrastructure/App references, private parameterless ctor for EF, public ctor with DomainException validation, BaseEntity domain events.
- Implications:
  - Opening Balances domain engine scaffold is build-verified and architecturally compliant; ready for Application/Infrastructure implementation in subsequent G2 phase.
  - Event minimalism pattern now enforced across Opening Balances, CompanySettings, and existing entities.

### [G1] User Management domain redesign — consolidated learnings — 2026-09-21
- Redesign summary:
  - Initial design: User company-scoped with CompanyId, Email unique per company, UserCreated event carried CompanyId.
  - Fix applied: User redesigned global identity-agnostic. CompanyId removed from User. Mandatory ExternalId added for Microsoft Entra ObjectId mapping. Email unique globally.
  - Domain events minimalism enforced: UserCreated carries UserId only (no CompanyId). CompanyMembershipCreated event added and raised on construction with MembershipId + CompanyId + OccurredOn.
  - IUsersRepository redesigned to global queries: GetByExternalIdAsync, GetByEmailAsync, GetAllAsync (no company filter). Role remains company-scoped.
- EF configuration changes:
  - UserConfiguration: table users, columns external_id, email, display_name, user_name, is_active, xmin. Unique indexes on external_id and email separately. CompanyId FK removed.
  - CompanyMembershipConfiguration: FK Restrict to User and Company, unique index (user_id, company_id).
  - UserRoleConfiguration: FK Restrict to Company/User/Role, unique index (user_id, role_id, company_id).
  - Role remains company-scoped with CompanyId, Code, Name, unique index (company_id, code).
- Patterns confirmed:
  - Clean Architecture: Domain zero NuGet refs, no ASP.NET Identity coupling, no EF Core refs, no Infrastructure/App refs.
  - Domain purity: private parameterless ctor for EF, public ctor with DomainException validation, BaseEntity domain events.
  - FK Restrict to Company universal, no navigation properties on entities.
  - Snake_case tables/columns, xmin row version, composite unique indexes for per-company uniqueness on Role/CompanyMembership/UserRole.
  - Domain events minimalism: UserCreated(UserId), RoleCreated(RoleId+CompanyId), UserRoleAssigned(UserRoleId+CompanyId), CompanyMembershipCreated(MembershipId+CompanyId).
  - Authentication/authorization separation: passwords/credentials not stored in Domain; Microsoft sign-in integration handled by Infrastructure adapter.
- Decisions:
  - User global for Microsoft-first sign-in; ExternalId mandatory, Email globally unique.
  - CompanyMembership as explicit link aggregate between global User and Company.
  - Role company-scoped; UserRole per-company assignment.
  - No password hash/secrets in Domain.
  - Build verified 0 warnings, 22/22 NetArchTest rules pass.

### [G2] CompanySettings Application + Infrastructure implemented — 2026-09-21
- DbSet<CompanySetting> added to SmeAccountingDbContext.CompanySettings, CompanySettingCreated ignored in OnModelCreating.
- EfCompanySettingRepository created implementing ICompanySettingRepository with GetByIdAsync, GetByCompanyIdAsync, AddAsync using DbContext.
- Application layer: CreateCompanySettingCommand record + CreateCompanySettingResult, CreateCompanySettingCommandValidator with FluentValidation rules, CreateCompanySettingHandler using ICompanySettingRepository and IUnitOfWork.
- Queries: GetCompanySettingByIdQuery, GetCompanySettingByCompanyIdQuery with handlers returning CompanySettingDto.
- DTO CompanySettingDto record created per entity properties.
- DI registration: ICompanySettingRepository -> EfCompanySettingRepository added to Infrastructure DependencyInjection.
- Build verified: dotnet build SmeAccounting.sln succeeds 0 warnings 0 errors.
- Architecture tests: 22/22 NetArchTest rules pass.
- Patterns followed: MediatR IRequest handlers, FluentValidation pipeline, DTO records without domain references, repository pattern with async EF Core, DbContext unit of work.

### [G2] CompanySettings Application + Infrastructure consolidated learnings — 2026-09-21
- DbContext: DbSet<CompanySetting> CompanySettings exposed, CompanySettingCreated ignored in OnModelCreating.
- Infrastructure: EfCompanySettingRepository implements ICompanySettingRepository with GetByIdAsync (FirstOrDefaultAsync), GetByCompanyIdAsync (FirstOrDefaultAsync), AddAsync (DbSet.AddAsync). No UpdateAsync — change tracking handles updates.
- DI: services.AddScoped<ICompanySettingRepository, EfCompanySettingRepository> in Infrastructure DependencyInjection.
- Application Command: CreateCompanySettingCommand record with CompanyId, LegalRepresentativeName, LegalRepresentativeTaxId, optional ChiefAccountantName/TaxId, FiscalYearStartMonth, Currency, ReportingSettingsJson : IRequest<CreateCompanySettingResult>. CreateCompanySettingResult record with Id.
- Application Handler: CreateCompanySettingHandler sealed class primary ctor (ICompanySettingRepository, IUnitOfWork). Creates CompanySetting via domain public ctor, repo.AddAsync, unitOfWork.SaveChangesAsync, returns Id. DomainException validation executed in entity ctor.
- Validation: CreateCompanySettingCommandValidator FluentValidation: CompanyId >0, LegalRepresentativeName not empty max200, LegalRepresentativeTaxId not empty max50, ChiefAccountantName max200, ChiefAccountantTaxId max50, FiscalYearStartMonth inclusive 1-12 when present, Currency max3 when present.
- Queries: GetCompanySettingByIdQuery(long Id) : IRequest<CompanySettingDto?>, GetCompanySettingByCompanyIdQuery(long CompanyId) : IRequest<CompanySettingDto?>. Handlers map entity to DTO manually, no AutoMapper.
- DTO: CompanySettingDto record with Id, CompanyId, LegalRepresentativeName, LegalRepresentativeTaxId, ChiefAccountantName?, ChiefAccountantTaxId?, FiscalYearStartMonth?, Currency?, ReportingSettingsJson?. No domain references.
- Patterns confirmed: MediatR IRequest handlers, FluentValidation pipeline via ValidationBehavior, DTO records, repository async EF Core, Unit of Work SaveChangesAsync, domain events raised on entity construction, Clean Architecture purity maintained.
- Build verification: dotnet build SmeAccounting.sln succeeds 0 warnings 0 errors, 22/22 NetArchTest rules pass.
