# Requirements Document

## Introduction

ปรับปรุงประสบการณ์การใช้งาน (UX) ของระบบ Batch Management ให้ใช้งานง่าย รวดเร็ว และมีประสิทธิภาพมากขึ้น โดยเน้นการลดขั้นตอนการทำงาน เพิ่มความสะดวกในการค้นหาและจัดการ Batch และแก้ไขปัญหาที่พบในระบบปัจจุบัน

## Glossary

- **Batch Management System**: ระบบจัดการกลุ่มออเดอร์ที่รวมออเดอร์จากแต่ละ Platform (Shopee, Lazada, TikTok) เข้าด้วยกันตาม Run
- **Quick Create**: ฟีเจอร์สร้าง Batch แบบรวดเร็วด้วยคลิกเดียว โดยไม่ต้องผ่านหลายขั้นตอน
- **Pending Orders**: ออเดอร์ที่มีสถานะ "pending_batch" รอการสร้าง Batch
- **Batch ID**: รหัสประจำตัว Batch ในรูปแบบ {Platform}-{Date}-R{Run} เช่น SH-2024-11-13-R1
- **Run Number**: หมายเลขรอบการสร้าง Batch ในแต่ละวัน (R1, R2, R3, ...)
- **Carrier**: บริษัทขนส่ง เช่น SPX, Flash, LEX, J&T
- **Platform**: แพลตฟอร์มอีคอมเมิร์ซ ได้แก่ Shopee, Lazada, TikTok

## Requirements

### Requirement 1: Quick Create API Implementation

**User Story:** ในฐานะผู้ใช้งาน ฉันต้องการสร้าง Batch แบบรวดเร็วด้วยคลิกเดียว เพื่อประหยัดเวลาและลดขั้นตอนการทำงาน

#### Acceptance Criteria

1. WHEN ผู้ใช้คลิกปุ่ม "⚡ สร้างเร็ว" สำหรับ Platform ใดๆ, THE Batch Management System SHALL แสดง Modal พร้อมข้อมูลตัวอย่าง Batch ที่จะสร้าง
2. THE Batch Management System SHALL จัดเตรียม API endpoint `/batch/next-run/<platform>` ที่คืนค่า Batch ID ถัดไป, Run number ถัดไป, และสรุปออเดอร์ที่รอสร้าง
3. THE Batch Management System SHALL จัดเตรียม API endpoint `/batch/quick-create/<platform>` ที่สร้าง Batch ด้วย Run number ถัดไปโดยอัตโนมัติ
4. WHEN ผู้ใช้ยืนยันการสร้าง Batch ใน Quick Create Modal, THE Batch Management System SHALL สร้าง Batch และนำผู้ใช้ไปยังหน้ารายละเอียด Batch ที่สร้างขึ้น
5. IF ไม่มีออเดอร์รอสร้าง Batch สำหรับ Platform ที่เลือก, THEN THE Batch Management System SHALL แสดงข้อความแจ้งเตือนและปิดการใช้งานปุ่ม "⚡ สร้างเร็ว"

### Requirement 2: Batch List Filtering and Search

**User Story:** ในฐานะผู้ใช้งาน ฉันต้องการค้นหาและกรอง Batch ได้อย่างรวดเร็ว เพื่อหา Batch ที่ต้องการได้ง่ายขึ้น

#### Acceptance Criteria

1. THE Batch Management System SHALL จัดเตรียมช่องค้นหา (Search box) ที่สามารถค้นหา Batch ID ได้
2. THE Batch Management System SHALL จัดเตรียม Filter dropdown สำหรับกรองตาม Platform (All, Shopee, Lazada, TikTok)
3. THE Batch Management System SHALL จัดเตรียม Filter dropdown สำหรับกรองตามสถานะ (All, Locked, Unlocked)
4. THE Batch Management System SHALL จัดเตรียม Date range picker สำหรับกรองตามช่วงวันที่สร้าง Batch
5. WHEN ผู้ใช้ใช้ Filter หรือ Search, THE Batch Management System SHALL อัปเดตตาราง Batch แบบ real-time โดยไม่ต้อง reload หน้า

### Requirement 3: Enhanced Batch Status Display

**User Story:** ในฐานะผู้ใช้งาน ฉันต้องการเห็นสถานะของ Batch อย่างชัดเจน เพื่อเข้าใจสถานะการทำงานได้ทันที

#### Acceptance Criteria

1. THE Batch Management System SHALL แสดง Badge สีสันสดใสสำหรับสถานะ Locked (สีเขียว) และ Unlocked (สีเหลือง)
2. THE Batch Management System SHALL แสดงจำนวนออเดอร์ทั้งหมดใน Batch ด้วยตัวเลขขนาดใหญ่และเด่นชัด
3. THE Batch Management System SHALL แสดงสรุปจำนวนออเดอร์แยกตาม Carrier ในรูปแบบ Badge สีต่างกันสำหรับแต่ละ Carrier
4. THE Batch Management System SHALL แสดงข้อมูลผู้สร้าง Batch และเวลาที่สร้างอย่างชัดเจน
5. THE Batch Management System SHALL จัดเรียง Batch ตามวันที่สร้างล่าสุดก่อน (Descending order)

### Requirement 4: Improved Batch Creation Flow

**User Story:** ในฐานะผู้ใช้งาน ฉันต้องการเห็นข้อมูลตัวอย่างที่ชัดเจนก่อนสร้าง Batch เพื่อตัดสินใจได้ถูกต้อง

