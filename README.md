# SME Accounting

Vietnamese SME accounting web application built with ASP.NET Core, Clean Architecture, and Modular Monolith pattern.

## Tech Stack

- **ASP.NET Core 9** — MVC with Razor views
- **Entity Framework Core 9** — ORM with Npgsql 9 for PostgreSQL
- **PostgreSQL 16.14** — Primary database
- **ASP.NET Core Identity** — Authentication with cookie auth
- **MediatR** — CQRS within modules
- **FluentValidation** — Request validation pipeline
- **Serilog** — Structured logging (console + rolling file)
- **xUnit + NSubstitute + Testcontainers** — Testing

## Architecture

Clean Architecture + Modular Monolith with 12 MVP modules.

```
Api → Application → Domain → SharedKernel
  ↘ Infrastructure ↗
```

See [docs/architecture.md](docs/architecture.md) for full details.

## Quick Start

### Prerequisites

- .NET 9 SDK
- PostgreSQL 16+

### Setup

```bash
# Clone and restore
git clone <repo-url> sme_acct
cd sme_acct
dotnet restore

# Create database createdb smeaccounting

# Apply migrations
export SME_ACCT_CONNECTION_STRING="Host=localhost;Port=5432;Database=smeaccounting;Username=postgres;Password=postgres"
dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api

# Run
dotnet run --project src/SmeAccounting.Api
```

App starts at `http://localhost:5000`.

### Default Login

| Field | Value |
|-------|-------|
| Email | admin@smeaccounting.vn |
| Password | Admin@12345 |

Override password via `ADMIN_PASSWORD` environment variable.

### Run Tests

```bash
dotnet test
```

## Modules (12 MVP)

| Module | Purpose |
|--------|---------|
| Identity | User management, login |
| Authorization | Roles, permissions, RBAC policy engine |
| Organization | Company, branch hierarchy |
| MasterData | Reference data |
| Audit | Change tracking |
| ChartOfAccounts | Account tree |
| AccountingPeriod | Period management |
| Journal | Journal entries |
| Posting | Post to GL |
| GeneralLedger | GL queries, balances |
| Tax | VAT, CIT |
| FinancialReporting | Balance sheet, P&L |

See [docs/modules.md](docs/modules.md) for full module map.

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | Clean Architecture, layer rules, module system |
| [Modules](docs/modules.md) | Module map, ownership, isolation rules |
| [Database](docs/database.md) | PostgreSQL conventions, migrations, seeds |
| [Security](docs/security.md) | Identity, RBAC, headers, data protection |
| [Authorization](docs/authorization.md) | Roles, permissions, RBAC pipeline |
| [Deployment](docs/deployment.md) | Linux, Docker, secrets, zero-downtime |
| [Testing](docs/testing.md) | Test tiers, running tests, CI |
| [ADR-001](docs/adr/001-naming-and-pk-strategy.md) | DB naming + PK strategy decision |

## Project Structure

```
src/
├── SmeAccounting.SharedKernel/     # Primitives, Result<T>
├── SmeAccounting.Domain/           # Domain markers
├── SmeAccounting.Application/      # IModule, MediatR, validation
├── SmeAccounting.Infrastructure/   # EF Core, Identity, logging
├── SmeAccounting.Api/              # ASP.NET Core host
└── Modules/                        # 12 MVP modules (Domain/Application/Infrastructure each)

tests/
├── SmeAccounting.Domain.Tests/
├── SmeAccounting.Application.Tests/
├── SmeAccounting.Infrastructure.Tests/
├── SmeAccounting.Architecture.Tests/
├── SmeAccounting.Security.Tests/
└── SmeAccounting.Web.Tests/
```
