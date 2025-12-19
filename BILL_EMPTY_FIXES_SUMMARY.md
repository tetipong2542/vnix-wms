# สรุปการแก้ไข BILL_EMPTY Functionality

## วันที่: 2025-12-19

---

## 1. แก้ไขปัญหา BILL_EMPTY Orders ไม่แสดงปุ่ม "รับ"

### ปัญหา
Order ที่มีสถานะ `BILL_EMPTY` และมี Stock เพียงพอ แสดงปุ่ม "รอครบ" แทนที่จะเป็นปุ่ม "รับ"

### สาเหตุ
ฟังก์ชัน `_orders_ready_set` และ `_orders_lowstock_order_set` ไม่ได้รวม `BILL_EMPTY` ในการตรวจสอบ

### การแก้ไข

#### app.py:624 - ฟังก์ชัน `_orders_ready_set`
```python
# เพิ่ม BILL_EMPTY ในเงื่อนไขการตรวจสอบ
if not ((status == "READY_ACCEPT" or status == "BILL_EMPTY") and not accepted and not packed and not is_issued):
```

#### app.py:655 - ฟังก์ชัน `_orders_lowstock_order_set`
```python
# เพิ่ม BILL_EMPTY ในรายการสถานะที่ยอมรับได้
if status not in ("READY_ACCEPT", "LOW_STOCK", "BILL_EMPTY"):
```

#### app.py:2153 - การนับ KPI
```python
# รวม BILL_EMPTY ในการนับ ready orders
"ready": sum(1 for r in scope_rows if r.get("allocation_status") in ("READY_ACCEPT", "BILL_EMPTY") and not r.get("packed") and not r.get("is_cancelled")),
```

#### templates/dashboard.html:837, 846 - เงื่อนไขปุ่มรับงาน
```html
<!-- เพิ่ม BILL_EMPTY ในเงื่อนไขการแสดงปุ่ม -->
{% elif (r.allocation_status == "READY_ACCEPT" or r.allocation_status == "BILL_EMPTY") and r.order_id in ready_oids %}
```

---

## 2. เอา Card KPI "รวมบิลเปล่า" ออกจากหน้า /import/bill_empty

### การแก้ไข

#### templates/import_bill_empty.html:94-109
ลบ Card KPI "รวมบิลเปล่า" ออกทั้งหมด (ผู้ใช้ไม่ได้ใช้งาน)

---

## 3. เพิ่มฟังก์ชันยกเลิกสถานะบิลเปล่าที่ import วันนี้

### ความต้องการ
เพิ่ม option ในหน้า `/admin/clear` เพื่อยกเลิกสถานะ `BILL_EMPTY` ของ Orders ที่ import วันนี้ โดย:
- เปลี่ยน `allocation_status` จาก `BILL_EMPTY` กลับเป็น `NULL`
- ลบ `ImportLog` ที่เกี่ยวข้อง
- Order ยังคงอยู่ในระบบ แต่ badge บิลเปล่าจะหายไป
- KPI count จะเป็น 0

### การแก้ไข

#### templates/clear_confirm.html:25
เพิ่ม option ใหม่:
```html
<option value="bill_empty_today">ยกเลิกสถานะบิลเปล่าที่ import วันนี้</option>
```

#### templates/clear_confirm.html:104
เพิ่มคำอธิบาย:
```html
<li><strong>ยกเลิกสถานะบิลเปล่าที่ import วันนี้:</strong>
เปลี่ยน allocation_status จาก BILL_EMPTY กลับเป็น NULL สำหรับ Orders ที่ import วันนี้
(Order ยังอยู่ในระบบ แต่ไม่แสดง badge บิลเปล่า และลบ ImportLog ที่เกี่ยวข้อง)
</li>
```

#### templates/clear_confirm.html:160-167
เพิ่ม stats card:
```html
<div class="col-md-3 mt-3">
  <div class="card bg-light" style="border: 1px solid #6f42c1;">
    <div class="card-body">
      <h6 class="card-subtitle mb-2 text-muted">บิลเปล่าวันนี้</h6>
      <h4 class="mb-0" style="color: #6f42c1;">{{ stats.bill_empty_today }}</h4>
    </div>
  </div>
</div>
```

