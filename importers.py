
# importers.py
from __future__ import annotations

import pandas as pd
from datetime import datetime, date
from flask import flash
from sqlalchemy.exc import IntegrityError

from utils import parse_datetime_guess, normalize_platform, TH_TZ
from models import db, Shop, Product, Stock, Sales, OrderLine

# ===== Column dictionaries =====
COMMON_ORDER_ID   = ["orderNumber","Order Number","order_id","Order ID","order_sn","Order No","เลข Order","No.","OrderNo"]
COMMON_SKU        = ["sellerSku","Seller SKU","SKU","Sku","Item SKU","SKU Reference No.","รหัสสินค้า"]
COMMON_ITEM_NAME  = ["itemName","Item Name","Product Name","ชื่อสินค้า","ชื่อรุ่น","title","name"]
COMMON_QTY        = ["quantity","Quantity","Qty","จำนวน","จำนวนที่สั่ง","Purchased Qty","Order Item Qty"]
COMMON_ORDER_TIME = ["order_time","createdAt","create_time","created_time","Order Time","OrderDate","Order Date","วันที่สั่งซื้อ","Paid Time","paid_time","Created Time","createTime","Created Time"]
COMMON_LOGISTICS  = ["logistics_service","logistic_type","Logistics Service","Shipping Provider","ประเภทขนส่ง","Shipment Method","Delivery Type"]

# เพิ่มคีย์หัวคอลัมน์สำหรับ "ชื่อร้าน"
COMMON_SHOP = ["ชื่อร้าน","Shop","Shop Name","Store","Store Name","ร้าน","ร้านค้า"]

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

def clean_shop_name(s) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    # ตัด "(Shopee)" หรือ "(Lazada)" ที่มาจาก datalist
    if s.endswith(")") and " (" in s:
        try:
            s = s[:s.rfind(" (")].strip()
        except Exception:
            pass
    # ตัดสัญลักษณ์พิเศษ เช่น "•"
    s = s.replace("•", " ").strip()
    return s

def get_or_create_shop(platform, shop_name):
    platform = normalize_platform(platform)
    name = clean_shop_name(shop_name)
    shop = Shop.query.filter_by(name=name).first()
    if not shop:
        shop = Shop(platform=platform, name=name)
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

# >>> ฟังก์ชันนี้ถูกแพตช์ใหม่ให้ทน NaN/หัวคอลัมน์หลายแบบ + Full Sync Mode
def import_stock(df: pd.DataFrame, full_replace: bool = True) -> int:
    """
    นำเข้าสต็อกจาก DataFrame:
    - รองรับหัวคอลัมน์หลายแบบ (ไทย/อังกฤษ)
    - Qty ว่าง/NaN จะถูกมองเป็น 0
    - รวมยอดเมื่อไฟล์มี SKU ซ้ำหลายบรรทัด
    - โหมด full_replace=True: SKU ที่ไม่อยู่ในไฟล์/ชีต ให้ถือว่าเป็น 0 (SabuySoft)
    คืนค่าจำนวน SKU ที่บันทึก (insert/update)
    """
    sku_col = first_existing(df, COMMON_STOCK_SKU)
    qty_col = first_existing(df, COMMON_STOCK_QTY)
    if not sku_col:
        raise ValueError("ไม่พบคอลัมน์ SKU/รหัสสินค้า ในไฟล์สต็อก")
    if not qty_col:
        raise ValueError("ไม่พบคอลัมน์ คงเหลือ/Qty/Stock ในไฟล์สต็อก")

    df = df.copy()
    df.rename(columns={sku_col: "sku", qty_col: "qty"}, inplace=True)

    df["sku"] = df["sku"].astype(str).fillna("").str.strip()
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)

    # คัดแถวที่ไม่มี SKU
    df = df[df["sku"] != ""]

    # ✅ SabuySoft rule: ถ้า SKU หายไป ต้องถือว่าเป็น 0
    # ทำ full sync โดย reset ทั้งตารางเป็น 0 ก่อน แล้วค่อย update ตามไฟล์
    if full_replace:
        reset_data = {Stock.qty: 0, Stock.updated_at: datetime.now(TH_TZ)}
        Stock.query.update(reset_data, synchronize_session=False)

        # ถ้าไฟล์ว่างจริง ๆ = แปลว่าไม่มี SKU ไหนเหลือเลย → ทั้งหมดเป็น 0
        if df.empty:
            db.session.commit()
            return 0
    else:
        if df.empty:
            return 0

    # รวมยอดตาม SKU (กันไฟล์ซ้ำแถว)
    agg = df.groupby("sku", as_index=False)["qty"].sum()

    saved = 0
    for _, row in agg.iterrows():
        sku = row["sku"]
        qty = int(row["qty"] or 0)

        st = Stock.query.filter_by(sku=sku).first()
        if not st:
            st = Stock(sku=sku, qty=qty)
            db.session.add(st)
        else:
            st.qty = qty
            st.updated_at = datetime.now(TH_TZ)

        # ถ้ามีฟิลด์ product.stock_qty ให้ sync ด้วย
        prod = Product.query.filter_by(sku=sku).first()
        if prod is not None and hasattr(prod, "stock_qty"):
            try:
                prod.stock_qty = qty
            except Exception:
                # กันชนิดคอลัมน์ไม่ใช่ int
                pass

        saved += 1

    db.session.commit()
    return saved

