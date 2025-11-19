-- Migration: Add reserved_qty column to stocks table
-- Created: 2025-11-19
-- Purpose: Support stock reservation system for batch creation

-- Add reserved_qty column (default 0)
ALTER TABLE stocks ADD COLUMN reserved_qty INTEGER DEFAULT 0;

-- Update existing records to have reserved_qty = 0
UPDATE stocks SET reserved_qty = 0 WHERE reserved_qty IS NULL;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_stocks_reserved ON stocks(reserved_qty);

-- Verify migration
SELECT 'Migration completed. Checking stocks table...' as status;
PRAGMA table_info(stocks);
