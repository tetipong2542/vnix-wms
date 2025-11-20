-- Migration: Add notes column to shortage_queue table
-- Date: 2025-01-20
-- Description: Add notes column for storing picker's notes when marking shortage

-- Add notes column
ALTER TABLE shortage_queue
ADD COLUMN notes TEXT;

-- Verify column added
SELECT name FROM pragma_table_info('shortage_queue') WHERE name = 'notes';
