#!/bin/bash
################################################################################
# WMS Database Backup Script
#
# Description:
#   - Creates a backup of the SQLite database
#   - Keeps backups for the last 30 days
#   - Logs all backup operations
#
# Usage:
#   ./backup_database.sh
#
# Cron Setup (backup every 6 hours):
#   0 */6 * * * /path/to/vnix-wms-main/backup_database.sh >> /var/log/wms_backup.log 2>&1
################################################################################

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Use DATABASE_PATH from .env, fallback to data.db
DB_FILE="${DATABASE_PATH:-data.db}"
# Convert to absolute path if relative
if [[ "$DB_FILE" != /* ]]; then
    DB_FILE="$SCRIPT_DIR/$DB_FILE"
fi

# Use BACKUP_DIR from .env, fallback to backups
BACKUP_DIR="${BACKUP_DIR:-backups}"
if [[ "$BACKUP_DIR" != /* ]]; then
    BACKUP_DIR="$SCRIPT_DIR/$BACKUP_DIR"
fi

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/$(basename "$DB_FILE" .db)_$DATE.db"
LOG_FILE="$BACKUP_DIR/backup.log"
RETENTION_DAYS=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    echo -e "${RED}❌ ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

# Success message
success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

# Warning message
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

# Main backup process
main() {
    log "========================================="
    log "Starting WMS Database Backup"
    log "========================================="

    # Check if database file exists
    if [ ! -f "$DB_FILE" ]; then
        error_exit "Database file not found: $DB_FILE"
    fi

    # Create backup directory if it doesn't exist
    if [ ! -d "$BACKUP_DIR" ]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory"
    fi

    # Check database integrity
    log "Checking database integrity..."
    if command -v sqlite3 &> /dev/null; then
        sqlite3 "$DB_FILE" "PRAGMA integrity_check;" > /tmp/integrity_check.txt
        if grep -q "ok" /tmp/integrity_check.txt; then
            success "Database integrity check passed"
        else
            warning "Database integrity check failed! Backing up anyway..."
            cat /tmp/integrity_check.txt | tee -a "$LOG_FILE"
        fi
        rm -f /tmp/integrity_check.txt
    else
        warning "sqlite3 command not found. Skipping integrity check."
    fi

    # Get database size
    DB_SIZE=$(du -h "$DB_FILE" | cut -f1)
    log "Database size: $DB_SIZE"

    # Create backup using sqlite3 .backup command (safer than cp)
    log "Creating backup: $BACKUP_FILE"
    if command -v sqlite3 &> /dev/null; then
        sqlite3 "$DB_FILE" ".backup '$BACKUP_FILE'" || error_exit "Backup failed using sqlite3"
    else
        # Fallback to cp if sqlite3 is not available
        warning "sqlite3 not found. Using cp as fallback..."
        cp "$DB_FILE" "$BACKUP_FILE" || error_exit "Backup failed using cp"
    fi

    # Verify backup was created
    if [ ! -f "$BACKUP_FILE" ]; then
        error_exit "Backup file was not created"
    fi

    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    success "Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)"

    # Count existing backups
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/data_*.db 2>/dev/null | wc -l)
    log "Total backups: $BACKUP_COUNT"

    # Clean up old backups (keep only last 30 days)
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "data_*.db" -mtime +$RETENTION_DAYS 2>/dev/null)

    if [ -n "$OLD_BACKUPS" ]; then
        OLD_COUNT=$(echo "$OLD_BACKUPS" | wc -l)
        echo "$OLD_BACKUPS" | while read -r old_backup; do
            log "Deleting old backup: $(basename "$old_backup")"
            rm -f "$old_backup"
        done
        success "Deleted $OLD_COUNT old backup(s)"
    else
        log "No old backups to delete"
    fi

    # Final summary
    REMAINING_BACKUPS=$(ls -1 "$BACKUP_DIR"/data_*.db 2>/dev/null | wc -l)
    log "========================================="
    success "Backup completed successfully!"
    log "Backup file: $BACKUP_FILE"
    log "Backups retained: $REMAINING_BACKUPS"
    log "========================================="

    # Check disk space
    DISK_USAGE=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 80 ]; then
        warning "Disk usage is high: ${DISK_USAGE}%. Consider cleaning up old backups."
    fi
}

# Run main function
main

exit 0
