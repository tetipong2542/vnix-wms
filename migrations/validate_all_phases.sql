-- ===================================================================
-- Validation Script for All Phases (0-4)
-- ===================================================================
-- Purpose: ตรวจสอบความถูกต้องของการ implement ทุก Phase
-- Usage: sqlite3 data.db < migrations/validate_all_phases.sql
-- ===================================================================

.mode column
.headers on
.width 40 15 15

-- ===================================================================
-- PHASE 0: Reserved Stock Release Validation
-- ===================================================================

SELECT '=== PHASE 0 VALIDATION ===' as check_name;
SELECT '';

-- Check 1: No Over-Reservation
SELECT
    'Over-Reservation Check' as check_name,
    COUNT(*) as count,
    CASE
        WHEN COUNT(*) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL - Fix Required!'
    END as status
FROM stocks
WHERE reserved_qty > qty;

-- Check 2: No Negative Available
SELECT
    'Negative Available Check' as check_name,
    COUNT(*) as count,
    CASE
        WHEN COUNT(*) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL - Fix Required!'
    END as status
FROM stocks
WHERE (qty - reserved_qty) < 0;

-- Check 3: No Reservation Leaks (Completed Batches)
SELECT
    'Reservation Leak Check' as check_name,
    COUNT(DISTINCT s.sku) as count,
    CASE
        WHEN COUNT(DISTINCT s.sku) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL - Reservation not released!'
    END as status
FROM stocks s
JOIN order_lines ol ON ol.sku = s.sku
JOIN batches b ON b.batch_id = ol.batch_id
WHERE s.reserved_qty > 0
  AND b.handover_confirmed = 1;

SELECT '';

-- ===================================================================
-- PHASE 1: SLA Fields Validation
-- ===================================================================

SELECT '=== PHASE 1 VALIDATION ===' as check_name;
SELECT '';

-- Check 4: SLA Column Exists in order_lines
SELECT
    'order_lines.sla_date exists' as check_name,
    COUNT(*) as columns_found,
    CASE
        WHEN COUNT(*) > 0 THEN '✅ PASS'
        ELSE '❌ FAIL - Column not found!'
    END as status
FROM pragma_table_info('order_lines')
WHERE name = 'sla_date';

-- Check 5: SLA Column Exists in batches
SELECT
    'batches.sla_date exists' as check_name,
    COUNT(*) as columns_found,
    CASE
        WHEN COUNT(*) > 0 THEN '✅ PASS'
        ELSE '❌ FAIL - Column not found!'
    END as status
FROM pragma_table_info('batches')
WHERE name = 'sla_date';

-- Check 6: SLA Data Completeness (Orders)
SELECT
    'SLA Data Completeness' as check_name,
    COUNT(*) as missing_sla_count,
    CASE
        WHEN COUNT(*) = 0 THEN '✅ PASS - All orders have SLA'
        WHEN COUNT(*) < 10 THEN '⚠️ WARNING - Some orders missing SLA'
        ELSE '❌ FAIL - Many orders missing SLA'
    END as status
FROM order_lines
WHERE order_time IS NOT NULL
  AND sla_date IS NULL;

SELECT '';

-- ===================================================================
-- PHASE 2: SLA-based Batch Creation Validation
-- ===================================================================

SELECT '=== PHASE 2 VALIDATION ===' as check_name;
SELECT '';

-- Check 7: Batch SLA Matches Earliest Order SLA
SELECT
    'Batch SLA Accuracy' as check_name,
    COUNT(*) as mismatch_count,
    CASE
        WHEN COUNT(*) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL - Batch SLA mismatch!'
    END as status
FROM (
    SELECT
        b.batch_id,
        b.sla_date as batch_sla,
        MIN(ol.sla_date) as earliest_order_sla
    FROM batches b
    JOIN order_lines ol ON ol.batch_id = b.batch_id
    WHERE b.sla_date IS NOT NULL
    GROUP BY b.batch_id
    HAVING b.sla_date != MIN(ol.sla_date)
);

-- Check 8: waiting_stock Status
SELECT
    'waiting_stock Orders' as check_name,
    COUNT(*) as count,
    CASE
        WHEN COUNT(*) >= 0 THEN '✅ INFO - ' || COUNT(*) || ' orders waiting'
        ELSE 'N/A'
    END as status
FROM order_lines
WHERE batch_status = 'waiting_stock';

SELECT '';

-- ===================================================================
-- PHASE 3: Stock Reallocation Validation
-- ===================================================================

SELECT '=== PHASE 3 VALIDATION ===' as check_name;
SELECT '';

-- Check 9: Reallocation Function Exists
-- (Cannot check from SQL, must verify in importers.py manually)
SELECT
    'Reallocation Function' as check_name,
    'N/A' as count,
    '⚠️ MANUAL CHECK - Verify reallocate_waiting_orders() in importers.py' as status;

