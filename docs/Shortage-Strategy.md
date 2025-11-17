# 🎯 Shortage Strategy & Batch Split Recommendation
## แนวทางจัดการ Shortage และการแบ่ง Batch

---

## 📊 สถานะปัจจุบันของระบบ (Current System)

### 🔍 **ตรวจสอบจาก Code:**

```python
# app.py:2537-2559
@app.route("/api/batch/<batch_id>/generate-handover-code", methods=["POST"])
def api_generate_handover_code(batch_id):
    progress_data = calculate_batch_progress(batch_id)

    # ❌ ต้องรอ Progress 100% ก่อนถึงจะสร้าง Handover Code ได้
    if progress_data["progress_percent"] < 100:
        return jsonify({
            "success": False,
            "error": "Batch ยังไม่เสร็จ (Progress: XX%)"
        }), 400
```

### ⚠️ **ปัญหาที่เกิดขึ้นตอนนี้:**

```
┌─────────────────────────────────────────────────────────────────┐
│                  สถานการณ์ปัญหา: Shortage นาน                   │
└─────────────────────────────────────────────────────────────────┘

Batch: SH-2025-11-17-R1
Orders: 10 Orders
Total Qty: 50 ชิ้น

Day 1: Picker หยิบของ
├─ SKU A: 10/10 ชิ้น ✅
├─ SKU B: 15/15 ชิ้น ✅
├─ SKU C: 0/5 ชิ้น ❌ (Shortage 5 ชิ้น - สินค้าหมด)
├─ SKU D: 12/12 ชิ้น ✅
└─ SKU E: 8/8 ชิ้น ✅

Progress = 45/50 = 90% ⚠️

❌ ปัญหา:
   ├─ Batch ค้างที่ 90%
   ├─ ไม่สามารถสร้าง Handover Code ได้ (ต้อง 100%)
   ├─ สินค้า 45 ชิ้นที่หยิบได้แล้วต้องรอ
   └─ ลูกค้า 9 Orders (ที่ไม่มี SKU C) ต้องรอ

Day 2: รอสต็อก SKU C
   └─ ❌ ยังไม่มีสต็อก

Day 3: รอสต็อก SKU C
   └─ ❌ ยังไม่มีสต็อก

💥 ผลกระทบ:
   ├─ Batch ค้าง 3 วัน
   ├─ ลูกค้าที่ควรได้รับสินค้าแล้วต้องรอ
   ├─ Packer ไม่สามารถทำงานได้ (ไม่มี Handover Code)
   └─ SLA เลยกำหนด
```

---

## 💡 ทางออก: 3 แนวทาง

---

## 🎯 **Option 1: Partial Handover (แนะนำ!!)** ⭐⭐⭐

### แนวคิด: **ส่งได้เลยถ้า Progress >= 80%**

```
┌─────────────────────────────────────────────────────────────────┐
│              Option 1: Partial Handover System                   │
└─────────────────────────────────────────────────────────────────┘

📋 กฎใหม่:
   ✅ ถ้า Progress >= 80% → อนุญาตให้สร้าง Handover Code
   ✅ Shortage ที่เหลือแยกจัดการใน Shortage Queue
   ✅ สินค้าที่หยิบได้ส่งได้เลย

🔄 Workflow:

Day 1: Picker หยิบของ
├─ Progress = 90% (45/50 ชิ้น)
├─ SKU C: Shortage 5 ชิ้น → บันทึกลง Shortage Queue
└─> ✅ Progress >= 80% → อนุญาตให้ Packer ทำงานต่อ!

Day 1: Packer แพ็คและส่งมอบ
├─ สร้าง Handover Code: BH-20251117-001 ✅
├─ แพ็ค 45 ชิ้นที่มี
├─ ส่งมอบให้ขนส่ง
└─> ลูกค้า 9 Orders ได้รับสินค้าทันเวลา ✅

Day 1: ทีมออนไลน์จัดการ Shortage
├─ ดู Shortage Queue
├─ SKU C: Shortage 5 ชิ้น (1 Order)
└─> ตัดสินใจ:
    ├─ รอสต็อกเข้า → สร้าง Batch ใหม่ (R2) ทีหลัง
    ├─ ยกเลิก → แจ้งลูกค้า refund
    └─ แทน SKU → เปลี่ยนเป็น SKU อื่น

Day 3: สต็อก SKU C เข้า
└─> สร้าง Batch ใหม่ (SH-2025-11-20-R1) สำหรับ SKU C
    └─> ส่งให้ลูกค้า 1 Order ที่เหลือ
```