def import_sales(df: pd.DataFrame) -> dict:
    """
    นำเข้าข้อมูลใบสั่งขาย (Sales)
    Returns: Dict ที่มี {'ids': [...], 'skipped': [...]}
        - ids: List ของ Order ID ที่ทำการ Create/Update สำเร็จ
        - skipped: List ของ Dict ที่มีข้อมูลแถวที่ถูกข้าม
    """
    # 1. หาชื่อคอลัมน์
    col_oid = first_existing(df, ["เลข Order", "Order ID", "order_id", "Order No", "เลขที่คำสั่งซื้อ", "orderNumber", "Order Number"])
    col_po  = first_existing(df, ["เลขที่ PO", "PO", "PO No", "เลขที่เอกสาร", "Document No", "เอกสาร"])
    col_st  = first_existing(df, ["สถานะ", "Status", "สถานะการขาย", "Sales Status"])

    if not col_oid:
        raise ValueError("ไม่พบคอลัมน์ 'เลข Order' หรือ 'Order ID' ในไฟล์")

    processed_ids = []  # เก็บ Order ID ที่ทำสำเร็จ
    skipped_rows = []   # เก็บข้อมูลแถวที่ถูกข้าม

    # 2. แปลงข้อมูลให้สะอาด
    for idx, row in df.iterrows():
        # แปลง Order ID ให้ปลอดภัย (รองรับตัวเลขขนาดใหญ่)
        raw_oid = row.get(col_oid, "")

        # กรณี Order ID เป็นตัวเลขขนาดใหญ่ (scientific notation)
        if pd.notna(raw_oid):
            try:
                # ถ้าเป็น float ให้แปลงเป็น int ก่อนแล้วค่อยแปลงเป็น string
                if isinstance(raw_oid, (int, float)):
                    oid = str(int(raw_oid)).strip()
                else:
                    oid = str(raw_oid).strip()
            except (ValueError, OverflowError):
                oid = str(raw_oid).strip()
        else:
            oid = ""

        # ข้ามถ้าไม่มี Order ID
        if not oid or oid == 'nan' or oid == 'None':
            skipped_rows.append({
                "row_number": idx + 2,  # +2 เพราะ index เริ่มที่ 0 และมี header row
                "reason": "Order ID ว่างเปล่า",
                "order_id": raw_oid if pd.notna(raw_oid) else "(ว่าง)",
                "po_no": row.get(col_po, "") if col_po else "",
                "status": row.get(col_st, "") if col_st else ""
            })
            continue

        try:
            # หาข้อมูล Sales เดิม (ถ้ามี)
            sale = Sales.query.filter_by(order_id=oid).first()

            # ถ้าไม่มี ให้สร้างใหม่
            if not sale:
                sale = Sales(order_id=oid)
                db.session.add(sale)

            # อัปเดตข้อมูล
            if col_po and pd.notna(row.get(col_po)):
                val_po = str(row.get(col_po)).strip()
                if val_po:
                    sale.po_no = val_po

            if col_st and pd.notna(row.get(col_st)):
                val_st = str(row.get(col_st)).strip()
                if val_st:
                    sale.status = val_st

            # เก็บ ID เข้า List
            processed_ids.append(oid)

        except Exception as e:
            # บันทึกข้อผิดพลาดที่เกิดขึ้นระหว่างการประมวลผล
            skipped_rows.append({
                "row_number": idx + 2,
                "reason": f"เกิดข้อผิดพลาด: {str(e)}",
                "order_id": oid,
                "po_no": row.get(col_po, "") if col_po else "",
                "status": row.get(col_st, "") if col_st else ""
            })
            continue

    db.session.commit()

    return {
        "ids": processed_ids,
        "skipped": skipped_rows
    }

