# Research Log
## Context & Prior Work
Global context:
- .NET 10 LTS, ASP.NET Core 10, EF Core 9 via Pomelo.EntityFrameworkCore.MySql 9.0.0 per loop-stack/.global/MEMORY.md
- MariaDB 10.6+ LTS target, utf8mb4 charset
- Clean Architecture modular monolith, single DbContext SmeAccountingDbContext centralized in Infrastructure
- DbProviderSelector exists with DatabaseProvider enum PostgreSql/MariaDb/Sqlite/SqlServer, Resolve/ResolveConnectionString/Configure for all four providers

SmeAccountingDbContext (src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs):
- PostgreSQL-specific imports: Npgsql.EntityFrameworkCore.PostgreSQL.Metadata
- OnModelCreating:
  - modelBuilder.HasPostgresExtension("uuid-ossp")
  - Identity generation via NpgsqlValueGenerationStrategy.IdentityByDefaultColumn for long Id on BaseEntity
  - Shadow property Xmin type uint column "xmin" type "xid", IsConcurrencyToken=true, BeforeSaveBehavior.Ignore, AfterSaveBehavior.Ignore — PostgreSQL system column
  - Decimal default numeric(18,2)
  - Snake_case naming convention applied manually
  - Seed data includes Xmin = 0u
- Migrations generated with Npgsql annotations:
  - InitialFoundationXminV3.cs uses Npgsql.EntityFrameworkCore.PostgreSQL.Metadata, column types bigint with Npgsql:ValueGenerationStrategy.IdentityByDefaultColumn, timestamp with time zone, uuid, xid
  - ModelSnapshot references NpgsqlModelBuilderExtensions.HasPostgresExtension, UseIdentityByDefaultColumns, NpgsqlPropertyBuilderExtensions.UseIdentityByDefaultColumn

IdentityDbContext (src/Modules/Identity/Infrastructure/IdentityDbContext.cs):
- Inherits IdentityDbContext<ApplicationUser, ApplicationRole, long>
- OnModelCreating only applies snake_case table/column renaming, no provider-specific logic
- IdentityServiceExtensions.AddIdentityInfrastructure hardcodes options.UseNpgsql(configuration.GetConnectionString("DefaultConnection"))
- IdentityDbContextFactory uses DbProviderSelector.Resolve/Configure for design-time, so factory is provider-neutral but runtime registration is PostgreSQL-only

Migrations & design-time:
- DesignTimeDbContextFactory for SmeAccountingDbContext uses DbProviderSelector.Resolve/Configure — provider-neutral factory
- IdentityDbContextFactory also uses DbProviderSelector
- Existing migrations are PostgreSQL-only; no provider-specific conditional model building present
- DbProviderSelector.Configure sets MigrationsAssembly for all providers, enables retry, command timeout

Provider-specific code summary:
- SmeAccountingDbContext contains PostgreSQL-only features: uuid-ossp extension, Npgsql identity strategy, xmin concurrency token, xid column type
- Identity infrastructure runtime registration is PostgreSQL-only
- No conditional model building based on provider; no abstraction for identity generation, concurrency token, or extension per provider
## External Knowledge & Resources
(pending)
## Requirements & Constraints
- Provider-conditional model building required for identity generation, concurrency token, extensions, decimal precision, snake_case naming
- Must support PostgreSQL, MariaDB/MySQL, SQLite, SQL Server
- Existing PostgreSQL-specific code must be isolated behind provider check
- Seed data currently includes Xmin shadow property; must remain compatible or be conditionally seeded
- Migrations must remain provider-agnostic where possible; existing migrations are Npgsql-only
- DbProviderSelector already resolves provider from configuration; runtime DI uses it for SmeAccountingDbContext
- Identity infrastructure runtime registration currently hardcodes UseNpgsql; needs provider-neutral update (separate task)
- Snake_case naming convention currently manual; should remain for all providers
- Decimal precision default numeric(18,2) works for PostgreSQL/MariaDB/SQL Server; SQLite uses REAL/NUMERIC
- Concurrency token xmin is PostgreSQL-specific; MariaDB/MySQL/SQL Server/SQLite need alternative (rowversion/timestamp or none)
- Identity generation: PostgreSQL uses IdentityByDefaultColumn; MariaDB uses AUTO_INCREMENT; SQL Server uses IDENTITY; SQLite uses AUTOINCREMENT
- uuid-ossp extension is PostgreSQL-only
## Task-Specific Research — [G1] Refactor SmeAccountingDbContext
- Current SmeAccountingDbContext.OnModelCreating (src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs):
  - Imports Npgsql.EntityFrameworkCore.PostgreSQL.Metadata
  - Calls modelBuilder.HasPostgresExtension("uuid-ossp") unconditionally
  - Applies snake_case naming via ApplySnakeCaseNamingConvention
  - Loops entities: if BaseEntity and Id long → SetAnnotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn)
  - Adds shadow property Xmin uint column "xmin" type "xid", IsConcurrencyToken=true, BeforeSaveBehavior.Ignore, AfterSaveBehavior.Ignore for all BaseEntity types
  - Sets decimal properties column type "numeric(18,2)" unconditionally
  - Soft delete query filter applied
  - SeedData includes Xmin = 0u for Company and Branch