### ✅ ข้อดี:
- ✅ **ไม่ Block Batch** - ส่งของที่มีได้เลย
- ✅ **ลูกค้าได้รับของเร็วขึ้น** - 90% ของลูกค้าไม่ต้องรอ
- ✅ **ยืดหยุ่น** - Shortage จัดการแยกได้
- ✅ **SLA ดีขึ้น** - ส่งทันเวลา

### ❌ ข้อเสีย:
- ⚠️ **ลูกค้าบางรายได้สินค้าไม่ครบ** - แต่แจ้งให้ทราบและส่งภายหลัง
- ⚠️ **ต้องสร้าง Batch เพิ่ม** - สำหรับ Shortage

### 🛠️ Implementation:

**แก้ไข `app.py`:**

```python
@app.route("/api/batch/<batch_id>/generate-handover-code", methods=["POST"])
@login_required
def api_generate_handover_code(batch_id):
    batch = db.session.get(Batch, batch_id)
    if not batch:
        return jsonify({"success": False, "error": "ไม่พบ Batch"}), 404

    progress_data = calculate_batch_progress(batch_id)

    # ✅ NEW: อนุญาตให้ส่งถ้า Progress >= 80%
    MINIMUM_PROGRESS = 80  # กำหนดเกณฑ์ขั้นต่ำ

    if progress_data["progress_percent"] < MINIMUM_PROGRESS:
        return jsonify({
            "success": False,
            "error": f"Batch Progress ต่ำกว่า {MINIMUM_PROGRESS}% (ปัจจุบัน: {progress_data['progress_percent']:.1f}%)\n"
                    f"หยิบได้: {progress_data['completed_qty']}/{progress_data['total_qty']} ชิ้น\n"
                    f"กรุณาหยิบให้ครบอย่างน้อย {MINIMUM_PROGRESS}% ก่อน"
        }), 400

    # ⚠️ เตือนถ้า Progress ไม่ถึง 100%
    warning_message = None
    if progress_data["progress_percent"] < 100:
        shortage_count = progress_data["total_qty"] - progress_data["completed_qty"]
        warning_message = f"⚠️ Batch นี้มี Shortage {shortage_count} ชิ้น ({100 - progress_data['progress_percent']:.1f}%)\n" \
                         f"สินค้าที่หยิบได้ {progress_data['completed_qty']} ชิ้น จะถูกส่งมอบ\n" \
                         f"Shortage จะถูกจัดการแยกใน Shortage Queue"

    # Check if code already exists
    if batch.handover_code:
        return jsonify({
            "success": False,
            "error": f"Batch นี้มีรหัสส่งมอบแล้ว: {batch.handover_code}"
        }), 400

    # สร้าง Handover Code ต่อ...
    # (โค้ดเดิม)

    return jsonify({
        "success": True,
        "handover_code": handover_code,
        "batch_id": batch_id,
        "warning": warning_message  # ✅ ส่ง warning กลับไป
    })
```

---

## 🔄 **Option 2: Auto Batch Split (ซับซ้อน แต่ยืดหยุ่นมาก)** ⭐⭐

### แนวคิด: **แยก Batch อัตโนมัติเมื่อเจอ Shortage**

```
┌─────────────────────────────────────────────────────────────────┐
│              Option 2: Auto Batch Split System                   │
└─────────────────────────────────────────────────────────────────┘

🔄 Workflow:

Day 1: Picker หยิบของ
├─ Progress = 90% (45/50 ชิ้น)
├─ SKU C: Shortage 5 ชิ้น
└─> ✅ ระบบแยก Batch อัตโนมัติ!

ระบบทำงาน:
├─> สร้าง Batch A: SH-2025-11-17-R1-A (Complete 100%)
│   ├─ Orders: 9 Orders (ไม่มี SKU C)
│   ├─ Qty: 45/45 ชิ้น ✅
│   └─> พร้อมส่งได้เลย!
│
└─> สร้าง Batch B: SH-2025-11-17-R1-B (Pending)
    ├─ Orders: 1 Order (มี SKU C)
    ├─ Qty: 0/5 ชิ้น ⚠️ (Shortage)
    └─> รอสต็อกเข้า

Day 1: Packer
├─> ทำงานกับ Batch A
├─> สร้าง Handover Code: BH-20251117-001
└─> ส่งมอบ 9 Orders ✅

Day 3: สต็อก SKU C เข้า
├─> Picker หยิบ Batch B
├─> Progress = 100% (5/5 ชิ้น)
└─> Packer ส่งมอบ Batch B
```

### ✅ ข้อดี:
- ✅ **แยกชัดเจน** - Batch ที่พร้อมกับที่ไม่พร้อม
- ✅ **ไม่ Block** - ส่งได้ทันที
- ✅ **ยืดหยุ่นมาก** - จัดการแยกกันได้