# ============================
# INSERT-ONLY ORDER IMPORTER
# ============================
def import_orders(df: pd.DataFrame, platform: str, shop_name: str | None, import_date: date) -> dict:
    """
    นำเข้าออเดอร์แบบ INSERT-ONLY พร้อมส่งคืนสถิติละเอียด
    
    Returns dict:
        {
            'added': int,           # จำนวน Order ID ที่เพิ่มสำเร็จ (ไม่ซ้ำ)
            'duplicates': int,      # จำนวน Order ID ที่ซ้ำ (ข้าม)
            'failed': int,          # จำนวน Order ID ที่ไม่สำเร็จ
            'errors': list,         # รายการสาเหตุที่ไม่สำเร็จ (สูงสุด 10 รายการ)
            'added_ids': list,      # รายชื่อ Order ID ที่เพิ่มสำเร็จ
            'duplicate_ids': list,  # รายชื่อ Order ID ที่ซ้ำ
            'failed_ids': list      # รายชื่อ Order ID ที่ไม่สำเร็จ
        }
    นับยอดตาม Order ID ไม่ซ้ำ (Unique Order IDs)
    """
    platform_std = normalize_platform(platform)

    # --- หา columns จากหลายแพลตฟอร์ม ---
    shop_col  = first_existing(df, COMMON_SHOP)
    order_col = first_existing(df, COMMON_ORDER_ID)
    sku_col   = first_existing(df, COMMON_SKU)
    name_col  = first_existing(df, COMMON_ITEM_NAME)
    qty_col   = first_existing(df, COMMON_QTY)
    time_col  = first_existing(df, COMMON_ORDER_TIME)
    logi_col  = first_existing(df, COMMON_LOGISTICS)

    stats = {
        "added": 0,
        "duplicates": 0,           # รวมซ้ำทั้งหมด (old + today)
        "duplicates_old": 0,       # ซ้ำข้ามวัน (แสดงในการ์ด)
        "duplicates_today": 0,     # ซ้ำในวันเดียวกัน (ไม่แสดงในการ์ด)
        "failed": 0,
        "errors": [],  # เก็บสาเหตุที่ไม่สำเร็จ (สูงสุด 10 รายการ)
        "added_ids": [],
        "duplicate_ids": [],
        "duplicate_old_ids": [],   # รายการ Order ID ที่ซ้ำข้ามวัน
        "duplicate_today_ids": [], # รายการ Order ID ที่ซ้ำในวัน
        "failed_ids": []
    }

    if not order_col or not sku_col:
        stats["errors"].append("ไม่พบคอลัมน์ Order ID หรือ SKU ในไฟล์")
        return stats

    # fallback ชื่อร้านจากฟอร์ม (ถ้ามี)
    fallback_shop = clean_shop_name(shop_name) if shop_name else ""

    # Group ข้อมูลตาม Order ID ก่อน (เพื่อจัดการเป็นราย Order)
    # key = (shop, order_id), value = list of items
    grouped: dict[tuple[str, str], list[dict]] = {}
    failed_oids_in_parsing: set[str] = set()
    
    for idx, row in df.iterrows():
        oid = str(row.get(order_col, "")).strip()
        sku = str(row.get(sku_col, "")).strip()
        
        # เช็คข้อมูลสำคัญ
        if not oid or not sku:
            if oid and oid not in failed_oids_in_parsing:
                failed_oids_in_parsing.add(oid)
                if oid not in stats["failed_ids"]:
                    stats["failed_ids"].append(oid)
                    stats["failed"] += 1
            elif not oid:
                # ไม่มี OID เลย นับ failed แบบไม่มี ID
                stats["failed"] += 1
            if len(stats["errors"]) < 10:
                stats["errors"].append(f"แถว {idx+2}: ไม่มี Order ID หรือ SKU")
            continue

        sname = clean_shop_name(row.get(shop_col)) if shop_col else fallback_shop
        if not sname:
            if oid not in failed_oids_in_parsing:
                failed_oids_in_parsing.add(oid)
                if oid not in stats["failed_ids"]:
                    stats["failed_ids"].append(oid)
                    stats["failed"] += 1
            if len(stats["errors"]) < 10:
                stats["errors"].append(f"Order {oid}: ไม่ระบุชื่อร้าน")
            continue

        qty = pd.to_numeric(row.get(qty_col), errors="coerce") if qty_col else None
        qty = int(qty) if pd.notnull(qty) else 1

        key = (sname, oid)
        if key not in grouped:
            grouped[key] = []
        
        grouped[key].append({
            "sku": sku,
            "qty": max(qty, 0),
            "name": str(row.get(name_col, "") or ""),
            "time": row.get(time_col) if time_col else None,
            "logi": str(row.get(logi_col, "") or "") if logi_col else "",
        })

    if not grouped and stats["failed"] == 0:
        return stats  # Empty but valid file structure

    has_product_fk = hasattr(OrderLine, "product_id")

    # Process แต่ละ Order (ระดับ Transaction)
    for (sname, oid), items in grouped.items():
        try:
            shop = get_or_create_shop(platform_std, sname)

            # เช็คว่า Order นี้เคยมีในระบบแล้วหรือยัง (เช็คระดับ Order)
            exists = OrderLine.query.filter_by(shop_id=shop.id, order_id=oid).first()
            if exists:
                if oid not in stats["duplicate_ids"]:
                    stats["duplicates"] += 1
                    stats["duplicate_ids"].append(oid)
                    
                    # [NEW] เช็คว่าซ้ำข้ามวันหรือซ้ำในวันเดียวกัน
                    is_old_duplicate = True
                    if exists.import_date and exists.import_date == import_date:
                        is_old_duplicate = False
                    
                    if is_old_duplicate:
                        stats["duplicates_old"] += 1
                        stats["duplicate_old_ids"].append(oid)
                    else:
                        stats["duplicates_today"] += 1
                        stats["duplicate_today_ids"].append(oid)
                continue

            # ถ้ายังไม่มี -> เพิ่มสินค้าลง DB
            # รวม SKU ซ้ำใน Order เดียวกัน
            sku_agg: dict[str, dict] = {}
            for item in items:
                sku = item["sku"]
                if sku not in sku_agg:
                    sku_agg[sku] = {
                        "qty": 0,
                        "name": item.get("name", ""),
                        "time": item.get("time"),
                        "logi": item.get("logi", ""),
                    }
                sku_agg[sku]["qty"] += item.get("qty", 0)
                if not sku_agg[sku].get("name"):
                    sku_agg[sku]["name"] = item.get("name", "")
                if item.get("time"):
                    sku_agg[sku]["time"] = item.get("time")
                if item.get("logi"):
                    sku_agg[sku]["logi"] = item.get("logi")

            items_added_count = 0
            for sku, rec in sku_agg.items():
                order_time = parse_datetime_guess(rec.get("time")) if rec.get("time") is not None else None

                ol_kwargs = dict(
                    platform=platform_std,
                    shop_id=shop.id,
                    order_id=oid,
                    sku=sku,
                    item_name=rec.get("name", "")[:255],
                    qty=int(rec.get("qty") or 0) or 1,
                    order_time=order_time,
                    logistic_type=(rec.get("logi") or "")[:60],
                    import_date=import_date,
                )

                # ผูก product ถ้าตารางมีและเจอสินค้า
                if has_product_fk:
                    prod = Product.query.filter_by(sku=sku).first()
                    if prod:
                        ol_kwargs["product_id"] = prod.id

                line = OrderLine(**ol_kwargs)
                db.session.add(line)
                items_added_count += 1
            
            # นับยอด Added (เฉพาะถ้ายังไม่เคยนับ)
            if items_added_count > 0 and oid not in stats["added_ids"]:
                stats["added"] += 1
                stats["added_ids"].append(oid)

        except Exception as e:
            if oid not in stats["failed_ids"]:
                stats["failed"] += 1
                stats["failed_ids"].append(oid)
            if len(stats["errors"]) < 10:
                stats["errors"].append(f"Order {oid}: {str(e)}")

    db.session.commit()
    return stats