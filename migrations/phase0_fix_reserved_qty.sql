-- ===================================================================
-- Phase 0: Fix Reserved Stock Release Bug
-- ===================================================================
-- Problem: reserved_qty ไม่ถูก release เมื่อ Batch เสร็จสิ้น
-- Solution: Recalculate reserved_qty สำหรับทุก SKU ตามสถานะ Batch จริง
-- ===================================================================

-- Step 1: Reset reserved_qty ให้เป็น 0 ทั้งหมด (เริ่มต้นใหม่)
UPDATE stocks SET reserved_qty = 0;

-- Step 2: คำนวณ reserved_qty ใหม่ สำหรับ Batch ที่ยังไม่ handover_confirmed
--         (เฉพาะ Batch ที่ยังทำงานอยู่เท่านั้น)
--
-- Logic:
--   reserved_qty = SUM(order_lines.qty)
--   WHERE:
--     - order_lines.accepted = TRUE (รับงานแล้ว)
--     - batch.handover_confirmed = FALSE หรือ NULL (ยังไม่ส่งมอบ)
--     - order_lines.dispatch_status != 'dispatched' (ยังไม่ส่งของ)
--
UPDATE stocks
SET reserved_qty = (
    SELECT COALESCE(SUM(ol.qty), 0)
    FROM order_lines ol
    LEFT JOIN batches b ON ol.batch_id = b.batch_id
    WHERE
        ol.sku = stocks.sku
        AND ol.accepted = 1
        AND (b.handover_confirmed IS NULL OR b.handover_confirmed = 0)
        AND ol.dispatch_status != 'dispatched'
);

-- Step 3: ตรวจสอบผลลัพธ์
SELECT
    s.sku,
    s.qty AS total_stock,
    s.reserved_qty,
    (s.qty - s.reserved_qty) AS available,
    -- แสดงจำนวน Active Batches ที่จอง SKU นี้
    (SELECT COUNT(DISTINCT ol.batch_id)
     FROM order_lines ol
     LEFT JOIN batches b ON ol.batch_id = b.batch_id
     WHERE ol.sku = s.sku
       AND ol.accepted = 1
       AND (b.handover_confirmed IS NULL OR b.handover_confirmed = 0)
    ) AS active_batches,
    -- แสดงจำนวนที่หยิบแล้ว
    (SELECT COALESCE(SUM(ol.picked_qty), 0)
     FROM order_lines ol
     WHERE ol.sku = s.sku
       AND ol.accepted = 1
    ) AS total_picked
FROM stocks s
WHERE s.reserved_qty > 0 OR s.qty > 0
ORDER BY s.reserved_qty DESC, s.sku ASC;

-- ===================================================================
-- Validation Queries (ตรวจสอบว่า reserved_qty ถูกต้อง)
-- ===================================================================

-- Query 1: SKU ที่ reserved_qty > stock_qty (ผิดปกติ - ไม่ควรเกิด)
SELECT
    sku,
    qty AS stock_qty,
    reserved_qty,
    (reserved_qty - qty) AS over_reserved
FROM stocks
WHERE reserved_qty > qty
ORDER BY over_reserved DESC;

-- Query 2: Batch ที่ handover แล้วแต่ยังมี reserved_qty (ผิดปกติ)
SELECT
    b.batch_id,
    b.handover_confirmed,
    b.handover_confirmed_at,
    s.sku,
    s.reserved_qty,
    SUM(ol.qty) AS total_qty_in_batch
FROM batches b
JOIN order_lines ol ON ol.batch_id = b.batch_id
JOIN stocks s ON s.sku = ol.sku
WHERE
    b.handover_confirmed = 1
    AND s.reserved_qty > 0
GROUP BY b.batch_id, s.sku
ORDER BY b.handover_confirmed_at DESC;

-- Query 3: Summary Report
SELECT
    'Total SKUs' AS metric,
    COUNT(*) AS value
FROM stocks
WHERE qty > 0 OR reserved_qty > 0

UNION ALL

SELECT
    'SKUs with Reservation' AS metric,
    COUNT(*) AS value
FROM stocks
WHERE reserved_qty > 0

UNION ALL

SELECT
    'Total Reserved Qty' AS metric,
    SUM(reserved_qty) AS value
FROM stocks

UNION ALL

SELECT
    'Active Batches (Not Handed Over)' AS metric,
    COUNT(*) AS value
FROM batches
WHERE handover_confirmed IS NULL OR handover_confirmed = 0

UNION ALL

SELECT
    'Completed Batches (Handed Over)' AS metric,
    COUNT(*) AS value
FROM batches
WHERE handover_confirmed = 1;
