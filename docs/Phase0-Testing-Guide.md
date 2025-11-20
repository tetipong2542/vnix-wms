# Phase 0 Testing Guide: Reserved Stock Release Fix

## 🎯 Objective
ทดสอบว่า reserved_qty ถูก release อย่างถูกต้องในทุกสถานการณ์

---

## 📋 Pre-Testing Checklist

1. **Backup ฐานข้อมูล**
   ```bash
   cp data.db data.db.backup_phase0_$(date +%Y%m%d_%H%M%S)
   ```

2. **Run Migration**
   ```bash
   python migrations/run_phase0_migration.py
   ```

3. **ตรวจสอบ Migration สำเร็จ**
   - ดู Validation Report
   - ไม่มี over-reservation
   - ไม่มี reservation leaks จาก completed batches

---

## 🧪 Test Cases

### **Test 1: Picking Complete (หยิบครบ)**

**Scenario**: หยิบ SKU ครบตามจำนวนที่ต้องการ

**Steps**:
1. สร้าง Batch ใหม่ที่มี SKU-001 จำนวน 10 ชิ้น
2. เช็ค `stocks.reserved_qty` สำหรับ SKU-001 → ควรเป็น 10
3. ไปที่หน้า `/scan/sku` → สแกน SKU-001
4. หยิบครบ 10 ชิ้น
5. เช็ค `stocks.reserved_qty` สำหรับ SKU-001 → **ควรเป็น 0**

**Expected**:
```
✅ Stock Reservation Released: SKU-001 |
   Batch: ALL_BATCHES |
   Released: 10 |
   Reserved: 10 → 0 |
   Reason: picking_completed
```

---

### **Test 2: Partial Picking + Shortage**

**Scenario**: หยิบได้บางส่วน + มี shortage

**Steps**:
1. สร้าง Batch ที่มี SKU-002 จำนวน 10 ชิ้น (แต่สต็อกมีแค่ 6)
2. เช็ค `stocks.reserved_qty` → ควรเป็น 10
3. หยิบได้ 6 ชิ้น
4. Mark shortage 4 ชิ้น
5. เช็ค `stocks.reserved_qty` → **ควรเป็น 0** (เพราะ picked 6 + shortage 4 = 10)

**Expected**:
```
✅ Stock Reservation Released: SKU-002 |
   Released: 10 |
   Reason: picking_completed
```

---

### **Test 3: Shortage Cancel**

**Scenario**: ยกเลิก shortage

**Steps**:
1. สร้าง Batch ที่มี SKU-003 จำนวน 5 ชิ้น
2. Mark shortage 5 ชิ้น
3. เช็ค `stocks.reserved_qty` → ควรเป็น 5
4. ไปที่ `/shortage-queue` → Cancel shortage
5. เช็ค `stocks.reserved_qty` → **ควรเป็น 0**

**Expected**:
```
✅ Stock Reservation Released: SKU-003 |
   Batch: SH-2025-01-19-R1 |
   Released: 5 |
   Reason: shortage_cancel
```

---

### **Test 4: Handover Confirmation**

**Scenario**: ยืนยันส่งมอบ Batch ที่มี partial picking

**Steps**:
1. สร้าง Batch ที่มี:
   - SKU-004: ต้องการ 10, หยิบได้ 8, shortage 2
   - SKU-005: ต้องการ 5, หยิบได้ 5
2. เช็ค reserved_qty:
   - SKU-004: 10
   - SKU-005: 5
3. Generate Handover Code
4. ยืนยัน Handover
5. เช็ค reserved_qty:
   - SKU-004: **ควรเป็น 0** (picked 8 + shortage 2 = 10)
   - SKU-005: **ควรเป็น 0** (picked 5 = 5)

**Expected**:
```
✅ Stock Reservation Released: SKU-004 |
   Released: 10 |
   Reason: handover_confirmed

✅ Stock Reservation Released: SKU-005 |
   Released: 5 |
   Reason: handover_confirmed
```

