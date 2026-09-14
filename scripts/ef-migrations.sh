#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

case "${1:-}" in
    bundle)
        echo "Creating EF Core migration bundle..."
        dotnet ef migrations bundle \
            --project "$PROJECT_DIR/src/SmeAccounting.Infrastructure" \
            --startup-project "$PROJECT_DIR/src/SmeAccounting.Api" \
            --output "$PROJECT_DIR/artifacts/migrations bundle" \
            --force
        echo "Bundle created at artifacts/migrations bundle"
        ;;
    script)
        echo "Generating idempotent SQL script..."
        dotnet ef migrations script \
            --idempotent \
            --project "$PROJECT_DIR/src/SmeAccounting.Infrastructure" \
            --startup-project "$PROJECT_DIR/src/SmeAccounting.Api" \
            --output "$PROJECT_DIR/artifacts/sql/migrations.sql"
        echo "Script created at artifacts/sql/migrations.sql"
        ;;
    *)
        echo "Usage: $0 {bundle|script}"
        exit 1
        ;;
esac