#### Acceptance Criteria

1. WHEN ผู้ใช้เลือก Platform ในหน้าสร้าง Batch, THE Batch Management System SHALL แสดงข้อมูลตัวอย่างแบบละเอียด รวมถึงจำนวนออเดอร์, สรุปตาม Carrier, และสรุปตามร้าน
2. THE Batch Management System SHALL แสดง Batch ID ที่จะถูกสร้างแบบ real-time เมื่อผู้ใช้เลือก Run number
3. THE Batch Management System SHALL แสดงคำเตือนที่ชัดเจนว่า Batch จะถูก Lock ทันทีหลังสร้าง
4. THE Batch Management System SHALL จัดเตรียมปุ่ม "กลับ" ที่ชัดเจนในทุกขั้นตอนของการสร้าง Batch
5. WHEN ผู้ใช้ยืนยันสร้าง Batch, THE Batch Management System SHALL แสดง Loading indicator และข้อความยืนยันเมื่อสร้างสำเร็จ

### Requirement 5: Batch Detail Enhancement

**User Story:** ในฐานะผู้ใช้งาน ฉันต้องการเห็นรายละเอียดของ Batch อย่างครบถ้วนและเข้าใจง่าย เพื่อตรวจสอบข้อมูลได้อย่างรวดเร็ว

#### Acceptance Criteria

1. THE Batch Management System SHALL แสดงสรุปข้อมูล Batch ในรูปแบบ Card พร้อมไอคอนและสีสันที่เหมาะสม
2. THE Batch Management System SHALL แสดงสรุปจำนวนออเดอร์แยกตาม Carrier ในรูปแบบ Visual (Card หรือ Chart)
3. THE Batch Management System SHALL แสดงสรุปจำนวนออเดอร์แยกตามร้านในรูปแบบ Visual (Card หรือ Chart)
4. THE Batch Management System SHALL จัดเตรียมตารางรายการออเดอร์ที่มี DataTable พร้อม Sorting, Pagination, และ Search
5. THE Batch Management System SHALL จัดเตรียมปุ่ม Export ข้อมูล Batch เป็น Excel หรือ JSON

### Requirement 6: Responsive Design and Mobile Support

**User Story:** ในฐานะผู้ใช้งาน ฉันต้องการใช้งานระบบ Batch Management บนอุปกรณ์มือถือได้สะดวก เพื่อสามารถทำงานได้ทุกที่ทุกเวลา

#### Acceptance Criteria

1. THE Batch Management System SHALL แสดงผลได้ถูกต้องบนหน้าจอขนาดเล็ก (Mobile, Tablet)
2. THE Batch Management System SHALL ปรับขนาดตาราง Batch ให้เหมาะสมกับหน้าจอขนาดต่างๆ
3. THE Batch Management System SHALL จัดเตรียมปุ่มและ UI elements ที่มีขนาดเหมาะสมสำหรับการแตะบนหน้าจอสัมผัส
4. THE Batch Management System SHALL แสดง Modal และ Popup ที่ปรับขนาดตามหน้าจอ
5. THE Batch Management System SHALL ใช้ Bootstrap responsive classes อย่างถูกต้องในทุก component

### Requirement 7: Error Handling and User Feedback

**User Story:** ในฐานะผู้ใช้งาน ฉันต้องการได้รับข้อความแจ้งเตือนที่ชัดเจนเมื่อเกิดข้อผิดพลาด เพื่อเข้าใจปัญหาและแก้ไขได้ทันที

#### Acceptance Criteria

1. WHEN เกิดข้อผิดพลาดในการสร้าง Batch, THE Batch Management System SHALL แสดงข้อความแจ้งเตือนที่อธิบายสาเหตุอย่างชัดเจน
2. WHEN ผู้ใช้พยายามสร้าง Batch ที่มี Batch ID ซ้ำ, THE Batch Management System SHALL แสดงข้อความแจ้งเตือนและแนะนำให้เลือก Run number อื่น
3. WHEN ไม่มีออเดอร์รอสร้าง Batch, THE Batch Management System SHALL แสดงข้อความแจ้งเตือนและปิดการใช้งานปุ่มสร้าง Batch
4. THE Batch Management System SHALL แสดง Loading indicator ในขณะที่กำลังโหลดข้อมูลหรือประมวลผล
5. THE Batch Management System SHALL แสดงข้อความยืนยันเมื่อดำเนินการสำเร็จ (Success message)

### Requirement 8: Performance Optimization

**User Story:** ในฐานะผู้ใช้งาน ฉันต้องการให้ระบบ Batch Management ทำงานได้รวดเร็ว เพื่อประหยัดเวลาในการทำงาน

#### Acceptance Criteria

1. THE Batch Management System SHALL โหลดหน้า Batch List ภายใน 2 วินาที
2. THE Batch Management System SHALL โหลดข้อมูลตัวอย่าง Batch ใน Quick Create Modal ภายใน 1 วินาที
3. THE Batch Management System SHALL สร้าง Batch ภายใน 3 วินาที
4. THE Batch Management System SHALL ใช้ AJAX สำหรับการโหลดข้อมูลแบบ asynchronous เพื่อไม่ให้หน้าเว็บค้าง
5. THE Batch Management System SHALL ใช้ Database indexing สำหรับคอลัมน์ที่ใช้ในการค้นหาและกรอง
