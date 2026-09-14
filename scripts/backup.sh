#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/sme-accounting"
RETENTION_DAYS=14
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-sme_accounting}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_USER="${POSTGRES_USER:-postgres}"

mkdir -p "$BACKUP_DIR"

echo "Starting backup of $DB_NAME..."
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    | gzip > "$BACKUP_DIR/sme-accounting_$DATE.sql.gz"

echo "Backup created: sme-accounting_$DATE.sql.gz"

# Clean old backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "Cleaned backups older than $RETENTION_DAYS days"
