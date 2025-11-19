# Dispatch Status Documentation

**Phase 2.3**: เอกสารอธิบาย dispatch_status ใน OrderLine model

## Overview

`dispatch_status` เป็น field ที่ใช้ติดตามสถานะการจัดการออเดอร์ในแต่ละขั้นตอน ตั้งแต่การหยิบสินค้าจนถึงการส่งมอบให้ขนส่ง

## Status Lifecycle

```
pending → [picking] → ready → dispatched
    ↓
partial_ready (ถ้าหยิบไม่ครบ หรือมี shortage)
```

## Status Definitions

### `pending`
**คำอธิบาย:** ยังไม่เริ่มหยิบสินค้า

**เงื่อนไข:**
- `picked_qty = 0`
- เป็น status เริ่มต้น (default)

**Action ที่ทำได้:**
- พนักงานสามารถเริ่มหยิบสินค้าได้
- สามารถ assign ให้ picker ได้

**ตัวอย่าง:**
```python
order.dispatch_status = "pending"
order.picked_qty = 0
```

---

### `ready`
**คำอธิบาย:** หยิบสินค้าครบแล้ว พร้อมส่ง

**เงื่อนไข:**
- `picked_qty >= qty` (หยิบครบทุกชิ้น)
- ไม่มี shortage ที่ยังไม่ได้จัดการ

**Action ที่ทำได้:**
- พนักงานสามารถสแกนส่งมอบได้ (scan tracking number)
- สามารถสร้าง Handover Code ได้ (ถ้าทุก order ใน Batch เป็น ready)

**ตัวอย่าง:**
```python
order.dispatch_status = "ready"
order.picked_qty = order.qty  # 10/10 ชิ้น
```

---

### `partial_ready`
**คำอธิบาย:** หยิบได้บางส่วน หรือมี shortage ที่จัดการแล้ว

**เงื่อนไข (เป็นข้อใดข้อหนึ่ง):**
1. `0 < picked_qty < qty` AND `picked_qty > 0` (หยิบได้บางส่วน)
2. มี shortage record ที่มีสถานะ `resolved`, `cancelled`, หรือ `replaced`

**Action ที่ทำได้:**
- **กรณีที่ 1**: ยังหยิบไม่ครบ → ต้องหยิบเพิ่ม หรือ mark shortage
- **กรณีที่ 2**: shortage resolved → สามารถสแกนส่งมอบได้ (แม้จะส่งไม่ครบตาม qty เดิม)

**ตัวอย่าง:**

**กรณีที่ 1**: หยิบได้บางส่วน
```python
order.dispatch_status = "partial_ready"
order.picked_qty = 5  # หยิบได้ 5/10 ชิ้น
order.shortage_qty = 5  # ขาดอีก 5 ชิ้น
# → ต้องหยิบเพิ่ม หรือ mark shortage
```

**กรณีที่ 2**: มี shortage ที่จัดการแล้ว
```python
order.dispatch_status = "partial_ready"
order.picked_qty = 5  # หยิบได้ 5/10 ชิ้น
order.shortage_qty = 0  # shortage ถูก resolve/cancel แล้ว
# → สามารถส่งมอบได้ (ส่ง 5 ชิ้น)
```

---

### `dispatched`
**คำอธิบาย:** ส่งมอบให้ขนส่งแล้ว

**เงื่อนไข:**
- ได้ทำการสแกน tracking number ส่งมอบให้ขนส่งแล้ว
- `dispatched_at` != NULL

**Action ที่ทำได้:**
- **ไม่สามารถแก้ไขได้แล้ว** (read-only)
- บันทึกใน audit log แล้ว

**ตัวอย่าง:**
```python
order.dispatch_status = "dispatched"
order.dispatched_at = datetime.now()
order.dispatched_by_username = "admin"
```

---

### `shortage` (deprecated)
**คำอธิบาย:** **ไม่ใช้แล้ว** - เปลี่ยนมาใช้ `partial_ready` แทน

**เหตุผล:**
- สร้างความสับสนกับ ShortageQueue system
- `partial_ready` ครอบคลุมทั้งกรณีหยิบไม่ครบและมี shortage
- ลดความซับซ้อนของ logic

**Migration:**
- Order ที่เคยเป็น `shortage` จะถูกเปลี่ยนเป็น `partial_ready`
- ระบบจะไม่สร้าง status `shortage` ใหม่อีกต่อไป

---

## Status Transition Examples

### Example 1: Normal Flow (หยิบครบ)

```python
# 1. เริ่มต้น
order.dispatch_status = "pending"
order.picked_qty = 0
order.qty = 10

# 2. เริ่มหยิบ (หยิบได้ 5 ชิ้น)
order.dispatch_status = "partial_ready"
order.picked_qty = 5

# 3. หยิบเพิ่ม (หยิบครบ 10 ชิ้น)
order.dispatch_status = "ready"
order.picked_qty = 10

# 4. ส่งมอบให้ขนส่ง
order.dispatch_status = "dispatched"
order.dispatched_at = datetime.now()
```

### Example 2: Shortage Flow (หยิบไม่ครบ)

