# Phase 5: Comprehensive Testing & Validation

## 🎯 Objective
ทดสอบและตรวจสอบความถูกต้องของทุก Phase (0-4) เพื่อป้องกันปัญหาแบบที่เคยเกิด (reserved_qty ไม่ถูก release, สต็อกแสดงผิด, etc.)

---

## 📋 Testing Checklist Overview

```
✅ Phase 0: Reserved Stock Release
✅ Phase 1: SLA Field Migration
✅ Phase 2: SLA-based Batch Creation
✅ Phase 3: Stock Import Reallocation
✅ Phase 4: Shortage Queue SLA Display
✅ Integration Testing (All Phases Together)
```

---

# Part 1: Pre-Testing Preparation

## 1.1 Database Backup

**⚠️ CRITICAL**: สำรองฐานข้อมูลก่อนทดสอบ

```bash
# Backup with timestamp
cp data.db "data.db.backup_$(date +%Y%m%d_%H%M%S)"

# Verify backup exists
ls -lh data.db*
```

## 1.2 Run Migrations

```bash
# Phase 0: Fix reserved_qty
python migrations/run_phase0_migration.py

# Phase 1: Add SLA fields
python migrations/run_phase1_migration.py
```

**Validation**:
```sql
-- Check SLA columns exist
PRAGMA table_info(order_lines);
PRAGMA table_info(batches);

-- Should see sla_date column in both tables
```

## 1.3 Syntax Validation

```bash
# Test all Python files
python -m py_compile app.py
python -m py_compile importers.py
python -m py_compile utils.py
python -m py_compile models.py

# If all pass: No output
# If fail: Shows syntax error
```

---

# Part 2: Phase 0 Testing - Reserved Stock Release

## Test 0.1: Picking Complete (หยิบครบ)

**Purpose**: ตรวจสอบว่า reserved_qty ถูก release เมื่อหยิบครบ

### Setup:
```sql
-- Check current stock
SELECT sku, qty, reserved_qty, (qty - reserved_qty) as available
FROM stocks
WHERE sku = 'TEST-SKU-001';
```

### Steps:
1. สร้าง Batch ด้วย SKU-001 x10
2. เช็ค `reserved_qty` → ควรเป็น 10
3. หยิบ SKU-001 ครบ 10 ชิ้น
4. เช็ค `reserved_qty` → **ต้องเป็น 0**

### Validation Query:
```sql
SELECT
    s.sku,
    s.qty as total_stock,
    s.reserved_qty,
    (s.qty - s.reserved_qty) as available,
    -- Count active batches
    (SELECT COUNT(DISTINCT ol.batch_id)
     FROM order_lines ol
     JOIN batches b ON ol.batch_id = b.batch_id
     WHERE ol.sku = s.sku
       AND ol.accepted = 1
       AND (b.handover_confirmed IS NULL OR b.handover_confirmed = 0)
    ) as active_batches
FROM stocks s
WHERE s.sku = 'TEST-SKU-001';
```

### Expected Result:
```
✅ reserved_qty = 0
✅ active_batches = 0 (if batch completed)
✅ Log: "Stock Reservation Released: TEST-SKU-001 | Released: 10 | Reason: picking_completed"
```

### ❌ Failure Indicators:
- `reserved_qty` ยังเป็น 10 (ไม่ถูก release)
- `available_qty` ยังเป็นลบ
- ไม่มี log การ release

---

## Test 0.2: Handover Confirmation

**Purpose**: ตรวจสอบว่า reserved_qty ถูก release เมื่อ handover

### Steps:
1. สร้าง Batch ที่มี หลาย SKU
2. Generate Handover Code
3. ยืนยัน Handover
4. เช็ค `reserved_qty` ทุก SKU ใน Batch → **ต้องเป็น 0**

### Validation Query:
```sql
-- Check reserved_qty after handover
SELECT
    b.batch_id,
    b.handover_confirmed,
    b.handover_confirmed_at,
    s.sku,
    s.reserved_qty
FROM batches b
JOIN order_lines ol ON ol.batch_id = b.batch_id
JOIN stocks s ON s.sku = ol.sku
WHERE b.batch_id = 'SH-2025-01-19-R1'
  AND b.handover_confirmed = 1;
```