SELECT '';

-- ===================================================================
-- PHASE 4: Shortage Queue SLA Validation
-- ===================================================================

SELECT '=== PHASE 4 VALIDATION ===' as check_name;
SELECT '';

-- Check 10: Shortage Queue with SLA
SELECT
    'Shortage Queue Items' as check_name,
    COUNT(*) as count,
    CASE
        WHEN COUNT(*) >= 0 THEN '✅ INFO - ' || COUNT(*) || ' shortage items'
        ELSE 'N/A'
    END as status
FROM shortage_queue;

SELECT '';

-- ===================================================================
-- INTEGRATION VALIDATION
-- ===================================================================

SELECT '=== INTEGRATION VALIDATION ===' as check_name;
SELECT '';

-- Check 11: Batch/Order Status Consistency
SELECT
    'Batch/Order Consistency' as check_name,
    COUNT(*) as inconsistent_batches,
    CASE
        WHEN COUNT(*) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL - Inconsistent batch status!'
    END as status
FROM (
    SELECT
        b.batch_id,
        COUNT(ol.id) as total_orders,
        SUM(CASE WHEN ol.batch_status != 'batched' THEN 1 ELSE 0 END) as wrong_status
    FROM batches b
    LEFT JOIN order_lines ol ON ol.batch_id = b.batch_id
    GROUP BY b.batch_id
    HAVING wrong_status > 0
);

-- Check 12: Stock Reservation Accuracy
SELECT
    'Stock Reservation Accuracy' as check_name,
    CASE
        WHEN (
            SELECT COUNT(*) FROM stocks WHERE reserved_qty > qty
        ) = 0 AND (
            SELECT COUNT(*) FROM stocks WHERE (qty - reserved_qty) < 0
        ) = 0 THEN 'verified_qty = ' || (SELECT SUM(reserved_qty) FROM stocks)
        ELSE 'errors_found'
    END as count,
    CASE
        WHEN (
            SELECT COUNT(*) FROM stocks WHERE reserved_qty > qty
        ) = 0 AND (
            SELECT COUNT(*) FROM stocks WHERE (qty - reserved_qty) < 0
        ) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as status;

SELECT '';

-- ===================================================================
-- SUMMARY REPORT
-- ===================================================================

SELECT '=== SUMMARY ===' as check_name;
SELECT '';

-- Overall Statistics
SELECT 'Total Orders' as metric, COUNT(*) as value FROM order_lines
UNION ALL
SELECT 'Orders with SLA', COUNT(*) FROM order_lines WHERE sla_date IS NOT NULL
UNION ALL
SELECT 'Total Batches', COUNT(*) FROM batches
UNION ALL
SELECT 'Batches with SLA', COUNT(*) FROM batches WHERE sla_date IS NOT NULL
UNION ALL
SELECT 'Total Stock Items', COUNT(*) FROM stocks
UNION ALL
SELECT 'Reserved Stock Items', COUNT(*) FROM stocks WHERE reserved_qty > 0
UNION ALL
SELECT 'waiting_stock Orders', COUNT(*) FROM order_lines WHERE batch_status = 'waiting_stock'
UNION ALL
SELECT 'Shortage Queue Items', COUNT(*) FROM shortage_queue
UNION ALL
SELECT 'Completed Batches', COUNT(*) FROM batches WHERE handover_confirmed = 1;

SELECT '';

-- Critical Issues Count
SELECT
    'CRITICAL ISSUES FOUND' as summary,
    (
        (SELECT COUNT(*) FROM stocks WHERE reserved_qty > qty) +
        (SELECT COUNT(*) FROM stocks WHERE (qty - reserved_qty) < 0) +
        (SELECT COUNT(DISTINCT s.sku)
         FROM stocks s
         JOIN order_lines ol ON ol.sku = s.sku
         JOIN batches b ON b.batch_id = ol.batch_id
         WHERE s.reserved_qty > 0 AND b.handover_confirmed = 1)
    ) as total_issues,
    CASE
        WHEN (
            (SELECT COUNT(*) FROM stocks WHERE reserved_qty > qty) +
            (SELECT COUNT(*) FROM stocks WHERE (qty - reserved_qty) < 0) +
            (SELECT COUNT(DISTINCT s.sku)
             FROM stocks s
             JOIN order_lines ol ON ol.sku = s.sku
             JOIN batches b ON b.batch_id = ol.batch_id
             WHERE s.reserved_qty > 0 AND b.handover_confirmed = 1)
        ) = 0 THEN '✅ ALL TESTS PASSED - Ready for Production!'
        ELSE '❌ CRITICAL ISSUES FOUND - Fix Required Before Production!'
    END as status;

-- ===================================================================
-- END OF VALIDATION
-- ===================================================================
