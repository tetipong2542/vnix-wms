
# app.py
from __future__ import annotations

import os
import json
from datetime import datetime, date, timedelta
from io import BytesIO
from functools import wraps
from collections import defaultdict

import pandas as pd
import qrcode
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, jsonify, session
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, text
from sqlalchemy.sql import bindparam

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from utils import (
    now_thai, to_thai_be, to_be_date_str, TH_TZ, current_be_year,
    normalize_platform, sla_text, compute_due_date, clean_logistic,
    format_sla_thai  # ✅ NEW: แปลง SLA เป็นภาษาไทย
)
from models import db, Shop, Product, Stock, StockTransaction, Sales, OrderLine, User, Batch, AuditLog, ShortageQueue
from importers import import_products, import_stock, import_sales, import_orders
from allocation import compute_allocation


APP_NAME = os.environ.get("APP_NAME", "VNIX Order Management")


# -----------------------------
# สร้างแอป + บูตระบบเบื้องต้น
# -----------------------------
def create_app():
    app = Flask(__name__)

    # ✅ Security: Require SECRET_KEY from environment (no fallback!)
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "❌ SECURITY ERROR: SECRET_KEY environment variable is not set!\n\n"
            "Please create a .env file with:\n"
            "  SECRET_KEY=your-random-secret-key\n\n"
            "Generate a secure key using:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\"\n"
        )
    app.secret_key = secret_key

    # Database configuration
    db_path = os.environ.get("DATABASE_PATH", "data.db")
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.path.dirname(__file__), db_path)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # ---------- Helper: Table name (OrderLine) ----------
    def _ol_table_name() -> str:
        try:
            return OrderLine.__table__.name
        except Exception:
            return getattr(OrderLine, "__tablename__", "order_lines")

    # ---------- Auto-migrate: ensure print columns exist ----------
    def _ensure_orderline_print_columns():
        tbl = _ol_table_name()
        with db.engine.connect() as con:
            cols = {row[1] for row in con.execute(text(f"PRAGMA table_info({tbl})")).fetchall()}

            def add(col, ddl):
                if col not in cols:
                    con.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {ddl}"))

            # สำหรับ "ใบงานคลัง"
            add("printed_warehouse", "INTEGER DEFAULT 0")
            add("printed_warehouse_count", "INTEGER DEFAULT 0")
            add("printed_warehouse_at", "TEXT")
            add("printed_warehouse_by_user_id", "INTEGER")

            # สำหรับ "Picking list"
            add("printed_picking", "INTEGER DEFAULT 0")
            add("printed_picking_count", "INTEGER DEFAULT 0")
            add("printed_picking_at", "TEXT")
            add("printed_picking_by_user_id", "INTEGER")

            # Tracking & Dispatch Management
            add("tracking_number", "TEXT")

            # Picking Management
            add("picked_qty", "INTEGER DEFAULT 0")
            add("picked_at", "TEXT")
            add("picked_by_user_id", "INTEGER")
            add("picked_by_username", "TEXT")
            add("shortage_qty", "INTEGER DEFAULT 0")  # จำนวนที่ขาด (สำหรับ Partial Picking)

            # Dispatch Management
            add("dispatch_status", "TEXT DEFAULT 'pending'")
            add("dispatched_at", "TEXT")
            add("dispatched_by_user_id", "INTEGER")
            add("dispatched_by_username", "TEXT")

            con.commit()

    with app.app_context():
        db.create_all()
        _ensure_orderline_print_columns()

        # ✅ Security: Bootstrap admin with environment-based credentials
        if User.query.count() == 0:
            # Get username and password from environment
            admin_username = os.environ.get("ADMIN_USERNAME", "admin")
            admin_password = os.environ.get("ADMIN_DEFAULT_PASSWORD")

            if not admin_password:
                # Generate a random temporary password
                import secrets
                admin_password = secrets.token_urlsafe(16)
                print("\n" + "="*70)
                print("⚠️  IMPORTANT: Default admin account created!")
                print("="*70)
                print(f"  Username: {admin_username}")
                print(f"  Temporary Password: {admin_password}")
                print("")
                print("  ⚠️  Please login and change this password immediately!")
                print("  ⚠️  This password will not be shown again!")
                print("="*70 + "\n")

            admin = User(
                username=admin_username,
                password_hash=generate_password_hash(admin_password),
                role="admin",
                active=True
            )
            db.session.add(admin)
            db.session.commit()

    # -----------------
    # Jinja filters
    # -----------------
    @app.template_filter("thai_be")
    def thai_be_filter(dt):
        try:
            return to_thai_be(dt)
        except Exception:
            return ""

    @app.template_filter("be_date")
    def be_date_filter(d):
        try:
            return to_be_date_str(d)
        except Exception:
            return ""

    @app.template_filter("clean_logistic")
    def clean_logistic_filter(logistic):
        """ตัดข้อความยาวๆ ของ logistic type ให้สั้นลง"""
        try:
            return clean_logistic(logistic)
        except Exception:
            return logistic or ""

    @app.template_filter("from_json")
    def from_json_filter(json_str):
        """แปลง JSON string เป็น dict"""
        try:
            if json_str:
                return json.loads(json_str)
            return {}
        except Exception:
            return {}

    # -----------------
    # UI context
    # -----------------
    @app.context_processor
    def inject_globals():
        return {
            "APP_NAME": APP_NAME,
            "BE_YEAR": current_be_year(),
            "CURRENT_USER": current_user(),
            "now_thai": now_thai
        }

    # ให้ template ตรวจ endpoint ได้ (กันพังค่า has_endpoint)
    @app.template_global()
    def has_endpoint(endpoint: str) -> bool:
        try:
            return endpoint in app.view_functions
        except Exception:
            return False

    # -----------------
    # Auth helpers
    # -----------------
    def current_user():
        uid = session.get("uid")
        if not uid:
            return None
        return db.session.get(User, uid)

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user():
                return redirect(url_for("login", next=request.path))
            return fn(*args, **kwargs)
        return wrapper

    # -----------------
    # Audit logging helper (NFR-03)
    # -----------------
    def log_audit(action: str, details: dict = None, batch_id: str = None, order_count: int = None, print_count: int = None):
        """Create audit log entry for important actions"""
        cu = current_user()
        log = AuditLog(
            action=action,
            user_id=cu.id if cu else None,
            username=cu.username if cu else "system",
            details=json.dumps(details or {}, ensure_ascii=False),
            batch_id=batch_id,
            order_count=order_count,
            print_count=print_count
        )
        db.session.add(log)
        db.session.commit()

    # -----------------
    # Stock Transaction Logging (Option 2: Banking-style)
    # -----------------
    def log_stock_transaction(
        sku: str,
        transaction_type: str,
        quantity: int,
        reason_code: str,
        reference_type: str = None,
        reference_id: str = None,
        notes: str = None
    ):
        """
        Log stock transaction (Banking-style ledger)

        Args:
            sku: SKU code
            transaction_type: 'RECEIVE', 'RESERVE', 'RELEASE', 'PICK', 'DAMAGE', 'ADJUST', 'RETURN'
            quantity: Signed integer (+10 for increase, -2 for decrease)
            reason_code: Root cause code (e.g., 'IMPORT', 'BATCH_RESERVE', 'FOUND_DAMAGED', 'CANT_FIND')
            reference_type: 'import', 'batch', 'order_line', 'shortage', 'adjustment'
            reference_id: ID of the reference entity (batch_id, order_line_id, etc.)
            notes: Additional context

        Returns:
            StockTransaction: Created transaction record

        Example:
            # Stock import: +100 items
            log_stock_transaction('SKU-001', 'RECEIVE', +100, 'IMPORT', 'import', 'IMP-20250120')

            # Batch reserve: -10 items
            log_stock_transaction('SKU-001', 'RESERVE', -10, 'BATCH_RESERVE', 'batch', 'B-SHP-20250120-R1')

            # Handover release: +2 items (returned reserved stock)
            log_stock_transaction('SKU-001', 'RELEASE', +2, 'HANDOVER_RELEASE', 'batch', 'B-SHP-20250120-R1')

            # Damage found: -1 item
            log_stock_transaction('SKU-001', 'DAMAGE', -1, 'FOUND_DAMAGED', 'shortage', '123')
        """
        # Get current stock to calculate balance_after
        stock = Stock.query.filter_by(sku=sku).first()

        if not stock:
            # Create stock record if it doesn't exist
            stock = Stock(sku=sku, qty=0, reserved_qty=0)
            db.session.add(stock)
            db.session.flush()  # Get the ID without committing

        # Calculate balance based on transaction type
        if transaction_type in ['RECEIVE', 'RELEASE', 'RETURN', 'ADJUST']:
            # These affect qty (actual stock)
            balance_before = stock.qty or 0
            balance_after = balance_before + quantity
        elif transaction_type in ['RESERVE']:
            # Reserve affects reserved_qty (virtual deduction)
            balance_before = stock.reserved_qty or 0
            balance_after = balance_before + abs(quantity)  # RESERVE is always positive increase in reserved_qty
        else:
            # For other types (PICK, DAMAGE), use qty
            balance_before = stock.qty or 0
            balance_after = balance_before + quantity

        # Get current user
        cu = current_user()
        created_by_username = cu.username if cu else "system"

        # Create transaction record
        tx = StockTransaction(
            sku=sku,
            transaction_type=transaction_type,
            quantity=quantity,
            balance_after=balance_after,
            reason_code=reason_code,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=created_by_username,
            notes=notes
        )
        db.session.add(tx)

        # Note: We don't update the Stock table here - that's done separately
        # This function only LOGS the transaction for audit trail
        # The actual stock update happens in the calling code

        return tx

    # -----------------
    # Batch Management Helpers (FR-04 to FR-09)
    # -----------------
    def generate_batch_id(platform: str, batch_date: date, run_no: int) -> str:
        """
        FR-06: Generate Batch ID in format: SH-YYYY-MM-DD-RN
        Examples: SH-2024-11-13-R1, LA-2024-11-13-R2, TT-2024-11-13-R1
        """
        platform_prefix = {
            "Shopee": "SH",
            "Lazada": "LA",
            "TikTok": "TT",
        }.get(platform, "OT")  # OT = Other
        date_str = batch_date.strftime("%Y-%m-%d")
        return f"{platform_prefix}-{date_str}-R{run_no}"

    def compute_batch_summary(orders: list) -> dict:
        """
        FR-08: Compute batch summary by carrier and shop
        Returns: {total_orders, carrier_summary, shop_summary}

        แก้ไข: นับ carrier และ shop ตาม unique order_id เท่านั้น (ไม่นับซ้ำถ้า order มีหลาย SKU)
        """
        from importers import extract_carrier_from_logistics
        
        carrier_counts = defaultdict(int)
        shop_counts = defaultdict(int)
        order_ids_seen = set()

        # Group orders by order_id first
        orders_by_id = defaultdict(list)
        for order in orders:
            orders_by_id[order.order_id].append(order)

        # Count unique orders by carrier and shop
        for order_id, order_items in orders_by_id.items():
            # Take first item to get carrier and shop (all items in same order have same carrier/shop)
            first_item = order_items[0]

            # Extract carrier using the standard function
            # Try carrier field first, fallback to logistic_type
            carrier_text = first_item.carrier if first_item.carrier and str(first_item.carrier).strip() and str(first_item.carrier).lower() not in ['Unknown', 'none', ''] else first_item.logistic_type
            carrier = extract_carrier_from_logistics(carrier_text)
            
            carrier_counts[carrier] += 1

            # Get shop name
            shop = db.session.get(Shop, first_item.shop_id) if first_item.shop_id else None
            shop_name = shop.name if shop else "Unknown"
            shop_counts[shop_name] += 1

        return {
            "total_orders": len(orders_by_id),
            "carrier_summary": dict(carrier_counts),
            "shop_summary": dict(shop_counts)
        }

    def calculate_order_status(order_lines: list) -> str:
        """
        คำนวณสถานะของออเดอร์ตามรายการสินค้าทั้งหมด (Partial Picking Support)

        Returns:
        - "ready": ทุก line item หยิบครบแล้ว
        - "partial_ready": มีบาง line item หยิบครบ, บางตัวมี shortage
        - "pending_refill": มี shortage แต่ยังไม่มีการหยิบเลย หรือหยิบได้บางส่วน
        - "pending": ยังไม่เริ่มหยิบเลย
        - "dispatched": ส่งไปแล้ว
        """
        if not order_lines:
            return "pending"

        # ถ้า dispatch_status เป็น dispatched แล้ว ให้ return ทันที
        if all(line.dispatch_status == "dispatched" for line in order_lines):
            return "dispatched"

        # Check if any line has been picked
        any_picked = any(line.picked_qty and line.picked_qty > 0 for line in order_lines)

        # Check if all lines are fully picked
        all_complete = all(line.picked_qty and line.picked_qty >= line.qty for line in order_lines)

        # Check if any line has shortage
        has_shortage = any(getattr(line, 'shortage_qty', 0) and getattr(line, 'shortage_qty', 0) > 0 for line in order_lines)

        if all_complete and not has_shortage:
            return "ready"  # ทุกอย่างครบ พร้อมส่ง
        elif any_picked and has_shortage:
            return "partial_ready"  # หยิบได้บางส่วน มี shortage
        elif has_shortage:
            return "pending_refill"  # มี shortage รอเติมของ
        elif any_picked:
            return "partial_ready"  # กำลังหยิบอยู่
        else:
            return "pending"  # ยังไม่เริ่มหยิบ

    def check_batch_locked(batch_id: str, action: str = "modify") -> tuple:
        """
        Check if batch is locked before allowing modification (Phase 2.4)

        Args:
            batch_id: Batch ID to check
            action: Action being performed (for error message)

        Returns:
            tuple: (is_allowed: bool, error_message: str or None)
        """
        batch = db.session.get(Batch, batch_id)

        if not batch:
            return False, "ไม่พบ Batch"

        if not batch.locked:
            return True, None  # ไม่ได้ lock, อนุญาต

        cu = current_user()

        # Admin can bypass lock
        if cu and cu.role == "admin":
            return True, None

        # Locked - not allowed for non-admin users
        locked_info = f"โดย {batch.locked_by_username or 'Unknown'}"
        if batch.locked_at:
            from datetime import datetime
            locked_info += f" เมื่อ {batch.locked_at.strftime('%Y-%m-%d %H:%M')}"

        error = f"❌ Batch {batch_id} ถูก lock แล้ว {locked_info}\n\n"
        error += f"ไม่สามารถ{action}ได้\n"
        error += "กรุณาติดต่อ Admin หรือใช้ Batch อื่น"

        return False, error

    def calculate_batch_progress(batch_id: str) -> dict:
        """
        คำนวณ Batch Progress แบบ Quantity-based (นับจำนวนชิ้น)
        ใช้สูตรเดียวกันทุกที่เพื่อความสอดคล้อง

        Phase 2.1: แก้ไขปัญหา Progress Calculation ที่ไม่สอดคล้องกัน
        - ใช้ Quantity-based แทน Order-based
        - นับ shortage ที่ resolved/cancelled เป็น completed

        Args:
            batch_id: Batch ID to calculate progress

        Returns:
            dict: {
                "total_qty": int,
                "picked_qty": int,
                "shortage_qty": int,
                "completed_qty": int,
                "progress_percent": float,
                "total_orders": int,
                "completed_orders": int
            }
        """
        orders = OrderLine.query.filter_by(batch_id=batch_id).all()

        if not orders:
            return {
                "total_qty": 0,
                "picked_qty": 0,
                "shortage_qty": 0,
                "completed_qty": 0,
                "progress_percent": 0,
                "total_orders": 0,
                "completed_orders": 0
            }

        # คำนวณ Quantity
        total_qty = sum(order.qty for order in orders)
        picked_qty = sum(order.picked_qty or 0 for order in orders)

        # นับ shortage_qty จาก OrderLine (ไม่ใช่ ShortageQueue)
        # shortage_qty = จำนวนที่ขาดและไม่สามารถหยิบได้
        shortage_qty = sum(order.shortage_qty or 0 for order in orders)

        # ✅ Completed = เฉพาะที่หยิบได้จริง (ไม่นับ shortage)
        # เพราะ shortage คือสิ่งที่ขาด ไม่ใช่สิ่งที่เสร็จสมบูรณ์
        completed_qty = picked_qty

        # คำนวณ Progress
        if total_qty == 0:
            progress_percent = 0
        else:
            progress_percent = (completed_qty / total_qty) * 100

        # นับจำนวน Order (สำหรับ backward compatibility)
        total_orders = len(orders)
        completed_orders = sum(1 for o in orders if o.dispatch_status in ['dispatched', 'ready', 'partial_ready'])

        return {
            "total_qty": total_qty,
            "picked_qty": picked_qty,
            "shortage_qty": shortage_qty,
            "completed_qty": completed_qty,
            "progress_percent": round(progress_percent, 1),
            "total_orders": total_orders,
            "completed_orders": completed_orders
        }

    def is_batch_ready_for_handover(batch_id: str) -> dict:
        """
        ตรวจสอบว่า Batch พร้อมสร้าง Handover Code หรือไม่
        โดยดูว่าทุก SKU เสร็จสิ้นแล้วหรือยัง (SKU-based check)

        Returns:
            dict: {
                "ready": bool,
                "reason": str,
                "total_skus": int,
                "completed_skus": int,
                "pending_skus": list
            }
        """
        orders = OrderLine.query.filter_by(batch_id=batch_id).all()

        if not orders:
            return {
                "ready": False,
                "reason": "Batch ไม่มี Orders",
                "total_skus": 0,
                "completed_skus": 0,
                "pending_skus": []
            }

        # คำนวณ SKU Progress (เหมือนกับที่แสดงในหน้า Batch Detail)
        from collections import defaultdict
        sku_status = {}

        for order in orders:
            if order.sku not in sku_status:
                sku_status[order.sku] = {
                    "sku": order.sku,
                    "total_need": 0,
                    "total_picked": 0,
                    "total_shortage": 0
                }

            sku_status[order.sku]["total_need"] += order.qty
            sku_status[order.sku]["total_picked"] += (order.picked_qty or 0)
            sku_status[order.sku]["total_shortage"] += (order.shortage_qty or 0)

        # ตรวจสอบสถานะแต่ละ SKU
        total_skus = len(sku_status)
        completed_skus = 0
        pending_skus = []
        has_shortage = False

        for sku, data in sku_status.items():
            # ✅ SKU เสร็จสิ้น = หยิบครบ (ไม่นับ shortage)
            # ถ้ามี shortage แสดงว่ายังไม่เสร็จสมบูรณ์
            if data["total_shortage"] > 0:
                has_shortage = True
                pending_skus.append({
                    "sku": sku,
                    "need": data["total_need"],
                    "picked": data["total_picked"],
                    "shortage": data["total_shortage"],
                    "remaining": data["total_need"] - data["total_picked"]
                })
            elif data["total_picked"] >= data["total_need"]:
                completed_skus += 1
            else:
                pending_skus.append({
                    "sku": sku,
                    "need": data["total_need"],
                    "picked": data["total_picked"],
                    "shortage": 0,
                    "remaining": data["total_need"] - data["total_picked"]
                })

        # ✅ ทุก SKU ต้องเสร็จสิ้น และ ไม่มี shortage
        is_ready = (completed_skus == total_skus) and not has_shortage

        if is_ready:
            reason = "ทุก SKU เสร็จสิ้นแล้ว พร้อมสร้าง Handover Code"
        elif has_shortage:
            reason = f"ยังมี SKU ที่มี Shortage ({len([s for s in pending_skus if s.get('shortage', 0) > 0])} SKU)"
        else:
            reason = f"ยังมี {len(pending_skus)} SKU ที่ยังไม่เสร็จ"

        return {
            "ready": is_ready,
            "reason": reason,
            "total_skus": total_skus,
            "completed_skus": completed_skus,
            "pending_skus": pending_skus,
            "has_shortage": has_shortage
        }

    def get_next_run_number(platform: str, batch_date: date = None, lock: bool = True) -> int:
        """
        Get next available run number for a platform and date.
        Returns max(run_no) + 1, or 1 if no batches exist.

        ✅ Security: Race condition protection
        - Uses SELECT FOR UPDATE to lock rows during transaction
        - Prevents multiple users from getting the same run number

        Args:
            platform: Platform name (Shopee, Lazada, TikTok)
            batch_date: Date for batch (default: today)
            lock: Use SELECT FOR UPDATE lock (default: True)
        """
        if batch_date is None:
            batch_date = now_thai().date()

        platform_std = normalize_platform(platform)

        # ✅ Security: Use SELECT FOR UPDATE to lock batch records
        # This prevents race conditions when multiple users create batches simultaneously
        if lock:
            # Get the latest batch with lock to prevent concurrent access
            from sqlalchemy import select
            latest_batch = db.session.execute(
                select(Batch)
                .filter_by(platform=platform_std, batch_date=batch_date)
                .order_by(Batch.run_no.desc())
                .limit(1)
                .with_for_update()  # 🔒 Lock until transaction commits
            ).scalars().first()

            max_run = latest_batch.run_no if latest_batch else 0
        else:
            # Legacy query without lock (for read-only operations)
            max_run = db.session.query(func.max(Batch.run_no))\
                .filter_by(platform=platform_std, batch_date=batch_date)\
                .scalar()
            max_run = max_run or 0

        return max_run + 1

    def create_batch_from_pending(platform: str, run_no: int = None, batch_date: date = None) -> Batch:
        """
        FR-04 to FR-07 + Phase 2: Create batch from pending orders with SLA-based allocation

        ✅ Phase 2: SLA-based Stock Allocation
        - Calculates SLA for orders without sla_date
        - Sorts orders by SLA (earliest first)
        - Allocates stock based on SLA priority
        - Only creates batch with orders that have sufficient stock
        - Orders without stock are marked as 'waiting_stock'

        ✅ Security: Race condition protection using FOR UPDATE lock

        Args:
            platform: Platform name (Shopee, Lazada, TikTok)
            run_no: Run number (if None, auto-generate with lock)
            batch_date: Batch date (default: today)
        """
        if batch_date is None:
            batch_date = now_thai().date()

        platform_std = normalize_platform(platform)

        # ✅ Security: Auto-generate run_no with lock if not provided
        if run_no is None:
            run_no = get_next_run_number(platform_std, batch_date, lock=True)

        batch_id = generate_batch_id(platform_std, batch_date, run_no)

        # ✅ Security: Check if batch already exists (prevent duplicate batch_id)
        existing = db.session.get(Batch, batch_id)
        if existing:
            raise ValueError(f"Batch {batch_id} already exists")

        # ✅ Security: Use SELECT FOR UPDATE to lock pending orders
        # This prevents race conditions when multiple users create batches simultaneously
        from sqlalchemy import select
        pending_orders = db.session.execute(
            select(OrderLine)
            .filter_by(
                platform=platform_std,
                batch_status="pending_batch"
            )
            .with_for_update()  # 🔒 Lock rows until commit
        ).scalars().all()

        if not pending_orders:
            raise ValueError(f"No pending orders found for {platform_std}")

        # ✅ Phase 2: Calculate SLA for orders that don't have it yet
        orders_updated = 0
        for order in pending_orders:
            if not order.sla_date and order.order_time:
                order.sla_date = compute_due_date(platform_std, order.order_time)
                orders_updated += 1

        if orders_updated > 0:
            db.session.commit()
            app.logger.info(f"📅 Calculated SLA for {orders_updated} orders")

        # ✅ Phase 2: Sort orders by SLA (earliest first, None last)
        pending_orders = sorted(
            pending_orders,
            key=lambda o: (o.sla_date is None, o.sla_date, o.order_time or datetime.min)
        )

        app.logger.info(f"📊 Processing {len(pending_orders)} orders in SLA order")

        # ✅ Phase 2: SLA-based Stock Allocation Simulation
        # Build available stock tracker (current available - what we'll allocate)
        stock_tracker = {}  # {sku: available_qty}
        for sku in set(o.sku for o in pending_orders):
            stock = Stock.query.filter_by(sku=sku).first()
            if stock:
                stock_tracker[sku] = stock.available_qty
            else:
                stock_tracker[sku] = 0

        # Allocate orders to batch based on SLA priority
        batch_orders = []  # Orders that will be in the batch
        waiting_orders = []  # Orders that don't have stock

        for order in pending_orders:
            available = stock_tracker.get(order.sku, 0)

            if available >= order.qty:
                # ✅ Enough stock - allocate to batch
                batch_orders.append(order)
                stock_tracker[order.sku] = available - order.qty
                app.logger.debug(
                    f"  ✅ Allocated: {order.sku} x{order.qty} | "
                    f"SLA: {order.sla_date} | "
                    f"Remaining: {stock_tracker[order.sku]}"
                )
            else:
                # ❌ Not enough stock - mark as waiting
                waiting_orders.append(order)
                app.logger.warning(
                    f"  ⏳ Waiting: {order.sku} x{order.qty} | "
                    f"SLA: {order.sla_date} | "
                    f"Available: {available} | "
                    f"Shortage: {order.qty - available}"
                )

        # Check if we have any orders to create a batch
        if not batch_orders:
            # Mark all orders as waiting_stock
            for order in waiting_orders:
                order.batch_status = "waiting_stock"
            db.session.commit()
            raise ValueError(
                f"No orders can be batched for {platform_std} - "
                f"all {len(waiting_orders)} orders are waiting for stock"
            )

        # ✅ Phase 2: Compute summary from batch_orders only (not all pending orders)
        summary = compute_batch_summary(batch_orders)

        # ✅ Phase 2: Calculate batch SLA (earliest SLA in batch)
        batch_sla_dates = [o.sla_date for o in batch_orders if o.sla_date]
        batch_sla = min(batch_sla_dates) if batch_sla_dates else None

        # Create batch
        cu = current_user()
        batch = Batch(
            batch_id=batch_id,
            platform=platform_std,
            run_no=run_no,
            batch_date=batch_date,
            sla_date=batch_sla,  # ✅ Phase 2: Set batch SLA
            total_orders=summary["total_orders"],
            spx_count=summary["carrier_summary"].get("SPX", 0),
            flash_count=summary["carrier_summary"].get("Flash", 0),
            lex_count=summary["carrier_summary"].get("LEX", 0),
            jt_count=summary["carrier_summary"].get("J&T", 0),
            other_count=sum(v for k, v in summary["carrier_summary"].items() if k not in ["SPX", "Flash", "LEX", "J&T"]),
            shop_summary=json.dumps(summary["shop_summary"], ensure_ascii=False),
            locked=True,  # FR-07: Lock immediately
            created_by_user_id=cu.id if cu else None,
            created_by_username=cu.username if cu else "system"
        )
        db.session.add(batch)

        # ✅ Phase 2: Update orders to batched status (only batch_orders)
        for order in batch_orders:
            order.batch_status = "batched"
            order.batch_id = batch_id

        # ✅ Phase 2: Mark orders without stock as waiting_stock
        for order in waiting_orders:
            order.batch_status = "waiting_stock"
            # Keep batch_id as None for waiting orders

        # ✅ Priority 2.1: Create PRE_PICK shortage records for waiting orders
        cu = current_user() if 'cu' not in locals() else cu
        for order in waiting_orders:
            available = stock_tracker.get(order.sku, 0)
            shortage_qty = order.qty - available

            # Create PRE_PICK shortage record
            shortage_record = ShortageQueue(
                order_line_id=order.id,
                order_id=order.order_id,
                sku=order.sku,
                qty_required=order.qty,
                qty_picked=0,
                qty_shortage=shortage_qty,
                original_batch_id=None,  # No batch yet since stock insufficient
                shortage_reason='INSUFFICIENT_STOCK',
                shortage_type='PRE_PICK',  # ← KEY: Mark as PRE_PICK
                notes=f"Insufficient stock during batch creation. Available: {available}, Required: {order.qty}",
                status='waiting_stock',
                created_by_user_id=cu.id if cu else None,
                created_by_username=cu.username if cu else "system"
            )
            db.session.add(shortage_record)

            # Update order shortage_qty field
            order.shortage_qty = shortage_qty
            order.dispatch_status = "waiting_stock"

            # Log PRE_PICK transaction
            log_stock_transaction(
                sku=order.sku,
                transaction_type='DAMAGE',
                quantity=-shortage_qty,
                reason_code='PRE_PICK_SHORTAGE',
                reference_type='order_line',
                reference_id=str(order.id),
                notes=f"PRE_PICK shortage: {order.order_id} - Available: {available}, Required: {order.qty}"
            )

            app.logger.info(
                f"  📝 Created PRE_PICK shortage: {order.order_id} | "
                f"SKU: {order.sku} | Shortage: {shortage_qty}"
            )

        # ✅ Phase 2: Calculate SKU requirements for batch_orders only
        sku_requirements = {}
        for order in batch_orders:
            sku_requirements[order.sku] = sku_requirements.get(order.sku, 0) + order.qty

        # ✅ Stock Reservation: Reserve stock for this batch (batch_orders only)
        for sku, qty_needed in sku_requirements.items():
            stock = Stock.query.filter_by(sku=sku).first()
            if stock:
                stock.reserved_qty = (stock.reserved_qty or 0) + qty_needed
            else:
                # Create stock record with 0 qty but reserved amount
                stock = Stock(sku=sku, qty=0, reserved_qty=qty_needed)
                db.session.add(stock)

            # ✅ Option 2: Log stock reservation transaction
            log_stock_transaction(
                sku=sku,
                transaction_type='RESERVE',
                quantity=qty_needed,  # RESERVE is always positive (amount reserved)
                reason_code='BATCH_RESERVE',
                reference_type='batch',
                reference_id=batch_id,
                notes=f"Reserved {qty_needed} units for batch {batch_id}"
            )

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to create batch {batch_id}: {str(e)}")
            raise ValueError(f"Failed to create batch: {str(e)}")

        # ✅ Phase 2: Log SLA-based allocation results
        app.logger.info(
            f"✅ Batch {batch_id} created | "
            f"SLA: {batch_sla} | "
            f"Orders in batch: {len(batch_orders)} | "
            f"Waiting for stock: {len(waiting_orders)}"
        )

        if waiting_orders:
            app.logger.warning(
                f"⏳ {len(waiting_orders)} orders marked as waiting_stock for {platform_std}"
            )

        # Log audit
        log_audit("create_batch", {
            "batch_id": batch_id,
            "platform": platform_std,
            "run_no": run_no,
            "batch_sla": str(batch_sla) if batch_sla else None,  # ✅ Phase 2: Include SLA
            "orders_in_batch": len(batch_orders),  # ✅ Phase 2: Separate counts
            "orders_waiting": len(waiting_orders),
            "summary": summary
        }, batch_id=batch_id, order_count=summary["total_orders"])

        return batch

    def create_batch_with_retry(platform: str, batch_date: date = None, max_retries: int = 3) -> Batch:
        """
        Create batch with automatic retry on duplicate batch_id errors.

        ✅ Security: Handles race condition gracefully
        - Retries up to max_retries times if batch_id already exists
        - Uses exponential backoff between retries
        - Auto-generates run_no with lock on each attempt

        Args:
            platform: Platform name (Shopee, Lazada, TikTok)
            batch_date: Batch date (default: today)
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Batch: Created batch object

        Raises:
            ValueError: If all retry attempts fail
        """
        import time
        import random

        last_error = None

        for attempt in range(max_retries):
            try:
                # Try to create batch with auto-generated run_no
                batch = create_batch_from_pending(platform, run_no=None, batch_date=batch_date)
                return batch

            except ValueError as e:
                error_msg = str(e)

                # Check if it's a duplicate batch_id error
                if "already exists" in error_msg:
                    last_error = e
                    app.logger.warning(f"Batch creation attempt {attempt + 1}/{max_retries} failed: {error_msg}")

                    # If not the last attempt, wait and retry
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        wait_time = (2 ** attempt) * 0.1 + random.uniform(0, 0.1)
                        app.logger.info(f"Retrying in {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                        continue
                else:
                    # Not a duplicate error, re-raise immediately
                    raise

            except Exception as e:
                # Unexpected error, re-raise immediately
                app.logger.error(f"Unexpected error during batch creation: {str(e)}")
                raise

        # All retries failed
        raise ValueError(f"Failed to create batch after {max_retries} attempts. Last error: {last_error}")

    def release_stock_reservation(batch_id: str, sku: str, qty_to_release: int, reason: str = "completed") -> bool:
        """
        ✅ Phase 0: Release reserved stock for a specific SKU in a batch

        This function should be called when:
        1. SKU is fully picked (picked_qty >= required_qty)
        2. Shortage is resolved (cancelled/reduced)
        3. Batch is handed over (all SKUs completed)

        Args:
            batch_id: Batch ID
            sku: SKU to release reservation
            qty_to_release: Quantity to release
            reason: Reason for release (for logging)

        Returns:
            bool: True if released successfully, False otherwise

        Logic:
            released_qty = picked_qty + shortage_qty
            - picked_qty: จำนวนที่หยิบได้จริง (ออกจากสต็อกแล้ว)
            - shortage_qty: จำนวนที่ขาด (ไม่มีในสต็อกตั้งแต่แรก หรือถูก resolve แล้ว)

        IMPORTANT: This function does NOT commit. Caller must commit after calling this function.
        """
        if qty_to_release <= 0:
            return False

        try:
            stock = Stock.query.filter_by(sku=sku).with_for_update().first()

            if not stock:
                app.logger.warning(f"⚠️ Stock not found for SKU {sku} - cannot release reservation")
                return False

            if stock.reserved_qty <= 0:
                app.logger.warning(f"⚠️ No reserved stock for SKU {sku} - already released or never reserved")
                return False

            old_reserved = stock.reserved_qty
            stock.reserved_qty = max(0, stock.reserved_qty - qty_to_release)

            # ✅ Option 2: Log stock reservation release transaction
            log_stock_transaction(
                sku=sku,
                transaction_type='RELEASE',
                quantity=qty_to_release,  # Positive number (amount released from reservation)
                reason_code='HANDOVER_RELEASE',
                reference_type='batch',
                reference_id=batch_id,
                notes=f"Released {qty_to_release} units from reservation | Reason: {reason}"
            )

            app.logger.info(
                f"✅ Stock Reservation Released: {sku} | "
                f"Batch: {batch_id} | "
                f"Released: {qty_to_release} | "
                f"Reserved: {old_reserved} → {stock.reserved_qty} | "
                f"Reason: {reason}"
            )

            # ✅ FIX: ไม่ commit ที่นี่ ให้ caller เป็นคน commit
            # เพื่อป้องกัน partial commit และ race condition
            return True

        except Exception as e:
            app.logger.error(f"❌ Failed to release stock reservation for {sku}: {str(e)}")
            # ไม่ rollback ที่นี่ เพราะอาจมี operation อื่นใน transaction
            raise  # Re-raise exception ให้ caller จัดการ

    # -----------------
    # Utilities (app)
    # -----------------
    def parse_date_any(s: str | None):
        if not s:
            return None
        s = s.strip()
        try:
            if "-" in s:
                y, m, d = s.split("-")
                return date(int(y), int(m), int(d))
            else:
                d, m, y = s.split("/")
                y = int(y)
                if y > 2400:
                    y -= 543
                return date(y, int(m), int(d))
        except Exception:
            return None

    def _get_line_sku(line) -> str:
        if hasattr(line, "sku") and line.sku:
            return str(line.sku).strip()
        try:
            prod = getattr(line, "product", None)
            if prod and getattr(prod, "sku", None):
                return str(prod.sku).strip()
        except Exception:
            pass
        return ""

    def _calc_stock_qty_for_line(line: OrderLine) -> int:
        sku = _get_line_sku(line)
        if not sku:
            return 0
        prod = Product.query.filter_by(sku=sku).first()
        if prod and hasattr(prod, "stock_qty"):
            try:
                return int(prod.stock_qty or 0)
            except Exception:
                pass
        st = Stock.query.filter_by(sku=sku).first()
        try:
            return int(st.qty) if st and st.qty is not None else 0
        except Exception:
            return 0

    def _build_allqty_map(rows: list[dict]) -> dict[str, int]:
        total_by_sku: dict[str, int] = {}
        for r in rows:
            sku = (r.get("sku") or "").strip()
            if not sku:
                continue
            total_by_sku[sku] = total_by_sku.get(sku, 0) + int(r.get("qty", 0) or 0)
        return total_by_sku

    def _recompute_allocation_row(r: dict) -> dict:
        stock_qty = int(r.get("stock_qty", 0) or 0)
        allqty = int(r.get("allqty", r.get("qty", 0)) or 0)
        sales_status = (r.get("sales_status") or "").upper()
        packed_flag = bool(r.get("packed", False))
        accepted = bool(r.get("accepted", False))
        order_time = r.get("order_time")
        platform = r.get("platform") or (r.get("shop_platform") if r.get("shop_platform") else "")

        if sales_status == "PACKED" or packed_flag:
            allocation_status = "PACKED"
        elif accepted:
            allocation_status = "ACCEPTED"
        elif stock_qty <= 0:
            allocation_status = "SHORTAGE"
        elif allqty > stock_qty:
            allocation_status = "NOT_ENOUGH"
        elif stock_qty <= 3:
            allocation_status = "LOW_STOCK"
        else:
            allocation_status = "READY_ACCEPT"

        if allocation_status == "PACKED":
            sla = ""
        else:
            try:
                sla = sla_text(platform, order_time) if order_time else ""
            except Exception:
                sla = ""
        try:
            due_date = compute_due_date(platform, order_time) if order_time else None
        except Exception:
            due_date = None

        r["allocation_status"] = allocation_status
        r["sla"] = sla
        r["due_date"] = due_date
        return r

    def _annotate_order_spans(rows: list[dict]) -> list[dict]:
        seen = set()
        for r in rows:
            oid = (r.get("order_id") or "").strip()
            if not oid:
                r["show_order_id"] = True
                r["order_id_display"] = ""
                continue
            if oid in seen:
                r["show_order_id"] = False
                r["order_id_display"] = ""
            else:
                r["show_order_id"] = True
                r["order_id_display"] = oid
                seen.add(oid)
        return rows

    def _group_rows_for_report(rows: list[dict]) -> list[dict]:
        def _key(r):
            return (
                (r.get("order_id") or ""),
                (r.get("platform") or ""),
                (r.get("shop") or ""),
                (r.get("logistic") or ""),
                (r.get("sku") or "")
            )
        rows = sorted(rows, key=_key)
        rows = _annotate_order_spans(rows)

        counts: dict[str, int] = {}
        for r in rows:
            oid = (r.get("order_id") or "").strip()
            counts[oid] = counts.get(oid, 0) + 1

        for r in rows:
            oid = (r.get("order_id") or "").strip()
            r["order_rowspan"] = counts.get(oid, 1) if r.get("show_order_id") else 0
            r["order_id_display"] = oid if r.get("show_order_id") else ""
        return rows

    # -----------------
    # สร้างเซ็ต Order พร้อมรับทั้งออเดอร์ / สินค้าน้อยทั้งออเดอร์
    # -----------------
    def _orders_ready_set(rows: list[dict]) -> set[str]:
        by_oid: dict[str, list[dict]] = {}
        for r in rows:
            oid = (r.get("order_id") or "").strip()
            if not oid:
                continue
            by_oid.setdefault(oid, []).append(r)

        ready = set()
        for oid, items in by_oid.items():
            if not items:
                continue
            all_ready = True
            for it in items:
                status = (it.get("allocation_status") or "").upper()
                accepted = bool(it.get("accepted", False))
                packed = (status == "PACKED") or bool(it.get("packed", False))
                if not (status == "READY_ACCEPT" and not accepted and not packed):
                    all_ready = False
                    break
            if all_ready:
                ready.add(oid)
        return ready

    def _orders_lowstock_order_set(rows: list[dict]) -> set[str]:
        by_oid: dict[str, list[dict]] = {}
        for r in rows:
            oid = (r.get("order_id") or "").strip()
            if not oid:
                continue
            by_oid.setdefault(oid, []).append(r)

        result = set()
        for oid, items in by_oid.items():
            if not items:
                continue
            all_sendable = True
            has_low = False
            for it in items:
                status = (it.get("allocation_status") or "").upper()
                accepted = bool(it.get("accepted", False))
                packed = (status == "PACKED") or bool(it.get("packed", False))
                if packed or accepted:
                    all_sendable = False
                    break
                if status not in ("READY_ACCEPT", "LOW_STOCK"):
                    all_sendable = False
                    break
                if status == "LOW_STOCK":
                    has_low = True
            if all_sendable and has_low:
                result.add(oid)
        return result

    def _orders_accepted_set(rows: list[dict]) -> set[str]:
        """นับ orders ที่มีอย่างน้อย 1 item ที่ status = ACCEPTED"""
        result = set()
        for r in rows:
            oid = (r.get("order_id") or "").strip()
            if not oid:
                continue
            status = (r.get("allocation_status") or "").upper()
            if status == "ACCEPTED":
                result.add(oid)
        return result

    def _orders_shortage_set(rows: list[dict]) -> set[str]:
        """นับ orders ที่มีอย่างน้อย 1 item ที่ status = SHORTAGE"""
        result = set()
        for r in rows:
            oid = (r.get("order_id") or "").strip()
            if not oid:
                continue
            status = (r.get("allocation_status") or "").upper()
            if status == "SHORTAGE":
                result.add(oid)
        return result

    # ===========================================================
    # Packed helpers — จาก "เปิดใบขายครบตามจำนวนแล้ว"
    # ===========================================================
    def _is_line_opened_full(r: dict) -> bool:
        text_pool = [
            str(r.get("sale_status") or ""),
            str(r.get("sale_text") or ""),
            str(r.get("sales_status") or ""),
            str(r.get("sales_note") or ""),
        ]
        norm = " ".join(s.strip() for s in text_pool if s).lower()
        flag = bool(r.get("sale_open_full") or r.get("opened_full") or r.get("is_opened_full"))
        return flag or ("เปิดใบขายครบตามจำนวนแล้ว" in norm) or ("opened_full" in norm)

    def _orders_packed_set(rows: list[dict]) -> set[str]:
        by_oid: dict[str, list[dict]] = {}
        for r in rows:
            oid = (r.get("order_id") or "").strip()
            if not oid:
                continue
            by_oid.setdefault(oid, []).append(r)
        packed: set[str] = set()
        for oid, items in by_oid.items():
            if items and all(_is_line_opened_full(it) for it in items):
                packed.add(oid)
        return packed

    # ---------------------------------------------------------
    # ฟังก์ชัน DB raw (ใช้เพราะคอลัมน์ถูกเพิ่มแบบ ALTER TABLE)
    # ---------------------------------------------------------
    def _detect_already_printed(oids: list[str], kind: str) -> set[str]:
        if not oids:
            return set()
        tbl = _ol_table_name()
        col = "printed_warehouse" if kind == "warehouse" else "printed_picking"
        sql = text(f"SELECT DISTINCT order_id FROM {tbl} WHERE order_id IN :oids AND {col}=1")
        sql = sql.bindparams(bindparam("oids", expanding=True))
        rows = db.session.execute(sql, {"oids": oids}).scalars().all()
        return set(r for r in rows if r)

    def _mark_printed(oids: list[str], kind: str, user_id: int | None, when_iso: str):
        if not oids:
            return
        tbl = _ol_table_name()
        if kind == "warehouse":
            col_flag = "printed_warehouse"
            col_cnt  = "printed_warehouse_count"
            col_at   = "printed_warehouse_at"
            col_by   = "printed_warehouse_by_user_id"
        else:
            col_flag = "printed_picking"
            col_cnt  = "printed_picking_count"
            col_at   = "printed_picking_at"
            col_by   = "printed_picking_by_user_id"

        sql = text(
            f"""
            UPDATE {tbl}
               SET {col_flag}=1,
                   {col_cnt}=COALESCE({col_cnt},0)+1,
                   {col_by}=:uid,
                   {col_at}=:ts
             WHERE order_id IN :oids
            """
        ).bindparams(bindparam("oids", expanding=True))
        db.session.execute(sql, {"uid": user_id, "ts": when_iso, "oids": oids})
        db.session.commit()

    # --------------------------
    # Print count helpers (ใหม่)
    # --------------------------
    def _get_print_counts_local(oids: list[str], kind: str) -> dict[str, int]:
        """คืน dict: {order_id: count} ใช้ get_print_counts ถ้ามี ไม่งั้นอ่านจาก *_count"""
        try:
            if "get_print_counts" in globals() and callable(globals()["get_print_counts"]):
                res = get_print_counts(oids, kind) or {}
                if isinstance(res, dict):
                    return {str(k): int(v or 0) for k, v in res.items()}
        except Exception:
            pass
        if not oids:
            return {}
        tbl = _ol_table_name()
        col = "printed_warehouse_count" if kind == "warehouse" else "printed_picking_count"
        sql = text(f"SELECT order_id, COALESCE(MAX({col}),0) AS c FROM {tbl} WHERE order_id IN :oids GROUP BY order_id")
        sql = sql.bindparams(bindparam("oids", expanding=True))
        rows_sql = db.session.execute(sql, {"oids": oids}).all()
        return {str(r[0]): int(r[1] or 0) for r in rows_sql if r and r[0]}

    def _inject_print_counts_to_rows(rows: list[dict], kind: str):
        """ฝัง printed_*_count ลงในแต่ละแถว (ใช้กับ Warehouse report)"""
        oids = sorted({(r.get("order_id") or "").strip() for r in rows if r.get("order_id")})
        counts = _get_print_counts_local(oids, kind)
        for r in rows:
            oid = (r.get("order_id") or "").strip()
            c = int(counts.get(oid, 0))
            r["printed_count"] = c
            if kind == "warehouse":
                r["printed_warehouse_count"] = c
            else:
                r["printed_picking_count"] = c

    # -------------
    # Routes: Auth & Users
    # -------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            u = User.query.filter_by(username=username, active=True).first()
            if u and check_password_hash(u.password_hash, password):
                session["uid"] = u.id
                flash("เข้าสู่ระบบสำเร็จ", "success")
                return redirect(request.args.get("next") or url_for("dashboard"))
            flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("ออกจากระบบแล้ว", "info")
        return redirect(url_for("login"))

    @app.route("/admin/users", methods=["GET", "POST"])
    @login_required
    def admin_users():
        cu = current_user()
        if cu.role != "admin":
            flash("ต้องเป็นผู้ดูแลระบบเท่านั้น", "danger")
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            action = request.form.get("action")
            if action == "create":
                username = request.form.get("username").strip()
                password = request.form.get("password")
                role = request.form.get("role", "user")
                if not username or not password:
                    flash("กรุณากรอกชื่อผู้ใช้/รหัสผ่าน", "danger")
                elif User.query.filter_by(username=username).first():
                    flash("มีชื่อผู้ใช้นี้อยู่แล้ว", "warning")
                else:
                    u = User(
                        username=username,
                        password_hash=generate_password_hash(password),
                        role=role,
                        active=True
                    )
                    db.session.add(u)
                    db.session.commit()
                    flash(f"สร้างผู้ใช้ {username} แล้ว", "success")
            elif action == "delete":
                uid = int(request.form.get("uid"))
                if uid == cu.id:
                    flash("ลบตัวเองไม่ได้", "warning")
                else:
                    User.query.filter_by(id=uid).delete()
                    db.session.commit()
                    flash("ลบผู้ใช้แล้ว", "success")
        users = User.query.order_by(User.created_at.desc()).all() if hasattr(User, "created_at") else User.query.all()
        return render_template("users.html", users=users)

    # -------------
    # Dashboard
    # -------------
    @app.route("/")
    @login_required
    def dashboard():
        platform = normalize_platform(request.args.get("platform"))
        shop_id = request.args.get("shop_id")
        import_date_str = request.args.get("import_date")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        status = request.args.get("status")
        include_dispatched = request.args.get("include_dispatched", "0") == "1"  # NEW: ฟิลเตอร์แสดงส่งแล้ว

        shops = Shop.query.order_by(Shop.name.asc()).all()

        filters = {
            "platform": platform if platform else None,
            "shop_id": int(shop_id) if shop_id else None,
            "import_date": parse_date_any(import_date_str),
            "date_from": datetime.combine(parse_date_any(date_from), datetime.min.time(), tzinfo=TH_TZ) if date_from else None,
            "date_to": datetime.combine(parse_date_any(date_to) + timedelta(days=1), datetime.min.time(), tzinfo=TH_TZ) if date_to else None,
        }

        rows, _kpis_from_allocation = compute_allocation(db.session, filters)

        for r in rows:
            if "stock_qty" not in r:
                sku = (r.get("sku") or "").strip()
                stock_qty = 0
                if sku:
                    prod = Product.query.filter_by(sku=sku).first()
                    if prod and hasattr(prod, "stock_qty"):
                        try:
                            stock_qty = int(prod.stock_qty or 0)
                        except Exception:
                            stock_qty = 0
                    else:
                        st = Stock.query.filter_by(sku=sku).first()
                        stock_qty = int(st.qty) if st and st.qty is not None else 0
                r["stock_qty"] = stock_qty
            r["accepted"] = bool(r.get("accepted", False))
            r["sales_status"] = r.get("sales_status", None)
            r["logistic"] = r.get("logistic") or r.get("logistic_type") or "Unknown"

        totals = _build_allqty_map(rows)
        for r in rows:
            r["allqty"] = int(totals.get((r.get("sku") or "").strip(), r.get("qty", 0)) or 0)
        rows = [_recompute_allocation_row(r) for r in rows]

        packed_oids = _orders_packed_set(rows)

        # NEW: หา Orders ที่ส่งมอบแล้ว (handover_confirmed = True)
        dispatched_oids = set()
        # ✅ หา Batch ที่เสร็จสิ้นแล้ว (Progress 100%) เพื่อ disable actions
        completed_batch_oids = set()
        # Cache batch progress เพื่อไม่ให้คำนวณซ้ำ
        batch_progress_cache = {}

        for r in rows:
            batch_id = r.get("batch_id")
            if batch_id:
                batch = db.session.get(Batch, batch_id)
                if batch and batch.handover_confirmed:
                    dispatched_oids.add((r.get("order_id") or "").strip())
                # ✅ เช็ค Progress ของ Batch
                elif batch:
                    # ใช้ cache เพื่อไม่ต้องคำนวณซ้ำ
                    if batch_id not in batch_progress_cache:
                        batch_progress_cache[batch_id] = calculate_batch_progress(batch_id)

                    progress_data = batch_progress_cache[batch_id]
                    if progress_data["progress_percent"] >= 100:
                        completed_batch_oids.add((r.get("order_id") or "").strip())

        for r in rows:
            oid = (r.get("order_id") or "").strip()
            if oid in dispatched_oids:
                r["allocation_status"] = "DISPATCHED"
                r["dispatched"] = True
                r["actions_disabled"] = True
            elif oid in packed_oids:
                r["allocation_status"] = "PACKED"
                r["packed"] = True
                r["actions_disabled"] = True
            elif oid in completed_batch_oids:
                # ✅ Batch เสร็จสิ้นแล้ว - ไม่ควรให้กดรับ/ยกเลิกได้อีก
                r["actions_disabled"] = True
                r["batch_completed"] = True
            else:
                r["actions_disabled"] = False

        orders_ready = _orders_ready_set(rows)
        orders_low_order = _orders_lowstock_order_set(rows)
        orders_accepted = _orders_accepted_set(rows)
        orders_shortage = _orders_shortage_set(rows)
        status_norm = (status or "").strip().upper()

        # เก็บ all_rows ไว้สำหรับคำนวณ KPI ก่อนกรอง
        all_rows = rows.copy()

        # กรองตามสถานะที่เลือก
        if status_norm in {"PACKED"}:
            rows = [r for r in rows if (r.get("order_id") or "").strip() in packed_oids]
        elif status_norm == "DISPATCHED":
            # เลือกดู DISPATCHED โดยเฉพาะ → แสดงเฉพาะ dispatched
            rows = [r for r in rows if (r.get("order_id") or "").strip() in dispatched_oids]
        else:
            # กรอง packed ออกก่อน
            rows = [r for r in rows if (r.get("order_id") or "").strip() not in packed_oids]

            # ถ้าไม่เลือก include_dispatched → กรอง dispatched ออกด้วย
            if not include_dispatched:
                rows = [r for r in rows if (r.get("order_id") or "").strip() not in dispatched_oids]

            # กรองตามสถานะอื่นๆ
            if status_norm == "ORDER_READY":
                rows = [r for r in rows if (r.get("order_id") or "").strip() in orders_ready]
            elif status_norm in {"ORDER_LOW_STOCK", "ORDER_LOW"}:
                rows = [r for r in rows if (r.get("order_id") or "").strip() in orders_low_order]
            elif status_norm:
                rows = [r for r in rows if (r.get("allocation_status") or "").strip().upper() == status_norm]

        def _sort_key(r):
            return ((r.get("order_id") or ""), (r.get("platform") or ""), (r.get("shop") or ""), (r.get("sku") or ""))
        rows = sorted(rows, key=_sort_key)

        # KPI คำนวณจาก all_rows (ไม่นับ dispatched ถ้าไม่เลือก include_dispatched)
        kpi_rows = [r for r in all_rows if (r.get("order_id") or "").strip() not in dispatched_oids] if not include_dispatched else all_rows
        
        kpis = {
            "ready":     sum(1 for r in kpi_rows if r["allocation_status"] == "READY_ACCEPT"),
            "accepted":  sum(1 for r in kpi_rows if r["allocation_status"] == "ACCEPTED"),
            "low":       sum(1 for r in kpi_rows if r["allocation_status"] == "LOW_STOCK"),
            "nostock":   sum(1 for r in kpi_rows if r["allocation_status"] == "SHORTAGE"),
            "notenough": sum(1 for r in kpi_rows if r["allocation_status"] == "NOT_ENOUGH"),
            "packed":    len([oid for oid in packed_oids if oid not in dispatched_oids]),
            "dispatched": len(dispatched_oids),
            "total_items": len(kpi_rows),
            "total_qty":   sum(int(r.get("qty", 0) or 0) for r in kpi_rows),
            "orders_unique": len({(r.get("order_id") or "").strip() for r in kpi_rows if r.get("order_id")}),
            "orders_ready": len([oid for oid in orders_ready if oid not in dispatched_oids]),
            "orders_low":   len([oid for oid in orders_low_order if oid not in dispatched_oids]),
            "orders_accepted": len([oid for oid in orders_accepted if oid not in dispatched_oids]),
            "orders_shortage": len([oid for oid in orders_shortage if oid not in dispatched_oids]),
        }

        return render_template(
            "dashboard.html",
            rows=rows,
            shops=shops,
            platform_sel=platform,
            shop_sel=shop_id,
            import_date_sel=import_date_str,
            status_sel=status,
            date_from_sel=date_from,
            date_to_sel=date_to,
            include_dispatched=include_dispatched,
            kpis=kpis,
            packed_oids=packed_oids,
            dispatched_oids=dispatched_oids,
        )

    # -----------------------
    # Import endpoints
    # -----------------------
    @app.route("/import/orders", methods=["GET", "POST"])
    @login_required
    def import_orders_view():
        if request.method == "POST":
            platform = request.form.get("platform")
            shop_name = request.form.get("shop_name")
            f = request.files.get("file")
            if not platform or not shop_name or not f:
                flash("กรุณาเลือกแพลตฟอร์ม / ชื่อร้าน และเลือกไฟล์", "danger")
                return redirect(url_for("import_orders_view"))
            try:
                df = pd.read_excel(f)
                imported, updated = import_orders(
                    df, platform=platform, shop_name=shop_name, import_date=now_thai().date()
                )

                # NFR-03: Audit log for import action
                log_audit("import_orders", {
                    "platform": platform,
                    "shop_name": shop_name,
                    "filename": f.filename,
                    "imported": imported,
                    "updated": updated
                }, order_count=imported)

                flash(f"นำเข้าออเดอร์สำเร็จ: เพิ่ม {imported} อัปเดต {updated}", "success")
                return redirect(url_for("import_orders_view"))
            except Exception as e:
                flash(f"เกิดข้อผิดพลาดในการนำเข้าออเดอร์: {e}", "danger")
                return redirect(url_for("import_orders_view"))
        shops = Shop.query.order_by(Shop.name.asc()).all()
        # Query import logs
        logs = AuditLog.query.filter_by(action="import_orders").order_by(AuditLog.timestamp.desc()).limit(50).all()
        return render_template("import_orders.html", shops=shops, logs=logs)

    @app.route("/import/products", methods=["GET", "POST"])
    @login_required
    def import_products_view():
        if request.method == "POST":
            f = request.files.get("file")
            if not f:
                flash("กรุณาเลือกไฟล์สินค้า", "danger")
                return redirect(url_for("import_products_view"))
            try:
                df = pd.read_excel(f)
                cnt = import_products(df)

                # Create audit log for products import
                log_audit("import_products", {
                    "count": cnt,
                    "filename": f.filename
                })

                flash(f"นำเข้าสินค้าสำเร็จ {cnt} รายการ", "success")
                return redirect(url_for("import_products_view"))
            except Exception as e:
                flash(f"เกิดข้อผิดพลาดในการนำเข้าสินค้า: {e}", "danger")
                return redirect(url_for("import_products_view"))

        # Query import logs
        logs = AuditLog.query.filter_by(action="import_products").order_by(AuditLog.timestamp.desc()).limit(50).all()
        return render_template("import_products.html", logs=logs)

    @app.route("/import/stock", methods=["GET", "POST"])
    @login_required
    def import_stock_view():
        if request.method == "POST":
            f = request.files.get("file")
            if not f:
                flash("กรุณาเลือกไฟล์สต็อก", "danger")
                return redirect(url_for("import_stock_view"))
            try:
                df = pd.read_excel(f)
                cnt = import_stock(df)

                # Create audit log for stock import
                log_audit("import_stock", {
                    "count": cnt,
                    "filename": f.filename
                })

                flash(f"นำเข้าสต็อกสำเร็จ {cnt} รายการ", "success")
                return redirect(url_for("import_stock_view"))
            except Exception as e:
                flash(f"เกิดข้อผิดพลาดในการนำเข้าสต็อก: {e}", "danger")
                return redirect(url_for("import_stock_view"))

        # Query import logs
        logs = AuditLog.query.filter_by(action="import_stock").order_by(AuditLog.timestamp.desc()).limit(50).all()
        return render_template("import_stock.html", logs=logs)

    @app.route("/import/sales", methods=["GET", "POST"])
    @login_required
    def import_sales_view():
        if request.method == "POST":
            f = request.files.get("file")
            if not f:
                flash("กรุณาเลือกไฟล์สั่งขาย", "danger")
                return redirect(url_for("import_sales_view"))
            try:
                df = pd.read_excel(f)
                cnt = import_sales(df)

                # Create audit log for sales import
                log_audit("import_sales", {
                    "count": cnt,
                    "filename": f.filename
                })

                flash(f"นำเข้าไฟล์สั่งขายสำเร็จ {cnt} รายการ", "success")
                return redirect(url_for("import_sales_view"))
            except Exception as e:
                flash(f"เกิดข้อผิดพลาดในการนำเข้าไฟล์สั่งขาย: {e}", "danger")
                return redirect(url_for("import_sales_view"))

        # Query import logs
        logs = AuditLog.query.filter_by(action="import_sales").order_by(AuditLog.timestamp.desc()).limit(50).all()
        return render_template("import_sales.html", logs=logs)

    # -----------------------
    # Stock Ledger & Analytics (Option 2: Banking-style)
    # -----------------------
    @app.route("/stock/<sku>/ledger")
    @login_required
    def stock_ledger(sku):
        """
        Display transaction history for a specific SKU (Banking-style ledger)
        Similar to bank statement showing all debits/credits
        """
        # Get stock info
        stock = Stock.query.filter_by(sku=sku).first()
        if not stock:
            flash(f"ไม่พบข้อมูลสต็อก SKU: {sku}", "warning")
            return redirect(url_for("dashboard"))

        # Get product info
        product = Product.query.filter_by(sku=sku).first()

        # Get all transactions for this SKU (newest first)
        transactions = StockTransaction.query.filter_by(sku=sku).order_by(
            StockTransaction.created_at.desc()
        ).all()

        # Calculate summary statistics
        total_received = db.session.query(func.sum(StockTransaction.quantity)).filter(
            StockTransaction.sku == sku,
            StockTransaction.transaction_type == 'RECEIVE'
        ).scalar() or 0

        total_reserved = stock.reserved_qty or 0
        total_available = stock.available_qty

        # Get active batches using this SKU
        active_batches = db.session.query(Batch.batch_id).join(
            OrderLine, OrderLine.batch_id == Batch.batch_id
        ).filter(
            OrderLine.sku == sku,
            Batch.handover_confirmed == False
        ).distinct().all()

        return render_template(
            "stock_ledger.html",
            sku=sku,
            stock=stock,
            product=product,
            transactions=transactions,
            total_received=total_received,
            total_reserved=total_reserved,
            total_available=total_available,
            active_batches=[b[0] for b in active_batches]
        )

    # -----------------------
    # Batch Management Routes (FR-04 to FR-09)
    # -----------------------
    @app.route("/batch/list")
    @login_required
    def batch_list():
        """Display all batches with summary"""
        # รับ filters จาก query parameters
        platform_filter = request.args.get("platform")
        handover_status = request.args.get("handover_status")  # all, pending, confirmed
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")

        # Query batches
        query = Batch.query

        # กรองตาม platform
        if platform_filter:
            query = query.filter_by(platform=normalize_platform(platform_filter))

        # กรองตามสถานะการส่งมอบ
        if handover_status == "confirmed":
            query = query.filter_by(handover_confirmed=True)
        elif handover_status == "pending":
            query = query.filter_by(handover_confirmed=False)
        # ถ้าเป็น "all" หรือไม่ระบุ → แสดงทั้งหมด

        # กรองตามวันที่
        if date_from:
            query = query.filter(Batch.batch_date >= parse_date_any(date_from))
        if date_to:
            query = query.filter(Batch.batch_date <= parse_date_any(date_to))

        # เรียงลำดับ: ยังไม่ส่งมอบก่อน (handover_confirmed=False), แล้วเรียงตามวันที่ล่าสุด
        batches = query.order_by(
            Batch.handover_confirmed.asc(),  # False (ยังไม่ส่ง) มาก่อน True (ส่งแล้ว)
            Batch.created_at.desc()
        ).all()

        # Count pending orders by platform
        pending_by_platform = db.session.query(
            OrderLine.platform,
            func.count(func.distinct(OrderLine.order_id))
        ).filter_by(batch_status="pending_batch").group_by(OrderLine.platform).all()

        pending_counts = {platform: count for platform, count in pending_by_platform}

        # คำนวณ Progress ของแต่ละ Batch (สำหรับแสดงใน UI)
        # ✅ Phase 2.1: ใช้ Quantity-based calculation แทน Order-based
        batch_progress = {}
        batch_readiness = {}  # ✨ NEW: SKU-based readiness check
        batch_carriers = {}  # ✨ NEW: Real-time carrier counts

        for batch in batches:
            progress_data = calculate_batch_progress(batch.batch_id)
            readiness_data = is_batch_ready_for_handover(batch.batch_id)

            # สร้าง structure ให้เข้ากับ UI เดิม
            batch_progress[batch.batch_id] = {
                "total": progress_data["total_orders"],  # จำนวน orders (สำหรับ backward compatibility)
                "dispatched": progress_data["completed_orders"],  # จำนวน orders ที่เสร็จ
                "pending": progress_data["total_orders"] - progress_data["completed_orders"],
                "percent": progress_data["progress_percent"],  # ✅ ใช้ Quantity-based %
                # เพิ่มข้อมูล Quantity สำหรับใช้งานในอนาคต
                "total_qty": progress_data["total_qty"],
                "picked_qty": progress_data["picked_qty"],
                "shortage_qty": progress_data["shortage_qty"],
                "completed_qty": progress_data["completed_qty"]
            }

            # ✨ NEW: เพิ่ม SKU-based readiness
            batch_readiness[batch.batch_id] = readiness_data["ready"]

            # ✨ NEW: คำนวณ Carrier Counts แบบ Real-time
            from collections import defaultdict
            carrier_counts = defaultdict(int)
            orders = OrderLine.query.filter_by(batch_id=batch.batch_id).all()
            counted_orders = set()

            for order in orders:
                if order.order_id not in counted_orders:
                    counted_orders.add(order.order_id)
                    carrier = order.carrier or "Other"
                    carrier_counts[carrier] += 1

            batch_carriers[batch.batch_id] = {
                "SPX": carrier_counts.get("SPX", 0),
                "Flash": carrier_counts.get("Flash", 0),
                "LEX": carrier_counts.get("LEX", 0),
                "J&T": carrier_counts.get("J&T", 0),
                "Other": sum(v for k, v in carrier_counts.items() if k not in ["SPX", "Flash", "LEX", "J&T"])
            }

        return render_template(
            "batch_list.html",
            batches=batches,
            pending_counts=pending_counts,
            batch_progress=batch_progress,
            batch_readiness=batch_readiness,  # ✨ NEW: ส่ง readiness status
            batch_carriers=batch_carriers,  # ✨ NEW: ส่ง real-time carrier counts
            platform_filter=platform_filter,
            handover_status=handover_status or "all",
            date_from=date_from,
            date_to=date_to
        )

    @app.route("/batch/create", methods=["GET", "POST"])
    @login_required
    def batch_create():
        """
        FR-04, FR-05: Create new batch from pending orders
        UX-02: Show confirmation popup with summary
        """
        if request.method == "GET":
            # Show form to select platform and run
            platform = request.args.get("platform")

            if platform:
                # ✅ Phase 2: Preview with SLA-based allocation simulation
                platform_std = normalize_platform(platform)
                pending = OrderLine.query.filter_by(
                    platform=platform_std,
                    batch_status="pending_batch"
                ).all()

                if pending:
                    # Calculate SLA for preview (don't save yet)
                    for order in pending:
                        if not order.sla_date and order.order_time:
                            order.sla_date = compute_due_date(platform_std, order.order_time)

                    # Sort by SLA
                    pending = sorted(
                        pending,
                        key=lambda o: (o.sla_date is None, o.sla_date, o.order_time or datetime.min)
                    )

                    # Simulate stock allocation
                    stock_tracker = {}
                    for sku in set(o.sku for o in pending):
                        stock = Stock.query.filter_by(sku=sku).first()
                        stock_tracker[sku] = stock.available_qty if stock else 0

                    batch_orders = []
                    waiting_orders = []

                    for order in pending:
                        available = stock_tracker.get(order.sku, 0)
                        if available >= order.qty:
                            batch_orders.append(order)
                            stock_tracker[order.sku] = available - order.qty
                        else:
                            waiting_orders.append(order)

                    # Create preview summary
                    if batch_orders:
                        preview_summary = compute_batch_summary(batch_orders)
                        # ✅ Phase 2: Add allocation info
                        preview_summary["allocation"] = {
                            "batch_orders": len(batch_orders),
                            "waiting_orders": len(waiting_orders),
                            "batch_sla": min([o.sla_date for o in batch_orders if o.sla_date], default=None)
                        }
                    else:
                        preview_summary = None

                    # ✅ Phase 2: Pass waiting_orders to template
                    # ✅ Pass batch_orders for detailed order list display
                    return render_template(
                        "batch_create.html",
                        platform=platform_std,
                        preview=preview_summary,
                        waiting_orders=waiting_orders,
                        batch_orders=batch_orders
                    )
                else:
                    preview_summary = None
                    return render_template("batch_create.html", platform=platform_std, preview=preview_summary)
            else:
                # Initial form
                platforms = ["Shopee", "Lazada", "TikTok"]
                return render_template("batch_create.html", platforms=platforms, platform=None, preview=None)

        elif request.method == "POST":
            # Create batch
            platform = request.form.get("platform")

            try:
                # ✅ Security: Use retry wrapper with auto-generated run_no
                # This prevents race conditions when multiple users create batches
                batch = create_batch_with_retry(platform)
                flash(f"สร้าง Batch {batch.batch_id} สำเร็จ! รวม {batch.total_orders} ออเดอร์", "success")
                return redirect(url_for("batch_detail", batch_id=batch.batch_id))
            except ValueError as e:
                flash(str(e), "danger")
                return redirect(url_for("batch_create", platform=platform))
            except Exception as e:
                flash(f"เกิดข้อผิดพลาด: {e}", "danger")
                return redirect(url_for("batch_create"))

    @app.route("/batch/<batch_id>")
    @login_required
    def batch_detail(batch_id):
        """FR-09: Display batch details and orders"""
        batch = Batch.query.get_or_404(batch_id)

        # Get all orders in this batch
        orders = OrderLine.query.filter_by(batch_id=batch_id).all()

        # คำนวณ Carrier Summary และ Shop Summary แบบ Real-time
        # เพื่อให้แน่ใจว่าข้อมูลถูกต้องทั้ง Parent และ Sub-Batch
        from collections import defaultdict
        carrier_counts = defaultdict(int)
        shop_counts = defaultdict(int)

        # ใช้ set เพื่อนับ order_id ที่ unique (1 order อาจมีหลาย SKU)
        counted_orders = set()

        for order in orders:
            if order.order_id not in counted_orders:
                counted_orders.add(order.order_id)

                # นับ carrier
                carrier = order.carrier or "Other"
                carrier_counts[carrier] += 1

                # นับ shop (ต้อง query Shop model เพื่อเอา name)
                shop = db.session.get(Shop, order.shop_id) if order.shop_id else None
                shop_name = shop.name if shop else "Unknown"
                shop_counts[shop_name] += 1

        # สร้าง carrier_summary dict
        carrier_summary = {
            "SPX": carrier_counts.get("SPX", 0),
            "Flash": carrier_counts.get("Flash", 0),
            "LEX": carrier_counts.get("LEX", 0),
            "J&T": carrier_counts.get("J&T", 0),
            "Other": sum(v for k, v in carrier_counts.items() if k not in ["SPX", "Flash", "LEX", "J&T"])
        }

        # สร้าง shop_summary dict
        shop_summary = dict(shop_counts)

        # คำนวณ SKU Progress (สำหรับติดตามความคืบหน้าการหยิบสินค้า)
        from collections import defaultdict
        sku_progress = {}

        for order in orders:
            if order.sku not in sku_progress:
                product = Product.query.filter_by(sku=order.sku).first()
                stock = Stock.query.filter_by(sku=order.sku).first()
                sku_progress[order.sku] = {
                    "sku": order.sku,
                    "brand": product.brand if product else "",
                    "model": product.model if product else "",
                    "item_name": order.item_name,
                    "stock_qty": stock.qty if stock else 0,
                    "reserved_qty": stock.reserved_qty if stock else 0,  # ✅ NEW: จำนวน Stock ที่จองไว้
                    "available_qty": stock.available_qty if stock else 0,  # ✅ NEW: Stock ที่ใช้ได้จริง (Total - Reserved)
                    "total_need": 0,
                    "total_picked": 0,
                    "total_shortage": 0,
                    "earliest_sla": None  # ✅ NEW: Track earliest SLA for this SKU
                }

            sku_progress[order.sku]["total_need"] += order.qty
            sku_progress[order.sku]["total_picked"] += (order.picked_qty or 0)

            # ✅ Phase 2.2: ใช้ shortage_qty field แทนการคำนวณ
            # shortage_qty เป็น field จริงใน DB ที่อัปเดตเมื่อมีการ mark/resolve shortage
            sku_progress[order.sku]["total_shortage"] += (order.shortage_qty or 0)

            # ✅ NEW: Track earliest SLA (order_time) for this SKU
            current_sla = sku_progress[order.sku]["earliest_sla"]
            if order.order_time:
                if current_sla is None or order.order_time < current_sla:
                    sku_progress[order.sku]["earliest_sla"] = order.order_time

        # ✅ FIX: เช็ค Shortage จาก ShortageQueue Records เพื่อความแม่นยำ
        # เพราะ shortage_qty field อาจไม่ได้อัปเดตทันที
        shortage_from_queue = {}
        for order in orders:
            # ดึง Shortage Records ที่ยังไม่ได้ resolve
            pending_shortages = ShortageQueue.query.filter(
                ShortageQueue.order_line_id == order.id,
                ShortageQueue.sku == order.sku,
                ShortageQueue.status.in_(['pending', 'waiting_stock', 'ready_to_pick'])
            ).all()

            if pending_shortages:
                sku = order.sku
                if sku not in shortage_from_queue:
                    shortage_from_queue[sku] = 0
                for shortage in pending_shortages:
                    shortage_from_queue[sku] += (shortage.qty_shortage or 0)

        # คำนวณสถานะและเรียงลำดับ
        sku_list = []
        for sku, data in sku_progress.items():
            # ✅ "ต้องการอีก" = ต้องการ - หยิบแล้ว (ไม่นับ shortage)
            # เพราะ shortage คือสิ่งที่ขาดและจัดการไปแล้ว ไม่ใช่สิ่งที่ต้องหยิบ
            remaining_to_pick = data["total_need"] - data["total_picked"]
            data["remaining"] = max(0, remaining_to_pick)  # ป้องกันค่าติดลบ

            # ✅ FIX: "ขาด" = ใช้ค่าจาก ShortageQueue แทน shortage_qty field
            actual_shortage = shortage_from_queue.get(sku, 0) or data["total_shortage"]
            data["actual_shortage"] = actual_shortage

            # กำหนดสถานะ (ให้ Shortage มีลำดับความสำคัญสูงสุด)
            if actual_shortage > 0:
                # ✅ มี Shortage → แสดงสถานะ "ขาด" ทันที (ไม่ว่าจะหยิบแล้วหรือยัง)
                data["status"] = "shortage"
                data["status_badge"] = "danger"
                data["status_text"] = f"ขาด {actual_shortage} ชิ้น"
            elif data["total_picked"] >= data["total_need"]:
                data["status"] = "completed"
                data["status_badge"] = "success"
                data["status_text"] = "เสร็จสิ้น"
            elif data["total_picked"] > 0:
                data["status"] = "picking"
                data["status_badge"] = "warning"
                data["status_text"] = "กำลังหยิบ"
            else:
                data["status"] = "pending"
                data["status_badge"] = "secondary"
                data["status_text"] = "รอหยิบ"

            # ✅ Format earliest_sla for display
            if data["earliest_sla"]:
                data["earliest_sla"] = format_sla_thai(data["earliest_sla"])

            sku_list.append(data)

        # เรียงลำดับ: Pending → Picking → Shortage → Completed
        status_order = {"pending": 0, "picking": 1, "shortage": 2, "completed": 3}
        sku_list.sort(key=lambda x: status_order.get(x["status"], 0))

        # ✅ Phase 2.5: ดึงข้อมูล Shortage Queue เพื่อแสดงเหตุผลและรายละเอียด
        # Query shortage records สำหรับ batch นี้
        shortage_records = ShortageQueue.query.filter_by(
            original_batch_id=batch_id
        ).all()

        # สร้าง mapping: sku -> shortage details
        shortage_details = {}
        for shortage in shortage_records:
            if shortage.sku not in shortage_details:
                shortage_details[shortage.sku] = []

            shortage_details[shortage.sku].append({
                "id": shortage.id,
                "order_id": shortage.order_id,
                "qty_shortage": shortage.qty_shortage,
                "reason": shortage.shortage_reason or "ไม่ระบุ",
                "status": shortage.status,
                "created_at": shortage.created_at.strftime("%Y-%m-%d %H:%M") if shortage.created_at else "",
                "created_by": shortage.created_by_username or "",
                "resolved_at": shortage.resolved_at.strftime("%Y-%m-%d %H:%M") if shortage.resolved_at else "",
                "action_taken": shortage.action_taken or ""
            })

        # ✅ คำนวณ Overall Progress ด้วย calculate_batch_progress() เพื่อให้ตรงกับหน้า Batch List
        batch_progress_data = calculate_batch_progress(batch_id)

        # ✨ NEW: ดึงข้อมูล Batch Family (Parent + Children) สำหรับ Parent-Child Batch System
        batch_family_data = None
        try:
            # หา Parent Batch
            if batch.parent_batch_id:
                parent_batch = db.session.get(Batch, batch.parent_batch_id)
            else:
                parent_batch = batch

            # ดึง Children ทั้งหมด
            children = Batch.query.filter_by(
                parent_batch_id=parent_batch.batch_id
            ).order_by(Batch.sub_batch_number).all()

            # คำนวณ Progress แต่ละ Batch
            def get_batch_info(b):
                progress = calculate_batch_progress(b.batch_id)
                return {
                    "batch_id": b.batch_id,
                    "sub_batch_number": b.sub_batch_number,
                    "batch_type": b.batch_type,
                    "total_orders": b.total_orders,
                    "progress_percent": progress["progress_percent"],
                    "total_qty": progress["total_qty"],
                    "completed_qty": progress["completed_qty"],
                    "picked_qty": progress["picked_qty"],
                    "handover_code": b.handover_code,
                    "handover_confirmed": b.handover_confirmed,
                    "shortage_reason": b.shortage_reason,
                    "created_at": to_thai_be(b.created_at)
                }

            batch_family_data = {
                "parent": get_batch_info(parent_batch),
                "children": [get_batch_info(child) for child in children],
                "total_children": len(children),
                "can_split_more": len(children) < 5
            }
        except Exception as e:
            print(f"Error loading batch family: {e}")
            # ถ้าเกิด error ให้ใช้ None (UI จะไม่แสดง Parent-Child section)
            batch_family_data = None

        # ✨ NEW: ตรวจสอบว่า Batch พร้อมสร้าง Handover Code หรือไม่ (SKU-based)
        batch_readiness = is_batch_ready_for_handover(batch_id)

        # ✅ NEW: ตรวจสอบว่าสามารถแยก Batch ได้หรือไม่
        # เงื่อนไข:
        # 1. Batch มีสถานะ "ขาด" (มี SKU ที่มี shortage > 0)
        # 2. มีออเดอร์อย่างน้อย 1 ออเดอร์ที่หยิบครบ 100%
        # 3. ยังไม่ถึงระดับ R5
        can_split = False
        has_shortage = False
        has_complete_order = False

        # คำนวณระดับ (depth) ของ Batch
        current_depth = 0
        temp_batch = batch
        while temp_batch.parent_batch_id is not None:
            current_depth += 1
            temp_batch = db.session.get(Batch, temp_batch.parent_batch_id)
            if temp_batch is None:
                break

        # เช็คว่ามี Shortage หรือไม่
        for sku_data in sku_list:
            if sku_data.get("total_shortage", 0) > 0:
                has_shortage = True
                break

        # เช็คว่ามีออเดอร์ที่หยิบครบหรือไม่
        for order in orders:
            if order.picked_qty >= order.qty:
                has_complete_order = True
                break

        # สามารถแยกได้ถ้า: มี Shortage + มีออเดอร์ที่หยิบครบ + ยังไม่ถึง R5
        can_split = has_shortage and has_complete_order and current_depth < 5

        return render_template(
            "batch_detail.html",
            batch=batch,
            orders=orders,
            carrier_summary=carrier_summary,
            shop_summary=shop_summary,
            sku_progress=sku_list,
            shortage_details=shortage_details,  # ✅ ส่งข้อมูล shortage ไปด้วย
            batch_progress=batch_progress_data,  # ✅ ส่ง Overall Progress (Quantity-based)
            batch_family=batch_family_data,  # ✨ NEW: ส่งข้อมูล Parent-Child Batch Family
            batch_readiness=batch_readiness,  # ✨ NEW: ส่งข้อมูลว่าพร้อมสร้าง Handover Code หรือไม่
            can_split=can_split,  # ✅ NEW: ส่งข้อมูลว่าสามารถแยก Batch ได้หรือไม่
            current_depth=current_depth  # ✅ NEW: ระดับปัจจุบันของ Batch (0=Parent, 1=R1, 2=R2, ...)
        )

    @app.route("/batch/<batch_id>/summary")
    @login_required
    def batch_summary_json(batch_id):
        """FR-08, FR-09: Return batch summary as JSON"""
        batch = Batch.query.get_or_404(batch_id)

        try:
            shop_summary = json.loads(batch.shop_summary) if batch.shop_summary else {}
        except:
            shop_summary = {}

        result = {
            "batch_id": batch.batch_id,
            "platform": batch.platform,
            "run_no": batch.run_no,
            "batch_date": batch.batch_date.isoformat(),
            "total_orders": batch.total_orders,
            "carrier_summary": {
                "SPX": batch.spx_count,
                "Flash": batch.flash_count,
                "LEX": batch.lex_count,
                "J&T": batch.jt_count,
                "Other": batch.other_count
            },
            "shop_summary": shop_summary,
            "locked": batch.locked,
            "created_by": batch.created_by_username,
            "created_at": batch.created_at.isoformat() if batch.created_at else None
        }

        return jsonify(result)

    @app.route("/batch/next-run/<platform>")
    @login_required
    def batch_next_run(platform):
        """
        UX-01: Get next available run number and preview data for quick create
        Returns JSON with batch preview information
        """
        try:
            platform_std = normalize_platform(platform)
            batch_date = now_thai().date()
            
            # Get next run number
            next_run = get_next_run_number(platform_std, batch_date)
            
            # Generate preview batch ID
            batch_id_preview = generate_batch_id(platform_std, batch_date, next_run)
            
            # Get pending orders
            pending_orders = OrderLine.query.filter_by(
                platform=platform_std,
                batch_status="pending_batch"
            ).all()
            
            if not pending_orders:
                return jsonify({
                    "success": False,
                    "error": "no_pending_orders",
                    "message": f"ไม่มีออเดอร์รอสร้าง Batch สำหรับ {platform_std}"
                }), 404
            
            # Compute summary
            summary = compute_batch_summary(pending_orders)

            # ✅ Prepare order list for display
            order_list = []
            for order in pending_orders:
                # Get shop name
                shop_name = None
                if order.shop_id:
                    shop = db.session.get(Shop, order.shop_id)
                    shop_name = shop.name if shop else None

                order_list.append({
                    "order_id": order.order_id,
                    "sku": order.sku,
                    "item_name": order.item_name,
                    "qty": order.qty,
                    "platform": order.platform,
                    "carrier": order.carrier,
                    "shop_name": shop_name,
                    "sla_date": order.sla_date.isoformat() if order.sla_date else None
                })

            return jsonify({
                "success": True,
                "next_run": next_run,
                "batch_id_preview": batch_id_preview,
                "batch_date": batch_date.isoformat(),
                "platform": platform_std,
                "total_orders": summary["total_orders"],
                "carrier_summary": summary["carrier_summary"],
                "shop_summary": summary["shop_summary"],
                "orders": order_list  # ✅ Add order list
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": "server_error",
                "message": f"เกิดข้อผิดพลาด: {str(e)}"
            }), 500

    @app.route("/batch/quick-create/<platform>", methods=["POST"])
    @login_required
    def batch_quick_create(platform):
        """
        UX-01: Quick create batch with next available run number
        Creates batch automatically and returns success/error

        ✅ Security: Uses create_batch_with_retry() for race condition protection
        """
        try:
            platform_std = normalize_platform(platform)
            batch_date = now_thai().date()

            # ✅ Security: Use retry wrapper to handle race conditions
            batch = create_batch_with_retry(platform_std, batch_date)
            
            # Additional audit log for quick create
            log_audit("quick_create_batch", {
                "batch_id": batch.batch_id,
                "platform": platform_std,
                "run_no": batch.run_no,
                "method": "quick_create"
            }, batch_id=batch.batch_id, order_count=batch.total_orders)
            
            return jsonify({
                "success": True,
                "batch_id": batch.batch_id,
                "message": f"สร้าง Batch {batch.batch_id} สำเร็จ! รวม {batch.total_orders} ออเดอร์",
                "redirect_url": url_for("batch_detail", batch_id=batch.batch_id)
            })
            
        except ValueError as e:
            return jsonify({
                "success": False,
                "error": "validation_error",
                "message": str(e)
            }), 400
        except Exception as e:
            return jsonify({
                "success": False,
                "error": "server_error",
                "message": f"เกิดข้อผิดพลาด: {str(e)}"
            }), 500

    # -----------------------
    # Accept / Cancel / Bulk
    # -----------------------
    @app.route("/accept/<int:order_line_id>", methods=["POST"])
    @login_required
    def accept_order(order_line_id):
        ol = OrderLine.query.get_or_404(order_line_id)
        cu = current_user()

        sales_status = (getattr(ol, "sales_status", "") or "").upper()
        if sales_status == "PACKED" or bool(getattr(ol, "packed", False)):
            flash("รายการนี้ถูกแพ็คแล้ว (PACKED) — ไม่สามารถกดรับได้", "warning")
            return redirect(url_for("dashboard", **request.args))

        stock_qty = _calc_stock_qty_for_line(ol)
        if stock_qty <= 0:
            flash("สต็อกหมด — ไม่สามารถกดรับได้", "warning")
            return redirect(url_for("dashboard", **request.args))

        sku = _get_line_sku(ol)
        if not sku:
            flash("ไม่พบ SKU ของรายการนี้ — ไม่สามารถกดรับได้", "warning")
            return redirect(url_for("dashboard", **request.args))

        accepted_qty = db.session.query(func.coalesce(func.sum(OrderLine.qty), 0))\
            .filter(OrderLine.id != ol.id)\
            .filter(OrderLine.accepted.is_(True))\
            .filter(getattr(OrderLine, "sku") == sku).scalar() or 0

        proposed_total = int(accepted_qty) + int(ol.qty or 0)
        if proposed_total > int(stock_qty):
            flash("สินค้าไม่พอส่ง — ยอดที่รับจะเกินสต็อกรวมของ SKU นี้", "warning")
            return redirect(url_for("dashboard", **request.args))

        ol.accepted = True
        ol.accepted_at = now_thai()
        ol.accepted_by_user_id = cu.id if cu else None
        ol.accepted_by_username = cu.username if cu else None
        db.session.commit()
        flash(f"ทำเครื่องหมายกดรับ Order {ol.order_id} • SKU {sku} แล้ว", "success")
        return redirect(url_for("dashboard", **request.args))

    @app.route("/cancel_accept/<int:order_line_id>", methods=["POST"])
    @login_required
    def cancel_accept(order_line_id):
        ol = OrderLine.query.get_or_404(order_line_id)
        ol.accepted = False
        ol.accepted_at = None
        ol.accepted_by_user_id = None
        ol.accepted_by_username = None
        db.session.commit()
        flash(f"ยกเลิกการกดรับ Order {ol.order_id} • SKU {getattr(ol, 'sku', '')}", "warning")
        return redirect(url_for("dashboard", **request.args))

    @app.route("/bulk_accept", methods=["POST"])
    @login_required
    def bulk_accept():
        cu = current_user()
        order_line_ids = request.form.getlist("order_line_ids[]")
        if not order_line_ids:
            flash("กรุณาเลือกรายการที่ต้องการกดรับ", "warning")
            return redirect(url_for("dashboard", **request.args))
        success_count = 0
        error_messages = []
        for ol_id in order_line_ids:
            try:
                ol = OrderLine.query.get(int(ol_id))
                if not ol:
                    continue
                sales_status = (getattr(ol, "sales_status", "") or "").upper()
                if sales_status == "PACKED" or bool(getattr(ol, "packed", False)):
                    error_messages.append(f"Order {ol.order_id} ถูกแพ็คแล้ว")
                    continue
                stock_qty = _calc_stock_qty_for_line(ol)
                if stock_qty <= 0:
                    error_messages.append(f"Order {ol.order_id} สต็อกหมด")
                    continue
                sku = _get_line_sku(ol)
                if not sku:
                    error_messages.append(f"Order {ol.order_id} ไม่พบ SKU")
                    continue
                accepted_qty = db.session.query(func.coalesce(func.sum(OrderLine.qty), 0))\
                    .filter(OrderLine.id != ol.id)\
                    .filter(OrderLine.accepted.is_(True))\
                    .filter(getattr(OrderLine, "sku") == sku).scalar() or 0
                proposed_total = int(accepted_qty) + int(ol.qty or 0)
                if proposed_total > int(stock_qty):
                    error_messages.append(f"Order {ol.order_id} สินค้าไม่พอส่ง")
                    continue
                ol.accepted = True
                ol.accepted_at = now_thai()
                ol.accepted_by_user_id = cu.id if cu else None
                ol.accepted_by_username = cu.username if cu else None
                success_count += 1
            except Exception as e:
                error_messages.append(f"Order ID {ol_id}: {str(e)}")
                continue
        db.session.commit()
        if success_count > 0:
            flash(f"✅ กดรับสำเร็จ {success_count} รายการ", "success")
        if error_messages:
            for msg in error_messages[:5]:
                flash(f"⚠️ {msg}", "warning")
            if len(error_messages) > 5:
                flash(f"... และอีก {len(error_messages) - 5} รายการที่ไม่สามารถกดรับได้", "warning")
        return redirect(url_for("dashboard", **request.args))

    @app.route("/bulk_cancel", methods=["POST"])
    @login_required
    def bulk_cancel():
        order_line_ids = request.form.getlist("order_line_ids[]")
        if not order_line_ids:
            flash("กรุณาเลือกรายการที่ต้องการยกเลิก", "warning")
            return redirect(url_for("dashboard", **request.args))
        success_count = 0
        for ol_id in order_line_ids:
            try:
                ol = OrderLine.query.get(int(ol_id))
                if ol:
                    ol.accepted = False
                    ol.accepted_at = None
                    ol.accepted_by_user_id = None
                    ol.accepted_by_username = None
                    success_count += 1
            except Exception:
                continue
        db.session.commit()
        if success_count > 0:
            flash(f"✅ ยกเลิกสำเร็จ {success_count} รายการ", "success")
        return redirect(url_for("dashboard", **request.args))

    # -----------------------
    # Export dashboard
    # -----------------------
    @app.route("/export.xlsx")
    @login_required
    def export_excel():
        platform = normalize_platform(request.args.get("platform"))
        shop_id = request.args.get("shop_id")
        import_date = request.args.get("import_date")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        status = request.args.get("status")

        def _p(s):
            return parse_date_any(s)

        filters = {
            "platform": platform,
            "shop_id": int(shop_id) if shop_id else None,
            "import_date": _p(import_date),
            "date_from": datetime.combine(_p(date_from), datetime.min.time(), tzinfo=TH_TZ) if date_from else None,
            "date_to": datetime.combine(_p(date_to) + timedelta(days=1), datetime.min.time(), tzinfo=TH_TZ) if date_to else None,
        }

        rows, _ = compute_allocation(db.session, filters)

        for r in rows:
            if "stock_qty" not in r:
                sku = (r.get("sku") or "").strip()
                stock_qty = 0
                if sku:
                    prod = Product.query.filter_by(sku=sku).first()
                    if prod and hasattr(prod, "stock_qty"):
                        try:
                            stock_qty = int(prod.stock_qty or 0)
                        except Exception:
                            stock_qty = 0
                    else:
                        st = Stock.query.filter_by(sku=sku).first()
                        stock_qty = int(st.qty) if st and st.qty is not None else 0
                r["stock_qty"] = stock_qty
            r["accepted"] = bool(r.get("accepted", False))
            r["sales_status"] = r.get("sales_status", None)
            r["logistic"] = r.get("logistic") or r.get("logistic_type") or "Unknown"

        totals = _build_allqty_map(rows)
        for r in rows:
            r["allqty"] = int(totals.get((r.get("sku") or "").strip(), r.get("qty", 0)) or 0)
            _recompute_allocation_row(r)  # in-place

        packed_oids = _orders_packed_set(rows)
        for r in rows:
            if (r.get("order_id") or "").strip() in packed_oids:
                r["allocation_status"] = "PACKED"
                r["packed"] = True

        orders_ready = _orders_ready_set(rows)
        orders_low_order = _orders_lowstock_order_set(rows)

        status_norm = (status or "").strip().upper()
        if status_norm == "ORDER_READY":
            rows = [r for r in rows if (r.get("order_id") or "").strip() in orders_ready]
        elif status_norm in {"ORDER_LOW_STOCK", "ORDER_LOW"}:
            rows = [r for r in rows if (r.get("order_id") or "").strip() in orders_low_order]
        elif status_norm in {"PACKED"}:
            rows = [r for r in rows if (r.get("order_id") or "").strip() in packed_oids]
        elif status_norm:
            rows = [r for r in rows if (r.get("allocation_status") or "").strip().upper() == status_norm]
        else:
            rows = [r for r in rows if (r.get("order_id") or "").strip() not in packed_oids]

        rows = _annotate_order_spans(rows)

        df = pd.DataFrame([{
            "แพลตฟอร์ม": r.get("platform"),
            "ชื่อร้าน": r.get("shop"),
            "เลข Order": r.get("order_id_display"),
            "SKU": r.get("sku"),
            "Brand": r.get("brand"),
            "ชื่อสินค้า": r.get("model"),
            "Stock": r.get("stock_qty"),
            "Qty": r.get("qty"),
            "AllQty": r.get("allqty"),
            "เวลาที่ลูกค้าสั่ง": r.get("order_time"),
            "กำหนดส่ง": r.get("due_date"),
            "ประเภทขนส่ง": r.get("logistic"),
            "สั่งขาย": r.get("sales_status"),
            "สถานะ": r.get("allocation_status"),
            "ผู้กดรับ": r.get("accepted_by")
        } for r in rows])

        out = BytesIO()
        with pd.ExcelWriter(out, engine="xlsxwriter") as w:
            df.to_excel(w, index=False, sheet_name="Dashboard")
        out.seek(0)
        return send_file(out, as_attachment=True, download_name="dashboard_export.xlsx")

    # -----------------------
    # ใบงานคลัง (Warehouse Job Sheet)
    # -----------------------
    @app.route("/report/warehouse", methods=["GET"])
    @login_required
    def print_warehouse():
        platform = normalize_platform(request.args.get("platform"))
        shop_id = request.args.get("shop_id")
        logistic = request.args.get("logistic")
        compact_carrier = request.args.get("compact_carrier") in ("1", "true", "yes", "on")

        filters = {"platform": platform, "shop_id": int(shop_id) if shop_id else None, "import_date": None}
        rows, _ = compute_allocation(db.session, filters)
        rows = [r for r in rows if r.get("accepted") and r.get("allocation_status") in ("ACCEPTED", "READY_ACCEPT")]
        
        # NEW: กรอง Orders ที่ส่งมอบแล้วออก (ไม่ต้องพิมพ์ใบงานอีก)
        dispatched_oids = set()
        for r in rows:
            batch_id = r.get("batch_id")
            if batch_id:
                batch = db.session.get(Batch, batch_id)
                if batch and batch.handover_confirmed:
                    dispatched_oids.add((r.get("order_id") or "").strip())
        rows = [r for r in rows if (r.get("order_id") or "").strip() not in dispatched_oids]

        if logistic:
            rows = [r for r in rows if (r.get("logistic") or "").lower().find(logistic.lower()) >= 0]

        # >>> ฝังจำนวนครั้งที่พิมพ์ต่อออเดอร์
        _inject_print_counts_to_rows(rows, kind="warehouse")

        rows = _group_rows_for_report(rows)

        total_orders = len({(r.get("order_id") or "").strip() for r in rows if r.get("order_id")})
        total_qty = sum(int(r.get("qty", 0) or 0) for r in rows)

        # FR-11: Compute carrier and shop summary for Job Sheet
        carrier_counts = defaultdict(int)
        shop_counts = defaultdict(int)
        order_ids_set = set()

        for r in rows:
            oid = (r.get("order_id") or "").strip()
            if oid and oid not in order_ids_set:
                order_ids_set.add(oid)
                # Count by carrier (from logistic or carrier field)
                carrier = (r.get("carrier") or r.get("logistic") or "Unknown").strip()
                # Extract carrier name if it's in logistic text
                if "SPX" in carrier.upper() or "SHOPEE EXPRESS" in carrier.upper():
                    carrier = "SPX"
                elif "FLASH" in carrier.upper():
                    carrier = "Flash"
                elif "LEX" in carrier.upper() or "LAZADA EXPRESS" in carrier.upper():
                    carrier = "LEX"
                elif "J&T" in carrier.upper() or "JNT" in carrier.upper():
                    carrier = "J&T"
                elif not carrier or carrier == "-":
                    carrier = "Unknown"
                carrier_counts[carrier] += 1

                # Count by shop
                shop_name = r.get("shop") or "Unknown"
                shop_counts[shop_name] += 1

        shops = Shop.query.all()
        logistics = sorted(set(r.get("logistic") for r in rows if r.get("logistic")))

        # Use standalone print template (no base.html) to avoid blank pages
        return render_template(
            "report_print.html",
            rows=rows,
            count_orders=total_orders,
            total_qty=total_qty,
            carrier_summary=dict(carrier_counts),
            shop_summary=dict(shop_counts),
            shops=shops,
            logistics=logistics,
            platform_sel=platform,
            shop_sel=shop_id,
            logistic_sel=logistic,
            compact_carrier=compact_carrier,
            official_print=False,
            printed_meta=None,
            print_count_display=None
        )

    @app.route("/report/warehouse/print", methods=["POST"])
    @login_required
    def print_warehouse_commit():
        cu = current_user()
        platform = normalize_platform(request.form.get("platform"))
        shop_id = request.form.get("shop_id")
        logistic = request.form.get("logistic")
        compact_carrier = request.form.get("compact_carrier") in ("1", "true", "yes", "on")
        override = request.form.get("override") in ("1", "true", "yes")

        filters = {"platform": platform, "shop_id": int(shop_id) if shop_id else None, "import_date": None}
        rows, _ = compute_allocation(db.session, filters)
        rows = [r for r in rows if r.get("accepted") and r.get("allocation_status") in ("ACCEPTED", "READY_ACCEPT")]
        
        # NEW: กรอง Orders ที่ส่งมอบแล้วออก
        dispatched_oids = set()
        for r in rows:
            batch_id = r.get("batch_id")
            if batch_id:
                batch = db.session.get(Batch, batch_id)
                if batch and batch.handover_confirmed:
                    dispatched_oids.add((r.get("order_id") or "").strip())
        rows = [r for r in rows if (r.get("order_id") or "").strip() not in dispatched_oids]

        if logistic:
            rows = [r for r in rows if (r.get("logistic") or "").lower().find(logistic.lower()) >= 0]

        oids = sorted({(r.get("order_id") or "").strip() for r in rows if r.get("order_id")})
        if not oids:
            flash("ไม่พบออเดอร์สำหรับพิมพ์", "warning")
            return redirect(url_for("print_warehouse", platform=platform, shop_id=shop_id, logistic=logistic))

        already = _detect_already_printed(oids, kind="warehouse")
        if already and not (override and cu and cu.role == "admin"):
            head = ", ".join(list(already)[:10])
            more = "" if len(already) <= 10 else f" ... (+{len(already)-10})"
            flash(f"มีบางออเดอร์เคยพิมพ์ใบงานคลังไปแล้ว: {head}{more}", "danger")
            flash("ถ้าจำเป็นต้องพิมพ์ซ้ำ โปรดให้แอดมินกดยืนยัน 'อนุญาตพิมพ์ซ้ำ' แล้วพิมพ์อีกครั้ง", "warning")
            return redirect(url_for("print_warehouse", platform=platform, shop_id=shop_id, logistic=logistic))

        now_iso = now_thai().isoformat()
        _mark_printed(oids, kind="warehouse", user_id=(cu.id if cu else None), when_iso=now_iso)

        # NFR-03: Audit log for job sheet print
        log_audit("print_jobsheet", {
            "platform": platform,
            "shop_id": shop_id,
            "logistic": logistic,
            "override": override
        }, order_count=len(oids), print_count=1)

        # >>> ฝังจำนวนครั้งที่พิมพ์ (หลัง mark แล้ว)
        _inject_print_counts_to_rows(rows, kind="warehouse")

        rows = _group_rows_for_report(rows)
        total_orders = len({(r.get("order_id") or "").strip() for r in rows if r.get("order_id")})
        total_qty = sum(int(r.get("qty", 0) or 0) for r in rows)

        # FR-11: Compute carrier and shop summary for Job Sheet
        carrier_counts = defaultdict(int)
        shop_counts = defaultdict(int)
        order_ids_set = set()

        for r in rows:
            oid = (r.get("order_id") or "").strip()
            if oid and oid not in order_ids_set:
                order_ids_set.add(oid)
                carrier = (r.get("carrier") or r.get("logistic") or "Unknown").strip()
                if "SPX" in carrier.upper() or "SHOPEE EXPRESS" in carrier.upper():
                    carrier = "SPX"
                elif "FLASH" in carrier.upper():
                    carrier = "Flash"
                elif "LEX" in carrier.upper() or "LAZADA EXPRESS" in carrier.upper():
                    carrier = "LEX"
                elif "J&T" in carrier.upper() or "JNT" in carrier.upper():
                    carrier = "J&T"
                elif not carrier or carrier == "-":
                    carrier = "Unknown"
                carrier_counts[carrier] += 1

                shop_name = r.get("shop") or "Unknown"
                shop_counts[shop_name] += 1

        shops = Shop.query.all()
        logistics = sorted(set(r.get("logistic") for r in rows if r.get("logistic")))
        printed_meta = {"by": (cu.username if cu else "-"), "at": now_thai(), "orders": total_orders, "override": bool(already)}

        # Get max print count for display
        oids_for_count = sorted({(r.get("order_id") or "").strip() for r in rows if r.get("order_id")})
        print_counts = _get_print_counts_local(oids_for_count, "warehouse")
        print_count_display = max(print_counts.values()) if print_counts else 1

        return render_template(
            "report_print.html",
            rows=rows,
            count_orders=total_orders,
            total_qty=total_qty,
            carrier_summary=dict(carrier_counts),
            shop_summary=dict(shop_counts),
            shops=shops,
            logistics=logistics,
            platform_sel=platform,
            shop_sel=shop_id,
            logistic_sel=logistic,
            compact_carrier=compact_carrier,
            official_print=True,
            printed_meta=printed_meta,
            print_count_display=print_count_display
        )

    # -----------------------
    # Picking (รวมยอดหยิบ)
    # -----------------------
    def _aggregate_picking(rows: list[dict]) -> list[dict]:
        from collections import Counter
        rows = rows or []
        agg: dict[str, dict] = {}
        
        for r in rows:
            if not bool(r.get("accepted")):
                continue
            if (r.get("allocation_status") or "") not in ("ACCEPTED", "READY_ACCEPT"):
                continue
            sku = str(r.get("sku") or "").strip()
            if not sku:
                continue
            brand = str(r.get("brand") or "").strip()
            model = str(r.get("model") or "").strip()
            qty = int(r.get("qty", 0) or 0)
            stock_qty = int(r.get("stock_qty", 0) or 0)
            platform = str(r.get("platform") or "").strip()
            logistic = str(r.get("logistic") or "").strip()
            
            a = agg.setdefault(sku, {
                "sku": sku, "brand": brand, "model": model, 
                "need_qty": 0, "stock_qty": 0,
                "platforms": set(), "logistics_counter": Counter()
            })
            a["need_qty"] += qty
            if stock_qty > a["stock_qty"]:
                a["stock_qty"] = stock_qty
            if platform:
                a["platforms"].add(platform)
            if logistic and logistic not in ("-", ""):
                # ลบ 'Standard Delivery - ส่งธรรมดาในประเทศ-' ออกก่อนนับ
                clean_logistic = logistic.replace("Standard Delivery - ส่งธรรมดาในประเทศ-", "").strip()
                # ถ้าหลังจาก clean แล้วเป็นค่าว่างหรือ "-" ให้ใช้ "Unknown"
                if not clean_logistic or clean_logistic == "-":
                    clean_logistic = "Unknown"
                a["logistics_counter"][clean_logistic] += qty

        items = []
        for _, a in agg.items():
            need = int(a["need_qty"])
            stock = int(a["stock_qty"])
            shortage = max(0, need - stock)
            remain = stock - need
            
            # รวม platforms เป็น string
            platforms_str = ", ".join(sorted(a["platforms"])) if a["platforms"] else ""
            
            # สร้าง logistics string พร้อมจำนวน เช่น "SPX Express(4), nan(2)"
            logistics_parts = []
            for carrier, count in sorted(a["logistics_counter"].items()):
                logistics_parts.append(f"{carrier}({count})")
            logistics_str = ", ".join(logistics_parts) if logistics_parts else ""
            
            items.append({
                "sku": a["sku"], "brand": a["brand"], "model": a["model"],
                "need_qty": need, "stock_qty": stock, "shortage": shortage, "remain_after_pick": remain,
                "platform": platforms_str, "logistic": logistics_str,
                "logistics_counter": dict(a["logistics_counter"])  # เก็บ counter ไว้ใช้คำนวณ summary
            })
        items.sort(key=lambda x: (x["brand"].lower(), x["model"].lower(), x["sku"].lower()))
        return items

    @app.route("/report/picking", methods=["GET"])
    @login_required
    def picking_list():
        try:
            platform = normalize_platform(request.args.get("platform"))
            shop_id = request.args.get("shop_id")
            logistic = request.args.get("logistic")
            sort_by = request.args.get("sort_by", "sku")  # UX-03: Sort parameter

            filters = {"platform": platform if platform else None, "shop_id": int(shop_id) if shop_id else None, "import_date": None}
            rows, _ = compute_allocation(db.session, filters)
        except Exception as e:
            import traceback
            traceback.print_exc()
            flash(f"Error loading picking list: {str(e)}", "danger")
            return redirect(url_for("dashboard"))

        # NEW: กรอง Orders ที่ส่งมอบแล้วออก (ไม่ต้องหยิบอีก)
        dispatched_oids = set()
        for r in rows:
            batch_id = r.get("batch_id")
            if batch_id:
                batch = db.session.get(Batch, batch_id)
                if batch and batch.handover_confirmed:
                    dispatched_oids.add((r.get("order_id") or "").strip())
        rows = [r for r in rows if (r.get("order_id") or "").strip() not in dispatched_oids]
        
        # เตรียมข้อมูลปลอดภัย + ใส่ stock_qty ให้ครบ
        safe_rows = []
        for r in rows:
            r = dict(r)
            if "stock_qty" not in r:
                sku = (r.get("sku") or "").strip()
                stock_qty = 0
                if sku:
                    prod = Product.query.filter_by(sku=sku).first()
                    if prod and hasattr(prod, "stock_qty"):
                        try:
                            stock_qty = int(prod.stock_qty or 0)
                        except Exception:
                            stock_qty = 0
                    else:
                        st = Stock.query.filter_by(sku=sku).first()
                        stock_qty = int(st.qty) if st and st.qty is not None else 0
                r["stock_qty"] = stock_qty
            r["accepted"] = bool(r.get("accepted", False))
            r["sales_status"] = r.get("sales_status", None)
            r["logistic"] = r.get("logistic") or r.get("logistic_type") or "Unknown"
            safe_rows.append(r)

        if logistic:
            safe_rows = [r for r in safe_rows if (r.get("logistic") or "").lower().find(logistic.lower()) >= 0]

        # รวมต่อ SKU
        items = _aggregate_picking(safe_rows)

        # UX-03: Sort items based on sort_by parameter
        if sort_by == "brand":
            items.sort(key=lambda x: (x["brand"].lower(), x["model"].lower(), x["sku"].lower()))
        elif sort_by == "shortage":
            items.sort(key=lambda x: (-x["shortage"], x["brand"].lower(), x["sku"].lower()))  # Descending shortage
        else:  # default: sku
            items.sort(key=lambda x: (x["sku"].lower(), x["brand"].lower()))

        # ===== นับจำนวนครั้งที่พิมพ์ Picking (รวมทั้งชุดงาน) — ใช้ MAX ไม่ใช่ SUM =====
        valid_rows = [r for r in safe_rows if r.get("accepted") and r.get("allocation_status") in ("ACCEPTED", "READY_ACCEPT")]
        order_ids = sorted({(r.get("order_id") or "").strip() for r in valid_rows if r.get("order_id")})
        print_counts_pick = _get_print_counts_local(order_ids, "picking")
        print_count_overall = max(print_counts_pick.values()) if print_counts_pick else 0

        # ชื่อร้านสำหรับแสดงในคอลัมน์ใหม่
        shop_sel_name = None
        if shop_id:
            s = Shop.query.get(int(shop_id))
            if s:
                shop_sel_name = f"{s.platform} • {s.name}"

        # เติมแพลตฟอร์ม/ร้าน/ประเภทขนส่งให้แต่ละ item เพื่อไม่ให้ขึ้น '-'
        for it in items:
            # ใช้ค่าจาก item ก่อน ถ้าไม่มีหรือเป็นค่าว่าง ค่อยใช้จาก filter
            if not it.get("platform") or it.get("platform") == "":
                it["platform"] = platform if platform else "-"
            if not it.get("logistic") or it.get("logistic") == "" or it.get("logistic") == "-":
                it["logistic"] = logistic if logistic and logistic != "-" else ""
            it["shop"] = shop_sel_name if shop_sel_name else "-"

        totals = {
            "total_skus": len(items),
            "total_need_qty": sum(i["need_qty"] for i in items),
            "total_shortage": sum(i["shortage"] for i in items),
        }
        
        # นับจำนวนขนส่งแต่ละประเภท (จาก logistics_counter ของแต่ละ item)
        from collections import Counter
        carrier_counts = Counter()
        for it in items:
            logistics_counter = it.get("logistics_counter", {})
            for carrier, count in logistics_counter.items():
                carrier_counts[carrier] += count

        shops = Shop.query.order_by(Shop.name.asc()).all()
        logistics = sorted(set(r.get("logistic") for r in safe_rows if r.get("logistic")))

        return render_template(
            "picking_print.html",
            items=items,
            totals=totals,
            carrier_summary=dict(carrier_counts),
            shops=shops,
            logistics=logistics,
            platform_sel=platform,
            shop_sel=shop_id,
            shop_sel_name=shop_sel_name,
            logistic_sel=logistic,
            official_print=False,
            printed_meta=None,
            print_count_overall=print_count_overall,
        )

    @app.route("/report/picking/print", methods=["POST"])
    @login_required
    def picking_list_commit():
        cu = current_user()
        platform = normalize_platform(request.form.get("platform"))
        shop_id = request.form.get("shop_id")
        logistic = request.form.get("logistic")
        override = request.form.get("override") in ("1", "true", "yes")

        filters = {"platform": platform if platform else None, "shop_id": int(shop_id) if shop_id else None, "import_date": None}
        rows, _ = compute_allocation(db.session, filters)

        # NEW: กรอง Orders ที่ส่งมอบแล้วออก
        dispatched_oids = set()
        for r in rows:
            batch_id = r.get("batch_id")
            if batch_id:
                batch = db.session.get(Batch, batch_id)
                if batch and batch.handover_confirmed:
                    dispatched_oids.add((r.get("order_id") or "").strip())
        rows = [r for r in rows if (r.get("order_id") or "").strip() not in dispatched_oids]

        safe_rows = []
        for r in rows:
            r = dict(r)
            if "stock_qty" not in r:
                sku = (r.get("sku") or "").strip()
                stock_qty = 0
                if sku:
                    prod = Product.query.filter_by(sku=sku).first()
                    if prod and hasattr(prod, "stock_qty"):
                        try:
                            stock_qty = int(prod.stock_qty or 0)
                        except Exception:
                            stock_qty = 0
                    else:
                        st = Stock.query.filter_by(sku=sku).first()
                        stock_qty = int(st.qty) if st and st.qty is not None else 0
                r["stock_qty"] = stock_qty
            r["accepted"] = bool(r.get("accepted", False))
            r["logistic"] = r.get("logistic") or r.get("logistic_type") or "Unknown"
            safe_rows.append(r)

        if logistic:
            safe_rows = [r for r in safe_rows if (r.get("logistic") or "").lower().find(logistic.lower()) >= 0]

        valid_rows = [r for r in safe_rows if r.get("accepted") and r.get("allocation_status") in ("ACCEPTED", "READY_ACCEPT")]
        oids = sorted({(r.get("order_id") or "").strip() for r in valid_rows if r.get("order_id")})

        # ป้องกันพิมพ์ซ้ำ
        if not oids:
            flash("ไม่พบออเดอร์สำหรับพิมพ์ Picking", "warning")
            return redirect(url_for("picking_list", platform=platform, shop_id=shop_id, logistic=logistic))

        already = _detect_already_printed(oids, kind="picking")
        if already and not (override and cu and cu.role == "admin"):
            head = ", ".join(list(already)[:10])
            more = "" if len(already) <= 10 else f" ... (+{len(already)-10})"
            flash(f"มีบางออเดอร์เคยพิมพ์ Picking ไปแล้ว: {head}{more}", "danger")
            flash("ถ้าจำเป็นต้องพิมพ์ซ้ำ โปรดให้แอดมินติ๊ก 'อนุญาตพิมพ์ซ้ำ' แล้วพิมพ์อีกครั้ง", "warning")
            return redirect(url_for("picking_list", platform=platform, shop_id=shop_id, logistic=logistic))

        # บันทึกการพิมพ์
        now_iso = now_thai().isoformat()
        _mark_printed(oids, kind="picking", user_id=(cu.id if cu else None), when_iso=now_iso)

        # NFR-03: Audit log for picking list print
        log_audit("print_picklist", {
            "platform": platform,
            "shop_id": shop_id,
            "logistic": logistic,
            "override": override
        }, order_count=len(oids), print_count=1)

        # รวมต่อ SKU สำหรับแสดงผล
        items = _aggregate_picking(safe_rows)
        for it in items:
            it["platform"] = platform or "-"
            # แสดงชื่อร้านสวยงาม
            if shop_id:
                s = Shop.query.get(int(shop_id))
                it["shop"] = (f"{s.platform} • {s.name}") if s else "-"
            else:
                it["shop"] = "-"
            # Don't set logistic to "-", let template handle Unknown display
            if not it.get("logistic") or it.get("logistic") == "-":
                it["logistic"] = logistic if logistic and logistic != "-" else ""

        totals = {
            "total_skus": len(items),
            "total_need_qty": sum(i["need_qty"] for i in items),
            "total_shortage": sum(i["shortage"] for i in items),
        }
        
        # นับจำนวนขนส่งแต่ละประเภท (จาก logistics_counter ของแต่ละ item)
        from collections import Counter
        carrier_counts = Counter()
        for it in items:
            logistics_counter = it.get("logistics_counter", {})
            for carrier, count in logistics_counter.items():
                carrier_counts[carrier] += count
        
        shops = Shop.query.order_by(Shop.name.asc()).all()
        logistics = sorted(set(r.get("logistic") for r in safe_rows if r.get("logistic")))
        printed_meta = {"by": (cu.username if cu else "-"), "at": now_thai(), "orders": len(oids), "override": bool(already)}

        # ดึงจำนวนครั้งที่พิมพ์ล่าสุด (หลัง mark แล้ว) — ใช้ MAX
        print_counts_pick = _get_print_counts_local(oids, "picking")
        print_count_overall = max(print_counts_pick.values()) if print_counts_pick else 0

        # ชื่อร้านสำหรับหัวกระดาษ
        shop_sel_name = None
        if shop_id:
            s = Shop.query.get(int(shop_id))
            if s:
                shop_sel_name = f"{s.platform} • {s.name}"

        return render_template(
            "picking_print.html",
            items=items,
            totals=totals,
            carrier_summary=dict(carrier_counts),
            shops=shops,
            logistics=logistics,
            platform_sel=platform,
            shop_sel=shop_id,
            shop_sel_name=shop_sel_name,
            logistic_sel=logistic,
            official_print=True,
            printed_meta=printed_meta,
            print_count_overall=print_count_overall,
        )

    @app.route("/batch/<batch_id>/export.xlsx")
    @login_required
    def batch_export_excel(batch_id):
        """Export batch orders to Excel"""
        batch = Batch.query.get_or_404(batch_id)
        orders = OrderLine.query.filter_by(batch_id=batch_id).all()
        
        # Prepare data for export
        data = []
        for order in orders:
            shop = Shop.query.get(order.shop_id) if order.shop_id else None
            data.append({
                "Batch ID": batch.batch_id,
                "Order ID": order.order_id,
                "SKU": order.sku,
                "สินค้า": order.item_name,
                "จำนวน": order.qty,
                "Carrier": order.carrier or order.logistic_type or "-",
                "ร้าน": shop.name if shop else "-",
                "Platform": order.platform,
                "เวลาสั่ง": order.order_time.strftime("%Y-%m-%d %H:%M:%S") if order.order_time else "-"
            })
        
        df = pd.DataFrame(data)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name=f"Batch {batch.batch_id}")
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[f"Batch {batch.batch_id}"]
            
            # Add header format
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })
            
            # Write headers with format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-adjust column widths
            for i, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.set_column(i, i, min(max_len, 50))
        
        out.seek(0)
        return send_file(
            out,
            as_attachment=True,
            download_name=f"batch_{batch.batch_id}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # -----------------------
    # Print Batch Warehouse Sheet
    # -----------------------
    @app.route("/batch/<batch_id>/print-warehouse")
    @login_required
    def batch_print_warehouse(batch_id):
        """พิมพ์ใบงานคลังตาม Batch - ใช้ Layout เดียวกับ /report/warehouse"""
        batch = Batch.query.get_or_404(batch_id)
        orders = OrderLine.query.filter_by(batch_id=batch_id).order_by(OrderLine.order_id, OrderLine.sku).all()

        if not orders:
            flash(f"ไม่พบออเดอร์ใน Batch {batch_id}", "warning")
            return redirect(url_for('batch_detail', batch_id=batch_id))

        # จัดกลุ่มตาม order_id (แสดงเหมือน /report/warehouse)
        rows = []
        prev_order_id = None

        for order in orders:
            shop = db.session.get(Shop, order.shop_id)

            # แสดง order_id เฉพาะแถวแรกของแต่ละ order
            show_order_id = (order.order_id != prev_order_id)

            # ดึงข้อมูลสินค้า
            product = Product.query.filter_by(sku=order.sku).first()

            rows.append({
                "order_id": order.order_id,
                "order_id_display": order.order_id if show_order_id else "",
                "show_order_id": show_order_id,
                "platform": order.platform,
                "shop": shop.name if shop else "-",
                "sku": order.sku,
                "model": product.model if product else "",
                "product_name": order.item_name,
                "qty": order.qty,
                "carrier": order.carrier,
                "logistic": order.logistic_type,
                "accepted_by": batch.created_by_username or "System",  # ผู้สร้าง Batch
                "printed_warehouse_count": getattr(order, 'printed_warehouse_count', 0) or 0,
            })

            prev_order_id = order.order_id

        # คำนวณสรุป
        count_orders = len(set(o.order_id for o in orders))
        total_qty = sum(o.qty for o in orders)

        # สรุปตาม Carrier
        from importers import extract_carrier_from_logistics
        carrier_counts = defaultdict(int)
        shop_counts = defaultdict(int)
        order_ids_seen = set()

        for order in orders:
            if order.order_id not in order_ids_seen:
                order_ids_seen.add(order.order_id)
                carrier = order.carrier or extract_carrier_from_logistics(order.logistic_type or "")
                carrier_counts[carrier] += 1
                shop = db.session.get(Shop, order.shop_id)
                if shop:
                    shop_counts[shop.name] += 1

        return render_template(
            "report_print.html",
            rows=rows,
            count_orders=count_orders,
            total_qty=total_qty,
            carrier_summary=dict(carrier_counts),
            shop_summary=dict(shop_counts),
            shops=Shop.query.all(),
            logistics=[],
            platform_sel=batch.platform,
            shop_sel=None,
            logistic_sel=None,
            compact_carrier=False,
            official_print=False,  # เปลี่ยนเป็น False เพื่อแสดง filter-form
            printed_meta=None,
            print_count_display=None,
            batch=batch,  # ส่งข้อมูล Batch ไปด้วย
            is_batch_print=True  # flag เพื่อแสดงว่าเป็นการพิมพ์จาก Batch
        )

    # -----------------------
    # Print Batch Picking List
    # -----------------------
    @app.route("/batch/<batch_id>/print-picking")
    @login_required
    def batch_print_picking(batch_id):
        """พิมพ์ Picking List ตาม Batch - ใช้ Layout เดียวกับ /report/picking"""
        batch = Batch.query.get_or_404(batch_id)
        orders = OrderLine.query.filter_by(batch_id=batch_id).all()

        # อ่านค่า compact_carrier จาก query string
        compact_carrier = request.args.get("compact_carrier") in ("1", "true", "yes", "on")

        if not orders:
            flash(f"ไม่พบออเดอร์ใน Batch {batch_id}", "warning")
            return redirect(url_for('batch_detail', batch_id=batch_id))

        # ฟังก์ชันสำหรับลบ prefix ขนส่ง
        def clean_carrier(carrier_text):
            if not compact_carrier:
                return carrier_text
            cleaned = carrier_text.replace('Standard Delivery - ส่งธรรมดาในประเทศ-', '')
            cleaned = cleaned.replace('Standard Delivery-', '')
            cleaned = cleaned.replace('Standard Delivery - ', '')
            return cleaned.strip()

        # รวมยอดตาม SKU (เหมือน compute_allocation)
        sku_summary = defaultdict(lambda: {
            "need_qty": 0,
            "platform": "",
            "shop_names": set(),
            "logistics": set(),
            "brand": "",
            "model": "",
            "item_name": "",
        })

        for order in orders:
            shop = db.session.get(Shop, order.shop_id)
            product = Product.query.filter_by(sku=order.sku).first()

            sku_summary[order.sku]["need_qty"] += order.qty
            sku_summary[order.sku]["platform"] = order.platform
            if shop:
                sku_summary[order.sku]["shop_names"].add(shop.name)
            if order.logistic_type:
                # ทำความสะอาด carrier ก่อนเก็บ
                cleaned = clean_carrier(order.logistic_type)
                sku_summary[order.sku]["logistics"].add(cleaned)

            # ดึงชื่อสินค้าจาก OrderLine ก่อน (มาจากไฟล์ Excel)
            if order.item_name:
                sku_summary[order.sku]["item_name"] = order.item_name

            # ถ้ามีข้อมูล Product ให้ดึง brand และ model เพิ่มเติม
            if product:
                sku_summary[order.sku]["brand"] = product.brand or ""
                # ใช้ model จาก Product ถ้ามี ไม่งั้นใช้ item_name
                sku_summary[order.sku]["model"] = product.model or sku_summary[order.sku]["item_name"]

        # สร้าง items list
        items = []
        for sku, data in sku_summary.items():
            stock = Stock.query.filter_by(sku=sku).first()
            stock_qty = stock.qty if stock else 0

            items.append({
                "sku": sku,
                "brand": data["brand"],
                "model": data["model"] or data["item_name"],  # ใช้ item_name ถ้า model ว่าง
                "need_qty": data["need_qty"],
                "stock_qty": stock_qty,
                "shortage": max(0, data["need_qty"] - stock_qty),
                "remain_after_pick": stock_qty - data["need_qty"],
                "platform": data["platform"],
                "shop_name": ", ".join(sorted(data["shop_names"])),
                "logistic": ", ".join(sorted(data["logistics"])),
            })

        # เรียงตาม SKU
        items.sort(key=lambda x: x["sku"])

        # คำนวณสรุป
        totals = {
            "total_skus": len(items),
            "total_need_qty": sum(item["need_qty"] for item in items),
            "total_shortage": sum(item["shortage"] for item in items),
        }

        # นับจำนวนขนส่งแต่ละประเภท
        from collections import Counter
        carrier_counts = Counter()
        for item in items:
            # แยก logistics ที่มีหลายค่า (คั่นด้วย ", ")
            logistics_list = item.get("logistic", "").split(", ")
            for log in logistics_list:
                log = log.strip()
                if log and log != "-":
                    carrier_counts[log] += 1

        return render_template(
            "picking_print.html",
            items=items,
            totals=totals,
            carrier_summary=dict(carrier_counts),
            shops=Shop.query.all(),
            logistics=[],
            platform_sel=batch.platform,
            shop_sel=None,
            shop_sel_name=None,
            logistic_sel=None,
            compact_carrier=compact_carrier,  # ส่งค่า compact_carrier ไปด้วย
            official_print=False,  # เปลี่ยนเป็น False เพื่อแสดง filter-form
            printed_meta=None,
            print_count_overall=None,
            batch=batch,  # ส่งข้อมูล Batch ไปด้วย
            is_batch_print=True  # flag เพื่อแสดงว่าเป็นการพิมพ์จาก Batch
        )

    @app.route("/batch/<batch_id>/print-sku-qr")
    @login_required
    def batch_print_sku_qr(batch_id):
        """พิมพ์ QR Code ขนาดใหญ่สำหรับทุก SKU ใน Batch"""
        batch = Batch.query.get_or_404(batch_id)
        orders = OrderLine.query.filter_by(batch_id=batch_id).all()

        if not orders:
            flash(f"ไม่พบออเดอร์ใน Batch {batch_id}", "warning")
            return redirect(url_for('batch_detail', batch_id=batch_id))

        # รวม SKU ที่ไม่ซ้ำกัน พร้อมข้อมูลสินค้า
        sku_dict = {}
        tracking_dict = {}

        for order in orders:
            # รวม SKU
            if order.sku not in sku_dict:
                product = Product.query.filter_by(sku=order.sku).first()
                stock = Stock.query.filter_by(sku=order.sku).first()

                sku_dict[order.sku] = {
                    "sku": order.sku,
                    "brand": product.brand if product else "",
                    "model": product.model if product else order.item_name or "",
                    "item_name": order.item_name or "",
                    "stock_qty": stock.qty if stock else 0,
                    "need_qty": 0
                }

            # นับจำนวนที่ต้องหยิบ
            sku_dict[order.sku]["need_qty"] += order.qty

            # รวม Tracking Numbers (ไม่ซ้ำกัน)
            if order.tracking_number and order.tracking_number not in tracking_dict:
                tracking_dict[order.tracking_number] = {
                    "tracking": order.tracking_number,
                    "order_id": order.order_id,
                    "carrier": order.carrier or "Unknown"
                }

        # แปลงเป็น list และเรียงตาม SKU / Tracking
        sku_list = sorted(sku_dict.values(), key=lambda x: x["sku"])
        tracking_list = sorted(tracking_dict.values(), key=lambda x: x["tracking"])

        return render_template(
            "sku_qr_print.html",
            batch=batch,
            sku_list=sku_list,
            tracking_list=tracking_list,
            total_skus=len(sku_list),
            total_trackings=len(tracking_list)
        )

    # ==========================================
    # Handover Code System Routes
    # ==========================================

    @app.route("/api/batch/<batch_id>/generate-handover-code", methods=["POST"])
    @login_required
    def api_generate_handover_code(batch_id):
        """Generate handover code for batch completion (BH-YYYYMMDD-XXX format)"""
        batch = db.session.get(Batch, batch_id)

        if not batch:
            return jsonify({"success": False, "error": "ไม่พบ Batch"}), 404

        # Check if batch is 100% complete
        # ✅ Phase 2.1: ใช้ Quantity-based calculation แทน Order-based
        progress_data = calculate_batch_progress(batch_id)

        if progress_data["total_qty"] == 0:
            return jsonify({"success": False, "error": "Batch ไม่มีออเดอร์"}), 400

        if progress_data["progress_percent"] < 100:
            return jsonify({
                "success": False,
                "error": f"Batch ยังไม่เสร็จ (Progress: {progress_data['progress_percent']:.1f}%)\n"
                        f"หยิบได้: {progress_data['picked_qty']}/{progress_data['total_qty']} ชิ้น\n"
                        f"Shortage: {progress_data['shortage_qty']} ชิ้น"
            }), 400

        # Check if code already exists
        if batch.handover_code:
            return jsonify({
                "success": False,
                "error": f"Batch นี้มีรหัสส่งมอบแล้ว: {batch.handover_code}"
            }), 400

        # ✅ Phase 2.6: Retry on conflict to prevent race condition
        from sqlalchemy.exc import IntegrityError
        import time

        MAX_RETRIES = 3
        batch_date_str = batch.batch_date.strftime('%Y%m%d')

        for attempt in range(MAX_RETRIES):
            try:
                # Find next running number for this date
                max_code = db.session.query(Batch.handover_code)\
                    .filter(Batch.handover_code.like(f"BH-{batch_date_str}-%"))\
                    .order_by(Batch.handover_code.desc())\
                    .first()

                if max_code and max_code[0]:
                    # Extract running number from last code
                    try:
                        last_num = int(max_code[0].split('-')[-1])
                        next_num = last_num + 1
                    except:
                        next_num = 1
                else:
                    next_num = 1

                handover_code = f"BH-{batch_date_str}-{next_num:03d}"

                # Save to database (will raise IntegrityError if duplicate)
                cu = current_user()
                batch.handover_code = handover_code
                batch.handover_code_generated_at = now_thai()
                batch.handover_code_generated_by_user_id = cu.id
                batch.handover_code_generated_by_username = cu.username

                db.session.commit()

                # Audit log
                log = AuditLog(
                    action="generate_handover_code",
                    user_id=cu.id,
                    username=cu.username,
                    details=json.dumps({
                        "batch_id": batch_id,
                        "handover_code": handover_code
                    }),
                    batch_id=batch_id
                )
                db.session.add(log)
                db.session.commit()

                return jsonify({
                    "success": True,
                    "handover_code": handover_code,
                    "message": "สร้างรหัสส่งมอบสำเร็จ"
                })

            except IntegrityError as e:
                # Conflict detected! Rollback and retry
                db.session.rollback()
                print(f"Handover code conflict (attempt {attempt + 1}/{MAX_RETRIES}), retrying...")

                if attempt == MAX_RETRIES - 1:
                    # Last attempt failed
                    return jsonify({
                        "success": False,
                        "error": "ไม่สามารถสร้างรหัสส่งมอบได้ กรุณาลองอีกครั้ง"
                    }), 500

                # Wait before retry (exponential backoff)
                time.sleep(0.1 * (attempt + 1))  # 100ms, 200ms, 300ms
                continue

        # Should not reach here
        return jsonify({
            "success": False,
            "error": "เกิดข้อผิดพลาดในการสร้างรหัส"
        }), 500

    # ============================================================
    # Parent-Child Batch System (Phase 3: Shortage Management)
    # ============================================================

    @app.route("/api/batch/<batch_id>/auto-split", methods=["POST"])
    @login_required
    def api_auto_split_batch(batch_id):
        """
        แยก Batch อัตโนมัติเมื่อมี Shortage
        - Orders ที่หยิบครบแล้วอยู่ใน Parent Batch (Progress = 100%)
        - Orders ที่มี Shortage ย้ายไป Child Batch (Progress < 100%)

        Business Rules:
        - ไม่สามารถแยก Child Batch ได้ (แยกได้เฉพาะ Parent)
        - จำกัดสูงสุด 5 Child Batches ต่อ 1 Parent
        - ต้องมี Orders อย่างน้อย 2 กลุ่ม (complete + shortage)
        """
        batch = db.session.get(Batch, batch_id)

        if not batch:
            return jsonify({"success": False, "error": "ไม่พบ Batch"}), 404

        # ✅ NEW: คำนวณระดับ (depth) ของ Batch นี้
        # R1 = depth 1, R2 = depth 2, ..., R5 = depth 5
        current_depth = 0
        temp_batch = batch
        while temp_batch.parent_batch_id is not None:
            current_depth += 1
            temp_batch = db.session.get(Batch, temp_batch.parent_batch_id)
            if temp_batch is None:
                break

        # ถ้า Batch นี้เป็น R5 แล้ว → ไม่สามารถแยกต่อได้
        if current_depth >= 5:
            return jsonify({
                "success": False,
                "error": "ถึงขอบเขตแล้ว: Batch นี้อยู่ที่ระดับ R5 แล้ว ไม่สามารถแยกต่อได้"
            }), 400

        # ตรวจสอบจำนวน Child Batch ที่มีอยู่แล้ว (สำหรับการสร้างหมายเลข sub_batch_number)
        existing_children = Batch.query.filter_by(parent_batch_id=batch_id).count()
        if existing_children >= 5:
            return jsonify({
                "success": False,
                "error": "ถึงขอบเขตแล้ว: Batch นี้มี Child Batch ครบ 5 Batch แล้ว"
            }), 400

        # ดึง Orders ทั้งหมดใน Batch
        orders = OrderLine.query.filter_by(batch_id=batch_id).all()

        if not orders:
            return jsonify({"success": False, "error": "Batch ไม่มี Orders"}), 404

        # แยก Orders เป็น 2 กลุ่ม
        complete_orders = []  # Orders ที่หยิบครบ (ไม่มี Shortage)
        shortage_orders = []  # Orders ที่มี Shortage

        shortage_details = []  # รวบรวมรายละเอียด Shortage

        # ✅ FIX: เช็คจาก ShortageQueue แทน shortage_qty field
        # เพราะบางครั้ง shortage_qty ไม่ได้อัปเดตแต่มี Shortage Record อยู่
        for order in orders:
            # เช็คว่ามี Shortage Record หรือไม่
            has_shortage_record = ShortageQueue.query.filter(
                ShortageQueue.order_line_id == order.id,
                ShortageQueue.status.in_(['pending', 'waiting_stock', 'ready_to_pick'])
            ).first()

            # หรือเช็คจาก shortage_qty field
            has_shortage_qty = (order.shortage_qty or 0) > 0

            # หรือเช็คว่ายังหยิบไม่ครบ
            not_fully_picked = order.picked_qty < order.qty

            if has_shortage_record or has_shortage_qty or not_fully_picked:
                shortage_orders.append(order)
                qty_shortage = order.shortage_qty or (order.qty - order.picked_qty)
                shortage_details.append(
                    f"Order {order.order_id}: SKU {order.sku} ขาด {qty_shortage} ชิ้น"
                )
            else:
                complete_orders.append(order)

        # ถ้าไม่มี Shortage → ไม่ต้องแยก
        if not shortage_orders:
            return jsonify({
                "success": False,
                "error": "Batch นี้ไม่มี Shortage ไม่จำเป็นต้องแยก"
            }), 400

        # ถ้าทุก Order มี Shortage → ไม่ต้องแยก (รอสต็อกเข้าทั้งหมด)
        if not complete_orders:
            return jsonify({
                "success": False,
                "error": "Batch นี้ทุก Order มี Shortage กรุณารอสต็อกเข้าแทน"
            }), 400

        # สร้าง Child Batch
        next_sub_number = existing_children + 1
        child_batch_id = f"{batch_id}.{next_sub_number}"

        # รวบรวม Shortage Info
        shortage_reason = "\n".join(shortage_details)

        # นับ Orders ตาม Order ID (เพราะ 1 Order อาจมีหลาย SKU)
        complete_order_ids = set(o.order_id for o in complete_orders)
        shortage_order_ids = set(o.order_id for o in shortage_orders)

        # คำนวณ Carrier Summary และ Shop Summary สำหรับ Child Batch
        from collections import defaultdict
        child_carrier_counts = defaultdict(int)
        child_shop_counts = defaultdict(int)

        # ใช้ set เพื่อนับ order_id ที่ unique
        counted_orders = set()

        for order in shortage_orders:
            if order.order_id not in counted_orders:
                counted_orders.add(order.order_id)

                # นับ carrier
                carrier = order.carrier or "Other"
                child_carrier_counts[carrier] += 1

                # นับ shop (ต้อง query Shop model เพื่อเอา name)
                shop = db.session.get(Shop, order.shop_id) if order.shop_id else None
                shop_name = shop.name if shop else "Unknown"
                child_shop_counts[shop_name] += 1

        # สร้าง Child Batch
        child_batch = Batch(
            batch_id=child_batch_id,
            platform=batch.platform,
            batch_date=batch.batch_date,
            run_no=batch.run_no,
            parent_batch_id=batch_id,
            sub_batch_number=next_sub_number,
            batch_type='shortage',
            shortage_reason=shortage_reason,
            total_orders=len(shortage_order_ids),
            spx_count=child_carrier_counts.get("SPX", 0),
            flash_count=child_carrier_counts.get("Flash", 0),
            lex_count=child_carrier_counts.get("LEX", 0),
            jt_count=child_carrier_counts.get("J&T", 0),
            other_count=sum(v for k, v in child_carrier_counts.items() if k not in ["SPX", "Flash", "LEX", "J&T"]),
            shop_summary=json.dumps(dict(child_shop_counts), ensure_ascii=False),
            locked=True,
            created_by_user_id=current_user().id,
            created_by_username=current_user().username,
            created_at=now_thai()
        )

        db.session.add(child_batch)

        # ย้าย Orders ที่มี Shortage ไป Child Batch
        for order in shortage_orders:
            order.batch_id = child_batch_id

        # ✨ NEW: อัปเดต ShortageQueue ให้ชี้ไปที่ Child Batch
        # เพื่อให้ปุ่ม "ดูเหตุผล" หา Shortage Queue ได้ถูกต้อง
        shortage_order_line_ids = [order.id for order in shortage_orders]
        if shortage_order_line_ids:
            ShortageQueue.query.filter(
                ShortageQueue.order_line_id.in_(shortage_order_line_ids)
            ).update(
                {ShortageQueue.original_batch_id: child_batch_id},
                synchronize_session=False
            )

        # อัปเดต Parent Batch - คำนวณ Carrier และ Shop Summary ใหม่
        parent_carrier_counts = defaultdict(int)
        parent_shop_counts = defaultdict(int)

        # ใช้ set เพื่อนับ order_id ที่ unique
        parent_counted_orders = set()

        for order in complete_orders:
            if order.order_id not in parent_counted_orders:
                parent_counted_orders.add(order.order_id)

                # นับ carrier
                carrier = order.carrier or "Other"
                parent_carrier_counts[carrier] += 1

                # นับ shop (ต้อง query Shop model เพื่อเอา name)
                shop = db.session.get(Shop, order.shop_id) if order.shop_id else None
                shop_name = shop.name if shop else "Unknown"
                parent_shop_counts[shop_name] += 1

        batch.total_orders = len(complete_order_ids)
        batch.spx_count = parent_carrier_counts.get("SPX", 0)
        batch.flash_count = parent_carrier_counts.get("Flash", 0)
        batch.lex_count = parent_carrier_counts.get("LEX", 0)
        batch.jt_count = parent_carrier_counts.get("J&T", 0)
        batch.other_count = sum(v for k, v in parent_carrier_counts.items() if k not in ["SPX", "Flash", "LEX", "J&T"])
        batch.shop_summary = json.dumps(dict(parent_shop_counts), ensure_ascii=False)

        db.session.commit()

        # Log Audit
        log = AuditLog(
            action="batch_split",
            user_id=current_user().id,
            username=current_user().username,
            details=json.dumps({
                "parent_batch": batch_id,
                "child_batch": child_batch_id,
                "shortage_orders": len(shortage_order_ids),
                "complete_orders": len(complete_order_ids),
                "reason": shortage_reason
            }),
            batch_id=batch_id
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"แยก Batch สำเร็จ",
            "parent_batch": {
                "batch_id": batch_id,
                "total_orders": len(complete_order_ids),
                "progress": 100  # Parent Batch มีแต่ Orders ที่ครบแล้ว
            },
            "child_batch": {
                "batch_id": child_batch_id,
                "sub_batch_number": next_sub_number,
                "total_orders": len(shortage_order_ids),
                "shortage_reason": shortage_reason
            }
        })

    @app.route("/api/batch/<batch_id>/family", methods=["GET"])
    @login_required
    def api_get_batch_family(batch_id):
        """
        ดึงข้อมูล Batch Family (Parent + All Children)
        Returns: Parent Batch + Children Batches with progress for each
        """
        # หา Batch
        batch = db.session.get(Batch, batch_id)
        if not batch:
            return jsonify({"success": False, "error": "ไม่พบ Batch"}), 404

        # ถ้าเป็น Child Batch → ไปหา Parent
        if batch.parent_batch_id:
            parent_batch = db.session.get(Batch, batch.parent_batch_id)
        else:
            parent_batch = batch

        # ดึง Children ทั้งหมด
        children = Batch.query.filter_by(
            parent_batch_id=parent_batch.batch_id
        ).order_by(Batch.sub_batch_number).all()

        # คำนวณ Progress แต่ละ Batch
        def get_batch_info(b):
            progress = calculate_batch_progress(b.batch_id)
            return {
                "batch_id": b.batch_id,
                "sub_batch_number": b.sub_batch_number,
                "batch_type": b.batch_type,
                "total_orders": b.total_orders,
                "progress_percent": progress["progress_percent"],
                "total_qty": progress["total_qty"],
                "completed_qty": progress["completed_qty"],
                "picked_qty": progress["picked_qty"],
                "handover_code": b.handover_code,
                "handover_confirmed": b.handover_confirmed,
                "shortage_reason": b.shortage_reason,
                "created_at": to_thai_be(b.created_at)
            }

        result = {
            "parent": get_batch_info(parent_batch),
            "children": [get_batch_info(child) for child in children],
            "total_children": len(children),
            "can_split_more": len(children) < 5
        }

        return jsonify({"success": True, "family": result})

    # ============================================================
    # Handover & Dispatch APIs
    # ============================================================

    @app.route("/api/handover/verify", methods=["POST"])
    @login_required
    def api_verify_handover():
        """Verify handover code and return batch information"""
        data = request.get_json()
        code = data.get("handover_code", "").strip().upper()

        if not code:
            return jsonify({"success": False, "error": "กรุณาระบุ Handover Code"}), 400

        # Find batch by handover code
        batch = Batch.query.filter_by(handover_code=code).first()

        if not batch:
            return jsonify({"success": False, "error": "ไม่พบรหัสส่งมอบนี้"}), 404

        # Check if already confirmed
        if batch.handover_confirmed:
            return jsonify({
                "success": False,
                "error": f"Batch นี้ยืนยันส่งมอบแล้ว เมื่อ {to_thai_be(batch.handover_confirmed_at)}",
                "already_confirmed": True
            }), 400

        # Get batch summary
        orders = OrderLine.query.filter_by(batch_id=batch.batch_id).all()
        total = len(orders)

        # Count orders by status
        ready_count = sum(1 for o in orders if o.dispatch_status == 'ready')
        partial_ready_count = sum(1 for o in orders if o.dispatch_status == 'partial_ready')
        dispatched_count = sum(1 for o in orders if o.dispatch_status == 'dispatched')

        # Parse shop summary
        try:
            shop_summary = json.loads(batch.shop_summary) if batch.shop_summary else {}
        except:
            shop_summary = {}

        return jsonify({
            "success": True,
            "batch": {
                "batch_id": batch.batch_id,
                "platform": batch.platform,
                "run_no": batch.run_no,
                "batch_date": to_be_date_str(batch.batch_date),
                "total_orders": batch.total_orders,
                "carrier_summary": {
                    "SPX": batch.spx_count,
                    "Flash": batch.flash_count,
                    "LEX": batch.lex_count,
                    "J&T": batch.jt_count,
                    "Other": batch.other_count
                },
                "shop_summary": shop_summary,
                "status_summary": {
                    "ready": ready_count,
                    "partial_ready": partial_ready_count,
                    "dispatched": dispatched_count,
                    "total": total
                },
                "handover_code": code,
                "generated_by": batch.handover_code_generated_by_username,
                "generated_at": to_thai_be(batch.handover_code_generated_at)
            }
        })

    @app.route("/api/handover/confirm", methods=["POST"])
    @login_required
    def api_confirm_handover():
        """Confirm handover and dispatch all ready orders in batch"""
        data = request.get_json()
        code = data.get("handover_code", "").strip().upper()
        notes = data.get("notes", "").strip()

        if not code:
            return jsonify({"success": False, "error": "กรุณาระบุ Handover Code"}), 400

        # Find batch by handover code
        batch = Batch.query.filter_by(handover_code=code).first()

        if not batch:
            return jsonify({"success": False, "error": "ไม่พบรหัสส่งมอบนี้"}), 404

        # Check if already confirmed
        if batch.handover_confirmed:
            return jsonify({
                "success": False,
                "error": f"Batch นี้ยืนยันส่งมอบแล้ว เมื่อ {to_thai_be(batch.handover_confirmed_at)}"
            }), 400

        # Get all orders and dispatch ready ones
        cu = current_user()
        orders = OrderLine.query.filter_by(batch_id=batch.batch_id).all()
        dispatched_count = 0
        now = now_thai()

        for order in orders:
            # Dispatch orders that are "ready" or "partial_ready"
            if order.dispatch_status in ["ready", "partial_ready"]:
                order.dispatch_status = "dispatched"
                order.dispatched_at = now
                order.dispatched_by_user_id = cu.id
                order.dispatched_by_username = cu.username
                dispatched_count += 1

        # Update batch
        batch.handover_confirmed = True
        batch.handover_confirmed_at = now
        batch.handover_confirmed_by_user_id = cu.id
        batch.handover_confirmed_by_username = cu.username
        batch.handover_notes = notes

        # ✅ Phase 0: Release Stock Reservation เมื่อยืนยันส่งมอบแล้ว
        # Logic: released_qty = picked_qty + shortage_qty
        # - picked_qty: ของที่หยิบได้จริง (ออกจากคลังแล้ว)
        # - shortage_qty: ของที่ขาด (ไม่มีในสต็อกตั้งแต่แรก หรือถูก resolve แล้ว)
        released_skus = {}
        for order in orders:
            sku = order.sku
            # ✅ FIX: คำนวณ released_qty = picked_qty + shortage_qty
            picked = order.picked_qty or 0
            shortage = order.shortage_qty or 0
            released = picked + shortage

            if released > 0:
                if sku not in released_skus:
                    released_skus[sku] = 0
                released_skus[sku] += released

        # Release reservation for each SKU (ก่อน commit เพื่อให้อยู่ใน transaction เดียวกัน)
        for sku, qty_released in released_skus.items():
            release_stock_reservation(batch.batch_id, sku, qty_released, reason="handover_confirmed")

        # ✅ Commit ทั้ง handover update และ stock release ในครั้งเดียว
        db.session.commit()

        # Audit log
        log = AuditLog(
            action="confirm_handover",
            user_id=cu.id,
            username=cu.username,
            details=json.dumps({
                "batch_id": batch.batch_id,
                "handover_code": code,
                "dispatched_count": dispatched_count,
                "notes": notes
            }),
            batch_id=batch.batch_id,
            order_count=dispatched_count
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"ยืนยันส่งมอบสำเร็จ - ส่งแล้ว {dispatched_count} รายการ",
            "dispatched_count": dispatched_count,
            "total_orders": len(orders)
        })

    @app.route("/scan-handover")
    @login_required
    def scan_handover():
        """Page for scanning handover code to confirm batch dispatch"""
        return render_template("scan_handover.html")

    @app.route("/batch/<batch_id>/print-handover")
    @login_required
    def batch_print_handover(batch_id):
        """Print handover sheet with QR code for courier sign-off"""
        batch = db.session.get(Batch, batch_id)

        if not batch:
            flash("ไม่พบ Batch", "error")
            return redirect(url_for('batch_list'))

        if not batch.handover_code:
            flash("ไม่พบรหัสส่งมอบ กรุณาสร้างรหัสก่อน", "error")
            return redirect(url_for('batch_detail', batch_id=batch_id))

        # Parse shop summary
        try:
            shop_summary = json.loads(batch.shop_summary) if batch.shop_summary else {}
        except:
            shop_summary = {}

        # Get carrier summary
        carrier_summary = {
            "SPX": batch.spx_count,
            "Flash": batch.flash_count,
            "LEX": batch.lex_count,
            "J&T": batch.jt_count,
            "Other": batch.other_count
        }

        return render_template(
            'batch_print_handover.html',
            batch=batch,
            carrier_summary=carrier_summary,
            shop_summary=shop_summary,
            print_time=now_thai()
        )

    # ==========================================
    # End of Handover Code System Routes
    # ==========================================

    @app.route("/export_picking.xlsx")
    @login_required
    def export_picking_excel():
        platform = normalize_platform(request.args.get("platform"))
        shop_id = request.args.get("shop_id")
        logistic = request.args.get("logistic")

        filters = {"platform": platform if platform else None, "shop_id": int(shop_id) if shop_id else None, "import_date": None}
        rows, _ = compute_allocation(db.session, filters)

        safe_rows = []
        for r in rows:
            r = dict(r)
            if "stock_qty" not in r:
                sku = (r.get("sku") or "").strip()
                stock_qty = 0
                if sku:
                    prod = Product.query.filter_by(sku=sku).first()
                    if prod and hasattr(prod, "stock_qty"):
                        try:
                            stock_qty = int(prod.stock_qty or 0)
                        except Exception:
                            stock_qty = 0
                    else:
                        st = Stock.query.filter_by(sku=sku).first()
                        stock_qty = int(st.qty) if st and st.qty is not None else 0
                r["stock_qty"] = stock_qty
            r["accepted"] = bool(r.get("accepted", False))
            r["logistic"] = r.get("logistic") or r.get("logistic_type") or "Unknown"
            safe_rows.append(r)

        if logistic:
            safe_rows = [r for r in safe_rows if (r.get("logistic") or "").lower().find(logistic.lower()) >= 0]

        items = _aggregate_picking(safe_rows)

        # นับครั้งพิมพ์รวมของชุดงาน (ใช้ MAX)
        valid_rows = [r for r in safe_rows if r.get("accepted") and r.get("allocation_status") in ("ACCEPTED", "READY_ACCEPT")]
        order_ids = sorted({(r.get("order_id") or "").strip() for r in valid_rows if r.get("order_id")})
        print_counts_pick = _get_print_counts_local(order_ids, "picking")
        print_count_overall = max(print_counts_pick.values()) if print_counts_pick else 0

        # แปลงชื่อร้าน
        shop_name = ""
        if shop_id:
            s = Shop.query.get(int(shop_id))
            if s:
                shop_name = f"{s.platform} • {s.name}"

        # เติม platform/shop/logistic ใน items เพื่อให้ไฟล์มีข้อมูลครบ
        for it in items:
            it["platform"] = platform or ""
            it["shop_name"] = shop_name or ""
            it["logistic"] = logistic or ""

        df = pd.DataFrame([{
            "แพลตฟอร์ม": it["platform"],
            "ร้าน": it["shop_name"],
            "SKU": it["sku"],
            "Brand": it["brand"],
            "สินค้า": it["model"],
            "ต้องหยิบ": it["need_qty"],
            "สต็อก": it["stock_qty"],
            "ขาด": it["shortage"],
            "คงเหลือหลังหยิบ": it["remain_after_pick"],
            "ประเภทขนส่ง": it["logistic"],
            "พิมพ์แล้ว (ครั้ง)": print_count_overall,
        } for it in items])

        out = BytesIO()
        with pd.ExcelWriter(out, engine="xlsxwriter") as w:
            df.to_excel(w, index=False, sheet_name="Picking List")
        out.seek(0)
        return send_file(out, as_attachment=True, download_name="picking_list.xlsx")

    # -----------------------
    # Admin clear
    # -----------------------
    @app.route("/admin/clear", methods=["GET"])
    @login_required
    def admin_clear():
        """Show admin clear page with checkboxes"""
        return render_template("clear_confirm.html")

    @app.route("/admin/test-stock", methods=["GET"])
    @login_required
    def admin_test_stock():
        """Test stock API page"""
        return render_template("test_stock.html")

    @app.route("/api/admin/preview", methods=["POST"])
    @login_required
    def api_admin_preview():
        """Preview data before deletion"""
        data = request.get_json()
        preview_type = data.get("type")

        try:
            today = now_thai().date()
            html = ""

            if preview_type == "orders":
                # Orders preview
                total = OrderLine.query.count()
                today_count = OrderLine.query.filter(OrderLine.import_date == today).count()
                week_ago = today - timedelta(days=7)
                week_count = OrderLine.query.filter(OrderLine.import_date >= week_ago).count()
                month_ago = today - timedelta(days=30)
                month_count = OrderLine.query.filter(OrderLine.import_date >= month_ago).count()

                # Get recent 5 orders
                recent = OrderLine.query.order_by(OrderLine.import_date.desc()).limit(5).all()

                html = f"""
                <div class="alert alert-info">
                  <h6><i data-lucide="info"></i> สรุปข้อมูลออเดอร์</h6>
                  <ul class="mb-0">
                    <li>ออเดอร์วันนี้: <strong>{today_count}</strong> รายการ</li>
                    <li>ออเดอร์สัปดาห์นี้: <strong>{week_count}</strong> รายการ</li>
                    <li>ออเดอร์เดือนนี้: <strong>{month_count}</strong> รายการ</li>
                    <li>ออเดอร์ทั้งหมด: <strong>{total}</strong> รายการ</li>
                  </ul>
                </div>

                <h6 class="mt-3">ออเดอร์ล่าสุด 5 รายการ:</h6>
                <div class="table-responsive">
                  <table class="table table-sm table-striped">
                    <thead>
                      <tr>
                        <th>Tracking</th>
                        <th>Platform</th>
                        <th>Shop</th>
                        <th>วันที่นำเข้า</th>
                        <th>สถานะ</th>
                      </tr>
                    </thead>
                    <tbody>
                """

                for order in recent:
                    # ✅ แก้ไข: tracking_id → tracking_number
                    html += f"""
                      <tr>
                        <td><small>{order.tracking_number or '-'}</small></td>
                        <td><span class="badge bg-secondary">{order.platform or '-'}</span></td>
                        <td><small>{order.shop_id or '-'}</small></td>
                        <td><small>{order.import_date or '-'}</small></td>
                        <td><span class="badge bg-info">{order.batch_status or 'pending'}</span></td>
                      </tr>
                    """

                html += """
                    </tbody>
                  </table>
                </div>
                <p class="text-muted small mt-2">แสดงเพียง 5 รายการล่าสุด</p>
                """

            elif preview_type == "batches":
                # Batches preview
                total = Batch.query.count()
                today_count = Batch.query.filter(db.func.date(Batch.created_at) == today).count()
                unlocked_count = Batch.query.filter(Batch.locked == False).count()  # ✅ แก้ไข: is_locked → locked
                completed_count = Batch.query.filter(Batch.handover_confirmed == True).count()

                recent = Batch.query.order_by(Batch.created_at.desc()).limit(5).all()

                html = f"""
                <div class="alert alert-info">
                  <h6><i data-lucide="info"></i> สรุปข้อมูล Batch</h6>
                  <ul class="mb-0">
                    <li>Batch วันนี้: <strong>{today_count}</strong> Batch</li>
                    <li>Batch ที่ Unlocked: <strong>{unlocked_count}</strong> Batch</li>
                    <li>Batch ที่ส่งมอบแล้ว: <strong>{completed_count}</strong> Batch</li>
                    <li>Batch ทั้งหมด: <strong>{total}</strong> Batch</li>
                  </ul>
                </div>

                <h6 class="mt-3">Batch ล่าสุด 5 รายการ:</h6>
                <div class="table-responsive">
                  <table class="table table-sm table-striped">
                    <thead>
                      <tr>
                        <th>Batch ID</th>
                        <th>จำนวนออเดอร์</th>
                        <th>สถานะ</th>
                        <th>ส่งมอบ</th>
                        <th>สร้างเมื่อ</th>
                      </tr>
                    </thead>
                    <tbody>
                """

                for batch in recent:
                    locked = "🔒 Locked" if batch.locked else "🔓 Unlocked"  # ✅ แก้ไข: is_locked → locked
                    handover = "✅ ส่งแล้ว" if batch.handover_confirmed else "⏳ ยังไม่ส่ง"
                    html += f"""
                      <tr>
                        <td><small><strong>{batch.batch_id}</strong></small></td>
                        <td>{batch.total_orders}</td>
                        <td><span class="badge bg-secondary">{locked}</span></td>
                        <td><span class="badge bg-info">{handover}</span></td>
                        <td><small>{batch.created_at.strftime('%Y-%m-%d %H:%M') if batch.created_at else '-'}</small></td>
                      </tr>
                    """

                html += """
                    </tbody>
                  </table>
                </div>
                <p class="text-muted small mt-2">แสดงเพียง 5 รายการล่าสุด</p>
                """

            elif preview_type == "products":
                # Products preview
                products_count = Product.query.count()
                stock_count = Stock.query.count()

                products = Product.query.limit(5).all()

                html = f"""
                <div class="alert alert-info">
                  <h6><i data-lucide="info"></i> สรุปข้อมูลสินค้าและสต็อก</h6>
                  <ul class="mb-0">
                    <li>สินค้าทั้งหมด: <strong>{products_count}</strong> รายการ</li>
                    <li>สต็อกทั้งหมด: <strong>{stock_count}</strong> รายการ</li>
                  </ul>
                </div>

                <h6 class="mt-3">สินค้า 5 รายการแรก:</h6>
                <div class="table-responsive">
                  <table class="table table-sm table-striped">
                    <thead>
                      <tr>
                        <th>SKU</th>
                        <th>ชื่อสินค้า</th>
                        <th>ตำแหน่ง</th>
                      </tr>
                    </thead>
                    <tbody>
                """

                for product in products:
                    # ✅ แก้ไข: Product model ไม่มี product_name และ location
                    product_name = f"{product.brand or ''} {product.model or ''}".strip() or '-'
                    html += f"""
                      <tr>
                        <td><small><strong>{product.sku}</strong></small></td>
                        <td><small>{product_name}</small></td>
                        <td><small>-</small></td>
                      </tr>
                    """

                html += """
                    </tbody>
                  </table>
                </div>
                <p class="text-muted small mt-2">แสดงเพียง 5 รายการแรก</p>
                """

            elif preview_type == "audit_logs":
                # Audit logs preview
                total = AuditLog.query.count()
                thirty_days_ago = now_thai() - timedelta(days=30)
                old_count = AuditLog.query.filter(AuditLog.timestamp < thirty_days_ago).count()

                recent = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

                html = f"""
                <div class="alert alert-info">
                  <h6><i data-lucide="info"></i> สรุปข้อมูล Audit Logs</h6>
                  <ul class="mb-0">
                    <li>Logs เก่ากว่า 30 วัน: <strong>{old_count}</strong> รายการ</li>
                    <li>Logs ทั้งหมด: <strong>{total}</strong> รายการ</li>
                  </ul>
                </div>

                <h6 class="mt-3">Audit Logs ล่าสุด 10 รายการ:</h6>
                <div class="table-responsive">
                  <table class="table table-sm table-striped">
                    <thead>
                      <tr>
                        <th>เวลา</th>
                        <th>ผู้ใช้</th>
                        <th>Action</th>
                        <th>รายละเอียด</th>
                      </tr>
                    </thead>
                    <tbody>
                """

                for log in recent:
                    timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '-'
                    details = (log.details[:50] + '...') if log.details and len(log.details) > 50 else (log.details or '-')
                    html += f"""
                      <tr>
                        <td><small>{timestamp}</small></td>
                        <td><small>{log.username or '-'}</small></td>
                        <td><span class="badge bg-primary">{log.action}</span></td>
                        <td><small>{details}</small></td>
                      </tr>
                    """

                html += """
                    </tbody>
                  </table>
                </div>
                <p class="text-muted small mt-2">แสดงเพียง 10 รายการล่าสุด</p>
                """

            elif preview_type == "shortage_queue":
                # ✅ Shortage Queue preview
                total = ShortageQueue.query.count()
                pending_count = ShortageQueue.query.filter_by(status='pending').count()
                resolved_count = ShortageQueue.query.filter(
                    ShortageQueue.status.in_(['resolved', 'cancelled', 'replaced'])
                ).count()

                recent = ShortageQueue.query.order_by(ShortageQueue.created_at.desc()).limit(10).all()

                html = f"""
                <div class="alert alert-info">
                  <h6><i data-lucide="info"></i> สรุปข้อมูล Shortage Queue</h6>
                  <ul class="mb-0">
                    <li>รอจัดการ (Pending): <strong>{pending_count}</strong> รายการ</li>
                    <li>จัดการแล้ว (Resolved): <strong>{resolved_count}</strong> รายการ</li>
                    <li>ทั้งหมด: <strong>{total}</strong> รายการ</li>
                  </ul>
                </div>

                <h6 class="mt-3">Shortage Queue ล่าสุด 10 รายการ:</h6>
                <div class="table-responsive">
                  <table class="table table-sm table-striped">
                    <thead>
                      <tr>
                        <th>Order ID</th>
                        <th>SKU</th>
                        <th>Batch</th>
                        <th>จำนวนขาด</th>
                        <th>สถานะ</th>
                        <th>สร้างเมื่อ</th>
                      </tr>
                    </thead>
                    <tbody>
                """

                for shortage in recent:
                    created_at = shortage.created_at.strftime('%Y-%m-%d %H:%M') if shortage.created_at else '-'
                    status_badge_map = {
                        'pending': 'warning',
                        'waiting_stock': 'info',
                        'resolved': 'success',
                        'cancelled': 'secondary',
                        'replaced': 'primary'
                    }
                    status_badge = status_badge_map.get(shortage.status, 'secondary')

                    html += f"""
                      <tr>
                        <td><small>{shortage.order_id}</small></td>
                        <td><small><code>{shortage.sku}</code></small></td>
                        <td><small>{shortage.original_batch_id or '-'}</small></td>
                        <td><strong class="text-danger">{shortage.qty_shortage}</strong></td>
                        <td><span class="badge bg-{status_badge}">{shortage.status}</span></td>
                        <td><small>{created_at}</small></td>
                      </tr>
                    """

                html += """
                    </tbody>
                  </table>
                </div>
                <p class="text-muted small mt-2">แสดงเพียง 10 รายการล่าสุด</p>
                """

            else:
                return jsonify({"success": False, "error": "Invalid preview type"}), 400

            return jsonify({"success": True, "html": html})

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/admin/stock-list", methods=["GET"])
    @login_required
    def api_admin_stock_list():
        """API สำหรับดึงข้อมูลสต็อกพร้อม Pagination และ Filters"""
        try:
            # Get query parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 100))
            filter_type = request.args.get('filter', 'all')  # all, low_stock, out_of_stock
            search = request.args.get('search', '').strip()

            # Build query - Join Stock with Product
            query = db.session.query(
                Stock.sku,
                Stock.qty,
                Product.brand,
                Product.model
            ).outerjoin(Product, Stock.sku == Product.sku)

            # Apply filters
            if filter_type == 'low_stock':
                query = query.filter(Stock.qty <= 3, Stock.qty > 0)
            elif filter_type == 'out_of_stock':
                query = query.filter(Stock.qty == 0)

            # Apply search
            if search:
                query = query.filter(
                    db.or_(
                        Stock.sku.like(f'%{search}%'),
                        Product.brand.like(f'%{search}%'),
                        Product.model.like(f'%{search}%')
                    )
                )

            # Order by qty ascending (show low stock first) then by SKU
            query = query.order_by(Stock.qty.asc(), Stock.sku.asc())

            # Paginate
            total = query.count()
            stocks = query.offset((page - 1) * per_page).limit(per_page).all()

            # Format results
            stock_list = []
            for stock in stocks:
                product_name = f"{stock.brand or ''} {stock.model or ''}".strip() or '-'
                is_low_stock = stock.qty <= 3 and stock.qty > 0
                is_out_of_stock = stock.qty == 0

                stock_list.append({
                    'sku': stock.sku,
                    'product_name': product_name,
                    'stock': stock.qty,
                    'location': '-',  # ยังไม่มีในระบบ
                    'is_low_stock': is_low_stock,
                    'is_out_of_stock': is_out_of_stock
                })

            # Calculate summary
            total_products = Stock.query.count()
            low_stock_count = Stock.query.filter(Stock.qty <= 3, Stock.qty > 0).count()
            out_of_stock_count = Stock.query.filter(Stock.qty == 0).count()

            return jsonify({
                'success': True,
                'stocks': stock_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': (total + per_page - 1) // per_page
                },
                'summary': {
                    'total_products': total_products,
                    'low_stock': low_stock_count,
                    'out_of_stock': out_of_stock_count,
                    'in_stock': total_products - out_of_stock_count
                }
            })

        except Exception as e:
            print(f"ERROR in /api/admin/stock-list: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route("/api/admin/export-stock-excel", methods=["GET"])
    @login_required
    def api_admin_export_stock_excel():
        """Export Stock to Excel"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from io import BytesIO

            # Get filter parameters
            filter_type = request.args.get('filter', 'all')
            search = request.args.get('search', '').strip()

            # Build query
            query = db.session.query(
                Stock.sku,
                Stock.qty,
                Product.brand,
                Product.model
            ).outerjoin(Product, Stock.sku == Product.sku)

            # Apply filters
            if filter_type == 'low_stock':
                query = query.filter(Stock.qty <= 3, Stock.qty > 0)
            elif filter_type == 'out_of_stock':
                query = query.filter(Stock.qty == 0)

            # Apply search
            if search:
                query = query.filter(
                    db.or_(
                        Stock.sku.like(f'%{search}%'),
                        Product.brand.like(f'%{search}%'),
                        Product.model.like(f'%{search}%')
                    )
                )

            # Order by qty ascending
            stocks = query.order_by(Stock.qty.asc(), Stock.sku.asc()).all()

            # Create workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Stock Report"

            # Header styling
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            header_alignment = Alignment(horizontal="center", vertical="center")

            # Headers
            headers = ["#", "SKU", "ชื่อสินค้า", "Stock คงเหลือ", "ตำแหน่ง", "สถานะ"]
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = header
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment

            # Data rows
            for idx, stock in enumerate(stocks, 1):
                product_name = f"{stock.brand or ''} {stock.model or ''}".strip() or '-'

                # Status
                if stock.qty == 0:
                    status = "หมดสต็อก"
                elif stock.qty <= 3:
                    status = "ใกล้หมด"
                else:
                    status = "ปกติ"

                ws.cell(row=idx + 1, column=1, value=idx)
                ws.cell(row=idx + 1, column=2, value=stock.sku)
                ws.cell(row=idx + 1, column=3, value=product_name)
                ws.cell(row=idx + 1, column=4, value=stock.qty)
                ws.cell(row=idx + 1, column=5, value="-")
                ws.cell(row=idx + 1, column=6, value=status)

                # Highlight low stock rows
                if stock.qty == 0:
                    fill = PatternFill(start_color="FFB6C1", end_color="FFB6C1", fill_type="solid")
                elif stock.qty <= 3:
                    fill = PatternFill(start_color="FFF4CE", end_color="FFF4CE", fill_type="solid")
                else:
                    fill = None

                if fill:
                    for col in range(1, 7):
                        ws.cell(row=idx + 1, column=col).fill = fill

            # Adjust column widths
            ws.column_dimensions['A'].width = 6
            ws.column_dimensions['B'].width = 25
            ws.column_dimensions['C'].width = 60
            ws.column_dimensions['D'].width = 15
            ws.column_dimensions['E'].width = 20
            ws.column_dimensions['F'].width = 12

            # Save to BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            # Return file
            from flask import send_file
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"stock_report_{timestamp}.xlsx"

            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )

        except Exception as e:
            print(f"ERROR in /api/admin/export-stock-excel: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route("/api/admin/delete-multiple", methods=["POST"])
    @login_required
    def api_admin_delete_multiple():
        """Execute multiple deletions with password verification"""
        data = request.get_json()
        scopes = data.get("scopes", [])
        password = data.get("password")

        # Verify password
        if password != "vnixdelete":
            return jsonify({"success": False, "error": "รหัสผ่านไม่ถูกต้อง"}), 403

        if not scopes or len(scopes) == 0:
            return jsonify({"success": False, "error": "กรุณาเลือกข้อมูลที่ต้องการลบ"}), 400

        try:
            cu = current_user()
            total_deleted = 0
            messages = []
            today = now_thai().date()

            for scope in scopes:
                deleted_count = 0

                if scope == "orders_today":
                    deleted_count = OrderLine.query.filter(OrderLine.import_date == today).delete()
                    messages.append(f"ลบออเดอร์ของวันนี้: {deleted_count} รายการ")

                elif scope == "orders_week":
                    week_ago = today - timedelta(days=7)
                    deleted_count = OrderLine.query.filter(OrderLine.import_date >= week_ago).delete()
                    messages.append(f"ลบออเดอร์สัปดาห์นี้: {deleted_count} รายการ")

                elif scope == "orders_month":
                    month_ago = today - timedelta(days=30)
                    deleted_count = OrderLine.query.filter(OrderLine.import_date >= month_ago).delete()
                    messages.append(f"ลบออเดอร์เดือนนี้: {deleted_count} รายการ")

                elif scope == "orders_all":
                    deleted_count = OrderLine.query.delete()
                    messages.append(f"ลบออเดอร์ทั้งหมด: {deleted_count} รายการ")

                elif scope in ["batches_today", "batches_week", "batches_unlocked", "batches_completed", "batches_all"]:
                    # ⚠️ WARNING: Batch Deletion is DISABLED for production safety
                    # Deleting batches can cause:
                    # 1. reserved_qty leaks (stock incorrectly reserved)
                    # 2. Loss of audit trail
                    # 3. Data inconsistency
                    #
                    # If you need to clean up batches, use migration script instead:
                    #   python migrations/run_phase0_migration.py
                    #
                    messages.append(
                        "❌ การลบ Batch ถูกปิดใช้งานเพื่อความปลอดภัย\n\n"
                        "เหตุผล:\n"
                        "- ป้องกัน reserved_qty ค้างในระบบ\n"
                        "- รักษา audit trail\n"
                        "- หลีกเลี่ยงข้อมูลไม่สอดคล้อง\n\n"
                        "หากต้องการทำความสะอาด Batch:\n"
                        "1. ใช้ Unlock Batch แทน\n"
                        "2. รัน migration: python migrations/run_phase0_migration.py\n"
                        "3. ติดต่อ Admin"
                    )
                    continue  # Skip to next scope

                elif scope == "products_all":
                    deleted_count = Product.query.delete()
                    messages.append(f"ลบข้อมูลสินค้า: {deleted_count} รายการ")

                elif scope == "stock_all":
                    deleted_count = Stock.query.delete()
                    messages.append(f"ลบข้อมูลสต็อก: {deleted_count} รายการ")

                elif scope == "audit_logs_import_orders":
                    deleted_count = AuditLog.query.filter(AuditLog.action == "import_orders").delete()
                    messages.append(f"ลบ Log การนำเข้า Orders: {deleted_count} รายการ")

                elif scope == "audit_logs_import_products":
                    deleted_count = AuditLog.query.filter(AuditLog.action == "import_products").delete()
                    messages.append(f"ลบ Log การนำเข้าสินค้า: {deleted_count} รายการ")

                elif scope == "audit_logs_import_stock":
                    deleted_count = AuditLog.query.filter(AuditLog.action == "import_stock").delete()
                    messages.append(f"ลบ Log การนำเข้าสต็อก: {deleted_count} รายการ")

                elif scope == "audit_logs_import_sales":
                    deleted_count = AuditLog.query.filter(AuditLog.action == "import_sales").delete()
                    messages.append(f"ลบ Log การนำเข้าสั่งขาย: {deleted_count} รายการ")

                elif scope == "audit_logs":
                    deleted_count = AuditLog.query.delete()
                    messages.append(f"ลบ Audit Logs: {deleted_count} รายการ")

                elif scope == "audit_logs_old":
                    thirty_days_ago = now_thai() - timedelta(days=30)
                    deleted_count = AuditLog.query.filter(AuditLog.timestamp < thirty_days_ago).delete()
                    messages.append(f"ลบ Audit Logs เก่า: {deleted_count} รายการ")

                elif scope == "shortage_queue_pending":
                    deleted_count = ShortageQueue.query.filter_by(status='pending').delete()
                    messages.append(f"ลบ Shortage Queue (Pending): {deleted_count} รายการ")

                elif scope == "shortage_queue_resolved":
                    deleted_count = ShortageQueue.query.filter(
                        ShortageQueue.status.in_(['resolved', 'cancelled', 'replaced'])
                    ).delete()
                    messages.append(f"ลบ Shortage Queue (Resolved): {deleted_count} รายการ")

                elif scope == "shortage_queue_all":
                    deleted_count = ShortageQueue.query.delete()
                    messages.append(f"ลบ Shortage Queue ทั้งหมด: {deleted_count} รายการ")

                elif scope == "all_data":
                    OrderLine.query.delete()
                    Batch.query.delete()
                    Product.query.delete()
                    Stock.query.delete()
                    AuditLog.query.delete()
                    ShortageQueue.query.delete()  # ✅ Add ShortageQueue to all_data deletion
                    deleted_count = 9999  # Special marker
                    messages.append("ลบข้อมูลทั้งหมดในระบบ")

                total_deleted += deleted_count

            # Commit all changes at once
            db.session.commit()

            # Create audit log
            log = AuditLog(
                user_id=cu.id,
                username=cu.username,
                action="admin_delete_multiple",
                details=f"Admin delete multiple: {', '.join(messages)} (scopes: {','.join(scopes)})"
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "<br>".join(messages),
                "total_deleted": total_deleted
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500

    # =============================
    # QR Code Generation
    # =============================

    @app.route("/qr/<path:text>")
    def generate_qr(text):
        """
        Generate QR Code image for any text
        Usage: /qr/BATCH-ID or /qr/SKU-001
        """
        # Create QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')

    # =============================
    # Warehouse Scanning Routes
    # =============================

    # -----------------------
    # Scan Batch (รับงาน)
    # -----------------------
    @app.route("/scan/batch")
    @login_required
    def scan_batch():
        """หน้าสแกน Batch QR เพื่อรับงาน"""
        return render_template("scan_batch.html")

    @app.route("/api/quick-assign/batches")
    @login_required
    def api_quick_assign_batches():
        """API สำหรับดึง Batch ที่ยังไม่เสร็จ (Quick Assign)"""
        # หา Batch ที่ยังไม่ส่งมอบ (handover_confirmed = False)
        batches = Batch.query.filter_by(
            handover_confirmed=False
        ).order_by(Batch.created_at.desc()).limit(10).all()

        result = []
        for batch in batches:
            # ✅ ใช้ calculate_batch_progress() เพื่อความสอดคล้อง
            progress_data = calculate_batch_progress(batch.batch_id)

            result.append({
                "batch_id": batch.batch_id,
                "platform": batch.platform,
                "run_no": batch.run_no,
                "total_orders": batch.total_orders,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "created_by": batch.created_by_username,
                # ✅ เพิ่ม Progress (Quantity-based)
                "progress_percent": progress_data["progress_percent"],
                "total_qty": progress_data["total_qty"],
                "completed_qty": progress_data["completed_qty"],
                "picked_qty": progress_data["picked_qty"]
            })

        return jsonify({"success": True, "batches": result})

    @app.route("/api/scan/batch", methods=["POST"])
    @login_required
    def api_scan_batch():
        """API สำหรับสแกน Batch ID และรับงาน"""
        data = request.get_json()
        batch_id = data.get("batch_id", "").strip()

        if not batch_id:
            return jsonify({"success": False, "error": "กรุณาระบุ Batch ID"}), 400

        # ตรวจสอบว่า Batch มีอยู่จริง
        batch = Batch.query.filter_by(batch_id=batch_id).first()
        if not batch:
            return jsonify({"success": False, "error": f"ไม่พบ Batch ID: {batch_id}"}), 404

        # นับจำนวนออเดอร์ใน Batch
        orders = OrderLine.query.filter_by(batch_id=batch_id).all()
        if not orders:
            return jsonify({"success": False, "error": "Batch นี้ไม่มีออเดอร์"}), 404

        cu = current_user()
        now = now_thai()

        # รับงาน (Accept Batch) - อัปเดตทุก OrderLine ใน Batch
        for order in orders:
            if not order.accepted:
                order.accepted = True
                order.accepted_at = now
                order.accepted_by_user_id = cu.id
                order.accepted_by_username = cu.username

        db.session.commit()

        # บันทึก Audit Log
        log_audit(
            action="scan_batch_accept",
            details={
                "batch_id": batch_id,
                "platform": batch.platform,
                "total_orders": len(set(o.order_id for o in orders)),
                "accepted_by": cu.username
            },
            batch_id=batch_id,
            order_count=len(orders)
        )

        return jsonify({
            "success": True,
            "batch_id": batch_id,
            "platform": batch.platform,
            "total_orders": batch.total_orders,
            "accepted_by": cu.username,
            "accepted_at": now.isoformat()
        })

    # -----------------------
    # Scan SKU (หยิบของ)
    # -----------------------
    @app.route("/scan/sku")
    @login_required
    def scan_sku():
        """หน้าสแกน SKU เพื่อหยิบสินค้า"""
        return render_template("scan_sku.html")

    @app.route("/api/quick-assign/skus")
    @login_required
    def api_quick_assign_skus():
        """API สำหรับดึง Batch และ SKU ที่ยังต้องหยิบ (Quick Assign)"""
        cu = current_user()

        # หา Batch ที่ user รับงานแล้ว และยังมี SKU ที่ต้องหยิบ
        from sqlalchemy import func

        # Query: หา SKU ที่ยังต้องหยิบ (picked_qty < qty)
        pending_skus = db.session.query(
            OrderLine.batch_id,
            OrderLine.sku,
            func.sum(OrderLine.qty).label('total_need'),
            func.sum(OrderLine.picked_qty).label('total_picked'),
            func.max(Product.brand).label('brand'),
            func.max(Product.model).label('model'),
            func.max(OrderLine.item_name).label('item_name')
        ).outerjoin(
            Product, OrderLine.sku == Product.sku
        ).filter(
            OrderLine.accepted == True,
            OrderLine.accepted_by_user_id == cu.id,  # รับงานโดย user นี้
            OrderLine.dispatch_status != "dispatched"
        ).group_by(
            OrderLine.batch_id, OrderLine.sku
        ).having(
            func.sum(OrderLine.picked_qty) < func.sum(OrderLine.qty)  # ยังหยิบไม่ครบ
        ).order_by(
            OrderLine.batch_id.desc(), OrderLine.sku
        ).limit(20).all()

        # จัดกลุ่มตาม Batch
        from collections import defaultdict
        batches_dict = defaultdict(list)

        for row in pending_skus:
            batch_id = row.batch_id
            batches_dict[batch_id].append({
                "sku": row.sku,
                "brand": row.brand or "",
                "model": row.model or "",
                "item_name": row.item_name or "",
                "total_need": row.total_need or 0,
                "total_picked": row.total_picked or 0,
                "remaining": (row.total_need or 0) - (row.total_picked or 0)
            })

        # สร้าง result
        result = []
        for batch_id, skus in batches_dict.items():
            batch = Batch.query.filter_by(batch_id=batch_id).first()
            result.append({
                "batch_id": batch_id,
                "platform": batch.platform if batch else "",
                "run_no": batch.run_no if batch else 0,
                "skus": skus
            })

        return jsonify({"success": True, "batches": result})

    @app.route("/api/scan/sku", methods=["POST"])
    @login_required
    def api_scan_sku():
        """API สำหรับสแกน SKU และแสดงข้อมูล Need/Picked/Remaining (รองรับ Partial Picking)"""
        try:
            data = request.get_json()
            sku = data.get("sku", "").strip()

            if not sku:
                return jsonify({"success": False, "error": "กรุณาระบุ SKU"}), 400

            # หาออเดอร์ที่ยังไม่ dispatch และต้องการ SKU นี้
            orders = OrderLine.query.filter(
                OrderLine.sku == sku,
                OrderLine.dispatch_status != "dispatched",
                OrderLine.accepted == True
            ).all()

            if not orders:
                return jsonify({
                    "success": False,
                    "error": f"ไม่พบออเดอร์ที่ต้องการ SKU: {sku} (หรือยังไม่รับงาน)"
                }), 404

            # ✅ Phase 2.4: Check if any batch is locked (non-admin users cannot pick from locked batches)
            batch_ids = set(o.batch_id for o in orders if o.batch_id)
            for batch_id in batch_ids:
                allowed, error_msg = check_batch_locked(batch_id, "หยิบสินค้า")
                if not allowed:
                    return jsonify({"success": False, "error": error_msg}), 403

            # คำนวณ Need / Picked / Remaining / Shortage (with fallback for missing column)
            total_need = sum(o.qty for o in orders)
            total_picked = sum(o.picked_qty or 0 for o in orders)
            total_shortage = sum(getattr(o, 'shortage_qty', 0) or 0 for o in orders)
            total_remaining = total_need - total_picked

            # ดึงข้อมูลสินค้า
            product = Product.query.filter_by(sku=sku).first()
            stock = Stock.query.filter_by(sku=sku).first()
            stock_qty = stock.qty if stock else 0

            # ⚠️ เช็คว่ามี Shortage Records อยู่แล้วหรือไม่ (ทุกสถานะยกเว้น resolved, cancelled, replaced)
            existing_shortage_records = ShortageQueue.query.filter(
                ShortageQueue.sku == sku,
                ShortageQueue.status.in_(['pending', 'waiting_stock', 'ready_to_pick'])
            ).join(OrderLine, ShortageQueue.order_line_id == OrderLine.id).filter(
                OrderLine.accepted == True
            ).all()

            # สร้างรายการออเดอร์ที่ต้องการ SKU นี้ + เพิ่มสถานะ Shortage
            order_list = []
            for order in orders:
                # ✅ NEW: ดึงสถานะ Shortage Record สำหรับแต่ละ Order
                shortage_status = None
                shortage_reason = None
                shortage_record = ShortageQueue.query.filter(
                    ShortageQueue.sku == sku,
                    ShortageQueue.order_line_id == order.id
                ).order_by(ShortageQueue.created_at.desc()).first()

                if shortage_record:
                    shortage_status = shortage_record.status
                    shortage_reason = shortage_record.shortage_reason  # ✅ FIX: ใช้ shortage_reason แทน reason

                order_list.append({
                    "order_id": order.order_id,
                    "qty": order.qty,
                    "picked_qty": order.picked_qty or 0,
                    "shortage_qty": getattr(order, 'shortage_qty', 0) or 0,
                    "status": order.dispatch_status,
                    # ✅ NEW: เพิ่มสถานะ Shortage
                    "shortage_status": shortage_status,
                    "shortage_reason": shortage_reason,
                    # ✅ NEW: เพิ่ม SLA (order_time) แบบภาษาไทย
                    "order_time": format_sla_thai(order.order_time) if order.order_time else ""
                })

            return jsonify({
                "success": True,
                "sku": sku,
                "brand": product.brand if product else "",
                "has_pending_shortage": len(existing_shortage_records) > 0,
                "existing_shortage_count": len(existing_shortage_records),
                "model": product.model if product else "",
                "stock_qty": stock_qty,
                "reserved_qty": stock.reserved_qty if stock else 0,  # ✅ NEW: จำนวน Stock ที่จองไว้
                "available_qty": stock.available_qty if stock else 0,  # ✅ NEW: Stock ที่ใช้ได้จริง
                "total_need": total_need,
                "total_picked": total_picked,
                "total_shortage": total_shortage,
                "total_remaining": total_remaining,
                "order_count": len(orders),
                "orders": order_list,
                "can_fulfill": stock_qty >= total_remaining,
                "suggested_pick_qty": min(stock_qty, total_remaining)
            })
        except Exception as e:
            # Log the error for debugging
            print(f"ERROR in /api/scan/sku: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาดในระบบ: {str(e)}"
            }), 500

    @app.route("/api/pick/sku", methods=["POST"])
    @login_required
    def api_pick_sku():
        """API สำหรับบันทึกการหยิบ SKU (รองรับ Partial Picking)"""
        try:
            data = request.get_json()
            sku = data.get("sku", "").strip()
            qty = data.get("qty", 1)
            mark_shortage = data.get("mark_shortage", False)  # บอกว่านี่คือการ mark shortage

            if not sku:
                return jsonify({"success": False, "error": "กรุณาระบุ SKU"}), 400

            # หาออเดอร์ที่ยังหยิบไม่ครบ
            orders = OrderLine.query.filter(
                OrderLine.sku == sku,
                OrderLine.dispatch_status != "dispatched",
                OrderLine.accepted == True
            ).order_by(OrderLine.order_time).all()

            if not orders:
                return jsonify({"success": False, "error": "ไม่พบออเดอร์"}), 404

            # ⚠️ ตรวจสอบสต็อกก่อนอนุญาตให้หยิบ (ป้องกันการมักง่ายและป้องกันการผิดพลาด)
            if not mark_shortage:
                stock = Stock.query.filter_by(sku=sku).first()
                stock_qty = stock.qty if stock else 0

                if qty > stock_qty:
                    return jsonify({
                        "success": False,
                        "error": f"❌ ไม่สามารถหยิบได้!\n\nสต็อกมีเพียง {stock_qty} ชิ้น แต่คุณพยายามหยิบ {qty} ชิ้น\n\nกรุณาหยิบไม่เกิน {stock_qty} ชิ้น หรือกด 'Mark as Shortage'"
                    }), 400

            cu = current_user()
            now = now_thai()
            remaining_to_pick = qty

            picked_orders = []
            shortage_orders = []

            # อัปเดตการหยิบตามลำดับออเดอร์
            for order in orders:
                if remaining_to_pick <= 0 and not mark_shortage:
                    break

                need = order.qty - order.picked_qty
                if need > 0:
                    if mark_shortage:
                        # กรณี Mark Shortage: บันทึกว่าขาดเท่าไหร่
                        if hasattr(order, 'shortage_qty'):
                            order.shortage_qty = need
                        order.dispatch_status = "partial_ready"  # สถานะใหม่: หยิบได้บางส่วน
                        shortage_orders.append({
                            "order_id": order.order_id,
                            "sku": order.sku,
                            "needed": need,
                            "shortage": need
                        })
                    else:
                        # กรณีปกติ: หยิบตามจำนวนที่มี
                        pick_this = min(need, remaining_to_pick)
                        order.picked_qty += pick_this
                        order.picked_at = now
                        order.picked_by_user_id = cu.id
                        order.picked_by_username = cu.username

                        # ✅ Phase 2.2: คำนวณ shortage_qty
                        still_need = order.qty - order.picked_qty
                        order.shortage_qty = max(0, still_need)  # ป้องกันค่าติดลบ

                        # อัปเดตสถานะ
                        if order.picked_qty >= order.qty:
                            order.dispatch_status = "ready"  # หยิบครบแล้ว
                            picked_orders.append({
                                "order_id": order.order_id,
                                "sku": order.sku,
                                "picked": pick_this,
                                "status": "complete"
                            })
                        elif order.picked_qty > 0:
                            order.dispatch_status = "partial_ready"  # หยิบได้บางส่วน
                            picked_orders.append({
                                "order_id": order.order_id,
                                "sku": order.sku,
                                "picked": pick_this,
                                "shortage": still_need,
                                "status": "partial"
                            })

                        remaining_to_pick -= pick_this

            # ✅ Phase 0: Release reservation สำหรับ SKU ที่หยิบครบแล้ว (ก่อน commit)
            # เช็คว่าทุก order สำหรับ SKU นี้หยิบครบหรือยัง
            all_orders_for_sku = OrderLine.query.filter_by(sku=sku, accepted=True).all()
            total_need = sum(o.qty for o in all_orders_for_sku)
            total_picked = sum(o.picked_qty or 0 for o in all_orders_for_sku)
            total_shortage = sum(o.shortage_qty or 0 for o in all_orders_for_sku)

            # ถ้า picked + shortage >= need แสดงว่า SKU นี้เสร็จแล้ว → release reservation
            if (total_picked + total_shortage) >= total_need:
                # Release reservation สำหรับ SKU นี้ทั้งหมด
                release_stock_reservation("ALL_BATCHES", sku, total_need, reason="picking_completed")

            # ✅ Commit ทั้ง picking update และ stock release ในครั้งเดียว
            db.session.commit()

            # ✅ Auto-resolve Shortage Records when picked completely
            # NOTE: reserved_qty จะถูก release ผ่าน helper function ที่บรรทัด 4839-4849 แล้ว
            # ไม่ต้อง release ซ้ำที่นี่
            auto_resolved_count = 0
            if not mark_shortage:
                for order in orders:
                    remaining = order.qty - order.picked_qty

                    if remaining == 0:  # หยิบครบแล้ว
                        # ✅ FIX: ใช้ order_line_id เพื่อความแม่นยำ (1 order_id อาจมีหลาย SKU)
                        shortages = ShortageQueue.query.filter(
                            ShortageQueue.order_line_id == order.id,
                            ShortageQueue.sku == sku,
                            ShortageQueue.status.in_(['pending', 'waiting_stock', 'ready_to_pick'])
                        ).all()

                        for shortage in shortages:
                            shortage.status = 'resolved'
                            shortage.resolution_notes = (shortage.resolution_notes or "") + f'\n[{now}] ✅ Auto-resolved: หยิบครบแล้ว (Order: {order.order_id})'
                            shortage.resolved_at = now
                            shortage.resolved_by_user_id = cu.id
                            shortage.resolved_by_username = cu.username
                            auto_resolved_count += 1

                if auto_resolved_count > 0:
                    db.session.commit()

            # บันทึก Audit Log
            log_audit(
                action="pick_sku" if not mark_shortage else "mark_shortage",
                details={
                    "sku": sku,
                    "qty_picked": qty,
                    "picked_by": cu.username,
                    "mark_shortage": mark_shortage,
                    "orders_affected": len(picked_orders) + len(shortage_orders),
                    "auto_resolved_shortages": auto_resolved_count
                }
            )

            # คำนวณข้อมูลใหม่
            total_need = sum(o.qty for o in orders)
            total_picked = sum(o.picked_qty for o in orders)
            total_shortage = sum(getattr(o, 'shortage_qty', 0) or 0 for o in orders)
            total_remaining = total_need - total_picked

            return jsonify({
                "success": True,
                "sku": sku,
                "qty_picked": qty,
                "total_need": total_need,
                "total_picked": total_picked,
                "total_shortage": total_shortage,
                "total_remaining": total_remaining,
                "picked_orders": picked_orders,
                "shortage_orders": shortage_orders,
                "has_shortage": total_shortage > 0
            })
        except Exception as e:
            # Log the error for debugging
            print(f"ERROR in /api/pick/sku: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาดในระบบ: {str(e)}"
            }), 500

    # -----------------------
    # Shortage Queue Management (Option 2)
    # -----------------------
    @app.route("/shortage-queue")
    @login_required
    def shortage_queue():
        """หน้า Shortage Queue Dashboard"""
        return render_template("shortage_queue.html")

    @app.route("/api/shortage/queue", methods=["GET"])
    @login_required
    def api_shortage_queue():
        """API สำหรับดึงข้อมูล Shortage Queue"""
        try:
            status = request.args.get("status", "").strip()
            order_id = request.args.get("order_id", "").strip()
            batch_id = request.args.get("batch", "").strip()
            sku = request.args.get("sku", "").strip()

            # Query
            query = ShortageQueue.query

            if status:
                query = query.filter_by(status=status)
            if order_id:
                query = query.filter(ShortageQueue.order_id.like(f"%{order_id}%"))
            if batch_id:
                query = query.filter(ShortageQueue.original_batch_id.like(f"%{batch_id}%"))
            if sku:
                query = query.filter(ShortageQueue.sku.like(f"%{sku}%"))

            # ✅ Phase 4: SLA-based sorting
            # Get all shortages first, then sort by SLA in Python
            # (because SLA is in OrderLine table, not ShortageQueue)
            shortages = query.all()

            # ✅ Phase 4: Sort by SLA (earliest first), then by created_at
            def get_sla_for_shortage(shortage):
                order_line = shortage.order_line
                if order_line and order_line.sla_date:
                    return (False, order_line.sla_date, shortage.created_at)
                else:
                    # No SLA = last
                    return (True, datetime.max.date(), shortage.created_at)

            shortages = sorted(shortages, key=get_sla_for_shortage)

            # Summary counts
            summary = {
                "pending": ShortageQueue.query.filter_by(status="pending").count(),
                "waiting_stock": ShortageQueue.query.filter_by(status="waiting_stock").count(),
                "cancelled": ShortageQueue.query.filter_by(status="cancelled").count(),
                "replaced": ShortageQueue.query.filter_by(status="replaced").count(),
                "resolved": ShortageQueue.query.filter_by(status="resolved").count(),
                "total": ShortageQueue.query.count()
            }

            # Format data
            shortages_data = []
            for s in shortages:
                # ✅ Phase 2.5: ใช้ Real-time data จาก OrderLine แทนข้อมูลที่เก็บใน ShortageQueue
                order_line = s.order_line
                qty_picked_realtime = order_line.picked_qty if order_line else s.qty_picked
                qty_shortage_realtime = max(0, s.qty_required - qty_picked_realtime)

                # ✅ Phase 4: Add SLA information
                sla_date = None
                sla_status = None
                sla_text = None
                platform = None

                if order_line:
                    sla_date = str(order_line.sla_date) if order_line.sla_date else None
                    platform = order_line.platform

                    # Calculate SLA status
                    if order_line.sla_date:
                        from datetime import date
                        today = date.today()
                        if order_line.sla_date < today:
                            sla_status = "overdue"
                            days_overdue = (today - order_line.sla_date).days
                            sla_text = f"เลยกำหนด {days_overdue} วัน"
                        elif order_line.sla_date == today:
                            sla_status = "today"
                            sla_text = "วันนี้"
                        elif order_line.sla_date == today + timedelta(days=1):
                            sla_status = "tomorrow"
                            sla_text = "พรุ่งนี้"
                        else:
                            days_left = (order_line.sla_date - today).days
                            sla_status = "upcoming"
                            sla_text = f"อีก {days_left} วัน"

                shortages_data.append({
                    "id": s.id,
                    "order_id": s.order_id,
                    "sku": s.sku,
                    "batch_id": s.original_batch_id,
                    "qty_required": s.qty_required,
                    "qty_picked": qty_picked_realtime,  # ✅ Real-time from OrderLine
                    "qty_shortage": qty_shortage_realtime,  # ✅ Recalculated
                    "reason": s.shortage_reason,
                    "shortage_type": s.shortage_type,  # ✅ Phase 2: PRE_PICK or POST_PICK
                    "notes": s.notes,  # ✅ Priority 1.3: Notes from picker
                    "status": s.status,
                    "created_by": s.created_by_username,
                    "created_at": to_thai_be(s.created_at) if s.created_at else "-",
                    "resolved_at": to_thai_be(s.resolved_at) if s.resolved_at else None,
                    "resolved_by": s.resolved_by_username,
                    # ✅ Phase 4: SLA fields
                    "sla_date": sla_date,
                    "sla_status": sla_status,
                    "sla_text": sla_text,
                    "platform": platform
                })

            return jsonify({
                "success": True,
                "shortages": shortages_data,
                "summary": summary
            })

        except Exception as e:
            print(f"ERROR in /api/shortage/queue: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }), 500

    @app.route("/api/shortage/action", methods=["POST"])
    @login_required
    def api_shortage_action():
        """API สำหรับจัดการ Shortage (รอสต็อก/ยกเลิก/แทน SKU)"""
        try:
            data = request.get_json()
            shortage_id = data.get("shortage_id")
            action = data.get("action", "").strip()
            replacement_sku = data.get("replacement_sku", "").strip()
            notes = data.get("notes", "").strip()

            if not shortage_id or not action:
                return jsonify({"success": False, "error": "ข้อมูลไม่ครบ"}), 400

            shortage = db.session.get(ShortageQueue, shortage_id)
            if not shortage:
                return jsonify({"success": False, "error": "ไม่พบ Shortage Record"}), 404

            if shortage.status != "pending":
                return jsonify({"success": False, "error": "Shortage นี้ถูกจัดการไปแล้ว"}), 400

            cu = current_user()
            now = now_thai()

            # Update status based on action
            if action == "wait_stock":
                shortage.status = "waiting_stock"
                shortage.action_taken = "wait_stock"
            elif action == "cancel":
                shortage.status = "cancelled"
                shortage.action_taken = "cancel"
            elif action == "replace_sku":
                if not replacement_sku:
                    return jsonify({"success": False, "error": "กรุณาระบุ SKU ที่ใช้แทน"}), 400
                shortage.status = "replaced"
                shortage.action_taken = "replace_sku"
                shortage.replacement_sku = replacement_sku
            elif action == "resolved":
                # ✅ ตรวจสอบว่ามีการหยิบสินค้าครบแล้วหรือยัง
                order_line = shortage.order_line
                if not order_line:
                    return jsonify({
                        "success": False,
                        "error": "ไม่พบข้อมูล Order Line"
                    }), 404

                # คำนวณว่าต้องหยิบกี่ชิ้น (ต้องการ - ขาด)
                expected_picked = shortage.qty_required - shortage.qty_shortage
                actual_picked = order_line.picked_qty or 0

                # ถ้ายังหยิบไม่ครบ → ไม่อนุญาตให้เปลี่ยนเป็น "จัดการเรียบร้อย"
                if actual_picked < expected_picked:
                    return jsonify({
                        "success": False,
                        "error": f"❌ ยังหยิบสินค้าไม่ครบ!\n\n📦 SKU: {shortage.sku}\n✅ ต้องหยิบ: {expected_picked} ชิ้น\n📊 หยิบแล้ว: {actual_picked} ชิ้น\n⚠️ ยังขาดอีก: {expected_picked - actual_picked} ชิ้น\n\n💡 กรุณาไปหยิบสินค้าในหน้า /scan/sku ก่อน หรือเลือก Action อื่น เช่น 'ยกเลิก' หรือ 'รอสต็อกเข้า'"
                    }), 400

                shortage.status = "resolved"
                shortage.action_taken = "resolved"
            else:
                return jsonify({"success": False, "error": "Action ไม่ถูกต้อง"}), 400

            shortage.resolution_notes = notes
            shortage.resolved_at = now
            shortage.resolved_by_user_id = cu.id
            shortage.resolved_by_username = cu.username

            # ✅ Priority 2.2: Log transaction when resolving/cancelling shortage
            if action in ['resolved', 'cancel']:
                # Note: We don't reverse the DAMAGE transaction
                # Instead, we log the resolution action for audit trail
                # The actual stock adjustment (if any) happens elsewhere
                log_stock_transaction(
                    sku=shortage.sku,
                    transaction_type='ADJUST',
                    quantity=0,  # No actual stock movement, just recording the action
                    reason_code=f'SHORTAGE_{action.upper()}',
                    reference_type='shortage',
                    reference_id=str(shortage.id),
                    notes=f"Shortage {action} by {cu.username}: {notes}" if notes else f"Shortage {action} by {cu.username}"
                )
                app.logger.info(
                    f"📝 Logged shortage {action}: {shortage.order_id} | "
                    f"SKU: {shortage.sku} | Qty: {shortage.qty_shortage}"
                )

            # ✅ Phase 2.2: อัปเดต shortage_qty ใน OrderLine เมื่อ resolve/cancel/replace
            if action in ['cancel', 'resolved', 'replace_sku']:
                order_line = shortage.order_line
                if order_line:
                    # ลด shortage_qty ลงตามจำนวนที่จัดการแล้ว
                    current_shortage = order_line.shortage_qty or 0
                    order_line.shortage_qty = max(0, current_shortage - shortage.qty_shortage)

            # ✅ Phase 0: Release reservation เมื่อ shortage ถูก cancel/resolve (ก่อน commit)
            # เพราะ cancel = ไม่ต้องการของแล้ว, resolved = จัดการเรียบร้อยแล้ว
            if action in ['cancel', 'resolved']:
                release_stock_reservation(
                    shortage.original_batch_id or "UNKNOWN",
                    shortage.sku,
                    shortage.qty_shortage,
                    reason=f"shortage_{action}"
                )

            # ✅ Commit ทั้ง shortage resolution และ stock release ในครั้งเดียว
            db.session.commit()

            # Audit Log
            log_audit(
                action="shortage_action",
                details={
                    "shortage_id": shortage_id,
                    "order_id": shortage.order_id,
                    "sku": shortage.sku,
                    "action": action,
                    "replacement_sku": replacement_sku,
                    "notes": notes,
                    "resolved_by": cu.username
                }
            )

            # ✅ Phase 1.2: Recalculate Batch Progress หลัง resolve shortage
            batch_progress = None
            if shortage.original_batch_id:
                try:
                    progress_data = calculate_batch_progress(shortage.original_batch_id)
                    batch_progress = {
                        "batch_id": shortage.original_batch_id,
                        "progress_percent": progress_data["progress_percent"],
                        "completed_qty": progress_data["completed_qty"],
                        "total_qty": progress_data["total_qty"]
                    }
                except Exception as e:
                    print(f"Warning: Could not calculate batch progress: {e}")

            return jsonify({
                "success": True,
                "message": f"บันทึกสำเร็จ: {shortage.order_id}",
                "batch_progress": batch_progress  # ✅ Phase 1.2: Return progress
            })

        except Exception as e:
            print(f"ERROR in /api/shortage/action: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }), 500

    @app.route("/api/shortage/quick-action", methods=["POST"])
    @login_required
    def api_shortage_quick_action():
        """API สำหรับ Quick Action จาก Batch Detail - จัดการ Shortage ทั้งหมดของ SKU ใน Batch"""
        try:
            data = request.get_json()
            sku = data.get("sku", "").strip()
            batch_id = data.get("batch_id", "").strip()
            action = data.get("action", "").strip()
            notes = data.get("notes", "").strip()

            if not sku or not batch_id or not action:
                return jsonify({"success": False, "error": "ข้อมูลไม่ครบ"}), 400

            # หา Shortage Records ทั้งหมดที่ pending สำหรับ SKU และ Batch นี้
            shortages = ShortageQueue.query.filter(
                ShortageQueue.sku == sku,
                ShortageQueue.original_batch_id == batch_id,
                ShortageQueue.status == "pending"
            ).all()

            if not shortages:
                return jsonify({"success": False, "error": "ไม่พบ Shortage ที่รอจัดการ"}), 404

            cu = current_user()
            now = now_thai()
            updated_count = 0
            validation_errors = []

            # Update all pending shortages
            for shortage in shortages:
                if action == "resolved":
                    # ✅ ตรวจสอบว่ามีการหยิบสินค้าครบแล้วหรือยัง
                    order_line = shortage.order_line
                    if not order_line:
                        validation_errors.append(f"Order {shortage.order_id}: ไม่พบข้อมูล Order Line")
                        continue

                    # คำนวณว่าต้องหยิบกี่ชิ้น (ต้องการ - ขาด)
                    expected_picked = shortage.qty_required - shortage.qty_shortage
                    actual_picked = order_line.picked_qty or 0

                    # ถ้ายังหยิบไม่ครบ → ข้าม shortage นี้
                    if actual_picked < expected_picked:
                        validation_errors.append(
                            f"Order {shortage.order_id}: ยังหยิบไม่ครบ (ต้องหยิบ {expected_picked} แต่หยิบได้ {actual_picked})"
                        )
                        continue

                    shortage.status = "resolved"
                    shortage.action_taken = "resolved"
                elif action == "cancelled":
                    shortage.status = "cancelled"
                    shortage.action_taken = "cancel"
                else:
                    return jsonify({"success": False, "error": "Action ไม่ถูกต้อง"}), 400

                shortage.resolution_notes = notes
                shortage.resolved_at = now
                shortage.resolved_by_user_id = cu.id
                shortage.resolved_by_username = cu.username

                # ✅ Phase 2.2: อัปเดต shortage_qty ใน OrderLine
                if action in ['resolved', 'cancelled']:
                    order_line = shortage.order_line
                    if order_line:
                        current_shortage = order_line.shortage_qty or 0
                        order_line.shortage_qty = max(0, current_shortage - shortage.qty_shortage)

                updated_count += 1

            # ถ้ามี validation errors → แสดงข้อความเตือน
            if validation_errors and updated_count == 0:
                error_msg = "❌ ไม่สามารถจัดการเรียบร้อยได้:\n\n" + "\n".join(validation_errors)
                error_msg += "\n\n💡 กรุณาไปหยิบสินค้าในหน้า /scan/sku ก่อน"
                return jsonify({"success": False, "error": error_msg}), 400

            db.session.commit()

            # Audit Log
            log_audit(
                action="shortage_quick_action",
                details={
                    "sku": sku,
                    "batch_id": batch_id,
                    "action": action,
                    "count": updated_count,
                    "notes": notes,
                    "resolved_by": cu.username
                }
            )

            # สร้าง response message
            message = f"จัดการ Shortage สำเร็จ ({updated_count} รายการ)"
            if validation_errors:
                message += f"\n\n⚠️ มีบางรายการที่ยังหยิบไม่ครบ ({len(validation_errors)} รายการ):\n" + "\n".join(validation_errors[:3])
                if len(validation_errors) > 3:
                    message += f"\n... และอีก {len(validation_errors) - 3} รายการ"

            return jsonify({
                "success": True,
                "message": message,
                "count": updated_count,
                "warnings": validation_errors if validation_errors else None
            })

        except Exception as e:
            print(f"ERROR in /api/shortage/quick-action: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }), 500

    # ✅ Phase 1.1: Bulk Action API
    @app.route("/api/shortage/bulk-action", methods=["POST"])
    @login_required
    def api_shortage_bulk_action():
        """
        API สำหรับจัดการ Shortage หลายรายการพร้อมกัน (Bulk Action)

        Request:
            {
                "shortage_ids": [1, 2, 3],
                "action": "wait_stock" | "cancel" | "resolved" | "replace_sku",
                "replacement_sku": "SKU-002" (optional, required for replace_sku),
                "notes": "หมายเหตุ" (optional)
            }

        Response:
            {
                "success": true,
                "processed": 3,
                "failed": 0,
                "errors": []
            }
        """
        try:
            data = request.get_json()
            shortage_ids = data.get("shortage_ids", [])
            action = data.get("action", "").strip()
            replacement_sku = data.get("replacement_sku", "").strip()
            notes = data.get("notes", "").strip()

            # Validation
            if not shortage_ids or not isinstance(shortage_ids, list):
                return jsonify({"success": False, "error": "กรุณาเลือกรายการที่ต้องการจัดการ"}), 400

            if not action:
                return jsonify({"success": False, "error": "กรุณาเลือก Action"}), 400

            if action == "replace_sku" and not replacement_sku:
                return jsonify({"success": False, "error": "กรุณาระบุ SKU ที่ใช้แทน"}), 400

            cu = current_user()
            now = now_thai()

            processed_count = 0
            failed_count = 0
            errors = []

            # Process each shortage
            for shortage_id in shortage_ids:
                try:
                    shortage = db.session.get(ShortageQueue, shortage_id)

                    if not shortage:
                        errors.append(f"Shortage ID {shortage_id}: ไม่พบข้อมูล")
                        failed_count += 1
                        continue

                    if shortage.status != "pending":
                        errors.append(f"Shortage ID {shortage_id} ({shortage.order_id}): ถูกจัดการไปแล้ว")
                        failed_count += 1
                        continue

                    # Update based on action
                    if action == "wait_stock":
                        shortage.status = "waiting_stock"
                        shortage.action_taken = "wait_stock"

                    elif action == "cancel":
                        shortage.status = "cancelled"
                        shortage.action_taken = "cancel"

                    elif action == "replace_sku":
                        shortage.status = "replaced"
                        shortage.action_taken = "replace_sku"
                        shortage.replacement_sku = replacement_sku

                    elif action == "resolved":
                        # ✅ Validation: ตรวจสอบว่ามีการหยิบสินค้าครบแล้วหรือยัง
                        order_line = shortage.order_line
                        if not order_line:
                            errors.append(f"Shortage ID {shortage_id} ({shortage.order_id}): ไม่พบข้อมูล Order Line")
                            failed_count += 1
                            continue

                        # คำนวณว่าต้องหยิบกี่ชิ้น (ต้องการ - ขาด)
                        expected_picked = shortage.qty_required - shortage.qty_shortage
                        actual_picked = order_line.picked_qty or 0

                        # ถ้ายังหยิบไม่ครบ → ข้าม
                        if actual_picked < expected_picked:
                            errors.append(
                                f"Order {shortage.order_id} ({shortage.sku}): ยังหยิบไม่ครบ (ต้อง {expected_picked} แต่มี {actual_picked})"
                            )
                            failed_count += 1
                            continue

                        shortage.status = "resolved"
                        shortage.action_taken = "resolved"

                    else:
                        errors.append(f"Shortage ID {shortage_id}: Action ไม่ถูกต้อง")
                        failed_count += 1
                        continue

                    # Update audit fields
                    shortage.resolution_notes = notes
                    shortage.resolved_at = now
                    shortage.resolved_by_user_id = cu.id
                    shortage.resolved_by_username = cu.username

                    # ✅ Phase 2.2: อัปเดต shortage_qty ใน OrderLine
                    if action in ['cancel', 'resolved', 'replace_sku']:
                        order_line = shortage.order_line
                        if order_line:
                            current_shortage = order_line.shortage_qty or 0
                            order_line.shortage_qty = max(0, current_shortage - shortage.qty_shortage)

                    processed_count += 1

                except Exception as e:
                    errors.append(f"Shortage ID {shortage_id}: {str(e)}")
                    failed_count += 1
                    continue

            # Commit all changes
            if processed_count > 0:
                db.session.commit()

                # Audit Log
                log_audit(
                    action="shortage_bulk_action",
                    details={
                        "shortage_ids": shortage_ids,
                        "action": action,
                        "replacement_sku": replacement_sku,
                        "notes": notes,
                        "processed": processed_count,
                        "failed": failed_count,
                        "resolved_by": cu.username
                    }
                )

            # ✅ Phase 1.2: Recalculate Batch Progress หลัง bulk resolve
            # หา batch IDs ทั้งหมดที่ได้รับผลกระทบ
            affected_batches = {}
            if processed_count > 0:
                for shortage_id in shortage_ids:
                    shortage = db.session.get(ShortageQueue, shortage_id)
                    if shortage and shortage.original_batch_id:
                        batch_id = shortage.original_batch_id
                        if batch_id not in affected_batches:
                            try:
                                progress_data = calculate_batch_progress(batch_id)
                                affected_batches[batch_id] = {
                                    "progress_percent": progress_data["progress_percent"],
                                    "completed_qty": progress_data["completed_qty"],
                                    "total_qty": progress_data["total_qty"]
                                }
                            except Exception as e:
                                print(f"Warning: Could not calculate progress for batch {batch_id}: {e}")

            # Response
            if failed_count > 0 and processed_count == 0:
                # ทุกรายการล้มเหลว
                error_msg = f"❌ ไม่สามารถจัดการได้ทั้งหมด ({failed_count} รายการ)\n\n"
                error_msg += "\n".join(errors[:5])  # แสดงแค่ 5 รายการแรก
                if len(errors) > 5:
                    error_msg += f"\n... และอีก {len(errors) - 5} รายการ"
                return jsonify({
                    "success": False,
                    "error": error_msg,
                    "errors": errors
                }), 400

            # มีบางรายการสำเร็จ
            response = {
                "success": True,
                "processed": processed_count,
                "failed": failed_count,
                "message": f"✅ จัดการสำเร็จ {processed_count} รายการ",
                "batch_progress": affected_batches  # ✅ Phase 1.2: Return progress
            }

            if failed_count > 0:
                response["warnings"] = errors
                response["message"] += f" (ล้มเหลว {failed_count} รายการ)"

            return jsonify(response)

        except Exception as e:
            db.session.rollback()
            print(f"ERROR in /api/shortage/bulk-action: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }), 500

    # ✅ Phase 1.3: Export Shortage Report to Excel
    @app.route("/api/shortage/export-excel")
    @login_required
    def api_export_shortage_excel():
        """Export Shortage Queue to Excel with filters"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
            from openpyxl.utils import get_column_letter
            from io import BytesIO
            from datetime import datetime

            # Get filters from query params
            status = request.args.get('status', '').strip()
            order_id = request.args.get('order_id', '').strip()
            batch = request.args.get('batch', '').strip()
            sku = request.args.get('sku', '').strip()

            # Query data with filters
            query = ShortageQueue.query

            if status:
                query = query.filter_by(status=status)
            if order_id:
                query = query.filter(ShortageQueue.order_id.like(f'%{order_id}%'))
            if batch:
                query = query.filter_by(original_batch_id=batch)
            if sku:
                query = query.filter(ShortageQueue.sku.like(f'%{sku}%'))

            # Order by created_at desc (newest first)
            shortages = query.order_by(ShortageQueue.created_at.desc()).limit(10000).all()

            if not shortages:
                return jsonify({"success": False, "error": "ไม่พบข้อมูลที่ตรงกับเงื่อนไข"}), 404

            # Create workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Shortage Report"

            # Header row
            headers = [
                "Order ID", "SKU", "Product Name", "Batch ID",
                "Required", "Picked", "Shortage",
                "Reason", "Type", "Status",
                "Created At", "Created By",
                "Resolved At", "Resolved By",
                "Action Taken", "Replacement SKU", "Notes"
            ]
            ws.append(headers)

            # Style header row
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            for col_num, cell in enumerate(ws[1], 1):
                cell.fill = header_fill
                cell.font = header_font
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')

            # Add data rows
            for shortage in shortages:
                # Get product name from OrderLine
                product_name = ""
                if shortage.order_line:
                    product_name = shortage.order_line.item_name or ""

                row_data = [
                    shortage.order_id,
                    shortage.sku,
                    product_name,
                    shortage.original_batch_id or "",
                    shortage.qty_required,
                    shortage.qty_picked,
                    shortage.qty_shortage,
                    shortage.shortage_reason or "",
                    shortage.shortage_type or "",
                    shortage.status,
                    shortage.created_at.strftime("%Y-%m-%d %H:%M") if shortage.created_at else "",
                    shortage.created_by_username or "",
                    shortage.resolved_at.strftime("%Y-%m-%d %H:%M") if shortage.resolved_at else "",
                    shortage.resolved_by_username or "",
                    shortage.action_taken or "",
                    shortage.replacement_sku or "",
                    shortage.resolution_notes or ""
                ]
                ws.append(row_data)

                # Apply border to data rows
                for cell in ws[ws.max_row]:
                    cell.border = thin_border

            # Auto-adjust column widths
            for col_num in range(1, len(headers) + 1):
                col_letter = get_column_letter(col_num)
                max_length = 0

                for cell in ws[col_letter]:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass

                adjusted_width = min(max_length + 2, 50)  # Max width = 50
                ws.column_dimensions[col_letter].width = adjusted_width

            # Freeze header row
            ws.freeze_panes = 'A2'

            # Save to BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Shortage_Report_{timestamp}.xlsx"

            # Send file
            from flask import send_file
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )

        except Exception as e:
            print(f"ERROR in /api/shortage/export-excel: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }), 500

    @app.route("/api/shortage/mark", methods=["POST"])
    @login_required
    def api_mark_shortage():
        """API สำหรับบันทึก Shortage และเพิ่มเข้า Shortage Queue (✅ Phase 2: With Reason Code)"""
        try:
            data = request.get_json()
            sku = data.get("sku", "").strip()
            picked_qty = int(data.get("picked_qty", 0))
            shortage_qty = int(data.get("shortage_qty", 0))
            reason = data.get("reason", "").strip()
            notes = data.get("notes", "").strip()  # ✅ Phase 2: Accept notes from picker

            if not sku:
                return jsonify({"success": False, "error": "กรุณาระบุ SKU"}), 400

            if shortage_qty <= 0:
                return jsonify({"success": False, "error": "จำนวนที่ขาดต้องมากกว่า 0"}), 400

            if not reason:
                return jsonify({"success": False, "error": "กรุณาระบุเหตุผล"}), 400

            # ✅ FIX: เช็คว่ามี Shortage Record อยู่แล้วหรือไม่ (ป้องกันการบันทึกซ้ำ)
            existing_shortage = ShortageQueue.query.filter(
                ShortageQueue.sku == sku,
                ShortageQueue.status.in_(['pending', 'waiting_stock', 'ready_to_pick'])
            ).join(OrderLine, ShortageQueue.order_line_id == OrderLine.id).filter(
                OrderLine.accepted == True,
                OrderLine.dispatch_status != "dispatched"
            ).first()

            if existing_shortage:
                return jsonify({
                    "success": False,
                    "error": f"⚠️ SKU นี้มี Shortage Record อยู่แล้ว!\n\nสถานะ: {existing_shortage.status}\nกรุณาไปจัดการที่หน้า Shortage Queue แทน\n\nหากต้องการอัปเดตข้อมูล กรุณาใช้ปุ่ม 'แก้ไข Shortage'"
                }), 400

            # หาออเดอร์ที่ยังหยิบไม่ครบ (จาก Batch ที่ Accept แล้ว)
            orders = OrderLine.query.filter(
                OrderLine.sku == sku,
                OrderLine.dispatch_status != "dispatched",
                OrderLine.accepted == True
            ).order_by(OrderLine.order_time).all()

            if not orders:
                return jsonify({"success": False, "error": "ไม่พบออเดอร์ที่ต้องการ SKU นี้"}), 404

            cu = current_user()
            now = now_thai()

            total_need = sum(o.qty for o in orders)
            total_remaining = sum(o.qty - o.picked_qty for o in orders)

            # Validate
            if picked_qty + shortage_qty != total_remaining:
                return jsonify({
                    "success": False,
                    "error": f"ข้อมูลไม่ถูกต้อง: หยิบได้ {picked_qty} + ขาด {shortage_qty} = {picked_qty + shortage_qty} แต่ต้องการทั้งหมด {total_remaining}"
                }), 400

            # 1. บันทึกการหยิบ (ถ้ามี)
            remaining_to_pick = picked_qty
            picked_orders_data = []

            if picked_qty > 0:
                # หยิบตามลำดับออเดอร์
                for order in orders:
                    if remaining_to_pick <= 0:
                        break

                    need = order.qty - order.picked_qty
                    if need > 0:
                        pick_this = min(need, remaining_to_pick)
                        order.picked_qty += pick_this
                        order.picked_at = now
                        order.picked_by_user_id = cu.id
                        order.picked_by_username = cu.username

                        # อัปเดตสถานะ
                        if order.picked_qty >= order.qty:
                            order.dispatch_status = "ready"
                        else:
                            order.dispatch_status = "partial_ready"

                        picked_orders_data.append({
                            "order_id": order.order_id,
                            "picked": pick_this,
                            "status": "ready" if order.picked_qty >= order.qty else "partial_ready"
                        })

                        remaining_to_pick -= pick_this

            # 2. สร้าง Shortage Records
            remaining_shortage = shortage_qty
            shortage_records_created = []

            for order in orders:
                if remaining_shortage <= 0:
                    break

                need = order.qty - order.picked_qty
                if need > 0:
                    shortage_this = min(need, remaining_shortage)

                    # ✅ Phase 2: Create Shortage Record with reason code and type
                    shortage_record = ShortageQueue(
                        order_line_id=order.id,
                        order_id=order.order_id,
                        sku=sku,
                        qty_required=order.qty,
                        qty_picked=order.picked_qty,
                        qty_shortage=shortage_this,
                        original_batch_id=order.batch_id,
                        shortage_reason=reason,
                        shortage_type='POST_PICK',  # ✅ Phase 2: POST_PICK (found during picking)
                        status='pending',
                        notes=notes,  # ✅ Phase 2: Save additional notes from picker
                        created_by_user_id=cu.id,
                        created_by_username=cu.username
                    )
                    db.session.add(shortage_record)

                    # ✅ Phase 2: Log transaction for shortage (DAMAGE/ADJUST)
                    log_stock_transaction(
                        sku=sku,
                        transaction_type='DAMAGE',
                        quantity=-shortage_this,  # Negative (減少)
                        reason_code=reason,
                        reference_type='shortage',
                        reference_id=str(order.id),  # Use order_line_id as reference
                        notes=f"Shortage marked by {cu.username}: {reason}" + (f" | {notes}" if notes else "")
                    )

                    # อัปเดตสถานะออเดอร์
                    if order.picked_qty == 0:
                        order.dispatch_status = "shortage"  # ขาดหมด
                    else:
                        order.dispatch_status = "partial_ready"  # หยิบได้บางส่วน

                    # ✅ Phase 2.2: อัปเดต shortage_qty field
                    order.shortage_qty = (order.shortage_qty or 0) + shortage_this

                    shortage_records_created.append({
                        "order_id": order.order_id,
                        "sku": sku,
                        "shortage": shortage_this
                    })

                    remaining_shortage -= shortage_this

            db.session.commit()

            # Audit Log
            log_audit(
                action="mark_shortage",
                details={
                    "sku": sku,
                    "picked_qty": picked_qty,
                    "shortage_qty": shortage_qty,
                    "reason": reason,
                    "created_by": cu.username,
                    "shortage_records": len(shortage_records_created),
                    "orders_affected": len(picked_orders_data) + len(shortage_records_created)
                }
            )

            return jsonify({
                "success": True,
                "sku": sku,
                "picked_qty": picked_qty,
                "shortage_qty": shortage_qty,
                "reason": reason,
                "picked_orders": picked_orders_data,
                "shortage_records": shortage_records_created,
                "total_shortage": shortage_qty,
                "message": f"บันทึก Shortage สำเร็จ: {len(shortage_records_created)} รายการ"
            })

        except Exception as e:
            print(f"ERROR in /api/shortage/mark: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาดในระบบ: {str(e)}"
            }), 500

    @app.route("/api/shortage/update", methods=["POST"])
    @login_required
    def api_update_shortage():
        """API สำหรับอัพเดท Shortage Records ที่มีอยู่แล้ว (ป้องกันการสร้างซ้ำ)"""
        try:
            data = request.get_json()
            sku = data.get("sku", "").strip()
            picked_qty = int(data.get("picked_qty", 0))
            shortage_qty = int(data.get("shortage_qty", 0))
            reason = data.get("reason", "").strip()

            if not sku:
                return jsonify({"success": False, "error": "กรุณาระบุ SKU"}), 400

            if shortage_qty <= 0:
                return jsonify({"success": False, "error": "จำนวนที่ขาดต้องมากกว่า 0"}), 400

            if not reason:
                return jsonify({"success": False, "error": "กรุณาระบุเหตุผล"}), 400

            # หา Shortage Records ที่มีอยู่แล้ว (pending status)
            existing_records = ShortageQueue.query.filter(
                ShortageQueue.sku == sku,
                ShortageQueue.status == 'pending'
            ).join(OrderLine, ShortageQueue.order_line_id == OrderLine.id).filter(
                OrderLine.accepted == True
            ).all()

            if not existing_records:
                return jsonify({
                    "success": False,
                    "error": "ไม่พบรายการ Shortage ที่ต้องการอัพเดท กรุณาใช้ 'บันทึก Shortage' แทน"
                }), 404

            cu = current_user()
            now = now_thai()

            # อัพเดทเหตุผลของ Shortage Records ทั้งหมด
            updated_count = 0
            for record in existing_records:
                record.shortage_reason = reason
                record.updated_at = now
                record.updated_by_user_id = cu.id
                record.updated_by_username = cu.username
                updated_count += 1

            db.session.commit()

            # Audit Log
            log_audit(
                action="update_shortage",
                details={
                    "sku": sku,
                    "new_reason": reason,
                    "updated_by": cu.username,
                    "records_updated": updated_count
                }
            )

            return jsonify({
                "success": True,
                "sku": sku,
                "shortage_qty": shortage_qty,
                "reason": reason,
                "shortage_records": [{"order_id": r.order_id, "qty_shortage": r.qty_shortage} for r in existing_records],
                "total_shortage": sum(r.qty_shortage for r in existing_records),
                "message": f"อัพเดท Shortage สำเร็จ: {updated_count} รายการ"
            })

        except Exception as e:
            print(f"ERROR in /api/shortage/update: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาดในระบบ: {str(e)}"
            }), 500

    @app.route("/api/shortage/order-details", methods=["GET"])
    @login_required
    def api_shortage_order_details():
        """API สำหรับดึงข้อมูล Shortage Details ของ Order ID เฉพาะ"""
        try:
            order_id = request.args.get("order_id", "").strip()

            if not order_id:
                return jsonify({"success": False, "error": "กรุณาระบุ Order ID"}), 400

            # หา Shortage Queue ของ Order ID นี้
            shortages = ShortageQueue.query.filter_by(order_id=order_id).order_by(ShortageQueue.created_at.desc()).all()

            if not shortages:
                return jsonify({
                    "success": False,
                    "error": f"ไม่พบข้อมูล Shortage สำหรับ Order ID: {order_id}"
                }), 404

            # Format data
            shortage_data = []
            for s in shortages:
                order_line = s.order_line
                qty_picked_realtime = order_line.picked_qty if order_line else s.qty_picked

                shortage_data.append({
                    "id": s.id,
                    "order_id": s.order_id,
                    "sku": s.sku,
                    "batch_id": s.original_batch_id,
                    "qty_required": s.qty_required,
                    "qty_picked": qty_picked_realtime,
                    "qty_shortage": s.qty_shortage,
                    "reason": s.shortage_reason,
                    "shortage_type": s.shortage_type,  # ✅ Priority 1.2: Added shortage_type
                    "notes": s.notes,  # ✅ Priority 1.2: Added notes field
                    "status": s.status,
                    "created_by": s.created_by_username,
                    "created_at": to_thai_be(s.created_at) if s.created_at else "-",
                    "resolved_at": to_thai_be(s.resolved_at) if s.resolved_at else None,
                    "resolved_by": s.resolved_by_username
                })

            return jsonify({
                "success": True,
                "order_id": order_id,
                "shortages": shortage_data
            })

        except Exception as e:
            print(f"ERROR in /api/shortage/order-details: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }), 500

    @app.route("/api/shortage/change-status", methods=["POST"])
    @login_required
    def api_shortage_change_status():
        """
        API สำหรับเปลี่ยนสถานะ Shortage Record โดยตรง (Admin use)
        รองรับการเปลี่ยนเป็น: pending, waiting_stock, ready_to_pick, cancelled, replaced, resolved
        """
        try:
            data = request.get_json()
            shortage_id = data.get("shortage_id")
            new_status = data.get("status", "").strip()
            force = data.get("force", False)  # สำหรับ Force Resolve
            notes = data.get("notes", "").strip()

            if not shortage_id or not new_status:
                return jsonify({"success": False, "error": "ข้อมูลไม่ครบ"}), 400

            # Validate status
            valid_statuses = ["pending", "waiting_stock", "ready_to_pick", "cancelled", "replaced", "resolved"]
            if new_status not in valid_statuses:
                return jsonify({"success": False, "error": f"สถานะไม่ถูกต้อง: {new_status}"}), 400

            shortage = db.session.get(ShortageQueue, shortage_id)
            if not shortage:
                return jsonify({"success": False, "error": "ไม่พบ Shortage Record"}), 404

            cu = current_user()
            now = now_thai()

            # ✅ Validation: ถ้าเปลี่ยนเป็น 'resolved' ต้องตรวจสอบว่าหยิบครบหรือยัง
            if new_status == "resolved" and not force:
                order_line = shortage.order_line
                if order_line:
                    expected_picked = shortage.qty_required - shortage.qty_shortage
                    actual_picked = order_line.picked_qty or 0

                    if actual_picked < expected_picked:
                        return jsonify({
                            "success": False,
                            "warning": True,  # Flag สำหรับแสดง Confirmation Dialog
                            "error": f"⚠️ ยังหยิบไม่ครบ!\n\nSKU: {shortage.sku}\nต้องหยิบ: {expected_picked} ชิ้น\nหยิบแล้ว: {actual_picked} ชิ้น\nขาดอีก: {expected_picked - actual_picked} ชิ้น\n\nคุณต้องการบังคับเปลี่ยนสถานะหรือไม่?",
                            "shortage_id": shortage_id,
                            "expected_picked": expected_picked,
                            "actual_picked": actual_picked
                        }), 400

            # Update status
            old_status = shortage.status
            shortage.status = new_status

            # Update metadata
            if new_status in ["cancelled", "replaced", "resolved"]:
                shortage.resolved_at = now
                shortage.resolved_by_user_id = cu.id
                shortage.resolved_by_username = cu.username

            if notes:
                shortage.resolution_notes = (shortage.resolution_notes or "") + f"\n[{now}] Status changed: {old_status} → {new_status} by {cu.username}: {notes}"

            # ✅ ลด shortage_qty ใน OrderLine เมื่อเปลี่ยนเป็น resolved/cancelled/replaced
            if new_status in ['cancelled', 'resolved', 'replaced']:
                order_line = shortage.order_line
                if order_line:
                    current_shortage = order_line.shortage_qty or 0
                    order_line.shortage_qty = max(0, current_shortage - shortage.qty_shortage)

            db.session.commit()

            # Audit Log
            log_audit(
                action="shortage_status_change",
                details={
                    "shortage_id": shortage_id,
                    "order_id": shortage.order_id,
                    "sku": shortage.sku,
                    "old_status": old_status,
                    "new_status": new_status,
                    "force": force,
                    "changed_by": cu.username
                }
            )

            # ✅ Recalculate Batch Progress
            batch_progress = None
            if shortage.original_batch_id:
                try:
                    progress_data = calculate_batch_progress(shortage.original_batch_id)
                    batch_progress = {
                        "batch_id": shortage.original_batch_id,
                        "progress_percent": progress_data["progress_percent"],
                        "completed_qty": progress_data["completed_qty"],
                        "total_qty": progress_data["total_qty"]
                    }
                except Exception as e:
                    print(f"Warning: Could not calculate batch progress: {e}")

            return jsonify({
                "success": True,
                "message": f"เปลี่ยนสถานะสำเร็จ: {old_status} → {new_status}",
                "old_status": old_status,
                "new_status": new_status,
                "batch_progress": batch_progress
            })

        except Exception as e:
            print(f"ERROR in /api/shortage/change-status: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"เกิดข้อผิดพลาด: {str(e)}"
            }), 500

    # -----------------------
    # Shortage Analytics Dashboard (Option 2 - Phase 3)
    # -----------------------
    @app.route("/analytics/shortage")
    @login_required
    def shortage_analytics():
        """
        Shortage Analytics Dashboard
        Displays root cause analysis and trends for shortage management
        """
        # ✅ Priority 1.4: Add error handling
        try:
            from datetime import date, timedelta
            from sqlalchemy import func, case

            # Date range for analysis (default: last 30 days)
            days_range = request.args.get("days", default=30, type=int)

            # Validate days_range
            if days_range not in [7, 30, 90]:
                days_range = 30

            end_date = date.today()
            start_date = end_date - timedelta(days=days_range)

            # ========== 1. Pre-pick vs Post-pick Breakdown ==========
            type_breakdown = db.session.query(
                ShortageQueue.shortage_type,
                func.count(ShortageQueue.id).label('count'),
                func.sum(ShortageQueue.qty_shortage).label('total_qty')
            ).filter(
                ShortageQueue.created_at >= start_date
            ).group_by(
                ShortageQueue.shortage_type
            ).all()

            pre_pick_count = 0
            post_pick_count = 0
            no_type_count = 0
            pre_pick_qty = 0
            post_pick_qty = 0

            for row in type_breakdown:
                if row.shortage_type == 'PRE_PICK':
                    pre_pick_count = row.count
                    pre_pick_qty = row.total_qty or 0
                elif row.shortage_type == 'POST_PICK':
                    post_pick_count = row.count
                    post_pick_qty = row.total_qty or 0
                else:
                    no_type_count += row.count

            total_shortages = pre_pick_count + post_pick_count + no_type_count

            # ========== 2. Shortage by Reason Code ==========
            reason_breakdown = db.session.query(
                ShortageQueue.shortage_reason,
                func.count(ShortageQueue.id).label('count'),
                func.sum(ShortageQueue.qty_shortage).label('total_qty')
            ).filter(
                ShortageQueue.created_at >= start_date
            ).group_by(
                ShortageQueue.shortage_reason
            ).order_by(
                func.count(ShortageQueue.id).desc()
            ).all()

            # ========== 3. Top 10 SKUs with Most Shortages ==========
            top_skus = db.session.query(
                ShortageQueue.sku,
                func.count(ShortageQueue.id).label('shortage_count'),
                func.sum(ShortageQueue.qty_shortage).label('total_shortage_qty')
            ).filter(
                ShortageQueue.created_at >= start_date
            ).group_by(
                ShortageQueue.sku
            ).order_by(
                func.sum(ShortageQueue.qty_shortage).desc()
            ).limit(10).all()

            # Get product names for top SKUs (using OrderLine.item_name)
            top_skus_data = []
            for sku_row in top_skus:
                # Get first OrderLine with this SKU to get product name
                order_line = OrderLine.query.filter_by(sku=sku_row.sku).first()
                product_name = order_line.item_name if order_line else '-'

                top_skus_data.append({
                    'sku': sku_row.sku,
                    'product_name': product_name,
                    'shortage_count': sku_row.shortage_count,
                    'total_shortage_qty': sku_row.total_shortage_qty
                })

            # ========== 4. Daily Shortage Trend (Last 30 Days) ==========
            # Generate date range
            date_range = []
            for i in range(days_range):
                date_range.append(start_date + timedelta(days=i))

            # Query daily shortage counts
            daily_shortages = db.session.query(
                func.date(ShortageQueue.created_at).label('date'),
                func.count(ShortageQueue.id).label('count'),
                func.sum(ShortageQueue.qty_shortage).label('total_qty')
            ).filter(
                ShortageQueue.created_at >= start_date
            ).group_by(
                func.date(ShortageQueue.created_at)
            ).all()

            # Create dictionary for easy lookup
            daily_data = {row.date: {'count': row.count, 'qty': row.total_qty or 0} for row in daily_shortages}

            # Fill in missing dates with zeros
            trend_data = []
            for d in date_range:
                trend_data.append({
                    'date': d.strftime('%Y-%m-%d'),
                    'date_thai': d.strftime('%d/%m') + f'/{d.year + 543}',
                    'count': daily_data.get(d, {}).get('count', 0),
                    'qty': daily_data.get(d, {}).get('qty', 0)
                })

            # ========== 5. Shortage Status Summary ==========
            status_summary = db.session.query(
                ShortageQueue.status,
                func.count(ShortageQueue.id).label('count')
            ).filter(
                ShortageQueue.created_at >= start_date
            ).group_by(
                ShortageQueue.status
            ).all()

            status_counts = {row.status: row.count for row in status_summary}

            # ========== 6. Reason Code Labels (for chart) ==========
            reason_labels = {
                'CANT_FIND': '🔍 หาไม่เจอ',
                'FOUND_DAMAGED': '💔 ของชำรุด',
                'MISPLACED': '📦 วางผิดที่',
                'BARCODE_MISSING': '🏷️ บาร์โค้ดหลุด',
                'STOCK_NOT_FOUND': '❌ ไม่มีในระบบ',
                'OTHER': '📝 อื่นๆ'
            }

            # ========== 7. Shortage Logs (Latest 20) ==========
            shortage_logs = ShortageQueue.query.filter(
                ShortageQueue.created_at >= start_date
            ).order_by(
                ShortageQueue.created_at.desc()
            ).limit(20).all()

            # ✅ Priority 2.4: Pass empty state flag to template
            return render_template(
                "shortage_analytics.html",
                # Date range
                days_range=days_range,
                start_date=start_date,
                end_date=end_date,

                # Type breakdown
                pre_pick_count=pre_pick_count,
                post_pick_count=post_pick_count,
                no_type_count=no_type_count,
                total_shortages=total_shortages,
                pre_pick_qty=pre_pick_qty,
                post_pick_qty=post_pick_qty,

                # Reason breakdown
                reason_breakdown=reason_breakdown,
                reason_labels=reason_labels,

                # Top SKUs
                top_skus=top_skus_data,

                # Trend data
                trend_data=trend_data,

                # Status summary
                status_counts=status_counts,

                # Shortage logs
                shortage_logs=shortage_logs,

                # Empty state
                empty_state=(total_shortages == 0)
            )

        except Exception as e:
            flash(f"เกิดข้อผิดพลาดในการโหลดข้อมูล Analytics: {str(e)}", "danger")
            import traceback
            traceback.print_exc()
            return redirect(url_for("dashboard"))

    # -----------------------
    # Scan Tracking (ส่งของ)
    # -----------------------
    @app.route("/scan/tracking")
    @login_required
    def scan_tracking():
        """หน้าสแกน Tracking Number เพื่อส่งมอบให้ขนส่ง"""
        return render_template("scan_tracking.html")

    @app.route("/api/scan/tracking", methods=["POST"])
    @login_required
    def api_scan_tracking():
        """API สำหรับสแกน Tracking Number และแสดงข้อมูลออเดอร์ (รองรับ Partial Picking)"""
        data = request.get_json()
        tracking = data.get("tracking", "").strip()

        if not tracking:
            return jsonify({"success": False, "error": "กรุณาระบุ Tracking Number"}), 400

        # หาออเดอร์จาก tracking_number
        orders = OrderLine.query.filter_by(tracking_number=tracking).all()

        if not orders:
            return jsonify({
                "success": False,
                "error": f"ไม่พบออเดอร์ที่มี Tracking: {tracking}"
            }), 404

        # ใช้ข้อมูลจากออเดอร์แรก (order_id เดียวกัน)
        first_order = orders[0]
        shop = db.session.get(Shop, first_order.shop_id)

        # คำนวณสถานะใหม่โดยใช้ calculate_order_status
        order_status = calculate_order_status(orders)

        # คำนวณข้อมูล shortage
        total_shortage = sum(getattr(o, 'shortage_qty', 0) or 0 for o in orders)
        total_qty = sum(o.qty for o in orders)
        total_picked = sum(o.picked_qty or 0 for o in orders)

        # สร้างรายการสินค้าที่มี shortage
        shortage_items = []
        for order in orders:
            shortage_qty = getattr(order, 'shortage_qty', 0) or 0
            if shortage_qty > 0:
                shortage_items.append({
                    "sku": order.sku,
                    "item_name": order.item_name,
                    "shortage_qty": shortage_qty,
                    "picked_qty": order.picked_qty or 0,
                    "total_qty": order.qty
                })

        # กำหนดว่าสามารถ dispatch ได้หรือไม่
        # เฉพาะออเดอร์ที่ status = "ready" เท่านั้นที่ส่งได้
        can_dispatch = (order_status == "ready")

        return jsonify({
            "success": True,
            "tracking": tracking,
            "platform": first_order.platform,
            "shop": shop.name if shop else "",
            "order_id": first_order.order_id,
            "batch_id": first_order.batch_id,
            "carrier": first_order.carrier,
            "status": order_status,
            "item_count": len(orders),
            "total_qty": total_qty,
            "total_picked": total_picked,
            "total_shortage": total_shortage,
            "shortage_items": shortage_items,
            "can_dispatch": can_dispatch,
            "status_message": {
                "ready": "พร้อมส่ง - ครบทุกรายการ",
                "partial_ready": f"หยิบได้บางส่วน - ขาดสินค้า {total_shortage} ชิ้น",
                "pending_refill": f"รอเติมของ - ขาดสินค้า {total_shortage} ชิ้น",
                "pending": "ยังไม่เริ่มหยิบ",
                "dispatched": "ส่งไปแล้ว"
            }.get(order_status, order_status)
        })

    @app.route("/api/confirm-dispatch", methods=["POST"])
    @login_required
    def api_confirm_dispatch():
        """API สำหรับยืนยันส่งมอบให้ขนส่ง (รองรับ Partial Picking - ส่งได้เฉพาะออเดอร์ที่ครบเท่านั้น)"""
        data = request.get_json()
        tracking = data.get("tracking", "").strip()

        if not tracking:
            return jsonify({"success": False, "error": "กรุณาระบุ Tracking Number"}), 400

        orders = OrderLine.query.filter_by(tracking_number=tracking).all()

        if not orders:
            return jsonify({"success": False, "error": "ไม่พบออเดอร์"}), 404

        # คำนวณสถานะโดยใช้ calculate_order_status
        order_status = calculate_order_status(orders)

        # ตรวจสอบว่าส่งไปแล้วหรือยัง
        if order_status == "dispatched":
            return jsonify({
                "success": False,
                "error": "ออเดอร์นี้ส่งไปแล้ว"
            }), 400

        # ตรวจสอบว่าพร้อมส่งหรือไม่ - เฉพาะ status "ready" เท่านั้นที่ส่งได้
        if order_status != "ready":
            # คำนวณรายละเอียด shortage
            total_shortage = sum(getattr(o, 'shortage_qty', 0) or 0 for o in orders)
            shortage_items = [
                f"{o.sku} (ขาด {getattr(o, 'shortage_qty', 0)} ชิ้น)"
                for o in orders if getattr(o, 'shortage_qty', 0) and getattr(o, 'shortage_qty', 0) > 0
            ]

            error_messages = {
                "partial_ready": f"ออเดอร์นี้หยิบได้บางส่วน มีสินค้าขาด {total_shortage} ชิ้น ไม่สามารถส่งได้\n\nสินค้าที่ขาด:\n" + "\n".join(shortage_items),
                "pending_refill": f"ออเดอร์นี้มีสินค้าขาด {total_shortage} ชิ้น รอเติมสต็อก ไม่สามารถส่งได้\n\nสินค้าที่ขาด:\n" + "\n".join(shortage_items),
                "pending": "ออเดอร์นี้ยังไม่เริ่มหยิบของ กรุณาไปหน้า 'หยิบของ' เพื่อหยิบสินค้า"
            }

            return jsonify({
                "success": False,
                "error": error_messages.get(order_status, "ออเดอร์นี้ยังไม่พร้อมส่ง"),
                "order_status": order_status,
                "total_shortage": total_shortage
            }), 400

        cu = current_user()
        now = now_thai()

        # อัปเดตสถานะเป็น dispatched
        for order in orders:
            order.dispatch_status = "dispatched"
            order.dispatched_at = now
            order.dispatched_by_user_id = cu.id
            order.dispatched_by_username = cu.username

        db.session.commit()

        # บันทึก Audit Log
        log_audit(
            action="confirm_dispatch",
            details={
                "tracking": tracking,
                "order_id": orders[0].order_id,
                "carrier": orders[0].carrier,
                "dispatched_by": cu.username
            },
            batch_id=orders[0].batch_id
        )

        return jsonify({
            "success": True,
            "tracking": tracking,
            "dispatched_by": cu.username,
            "dispatched_at": now.isoformat(),
            "message": "ส่งมอบให้ขนส่งเรียบร้อยแล้ว"
        })

    return app


app = create_app()

if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", "8000"))
    serve(app, host="0.0.0.0", port=port)