### ❌ ข้อเสีย:
- ❌ **ซับซ้อนมาก** - ต้องเขียน Logic แยก Batch
- ❌ **Batch จำนวนมาก** - ถ้ามี Shortage บ่อย
- ❌ **ยากต่อการ Track** - Batch เดิมถูกแยก

### 🛠️ Implementation:

**สร้าง Function ใหม่:**

```python
def split_batch_by_shortage(batch_id):
    """
    แยก Batch เป็น 2 Batch:
    - Batch A: Orders ที่หยิบครบแล้ว (Progress 100%)
    - Batch B: Orders ที่มี Shortage (รอสต็อก)
    """
    batch = db.session.get(Batch, batch_id)
    orders = OrderLine.query.filter_by(batch_id=batch_id).all()

    # แยก Orders
    complete_orders = []
    shortage_orders = []

    for order in orders:
        if order.shortage_qty > 0:
            shortage_orders.append(order)
        else:
            complete_orders.append(order)

    if not shortage_orders:
        return None  # ไม่ต้องแยก

    # สร้าง Batch A (Complete)
    batch_a_id = f"{batch_id}-A"
    batch_a = Batch(
        batch_id=batch_a_id,
        platform=batch.platform,
        batch_date=batch.batch_date,
        run_no=batch.run_no,
        total_orders=len(complete_orders),
        # ... copy other fields
    )
    db.session.add(batch_a)

    # ย้าย Orders ไป Batch A
    for order in complete_orders:
        order.batch_id = batch_a_id

    # Batch B = Batch เดิม (เหลือแต่ Shortage)
    batch.batch_id = f"{batch_id}-B"
    batch.total_orders = len(shortage_orders)

    db.session.commit()

    return {
        "batch_a": batch_a_id,  # พร้อมส่ง
        "batch_b": f"{batch_id}-B"  # รอสต็อก
    }
```

**เรียกใช้:**

```python
@app.route("/api/batch/<batch_id>/split", methods=["POST"])
@login_required
def api_split_batch(batch_id):
    result = split_batch_by_shortage(batch_id)

    if result:
        return jsonify({
            "success": True,
            "message": "แยก Batch สำเร็จ",
            "batch_complete": result["batch_a"],
            "batch_shortage": result["batch_b"]
        })
    else:
        return jsonify({
            "success": False,
            "error": "Batch นี้ไม่มี Shortage ไม่ต้องแยก"
        })
```

---

## 🚫 **Option 3: รอจนครบ 100% (ระบบปัจจุบัน)** ⭐

### แนวคิด: **ต้องหยิบครบทุกอย่างก่อนถึงจะส่งได้**

```
Day 1: Progress 90% → ❌ ไม่สามารถส่งได้
Day 2: Progress 90% → ❌ ยังไม่สามารถส่งได้
Day 3: Progress 100% → ✅ ส่งได้
```

### ✅ ข้อดี:
- ✅ **ง่าย** - ไม่ต้องแก้โค้ด
- ✅ **ลูกค้าได้สินค้าครบ** - ไม่ต้องส่งแยก

### ❌ ข้อเสีย:
- ❌ **Batch ค้าง** - รอนานถ้า Shortage นาน
- ❌ **ลูกค้าที่ไม่เกี่ยวต้องรอ** - 90% ต้องรอ 10%
- ❌ **SLA แย่** - มักเลยกำหนด

---

## 🎯 คำแนะนำสุดท้าย

### ✨ **แนวทางที่ดีที่สุดสำหรับคุณ: Hybrid (Option 1 + Manual Split)**

```
┌─────────────────────────────────────────────────────────────────┐
│           Hybrid: Partial Handover + Manual Split                │
└─────────────────────────────────────────────────────────────────┘

กฎการทำงาน:
├─ ✅ ถ้า Progress >= 90% → อนุญาตส่งได้ (Partial Handover)
├─ ⚠️ ถ้า Progress < 90% → ให้ทีมออนไลน์ตัดสินใจ:
│   ├─ รอสต็อก (ถ้าคาดว่ามาเร็ว)
│   └─ Manual Split (ถ้าคาดว่ามานาน)
└─ 📋 Shortage Queue: จัดการ Shortage แยกต่างหาก

📊 ตัวอย่าง:

Scenario A: Shortage น้อย (5%)
├─ Progress = 95%
└─> ✅ ส่งเลย! (Partial Handover)

Scenario B: Shortage ปานกลาง (15%)
├─ Progress = 85%
├─> ⏳ รอสต็อก 1-2 วัน หรือ
└─> 🔄 Manual Split (ถ้ารอนาน)

Scenario C: Shortage เยอะ (30%)
├─ Progress = 70%
└─> 🔄 แนะนำ Split ทันที
```

