# Research Log
## Context & Prior Work
Global conventions from loop-stack/.global/MEMORY.md and TOOLS.md:
- .NET 10 LTS net10.0, ASP.NET Core 10, EF Core 9 via Pomelo for MariaDB; MariaDB 10.6+ LTS, utf8mb4
- Clean Architecture + Modular Monolith, 4-layer: Domain/Application/Infrastructure/Api
- CQRS MediatR 12.5.0, FluentValidation 12.1.1 pipeline
- Central package management Directory.Packages.props, locked mode, .slnx, UseArtifactsOutput=true
- Test runner Microsoft.Testing.Platform via global.json, xunit.v3 requires OutputType=Exe + UseAppHost + <Using Include="Xunit"/>
- NETSDK1188 NoWarn, IDE0005 trap, CPM rules
- Module registry pattern: IModule + Add{Module}Module() + explicit AddModules([...]) in Api, no reflection
- Api references module Application + Infrastructure; DB centralized in SmeAccounting.Infrastructure + single DbContext
- FrameworkReference Microsoft.AspNetCore.App for libs needing ASP.NET Core services
- Permission authorization types in Application: PermissionRequirement, PermissionAuthorizationHandler, PermissionPolicyProvider, ClaimsPrincipalExtensions, Permissions
- Identity Infrastructure uses IdentityDbContext<ApplicationUser,ApplicationRole,long> with snake_case naming via OnModelCreating loop
- IdentityDbContextFactory design-time with Npgsql connection string
- Package versions: Microsoft.AspNetCore.Identity.EntityFrameworkCore 10.0.12, EF Core 10.0.12, Npgsql.EntityFrameworkCore.PostgreSQL 10.0.3

Source structure for SmeAccounting.Modules.Identity:
- Domain: SmeAccounting.Modules.Identity.Domain.csproj
  References: SmeAccounting.Domain, SmeAccounting.SharedKernel
  Types: Domain/User.cs, Domain/Role.cs
- Application: SmeAccounting.Modules.Identity.Application.csproj
  References: Domain, SmeAccounting.Application, SmeAccounting.SharedKernel
  FrameworkReference Microsoft.AspNetCore.App
  Package MediatR
  Types: Permissions.cs, PermissionPolicyProvider.cs, PermissionAuthorizationHandler.cs, ClaimsPrincipalExtensions.cs, IdentityApplicationMarker.cs
- Infrastructure: SmeAccounting.Modules.Identity.Infrastructure.csproj
  FrameworkReference Microsoft.AspNetCore.App
  Packages: Microsoft.AspNetCore.Identity.EntityFrameworkCore, Microsoft.EntityFrameworkCore, Microsoft.EntityFrameworkCore.Design PrivateAssets=all, Npgsql.EntityFrameworkCore.PostgreSQL
  References: Application, Domain
  Types: IdentityDbContext.cs (snake_case mapping), IdentityDbContextFactory.cs, ApplicationUser.cs, ApplicationRole.cs, IdentityModule.cs, IdentityModuleExtensions.cs, IdentityServiceExtensions.cs, RoleSeeder.cs, UserSeeder.cs, ApplicationUserMapper.cs

Patterns observed:
- IdentityModule implements IModule, AddModule registers MediatR from IdentityApplicationMarker
- IdentityModuleExtensions.AddIdentityModule registers module + AddIdentityInfrastructure
- AddIdentityInfrastructure registers IdentityDbContext with UseNpgsql, AddIdentity<ApplicationUser,ApplicationRole>, cookie config, PermissionPolicyProvider singleton, PermissionAuthorizationHandler scoped
- DbContext snake_case conversion manual ToSnakeCase in OnModelCreating
- PermissionPolicyProvider intercepts "Permission:{name}" → PermissionRequirement
- PermissionAuthorizationHandler grants if user has permission or Users.ManageRoles admin bypass

Package files:
- Directory.Packages.props central versions for MediatR 12.5.0, FluentValidation 12.1.1, Identity.EFCore 10.0.12, EF Core 10.0.12, Npgsql 10.0.3
- No MariaDB/SQLite/SQL Server EF providers currently referenced in Identity module

