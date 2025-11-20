# Phase 3: Stock Import + SLA-based Reallocation

## 🎯 Objective
เมื่อ import สต็อกใหม่ → จัดสรรให้ orders ที่ `waiting_stock` โดยอัตโนมัติตามลำดับ SLA (เร็วสุดก่อน)

---

## 📋 Changes Summary

### 1. **New Function: `reallocate_waiting_orders()`** (`importers.py:304-419`)

ฟังก์ชันใหม่สำหรับจัดสรรสต็อกให้ orders ที่รอสต็อก

#### Workflow:
```python
def reallocate_waiting_orders(updated_skus: list) -> dict:
    """
    1. หา orders ที่ batch_status='waiting_stock' สำหรับ SKU ที่ import
    2. คำนวณ SLA ถ้ายังไม่มี
    3. เรียงตาม SLA (เร็วสุดก่อน)
    4. จัดสรรสต็อก:
       - มีสต็อกพอ → เปลี่ยนเป็น 'pending_batch'
       - สต็อกไม่พอ → ยังคงเป็น 'waiting_stock'
    5. Return สรุปผลการจัดสรร
    """
```

#### Return Value:
```python
{
    'total_reallocated': 5,  # จำนวน orders ที่จัดสรรได้ทั้งหมด
    'by_sku': {
        'SKU-001': {
            'reallocated': 3,      # จัดสรรได้ 3 orders
            'still_waiting': 2,    # ยังรอ 2 orders
            'old_qty': 10,
            'new_qty': 15
        }
    },
    'messages': [
        "📦 SKU-001: สต็อก 10 → 15 | จัดสรรให้ 3 orders ตาม SLA | ยังรอ 2 orders"
    ]
}
```

---

### 2. **Integration into `import_stock()`** (`importers.py:301-316`)

เพิ่มการเรียก `reallocate_waiting_orders()` หลังจาก import สต็อกเสร็จ

```python
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
```

---

## 🔄 Complete Workflow

### Before Phase 3:
```
1. Import Stock
2. Update Stock table
3. Recalculate reserved_qty
4. Update Shortage Records (ShortageQueue)
5. ❌ Orders ที่ waiting_stock ยังคงรออยู่
```

### After Phase 3:
```
1. Import Stock
2. Update Stock table
3. Recalculate reserved_qty
4. Update Shortage Records (ShortageQueue)
5. ✅ Reallocate waiting_stock orders:
   a. Sort by SLA (earliest first)
   b. Check stock availability
   c. Change status: waiting_stock → pending_batch
   d. Show flash messages
6. ✅ User can now create batch with reallocated orders
```

---

## 📊 Example Scenario

### Setup:
```
Orders:
- Order A: SKU-001 x5, SLA = 2025-01-20, batch_status = 'waiting_stock'
- Order B: SKU-001 x3, SLA = 2025-01-21, batch_status = 'waiting_stock'
- Order C: SKU-001 x2, SLA = 2025-01-22, batch_status = 'waiting_stock'

Current Stock:
- SKU-001: qty = 0, reserved_qty = 0, available_qty = 0
```

### Action:
```
Import Stock:
- SKU-001: qty = 8
```

### Result:
```
✅ Reallocation (SLA Priority):

1. Order A (SLA: 2025-01-20):
   - Need: 5, Available: 8
   - ✅ Reallocated → pending_batch
   - Remaining: 3

2. Order B (SLA: 2025-01-21):
   - Need: 3, Available: 3
   - ✅ Reallocated → pending_batch
   - Remaining: 0

3. Order C (SLA: 2025-01-22):
   - Need: 2, Available: 0
   - ⏳ Still waiting_stock
   - Remaining: 0

Summary:
- Total Reallocated: 2 orders (A, B)
- Still Waiting: 1 order (C)

Flash Message:
🔄 จัดสรรสต็อกใหม่สำเร็จ: 2 orders ถูกเปลี่ยนจาก 'รอสต็อก' เป็น 'รอสร้าง Batch' ตามลำดับ SLA
📦 SKU-001: สต็อก 0 → 8 | จัดสรรให้ 2 orders ตาม SLA | ยังรอ 1 orders
```

