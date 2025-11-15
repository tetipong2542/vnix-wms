
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

from utils import (
    now_thai, to_thai_be, to_be_date_str, TH_TZ, current_be_year,
    normalize_platform, sla_text, compute_due_date
)
from models import db, Shop, Product, Stock, Sales, OrderLine, User, Batch, AuditLog
from importers import import_products, import_stock, import_sales, import_orders
from allocation import compute_allocation


APP_NAME = os.environ.get("APP_NAME", "VNIX Order Management")


# -----------------------------
# สร้างแอป + บูตระบบเบื้องต้น
# -----------------------------
def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "vnix-secret")

    db_path = os.path.join(os.path.dirname(__file__), "data.db")
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
        # bootstrap admin
        if User.query.count() == 0:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
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
            shop = Shop.query.get(first_item.shop_id) if first_item.shop_id else None
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
        has_shortage = any(line.shortage_qty and line.shortage_qty > 0 for line in order_lines)

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

    def get_next_run_number(platform: str, batch_date: date = None) -> int:
        """
        Get next available run number for a platform and date.
        Returns max(run_no) + 1, or 1 if no batches exist.
        """
        if batch_date is None:
            batch_date = now_thai().date()
        
        platform_std = normalize_platform(platform)
        
        # Query for max run number on this platform and date
        max_run = db.session.query(func.max(Batch.run_no))\
            .filter_by(platform=platform_std, batch_date=batch_date)\
            .scalar()
        
        return (max_run or 0) + 1

    def create_batch_from_pending(platform: str, run_no: int, batch_date: date = None) -> Batch:
        """
        FR-04 to FR-07: Create batch from pending orders
        - Selects orders with batch_status='pending_batch'
        - Creates Batch record with summary
        - Updates orders to batch_status='batched'
        - Locks batch immediately
        """
        if batch_date is None:
            batch_date = now_thai().date()

        platform_std = normalize_platform(platform)
        batch_id = generate_batch_id(platform_std, batch_date, run_no)

        # Check if batch already exists
        existing = Batch.query.get(batch_id)
        if existing:
            raise ValueError(f"Batch {batch_id} already exists")

        # Get pending orders for this platform
        pending_orders = OrderLine.query.filter_by(
            platform=platform_std,
            batch_status="pending_batch"
        ).all()

        if not pending_orders:
            raise ValueError(f"No pending orders found for {platform_std}")

        # Compute summary
        summary = compute_batch_summary(pending_orders)

        # Create batch
        cu = current_user()
        batch = Batch(
            batch_id=batch_id,
            platform=platform_std,
            run_no=run_no,
            batch_date=batch_date,
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

        # Update orders to batched status
        for order in pending_orders:
            order.batch_status = "batched"
            order.batch_id = batch_id

        db.session.commit()

        # Log audit
        log_audit("create_batch", {
            "batch_id": batch_id,
            "platform": platform_std,
            "run_no": run_no,
            "summary": summary
        }, batch_id=batch_id, order_count=summary["total_orders"])

        return batch

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
        for r in rows:
            if (r.get("order_id") or "").strip() in packed_oids:
                r["allocation_status"] = "PACKED"
                r["packed"] = True
                r["actions_disabled"] = True
            else:
                r["actions_disabled"] = False

        orders_ready = _orders_ready_set(rows)
        orders_low_order = _orders_lowstock_order_set(rows)
        orders_accepted = _orders_accepted_set(rows)
        orders_shortage = _orders_shortage_set(rows)
        status_norm = (status or "").strip().upper()

        if status_norm in {"PACKED"}:
            rows = [r for r in rows if (r.get("order_id") or "").strip() in packed_oids]
        else:
            rows = [r for r in rows if (r.get("order_id") or "").strip() not in packed_oids]
            if status_norm == "ORDER_READY":
                rows = [r for r in rows if (r.get("order_id") or "").strip() in orders_ready]
            elif status_norm in {"ORDER_LOW_STOCK", "ORDER_LOW"}:
                rows = [r for r in rows if (r.get("order_id") or "").strip() in orders_low_order]
            elif status_norm:
                rows = [r for r in rows if (r.get("allocation_status") or "").strip().upper() == status_norm]

        def _sort_key(r):
            return ((r.get("order_id") or ""), (r.get("platform") or ""), (r.get("shop") or ""), (r.get("sku") or ""))
        rows = sorted(rows, key=_sort_key)

        kpis = {
            "ready":     sum(1 for r in rows if r["allocation_status"] == "READY_ACCEPT"),
            "accepted":  sum(1 for r in rows if r["allocation_status"] == "ACCEPTED"),
            "low":       sum(1 for r in rows if r["allocation_status"] == "LOW_STOCK"),
            "nostock":   sum(1 for r in rows if r["allocation_status"] == "SHORTAGE"),
            "notenough": sum(1 for r in rows if r["allocation_status"] == "NOT_ENOUGH"),
            "packed":    len(packed_oids),
            "total_items": len(rows),
            "total_qty":   sum(int(r.get("qty", 0) or 0) for r in rows),
            "orders_unique": len({(r.get("order_id") or "").strip() for r in rows if r.get("order_id")}),
            "orders_ready": len(orders_ready),
            "orders_low":   len(orders_low_order),
            "orders_accepted": len(orders_accepted),
            "orders_shortage": len(orders_shortage),
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
            kpis=kpis,
            packed_oids=packed_oids,
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
                return redirect(url_for("dashboard", import_date=now_thai().date().isoformat()))
            except Exception as e:
                flash(f"เกิดข้อผิดพลาดในการนำเข้าออเดอร์: {e}", "danger")
                return redirect(url_for("import_orders_view"))
        shops = Shop.query.order_by(Shop.name.asc()).all()
        return render_template("import_orders.html", shops=shops)

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
                flash(f"นำเข้าสินค้าสำเร็จ {cnt} รายการ", "success")
                return redirect(url_for("dashboard"))
            except Exception as e:
                flash(f"เกิดข้อผิดพลาดในการนำเข้าสินค้า: {e}", "danger")
                return redirect(url_for("import_products_view"))
        return render_template("import_products.html")

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
                flash(f"นำเข้าสต็อกสำเร็จ {cnt} รายการ", "success")
                return redirect(url_for("dashboard"))
            except Exception as e:
                flash(f"เกิดข้อผิดพลาดในการนำเข้าสต็อก: {e}", "danger")
                return redirect(url_for("import_stock_view"))
        return render_template("import_stock.html")

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
                flash(f"นำเข้าไฟล์สั่งขายสำเร็จ {cnt} รายการ", "success")
                return redirect(url_for("dashboard"))
            except Exception as e:
                flash(f"เกิดข้อผิดพลาดในการนำเข้าไฟล์สั่งขาย: {e}", "danger")
                return redirect(url_for("import_sales_view"))
        return render_template("import_sales.html")

    # -----------------------
    # Batch Management Routes (FR-04 to FR-09)
    # -----------------------
    @app.route("/batch/list")
    @login_required
    def batch_list():
        """Display all batches with summary"""
        batches = Batch.query.order_by(Batch.created_at.desc()).all()

        # Count pending orders by platform
        pending_by_platform = db.session.query(
            OrderLine.platform,
            func.count(func.distinct(OrderLine.order_id))
        ).filter_by(batch_status="pending_batch").group_by(OrderLine.platform).all()

        pending_counts = {platform: count for platform, count in pending_by_platform}

        return render_template("batch_list.html", batches=batches, pending_counts=pending_counts)

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
                # Preview: count pending orders
                platform_std = normalize_platform(platform)
                pending = OrderLine.query.filter_by(
                    platform=platform_std,
                    batch_status="pending_batch"
                ).all()

                if pending:
                    preview_summary = compute_batch_summary(pending)
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
            run_no = int(request.form.get("run_no", 1))

            try:
                batch = create_batch_from_pending(platform, run_no)
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

        # Parse shop summary
        try:
            shop_summary = json.loads(batch.shop_summary) if batch.shop_summary else {}
        except:
            shop_summary = {}

        # Carrier summary
        carrier_summary = {
            "SPX": batch.spx_count,
            "Flash": batch.flash_count,
            "LEX": batch.lex_count,
            "J&T": batch.jt_count,
            "Other": batch.other_count
        }

        return render_template(
            "batch_detail.html",
            batch=batch,
            orders=orders,
            carrier_summary=carrier_summary,
            shop_summary=shop_summary
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
            
            return jsonify({
                "success": True,
                "next_run": next_run,
                "batch_id_preview": batch_id_preview,
                "batch_date": batch_date.isoformat(),
                "platform": platform_std,
                "total_orders": summary["total_orders"],
                "carrier_summary": summary["carrier_summary"],
                "shop_summary": summary["shop_summary"]
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
        """
        try:
            platform_std = normalize_platform(platform)
            batch_date = now_thai().date()
            
            # Get next run number automatically
            next_run = get_next_run_number(platform_std, batch_date)
            
            # Create batch
            batch = create_batch_from_pending(platform_std, next_run, batch_date)
            
            # Additional audit log for quick create
            log_audit("quick_create_batch", {
                "batch_id": batch.batch_id,
                "platform": platform_std,
                "run_no": next_run,
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
        
        # DEBUG: Print first item to check data
        if items:
            print(f"DEBUG - First item logistic: '{items[0].get('logistic')}'")
            print(f"DEBUG - First item logistics_counter: {items[0].get('logistics_counter')}")
        
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
        for order in orders:
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

        # แปลงเป็น list และเรียงตาม SKU
        sku_list = sorted(sku_dict.values(), key=lambda x: x["sku"])

        return render_template(
            "sku_qr_print.html",
            batch=batch,
            sku_list=sku_list,
            total_skus=len(sku_list)
        )

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
    @app.route("/admin/clear", methods=["GET","POST"])
    @login_required
    def admin_clear():
        if request.method=="POST":
            scope = request.form.get("scope")
            if scope == "today":
                today = now_thai().date()
                OrderLine.query.filter(OrderLine.import_date==today).delete()
                db.session.commit()
                flash("ลบข้อมูลของวันนี้แล้ว", "warning")
            elif scope == "all":
                OrderLine.query.delete(); db.session.commit()
                flash("ลบข้อมูลออเดอร์ทั้งหมดแล้ว", "danger")
            return redirect(url_for("dashboard"))
        return render_template("clear_confirm.html")

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

    @app.route("/api/scan/sku", methods=["POST"])
    @login_required
    def api_scan_sku():
        """API สำหรับสแกน SKU และแสดงข้อมูล Need/Picked/Remaining (รองรับ Partial Picking)"""
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

        # คำนวณ Need / Picked / Remaining / Shortage
        total_need = sum(o.qty for o in orders)
        total_picked = sum(o.picked_qty or 0 for o in orders)
        total_shortage = sum(o.shortage_qty or 0 for o in orders)
        total_remaining = total_need - total_picked

        # ดึงข้อมูลสินค้า
        product = Product.query.filter_by(sku=sku).first()
        stock = Stock.query.filter_by(sku=sku).first()
        stock_qty = stock.qty if stock else 0

        # สร้างรายการออเดอร์ที่ต้องการ SKU นี้
        order_list = []
        for order in orders:
            order_list.append({
                "order_id": order.order_id,
                "qty": order.qty,
                "picked_qty": order.picked_qty or 0,
                "shortage_qty": order.shortage_qty or 0,
                "status": order.dispatch_status
            })

        return jsonify({
            "success": True,
            "sku": sku,
            "brand": product.brand if product else "",
            "model": product.model if product else "",
            "stock_qty": stock_qty,
            "total_need": total_need,
            "total_picked": total_picked,
            "total_shortage": total_shortage,
            "total_remaining": total_remaining,
            "order_count": len(orders),
            "orders": order_list,
            "can_fulfill": stock_qty >= total_remaining,
            "suggested_pick_qty": min(stock_qty, total_remaining)
        })

    @app.route("/api/pick/sku", methods=["POST"])
    @login_required
    def api_pick_sku():
        """API สำหรับบันทึกการหยิบ SKU (รองรับ Partial Picking)"""
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

                    # คำนวณ shortage
                    still_need = order.qty - order.picked_qty
                    order.shortage_qty = still_need

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

        db.session.commit()

        # บันทึก Audit Log
        log_audit(
            action="pick_sku" if not mark_shortage else "mark_shortage",
            details={
                "sku": sku,
                "qty_picked": qty,
                "picked_by": cu.username,
                "mark_shortage": mark_shortage,
                "orders_affected": len(picked_orders) + len(shortage_orders)
            }
        )

        # คำนวณข้อมูลใหม่
        total_need = sum(o.qty for o in orders)
        total_picked = sum(o.picked_qty for o in orders)
        total_shortage = sum(o.shortage_qty or 0 for o in orders)
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
        total_shortage = sum(o.shortage_qty or 0 for o in orders)
        total_qty = sum(o.qty for o in orders)
        total_picked = sum(o.picked_qty or 0 for o in orders)

        # สร้างรายการสินค้าที่มี shortage
        shortage_items = []
        for order in orders:
            if order.shortage_qty and order.shortage_qty > 0:
                shortage_items.append({
                    "sku": order.sku,
                    "item_name": order.item_name,
                    "shortage_qty": order.shortage_qty,
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
            total_shortage = sum(o.shortage_qty or 0 for o in orders)
            shortage_items = [
                f"{o.sku} (ขาด {o.shortage_qty} ชิ้น)"
                for o in orders if o.shortage_qty and o.shortage_qty > 0
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