Existing tests:
- tests/SmeAccounting.Security.Tests/PermissionTests.cs uses Permissions and RoleSeeder.StandardRoles
  Tests: AllPermissions_AreNonEmpty, AllPermissions_HaveCorrectFormat, EachModule_HasViewPermission, AdminRole_HasAllPermissions, ViewerRole_OnlyHasViewPermissions, PermissionConstants_AreUnique
- tests/SmeAccounting.Architecture.Tests/ArchitectureTests.cs lists "Identity" as module
- No dedicated Identity unit/integration tests found; security tests cover permissions

Current runtime DB provider:
- DependencyInjection.AddInfrastructure registers SmeAccountingDbContext with UseNpgsql
- IdentityServiceExtensions registers IdentityDbContext with UseNpgsql(configuration.GetConnectionString("DefaultConnection"))
- No runtime provider selection; PostgreSQL 16 default hardcoded

Prior work notes:
- Global memory notes EF Core 10 native support delayed, Pomelo works with .NET 10 but EF Core 9.x
- Identity module currently PostgreSQL-only via Npgsql
## External Knowledge & Resources
### README
- Project: SME Accounting Vietnamese SME accounting web app, ASP.NET Core MVC, Clean Architecture + Modular Monolith
- Tech stack documented: ASP.NET Core 9, EF Core 9, Npgsql 9, PostgreSQL 16.14, ASP.NET Core Identity cookie auth, MediatR, FluentValidation, Serilog, xUnit + NSubstitute + Testcontainers
- Quick start requires .NET 9 SDK, PostgreSQL 16+, connection via SME_ACCT_CONNECTION_STRING env var, `dotnet ef database update`, run `dotnet run --project src/SmeAccounting.Api`
- Default login admin@smeaccounting.vn / Admin@12345, override via ADMIN_PASSWORD env var
- 12 MVP modules listed: Identity, Authorization, Organization, MasterData, Audit, ChartOfAccounts, AccountingPeriod, Journal, Posting, GeneralLedger, Tax, FinancialReporting
- Docs referenced: architecture.md, modules.md, database.md, security.md, deployment.md, testing.md, ADR-001

### docs/
- architecture.md: Clean Architecture + Modular Monolith, layer rules Api→Application→Domain→SharedKernel, Infrastructure separate. IModule interface, composition root AddModules([...]) in Program.cs, module structure Domain/Application/Infrastructure, MediatR, cookie auth, bigint PKs, xmin concurrency, snake_case DB naming via custom converter
- database.md: PostgreSQL 16.14, EF Core 9.0.0 Npgsql 9.0.0, connection string DefaultConnection fallback SME_ACCT_CONNECTION_STRING, snake_case naming enforced, bigint GENERATED BY DEFAULT AS IDENTITY, xmin concurrency token, IAuditable/ISoftDeletable/ICompanyScoped, numeric(18,2) decimals, uuid-ossp extension, migrations fail-fast in Program.cs, seeds Demo Company/Head Office, Circular133COASeed, Identity seeds roles/users
- security.md: ASP.NET Core Identity cookie auth, password policy 8 min digit/lower/upper/non-alphanumeric, lockout 5/15min, require confirmed email, cookie 8h sliding HttpOnly SameSite Lax, ApplicationUser/ApplicationRole models, separate IdentityDbContext snake_case, RBAC 19 permissions, 5 roles seeded, PermissionPolicyProvider intercepts Permission:* policies, PermissionAuthorizationHandler grants, ClaimsPrincipalExtensions helpers, default seeded user, DataProtection keys persisted to filesystem, security headers middleware, antiforgery, forwarded headers, global exception handling
- modules.md: 12 MVP modules scaffolded, each with Domain/Application/Infrastructure, module registration pattern IModule + AddMediatR, isolation rules no inter-module refs, shared DbContext for MVP, Phase 2 and future modules listed
- deployment.md, testing.md, adr/001-naming-and-pk-strategy.md exist per README index

### .env.example / configs
- No .env.example file found in repo
- No appsettings*.json files found in repo tree; configuration appears env-var driven
- Connection string priority: SME_ACCT_CONNECTION_STRING env var > appsettings ConnectionStrings:DefaultConnection (per docs/database.md and AGENTS.md)
- ADMIN_PASSWORD env var overrides seeded admin password
- Security:DataProtectionPath configurable via env or config for DataProtection keys
- EF migrations design-time factory reads SME_ACCT_CONNECTION_STRING

