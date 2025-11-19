#!/bin/bash
################################################################################
# Setup Cron Job for Database Backup
#
# This script helps you setup automatic database backups
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_database.sh"

echo "========================================="
echo "WMS Database Backup - Cron Setup"
echo "========================================="
echo ""

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "❌ Error: backup_database.sh not found!"
    exit 1
fi

echo "Current directory: $SCRIPT_DIR"
echo "Backup script: $BACKUP_SCRIPT"
echo ""

echo "This will setup automatic backups every 6 hours."
echo ""
echo "The cron job will be:"
echo "  0 */6 * * * $BACKUP_SCRIPT >> $SCRIPT_DIR/backups/backup.log 2>&1"
echo ""

read -p "Do you want to add this cron job? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add cron job
    (crontab -l 2>/dev/null; echo "0 */6 * * * $BACKUP_SCRIPT >> $SCRIPT_DIR/backups/backup.log 2>&1") | crontab -

    echo ""
    echo "✅ Cron job added successfully!"
    echo ""
    echo "Current crontab:"
    echo "----------------------------------------"
    crontab -l | grep backup_database.sh
    echo "----------------------------------------"
    echo ""
    echo "Backups will run automatically every 6 hours at:"
    echo "  - 00:00 (midnight)"
    echo "  - 06:00 (6am)"
    echo "  - 12:00 (noon)"
    echo "  - 18:00 (6pm)"
    echo ""
    echo "To view backup logs:"
    echo "  tail -f $SCRIPT_DIR/backups/backup.log"
    echo ""
    echo "To remove this cron job later:"
    echo "  crontab -e"
    echo "  (then delete the line with backup_database.sh)"
else
    echo ""
    echo "❌ Cancelled. No cron job was added."
    echo ""
    echo "To manually add the cron job later:"
    echo "  1. Run: crontab -e"
    echo "  2. Add this line:"
    echo "     0 */6 * * * $BACKUP_SCRIPT >> $SCRIPT_DIR/backups/backup.log 2>&1"
fi

echo ""
echo "========================================="