### Expected Result:
```
✅ All reserved_qty = 0 for handover_confirmed batches
✅ Log: "Stock Reservation Released: ... | Reason: handover_confirmed"
```

---

## Test 0.3: No Over-Reservation

**Purpose**: ตรวจสอบว่า reserved_qty ≤ qty เสมอ

### Validation Query:
```sql
-- Find over-reservations
SELECT
    sku,
    qty as total,
    reserved_qty as reserved,
    (reserved_qty - qty) as over_reserved
FROM stocks
WHERE reserved_qty > qty;
```

### Expected Result:
```
✅ No rows returned (no over-reservation)
```

### ❌ Failure: If any rows returned
```
Action: Run phase0 migration again
```

---

# Part 3: Phase 1 Testing - SLA Fields

## Test 1.1: SLA Field Exists

### Validation Query:
```sql
-- Check SLA columns
SELECT COUNT(*) as orders_with_sla
FROM order_lines
WHERE sla_date IS NOT NULL;

SELECT COUNT(*) as batches_with_sla
FROM batches
WHERE sla_date IS NOT NULL;
```

### Expected Result:
```
✅ orders_with_sla > 0 (if you have orders with order_time)
✅ batches_with_sla > 0 (if you have completed batches)
```

---

## Test 1.2: SLA Calculation Correctness

**Purpose**: ตรวจสอบว่า SLA คำนวณถูกต้องตาม platform

### Validation Query:
```sql
-- Check SLA distribution
SELECT
    platform,
    COUNT(*) as total_orders,
    COUNT(sla_date) as with_sla,
    COUNT(*) - COUNT(sla_date) as without_sla
FROM order_lines
GROUP BY platform;
```

### Manual Verification:
```sql
-- Pick a sample order
SELECT
    order_id,
    platform,
    datetime(order_time, 'localtime') as order_time_th,
    sla_date
FROM order_lines
WHERE platform = 'Shopee'
  AND order_time IS NOT NULL
LIMIT 5;
```

**Check Rules**:
- **Shopee/TikTok**: Order before 12:00 → SLA = same day (if business day)
- **Lazada**: Order before 11:00 → SLA = same day (if business day)
- **Weekend orders** → SLA = next business day

---

# Part 4: Phase 2 Testing - SLA-based Batch Creation

## Test 2.1: SLA Priority Allocation

**Purpose**: ตรวจสอบว่า orders ที่ SLA เร็วกว่าได้สต็อกก่อน

### Setup:
```
Create 3 pending orders for SKU-001:
- Order A: qty=3, SLA=2025-01-22 (ช้าสุด)
- Order B: qty=3, SLA=2025-01-20 (เร็วสุด)
- Order C: qty=3, SLA=2025-01-21 (กลาง)

Stock: SKU-001 = 3 (พอสำหรับ 1 order เท่านั้น)
```

### Steps:
1. สร้าง Batch สำหรับ Shopee
2. Preview → ควรแสดงว่า Order B จะเข้า Batch
3. สร้าง Batch
4. เช็คผลลัพธ์

### Validation Query:
```sql
-- Check which order got into batch
SELECT
    order_id,
    sku,
    qty,
    sla_date,
    batch_status,
    batch_id
FROM order_lines
WHERE sku = 'SKU-001'
ORDER BY sla_date;
```

### Expected Result:
```
Order B: batch_status = 'batched', batch_id = 'SH-...'  ← SLA เร็วสุด
Order C: batch_status = 'waiting_stock', batch_id = NULL
Order A: batch_status = 'waiting_stock', batch_id = NULL
```

---

## Test 2.2: Batch SLA Calculation

**Purpose**: ตรวจสอบว่า batch.sla_date = earliest SLA in batch