### External APIs
- No external third-party APIs documented in README/docs
- Identity uses ASP.NET Core Identity cookie auth only; no OAuth/OIDC providers referenced
- Reporting uses QuestPDF community license
- CI uses GitHub Actions with actions/checkout@v6, actions/setup-dotnet@v4, shogo82148/actions-setup-mysql@v1 for MariaDB tests

### Config files discovered
- global.json pins .NET 10.0.401 per AGENTS.md
- Directory.Packages.props central versioning with locked mode
- .editorconfig enforced
- Program.cs fail-fast pending migrations check

## Requirements & Constraints

### DB Schema & Naming
- Snake_case enforced for all tables/columns/FKs.
  - `SmeAccountingDbContext.ApplySnakeCaseNamingConvention` converts entity/table/property names via `ToSnakeCase`; also renames FK constraints.
  - `IdentityDbContext.OnModelCreating` applies manual `ToSnakeCase` to table and column names for ASP.NET Core Identity tables.
- Primary keys: `bigint GENERATED BY DEFAULT AS IDENTITY`. `BaseEntity.Id` is `long`. EF annotation `NpgsqlValueGenerationStrategy.IdentityByDefaultColumn` currently applied for PostgreSQL.
- Concurrency token: shadow property `xmin` type `xid` added to every `BaseEntity` subtype.
  - `IsConcurrencyToken=true`, `BeforeSaveBehavior.Ignore`, `AfterSaveBehavior.Ignore`.
  - PostgreSQL system column only. Multi-DBMS requires alternative strategy for MariaDB/SQLite/SQL Server (e.g., `rowversion`/timestamp or EF concurrency token column).
- Soft-delete: global query filter for `ISoftDeletable` (`IsDeleted`).
- Audit: `IAuditable` fields `CreatedAtUtc`, `CreatedBy`, `UpdatedAtUtc`, `UpdatedBy`.
- Tenant isolation: `ICompanyScoped` (`CompanyId`).
- Decimal default: `numeric(18,2)` for `decimal`/`decimal?` properties.
- Extensions: `uuid-ossp` enabled via `modelBuilder.HasPostgresExtension("uuid-ossp")` — provider-specific.
- Seed data uses anonymous types with shadow `Xmin = 0u`.

### Data Models — Identity
- Infrastructure models:
  - `ApplicationUser : IdentityUser<long>` with `DisplayName`, `BranchId?`, `IsEnabled`, `CreatedAtUtc`, `LastLoginAtUtc`.
  - `ApplicationRole : IdentityRole<long>` with `Description`, `DisplayOrder`.
- Domain models separate:
  - `Modules.Identity.Domain.User : BaseEntity` with `DisplayName`, `Email`, `UserName`, `BranchId?`, `IsEnabled`, `CreatedAtUtc`, `LastLoginAtUtc`, `PasswordHash`, `FailedLoginAttempts`, `LockedUntilUtc`, domain methods `RecordSuccessfulLogin/RecordFailedLogin/Lock/Unlock/Deactivate/Activate`.
  - `Modules.Identity.Domain.Role : BaseEntity` with `Name`, `NormalizedName`, `Description`, `DisplayOrder`.
- Mapping via `ApplicationUserMapper.ToDomain` for Application layer use.
- Identity tables are snake_cased via `IdentityDbContext.OnModelCreating`. No `xmin` concurrency added to Identity context currently.
- Design-time factory `IdentityDbContextFactory` hardcodes Npgsql connection string.

### State Management — Auth & Cookies
- Cookie-based auth only. No OAuth/OIDC providers.
- `AddIdentity<ApplicationUser,ApplicationRole>` configured:
  - Password: 8 min, digit/lower/upper/non-alphanumeric.
  - Lockout: 5 attempts / 15 min, allowed for new users.
  - Unique email required, require confirmed email.
- Cookie options:
  - `LoginPath=/Accounts/Login`, `LogoutPath=/Accounts/Logout`, `AccessDeniedPath=/Accounts/AccessDenied`.
  - `ExpireTimeSpan=8h`, `SlidingExpiration=true`.
  - `HttpOnly=true`, `SameSite=Lax`, `SecurePolicy=SameAsRequest`.
