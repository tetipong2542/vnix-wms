
# importers.py
from __future__ import annotations

import pandas as pd
from datetime import datetime, date
from flask import flash
from sqlalchemy.exc import IntegrityError

from utils import parse_datetime_guess, normalize_platform, TH_TZ, now_thai
from models import db, Shop, Product, Stock, StockTransaction, Sales, OrderLine, ShortageQueue

# ===== Column dictionaries =====
COMMON_ORDER_ID   = ["orderNumber","Order Number","order_id","Order ID","order_sn","Order No","เลข Order","No.","OrderNo"]
COMMON_SKU        = ["sellerSku","Seller SKU","SKU","Sku","Item SKU","SKU Reference No.","รหัสสินค้า"]
COMMON_ITEM_NAME  = ["itemName","Item Name","Product Name","ชื่อสินค้า","ชื่อรุ่น","title","name"]
COMMON_QTY        = ["quantity","Quantity","Qty","จำนวน","จำนวนที่สั่ง","Purchased Qty","Order Item Qty"]
COMMON_ORDER_TIME = ["createdAt","create_time","created_time","Order Time","OrderDate","Order Date","วันที่สั่งซื้อ","Paid Time","paid_time","Created Time","createTime","Created Time"]
COMMON_LOGISTICS  = ["logistic_type","Logistics Service","Shipping Provider","ประเภทขนส่ง","Shipment Method","Delivery Type"]
COMMON_CARRIER    = ["Carrier","Shipping Carrier","carrier","ผู้ให้บริการขนส่ง","Shipment Provider"]
COMMON_TRACKING   = ["Tracking Number","tracking_number","tracking","Tracking No","Tracking No.","เลข Tracking","AWB","tracking_no","trackingNo","Tracking Code"]

# >>> ขยายตัวเลือกหัวคอลัมน์สต็อก (กันเคสหลากหลาย/ภาษาไทย-อังกฤษ)
COMMON_STOCK_SKU  = [
    "รหัสสินค้า","SKU","sku","รหัส","รหัส สินค้า","รหัสสินค้า*",
    "รหัสสินค้า Sabuy Soft","SKU Reference No.","รหัส/sku","รหัสสินค้า/sku"
]
COMMON_STOCK_QTY  = [
    "คงเหลือ","Stock","stock","Available","จำนวน","Qty","QTY","STOCK","ปัจจุบัน",
    "ยอดคงเหลือ","จำนวนคงเหลือ","คงเหลือในสต๊อก"
]

COMMON_PRODUCT_SKU   = ["รหัสสินค้า","SKU","sku"]
COMMON_PRODUCT_BRAND = ["Brand","แบรนด์"]
COMMON_PRODUCT_MODEL = ["ชื่อสินค้า","รุ่น","Model","Product"]

