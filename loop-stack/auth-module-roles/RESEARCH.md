# Research Findings

## Context & Prior Work

### Global Project Conventions
- Target .NET 10 LTS net10.0, ASP.NET Core 10, EF Core 9 via Pomelo for MariaDB
- Clean Architecture + Modular Monolith, 4-layer standard Domain/Application/Infrastructure/Api
- CQRS via MediatR, FluentValidation pipeline
- MariaDB 10.6+ LTS, utf8mb4
- Testing xUnit v3 + MTP runner, NSubstitute, AwesomeAssertions, NetArchTest
- Naming prefix SmeAccounting.*

### Module Structure
Modules under /home/projects/sme_acct/src/Modules/
12 modules registered in Api Program.cs:
Identity, Authorization, Organization, MasterData, Audit, ChartOfAccounts, AccountingPeriod, Journal, Posting, GeneralLedger, Tax, FinancialReporting

Module pattern:
- Each module has Domain/Application/Infrastructure sub-projects
- Domain csproj references SmeAccounting.Domain + SmeAccounting.SharedKernel
- Application csproj references Domain + SmeAccounting.Application + SharedKernel + MediatR
- Infrastructure csproj references Application, implements IModule with AddModule returning IServiceCollection
- Module registration via AddModules([...]) in Program.cs, explicit list, no reflection
- Module Infrastructure contains AuthorizationModule.cs with AddMediatR(RegisterServicesFromAssemblyContaining<*ApplicationMarker>)

### Authorization Module Current State
Path: src/Modules/Authorization/
- Domain/SmeAccounting.Modules.Authorization.Domain.csproj exists, no source files found
- Application/SmeAccounting.Modules.Authorization.Application.csproj exists, contains AuthorizationApplicationMarker.cs only
- Infrastructure/SmeAccounting.Modules.Authorization.Infrastructure.csproj exists, contains AuthorizationModule.cs and AuthorizationModuleExtensions.cs
- AuthorizationModule.AddModule registers MediatR from assembly containing AuthorizationApplicationMarker
- No domain entities, no application services, no infrastructure implementations present yet

### Identity Module Implementation
Path: src/Modules/Identity/
Domain:
- Role.cs, User.cs in Domain project
- Role: BaseEntity with Name, NormalizedName, Description, DisplayOrder
- User: BaseEntity with DisplayName, Email, UserName, BranchId, IsEnabled, audit fields, password hash, lockout logic

Application:
- Permissions.cs static class with nested modules Accounts, Journal, Reports, Settings, Users, Audit. All permissions format "module.action"
- PermissionPolicyProvider implements IAuthorizationPolicyProvider, intercepts "Permission:{name}" → PermissionRequirement
- PermissionAuthorizationHandler grants if user has permission or Users.ManageRoles admin bypass
- ClaimsPrincipalExtensions: GetUserId, GetDisplayName, GetBranchId, GetPermissions, HasPermission

Infrastructure:
- ApplicationUser, ApplicationRole extend Identity classes
- IdentityDbContext extends IdentityDbContext<ApplicationUser, ApplicationRole, long> with snake_case naming
- IdentityDbContextFactory for design-time
- RoleSeeder with StandardRoles: Admin, ChiefAccountant, Accountant, Viewer, Auditor with permission sets
- UserSeeder
- IdentityModule registers services

csproj references:
- Domain → SmeAccounting.Domain + SharedKernel
- Application → Domain + SmeAccounting.Application + SharedKernel + FrameworkReference Microsoft.AspNetCore.App + MediatR
- Infrastructure → Application + Domain + FrameworkReference Microsoft.AspNetCore.App + Microsoft.AspNetCore.Identity.EntityFrameworkCore + EF Core + Npgsql

### Existing Tests
tests/SmeAccounting.Security.Tests/PermissionTests.cs
- Validates Permissions.All non-empty, format, module view permissions, Admin role has all permissions, Viewer only view, constants unique
- Uses RoleSeeder.StandardRoles

Architecture tests enforce layer rules, module domain no infrastructure dependency, controllers IL size <1000, entities have audit fields

### Package Files & Conventions
- Directory.Packages.props central versioning, locked mode
- .slnx format, UseArtifactsOutput=true
- TreatWarningsAsErrors, AnalysisLevel latest-recommended
- FrameworkReference Microsoft.AspNetCore.App used for ASP.NET Core services in net10.0 libs
- MediatR 12.5.0 pinned
- Module marker pattern used for MediatR assembly scanning

### Patterns Observed
- Permission authorization types belong in Application layer, not Infrastructure
- PermissionPolicyProvider intercepts Permission:* policy strings
- Admin bypass via Users.ManageRoles permission
- Claims "permission" used for role claims
- Snake_case naming enforced via EF Core converter
- Soft delete, audit fields via interfaces
- Module registration explicit in Program.cs

## External Knowledge & Resources

### README.md
- Tech stack: ASP.NET Core 9, EF Core 9 + Npgsql 9, PostgreSQL 16.14, ASP.NET Core Identity cookie auth, MediatR, FluentValidation, Serilog, xUnit + NSubstitute + Testcontainers
- Architecture Clean Architecture + Modular Monolith, 12 MVP modules
- Quick start: dotnet restore, create DB, export SME_ACCT_CONNECTION_STRING, dotnet ef database update, dotnet run --project src/SmeAccounting.Api
- App URL http://localhost:5000
- Default login admin@smeaccounting.vn / Admin@12345, override via ADMIN_PASSWORD env var
- Modules list: Identity, Authorization, Organization, MasterData, Audit, ChartOfAccounts, AccountingPeriod, Journal, Posting, GeneralLedger, Tax, FinancialReporting
- Docs links: architecture.md, modules.md, database.md, security.md, deployment.md, testing.md, ADR-001

### docs/security.md
- Identity config: Password RequireDigit/Lowercase/Uppercase/NonAlphanumeric, RequiredLength 8, Lockout 5 attempts/15 min, RequireUniqueEmail, RequireConfirmedEmail
- Cookie settings: LoginPath /Accounts/Login, LogoutPath /Accounts/Logout, AccessDeniedPath /Accounts/AccessDenied, ExpireTimeSpan 8h, SlidingExpiration true, HttpOnly true, SameSite Lax, SecurePolicy SameAsRequest
- User/Role models: ApplicationUser extends IdentityUser<long> with DisplayName, BranchId, IsEnabled, CreatedAtUtc, LastLoginAtUtc; ApplicationRole extends IdentityRole<long> with Description, DisplayOrder
- IdentityDbContext separate, snake_case naming applied
- RBAC Permissions 19 defined in src/SmeAccounting.Infrastructure/Identity/Permissions.cs:
  Accounts: accounts.view, accounts.create, accounts.edit, accounts.delete
  Journal: journal.view, journal.create, journal.edit, journal.post, journal.reverse
  Reports: reports.view, reports.export
  Settings: settings.view, settings.manage
  Users: users.view, users.create, users.edit, users.delete, users.manage_roles
  Audit: audit.view
- Roles seeded by RoleSeeder: Admin (all 19), ChiefAccountant (Accounts+Journal+Reports+Settings), Accountant (Accounts view/create/edit + Journal view/create/edit + Reports.view), Viewer (Accounts.view + Journal.view + Reports.view + Audit.view), Auditor (Audit.view + Accounts.view + Journal.view + Reports view/export)
- Permissions stored as "permission" claims on roles
- Authorization pipeline: PermissionPolicyProvider intercepts "Permission:{name}" → PermissionRequirement; PermissionAuthorizationHandler checks permission claims, admin bypass for users.manage_roles
- Usage: [Authorize(Policy = "Permission:accounts.view")]
- ClaimsPrincipalExtensions: GetUserId, GetDisplayName, GetBranchId, GetPermissions, HasPermission
- Default seeded user admin@smeaccounting.vn / Admin@12345, EmailConfirmed true, Role Admin
- Data protection keys persisted to filesystem Security:DataProtectionPath or ./dataprotection-keys
- Security headers: X-Content-Type-Options nosniff, X-Frame-Options DENY, X-XSS-Protection 1; mode=block, Referrer-Policy strict-origin-when-cross-origin, CSP default-src 'self', HSTS max-age 31536000 excludes /health
- Antiforgery default enabled
- ForwardedHeaders configured for Nginx reverse proxy
- GlobalExceptionMiddleware catches unhandled exceptions
- SecurityOptions: LockoutMaxAttempts 5, LockoutDurationMinutes 15, DataProtectionPath ./dataprotection-keys

### docs/modules.md
- MVP modules 12, all scaffolded, registered in Program.cs
- Module structure: each module has Domain/Application/Infrastructure sub-projects
- Application references MediatR, FluentValidation
- Infrastructure implements IModule, registers MediatR from assembly
- Domain zero external deps beyond SharedKernel
- Module registration pattern: {Name}Module : IModule AddModule → AddMediatR(RegisterServicesFromAssemblyContaining<{Name}ApplicationMarker>)
- Extension Add{Name}Module()
- Isolation rules: modules communicate via MediatR, no direct assembly refs, Domain must not reference Infrastructure, cross-module entities via shared DbContext, Application marker used for MediatR registration
- Phase 2 modules: Inventory, Payroll, FixedAssets, Budgeting, Banking
- Future modules: MultiCurrency, InterCompany, DocumentManagement, Workflow, Integration, Reporting, Notification
- Sealed decisions: no inter-module project refs, module marker pattern, IModule registration via AddModules(), shared DbContext for MVP

