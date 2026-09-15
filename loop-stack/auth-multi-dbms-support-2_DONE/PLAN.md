# Loop Plan
## Mode
patch
## Goal
Complete provider-neutral DbContext conditional model building, Identity auth implementation, per-provider migrations and tests for multi-DBMS support
## Stop Condition
all tasks in loop-stack/auth-multi-dbms-support-2/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
- [x] [G1] Remove PostgreSQL-only usings and HasPostgresExtension from SmeAccountingDbContext
- [x] [G1] Remove NpgsqlValueGenerationStrategy annotation and replace with provider-neutral identity configuration
- [x] [G1] Remove xmin shadow concurrency token and Xmin seed data from SmeAccountingDbContext
- [x] [G1] Add provider detection helper and conditional model building for identity/concurrency per provider
- [x] [G1] Update Identity infrastructure DI registration to use DbProviderSelector instead of hardcoded UseNpgsql for provider-neutral runtime connection
- [x] [G2] Implement provider-specific model configuration helpers for MariaDB/MySQL/SQLite/SQLServer (identity strategy, remove xmin concurrency token, conditional uuid-ossp extension)
- [x] [G2] Create per-provider EF Core migrations for MariaDB and update ModelSnapshot to support provider-agnostic schema generation
- [x] [G3] Add integration tests for multi-DBMS DbContext and Identity auth using Testcontainers MariaDB and existing PostgreSQL tests
- [x] [G3] Run full test suite and verify provider-neutral migrations apply cleanly for PostgreSQL and MariaDB
