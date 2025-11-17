-- Migration: Add shortage_qty field to OrderLine table
-- Date: 2025-11-16
-- Phase: 2.2
-- Description: Add shortage_qty column to track item shortages directly in OrderLine
--
-- Why: Previously shortage_qty was a dynamic attribute (qty - picked_qty), which:
--   - Caused performance issues (calculated every time)
--   - Couldn't be queried efficiently
--   - Made logic inconsistent across the codebase
--
-- Solution: Add shortage_qty as a real database column

-- Add shortage_qty column
ALTER TABLE order_lines ADD COLUMN shortage_qty INTEGER DEFAULT 0;

-- Populate existing data: shortage_qty = max(0, qty - picked_qty)
UPDATE order_lines
SET shortage_qty = CASE
    WHEN (qty - COALESCE(picked_qty, 0)) > 0
    THEN (qty - COALESCE(picked_qty, 0))
    ELSE 0
END
WHERE shortage_qty IS NULL OR shortage_qty = 0;

-- Create index for efficient shortage queries
CREATE INDEX idx_orderline_shortage ON order_lines(shortage_qty)
WHERE shortage_qty > 0;

-- Verify migration
SELECT
    COUNT(*) as total_rows,
    SUM(CASE WHEN shortage_qty > 0 THEN 1 ELSE 0 END) as rows_with_shortage,
    SUM(shortage_qty) as total_shortage_qty
FROM order_lines;
