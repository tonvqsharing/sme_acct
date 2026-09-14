# Audit: Identity and Infrastructure DI – Hard-coded Npgsql / PostgreSQL-only Features

Date: 2026-09-14
Task: [G1] Audit Identity and Infrastructure DI for hard-coded Npgsql and PostgreSQL-only features

## Summary
Hard-coded PostgreSQL/Npgsql usage found in DI registration, design-time factories, model building, and package references. Provider selection is not runtime-configurable. PostgreSQL-only model features block multi-DBMS support.

## Hard-coded Npgsql in DI

### Infrastructure
- `src/SmeAccounting.Infrastructure/DependencyInjection.cs:32-39`
  - `services.AddDbContext<SmeAccountingDbContext>(options => options.UseNpgsql(connectionString, ...))`
  - Connection string fallback: `Host=localhost;Port=5432;Database=smeaccounting;Username=postgres;Password=postgres`
  - Npgsql-specific options: `EnableRetryOnFailure(3)`, `CommandTimeout(30)`

### Identity
- `src/Modules/Identity/Infrastructure/IdentityServiceExtensions.cs:15-16`
  - `services.AddDbContext<IdentityDbContext>(options => options.UseNpgsql(configuration.GetConnectionString("DefaultConnection")))`
- `src/Modules/Identity/Infrastructure/IdentityModuleExtensions.cs:8-13`
  - Calls `AddIdentityInfrastructure(configuration)` which registers Npgsql

### Design-time factories
- `src/SmeAccounting.Infrastructure/Persistence/DesignTimeDbContextFactory.cs:11-14`
  - `optionsBuilder.UseNpgsql(connectionString, o => o.EnableRetryOnFailure())`
  - Connection string fallback hard-coded to PostgreSQL
- `src/Modules/Identity/Infrastructure/IdentityDbContextFactory.cs:11`
  - `optionsBuilder.UseNpgsql("Host=localhost;Port=5432;Database=sme_accounting;Username=postgres;Password=postgres")`
  - Hard-coded PostgreSQL connection string

### Tests
- `tests/SmeAccounting.Infrastructure.Tests/DatabaseIntegrationTests.cs:31`
  - `options.UseNpgsql(_postgres.GetConnectionString())`
  - Assumes PostgreSQL Testcontainers

### Package references
- `src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj:19`
  - `<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" />`
- `src/Modules/Identity/Infrastructure/SmeAccounting.Modules.Identity.Infrastructure.csproj:16`
  - `<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" />`

## PostgreSQL-only model building features

### SmeAccountingDbContext
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:26`
  - `modelBuilder.HasPostgresExtension("uuid-ossp");`
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:37`
  - `entityType.FindProperty("Id")!.SetAnnotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn);`
  - Import: `using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;`
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:40-50`
  - Shadow property `Xmin` added for every `BaseEntity` subtype:
    - `entityType.AddProperty("Xmin", typeof(uint))`
    - `SetColumnName("xmin")`
    - `SetColumnType("xid")`
    - `IsConcurrencyToken = true`
    - `SetBeforeSaveBehavior(PropertySaveBehavior.Ignore)`
    - `SetAfterSaveBehavior(PropertySaveBehavior.Ignore)`
  - `xid` is PostgreSQL system type

### Seed data
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs:91-107,109-126`
  - Seed objects include `Xmin = 0u`

### Migrations
- `src/SmeAccounting.Infrastructure/Migrations/20260914031632_InitialFoundationXminV3.cs`
  - Columns `type: "xid"` and annotations `Npgsql:ValueGenerationStrategy`
- `src/SmeAccounting.Infrastructure/Migrations/SmeAccountingDbContextModelSnapshot.cs:23`
  - `NpgsqlModelBuilderExtensions.HasPostgresExtension(modelBuilder, "uuid-ossp");`
- Seed inserts include `xmin` column

### IdentityDbContext
- No PostgreSQL-specific model building, but DI forces Npgsql
- Snake_case naming via manual `ToSnakeCase` – provider-agnostic

## Composition root
- `src/SmeAccounting.Api/Program.cs:27-28`
  - `builder.Services.AddInfrastructure(builder.Configuration);`
  - `builder.Services.AddIdentityModule(builder.Configuration);`
  - No provider selection logic

## Impact
- Provider cannot change at runtime
- Model building assumes PostgreSQL: `HasPostgresExtension`, `NpgsqlValueGenerationStrategy`, `xmin` shadow concurrency token with `xid`
- Migrations contain PostgreSQL-specific annotations and column types
- Design-time factories hard-code PostgreSQL connection strings
- Tests assume PostgreSQL Testcontainers

## Files requiring changes for abstraction
- `src/SmeAccounting.Infrastructure/DependencyInjection.cs`
- `src/SmeAccounting.Infrastructure/Persistence/DesignTimeDbContextFactory.cs`
- `src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs`
- `src/Modules/Identity/Infrastructure/IdentityServiceExtensions.cs`
- `src/Modules/Identity/Infrastructure/IdentityDbContextFactory.cs`
- `src/Modules/Identity/Infrastructure/IdentityModuleExtensions.cs`
- `tests/SmeAccounting.Infrastructure.Tests/DatabaseIntegrationTests.cs`
- `src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj`
- `src/Modules/Identity/Infrastructure/SmeAccounting.Modules.Identity.Infrastructure.csproj`

## Recommendations
1. Introduce provider selector based on config/connection string or `DatabaseProvider` setting
2. Guard PostgreSQL-only model building: conditional `HasPostgresExtension`, `xmin`, Npgsql annotation
3. Replace `UseNpgsql` with provider switch in `AddInfrastructure` and `AddIdentityInfrastructure`
4. Make design-time factories read provider from env var `SME_ACCT_DB_PROVIDER`
5. Keep `ApplySnakeCaseNamingConvention` unchanged; extract `ToSnakeCase` to SharedKernel
6. Add conditional EF provider packages for MariaDB/SQLite/SQL Server
7. Update tests to support provider selection; keep PostgreSQL as default for CI