- Data Protection:
  - `services.AddDataProtection().PersistKeysToFileSystem(new DirectoryInfo(configuration["Security:DataProtectionPath"] ?? "./dataprotection-keys")).SetApplicationName("SmeAccounting")`.
  - Keys persisted to filesystem; multi-instance requires external store.
- Authorization:
  - `PermissionPolicyProvider` intercepts `"Permission:{name}"` → `PermissionRequirement`.
  - `PermissionAuthorizationHandler` grants if user has permission claim or `Users.ManageRoles` admin bypass.
  - Permission types defined in `Modules.Identity.Application.Permissions`.
- Auth state stored in encrypted cookie + DataProtection; no server-side session store.

### Multi-DBMS Constraints
- Goal: EF Core provider selectable at runtime; PostgreSQL 16 default, MariaDB/SQLite/SQL Server supported.
- Current hardcoding:
  - `SmeAccounting.Infrastructure.DependencyInjection.AddInfrastructure` → `options.UseNpgsql(connectionString)`.
  - `IdentityServiceExtensions.AddIdentityInfrastructure` → `options.UseNpgsql(configuration.GetConnectionString("DefaultConnection"))`.
  - `IdentityDbContextFactory.CreateDbContext` hardcodes Npgsql.
- Required changes:
  - Runtime provider selection based on connection string / config flag.
  - Provider-specific packages: `Pomelo.EntityFrameworkCore.MySql` for MariaDB, `Microsoft.EntityFrameworkCore.Sqlite`, `Microsoft.EntityFrameworkCore.SqlServer`.
  - Remove PostgreSQL-only features or make conditional:
    - `HasPostgresExtension("uuid-ossp")`
    - `NpgsqlValueGenerationStrategy.IdentityByDefaultColumn`
    - `xmin` shadow concurrency token
  - Snake_case naming must remain provider-agnostic.
  - Migrations must be provider-agnostic or generated per provider; fail-fast pending migration check remains.
- Connection string priority: `SME_ACCT_CONNECTION_STRING` env var > appsettings `ConnectionStrings:DefaultConnection`.
- No external auth APIs; all state remains cookie + DataProtection.

### Non-Negotiables
- Clean Architecture layer rules enforced by ArchitectureTests.
- Module registry explicit, no reflection.
- `TreatWarningsAsErrors=true`, `AnalysisLevel=latest-recommended`, `EnforceCodeStyleInBuild=true`.
- Identity module must stay cookie-only; no third-party auth libraries.
- Migrations fail-fast at startup unless `Testing` environment.

## Environment & Integration
### Build & Toolchain
- .NET SDK pinned 10.0.401 via global.json, rollForward latestFeature.
- global.json test.runner = Microsoft.Testing.Platform.
- Directory.Build.props: TargetFramework net10.0, LangVersion 14.0, Nullable enable, ImplicitUsings enable, TreatWarningsAsErrors true, AnalysisLevel latest-recommended, EnforceCodeStyleInBuild true, GenerateDocumentationFile false, UseArtifactsOutput true.
- NoWarn includes NETSDK1188;CA1000;IDE0161;CA1861;CA1848;CA1873.
- Central Package Management via Directory.Packages.props, locked mode required, --locked-mode in CI.
- .slnx format, UseArtifactsOutput true → artifacts/{bin,obj}/{Project}/{Config}/.
- Global tools installed WSL2 Kali: dotnet-ef 10.0.12, LibMan CLI 3.0.114. Use dotnet tool restore in CI, verify with dotnet tool list -g.
- xunit.v3 projects require OutputType=Exe + UseAppHost + <Using Include="Xunit"/>; mixing VSTest + MTP fails.
- Build commands: dotnet build -c Release SmeAccounting.slnx, dotnet test, dotnet ef migrations add/update via scripts/ef-migrations.sh.

### CI/CD
- GitHub Actions workflow .github/workflows/ci.yml:
  - triggers push/PR to main.
  - runs-on ubuntu-latest.
  - actions/checkout@v4, actions/setup-dotnet@v4 with dotnet-version 10.0.x.
  - steps: dotnet restore --locked-mode, dotnet build -c Release --no-restore, dotnet test -c Release --no-build, dotnet publish src/SmeAccounting.Api/SmeAccounting.Api.csproj -c Release -o artifacts/publish, upload artifact.
