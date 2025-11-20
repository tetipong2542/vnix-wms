# Phase 2: SLA-based Batch Creation

## 🎯 Objective
แก้ไขระบบการสร้าง Batch จากแบบ FIFO (First In First Out) เป็นแบบ **SLA-based Priority Allocation** เพื่อให้ออเดอร์ที่มี SLA เร็วกว่าได้รับการจัดสรรสต็อกก่อน

---

## 📋 Changes Summary

### 1. **Modified `create_batch_from_pending()` Function** (`app.py:568-767`)

#### Before (FIFO):
```python
# เลือกออเดอร์ทั้งหมดที่ pending_batch
pending_orders = OrderLine.query.filter_by(
    platform=platform_std,
    batch_status="pending_batch"
).all()

# สร้าง Batch ทั้งหมด (ไม่สนใจสต็อก)
for order in pending_orders:
    order.batch_status = "batched"
    order.batch_id = batch_id
```

#### After (SLA-based):
```python
# 1. คำนวณ SLA สำหรับ orders ที่ยังไม่มี
for order in pending_orders:
    if not order.sla_date and order.order_time:
        order.sla_date = compute_due_date(platform_std, order.order_time)

# 2. เรียงลำดับตาม SLA (เร็วสุดก่อน)
pending_orders = sorted(
    pending_orders,
    key=lambda o: (o.sla_date is None, o.sla_date, o.order_time or datetime.min)
)

# 3. จำลองการจัดสรรสต็อก (SLA Priority)
stock_tracker = {}  # Track available stock
batch_orders = []   # Orders that will be in batch
waiting_orders = [] # Orders without stock

for order in pending_orders:
    available = stock_tracker.get(order.sku, 0)
    if available >= order.qty:
        batch_orders.append(order)  # ✅ มีสต็อก → เข้า Batch
        stock_tracker[order.sku] = available - order.qty
    else:
        waiting_orders.append(order)  # ❌ ไม่มีสต็อก → รอ

# 4. สร้าง Batch กับ batch_orders เท่านั้น
for order in batch_orders:
    order.batch_status = "batched"
    order.batch_id = batch_id

# 5. Mark waiting_orders เป็น "waiting_stock"
for order in waiting_orders:
    order.batch_status = "waiting_stock"

# 6. ตั้ง Batch SLA = earliest SLA ใน Batch
batch.sla_date = min([o.sla_date for o in batch_orders if o.sla_date])
```

---

### 2. **Updated Batch Preview UI** (`app.py:1662-1728`)

#### Preview Route Enhancement:
- เพิ่มการจำลองการจัดสรรสต็อกก่อนสร้าง Batch
- แสดงจำนวน orders ที่จะเข้า Batch vs. ที่จะรอสต็อก
- แสดง SLA ของ Batch

```python
# Simulate allocation in preview
for order in pending:
    available = stock_tracker.get(order.sku, 0)
    if available >= order.qty:
        batch_orders.append(order)
        stock_tracker[order.sku] = available - order.qty
    else:
        waiting_orders.append(order)

# Add allocation info to preview
preview_summary["allocation"] = {
    "batch_orders": len(batch_orders),
    "waiting_orders": len(waiting_orders),
    "batch_sla": min([o.sla_date for o in batch_orders if o.sla_date], default=None)
}
```

---

### 3. **Enhanced Batch Create Template** (`templates/batch_create.html`)

#### New UI Elements:

**Allocation Summary Box:**
```html
<div class="alert alert-info">
  <h6>สรุปการจัดสรรสต็อกตาม SLA:</h6>
  <ul>
    <li>ออเดอร์ที่จะเข้า Batch: {{ preview.allocation.batch_orders }} ออเดอร์</li>
    <li>ออเดอร์ที่รอสต็อก: {{ preview.allocation.waiting_orders }} ออเดอร์</li>
    <li>SLA ของ Batch: {{ preview.allocation.batch_sla }}</li>
  </ul>
</div>
```

**Waiting Orders Table:**
- แสดงรายการ orders ที่จะถูก mark เป็น `waiting_stock`
- แสดง Order ID, SKU, Quantity, SLA
- จำกัดแสดงแค่ 10 รายการแรก (ถ้ามีเยอะกว่า)

---

## 🔄 Workflow Comparison