---

## 🛠️ Implementation Plan

### Phase 1: Partial Handover (เริ่มใช้ได้ทันที) ⭐

**ขั้นตอน:**

1. **แก้ไข `app.py` (5 นาที)**
   ```python
   # เปลี่ยนจาก:
   if progress_data["progress_percent"] < 100:

   # เป็น:
   MINIMUM_PROGRESS = 80  # หรือ 90
   if progress_data["progress_percent"] < MINIMUM_PROGRESS:
   ```

2. **เพิ่ม Warning Message**
   - แสดงว่ามี Shortage เท่าไหร่
   - แจ้งว่าจะส่งเฉพาะที่มี

3. **อัปเดต UI** (Optional)
   - ปุ่ม "ส่งมอบบางส่วน" (Partial Handover)
   - แสดง Warning ชัดเจน

4. **ทดสอบ**
   - สร้าง Batch ที่มี Shortage
   - ลอง Generate Handover Code
   - ตรวจสอบว่าทำงานถูกต้อง

---

### Phase 2: Manual Split (เพิ่มทีหลังถ้าต้องการ)

**ขั้นตอน:**

1. **สร้าง UI ปุ่ม "แยก Batch"**
   - ใน Batch Detail
   - แสดงเฉพาะ Admin

2. **สร้าง API `/api/batch/<id>/split`**
   - แยก Orders ที่ครบแล้ว
   - แยก Orders ที่มี Shortage

3. **อัปเดต Batch ID**
   - `-A` = พร้อมส่ง
   - `-B` = รอสต็อก

4. **ทดสอบ**

---

## 📋 สรุปการตัดสินใจ

| คำถาม | คำตอบ | แนวทาง |
|-------|-------|--------|
| **Batch ต้องค้าง 3 วันไหม?** | ❌ ไม่ต้อง | ใช้ Partial Handover (>= 80%) |
| **สินค้าอื่นควรส่งได้ไหม?** | ✅ ควรส่ง | อย่ารอให้ลูกค้าเสียเวลา |
| **ต้องรอ SKU เดียวก่อนไหม?** | ❌ ไม่ต้อง | แยกจัดการ Shortage ใน Queue |
| **ควร Split Batch ไหม?** | ✅ ขึ้นกับสถานการณ์ | Manual Split เมื่อ Shortage เยอะ |

---

## 🎯 แผนการทำงานที่แนะนำ

```
┌─────────────────────────────────────────────────────────────────┐
│                   Recommended Workflow                           │
└─────────────────────────────────────────────────────────────────┘

1. Picker หยิบของ
   ├─ บันทึก picked_qty
   └─ บันทึก shortage_qty (ถ้ามี)

2. Progress >= 80%?
   ├─ ✅ ใช่ → อนุญาตให้ Packer ส่งได้
   │   ├─ สร้าง Handover Code
   │   ├─ แพ็คสินค้าที่มี
   │   └─ ส่งมอบ
   │
   └─ ❌ ไม่ใช่ → ทีมออนไลน์ตัดสินใจ:
       ├─ รอสต็อก (ถ้าคาดว่ามาเร็ว < 2 วัน)
       └─ Manual Split (ถ้าคาดว่ามานาน >= 3 วัน)

3. Shortage Queue
   ├─ ทีมออนไลน์ดูทุกวัน
   ├─ ตัดสินใจ: รอ/ยกเลิก/แทน SKU
   └─ ถ้าได้สต็อก → สร้าง Batch ใหม่

4. Monitor SLA
   ├─ ดู Dashboard → กรอง "เลยกำหนด"
   └─ จัดการ Shortage ที่ค้างนาน
```

---

## 📞 Next Steps

1. **ตัดสินใจว่าจะใช้แนวทางไหน:**
   - Option 1: Partial Handover (แนะนำ)
   - Option 2: Auto Split (ซับซ้อน)
   - Hybrid: Partial + Manual Split

2. **กำหนด MINIMUM_PROGRESS:**
   - 80% = ยืดหยุ่นมาก
   - 90% = กลางๆ (แนะนำ)
   - 95% = เข้มงวด

3. **Implement Phase 1** (Partial Handover)

4. **ทดสอบกับ Batch จริง**

5. **Feedback จากทีม** → ปรับแต่ง

---

**อัปเดตล่าสุด:** 2025-11-17
**เวอร์ชัน:** 1.0
**ผู้เขียน:** VNIX Development Team