- No explicit MariaDB setup in CI workflow currently; global memory notes shogo82148/actions-setup-mysql@v1 distribution mariadb for tests.
- CI uses locked mode restore.

### Docker & Infrastructure
- Dockerfile at deploy/Dockerfile:
  - Build stage: mcr.microsoft.com/dotnet/sdk:10.0 AS build, WORKDIR /src, copies Directory.Build.props/targets/Packages.props, restores Api project, copies src/, dotnet publish -c Release -o /app/publish --no-restore.
  - Runtime stage: mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled AS runtime, WORKDIR /app, EXPOSE 8080, ENV ASPNETCORE_URLS=http://+:8080, DOTNET_gcServer=1, copy publish, USER 1654, ENTRYPOINT ["dotnet","SmeAccounting.Api.dll"].
- docker-compose.yml at deploy/docker-compose.yml:
  - services app builds context .. dockerfile deploy/Dockerfile, ports 5000:8080, env ConnectionStrings__DefaultConnection=Host=db;Port=5432;Database=sme_accounting;Username=postgres;Password=postgres, ASPNETCORE_ENVIRONMENT=Production, depends_on db healthy, restart unless-stopped.
  - db service image postgres:16.14-alpine, ports 5432:5432, env POSTGRES_DB/USER/PASSWORD, volume pgdata, healthcheck pg_isready, restart unless-stopped.
- Runtime environment WSL2 Kali discovered: .NET SDK 10.0.401, MariaDB client 11.8.6, Git 2.51.0, Node v26.5.0, curl, sed. Global tools dotnet-ef 10.0.12, LibMan 3.0.114. NOT installed: jq, Docker, mariadb-dump.
- Deploy options per global memory: Windows IIS in-process or Linux Kestrel + Nginx + systemd with ForwardedHeaders.
- EF migrations idempotent SQL script or migration bundle for review-gated on-premise deploys.
- Connection string priority: SME_ACCT_CONNECTION_STRING env var > appsettings ConnectionStrings:DefaultConnection.
- DataProtection keys persisted to filesystem Security:DataProtectionPath or ./dataprotection-keys; multi-instance needs external store.
- ForwardedHeaders configured for Nginx reverse proxy.

### Integration Notes
- No .env.example file found; configuration env-var driven.
- No GitHub Actions workflow for MariaDB tests currently present; global memory references actions-setup-mysql for MariaDB tests.
- Docker compose currently hardcodes PostgreSQL 16.14-alpine; multi-DBMS support requires compose overrides or provider selection via connection string.
- Build artifacts output to artifacts/bin/.../release per UseArtifactsOutput.

## Task-Specific Research
## Task-Specific Research — [G1] Audit Identity and Infrastructure DI for hard-coded Npgsql and PostgreSQL-only features

### Hard-coded Npgsql / PostgreSQL provider usage in DI

**Infrastructure DI**
- `src/SmeAccounting.Infrastructure/DependencyInjection.cs:32-39`
  - `services.AddDbContext<SmeAccountingDbContext>(options => options.UseNpgsql(connectionString, ...))`
  - Connection string fallback hard-coded to PostgreSQL host/port/db/user/password.
  - `UseNpgsql` with `EnableRetryOnFailure(3)` and `CommandTimeout(30)` — provider-specific options.

**Identity DI**
- `src/Modules/Identity/Infrastructure/IdentityServiceExtensions.cs:15-16`
  - `services.AddDbContext<IdentityDbContext>(options => options.UseNpgsql(configuration.GetConnectionString("DefaultConnection")))`
  - No provider selection; assumes PostgreSQL connection string.
- `src/Modules/Identity/Infrastructure/IdentityModuleExtensions.cs:8-13`
  - Calls `AddIdentityInfrastructure(configuration)` which registers Npgsql.

**Design-time factories**
- `src/SmeAccounting.Infrastructure/Persistence/DesignTimeDbContextFactory.cs:11-14`
  - `optionsBuilder.UseNpgsql(connectionString, o => o.EnableRetryOnFailure())`
  - Connection string fallback hard-coded to PostgreSQL.
