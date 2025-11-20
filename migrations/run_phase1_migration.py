#!/usr/bin/env python3
"""
Phase 1 Migration Script: Add SLA Fields and Calculate Historical SLA

Usage:
    python migrations/run_phase1_migration.py

This script will:
1. Add sla_date columns to order_lines and batches tables
2. Calculate SLA for all existing orders based on order_time + platform
3. Calculate SLA for all batches (earliest SLA in batch)
4. Show validation report
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models import db, OrderLine, Batch
from sqlalchemy import text
from utils import compute_due_date, TH_TZ

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def run_sql_migration():
    """Run SQL migration to add sla_date columns"""
    print_header("📝 Running SQL Migration")

    sql_file = Path(__file__).parent / "phase1_add_sla_fields.sql"

    if not sql_file.exists():
        print(f"  ❌ SQL file not found: {sql_file}")
        return False

    print(f"  📄 Reading SQL file: {sql_file.name}")

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split by semicolons and execute each statement
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]

    executed = 0
    for stmt in statements:
        # Skip comments and validation queries
        if stmt.startswith('--') or stmt.upper().startswith('SELECT'):
            continue

        try:
            db.session.execute(text(stmt))
            executed += 1
        except Exception as e:
            # Ignore "column already exists" errors
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"  ⚠️  Column already exists (skipping)")
            else:
                print(f"  ❌ Error executing statement: {e}")
                return False

    db.session.commit()
    print(f"  ✅ Executed {executed} SQL statements")
    return True

def calculate_order_sla():
    """Calculate SLA for all orders based on order_time + platform"""
    print_header("🔄 Calculating SLA for Orders")

    # Get orders without SLA
    orders = OrderLine.query.filter(
        OrderLine.order_time.isnot(None),
        OrderLine.sla_date.is_(None)
    ).all()

    if not orders:
        print("  ℹ️  No orders need SLA calculation")
        return 0

    print(f"  📦 Found {len(orders)} orders without SLA")
    print("  🔄 Calculating SLA dates...")

    updated = 0
    errors = 0

    for order in orders:
        try:
            # Use existing compute_due_date function from utils.py
            sla_date = compute_due_date(order.platform, order.order_time)
            order.sla_date = sla_date
            updated += 1

            if updated % 100 == 0:
                print(f"  ... processed {updated} orders")
                db.session.commit()

        except Exception as e:
            errors += 1
            print(f"  ⚠️  Error calculating SLA for order {order.order_id}: {e}")

    db.session.commit()

    print(f"  ✅ Updated: {updated} orders")
    if errors > 0:
        print(f"  ⚠️  Errors: {errors} orders")

    return updated

def calculate_batch_sla():
    """Calculate SLA for all batches (use earliest SLA from orders in batch)"""
    print_header("🔄 Calculating SLA for Batches")

    # Get batches without SLA
    batches = Batch.query.filter(Batch.sla_date.is_(None)).all()

    if not batches:
        print("  ℹ️  No batches need SLA calculation")
        return 0

    print(f"  📦 Found {len(batches)} batches without SLA")
    print("  🔄 Calculating SLA dates...")

    updated = 0
    skipped = 0

    for batch in batches:
        # Get earliest SLA from orders in this batch
        orders = OrderLine.query.filter_by(batch_id=batch.batch_id).all()

        if not orders:
            skipped += 1
            continue

        # Find earliest SLA date
        sla_dates = [o.sla_date for o in orders if o.sla_date]

        if sla_dates:
            batch.sla_date = min(sla_dates)
            updated += 1
        else:
            skipped += 1

    db.session.commit()

    print(f"  ✅ Updated: {updated} batches")
    if skipped > 0:
        print(f"  ⚠️  Skipped: {skipped} batches (no orders or no SLA)")

    return updated

def show_validation_report():
    """Show validation report after migration"""
    print_header("📊 Validation Report")

    # Count orders with/without SLA
    total_orders = OrderLine.query.count()
    orders_with_sla = OrderLine.query.filter(OrderLine.sla_date.isnot(None)).count()
    orders_without_sla = total_orders - orders_with_sla

    print(f"\n  📦 Orders:")
    print(f"    Total:        {total_orders}")
    print(f"    With SLA:     {orders_with_sla}")
    print(f"    Without SLA:  {orders_without_sla}")

    # Count batches with/without SLA
    total_batches = Batch.query.count()
    batches_with_sla = Batch.query.filter(Batch.sla_date.isnot(None)).count()
    batches_without_sla = total_batches - batches_with_sla

    print(f"\n  📦 Batches:")
    print(f"    Total:        {total_batches}")
    print(f"    With SLA:     {batches_with_sla}")
    print(f"    Without SLA:  {batches_without_sla}")

    # Show urgent orders (SLA today or overdue)
    from datetime import date
    today = date.today()

    urgent_orders = OrderLine.query.filter(
        OrderLine.sla_date <= today,
        OrderLine.dispatch_status != 'dispatched'
    ).count()

    print(f"\n  ⚠️  Urgent Orders (SLA today or overdue): {urgent_orders}")

    # Show SLA distribution
    print(f"\n  📊 SLA Distribution by Platform:")

    platforms = ['Shopee', 'Lazada', 'TikTok']
    for platform in platforms:
        total = OrderLine.query.filter_by(platform=platform).count()
        with_sla = OrderLine.query.filter_by(platform=platform).filter(
            OrderLine.sla_date.isnot(None)
        ).count()

        if total > 0:
            percentage = (with_sla / total) * 100
            print(f"    {platform:10s}: {with_sla:5d} / {total:5d} ({percentage:5.1f}%)")

def main():
    print("\n🚀 Phase 1 Migration: Add SLA Fields and Calculate Historical SLA")
    print("=" * 70)

    app = create_app()

    with app.app_context():
        # Confirm before proceeding
        print("\n" + "⚠️  " * 15)
        response = input("\n  📝 Proceed with migration? (yes/no): ").strip().lower()

        if response != 'yes':
            print("\n  ❌ Migration cancelled by user")
            return

        # Step 1: Run SQL migration
        if not run_sql_migration():
            print("\n  ❌ Migration failed at SQL step")
            return

        # Step 2: Calculate SLA for orders
        orders_updated = calculate_order_sla()

        # Step 3: Calculate SLA for batches
        batches_updated = calculate_batch_sla()

        # Step 4: Show validation report
        show_validation_report()

        # Success
        print_header("✅ Migration Complete!")
        print("\n  Summary:")
        print(f"    Orders updated:  {orders_updated}")
        print(f"    Batches updated: {batches_updated}")
        print("\n  Next steps:")
        print("    1. Review the validation report above")
        print("    2. Test SLA features in the application")
        print("    3. Check that SLA priority is working correctly")
        print("    4. Ready for Phase 2: SLA-based Batch Creation")
        print("\n")

if __name__ == "__main__":
    main()
