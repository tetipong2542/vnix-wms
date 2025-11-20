#!/usr/bin/env python3
"""
Migration Verification Tool
============================
Check if database migration has been run successfully.

Usage:
    python check_migration.py
"""

import os
import sys
import sqlite3
from datetime import datetime


def get_db_path():
    """Get database path from app.py or use default."""
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

    return 'data.db'  # Changed default from wms.db to data.db


def check_migration_status(db_path):
    """Check comprehensive migration status."""

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("\n💡 Tip: Make sure you're in the correct directory")
        return False

    print("=" * 60)
    print("VNIX WMS - Migration Status Check")
    print("=" * 60)
    print(f"\n📁 Database: {db_path}")
    print(f"📅 Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "-" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    all_checks_passed = True

    try:
        # Check 1: stock_transactions table
        print("\n✓ Check 1: stock_transactions table")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='stock_transactions'
        """)
        has_table = cursor.fetchone() is not None

        if has_table:
            # Count records
            cursor.execute("SELECT COUNT(*) FROM stock_transactions")
            count = cursor.fetchone()[0]
            print(f"   ✅ Table exists ({count} transactions)")

            # Show columns
            cursor.execute("PRAGMA table_info(stock_transactions)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"   📋 Columns: {', '.join(columns[:5])}...")
        else:
            print("   ❌ Table NOT found")
            all_checks_passed = False

        # Check 2: shortage_queue columns
        print("\n✓ Check 2: shortage_queue new columns")
        cursor.execute("PRAGMA table_info(shortage_queue)")
        columns = {col[1] for col in cursor.fetchall()}

        required_columns = {
            'shortage_reason': '❌ หาไม่เจอ, ของชำรุด, etc.',
            'shortage_type': 'PRE_PICK / POST_PICK',
            'notes': 'หมายเหตุจาก picker'
        }

        for col, description in required_columns.items():
            if col in columns:
                print(f"   ✅ {col:<20} - {description}")
            else:
                print(f"   ❌ {col:<20} - MISSING!")
                all_checks_passed = False

        # Check 3: Indexes
        print("\n✓ Check 3: Performance indexes")
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND (
                name LIKE 'idx_stock_transactions%' OR
                name LIKE 'idx_shortage_queue%'
            )
            ORDER BY name
        """)
        indexes = cursor.fetchall()

        if indexes:
            print(f"   ✅ Found {len(indexes)} indexes:")
            for idx in indexes:
                print(f"      • {idx[0]}")
        else:
            print("   ⚠️  No indexes found (may impact performance)")

        # Check 4: Sample data
        print("\n✓ Check 4: Sample data check")

        # Count shortage records with reason
        cursor.execute("""
            SELECT COUNT(*) FROM shortage_queue
            WHERE shortage_reason IS NOT NULL
        """)
        shortage_with_reason = cursor.fetchone()[0]

        # Count shortage records total
        cursor.execute("SELECT COUNT(*) FROM shortage_queue")
        total_shortages = cursor.fetchone()[0]

        print(f"   📊 Shortage records: {total_shortages} total")
        if shortage_with_reason > 0:
            percentage = (shortage_with_reason / total_shortages * 100) if total_shortages > 0 else 0
            print(f"   📊 With reason code: {shortage_with_reason} ({percentage:.1f}%)")
        else:
            print(f"   ℹ️  No shortage records with reason codes yet")

        # Check 5: Legacy data backfill
        print("\n✓ Check 5: Legacy data backfill")
        cursor.execute("""
            SELECT COUNT(*) FROM shortage_queue
            WHERE shortage_reason = 'LEGACY_DATA'
        """)
        legacy_count = cursor.fetchone()[0]

        if legacy_count > 0:
            print(f"   ✅ Legacy records backfilled: {legacy_count}")
        else:
            print(f"   ℹ️  No legacy data (all records are new)")

        # Summary
        print("\n" + "=" * 60)
        if all_checks_passed:
            print("✅ MIGRATION STATUS: COMPLETE")
            print("=" * 60)
            print("\n🎉 All checks passed! The migration has been run successfully.")
            print("\n✅ Phase 1 (Transaction Logging): Ready")
            print("✅ Phase 2 (Shortage Reason Codes): Ready")
            print("✅ Phase 3 (Analytics Dashboard): Ready")
            print("\n📝 You can now:")
            print("   • Import stock (transaction logging works)")
            print("   • Mark shortages with reason codes")
            print("   • View analytics dashboard at /analytics/shortage")
        else:
            print("❌ MIGRATION STATUS: INCOMPLETE")
            print("=" * 60)
            print("\n⚠️  Some checks failed. Please run migration:")
            print("   python run_migration.py")

        print("\n")

        return all_checks_passed

    except Exception as e:
        print(f"\n❌ Error checking migration status: {e}")
        return False

    finally:
        conn.close()


def main():
    """Main function."""
    db_path = get_db_path()
    success = check_migration_status(db_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