### Before (FIFO):
```
1. เลือกออเดอร์ทั้งหมดที่ pending_batch
2. สร้าง Batch ทั้งหมด
3. Reserve สต็อก (อาจ over-reserve)
4. เมื่อหยิบจะเจอ shortage
```

### After (SLA-based):
```
1. เลือกออเดอร์ที่ pending_batch
2. คำนวณ SLA ถ้ายังไม่มี
3. เรียงตาม SLA (เร็วสุดก่อน)
4. จำลองการจัดสรรสต็อก:
   - มีสต็อกพอ → เข้า Batch
   - สต็อกไม่พอ → mark เป็น waiting_stock
5. สร้าง Batch กับ orders ที่มีสต็อกเท่านั้น
6. Reserve สต็อกเท่าที่จัดสรรจริง
```

---

## 📊 New Fields and Statuses

### Batch Model:
- ✅ `sla_date` (Date): SLA ของ Batch (ใช้ SLA เร็วสุดในบัตช์)

### OrderLine Model:
- ✅ `sla_date` (Date): SLA ของ order แต่ละรายการ
- ✅ `batch_status` values:
  - `pending_batch`: รอสร้าง Batch
  - `batched`: อยู่ใน Batch แล้ว
  - `waiting_stock`: รอสต็อกเข้า (ใหม่!)

---

## 🔍 Key Benefits

### 1. **SLA Compliance**
- ออเดอร์ที่ SLA เร็วกว่า ได้รับการจัดสรรสต็อกก่อน
- ลดความเสี่ยงที่จะส่งของเลย SLA

### 2. **Stock Efficiency**
- ไม่ reserve สต็อกเกินจำนวนที่มีจริง
- ออเดอร์ที่ไม่มีสต็อก จะไม่เข้า Batch (รอจัดสรรใหม่ใน Phase 3)

### 3. **Better Visibility**
- Preview แสดงข้อมูลการจัดสรรก่อนสร้าง Batch
- ผู้ใช้เห็นว่า order ไหนจะรอสต็อก

### 4. **Audit Trail**
- Log ข้อมูล SLA, จำนวน orders ในแต่ละ Batch
- Log จำนวน orders ที่รอสต็อก

---

## 🧪 Testing Checklist

### Test Case 1: Normal Batch Creation (มีสต็อกพอ)
**Scenario**: สร้าง Batch โดยมีสต็อกเพียงพอสำหรับทุก order

**Steps**:
1. Import orders สำหรับ Shopee (10 orders)
2. Import stock ให้เพียงพอทุก SKU
3. สร้าง Batch
4. ตรวจสอบ:
   - ✅ ออเดอร์ทั้งหมดอยู่ใน Batch
   - ✅ `batch.sla_date` = SLA เร็วสุด
   - ✅ ไม่มี orders ที่เป็น `waiting_stock`

**Expected Result**:
```
✅ Batch SH-2025-01-19-R1 created |
   SLA: 2025-01-20 |
   Orders in batch: 10 |
   Waiting for stock: 0
```

---

### Test Case 2: Partial Stock (บางออเดอร์ไม่มีสต็อก)
**Scenario**: สร้าง Batch โดยมีสต็อกไม่พอสำหรับบางออเดอร์

**Steps**:
1. Import orders:
   - Order A: SKU-001 x5, SLA = 2025-01-20 (วันนี้)
   - Order B: SKU-002 x3, SLA = 2025-01-21 (พรุ่งนี้)
   - Order C: SKU-001 x5, SLA = 2025-01-22 (มะรืน)
2. Import stock:
   - SKU-001: qty = 5 (พอสำหรับ Order A เท่านั้น)
   - SKU-002: qty = 3 (พอสำหรับ Order B)
3. สร้าง Batch
4. ตรวจสอบ:
   - ✅ Order A, B เข้า Batch (SLA เร็วกว่า + มีสต็อก)
   - ✅ Order C → `waiting_stock` (SLA ช้ากว่า + สต็อกไม่พอ)
   - ✅ `batch.sla_date` = 2025-01-20 (SLA ของ Order A)

**Expected Result**:
```
✅ Batch SH-2025-01-19-R1 created |
   SLA: 2025-01-20 |
   Orders in batch: 2 |
   Waiting for stock: 1

⏳ 1 orders marked as waiting_stock for Shopee
```

