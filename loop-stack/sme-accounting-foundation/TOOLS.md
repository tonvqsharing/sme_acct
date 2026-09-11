# Discovered Tools
## Status
DONE (Researcher 2, "External Knowledge & Resources")
## .NET 10 SDK / Templates
- `dotnet new sln` → slnx format by default (can choose `-f sln|slnx`)
- `dotnet new xunit --test-runner MTP` (MTP = Microsoft Testing Platform, new in SDK 10)
- `dotnet new install Clean.Architecture.Solution.Template` (Jason Taylor, v10.x, Aspire + EF Core 10)
- MinimDev/dotnet-clean-architecture-template (.NET 10, MediatR 12)
- deadislove/dotnet-CleanArchMediatR-template + dotnet-ModularMonolith-template
- Modular monolith references: kgrzybek/modular-monolith-with-ddd, NET-Architecture-Templates/ModularMonolith, arno-cassaniga fork
## Packages / Libraries
- Npgsql 8.x+ (EF Core 10 provider for PostgreSQL 16.14) — historical: Pomelo.EntityFrameworkCore.MySql 9.0.0 (EF Core 9.x) was MariaDB baseline, superseded 2026-09-11.
- MySqlConnector removed from baseline; retained in research history only.
- MediatR, FluentValidation
- Testcontainers.PostgreSql + Testcontainers.XunitV3 (historical: Testcontainers.MariaDb / Testcontainers.MySql v4.14.0 superseded)
- Respawn (DB reset between integration tests, by jbogard)
- NetArchTest.Rules 1.3.2 (latest; dev-dormant) or TNG/ArchUnitNET (maintained, reads IL)
- NSubstitute (preferred over Moq — 4.20 analytics controversy)
- Assertions: FluentAssertions now paid license (2025) → AwesomeAssertions fork or Shouldly (DECIDED: revisit)
- QuestPDF (2026.8.0) for PDF reports — license key required, free Community license; NuGet: QuestPDF
- Microsoft.AspNetCore.Mvc.Testing — WebApplicationFactory<T> integration tests
## Client-Side
- LibMan (`libman.json`, providers cdnjs/jsDelivr/unpkg → wwwroot/lib/) for Bootstrap 5.3.x + jQuery 3.7.x
- Sneat free Bootstrap 5 ASP.NET Core MVC admin template (themeselection repo)
## CI/CD
- GitHub Actions: actions/checkout@v6, actions/setup-dotnet@v4, dotnet restore/build --no-restore/test
- PostgreSQL for tests: Testcontainers.PostgreSql (Docker-in-CI) or GitHub Actions `postgres` service; historical MariaDB option `shogo82148/actions-setup-mysql@v1` retained in research.
## Deployment
- Windows: .NET Hosting Bundle, IIS in-process; Windows Service for background
- Linux: Kestrel behind Nginx + systemd, ForwardedHeaders middleware
- EF Core migrations: idempotent SQL script (`dotnet ef migrations script --idempotent`) or migration bundle (`dotnet ef migrations bundle --self-contained`)
## Runtime Environment (discovered)
- OS: Kali GNU/Linux Rolling 2025.4 on WSL2
- .NET SDK: 10.0.401 ✅
- PostgreSQL 16.14 installed on Windows 10 host at 172.21.208.1:5432, reachable from WSL via `psql -h 172.21.208.1 -p 5432 -U postgres -d postgres` ✅; historical MariaDB client 11.8.6 retained in research notes.
- Git: 2.51.0 ✅
- GitHub CLI: 2.96.0 ✅ (auth expired — needs `gh auth login`)
- Node.js: v26.5.0, npm 11.17.0 ✅
- VS Code: /mnt/d/vscode/bin/code ✅ (WSL-accessible)
- NuGet: nuget.org reachable ✅
- curl: 8.20.0 ✅
- sed: GNU sed 4.9 ✅
## Gaps (install before build)
- dotnet-ef: `dotnet tool install --global dotnet-ef`
- LibMan CLI: `dotnet tool install --global Microsoft.Web.LibraryManager.Cli`
- jq: `apt install jq`
- Docker: NOT installed — integration tests with Testcontainers won't run locally
- pg_dump/pg_restore: available via PostgreSQL 16 host; historical mariadb-dump note retained.
## Reference / Standards
- Circular 133/2016/TT-BTC (SME), Annexes PL1-PL4 of Circular 200/2014 (superseded by Circular 99/2025/TT-BTC)
- Open-source double-entry references: dmitry-merzlyakov/nledger (C#), dubbl, Ledger/GnuCash
