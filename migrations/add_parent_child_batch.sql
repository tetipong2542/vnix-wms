-- Migration: Parent-Child Batch System
-- Date: 2025-11-17
-- Description: เพิ่มฟีเจอร์ Parent-Child Batch เพื่อจัดการ Shortage โดยไม่ Block งาน

-- ✅ Step 1: เพิ่ม columns ใหม่
-- Note: SQLite จะ validate Foreign Key เมื่อมีการ INSERT/UPDATE เท่านั้น
-- SQLAlchemy จะจัดการ Foreign Key Constraint ให้อัตโนมัติ
ALTER TABLE batches ADD COLUMN parent_batch_id VARCHAR(64);
ALTER TABLE batches ADD COLUMN sub_batch_number INTEGER DEFAULT 0;
ALTER TABLE batches ADD COLUMN batch_type VARCHAR(20) DEFAULT 'original';
ALTER TABLE batches ADD COLUMN shortage_reason TEXT;

-- ✅ Step 2: เพิ่ม Indexes เพื่อความเร็ว
CREATE INDEX idx_parent_batch ON batches(parent_batch_id);
CREATE INDEX idx_batch_type ON batches(batch_type);

-- ✅ Step 4: อัปเดต Batch ที่มีอยู่ให้เป็น 'original'
UPDATE batches
SET batch_type = 'original', sub_batch_number = 0
WHERE batch_type IS NULL OR batch_type = '';

-- ✅ Step 5: ตรวจสอบผลลัพธ์
-- SELECT batch_id, parent_batch_id, sub_batch_number, batch_type
-- FROM batches
-- ORDER BY batch_id;