### Validation Query:
```sql
-- Check batch SLA matches earliest order SLA
SELECT
    b.batch_id,
    b.sla_date as batch_sla,
    MIN(ol.sla_date) as earliest_order_sla,
    CASE
        WHEN b.sla_date = MIN(ol.sla_date) THEN '✅ MATCH'
        ELSE '❌ MISMATCH'
    END as validation
FROM batches b
JOIN order_lines ol ON ol.batch_id = b.batch_id
WHERE b.batch_id = 'SH-2025-01-19-R1'
GROUP BY b.batch_id;
```

### Expected Result:
```
validation = '✅ MATCH'
```

---

## Test 2.3: Waiting Stock Orders

**Purpose**: ตรวจสอบว่า orders ที่ไม่มีสต็อกถูก mark เป็น waiting_stock

### Validation Query:
```sql
-- Count waiting_stock orders
SELECT
    COUNT(*) as waiting_count,
    GROUP_CONCAT(DISTINCT platform) as platforms
FROM order_lines
WHERE batch_status = 'waiting_stock';
```

### Expected Result:
```
✅ waiting_count > 0 (if there were insufficient stock orders)
```

---

# Part 5: Phase 3 Testing - Stock Reallocation

## Test 3.1: Reallocation on Stock Import

**Purpose**: ตรวจสอบว่า waiting_stock orders ถูกจัดสรรใหม่เมื่อ import สต็อก

### Setup:
```sql
-- Create waiting_stock order
UPDATE order_lines
SET batch_status = 'waiting_stock'
WHERE order_id = 'TEST-ORDER-001';

-- Check before import
SELECT batch_status FROM order_lines WHERE order_id = 'TEST-ORDER-001';
-- Result: 'waiting_stock'
```

### Steps:
1. Import Stock สำหรับ SKU ที่ order รอ
2. ดู flash message → ควรแสดง reallocation success
3. เช็คสถานะ order

### Validation Query:
```sql
-- Check after import
SELECT
    order_id,
    sku,
    batch_status,
    sla_date
FROM order_lines
WHERE order_id = 'TEST-ORDER-001';
```

### Expected Result:
```
batch_status = 'pending_batch'  ← Changed from 'waiting_stock'

Flash Message:
🔄 จัดสรรสต็อกใหม่สำเร็จ: 1 orders ถูกเปลี่ยนจาก 'รอสต็อก' เป็น 'รอสร้าง Batch' ตามลำดับ SLA
```

---

## Test 3.2: SLA Priority in Reallocation

**Purpose**: ตรวจสอบว่า reallocation เรียงตาม SLA

### Setup:
```
3 waiting_stock orders for SKU-002:
- Order X: SLA=2025-01-25 (ช้าสุด)
- Order Y: SLA=2025-01-20 (เร็วสุด)
- Order Z: SLA=2025-01-22 (กลาง)

Import: SKU-002 qty = 4 (พอสำหรับ 2 orders)
```

### Expected Result:
```
Order Y (SLA เร็วสุด): batch_status = 'pending_batch'
Order Z (SLA กลาง): batch_status = 'pending_batch'
Order X (SLA ช้าสุด): batch_status = 'waiting_stock'  ← Still waiting
```

---

# Part 6: Phase 4 Testing - Shortage Queue UI

## Test 4.1: SLA Display

**Purpose**: ตรวจสอบว่า SLA แสดงถูกต้องใน Shortage Queue

### Steps:
1. ไปที่ `/shortage-queue`
2. ตรวจสอบ SLA column

### Expected Result:
```
✅ SLA column exists
✅ Badges with correct colors:
   - 🚨 Red: เลยกำหนด
   - ⚠️ Yellow: วันนี้
   - 📅 Blue: พรุ่งนี้
   - Gray: อีกหลายวัน
```

---

## Test 4.2: SLA Sorting

**Purpose**: ตรวจสอบว่า shortage items เรียงตาม SLA

### Validation:
```
Check table order manually:
- Row 1 should have earliest SLA (most urgent)
- Last row should have latest SLA (least urgent)
```

---

# Part 7: Integration Testing (All Phases)

## Integration Test 1: Complete Workflow

**Scenario**: End-to-end workflow from order import to batch handover