# ===== helpers =====
def first_existing(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    # fuzzy contains (lower)
    lower_cols = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        key = cand.lower()
        for col_lower, original in lower_cols.items():
            if key == col_lower or key in col_lower:
                return original
    return None


def extract_carrier_from_logistics(logistics_text: str) -> str:
    """
    FR-02: Extract carrier name from logistics text
    Maps various carrier names to standard names: SPX, Flash, LEX, JT, Kerry, Ninja, etc.
    """
    if not logistics_text:
        return "Unknown"

    text = str(logistics_text).upper().strip()

    # Mapping rules
    if "SPX" in text or "SHOPEE EXPRESS" in text or "SHOPEE XPRESS" in text:
        return "SPX"
    elif "FLASH" in text:
        return "Flash"
    elif "LEX" in text or "LAZADA EXPRESS" in text:
        return "LEX"
    elif "J&T" in text or "J AND T" in text or "J T" in text or "JT" in text or "JNT" in text:
        return "J&T"
    elif "KERRY" in text:
        return "Kerry"
    elif "NINJA" in text or "NINJAVAN" in text:
        return "Ninja"
    elif "BEST" in text:
        return "Best"
    elif "THAILAND POST" in text or "EMS" in text or "ไปรษณีย์" in text:
        return "ThaiPost"
    else:
        return "Other"

def get_or_create_shop(platform, shop_name):
    platform = normalize_platform(platform)
    shop = Shop.query.filter_by(name=shop_name).first()
    if not shop:
        shop = Shop(platform=platform, name=shop_name)
        db.session.add(shop)
        db.session.commit()
    return shop

# ===== Importers =====
def import_products(df: pd.DataFrame) -> int:
    sku_col   = first_existing(df, COMMON_PRODUCT_SKU)   or "รหัสสินค้า"
    brand_col = first_existing(df, COMMON_PRODUCT_BRAND) or "Brand"
    model_col = first_existing(df, COMMON_PRODUCT_MODEL) or "ชื่อสินค้า"
    cnt = 0
    for _, row in df.iterrows():
        sku = str(row.get(sku_col, "")).strip()
        if not sku:
            continue
        prod = Product.query.filter_by(sku=sku).first()
        if not prod:
            prod = Product(sku=sku)
        prod.brand = str(row.get(brand_col, "")).strip()
        prod.model = str(row.get(model_col, "")).strip()
        db.session.add(prod); cnt += 1
    db.session.commit()
    return cnt

# >>> ฟังก์ชันนี้ถูกแพตช์ใหม่ให้ทน NaN/หัวคอลัมน์หลายแบบ
def import_stock(df: pd.DataFrame) -> int:
    """
    นำเข้าสต็อกจาก DataFrame:
    - รองรับหัวคอลัมน์หลายแบบ (ไทย/อังกฤษ)
    - Qty ว่าง/NaN จะถูกมองเป็น 0 (กัน error: cannot convert float NaN to integer)
    - รวมยอดเมื่อไฟล์มี SKU ซ้ำหลายบรรทัด
    - อัปเดตทั้งตาราง Stock และ (ถ้ามีคอลัมน์) Product.stock_qty
    คืนค่าจำนวนแถวที่บันทึก (insert/update)
    """
    sku_col = first_existing(df, COMMON_STOCK_SKU)
    qty_col = first_existing(df, COMMON_STOCK_QTY)
    if not sku_col:
        raise ValueError("ไม่พบคอลัมน์ SKU/รหัสสินค้า ในไฟล์สต็อก")
    if not qty_col:
        raise ValueError("ไม่พบคอลัมน์ คงเหลือ/Qty/Stock ในไฟล์สต็อก")

    # ตั้งชื่อมาตรฐาน
    df = df.rename(columns={sku_col: "sku", qty_col: "qty"})

    # ทำความสะอาด
    df["sku"] = df["sku"].astype(str).fillna("").map(lambda x: x.strip())
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)

    # คัดแถวที่ไม่มี SKU
    df = df[df["sku"] != ""]
    if df.empty:
        return 0

    # รวมยอดตาม SKU (กันไฟล์ซ้ำแถว)
    agg = df.groupby("sku", as_index=False)["qty"].sum()

    # อัปเดตฐานข้อมูล
    saved = 0
    updated_skus = []  # เก็บ SKU ที่อัปเดตเพื่อตรวจสอบ Shortage

    for _, row in agg.iterrows():
        sku = row["sku"]
        qty = int(row["qty"] or 0)

        st = Stock.query.filter_by(sku=sku).first()
        old_qty = st.qty if st else 0

        if not st:
            st = Stock(sku=sku, qty=qty, reserved_qty=0)
            db.session.add(st)
        else:
            st.qty = qty
            # ✅ FIX: ไม่ reset reserved_qty เมื่อ import stock
            # เพราะ reserved_qty เป็นการจอง Stock ให้ Batch ที่กำลังทำงานอยู่
            # การ import stock ใหม่ควรปรับเฉพาะ total stock (qty) เท่านั้น
            # reserved_qty จะถูกปรับลดเมื่อ Batch dispatch เสร็จแล้ว

        # ✅ Option 2: Log stock transaction (Banking-style)
        if qty != old_qty:
            qty_change = qty - old_qty
            tx = StockTransaction(
                sku=sku,
                transaction_type='RECEIVE' if qty_change > 0 else 'ADJUST',
                quantity=qty_change,
                balance_after=qty,
                reason_code='IMPORT',
                reference_type='import',
                reference_id=f"IMPORT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                created_by='system',
                notes=f"Stock import: {old_qty} → {qty}"
            )
            db.session.add(tx)

        # ถ้ามีฟิลด์ product.stock_qty ให้ sync ด้วย
        prod = Product.query.filter_by(sku=sku).first()
        if prod is not None and hasattr(prod, "stock_qty"):
            try:
                prod.stock_qty = qty
            except Exception:
                # กันชนิดคอลัมน์ไม่ใช่ int
                pass

        saved += 1

        # ✅ NEW: Track all SKU updates (not just increases) for Shortage auto-detection
        if qty != old_qty:
            updated_skus.append({'sku': sku, 'old_qty': old_qty, 'new_qty': qty})

    db.session.commit()

    # ✅ NEW: Recalculate reserved_qty เมื่อ Import Stock ใหม่
    # เพื่อให้ reserved_qty สะท้อนความเป็นจริง (เฉพาะ Orders ที่ยังไม่เสร็จ)
    for _, row in agg.iterrows():
        sku = row["sku"]

        # คำนวณ reserved_qty จริงจากฐานข้อมูล
        # reserved_qty = ผลรวม (qty - picked_qty) ของทุก Order ที่ยังไม่ dispatch
        from models import OrderLine
        from sqlalchemy import func

        result = db.session.query(
            func.sum(OrderLine.qty - OrderLine.picked_qty).label('total_reserved')
        ).filter(
            OrderLine.sku == sku,
            OrderLine.dispatch_status != 'dispatched',
            OrderLine.accepted == True,
            OrderLine.picked_qty < OrderLine.qty  # ยังหยิบไม่ครบ
        ).first()

        calculated_reserved = max(0, result.total_reserved or 0)

        # อัปเดต reserved_qty ใน Stock table
        st = Stock.query.filter_by(sku=sku).first()
        if st:
            old_reserved = st.reserved_qty
            st.reserved_qty = calculated_reserved
            if old_reserved != calculated_reserved:
                print(f"✅ Recalculated Reserved: {sku} - Reserved {old_reserved} → {calculated_reserved}")

    db.session.commit()

    # ✅ NEW: Auto-update Shortage Records based on stock availability
    if updated_skus:
        now = now_thai()
        total_updated_shortages = 0

        for sku_data in updated_skus:
            sku = sku_data['sku']
            old_qty = sku_data['old_qty']
            new_qty = sku_data['new_qty']

            # หา Shortage Records ที่ยัง active (pending, waiting_stock)
            pending_shortages = ShortageQueue.query.filter(
                ShortageQueue.sku == sku,
                ShortageQueue.status.in_(['pending', 'waiting_stock'])
            ).all()

            if pending_shortages:
                # ✅ FIX: เรียง Shortage Records ตาม SLA (เร็วที่สุดก่อน) เพื่อจัดสรรสต็อกตามลำดับความเร่งด่วน
                from models import OrderLine

                # Join กับ OrderLine เพื่อดึง order_time (SLA)
                shortages_with_sla = []
                for shortage in pending_shortages:
                    order_line = OrderLine.query.get(shortage.order_line_id)
                    if order_line:
                        shortages_with_sla.append({
                            'shortage': shortage,
                            'order_time': order_line.order_time or '',
                            'qty_shortage': shortage.qty_shortage or 0
                        })

                # เรียงตาม order_time (SLA เร็วที่สุดก่อน)
                shortages_with_sla.sort(key=lambda x: x['order_time'])

                # คำนวณสต็อกที่มี
                orders = OrderLine.query.filter(
                    OrderLine.sku == sku,
                    OrderLine.dispatch_status != "dispatched",
                    OrderLine.accepted == True
                ).all()

                total_picked = sum(o.picked_qty or 0 for o in orders)
                total_need = sum(o.qty for o in orders)
                total_remaining = total_need - total_picked

                # จัดสรรสต็อกตามลำดับ SLA
                available_stock = new_qty
                updated_count = 0
                fully_covered_count = 0
                partial_covered_count = 0

                for item in shortages_with_sla:
                    shortage = item['shortage']
                    qty_shortage = item['qty_shortage']

                    if available_stock > 0:
                        # มีสต็อกเหลือ → เปลี่ยนเป็น ready_to_pick
                        shortage.status = 'ready_to_pick'

                        # เช็คว่าสต็อกพอครอบคลุม Shortage นี้ครบหรือไม่
                        if available_stock >= qty_shortage:
                            # พอครบ
                            shortage.resolution_notes = (shortage.resolution_notes or "") + f"\n[{now}] สต็อกเข้า ({old_qty} → {new_qty}) - พอหยิบครบ {qty_shortage} ชิ้น [SLA: {item['order_time']}]"
                            available_stock -= qty_shortage
                            fully_covered_count += 1
                        else:
                            # พอบางส่วน
                            shortage.resolution_notes = (shortage.resolution_notes or "") + f"\n[{now}] สต็อกเข้า ({old_qty} → {new_qty}) - หยิบได้ {available_stock}/{qty_shortage} ชิ้น [SLA: {item['order_time']}]"
                            available_stock = 0
                            partial_covered_count += 1

                        updated_count += 1
                    else:
                        # สต็อกหมดแล้ว → ไม่เปลี่ยนสถานะ
                        break

                total_updated_shortages += updated_count

                db.session.commit()

                # แสดง Flash Message
                if fully_covered_count > 0 and partial_covered_count > 0:
                    flash(f'✅ SKU {sku}: สต็อก {old_qty} → {new_qty} ชิ้น | อัปเดต {fully_covered_count} รายการ (ครบ) + {partial_covered_count} รายการ (บางส่วน) ตามลำดับ SLA', 'success')
                elif fully_covered_count > 0:
                    flash(f'✅ SKU {sku}: สต็อก {old_qty} → {new_qty} ชิ้น | อัปเดต {fully_covered_count} รายการเป็น "พร้อมหยิบ" (ครบ) ตามลำดับ SLA', 'success')
                elif partial_covered_count > 0:
                    flash(f'✅ SKU {sku}: สต็อก {old_qty} → {new_qty} ชิ้น | อัปเดต {partial_covered_count} รายการเป็น "พร้อมหยิบ" (บางส่วน) ตามลำดับ SLA', 'success')
                else:
                    flash(f'✅ SKU {sku}: สต็อก {old_qty} → {new_qty} ชิ้น | อัปเดต Shortage ตามลำดับ SLA', 'success')

    # ✅ Phase 3: Reallocate waiting_stock orders after stock import
    if updated_skus:
        realloc_result = reallocate_waiting_orders(updated_skus)

        # แสดง flash messages สำหรับ reallocation
        for msg in realloc_result['messages']:
            flash(msg, 'info')

        # Summary message
        if realloc_result['total_reallocated'] > 0:
            flash(
                f"🔄 จัดสรรสต็อกใหม่สำเร็จ: {realloc_result['total_reallocated']} orders "
                f"ถูกเปลี่ยนจาก 'รอสต็อก' เป็น 'รอสร้าง Batch' ตามลำดับ SLA",
                'success'
            )

    return saved


