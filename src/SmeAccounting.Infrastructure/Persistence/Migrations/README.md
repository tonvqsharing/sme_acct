# Per-Provider Migrations

Migrations are provider-specific.

## Generate
```
Database__Provider=PostgreSql dotnet ef migrations add Initial_PostgreSql --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api --output-dir Persistence/Migrations/PostgreSql
Database__Provider=MariaDb dotnet ef migrations add Initial_MariaDb --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api --output-dir Persistence/Migrations/MariaDb
...
```