### Steps:

**1. Import Orders**
```
Import 10 orders:
- 5 Shopee orders (SLA: Today, Tomorrow, etc.)
- 3 Lazada orders
- 2 TikTok orders
```

**Validation**:
```sql
SELECT COUNT(*) FROM order_lines WHERE import_date = DATE('now');
-- Should be 10
```

---

**2. Import Stock (Insufficient)**
```
Import stock:
- SKU-A: qty = 5 (need 10)
- SKU-B: qty = 3 (need 7)
```

**Validation**:
```sql
SELECT sku, qty, reserved_qty, (qty - reserved_qty) as available
FROM stocks
WHERE sku IN ('SKU-A', 'SKU-B');
```

---

**3. Create Batch**
```
Create Shopee Batch
```

**Expected**:
- ✅ Orders with SLA เร็วสุดเข้า Batch ก่อน
- ✅ Orders ที่ไม่มีสต็อก → `waiting_stock`
- ✅ Batch SLA = earliest SLA
- ✅ Stock reserved correctly

**Validation**:
```sql
-- Check batch
SELECT
    batch_id,
    sla_date,
    total_orders,
    locked
FROM batches
WHERE batch_date = DATE('now');

-- Check waiting_stock orders
SELECT COUNT(*) FROM order_lines WHERE batch_status = 'waiting_stock';
```

---

**4. Import More Stock**
```
Import additional stock:
- SKU-A: qty = 15
- SKU-B: qty = 10
```

**Expected**:
- ✅ Reallocation message appears
- ✅ `waiting_stock` orders → `pending_batch`

**Validation**:
```sql
SELECT batch_status, COUNT(*)
FROM order_lines
GROUP BY batch_status;
```

---

**5. Create 2nd Batch**
```
Create another Shopee Batch with reallocated orders
```

**Expected**:
- ✅ Reallocated orders enter 2nd batch
- ✅ Stock reserved for 2nd batch
- ✅ No over-reservation

---

**6. Pick Orders**
```
Pick all orders in Batch 1
```

**Expected**:
- ✅ `reserved_qty` released when picked
- ✅ If shortage → appears in Shortage Queue

---

**7. Handover**
```
Handover both batches
```

**Expected**:
- ✅ All `reserved_qty` = 0
- ✅ Stock available for new orders

**Final Validation**:
```sql
-- Check no reservation leaks
SELECT sku, reserved_qty
FROM stocks
WHERE reserved_qty > 0;

-- Should only show active batches (not handover_confirmed)
SELECT
    s.sku,
    s.reserved_qty,
    COUNT(DISTINCT b.batch_id) as active_batches
FROM stocks s
LEFT JOIN order_lines ol ON ol.sku = s.sku AND ol.accepted = 1
LEFT JOIN batches b ON b.batch_id = ol.batch_id AND (b.handover_confirmed IS NULL OR b.handover_confirmed = 0)
WHERE s.reserved_qty > 0
GROUP BY s.sku;
```

---

# Part 8: Critical Validation Queries

## Query 1: Reserved Stock Integrity

```sql
-- Check for anomalies
SELECT
    'Over-Reservation' as issue,
    COUNT(*) as count
FROM stocks
WHERE reserved_qty > qty

UNION ALL

SELECT
    'Negative Available' as issue,
    COUNT(*) as count
FROM stocks
WHERE (qty - reserved_qty) < 0

UNION ALL

SELECT
    'Reservation Leak (Completed Batch)' as issue,
    COUNT(DISTINCT s.sku) as count
FROM stocks s
JOIN order_lines ol ON ol.sku = s.sku
JOIN batches b ON b.batch_id = ol.batch_id
WHERE s.reserved_qty > 0
  AND b.handover_confirmed = 1;
```

### Expected Result:
```
All counts should be 0
```

---

## Query 2: SLA Data Completeness

