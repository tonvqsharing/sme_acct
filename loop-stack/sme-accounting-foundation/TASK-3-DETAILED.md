# Task 3 [G3] Detailed Implementation Plan
**Pillar:** Database Strategy & Persistence
**Baseline:** PostgreSQL 16.14 / EF Core 10 / Npgsql
**Status:** IN PROGRESS

## Preconditions
- Task 1 Solution Skeleton & Build Conventions DONE
- Task 2 Core Architecture Clean Architecture + Modular Monolith Kernel DONE
- RESEARCH VALIDATION 2026-09-11 completed: database baseline changed from MariaDB/Pomelo to PostgreSQL 16.14/Npgsql/EF Core 10
- SharedKernel + module triads exist, Api composition root wired
- PostgreSQL 16.14 reachable at 172.21.208.1:5432 from WSL

## Gating Decisions Required Before Coding
- OQ-1 Naming convention: snake_case vs PascalCase for PostgreSQL tables/columns. Decision must be recorded in docs/architecture-notes.md
- PK strategy: UUID vs bigint. Decision affects Company/Branch/Account PK definitions
- Concurrency token: RowVersion / xmin / none. Decision affects entity concurrency handling
- Npgsql version for EF Core 10: pin in Directory.Packages.props
- Regulatory regime: confirm Circular 133 vs Circular 99 baseline for COA seed structure. Seed is structural only, no business rules.

## Subtasks

### 3.1 Infrastructure DbContext Scaffold
- Create `SmeAccounting.Infrastructure.Persistence` namespace
- `SmeAccountingDbContext : DbContext` with `OnConfiguring` guard
- DbSet declarations for foundation entities: Company, Branch, Account, AuditLogEntry
- `OnModelCreating` base conventions:
  - Property convention: decimal precision 18,2
  - Property convention: DateTimeOffset -> `timestamptz`
  - String max length default 256
  - Apply `HasDefaultValueSql` for audit timestamps where appropriate
- Global query filter: `!IsDeleted` for `ISoftDeletable`
- Audit interceptors seam for CreatedBy/UpdatedBy/DeletedBy using `ICurrentUserProvider` and `IDateTimeProvider`

### 3.2 Entity Definitions - Foundation Only
- Company: Id, Name, Code, IsActive, CompanyId? Actually top-level. CompanyScoped entities get CompanyId.
- Branch: Id, CompanyId, Name, Code, IsActive
- Account: Id, CompanyId, Code, Name, AccountType, Level, ParentId?, IsActive, NormalBalance
- AuditLogEntry: Id, EntityName, EntityId, Action, ChangedBy, ChangedAt, Snapshot JSONB
- No EF attributes in Domain/SharedKernel. Entities live in Infrastructure.Persistence for now per Option-B.
- Ensure persistence-ignorant Domain/SharedKernel remain free of EF usings

### 3.3 Npgsql Configuration
- `AddInfrastructure()` registers `SmeAccountingDbContext` with Npgsql
- Connection string from `ConnectionStrings:DefaultConnection`
- UseNpgsql with explicit PostgreSQL version 16, `EnableRetryOnFailure`, `DisableSensitiveDataLogging` in production
- `IDesignTimeDbContextFactory<SmeAccountingDbContext>` for `dotnet ef` tooling
- No `AutoDetect` version; pin server version in config

### 3.4 Migrations Setup
- Enable EF Core Migrations in Infrastructure project
- Initial migration `InitialFoundation`
- Generate idempotent SQL script: `dotnet ef migrations script --idempotent`
- Verify script contains `numeric(18,2)` for money, `timestamptz` for timestamps, chosen naming convention
- Migration bundle generation tested for headless deploy

### 3.5 Seeding
- Implement `UseSeeding` and `UseAsyncSeeding` extensions
- Seed 5 default roles, default admin user with hashed password from env var
- Seed COA structural seed: 49 Level-1 accounts for Circular 133 skeleton, idempotent
- Development-only demo guard data
- `HasData` only for tiny static lookups

### 3.6 Startup Model Validation
- Add `PendingModelChangeException` check on startup in Development
- Never auto-migrate in Production
- Health check for DB connectivity

### 3.7 Testing
- Integration tests with WebApplicationFactory + Testcontainers.PostgreSql + Respawn
- Seed idempotency test
- Soft delete filter test
- Audit fields written test
- Pending model change check test

### 3.8 Documentation
- Update `docs/architecture-notes.md` with naming convention decision, PK strategy, concurrency token
- Record OQ-7 audit granularity decision
- Update `MEMORY.md` with PostgreSQL specifics

## Acceptance Criteria
- `dotnet restore --locked-mode` exits 0
- `dotnet build -c Release` exits 0 with 0 warnings
- `dotnet ef migrations script --idempotent` generates SQL with numeric/timestamptz and chosen naming convention
- Migration script runs clean second time
- Seed runs twice with no duplicates
- Domain/SharedKernel contain zero EF usings
- Integration tests pass against PostgreSQL Testcontainers
- Pending model change check passes
- No accounting business logic implemented, no fake CRUD

## Risks
- OQ-1 naming convention undecided -> leads to migration churn
- Regulatory regime ambiguity -> COA seed may need revision
- Npgsql EF Core 10 version pin not confirmed -> compatibility issue

Next: Execute 3.1 Infrastructure DbContext Scaffold