---

## 🧪 Test Cases

### Test Case 1: Full Reallocation (สต็อกพอทั้งหมด)

**Scenario**: Import สต็อกพอสำหรับทุก waiting orders

**Steps**:
1. สร้าง orders:
   - Order 1: SKU-A x5, SLA = Today, waiting_stock
   - Order 2: SKU-A x3, SLA = Tomorrow, waiting_stock
2. Import Stock: SKU-A = 10
3. ตรวจสอบ:
   - ✅ Order 1, 2 → `pending_batch`
   - ✅ Flash: "จัดสรรสต็อกใหม่สำเร็จ: 2 orders"
   - ✅ สามารถสร้าง Batch ได้

**Expected Log**:
```
✅ Reallocated: Order 1 | SKU-A x5 | SLA: 2025-01-20 | Remaining: 5
✅ Reallocated: Order 2 | SKU-A x3 | SLA: 2025-01-21 | Remaining: 2
✅ Total Reallocated: 2 orders
```

---

### Test Case 2: Partial Reallocation (สต็อกพอบางส่วน)

**Scenario**: Import สต็อกพอสำหรับบาง orders เท่านั้น

**Steps**:
1. สร้าง orders (เรียงตาม SLA):
   - Order A: SKU-B x5, SLA = 2025-01-20 (วันนี้)
   - Order B: SKU-B x3, SLA = 2025-01-21 (พรุ่งนี้)
   - Order C: SKU-B x4, SLA = 2025-01-22 (มะรืน)
2. Import Stock: SKU-B = 7
3. ตรวจสอบ:
   - ✅ Order A (SLA เร็วสุด) → `pending_batch` (ใช้สต็อก 5, เหลือ 2)
   - ⏳ Order B → ยังคง `waiting_stock` (ต้องการ 3, มีแค่ 2)
   - ⏳ Order C → ยังคง `waiting_stock` (ไม่มีสต็อกเหลือ)

**Expected Result**:
- Reallocated: 1 order (Order A only)
- Still Waiting: 2 orders (B, C)
- Flash: "จัดสรรให้ 1 orders ตาม SLA | ยังรอ 2 orders"

---

### Test Case 3: No Waiting Orders (ไม่มี orders ที่รอ)

**Scenario**: Import สต็อก แต่ไม่มี orders ที่ waiting_stock

**Steps**:
1. Import Stock: SKU-C = 100
2. ไม่มี orders ที่ `waiting_stock`
3. ตรวจสอบ:
   - ✅ Stock อัปเดตปกติ
   - ✅ ไม่มี reallocation message
   - ✅ ไม่มี error

**Expected Result**:
```python
realloc_result = {
    'total_reallocated': 0,
    'by_sku': {},
    'messages': []
}
```

---

### Test Case 4: SLA Priority Verification

**Scenario**: ตรวจสอบว่า order ที่ SLA เร็วกว่าได้รับสต็อกก่อน

**Steps**:
1. สร้าง orders (ลำดับสุ่ม):
   - Order X: SKU-D x2, SLA = 2025-01-25 (ช้าสุด)
   - Order Y: SKU-D x2, SLA = 2025-01-20 (เร็วสุด)
   - Order Z: SKU-D x2, SLA = 2025-01-22 (กลาง)
2. Import Stock: SKU-D = 4
3. ตรวจสอบ:
   - ✅ Order Y (SLA เร็วสุด) → `pending_batch`
   - ✅ Order Z (SLA กลาง) → `pending_batch`
   - ⏳ Order X (SLA ช้าสุด) → ยังคง `waiting_stock`

**Expected Log Order**:
```
✅ Reallocated: Order Y | SKU-D x2 | SLA: 2025-01-20 | Remaining: 2
✅ Reallocated: Order Z | SKU-D x2 | SLA: 2025-01-22 | Remaining: 0
⏳ Still Waiting: Order X | SKU-D x2 | SLA: 2025-01-25 | Available: 0
```