```sql
-- Check SLA coverage
SELECT
    'Orders with order_time but no SLA' as issue,
    COUNT(*) as count
FROM order_lines
WHERE order_time IS NOT NULL
  AND sla_date IS NULL

UNION ALL

SELECT
    'Batches with orders but no SLA' as issue,
    COUNT(*) as count
FROM batches b
WHERE b.sla_date IS NULL
  AND EXISTS (
      SELECT 1 FROM order_lines ol
      WHERE ol.batch_id = b.batch_id
  );
```

### Expected Result:
```
All counts should be 0 (after running Phase 1 migration)
```

---

## Query 3: Batch Status Consistency

```sql
-- Check batch/order status consistency
SELECT
    b.batch_id,
    b.locked,
    b.handover_confirmed,
    COUNT(ol.id) as total_orders,
    SUM(CASE WHEN ol.batch_status = 'batched' THEN 1 ELSE 0 END) as batched_count,
    SUM(CASE WHEN ol.batch_status != 'batched' THEN 1 ELSE 0 END) as wrong_status_count
FROM batches b
LEFT JOIN order_lines ol ON ol.batch_id = b.batch_id
GROUP BY b.batch_id
HAVING wrong_status_count > 0;
```

### Expected Result:
```
No rows (all orders in batch should have batch_status='batched')
```

---

# Part 9: Performance Testing

## Test 9.1: Large Dataset Performance

### Setup:
```sql
-- Check current data size
SELECT
    (SELECT COUNT(*) FROM order_lines) as orders,
    (SELECT COUNT(*) FROM batches) as batches,
    (SELECT COUNT(*) FROM stocks) as stocks;
```

### Performance Benchmarks:

**Batch Creation**:
```
✅ < 2 seconds for 100 orders
✅ < 5 seconds for 500 orders
⚠️ > 10 seconds for 1000+ orders (consider optimization)
```

**Stock Import with Reallocation**:
```
✅ < 3 seconds for 50 SKUs
✅ < 10 seconds for 200 SKUs
```

**Shortage Queue Load**:
```
✅ < 1 second for < 100 items
✅ < 3 seconds for < 500 items
```

---

# Part 10: Final Checklist

## ✅ All Tests Must Pass

### Phase 0:
- [ ] Reserved stock released on picking complete
- [ ] Reserved stock released on handover
- [ ] No over-reservation
- [ ] No reservation leaks

### Phase 1:
- [ ] SLA fields exist in database
- [ ] SLA calculated correctly
- [ ] All orders have SLA (if order_time exists)

### Phase 2:
- [ ] SLA priority allocation works
- [ ] Batch SLA = earliest order SLA
- [ ] Waiting stock orders marked correctly
- [ ] Preview shows accurate allocation

### Phase 3:
- [ ] Reallocation triggered on stock import
- [ ] waiting_stock → pending_batch transition
- [ ] SLA priority maintained in reallocation
- [ ] Flash messages shown

### Phase 4:
- [ ] SLA column displayed
- [ ] SLA badges with correct colors
- [ ] Shortage queue sorted by SLA
- [ ] Platform column displayed

### Integration:
- [ ] End-to-end workflow works
- [ ] No data inconsistencies
- [ ] Performance acceptable
- [ ] All validation queries pass

---

## 🚨 If Any Test Fails

### 1. Document the Failure
```
Test: [Test Name]
Expected: [Expected Result]
Actual: [Actual Result]
Data: [Relevant IDs, values]
Logs: [Error messages]
```

### 2. Investigation Steps
```
1. Check app logs
2. Run validation queries
3. Check recent changes
4. Review related code
```

### 3. Rollback if Needed
```bash
# Restore backup
cp data.db.backup_YYYYMMDD_HHMMSS data.db

# Re-run migrations
python migrations/run_phase0_migration.py
python migrations/run_phase1_migration.py
```

---

## ✅ Success Criteria

**All phases deployed successfully if**:
1. ✅ All 25+ test cases pass
2. ✅ All validation queries return expected results
3. ✅ No over-reservation
4. ✅ No reservation leaks
5. ✅ SLA data complete and accurate
6. ✅ Performance acceptable
7. ✅ UI displays correctly
8. ✅ Workflow functions end-to-end

**Ready for Production!** 🎉