- `src/Modules/Identity/Infrastructure/IdentityDbContextFactory.cs:11`
  - `optionsBuilder.UseNpgsql("Host=localhost;Port=5432;Database=sme_accounting;Username=postgres;Password=postgres")`
  - Hard-coded PostgreSQL connection string.

**Tests**
- `tests/SmeAccounting.Infrastructure.Tests/DatabaseIntegrationTests.cs:31`
  - `options.UseNpgsql(_postgres.GetConnectionString())`
  - Test setup assumes PostgreSQL Testcontainers.

**Package references**
- `src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj:19`
  - `<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" />`
- `src/Modules/Identity/Infrastructure/SmeAccounting.Modules.Identity.Infrastructure.csproj:16`
  - `<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" />`

### PostgreSQL-only model building features

**SmeAccountingDbContext**
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:26`
  - `modelBuilder.HasPostgresExtension("uuid-ossp");` — PostgreSQL extension.
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:37`
  - `entityType.FindProperty("Id")!.SetAnnotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn);`
  - Npgsql-specific annotation for `bigint GENERATED BY DEFAULT AS IDENTITY`.
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:40-50`
  - Shadow property `Xmin` added for every `BaseEntity` subtype:
    - `entityType.AddProperty("Xmin", typeof(uint))`
    - `SetColumnName("xmin")`
    - `SetColumnType("xid")`
    - `IsConcurrencyToken = true`
    - `SetBeforeSaveBehavior(PropertySaveBehavior.Ignore)`
    - `SetAfterSaveBehavior(PropertySaveBehavior.Ignore)`
  - `xid` is PostgreSQL system type; concurrency token is PostgreSQL-specific.

**Migrations**
- `src/SmeAccounting.Infrastructure/Migrations/20260914031632_InitialFoundationXminV3.cs`
  - Columns defined as `type: "xid"` and annotations `Npgsql:ValueGenerationStrategy`.
- `src/SmeAccounting.Infrastructure/Migrations/SmeAccountingDbContextModelSnapshot.cs:23`
  - `NpgsqlModelBuilderExtensions.HasPostgresExtension(modelBuilder, "uuid-ossp");`
- Seed data in `OnModelCreating.SeedData` includes `Xmin = 0u` for Company/Branch.

**IdentityDbContext**
- No PostgreSQL-specific model building currently, but DI forces Npgsql.

### Program / composition root
- `src/SmeAccounting.Api/Program.cs:27-28`
  - `builder.Services.AddInfrastructure(builder.Configuration);`
  - `builder.Services.AddIdentityModule(builder.Configuration);`
  - No provider selection logic; relies on hard-coded DI.

### Impact for multi-DBMS
- Provider selection cannot change at runtime; `UseNpgsql` is baked into DI and factories.
- Model building assumes PostgreSQL:
  - `HasPostgresExtension`
  - `NpgsqlValueGenerationStrategy.IdentityByDefaultColumn`
  - `xmin` shadow concurrency token with `xid` type
- Migrations contain PostgreSQL-specific annotations and column types.
- Design-time factories hard-code PostgreSQL connection strings.
- Tests assume PostgreSQL Testcontainers.

### Files requiring changes for abstraction
- `src/SmeAccounting.Infrastructure/DependencyInjection.cs`
- `src/SmeAccounting.Infrastructure/Persistence/DesignTimeDbContextFactory.cs`
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`
- `src/Modules/Identity/Infrastructure/IdentityServiceExtensions.cs`
- `src/Modules/Identity/Infrastructure/IdentityDbContextFactory.cs`
- `src/Modules/Identity/Infrastructure/IdentityModuleExtensions.cs`
- `tests/SmeAccounting.Infrastructure.Tests/DatabaseIntegrationTests.cs`
- `src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj`
- `src/Modules/Identity/Infrastructure/SmeAccounting.Modules.Identity.Infrastructure.csproj`

### Suggested audit checklist for executor
- Replace `UseNpgsql` with provider-agnostic registration based on config/connection string.
- Remove or conditionally apply `HasPostgresExtension`, `NpgsqlValueGenerationStrategy`, `xmin` shadow property.
- Make design-time factories read provider from config/env.
- Update migrations/snapshot handling for provider-agnostic schema.
- Add conditional EF provider packages for MariaDB/SQLite/SQL Server.
- Ensure snake_case naming convention remains provider-agnostic.

