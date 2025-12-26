# PRD: VNIX Order Management System - Frontend
## Product Requirements Document - Business & Functional Requirements

**Version:** 5.52
**Document Type:** Frontend Specifications (Business & Functional Requirements)
**Last Updated:** 2025-12-26
**Status:** Production

---

## 1. EXECUTIVE SUMMARY

### 1.1 Product Overview
VNIX Order Management System เป็นระบบจัดการคำสั่งซื้อและคลังสินค้าสำหรับธุรกิจ E-commerce ที่ขายสินค้าผ่านหลายแพลตฟอร์ม (Multi-Platform) ได้แก่ Shopee, TikTok, Lazada และแพลตฟอร์มอื่นๆ ระบบช่วยในการจัดสรรสต็อก (Stock Allocation), ติดตาม SLA ตามวันทำการ, จัดการการจัดส่ง (Dispatch) และรายงานต่างๆ

### 1.2 Target Users
- **พนักงานคลังสินค้า (Warehouse Staff):** ผู้รับคำสั่งซื้อ, แพ็คสินค้า, สแกนบาร์โค้ด
- **หัวหน้าคลังสินค้า (Warehouse Manager):** ดูภาพรวม, จัดการรอบจัดส่ง, พิมพ์เอกสาร
- **ทีมจัดซื้อ (Purchasing Team):** ดูรายงานสินค้าขาดสต็อก/สต็อกต่ำ
- **ผู้ดูแลระบบ (Admin):** จัดการผู้ใช้, ร้านค้า, นำเข้าข้อมูล
- **ผู้บริหาร (Management):** ดูรายงาน KPI และภาพรวมธุรกิจ

### 1.3 Business Objectives
1. **ลดเวลาการประมวลผลคำสั่งซื้อ:** จาก Manual → Automated Allocation
2. **ป้องกัน Over-selling:** Real-time Stock Allocation Engine
3. **เพิ่มประสิทธิภาพการ Pick & Pack:** Grouped Picking List
4. **ตรวจสอบ SLA แบบ Real-time:** Business-day Aware SLA Calculation
5. **รองรับการขยายธุรกิจ:** Multi-platform, Multi-shop Support
6. **ลดข้อผิดพลาด:** Barcode Scanning Verification

---

## 2. USER ROLES & PERSONAS

### 2.1 Role: Admin
**Access Level:** Full System Access
**Primary Goals:**
- จัดการผู้ใช้และสิทธิ์การเข้าถึง
- จัดการข้อมูลร้านค้า (Shops)
- นำเข้าข้อมูลหลัก (Products, Stock, Sales, Orders)
- ตรวจสอบ System Health

**Typical Tasks:**
- เพิ่ม/ลบ/แก้ไขผู้ใช้
- เพิ่ม/ลบ/แก้ไขร้านค้า
- Upload Excel/CSV/Google Sheets
- ดู Import History Dashboard
- ตั้งค่า Google Sheet Auto-import

### 2.2 Role: User (Warehouse Staff)
**Access Level:** Order Operations Only
**Primary Goals:**
- รับคำสั่งซื้อ (Accept Orders)
- พิมพ์เอกสารคลังสินค้า (Warehouse Job Sheet)
- พิมพ์ใบเบิกสินค้า (Picking List)
- สแกนบาร์โค้ดเพื่อยืนยัน

**Typical Tasks:**
- กรองคำสั่งซื้อตามแพลตฟอร์ม/ร้านค้า/โลจิสติกส์
- Bulk Accept Orders
- พิมพ์ Warehouse Job Sheet พร้อมระบุรอบจัดส่ง
- สแกนบาร์โค้ด Order ID
- ดู Picking List แบบ Group by SKU
- Bulk Cancel Orders (ถ้าจำเป็น)

### 2.3 Role: Purchasing Team
**Access Level:** Read-only + Report Access
**Primary Goals:**
- ตรวจสอบสินค้าที่มีสต็อกต่ำ/หมด
- วางแผนการสั่งซื้อสินค้าเพิ่ม
- Export รายงานเพื่อส่งให้ Supplier

**Typical Tasks:**
- ดู Low Stock Report
- ดู No Stock Report
- ดู Not Enough Stock Report
- Export รายงานเป็น Excel
- พิมพ์รายการสินค้าที่ต้องสั่งซื้อ

### 2.4 Role: Management
**Access Level:** Dashboard + Reports (Read-only)
**Primary Goals:**
- ติดตาม KPI ประจำวัน
- ตรวจสอบประสิทธิภาพการดำเนินงาน
- วิเคราะห์แนวโน้มการขาย

**Typical Tasks:**
- ดู Dashboard KPI Cards
- กรองข้อมูลตามวันที่/แพลตฟอร์ม
- Export Dashboard Data
- ดู Order Status Distribution

---

## 3. USER STORIES

### 3.1 Import & Data Management

#### US-001: นำเข้าข้อมูลสินค้า (Product Master)
**As a** Admin
**I want to** นำเข้าข้อมูลสินค้าจาก Excel
**So that** ระบบมีข้อมูล SKU, Brand, Model ที่ถูกต้อง

**Acceptance Criteria:**
- รองรับไฟล์ .xlsx, .xls, .csv
- ตรวจจับคอลัมน์อัตโนมัติ (SKU, Brand, Model)
- แสดงจำนวน Products ที่ Import สำเร็จ
- แสดง Error หากมี Duplicate SKU
- แสดง Flash Message ผลลัพธ์

#### US-002: นำเข้าข้อมูลสต็อก (Stock Import)
**As a** Admin
**I want to** นำเข้าข้อมูลสต็อกจาก Excel หรือ Google Sheets
**So that** ระบบมีข้อมูลสต็อกที่เป็นปัจจุบัน

**Acceptance Criteria:**
- รองรับ Excel (.xlsx, .xls, .csv) และ Google Sheets
- โหมด Full Sync: SKU ที่ไม่มีในไฟล์ = สต็อก 0
- ตรวจจับคอลัมน์ SKU, Qty อัตโนมัติ
- อัพเดท updated_at timestamp
- แสดงจำนวนแถวที่ Import สำเร็จ

#### US-003: นำเข้าคำสั่งซื้อ (Order Import)
**As a** Admin
**I want to** นำเข้าคำสั่งซื้อจาก Excel/CSV/Google Sheets
**So that** ระบบมีข้อมูลคำสั่งซื้อจากทุกแพลตฟอร์ม

**Acceptance Criteria:**
- รองรับหลายแพลตฟอร์ม (Shopee, TikTok, Lazada, Other)
- ตรวจจับคอลัมน์อัตโนมัติ (Platform, Shop, Order ID, SKU, Qty, Order Time, Logistic)
- INSERT-ONLY mode: ไม่อัพเดทคำสั่งซื้อเดิม
- Duplicate Detection: ตรวจจับคำสั่งซื้อซ้ำในวันเดียวกัน
- แสดง Import Summary (Success, Duplicate, Error)
- บันทึก Import Log พร้อม Timestamp

#### US-004: ดู Import History Dashboard
**As a** Admin
**I want to** ดูประวัติการ Import ทั้งหมด
**So that** ติดตามว่าข้อมูลถูกนำเข้าเมื่อไหร่โดยใคร

**Acceptance Criteria:**
- แสดง Import Cards แบบ Reverse Chronological Order
- แสดง Import Type (Products/Stock/Sales/Orders/Cancel/Issued)
- แสดงจำนวน Success, Duplicate, Error
- แสดง Timestamp และ Username
- แสดงชื่อไฟล์ที่ Upload

### 3.2 Dashboard & Order Management

#### US-005: ดู Dashboard Overview
**As a** Warehouse Staff/Management
**I want to** ดู Dashboard พร้อม KPI Cards
**So that** เห็นภาพรวมคำสั่งซื้อและสถานะสต็อก

