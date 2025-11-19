# Database Backups

This folder contains automatic backups of the WMS database.

## Backup Schedule

Backups are created:
- **Automatically**: Every 6 hours (via cron job)
- **Manually**: Run `./backup_database.sh` anytime

## Backup Retention

- Backups are kept for **30 days**
- Older backups are automatically deleted
- Each backup file is named: `data_YYYYMMDD_HHMMSS.db`

## Restore from Backup

To restore from a backup:

```bash
# 1. Stop the application first
# (Close Flask app)

# 2. Backup current database (just in case)
cp data.db data_backup_before_restore.db

# 3. Restore from backup file
cp backups/data_20251119_000308.db data.db

# 4. Restart the application
python app.py
```

## Manual Backup

To create a manual backup:

```bash
./backup_database.sh
```

## Check Backup Logs

View backup history:

```bash
tail -f backup.log
```

## Disk Space

Monitor disk usage:

```bash
du -sh backups/
```

## Important Notes

⚠️ **DO NOT** delete this folder!
✅ Backups are created using SQLite's `.backup` command (safe)
✅ Database integrity is checked before each backup
✅ Old backups (>30 days) are automatically cleaned up