---

## 🔍 Key Implementation Details

### 1. **SLA Sorting Logic**
```python
waiting_orders = sorted(
    waiting_orders,
    key=lambda o: (o.sla_date is None, o.sla_date, o.order_time or datetime.min)
)
```
- `o.sla_date is None`: Orders without SLA ไปท้ายสุด
- `o.sla_date`: เรียงตาม SLA date (เร็ว → ช้า)
- `o.order_time`: ถ้า SLA เท่ากัน ให้เรียงตาม order_time

### 2. **Stock Availability Check**
```python
stock = Stock.query.filter_by(sku=sku).first()
available = stock.available_qty  # Uses property: qty - reserved_qty
```
- ใช้ `available_qty` (not `qty`) เพื่อไม่รบกวน reserved stock

### 3. **Status Transition**
```
waiting_stock → pending_batch
```
- **NOT** directly to `batched` (ต้อง create batch ก่อน)
- User ยังต้องไป create batch manually หลัง reallocation

---

## 🚀 Next Steps After Reallocation

### Manual Batch Creation:
1. User เห็น flash message: "จัดสรรสต็อกใหม่สำเร็จ: X orders"
2. ไปที่ `/batch/create`
3. เลือก platform
4. Preview จะแสดง orders ที่ถูก reallocate
5. สร้าง Batch

### Future Enhancement (Optional):
**Auto-Batch Creation**:
- สร้าง Batch อัตโนมัติทันทีหลัง reallocation
- ต้องระวัง race condition
- ต้องจัดการ run_no ให้ถูกต้อง

---

## 📝 Logging and Notification

### Console Logs:
```
✅ Reallocated: Order ABC123 | SKU-001 x5 | SLA: 2025-01-20 | Remaining: 10
⏳ Still Waiting: Order DEF456 | SKU-001 x3 | SLA: 2025-01-21 | Available: 0
✅ Total Reallocated: 3 orders
```

### Flash Messages:
```
📦 SKU-001: สต็อก 5 → 15 | จัดสรรให้ 3 orders ตาม SLA | ยังรอ 2 orders
🔄 จัดสรรสต็อกใหม่สำเร็จ: 3 orders ถูกเปลี่ยนจาก 'รอสต็อก' เป็น 'รอสร้าง Batch' ตามลำดับ SLA
```

---

## ✅ Phase 3 Completion Checklist

- [x] Created `reallocate_waiting_orders()` function
- [x] Integrated into `import_stock()`
- [x] SLA-based sorting implementation
- [x] Stock availability check
- [x] Status transition (waiting_stock → pending_batch)
- [x] Flash messages and logging
- [x] Return reallocation summary
- [x] Test syntax (Python compilation)
- [x] Create Phase 3 documentation

**Status**: ✅ Phase 3 Complete - Ready for Testing!

---

## 🔗 Integration with Previous Phases

### Phase 0 ✅
- Stock reservation fix ensures `available_qty` is accurate
- No over-reservation issues

### Phase 1 ✅
- `sla_date` field is used for sorting
- Auto-calculated if missing

### Phase 2 ✅
- Orders marked as `waiting_stock` by batch creation
- Phase 3 reallocates them back to `pending_batch`

### Phase 3 ✅ (Current)
- Auto-reallocation when stock imported
- SLA priority maintained

### Phase 4 🔜 (Next)
- Shortage Queue UI improvements
- SLA-based sorting in UI
- Visual SLA warnings

---

## 📚 References

- **Phase 2 Doc**: [SLA-based Batch Creation](./Phase2-SLA-Based-Batch-Creation.md)
- **Function**: `reallocate_waiting_orders()` in `importers.py:304`
- **Integration**: `import_stock()` in `importers.py:301-316`
- **Route**: `import_stock_view()` in `app.py:1493`