**Acceptance Criteria:**
- แสดง KPI Cards:
  - ทั้งหมด (Total Orders)
  - พร้อมรับ (READY_ACCEPT)
  - สต็อกต่ำ (LOW_STOCK)
  - ขาดสต็อก (SHORTAGE)
  - ไม่พอ (NOT_ENOUGH)
  - รับแล้ว (ACCEPTED)
  - จัดส่งแล้ว (PACKED)
- แสดงจำนวนแต่ละสถานะพร้อมสี Gradient
- แสดงตาราง Orders พร้อม DataTables
- เรียงตาม Platform Priority → Order Time (FIFO)

#### US-006: กรองคำสั่งซื้อตามเงื่อนไข
**As a** Warehouse Staff
**I want to** กรองคำสั่งซื้อตาม Platform, Shop, Logistic, Status, Date Range
**So that** มองเห็นเฉพาะคำสั่งซื้อที่ต้องการ

**Acceptance Criteria:**
- ตัวกรอง Platform (Multi-select dropdown)
- ตัวกรอง Shop (Multi-select dropdown)
- ตัวกรอง Logistic Type (Multi-select dropdown)
- ตัวกรอง Status (Multi-select dropdown)
- ตัวกรอง Date Range (Date picker - From/To)
- Filter Persistence: บันทึกการตั้งค่าใน Browser
- แสดงจำนวนผลลัพธ์หลังกรอง
- ปุ่ม Clear All Filters

#### US-007: รับคำสั่งซื้อทีละรายการ (Single Accept)
**As a** Warehouse Staff
**I want to** รับคำสั่งซื้อทีละรายการ
**So that** ยืนยันว่าสินค้าพร้อมจัดเตรียม

**Acceptance Criteria:**
- ปุ่ม Accept สำหรับคำสั่งซื้อที่ Status = READY_ACCEPT หรือ LOW_STOCK
- คลิกแล้วเปลี่ยนเป็น ACCEPTED
- บันทึก accepted_at timestamp และ accepted_by username
- แสดง Flash Message "รับออเดอร์สำเร็จ"
- Refresh Dashboard KPI Cards

#### US-008: รับคำสั่งซื้อแบบ Bulk (Bulk Accept)
**As a** Warehouse Staff
**I want to** รับคำสั่งซื้อหลายรายการพร้อมกัน
**So that** ประหยัดเวลา

**Acceptance Criteria:**
- Checkbox ในตาราง Orders
- ปุ่ม "รับออเดอร์ที่เลือก (Bulk Accept)"
- รับเฉพาะที่ Checkbox ติ๊กและ Status = READY_ACCEPT หรือ LOW_STOCK
- แสดงจำนวนรายการที่รับสำเร็จ
- บันทึก accepted_at และ accepted_by สำหรับทุกรายการ
- Refresh Dashboard

#### US-009: ยกเลิกคำสั่งซื้อแบบ Bulk (Bulk Cancel)
**As a** Warehouse Staff
**I want to** ยกเลิกคำสั่งซื้อหลายรายการพร้อมกัน
**So that** จัดการคำสั่งซื้อที่ยกเลิกได้รวดเร็ว

**Acceptance Criteria:**
- Checkbox ในตาราง Orders
- ปุ่ม "ยกเลิกที่เลือก (Bulk Cancel)"
- ยกเลิกเฉพาะที่ Checkbox ติ๊ก
- เปลี่ยน Status เป็น CANCELLED
- แสดงแถวที่ยกเลิกด้วยสี (เช่น strikethrough)
- แสดงจำนวนรายการที่ยกเลิกสำเร็จ

#### US-010: ลบคำสั่งซื้อแบบ Soft Delete (Recycle Bin)
**As a** Admin
**I want to** ลบคำสั่งซื้อไปยัง Recycle Bin
**So that** สามารถกู้คืนได้หากลบผิด

**Acceptance Criteria:**
- Checkbox ในตาราง Orders
- ปุ่ม "ลบที่เลือก (Delete Selected)"
- ย้ายข้อมูลไปยังตาราง DeletedOrder
- ลบจากตาราง OrderLine
- แสดงจำนวนรายการที่ลบ
- หน้า Deleted Orders สำหรับดูรายการที่ลบ

#### US-011: อัพเดทรอบจัดส่ง (Dispatch Round)
**As a** Warehouse Manager
**I want to** ระบุรอบจัดส่งให้กับคำสั่งซื้อที่เลือก
**So that** แยกคำสั่งซื้อเป็นกลุ่มตามรอบการจัดส่ง

**Acceptance Criteria:**
- Checkbox ในตาราง Orders
- Input Field: "ระบุรอบจัดส่ง"
- ปุ่ม "อัพเดทรอบจัดส่ง"
- อัพเดท dispatch_round สำหรับรายการที่เลือก
- แสดง Flash Message จำนวนรายการที่อัพเดท

#### US-012: สแกนบาร์โค้ดยืนยันคำสั่งซื้อ (Barcode Scanning)
**As a** Warehouse Staff
**I want to** สแกนบาร์โค้ด Order ID
**So that** ยืนยันว่าได้แพ็คสินค้าแล้ว

**Acceptance Criteria:**
- ปุ่ม "สแกนบาร์โค้ด"
- แสดง Modal พร้อม Input Field
- ใส่ Order ID ลงใน Input (จาก Barcode Scanner)
- กด Enter หรือ Submit
- บันทึก scanned_at timestamp และ scanned_by username
- แสดง Checkbox ✓ ในคอลัมน์ "สแกนแล้ว"
- แสดง Toast Message "สแกนสำเร็จ"

#### US-013: รีเซ็ตสถานะการสแกน (Reset Scans)
**As a** Warehouse Manager
**I want to** รีเซ็ตสถานะการสแกนหลายรายการพร้อมกัน
**So that** สามารถสแกนใหม่ได้ (กรณีสแกนผิด)

**Acceptance Criteria:**
- Checkbox ในตาราง Orders
- ปุ่ม "รีเซ็ตการสแกน"
- รีเซ็ต scanned_at และ scanned_by เป็น NULL
- แสดงจำนวนรายการที่รีเซ็ตสำเร็จ

### 3.3 Reports & Printing

#### US-014: พิมพ์เอกสารคลังสินค้า (Warehouse Job Sheet)
**As a** Warehouse Staff
**I want to** พิมพ์เอกสารคลังสินค้าสำหรับคำสั่งซื้อที่รับแล้ว
**So that** นำไปใช้ในการแพ็คสินค้า

**Acceptance Criteria:**
- เข้าหน้า /report/warehouse
- กรองตาม Platform, Shop, Logistic, Dispatch Round
- แสดงตารางคำสั่งซื้อที่ Status = ACCEPTED
- ปุ่ม "พิมพ์เอกสาร"
- ระบบ:
  - บันทึก printed_warehouse = True
  - บันทึก printed_warehouse_at timestamp
  - สร้าง IssuedOrder record (source: 'print')
  - เปลี่ยน Status เป็น PACKED
- Export เป็น Excel พร้อมหัวข้อภาษาไทย
- แสดงจำนวนรายการที่พิมพ์

#### US-015: พิมพ์ใบเบิกสินค้า (Picking List)
**As a** Warehouse Staff
**I want to** พิมพ์ใบเบิกสินค้าแบบจัดกลุ่มตาม SKU
**So that** เบิกสินค้าได้อย่างมีประสิทธิภาพ

**Acceptance Criteria:**
- เข้าหน้า /report/picking
- กรองตาม Platform, Shop, Logistic
- แสดงตารางแบบ Group by SKU
- แสดง Total Qty ที่ต้องเบิกสำหรับแต่ละ SKU
- แสดงรายชื่อ Order IDs ที่เกี่ยวข้อง
- ปุ่ม "พิมพ์ใบเบิก"
- ระบบ:
  - บันทึก printed_picking = True
  - บันทึก printed_picking_at timestamp
  - สร้าง SkuPrintHistory record
  - เพิ่ม print_count สำหรับแต่ละ SKU
