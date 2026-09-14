# Testing

## Test Projects

| Project | Type | Purpose |
|---------|------|---------|
| `SmeAccounting.Domain.Tests` | Unit | SharedKernel primitives (Result, BaseEntity) |
| `SmeAccounting.Application.Tests` | Unit | MediatR pipeline behaviors (ValidationBehaviour) |
| `SmeAccounting.Infrastructure.Tests` | Integration | Database schema, migrations, soft delete (Testcontainers) |
| `SmeAccounting.Architecture.Tests` | Architecture | Layer dependency rules, entity audit fields |
| `SmeAccounting.Security.Tests` | Security | Permission constants, role seeding |
| `SmeAccounting.Web.Tests` | Integration | Health checks via WebApplicationFactory |

## How to Run

```bash
# All tests
dotnet test

# Specific project
dotnet test tests/SmeAccounting.Domain.Tests
dotnet test tests/SmeAccounting.Application.Tests
dotnet test tests/SmeAccounting.Infrastructure.Tests
dotnet test tests/SmeAccounting.Architecture.Tests
dotnet test tests/SmeAccounting.Security.Tests
dotnet test tests/SmeAccounting.Web.Tests

# With verbosity
dotnet test --verbosity normal

# Filter by test name
dotnet test --filter "FullyQualifiedName~ResultTests"
dotnet test --filter "FullyQualifiedName~ArchitectureTests"
```

## Test Details

### Domain Tests (`tests/SmeAccounting.Domain.Tests/`)

Tests for `SmeAccounting.SharedKernel`:

- **ResultTests.cs** — `Result.Success()`, `Result.Fail()`, implicit conversions, value access throws on failure
- **BaseEntityTests.cs** — Id defaults, domain events collection, raise/clear events
- **SkeletonTests.cs** — Placeholder for additional domain tests

### Application Tests (`tests/SmeAccounting.Application.Tests/`)

Tests for MediatR pipeline:

- **ValidationBehaviourTests.cs** — No validators → calls next; valid request → calls next; invalid request → throws `ValidationException`
  - Uses NSubstitute for mocking `IValidator<T>` and `RequestHandlerDelegate<T>`
- **SkeletonTests.cs** — Placeholder

### Infrastructure Tests (`tests/SmeAccounting.Infrastructure.Tests/`)

Database integration tests using **Testcontainers** (`PostgreSqlContainer`):

- **DatabaseIntegrationTests.cs**:
  - `SchemaCreatedWithSnakeCaseNaming` — verifies table names are snake_case
  - `PrimaryKeysAreBigintIdentity` — verifies PK columns are `bigint`
  - `ColumnsUseSnakeCase` — verifies column naming convention
  - `SeedDataPresent` — verifies Demo Company and Head Office branch
  - `SoftDeleteFilterApplied` — verifies global query filter excludes deleted rows
  - `ForeignKeyConstraintsExist` — verifies FK relationships

Test setup: spins up `postgres:16.14-alpine` container, runs migrations, cleans up on dispose.

### Architecture Tests (`tests/SmeAccounting.Architecture.Tests/`)

Uses **NetArchTest.Rules** to enforce structural rules:

- **ArchitectureTests.cs**:
  - Domain must not depend on Infrastructure or Application
  - SharedKernel must not depend on any project
  - Application must not depend on Infrastructure
  - Infrastructure must not depend on Api
  - Module Domain projects must not depend on Infrastructure
  - Controllers must not contain business logic (IL size < 1000)
  - Entities implementing `ISoftDeletable` must have required properties
  - Entities implementing `IAuditable` must have required properties

### Security Tests (`tests/SmeAccounting.Security.Tests/`)

Validates RBAC implementation:

- **PermissionTests.cs**:
  - All permissions are non-empty and formatted as `{module}.{action}`
  - Each module has a `view` permission
  - Admin role has all permissions
  - Viewer role only has `.view` permissions
  - All permission constants are unique

### Web Tests (`tests/SmeAccounting.Web.Tests/`)

Integration tests using **WebApplicationFactory**:

- **HealthCheckTests.cs**:
  - `HealthLive_ReturnsOk` — GET `/health/live` → 200
  - `HealthReady_ReturnsOk` — GET `/health/ready` → 200 or 503

- **TestWebApplicationFactory.cs** — Sets environment to `Testing`, removes DB-dependent health checks for isolation

- **SkeletonTests.cs** — Placeholder for additional web integration tests

## Test Frameworks

| Library | Purpose |
|---------|---------|
| xUnit | Test framework |
| NSubstitute | Mocking |
| Testcontainers.PostgreSql | Database integration tests |
| NetArchTest.Rules | Architecture constraint tests |
| Microsoft.AspNetCore.Mvc.Testing | WebApplicationFactory for integration tests |

## CI Integration

```bash
# Full CI pipeline
dotnet restore
dotnet build --no-restore
dotnet test --no-build --verbosity normal --logger "trx;LogFileName=TestResults.trx"
```

## Adding New Tests

1. Create test class implementing `IClassFixture<T>` for shared context
2. Use NSubstitute for external dependencies
3. Use Testcontainers for any test requiring a database
4. Architecture tests: add new rules to `ArchitectureTests.cs`
5. Security tests: update permission assertions when new permissions are added
