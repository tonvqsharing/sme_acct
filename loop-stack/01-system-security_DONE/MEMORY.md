# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
### 2026-09-21 G1 Company/CompanySetting design verification
- Company entity updated to use DomainException for validation: Name, TaxCode, Address, FunctionalCurrencyCode required non-empty; FiscalYearStartMonth 1-12; FiscalYearStartDay 1-28. Removed ArgumentNullException/ArgumentOutOfRangeException for consistency with CompanySetting and domain exception hierarchy.
- Company follows BaseEntity pattern: private parameterless ctor for EF, public validating ctor, AddDomainEvent(new CompanyCreated(Id, DateTimeOffset.UtcNow)).
- CompanySetting entity already compliant: private parameterless ctor, public ctor validates CompanyId>0, LegalRepresentativeName/TaxId required, FiscalYearStartMonth 1-12 if provided, throws DomainException. Raises CompanySettingCreated(Id,CompanyId,OccurredOn).
- Domain events minimalism confirmed: CompanyCreated carries CompanyId + OccurredOn (base), CompanySettingCreated carries SettingId + CompanyId + OccurredOn.
- Ports exist: ICompanyRepository (GetByIdAsync, GetByTaxCodeAsync, GetAllAsync, AddAsync), ICompanySettingRepository (GetByIdAsync, GetByCompanyIdAsync, AddAsync).
- EF configurations compliant:
  - CompanyConfiguration: table companies, snake_case columns, unique index tax_code, xmin row version, no FK.
  - CompanySettingConfiguration: table company_settings, snake_case columns, unique index company_id, HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(DeleteBehavior.Restrict), ReportingSettingsJson column type jsonb, xmin row version.
- VAS compliance fields present: Company TaxCode, Address, FiscalYearStartMonth/Day, FunctionalCurrencyCode; CompanySetting LegalRepresentativeName/TaxId, ChiefAccountantName/TaxId, FiscalYearStartMonth, Currency, ReportingSettingsJson for VAS reporting.
- Company isolation pattern confirmed: CompanySetting FK Restrict to Company, unique index on CompanyId ensures 1:1 per company. No navigation properties exposed.
- Build verified: Domain project builds with 0 warnings.

### 2026-09-21 G1 CompanyMembership/User/Role design verification
- Entities follow BaseEntity pattern: private parameterless ctor for EF, public ctor with DomainException validation, AddDomainEvent in ctor.
- User global: no CompanyId, ExternalId mandatory validated non-empty, Email trimmed lowercased, DisplayName required, UserCreated event carries UserId only.
- Role company-scoped: CompanyId>0, Code/Name required, RoleCreated event carries RoleId+CompanyId.
- CompanyMembership linking aggregate: UserId>0, CompanyId>0, JoinedAt set UtcNow, CompanyMembershipCreated event carries MembershipId+CompanyId.
- UserRole per-company assignment: UserId>0, RoleId>0, CompanyId>0, UserRoleAssigned event carries UserRoleId+CompanyId.
- Domain events minimalism confirmed: all events carry EntityId + CompanyId (+OccurredOn) only, no payload duplication; UserCreated carries UserId only.
- Ports exist and match pattern: IUsersRepository GetByIdAsync/GetByExternalIdAsync/GetByEmailAsync/GetAllAsync/AddAsync; IRoleRepository GetByIdAsync/GetByCompanyAndCodeAsync/GetAllByCompanyAsync/AddAsync; ICompanyMembershipRepository AddAsync; IUserRoleRepository AddAsync.
- EF configurations compliant snake_case/xmin/FK Restrict:
  - UserConfiguration: table users, external_id unique, email unique, xmin row version, no CompanyId.
  - RoleConfiguration: table roles, company_id FK Restrict to Company, unique index (company_id,code), xmin.
  - CompanyMembershipConfiguration: table company_memberships, unique index (user_id,company_id), FK Restrict to Company and User, xmin.
  - UserRoleConfiguration: table user_roles, unique index (user_id,role_id,company_id), FK Restrict to Company/User/Role, xmin.
- Repositories implemented: EfUsersRepository, EfRoleRepository, EfCompanyMembershipRepository, EfUserRoleRepository follow async AddAsync pattern with AsNoTracking for reads.
- DbContext includes DbSet<User>, DbSet<Role>, DbSet<CompanyMembership>, DbSet<UserRole> and ignores domain events.
- Uniqueness enforced: User ExternalId and Email globally unique; Role unique per company (CompanyId,Code); CompanyMembership unique per user/company; UserRole unique per user/role/company.
- Build verified: domain entities compile, 22 NetArchTest rules pass, Clean Architecture maintained, no Domain NuGet refs, no ASP.NET Identity coupling.

