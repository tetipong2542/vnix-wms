-- ===================================================================
-- Migration: Add Stock Transaction Logging (Banking-style)
-- ===================================================================
-- Purpose: Implement transaction-based inventory tracking
-- Date: 2025-01-20
-- Option: 2 (Balanced - Transaction Log + Reason Code)
-- ===================================================================

-- ===================================================================
-- Part 1: Create stock_transactions table (Banking-style ledger)
-- ===================================================================

CREATE TABLE IF NOT EXISTS stock_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Stock Info
    sku TEXT NOT NULL,

    -- Transaction Details
    transaction_type TEXT NOT NULL, -- 'RECEIVE', 'RESERVE', 'RELEASE', 'PICK', 'DAMAGE', 'ADJUST', 'RETURN'
    quantity INTEGER NOT NULL, -- Signed integer: +10 (เพิ่ม), -2 (ลด)
    balance_after INTEGER NOT NULL, -- ยอดคงเหลือหลัง transaction (snapshot)

    -- Root Cause Analysis
    reason_code TEXT, -- 'IMPORT', 'BATCH_RESERVE', 'HANDOVER_RELEASE', 'FOUND_DAMAGED', 'CANT_FIND', etc.

    -- Reference Link (Audit Trail)
    reference_type TEXT, -- 'import', 'batch', 'order_line', 'shortage', 'adjustment'
    reference_id TEXT, -- batch_id, order_line_id, shortage_id, etc.

    -- Metadata
    created_by TEXT, -- username who triggered this transaction
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT, -- Additional context

    -- Indexes for performance
    FOREIGN KEY (sku) REFERENCES stocks(sku)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_stock_transactions_sku ON stock_transactions(sku);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_type ON stock_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_created_at ON stock_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_stock_transactions_reference ON stock_transactions(reference_type, reference_id);

-- ===================================================================
-- Part 2: Update shortage_queue table with reason codes
-- ===================================================================

-- Add shortage reason and type columns
ALTER TABLE shortage_queue ADD COLUMN shortage_reason TEXT; -- 'CANT_FIND', 'FOUND_DAMAGED', 'MISPLACED', 'BARCODE_MISSING', 'OTHER'
ALTER TABLE shortage_queue ADD COLUMN shortage_type TEXT; -- 'PRE_PICK' (ของไม่มีตั้งแต่ในระบบ), 'POST_PICK' (หาไม่เจอตอนหยิบ)
ALTER TABLE shortage_queue ADD COLUMN notes TEXT; -- Additional details from picker

-- Index for analytics queries
CREATE INDEX IF NOT EXISTS idx_shortage_queue_reason ON shortage_queue(shortage_reason);
CREATE INDEX IF NOT EXISTS idx_shortage_queue_type ON shortage_queue(shortage_type);

-- ===================================================================
-- Part 3: Backfill existing data (optional - for historical data)
-- ===================================================================

-- Mark existing shortages as 'PRE_PICK' (we don't know if they're pre or post)
UPDATE shortage_queue
SET shortage_type = 'PRE_PICK',
    shortage_reason = 'LEGACY_DATA'
WHERE shortage_type IS NULL;

-- ===================================================================
-- Verification Queries
-- ===================================================================

-- Check stock_transactions table structure
SELECT '=== stock_transactions table ===' as info;
PRAGMA table_info(stock_transactions);

SELECT '' as separator;

-- Check shortage_queue updates
SELECT '=== shortage_queue new columns ===' as info;
PRAGMA table_info(shortage_queue);

SELECT '' as separator;

-- Summary
SELECT '=== Migration Summary ===' as info;
SELECT
    'stock_transactions table created' as step,
    COUNT(*) as record_count
FROM stock_transactions
UNION ALL
SELECT
    'shortage_queue columns added',
    COUNT(*)
FROM pragma_table_info('shortage_queue')
WHERE name IN ('shortage_reason', 'shortage_type', 'notes');

-- ===================================================================
-- END OF MIGRATION
-- ===================================================================
