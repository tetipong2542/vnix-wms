#!/usr/bin/env python3
"""
Database Migration Runner
==========================
Safely runs database migrations for VNIX WMS.

Usage:
    python run_migration.py [migration_file]

Example:
    python run_migration.py migrations/add_stock_transactions.sql

Features:
- Automatic database backup before migration
- Rollback capability if migration fails
- Verification of migration success
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Configuration
DEFAULT_DB = 'data.db'  # Default database name
BACKUP_DIR = 'backups'


def get_db_path():
    """Get database path from app.py or use default."""
    # Try to read from app.py
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for DATABASE_PATH default value
            for line in content.split('\n'):
                if 'DATABASE_PATH' in line and 'data.db' in line:
                    return 'data.db'
                if 'db_path = ' in line and '"' in line:
                    # Extract database name from quotes
                    parts = line.split('"')
                    if len(parts) >= 2:
                        return parts[1]
    except:
        pass

    # Use default
    return DEFAULT_DB


def backup_database(db_path):
    """Create backup of database before migration."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    # Create backup directory
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'backup_{timestamp}_{os.path.basename(db_path)}')

    # Copy database
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")

    return backup_path


def check_if_migrated(db_path):
    """Check if migration has already been run."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    has_transactions_table = False
    has_shortage_columns = False

    try:
        # Check for stock_transactions table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='stock_transactions'
        """)
        has_transactions_table = cursor.fetchone() is not None

        # Check for shortage_queue columns
        cursor.execute("PRAGMA table_info(shortage_queue)")
        columns = [col[1] for col in cursor.fetchall()]
        has_shortage_columns = all(col in columns for col in ['shortage_reason', 'shortage_type', 'notes'])

    except Exception as e:
        print(f"⚠️  Warning: Could not check migration status: {e}")
    finally:
        conn.close()

    return has_transactions_table and has_shortage_columns


def run_migration(db_path, migration_file):
    """Run the migration file."""
    # Check if migration file exists
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    # Read migration SQL
    print(f"\n📄 Reading migration file: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    # Connect to database
    print(f"🔗 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        # Execute migration
        print("🚀 Running migration...")
        cursor = conn.cursor()

        # Split and execute statements (to show progress)
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]

        for i, statement in enumerate(statements, 1):
            # Skip comments and empty lines
            if statement.startswith('--') or not statement:
                continue

            # Skip SELECT statements (verification queries)
            if statement.upper().startswith('SELECT'):
                continue

            try:
                cursor.execute(statement)
                # Show progress for important operations
                if any(keyword in statement.upper() for keyword in ['CREATE TABLE', 'ALTER TABLE', 'CREATE INDEX']):
                    if 'CREATE TABLE' in statement.upper():
                        table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip().split()[0]
                        print(f"   ✓ Created table: {table_name}")
                    elif 'ALTER TABLE' in statement.upper():
                        table_name = statement.split('ALTER TABLE')[1].split('ADD')[0].strip()
                        column_name = statement.split('ADD COLUMN')[1].split()[0].strip() if 'ADD COLUMN' in statement.upper() else '...'
                        print(f"   ✓ Added column to {table_name}: {column_name}")
                    elif 'CREATE INDEX' in statement.upper():
                        index_name = statement.split('CREATE INDEX')[1].split('ON')[0].strip().split()[-1]
                        print(f"   ✓ Created index: {index_name}")
            except sqlite3.OperationalError as e:
                # Ignore "already exists" errors (idempotent migrations)
                if 'already exists' in str(e) or 'duplicate column name' in str(e):
                    print(f"   ⊙ Skipped (already exists)")
                else:
                    raise

        # Commit transaction
        conn.commit()
        print("\n✅ Migration completed successfully!")

        return True

    except Exception as e:
        # Rollback on error
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print("\n💡 Database has been rolled back to previous state.")
        print(f"💡 Backup is available at: {backup_path}")
        return False

    finally:
        conn.close()


def verify_migration(db_path):
    """Verify that migration was successful."""
    print("\n🔍 Verifying migration...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check stock_transactions table
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='stock_transactions'")
        has_table = cursor.fetchone()[0] == 1

        if has_table:
            print("   ✓ stock_transactions table exists")
        else:
            print("   ✗ stock_transactions table NOT found")
            return False

        # Check shortage_queue columns
        cursor.execute("PRAGMA table_info(shortage_queue)")
        columns = {col[1] for col in cursor.fetchall()}

        required_columns = {'shortage_reason', 'shortage_type', 'notes'}
        missing_columns = required_columns - columns

        if not missing_columns:
            print("   ✓ All shortage_queue columns added")
        else:
            print(f"   ✗ Missing columns: {', '.join(missing_columns)}")
            return False

        # Check indexes
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_stock_transactions%'
        """)
        index_count = cursor.fetchone()[0]

        if index_count >= 4:
            print(f"   ✓ Indexes created ({index_count} indexes)")
        else:
            print(f"   ⚠ Some indexes might be missing ({index_count} found)")

        print("\n✅ Migration verification passed!")
        return True

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return False

    finally:
        conn.close()


def main():
    """Main function."""
    print("=" * 60)
    print("VNIX WMS - Database Migration Runner")
    print("=" * 60)

    # Get database path
    db_path = get_db_path()
    print(f"\n📁 Database: {db_path}")

    # Get migration file
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]
    else:
        migration_file = 'migrations/add_stock_transactions.sql'

    print(f"📄 Migration: {migration_file}")

    # Check if already migrated
    print("\n🔍 Checking migration status...")
    if check_if_migrated(db_path):
        print("\n⚠️  WARNING: Migration appears to have been run already!")
        print("   - stock_transactions table exists")
        print("   - shortage_queue columns exist")

        response = input("\n❓ Do you want to run migration anyway? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\n✋ Migration cancelled by user.")
            sys.exit(0)

    # Backup database
    print("\n💾 Creating backup...")
    global backup_path
    backup_path = backup_database(db_path)

    # Run migration
    success = run_migration(db_path, migration_file)

    if success:
        # Verify migration
        verify_migration(db_path)

        print("\n" + "=" * 60)
        print("🎉 Migration completed successfully!")
        print("=" * 60)
        print(f"\n✅ Database updated: {db_path}")
        print(f"💾 Backup available: {backup_path}")
        print("\n📝 Next steps:")
        print("   1. Restart your Flask application")
        print("   2. Test the new features (Phase 1-3)")
        print("   3. Check the documentation in docs/")
        print("\n")
    else:
        print("\n" + "=" * 60)
        print("❌ Migration failed - Database unchanged")
        print("=" * 60)
        print(f"\n💾 Backup available: {backup_path}")
        print("\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