### 2026-09-21 G1 DocumentNumberingSeries/VoucherType/TransactionReason design verification
- Entities extend BaseEntity with private parameterless ctor for EF and public validating ctor using DomainException.
- DocumentNumberingSeries: CompanyId>0, VoucherTypeId>0, Prefix required non-empty, PaddingLength 1-10 validated. Properties NextNumber, PaddingLength, IsDefault, IsActive, Description. Methods Increment(), Reset(startFrom>0) with DomainException, Deactivate(). No domain event raised on creation (design gap vs VoucherType/TransactionReason). Concurrency-safe numbering relies on optimistic concurrency via xmin row version; Increment must occur within same EF transaction with row version check to avoid lost updates. Unique index (VoucherTypeId,CompanyId,Prefix) enforced.
- VoucherType: CompanyId>0, Code/Name required. VoucherCategory enum stored as string. Raises VoucherTypeCreated(Id,CompanyId,UtcNow) on construction. Deactivate() sets IsActive false. Event minimalism confirmed: VoucherTypeId + CompanyId + OccurredOn.
- TransactionReason: CompanyId>0, VoucherTypeId>0, Code/Name required. Raises TransactionReasonCreated(Id,CompanyId,UtcNow) on construction. Deactivate() sets IsActive false. Event minimalism confirmed: TransactionReasonId + CompanyId + OccurredOn.
- EF configurations compliant snake_case/xmin/FK Restrict:
  - DocumentNumberingSeriesConfiguration: table document_numbering_series, columns snake_case, unique index (voucher_type_id,company_id,prefix), HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(Restrict), HasOne<VoucherType>().WithMany().HasForeignKey(VoucherTypeId).OnDelete(Restrict), xmin row version.
  - VoucherTypeConfiguration: table voucher_types, columns snake_case, unique index (company_id,code), HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(Restrict), VoucherCategory HasConversion<string>(), xmin row version.
  - TransactionReasonConfiguration: table transaction_reasons, columns snake_case, unique index (company_id,code), HasOne<Company>().WithMany().HasForeignKey(CompanyId).OnDelete(Restrict), HasOne<VoucherType>().WithMany().HasForeignKey(VoucherTypeId).OnDelete(Restrict), xmin row version.
- Validation uses DomainException consistently, private parameterless ctor present, properties private set.
- Domain events minimalism observed for VoucherType and TransactionReason; DocumentNumberingSeries lacks creation event, recommend adding DocumentNumberingSeriesCreated(Id,CompanyId) for consistency.
- Build verified: entities compile, 22 NetArchTest rules pass, Clean Architecture maintained.

### 2026-09-21 Infrastructure Identity components verification
- IdentityUserAdapter present at src/SmeAccounting.Infrastructure/Adapters/IdentityUserAdapter.cs with static mapping ToIdentityUser(User) and ToDomainUser(IdentityUserModel). Adapter uses Domain Entities.User only; no ASP.NET Identity package dependency; IdentityUserModel is a local record placeholder.
- MicrosoftSignInProvider stub present at src/SmeAccounting.Infrastructure/Adapters/MicrosoftSignInProvider.cs implementing IMicrosoftSignInProvider with ValidateTokenAsync and GetExternalIdAsync placeholder returning token presence check and null external id.
- DI registration present in src/SmeAccounting.Infrastructure/DependencyInjection.cs line 73: services.AddScoped<IMicrosoftSignInProvider, MicrosoftSignInProvider>().
- Domain clean: SmeAccounting.Domain contains no references to IdentityUserAdapter, MicrosoftSignInProvider, Infrastructure namespace, or 'Identity'; Domain.csproj has zero package references; grep for Identity returns no results in Domain.
- Clean Architecture maintained; Infrastructure depends on Domain, Domain has no external dependencies.

### 2026-09-21 System Security loop updates
- ArchitectureTests passed 22/22: `dotnet test tests/SmeAccounting.ArchitectureTests/` reports Passed! - Failed: 0, Passed: 22, Skipped: 0.
- Seed defaults documentation created at docs/seed-system-security-defaults.md covering VoucherType, TransactionReason, DocumentNumberingSeries defaults per company with implementation notes for CreateCompanyWithDefaultsCommandHandler.
- IdentityUserAdapter fix applied: ToDomainUser now correctly maps IdentityUserModel.UserName to User.UserName and derives DisplayName from UserName with fallback to Email, matching User ctor signature User(externalId, email, displayName, userName).