---

### **Test 5: Multiple Batches for Same SKU**

**Scenario**: SKU เดียวกันอยู่ในหลาย Batch

**Steps**:
1. สร้าง Batch A: SKU-006 = 10 ชิ้น
2. สร้าง Batch B: SKU-006 = 5 ชิ้น
3. เช็ค reserved_qty → ควรเป็น 15
4. Handover Batch A → reserved_qty ควรเป็น 5
5. Handover Batch B → reserved_qty ควรเป็น 0

**Expected**:
- หลัง Handover Batch A: `reserved_qty = 5` (เหลือแค่ Batch B)
- หลัง Handover Batch B: `reserved_qty = 0`

---

## 🔍 Validation Queries

### **Query 1: ตรวจสอบ reserved_qty ทั้งหมด**
```sql
SELECT
    s.sku,
    s.qty AS total_stock,
    s.reserved_qty,
    (s.qty - s.reserved_qty) AS available,
    -- Active Batches
    (SELECT COUNT(DISTINCT ol.batch_id)
     FROM order_lines ol
     LEFT JOIN batches b ON ol.batch_id = b.batch_id
     WHERE ol.sku = s.sku
       AND ol.accepted = 1
       AND (b.handover_confirmed IS NULL OR b.handover_confirmed = 0)
    ) AS active_batches
FROM stocks s
WHERE s.reserved_qty > 0
ORDER BY s.reserved_qty DESC;
```

### **Query 2: ตรวจหา Batch ที่ handover แล้วแต่ยังจอง stock**
```sql
SELECT
    b.batch_id,
    b.handover_confirmed_at,
    SUM(ol.qty) AS reserved_qty_should_be_zero
FROM batches b
JOIN order_lines ol ON ol.batch_id = b.batch_id
WHERE b.handover_confirmed = 1
GROUP BY b.batch_id
HAVING SUM(ol.qty) > 0;
```

---

## ✅ Success Criteria

1. **reserved_qty = 0** สำหรับ Batch ที่:
   - Handover แล้ว
   - SKU หยิบครบแล้ว (picked + shortage = required)
   - Shortage ถูก cancel/resolve

2. **reserved_qty > 0** สำหรับ Batch ที่:
   - ยังไม่ handover
   - SKU ยังหยิบไม่ครบ

3. **No over-reservation**: `reserved_qty <= qty` เสมอ

4. **Logs ครบถ้วน**: ทุกครั้งที่ release ต้องมี log
   ```
   ✅ Stock Reservation Released: SKU | Batch | Released | Reserved | Reason
   ```

---

## 🐛 Known Issues

ถ้าเจอปัญหา:

1. **reserved_qty เป็นค่าลบ**
   - Run migration ใหม่
   - ตรวจสอบว่ามี concurrent requests หรือไม่

2. **reserved_qty ไม่ลดลงหลัง handover**
   - เช็ค app logs ว่ามี error ไหม
   - ตรวจสอบว่า `release_stock_reservation()` ถูกเรียกหรือไม่

3. **Over-reservation (reserved_qty > qty)**
   - ปัญหาจาก migration ก่อนหน้า
   - Run `phase0_fix_reserved_qty.sql` อีกรอบ

---

## 📝 Test Report Template

```markdown
## Phase 0 Test Report
Date: _______________
Tester: _______________

### Test Results
- [ ] Test 1: Picking Complete - PASS/FAIL
- [ ] Test 2: Partial Picking + Shortage - PASS/FAIL
- [ ] Test 3: Shortage Cancel - PASS/FAIL
- [ ] Test 4: Handover Confirmation - PASS/FAIL
- [ ] Test 5: Multiple Batches - PASS/FAIL

### Validation
- [ ] No over-reservation
- [ ] No reservation leaks
- [ ] Logs present

### Issues Found
(List any issues here)

### Conclusion
- [ ] Phase 0 APPROVED - Ready for Phase 1
- [ ] Phase 0 FAILED - Needs fixes
```
