# Discovered Tools — build-identity-auth
## Framework & Runtime
- .NET SDK 10.0.401 (net10.0)
- ASP.NET Core 10.0.12, EF Core 10.0.12
- MariaDB client 11.8.6 (server not running locally)
## Global Tools
- dotnet-ef 10.0.12
- LibMan CLI 3.0.114 (libman)
- roslyn-language-server 5.12.0-1.26426.8
## NuGet
- Source: nuget.org (enabled)
- Key packages (from global inventory): MediatR 12.5.0, FluentValidation 12.1.1, MySqlConnector, Pomelo.EntityFrameworkCore.MySql 9.0.0, QuestPDF 2026.8.0
## Testing
- xUnit v3 (4.0.0) + Microsoft.Testing.Platform
- NSubstitute (mocking)
- AwesomeAssertions 9.6.0 (AwesomeAssertions) / Shouldly
- Testcontainers.MariaDb + Respawn (integration tests)
## Frontend
- Bootstrap 5.3.x, jQuery 3.7.x (LibMan)
- Sneat Bootstrap 5 admin template
## CI/CD
- GitHub Actions: actions/checkout@v6, actions/setup-dotnet@v4
- EF Core: idempotent SQL script or migration bundle
## Runtime Availability
- **dotnet**: 10.0.401
- **docker**: NOT AVAILABLE
- **mariadb-dump**: NOT AVAILABLE
- **jq**: NOT AVAILABLE
- **node**: v26.5.0
- **git**: 2.51.0
## Git Status
- M .opencode/agents/verifier.md (modified)
- ?? loop-stack/build-identity-auth/ (untracked — this loop)
