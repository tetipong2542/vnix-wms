-- Migration: Add Handover Code System fields to Batch table
-- Date: 2025-11-16
-- Description: Add fields for Batch Handover Code workflow (BH-YYYYMMDD-XXX format)

-- SQLite doesn't support ALTER TABLE ADD COLUMN with UNIQUE constraint directly
-- So we add column first, then create unique index

-- Add handover code generation fields
ALTER TABLE batches ADD COLUMN handover_code VARCHAR(20);
ALTER TABLE batches ADD COLUMN handover_code_generated_at DATETIME;
ALTER TABLE batches ADD COLUMN handover_code_generated_by_user_id INTEGER;
ALTER TABLE batches ADD COLUMN handover_code_generated_by_username VARCHAR(64);

-- Add handover confirmation fields
ALTER TABLE batches ADD COLUMN handover_confirmed BOOLEAN DEFAULT 0;
ALTER TABLE batches ADD COLUMN handover_confirmed_at DATETIME;
ALTER TABLE batches ADD COLUMN handover_confirmed_by_user_id INTEGER;
ALTER TABLE batches ADD COLUMN handover_confirmed_by_username VARCHAR(64);
ALTER TABLE batches ADD COLUMN handover_notes TEXT;

-- Create UNIQUE index for handover_code (enforces uniqueness + fast lookup)
CREATE UNIQUE INDEX idx_batch_handover_code ON batches(handover_code) WHERE handover_code IS NOT NULL;

-- Verify migration
SELECT COUNT(*) as migrated FROM pragma_table_info('batches') WHERE name='handover_code';
