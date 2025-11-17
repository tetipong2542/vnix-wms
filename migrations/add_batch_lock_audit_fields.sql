-- Migration: Add Batch Lock Audit Fields
-- Date: 2025-11-16
-- Phase: 2.4
-- Description: Add audit fields to track who locked batch and when

-- Add batch lock audit fields
ALTER TABLE batches ADD COLUMN locked_at DATETIME;
ALTER TABLE batches ADD COLUMN locked_by_user_id INTEGER;
ALTER TABLE batches ADD COLUMN locked_by_username VARCHAR(64);

-- Verify migration
SELECT COUNT(*) as migrated FROM pragma_table_info('batches') WHERE name='locked_at';
