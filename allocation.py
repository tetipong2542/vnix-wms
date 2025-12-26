
from collections import defaultdict
from datetime import datetime
from sqlalchemy import func, text
from utils import PLATFORM_PRIORITY, now_thai, sla_status, due_date_for, normalize_platform, TH_TZ
from models import db, Shop, Product, Stock, Sales, OrderLine

def compute_allocation(session, filters:dict):
    """
    คืน list ของ dict ครบทุกคอลัมน์ที่จอ Dashboard ต้องใช้

    Logic การจัดสรร (แก้ไขตาม Requirement):
    1. เรียง Priority: Shopee > TikTok > Lazada > อื่นๆ, แล้วตามเวลาสั่ง (มาก่อนได้ก่อน)
    2. Order ที่ Packed / Cancelled / เปิดใบขายครบ -> ไม่นำ Qty มาคำนวณ (ข้ามการตัดสต็อก)
    3. Order ที่ Issued (จ่ายแล้ว) / Accepted (รับแล้ว) -> ต้องนำ Qty มาตัดสต็อก (จองของไว้)
    4. Order ใหม่ -> คำนวณตัดสต็อกตามลำดับ
       - ถ้าสต็อกพอ -> READY_ACCEPT (หรือ LOW_STOCK ถ้าเหลือน้อย)
       - ถ้าสต็อกหมด -> SHORTAGE
       - ถ้าสต็อกเหลือแต่ไม่พอจำนวนที่ขอ -> NOT_ENOUGH (ไม่ตัดสต็อก)
    """

    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔧 compute_allocation called with filters: {filters}")

    # Query ข้อมูล Order ทั้งหมด
    q = session.query(OrderLine, Shop, Product, Stock, Sales)\
        .join(Shop, Shop.id==OrderLine.shop_id)\
        .outerjoin(Product, Product.sku==OrderLine.sku)\
        .outerjoin(Stock, Stock.sku==OrderLine.sku)\
        .outerjoin(Sales, Sales.order_id==OrderLine.order_id)

    # Platform / Shop ต้องกรองเสมอ (เพราะเป็น Scope ของร้าน)
    if filters.get("platform"):
        q = q.filter(Shop.platform==filters["platform"])
    if filters.get("shop_id"):
        q = q.filter(Shop.id==filters["shop_id"])
    
    # [แก้ไขหลัก] ไม่กรองวันที่ใน SQL เพื่อให้โหลด Order ค้างเก่ามาคำนวณสต็อกด้วยเสมอ
    # (เราจะไปกรองวันที่ใน Loop ด้านล่างแทน)

    # ดึงรายการ Order ที่ยกเลิก (จากตาราง cancelled_orders)
    cancelled_order_ids = set()
    try:
        result = session.execute(text("SELECT order_id FROM cancelled_orders")).fetchall()
        cancelled_order_ids = {row[0] for row in result if row and row[0]}
    except:
        pass

    # ดึงรายการ Order ที่จ่ายแล้ว (issued_orders)
    issued_order_ids = set()
    try:
        result = session.execute(text("SELECT order_id FROM issued_orders")).fetchall()
        issued_order_ids = {row[0] for row in result if row and row[0]}
    except:
        pass
    
    # ดึงรายการ Order ที่เป็นบิลเปล่า (จากตาราง order_lines ที่มี allocation_status = 'BILL_EMPTY')
    # ใช้วิธีเช็คจากตาราง order_lines โดยตรง (ถ้ามีคอลัมน์) หรือใช้วิธีอื่น
    bill_empty_order_ids = set()
    try:
        # ลองเช็คว่ามีคอลัมน์ allocation_status หรือไม่
        result = session.execute(text("SELECT DISTINCT order_id FROM order_lines WHERE allocation_status = 'BILL_EMPTY'")).fetchall()
        bill_empty_order_ids = {row[0] for row in result if row and row[0]}
    except:
        # ถ้าไม่มีคอลัมน์ ให้ใช้วิธีอื่น (เช่นเช็คจากตารางแยก)
        pass

    rows = []

    # เรียงลำดับเวลา เพื่อให้ FIFO (First-In-First-Out) ทำงานถูกต้อง
    all_data = q.order_by(OrderLine.order_time.asc()).all()

    # Debug: count filters
    filtered_by_date = 0
    total_rows_checked = 0

    for ol, shop, prod, stock, sales in all_data:
        # --- ตรวจสอบเงื่อนไขการแสดงผล (Filter) ใน Python ---
        show_this_row = True
        total_rows_checked += 1

        # [แก้ไข] เตรียมตัวแปรเวลา Order ให้มี Timezone (ถ้ายังไม่มี) เพื่อให้เทียบกับ Filter ได้
        current_order_time = ol.order_time
        if current_order_time and current_order_time.tzinfo is None:
            # ถ้าเวลาจาก DB ไม่มีโซน ให้ใส่โซนไทยเข้าไป (TH_TZ)
            current_order_time = current_order_time.replace(tzinfo=TH_TZ)

        # ถ้าไม่ใช่โหมดดูงานค้าง/ทั้งหมด (คือมีการระบุวันที่) ให้เช็ควันที่
        was_shown_before_date_filter = show_this_row
        if not (filters.get("active_only") or filters.get("all_time")):
            # กรอง Import Date (เทียบเป็น date object)
            if filters.get("import_from"):
                imp_from_val = filters["import_from"]
                ol_imp_date = ol.import_date
                # แปลง datetime เป็น date ถ้าจำเป็น
                if hasattr(imp_from_val, 'date'):
                    imp_from_val = imp_from_val.date()
                if hasattr(ol_imp_date, 'date'):
                    ol_imp_date = ol_imp_date.date()
                if not ol_imp_date or ol_imp_date < imp_from_val:
                    show_this_row = False

            if filters.get("import_to"):
                imp_to_val = filters["import_to"]
                ol_imp_date = ol.import_date
                # แปลง datetime เป็น date ถ้าจำเป็น
                if hasattr(imp_to_val, 'date'):
                    imp_to_val = imp_to_val.date()
                if hasattr(ol_imp_date, 'date'):
                    ol_imp_date = ol_imp_date.date()
                if not ol_imp_date or ol_imp_date > imp_to_val:
                    show_this_row = False

            # รองรับ key เก่า
            if filters.get("import_date") and ol.import_date != filters["import_date"]:
                show_this_row = False

            # [แก้ไข] กรอง Order Date (ใช้ current_order_time ที่แก้ Timezone แล้ว)
            if filters.get("date_from"):
                if not current_order_time or current_order_time < filters["date_from"]:
                    show_this_row = False

            if filters.get("date_to"):
                if not current_order_time or current_order_time >= filters["date_to"]:
                    show_this_row = False

        # Track filtering
        if was_shown_before_date_filter and not show_this_row:
            filtered_by_date += 1

        # --- กรองวันที่กดรับ (Accepted Date) แบบ Timezone-Safe ---
        if filters.get("accepted_from") or filters.get("accepted_to"):
            # ดึงเวลาจาก DB และทำให้เป็น Naive (ไม่มีโซน) เพื่อเทียบกันได้
            acc_at = ol.accepted_at
            if acc_at and acc_at.tzinfo:
                acc_at = acc_at.replace(tzinfo=None)
            
            # เตรียมเวลาจาก Filter และทำให้เป็น Naive เหมือนกัน
            limit_from = filters.get("accepted_from")
            if limit_from and hasattr(limit_from, 'tzinfo') and limit_from.tzinfo:
                limit_from = limit_from.replace(tzinfo=None)
                
            limit_to = filters.get("accepted_to")
            if limit_to and hasattr(limit_to, 'tzinfo') and limit_to.tzinfo:
                limit_to = limit_to.replace(tzinfo=None)

            # เริ่มเปรียบเทียบ
            if limit_from and (not acc_at or acc_at < limit_from): 
                show_this_row = False
            if limit_to and (not acc_at or acc_at >= limit_to): 
                show_this_row = False
        # --- จบส่วนการกรอง ---

        stock_qty = int(stock.qty) if stock and stock.qty is not None else 0
        brand = prod.brand if prod else ""
        model = prod.model if prod else (ol.item_name or "")
        
        # [แก้ไข] แยกแยะระหว่าง "ยังไม่นำเข้า SBS" กับ "ยังไม่มีการเปิดใบขาย"
        is_not_in_sbs = False
        if sales is None:
            # กรณีไม่มีข้อมูลในตาราง Sales เลย -> Order ยังไม่นำเข้า SBS
            s_label = "Orderยังไม่นำเข้าSBS"
            is_not_in_sbs = True
        else:
            # กรณีมีข้อมูล Sales แต่สถานะว่าง -> ยังไม่มีการเปิดใบขาย
            s_label = sales.status if sales.status else "ยังไม่มีการเปิดใบขาย"
        
        sla, due = sla_status(shop.platform, ol.order_time or now_thai())
        
        # เช็คสถานะ Packed / เปิดใบขายครบ (ระวัง: ต้องไม่นับ "Orderยังไม่นำเข้าSBS" เป็น packed)
        is_packed = False
        if s_label and not is_not_in_sbs:
            s_lower = s_label.lower()
            if any(keyword in s_lower for keyword in ["ครบตามจำนวน", "packed", "แพ็คแล้ว", "opened_full"]):
                is_packed = True
        
        is_cancelled = ol.order_id in cancelled_order_ids
        is_issued = ol.order_id in issued_order_ids
        
        # ถ้าเป็นโหมด active_only (ดูงานค้าง) ให้ข้ามพวกที่จบงานแล้วไปเลย
        if filters.get("active_only"):
            if is_packed or is_cancelled:
                continue
        
        # ถ้าผ่านเกณฑ์ หรือเป็น Order ที่ต้องใช้คำนวณสต็อก ให้สร้าง Object เตรียมไว้
        row_data = {
            "id": ol.id,
            "platform": shop.platform,
            "shop": shop.name,
            "shop_id": shop.id,
            "order_id": ol.order_id,
            "sku": ol.sku,
            "brand": brand,
            "model": model,
            "stock_qty": stock_qty,
            "qty": int(ol.qty or 0),
            "order_time": ol.order_time,
            "order_time_iso": (ol.order_time.astimezone(TH_TZ).isoformat() if ol.order_time else ""),
            "import_date": ol.import_date,  # [เพิ่ม] เพื่อให้ Dashboard รู้ว่านำเข้าวันไหน
            "due_date": due,
            "sla": sla,
            "logistic": ol.logistic_type or "",
            "sales_status": s_label,
            "is_not_in_sbs": is_not_in_sbs,
            "accepted": bool(ol.accepted),
            "accepted_by": ol.accepted_by_username or "",
            "dispatch_round": ol.dispatch_round if hasattr(ol, 'dispatch_round') else None,
            "printed_warehouse": ol.printed_warehouse if hasattr(ol, 'printed_warehouse') else 0,
            "printed_warehouse_at": ol.printed_warehouse_at if hasattr(ol, 'printed_warehouse_at') else None,
            "printed_warehouse_by": ol.printed_warehouse_by if hasattr(ol, 'printed_warehouse_by') else None,
            "printed_picking": ol.printed_picking if hasattr(ol, 'printed_picking') else 0,
            "printed_picking_at": ol.printed_picking_at if hasattr(ol, 'printed_picking_at') else None,
            "printed_picking_by": ol.printed_picking_by if hasattr(ol, 'printed_picking_by') else None,
            "is_packed": is_packed,
            "is_cancelled": is_cancelled,
            "is_issued": is_issued,
            "allocation_status": "", 
            "show_in_view": show_this_row  # flag เพื่อบอกว่าแถวนี้ต้องแสดงในผลลัพธ์หรือไม่
        }
        rows.append(row_data)

    # คำนวณ AllQty (ยอดรวมที่ต้องใช้ต่อ SKU) - นับเฉพาะที่ยังไม่ Packed/Cancelled
    sku_total = defaultdict(int)
    for r in rows:
        if not r["is_packed"] and not r["is_cancelled"]:
            sku_total[r["sku"]] += r["qty"]
    
    for r in rows:
        r["allqty"] = sku_total[r["sku"]]

    # จัดสรรสต็อกตาม Priority
    by_sku = defaultdict(list)
    for r in rows:
        by_sku[r["sku"]].append(r)
    
    for sku, arr in by_sku.items():
        # เรียงตาม Priority: Platform > Order Time
        arr.sort(key=lambda x: (
            PLATFORM_PRIORITY.get(x["platform"], 999), 
            x["order_time"] or datetime.max
        ))
        
        # สต็อกเริ่มต้นของ SKU นี้
        current_stock = arr[0]["stock_qty"]
        
        for r in arr:
            # ข้อ 3: Order ที่ Packed หรือ Cancelled -> ไม่ดึง Qty มาคำนวณ (จบงานแล้ว)
            if r["is_packed"]:
                r["allocation_status"] = "PACKED"
                continue
            
            if r["is_cancelled"]:
                r["allocation_status"] = "CANCELLED"
                continue
            
            # เช็ค BILL_EMPTY (ต้องเช็คก่อนคำนวณสถานะอื่น)
            if r["order_id"] in bill_empty_order_ids:
                r["allocation_status"] = "BILL_EMPTY"
                continue
            
            # --- คำนวณสถานะก่อน (ยังไม่ดู Issued/Accepted) ---
            req_qty = r["qty"]
            calculated_status = ""
            
            if current_stock <= 0:
                calculated_status = "SHORTAGE"
            elif current_stock < req_qty:
                calculated_status = "NOT_ENOUGH"
            else:
                # สต็อกพอ -> ถ้าเหลือน้อยเป็น LOW_STOCK
                if current_stock - req_qty <= 3:
                    calculated_status = "LOW_STOCK"
                else:
                    calculated_status = "READY_ACCEPT"
            
            # --- บันทึกสถานะ และ ตัดสต็อก ---
            
            # [แก้ไข] ย้ายเช็ค Accepted ขึ้นมาก่อน Issued
            # เพื่อให้ถ้ากดรับแล้ว สถานะต้องเป็น "ACCEPTED" (รับแล้ว) เท่านั้น
            if r["accepted"]:
                r["allocation_status"] = "ACCEPTED"
                # ตัดสต็อกเฉพาะกรณีของพอ
                if calculated_status in ["READY_ACCEPT", "LOW_STOCK"]:
                    current_stock -= req_qty
                continue
            
            # ถ้า Issued (จ่ายแล้ว) -> คงสถานะที่คำนวณได้ไว้ (เช่น LOW_STOCK, SHORTAGE)
            # และทำการตัดสต็อก (ถ้าของพอ) เพื่อจองของ
            if r["is_issued"]:
                r["allocation_status"] = calculated_status  # เก็บสถานะจริงไว้
                # ตัดสต็อกเฉพาะกรณีของพอ (READY_ACCEPT หรือ LOW_STOCK)
                if calculated_status in ["READY_ACCEPT", "LOW_STOCK"]:
                    current_stock -= req_qty
                continue
            
            # --- Order ใหม่ / ยังไม่ดำเนินการ ---
            if calculated_status in ["SHORTAGE", "NOT_ENOUGH"]:
                r["allocation_status"] = calculated_status
                # ของไม่พอ ไม่ตัดสต็อก
            else:
                r["allocation_status"] = calculated_status
                current_stock -= req_qty  # ของพอ จองของไว้

    # --- คัดกรองแถวที่จะส่งออก (เฉพาะที่ตรงกับ Filter) ---
    final_rows = [r for r in rows if r["show_in_view"]]

    # --- KPI (คำนวณจาก final_rows ที่แสดงผล) ---
    all_active_rows = [r for r in final_rows if not r["is_packed"] and not r["is_cancelled"]]
    unique_active_orders = set(r["order_id"] for r in all_active_rows)
    
    orders_ready_actionable = set(r["order_id"] for r in all_active_rows 
                                  if r["allocation_status"] == "READY_ACCEPT" 
                                  and not r["accepted"] 
                                  and not r["is_issued"])
    
    orders_low_actionable = set(r["order_id"] for r in all_active_rows 
                                if r["allocation_status"] == "LOW_STOCK" 
                                and not r["accepted"] 
                                and not r["is_issued"])

    kpis = {
        "total_items": len(final_rows),
        "total_qty": sum(r["qty"] for r in final_rows),
        "orders_total": len(set(r["order_id"] for r in final_rows if r["order_id"])),
        "orders_unique": len(unique_active_orders),
        "ready": sum(1 for r in final_rows if r["allocation_status"]=="READY_ACCEPT"),
        "accepted": sum(1 for r in final_rows if r["allocation_status"]=="ACCEPTED"),
        "low": sum(1 for r in final_rows if r["allocation_status"]=="LOW_STOCK"),
        "nostock": sum(1 for r in final_rows if r["allocation_status"]=="SHORTAGE"),
        "notenough": sum(1 for r in final_rows if r["allocation_status"]=="NOT_ENOUGH"),
        "packed": sum(1 for r in final_rows if r["allocation_status"]=="PACKED"),
        "orders_ready": len(orders_ready_actionable),
        "orders_low": len(orders_low_actionable),
        "orders_cancelled": len(set(r["order_id"] for r in final_rows if r["is_cancelled"])),
        "orders_not_in_sbs": len(set(r["order_id"] for r in final_rows if r.get("is_not_in_sbs"))),
        "orders_nosales": len(set(r["order_id"] for r in final_rows if not r.get("is_not_in_sbs") and r.get("sales_status") == "ยังไม่มีการเปิดใบขาย")),
    }

    # Debug logging
    logger.info(f"📊 compute_allocation returning {len(final_rows)} rows")
    logger.info(f"   Total rows checked: {total_rows_checked}, Filtered by date: {filtered_by_date}")
    if filters.get("date_from") or filters.get("date_to"):
        logger.info(f"   Date range filter: {filters.get('date_from')} to {filters.get('date_to')}")
        logger.info(f"   Unique orders: {len(set(r['order_id'] for r in final_rows))}")

    return final_rows, kpis