def reallocate_waiting_orders(updated_skus: list) -> dict:
    """
    ✅ Phase 3: SLA-based Reallocation for waiting_stock orders

    When stock is imported, this function:
    1. Finds orders with batch_status='waiting_stock' for the imported SKUs
    2. Sorts by SLA (earliest first)
    3. Checks if stock is now available
    4. Changes status from 'waiting_stock' to 'pending_batch' if stock is available

    Args:
        updated_skus: List of dicts with {'sku': str, 'old_qty': int, 'new_qty': int}

    Returns:
        dict: {
            'total_reallocated': int,
            'by_sku': {sku: {'reallocated': int, 'still_waiting': int}},
            'messages': [str]
        }
    """
    from models import OrderLine, Stock
    from utils import compute_due_date

    result = {
        'total_reallocated': 0,
        'by_sku': {},
        'messages': []
    }

    if not updated_skus:
        return result

    for sku_data in updated_skus:
        sku = sku_data['sku']
        old_qty = sku_data['old_qty']
        new_qty = sku_data['new_qty']

        # หา orders ที่รอสต็อก สำหรับ SKU นี้
        waiting_orders = OrderLine.query.filter_by(
            sku=sku,
            batch_status="waiting_stock"
        ).all()

        if not waiting_orders:
            continue

        # คำนวณ SLA ถ้ายังไม่มี
        for order in waiting_orders:
            if not order.sla_date and order.order_time:
                order.sla_date = compute_due_date(order.platform, order.order_time)

        # เรียงตาม SLA (เร็วสุดก่อน)
        waiting_orders = sorted(
            waiting_orders,
            key=lambda o: (o.sla_date is None, o.sla_date, o.order_time or datetime.min)
        )

        # ดึงสต็อกปัจจุบัน
        stock = Stock.query.filter_by(sku=sku).first()
        if not stock:
            continue

        available = stock.available_qty  # qty - reserved_qty

        # จัดสรรตามลำดับ SLA
        reallocated = 0
        still_waiting = 0

        for order in waiting_orders:
            if available >= order.qty:
                # ✅ มีสต็อกพอ → เปลี่ยนเป็น pending_batch
                order.batch_status = "pending_batch"
                available -= order.qty
                reallocated += 1

                print(
                    f"  ✅ Reallocated: Order {order.order_id} | "
                    f"SKU {sku} x{order.qty} | "
                    f"SLA: {order.sla_date} | "
                    f"Remaining: {available}"
                )
            else:
                # ❌ สต็อกไม่พอ → ยังคงเป็น waiting_stock
                still_waiting += 1
                print(
                    f"  ⏳ Still Waiting: Order {order.order_id} | "
                    f"SKU {sku} x{order.qty} | "
                    f"SLA: {order.sla_date} | "
                    f"Available: {available}"
                )

        # บันทึกผลลัพธ์
        result['by_sku'][sku] = {
            'reallocated': reallocated,
            'still_waiting': still_waiting,
            'old_qty': old_qty,
            'new_qty': new_qty
        }
        result['total_reallocated'] += reallocated

        # สร้าง message
        if reallocated > 0:
            msg = (
                f"📦 SKU {sku}: สต็อก {old_qty} → {new_qty} | "
                f"จัดสรรให้ {reallocated} orders ตาม SLA"
            )
            if still_waiting > 0:
                msg += f" | ยังรอ {still_waiting} orders"
            result['messages'].append(msg)

    # Commit การเปลี่ยนแปลง
    if result['total_reallocated'] > 0:
        db.session.commit()
        print(f"\n✅ Total Reallocated: {result['total_reallocated']} orders")

    return result


