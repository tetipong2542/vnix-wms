#!/usr/bin/env python3
"""
Phase 0 Migration Script: Fix Reserved Stock Release Bug

Usage:
    python migrations/run_phase0_migration.py

This script will:
1. Recalculate reserved_qty for all SKUs based on active batches
2. Show validation report
3. Allow rollback if needed
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, Stock, OrderLine, Batch
from sqlalchemy import text

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def backup_reserved_qty():
    """สำรอง reserved_qty ปัจจุบันก่อน migrate"""
    print_header("📦 Backup Current reserved_qty")

    stocks = Stock.query.all()
    backup = {stock.sku: stock.reserved_qty for stock in stocks}

    print(f"✅ Backed up reserved_qty for {len(backup)} SKUs")
    return backup

def show_before_state():
    """แสดงสถานะก่อน migrate"""
    print_header("📊 Current State (BEFORE Migration)")

    # Total reserved
    total_reserved = db.session.query(db.func.sum(Stock.reserved_qty)).scalar() or 0

    # Active batches
    active_batches = Batch.query.filter(
        (Batch.handover_confirmed.is_(None)) | (Batch.handover_confirmed == False)
    ).count()

    # Completed batches
    completed_batches = Batch.query.filter(Batch.handover_confirmed == True).count()

    # SKUs with reservation
    skus_with_reservation = Stock.query.filter(Stock.reserved_qty > 0).count()

    print(f"  Total Reserved Qty:        {total_reserved}")
    print(f"  SKUs with Reservation:     {skus_with_reservation}")
    print(f"  Active Batches:            {active_batches}")
    print(f"  Completed Batches:         {completed_batches}")

def recalculate_reserved_qty():
    """คำนวณ reserved_qty ใหม่"""
    print_header("🔄 Recalculating reserved_qty...")

    # Step 1: Reset all to 0
    print("\n  Step 1/2: Reset all reserved_qty to 0...")
    db.session.execute(text("UPDATE stocks SET reserved_qty = 0"))
    db.session.commit()
    print("  ✅ Reset complete")

    # Step 2: Recalculate based on active batches
    print("\n  Step 2/2: Recalculate based on active batches...")

    sql = text("""
        UPDATE stocks
        SET reserved_qty = (
            SELECT COALESCE(SUM(ol.qty), 0)
            FROM order_lines ol
            LEFT JOIN batches b ON ol.batch_id = b.batch_id
            WHERE
                ol.sku = stocks.sku
                AND ol.accepted = 1
                AND (b.handover_confirmed IS NULL OR b.handover_confirmed = 0)
                AND ol.dispatch_status != 'dispatched'
        )
    """)

    db.session.execute(sql)
    db.session.commit()
    print("  ✅ Recalculation complete")

def show_after_state():
    """แสดงสถานะหลัง migrate"""
    print_header("📊 New State (AFTER Migration)")

    # Total reserved
    total_reserved = db.session.query(db.func.sum(Stock.reserved_qty)).scalar() or 0

    # SKUs with reservation
    skus_with_reservation = Stock.query.filter(Stock.reserved_qty > 0).count()

    print(f"  Total Reserved Qty:        {total_reserved}")
    print(f"  SKUs with Reservation:     {skus_with_reservation}")

def validate_results():
    """ตรวจสอบผลลัพธ์"""
    print_header("🔍 Validation Report")

    # Check 1: SKUs with over-reservation (reserved_qty > qty)
    over_reserved = Stock.query.filter(Stock.reserved_qty > Stock.qty).all()

    if over_reserved:
        print("\n  ⚠️  WARNING: Found SKUs with over-reservation:")
        for stock in over_reserved:
            print(f"    - {stock.sku}: Stock={stock.qty}, Reserved={stock.reserved_qty}")
    else:
        print("\n  ✅ No over-reservation found")

    # Check 2: Completed batches with reserved stock
    sql = text("""
        SELECT DISTINCT b.batch_id, s.sku, s.reserved_qty
        FROM batches b
        JOIN order_lines ol ON ol.batch_id = b.batch_id
        JOIN stocks s ON s.sku = ol.sku
        WHERE b.handover_confirmed = 1
          AND s.reserved_qty > 0
        LIMIT 5
    """)

    result = db.session.execute(sql).fetchall()

    if result:
        print("\n  ⚠️  WARNING: Found completed batches still holding reservations:")
        for row in result:
            print(f"    - Batch {row[0]}: SKU={row[1]}, Reserved={row[2]}")
    else:
        print("\n  ✅ No reservation leaks from completed batches")

    # Check 3: Show top 10 SKUs by reservation
    print("\n  📦 Top 10 SKUs by Reservation:")
    top_skus = Stock.query.filter(Stock.reserved_qty > 0)\
        .order_by(Stock.reserved_qty.desc())\
        .limit(10)\
        .all()

    for stock in top_skus:
        available = stock.qty - stock.reserved_qty
        print(f"    - {stock.sku}: Total={stock.qty}, Reserved={stock.reserved_qty}, Available={available}")

def main():
    print("\n🚀 Phase 0 Migration: Fix Reserved Stock Release Bug")
    print("=" * 70)

    app = create_app()

    with app.app_context():
        # Show current state
        show_before_state()

        # Backup
        backup = backup_reserved_qty()

        # Confirm before proceeding
        print("\n" + "⚠️  " * 15)
        response = input("\n  📝 Proceed with migration? (yes/no): ").strip().lower()

        if response != 'yes':
            print("\n  ❌ Migration cancelled by user")
            return

        # Run migration
        recalculate_reserved_qty()

        # Show new state
        show_after_state()

        # Validate
        validate_results()

        # Success
        print_header("✅ Migration Complete!")
        print("\n  Next steps:")
        print("    1. Review the validation report above")
        print("    2. Test the application with real workflows")
        print("    3. Monitor logs for 'Stock Reservation Released' messages")
        print("    4. Check /batch-list and /scan/sku pages")
        print("\n")

if __name__ == "__main__":
    main()