```python
# 1. เริ่มต้น
order.dispatch_status = "pending"
order.picked_qty = 0
order.qty = 10

# 2. หยิบได้บางส่วน (มีสต็อกแค่ 5 ชิ้น)
order.dispatch_status = "partial_ready"
order.picked_qty = 5
order.shortage_qty = 5

# 3. Mark shortage (ขาด 5 ชิ้น)
shortage_record = ShortageQueue(
    order_line_id=order.id,
    qty_shortage=5,
    status="pending"
)
# dispatch_status ยังเป็น "partial_ready"

# 4. Resolve shortage (ยกเลิก หรือ รอสต็อก หรือ แทน SKU)
shortage_record.status = "cancelled"
order.shortage_qty = 0  # ลด shortage_qty ลง
# dispatch_status ยังเป็น "partial_ready" แต่สามารถส่งมอบได้แล้ว

# 5. ส่งมอบให้ขนส่ง (ส่ง 5 ชิ้น)
order.dispatch_status = "dispatched"
order.dispatched_at = datetime.now()
```

### Example 3: Partial Pick then Complete (หยิบเพิ่มจนครบ)

```python
# 1. หยิบได้บางส่วน
order.dispatch_status = "partial_ready"
order.picked_qty = 5
order.qty = 10

# 2. พบสต็อกเพิ่ม หยิบเพิ่ม 5 ชิ้น
order.dispatch_status = "ready"  # เปลี่ยนจาก partial_ready เป็น ready
order.picked_qty = 10
order.shortage_qty = 0

# 3. ส่งมอบ
order.dispatch_status = "dispatched"
```

---

## Common Queries

### Query 1: หา Order ที่ยังไม่เริ่มหยิบ

```python
pending_orders = OrderLine.query.filter_by(
    dispatch_status="pending"
).all()
```

### Query 2: หา Order ที่พร้อมส่ง (ready + partial_ready with no shortage)

```python
ready_orders = OrderLine.query.filter(
    OrderLine.dispatch_status.in_(['ready', 'partial_ready']),
    OrderLine.shortage_qty == 0
).all()
```

### Query 3: หา Order ที่มี Shortage ยังไม่จัดการ

```python
shortage_orders = OrderLine.query.filter(
    OrderLine.shortage_qty > 0
).all()
```

### Query 4: หา Order ที่ส่งมอบแล้ว

```python
dispatched_orders = OrderLine.query.filter_by(
    dispatch_status="dispatched"
).all()
```

---

## Business Logic Rules

### Rule 1: Order ต้องหยิบครบหรือ resolve shortage ก่อนส่งมอบ

```python
def can_dispatch(order):
    """Check if order can be dispatched"""
    if order.dispatch_status == "ready":
        return True  # หยิบครบแล้ว
    elif order.dispatch_status == "partial_ready" and order.shortage_qty == 0:
        return True  # มี shortage แต่จัดการแล้ว
    else:
        return False  # ยังหยิบไม่ครบ หรือมี shortage ที่ยังไม่จัดการ
```

### Rule 2: Batch สามารถสร้าง Handover Code ได้เมื่อ Progress = 100%

```python
def can_generate_handover_code(batch):
    """Check if batch can generate handover code"""
    progress = calculate_batch_progress(batch.batch_id)
    return progress["progress_percent"] >= 100
    # Progress คำนวณจาก: picked_qty / total_qty * 100 (shortage ไม่นับเป็นความสำเร็จ)
```

### Rule 3: Shortage ต้องได้รับการจัดการก่อนถึง resolve

```python
def resolve_shortage(shortage):
    """Resolve shortage record"""
    order = shortage.order_line

    # ต้องหยิบสินค้าครบก่อน (หรือ cancel/replace)
    expected_picked = shortage.qty_required - shortage.qty_shortage
    if order.picked_qty < expected_picked:
        raise ValidationError("ยังหยิบสินค้าไม่ครบ!")

    shortage.status = "resolved"
    order.shortage_qty -= shortage.qty_shortage  # ลด shortage_qty
```

---

## FAQ

### Q1: ทำไม partial_ready ถึงมี 2 ความหมาย?

**A:** เพื่อความยืดหยุ่นในการจัดการ:
- **ความหมายที่ 1**: หยิบได้บางส่วน → ยังทำงานไม่เสร็จ
- **ความหมายที่ 2**: มี shortage แต่จัดการแล้ว → ทำงานเสร็จแล้ว แต่ส่งไม่ครบตามจำนวนเดิม

ใช้ `shortage_qty` เป็นตัวแยกความหมาย:
- `shortage_qty > 0` → ความหมายที่ 1
- `shortage_qty = 0` → ความหมายที่ 2

### Q2: สามารถเปลี่ยน status กลับไปข้างหลังได้ไหม?

**A:** ไม่แนะนำ แต่สามารถทำได้:
- `dispatched` → **ห้าม** เปลี่ยน (ยกเว้น admin)
- `ready/partial_ready` → `pending` **ได้** (ถ้ามีการ reset picked_qty)

### Q3: ถ้า Order มีหลาย SKU จะมีหลาย dispatch_status ไหม?

**A:** ไม่ - แต่ละ OrderLine (order_id + sku) มี dispatch_status เป็นของตัวเอง

ตัวอย่าง:
```
Order #123 มี 2 SKU:
- OrderLine 1: order_id=123, sku=A, dispatch_status="ready"
- OrderLine 2: order_id=123, sku=B, dispatch_status="partial_ready"

→ Order #123 มีสถานะรวม = "partial_ready" (ยังไม่เสร็จ)
```

---

## Version History

- **v1.0** (2025-11-16): สร้างเอกสารฉบับแรก (Phase 2.3)
- สถานะปัจจุบัน: `pending`, `ready`, `partial_ready`, `dispatched`, `shortage` (deprecated)