- Provider detection options:
  - DbContextOptions can be inspected via modelBuilder.Model.GetProviderName() or via Database.ProviderName after context initialized
  - DbProviderSelector.Resolve(configuration) already used in DI and design-time factories; provider can be passed via DbContext option extension or via service locator
  - Simpler: detect provider name string from modelBuilder.Model.GetRelationalModel() or from options.Extensions
- Required refactor steps:
  1. Remove unconditional Npgsql imports and HasPostgresExtension call; guard with provider check
  2. Replace Npgsql identity annotation with provider-specific identity configuration:
     - PostgreSQL: NpgsqlValueGenerationStrategy.IdentityByDefaultColumn or UseIdentityByDefaultColumn
     - MariaDB/MySQL: UseMySql identity via annotation or convention; Pomelo supports UseMySql with ServerVersion.AutoDetect
     - SQL Server: UseIdentityColumn
     - SQLite: UseAutoincrement
  3. Conditionally add concurrency token:
     - PostgreSQL: xmin shadow property as current
     - Others: remove xmin; optionally add RowVersion for SQL Server, or no concurrency token
  4. Decimal precision: keep numeric(18,2) for relational providers; for SQLite use "NUMERIC"
  5. Extension: HasPostgresExtension only for PostgreSQL
  6. Seed data: conditionally include Xmin only for PostgreSQL; otherwise omit property
  7. Snake_case naming: keep for all providers
- Existing dependencies:
  - BaseEntity.Id long, BaseEntity used for identity check
  - ISoftDeletable interface used for query filter
  - ApplySnakeCaseNamingConvention manually loops entity types
- Risks:
  - Existing migrations contain Npgsql annotations and xmin columns; changing model building may cause migration diffs
  - Seed data with Xmin will fail for non-PostgreSQL providers if property remains
  - Tests DatabaseIntegrationTests verify snake_case naming, bigint PKs, soft-delete filter, seed data presence
- Verification criteria:
  - OnModelCreating runs without Npgsql exceptions on MariaDB/SQLite/SQLServer
  - Model snapshot no longer contains Npgsql-specific annotations for non-PostgreSQL builds
  - Identity columns configured per provider
  - Concurrency token present only for PostgreSQL
  - Decimal columns typed correctly per provider
  - Snake_case naming preserved

## Task-Specific Research — [G1] Remove PostgreSQL-only usings and HasPostgresExtension from SmeAccountingDbContext
- Target file: src/SmeAccounting.Infrastructure/Persistence/SmeAccountingDbContext.cs
- Current PostgreSQL-only using:
  - Line 4: `using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;`
- Current PostgreSQL-only call:
  - Line 26: `modelBuilder.HasPostgresExtension("uuid-ossp");`
- Related PostgreSQL-only references in same file:
  - Line 37: `entityType.FindProperty("Id")!.SetAnnotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn);`
  - Uses NpgsqlValueGenerationStrategy from removed namespace; will require fully-qualified name or removal in subsequent task [G1] Remove NpgsqlValueGenerationStrategy annotation
  - Comment line 29 references Npgsql EF Core 9 convention extension
- Provider detection available:
  - DbProviderSelector.Resolve(IConfiguration) returns DatabaseProvider enum
  - DbContextOptions can be inspected via `modelBuilder.Model.GetRelationalModel()` provider name or `Database.ProviderName` after initialization
  - Design-time factory already uses DbProviderSelector for provider-neutral configuration
- Impact:
  - Removing using will break compilation if NpgsqlValueGenerationStrategy usage remains; next task removes/replaces that annotation
  - Removing HasPostgresExtension eliminates uuid-ossp extension registration for all providers; extension is PostgreSQL-only and should be guarded or removed
  - Migrations and ModelSnapshot contain NpgsqlModelBuilderExtensions.HasPostgresExtension; they will be regenerated on next migration
- Existing tests to verify:
  - tests/SmeAccounting.Infrastructure.Tests/DatabaseIntegrationTests.cs verifies snake_case naming, bigint PKs, soft-delete filter, seed data presence
- Verification criteria for this task:
  - `using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;` absent from SmeAccountingDbContext.cs
  - `modelBuilder.HasPostgresExtension("uuid-ossp");` absent from OnModelCreating
  - File builds without Npgsql-specific using errors after subsequent task removes NpgsqlValueGenerationStrategy usage
  - No runtime exception when OnModelCreating executes under MariaDB/SQLite/SQLServer provider