- Export เป็น Excel

#### US-016: ดูรายงานสต็อกต่ำ (Low Stock Report)
**As a** Purchasing Team
**I want to** ดูรายงาน SKU ที่มีสต็อกเหลือน้อย (≤3 หลังจัดสรร)
**So that** วางแผนสั่งซื้อเพิ่ม

**Acceptance Criteria:**
- เข้าหน้า /report/lowstock
- แสดงตาราง SKU ที่มี Status = LOW_STOCK
- แสดงคอลัมน์:
  - SKU
  - สต็อกปัจจุบัน
  - ยอดจอง (Allocated)
  - สต็อกคงเหลือ (≤3)
  - จำนวน Orders ที่เกี่ยวข้อง
- ปุ่ม "พิมพ์รายงาน" พร้อมระบุรอบจัดส่ง
- Export เป็น Excel

#### US-017: ดูรายงานขาดสต็อก (No Stock Report)
**As a** Purchasing Team
**I want to** ดูรายงาน SKU ที่หมดสต็อก (สต็อก = 0)
**So that** สั่งซื้อด่วน

**Acceptance Criteria:**
- เข้าหน้า /report/nostock
- แสดงตาราง SKU ที่มี Status = SHORTAGE
- แสดงคอลัมน์:
  - SKU
  - สต็อกปัจจุบัน (0)
  - จำนวน Orders ที่รอคอย
  - แพลตฟอร์มที่เกี่ยวข้อง
- ปุ่ม "พิมพ์รายงาน" พร้อมระบุรอบจัดส่ง
- Export เป็น Excel

#### US-018: ดูรายงานสต็อกไม่พอ (Not Enough Stock Report)
**As a** Purchasing Team
**I want to** ดูรายงาน SKU ที่มีสต็อกแต่ไม่พอสำหรับคำสั่งซื้อ
**So that** จัดลำดับความสำคัญในการสั่งซื้อ

**Acceptance Criteria:**
- เข้าหน้า /report/notenough
- แสดงตาราง SKU ที่มี Status = NOT_ENOUGH
- แสดงคอลัมน์:
  - SKU
  - สต็อกปัจจุบัน (> 0)
  - ยอดที่ต้องการ (Required)
  - ส่วนต่าง (Shortage)
- ปุ่ม "พิมพ์รายงาน" พร้อมระบุรอบจัดส่ง
- Export เป็น Excel

#### US-019: Print with Round Validation (Low/No/NotEnough Reports)
**As a** Warehouse Manager
**I want to** พิมพ์รายงานพร้อมระบุรอบจัดส่ง และเลือก Orders ที่ต้องการพิมพ์
**So that** จัดการคำสั่งซื้อแยกตามรอบ

**Acceptance Criteria:**
- ปุ่ม "พิมพ์รายการที่เลือก" (Print Selected Orders)
- ระบุรอบจัดส่ง (Dispatch Round) ใน Modal
- เลือก Orders ที่ต้องการพิมพ์ผ่าน Checkbox
- ระบบตรวจสอบ:
  - ต้องระบุรอบจัดส่ง
  - ต้องเลือกอย่างน้อย 1 รายการ
- บันทึก:
  - printed_lowstock/nostock/notenough = True
  - printed_*_at timestamp
  - dispatch_round
- แสดงจำนวนรายการที่พิมพ์

### 3.4 Admin & Settings

#### US-020: จัดการผู้ใช้ (User Management)
**As an** Admin
**I want to** เพิ่ม/แก้ไข/ลบผู้ใช้
**So that** ควบคุมการเข้าถึงระบบ

**Acceptance Criteria:**
- เข้าหน้า /admin/users
- แสดงตารางผู้ใช้ทั้งหมด (Username, Role, Active Status)
- ปุ่ม "เพิ่มผู้ใช้"
  - กรอก Username, Password, Role (Admin/User), Active (Yes/No)
  - บันทึกลง Database
- ปุ่ม "แก้ไข" สำหรับแต่ละผู้ใช้
  - แก้ไข Role, Active Status, รีเซ็ตรหัสผ่าน
- ปุ่ม "ลบ" สำหรับแต่ละผู้ใช้
  - Soft Delete (active = False) หรือ Hard Delete

#### US-021: จัดการร้านค้า (Shop Management)
**As an** Admin
**I want to** เพิ่ม/แก้ไข/ลบร้านค้า
**So that** ระบบรู้จักร้านค้าที่เชื่อมต่อ

**Acceptance Criteria:**
- เข้าหน้า /admin/shops
- แสดงตารางร้านค้าทั้งหมด (Platform, Shop Name, Google Sheet URL)
- ปุ่ม "เพิ่มร้านค้า"
  - กรอก Platform, Shop Name, Google Sheet URL (Optional)
  - Unique Constraint: Platform + Name
- ปุ่ม "แก้ไข" สำหรับแต่ละร้านค้า
  - แก้ไข Google Sheet URL
- ปุ่ม "ลบ" สำหรับแต่ละร้านค้า
  - ตรวจสอบว่าไม่มี Orders อ้างอิงอยู่

#### US-022: ตรวจสอบสุขภาพระบบ (System Health Check)
**As an** Admin
**I want to** ตรวจสอบสถานะระบบ
**So that** มั่นใจว่าระบบทำงานปกติ

**Acceptance Criteria:**
- เข้าหน้า /system-status
- แสดง:
  - Database Status (Connected/Disconnected)
  - Total Orders Count
  - Total Stock Items Count
  - Last Import Timestamp
  - Server Uptime (ถ้ามี)
- แสดงสีเขียวถ้าปกติ, สีแดงถ้ามีปัญหา

---

## 4. UI/UX REQUIREMENTS

### 4.1 Design System

#### 4.1.1 Typography
- **Primary Font:** Kanit (Google Fonts) - ภาษาไทย
- **Font Weights:**
  - Light (300): Labels
  - Regular (400): Body text
  - Medium (500): Headings
  - SemiBold (600): Buttons
  - Bold (700): Page titles
- **Font Sizes:**
  - h1: 2rem (32px) - Page Titles
  - h2: 1.5rem (24px) - Section Headers
  - h3: 1.25rem (20px) - Card Titles
  - body: 1rem (16px) - Content
  - small: 0.875rem (14px) - Helper text

#### 4.1.2 Color Palette
**Primary Colors:**
- Fire Gradient: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Success Gradient: `linear-gradient(135deg, #f093fb 0%, #f5576c 100%)`
- Warning Gradient: `linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)`
- Danger Gradient: `linear-gradient(135deg, #fa709a 0%, #fee140 100%)`
- Info Gradient: `linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)`

