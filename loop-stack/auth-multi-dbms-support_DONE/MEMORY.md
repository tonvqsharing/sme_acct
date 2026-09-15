# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
- Audit completed for hard-coded Npgsql/PostgreSQL in Identity and Infrastructure DI
- Provider code map created at docs/provider-code-map.md
- Hard-coded UseNpgsql found in:
  - src/SmeAccounting.Infrastructure/DependencyInjection.cs:32-39
  - src/Modules/Identity/Infrastructure/IdentityServiceExtensions.cs:15-16
  - src/SmeAccounting.Infrastructure/Persistence/DesignTimeDbContextFactory.cs:11-14
  - src/Modules/Identity/Infrastructure/IdentityDbContextFactory.cs:11
- PostgreSQL-only model features:
  - SmeAccountingDbContext.HasPostgresExtension("uuid-ossp")
  - NpgsqlValueGenerationStrategy.IdentityByDefaultColumn annotation
  - xmin shadow concurrency token with type xid
  - Seed data includes Xmin = 0u
  - Migrations contain Npgsql annotations and xid columns
- Package references hard-coded to Npgsql.EntityFrameworkCore.PostgreSQL in Infrastructure and Identity.Infrastructure csproj
- Snake_case naming is provider-agnostic; ToSnakeCase duplicated in SmeAccountingDbContext and IdentityDbContext
- Audit report written to docs/audit-identity-infrastructure-di.md
- 2026-09-14: Verified audit report exists at docs/audit-identity-infrastructure-di.md with BLOCK findings; MEMORY and STATUS updated; no code changes per audit task