---

### Test Case 3: No Stock (ไม่มีสต็อกเลย)
**Scenario**: ไม่มีสต็อกสำหรับออเดอร์ใดเลย

**Steps**:
1. Import orders (10 orders)
2. ไม่ import stock (หรือสต็อก = 0)
3. พยายามสร้าง Batch
4. ตรวจสอบ:
   - ❌ Batch ไม่ถูกสร้าง
   - ✅ Error message: "No orders can be batched - all X orders are waiting for stock"
   - ✅ Orders ทั้งหมดถูก mark เป็น `waiting_stock`

**Expected Result**:
```
ValueError: No orders can be batched for Shopee - all 10 orders are waiting for stock
```

---

### Test Case 4: SLA Priority Order
**Scenario**: ตรวจสอบว่าออเดอร์ที่ SLA เร็วกว่า ได้รับการจัดสรรก่อน

**Steps**:
1. Import orders:
   - Order 1: SKU-001 x3, SLA = 2025-01-22 (มะรืน)
   - Order 2: SKU-001 x3, SLA = 2025-01-20 (วันนี้) ← เร็วสุด
   - Order 3: SKU-001 x3, SLA = 2025-01-21 (พรุ่งนี้)
2. Import stock: SKU-001 = 3 (พอสำหรับ 1 order เท่านั้น)
3. สร้าง Batch
4. ตรวจสอบ:
   - ✅ Order 2 เข้า Batch (SLA เร็วสุด)
   - ✅ Order 1, 3 → `waiting_stock`
   - ✅ `batch.sla_date` = 2025-01-20

**Expected Result**:
```
✅ Batch created | SLA: 2025-01-20 | Orders in batch: 1 | Waiting for stock: 2

Allocation Log:
  ✅ Allocated: SKU-001 x3 | SLA: 2025-01-20 | Remaining: 0
  ⏳ Waiting: SKU-001 x3 | SLA: 2025-01-21 | Available: 0 | Shortage: 3
  ⏳ Waiting: SKU-001 x3 | SLA: 2025-01-22 | Available: 0 | Shortage: 3
```

---

## 📝 Migration Notes

### Database Changes:
- ✅ Phase 1 ต้องรันก่อน (เพิ่มฟิลด์ `sla_date`)
- ✅ ใช้ Migration Script: `python migrations/run_phase1_migration.py`

### Code Changes:
- ✅ `app.py`: Modified `create_batch_from_pending()` function
- ✅ `app.py`: Modified `batch_create()` route (GET preview)
- ✅ `templates/batch_create.html`: Added allocation summary and waiting orders table

### No Breaking Changes:
- ✅ ฟังก์ชันเดิมยังใช้งานได้ (backward compatible)
- ✅ Existing batches ไม่ได้รับผลกระทบ
- ✅ API signature ไม่เปลี่ยน

---

## 🚀 Next Phase: Phase 3 - Stock Import Reallocation

Phase 3 จะเพิ่มฟีเจอร์:
1. เมื่อ import สต็อกใหม่ → จัดสรรให้ orders ที่ `waiting_stock` โดยอัตโนมัติ
2. สร้าง Batch ใหม่สำหรับ orders ที่ได้รับการจัดสรร
3. Notification เมื่อ orders ได้รับสต็อก

---

## 📚 References

- **Phase 0**: [Reserved Stock Release Fix](./Phase0-Testing-Guide.md)
- **Phase 1**: [SLA Fields Migration](../migrations/run_phase1_migration.py)
- **Flowchart**: [SLA-based Stock Allocation](../flowchart.png)
- **Utils**: `compute_due_date()` in `utils.py:244`

---

## ✅ Phase 2 Completion Checklist

- [x] Modify `create_batch_from_pending()` with SLA logic
- [x] Calculate SLA for orders without `sla_date`
- [x] Sort orders by SLA (earliest first)
- [x] Implement stock allocation simulation
- [x] Set `batch.sla_date` to earliest SLA
- [x] Mark orders without stock as `waiting_stock`
- [x] Update batch preview UI
- [x] Add allocation summary to template
- [x] Add waiting orders table to template
- [x] Test syntax (Python compilation)
- [x] Create Phase 2 documentation

**Status**: ✅ Phase 2 Complete - Ready for Testing!