### docs/architecture.md
- Clean Architecture + Modular Monolith, single deployable
- Layer dependency: Api → Application → Domain → SharedKernel; Infrastructure referenced by Api/Application
- Project layout: SharedKernel, Domain, Application, Infrastructure, Api, Modules/*
- SharedKernel primitives: BaseEntity long Id, Result<T>, IDomainEvent, IAuditable, ISoftDeletable, ICompanyScoped, IRepository, IUnitOfWork, ICurrentUserProvider, IDateTimeProvider
- IModule interface with AddModule(IServiceCollection)
- Composition root Program.cs AddModules([...]) explicit list
- ModulesAddExtensions iterates IModule collection
- Module internal structure Domain/Application/Infrastructure
- Infrastructure DI composition AddInfrastructure(): Persistence SmeAccountingDbContext with Npgsql retry 30s, Identity + RBAC, Serilog console+rolling file 14-day retention, Health checks PostgreSQL+EF, Localization vi-VN default, AuditLoggingService, SystemDateTimeProvider, HttpContextCurrentUserProvider, FluentValidation pipeline, LocalFileStorage, DataProtection, ForwardedHeaders
- Request pipeline: ForwardedHeaders → RequestLocalization → GlobalExceptionHandler → Routing → Authorization → Controller → MediatR Pipeline → ValidationBehaviour → Handler → Response
- Health endpoints bypass auth /health/live, /health/ready
- Design decisions: MediatR over messaging, Cookie auth over JWT, bigint PKs over UUID, xmin concurrency tokens, snake_case DB naming via custom converter

### docs/database.md
- Engine PostgreSQL 16.14 Alpine, EF Core 9.0.0 + Npgsql 9.0.0
- Connection string DefaultConnection appsettings, fallback SME_ACCT_CONNECTION_STRING env var
- Naming convention snake_case enforced by SmeAccountingDbContext.ApplySnakeCaseNamingConvention()
- Primary keys bigint GENERATED BY DEFAULT AS IDENTITY, BaseEntity.Id long, EF annotation NpgsqlValueGenerationStrategy.IdentityByDefaultColumn
- Concurrency token PostgreSQL xmin shadow property, IsConcurrencyToken true, BeforeSaveBehavior.Ignore, AfterSaveBehavior.Ignore
- Audit fields IAuditable: CreatedAtUtc, CreatedBy, UpdatedAtUtc, UpdatedBy
- Soft delete ISoftDeletable: IsDeleted, DeletedAtUtc, DeletedBy, global query filter IsDeleted == false
- Tenant isolation ICompanyScoped CompanyId
- Decimal precision numeric(18,2) default
- PostgreSQL extension uuid-ossp enabled
- Migrations: InitialFoundationXminV3 core schema, Circular133COASeed Vietnamese COA 98 accounts
- Commands dotnet ef migrations add/update/script with project src/SmeAccounting.Infrastructure startup src/SmeAccounting.Api
- Migration policy fail-fast on pending migrations, DesignTimeDbContextFactory reads SME_ACCT_CONNECTION_STRING, idempotent-safe
- Seeds: Company Demo Company id1, Branch Head Office id1 CompanyId1, COA seed 98 accounts classes 1-9, Identity seeds roles Admin/ChiefAccountant/Accountant/Viewer/Auditor, user admin@smeaccounting.vn / Admin@12345
- Entities Company BaseEntity IAuditable ISoftDeletable, Branch BaseEntity IAuditable ISoftDeletable ICompanyScoped, Account BaseEntity IAuditable ISoftDeletable ICompanyScoped with code, name, account_type, level, parent_id, normal_balance, is_active
- Backup pg_dump -Fc, pg_restore

### docs/deployment.md
- Linux Nginx + systemd config examples
- Environment variables: ConnectionStrings__DefaultConnection, ADMIN_PASSWORD, SME_ACCT_CONNECTION_STRING, Security__DataProtectionPath
- Production secrets via systemd Environment or /etc/default/smeaccounting, Docker secrets, .env not committed
- appsettings hierarchy appsettings.json, appsettings.{Environment}.json sections ConnectionStrings, Serilog, Security, RequestLocalization
- Zero-downtime rolling restart: apply migrations first backwards-compatible, deploy binaries, restart, verify health
- Migration safety additive-only, default values, rename via add-new copy drop-old
- Health checks /health/live liveness, /health/ready readiness
- Build steps restore, build, test, publish to artifacts/publish

### Directory.Packages.props
- CentralPackageTransitivePinningEnabled true, ManagePackageVersionsCentrally true
- Packages: MediatR 12.5.0, FluentValidation 12.1.1, FluentValidation.DependencyInjectionExtensions 12.1.1, Microsoft.AspNetCore.Identity.EntityFrameworkCore 10.0.12, Microsoft.EntityFrameworkCore 10.0.12, Microsoft.EntityFrameworkCore.Design 10.0.12, Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3, Serilog.AspNetCore 10.0.0, Serilog.Formatting.Compact 3.0.0, Serilog.Sinks.Async 2.1.0, Serilog.Sinks.Seq 9.1.0, Serilog.Enrichers.Environment 3.0.1, Serilog.Enrichers.Thread 4.0.0, Serilog.Enrichers.Process 3.0.0, Serilog.Exceptions 8.4.0, AspNetCore.HealthChecks.NpgSql 9.0.0, Microsoft.Extensions.Diagnostics.HealthChecks 10.0.12, Microsoft.Extensions.Diagnostics.HealthChecks.EntityFrameworkCore 10.0.12, xunit.v3 4.0.0, NSubstitute 6.2.0, AwesomeAssertions 9.6.0, NetArchTest.Rules 1.3.2, Microsoft.AspNetCore.Mvc.Testing 10.0.12, Testcontainers.PostgreSql 4.15.0, Testcontainers.XunitV3 4.15.0, Respawn 7.0.0

### Configs & Env
- No appsettings*.json files found in repo; configuration via environment variables per deployment docs
- Env examples from deployment.md: ConnectionStrings__DefaultConnection, ADMIN_PASSWORD, SME_ACCT_CONNECTION_STRING, Security__DataProtectionPath
- global.json SDK 10.0.401 rollForward latestFeature, test.runner Microsoft.Testing.Platform
- No .env.example file present

### Provider Selection
- Database provider Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3 for PostgreSQL 16.14
- Identity provider Microsoft.AspNetCore.Identity.EntityFrameworkCore 10.0.12 with cookie authentication
- Authorization provider ASP.NET Core Authorization with custom PermissionPolicyProvider and PermissionAuthorizationHandler
- Logging Serilog with sinks Async, Seq, console, file
- Health checks AspNetCore.HealthChecks.NpgSql

### Seed Patterns
- EF Core SeedData() for Company and Branch demo data
- Migration Circular133COASeed for chart of accounts
- RoleSeeder for 5 roles with permission claims
- UserSeeder for admin user with password override via ADMIN_PASSWORD env var
- Seeds use anonymous types to include xmin shadow property
- Migrations idempotent-safe, fail-fast check in Program.cs

## Requirements & Constraints

### DB Schema & Provider
- Engine PostgreSQL 16.14 Alpine, EF Core 10.0.12, Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3
- DbProviderSelector resolves DatabaseProvider from config `Database:Provider`, defaults PostgreSql
- Connection string priority: `Database:ConnectionString` > `SME_ACCT_CONNECTION_STRING` env > `SME_ACCT_CONNECTION_STRING` env var > appsettings `ConnectionStrings:DefaultConnection`
- Configure via `DbProviderSelector.Configure` with retry, timeout, MigrationsAssembly set to current assembly
- Migrations centralized in `src/SmeAccounting.Infrastructure/Migrations`:
  - `20260914031632_InitialFoundationXminV3` creates tables `accounts`, `audit_log_entries`, `companies`, `branches` with snake_case columns, bigint identity PK, xmin concurrency column
  - `20260914032154_Circular133COASeed` seeds Vietnamese COA
- Identity tables managed by separate `IdentityDbContext` extending `IdentityDbContext<ApplicationUser, ApplicationRole, long>` with snake_case naming applied in `OnModelCreating`
- Naming convention snake_case enforced by `SmeAccountingDbContext.ApplySnakeCaseNamingConvention()`:
  - Table names, column names, FK constraint names converted via `ToSnakeCase`
  - IdentityDbContext applies same conversion via `ToSnakeCase`
- Primary keys: `bigint GENERATED BY DEFAULT AS IDENTITY`, `BaseEntity.Id` long, EF annotation `NpgsqlValueGenerationStrategy.IdentityByDefaultColumn`
- Concurrency: shadow property `xmin` type `xid` uint on all `BaseEntity` subtypes, `IsConcurrencyToken=true`, `BeforeSaveBehavior.Ignore`, `AfterSaveBehavior.Ignore`
- Decimal precision default `numeric(18,2)` set per entity property in `OnModelCreating`
- PostgreSQL extension `uuid-ossp` enabled via migration `AlterDatabase().Annotation("Npgsql:PostgresExtension:uuid-ossp", ",,")`
- Soft delete filter: `ISoftDeletable` entities get global query filter `IsDeleted == false` built via expression tree in `OnModelCreating`
- Audit fields via `IAuditable`: `CreatedAtUtc DateTime`, `CreatedBy Guid?`, `UpdatedAtUtc DateTime?`, `UpdatedBy Guid?`
- Soft delete fields via `ISoftDeletable`: `IsDeleted bool`, `DeletedAtUtc DateTime?`, `DeletedBy Guid?`
- Tenant isolation via `ICompanyScoped` with `CompanyId long`
- Seed data in `SmeAccountingDbContext.SeedData` for Company id1 Demo Company and Branch id1 Head Office with audit/soft-delete fields populated

### Data Models
- SharedKernel:
  - `BaseEntity` abstract with `long Id`, domain events list, `RaiseDomainEvent`, `ClearDomainEvents`
  - `IAuditable` interface with Created/Updated fields
  - `ISoftDeletable` interface with IsDeleted/DeletedAtUtc/DeletedBy
  - `ICompanyScoped` interface with `CompanyId`
  - `Result` and `Result<T>` with static factories `Success()`, `Fail(...)`, `Create`, implicit operators, `IsSuccess`, `IsFailure`, `Failures`
  - `ICurrentUserProvider` with `Guid? UserId`, `bool IsAuthenticated`
  - `IUnitOfWork` with `SaveChangesAsync`
- Infrastructure entities:
  - `Company : BaseEntity, IAuditable, ISoftDeletable` with Name, Code, IsActive, audit/soft-delete fields, `ICollection<Branch>`
  - `Branch : BaseEntity, IAuditable, ISoftDeletable, ICompanyScoped` with CompanyId, Name, Code, IsActive
  - `Account : BaseEntity, IAuditable, ISoftDeletable, ICompanyScoped` with company_id, code, name, account_type, level, parent_id, normal_balance, is_active
  - `AuditLogEntry : BaseEntity, IAuditable` with entity_name, entity_id, action, changed_by, changed_at_utc, snapshot
- Identity infrastructure:
  - `ApplicationUser : IdentityUser<long>` with `DisplayName string`, `BranchId long?`, `IsEnabled bool`, `CreatedAtUtc DateTime`, `LastLoginAtUtc DateTime?`
  - `ApplicationRole : IdentityRole<long>` with `Description string`, `DisplayOrder int`
  - Domain models `User : BaseEntity` with DisplayName, Email, UserName, BranchId, IsEnabled, CreatedAtUtc, LastLoginAtUtc, PasswordHash, FailedLoginAttempts, LockedUntilUtc, lockout methods
  - Domain `Role : BaseEntity` with Name, NormalizedName, Description, DisplayOrder
  - Mapper `ApplicationUserMapper.ToDomain` maps infrastructure to domain via reflection
- Claims:
  - Permission claims stored as claim type `"permission"` with value `module.action`
  - `ClaimsPrincipalExtensions`:
    - `GetUserId()` parses `ClaimTypes.NameIdentifier` to long?
    - `GetDisplayName()` reads `display_name` or `ClaimTypes.Name`
    - `GetBranchId()` parses `branch_id` claim to long?
    - `GetPermissions()` returns all `permission` claims
    - `HasPermission(string)` checks containment

### State Management & Authorization
- CQRS via MediatR 12.5.0, `AddMediatR` per module with `RegisterServicesFromAssemblyContaining<*ApplicationMarker>`, lifetime Scoped
- Validation via FluentValidation 12.1.1, pipeline behavior `ValidationBehaviour<TRequest,TResponse>` throws `ValidationException` on failures
- Authorization:
  - `Permissions` static class in `SmeAccounting.Modules.Identity.Application` with nested classes Accounts, Journal, Reports, Settings, Users, Audit
  - Permission format `module.action`, total 19 permissions:
    - Accounts: view, create, edit, delete
    - Journal: view, create, edit, post, reverse
    - Reports: view, export
    - Settings: view, manage
    - Users: view, create, edit, delete, manage_roles
    - Audit: view
  - `PermissionPolicyProvider : IAuthorizationPolicyProvider` intercepts policy names starting with `Permission:` case-insensitive, builds `AuthorizationPolicy` with `PermissionRequirement`
  - `PermissionRequirement : IAuthorizationRequirement` holds permission string
  - `PermissionAuthorizationHandler : AuthorizationHandler<PermissionRequirement>` succeeds if user has required permission or has `users.manage_roles` admin bypass
  - Usage: `[Authorize(Policy = "Permission:accounts.view")]`
- Role seeding:
  - `RoleSeeder.StandardRoles` defines Admin, ChiefAccountant, Accountant, Viewer, Auditor with permission sets
  - Admin gets all 19 permissions
  - ChiefAccountant gets Accounts + Journal + Reports + Settings
  - Accountant gets Accounts view/create/edit + Journal view/create/edit + Reports.view
  - Viewer gets Accounts.view + Journal.view + Reports.view + Audit.view
  - Auditor gets Audit.view + Accounts.view + Journal.view + Reports.view/export
  - Permissions stored as `"permission"` claims on roles via `RoleManager.AddClaimAsync`
- Identity configuration:
  - Password: RequireDigit, RequireLowercase, RequireUppercase, RequireNonAlphanumeric, RequiredLength 8
  - Lockout: MaxFailedAccessAttempts 5, DefaultLockoutTimeSpan 15 min
  - User: RequireUniqueEmail true, RequireConfirmedEmail true
  - Cookie: LoginPath `/Accounts/Login`, LogoutPath `/Accounts/Logout`, AccessDeniedPath `/Accounts/AccessDenied`, ExpireTimeSpan 8h, SlidingExpiration true, HttpOnly true, SameSite Lax, SecurePolicy SameAsRequest
- Current user provider:
  - `HttpContextCurrentUserProvider : ICurrentUserProvider` uses `IHttpContextAccessor`, `UserId` parsed from `ClaimTypes.NameIdentifier` as Guid?, `IsAuthenticated` from HttpContext.User.Identity
- Data protection keys persisted to filesystem path `Security:DataProtectionPath` or `./dataprotection-keys`

### Constraints & Non-Negotiables
- Clean Architecture layer rules enforced by `ArchitectureTests`:
  - SharedKernel → nothing
  - Domain → SharedKernel only
  - Application → Domain + SharedKernel
  - Infrastructure → Application + Domain + SharedKernel
  - Api → Infrastructure + Application + Modules
  - Module Domain must not reference Infrastructure
- Module structure: each module has Domain/Application/Infrastructure, `IModule` with `AddModule(IServiceCollection)`, registration via explicit `AddModules([...])` in Api, no reflection
- No module-to-module project references; communication via MediatR
- Naming: snake_case DB, PascalCase code, namespace prefix `SmeAccounting.*`
- PKs bigint identity only, no UUID PKs
- Concurrency via xmin shadow property, no app-managed version column
- Soft delete global filter mandatory for `ISoftDeletable`
- Audit fields mandatory for `IAuditable`
- Migrations fail-fast at startup, pending migrations throw
- TreatWarningsAsErrors true, AnalysisLevel latest-recommended, EnforceCodeStyleInBuild true
- FrameworkReference `Microsoft.AspNetCore.App` required for libs using ASP.NET Core services in net10.0
- Permission catalog must match docs/security.md: 19 permissions, 5 roles, policy prefix `Permission:`
- Claims type for permissions is `"permission"` lowercase
- Admin bypass via `users.manage_roles` permission check in handler
- Seed data must include xmin shadow property values
- Central package management with locked mode, all projects commit `packages.lock.json`
- Test runner Microsoft.Testing.Platform via global.json, xUnit v3 projects need `OutputType=Exe`, `UseAppHost`, `<Using Include="Xunit"/>`

## Environment & Integration

### SDK & Build
- global.json SDK 10.0.401 rollForward latestFeature, allowPrerelease false
- test.runner Microsoft.Testing.Platform
- Directory.Build.props TargetFramework net10.0, LangVersion 14.0, Nullable enable, ImplicitUsings enable, TreatWarningsAsErrors true, AnalysisLevel latest-recommended, EnforceCodeStyleInBuild true, GenerateDocumentationFile false, UseArtifactsOutput true, NoWarn NETSDK1188;CA1000;IDE0161;CA1861;CA1848;CA1873
- Directory.Packages.props ManagePackageVersionsCentrally true, CentralPackageTransitivePinningEnabled true
- Central packages: MediatR 12.5.0, FluentValidation 12.1.1, Microsoft.AspNetCore.Identity.EntityFrameworkCore 10.0.12, Microsoft.EntityFrameworkCore 10.0.12, Microsoft.EntityFrameworkCore.Design 10.0.12, Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3, Serilog.*, AspNetCore.HealthChecks.NpgSql 9.0.0, xunit.v3 4.0.0, NSubstitute 6.2.0, AwesomeAssertions 9.6.0, NetArchTest.Rules 1.3.2, Microsoft.AspNetCore.Mvc.Testing 10.0.12, Testcontainers.PostgreSql 4.15.0, Testcontainers.XunitV3 4.15.0, Respawn 7.0.0
- Build commands: dotnet restore --locked-mode, dotnet build -c Release --no-restore, dotnet test -c Release --no-build, dotnet publish src/SmeAccounting.Api/SmeAccounting.Api.csproj -c Release -o artifacts/publish
- Artifacts output to artifacts/bin/obj per UseArtifactsOutput
- .slnx format, no GUIDs, UseArtifactsOutput true

### CI/CD
- .github/workflows/ci.yml runs on push/PR to main
- runs-on ubuntu-latest
- steps: actions/checkout@v4, actions/setup-dotnet@v4 dotnet-version 10.0.x, dotnet restore --locked-mode, dotnet build -c Release --no-restore, dotnet test -c Release --no-build, dotnet publish src/SmeAccounting.Api/SmeAccounting.Api.csproj -c Release -o artifacts/publish, upload-artifact publish
- Quality gates: locked mode restore, TreatWarningsAsErrors, AnalysisLevel latest-recommended, EnforceCodeStyleInBuild

### Docker & Compose
- deploy/Dockerfile multi-stage: build from mcr.microsoft.com/dotnet/sdk:10.0, copy Directory.Build.props/targets/Packages.props, restore Api csproj, copy src/, dotnet publish -c Release -o /app/publish --no-restore
- runtime from mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled, WORKDIR /app, EXPOSE 8080, ENV ASPNETCORE_URLS=http://+:8080, DOTNET_gcServer=1, COPY --from=build /app/publish ., USER 1654, ENTRYPOINT ["dotnet","SmeAccounting.Api.dll"]
- deploy/docker-compose.yml version 3.8
- services app build context .. dockerfile deploy/Dockerfile, ports 5000:8080, environment ConnectionStrings__DefaultConnection=Host=db;Port=5432;Database=sme_accounting;Username=postgres;Password=postgres, ASPNETCORE_ENVIRONMENT=Production, depends_on db condition service_healthy, restart unless-stopped
- db image postgres:16.14-alpine, ports 5432:5432, env POSTGRES_DB/USER/PASSWORD, volumes pgdata:/var/lib/postgresql/data, healthcheck pg_isready -U postgres interval 5s timeout 5s retries 5

### EF Migrations & Scripts
- scripts/ef-migrations.sh bundle|script
- bundle: dotnet ef migrations bundle --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api --output artifacts/migrations bundle --force
- script: dotnet ef migrations script --idempotent --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api --output artifacts/sql/migrations.sql
- Design-time factory reads SME_ACCT_CONNECTION_STRING env var
- Program.cs fail-fast: if not Testing env, create scope, get SmeAccountingDbContext, throw if GetPendingMigrations().Any()
- Migration commands: dotnet ef migrations add {Name} --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api, dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api

### Environment Variables & Configuration Priority
- DbProviderSelector.ResolveConnectionString priority:
  1. configuration["Database:ConnectionString"]
  2. configuration["SME_ACCT_CONNECTION_STRING"]
  3. Environment.GetEnvironmentVariable("SME_ACCT_CONNECTION_STRING")
  4. provider switch default: PostgreSql → configuration.GetConnectionString("DefaultConnection") ?? "Host=localhost;Port=5432;Database=smeaccounting;Username=postgres;Password=postgres"
- Provider resolved from configuration["Database:Provider"] else DatabaseProvider.PostgreSql
- Data protection path: configuration["Security:DataProtectionPath"] ?? "./dataprotection-keys", persisted via AddDataProtection().PersistKeysToFileSystem(new DirectoryInfo(...)).SetApplicationName("SmeAccounting")
- Forwarded headers configured via AddForwardedHeadersInfrastructure: ForwardedHeaders XForwardedFor | XForwardedProto, KnownProxies.Clear()
- Program.cs calls app.UseForwardedHeaders()
- Environment variables used: SME_ACCT_CONNECTION_STRING, ADMIN_PASSWORD, Security__DataProtectionPath, ConnectionStrings__DefaultConnection, ASPNETCORE_ENVIRONMENT
- No appsettings*.json files present in repo; configuration via env vars per deployment docs

### Testcontainers & Testing Infrastructure
- tests/SmeAccounting.Infrastructure.Tests/DatabaseIntegrationTests uses Testcontainers.PostgreSql
- PostgreSqlBuilder "postgres:16.14-alpine" WithDatabase sme_accounting_test, WithUsername postgres, WithPassword postgres, WithCleanUp true
- InitializeAsync starts container, builds ServiceCollection, AddDbContext with UseNpgsql(_postgres.GetConnectionString()), MigrateAsync
- Tests verify snake_case naming, bigint identity PKs, columns snake_case, seed data presence, soft delete filter, FK constraints
- Test runner Microsoft.Testing.Platform via global.json
- Integration tests spin up postgres:16.14-alpine via Testcontainers, no local DB required

### Security & Headers
- Security headers middleware adds X-Content-Type-Options nosniff, X-Frame-Options DENY, X-XSS-Protection 1; mode=block, Referrer-Policy strict-origin-when-cross-origin, Content-Security-Policy default-src 'self', Strict-Transport-Security max-age 31536000 excludes /health
- ForwardedHeaders configured for Nginx reverse proxy
- Data protection keys persisted to filesystem

## Task-Specific Research — [G1] Discover module structure and design domain entities

### Authorization Module Current File Inventory
- Path: src/Modules/Authorization/
- Domain project: SmeAccounting.Modules.Authorization.Domain.csproj
  - References: SmeAccounting.Domain, SmeAccounting.SharedKernel
  - Source files: none discovered (empty scaffold)
- Application project: SmeAccounting.Modules.Authorization.Application.csproj
  - References: Domain, SmeAccounting.Application, SmeAccounting.SharedKernel, Package MediatR
  - Source files:
    - AuthorizationApplicationMarker.cs (abstract marker class for MediatR assembly scan)
- Infrastructure project: SmeAccounting.Modules.Authorization.Infrastructure.csproj
  - References: Application project only
  - Source files:
    - AuthorizationModule.cs (IModule implementation, AddMediatR RegisterServicesFromAssemblyContaining<AuthorizationApplicationMarker>)
    - AuthorizationModuleExtensions.cs (AddAuthorizationModule extension)
  - packages.lock.json present

### Identity Module Mirroring Reference
- Path: src/Modules/Identity/
- Domain:
  - SmeAccounting.Modules.Identity.Domain.csproj references SmeAccounting.Domain + SharedKernel
  - Entities: Role.cs (BaseEntity, Name, NormalizedName, Description, DisplayOrder), User.cs (BaseEntity with DisplayName, Email, UserName, BranchId, IsEnabled, CreatedAtUtc, LastLoginAtUtc, PasswordHash, FailedLoginAttempts, LockedUntilUtc, lockout methods)
- Application:
  - SmeAccounting.Modules.Identity.Application.csproj references Domain + Application + SharedKernel + FrameworkReference Microsoft.AspNetCore.App + MediatR
  - Permissions.cs static class with nested groups Accounts, Journal, Reports, Settings, Users, Audit; 19 permission constants format "module.action", All list via spread
  - PermissionPolicyProvider.cs implements IAuthorizationPolicyProvider, intercepts "Permission:" prefix → PermissionRequirement
  - PermissionAuthorizationHandler.cs defines PermissionRequirement and handler, admin bypass via Permissions.Users.ManageRoles
  - ClaimsPrincipalExtensions.cs provides GetUserId, GetDisplayName, GetBranchId, GetPermissions, HasPermission
- Infrastructure:
  - SmeAccounting.Modules.Identity.Infrastructure.csproj references Application + Domain + FrameworkReference Microsoft.AspNetCore.App + Microsoft.AspNetCore.Identity.EntityFrameworkCore + EF Core + Npgsql
  - ApplicationUser.cs extends IdentityUser<long> with DisplayName, BranchId, IsEnabled, CreatedAtUtc, LastLoginAtUtc
  - ApplicationRole.cs extends IdentityRole<long> with Description, DisplayOrder
  - IdentityDbContext.cs extends IdentityDbContext<ApplicationUser, ApplicationRole, long> with snake_case naming via OnModelCreating loop
  - IdentityDbContextFactory.cs design-time factory
  - RoleSeeder.cs seeds 5 roles with permission claims
  - UserSeeder.cs seeds admin user
  - IdentityModule.cs / IdentityModuleExtensions.cs

### Permissions Catalog & Role Definitions
- Source: src/Modules/Identity/Application/Permissions.cs and docs/security.md
- Permission groups:
  - Accounts: accounts.view, accounts.create, accounts.edit, accounts.delete
  - Journal: journal.view, journal.create, journal.edit, journal.post, journal.reverse
  - Reports: reports.view, reports.export
  - Settings: settings.view, settings.manage
  - Users: users.view, users.create, users.edit, users.delete, users.manage_roles
  - Audit: audit.view
- Total 19 permissions
- Roles seeded:
  - Admin: all 19 permissions
  - ChiefAccountant: Accounts + Journal + Reports + Settings
  - Accountant: Accounts view/create/edit + Journal view/create/edit + Reports.view
  - Viewer: Accounts.view + Journal.view + Reports.view + Audit.view
  - Auditor: Audit.view + Accounts.view + Journal.view + Reports view/export
- Permissions stored as claim type "permission" on roles
- Policy usage: [Authorize(Policy = "Permission:accounts.view")]

### RolePermissionMap Requirements
- No existing RolePermission mapping entity found in codebase
- Current implementation uses ASP.NET Core Identity role claims for permissions
- Authorization module intended to provide domain entities for Role, Permission, RolePermission aggregate
- Expected design per plan: Role, Permission, RolePermission aggregates, value objects, domain events
- Naming conventions to follow:
  - C# PascalCase, DB snake_case via EF converter
  - Primary keys bigint GENERATED BY DEFAULT AS IDENTITY
  - BaseEntity.Id long, concurrency xmin shadow property
  - IAuditable fields CreatedAtUtc, CreatedBy, UpdatedAtUtc, UpdatedBy
  - ISoftDeletable fields IsDeleted, DeletedAtUtc, DeletedBy with global filter
  - ICompanyScoped CompanyId where applicable
  - Decimal numeric(18,2)
- Module structure mirrors Identity: Domain/Application/Infrastructure with marker class, IModule registration, MediatR assembly scan
- Csproj references pattern:
  - Domain → SharedKernel + Domain
  - Application → Domain + Application + SharedKernel + MediatR (+ FrameworkReference if ASP.NET Core services needed)
  - Infrastructure → Application (+ Domain) + FrameworkReference + EF packages
- Authorization module currently scaffolded but empty; domain entities to be designed for roles/permissions management separate from Identity ASP.NET Core Identity tables

### Docs References
- docs/security.md defines RBAC, permissions, roles, policy provider/handler, claims extensions, cookie auth config
- docs/modules.md confirms Authorization module scaffolded, structure Domain/Application/Infrastructure, registration via AddModules
- docs/database.md confirms PostgreSQL 16.14, snake_case naming, bigint identity PKs, xmin concurrency, IAuditable/ISoftDeletable/ICompanyScoped, decimal precision, migrations policy
- docs/architecture.md confirms Clean Architecture + Modular Monolith, layer rules, IModule pattern, shared DbContext


## Task-Specific Research — [G1] Implement Domain layer

### Domain Project Structure
- Path: src/Modules/Authorization/Domain/
- Csproj: SmeAccounting.Modules.Authorization.Domain.csproj
- RootNamespace: SmeAccounting.Modules.Authorization.Domain
- ProjectReferences:
  - ../../../SmeAccounting.Domain/SmeAccounting.Domain.csproj
  - ../../../SmeAccounting.SharedKernel/SmeAccounting.SharedKernel.csproj
- No source files currently present. Scaffold empty.

### Reference Pattern from Identity.Domain
- Identity Domain csproj identical references: SmeAccounting.Domain + SmeAccounting.SharedKernel
- Namespace: SmeAccounting.Modules.Identity.Domain
- Role.cs pattern:
  - Inherits BaseEntity
  - Protected parameterless ctor
  - Properties: Name string, NormalizedName string, Description string, DisplayOrder int
- User.cs pattern:
  - Inherits BaseEntity
  - Properties: DisplayName, Email, UserName, BranchId?, IsEnabled, CreatedAtUtc, LastLoginAtUtc?, PasswordHash?, FailedLoginAttempts, LockedUntilUtc?
  - Domain methods: RecordSuccessfulLogin, RecordFailedLogin, Lock, Unlock, SetPasswordHash, Deactivate, Activate
  - IsLockedOut computed

### SharedKernel Conventions
- BaseEntity: long Id, domain events list, RaiseDomainEvent, ClearDomainEvents
- IAuditable: CreatedAtUtc, CreatedBy?, UpdatedAtUtc?, UpdatedBy?
- ISoftDeletable: IsDeleted, DeletedAtUtc?, DeletedBy?
- ICompanyScoped: CompanyId long
- Naming: snake_case DB via EF converter, PascalCase code
- PK: bigint GENERATED BY DEFAULT AS IDENTITY
- Concurrency: shadow xmin xid
- Soft delete global filter mandatory
- Audit fields mandatory

### Permissions Catalog
- Current static catalog lives in src/Modules/Identity/Application/Permissions.cs
- Namespace SmeAccounting.Modules.Identity.Application
- Static class Permissions with nested static classes Accounts, Journal, Reports, Settings, Users, Audit
- Constants format "module.action"
- 19 permissions total
- All property returns IReadOnlyList<string>
- Policy prefix "Permission:" used in Authorization
- Claims type "permission" lowercase
- Admin bypass via Users.ManageRoles

### Built-in Roles
- Seeded by RoleSeeder in Identity Infrastructure
- Roles: Admin, ChiefAccountant, Accountant, Viewer, Auditor
- Permissions assigned via role claims
- Admin gets all 19 permissions
- ChiefAccountant: Accounts + Journal + Reports + Settings
- Accountant: Accounts view/create/edit + Journal view/create/edit + Reports.view
- Viewer: Accounts.view + Journal.view + Reports.view + Audit.view
- Auditor: Audit.view + Accounts.view + Journal.view + Reports view/export

### Domain Layer Requirements for Authorization Module
- No Permission entity. Permission is static catalog, not persisted entity.
- Role entity required in Domain: BaseEntity, Name, NormalizedName, Description, DisplayOrder, IsBuiltIn bool?, maybe IsSystem?
- RolePermissionMap entity required: links Role to permission string
  - RoleId long FK
  - Permission string (value object)
  - Possibly Id long PK
  - IAuditable? Possibly not, mapping table may be simple
- Value objects: Permission string validation, maybe Permission value object with static factory
- Domain events: RoleCreated, RoleUpdated, RoleDeleted, PermissionAssigned, PermissionRemoved
- Ensure Domain has no reference to Infrastructure, no EF Core, no ASP.NET Core
- Namespace SmeAccounting.Modules.Authorization.Domain
- Files to create:
  - Roles.cs (Role aggregate root)
  - RolePermissionMap.cs (mapping entity)
  - Permissions.cs (static catalog? Could be in Application per existing pattern, but task lists Permissions.cs for domain. Might be static catalog duplicated for domain reference. Ensure no Permission entity.)
  - Possibly Permission value object file
- Domain project references already correct, no changes needed
- Ensure Role entity does NOT duplicate Identity.Domain Role? Possibly Authorization module manages application-level roles separate from ASP.NET Core Identity roles. Keep separate namespace.

### Verification Criteria
- Domain project builds with zero warnings
- Role class inherits BaseEntity, has required properties
- RolePermissionMap class exists with RoleId and Permission string
- No Permission entity class with Id
- Permissions static catalog contains 19 constants matching docs/security.md
- Built-in roles constants defined
- No Infrastructure dependencies in Domain
- Namespace correct
- Follows snake_case naming convention via EF later, but domain classes PascalCase

### Quality Standards
- Follow Identity.Domain Role.cs pattern for ctor and properties
- Use protected parameterless ctor for EF
- Domain events via BaseEntity.RaiseDomainEvent
- No ASP.NET Core types in Domain
- Static catalog immutable
- Permission strings match existing catalog exactly
- RolePermissionMap should be entity with Id, RoleId, Permission
- Avoid duplication with Identity.Domain Role; if overlap, ensure distinct purpose

### Prior Attempt Analysis
- No prior attempts for this task. Module scaffold empty.

## Task-Specific Research — [G2] Implement Application layer

### Context & Prior Work
- Authorization.Application currently contains ONLY AuthorizationApplicationMarker.cs (abstract marker for MediatR assembly scan). AuthorizationModule.AddModule already scans this assembly. No commands, queries, handlers, validators, or policy types exist yet.
- G1 created Domain catalog: Permissions.cs (19 constants, mirrors Identity catalog), Roles.cs (5 constants + All), RolePermissionMap.cs (static Map + GetPermissions). Application validators/handlers must validate against Domain.Permissions.All and Roles.All — no new catalog needed.
- Identity.Application is verbatim reference implementation (4 files): Permissions.cs, PermissionPolicyProvider.cs, PermissionAuthorizationHandler.cs (holds PermissionRequirement + handler), ClaimsPrincipalExtensions.cs. Full source captured via codegraph this session.
- No IRequest/IRequestHandler/AbstractValidator/IPermissionService/IRoleService exists anywhere in src (grep: only ValidationBehaviour references IRequest). G2 is greenfield CQRS — no in-repo handler example to copy; follow MediatR + SharedKernel.Result conventions below.
- Two ValidationBehaviour copies exist: src/SmeAccounting.Application/Behaviours/ValidationBehaviour.cs (sealed, canonical) and src/SmeAccounting.Infrastructure/Validation/ValidationBehaviour.cs (non-sealed duplicate). Global AddApplication() registers pipeline once; module handlers get validation free. Executor must NOT re-register pipeline in AuthorizationModule.

### Existing Tools & Resources
- MediatR 12.5.0 (pinned, Apache-2.0 last; 13+ is RPL — do NOT upgrade). DI merged into main package. Pattern: `IRequest<Result>` / `IRequest<Result<T>>` + `IRequestHandler<TReq,TResp>`; marker already wired via `RegisterServicesFromAssemblyContaining<AuthorizationApplicationMarker>`, `Lifetime=Scoped` set globally.
- FluentValidation 12.1.1 + FluentValidation.DependencyInjectionExtensions 12.1.1 (central pins). Base SmeAccounting.Application csproj references both; Authorization.Application gets them transitively via ProjectReference, but executor should add explicit versionless `<PackageReference Include="FluentValidation" />` for direct AbstractValidator<T> use (CPM: versionless, lock file update required).
- SharedKernel.Result API (exact): `Result.Success()`, `Result.Fail(code, description)` / `Fail(Failure)` / `Fail(IEnumerable<Failure>)`, `Result<T>.Create(value)` / `Fail(...)` (note `new` keyword on Fail overloads), implicit operators from T and Failure, `IsSuccess/IsFailure/Failures`. `Failure` is `sealed record Failure(string Code, string Description)` + `Failure.None`. CA1000 already suppressed in .editorconfig per global memory.
- SharedKernel abstractions: `IRepository<T>` (GetByIdAsync/ListAsync/AddAsync/Update/Remove), `IUnitOfWork.SaveChangesAsync`. GOTCHA: `IRepository<T>.GetByIdAsync` takes `Guid id` but all BaseEntity PKs are `long` — generic repo is unusable for Role directly. G2 must define module-specific abstractions (e.g. `IRoleRepository` with long ids, `IPermissionService`/`IRoleService`) as interfaces in Application; concrete EF repos land in G2-Infrastructure task.
- FrameworkReference: Identity.Application csproj proves any lib using `IAuthorizationPolicyProvider` / `AuthorizationHandler<T>` / `AuthorizationPolicyBuilder` needs `<FrameworkReference Include="Microsoft.AspNetCore.App" />`. Authorization.Application csproj currently LACKS it (has only MediatR + 3 ProjectReferences) — executor must add it. Same no-package pattern as IHttpContextAccessor.
- Analyzer traps (verified, global memory): FV DI namespace is `FluentValidation` (not `.DependencyInjectionExtensions`); `ValidationFailure` lives in `FluentValidation.Results`; pipeline override params must name `cancellationToken`; file-scoped namespaces enforced (IDE0161 error); `TreatWarningsAsErrors` + nullable + ImplicitUsings on; LangVersion 14 collection expressions `[..]` allowed.

### Requirements & Constraints
- Layer rules (ArchitectureTests): module Application may depend on Domain + SharedKernel only (plus FrameworkReference/MediatR/FV packages). No reference to Identity module, Infrastructure, or Api. `Module_Domains_Should_NotDependOnInfrastructure` enforced; Application→Infrastructure dependency would fail `Application_Should_OnlyDependOnDomainAndSharedKernel`-style review.
- No module-to-module ProjectReference allowed → G2 CANNOT reuse `SmeAccounting.Modules.Identity.Application` policy types. Must port (duplicate) `PermissionRequirement`, `PermissionAuthorizationHandler`, `PermissionPolicyProvider`, `ClaimsPrincipalExtensions` into `SmeAccounting.Modules.Authorization.Application` namespace, rewired to Domain.Permissions catalog. Identity copies stay untouched.
- Policy contract (must match exactly): intercept `"Permission:{name}"` case-insensitive, fallback to `DefaultAuthorizationPolicyProvider` for all other policies; handler succeeds on exact permission claim OR `users.manage_roles` admin bypass; claim type lowercase `"permission"`; usage `[Authorize(Policy = "Permission:accounts.view")]`.
- Suggested CQRS surface (minimal, covers PLAN scope): commands CreateRole / UpdateRole / DeleteRole / AssignPermission / RemovePermission; queries GetRoleById / ListRoles / GetPermissions (+ GetRolePermissions). Each request returns `Result` or `Result<T>` with DTO records defined alongside; validators (`AbstractValidator<T>`) check Name non-empty/max length, permission strings ∈ `Domain.Permissions.All`, role names ∈ `Roles.All` where applicable.
- csproj changes: add `<FrameworkReference Include="Microsoft.AspNetCore.App" />` + versionless FluentValidation PackageReference; commit updated `packages.lock.json` (locked-mode CI fails on NU1004 otherwise).

### Suggested Approach
Port 4 Identity policy files into Authorization.Application (namespace swap + Domain catalog rewire), add FrameworkReference to csproj; then define role/permission commands, queries, handlers returning Result<T>, validators against Domain catalog, plus IRoleRepository/IPermissionService abstractions for Infrastructure task.

### Verification Criteria
- Passing: `dotnet build -c Release SmeAccounting.slnx` zero warnings; new files under `src/Modules/Authorization/Application/` only (+ csproj + lock); namespace `SmeAccounting.Modules.Authorization.Application`; policy string `"Permission:"` prefix case-insensitive with DefaultAuthorizationPolicyProvider fallback; admin bypass via `users.manage_roles`; validators reject unknown permission strings and empty role names; handlers return `Result`/`Result<T>` (never throw for domain failures, never return raw DTOs); no ProjectReference to Identity/Infrastructure modules; packages.lock.json updated.
- Failing: referencing Identity.Application types (module coupling); missing FrameworkReference (compile fail on AuthorizationHandler); Permission entity created in Application; raw `Guid`-based generic `IRepository<Role>` used despite long PKs; pipeline re-registered in AuthorizationModule; MediatR upgraded past 12.5.0; TreatWarningsAsErrors violations (nullable, unused usings).

### Quality Standards
- Good: handlers thin (validate → repo → SaveChanges → Result), DTOs as sealed records colocated with requests, validators one-per-command, interfaces segregated (IRoleRepository, IPermissionService), file-scoped namespaces, collection expressions matching Domain style.
- Merely functional: handlers containing EF/claims logic, validators missing (relying on pipeline absence), duplicated permission string literals instead of Domain catalog refs.
- Anti-patterns: business logic in future controllers, direct RoleManager/DbContext use in Application, `Error`-named types (CA1716 — use `Failure`), covariant `Fail` without `new`.

### Prior Attempt Analysis
- No prior G2 attempts. STATUS.md shows G1 verified pass; G1 audit WARN noted catalog duplication (Domain Permissions duplicates Identity catalog) — G2 porting policy types extends that duplication deliberately per no-module-refs rule; verifier should accept duplication, flag only string drift vs docs/security.md 19 permissions.

## Task-Specific Research — [G2] Implement Infrastructure layer

### Context & Prior Work
- Authorization.Infrastructure currently contains ONLY AuthorizationModule.cs (IModule, single AddMediatR scan line) + AuthorizationModuleExtensions.cs (`AddAuthorizationModule()` with NO IConfiguration param). Authorization.Application contains ONLY the marker. G2-Application task is still OPEN — no IRoleRepository / IPermissionService / commands / ported policy types exist yet for Infrastructure to implement against.
- G1 Domain produced static-only types (Permissions, Roles, RolePermissionMap) — NO BaseEntity subclass, NO persistable entity. There is therefore nothing to map with EF and no table to migrate.
- Identity.Domain Role.cs is a plain BaseEntity mirror (Name/NormalizedName/Description/DisplayOrder), NOT the seeded runtime type. Runtime roles are Identity Infrastructure ApplicationRole : IdentityRole<long> + permission claims. Authorization must not create a parallel Role table.

### Existing Tools & Resources (verbatim, verified this session)
- ApplicationUser (`src/Modules/Identity/Infrastructure/ApplicationUser.cs`): `IdentityUser<long>` + DisplayName, BranchId long?, IsEnabled=true, CreatedAtUtc, LastLoginAtUtc?.
- ApplicationRole (`ApplicationRole.cs`): `IdentityRole<long>` + Description, DisplayOrder.
- IdentityDbContext (`IdentityDbContext.cs`): `IdentityDbContext<ApplicationUser, ApplicationRole, long>`; snake_case via OnModelCreating loop over GetEntityTypes (tables + columns only, no FK renaming); ToSnakeCase is naive uppercase-split.
- RoleSeeder: `StandardRoles` tuple array (Name/Description/Permissions), Admin=[..Permissions.All], permissions stored via `roleManager.AddClaimAsync(role, new Claim("permission", permission))` (lowercase literal). UserSeeder: admin@smeaccounting.vn / ADMIN_PASSWORD env ?? "Admin@12345", AddToRoleAsync "Admin".
- IdentityModule.cs: MediatR scan only. IdentityModuleExtensions.AddIdentityModule(services, configuration) calls AddModule + AddIdentityInfrastructure(configuration).
- IdentityServiceExtensions.AddIdentityInfrastructure (sole authorization wiring point): AddDbContext<IdentityDbContext> via DbProviderSelector, AddIdentity password/lockout/cookie (8h sliding, SameSite Lax), `AddSingleton<IAuthorizationPolicyProvider, PermissionPolicyProvider>` + `AddScoped<IAuthorizationHandler, PermissionAuthorizationHandler>`.
- Program.cs: AddIdentityModule(config) line 28 AND AddModules([... new IdentityModule(), new AuthorizationModule(), ...]) lines 29-43. AuthorizationModule already registered — NO Program.cs change needed unless extension signature changes.
- SmeAccountingDbContext: DbSets Companies/Branches/Accounts/AuditLogEntries only; `ApplyConfigurationsFromAssembly(typeof(SmeAccountingDbContext).Assembly)` = SmeAccounting.Infrastructure assembly — module-assembly IEntityTypeConfiguration classes are NOT auto-discovered. Snake_case covers tables/columns/FKs; numeric(18,2) default; soft-delete filter via expression tree; SeedData Company+Branch only. Fail-fast pending-migration throw in Program.cs (non-Testing env).
- DependencyInjection.AddInfrastructure registers AddHttpContextAccessor + SmeAccountingDbContext + `AddScoped<ICurrentUserProvider, HttpContextCurrentUserProvider>` — do NOT re-register either in AuthorizationModule.
- IRepository<T> (SharedKernel, verbatim): GetByIdAsync(Guid id) — Guid vs long-PK mismatch confirmed; unusable for Role/ApplicationRole. ICurrentUserProvider: Guid? UserId + IsAuthenticated; HttpContextCurrentUserProvider parses NameIdentifier as Guid, while Identity ClaimsPrincipalExtensions.GetUserId parses long — live inconsistency, follow the long convention for role work.
- ClaimsPrincipalExtensions (Identity.Application, verbatim): claim types "permission" (lowercase), "display_name", "branch_id", ClaimTypes.NameIdentifier→long.
- PermissionRequirement/Handler + PermissionPolicyProvider source captured verbatim in G2-Application research section above (policy prefix "Permission:" case-insensitive, DefaultAuthorizationPolicyProvider fallback, users.manage_roles admin bypass).
- Grep verdicts (src-wide): zero IEntityTypeConfiguration, zero AddPermissionPolicies/AddAuthorization helper, zero IRoleRepository/IPermissionService, zero module-infra→DbContext references. No in-repo EF-config or Authorization-repo example to copy.
- Identity.Infrastructure csproj (mirror target): FrameworkReference Microsoft.AspNetCore.App + versionless Identity.EFCore/EFCore/EFCore.Design(PrivateAssets=all)/Npgsql + ProjectRefs Application + Domain. Authorization.Infrastructure csproj currently refs Application ONLY.

### Requirements & Constraints
- NO new DbContext. NO DbSet additions to SmeAccountingDbContext (no entities). NO migration from this task (migrations centralized in SmeAccounting.Infrastructure; G3 handles seeds). No `Permission` entity (static catalog rule from G1).
- Module registration already complete via AddModules list; keep AddAuthorizationModule() signature stable (no IConfiguration param, no Program.cs edit).
- Do NOT duplicate authorization DI: PermissionPolicyProvider/handler singletons already registered by AddIdentityInfrastructure. If G2-app ports policy types into Authorization.Application, executor must explicitly decide + document whether AuthorizationModule registers the ported copies or Identity wiring stays canonical — double registration = last-wins override, must not happen silently.
- Do NOT re-register MediatR pipeline, ICurrentUserProvider, HttpContextAccessor, or SmeAccountingDbContext in AuthorizationModule (all owned by base Application/Infrastructure).
- Layer rules: Infrastructure → Application + Domain + SharedKernel only; no ProjectReference to Identity module; consume Identity types (RoleManager<ApplicationRole>) only via shared ASP.NET Core Identity abstractions if needed, never via module ProjectReference. ArchitectureTests enforce Module_Domains rule; follow same discipline for Infra csproj.
- csproj changes mirror Identity.Infra: add FrameworkReference + versionless EF/Identity PackageReferences + Domain ProjectReference; commit updated packages.lock.json (locked-mode CI NU1004).
- BLOCKED-UNTIL sequencing: repository implementations need Application-layer abstractions (IRoleRepository long-keyed, IPermissionService) from the still-open G2-Application task. Executor must either wait for it or define both sides consistently in one pass and note the overlap.
- TreatWarningsAsErrors + nullable + file-scoped namespaces (IDE0161) + ImplicitUsings on; LangVersion 14.

### Suggested Approach
Register only what is new in AuthorizationModule (role/permission repositories and services over RoleManager + static RolePermissionMap, no DbContext, no auth-policy duplication); add FrameworkReference + Identity/EF PackageReferences + Domain ProjectReference to the Infrastructure csproj; coordinate with or subsume the pending Application-layer abstractions first since nothing implementable exists yet.

### Verification Criteria
- Passing: `dotnet build -c Release SmeAccounting.slnx` zero warnings; new files only under src/Modules/Authorization/Infrastructure/ (+ csproj + lock); namespace SmeAccounting.Modules.Authorization.Infrastructure; no new DbContext/DbSet/migration; no duplicate AddSingleton<IAuthorizationPolicyProvider>/AddScoped<IAuthorizationHandler>/AddDbContext/AddHttpContextAccessor/ICurrentUserProvider registrations; claim literal "permission" lowercase; admin bypass users.manage_roles preserved wherever permissions are evaluated; no ProjectReference to Identity/Infrastructure/Authorization-outside-module; packages.lock.json updated; Program.cs untouched (module already in AddModules list).
- Failing: new IdentityDbContext-style context or SmeAccountingDbContext DbSet; IEntityTypeConfiguration placed in module assembly expecting auto-discovery (ApplyConfigurationsFromAssembly scans SmeAccounting.Infrastructure only); Permission entity with Id; Guid-based IRepository<Role> use; policy-handler double registration; IConfiguration added to AddAuthorizationModule without Program.cs update; MediatR/Identity package upgrade past pins (MediatR 12.5.0, Identity.EFCore 10.0.12).

### Quality Standards
- Good: thin repositories delegating to RoleManager<ApplicationRole>/UserManager via abstractions (no EF types leak), permission reads served from Domain.RolePermissionMap (zero DB round-trip), RoleSeeder parity (same 5 roles, same permission sets, same "permission" claim type), explicit comment wherever registration is deliberately skipped (auth policy, DbContext, current-user) citing the owner.
- Merely functional: EF DbContext injected into Authorization repos for tables that do not exist; permission strings hard-coded instead of Domain.Permissions refs.
- Anti-patterns: parallel Role table, parallel DbContext, AddAuthorization()-style policy re-registration, Permission entity, cross-module ProjectReference to Identity.

### Prior Attempt Analysis
- No prior G2-Infrastructure attempts. Open dependency: G2-Application task still unchecked with only marker file present — executor cannot implement repository interfaces that do not exist yet; plan for interface-first ordering.

## Task-Specific Research — [G3] Seed

### Context & Prior Work
- RoleSeeder (`src/Modules/Identity/Infrastructure/RoleSeeder.cs`): static class, `StandardRoles` tuple array (Name/Description/Permissions) for 5 roles; Admin=[..Identity Permissions.All], ChiefAccountant=Accounts+Journal+Reports+Settings, Accountant=7 perms, Viewer=4 perms, Auditor=5 perms. `SeedAsync(RoleManager<ApplicationRole>, ILogger)` — FindByNameAsync, CreateAsync if missing, AddClaimAsync per permission with literal `new Claim("permission", permission)` (lowercase). Idempotent on roles (skips existing) but does NOT reconcile claims on existing roles (claim drift never repaired).
- UserSeeder (`UserSeeder.cs`): `SeedAsync(UserManager, RoleManager, ILogger, adminPassword?)` — FindByEmailAsync admin@smeaccounting.vn, creates ApplicationUser (UserName admin, EmailConfirmed true, DisplayName System Administrator, IsEnabled, CreatedAtUtc UtcNow), password = param ?? ADMIN_PASSWORD env ?? "Admin@12345", then AddToRoleAsync Admin. Idempotent (skips if exists).
- CRITICAL GAP: grep src-wide shows SeedAsync referenced NOWHERE — neither seeder is ever invoked (no Program.cs call, no hosted service, no IdentityModule wiring). IdentityServiceExtensions registers DbContext+Identity+cookie+policy/handler only. So G3 must wire invocation, not just document seeders.
- Authorization Domain RolePermissionMap mirrors StandardRoles permission sets against Authorization Domain Permissions catalog (same 5 roles, same sets). Runtime seed must pick ONE catalog as source of truth — Identity Permissions (used by RoleSeeder today) vs Authorization Domain Permissions (G1/G2 services validate against). String values identical today; verifier must diff.
- G2 services reuse same "permission" lowercase claim literal + users.manage_roles admin bypass — seed data is what makes those checks pass at runtime.
- Guid-vs-long carryover (STATUS audit): Authorization IRoleService takes Guid userId, Identity PKs are long — admin user created by UserSeeder gets long Id; AssignRole paths via Authorization module will miss. G3 seed cannot fix type mismatch, but must document admin long Id vs Guid expectation.

### Existing Tools & Resources
- DbProviderSelector (`src/SmeAccounting.Infrastructure/Persistence/DbProviderSelector.cs`, internal static): Resolve (Database:Provider, default PostgreSql), ResolveConnectionString (Database:ConnectionString > SME_ACCT_CONNECTION_STRING config > env > provider default), Configure (UseNpgsql/UseMySql/UseSqlite/UseSqlServer + MigrationsAssembly=current assembly per branch). Reused by DesignTimeDbContextFactory, IdentityServiceExtensions, IdentityDbContextFactory. Provider-neutral seed invocation must NOT branch per provider — resolve RoleManager/UserManager from DI after provider-agnostic AddDbContext.
- IdentityDbContext (`IdentityDbContext.cs`): IdentityDbContext<ApplicationUser,ApplicationRole,long>, snake_case rename loop for tables+columns only (no FK rename, unlike SmeAccountingDbContext which also renames FKs). Yields tables asp_net_roles / asp_net_role_claims etc. (ToSnakeCase on default AspNet* names). Reuse as-is — no new tables.
- IdentityDbContextFactory: design-time only, env-var config, DbProviderSelector.Configure. `dotnet ef` commands target it via startup project Api.
- SmeAccountingDbContext (`Persistence/SmeAccountingDbContext.cs`): DbSets Companies/Branches/Accounts/AuditLogEntries only; HasData SeedData for Demo Company + Head Office (anonymous types incl. audit/soft-delete fields); ApplyConfigurationsFromAssembly scans Infrastructure assembly only. Authorization adds NO DbSet — confirmed no model change, so NO SmeAccountingDbContext migration from this task.
- Migration folders: `src/SmeAccounting.Infrastructure/Migrations/` holds 2 legacy migrations (InitialFoundationXminV3 + Circular133COASeed + snapshot). `Persistence/Migrations/` has README (per-provider generation commands with Database__Provider + --output-dir Persistence/Migrations/{PostgreSql,MariaDb,Sqlite,SqlServer}) + 4 EMPTY provider dirs. `src/Modules/Identity/` has ZERO Migrations folders — IdentityDbContext has NEVER had a migration generated (AspNet* tables exist only via EnsureCreated/Migrate if someone runs it — currently nothing runs it).
- Program.cs: fail-fast pending-migration check covers SmeAccountingDbContext ONLY (lines 55-65, skipped in Testing env). No IdentityDbContext check, no seed invocation, no MigrateAsync call anywhere. G3 wiring must extend this block or add adjacent scoped seed step.
- No raw SQL anywhere in seed path today (HasData + RoleManager/UserManager APIs only) — keep it that way.

### Requirements & Constraints
- No new tables: reuse AspNetRoles (ApplicationRole: Name/NormalizedName/Description/DisplayOrder) + AspNetRoleClaims (Type="permission", Value=permission string) + AspNetUsers + AspNetUserRoles. No DbSet additions, no IEntityTypeConfiguration, no Permission entity.
- No raw SQL: seed via RoleManager<ApplicationRole>/UserManager<ApplicationUser> (provider-neutral, handles hashing/normalization) or HasData only for static lookup rows. Never INSERT INTO asp_net_* by hand (breaks NormalizedName/security-stamp/password-hash invariants per provider).
- Provider-neutral: seed code takes resolved managers from DI; DbProviderSelector.Configure already abstracts provider. Migration generation (if any) must use Database__Provider + --output-dir per README; SmeAccountingDbContext model unchanged so expect empty/no-op migration — do NOT commit empty migration.
- Idempotent seed: FindByName/FindByEmail pre-check (already in seeders); safe re-run on every startup. Consider claim reconciliation for existing roles (current seeder skips claims if role exists — document as known gap or fix with GetClaimsAsync + AddClaimAsync delta).
- Admin assignment: admin@smeaccounting.vn → Admin role via AddToRoleAsync; password ADMIN_PASSWORD env override, EmailConfirmed=true. Keep default Admin@12345 dev fallback matching docs/security.md.
- Layer/architecture: seed invocation lives in Api composition root (Program.cs) or Identity Infrastructure extension (AddIdentityInfrastructure — has IConfiguration), NOT in Authorization module (would need cross-module manager types). Authorization module must NOT gain Identity ProjectReference for seeding. ArchitectureTests: no new layer violations; TreatWarningsAsErrors + nullable + file-scoped namespaces.
- Which DbContext gets migrated: IdentityDbContext needs its FIRST migration (per-provider dir per README) OR explicit Database.MigrateAsync at startup. SmeAccountingDbContext needs nothing new. Do NOT add Identity entities to SmeAccountingDbContext.

### Suggested Approach
Wire in Program.cs (or IdentityServiceExtensions) a scoped startup step after the existing SmeAccountingDbContext pending-migration check: MigrateAsync IdentityDbContext (provider-neutral via DI), then RoleSeeder.SeedAsync + UserSeeder.SeedAsync with ILogger + ADMIN_PASSWORD passthrough; generate the first Identity per-provider migration via README commands only if a persistent-migration strategy is chosen over startup-MigrateAsync — and document the choice.

### Verification Criteria
- Passing: app starts with empty DB → 5 rows in asp_net_roles, N rows in asp_net_role_claims matching StandardRoles counts (Admin 19), admin@smeaccounting.vn exists in asp_net_users with row in asp_net_user_roles → Admin; second startup changes nothing (idempotent, no dupes, no throw); works under PostgreSql provider at minimum; no raw SQL in diff; no new DbSet/table in any migration; snake_case asp_net_* table/column names preserved; locked-mode restore passes if csproj touched (expect none).
- Failing: new tables/DbSets; raw SQL INSERTs; provider-switched code paths; seed only runs once via migration HasData for Identity (password hashes cannot be HasData-seeded safely); admin user missing role; duplicate roles/claims on re-run; IdentityDbContext migration placed in legacy Migrations/ folder instead of per-provider dir; Program.cs pending-migration check still ignoring IdentityDbContext while claiming fail-fast.

### Quality Standards
- Good: single seed orchestration site (Program.cs block or AddIdentityInfrastructure-adjacent extension), ILogger logging per created role/user (existing pattern), ADMIN_PASSWORD env passthrough, claim-delta reconciliation noted/fixed, Testing-env skip consistent with existing fail-fast guard.
- Merely functional: fire-and-forget seed without logging, no re-run safety on claims, provider-specific connection strings hardcoded.
- Anti-patterns: Authorization module referencing Identity Infrastructure for seed types; Permission entity migration; hand-written AspNet* SQL; committing empty no-op migration to satisfy "create migrations" checkbox; seeding admin password from appsettings default committed to repo.

### Prior Attempt Analysis
- No prior G3 attempts. Pre-existing gaps executor inherits: seeders exist but are dead code (never invoked); IdentityDbContext has zero migrations ever generated; Program.cs fail-fast covers only SmeAccountingDbContext; per-provider migration dirs all empty (strategy undecided: startup-MigrateAsync vs checked-in per-provider migrations).

## Task-Specific Research — [G3] Tests

### Context & Prior Work
- Authorization surface to test (all new in G2, zero coverage today): Domain `Permissions` (19 consts), `Roles` (5 consts + All), `RolePermissionMap` (Map + GetPermissions, unknown role → `[]`); Application 6 commands (Create/Delete/AssignPermission/RevokePermission/AssignRoleToUser/RemoveRoleFromUser — sealed `IRequest<Result>` records, thin handlers delegating to IRoleService) + 3 queries (ListRoles/GetRolePermissions via IRoleService, GetUserPermissions via IPermissionService + `Result.Create` wrap) + 6 validators (role regex `^[A-Za-z0-9_.-]+$` + Max256 + NotEmpty; permission `Must(p => Domain.Permissions.All.Contains(p))`; UserId NotEmpty; QUERIES HAVE NO VALIDATORS); ported policy stack (PermissionRequirement/Handler/Provider + ClaimsPrincipalExtensions, rewired to Domain catalog); Infrastructure `RoleService` (RoleManager+UserManager facade, idempotent assigns, `IdentityFailure` collapse, lowercase `"permission"` claim const, Guid userId → `FindByIdAsync(userId.ToString())`) + `PermissionService` (Ordinal HashSet aggregation, unknown user → empty not Fail); `RolesController` (MVC `Controller`, class-level `[Authorize(Policy="Permission:users.manage_roles")]`, 8 mediator-only actions, `ToActionResult` Ok vs BadRequest).
- Known G2 issues tests must NOT paper over (STATUS audit WARN): Guid userId vs long Identity PKs → Assign/Remove/GetPermissions silently miss real users; ported PermissionPolicyProvider dead code unless registered; dual static-19-policies + dynamic provider + two handler regs; IPermissionService returns raw list/bool not Result. Tests asserting Guid-user happy paths against real Identity stores will FAIL on lookup — mock IRoleService for handler tests, and flag don't "fix" by changing prod types inside G3.
- `RolesController` is MVC `Controller` (not ApiController): unauthenticated request → cookie redirect 302 to `/Accounts/Login`, NOT 401/403. True 403 needs authenticated-without-permission principal → requires TestAuthHandler override in WebApplicationFactory. `ToActionResult` maps failure → 400, never 404.
- docs/testing.md is the contract: 6 test projects table + run/filter commands + per-project test inventory + frameworks (xUnit/NSubstitute/Testcontainers.PostgreSql/NetArchTest/Mvc.Testing) + "Adding New Tests" (IClassFixture, NSubstitute, Testcontainers for DB, new arch rules in ArchitectureTests.cs, update permission assertions when permissions added).

### Existing Tools & Resources
- Test project shape (ALL six csproj identical pattern, verified): `OutputType=Exe` + `UseAppHost=true` + `IsPackable=false` + `<Using Include="Xunit"/>` + `NoWarn $(NoWarn);CA1707` (Application.Tests + Web.Tests also suppress `xUnit1051`); MTP runner via global.json — any NEW test project must copy this shape exactly or mix-fail exit 1. Central pins only: xunit.v3 4.0.0, NSubstitute 6.2.0, AwesomeAssertions 9.6.0, NetArchTest.Rules 1.3.2, Mvc.Testing 10.0.12, Testcontainers.PostgreSql 4.15.0, Testcontainers.XunitV3 4.15.0, Respawn 7.0.0 — all versionless refs, lock file per project committed (locked-mode CI).
- `PermissionTests.cs` (Security.Tests, verbatim pattern for catalog tests): plain `Assert` (NOT AwesomeAssertions), `[Fact]`, 6 tests — non-empty, `module.action` 2-part format, each module has view, Admin==All count, Viewer ends `.view`, reflection uniqueness over nested static string fields. Extend with Authorization-catalog parity tests (same 6 assertions against `Authorization.Domain.Permissions`) + cross-catalog equality (`Identity.Permissions.All` ≡ `Authorization.Domain.Permissions.All`, order-insensitive) + Roles.All 5 names + RolePermissionMap (Admin==All, Viewer ⊆ view-only, unknown role → empty, every map value ⊆ Permissions.All). No mocking needed — pure static.
- `ValidationBehaviourTests.cs` (Application.Tests): NSubstitute pattern — `Substitute.For<IValidator<T>>` + `RequestHandlerDelegate<T>`, `Returns(validationResult)`, `Received(1)`. Validator unit tests simpler: instantiate validator directly, `await validator.ValidateAsync(cmd)` or `TestValidate`, assert `IsValid`/errors — no container needed. 6 existing validators × (valid + empty + bad-regex + unknown-permission + empty-Guid) matrix.
- `DatabaseIntegrationTests.cs` (Infrastructure.Tests): Testcontainers pattern — `PostgreSqlBuilder("postgres:16.14-alpine").WithDatabase(sme_accounting_test).WithUsername(postgres).WithPassword(postgres).WithCleanUp(true)`, `IAsyncLifetime`, `StartAsync(TestContext.Current.CancellationToken)` (xunit v3 TestContext pattern — copy verbatim), ServiceCollection + `AddDbContext(UseNpgsql(GetConnectionString()))`, `MigrateAsync`. RoleService/PermissionService integration needs SAME harness but with `IdentityDbContext` + `AddIdentity<ApplicationUser,ApplicationRole>()` + RoleManager/UserManager from provider — real stores, no NSubstitute (mocking RoleManager concrete class is pain, avoid).
- `MultiDbmsSmokeTests.cs`: placeholder `Assert.True(true)` only. BLOCKER for "per-provider smoke SQLite" ask: `Directory.Packages.props` has NO `Microsoft.EntityFrameworkCore.Sqlite`/`SqlServer`/Pomelo pins, and G2 memory records pre-existing NU1010 failures precisely for Sqlite/SqlServer/Pomelo version gaps — real SQLite smoke needs a new CPM pin + lock regen. Cheap alternative without new pins: `DbProviderSelector.Resolve` unit tests (provider parsing/default, no DB) + PostgreSql-only container smoke. Executor must pick one and document; do NOT hand-add PackageReference versions (CPM forbids, NU1008).
- `ArchitectureTests.cs`: NetArchTest, 8 tests; module loop covers Authorization already (`ModulePrefixes` includes it) but `GetModuleAssembly` loads `artifacts/bin/{Project}/debug/{Project}.dll` — lowercase `debug` + `UseArtifactsOutput` layout; Release-only builds → path missing → `return null` → `continue` (rule SILENTLY SKIPS). New arch tests must account for this: assert assembly non-null, or run `dotnet build` (Debug) before `dotnet test -c Release`. Gaps to add: Authorization.Application → no dep on Infrastructure/Api (mirrors `Application_Should_OnlyDependOnDomainAndSharedKernel` for module assembly), Authorization.Infrastructure → no dep on Api, Authorization Domain+Application loadable (fail if null, not skip), RolesController IL check already covered by existing controller test (mediator-only actions pass).
- `TestWebApplicationFactory.cs` (Web.Tests): `UseEnvironment("Testing")` (skips Program.cs fail-fast) + strips `IHealthCheck` regs. Web.Tests csproj is `Sdk="Microsoft.NET.Sdk.Web"` + already refs Mvc.Testing + Testcontainers.PostgreSql + Respawn. Roles endpoint tests (403/200): anonymous → 302 redirect (assert redirect, not 403); authenticated 200/400 needs TestAuthHandler with `permission` claims + `AddAuthorizationModule` policy wiring — and 200-path needs Identity stores seeded behind factory (Testcontainers + Respawn reset). Medium complexity; minimum viable: anonymous-redirect test + handler-level policy tests (PermissionAuthorizationHandler direct: has-permission → success, admin-bypass → success, none → no success) + ClaimsPrincipalExtensions tests.
- Where to put tests — NO new project needed for unit scope: `SmeAccounting.Security.Tests` refs Api (→ transitively module Application/Infrastructure via Api refs) and already has NSubstitute + AwesomeAssertions + Mvc.Testing. Integration scope (RoleService CRUD, controller 200/403) needs Testcontainers.PostgreSql pin added to Security.Tests csproj OR new `SmeAccounting.Authorization.Tests` project (copy canonical csproj shape + needed pins). Prefer extending Security.Tests (fewer lock/CI deltas) unless executor wants isolation.

### Requirements & Constraints
- New/existing test projects keep canonical shape (`OutputType=Exe`, `UseAppHost`, `Using Xunit`, MTP runner, versionless refs, committed lock). `TreatWarningsAsErrors` + CA1707 NoWarn pattern; xUnit1051 suppression needed if theory data style trips analyzer (copy Web/Application csproj NoWarn).
- Layer/architecture: test-only ProjectReferences allowed (tests are outside prod layer rules); prod code untouched except DI/test-only hooks. No module-to-module prod refs added for tests.
- Deterministic + isolated: Testcontainers for any DB touch (no local/shared DB), Respawn or fresh container per class, `TestContext.Current.CancellationToken` in async calls, no hardcoded passwords beyond existing `postgres/postgres` test convention, no live admin credentials.
- Do NOT "fix" G2 prod issues inside G3 (Guid-vs-long, dead provider, dual handlers) — tests document behavior as-is; flag failures to verifier/auditor.
- `dotnet test` full suite must stay green; CI runs `restore --locked-mode → build → test → publish`, so lock files updated if csproj pins added.

### Suggested Approach
Extend `SmeAccounting.Security.Tests` with Authorization catalog/roles-map/validator/handler/policy unit tests (no new pins), plus Testcontainers-backed RoleService/PermissionService CRUD + WebApplicationFactory anonymous-redirect tests (add Testcontainers.PostgreSql pin if reusing Security.Tests); add Authorization assembly-dependency arch tests with non-null assembly guard; defer real SQLite per-provider smoke to a CPM pin decision (else DbProviderSelector.Resolve unit tests only).

### Verification Criteria
- Passing: `dotnet test` green incl. new tests; catalog parity (19 perms, 5 roles, map ⊆ All, unknown role empty); validator matrix (accept valid, reject empty/bad-regex/unknown-perm/empty-Guid); handler delegation via mocked IRoleService (NSubstitute `Received`); policy handler (grant on claim, grant on admin bypass, no-success otherwise); RoleService integration (create→assign→revoke→delete round-trip, idempotent re-assign Success, unknown perm/role/user Fail codes); controller anonymous → redirect (not 200); arch tests assert Authorization Application↛Infrastructure/Api and assembly actually loaded; locks in sync (`--locked-mode` restore passes).
- Failing: new test project without Exe/UseAppHost/MTP shape; versioned PackageReference (NU1008) or missing lock (NU1004); tests requiring local DB; SQLite smoke without Sqlite CPM pin; Guid-user happy-path asserted against real stores (hits known Guid-vs-long miss); silent-skip arch test (null assembly + continue); prod behavior changes smuggled into G3.

### Quality Standards
- Good: mirrors PermissionTests/ValidationBehaviourTests/DatabaseIntegrationTests idioms (plain Assert for catalog, NSubstitute for interfaces, IAsyncLifetime + TestContext token for containers), `Theory` matrices for validators/map, failure-code assertions (`Authorization.RoleNotFound` etc.), Testing-env factory reuse.
- Merely functional: only happy-path tests, duplicated permission literals instead of Domain refs, container per-test (slow), 403 asserted on anonymous call (actually 302).
- Anti-patterns: mocking RoleManager/UserManager concrete classes; raw SQL against asp_net_*; shared dev DB; committing empty migration to "cover" seeding; changing prod signatures to make tests pass.

### Prior Attempt Analysis
- No prior G3-Tests attempts. STATUS shows current task still "[G3] Create migrations and seed" at 0 attempts — executor should confirm whether tests task runs before seed wiring lands (seed-dependent integration tests need Identity MigrateAsync in harness regardless, so independent).
