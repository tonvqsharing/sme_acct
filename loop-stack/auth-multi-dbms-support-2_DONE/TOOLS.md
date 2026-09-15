# Global Loop Tools
Status: REUSED FROM GLOBAL (cached 2026-09-11)
Shared tool/library inventory across all loops in this project.
## Framework & Runtime
- .NET 10 LTS (net10.0), ASP.NET Core 10, EF Core 9 via Pomelo.EntityFrameworkCore.MySql 9.0.0
- MariaDB 10.6+ LTS (recommend 10.11 LTS or 11.4 LTS), utf8mb4 charset (`utf8mb4_unicode_ci` for Vietnamese)
## Architecture Patterns (Modular Monolith)
- Per-module `Add{Module}Module()` extension + `IModule` in base Application; explicit `AddModules([...])` registry in Api (no reflection)
- MediatR: call `AddMediatR` multi-assembly (Scoped) — safe no-op override across modules, container decides lifetime
- Api references module Application (typed IRequest types) + module Infrastructure (DI); DB centralized in one Infrastructure project + single DbContext
## Backend Packages
- MediatR 12.5.0 (CQRS; DI merged into main package, no Extensions pkg), FluentValidation 12.1.1 (pipeline behaviour; DI extension namespace is `FluentValidation` itself — `FluentValidation.Results` = `ValidationFailure`), MySqlConnector (driver), Pomelo.EntityFrameworkCore.MySql (EF provider)
- net10.0 lib projects needing ASP.NET Core services (e.g. IHttpContextAccessor): `<FrameworkReference Include="Microsoft.AspNetCore.App" />` — env EOL for Http.Abstractions NuGet
## Testing
- xUnit v3 (4.0.0) + MTP runner — enabled via global.json `"test.runner": "Microsoft.Testing.Platform"` (NOT `--test-runner`; flag doesn't exist in dotnet new xunit). Test projects need `OutputType=Exe` + `UseAppHost` + `<Using Include="Xunit"/>`. All projects must share runner; VSTest+MTP mixed → exit 1.
- NETSDK1188 (MTP 2.3.3 locale resources) → NoWarn in Directory.Build.props
- NSubstitute (preferred; Moq has 4.20 analytics controversy)
- FluentAssertions license changed to paid (2025) → AwesomeAssertions 9.6.0 fork / Shouldly (validate before use)
- NetArchTest.Rules 1.3.2 (pinned; dev-dormant) or TNG/ArchUnitNET
- Microsoft.AspNetCore.Mvc.Testing (WebApplicationFactory) + Testcontainers.MariaDb + Respawn for integration tests
## Frontend
- Bootstrap 5.3.x + jQuery 3.7.x via LibMan into wwwroot/lib/; Sneat free Bootstrap 5 ASP.NET Core MVC admin template
## Reporting
- QuestPDF (2026.8.0) — PDF export for FS/ledger; free Community license; NuGet: QuestPDF
## CI/CD & Deploy
- GitHub Actions: actions/checkout@v6, actions/setup-dotnet@v4; MariaDB tests via shogo82148/actions-setup-mysql@v1 (`distribution: mariadb`)
- Deploy: Windows IIS in-process (.NET Hosting Bundle) or Linux Kestrel + Nginx + systemd with ForwardedHeaders
- EF Core migrations: idempotent SQL script or migration bundle for review-gated on-premise deploys
## Standards References
- Circular 133/2016/TT-BTC (SME accounting regime, effective 2017, ~90 articles + annexes), Circular 200/2014 (annexes PL1-PL4), Circular 99/2025/TT-BTC (supersedes 200)
- Open-source double-entry references: nledger (C# pure), dubbl, Ledger, GnuCash
## Runtime (WSL2 Kali, discovered)
- .NET SDK 10.0.401, MariaDB client 11.8.6, Git 2.51.0, Node v26.5.0, curl, sed
- **Global tools (installed)**: dotnet-ef 10.0.12, LibMan CLI 3.0.114
- NOT installed: jq, Docker, mariadb-dump