## Task-Specific Research — [G1] Map provider-specific code paths for abstraction (xmin concurrency, uuid-ossp, IdentityByDefaultColumn, snake_case)

### Provider-specific code paths identified

#### 1. xmin concurrency token (PostgreSQL-only)
- **Location**: `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:40-50`
  - Adds shadow property `Xmin` type `uint` for every `BaseEntity` subtype
  - `SetColumnName("xmin")`, `SetColumnType("xid")`
  - `IsConcurrencyToken = true`
  - `SetBeforeSaveBehavior(PropertySaveBehavior.Ignore)`, `SetAfterSaveBehavior(PropertySaveBehavior.Ignore)`
  - Comment explicitly notes PostgreSQL system column
- **Seed data**: `SmeAccountingDbContext.cs:91-107`, `109-126` includes `Xmin = 0u` in anonymous seed objects
- **Migrations**:
  - `src/SmeAccounting.Infrastructure/Migrations/20260914031632_InitialFoundationXminV3.cs:39,67,90,114` defines `xmin = table.Column<uint>(type: "xid", nullable: false)`
  - `src/SmeAccounting.Infrastructure/Migrations/SmeAccountingDbContextModelSnapshot.cs:102,166,231,307` maps column name `xmin`
  - `src/SmeAccounting.Infrastructure/Migrations/20260914032154_Circular133COASeed.cs` inserts include `xmin` column
- **Impact**: `xid` type and `xmin` system column exist only in PostgreSQL. MariaDB/SQLite/SQL Server require alternative concurrency token (e.g., `rowversion`, `timestamp`, or EF `ConcurrencyCheck` column).

#### 2. uuid-ossp extension (PostgreSQL-only)
- **Location**: `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:26`
  - `modelBuilder.HasPostgresExtension("uuid-ossp");`
- **Migrations**:
  - `src/SmeAccounting.Infrastructure/Migrations/20260914031632_InitialFoundationXminV3.cs:15-16` `migrationBuilder.AlterDatabase().Annotation("Npgsql:PostgresExtension:uuid-ossp", ",,");`
  - `src/SmeAccounting.Infrastructure/Migrations/SmeAccountingDbContextModelSnapshot.cs:23` `NpgsqlModelBuilderExtensions.HasPostgresExtension(modelBuilder, "uuid-ossp");`
  - Designer files repeat same annotation
- **Impact**: Extension creation is PostgreSQL-specific; other providers have built-in UUID generation or different extension names.

#### 3. IdentityByDefaultColumn (Npgsql-specific annotation)
- **Location**: `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:37`
  - `entityType.FindProperty("Id")!.SetAnnotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn);`
  - Applied to all `BaseEntity` with `long Id`
- **Migrations**:
  - `src/SmeAccounting.Infrastructure/Migrations/20260914031632_InitialFoundationXminV3.cs:23,56,79,102` `.Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn)`
  - Snapshot repeats annotation
- **Imports**: `using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;` in `SmeAccountingDbContext.cs:4`
- **Impact**: Annotation is Npgsql-specific. MariaDB uses `MySqlValueGenerationStrategy.IdentityColumn`, SQL Server uses `SqlServerValueGenerationStrategy.IdentityColumn`, SQLite uses `SqliteValueGenerationStrategy.IdentityColumn`. Provider-agnostic alternative is `entityType.FindProperty("Id")!.ValueGeneratedOnAdd()` or rely on EF conventions per provider.

#### 4. snake_case naming convention (provider-agnostic but custom)
- **Location**: `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:27` calls `ApplySnakeCaseNamingConvention(modelBuilder)`
- **Implementation**: `ApplySnakeCaseNamingConvention` at `129-148`
  - Converts table names, column names, FK constraint names via `ToSnakeCase`
  - `ToSnakeCase` at `150-168` manual PascalCase → snake_case conversion
- **Identity context**: `src/Modules/Identity/Infrastructure/IdentityDbContext.cs:13-34`
  - Own `OnModelCreating` loops entity types, calls `ToSnakeCase` for table and column names
  - `ToSnakeCase` at `37-55` duplicate implementation
