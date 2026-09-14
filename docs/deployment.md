# Deployment

## Linux (Nginx + systemd)

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name accounting.example.vn;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection keep-alive;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /health {
        proxy_pass http://localhost:5000;
        access_log off;
    }
}
```

### systemd Service

```ini
[Unit]
Description=SME Accounting Web App
After=network.target postgresql.service

[Service]
User=smeacct
Group=smeacct
WorkingDirectory=/opt/smeaccounting
ExecStart=/usr/bin/dotnet /opt/smeaccounting/SmeAccounting.Api.dll
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=smeaccounting
Environment=ASPNETCORE_ENVIRONMENT=Production
Environment=ASPNETCORE_URLS=http://localhost:5000
Environment=ConnectionStrings__DefaultConnection=Host=localhost;Port=5432;Database=smeaccounting;Username=smeacct;Password=<secret>
Environment=ADMIN_PASSWORD=<strong-password>

[Install]
WantedBy=multi-user.target
```

### Deploy Steps

```bash
# 1. Publish
dotnet publish src/SmeAccounting.Api -c Release -o /opt/smeaccounting

# 2. Apply migrations
export SME_ACCT_CONNECTION_STRING="Host=localhost;Port=5432;Database=smeaccounting;Username=smeacct;Password=<secret>"
dotnet ef database update --project src/SmeAccounting.Infrastructure --startup-project src/SmeAccounting.Api

# 3. Restart
sudo systemctl restart smeaccounting
```

## Docker

### Dockerfile

```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:9.0-alpine AS base
WORKDIR /app
EXPOSE 5000

FROM mcr.microsoft.com/dotnet/sdk:9.0-alpine AS build
WORKDIR /src
COPY . .
RUN dotnet restore
RUN dotnet publish src/SmeAccounting.Api -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "SmeAccounting.Api.dll"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  db:
    image: postgres:16.14-alpine
    environment:
      POSTGRES_DB: smeaccounting
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      ASPNETCORE_ENVIRONMENT: Production
      ConnectionStrings__DefaultConnection: "Host=db;Port=5432;Database=smeaccounting;Username=postgres;Password=postgres"
    depends_on:
      - db

volumes:
  pgdata:
```

### Docker Commands

```bash
# Build and run
docker compose up -d --build

# Apply migrations inside container
docker compose exec app dotnet ef database update \
  --project src/SmeAccounting.Infrastructure \
  --startup-project src/SmeAccounting.Api

# View logs
docker compose logs -f app
```

## Secrets Management

### Environment Variables (Development)

| Variable | Purpose |
|----------|---------|
| `ConnectionStrings__DefaultConnection` | PostgreSQL connection string |
| `ADMIN_PASSWORD` | Default admin user password |
| `SME_ACCT_CONNECTION_STRING` | Used by EF Core tooling (migrations) |
| `Security__DataProtectionPath` | Data protection key storage path |

### Production Secrets

- Use systemd `Environment` directives or `/etc/default/smeaccounting`
- For Docker: Docker secrets, `.env` files (not committed), or cloud secret managers
- Data Protection keys: persist to shared filesystem or cloud storage for multi-instance

### appsettings Hierarchy

```
appsettings.json                    # Defaults
appsettings.{Environment}.json      # Environment overrides
```

Sections: `ConnectionStrings`, `Serilog`, `Security`, `RequestLocalization`.

## Zero-Downtime Deployment

### Strategy: Rolling Restart

1. Apply database migrations first (backwards-compatible)
2. Deploy new binaries
3. Restart service (systemd or Docker Compose)
4. Verify health: `curl http://localhost:5000/health/ready`

### Migration Safety Rules

- Additive-only migrations (new columns, tables, indexes) — no breaking changes
- Default values for new non-nullable columns
- Rename columns via add-new → copy → drop-old pattern
- Never remove columns in same deployment as code that reads them

### Health Checks

| Endpoint | Purpose |
|----------|---------|
| `/health/live` | Liveness — always 200 (no checks) |
| `/health/ready` | Readiness — checks PostgreSQL + EF Core connectivity |

Docker HEALTHCHECK / Kubernetes livenessProbe should hit `/health/live`.
ReadinessProbe should hit `/health/ready`.

## Build

```bash
# Restore
dotnet restore

# Build
dotnet build --no-restore

# Run tests
dotnet test --no-build

# Publish
dotnet publish src/SmeAccounting.Api -c Release -o artifacts/publish
```

### Build Output

```
artifacts/
├── bin/           # Build outputs
├── publish/       # Publish output
└── sql/           # Idempotent SQL scripts
```
