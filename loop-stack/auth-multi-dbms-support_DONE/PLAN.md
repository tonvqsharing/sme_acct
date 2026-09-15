# Loop Plan
## Mode
patch
## Goal
Implement cookie-based auth in SmeAccounting.Modules.Identity and make EF Core provider selectable at runtime (PostgreSQL 16 default, MariaDB/SQLite/SQL Server supported).
## Stop Condition
all tasks in loop-stack/auth-multi-dbms-support/PLAN.md checked
## Budget
20 turns
## Git Integration
yes
## Tasks
- [x] [G1] Audit Identity and Infrastructure DI for hard-coded Npgsql and PostgreSQL-only features
- [x] [G1] Map provider-specific code paths for abstraction (xmin concurrency, uuid-ossp, IdentityByDefaultColumn, snake_case)
- [x] [G2] Implement runtime EF Core provider selector based on connection string/config with provider-agnostic DbContext registration
- [x] [G2] Add MariaDB/SQLite/SQL Server EF packages and conditional model building for PK, concurrency token, and naming conventions
- [x] [G3] Update IdentityDbContextFactory, migrations, and seed data for provider-agnostic execution
- [x] [G3] Add integration tests and CI verification for PostgreSQL and MariaDB provider selection