- **Provider impact**: Snake_case logic is provider-agnostic and safe for all DBMS. However, duplicate `ToSnakeCase` implementations exist; could be extracted to shared kernel. No provider-specific dependencies.
- **Note**: Comment at `SmeAccountingDbContext.cs:29` mentions `modelBuilder.UseSnakeCaseNamingConvention()` requires Npgsql EF Core 9 convention extension — not used.

#### 5. Hard-coded Npgsql DI registration
- **Infrastructure**: `src/SmeAccounting.Infrastructure/DependencyInjection.cs:32-39`
  - `services.AddDbContext<SmeAccountingDbContext>(options => options.UseNpgsql(connectionString, ...))`
  - Connection string fallback hard-coded to PostgreSQL host/port
- **Identity**: `src/Modules/Identity/Infrastructure/IdentityServiceExtensions.cs:15-16`
  - `services.AddDbContext<IdentityDbContext>(options => options.UseNpgsql(configuration.GetConnectionString("DefaultConnection")))`
- **Design-time factories**:
  - `src/SmeAccounting.Infrastructure/Persistence/DesignTimeDbContextFactory.cs:14` `optionsBuilder.UseNpgsql(connectionString, o => o.EnableRetryOnFailure())`
  - `src/Modules/Identity/Infrastructure/IdentityDbContextFactory.cs:11` hard-coded `UseNpgsql("Host=localhost;Port=5432;Database=sme_accounting;Username=postgres;Password=postgres")`
- **Tests**: `tests/SmeAccounting.Infrastructure.Tests/DatabaseIntegrationTests.cs:31` `options.UseNpgsql(_postgres.GetConnectionString())`
- **Packages**:
  - `src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj` references `Npgsql.EntityFrameworkCore.PostgreSQL`
  - `src/Modules/Identity/Infrastructure/SmeAccounting.Modules.Identity.Infrastructure.csproj` references `Npgsql.EntityFrameworkCore.PostgreSQL`

### Abstraction mapping summary

- **xmin concurrency**: Must be conditional on PostgreSQL provider; alternative concurrency strategy needed for MariaDB/SQLite/SQL Server. Shadow property creation, column type `xid`, seed data inclusion all provider-specific.
- **uuid-ossp**: Conditional `HasPostgresExtension` call; remove for non-PostgreSQL providers.
- **IdentityByDefaultColumn**: Replace Npgsql annotation with provider-agnostic value generation or conditional per provider. Remove `Npgsql.EntityFrameworkCore.PostgreSQL.Metadata` import or guard usage.
- **snake_case**: Already provider-agnostic; keep as-is. Consider consolidating duplicate `ToSnakeCase` implementations into `SharedKernel` to avoid drift.
- **DI registration**: Centralize provider selection logic based on connection string / config flag; replace hard-coded `UseNpgsql` with switch to `UseNpgsql` / `UseMySql` / `UseSqlite` / `UseSqlServer`.

### Files requiring abstraction changes
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`
- `src/SmeAccounting.Infrastructure/DependencyInjection.cs`
- `src/SmeAccounting.Infrastructure/Persistence/DesignTimeDbContextFactory.cs`
- `src/Modules/Identity/Infrastructure/IdentityServiceExtensions.cs`
- `src/Modules/Identity/Infrastructure/IdentityDbContextFactory.cs`
- `src/Modules/Identity/Infrastructure/IdentityDbContext.cs` (snake_case duplication)
- `src/SmeAccounting.Infrastructure/Migrations/*` (generated; will be regenerated per provider)
- `tests/SmeAccounting.Infrastructure.Tests/DatabaseIntegrationTests.cs`

### Suggested approach for executor
1. Introduce provider selector service reading connection string / config key `DatabaseProvider` (Postgres/MariaDB/SQLite/SqlServer).
2. Guard PostgreSQL-only model building: `if (provider == Postgres) { HasPostgresExtension; xmin shadow; Npgsql annotation }`
3. Replace `UseNpgsql` calls with provider switch in `AddInfrastructure` and `AddIdentityInfrastructure`.
4. Make design-time factories read provider from env var `SME_ACCT_DB_PROVIDER` and connection string.
5. Keep `ApplySnakeCaseNamingConvention` unchanged; extract `ToSnakeCase` to `SharedKernel` utility.
6. Update tests to support provider selection; keep PostgreSQL as default for CI.

