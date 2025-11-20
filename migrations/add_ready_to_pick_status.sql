-- Migration: Add 'ready_to_pick' status support for Shortage Queue
-- Date: 2025-01-19
-- Description:
--   เพิ่มสถานะ 'ready_to_pick' เพื่อให้ระบบแจ้ง Picker ว่าสต็อกพร้อมแล้ว
--   Status Lifecycle: pending → waiting_stock → ready_to_pick → resolved

-- ไม่ต้องเปลี่ยน Schema (ใช้ TEXT column เดิม)
-- แค่เพิ่ม Comment เพื่อบันทึก Status ใหม่

-- Shortage Queue Status Values:
-- - pending: รอ Admin จัดการ
-- - waiting_stock: รอสต็อกเข้า
-- - ready_to_pick: สต็อกพร้อมแล้ว ให้ Picker หยิบได้ (NEW!)
-- - replaced: แทน SKU แล้ว
-- - cancelled: ยกเลิกแล้ว
-- - resolved: จัดการเรียบร้อย

-- ตรวจสอบว่ามี shortage records ที่ status = 'waiting_stock' และสต็อกมีแล้ว
-- UPDATE shortage_queue
-- SET status = 'ready_to_pick'
-- WHERE status = 'waiting_stock'
-- AND sku IN (SELECT sku FROM stock WHERE qty > 0);

-- Run this manually only if needed (ไม่ใช่ Auto-migration)
