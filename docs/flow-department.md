# 🏢 คู่มือ Flow การทำงานแยกตามแผนก
## VNIX Warehouse Management System (WMS)

---

## 📋 สารบัญ

1. [System Menu Inventory](#1-system-menu-inventory)
2. [Detailed Flow Diagrams](#2-detailed-flow-diagrams)
3. [Daily Operation Guides](#3-daily-operation-guides)
4. [Training Manuals](#4-training-manuals)
5. [Risk Assessment & Mitigation](#5-risk-assessment--mitigation)
6. [Developer Roadmap](#6-developer-roadmap)

---

## 1. System Menu Inventory

### 1.1 เมนูทั้งหมดในระบบ (60+ Endpoints)

#### 📊 Dashboard & Reporting
| เมนู | Endpoint | Admin | Staff | Picker | Packer | คำอธิบาย |
|------|----------|:-----:|:-----:|:------:|:------:|----------|
| Dashboard | `/` | ✅ | ✅ | ❌ | ❌ | ภาพรวมออเดอร์ทั้งหมด |
| Export Dashboard | `/export/dashboard` | ✅ | ✅ | ❌ | ❌ | ส่งออก Excel |
| Report | `/report` | ✅ | ✅ | ❌ | ❌ | รายงานสรุป |
| Report Print | `/report/print` | ✅ | ✅ | ❌ | ❌ | พิมพ์รายงาน |

#### 📥 Import Management (Admin Only)
| เมนู | Endpoint | Admin | Staff | Picker | Packer | คำอธิบาย |
|------|----------|:-----:|:-----:|:------:|:------:|----------|
| Import Orders | `/import/orders` | ✅ | ❌ | ❌ | ❌ | นำเข้าออเดอร์ |
| Import Products | `/import/products` | ✅ | ❌ | ❌ | ❌ | นำเข้าสินค้า |
| Import Stock | `/import/stock` | ✅ | ❌ | ❌ | ❌ | นำเข้าสต็อก |
| Import Sales | `/import/sales` | ✅ | ❌ | ❌ | ❌ | นำเข้าข้อมูลขาย |

#### 📦 Batch Management
| เมนู | Endpoint | Admin | Staff | Picker | Packer | คำอธิบาย |
|------|----------|:-----:|:-----:|:------:|:------:|----------|
| Batch Create | `/batch/create` | ✅ | ✅ | ❌ | ❌ | สร้าง Batch ใหม่ |
| Batch List | `/batch/list` | ✅ | ✅ | ✅* | ✅** | รายการ Batch |
| Batch Detail | `/batch/<id>` | ✅ | ✅ | ✅* | ✅ | รายละเอียด Batch |
| Batch Delete | `/batch/<id>/delete` | ✅ | ❌ | ❌ | ❌ | ลบ Batch |


#### 🔍 Picking Operations (Warehouse Team)
| เมนู | Endpoint | Admin | Staff | Picker | Packer | คำอธิบาย |
|------|----------|:-----:|:-----:|:------:|:------:|----------|
| Scan Batch | `/scan/batch` | ✅ | ❌ | ✅ | ❌ | รับงาน Batch |
| Scan SKU | `/scan/sku` | ✅ | ❌ | ✅ | ❌ | หยิบสินค้า |
| Quick Assign Batch | `/api/quick_assign_batch` | ✅ | ❌ | ✅ | ❌ | เลือก Batch ด่วน |
| Quick Assign SKU | `/api/quick_assign_sku` | ✅ | ❌ | ✅ | ❌ | เลือก SKU ด่วน |

#### 🚚 Dispatch Operations (Packer Team)
| เมนู | Endpoint | Admin | Staff | Picker | Packer | คำอธิบาย |
|------|----------|:-----:|:-----:|:------:|:------:|----------|
| Scan Handover | `/scan/handover` | ✅ | ❌ | ❌ | ✅ | สแกนส่งมอบ |
| Scan Tracking | `/scan/tracking` | ✅ | ❌ | ❌ | ✅ | บันทึก Tracking |
| Handover Print | `/batch/<id>/print_handover` | ✅ | ❌ | ❌ | ✅ | พิมพ์ใบส่งมอบ |

#### 🖨️ Printing Operations
| เมนู | Endpoint | Admin | Staff | Picker | Packer | คำอธิบาย |
|------|----------|:-----:|:-----:|:------:|:------:|----------|
| Picking List Print | `/batch/<id>/print_picking` | ✅ | ✅ | ✅ | ❌ | พิมพ์ใบหยิบของ |
| SKU QR Print | `/sku_qr_print` | ✅ | ✅ | ✅ | ❌ | พิมพ์ QR สินค้า |

#### ⚠️ Shortage Management
| เมนู | Endpoint | Admin | Staff | Picker | Packer | คำอธิบาย |
|------|----------|:-----:|:-----:|:------:|:------:|----------|
| Shortage Queue | `/shortage/queue` | ✅ | ✅ | ✅* | ❌ | รายการสินค้าขาด |
| Shortage Resolve | `/shortage/<id>/resolve` | ✅ | ❌ | ❌ | ❌ | จัดการ Shortage |

#### 👥 User Management (Admin Only)
| เมนู | Endpoint | Admin | Staff | Picker | Packer | คำอธิบาย |
|------|----------|:-----:|:-----:|:------:|:------:|----------|
| Users List | `/users` | ✅ | ❌ | ❌ | ❌ | จัดการผู้ใช้ |
| User Create | `/users/create` | ✅ | ❌ | ❌ | ❌ | สร้างผู้ใช้ใหม่ |
| User Edit | `/users/<id>/edit` | ✅ | ❌ | ❌ | ❌ | แก้ไขผู้ใช้ |
| User Delete | `/users/<id>/delete` | ✅ | ❌ | ❌ | ❌ | ลบผู้ใช้ |

#### 🔐 Authentication
| เมนู | Endpoint | Admin | Staff | Picker | Packer | คำอธิบาย |
|------|----------|:-----:|:-----:|:------:|:------:|----------|
| Login | `/login` | ✅ | ✅ | ✅ | ✅ | เข้าสู่ระบบ |
| Logout | `/logout` | ✅ | ✅ | ✅ | ✅ | ออกจากระบบ |

**หมายเหตุ:**
- ✅ = มีสิทธิ์เข้าถึงเต็ม
- ✅* = เห็นเฉพาะของตัวเอง (Picker เห็นเฉพาะ Batch ที่รับไว้)
- ✅** = เห็นเฉพาะ Batch ที่พร้อมส่ง (Progress 100%)
- ❌ = ไม่มีสิทธิ์เข้าถึง

---

### 1.2 Permission Matrix (สรุป)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Permission Matrix                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ฟีเจอร์                │ Admin │ Staff │ Picker │ Packer │    │
│  ─────────────────────────────────────────────────────────────  │
│  📊 Dashboard           │  ✅   │  ✅   │   ❌   │   ❌   │    │
│  📥 Import              │  ✅   │  ❌   │   ❌   │   ❌   │    │
│  📦 Batch Create        │  ✅   │  ✅   │   ❌   │   ❌   │    │
│  📦 Batch Delete        │  ✅   │  ❌   │   ❌   │   ❌   │    │
│  🔍 Scan Batch          │  ✅   │  ❌   │   ✅   │   ❌   │    │
│  🔍 Scan SKU            │  ✅   │  ❌   │   ✅   │   ❌   │    │
│  🚚 Scan Handover       │  ✅   │  ❌   │   ❌   │   ✅   │    │
│  🚚 Scan Tracking       │  ✅   │  ❌   │   ❌   │   ✅   │    │
│  ⚠️ Shortage Resolve    │  ✅   │  ❌   │   ❌   │   ❌   │    │
│  👥 User Management     │  ✅   │  ❌   │   ❌   │   ❌   │    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Flow Diagrams

### 2.1 Master Flow: End-to-End Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    VNIX WMS Master Flow                          │
│              (From Import to Dispatch)                           │
└─────────────────────────────────────────────────────────────────┘

📥 Phase 1: Import (Online Admin)
   │
   ├─> Import Orders (Excel)
   ├─> Import Products (Excel)
   ├─> Import Stock (Excel)
   │
   ▼
📊 Phase 2: Dashboard Review (Online Team)
   │
   ├─> ดูสถานะออเดอร์
   │   ├─> READY (พร้อมรับ)
   │   ├─> LOW_STOCK (สต็อกน้อย)
   │   └─> SHORTAGE (ไม่มีสต็อก)
   │
   ▼
📦 Phase 3: Batch Creation (Online Staff)
   │
   ├─> เลือก Platform (Shopee/TikTok/Lazada)
   ├─> เลือกวันที่
   ├─> สร้าง Batch → Run Number (R1, R2, ...)
   ├─> พิมพ์ Picking List
   │
   ▼
🔍 Phase 4: Picking (Warehouse Picker)
   │
   ├─> Scan Batch QR (รับงาน)
   ├─> Scan SKU QR (หยิบของ)
   │   ├─> ✅ หยิบครบ → Update Progress
   │   └─> ❌ หยิบไม่ครบ → Mark Shortage
   │
   ▼
⚠️ Phase 5: Shortage Management (Online Admin)
   │
   ├─> ดู Shortage Queue
   ├─> จัดการ Shortage
   │   ├─> รอสต็อกเข้า (waiting_stock)
   │   ├─> ยกเลิก (cancelled)
   │   ├─> แทน SKU (replaced)
   │   └─> จัดการเรียบร้อย (resolved)
   │
   ▼
🚚 Phase 6: Dispatch (Warehouse Packer)
   │
   ├─> ตรวจสอบ Progress = 100%
   ├─> Scan Handover (สร้าง Handover Code)
   ├─> Scan Tracking (บันทึก Tracking Number)
   ├─> พิมพ์ใบส่งมอบ
   │
   ▼
✅ Phase 7: Complete
   │
   └─> Batch Status = DISPATCHED
```

---

### 2.2 Role-Based Flows

#### 2.2.1 Online Admin Flow (ผู้ดูแลระบบ)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Online Admin Daily Flow                     │
└─────────────────────────────────────────────────────────────────┘

🌅 เช้า (08:00 - 10:00)
   │
   ├─> 1. Import ข้อมูลประจำวัน
   │   ├─> Import Orders (Excel)
   │   ├─> Import Products (Excel - ถ้ามีสินค้าใหม่)
   │   └─> Import Stock (Excel - อัปเดตสต็อก)
   │
   ├─> 2. ตรวจสอบ Dashboard
   │   ├─> ดูจำนวน Orders ทั้งหมด
   │   ├─> ดู Orders ที่ READY
   │   ├─> ดู Orders ที่ LOW_STOCK
   │   └─> ดู Orders ที่ SHORTAGE
   │
   └─> 3. สร้าง Batch
       ├─> เลือก Platform (Shopee/TikTok/Lazada)
       ├─> เลือกวันที่
       ├─> สร้าง Batch → Run Number
       └─> พิมพ์ Picking List

☀️ กลางวัน (10:00 - 14:00)
   │
   ├─> 4. ติดตาม Progress
   │   ├─> ดู Batch List (Progress %)
   │   ├─> ดู Batch Detail (SKU Progress)
   │   └─> ตรวจสอบ Shortage Queue
   │
   └─> 5. จัดการ Shortage
       ├─> ดู Shortage Queue
       ├─> ตัดสินใจ Action
       │   ├─> รอสต็อกเข้า (waiting_stock)
       │   ├─> ยกเลิก (cancelled)
       │   ├─> แทน SKU (replaced)
       │   └─> จัดการเรียบร้อย (resolved)
       └─> อัปเดตสถานะ

🌆 บ่าย (14:00 - 17:00)
   │
   ├─> 6. Export รายงาน
   │   ├─> Export Dashboard (Excel)
   │   ├─> Export Batch Progress
   │   └─> Export Shortage Queue
   │
   └─> 7. ตรวจสอบ Dispatch
       ├─> ดู Batch ที่ส่งไปแล้ว
       ├─> ตรวจสอบ Tracking Number
       └─> สรุปยอดประจำวัน

⚠️ ถ้าทำผิด Flow จะเกิดอะไร:
- ❌ Import ข้อมูลผิด → Orders ไม่ถูกต้อง, สต็อกผิด
- ❌ ไม่ตรวจสอบ Dashboard → พลาด Orders ที่ต้องเร่งด่วน
- ❌ สร้าง Batch ผิด Platform → Picker หยิบผิดออเดอร์
- ❌ ไม่จัดการ Shortage → Orders ค้างไม่ส่ง, ลูกค้าร้องเรียน
```

---

#### 2.2.2 Online Staff Flow (พนักงานออนไลน์)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Online Staff Daily Flow                      │
└─────────────────────────────────────────────────────────────────┘

🌅 เช้า (08:00 - 10:00)
   │
   ├─> 1. ตรวจสอบ Dashboard
   │   ├─> ดูจำนวน Orders ทั้งหมด
   │   ├─> ดู Orders ที่ READY (พร้อมรับ)
   │   └─> ดู Orders ที่ LOW_STOCK (สต็อกน้อย)
   │
   └─> 2. สร้าง Batch
       ├─> เลือก Platform (Shopee/TikTok/Lazada)
       ├─> เลือกวันที่
       ├─> เลือก Orders ที่ต้องการ
       ├─> สร้าง Batch → Run Number (R1, R2, ...)
       └─> พิมพ์ Picking List

☀️ กลางวัน (10:00 - 14:00)
   │
   ├─> 3. ติดตาม Progress
   │   ├─> ดู Batch List (Progress %)
   │   ├─> ดู Batch Detail (SKU Progress)
   │   └─> ตรวจสอบ Shortage Queue (Read Only)
   │
   └─> 4. Export รายงาน (ถ้าต้องการ)
       ├─> Export Batch Progress
       └─> Export Shortage Queue

🌆 บ่าย (14:00 - 17:00)
   │
   └─> 5. ตรวจสอบ Dispatch
       ├─> ดู Batch ที่ส่งไปแล้ว
       └─> สรุปยอดประจำวัน

⚠️ ถ้าทำผิด Flow จะเกิดอะไร:
- ❌ สร้าง Batch ผิด Platform → Picker หยิบผิดออเดอร์
- ❌ เลือก Orders ผิด → ส่งของผิดลูกค้า
- ❌ ไม่ติดตาม Progress → ไม่รู้ว่า Batch เสร็จหรือยัง
- ❌ ไม่ตรวจสอบ Shortage → Orders ค้างไม่ส่ง

✅ Checklist ก่อนเลิกงาน:
- [ ] ตรวจสอบ Batch ที่สร้างวันนี้ทั้งหมด
- [ ] ดู Progress ของแต่ละ Batch
- [ ] ตรวจสอบ Shortage Queue (ถ้ามี)
- [ ] Export รายงานประจำวัน (ถ้าต้องการ)
```

---

#### 2.2.3 Picker Flow (พนักงานหยิบของ)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Picker Daily Flow                           │
│                  (Scan Batch → Scan SKU → Shortage)             │
└─────────────────────────────────────────────────────────────────┘

🌅 เช้า (08:00 - 10:00)
   │
   └─> 1. รับงาน Batch
       │
       ├─> ไปหน้า /scan/batch
       ├─> สแกน QR Code บนใบงาน Batch
       │   └─> หรือ: เลือกจาก Quick Assign
       └─> ✅ รับงาน Batch สำเร็จ

☀️ กลางวัน (10:00 - 14:00)
   │
   └─> 2. หยิบสินค้า
       │
       ├─> ไปหน้า /scan/sku
       ├─> เลือก Batch ที่รับไว้
       │   └─> หรือ: Quick Assign SKU
       ├─> สแกน SKU QR Code
       ├─> ระบุจำนวนที่หยิบ
       │
       ├─> ✅ สินค้าพอ → บันทึกสำเร็จ
       │
       └─> ❌ สินค้าไม่พอ → บันทึก Shortage
           │
           ├─> ระบุจำนวนที่ขาด
           ├─> เลือกเหตุผล
           │   ├─> สต็อกหมด (out_of_stock)
           │   ├─> สินค้าเสียหาย (damaged)
           │   └─> อื่นๆ
           └─> ⚠️ บันทึกลง Shortage Queue

🌆 บ่าย (14:00 - 17:00)
   │
   ├─> 3. ตรวจสอบ Progress
   │   ├─> ดู Batch Detail
   │   ├─> ✅ SKU ที่หยิบครบ (สีเขียว)
   │   ├─> ⏳ SKU ที่ยังหยิบไม่ครบ (สีเหลือง)
   │   └─> ❌ SKU ที่มี Shortage (สีแดง)
   │
   └─> 4. ทำงานจนครบ
       └─> ✅ Progress 100% → ส่งต่อให้ Packer

⚠️ ถ้าทำผิด Flow จะเกิดอะไร:
- ❌ รับ Batch ผิด → หยิบของผิดออเดอร์
- ❌ สแกน SKU ผิด → ส่งของผิดให้ลูกค้า
- ❌ ระบุจำนวนผิด → ส่งของไม่ครบ/เกิน
- ❌ ไม่ Mark Shortage → Orders ค้างไม่ส่ง, ไม่มีคนจัดการ
- ❌ หยิบไม่ครบแต่ไม่แจ้ง → Packer รอไม่ได้ส่ง

✅ Checklist ก่อนเลิกงาน:
- [ ] ตรวจสอบ Batch ที่รับไว้ทั้งหมด
- [ ] ดู Progress ของแต่ละ Batch
- [ ] ตรวจสอบว่ามี SKU ที่ยังหยิบไม่ครบหรือไม่
- [ ] ตรวจสอบ Shortage ที่บันทึกไว้
- [ ] แจ้ง Admin ถ้ามี Shortage ที่ต้องเร่งด่วน
```

---

#### 2.2.4 Packer Flow (พนักงานแพ็คและส่งมอบ)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Packer Daily Flow                           │
│            (Scan Handover → Tracking → Dispatch)                │
└─────────────────────────────────────────────────────────────────┘

🌅 เช้า (08:00 - 10:00)
   │
   └─> 1. ดู Batch ที่พร้อมส่ง
       │
       ├─> ไปหน้า /batch/list
       ├─> กรอง: Progress 100%
       └─> เลือก Batch ที่จะส่งมอบ

☀️ กลางวัน (10:00 - 14:00)
   │
   ├─> 2. แพ็คสินค้า
   │   ├─> แพ็คสินค้าตาม Batch
   │   ├─> ติดสติกเกอร์/เลข Tracking
   │   └─> ✅ พร้อมส่งมอบ
   │
   └─> 3. สแกนส่งมอบให้ขนส่ง
       │
       ├─> ไปหน้า /scan/handover
       ├─> สแกน Batch QR Code
       ├─> ระบุจำนวนกล่อง (ถ้ามี)
       └─> ✅ สร้าง Handover Code อัตโนมัติ
           └─> Format: BH-YYYYMMDD-NNN

🌆 บ่าย (14:00 - 17:00)
   │
   ├─> 4. บันทึก Tracking Number (Optional)
   │   ├─> ไปหน้า /scan/tracking
   │   ├─> สแกน Order QR Code
   │   ├─> ระบุ Tracking Number
   │   └─> ✅ บันทึกสำเร็จ
   │
   ├─> 5. พิมพ์ใบส่งมอบ
   │   ├─> พิมพ์ใบส่งมอบ (Handover Slip)
   │   ├─> มี QR Code สำหรับสแกนรับ
   │   └─> แนบกับสินค้า
   │
   └─> 6. ส่งมอบให้ขนส่ง
       └─> ✅ Batch Status = DISPATCHED

⚠️ ถ้าทำผิด Flow จะเกิดอะไร:
- ❌ แพ็คผิด Batch → ส่งของผิดลูกค้า
- ❌ ไม่สแกน Handover → ไม่มีหลักฐานการส่งมอบ
- ❌ บันทึก Tracking ผิด → ลูกค้าติดตามพัสดุไม่ได้
- ❌ ไม่พิมพ์ใบส่งมอบ → ขนส่งไม่รับของ
- ❌ ส่งมอบก่อน Progress 100% → ส่งของไม่ครบ

✅ Checklist ก่อนเลิกงาน:
- [ ] ตรวจสอบ Batch ที่ส่งไปแล้วทั้งหมด
- [ ] ตรวจสอบ Handover Code ที่สร้างไว้
- [ ] ตรวจสอบ Tracking Number ที่บันทึกไว้
- [ ] ตรวจสอบใบส่งมอบที่พิมพ์ไว้
- [ ] สรุปยอดส่งประจำวัน
```

---

### 2.3 Special Flows

#### 2.3.1 Shortage Management Flow (แบบละเอียดสุด)

```
┌─────────────────────────────────────────────────────────────────┐
│                  Shortage Management Flow                        │
│              (From Detection to Resolution)                      │
└─────────────────────────────────────────────────────────────────┘

📍 Step 1: Shortage Detection (Picker)
   │
   ├─> Picker หยิบสินค้า
   ├─> พบว่าสต็อกไม่พอ
   │   ├─> ต้องการ: 10 ชิ้น
   │   └─> มีจริง: 5 ชิ้น
   │
   └─> บันทึก Shortage
       ├─> ระบุจำนวนที่ขาด: 5 ชิ้น
       ├─> เลือกเหตุผล:
       │   ├─> สต็อกหมด (out_of_stock)
       │   ├─> สินค้าเสียหาย (damaged)
       │   ├─> สินค้าหาไม่เจอ (not_found)
       │   └─> อื่นๆ (other)
       └─> ✅ บันทึกลง Shortage Queue

📍 Step 2: Shortage Queue (Online Team)
   │
   ├─> ไปหน้า /shortage/queue
   ├─> ดูรายการ Shortage ทั้งหมด
   │   ├─> Order ID
   │   ├─> SKU
   │   ├─> จำนวนที่ขาด
   │   ├─> เหตุผล
   │   ├─> สถานะ (pending/waiting_stock/cancelled/replaced/resolved)
   │   └─> วันที่บันทึก
   │
   └─> เรียงตาม Priority
       ├─> High: Orders ที่ใกล้ SLA
       ├─> Medium: Orders ปกติ
       └─> Low: Orders ที่ยังมีเวลา

📍 Step 3: Shortage Analysis (Online Admin)
   │
   ├─> วิเคราะห์สาเหตุ
   │   ├─> สต็อกหมดจริงหรือไม่?
   │   ├─> สินค้าเสียหายหรือไม่?
   │   ├─> มีสินค้าทดแทนหรือไม่?
   │   └─> ลูกค้ายอมรอหรือไม่?
   │
   └─> ตัดสินใจ Action

📍 Step 4: Shortage Resolution (Online Admin)
   │
   ├─> Action 1: รอสต็อกเข้า (waiting_stock)
   │   ├─> เปลี่ยนสถานะเป็น "waiting_stock"
   │   ├─> ระบุวันที่คาดว่าสต็อกจะเข้า
   │   ├─> แจ้งลูกค้า (ถ้าจำเป็น)
   │   └─> ติดตามสต็อก
   │
   ├─> Action 2: ยกเลิก (cancelled)
   │   ├─> เปลี่ยนสถานะเป็น "cancelled"
   │   ├─> ระบุเหตุผล
   │   ├─> แจ้งลูกค้า
   │   └─> คืนเงิน (ถ้าจำเป็น)
   │
   ├─> Action 3: แทน SKU (replaced)
   │   ├─> เปลี่ยนสถานะเป็น "replaced"
   │   ├─> ระบุ SKU ที่แทน
   │   ├─> อัปเดต Order
   │   └─> แจ้งลูกค้า
   │
   └─> Action 4: จัดการเรียบร้อย (resolved)
       ├─> เปลี่ยนสถานะเป็น "resolved"
       ├─> ระบุวิธีการจัดการ
       └─> ปิด Shortage

📍 Step 5: Follow-up (Online Team)
   │
   ├─> ติดตาม Shortage ที่ waiting_stock
   │   ├─> ตรวจสอบสต็อกเข้าหรือยัง
   │   └─> อัปเดตสถานะ
   │
   ├─> ติดตาม Shortage ที่ replaced
   │   ├─> ตรวจสอบ SKU ทดแทนส่งหรือยัง
   │   └─> อัปเดตสถานะ
   │
   └─> สรุปรายงาน Shortage ประจำวัน

⚠️ ถ้าไม่จัดการทัน จะเกิดอะไร:
- ❌ Orders ค้างไม่ส่ง → ลูกค้าร้องเรียน
- ❌ เกิน SLA → ถูกปรับจาก Platform
- ❌ ลูกค้ายกเลิกออเดอร์ → สูญเสียรายได้
- ❌ ชื่อเสียงร้านเสียหาย → ยอดขายลดลง
```

---

#### 2.3.2 Import Order Flow (ทุกขั้นตอน)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Import Order Flow                             │
│              (From Excel to Database)                            │
└─────────────────────────────────────────────────────────────────┘

📍 Step 1: Prepare Excel File
   │
   ├─> ดาวน์โหลดออเดอร์จาก Platform
   │   ├─> Shopee Seller Center
   │   ├─> TikTok Shop Seller Center
   │   └─> Lazada Seller Center
   │
   ├─> ตรวจสอบ Format Excel
   │   ├─> มีคอลัมน์ที่จำเป็น:
   │   │   ├─> order_id (เลขออเดอร์)
   │   │   ├─> platform (Shopee/TikTok/Lazada)
   │   │   ├─> shop_name (ชื่อร้าน)
   │   │   ├─> sku (รหัสสินค้า)
   │   │   ├─> qty (จำนวน)
   │   │   ├─> item_name (ชื่อสินค้า)
   │   │   ├─> order_time (วันที่สั่งซื้อ)
   │   │   └─> logistic_type (ขนส่ง)
   │   └─> ตรวจสอบข้อมูลไม่มีช่องว่าง
   │
   └─> บันทึกไฟล์ Excel

📍 Step 2: Import to System (Online Admin)
   │
   ├─> ไปหน้า /import/orders
   ├─> เลือกไฟล์ Excel
   ├─> กด "Import"
   │
   └─> ระบบประมวลผล
       ├─> อ่านข้อมูลจาก Excel
       ├─> Validate ข้อมูล
       │   ├─> ตรวจสอบ order_id ซ้ำหรือไม่
       │   ├─> ตรวจสอบ SKU มีในระบบหรือไม่
       │   ├─> ตรวจสอบ Shop มีในระบบหรือไม่
       │   └─> ตรวจสอบ Format วันที่ถูกต้องหรือไม่
       │
       ├─> บันทึกลง Database
       │   ├─> สร้าง OrderLine ใหม่
       │   ├─> อัปเดต Stock
       │   └─> คำนวณ SLA Due Date
       │
       └─> แสดงผลลัพธ์
           ├─> ✅ Import สำเร็จ: X รายการ
           ├─> ⚠️ Import ไม่สำเร็จ: Y รายการ
           └─> ❌ Error: รายละเอียด

📍 Step 3: Auto-Classification
   │
   └─> ระบบจัดหมวดหมู่อัตโนมัติ
       ├─> READY (พร้อมรับ)
       │   └─> Stock >= Qty
       │
       ├─> LOW_STOCK (สต็อกน้อย)
       │   └─> 0 < Stock < Qty AND Stock <= 3
       │
       └─> SHORTAGE (ไม่มีสต็อก)
           └─> Stock = 0

📍 Step 4: Verification (Online Admin)
   │
   ├─> ไปหน้า Dashboard
   ├─> ตรวจสอบจำนวน Orders
   │   ├─> Total Orders
   │   ├─> READY Orders
   │   ├─> LOW_STOCK Orders
   │   └─> SHORTAGE Orders
   │
   ├─> ตรวจสอบ SLA Due Date
   │   ├─> Shopee: +3 วัน
   │   ├─> TikTok: +2 วัน
   │   └─> Lazada: +3 วัน
   │
   └─> ✅ ยืนยันข้อมูลถูกต้อง

⚠️ ถ้า Import ผิด จะเกิดอะไร:
- ❌ order_id ซ้ำ → Orders ทับกัน, ข้อมูลผิด
- ❌ SKU ผิด → หยิบของผิด, ส่งของผิดลูกค้า
- ❌ Shop ผิด → สต็อกผิด, หยิบของผิดร้าน
- ❌ Qty ผิด → ส่งของไม่ครบ/เกิน
- ❌ Platform ผิด → SLA ผิด, ถูกปรับ
- ❌ order_time ผิด → SLA ผิด, ส่งของช้า

✅ Best Practices:
- ✅ Import ทีละ Platform (ไม่ผสม)
- ✅ ตรวจสอบ Excel ก่อน Import
- ✅ Import เช้าๆ (ก่อน 10:00)
- ✅ Backup ข้อมูลก่อน Import
- ✅ ตรวจสอบ Dashboard หลัง Import
```

---

## 3. Daily Operation Guides

### 3.1 Online Team Daily Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  Online Team Daily Checklist                     │
└─────────────────────────────────────────────────────────────────┘

⏰ 08:00 - 09:00 | เช้า - Import & Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 1. เปิดระบบ VNIX WMS
[ ] 2. Login เข้าสู่ระบบ
[ ] 3. Import Orders (Excel)
    └─> ตรวจสอบ Format ก่อน Import
[ ] 4. Import Products (ถ้ามีสินค้าใหม่)
[ ] 5. Import Stock (อัปเดตสต็อก)
[ ] 6. ตรวจสอบ Dashboard
    ├─> Total Orders
    ├─> READY Orders
    ├─> LOW_STOCK Orders
    └─> SHORTAGE Orders

⏰ 09:00 - 10:00 | เช้า - Batch Creation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 7. สร้าง Batch สำหรับ Shopee
    ├─> เลือก Platform: Shopee
    ├─> เลือกวันที่
    ├─> เลือก Orders ที่ READY
    └─> สร้าง Batch → Run Number (R1)
[ ] 8. สร้าง Batch สำหรับ TikTok
    └─> Run Number (R1)
[ ] 9. สร้าง Batch สำหรับ Lazada
    └─> Run Number (R1)
[ ] 10. พิมพ์ Picking List ทุก Batch
[ ] 11. ส่งใบงานให้ Picker

⏰ 10:00 - 12:00 | กลางวัน - Progress Monitoring
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 12. ติดตาม Batch Progress
    ├─> ดู Batch List
    ├─> ตรวจสอบ Progress %
    └─> ดู Batch Detail (SKU Progress)
[ ] 13. ตรวจสอบ Shortage Queue
    ├─> ดูรายการ Shortage
    ├─> เรียงตาม Priority
    └─> วางแผนจัดการ

⏰ 12:00 - 13:00 | พักเที่ยง
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 14. พักเที่ยง

⏰ 13:00 - 15:00 | บ่าย - Shortage Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 15. จัดการ Shortage (Admin Only)
    ├─> ดู Shortage Queue
    ├─> วิเคราะห์สาเหตุ
    ├─> ตัดสินใจ Action
    │   ├─> รอสต็อกเข้า (waiting_stock)
    │   ├─> ยกเลิก (cancelled)
    │   ├─> แทน SKU (replaced)
    │   └─> จัดการเรียบร้อย (resolved)
    └─> อัปเดตสถานะ
[ ] 16. แจ้งลูกค้า (ถ้าจำเป็น)
[ ] 17. ติดตามสต็อก (ถ้ารอสต็อกเข้า)

⏰ 15:00 - 17:00 | บ่าย - Dispatch & Reporting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 18. ตรวจสอบ Dispatch
    ├─> ดู Batch ที่ส่งไปแล้ว
    ├─> ตรวจสอบ Handover Code
    └─> ตรวจสอบ Tracking Number
[ ] 19. Export รายงาน
    ├─> Export Dashboard (Excel)
    ├─> Export Batch Progress
    └─> Export Shortage Queue
[ ] 20. สรุปยอดประจำวัน
    ├─> Orders ทั้งหมด
    ├─> Orders ที่ส่งไปแล้ว
    ├─> Orders ที่ค้าง
    └─> Shortage ที่ยังไม่จัดการ

⏰ 17:00 | เลิกงาน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 21. Logout ออกจากระบบ
```

---

### 3.2 Picker Daily Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Picker Daily Checklist                        │
└─────────────────────────────────────────────────────────────────┘

⏰ 08:00 - 09:00 | เช้า - Setup & Batch Assignment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 1. เปิดระบบ VNIX WMS (Mobile)
[ ] 2. Login เข้าสู่ระบบ
[ ] 3. รับใบงาน Batch จาก Online Team
[ ] 4. ไปหน้า /scan/batch
[ ] 5. สแกน QR Code บนใบงาน Batch
    └─> หรือ: เลือกจาก Quick Assign
[ ] 6. ✅ รับงาน Batch สำเร็จ
[ ] 7. ตรวจสอบรายการสินค้าใน Batch

⏰ 09:00 - 12:00 | เช้า - Picking (Round 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 8. ไปหน้า /scan/sku
[ ] 9. เลือก Batch ที่รับไว้
[ ] 10. เริ่มหยิบสินค้า
    ├─> สแกน SKU QR Code
    ├─> ตรวจสอบชื่อสินค้า
    ├─> ตรวจสอบจำนวนที่ต้องหยิบ
    ├─> หยิบสินค้า
    └─> ระบุจำนวนที่หยิบได้

[ ] 11. กรณีหยิบครบ (Happy Path)
    ├─> ระบุจำนวน = จำนวนที่ต้องการ
    ├─> กด "บันทึก"
    └─> ✅ บันทึกสำเร็จ

[ ] 12. กรณีหยิบไม่ครบ (Shortage Path)
    ├─> ระบุจำนวนที่หยิบได้
    ├─> เลือกเหตุผล:
    │   ├─> สต็อกหมด (out_of_stock)
    │   ├─> สินค้าเสียหาย (damaged)
    │   ├─> สินค้าหาไม่เจอ (not_found)
    │   └─> อื่นๆ (other)
    ├─> กด "บันทึก Shortage"
    └─> ⚠️ บันทึกลง Shortage Queue

[ ] 13. ทำซ้ำจนครบทุก SKU ใน Batch

⏰ 12:00 - 13:00 | พักเที่ยง
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 14. พักเที่ยง

⏰ 13:00 - 15:00 | บ่าย - Picking (Round 2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 15. ตรวจสอบ Progress
    ├─> ดู Batch Detail
    ├─> ✅ SKU ที่หยิบครบ (สีเขียว)
    ├─> ⏳ SKU ที่ยังหยิบไม่ครบ (สีเหลือง)
    └─> ❌ SKU ที่มี Shortage (สีแดง)

[ ] 16. หยิบ SKU ที่ยังไม่ครบ (ถ้ามี)
[ ] 17. ตรวจสอบ Shortage ที่บันทึกไว้
[ ] 18. แจ้ง Admin ถ้ามี Shortage ที่ต้องเร่งด่วน

⏰ 15:00 - 17:00 | บ่าย - Final Check & Handover
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 19. ตรวจสอบ Progress = 100% (ถ้าเป็นไปได้)
[ ] 20. ส่งต่อให้ Packer (ถ้า Progress = 100%)
[ ] 21. รับ Batch ใหม่ (ถ้ามี)
[ ] 22. สรุปงานประจำวัน
    ├─> Batch ที่รับทั้งหมด
    ├─> Batch ที่เสร็จแล้ว
    ├─> Batch ที่ยังไม่เสร็จ
    └─> Shortage ที่บันทึกไว้

⏰ 17:00 | เลิกงาน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 23. Logout ออกจากระบบ

⚠️ สิ่งที่ต้องระวัง:
- ❌ อย่าสแกน SKU ผิด → ส่งของผิดลูกค้า
- ❌ อย่าระบุจำนวนผิด → ส่งของไม่ครบ/เกิน
- ❌ อย่าลืม Mark Shortage → Orders ค้างไม่ส่ง
- ❌ อย่าหยิบของผิด Batch → ส่งของผิดออเดอร์
```

---

### 3.3 Packer Daily Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Packer Daily Checklist                        │
└─────────────────────────────────────────────────────────────────┘

⏰ 08:00 - 09:00 | เช้า - Setup & Batch Review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 1. เปิดระบบ VNIX WMS (Mobile)
[ ] 2. Login เข้าสู่ระบบ
[ ] 3. ไปหน้า /batch/list
[ ] 4. กรอง: Progress 100%
[ ] 5. ดู Batch ที่พร้อมส่ง
[ ] 6. เลือก Batch ที่จะแพ็ควันนี้

⏰ 09:00 - 12:00 | เช้า - Packing (Round 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 7. เตรียมอุปกรณ์แพ็ค
    ├─> กล่อง
    ├─> เทป
    ├─> สติกเกอร์
    └─> ใบปะหน้า

[ ] 8. แพ็คสินค้าตาม Batch
    ├─> ตรวจสอบรายการสินค้า
    ├─> ตรวจสอบจำนวน
    ├─> แพ็คสินค้าลงกล่อง
    ├─> ติดสติกเกอร์
    └─> ติดใบปะหน้า

[ ] 9. ตรวจสอบความถูกต้อง
    ├─> Order ID ถูกต้อง
    ├─> SKU ครบถ้วน
    ├─> จำนวนถูกต้อง
    └─> ใบปะหน้าถูกต้อง

⏰ 12:00 - 13:00 | พักเที่ยง
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 10. พักเที่ยง

⏰ 13:00 - 15:00 | บ่าย - Handover Scanning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 11. ไปหน้า /scan/handover
[ ] 12. สแกน Batch QR Code
[ ] 13. ระบุจำนวนกล่อง (ถ้ามี)
[ ] 14. กด "สร้าง Handover Code"
[ ] 15. ✅ สร้าง Handover Code สำเร็จ
    └─> Format: BH-YYYYMMDD-NNN

[ ] 16. บันทึก Tracking Number (Optional)
    ├─> ไปหน้า /scan/tracking
    ├─> สแกน Order QR Code
    ├─> ระบุ Tracking Number
    └─> ✅ บันทึกสำเร็จ

⏰ 15:00 - 17:00 | บ่าย - Printing & Dispatch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 17. พิมพ์ใบส่งมอบ
    ├─> ไปหน้า /batch/<id>/print_handover
    ├─> พิมพ์ใบส่งมอบ (Handover Slip)
    ├─> ตรวจสอบ QR Code
    └─> แนบกับสินค้า

[ ] 18. ส่งมอบให้ขนส่ง
    ├─> เรียกขนส่งมารับ
    ├─> ส่งมอบสินค้า + ใบส่งมอบ
    ├─> ให้ขนส่งสแกน QR Code รับ
    └─> ✅ Batch Status = DISPATCHED

[ ] 19. สรุปงานประจำวัน
    ├─> Batch ที่แพ็คทั้งหมด
    ├─> Batch ที่ส่งไปแล้ว
    ├─> Handover Code ที่สร้างไว้
    └─> Tracking Number ที่บันทึกไว้

⏰ 17:00 | เลิกงาน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] 20. Logout ออกจากระบบ

⚠️ สิ่งที่ต้องระวัง:
- ❌ อย่าแพ็คผิด Batch → ส่งของผิดลูกค้า
- ❌ อย่าลืมสแกน Handover → ไม่มีหลักฐานการส่งมอบ
- ❌ อย่าบันทึก Tracking ผิด → ลูกค้าติดตามพัสดุไม่ได้
- ❌ อย่าส่งมอบก่อน Progress 100% → ส่งของไม่ครบ
```

---

## 4. Training Manuals

### 4.1 Shortage Controller Training (สำหรับหัวหน้าคลัง)

```
┌─────────────────────────────────────────────────────────────────┐
│              Shortage Controller Training Manual                 │
│                  (Complete Guide)                                │
└─────────────────────────────────────────────────────────────────┘

📚 Module 1: Understanding Shortage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1.1 What is Shortage?
   - Shortage = สินค้าไม่พอส่ง
   - เกิดจาก: สต็อกหมด, สินค้าเสียหาย, หาไม่เจอ
   - ผลกระทบ: Orders ค้าง, ลูกค้าร้องเรียน, ถูกปรับ

1.2 Shortage Types
   - Partial Shortage: หยิบได้บางส่วน (เช่น ต้องการ 10, มี 5)
   - Complete Shortage: หยิบไม่ได้เลย (เช่น ต้องการ 10, มี 0)

1.3 Shortage Status
   - pending: รอจัดการ (ใหม่)
   - waiting_stock: รอสต็อกเข้า
   - cancelled: ยกเลิกแล้ว
   - replaced: แทน SKU แล้ว
   - resolved: จัดการเรียบร้อย

📚 Module 2: Shortage Detection & Recording
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2.1 How Shortage is Detected
   - Picker หยิบสินค้า
   - พบว่าสต็อกไม่พอ
   - บันทึก Shortage ในระบบ

2.2 Shortage Information
   - Order ID: เลขออเดอร์
   - SKU: รหัสสินค้า
   - Qty Required: จำนวนที่ต้องการ
   - Qty Picked: จำนวนที่หยิบได้
   - Qty Shortage: จำนวนที่ขาด
   - Reason: เหตุผล (out_of_stock/damaged/not_found/other)
   - Created At: วันที่บันทึก

2.3 Shortage Priority
   - High: Orders ที่ใกล้ SLA (< 1 วัน)
   - Medium: Orders ปกติ (1-2 วัน)
   - Low: Orders ที่ยังมีเวลา (> 2 วัน)

📚 Module 3: Shortage Management Actions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3.1 Action 1: รอสต็อกเข้า (waiting_stock)
   ✅ เมื่อไหร่ใช้:
   - สต็อกจะเข้าในอีก 1-2 วัน
   - ลูกค้ายอมรอได้
   - ยังไม่เกิน SLA

   📝 ขั้นตอน:
   1. ตรวจสอบว่าสต็อกจะเข้าเมื่อไหร่
   2. เปลี่ยนสถานะเป็น "waiting_stock"
   3. ระบุวันที่คาดว่าสต็อกจะเข้า
   4. แจ้งลูกค้า (ถ้าจำเป็น)
   5. ติดตามสต็อก

   ⚠️ ถ้าไม่จัดการทัน:
   - เกิน SLA → ถูกปรับ
   - ลูกค้ายกเลิกออเดอร์

3.2 Action 2: ยกเลิก (cancelled)
   ✅ เมื่อไหร่ใช้:
   - สต็อกไม่มีเลย
   - ไม่มีสินค้าทดแทน
   - ลูกค้าไม่ยอมรอ

   📝 ขั้นตอน:
   1. เปลี่ยนสถานะเป็น "cancelled"
   2. ระบุเหตุผล
   3. แจ้งลูกค้า
   4. คืนเงิน (ถ้าจำเป็น)
   5. ปิด Shortage

   ⚠️ ถ้าไม่จัดการทัน:
   - ลูกค้าร้องเรียน
   - ชื่อเสียงร้านเสียหาย

3.3 Action 3: แทน SKU (replaced)
   ✅ เมื่อไหร่ใช้:
   - มีสินค้าทดแทน
   - ลูกค้ายอมรับ
   - ราคาใกล้เคียงกัน

   📝 ขั้นตอน:
   1. หาสินค้าทดแทน
   2. เปลี่ยนสถานะเป็น "replaced"
   3. ระบุ SKU ที่แทน
   4. อัปเดต Order
   5. แจ้งลูกค้า
   6. ส่งสินค้าทดแทน

   ⚠️ ถ้าไม่จัดการทัน:
   - ส่งของผิด
   - ลูกค้าไม่พอใจ

3.4 Action 4: จัดการเรียบร้อย (resolved)
   ✅ เมื่อไหร่ใช้:
   - จัดการเสร็จแล้ว
   - ลูกค้าพอใจ
   - ไม่มีปัญหาแล้ว

   📝 ขั้นตอน:
   1. เปลี่ยนสถานะเป็น "resolved"
   2. ระบุวิธีการจัดการ
   3. ปิด Shortage

📚 Module 4: Shortage Scenarios & Solutions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scenario 1: สต็อกหมด แต่จะเข้าพรุ่งนี้
   ✅ Solution: waiting_stock
   📝 Action:
   - เปลี่ยนสถานะเป็น "waiting_stock"
   - ระบุวันที่: พรุ่งนี้
   - แจ้งลูกค้า: "สินค้าจะเข้าพรุ่งนี้ ส่งได้ภายใน 2 วัน"
   - ติดตามสต็อก

Scenario 2: สต็อกหมด ไม่มีเข้าเลย
   ✅ Solution: cancelled
   📝 Action:
   - เปลี่ยนสถานะเป็น "cancelled"
   - แจ้งลูกค้า: "ขออภัย สินค้าหมด ขอคืนเงิน"
   - คืนเงิน

Scenario 3: สต็อกหมด แต่มีสินค้าทดแทน
   ✅ Solution: replaced
   📝 Action:
   - หาสินค้าทดแทน (SKU ใกล้เคียง)
   - แจ้งลูกค้า: "สินค้าหมด ขอเปลี่ยนเป็น SKU XXX ได้ไหม"
   - ถ้าลูกค้าตกลง → เปลี่ยนสถานะเป็น "replaced"
   - ส่งสินค้าทดแทน

Scenario 4: สินค้าเสียหาย
   ✅ Solution: cancelled หรือ replaced
   📝 Action:
   - ตรวจสอบว่ามีสินค้าดีอยู่หรือไม่
   - ถ้ามี → แทนด้วยสินค้าดี
   - ถ้าไม่มี → ยกเลิก + คืนเงิน

Scenario 5: หาสินค้าไม่เจอ
   ✅ Solution: waiting_stock หรือ cancelled
   📝 Action:
   - ค้นหาสินค้าอีกครั้ง
   - ถ้าเจอ → หยิบเพิ่ม
   - ถ้าไม่เจอ → ยกเลิก

⚠️ ถ้าไม่จัดการทัน จะเกิดอะไร:
- ❌ Orders ค้างไม่ส่ง → ลูกค้าร้องเรียน
- ❌ เกิน SLA → ถูกปรับจาก Platform
- ❌ ลูกค้ายกเลิกออเดอร์ → สูญเสียรายได้
- ❌ ชื่อเสียงร้านเสียหาย → ยอดขายลดลง
```

---

### 4.2 Online Import Training (สำหรับหัวหน้าออนไลน์)

```
┌─────────────────────────────────────────────────────────────────┐
│              Online Import Training Manual                       │
│                  (Complete Guide)                                │
└─────────────────────────────────────────────────────────────────┘

📚 Module 1: Understanding Import Process
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1.1 What is Import?
   - Import = นำเข้าข้อมูลจาก Excel เข้าระบบ
   - ประเภท:
     ├─> Import Orders (ออเดอร์)
     ├─> Import Products (สินค้า)
     ├─> Import Stock (สต็อก)
     └─> Import Sales (ข้อมูลขาย)

1.2 Why Import?
   - ประหยัดเวลา (ไม่ต้องพิมพ์ทีละรายการ)
   - ลดข้อผิดพลาด (ไม่ต้องพิมพ์เอง)
   - อัปเดตข้อมูลเป็นชุด

1.3 Import Frequency
   - Orders: ทุกวัน (เช้า 08:00-09:00)
   - Products: เมื่อมีสินค้าใหม่
   - Stock: ทุกวัน (เช้า 08:00-09:00)
   - Sales: ตามต้องการ

📚 Module 2: Import Orders (Step-by-Step)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: ดาวน์โหลดออเดอร์จาก Platform
   ├─> Shopee Seller Center
   │   └─> My Sales → Export Orders
   ├─> TikTok Shop Seller Center
   │   └─> Orders → Export
   └─> Lazada Seller Center
       └─> Orders → Export

Step 2: ตรวจสอบ Format Excel
   ✅ คอลัมน์ที่จำเป็น:
   - order_id: เลขออเดอร์ (ห้ามซ้ำ)
   - platform: Shopee/TikTok/Lazada
   - shop_name: ชื่อร้าน
   - sku: รหัสสินค้า
   - qty: จำนวน (ต้องเป็นตัวเลข)
   - item_name: ชื่อสินค้า
   - order_time: วันที่สั่งซื้อ (Format: YYYY-MM-DD HH:MM:SS)
   - logistic_type: ขนส่ง (SPX/Flash/LEX/J&T)

   ⚠️ Validation Rules:
   - order_id ห้ามว่าง
   - platform ต้องเป็น Shopee/TikTok/Lazada
   - sku ต้องมีในระบบ
   - qty ต้องเป็นตัวเลข > 0
   - order_time ต้องเป็น Format ที่ถูกต้อง

Step 3: Import to System
   1. Login เข้าระบบ
   2. ไปหน้า /import/orders
   3. เลือกไฟล์ Excel
   4. กด "Import"
   5. รอระบบประมวลผล

Step 4: ตรวจสอบผลลัพธ์
   ✅ Import สำเร็จ:
   - แสดงจำนวนรายการที่ Import สำเร็จ
   - ไปหน้า Dashboard ตรวจสอบ

   ❌ Import ไม่สำเร็จ:
   - แสดง Error Message
   - ตรวจสอบข้อมูลใน Excel
   - แก้ไขและ Import ใหม่

Step 5: Verification
   1. ไปหน้า Dashboard
   2. ตรวจสอบจำนวน Orders
   3. ตรวจสอบ SLA Due Date
   4. ตรวจสอบ Order Status
      ├─> READY (พร้อมรับ)
      ├─> LOW_STOCK (สต็อกน้อย)
      └─> SHORTAGE (ไม่มีสต็อก)

📚 Module 3: Common Errors & Solutions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Error 1: "order_id ซ้ำ"
   ❌ สาเหตุ: มี order_id ซ้ำในระบบ
   ✅ วิธีแก้:
   - ตรวจสอบว่า Import ไปแล้วหรือยัง
   - ถ้า Import ไปแล้ว → ไม่ต้อง Import ซ้ำ
   - ถ้ายัง → ลบ order_id เก่าออก แล้ว Import ใหม่

Error 2: "SKU ไม่พบในระบบ"
   ❌ สาเหตุ: SKU ยังไม่มีในระบบ
   ✅ วิธีแก้:
   - Import Products ก่อน
   - แล้ว Import Orders ใหม่

Error 3: "Shop ไม่พบในระบบ"
   ❌ สาเหตุ: Shop ยังไม่มีในระบบ
   ✅ วิธีแก้:
   - สร้าง Shop ในระบบก่อน
   - แล้ว Import Orders ใหม่

Error 4: "qty ต้องเป็นตัวเลข"
   ❌ สาเหตุ: qty เป็นข้อความ (เช่น "10 ชิ้น")
   ✅ วิธีแก้:
   - แก้ไข qty ให้เป็นตัวเลขเท่านั้น (เช่น 10)
   - Import ใหม่

Error 5: "order_time Format ผิด"
   ❌ สาเหตุ: order_time ไม่ใช่ Format YYYY-MM-DD HH:MM:SS
   ✅ วิธีแก้:
   - แก้ไข Format ให้ถูกต้อง
   - ตัวอย่าง: 2024-11-18 10:30:00
   - Import ใหม่

⚠️ ถ้า Import ผิด จะเกิดอะไร:
- ❌ order_id ซ้ำ → Orders ทับกัน, ข้อมูลผิด
- ❌ SKU ผิด → หยิบของผิด, ส่งของผิดลูกค้า
- ❌ Shop ผิด → สต็อกผิด, หยิบของผิดร้าน
- ❌ Qty ผิด → ส่งของไม่ครบ/เกิน
- ❌ Platform ผิด → SLA ผิด, ถูกปรับ
- ❌ order_time ผิด → SLA ผิด, ส่งของช้า

✅ Best Practices:
- ✅ Import ทีละ Platform (ไม่ผสม)
- ✅ ตรวจสอบ Excel ก่อน Import
- ✅ Import เช้าๆ (ก่อน 10:00)
- ✅ Backup ข้อมูลก่อน Import
- ✅ ตรวจสอบ Dashboard หลัง Import
- ✅ ทดสอบ Import ด้วยข้อมูลน้อยๆ ก่อน
```

---

## 5. Risk Assessment & Mitigation

### 5.1 รายการจุดเสี่ยง (Risk List)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Risk Assessment Matrix                      │
└─────────────────────────────────────────────────────────────────┘

Risk ID | จุดเสี่ยง | ผลกระทบ | โอกาส | Priority | แผนป้องกัน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

R01 | Import ข้อมูลผิด | สูง | กลาง | HIGH | Validation + Training
R02 | สแกน SKU ผิด | สูง | กลาง | HIGH | QR Code + Double Check
R03 | Shortage ไม่จัดการทัน | สูง | สูง | HIGH | Priority Queue + Alert
R04 | Batch ผิด Platform | กลาง | ต่ำ | MEDIUM | UI Warning + Confirmation
R05 | Progress คำนวณผิด | กลาง | ต่ำ | MEDIUM | Unit Test + Monitoring
R06 | Handover Code ซ้ำ | ต่ำ | ต่ำ | LOW | Auto-increment + Unique Index
R07 | Tracking Number ผิด | กลาง | กลาง | MEDIUM | Manual Check + Validation
R08 | สต็อกไม่ตรงกับจริง | สูง | กลาง | HIGH | Daily Stock Check
R09 | SLA คำนวณผิด | สูง | ต่ำ | HIGH | Unit Test + Monitoring
R10 | Picker หยิบผิด Batch | กลาง | กลาง | MEDIUM | QR Code + Confirmation
R11 | Packer แพ็คผิด Order | สูง | ต่ำ | HIGH | Double Check + QR Code
R12 | ระบบล่ม | สูง | ต่ำ | HIGH | Backup + Monitoring
R13 | ข้อมูลสูญหาย | สูง | ต่ำ | HIGH | Daily Backup + Audit Log
R14 | User ใช้งานผิด Role | กลาง | กลาง | MEDIUM | Permission + Training
R15 | Batch Lock ไม่ทำงาน | กลาง | ต่ำ | MEDIUM | Unit Test + Monitoring
```

---

### 5.2 แผนพัฒนาระยะสั้น (Short-term Roadmap)

```
┌─────────────────────────────────────────────────────────────────┐
│                  Short-term Roadmap (1-3 เดือน)                 │
└─────────────────────────────────────────────────────────────────┘

Phase 1: Role-Based Access Control (1 เดือน)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] เพิ่ม department และ role ใน User model
[ ] สร้าง Permission Decorator
[ ] ซ่อน/แสดงเมนูตาม Role
[ ] ทดสอบ Permission ทุก Endpoint
[ ] Training พนักงาน

Phase 2: Shortage Management Enhancement (1 เดือน)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] เพิ่ม Priority System
[ ] เพิ่ม Alert System (Email/Line)
[ ] เพิ่ม Shortage Report
[ ] เพิ่ม Shortage Analytics
[ ] Training หัวหน้าคลัง

Phase 3: Mobile Optimization (1 เดือน)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] ปรับ UI ให้เหมาะกับ Mobile
[ ] เพิ่ม Touch-friendly Buttons
[ ] เพิ่ม Offline Mode (ถ้าเป็นไปได้)
[ ] ทดสอบบน Mobile Device
[ ] Training พนักงานคลัง
```

---

### 5.3 แผนพัฒนาระยะยาว (Long-term Roadmap)

```
┌─────────────────────────────────────────────────────────────────┐
│                  Long-term Roadmap (3-12 เดือน)                 │
└─────────────────────────────────────────────────────────────────┘

Phase 4: Advanced Analytics (3-6 เดือน)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Dashboard แบบ Real-time
[ ] Picker Performance Report
[ ] Shortage Trend Analysis
[ ] SLA Compliance Report
[ ] Carrier Performance Report

Phase 5: Automation (6-9 เดือน)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Auto Batch Creation (AI-based)
[ ] Auto Shortage Resolution (Rule-based)
[ ] Auto Stock Replenishment Alert
[ ] Auto SLA Alert
[ ] Auto Carrier Selection

Phase 6: Integration (9-12 เดือน)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] API Integration กับ Platform (Shopee/TikTok/Lazada)
[ ] API Integration กับ Carrier (SPX/Flash/LEX/J&T)
[ ] API Integration กับ ERP
[ ] Webhook สำหรับ Real-time Update
[ ] Mobile App (iOS/Android)
```

---

## 6. Developer Roadmap

### 6.1 Checklist ฟีเจอร์ที่ยังไม่ครบ

```
┌─────────────────────────────────────────────────────────────────┐
│                    Feature Checklist                             │
└─────────────────────────────────────────────────────────────────┘

Core Features (Must Have)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[✅] Import Orders
[✅] Import Products
[✅] Import Stock
[✅] Batch Creation
[✅] Batch List
[✅] Batch Detail
[✅] Scan Batch (Picker)
[✅] Scan SKU (Picker)
[✅] Shortage Queue
[✅] Scan Handover (Packer)
[✅] Scan Tracking (Packer)
[✅] Dashboard
[✅] Export Excel

Role-Based Access Control (Phase 2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[❌] User Department (online/warehouse)
[❌] User Role (admin/staff/picker/packer)
[❌] Permission Decorator
[❌] UI Menu Filter by Role
[❌] Batch List Filter by Role
[❌] Shortage Queue Filter by Role

Shortage Management Enhancement (Phase 3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[✅] Shortage Detection
[✅] Shortage Queue
[✅] Shortage Status (pending/waiting_stock/cancelled/replaced/resolved)
[❌] Shortage Priority (high/medium/low)
[❌] Shortage Alert (Email/Line)
[❌] Shortage Report
[❌] Shortage Analytics

Mobile Optimization (Phase 4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[⚠️] Mobile-friendly UI (Partial)
[❌] Touch-friendly Buttons
[❌] Offline Mode
[❌] PWA Support
[❌] Mobile App (iOS/Android)

Advanced Features (Phase 5+)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[❌] Real-time Dashboard
[❌] Picker Performance Report
[❌] Auto Batch Creation
[❌] Auto Shortage Resolution
[❌] API Integration (Platform)
[❌] API Integration (Carrier)
[❌] Webhook Support
```

---

### 6.2 Technical Debt List

```
┌─────────────────────────────────────────────────────────────────┐
│                    Technical Debt List                           │
└─────────────────────────────────────────────────────────────────┘

Database & Models
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[❌] TD-01: เพิ่ม Index สำหรับ Query ที่ใช้บ่อย
[❌] TD-02: เพิ่ม Foreign Key Constraints
[❌] TD-03: เพิ่ม Cascade Delete Rules
[❌] TD-04: Normalize Database Schema
[❌] TD-05: เพิ่ม Database Migration System

Code Quality
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[❌] TD-06: แยก Business Logic ออกจาก Routes
[❌] TD-07: สร้าง Service Layer
[❌] TD-08: สร้าง Repository Pattern
[❌] TD-09: เพิ่ม Type Hints
[❌] TD-10: เพิ่ม Docstrings

Testing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[❌] TD-11: เพิ่ม Unit Tests
[❌] TD-12: เพิ่ม Integration Tests
[❌] TD-13: เพิ่ม E2E Tests
[❌] TD-14: เพิ่ม Test Coverage Report
[❌] TD-15: เพิ่ม CI/CD Pipeline

Security
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[❌] TD-16: เพิ่ม CSRF Protection
[❌] TD-17: เพิ่ม Rate Limiting
[❌] TD-18: เพิ่ม Input Validation
[❌] TD-19: เพิ่ม SQL Injection Protection
[❌] TD-20: เพิ่ม XSS Protection

Performance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[❌] TD-21: เพิ่ม Caching (Redis)
[❌] TD-22: เพิ่ม Query Optimization
[❌] TD-23: เพิ่ม Lazy Loading
[❌] TD-24: เพิ่ม Pagination
[❌] TD-25: เพิ่ม Background Jobs (Celery)
```

---

### 6.3 แผนพัฒนา Phase 3 (Detailed)

```
┌─────────────────────────────────────────────────────────────────┐
│                  Phase 3 Development Plan                        │
│              (Role-Based Access Control)                         │
└─────────────────────────────────────────────────────────────────┘

Week 1: Database Schema Update
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Day 1-2: เพิ่ม department และ role ใน User model
[ ] Day 3-4: สร้าง Migration Script
[ ] Day 5: ทดสอบ Migration

Week 2: Permission System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Day 1-2: สร้าง Permission Decorator
[ ] Day 3-4: เพิ่ม Permission ใน Routes
[ ] Day 5: ทดสอบ Permission

Week 3: UI Update
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Day 1-2: ซ่อน/แสดงเมนูตาม Role
[ ] Day 3-4: เพิ่ม Role Badge ใน UI
[ ] Day 5: ทดสอบ UI

Week 4: Testing & Training
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Day 1-2: ทดสอบ Permission ทุก Endpoint
[ ] Day 3-4: สร้างเอกสาร Training
[ ] Day 5: Training พนักงาน
```

---

## 📞 ติดต่อ & สนับสนุน

หากมีข้อสงสัยเกี่ยวกับ Flow การทำงาน:
- 📧 Email: support@vnix.com
- 💬 Line: @vnixsupport
- 📚 Docs: https://github.com/vnix-wms/docs

---

**อัปเดตล่าสุด:** 2025-11-18
**เวอร์ชัน:** 1.0
**ผู้เขียน:** VNIX Development Team

---

🎉 **หมายเหตุ:** เอกสารนี้เป็นคู่มือฉบับสมบูรณ์ สามารถพิมพ์แจกให้พนักงานแต่ละแผนกได้

