
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from utils import TH_TZ

db = SQLAlchemy()

class Shop(db.Model):
    __tablename__ = "shops"
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(120), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ))

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    brand = db.Column(db.String(120))
    model = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ))

class Stock(db.Model):
    __tablename__ = "stocks"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), nullable=False, index=True)
    qty = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ), onupdate=lambda: datetime.now(TH_TZ))

class Sales(db.Model):
    __tablename__ = "sales"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(128), nullable=False, index=True)
    po_no = db.Column(db.String(128))
    status = db.Column(db.String(64))  # เปิดใบขายครบตามจำนวนแล้ว / ยังไม่มีการเปิดใบขาย
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ))

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), default="user")  # admin/user
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ))

class OrderLine(db.Model):
    __tablename__ = "order_lines"
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    order_id = db.Column(db.String(128), nullable=False)
    sku = db.Column(db.String(64), nullable=False)
    qty = db.Column(db.Integer, default=1)
    item_name = db.Column(db.String(512))
    order_time = db.Column(db.DateTime)  # tz-aware
    logistic_type = db.Column(db.String(255))
    carrier = db.Column(db.String(64))  # FR-02: SPX/Flash/LEX/J&T/etc
    imported_at = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ))
    import_date = db.Column(db.Date)  # วันที่นำเข้า (อ้างอิง พ.ศ. ในหน้า UI)

    # FR-03: Batch management
    batch_status = db.Column(db.String(20), default="pending_batch")  # pending_batch, batched
    batch_id = db.Column(db.String(64), db.ForeignKey("batches.batch_id"))

    accepted = db.Column(db.Boolean, default=False)
    accepted_at = db.Column(db.DateTime)
    accepted_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    accepted_by_username = db.Column(db.String(64))

    # Tracking & Dispatch Management
    tracking_number = db.Column(db.String(128))  # เลข tracking จากขนส่ง

    # Picking Management
    picked_qty = db.Column(db.Integer, default=0)  # จำนวนที่หยิบไปแล้ว
    picked_at = db.Column(db.DateTime)  # เวลาที่หยิบ
    picked_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    picked_by_username = db.Column(db.String(64))

    # Dispatch Management
    dispatch_status = db.Column(db.String(20), default="pending")  # pending, ready, dispatched
    dispatched_at = db.Column(db.DateTime)  # เวลาที่ส่งมอบให้ขนส่ง
    dispatched_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    dispatched_by_username = db.Column(db.String(64))

    __table_args__ = (
        db.UniqueConstraint('platform', 'shop_id', 'order_id', 'sku', name='uq_orderline'),
    )


class Batch(db.Model):
    """FR-06: Batch model for grouping orders"""
    __tablename__ = "batches"
    batch_id = db.Column(db.String(64), primary_key=True)  # e.g., SH-2024-11-13-R1
    platform = db.Column(db.String(20), nullable=False, index=True)
    run_no = db.Column(db.Integer, nullable=False)  # 1, 2, 3...
    batch_date = db.Column(db.Date, nullable=False, index=True)

    # Summary counts (FR-08)
    total_orders = db.Column(db.Integer, default=0)
    spx_count = db.Column(db.Integer, default=0)
    flash_count = db.Column(db.Integer, default=0)
    lex_count = db.Column(db.Integer, default=0)
    jt_count = db.Column(db.Integer, default=0)
    other_count = db.Column(db.Integer, default=0)

    # Shop summary (stored as JSON string)
    shop_summary = db.Column(db.Text)  # JSON: {"shop_name": count}

    # FR-07: Lock status
    locked = db.Column(db.Boolean, default=True)

    # Audit fields
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_by_username = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ), index=True)

    # Relationships
    orders = db.relationship("OrderLine", backref="batch", lazy="dynamic")
    
    # Composite index for common queries
    __table_args__ = (
        db.Index('idx_batch_platform_date', 'platform', 'batch_date'),
    )


class AuditLog(db.Model):
    """NFR-03: Audit trail for all important actions"""
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(64), nullable=False)  # import, create_batch, print_jobsheet, print_picklist
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    username = db.Column(db.String(64))
    details = db.Column(db.Text)  # JSON string with action details
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ))

    # References
    batch_id = db.Column(db.String(64), db.ForeignKey("batches.batch_id"))
    order_count = db.Column(db.Integer)
    print_count = db.Column(db.Integer)  # for print actions
