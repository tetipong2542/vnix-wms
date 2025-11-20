-- ===================================================================
-- Phase 1: Add SLA Fields to Database
-- ===================================================================
-- Purpose: เพิ่มฟิลด์ sla_date ใน order_lines และ batches เพื่อรองรับ
--          SLA-based stock allocation และ priority management
-- ===================================================================

-- Step 1: Add sla_date column to order_lines table
ALTER TABLE order_lines ADD COLUMN sla_date DATE;

-- Step 2: Add sla_date column to batches table
ALTER TABLE batches ADD COLUMN sla_date DATE;

-- Step 3: Create indexes for SLA queries (performance optimization)
CREATE INDEX IF NOT EXISTS idx_order_lines_sla_date ON order_lines(sla_date);
CREATE INDEX IF NOT EXISTS idx_batches_sla_date ON batches(sla_date);

-- ===================================================================
-- NOTE: SLA Calculation Logic (for Python migration script)
-- ===================================================================
-- SLA is calculated based on platform and order_time:
--
-- 1. Lazada:
--    - Order before 11:00 → SLA = same day (if business day)
--    - Order after 11:00 → SLA = next business day
--
-- 2. Shopee / TikTok:
--    - Order before 12:00 → SLA = same day (if business day)
--    - Order after 12:00 → SLA = next business day
--
-- 3. Business day rules:
--    - Monday-Friday are business days
--    - Saturday/Sunday are NOT business days
--    - Holidays (TH_HOLIDAYS set) are NOT business days
--
-- 4. For Batches:
--    - batch.sla_date = MIN(order.sla_date) for all orders in batch
--    - Use earliest SLA in batch for priority
--
-- ===================================================================

-- Step 4: Validation Queries
-- ===================================================================

-- Query 1: Count orders without SLA
SELECT COUNT(*) as orders_without_sla
FROM order_lines
WHERE sla_date IS NULL AND order_time IS NOT NULL;

-- Query 2: Count batches without SLA
SELECT COUNT(*) as batches_without_sla
FROM batches
WHERE sla_date IS NULL;

-- Query 3: Show SLA distribution by platform
SELECT
    platform,
    COUNT(*) as total_orders,
    COUNT(sla_date) as with_sla,
    COUNT(*) - COUNT(sla_date) as without_sla
FROM order_lines
GROUP BY platform
ORDER BY platform;

-- Query 4: Show orders with urgent SLA (today or overdue)
SELECT
    order_id,
    sku,
    platform,
    order_time,
    sla_date,
    CASE
        WHEN sla_date < DATE('now') THEN 'OVERDUE'
        WHEN sla_date = DATE('now') THEN 'TODAY'
        WHEN sla_date = DATE('now', '+1 day') THEN 'TOMORROW'
        ELSE 'LATER'
    END as sla_priority
FROM order_lines
WHERE sla_date IS NOT NULL
  AND sla_date <= DATE('now', '+1 day')
ORDER BY sla_date ASC, order_time ASC
LIMIT 20;

-- Query 5: Show batches by SLA priority
SELECT
    batch_id,
    platform,
    sla_date,
    total_orders,
    handover_confirmed,
    CASE
        WHEN sla_date < DATE('now') THEN 'OVERDUE'
        WHEN sla_date = DATE('now') THEN 'TODAY'
        WHEN sla_date = DATE('now', '+1 day') THEN 'TOMORROW'
        ELSE 'LATER'
    END as sla_priority
FROM batches
WHERE sla_date IS NOT NULL
ORDER BY sla_date ASC
LIMIT 20;

-- ===================================================================
-- Rollback Script (ถ้าต้องการย้อนกลับ)
-- ===================================================================
-- CAUTION: This will DELETE all SLA data!
--
-- DROP INDEX IF EXISTS idx_order_lines_sla_date;
-- DROP INDEX IF EXISTS idx_batches_sla_date;
--
-- -- SQLite doesn't support DROP COLUMN directly
-- -- Need to recreate table without sla_date column
-- -- Or set all sla_date to NULL:
-- UPDATE order_lines SET sla_date = NULL;
-- UPDATE batches SET sla_date = NULL;