**Semantic Colors:**
- READY_ACCEPT: Green (#28a745)
- LOW_STOCK: Orange (#ffc107)
- SHORTAGE: Red (#dc3545)
- NOT_ENOUGH: Yellow (#ffc107)
- ACCEPTED: Blue (#007bff)
- PACKED: Purple (#6f42c1)
- CANCELLED: Gray (#6c757d) with strikethrough

**Background:**
- Page Background: #f8f9fa (Light Gray)
- Card Background: #ffffff (White)
- Sidebar Background: #2c3e50 (Dark Blue-Gray)

#### 4.1.3 Spacing & Layout
- **Container Max Width:** 1400px
- **Grid System:** Bootstrap 5 Grid (12 columns)
- **Card Padding:** 1.5rem (24px)
- **Section Spacing:** 2rem (32px)
- **Button Padding:** 0.5rem 1rem (8px 16px)

#### 4.1.4 Icons
- **Icon Library:** Lucide Icons (258 total icons)
- **Implementation:** Inline SVG (no FOUT)
- **Size:** 16px-24px (depends on context)
- **Common Icons:**
  - Menu: `menu` (Hamburger)
  - Dashboard: `layout-dashboard`
  - Upload: `upload`
  - Print: `printer`
  - Export: `download`
  - Accept: `check-circle`
  - Cancel: `x-circle`
  - Scan: `scan`
  - User: `user`
  - Shop: `store`

#### 4.1.5 Shadows & Elevation
- **Card Shadow:** `0 2px 4px rgba(0,0,0,0.1)`
- **Card Hover:** `0 4px 12px rgba(0,0,0,0.15)`
- **Button Shadow:** `0 2px 4px rgba(0,0,0,0.1)`

### 4.2 Responsive Design

#### 4.2.1 Breakpoints
- **xs:** <576px (Mobile Portrait)
- **sm:** ≥576px (Mobile Landscape)
- **md:** ≥768px (Tablet Portrait)
- **lg:** ≥992px (Tablet Landscape / Desktop)
- **xl:** ≥1200px (Large Desktop)
- **xxl:** ≥1400px (Extra Large Desktop)

#### 4.2.2 Mobile Adaptations
- **Sidebar:** Collapsible on Mobile (<768px)
- **Tables:** Horizontal scroll on small screens
- **KPI Cards:** Stack vertically on Mobile (col-12)
- **Filters:** Accordion-style collapse on Mobile
- **Buttons:** Full-width on Mobile (<576px)

#### 4.2.3 Touch Targets
- **Minimum Size:** 44x44px (Apple Guidelines)
- **Spacing:** 8px minimum between clickable elements
- **Checkbox Size:** 20x20px

### 4.3 Navigation Structure

#### 4.3.1 Sidebar Navigation (Collapsible)
```
┌─────────────────────────────┐
│ VNIX Order Management       │ (Logo + Title)
├─────────────────────────────┤
│ ⚡ Dashboard                │
│ 📦 Import                   │ (Expandable)
│   ├─ Products               │
│   ├─ Stock                  │
│   ├─ Sales Status           │
│   ├─ Orders                 │
│   ├─ Cancel Orders          │
│   └─ Issued Orders          │
│ 📊 Reports                  │ (Expandable)
│   ├─ Warehouse Job Sheet   │
│   ├─ Picking List           │
│   ├─ Low Stock              │
│   ├─ No Stock               │
│   └─ Not Enough Stock       │
│ ⚙️  Admin                   │ (Admin Only)
│   ├─ Users                  │
│   ├─ Shops                  │
│   └─ System Status          │
│ 🗑️ Deleted Orders           │
│ 📜 Import History           │
│ 🚪 Logout                   │
└─────────────────────────────┘
```

#### 4.3.2 Top Bar
- **Left:** Hamburger Menu (Toggle Sidebar on Mobile)
- **Center:** Page Title
- **Right:**
  - Real-time Thai Buddhist Calendar Clock
  - Username Display
  - Logout Button

### 4.4 Data Tables Configuration

#### 4.4.1 DataTables Features
- **Pagination:** 50 rows per page (default)
- **Search:** Global search bar (top-right)
- **Column Filters:** Individual filter per column (footer)
- **Sorting:** Click column header to sort (ASC/DESC)
- **State Persistence:** Save filter/sort/pagination in Browser
- **Thai Localization:** All labels in Thai
- **Responsive:** Horizontal scroll on small screens

#### 4.4.2 Column Configuration (Dashboard Table)
| Column | Width | Sortable | Filterable | Alignment |
|--------|-------|----------|------------|-----------|
| Checkbox | 40px | No | No | Center |
| Status | 100px | Yes | Yes | Center |
| Platform | 100px | Yes | Yes | Left |
| Shop | 120px | Yes | Yes | Left |
| Order ID | 150px | Yes | Yes | Left |
| SKU | 120px | Yes | Yes | Left |
| Item Name | 200px | Yes | Yes | Left |
| Qty | 60px | Yes | No | Center |
| Stock | 60px | Yes | No | Center |
| SLA | 120px | Yes | Yes | Center |
| Order Time | 150px | Yes | Yes | Center |
| Logistic | 100px | Yes | Yes | Left |
| Dispatch Round | 80px | Yes | Yes | Center |
| Scanned | 80px | Yes | Yes | Center |
| Actions | 150px | No | No | Center |

#### 4.4.3 Row Styling Rules
- **READY_ACCEPT:** Green background (#d4edda)
- **LOW_STOCK:** Orange background (#fff3cd)
- **SHORTAGE:** Red background (#f8d7da)
- **NOT_ENOUGH:** Yellow background (#fff3cd)
- **ACCEPTED:** Blue background (#d1ecf1)
- **PACKED:** Purple background (#e2d9f3)
- **CANCELLED:** Gray background + strikethrough text
- **Order Grouping:** Border-top (3px solid #dee2e6) every 5 rows

### 4.5 Forms & Input Fields

#### 4.5.1 Form Layout
- **Label Position:** Top-aligned
- **Required Fields:** Red asterisk (*)
- **Field Width:** Full-width (100%) on Mobile, 50%-75% on Desktop
- **Input Height:** 38px (default Bootstrap)
- **Error Messages:** Below field, red text (#dc3545)
- **Success Messages:** Below field, green text (#28a745)

#### 4.5.2 Input Types
- **Text Input:** Username, Shop Name, SKU
- **Password Input:** Password (hidden characters)
- **Number Input:** Qty, Stock, Dispatch Round
- **Select Dropdown:** Platform, Logistic Type, Role
- **Multi-select:** Platform Filter, Shop Filter
- **Date Picker:** Import Date, Date Range Filter
- **File Upload:** Excel/CSV Upload (drag-and-drop)
- **Textarea:** Google Sheet URL

#### 4.5.3 Buttons
**Primary Button:**
- Background: #007bff (Blue)
- Hover: #0056b3 (Darker Blue)
- Text: White
- Border-radius: 4px
- Use for: Accept, Save, Submit

**Secondary Button:**
- Background: #6c757d (Gray)
- Hover: #545b62 (Darker Gray)
- Text: White
- Use for: Cancel, Reset, Clear

**Success Button:**
- Background: #28a745 (Green)
- Hover: #1e7e34 (Darker Green)
- Text: White
- Use for: Print, Export

**Danger Button:**
- Background: #dc3545 (Red)
- Hover: #bd2130 (Darker Red)
- Text: White
- Use for: Delete, Bulk Cancel

**Warning Button:**
- Background: #ffc107 (Yellow)
- Hover: #e0a800 (Darker Yellow)
- Text: Dark Gray
- Use for: Low Stock actions

### 4.6 Modals & Dialogs

#### 4.6.1 Modal Structure
- **Header:** Title + Close Button (×)
- **Body:** Form fields or content
- **Footer:** Cancel + Confirm buttons
- **Backdrop:** Dark overlay (#000, 50% opacity)
- **Close Behavior:** Click outside = Close, ESC key = Close

#### 4.6.2 Common Modals
1. **Barcode Scan Modal**
   - Input: Order ID
   - Auto-focus on input
   - Submit on Enter key

2. **Bulk Accept Confirmation Modal**
   - Display: จำนวนรายการที่เลือก
   - Buttons: ยกเลิก, ยืนยันการรับออเดอร์

3. **Print with Round Modal**
   - Input: Dispatch Round (required)
   - Checkbox: Select Orders to print
   - Validation: Must enter round + select ≥1 order
   - Buttons: ยกเลิก, พิมพ์

4. **Delete Confirmation Modal**
   - Display: จำนวนรายการที่จะลบ
   - Warning: "คุณแน่ใจหรือไม่?"
   - Buttons: ยกเลิก, ลบ

### 4.7 Notifications & Feedback

#### 4.7.1 Flash Messages
- **Position:** Top-center (below top bar)
- **Duration:** 5 seconds (auto-dismiss)
- **Types:**
  - Success: Green background (#d4edda), green border
  - Error: Red background (#f8d7da), red border
  - Warning: Yellow background (#fff3cd), yellow border
  - Info: Blue background (#d1ecf1), blue border
- **Dismiss:** Manual close button (×)

#### 4.7.2 Toast Notifications (Barcode Scan)
- **Position:** Bottom-right
- **Duration:** 3 seconds
- **Type:** Success (green) or Error (red)
- **Content:** "สแกนสำเร็จ: ORDER123456" หรือ "ไม่พบออเดอร์"

#### 4.7.3 Loading States
- **Page Load:** Spinner overlay (center of page)
- **Button Click:** Disable button + show spinner inside button
- **Table Load:** DataTables "Loading..." message

### 4.8 Accessibility (a11y)

#### 4.8.1 Keyboard Navigation
- **Tab Order:** Logical flow (top → bottom, left → right)
- **Focus Indicators:** Blue outline (2px solid #007bff)
- **Enter Key:** Submit forms, activate buttons
- **ESC Key:** Close modals
- **Space Key:** Toggle checkboxes

#### 4.8.2 Screen Reader Support
- **Alt Text:** All images and icons
- **ARIA Labels:** Buttons without visible text
- **ARIA Live Regions:** Flash messages, toast notifications
- **Semantic HTML:** `<header>`, `<nav>`, `<main>`, `<footer>`

#### 4.8.3 Color Contrast
- **Minimum Ratio:** 4.5:1 (WCAG AA)
- **Large Text:** 3:1 (WCAG AA)
- **Test Tool:** Chrome DevTools Lighthouse

---

## 5. PAGE-BY-PAGE SPECIFICATIONS

### 5.1 Login Page (`/login`)

**Purpose:** User Authentication

**Layout:**
- Centered card (400px width)
- Logo + Title: "VNIX Order Management"
- Form fields:
  - Username (text input)
  - Password (password input)
  - Remember Me (checkbox)
- Submit button: "เข้าสู่ระบบ"
- Error message area (red text)

**Business Rules:**
- Hash password with werkzeug security
- Session-based authentication
- Redirect to Dashboard on success
- Flash error on failure

**Acceptance Criteria:**
- ✓ Username and Password required
- ✓ Show error if credentials invalid
- ✓ Redirect to Dashboard after login
- ✓ Session expires after 24 hours (or logout)

---

### 5.2 Dashboard (`/`)

**Purpose:** Main Order Management Interface

**Sections:**

#### 5.2.1 Top Filter Bar
- **Date Range Filter:** From Date, To Date (default: today)
- **Platform Filter:** Multi-select dropdown (Shopee, TikTok, Lazada, Other, All)
- **Shop Filter:** Multi-select dropdown (dynamic from DB)
- **Logistic Filter:** Multi-select dropdown (dynamic from DB)
- **Status Filter:** Multi-select dropdown (All statuses)
- **Buttons:** Apply Filters, Clear All

#### 5.2.2 KPI Cards Row
- **Card 1: Total Orders**
  - Count: All orders (filtered)
  - Gradient: Fire Gradient
  - Icon: `package`

- **Card 2: Ready to Accept (READY_ACCEPT)**
  - Count: Orders with status READY_ACCEPT
  - Gradient: Success Gradient
  - Icon: `check-circle`

- **Card 3: Low Stock (LOW_STOCK)**
  - Count: Orders with status LOW_STOCK
  - Gradient: Warning Gradient
  - Icon: `alert-triangle`

- **Card 4: Out of Stock (SHORTAGE)**
  - Count: Orders with status SHORTAGE
  - Gradient: Danger Gradient
  - Icon: `x-circle`

- **Card 5: Not Enough Stock (NOT_ENOUGH)**
  - Count: Orders with status NOT_ENOUGH
  - Gradient: Warning Gradient
  - Icon: `minus-circle`

- **Card 6: Accepted (ACCEPTED)**
  - Count: Orders with status ACCEPTED
  - Gradient: Info Gradient
  - Icon: `thumbs-up`

- **Card 7: Packed (PACKED)**
  - Count: Orders with status PACKED
  - Gradient: Success Gradient
  - Icon: `box`

#### 5.2.3 Bulk Action Bar
- **Checkbox:** Select All
- **Buttons:**
  - รับออเดอร์ที่เลือก (Bulk Accept) - Blue
  - ยกเลิกที่เลือก (Bulk Cancel) - Red
  - ลบที่เลือก (Bulk Delete) - Dark Red
  - อัพเดทรอบจัดส่ง - Orange
  - รีเซ็ตการสแกน - Gray
- **Export Button:** Export to Excel - Green

#### 5.2.4 Orders Table
- **Columns:** (see Section 4.4.2)
- **Sorting:** Platform Priority (Shopee > TikTok > Lazada > Other), then Order Time (FIFO)
- **Row Actions:**
  - Accept (ปุ่มรับ) - for READY_ACCEPT/LOW_STOCK
  - Cancel Accept (ยกเลิกการรับ) - for ACCEPTED
- **Row Grouping:** Visual separator every 5 rows

**Business Rules:**
- Default Date Range: Today
- Platform Priority: Shopee > TikTok > Lazada > Other
- FIFO Sorting: Oldest order first within same priority
- Stock Allocation: Real-time calculation from allocation.py
- SLA Calculation: Business-day aware (exclude weekends/holidays)

**Acceptance Criteria:**
- ✓ Load orders within 2 seconds
- ✓ Filter updates table without page reload
- ✓ KPI cards update on filter change
- ✓ Bulk actions work for selected rows only
- ✓ Export includes all filtered data

---

### 5.3 Import Pages

#### 5.3.1 Import Products (`/import/products`)

**Layout:**
- Page Title: "นำเข้าข้อมูลสินค้า (Product Master)"
- Instructions card:
  - รองรับไฟล์: .xlsx, .xls, .csv
  - คอลัมน์ที่ต้องการ: SKU, Brand, Model
  - ตัวอย่างไฟล์ (Download Template)
- File Upload Area (drag-and-drop)
- Upload Button: "อัพโหลดและนำเข้า"
- Result card (after upload):
  - จำนวนรายการที่นำเข้าสำเร็จ
  - จำนวน Error (ถ้ามี)
  - ข้อความ Error รายละเอียด

**Business Rules:**
- Upsert by SKU (Insert or Update)
- Auto-detect columns (Thai/English)
- Skip rows with missing SKU

**Acceptance Criteria:**
- ✓ Accept .xlsx, .xls, .csv files
- ✓ Auto-detect columns
- ✓ Show success count
- ✓ Show error details if any
- ✓ Flash success message

#### 5.3.2 Import Stock (`/import/stock`)

**Layout:**
- Page Title: "นำเข้าข้อมูลสต็อก"
- Two tabs:
  1. Upload Excel/CSV
  2. Import from Google Sheets
- **Tab 1: Upload File**
  - Instructions
  - File Upload Area
  - Upload Button
- **Tab 2: Google Sheets**
  - Shop Dropdown (select shop with Google Sheet URL)
  - Preview Button (show first 5 rows)
  - Import Button
- Result card

**Business Rules:**
- Full Sync Mode: SKUs not in file = stock 0
- Update updated_at timestamp
- Google Sheets: Fetch via gspread API

**Acceptance Criteria:**
- ✓ Support Excel + Google Sheets
- ✓ Full sync mode (missing SKU = 0)
- ✓ Show preview before import (Google Sheets)
- ✓ Flash success message with count

#### 5.3.3 Import Orders (`/import/orders`)

**Layout:**
- Page Title: "นำเข้าคำสั่งซื้อ"
- Platform Selector: Shopee, TikTok, Lazada, Other
- Shop Selector: Dropdown (filter by platform)
- Two tabs:
  1. Upload Excel/CSV
  2. Import from Google Sheets
- File Upload Area
- Upload Button: "อัพโหลดและนำเข้า"
- Result card:
  - Success count
  - Duplicate count
  - Error count
  - Details list

**Business Rules:**
- INSERT-ONLY mode (no updates)
- Duplicate Detection: Same Order ID + Platform + Shop + Import Date
- Auto-detect columns
- Batch insert for performance

**Acceptance Criteria:**
- ✓ Must select Platform and Shop before upload
- ✓ Show duplicate count
- ✓ Preserve existing data
- ✓ Create ImportLog record
- ✓ Flash summary message

#### 5.3.4 Import History Dashboard (`/import/history`)

**Layout:**
- Page Title: "ประวัติการนำเข้าข้อมูล"
- Cards Grid (Reverse Chronological):
  - Each card shows:
    - Import Type (icon + label)
    - Timestamp (Thai format)
    - Username
    - File Name
    - Success Count (green)
    - Duplicate Count (yellow)
    - Error Count (red)
    - Details (expandable)

**Acceptance Criteria:**
- ✓ Show all imports
- ✓ Sort by newest first
- ✓ Click card to expand details
- ✓ Pagination (20 cards per page)

---

### 5.4 Report Pages

#### 5.4.1 Warehouse Job Sheet (`/report/warehouse`)

**Purpose:** Print job sheet for accepted orders

**Layout:**
- Page Title: "เอกสารงานคลังสินค้า (Warehouse Job Sheet)"
- Filter Bar:
  - Platform Filter
  - Shop Filter
  - Logistic Filter
  - Dispatch Round Filter
  - Apply Filters button
- Table:
  - Order ID, SKU, Item Name, Qty, Platform, Shop, Logistic, Order Time, Dispatch Round
- Action Bar:
  - Input: Dispatch Round (for selected orders)
  - Button: "พิมพ์เอกสาร" (Print/Export)

**Business Rules:**
- Show only ACCEPTED orders
- Print action:
  - Mark as printed_warehouse = True
  - Create IssuedOrder record
  - Change status to PACKED
- Export to Excel with Thai headers

**Acceptance Criteria:**
- ✓ Filter works without page reload
- ✓ Print marks orders as PACKED
- ✓ Excel export includes all visible columns
- ✓ Show print count in table

#### 5.4.2 Picking List (`/report/picking`)

**Purpose:** Group orders by SKU for efficient picking

**Layout:**
- Page Title: "ใบเบิกสินค้า (Picking List)"
- Filter Bar: Platform, Shop, Logistic
- Table (Grouped by SKU):
  - SKU
  - Item Name
  - Total Qty (sum across all orders)
  - Order IDs (comma-separated list)
  - Print Count (from SkuPrintHistory)
- Button: "พิมพ์ใบเบิก"

**Business Rules:**
- Group by SKU + Platform + Shop + Logistic
- Sum Qty for each group
- Print action:
  - Mark printed_picking = True
  - Create/Update SkuPrintHistory
  - Increment print_count

**Acceptance Criteria:**
- ✓ Group by SKU correctly
- ✓ Show all related Order IDs
- ✓ Track print count per SKU
- ✓ Export to Excel

#### 5.4.3 Low Stock Report (`/report/lowstock`)

**Purpose:** Show SKUs with low remaining stock (≤3 after allocation)

**Layout:**
- Page Title: "รายงานสต็อกต่ำ (Low Stock Report)"
- Filter Bar: Platform, Shop, Logistic
- Table:
  - SKU
  - Item Name
  - Current Stock
  - Allocated Qty
  - Remaining Stock (≤3)
  - Order Count
  - Order IDs
- Checkbox: Select orders to print
- Button: "พิมพ์รายการที่เลือก" (with Round validation)

**Business Rules:**
- Show SKUs where remaining stock ≤ 3
- Calculate from allocation engine (lowstock_core.py)
- Print with Round validation:
  - Must enter dispatch round
  - Must select ≥1 order
  - Mark printed_lowstock = True

**Acceptance Criteria:**
- ✓ Show only LOW_STOCK status SKUs
- ✓ Calculate remaining stock correctly
- ✓ Validate round before print
- ✓ Export to Excel

#### 5.4.4 No Stock Report (`/report/nostock`)

**Purpose:** Show SKUs with zero stock

**Layout:**
- Page Title: "รายงานขาดสต็อก (No Stock Report)"
- Filter Bar: Platform, Shop, Logistic
- Table:
  - SKU
  - Item Name
  - Current Stock (0)
  - Required Qty
  - Order Count
  - Platforms (unique list)
- Checkbox: Select orders to print
- Button: "พิมพ์รายการที่เลือก" (with Round validation)

**Business Rules:**
- Show SKUs where stock = 0
- Status = SHORTAGE
- Print with Round validation

**Acceptance Criteria:**
- ✓ Show only SHORTAGE status SKUs
- ✓ Show required qty
- ✓ Validate round before print
- ✓ Export to Excel

#### 5.4.5 Not Enough Stock Report (`/report/notenough`)

**Purpose:** Show SKUs with partial stock (stock > 0 but < required)

**Layout:**
- Page Title: "รายงานสต็อกไม่พอ (Not Enough Stock Report)"
- Filter Bar: Platform, Shop, Logistic
- Table:
  - SKU
  - Item Name
  - Current Stock
  - Required Qty
  - Shortage (Required - Stock)
  - Order Count
- Checkbox: Select orders to print
- Button: "พิมพ์รายการที่เลือก" (with Round validation)

**Business Rules:**
- Show SKUs where 0 < stock < required qty
- Status = NOT_ENOUGH
- Print with Round validation

**Acceptance Criteria:**
- ✓ Show only NOT_ENOUGH status SKUs
- ✓ Calculate shortage correctly
- ✓ Validate round before print
- ✓ Export to Excel

---

### 5.5 Admin Pages

#### 5.5.1 User Management (`/admin/users`)

**Layout:**
- Page Title: "จัดการผู้ใช้งาน (User Management)"
- Button: "เพิ่มผู้ใช้"
- Table:
  - Username
  - Role (Admin/User)
  - Active Status (Yes/No)
  - Actions (Edit, Delete)
- Add/Edit User Modal:
  - Username (required)
  - Password (required for new, optional for edit)
  - Role (dropdown)
  - Active (checkbox)
  - Buttons: Cancel, Save

**Business Rules:**
- Admin role: full access
- User role: order operations only
- Password hashing: werkzeug.security
- Soft delete: set active = False

**Acceptance Criteria:**
- ✓ Admin can add/edit/delete users
- ✓ Password hashed in DB
- ✓ Role controls access
- ✓ Flash success/error messages

#### 5.5.2 Shop Management (`/admin/shops`)

**Layout:**
- Page Title: "จัดการร้านค้า (Shop Management)"
- Button: "เพิ่มร้านค้า"
- Table:
  - Platform
  - Shop Name
  - Google Sheet URL
  - Actions (Edit, Delete)
- Add/Edit Shop Modal:
  - Platform (dropdown)
  - Shop Name (required)
  - Google Sheet URL (optional)
  - Buttons: Cancel, Save

**Business Rules:**
- Unique constraint: Platform + Name
- Google Sheet URL: for auto-import
- Cannot delete shop with existing orders

**Acceptance Criteria:**
- ✓ Admin can add/edit/delete shops
- ✓ Unique validation works
- ✓ Cannot delete if orders exist
- ✓ Flash success/error messages

#### 5.5.3 System Status (`/system-status`)

**Layout:**
- Page Title: "สถานะระบบ (System Status)"
- Status Cards:
  - Database Status (Green/Red icon)
  - Total Orders (count)
  - Total Stock Items (count)
  - Last Import (timestamp)
  - Disk Space (if available)
- Refresh Button

**Acceptance Criteria:**
- ✓ Show real-time status
- ✓ Green if healthy, red if error
- ✓ Auto-refresh every 30 seconds
- ✓ Manual refresh button

---

### 5.6 Deleted Orders (`/deleted`)

**Purpose:** Recycle Bin for deleted orders

**Layout:**
- Page Title: "รายการที่ถูกลบ (Deleted Orders)"
- Table (similar to Dashboard):
  - All columns from OrderLine
  - Deleted At timestamp
  - Deleted By username
- Actions:
  - Restore (move back to OrderLine)
  - Permanent Delete

**Business Rules:**
- Show all records from DeletedOrder table
- Restore: Move back to OrderLine, delete from DeletedOrder
- Permanent Delete: Delete from DeletedOrder (cannot undo)

**Acceptance Criteria:**
- ✓ Show all deleted orders
- ✓ Restore moves back to main table
- ✓ Permanent delete is irreversible
- ✓ Confirmation modal before permanent delete

---

## 6. USER JOURNEYS

### 6.1 Journey: Daily Order Processing (Warehouse Staff)

**Goal:** Process daily orders from import to dispatch

**Steps:**
1. **Login** → Dashboard
2. **Check KPI Cards** → See order counts by status
3. **Filter Orders:**
   - Select Platform (e.g., Shopee)
   - Select Today's date
   - Apply Filters
4. **Review READY_ACCEPT Orders:**
   - Check stock availability
   - Check SLA countdown
5. **Bulk Accept Orders:**
   - Select all READY_ACCEPT orders via checkboxes
   - Click "รับออเดอร์ที่เลือก"
   - Confirm in modal
   - See flash message "รับออเดอร์สำเร็จ X รายการ"
6. **Navigate to Warehouse Job Sheet:**
   - Click "Reports" → "Warehouse Job Sheet"
   - Filter: Platform = Shopee, Today's date
   - See all ACCEPTED orders
7. **Update Dispatch Round:**
   - Select orders via checkboxes
   - Enter "Round 1" in input field
   - Click "อัพเดทรอบจัดส่ง"
8. **Print Warehouse Job Sheet:**
   - Click "พิมพ์เอกสาร"
   - System marks orders as PACKED
   - Downloads Excel file
   - Print Excel file
9. **Navigate to Picking List:**
   - Click "Reports" → "Picking List"
   - Filter: Platform = Shopee, Round 1
   - See SKUs grouped with total quantities
10. **Print Picking List:**
    - Click "พิมพ์ใบเบิก"
    - Downloads Excel file
    - Use to pick items from warehouse
11. **Scan Orders:**
    - Click "สแกนบาร์โค้ด" on Dashboard
    - Scan each Order ID barcode
    - See checkmark (✓) in "สแกนแล้ว" column
12. **Handle Low Stock:**
    - Navigate to "Low Stock Report"
    - See SKUs with stock ≤ 3
    - Select orders to print
    - Enter Round number
    - Print report
    - Inform purchasing team

**Success Criteria:**
- All orders processed within SLA
- No stock allocation errors
- All orders scanned before dispatch
- Low stock reported to purchasing team

---

### 6.2 Journey: Managing Out-of-Stock Situations (Purchasing Team)

**Goal:** Identify and order out-of-stock items

**Steps:**
1. **Login** → Dashboard
2. **Check Out-of-Stock KPI Card:**
   - See "ขาดสต็อก (SHORTAGE)" count
   - Click card to filter
3. **Navigate to No Stock Report:**
   - Click "Reports" → "No Stock Report"
4. **Review No Stock SKUs:**
   - See SKUs with 0 stock
   - See required quantities
   - See order counts
5. **Export Report:**
   - Click "Export to Excel"
   - Download report
6. **Navigate to Not Enough Stock Report:**
   - Click "Reports" → "Not Enough Stock Report"
7. **Review Partial Stock SKUs:**
   - See SKUs with partial stock
   - Calculate shortage amounts
8. **Export Report:**
   - Download Excel
9. **Send to Supplier:**
   - Combine both reports
   - Email to supplier
   - Request urgent restock
10. **Return to Dashboard:**
    - Monitor stock updates (after supplier delivers)
    - Re-run allocation
    - Accept orders when stock available

**Success Criteria:**
- All out-of-stock items identified
- Reports sent to supplier within 1 hour
- Stock updated after delivery
- Orders accepted after stock replenishment

---

### 6.3 Journey: Monthly User & Shop Management (Admin)

**Goal:** Maintain user accounts and shop configurations

**Steps:**
1. **Login** → Dashboard
2. **Navigate to User Management:**
   - Click "Admin" → "Users"
3. **Add New User:**
   - Click "เพิ่มผู้ใช้"
   - Fill form: Username, Password, Role = User, Active = Yes
   - Click "Save"
   - See flash message "เพิ่มผู้ใช้สำเร็จ"
4. **Edit Existing User:**
   - Click "Edit" for user
   - Change Role to Admin
   - Click "Save"
5. **Deactivate User:**
   - Click "Edit" for user
   - Uncheck "Active"
   - Click "Save"
   - User cannot login
6. **Navigate to Shop Management:**
   - Click "Admin" → "Shops"
7. **Add New Shop:**
   - Click "เพิ่มร้านค้า"
   - Select Platform = Shopee
   - Enter Shop Name
   - Paste Google Sheet URL
   - Click "Save"
8. **Edit Shop:**
   - Click "Edit" for shop
   - Update Google Sheet URL
   - Click "Save"
9. **Test Google Sheet Import:**
   - Navigate to "Import" → "Stock"
   - Select new shop from dropdown
   - Click "Import from Google Sheets"
   - Verify preview
   - Click "Import"
10. **Check System Status:**
    - Navigate to "Admin" → "System Status"
    - Verify database connected
    - Check disk space
    - Review last import time

**Success Criteria:**
- User accounts up to date
- All shops configured with Google Sheets
- Auto-import working
- System health verified

---

## 7. BUSINESS RULES (FRONTEND-RELATED)

### 7.1 Order Status Lifecycle

```
[Import]
  ↓
[Allocation Engine Evaluates]
  ↓
┌─────────────────────────────────────┐
│ READY_ACCEPT (Stock Available)      │ ←─ Can Accept
│ LOW_STOCK (Stock ≤3 after alloc)    │ ←─ Can Accept (with warning)
│ SHORTAGE (No stock)                 │ ←─ Cannot Accept
│ NOT_ENOUGH (Partial stock)          │ ←─ Cannot Accept
└─────────────────────────────────────┘
  ↓ (User accepts)
[ACCEPTED]
  ↓ (Print Warehouse Job Sheet)
[PACKED] (Issued to warehouse)
  ↓ (Scan barcode)
[Scanned] (Ready to ship)
  ↓ (Ship)
[Shipped] (Complete)

[CANCELLED] ←─ Can happen at any stage
```

### 7.2 Stock Allocation Priority

**Priority Rules:**
1. **Platform Priority:**
   - Shopee = 1st
   - TikTok = 2nd
   - Lazada = 3rd
   - Other = 4th

2. **Time Priority (within same platform):**
   - FIFO: First In, First Out
   - Sort by order_time (ASC)

3. **Allocation Logic:**
   - Iterate orders by priority
   - Deduct stock for each order
   - If stock ≥ required qty → READY_ACCEPT
   - If stock ≤ 3 after allocation → LOW_STOCK
   - If stock = 0 before allocation → SHORTAGE
   - If 0 < stock < required qty → NOT_ENOUGH

### 7.3 SLA Calculation (Business-Day Aware)

**Calculation Logic:**
- **Business Days:** Monday-Friday (exclude weekends)
- **Holidays:** Configurable list in code
- **Cutoff Times:**
  - Lazada: 11:00 AM
  - Shopee/TikTok/Others: 12:00 PM (noon)

**SLA Display:**
- "วันนี้" (Today) - Order before cutoff, ship same day
- "พรุ่งนี้" (Tomorrow) - Order after cutoff, ship next business day
- "อีก 2 วัน" (In 2 days) - 2 business days away
- "เลยกำหนด (3 วัน)" (Overdue: 3 days) - Red text, urgent

**Business Day Counting:**
- If order_time = Friday 1:00 PM, SLA = Monday (skip weekend)
- If holiday on Monday, SLA = Tuesday

### 7.4 Print Tracking Rules

**Print Types:**
1. **Warehouse Job Sheet (printed_warehouse):**
   - Marks order as PACKED
   - Creates IssuedOrder record (source: 'print')
   - Cannot print again (prevent duplicates)

2. **Picking List (printed_picking):**
   - Creates/Updates SkuPrintHistory
   - Increments print_count per SKU
   - Can print multiple times (for reprints)

3. **Report Prints (printed_lowstock, printed_nostock, printed_notenough):**
   - Tracks dispatch round
   - Validates round before print
   - Timestamps each print

**Idempotency:**
- Use ActionDedupe table to prevent double-clicks
- Token = user_id + action_type + timestamp
- Expire tokens after 5 minutes

### 7.5 Filter Persistence

**Rules:**
- Save filter state in Browser localStorage
- Persist across page reloads
- Key format: `vnix_filters_{page_name}`
- Saved data: Platform, Shop, Logistic, Date Range, Status
- Clear on logout

**DataTables State:**
- Save pagination, sorting, search in stateSave
- Restore on page load
- Clear button resets to defaults

### 7.6 Bulk Operation Rules

**Bulk Accept:**
- Only READY_ACCEPT and LOW_STOCK orders
- Ignore SHORTAGE, NOT_ENOUGH, ACCEPTED, PACKED
- Show confirmation modal with count
- Batch insert for performance (max 100 per batch)

**Bulk Cancel:**
- Any status except PACKED
- Cannot cancel orders already dispatched
- Show confirmation modal
- Mark as CANCELLED

**Bulk Delete:**
- Move to DeletedOrder table
- Cannot delete PACKED orders (must cancel first)
- Soft delete (can restore)

### 7.7 Date & Time Display

**Formats:**
- **Date:** DD/MM/YYYY (Thai format)
- **Time:** HH:MM (24-hour)
- **DateTime:** DD/MM/YYYY HH:MM
- **Buddhist Calendar:** YYYY + 543 = Buddhist Year

**Example:**
- Gregorian: 26/12/2025 14:30
- Buddhist: 26/12/2568 14:30

**Real-time Clock:**
- Update every second
- Display in top bar
- Show current Buddhist date + time

---

## 8. ACCEPTANCE CRITERIA SUMMARY

### 8.1 Performance
- ✓ Page load time < 2 seconds
- ✓ Filter update < 500ms
- ✓ Bulk action (100 orders) < 3 seconds
- ✓ Export (1000 rows) < 5 seconds
- ✓ Real-time clock update every 1 second

### 8.2 Usability
- ✓ All buttons have clear labels (Thai)
- ✓ Error messages explain what went wrong
- ✓ Success messages confirm action completed
- ✓ Forms validate before submit
- ✓ Confirmation modals for destructive actions

### 8.3 Data Integrity
- ✓ No duplicate order inserts
- ✓ Stock allocation never negative
- ✓ Print tracking accurate
- ✓ Soft delete preserves data
- ✓ Timestamps in GMT+7 (Thailand)

### 8.4 Browser Compatibility
- ✓ Chrome (latest)
- ✓ Firefox (latest)
- ✓ Safari (latest)
- ✓ Edge (latest)
- ✓ Mobile Safari (iOS 14+)
- ✓ Mobile Chrome (Android 10+)

### 8.5 Accessibility
- ✓ Keyboard navigation works
- ✓ Focus indicators visible
- ✓ Color contrast ≥ 4.5:1
- ✓ Alt text on all images/icons
- ✓ Screen reader compatible

### 8.6 Security
- ✓ Password hashed (never plaintext)
- ✓ Session-based authentication
- ✓ Role-based access control
- ✓ SQL injection prevention (parameterized queries)
- ✓ XSS prevention (escape user input)

---

## 9. APPENDIX

### 9.1 Glossary

| Term | Definition |
|------|------------|
| **SKU** | Stock Keeping Unit - รหัสสินค้า |
| **FIFO** | First In, First Out - สินค้าเข้าก่อนออกก่อน |
| **SLA** | Service Level Agreement - ข้อตกลงระดับการให้บริการ |
| **Platform** | แพลตฟอร์ม E-commerce (Shopee, TikTok, Lazada) |
| **Logistic** | บริษัทขนส่ง (Flash, Kerry, J&T, ฯลฯ) |
| **Dispatch Round** | รอบการจัดส่ง (1, 2, 3, ฯลฯ) |
| **Allocation** | การจัดสรรสต็อก |
| **Picking** | การเบิกสินค้าจากคลัง |
| **Packing** | การแพ็คสินค้า |
| **Barcode Scanning** | การสแกนบาร์โค้ดเพื่อยืนยัน |
| **Business Day** | วันทำการ (จันทร์-ศุกร์) |
| **Buddhist Calendar** | ปฏิทินพุทธศักราช (เพิ่ม 543 ปี) |

### 9.2 UI Component Mapping

| Component | Library | Version | Notes |
|-----------|---------|---------|-------|
| Grid System | Bootstrap | 5.3.2 | 12-column responsive grid |
| DataTables | DataTables | 1.13.x | Thai localization |
| Date Picker | (Custom) | - | Native HTML5 date input |
| Icons | Lucide | Latest | 258 icons, inline SVG |
| Fonts | Google Fonts | - | Kanit (Thai) |
| Modals | Bootstrap | 5.3.2 | JavaScript-based |
| Toast | Bootstrap | 5.3.2 | Auto-dismiss notifications |
| Charts | (Future) | - | Chart.js (if needed) |

### 9.3 Feature Priority Matrix

| Feature | Priority | Complexity | Status |
|---------|----------|------------|--------|
| Dashboard | P0 (Critical) | High | ✅ Done |
| Order Import | P0 (Critical) | High | ✅ Done |
| Stock Allocation | P0 (Critical) | Very High | ✅ Done |
| Bulk Accept | P0 (Critical) | Medium | ✅ Done |
| Warehouse Job Sheet | P0 (Critical) | Medium | ✅ Done |
| Picking List | P1 (High) | Medium | ✅ Done |
| Low Stock Report | P1 (High) | Medium | ✅ Done |
| No Stock Report | P1 (High) | Medium | ✅ Done |
| Not Enough Report | P1 (High) | Medium | ✅ Done |
| Barcode Scanning | P1 (High) | Low | ✅ Done |
| User Management | P2 (Medium) | Low | ✅ Done |
| Shop Management | P2 (Medium) | Low | ✅ Done |
| Google Sheets Import | P2 (Medium) | Medium | ✅ Done |
| Print Tracking | P2 (Medium) | Medium | ✅ Done |
| Import History | P2 (Medium) | Low | ✅ Done |
| Soft Delete | P3 (Low) | Low | ✅ Done |
| System Status | P3 (Low) | Low | ✅ Done |

### 9.4 Known Limitations & Future Enhancements

**Current Limitations:**
1. No mobile app (web-only)
2. No real-time notifications (WebSockets)
3. No advanced analytics/charts
4. No multi-warehouse support
5. No API for external integration

**Future Enhancements:**
1. Real-time order updates (WebSockets)
2. Mobile app (React Native / Flutter)
3. Advanced reporting with charts (Chart.js / D3.js)
4. Multi-warehouse inventory management
5. REST API for third-party integration
6. Automated email notifications
7. SMS alerts for urgent orders
8. AI-based demand forecasting
9. Barcode label printing
10. Integration with accounting systems

---

## 10. REVISION HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 5.52 | 2025-12-26 | Claude Code | Initial PRD created from codebase analysis |

---

**End of PRD-Frontend.md**