def import_sales(df: pd.DataFrame) -> int:
    order_col  = first_existing(df, ["เลข Order","Order ID","order_id","orderNumber","Order Number"]) or "เลข Order"
    po_col     = first_existing(df, ["เลขที่ PO","PO","เอกสาร","Document No","เลขที่เอกสาร"])
    status_col = first_existing(df, ["สถานะ","Status"])
    cnt = 0
    for _, row in df.iterrows():
        oid = str(row.get(order_col, "")).strip()
        if not oid:
            continue
        sale = Sales.query.filter_by(order_id=oid).first()
        if not sale:
            sale = Sales(order_id=oid)
        sale.po_no = str(row.get(po_col, "") or "").strip() if po_col else None
        sale.status = str(row.get(status_col, "") or "").strip() if status_col else None
        db.session.add(sale); cnt += 1
    db.session.commit()
    return cnt

# ============================
# INSERT-ONLY ORDER IMPORTER
# ============================
def import_orders(df: pd.DataFrame, platform: str, shop_name: str, import_date: date) -> tuple[int, int]:
    """
    เพิ่มเฉพาะรายการที่ 'ยังไม่เคยมี' ในระบบ
    key ความซ้ำ = (order_id + sku) ตามที่ระบุ
    - ถ้าซ้ำ: ข้าม (ไม่นับเพิ่ม, ไม่นับอัปเดต)
    - เก็บวันที่ import เดิมไว้เพื่อ flash เตือนรวมท้ายฟังก์ชัน
    """
    shop = get_or_create_shop(platform, shop_name)
    platform_std = normalize_platform(platform)

    # ค้นหาชื่อคอลัมน์จากไฟล์ที่อาจต่างแพลตฟอร์ม
    order_col = first_existing(df, COMMON_ORDER_ID)
    sku_col   = first_existing(df, COMMON_SKU)
    name_col  = first_existing(df, COMMON_ITEM_NAME)
    qty_col   = first_existing(df, COMMON_QTY)
    time_col  = first_existing(df, COMMON_ORDER_TIME)
    logi_col  = first_existing(df, COMMON_LOGISTICS)
    carrier_col = first_existing(df, COMMON_CARRIER)  # FR-02: dedicated carrier column
    tracking_col = first_existing(df, COMMON_TRACKING)  # Tracking number column

    if not order_col or not sku_col:
        raise ValueError("ไม่พบคอลัมน์ Order ID หรือ SKU ในไฟล์")

    # รวมรายการซ้ำภายในไฟล์เดียวกันก่อน (ตาม key: order_id+sku) เพื่อให้ qty รวมกัน
    grouped: dict[tuple[str, str], dict] = {}
    for _, row in df.iterrows():
        oid = str(row.get(order_col, "")).strip()
        sku = str(row.get(sku_col, "")).strip()
        if not oid or not sku:
            continue

        # qty fallback เป็น 1 ถ้าไม่มีข้อมูล
        raw_qty = row.get(qty_col, None) if qty_col else None
        if raw_qty is None or (isinstance(raw_qty, float) and pd.isna(raw_qty)):
            qty = 1
        else:
            try:
                qty = int(float(raw_qty))
            except Exception:
                qty = 1

        key = (oid, sku)
        # Helper to clean NaN values
        def clean_value(val):
            if val is None:
                return ""
            val_str = str(val).strip()
            if val_str.lower() in ['nan', 'none', '']:
                return ""
            return val_str
        
        rec = grouped.get(key, {
            "qty": 0,
            "name": clean_value(row.get(name_col, "")),
            "time": row.get(time_col) if time_col else None,
            "logi": clean_value(row.get(logi_col, "")) if logi_col else "",
            "carrier": clean_value(row.get(carrier_col, "")) if carrier_col else "",  # FR-02
            "tracking": clean_value(row.get(tracking_col, "")) if tracking_col else "",  # Tracking number
        })
        rec["qty"] += max(qty, 0)
        # เก็บชื่อสินค้าล่าสุดถ้าอันเดิมว่าง
        if not rec.get("name"):
            rec["name"] = clean_value(row.get(name_col, ""))
        # เวลา/โลจิสติกส์/carrier/tracking เก็บอันล่าสุดที่เจอ
        rec["time"] = row.get(time_col) if time_col else rec.get("time")
        rec["logi"] = clean_value(row.get(logi_col, "")) if logi_col else rec.get("logi", "")
        rec["carrier"] = clean_value(row.get(carrier_col, "")) if carrier_col else rec.get("carrier", "")
        rec["tracking"] = clean_value(row.get(tracking_col, "")) if tracking_col else rec.get("tracking", "")
        grouped[key] = rec

    added = 0
    updated = 0  # ต้องคงเป็น 0 ตาม requirement
    imported_dates: set[date] = set()

    # เตรียมค้นหา Product (optional) — ไม่บังคับ แต่ช่วยเติมข้อมูล
    # ถ้าโครงสร้าง OrderLine ไม่มี product_id ก็ข้ามได้
    has_product_fk = hasattr(OrderLine, "product_id")

    for (oid, sku), rec in grouped.items():
        # === ตรวจซ้ำ: key = (order_id + sku) ตามข้อกำหนด ===
        exists = OrderLine.query.filter_by(order_id=oid, sku=sku).first()
        if exists:
            # เก็บวันที่เคยนำเข้าไว้เตือน (ถ้ามี)
            if hasattr(exists, "import_date") and isinstance(exists.import_date, date):
                imported_dates.add(exists.import_date)
            # ข้ามรายการนี้ (ไม่เพิ่ม, ไม่อัปเดต)
            continue

        # === สร้างใหม่เท่านั้น (INSERT-ONLY) ===
        order_time = parse_datetime_guess(rec.get("time")) if rec.get("time") is not None else None

        # FR-02: Extract carrier from logistics_type or dedicated carrier column
        carrier_text = rec.get("carrier", "") or rec.get("logi", "")
        carrier = extract_carrier_from_logistics(carrier_text)

        ol_kwargs = dict(
            platform=platform_std,
            shop_id=shop.id,
            order_id=oid,
            sku=sku,
            qty=rec.get("qty", 0) or 0,
            item_name=rec.get("name", ""),
            order_time=order_time,
            logistic_type=rec.get("logi", ""),
            carrier=carrier,  # FR-02: standardized carrier
            tracking_number=rec.get("tracking", ""),  # Tracking number from import
            batch_status="pending_batch",  # FR-03: default status
            imported_at=datetime.now(TH_TZ),
            import_date=import_date,
        )

        # ผูก Product ถ้ามี FK
        if has_product_fk:
            prod = Product.query.filter_by(sku=sku).first()
            if not prod:
                prod = Product(sku=sku, brand="", model=rec.get("name", ""))
                db.session.add(prod)
                db.session.flush()
            ol_kwargs["product_id"] = prod.id

        line = OrderLine(**ol_kwargs)
        db.session.add(line)
        added += 1

    db.session.commit()

    # แจ้งผลสรุป
    flash(f"นำเข้าออเดอร์สำเร็จ: เพิ่ม {added} อัปเดต {updated}", "success")

    # เตือนรายการที่ซ้ำ (บอกวันที่เคยนำเข้า)
    if imported_dates:
        dates_th = " / ".join(sorted(d.strftime("%d/%m/%Y") for d in imported_dates))
        flash(f"คำเตือน: พบเลข Order ที่เคยนำเข้าแล้วเมื่อวันที่ {dates_th}", "warning")

    return added, updated