#### app.py:9421-9444 - เพิ่มฟังก์ชันล้างข้อมูล
```python
elif scope == "bill_empty_today":
    # ยกเลิกสถานะบิลเปล่าที่ import วันนี้ (เปลี่ยน BILL_EMPTY กลับเป็น NULL)
    today = now_thai().date()

    # 1. นับจำนวน OrderLine ที่จะถูกเปลี่ยนสถานะ
    affected_lines = db.session.execute(
        text("SELECT COUNT(*) FROM order_lines WHERE allocation_status = 'BILL_EMPTY' AND import_date = :today"),
        {"today": today}
    ).scalar() or 0

    # 2. เปลี่ยน allocation_status จาก 'BILL_EMPTY' เป็น NULL
    db.session.execute(
        text("UPDATE order_lines SET allocation_status = NULL WHERE allocation_status = 'BILL_EMPTY' AND import_date = :today"),
        {"today": today}
    )

    # 3. ลบ ImportLog ที่เกี่ยวข้อง
    deleted_logs = ImportLog.query.filter(
        ImportLog.platform == 'EMPTY_BILL_SYSTEM',
        ImportLog.import_date == today
    ).delete(synchronize_session=False)

    db.session.commit()
    flash(f"ยกเลิกสถานะบิลเปล่าวันนี้แล้ว ({affected_lines} รายการ, ลบ log {deleted_logs} รายการ)", "success")
```

#### app.py:9459-9462 - เพิ่มการนับสถิติ
```python
"bill_empty_today": ImportLog.query.filter(
    ImportLog.platform == 'EMPTY_BILL_SYSTEM',
    ImportLog.import_date == today
).count(),
```

---

## ปัญหาที่พบและแก้ไข

### AttributeError: OrderLine has no attribute 'allocation_status'

**สาเหตุ:**
คอลัมน์ `allocation_status` ถูกเพิ่มเข้า database ผ่าน `ALTER TABLE` ไม่ได้ถูกกำหนดใน OrderLine model class

**การแก้ไข:**
ใช้ Raw SQL แทน SQLAlchemy ORM:

```python
# ❌ ผิด - ใช้ ORM ไม่ได้
affected_lines = OrderLine.query.filter(
    OrderLine.allocation_status == 'BILL_EMPTY',
    OrderLine.import_date == today
).count()

# ✅ ถูก - ใช้ Raw SQL
affected_lines = db.session.execute(
    text("SELECT COUNT(*) FROM order_lines WHERE allocation_status = 'BILL_EMPTY' AND import_date = :today"),
    {"today": today}
).scalar() or 0
```

---

## สรุปผลกระทบ

### ✅ BILL_EMPTY Orders สามารถ:
1. แสดงปุ่ม "รับ" เมื่อมี Stock เพียงพอและครบทุกรายการ
2. ถูกนับรวมใน KPI "พร้อมรับ"
3. แสดงใน pile 2 (กอง 2) เมื่อมีบาง items เป็น LOW_STOCK
4. ถูกยกเลิกสถานะผ่านหน้า /admin/clear

### ✅ UI/UX Improvements:
1. ลบ Card KPI ที่ไม่ได้ใช้งานออก
2. เพิ่มตัวเลือกล้างข้อมูลที่ชัดเจนและปลอดภัย
3. แสดงจำนวน records ที่ได้รับผลกระทบเมื่อทำการล้าง

---

## การทดสอบที่แนะนำ

### 1. ทดสอบการรับงาน BILL_EMPTY
- [ ] Order BILL_EMPTY ที่มี Stock เพียงพอแสดงปุ่ม "รับ" ✓
- [ ] Order BILL_EMPTY ที่ของไม่ครบแสดงปุ่ม "รอครบ" ✓
- [ ] สามารถกดรับ Order BILL_EMPTY ได้ ✓

### 2. ทดสอบการล้างสถานะ BILL_EMPTY
- [ ] เข้าหน้า /admin/clear
- [ ] เลือก "ยกเลิกสถานะบิลเปล่าที่ import วันนี้"
- [ ] ตรวจสอบว่า badge BILL_EMPTY หายจาก Dashboard
- [ ] ตรวจสอบว่า KPI "บิลเปล่าวันนี้" เป็น 0

### 3. ทดสอบหลังยกเลิกสถานะ
- [ ] Order ที่ถูกยกเลิกสถานะยังอยู่ในระบบ
- [ ] Order สามารถทำงานได้ปกติ (รับ, แพ็ค, ยกเลิก)

---

## ไฟล์ที่เกี่ยวข้อง

1. `/Users/pond-dev/Documents/backup/oms-production/V.5.52 2/app.py`
   - Lines: 624, 655, 2153, 9421-9444, 9459-9462

2. `/Users/pond-dev/Documents/backup/oms-production/V.5.52 2/templates/dashboard.html`
   - Lines: 837, 846

3. `/Users/pond-dev/Documents/backup/oms-production/V.5.52 2/templates/clear_confirm.html`
   - Lines: 25, 104, 160-167

4. `/Users/pond-dev/Documents/backup/oms-production/V.5.52 2/templates/import_bill_empty.html`
   - Removed lines: 94-109 (KPI Card)

---

## เอกสารที่เกี่ยวข้อง

- [MIGRATION_TIMEZONE_README.md](MIGRATION_TIMEZONE_README.md) - คู่มือ Migration timezone สำหรับ ImportLog
