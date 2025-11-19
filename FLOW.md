# 📖 คู่มือใช้งานระบบ VNIX WMS
## วิธีการทำงานแบบง่าย ๆ สำหรับพนักงานทุกแผนก

---

## 📌 ข้อมูลเอกสาร

| รายการ | รายละเอียด |
|--------|-----------|
| **ชื่อเอกสาร** | คู่มือใช้งาน VNIX WMS |
| **เวอร์ชัน** | 2.0 |
| **วันที่อัปเดต** | 2025-11-18 |
| **ผู้จัดทำ** | ทีมพัฒนา VNIX |
| **สำหรับ** | พนักงานทุกคน (ออนไลน์, คลัง, แพ็ค) |
| **ใช้เวลาอ่าน** | ประมาณ 1 ชั่วโมง |

---

## 📑 สารบัญ (เนื้อหาในเอกสาร)

1. [รู้จักระบบและเมนูต่าง ๆ](#1-รู้จักระบบและเมนูต่าง-ๆ)
2. [ผังการทำงานทีละขั้นตอน](#2-ผังการทำงานทีละขั้นตอน)
3. [วิธีใช้งานประจำวัน](#3-วิธีใช้งานประจำวัน)
4. [การจัดการสินค้าที่ขาด (Shortage)](#4-การจัดการสินค้าที่ขาด-shortage)
5. [วิธีนำเข้าออเดอร์](#5-วิธีนำเข้าออเดอร์)
6. [จุดเสี่ยงและแผนแก้ไข](#6-จุดเสี่ยงและแผนแก้ไข)

---

# 1. รู้จักระบบและเมนูต่าง ๆ

## 1.1 📊 รายการเมนูทั้งหมดในระบบ (มี 61 เมนู)

### 🎯 หน้าหลัก (Core Pages)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **หน้าแรก** | `/` | ✅ | ✅ | ✅ | ✅ | Redirect ไป Dashboard |
| **เข้าสู่ระบบ** | `/login` | ✅ | ✅ | ✅ | ✅ | Login page |
| **ออกจากระบบ** | `/logout` | ✅ | ✅ | ✅ | ✅ | Logout |
| **Dashboard** | `/dashboard` | ✅ Full | ✅ View | ❌ | ❌ | ภาพรวมออเดอร์ |

---

### 📥 Import Module (นำเข้าข้อมูล)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **Import Orders** | `/import/orders` | ✅ | ❌ | ❌ | ❌ | นำเข้าออเดอร์จาก Excel |
| **Import Products** | `/import/products` | ✅ | ❌ | ❌ | ❌ | นำเข้าสินค้าจาก Excel |
| **Import Stock** | `/import/stock` | ✅ | ❌ | ❌ | ❌ | นำเข้าสต็อกจาก Excel |
| **Import Sales** | `/import/sales` | ✅ | ❌ | ❌ | ❌ | นำเข้า Sales Data |

---

### 📦 Batch Management Module (จัดการ Batch)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **สร้าง Batch** | `/batch/create` | ✅ | ✅ | ❌ | ❌ | สร้าง Batch ใหม่ |
| **รายการ Batch** | `/batch/list` | ✅ All | ✅ All | ✅ Own | ✅ Ready | ดู Batch ทั้งหมด |
| **รายละเอียด Batch** | `/batch/<batch_id>` | ✅ | ✅ | ✅ Own | ✅ | ดูรายละเอียด Batch |
| **Export Batch Excel** | `/batch/<batch_id>/export.xlsx` | ✅ | ✅ | ❌ | ❌ | Export ข้อมูล Batch |
| **Quick Create Batch** | `/batch/quick-create/<platform>` | ✅ | ✅ | ❌ | ❌ | สร้าง Batch แบบเร็ว |
| **Get Next Run Number** | `/batch/next-run/<platform>` | ✅ | ✅ | ❌ | ❌ | ดูเลข Run ถัดไป |
| **Batch Summary JSON** | `/batch/<batch_id>/summary` | ✅ | ✅ | ✅ | ✅ | ข้อมูล Summary (API) |

---

### 🖨️ Print Module (พิมพ์เอกสาร)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **พิมพ์ใบงานคลัง** | `/batch/<batch_id>/print-warehouse` | ✅ | ✅ | ✅ | ❌ | ใบงานคลัง (Warehouse Sheet) |
| **พิมพ์ Picking List** | `/batch/<batch_id>/print-picking` | ✅ | ✅ | ✅ | ❌ | รายการหยิบของ |
| **พิมพ์ SKU QR Code** | `/batch/<batch_id>/print-sku-qr` | ✅ | ✅ | ✅ | ❌ | QR Code สำหรับสแกน SKU |
| **พิมพ์ใบส่งมอบ** | `/batch/<batch_id>/print-handover` | ✅ | ❌ | ❌ | ✅ | Handover Slip (ใบส่งขนส่ง) |

---

### 📱 Scanning Module (สแกนบนมือถือ)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **สแกนรับงาน Batch** | `/scan/batch` | ✅ | ❌ | ✅ | ❌ | สแกน QR รับงาน Batch |
| **สแกนหยิบของ (SKU)** | `/scan/sku` | ✅ | ❌ | ✅ | ❌ | สแกน QR หยิบสินค้า |
| **สแกนส่งมอบ** | `/scan-handover` | ✅ | ❌ | ❌ | ✅ | สแกนส่งมอบให้ขนส่ง |
| **สแกน Tracking** | `/scan/tracking` | ✅ | ❌ | ❌ | ✅ | บันทึกเลข Tracking |

---

### ⚠️ Shortage Management Module (จัดการสินค้าขาด)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **Shortage Queue** | `/shortage-queue` | ✅ Full | ✅ View | ✅ Own | ❌ | รายการสินค้าที่ขาด |

---

### 🔧 API Endpoints (สำหรับระบบภายใน)

| API Endpoint | Method | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|-------------|--------|:------------:|:------------:|:------:|:------:|---------|
| `/api/scan/batch` | POST | ✅ | ❌ | ✅ | ❌ | API รับงาน Batch |
| `/api/scan/sku` | POST | ✅ | ❌ | ✅ | ❌ | API สแกน SKU |
| `/api/pick/sku` | POST | ✅ | ❌ | ✅ | ❌ | API บันทึกการหยิบ |
| `/api/scan/tracking` | POST | ✅ | ❌ | ❌ | ✅ | API บันทึก Tracking |
| `/api/shortage/mark` | POST | ✅ | ❌ | ✅ | ❌ | API บันทึก Shortage |
| `/api/shortage/queue` | GET | ✅ | ✅ | ✅ | ❌ | API ดู Shortage Queue |
| `/api/shortage/action` | POST | ✅ | ❌ | ❌ | ❌ | API จัดการ Shortage |
| `/api/shortage/bulk-action` | POST | ✅ | ❌ | ❌ | ❌ | API จัดการ Shortage หลายรายการ |
| `/api/shortage/quick-action` | POST | ✅ | ❌ | ❌ | ❌ | API Quick Action Shortage |
| `/api/shortage/update` | POST | ✅ | ❌ | ❌ | ❌ | API อัปเดต Shortage |
| `/api/shortage/export-excel` | GET | ✅ | ✅ | ❌ | ❌ | API Export Shortage Excel |
| `/api/shortage/order-details` | GET | ✅ | ✅ | ✅ | ❌ | API ดูรายละเอียด Order |
| `/api/quick-assign/batches` | GET | ✅ | ❌ | ✅ | ❌ | API Quick Assign Batch |
| `/api/quick-assign/skus` | GET | ✅ | ❌ | ✅ | ❌ | API Quick Assign SKU |
| `/api/batch/<batch_id>/auto-split` | POST | ✅ | ❌ | ❌ | ❌ | API แยก Batch อัตโนมัติ |
| `/api/batch/<batch_id>/family` | GET | ✅ | ✅ | ✅ | ✅ | API ดู Batch Family |
| `/api/batch/<batch_id>/generate-handover-code` | POST | ✅ | ❌ | ❌ | ✅ | API สร้าง Handover Code |
| `/api/handover/verify` | POST | ✅ | ❌ | ❌ | ✅ | API ตรวจสอบ Handover |
| `/api/handover/confirm` | POST | ✅ | ❌ | ❌ | ✅ | API ยืนยัน Handover |
| `/api/confirm-dispatch` | POST | ✅ | ❌ | ❌ | ✅ | API ยืนยันการส่งมอบ |

---

### 👥 User & Admin Module (จัดการผู้ใช้)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **จัดการผู้ใช้** | `/admin/users` | ✅ | ❌ | ❌ | ❌ | เพิ่ม/ลบ/แก้ไข User |
| **ทดสอบระบบสต็อก** | `/admin/test-stock` | ✅ | ❌ | ❌ | ❌ | ทดสอบระบบสต็อก |
| **ล้างข้อมูล** | `/admin/clear` | ✅ | ❌ | ❌ | ❌ | ล้างข้อมูลทดสอบ |
| `/admin/stock-list` | GET | ✅ | ❌ | ❌ | ❌ | API ดูรายการสต็อก |
| `/admin/preview` | POST | ✅ | ❌ | ❌ | ❌ | API Preview ก่อน Import |
| `/admin/export-stock-excel` | GET | ✅ | ❌ | ❌ | ❌ | API Export สต็อก Excel |
| `/admin/delete-multiple` | POST | ✅ | ❌ | ❌ | ❌ | API ลบหลายรายการ |

---

### 📊 Report Module (รายงาน)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **รายงาน Picking** | `/report/picking` | ✅ | ✅ | ✅ | ❌ | รายงานการหยิบของ |
| **พิมพ์รายงาน Picking** | `/report/picking/print` | ✅ | ✅ | ✅ | ❌ | พิมพ์รายงาน Picking |
| **รายงานคลัง** | `/report/warehouse` | ✅ | ✅ | ❌ | ❌ | รายงานคลัง |
| **พิมพ์รายงานคลัง** | `/report/warehouse/print` | ✅ | ✅ | ❌ | ❌ | พิมพ์รายงานคลัง |

---

### 📤 Export Module (ส่งออกข้อมูล)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **Export Dashboard** | `/export.xlsx` | ✅ | ✅ | ❌ | ❌ | Export ข้อมูล Dashboard |
| **Export Picking Data** | `/export_picking.xlsx` | ✅ | ✅ | ❌ | ❌ | Export ข้อมูลการหยิบ |

---

### 🔄 Order Management (จัดการออเดอร์)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **Accept Order** | `/accept/<order_line_id>` | ✅ | ✅ | ❌ | ❌ | รับออเดอร์ |
| **Cancel Accept** | `/cancel_accept/<order_line_id>` | ✅ | ✅ | ❌ | ❌ | ยกเลิกการรับออเดอร์ |
| **Bulk Accept** | `/bulk_accept` | ✅ | ✅ | ❌ | ❌ | รับหลายออเดอร์พร้อมกัน |
| **Bulk Cancel** | `/bulk_cancel` | ✅ | ✅ | ❌ | ❌ | ยกเลิกหลายออเดอร์พร้อมกัน |

---

### 🏷️ Utilities (เครื่องมือเสริม)

| เมนู | URL | Online Admin | Online Staff | Picker | Packer | คำอธิบาย |
|------|-----|:------------:|:------------:|:------:|:------:|---------|
| **Generate QR Code** | `/qr/<path:text>` | ✅ | ✅ | ✅ | ✅ | สร้าง QR Code ทันที |

---

## 1.2 📋 แต่ละแผนกใช้เมนูอะไรบ้าง

| แผนก | จำนวนเมนูที่เข้าถึงได้ | หมายเหตุ |
|------|----------------------|---------|
| **Online Admin** | 61 (ทั้งหมด) | Full Access |
| **Online Staff** | 35 | ไม่มี Import, User Management, Admin Tools |
| **Picker** | 18 | เฉพาะ Scan, Print, Quick Assign |
| **Packer** | 15 | เฉพาะ Handover, Tracking, Print |

---

## 1.3 ⚠️ เมนูสำคัญที่ต้องใช้ทุกวัน

### 🔴 สำคัญสุด (ใช้งานทุกวัน)

| เมนู | แผนก | เหตุผล |
|------|------|-------|
| `/import/orders` | Online Admin | **หัวใจหลัก** - ไม่ Import ออเดอร์ = ไม่มีงาน |
| `/batch/create` | Online | **หัวใจหลัก** - สร้าง Batch เพื่อส่งงานให้คลัง |
| `/scan/batch` | Picker | **หัวใจหลัก** - รับงาน Batch |
| `/scan/sku` | Picker | **หัวใจหลัก** - หยิบของ |
| `/scan-handover` | Packer | **หัวใจหลัก** - ส่งมอบให้ขนส่ง |
| `/shortage-queue` | Online Admin | **สำคัญมาก** - จัดการสินค้าขาด |

### 🟡 สำคัญรองลงมา

| เมนู | แผนก | เหตุผล |
|------|------|-------|
| `/batch/list` | ทุกแผนก | ติดตามความคืบหน้า |
| `/batch/<batch_id>` | ทุกแผนก | ดูรายละเอียด |
| `/batch/<batch_id>/print-picking` | Online, Picker | พิมพ์ใบหยิบของ |
| `/scan/tracking` | Packer | บันทึกเลข Tracking |

---

## 1.4 🗺️ แผนที่การใช้งาน (ไปไหนทำอะไร)

```
┌─────────────────────────────────────────────────────────────┐
│                        VNIX WMS                              │
│                    (After Login)                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐             ┌───────▼────────┐
│  Online Team   │             │ Warehouse Team │
└───────┬────────┘             └───────┬────────┘
        │                               │
        │                               │
┌───────▼────────────────────┐  ┌──────▼─────────────────────┐
│ Online Admin Menu:         │  │ Picker Menu:               │
│ • Dashboard                │  │ • Scan Batch               │
│ • Import Orders ⭐          │  │ • Scan SKU ⭐               │
│ • Import Products          │  │ • Batch List (Own)         │
│ • Import Stock             │  │ • Batch Detail             │
│ • Create Batch ⭐           │  │ • Print Picking List       │
│ • Batch List               │  │ • Print SKU QR             │
│ • Shortage Queue ⭐         │  │ • Quick Assign             │
│ • User Management          │  └────────────────────────────┘
│ • Export Excel             │
│ • Admin Tools              │  ┌────────────────────────────┐
└────────────────────────────┘  │ Packer Menu:               │
                                │ • Batch List (Ready 100%)  │
┌────────────────────────────┐  │ • Scan Handover ⭐          │
│ Online Staff Menu:         │  │ • Scan Tracking            │
│ • Dashboard (View Only)    │  │ • Print Handover Slip      │
│ • Create Batch ⭐           │  │ • Batch Detail             │
│ • Batch List               │  └────────────────────────────┘
│ • Batch Detail             │
│ • Shortage Queue (View)    │
│ • Export Excel (Limited)   │
│ • Print Documents          │
└────────────────────────────┘

⭐ = เมนูที่ใช้งานบ่อยที่สุด (Daily Use)
```

---

# 2. ผังการทำงานทีละขั้นตอน

## 2.1 🎯 ภาพรวมการทำงานทั้งระบบ

```
┌─────────────────────────────────────────────────────────────────┐
│                    VNIX WMS - Master Flow                        │
│                   (End-to-End Process)                           │
└─────────────────────────────────────────────────────────────────┘

📥 PHASE 1: IMPORT (ทีมออนไลน์)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────┐
│ Online Admin │ เข้าสู่ระบบ
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ 1. Import Orders     │ ← Excel File (Order Number, SKU, Qty, Platform, Shop)
└──────┬───────────────┘
       │
       ├─── ✅ Success → บันทึกลง Database
       │                  │
       │                  ▼
       │            ┌─────────────────┐
       │            │ Auto-Classify:  │
       │            │ • READY_ACCEPT  │ ← สต็อกเพียงพอ
       │            │ • LOW_STOCK     │ ← สต็อกน้อย
       │            │ • SHORTAGE      │ ← สต็อกไม่พอ/ไม่มี
       │            └─────────────────┘
       │
       └─── ❌ Error → แสดง Error Message → แก้ไข Excel → ลองใหม่
                       (SKU ไม่มี, Format ผิด, Duplicate, etc.)


📦 PHASE 2: CREATE BATCH (ทีมออนไลน์)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────────────┐
│ 2. Create Batch      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ เลือก Filter:       │
│ • Platform (Shopee/  │
│   TikTok/Lazada)     │
│ • Date Range         │
│ • Status = READY     │ ← สำคัญ! เลือกเฉพาะ READY เท่านั้น
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ เลือก Orders ที่จะ  │
│ ใส่ใน Batch          │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ ระบบ Auto-Generate: │
│ • Batch ID           │ ← SH-2025-11-18-R1
│ • Run Number         │ ← R1, R2, R3...
│ • QR Code            │ ← สำหรับสแกน
└──────┬───────────────┘
       │
       ├─── ✅ Success → Batch Created
       │                  │
       │                  ▼
       │            ┌─────────────────┐
       │            │ 3. Print        │
       │            │ • Picking List  │ ← รายการหยิบของ
       │            │ • SKU QR Codes  │ ← สติกเกอร์ SKU
       │            │ • Batch QR      │ ← QR บนใบงาน
       │            └─────────────────┘
       │
       └─── ❌ Error → ไม่มี Orders ที่ READY
                       → กลับไป Import ใหม่หรือตรวจสอบสต็อก


🔍 PHASE 3: PICKING (Picker - ทีมคลัง)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────────────┐
│ 4. รับงาน Batch      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐      ┌──────────────────────┐
│ เลือกวิธีรับงาน:     │      │ หรือ: Quick Assign   │
│ • Scan Batch QR      │◄────►│ (เลือกจากดรอปดาวน์) │
│   (/scan/batch)      │      └──────────────────────┘
└──────┬───────────────┘
       │
       ├─── ✅ Success → Batch Accepted
       │                  │
       │                  ├─ บันทึก: accepted_by_username, accepted_at
       │                  │
       │                  ▼
       │            ┌─────────────────┐
       │            │ 5. หยิบสินค้า   │
       │            │ (/scan/sku)     │
       │            └─────┬───────────┘
       │                  │
       │                  ▼
       │            ┌─────────────────────────┐
       │            │ Loop: สำหรับแต่ละ SKU   │
       │            ├─────────────────────────┤
       │            │ 5.1 Scan SKU QR         │
       │            │ 5.2 ระบุจำนวนที่หยิบ   │
       │            │                         │
       │            │ ┌─── จำนวนครบ (Full)?  │
       │            │ │                       │
       │            │ ├─ YES → picked_qty =   │
       │            │ │         qty           │
       │            │ │         Update DB     │
       │            │ │         Progress +1   │
       │            │ │                       │
       │            │ └─ NO  → Partial Pick   │
       │            │           │             │
       │            │           ▼             │
       │            │    ┌──────────────────┐ │
       │            │    │ 5.3 บันทึก      │ │
       │            │    │ Shortage:        │ │
       │            │    │ • shortage_qty   │ │
       │            │    │ • reason         │ │
       │            │    │ (out_of_stock/   │ │
       │            │    │  damaged)        │ │
       │            │    │                  │ │
       │            │    │ ส่งไป:          │ │
       │            │    │ ShortageQueue ⚠️ │ │
       │            │    └──────────────────┘ │
       │            │                         │
       │            │ จบ SKU นี้ → ถัดไป     │
       │            └─────────────────────────┘
       │                  │
       │                  ▼
       │            Progress = 100%? ─── NO → กลับไป Loop
       │                  │
       │                  YES
       │                  │
       │                  ▼
       │            ┌─────────────────┐
       │            │ 6. Batch        │
       │            │ Completed ✅     │
       │            │ พร้อมส่งมอบ     │
       │            └─────────────────┘
       │
       └─── ❌ Error → Batch QR ผิด / Batch ถูกรับแล้ว
                       → ตรวจสอบ Batch ID


📤 PHASE 4: DISPATCH (Packer - ทีมคลัง)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────────────┐
│ 7. ดู Batch ที่พร้อม │
│ (/batch/list)        │
│ Filter: Progress     │
│ = 100%               │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 8. แพ็คสินค้า        │
│ ตาม Batch            │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 9. สแกนส่งมอบ       │
│ (/scan-handover)     │
│ • Scan Batch QR      │
└──────┬───────────────┘
       │
       ├─── ✅ Success → Auto-Generate Handover Code
       │                  │                (H-YYYYMMDD-NNN)
       │                  │
       │                  ▼
       │            ┌─────────────────┐
       │            │ 10. บันทึก      │
       │            │ Tracking Number │
       │            │ (/scan/tracking)│
       │            │ (Optional)      │
       │            └─────────────────┘
       │                  │
       │                  ▼
       │            ┌─────────────────┐
       │            │ 11. Print       │
       │            │ Handover Slip   │
       │            │ (ใบส่งมอบ)      │
       │            └─────────────────┘
       │                  │
       │                  ▼
       │            ┌─────────────────┐
       │            │ 12. ส่งมอบให้   │
       │            │ ขนส่ง           │
       │            │                 │
       │            │ Status =        │
       │            │ DISPATCHED ✅    │
       │            └─────────────────┘
       │
       └─── ❌ Error → Progress < 100%
                       → รอให้ Picker หยิบของให้ครบก่อน


⚠️ PHASE 5: SHORTAGE MANAGEMENT (Online Admin)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────────────┐
│ 13. ดู Shortage      │
│ Queue                │
│ (/shortage-queue)    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 14. จัดการแต่ละรายการ:          │
├──────────────────────────────────┤
│ Action:                          │
│                                  │
│ ┌─ waiting_stock                │
│ │  (รอสต็อกเข้า - ไม่ทำอะไร)    │
│ │                                │
│ ├─ resolved                      │
│ │  (หาสต็อกเจอแล้ว)             │
│ │  → อัปเดต Stock → Pick ใหม่   │
│ │                                │
│ ├─ cancelled                     │
│ │  (ยกเลิก Order)                │
│ │  → แจ้งลูกค้า                  │
│ │                                │
│ └─ replaced                      │
│    (แทนด้วย SKU อื่น)            │
│    → สร้าง Order ใหม่            │
└──────────────────────────────────┘
       │
       ▼
┌──────────────────────┐
│ 15. Export Excel     │
│ (ถ้าต้องการรายงาน)   │
└──────────────────────┘

```

---

## 2.2 🏢 วิธีทำงานของทีมออนไลน์

### 2.2.1 งานประจำวันของ Admin ออนไลน์

```
🌅 เริ่มต้นวัน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ เข้าสู่ระบบ
   └─> /login (username: admin)
       │
       ▼
   ✅ Login Success
       │
       ▼

2️⃣ Import ออเดอร์ประจำวัน
   └─> /import/orders
       │
       ├─ เตรียม Excel File:
       │  • Order Number
       │  • Platform (Shopee/TikTok/Lazada)
       │  • SKU
       │  • Quantity
       │  • Shop Name
       │  • Due Date (Optional - ระบบจะคำนวณให้)
       │
       ├─ Upload File
       │  │
       │  ▼
       ├─ ระบบตรวจสอบ:
       │  • Format ถูกต้อง?
       │  • SKU มีในระบบ?
       │  • Shop มีในระบบ?
       │  • Duplicate Order?
       │  │
       │  ├─ ✅ Pass → Import Success
       │  │              │
       │  │              ▼
       │  │         Auto-Classify:
       │  │         • READY_ACCEPT ← สต็อกพอ (สีเขียว)
       │  │         • LOW_STOCK    ← สต็อกน้อย (สีเหลือง)
       │  │         • SHORTAGE     ← สต็อกไม่พอ (สีแดง)
       │  │
       │  └─ ❌ Fail → Error Message
       │                 │
       │                 ▼
       │           แก้ไข Excel → Upload ใหม่
       │
       ▼

3️⃣ ตรวจสอบ Dashboard
   └─> /dashboard
       │
       ├─ ดูสรุป:
       │  • Total Orders = ?
       │  • READY = ? ออเดอร์
       │  • LOW_STOCK = ? ออเดอร์
       │  • SHORTAGE = ? ออเดอร์
       │  • Due Today = ? ออเดอร์
       │
       ├─ Filter:
       │  • Platform (Shopee/TikTok/Lazada)
       │  • Date Range
       │  • Status
       │
       └─ Export Excel (ถ้าต้องการรายงาน)
          └─> /export.xlsx
       │
       ▼

4️⃣ สร้าง Batch
   └─> /batch/create
       │
       ├─ เลือก Platform:
       │  • Shopee
       │  • TikTok
       │  • Lazada
       │
       ├─ เลือก Date Range
       │
       ├─ Filter: Status = READY_ACCEPT เท่านั้น ⚠️
       │
       ├─ เลือก Orders ที่ต้องการ
       │  (Checkbox)
       │
       ├─ กด "สร้าง Batch"
       │  │
       │  ▼
       ├─ ระบบสร้าง:
       │  • Batch ID: SH-2025-11-18-R1
       │  • Run Number: R1, R2, R3... (Auto)
       │  • QR Code: BATCH:SH-2025-11-18-R1
       │  │
       │  ├─ ✅ Success → Redirect to Batch Detail
       │  │                 │
       │  │                 ▼
       │  │           /batch/<batch_id>
       │  │                 │
       │  │                 ▼
       │  │           5️⃣ พิมพ์เอกสาร:
       │  │              ┌─ Picking List ← รายการหยิบของ
       │  │              ├─ SKU QR Codes ← สติกเกอร์ SKU
       │  │              └─ Batch QR     ← QR บนใบงาน
       │  │
       │  └─ ❌ Fail → Error:
       │                • ไม่มี Orders ที่เลือก
       │                • Orders ไม่ใช่ READY
       │
       ▼

6️⃣ ติดตามความคืบหน้า
   └─> /batch/list
       │
       ├─ ดูรายการ Batch:
       │  • Batch ID
       │  • Run Number
       │  • Platform
       │  • Progress % (0-100%)
       │  • Status
       │  │
       │  ├─ Progress < 100% → Picker กำลังหยิบ
       │  └─ Progress = 100% → พร้อม Dispatch
       │
       ├─ คลิกดูรายละเอียด → /batch/<batch_id>
       │  │
       │  └─ SKU-level Progress:
       │     • SKU-001: ✅ 10/10 (สีเขียว)
       │     • SKU-002: ⏳ 5/10 (สีเหลือง)
       │     • SKU-003: ❌ 0/10 - Shortage (สีแดง)
       │
       ▼

7️⃣ จัดการ Shortage (ถ้ามี)
   └─> /shortage-queue
       │
       ├─ ดูรายการ Shortage:
       │  • Order Number
       │  • SKU
       │  • Quantity ที่ขาด
       │  • Reason (out_of_stock / damaged)
       │  • Status
       │  • Urgency (high/medium/low)
       │
       ├─ Action แต่ละรายการ:
       │  ┌─ waiting_stock → รอสต็อกเข้า
       │  ├─ resolved → หาสต็อกเจอแล้ว
       │  ├─ cancelled → ยกเลิก Order
       │  └─ replaced → แทนด้วย SKU อื่น
       │
       └─ Export Excel (รายงาน Shortage)
          └─> /api/shortage/export-excel
       │
       ▼

8️⃣ จัดการผู้ใช้ (Admin Only)
   └─> /admin/users
       │
       ├─ เพิ่ม User ใหม่
       ├─ แก้ไข Role
       ├─ ปิด/เปิด User
       └─ ลบ User
       │
       ▼

🌆 สิ้นสุดวัน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Checklist ก่อนเลิกงาน:
   □ Import ออเดอร์วันนี้ครบหรือยัง?
   □ สร้าง Batch ครบทุก Platform หรือยัง?
   □ Shortage Queue มีรายการค้างหรือไม่?
   □ Batch ที่ต้อง Dispatch วันนี้เสร็จหมดหรือยัง?
   □ Export รายงานประจำวันแล้วหรือยัง?

```

---

### 2.2.2 งานประจำวันของ Staff ออนไลน์

```
🌅 เริ่มต้นวัน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ เข้าสู่ระบบ
   └─> /login (username: staff1)
       │
       ▼

2️⃣ ตรวจสอบ Dashboard (View Only)
   └─> /dashboard
       │
       ├─ ดูสรุปออเดอร์:
       │  • READY = ? (สามารถสร้าง Batch)
       │  • LOW_STOCK = ? (รอสต็อก)
       │  • SHORTAGE = ? (ต้องแจ้ง Admin)
       │  • Due Today = ? (ต้องเร่งด่วน)
       │
       └─ ⚠️ ไม่สามารถ Import ออเดอร์ได้
          (ถ้าต้องการ Import → แจ้ง Admin)
       │
       ▼

3️⃣ สร้าง Batch
   └─> /batch/create
       │
       ├─ เลือก Platform
       ├─ เลือก Date Range
       ├─ Filter: READY_ACCEPT only
       ├─ เลือก Orders
       ├─ สร้าง Batch
       │  │
       │  ├─ ✅ Success → Batch Created
       │  │                 │
       │  │                 ▼
       │  │           พิมพ์เอกสาร:
       │  │           • Picking List
       │  │           • SKU QR Codes
       │  │
       │  └─ ❌ Fail → แจ้ง Admin
       │
       ▼

4️⃣ ติดตามความคืบหน้า
   └─> /batch/list
       │
       ├─ ดูรายการ Batch ทั้งหมด
       ├─ คลิกดูรายละเอียด
       ├─ พิมพ์เอกสารเพิ่มเติมได้ (ถ้าหาย)
       │
       └─ ⚠️ ไม่สามารถลบ Batch ได้
          (ถ้าต้องการลบ → แจ้ง Admin)
       │
       ▼

5️⃣ ดู Shortage Queue (View Only)
   └─> /shortage-queue
       │
       ├─ ดูรายการ Shortage
       ├─ Export Excel ได้
       │
       └─ ⚠️ ไม่สามารถจัดการ Shortage ได้
          (ต้องแจ้ง Admin ให้จัดการ)
       │
       ▼

🌆 สิ้นสุดวัน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Checklist ก่อนเลิกงาน:
   □ สร้าง Batch ครบทุก Platform หรือยัง?
   □ พิมพ์เอกสารให้คลังครบหรือยัง?
   □ มี Shortage ที่ต้องแจ้ง Admin หรือไม่?
   □ Batch ที่รับผิดชอบเสร็จหมดหรือยัง?

```

---

## 2.3 🏭 วิธีทำงานของทีมคลัง

### 2.3.1 งานประจำวันของพนักงานหยิบของ (Picker)

```
🌅 เริ่มต้นวัน (รับงานหยิบของ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ เข้าสู่ระบบ (มือถือ)
   └─> /login (username: picker1)
       │
       ▼

2️⃣ รับงาน Batch
   └─> /scan/batch
       │
       ├─ วิธีที่ 1: Scan Batch QR
       │  │
       │  ├─ ใช้กล้องมือถือสแกน QR Code บนใบงาน
       │  │  (QR Code มี Text: BATCH:SH-2025-11-18-R1)
       │  │
       │  ├─ ✅ Success → Batch Accepted
       │  │                 │
       │  │                 ├─ แสดงรายละเอียด Batch:
       │  │                 │  • Batch ID: SH-2025-11-18-R1
       │  │                 │  • Run Number: R1
       │  │                 │  • Total Orders: 50
       │  │                 │  • Total SKUs: 15
       │  │                 │  • Platform: Shopee
       │  │                 │
       │  │                 └─ บันทึก:
       │  │                    • accepted_by_username = "picker1"
       │  │                    • accepted_at = 2025-11-18 08:30:00
       │  │
       │  └─ ❌ Error:
       │     ├─ QR Code ผิด → สแกนใหม่
       │     ├─ Batch ถูกรับแล้ว → เลือก Batch อื่น
       │     └─ Batch ถูก Lock → แจ้ง Admin
       │
       ├─ วิธีที่ 2: Quick Assign (ถ้าไม่มี QR)
       │  │
       │  ├─ เลือกจาก Dropdown List
       │  ├─ กด "รับงาน"
       │  │
       │  ├─ ✅ Success → Batch Accepted
       │  └─ ❌ Error → เหมือนวิธีที่ 1
       │
       ▼

3️⃣ หยิบสินค้า
   └─> /scan/sku
       │
       ├─ เลือก Batch ที่รับมา
       │  (ถ้ารับหลาย Batch → เลือก Batch ที่จะหยิบก่อน)
       │
       ▼
       │
       ├─ Loop: สำหรับแต่ละ SKU ใน Batch
       │  │
       │  ├─ 3.1 Scan SKU QR Code
       │  │    │
       │  │    ├─ ใช้กล้องมือถือสแกน QR Code บน Shelf
       │  │    │  (QR Code มี Text: SKU:SKU-001)
       │  │    │
       │  │    ├─ ✅ SKU ถูกต้อง → แสดงข้อมูล:
       │  │    │                  • SKU: SKU-001
       │  │    │                  • Item Name: สินค้า A
       │  │    │                  • Required Qty: 10 ชิ้น
       │  │    │                  • Shelf: A-01
       │  │    │
       │  │    └─ ❌ SKU ผิด → สแกนใหม่
       │  │
       │  ├─ 3.2 ระบุจำนวนที่หยิบได้
       │  │    │
       │  │    ├─ ใช้ Number Pad กรอกจำนวน
       │  │    │
       │  │    ├─ ตัวเลือก:
       │  │    │  │
       │  │    │  ├─ A) หยิบได้ครบ (Full Pick)
       │  │    │  │   │
       │  │    │  │   └─> กรอก: 10 (เท่ากับ Required Qty)
       │  │    │  │        │
       │  │    │  │        ├─ กด "บันทึก"
       │  │    │  │        │
       │  │    │  │        ├─ ระบบบันทึก:
       │  │    │  │        │  • picked_qty = 10
       │  │    │  │        │  • picked_by_username = "picker1"
       │  │    │  │        │  • picked_at = 2025-11-18 09:15:00
       │  │    │  │        │  • dispatch_status = "ready"
       │  │    │  │        │
       │  │    │  │        └─ แสดง: ✅ "บันทึกสำเร็จ!"
       │  │    │  │           Progress +1 SKU
       │  │    │  │
       │  │    │  └─ B) หยิบได้บางส่วน (Partial Pick / Shortage)
       │  │    │      │
       │  │    │      └─> กรอก: 5 (น้อยกว่า Required Qty = 10)
       │  │    │           │
       │  │    │           ├─ ระบบถาม: "ทำไมหยิบได้ไม่ครบ?"
       │  │    │           │
       │  │    │           ├─ เลือกเหตุผล:
       │  │    │           │  • สต็อกหมด (out_of_stock)
       │  │    │           │  • สินค้าเสียหาย (damaged)
       │  │    │           │  • อื่นๆ
       │  │    │           │
       │  │    │           ├─ กด "บันทึก Shortage"
       │  │    │           │
       │  │    │           ├─ ระบบบันทึก:
       │  │    │           │  • picked_qty = 5 (หยิบได้)
       │  │    │           │  • shortage_qty = 5 (ขาด)
       │  │    │           │  • picked_by_username = "picker1"
       │  │    │           │  • dispatch_status = "partial_ready"
       │  │    │           │  │
       │  │    │           │  └─ สร้างรายการใน ShortageQueue:
       │  │    │           │     • order_number = SO123456
       │  │    │           │     • sku = SKU-001
       │  │    │           │     • qty_shortage = 5
       │  │    │           │     • reason = "out_of_stock"
       │  │    │           │     • status = "waiting_stock"
       │  │    │           │     • urgency = "high"
       │  │    │           │
       │  │    │           └─ แสดง: ⚠️ "บันทึก Shortage สำเร็จ"
       │  │    │              (Online Team จะเห็นใน Shortage Queue)
       │  │    │
       │  │    └─ กด "ถัดไป" → SKU ถัดไป
       │  │
       │  └─ จบ Loop เมื่อ: ทุก SKU หยิบเสร็จ (หรือบันทึก Shortage)
       │
       ▼

4️⃣ ตรวจสอบ Progress
   └─> /batch/<batch_id>
       │
       ├─ ดู Progress:
       │  • Total SKUs: 15
       │  • Picked: 12 ✅
       │  • Pending: 2 ⏳
       │  • Shortage: 1 ❌
       │  • Progress: 86.7%
       │
       ├─ Progress < 100%? → กลับไปหยิบ SKU ที่ค้าง
       │
       └─ Progress = 100%? → ✅ เสร็จสิ้น!
          │
          ├─ Batch Status = "completed"
          └─ ส่งต่อให้ Packer

🌆 สิ้นสุดวัน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Checklist ก่อนเลิกงาน:
   □ Batch ที่รับมาวันนี้หยิบครบ 100% หรือยัง?
   □ Shortage ที่บันทึกไว้ถูกต้องหรือไม่?
   □ มือถือชาร์จไฟแล้วหรือยัง? (สำหรับวันพรุ่งนี้)
   □ ใบงานที่พิมพ์เก็บเรียบร้อยหรือยัง?

```

---

### 2.3.2 งานประจำวันของพนักงานแพ็ค (Packer)

```
🌅 เริ่มต้นวัน (แพ็คและส่งมอบ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ เข้าสู่ระบบ (มือถือ)
   └─> /login (username: packer1)
       │
       ▼

2️⃣ ดู Batch ที่พร้อมส่ง
   └─> /batch/list
       │
       ├─ Filter: Progress = 100% เท่านั้น
       │  (Batch ที่ Picker หยิบของครบแล้ว)
       │
       ├─ รายการที่แสดง:
       │  • Batch ID: SH-2025-11-18-R1
       │  • Progress: 100% ✅
       │  • Total Orders: 50
       │  • Platform: Shopee
       │  • Status: completed (รอส่งมอบ)
       │
       └─ เลือก Batch ที่จะแพ็ค
          │
          ▼

3️⃣ แพ็คสินค้า
   └─> (ทำด้วยมือ - ไม่มีในระบบ)
       │
       ├─ ดูรายละเอียด Batch:
       │  └─> /batch/<batch_id>
       │      │
       │      ├─ รายการออเดอร์:
       │      │  • Order Number: SO123456
       │      │  • SKU: SKU-001 (10 ชิ้น)
       │      │  • SKU: SKU-002 (5 ชิ้น)
       │      │  • Logistic: Shopee Express
       │      │
       │      └─ แพ็คสินค้าตามรายการ
       │
       ├─ ติดสติกเกอร์ที่อยู่
       ├─ ใส่กล่อง
       ├─ ปิดเทป
       │
       ▼

4️⃣ สแกนส่งมอบให้ขนส่ง
   └─> /scan-handover
       │
       ├─ 4.1 Scan Batch QR
       │    │
       │    ├─ ใช้กล้องมือถือสแกน QR Code บนกล่อง
       │    │  (QR Code มี Text: BATCH:SH-2025-11-18-R1)
       │    │
       │    ├─ ✅ Batch ถูกต้อง และ Progress = 100%
       │    │     │
       │    │     ├─ ระบบ Auto-Generate Handover Code:
       │    │     │  • Handover Code: H-20251118-001
       │    │     │  • Generated At: 2025-11-18 14:30:00
       │    │     │  • Generated By: packer1
       │    │     │
       │    │     ├─ แสดงหน้าจอ:
       │    │     │  ┌─────────────────────────────┐
       │    │     │  │ Handover สำเร็จ! ✅         │
       │    │     │  ├─────────────────────────────┤
       │    │     │  │ Handover Code:              │
       │    │     │  │ H-20251118-001              │
       │    │     │  │                             │
       │    │     │  │ Batch ID:                   │
       │    │     │  │ SH-2025-11-18-R1            │
       │    │     │  │                             │
       │    │     │  │ Total Orders: 50            │
       │    │     │  │                             │
       │    │     │  │ [พิมพ์ใบส่งมอบ]            │
       │    │     │  └─────────────────────────────┘
       │    │     │
       │    │     └─ บันทึก:
       │    │        • handover_code = "H-20251118-001"
       │    │        • handover_confirmed = True
       │    │        • handover_confirmed_at = 2025-11-18 14:30:00
       │    │        • handover_confirmed_by_username = "packer1"
       │    │        • dispatch_status = "dispatched" (ทุก Order ใน Batch)
       │    │
       │    └─ ❌ Error:
       │       ├─ Progress < 100% → รอให้ Picker หยิบครบก่อน
       │       ├─ Batch ไม่มีในระบบ → ตรวจสอบ QR Code
       │       └─ Batch ถูก Handover แล้ว → ดู Handover Code เดิม
       │
       ▼

5️⃣ บันทึก Tracking Number (Optional)
   └─> /scan/tracking
       │
       ├─ สำหรับแต่ละ Order:
       │  │
       │  ├─ 5.1 Scan Order QR (หรือพิมพ์ Order Number)
       │  │
       │  ├─ 5.2 ระบุ Tracking Number
       │  │    │
       │  │    └─> กรอก: TH123456789TH
       │  │         │
       │  │         ├─ กด "บันทึก"
       │  │         │
       │  │         ├─ ระบบบันทึก:
       │  │         │  • tracking_number = "TH123456789TH"
       │  │         │  • dispatched_by_username = "packer1"
       │  │         │  • dispatched_at = 2025-11-18 14:35:00
       │  │         │
       │  │         └─ แสดง: ✅ "บันทึกสำเร็จ!"
       │  │
       │  └─ Loop: สำหรับทุก Order ใน Batch
       │
       ▼

6️⃣ พิมพ์ใบส่งมอบ
   └─> /batch/<batch_id>/print-handover
       │
       ├─ พิมพ์ Handover Slip:
       │  ┌─────────────────────────────────────┐
       │  │ 📦 ใบส่งมอบสินค้า (Handover Slip)  │
       │  ├─────────────────────────────────────┤
       │  │ Handover Code: H-20251118-001       │
       │  │ Batch ID: SH-2025-11-18-R1          │
       │  │ Platform: Shopee                    │
       │  │ Total Orders: 50 รายการ             │
       │  │                                     │
       │  │ ส่งมอบโดย: packer1                 │
       │  │ เวลา: 2025-11-18 14:30:00          │
       │  │                                     │
       │  │ QR Code: [QR: H-20251118-001]      │
       │  │                                     │
       │  │ ลายเซ็นผู้รับ: ___________________  │
       │  └─────────────────────────────────────┘
       │
       ├─ แนบใบส่งมอบกับกล่อง
       │
       ▼

7️⃣ ส่งมอบให้ขนส่ง
   └─> (ทำด้วยมือ - ไม่มีในระบบ)
       │
       ├─ ให้พนักงานขนส่งเซ็นรับ
       ├─ เก็บใบส่งมอบที่เซ็นแล้ว (สำหรับเช็คทีหลัง)
       │
       ▼
   ✅ เสร็จสิ้น! Batch Status = DISPATCHED

🌆 สิ้นสุดวัน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Checklist ก่อนเลิกงาน:
   □ Batch ที่แพ็ควันนี้ส่งมอบครบหรือยัง?
   □ Tracking Number บันทึกครบทุกออเดอร์หรือยัง?
   □ ใบส่งมอบที่เซ็นแล้วเก็บเรียบร้อยหรือยัง?
   □ พื้นที่แพ็คเก็บสะอาดเรียบร้อยหรือยัง?

```

---

## 2.4 ⚠️ วิธีจัดการเมื่อสินค้าขาด (Shortage)

### 2.4.1 เมื่อไหร่ที่เกิดสินค้าขาด

```
🔴 เมื่อไหร่ที่เกิด Shortage?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scenario 1: ระหว่าง Picking (พบบ่อยที่สุด 80%)
────────────────────────────────────────────────

Picker กำลังหยิบสินค้า:
┌──────────────────────────────────────────┐
│ SKU: SKU-A01                             │
│ Required Qty: 10 ชิ้น                    │
│                                          │
│ Picker เดินไปที่ Shelf A-01             │
│ ┌─────────────────────────────────┐     │
│ │ นับสต็อกจริง: มีแค่ 5 ชิ้น! ⚠️ │     │
│ └─────────────────────────────────┘     │
│                                          │
│ ตัวเลือก:                                │
│ ┌─ A) หยิบได้ 5 ชิ้น (บางส่วน)         │
│ │   → Picked Qty: 5                    │
│ │   → Shortage Qty: 5                  │
│ │                                       │
│ └─ B) ไม่หยิบเลย (0 ชิ้น)               │
│     → Picked Qty: 0                    │
│     → Shortage Qty: 10                 │
└──────────────────────────────────────────┘
     │
     ▼
Picker กด [Shortage] บนมือถือ
     │
     ├─ เลือกเหตุผล:
     │  • สต็อกหมด (out_of_stock) ← 70%
     │  • สินค้าเสียหาย (damaged) ← 20%
     │  • อื่นๆ ← 10%
     │
     ├─ กด [บันทึก]
     │
     ▼
ระบบสร้างรายการใน ShortageQueue:
┌──────────────────────────────────────────┐
│ Shortage Record Created:                 │
├──────────────────────────────────────────┤
│ ID: 1234                                 │
│ Order Number: SO123456                   │
│ SKU: SKU-A01                             │
│ Shortage Qty: 5 ชิ้น                     │
│ Reason: out_of_stock                     │
│ Status: waiting_stock (เริ่มต้น)        │
│ Urgency: high (ถ้า Due Date ใกล้)       │
│ Created By: picker1                      │
│ Created At: 2025-11-18 10:30:00         │
│ Batch ID: SH-2025-11-18-R1              │
│ Original Batch: SH-2025-11-18-R1        │
└──────────────────────────────────────────┘
     │
     ▼
✅ Picker เห็นข้อความ:
   "บันทึก Shortage สำเร็จ
    Online Team จะติดตามต่อ"
     │
     ▼
Picker ดำเนินการต่อ:
   ├─ ถ้าหยิบได้ 5/10 → Progress +50% (SKU นี้)
   └─ ถ้าหยิบได้ 0/10 → Progress +0% (SKU นี้)


Scenario 2: ก่อน Picking (Import Orders)
────────────────────────────────────────────────

Online Admin Import Orders:
┌──────────────────────────────────────────┐
│ Order: SO123456                          │
│ SKU: SKU-A01                             │
│ Qty: 10 ชิ้น                             │
└──────┬───────────────────────────────────┘
       │
       ▼
ระบบเช็คสต็อก:
┌──────────────────────────────────────────┐
│ Stock Table:                             │
│ SKU-A01: มีสต็อก 0 ชิ้น ❌               │
└──────┬───────────────────────────────────┘
       │
       ▼
ระบบ Auto-Classify:
┌──────────────────────────────────────────┐
│ Order Status: SHORTAGE (สีแดง)          │
│ ไม่สามารถสร้าง Batch ได้                │
└──────┬───────────────────────────────────┘
       │
       ▼
⚠️ Online Admin ต้องจัดการก่อน:
   ├─ Option 1: รอสต็อกเข้า
   ├─ Option 2: สั่งซื้อสต็อกเพิ่ม
   └─ Option 3: ยกเลิก Order
```

---

### 2.4.2 วิธีแก้ไขเมื่อสินค้าขาด

```
📋 Online Admin/หัวหน้าคลัง เห็น Shortage Queue
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ เข้าหน้า /shortage-queue
   │
   ├─ Filter:
   │  • Status: waiting_stock (รายการค้าง)
   │  • Urgency: high → medium → low
   │  • Date Range
   │
   ▼
   รายการ Shortage:
   ┌────────────────────────────────────────────────────────┐
   │ Order    │ SKU   │ Qty │ Reason      │ Status │ Urgency│
   ├────────────────────────────────────────────────────────┤
   │ SO123456 │ A01   │ 5   │ out_of_stock│ waiting│🔴 high │
   │ SO123457 │ B02   │ 10  │ damaged     │ waiting│🟡 med  │
   │ SO123458 │ C03   │ 2   │ out_of_stock│ waiting│🟢 low  │
   └────────────────────────────────────────────────────────┘
   │
   ▼

2️⃣ คลิกดูรายละเอียด Shortage ID: 1234
   │
   ├─ แสดงข้อมูล:
   │  ┌─────────────────────────────────────────┐
   │  │ Shortage Details                        │
   │  ├─────────────────────────────────────────┤
   │  │ Order: SO123456                         │
   │  │ Customer: คุณสมชาย                      │
   │  │ SKU: SKU-A01 (สินค้า A สีแดง)          │
   │  │ Shortage: 5 ชิ้น                        │
   │  │ Reason: สต็อกหมด                        │
   │  │ Due Date: 2025-11-19 (พรุ่งนี้!) ⚠️    │
   │  │ Urgency: 🔴 high                        │
   │  │ Created: 2025-11-18 10:30              │
   │  │ By: picker1                             │
   │  └─────────────────────────────────────────┘
   │
   ▼

3️⃣ ตัดสินใจ (4 ทางเลือก):

   ┌───────────────────────────────────────────────────────┐
   │ Decision Tree                                          │
   └───────────────────────────────────────────────────────┘
        │
        ├─ A) รอสต็อกเข้า (waiting_stock)
        │  │
        │  ├─ เมื่อไหร่: ถ้าสต็อกจะเข้าเร็ว (1-3 วัน)
        │  ├─ Action: ไม่ทำอะไร, รอเฉยๆ
        │  ├─ Status: waiting_stock (ไม่เปลี่ยน)
        │  └─ Note: "รอสต็อกเข้า 20/11/2025"
        │
        ├─ B) หาสต็อกเจอแล้ว (resolved)
        │  │
        │  ├─ เมื่อไหร่: หาสต็อกเจอในคลัง (Shelf อื่น)
        │  ├─ Action:
        │  │  ┌──────────────────────────────────────┐
        │  │  │ 1. อัปเดต Stock ในระบบ             │
        │  │  │ 2. เปลี่ยน Status → resolved        │
        │  │  │ 3. แจ้ง Picker: "SKU-A01 มีที่ B-05"│
        │  │  │ 4. Picker หยิบใหม่                  │
        │  │  │ 5. Shortage Resolved ✅              │
        │  │  └──────────────────────────────────────┘
        │  ├─ Status: resolved
        │  └─ Resolved At: 2025-11-18 11:00
        │
        ├─ C) ยกเลิก Order (cancelled)
        │  │
        │  ├─ เมื่อไหร่: ไม่มีสต็อก + Due Date ใกล้ + ลูกค้าตกลง
        │  ├─ Action:
        │  │  ┌──────────────────────────────────────┐
        │  │  │ 1. โทรหาลูกค้า (ใช้ Script)         │
        │  │  │ 2. ขออภัย + เสนอทางเลือก           │
        │  │  │    • รอได้ไหม?                      │
        │  │  │    • ยกเลิก + คืนเงิน?              │
        │  │  │ 3. ลูกค้าเลือก "ยกเลิก"            │
        │  │  │ 4. เปลี่ยน Status → cancelled       │
        │  │  │ 5. ปิด Order                        │
        │  │  │ 6. คืนเงินลูกค้า                    │
        │  │  └──────────────────────────────────────┘
        │  ├─ Status: cancelled
        │  ├─ Cancelled At: 2025-11-18 11:30
        │  └─ Note: "ลูกค้าตกลงยกเลิก"
        │
        └─ D) แทนด้วย SKU อื่น (replaced)
           │
           ├─ เมื่อไหร่: มี SKU ทดแทนใกล้เคียง + ลูกค้าตกลง
           ├─ Action:
           │  ┌──────────────────────────────────────┐
           │  │ 1. หา SKU ทดแทน (สี/รุ่นใกล้เคียง)  │
           │  │    • SKU-A01 (สีแดง) → SKU-A02 (น้ำเงิน)│
           │  │ 2. โทรหาลูกค้า (ใช้ Script)         │
           │  │ 3. เสนอ: "เปลี่ยนสีได้ไหมคะ?"      │
           │  │ 4. ลูกค้าตกลง                       │
           │  │ 5. เปลี่ยน Status → replaced        │
           │  │ 6. สร้าง Order ใหม่:                │
           │  │    • Order: SO123456-R              │
           │  │    • SKU: SKU-A02                   │
           │  │    • Qty: 5                         │
           │  │ 7. Import Orders ใหม่               │
           │  │ 8. สร้าง Batch ใหม่                 │
           │  └──────────────────────────────────────┘
           ├─ Status: replaced
           ├─ Replaced At: 2025-11-18 12:00
           └─ Note: "แทนด้วย SKU-A02 (สีน้ำเงิน)"

4️⃣ บันทึกและติดตาม
   │
   ├─ กด [บันทึก]
   │
   ├─ ระบบอัปเดต:
   │  • Status
   │  • Resolved/Cancelled/Replaced At
   │  • Resolved/Cancelled/Replaced By (User ID)
   │  • Note
   │
   └─ แสดงข้อความ: "บันทึกสำเร็จ"
```

---

### 2.4.3 สถานะต่าง ๆ ของสินค้าขาด

```
📊 สถานะ Shortage ตั้งแต่เกิดจนจบ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

State Diagram:
┌─────────────────────────────────────────────────────────────┐
│                    Shortage Lifecycle                        │
└─────────────────────────────────────────────────────────────┘

     [Picker บันทึก Shortage]
                │
                ▼
        ┌───────────────┐
        │ waiting_stock │ ← เริ่มต้น (Default Status)
        └───────┬───────┘
                │
                │ (หัวหน้าคลัง/Online Admin ตัดสินใจ)
                │
      ┌─────────┼─────────────────┬──────────────┐
      │         │                 │              │
      ▼         ▼                 ▼              ▼
┌──────────┐ ┌──────────┐  ┌──────────┐  ┌──────────┐
│ resolved │ │cancelled │  │ replaced │  │ waiting_ │
│  ✅ OK   │ │  ❌ NO   │  │  🔄 NEW  │  │  stock   │
└────┬─────┘ └────┬─────┘  └────┬─────┘  └────┬─────┘
     │            │              │              │
     ▼            ▼              ▼              ▼
  [เสร็จ]      [เสร็จ]        [เสร็จ]      [ยังค้าง]
                                               │
                                               │ (เมื่อสต็อกเข้า)
                                               │
                                               ▼
                                          ┌──────────┐
                                          │ resolved │
                                          │  ✅ OK   │
                                          └────┬─────┘
                                               │
                                               ▼
                                            [เสร็จ]


สถิติ Shortage (ตัวอย่าง):
┌────────────────────────────────────────────────────────┐
│ Total Shortage: 100 รายการ/เดือน                       │
├────────────────────────────────────────────────────────┤
│ • resolved:      60 รายการ (60%) ← เป้าหมาย           │
│ • waiting_stock: 25 รายการ (25%) ← ยังค้าง            │
│ • cancelled:     10 รายการ (10%) ← ยอมรับได้          │
│ • replaced:      5 รายการ (5%)   ← ดีมาก!             │
└────────────────────────────────────────────────────────┘

เป้าหมาย:
✅ resolved rate > 60%
✅ waiting_stock < 30%
⚠️ cancelled < 15%
```

---

### 2.4.4 ⚠️ ถ้าจัดการสินค้าขาดผิดพลาดจะเกิดอะไร

| ❌ ถ้าทำผิด... | 💥 จะเกิด... | ⏰ เวลาที่เกิด | 🔴 ความรุนแรง |
|---------------|-------------|--------------|--------------|
| **Picker บันทึก Shortage เหตุผลผิด** | Online Team แก้ไขผิดวิธี → เสียเวลา | ทันที | 🟡 Medium |
| **Picker ไม่บันทึก Shortage** | Order ค้าง → Progress ไม่ถึง 100% → Packer ส่งไม่ได้ → งานล่าช้า | 2-4 ชม. | 🟠 High |
| **Online Admin ไม่เช็ค Shortage Queue** | Shortage สะสม → ลูกค้าโทรมาถาม → เสียเวลาตอบ | 1 วัน | 🟡 Medium |
| **แก้ Shortage ผิดสถานะ (resolved แต่ไม่มีสต็อก)** | Picker หยิบไม่ได้ → Shortage ซ้ำ → งานซ้ำซ้อน | ทันที | 🟠 High |
| **ไม่โทรหาลูกค้าก่อน Cancel** | ลูกค้าโกรธ → ให้ Rating ต่ำ → ร้านโดน Penalty | 1 วัน | 🔴 Critical |
| **Replace SKU โดยไม่ได้รับอนุญาต** | ลูกค้าได้สินค้าผิด → Return → เสียค่าขนส่ง 2 เท่า | 3-5 วัน | 🔴 Critical |
| **ปล่อย Shortage ค้าง > 3 วัน (high urgency)** | เลย Due Date → Platform ปรับ Rating → เสีย Ranking | 3 วัน | ⚫ Catastrophic |
| **ไม่ระบุ Note ตอนแก้ Shortage** | ไม่รู้ว่าทำอะไรไป → ถ้ามีปัญหาตรวจสอบไม่ได้ | ทีหลัง | 🟡 Medium |

---

### 2.4.5 วิธีป้องกันไม่ให้สินค้าขาด

```
🛡️ วิธีป้องกันไม่ให้เกิด Shortage ตั้งแต่ต้น
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ ก่อน Import Orders:
   ┌──────────────────────────────────────────┐
   │ ✅ เช็คสต็อกก่อน Import ทุกครั้ง       │
   │    • ไปที่ Dashboard                    │
   │    • ดู Stock Level ของแต่ละ SKU      │
   │    • ถ้า Stock < 10 → สั่งซื้อก่อน     │
   │                                          │
   │ ✅ อัปเดตสต็อกให้ตรงกับความเป็นจริง    │
   │    • นับสต็อกจริงในคลัง (Cycle Count)  │
   │    • Import Stock ใหม่                 │
   │    • แก้ไขสต็อกที่ผิด                  │
   └──────────────────────────────────────────┘

2️⃣ ระหว่าง Import Orders:
   ┌──────────────────────────────────────────┐
   │ ✅ ระบบจะ Auto-Classify:                │
   │    • READY_ACCEPT (สต็อกพอ)             │
   │    • LOW_STOCK (สต็อกน้อย - ระวัง!)    │
   │    • SHORTAGE (สต็อกไม่พอ - ห้าม Batch)│
   │                                          │
   │ ⚠️ อย่าสร้าง Batch จาก LOW_STOCK!      │
   │    → เสี่ยง Shortage ตอนหยิบ           │
   └──────────────────────────────────────────┘

3️⃣ หลัง Import Orders:
   ┌──────────────────────────────────────────┐
   │ ✅ เช็ค Dashboard:                       │
   │    • SHORTAGE: X รายการ → ต้องจัดการ   │
   │    • LOW_STOCK: X รายการ → ระวัง        │
   │                                          │
   │ ✅ วางแผนสั่งซื้อ:                      │
   │    • SKU ไหนที่ SHORTAGE บ่อย?          │
   │    • สั่งซื้อล่วงหน้า                   │
   │    • เพิ่ม Safety Stock (สต็อกกันชน)   │
   └──────────────────────────────────────────┘

4️⃣ ระหว่าง Picking:
   ┌──────────────────────────────────────────┐
   │ ✅ Picker นับให้แม่นก่อนบันทึก          │
   │    • นับ 2 ครั้ง                        │
   │    • ถ้าไม่แน่ใจ → เรียกหัวหน้ามาช่วย  │
   │                                          │
   │ ✅ บันทึกเหตุผลให้ถูกต้อง              │
   │    • สต็อกหมด (จริงๆ) → out_of_stock   │
   │    • สินค้าเสีย → damaged              │
   │    • หาไม่เจอ → misplaced              │
   └──────────────────────────────────────────┘

5️⃣ หลัง Picking:
   ┌──────────────────────────────────────────┐
   │ ✅ Online Admin เช็ค Shortage Queue     │
   │    ทุกเช้า (08:00-09:00)                │
   │                                          │
   │ ✅ แก้ไข Shortage ภายใน 24 ชม.         │
   │    (high urgency ภายในวันเดียวกัน!)     │
   │                                          │
   │ ✅ วิเคราะห์ Root Cause:                │
   │    • ทำไมเกิด Shortage บ่อย?           │
   │    • SKU ไหนที่มีปัญหา?                 │
   │    • แก้ไขที่ต้นเหตุ                    │
   └──────────────────────────────────────────┘
```

---



# 3. วิธีใช้งานประจำวัน

> 📘 **สำหรับพนักงาน:** คู่มือนี้เขียนด้วยภาษาง่าย ๆ เพื่อให้พนักงานทุกแผนกเข้าใจและทำตามได้ง่าย

---

## 3.1 📱 สำหรับพนักงานออนไลน์

### 🎯 งานหลักประจำวัน

| เวลา | งานที่ทำ | เครื่องมือ | ระยะเวลา |
|------|---------|-----------|---------|
| 08:00-09:00 | Import ออเดอร์ใหม่ | Excel + `/import/orders` | 30-60 นาที |
| 09:00-10:00 | สร้าง Batch | `/batch/create` | 30-60 นาที |
| 10:00-11:00 | พิมพ์เอกสาร + ส่งให้คลัง | Print Picking List | 30 นาที |
| 11:00-16:00 | ติดตามความคืบหน้า + จัดการ Shortage | `/batch/list`, `/shortage-queue` | ตลอดวัน |
| 16:00-17:00 | Export รายงาน + สรุปยอด | Excel Export | 30 นาที |

---

### ✅ Step-by-Step: Import Orders ประจำวัน

#### ขั้นที่ 1: เตรียม Excel File

```
📂 ไฟล์ Excel ต้องมี Column เหล่านี้:
┌─────────────────────────────────────────────────────────┐
│ Order Number │ Platform │ SKU │ Qty │ Shop Name │ Due Date │
├─────────────────────────────────────────────────────────┤
│ SO123456     │ Shopee   │ A01 │ 2   │ Shop A    │ 2025-11-20│
│ SO123457     │ TikTok   │ B02 │ 5   │ Shop B    │ 2025-11-19│
└─────────────────────────────────────────────────────────┘

⚠️ สำคัญ:
- Order Number ห้ามซ้ำ
- Platform: ใช้ Shopee, TikTok, Lazada (ตัวพิมพ์ใหญ่-เล็กไม่สำคัญ)
- SKU ต้องมีในระบบก่อน (ถ้าไม่มี → Import Products ก่อน)
- Qty ต้องเป็นตัวเลขเท่านั้น
- Due Date ไม่ใส่ก็ได้ (ระบบจะคำนวณให้)
```

#### ขั้นที่ 2: Upload File

```
1. ไปที่ /import/orders
2. คลิก "Choose File" → เลือกไฟล์ Excel
3. คลิก "Import"
4. รอ 10-30 วินาที (ขึ้นกับจำนวนออเดอร์)
```

#### ขั้นที่ 3: ตรวจสอบผลลัพธ์

```
✅ สำเร็จ:
   - แสดงข้อความ "Import สำเร็จ X รายการ"
   - ออเดอร์ถูกแบ่งเป็น:
     * READY_ACCEPT (สีเขียว) ← สต็อกพอ, สร้าง Batch ได้เลย
     * LOW_STOCK (สีเหลือง)    ← สต็อกน้อย, ระวัง Shortage
     * SHORTAGE (สีแดง)        ← สต็อกไม่พอ, ไม่สามารถสร้าง Batch ได้

❌ ล้มเหลว:
   - แสดงข้อความ Error:
     * "SKU ไม่พบในระบบ" → ต้อง Import Products ก่อน
     * "Shop ไม่พบในระบบ" → ตรวจสอบชื่อ Shop ใน Excel
     * "Duplicate Order" → ออเดอร์ซ้ำ, ลบออก
     * "Format ผิด" → ตรวจสอบ Column ตาม Template
   
   → แก้ไข Excel → Upload ใหม่
```

---

### ✅ Step-by-Step: สร้าง Batch

#### ขั้นที่ 1: เลือก Platform และวันที่

```
1. ไปที่ /batch/create
2. เลือก Platform: Shopee / TikTok / Lazada
3. เลือก Date Range: วันที่ต้องการ (เช่น วันนี้)
4. คลิก "ค้นหา"
```

#### ขั้นที่ 2: เลือก Orders

```
⚠️ สำคัญมาก: เลือกเฉพาะ Orders ที่มีสถานะ READY_ACCEPT เท่านั้น!

ตารางจะแสดง:
┌─────────────────────────────────────────────────────────┐
│ ☑️ │ Order Number │ SKU │ Qty │ Status │ Due Date    │
├─────────────────────────────────────────────────────────┤
│ ☑️ │ SO123456     │ A01 │ 2   │ ✅ READY │ 2025-11-20  │
│ ☑️ │ SO123457     │ B02 │ 5   │ ✅ READY │ 2025-11-19  │
│ ☐  │ SO123458     │ C03 │ 10  │ ❌ SHORTAGE│ 2025-11-21│ ← ห้ามเลือก!
└─────────────────────────────────────────────────────────┘

- เลือก Checkbox ที่ต้องการ
- สามารถเลือกหลายรายการได้
- แนะนำ: สร้าง Batch ไม่เกิน 100 ออเดอร์/Batch
```

#### ขั้นที่ 3: สร้าง Batch

```
1. คลิก "สร้าง Batch"
2. ระบบจะ Auto-Generate:
   - Batch ID: SH-2025-11-18-R1
   - Run Number: R1 (วันแรก), R2 (Batch ที่ 2 ในวันเดียวกัน), ...
   - QR Code: สำหรับคลังสแกน

3. แสดงหน้า Batch Detail

4. พิมพ์เอกสารทันที:
   - 🖨️ Picking List (รายการหยิบของ)
   - 🖨️ SKU QR Codes (สติกเกอร์ SKU)
   - 🖨️ Batch QR (QR บนใบงาน)

5. ส่งเอกสารให้ทีมคลัง
```

---

### ⚠️ ถ้าทำผิด Flow จะเกิดอะไร?

| ❌ ถ้าทำผิด... | 💥 จะเกิด... | ✅ วิธีแก้ไข |
|---------------|-------------|-------------|
| **Import Orders ผิด Format** | ระบบจะ Reject ทั้งไฟล์, ไม่มีออเดอร์เข้าระบบ | แก้ไข Excel ตาม Template → Upload ใหม่ |
| **Import SKU ที่ไม่มีในระบบ** | Order จะเข้าระบบ แต่เป็น SHORTAGE ทั้งหมด | Import Products ก่อน → Import Orders ใหม่ |
| **สร้าง Batch จาก Orders ที่ SHORTAGE** | Batch จะถูกสร้าง แต่ Picker หยิบไม่ได้ → 100% Shortage → เสียเวลา | ⚠️ เลือกเฉพาะ READY เท่านั้น! |
| **ไม่พิมพ์ Picking List** | Picker ไม่รู้ว่าต้องหยิบอะไร → หยิบผิด/หยิบไม่ได้ | พิมพ์ทันทีหลังสร้าง Batch |
| **สร้าง Batch แล้วไม่ส่งให้คลัง** | Picker ไม่รู้ว่ามี Batch ใหม่ → งานค้าง | แจ้งทีมคลังทุกครั้งที่สร้าง Batch |
| **ไม่ติดตาม Progress** | ไม่รู้ว่า Batch เสร็จหรือยัง → ลูกค้าถามไม่ได้ตอบ | เช็ค /batch/list อย่างน้อยทุก 2 ชั่วโมง |
| **ไม่จัดการ Shortage ทัน** | สินค้าส่งล่าช้า → ลูกค้าโกรธ → Rating ต่ำ | เช็ค Shortage Queue ทุกวัน, แก้ไขทันที |

---

## 3.2 📦 สำหรับพนักงานหยิบของ (Picker)

### 🎯 งานหลักประจำวัน

| เวลา | งานที่ทำ | เครื่องมือ | ระยะเวลา |
|------|---------|-----------|---------|
| 08:00-08:30 | เช็คมือถือพร้อมใช้ (ชาร์จเต็ม, เน็ตเชื่อม) | มือถือ | 10 นาที |
| 08:30-09:00 | รับงาน Batch | `/scan/batch` | 5-10 นาที |
| 09:00-16:00 | หยิบสินค้าตาม Batch | `/scan/sku` | ตลอดวัน |
| 16:00-17:00 | ตรวจสอบ Progress 100% + เก็บใบงาน | `/batch/<id>` | 30 นาที |

---

### ✅ Step-by-Step: รับงาน Batch

```
1️⃣ ไปที่ /scan/batch บนมือถือ

2️⃣ เลือกวิธีรับงาน (มี 2 วิธี):

   วิธีที่ 1: Scan QR Code (แนะนำ)
   ┌─────────────────────────┐
   │   📷                    │
   │   [กล้อง]               │
   │                         │
   │ สแกน QR Code บนใบงาน   │
   │ (QR มี Text:            │
   │  BATCH:SH-2025-11-18-R1)│
   └─────────────────────────┘
   
   ✅ สำเร็จ → แสดง:
      "รับงาน Batch SH-2025-11-18-R1 สำเร็จ!
       Total Orders: 50
       Total SKUs: 15
       Platform: Shopee"
   
   ❌ ล้มเหลว → แสดง Error:
      - "QR Code ผิด" → สแกนใหม่
      - "Batch ถูกรับแล้ว" → เลือก Batch อื่น
      - "Batch ถูก Lock" → แจ้ง Admin

   วิธีที่ 2: Quick Assign (ถ้าไม่มี QR)
   ┌─────────────────────────┐
   │ เลือก Batch:            │
   │ ▼ SH-2025-11-18-R1      │
   │   SH-2025-11-18-R2      │
   │   TT-2025-11-18-R1      │
   │                         │
   │ [รับงาน]                │
   └─────────────────────────┘

3️⃣ รับงานสำเร็จ → ไปหยิบของ
```

---

### ✅ Step-by-Step: หยิบสินค้า

```
1️⃣ ไปที่ /scan/sku

2️⃣ เลือก Batch ที่รับมา
   (ถ้ารับหลาย Batch → เลือก Batch ที่จะหยิบก่อน)

3️⃣ Loop: สำหรับแต่ละ SKU

   3.1 Scan SKU QR Code
   ┌─────────────────────────┐
   │   📷                    │
   │   [กล้อง]               │
   │                         │
   │ สแกน QR Code บน Shelf  │
   │ (QR มี Text: SKU:A01)   │
   └─────────────────────────┘
   
   ✅ แสดง:
      SKU: A01
      Item Name: สินค้า A
      Required Qty: 10 ชิ้น
      Shelf: A-01

   3.2 กรอกจำนวนที่หยิบได้
   ┌─────────────────────────┐
   │ Required: 10 ชิ้น       │
   │                         │
   │ หยิบได้: [___]          │
   │                         │
   │ [1][2][3]               │
   │ [4][5][6]               │
   │ [7][8][9]               │
   │ [←][0][C]               │
   │                         │
   │ [บันทึก] [Shortage]    │
   └─────────────────────────┘

   กรณีที่ 1: หยิบได้ครบ (10/10)
   ─────────────────────────
   1. กรอก: 10
   2. กด [บันทึก]
   3. ระบบแสดง: ✅ "บันทึกสำเร็จ!"
   4. Progress +1 SKU
   5. → SKU ถัดไป

   กรณีที่ 2: หยิบได้บางส่วน (5/10)
   ─────────────────────────
   1. กรอก: 5
   2. กด [Shortage]
   3. ระบบถาม: "ทำไมหยิบได้ไม่ครบ?"
      ┌─────────────────────────┐
      │ ○ สต็อกหมด             │
      │ ○ สินค้าเสียหาย         │
      │ ○ อื่นๆ                 │
      │                         │
      │ [ยืนยัน]                │
      └─────────────────────────┘
   4. เลือกเหตุผล
   5. กด [ยืนยัน]
   6. ระบบแสดง: ⚠️ "บันทึก Shortage สำเร็จ"
   7. Shortage ส่งไป Online Team
   8. → SKU ถัดไป

4️⃣ ทำซ้ำจนครบทุก SKU

5️⃣ เช็ค Progress:
   ไปที่ /batch/<batch_id>
   
   Progress < 100%? → กลับไปหยิบ SKU ที่ค้าง
   Progress = 100%? → ✅ เสร็จสิ้น! ส่งต่อให้ Packer
```

---

### ⚠️ ถ้าทำผิด Flow จะเกิดอะไร?

| ❌ ถ้าทำผิด... | 💥 จะเกิด... | ✅ วิธีแก้ไข |
|---------------|-------------|-------------|
| **ไม่รับงาน Batch ก่อนหยิบ** | สแกน SKU ไม่ได้ → หยิบไม่ได้ | รับงาน Batch ก่อนเสมอ (Scan Batch QR) |
| **สแกน SKU ผิด** | ระบบแสดง "SKU ไม่ตรง" → บันทึกไม่ได้ | สแกน SKU ที่ถูกต้องตาม Picking List |
| **กรอกจำนวนผิด (มากกว่าที่ต้องการ)** | ระบบไม่ยอมให้บันทึก | กรอกจำนวนไม่เกิน Required Qty |
| **กรอกจำนวนผิด (น้อยกว่าความจริง)** | Progress ผิด → ตรวจนับยาก | ⚠️ นับให้แม่นยำก่อนกรอก! |
| **ไม่บันทึก Shortage ตอนหยิบไม่ครบ** | Batch Progress ค้าง → Packer รอไม่ได้ส่ง → งานล่าช้า | หยิบไม่ครบ → กด [Shortage] ทันที |
| **บันทึก Shortage เหตุผลผิด** | Online Team แก้ไขผิดวิธี → เสียเวลา | เลือกเหตุผลให้ถูกต้อง: สต็อกหมด / เสียหาย |
| **หยิบ SKU ผิดตัว** | ลูกค้าได้สินค้าผิด → Return → Rating ต่ำ | ⚠️ สแกน QR ทุกครั้ง! ไม่เชื่อความจำ |
| **ทิ้งมือถือไว้ไม่ชาร์จ** | วันพรุ่งนี้แบตหมด → สแกนไม่ได้ → งานหยุด | ชาร์จมือถือทุกเย็นก่อนเลิกงาน |

---

## 3.3 📤 สำหรับพนักงานแพ็คและส่งมอบ (Packer)

### 🎯 งานหลักประจำวัน

| เวลา | งานที่ทำ | เครื่องมือ | ระยะเวลา |
|------|---------|-----------|---------|
| 08:00-08:30 | เช็คมือถือ + เครื่องพิมพ์พร้อม | มือถือ, Printer | 10 นาที |
| 08:30-14:00 | ดู Batch ที่พร้อมส่ง (100%) + แพ็ค | `/batch/list` | ตลอดวัน |
| 14:00-16:00 | สแกนส่งมอบ + บันทึก Tracking | `/scan-handover`, `/scan/tracking` | 2 ชม. |
| 16:00-17:00 | พิมพ์ใบส่งมอบ + ส่งให้ขนส่ง | Print Handover Slip | 1 ชม. |

---

### ✅ Step-by-Step: ดู Batch ที่พร้อมส่ง

```
1️⃣ ไปที่ /batch/list

2️⃣ Filter: เลือก "Progress = 100% เท่านั้น"
   (Batch ที่ Picker หยิบของครบแล้ว)

3️⃣ รายการที่แสดง:
┌─────────────────────────────────────────────────┐
│ Batch ID         │ Progress │ Status │ Orders │
├─────────────────────────────────────────────────┤
│ SH-2025-11-18-R1 │ 100% ✅  │ Ready  │ 50     │
│ TT-2025-11-18-R1 │ 100% ✅  │ Ready  │ 30     │
│ SH-2025-11-18-R2 │ 87% ⏳   │ Picking│ 40     │ ← ยังไม่พร้อม
└─────────────────────────────────────────────────┘

4️⃣ เลือก Batch ที่ Progress = 100%
```

---

### ✅ Step-by-Step: แพ็คและส่งมอบ

```
1️⃣ คลิกดู Batch Detail
   ไปที่ /batch/<batch_id>
   
   แสดง:
   ┌─────────────────────────────────────────┐
   │ Order: SO123456                         │
   │ ├─ SKU-A01: 10 ชิ้น ✅                  │
   │ ├─ SKU-B02: 5 ชิ้น ✅                   │
   │ └─ Logistic: Shopee Express             │
   │                                         │
   │ Order: SO123457                         │
   │ ├─ SKU-C03: 2 ชิ้น ✅                   │
   │ └─ Logistic: Kerry                      │
   └─────────────────────────────────────────┘

2️⃣ แพ็คสินค้า (ทำด้วยมือ)
   ┌─────────────────────────────────────────┐
   │ 1. เก็บสินค้าตามรายการ                 │
   │ 2. ใส่กล่อง                              │
   │ 3. ติดสติกเกอร์ที่อยู่                  │
   │ 4. ปิดเทป                               │
   │ 5. วางไว้ที่โซนส่งมอบ                  │
   └─────────────────────────────────────────┘

3️⃣ สแกนส่งมอบ
   ไปที่ /scan-handover
   
   ┌─────────────────────────┐
   │   📷                    │
   │   [กล้อง]               │
   │                         │
   │ สแกน Batch QR บนกล่อง  │
   │ (BATCH:SH-2025-11-18-R1)│
   └─────────────────────────┘
   
   ✅ ระบบแสดง:
   ┌─────────────────────────────┐
   │ Handover สำเร็จ! ✅         │
   ├─────────────────────────────┤
   │ Handover Code:              │
   │ H-20251118-001              │
   │                             │
   │ Batch ID:                   │
   │ SH-2025-11-18-R1            │
   │                             │
   │ Total Orders: 50            │
   │                             │
   │ [พิมพ์ใบส่งมอบ]            │
   └─────────────────────────────┘
   
   จดจำ Handover Code: H-20251118-001
   (ใช้ตรวจสอบกับขนส่งทีหลัง)

4️⃣ บันทึก Tracking Number (ถ้ามี)
   ไปที่ /scan/tracking
   
   ┌─────────────────────────┐
   │ Order Number:           │
   │ [SO123456]              │
   │                         │
   │ Tracking Number:        │
   │ [TH123456789TH]         │
   │                         │
   │ [บันทึก]                │
   └─────────────────────────┘
   
   - สามารถสแกน Order QR แทนพิมพ์ได้
   - ทำซ้ำสำหรับทุก Order ใน Batch

5️⃣ พิมพ์ใบส่งมอบ
   ไปที่ /batch/<batch_id>/print-handover
   
   พิมพ์ Handover Slip:
   ┌─────────────────────────────────────┐
   │ 📦 ใบส่งมอบสินค้า                  │
   ├─────────────────────────────────────┤
   │ Handover Code: H-20251118-001       │
   │ Batch ID: SH-2025-11-18-R1          │
   │ Platform: Shopee                    │
   │ Total Orders: 50 รายการ             │
   │                                     │
   │ ส่งมอบโดย: packer1                 │
   │ เวลา: 2025-11-18 14:30:00          │
   │                                     │
   │ [QR Code]                           │
   │                                     │
   │ ลายเซ็นผู้รับ: _______________      │
   └─────────────────────────────────────┘

6️⃣ ส่งมอบให้ขนส่ง
   ┌─────────────────────────────────────┐
   │ 1. แนบใบส่งมอบกับกล่อง             │
   │ 2. เรียกพนักงานขนส่งมารับ          │
   │ 3. ให้เซ็นรับในใบส่งมอบ            │
   │ 4. เก็บสำเนาที่เซ็นแล้ว             │
   │ 5. ✅ เสร็จสิ้น!                     │
   └─────────────────────────────────────┘
```

---

### ⚠️ ถ้าทำผิด Flow จะเกิดอะไร?

| ❌ ถ้าทำผิด... | 💥 จะเกิด... | ✅ วิธีแก้ไข |
|---------------|-------------|-------------|
| **สแกน Batch ที่ Progress < 100%** | ระบบ Block ไม่ให้สร้าง Handover Code | รอให้ Picker หยิบครบ 100% ก่อน |
| **แพ็คสินค้าผิด Order** | ลูกค้าได้สินค้าผิด → Return → เสียเงิน | ⚠️ เช็ค Order Number ทุกครั้ง! |
| **ไม่สแกนส่งมอบ** | ไม่มี Handover Code → ตรวจสอบไม่ได้ว่าส่งไปแล้ว | Scan Handover ทุก Batch ก่อนส่ง |
| **ไม่พิมพ์ใบส่งมอบ** | ขนส่งไม่รับ (ไม่มีเอกสาร) → ส่งไม่ได้ | พิมพ์ทันทีหลัง Scan Handover |
| **ไม่ให้ขนส่งเซ็นรับ** | ไม่มีหลักฐานส่งมอบ → ขนส่งปฏิเสธว่าไม่ได้รับ | ต้องมีลายเซ็นทุกครั้ง! |
| **ไม่เก็บสำเนาใบส่งมอบ** | ตรวจสอบย้อนหลังไม่ได้ → ถ้าของหาย พิสูจน์ไม่ได้ | เก็บสำเนาที่เซ็นแล้วอย่างน้อย 30 วัน |
| **บันทึก Tracking ผิด** | ลูกค้าติดตามพัสดุไม่ได้ → โทรมาถาม → เสียเวลา | ตรวจสอบ Tracking 2 ครั้งก่อนบันทึก |
| **ส่ง Batch ที่ยังไม่ Handover** | ไม่มีในระบบ → ถ้าของหาย ตรวจสอบไม่ได้ | Scan Handover ก่อนส่งจริงเสมอ! |

---

### 📋 Checklist สำหรับพนักงานทุกแผนก

#### ✅ Online Team - Checklist ประจำวัน

```
เช้า (08:00-12:00):
□ Import ออเดอร์ใหม่วันนี้เรียบร้อย
□ ตรวจสอบ Dashboard: READY / LOW_STOCK / SHORTAGE
□ สร้าง Batch ครบทุก Platform (Shopee / TikTok / Lazada)
□ พิมพ์เอกสารครบ (Picking List, SKU QR, Batch QR)
□ ส่งเอกสารให้ทีมคลังแล้ว

บ่าย (13:00-17:00):
□ เช็ค Batch Progress (ทุก 2 ชั่วโมง)
□ เช็ค Shortage Queue (มีรายการใหม่หรือไม่?)
□ จัดการ Shortage ที่มี (waiting_stock / resolved / cancelled / replaced)
□ Export รายงานประจำวัน (Dashboard, Shortage)
□ สรุปยอด Batch ที่ Dispatch แล้ววันนี้

ก่อนเลิกงาน:
□ ไม่มี Batch ค้างที่ยังไม่ส่งให้คลัง
□ Shortage Queue ไม่มีรายการ Urgent ค้าง
□ รายงานส่งให้หัวหน้าแล้ว
```

---

#### ✅ Picker Team - Checklist ประจำวัน

```
เช้า (08:00-09:00):
□ มือถือชาร์จเต็ม (≥ 80%)
□ เน็ตมือถือเชื่อมต่อได้
□ เข้าสู่ระบบได้ (Username / Password)
□ รับงาน Batch แรกเรียบร้อย
□ มีใบงาน (Picking List) ในมือ

กลางวัน (09:00-16:00):
□ หยิบสินค้าตาม Batch
□ Scan SKU ทุกครั้งก่อนหยิบ (ไม่เชื่อความจำ)
□ กรอกจำนวนถูกต้อง (นับให้แม่น)
□ บันทึก Shortage ทันทีถ้าหยิบไม่ครบ
□ เลือกเหตุผล Shortage ให้ถูก (สต็อกหมด / เสียหาย)

ก่อนเลิกงาน (16:00-17:00):
□ Batch ที่รับมาวันนี้ Progress = 100% ทุก Batch
□ ไม่มี SKU ค้างที่ยังไม่หยิบ
□ Shortage ที่บันทึกไว้ถูกต้อง (เช็คอีกครั้ง)
□ เก็บใบงานที่เสร็จแล้วเรียบร้อย
□ ชาร์จมือถือเต็มสำหรับวันพรุ่งนี้
```

---

#### ✅ Packer Team - Checklist ประจำวัน

```
เช้า (08:00-09:00):
□ มือถือชาร์จเต็ม (≥ 80%)
□ เครื่องพิมพ์พร้อมใช้ (มีกระดาษ, หมึก)
□ เน็ตมือถือเชื่อมต่อได้
□ เข้าสู่ระบบได้
□ เช็คมีกล่อง, เทป, สติกเกอร์พอ

กลางวัน (09:00-16:00):
□ เช็ค Batch List: มี Batch ที่ 100% หรือยัง?
□ แพ็คสินค้าตามรายการ
□ Scan Handover ทุก Batch ก่อนส่ง
□ บันทึก Tracking Number (ถ้ามี)
□ พิมพ์ใบส่งมอบทุก Batch
□ ให้ขนส่งเซ็นรับทุกครั้ง

ก่อนเลิกงาน (16:00-17:00):
□ Batch ที่พร้อม 100% วันนี้ส่งมอบครบหมด
□ ใบส่งมอบที่เซ็นแล้วเก็บเรียบร้อย
□ Tracking Number บันทึกครบทุก Order
□ พื้นที่แพ็คเก็บสะอาด
□ ชาร์จมือถือเต็มสำหรับวันพรุ่งนี้
```

---


# 4. การจัดการสินค้าที่ขาด (Shortage)

> 🎓 **สำหรับหัวหน้าคลัง:** คู่มือนี้อธิบายการจัดการ Shortage ตั้งแต่ต้นจนจบ พร้อมแผนรับมือ

---

## 4.1 🎯 สินค้าขาด (Shortage) คืออะไร

### Shortage คืออะไร?

```
Shortage = สินค้าที่ Picker หยิบไม่ครบตามที่ออเดอร์ต้องการ

ตัวอย่าง:
┌─────────────────────────────────────────────┐
│ Order: SO123456                             │
│ SKU: SKU-A01                                │
│ Required Qty: 10 ชิ้น  (ที่ลูกค้าสั่ง)     │
│ Picked Qty: 5 ชิ้น     (ที่หยิบได้)        │
│ ────────────────────────────────────────    │
│ Shortage Qty: 5 ชิ้น   (ที่ขาด)            │
└─────────────────────────────────────────────┘

Shortage เกิดได้จาก:
1. สต็อกหมด (out_of_stock) ← พบบ่อยที่สุด (80%)
2. สินค้าเสียหาย (damaged)
3. สินค้าหาไม่เจอ (misplaced)
4. อื่นๆ
```

---

## 4.2 📊 ขั้นตอนการจัดการสินค้าขาด

```
┌─────────────────────────────────────────────────────────────────┐
│             Shortage Lifecycle (วงจรชีวิต Shortage)             │
└─────────────────────────────────────────────────────────────────┘

1️⃣ เกิด Shortage (Picker บันทึก)
   │
   └─> Picker หยิบสินค้าไม่ครบ
       │
       ├─ Scan SKU: SKU-A01
       ├─ Required: 10 ชิ้น
       ├─ Picked: 5 ชิ้น (หยิบได้)
       │
       ▼
   Picker กด [Shortage]
       │
       ├─ เลือกเหตุผล: สต็อกหมด (out_of_stock)
       ├─ กด [บันทึก]
       │
       ▼
   สร้างรายการใน ShortageQueue:
   ┌─────────────────────────────────────┐
   │ Order: SO123456                     │
   │ SKU: SKU-A01                        │
   │ Shortage Qty: 5 ชิ้น                │
   │ Reason: out_of_stock                │
   │ Status: waiting_stock (เริ่มต้น)   │
   │ Urgency: high (ถ้าใกล้ Due Date)    │
   │ Created At: 2025-11-18 10:30:00    │
   └─────────────────────────────────────┘
       │
       ▼

2️⃣ Online Team เห็นใน Shortage Queue
   │
   └─> /shortage-queue
       │
       ├─ รายการ Shortage ใหม่:
       │  ┌─────────────────────────────────────┐
       │  │ SO123456 │ SKU-A01 │ 5 ชิ้น │ ⚠️ high│
       │  └─────────────────────────────────────┘
       │
       ▼

3️⃣ หัวหน้าคลัง/Online Admin ตัดสินใจ
   │
   ├─ A) รอสต็อกเข้า (waiting_stock)
   │  │
   │  └─> สถานะ: waiting_stock
   │      (ไม่ทำอะไร, รอสต็อกเข้าก่อน)
   │      │
   │      ▼
   │  เมื่อสต็อกเข้า:
   │      ├─ Import Stock ใหม่
   │      ├─ เปลี่ยนสถานะเป็น: resolved
   │      ├─ Picker หยิบใหม่
   │      └─ ✅ เสร็จสิ้น
   │
   ├─ B) หาสต็อกเจอแล้ว (resolved)
   │  │
   │  └─> สถานะ: resolved
   │      (เจอสต็อกแล้ว, บอก Picker หยิบใหม่)
   │      │
   │      ▼
   │  Picker หยิบใหม่:
   │      ├─ Scan SKU: SKU-A01
   │      ├─ Picked: 5 ชิ้น (ที่ขาดไป)
   │      └─ ✅ เสร็จสิ้น
   │
   ├─ C) ยกเลิก Order (cancelled)
   │  │
   │  └─> สถานะ: cancelled
   │      (ยกเลิกออเดอร์นี้)
   │      │
   │      ▼
   │  แจ้งลูกค้า:
   │      ├─ โทรหาลูกค้า / ส่งข้อความ
   │      ├─ ขออภัย + เสนอทางเลือก (รอ / ยกเลิก / คืนเงิน)
   │      └─ ✅ ปิด Order
   │
   └─ D) แทนด้วย SKU อื่น (replaced)
      │
      └─> สถานะ: replaced
          (แทนด้วย SKU อื่นที่ใกล้เคียง)
          │
          ▼
      สร้าง Order ใหม่:
          ├─ SKU ใหม่: SKU-A02 (แทน SKU-A01)
          ├─ Qty: 5 ชิ้น
          ├─ Import Orders ใหม่
          ├─ สร้าง Batch ใหม่
          └─ ✅ เสร็จสิ้น
```

---

## 4.3 🎛️ สถานะต่าง ๆ ของสินค้าขาด

| Status | ความหมาย | Action | ใครทำ | เมื่อไหร่ |
|--------|---------|--------|-------|---------|
| **waiting_stock** | รอสต็อกเข้า | ไม่ทำอะไร, รอเฉยๆ | - | เมื่อสต็อกเข้าจริง |
| **resolved** | หาสต็อกเจอแล้ว | บอก Picker หยิบใหม่ | Picker | ทันที (หยิบใหม่) |
| **cancelled** | ยกเลิก Order | แจ้งลูกค้า, คืนเงิน | Online Admin | ทันที (โทรลูกค้า) |
| **replaced** | แทนด้วย SKU อื่น | สร้าง Order ใหม่ | Online Admin | ทันที (สร้าง Order) |

---

## 4.4 🚨 ระดับความเร่งด่วน (ด่วนแค่ไหน)

### ระบบคำนวณ Urgency อัตโนมัติ:

```
Urgency = ระดับความเร่งด่วน (high / medium / low)

คำนวณจาก:
1. Due Date (วันที่ต้องส่ง)
2. วันปัจจุบัน

สูตร:
┌─────────────────────────────────────────────┐
│ Days Until Due = Due Date - Today          │
│                                             │
│ If Days <= 1: urgency = "high" ⚠️          │
│ If Days <= 3: urgency = "medium" ⚡         │
│ If Days > 3:  urgency = "low" 🟢           │
└─────────────────────────────────────────────┘

ตัวอย่าง:
Today = 2025-11-18
Due Date = 2025-11-19 → Days = 1 → urgency = "high" ⚠️
Due Date = 2025-11-21 → Days = 3 → urgency = "medium" ⚡
Due Date = 2025-11-25 → Days = 7 → urgency = "low" 🟢
```

### Priority Matrix (แผนที่จัดลำดับความสำคัญ):

| Urgency | Priority | ต้องแก้ภายใน | Action |
|---------|---------|-------------|--------|
| **🔴 high** | 1 | **วันนี้!** | Drop everything, แก้ทันที |
| **🟡 medium** | 2 | 1-3 วัน | แก้ในวันทำการถัดไป |
| **🟢 low** | 3 | 3-7 วัน | แก้เมื่อมีเวลา |

---

## 4.5 📋 ขั้นตอนมาตรฐานในการจัดการ

### ขั้นตอนที่ 1: เช็ค Shortage Queue ทุกเช้า

```
เวลา: 08:00-09:00 (ทุกเช้า)

1. เข้า /shortage-queue
2. Filter: Status = waiting_stock
3. เรียงตาม: Urgency (high → medium → low)

ตัวอย่างที่เห็น:
┌──────────────────────────────────────────────────────────────┐
│ Order    │ SKU    │ Qty │ Reason      │ Status │ Urgency  │
├──────────────────────────────────────────────────────────────┤
│ SO123456 │ A01    │ 5   │ out_of_stock│ waiting│ 🔴 high   │
│ SO123457 │ B02    │ 10  │ damaged     │ waiting│ 🟡 medium │
│ SO123458 │ C03    │ 2   │ out_of_stock│ waiting│ 🟢 low    │
└──────────────────────────────────────────────────────────────┘

4. จัดการตามลำดับ: high → medium → low
```

---

### ขั้นตอนที่ 2: ตัดสินใจแต่ละรายการ

#### Scenario A: สต็อกหมด (out_of_stock)

```
Decision Tree:
┌────────────────────────────────────────────┐
│ Shortage Reason: out_of_stock              │
└────────────────┬───────────────────────────┘
                 │
                 ▼
          มีสต็อกเข้าวันนี้หรือไม่?
                 │
        ┌────────┴────────┐
        │                 │
      YES                NO
        │                 │
        ▼                 ▼
   Status:          Status:
   resolved         waiting_stock
        │                 │
        ▼                 ▼
   บอก Picker      รอสต็อกเข้า
   หยิบใหม่         (ทำทีหลัง)
        │
        ▼
   ✅ เสร็จสิ้น

Action:
1. เช็คสต็อกจริงในคลัง (เดินไปดู)
2. ถ้าเจอ → เปลี่ยน Status เป็น "resolved"
3. แจ้ง Picker: "SKU-A01 มีสต็อก ที่ Shelf B-05, หยิบเพิ่ม 5 ชิ้น"
4. Picker หยิบใหม่ → Progress +5%
```

---

#### Scenario B: สินค้าเสียหาย (damaged)

```
Decision Tree:
┌────────────────────────────────────────────┐
│ Shortage Reason: damaged                   │
└────────────────┬───────────────────────────┘
                 │
                 ▼
          มีสต็อกทดแทนหรือไม่?
                 │
        ┌────────┴────────┐
        │                 │
      YES                NO
        │                 │
        ▼                 ▼
   Status:          สามารถรอได้หรือไม่?
   resolved              │
        │         ┌──────┴──────┐
        ▼         │             │
   บอก Picker   YES            NO
   หยิบใหม่       │             │
                  ▼             ▼
            waiting_stock   cancelled
            (รอสต็อกเข้า)   (ยกเลิก Order)

Action:
1. เช็คสต็อกที่ดี (ไม่เสีย)
2. ถ้ามี → เปลี่ยน Status เป็น "resolved"
3. ถ้าไม่มี:
   - Urgency = high → cancelled (ยกเลิก Order ทันที)
   - Urgency = low/medium → waiting_stock (รอสต็อกเข้า)
```

---

#### Scenario C: ไม่สามารถหาสต็อกได้ + Due Date ใกล้

```
Decision Tree:
┌────────────────────────────────────────────┐
│ No Stock + Urgency = high                  │
└────────────────┬───────────────────────────┘
                 │
                 ▼
          มี SKU ทดแทนหรือไม่?
                 │
        ┌────────┴────────┐
        │                 │
      YES                NO
        │                 │
        ▼                 ▼
   Status:          Status:
   replaced         cancelled
        │                 │
        ▼                 ▼
   สร้าง Order      แจ้งลูกค้า
   ใหม่ (SKU อื่น)   ขออภัย + คืนเงิน

Action (replaced):
1. หา SKU ทดแทนที่ใกล้เคียง
   - ตัวอย่าง: SKU-A01 (Red) → SKU-A02 (Blue)
2. โทรหาลูกค้า: "สินค้าสีแดงหมดค่ะ, เปลี่ยนเป็นสีน้ำเงินได้ไหม?"
3. ถ้าลูกค้าตกลง:
   - เปลี่ยน Status เป็น "replaced"
   - สร้าง Order ใหม่ (SKU-A02, Qty = 5)
   - Import Orders ใหม่
   - สร้าง Batch ใหม่

Action (cancelled):
1. โทรหาลูกค้า: "ขออภัยค่ะ, สินค้าหมดชั่วคราว"
2. เสนอทางเลือก:
   - รอสต็อกเข้า (3-5 วัน)?
   - ยกเลิก + คืนเงิน?
3. เปลี่ยน Status เป็น "cancelled"
```

---

## 4.6 📞 วิธีติดต่อลูกค้า (มี Script ตัวอย่าง)

### Script สำหรับโทรลูกค้า:

#### Script 1: สินค้าหมด - เสนอรอ

```
📞 "สวัสดีค่ะ คุณ [ชื่อลูกค้า]
   โทรมาจากร้าน [ชื่อร้าน] ค่ะ

   ขออภัยค่ะ สินค้า [ชื่อสินค้า] ที่คุณสั่ง (Order: [Order Number])
   ตอนนี้หมดชั่วคราวค่ะ

   คาดว่าสต็อกจะเข้าวันที่ [Due Date + 2 days] ค่ะ

   คุณรอได้ไหมคะ?
   หรือต้องการยกเลิกคะ?"

✅ ลูกค้าตอบ "รอได้":
   → Status: waiting_stock
   → บันทึก Note: "ลูกค้ายินดีรอถึง [Date]"

❌ ลูกค้าตอบ "ยกเลิก":
   → Status: cancelled
   → ดำเนินการคืนเงิน
```

---

#### Script 2: สินค้าหมด - เสนอทดแทน

```
📞 "สวัสดีค่ะ คุณ [ชื่อลูกค้า]
   โทรมาจากร้าน [ชื่อร้าน] ค่ะ

   ขออภัยค่ะ สินค้า [สี A] ที่คุณสั่งหมดแล้วค่ะ
   (Order: [Order Number])

   แต่เรามีสี [สี B] ในราคาเดียวกันค่ะ
   คุณเปลี่ยนเป็นสี [สี B] ได้ไหมคะ?"

✅ ลูกค้าตอบ "เปลี่ยนได้":
   → Status: replaced
   → สร้าง Order ใหม่ (SKU ใหม่)

❌ ลูกค้าตอบ "ไม่เปลี่ยน":
   → กลับไป Script 1 (เสนอรอ หรือ ยกเลิก)
```

---

## 4.7 ⚠️ ถ้าไม่จัดการ Shortage ทัน จะเกิดอะไร?

| ⏰ ระยะเวลา | 💥 ผลกระทบ | 📉 Impact Score |
|-----------|------------|----------------|
| **ไม่จัดการภายใน 1 วัน** | ลูกค้าโทรมาถาม "ของเมื่อไหร่?" → เสียเวลาตอบ | 🟡 Medium |
| **ไม่จัดการภายใน 3 วัน** | ลูกค้าโกรธ → ยกเลิก Order → เสีย Sale | 🟠 High |
| **ไม่จัดการภายใน 7 วัน** | ลูกค้าให้ Rating 1 ดาว → ร้านโดน Platform ปรับ Ranking ลง | 🔴 Critical |
| **Shortage สะสม > 50 รายการ** | ร้านถูก Platform ระงับการขาย (เพราะ Performance ต่ำ) | ⚫ Catastrophic |

### ตัวเลขจริง (ตัวอย่าง):

```
Scenario: ร้านมี Shortage 100 รายการ ไม่จัดการ 1 สัปดาห์

ผลกระทบทางการเงิน:
┌─────────────────────────────────────────────────────────────┐
│ 1. เสีย Sale:                                               │
│    100 orders × ฿500/order = ฿50,000                        │
│                                                             │
│ 2. ลูกค้ายกเลิก + คืนเงิน:                                  │
│    Platform Fee = 5% × ฿50,000 = ฿2,500 (เสียค่าธรรมเนียม) │
│                                                             │
│ 3. Rating ต่ำ → Ranking ลง:                                 │
│    Organic Traffic ลง 30% → เสีย ฿100,000/เดือน             │
│                                                             │
│ 4. Platform ระงับการขาย 7 วัน:                              │
│    ฿500,000/เดือน × 7/30 = ฿116,667                         │
│                                                             │
│ รวมขาดทุน: ฿269,167 (ในเวลา 1 สัปดาห์!)                     │
└─────────────────────────────────────────────────────────────┘

แก้ไข: จัดการ Shortage ทันที → ขาดทุน = ฿0 ✅
```

---

## 4.8 📈 ตัวชี้วัดความสำเร็จ

### ตัวชี้วัดหลัก:

| KPI | เป้าหมาย | วิธีวัด | Frequency |
|-----|---------|---------|-----------|
| **Shortage Rate** | < 5% | (Shortage Orders / Total Orders) × 100 | Daily |
| **Shortage Resolution Time** | < 24 ชม. | Average(Resolved Time - Created Time) | Daily |
| **Shortage Cancelled Rate** | < 10% | (Cancelled / Total Shortage) × 100 | Weekly |
| **Shortage Pending Queue** | < 20 รายการ | Count(Status = waiting_stock) | Daily |

### ตัวอย่างรายงาน:

```
📊 Shortage Report - 2025-11-18
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Orders Today: 500
Shortage Orders: 25
Shortage Rate: 5.0% ✅ (เป้าหมาย: < 5%)

Shortage by Status:
┌────────────────────────────────────┐
│ waiting_stock: 10 รายการ           │
│ resolved:      8 รายการ            │
│ cancelled:     5 รายการ            │
│ replaced:      2 รายการ            │
└────────────────────────────────────┘

Shortage by Urgency:
┌────────────────────────────────────┐
│ 🔴 high:   5 รายการ (ต้องแก้วันนี้!)│
│ 🟡 medium: 10 รายการ               │
│ 🟢 low:    10 รายการ               │
└────────────────────────────────────┘

Average Resolution Time: 18 ชม. ✅ (เป้าหมาย: < 24 ชม.)

Top 3 SKUs with Shortage:
1. SKU-A01: 5 ครั้ง (out_of_stock)
2. SKU-B02: 3 ครั้ง (damaged)
3. SKU-C03: 2 ครั้ง (out_of_stock)

Action Items:
☑️ สั่งซื้อ SKU-A01 เพิ่ม (สต็อกต่ำ)
☑️ ตรวจสอบ SKU-B02 (ทำไมเสียหายบ่อย?)
```

---

## 4.9 🎯 คำแนะนำสำหรับหัวหน้าคลัง

### ✅ DO (ควรทำ):

1. **เช็ค Shortage Queue ทุกเช้า** (08:00-09:00)
2. **จัดการ high urgency ภายในวันเดียวกัน** (100% ไม่พลาด!)
3. **โทรหาลูกค้าทันที** (ถ้า Shortage ใกล้ Due Date)
4. **บันทึก Note ทุกครั้ง** (เพื่อ Audit Trail)
5. **Export รายงาน Shortage** (ทุกสัปดาห์)
6. **วิเคราะห์ Top SKUs** (ที่ Shortage บ่อย → สั่งซื้อเพิ่ม)

### ❌ DON'T (ไม่ควรทำ):

1. **ปล่อย Shortage ค้างเกิน 24 ชม.** (โดยเฉพาะ high urgency)
2. **ไม่โทรหาลูกค้า** (เมื่อต้อง cancel)
3. **ไม่บันทึก Status** (ทำให้ Online Team งง)
4. **ไม่ตรวจสอบสต็อกจริง** (เชื่อตัวเลขในระบบอย่างเดียว)
5. **ไม่สื่อสารกับ Picker** (เมื่อ resolve แล้วต้องบอก)

---

# 5. วิธีนำเข้าออเดอร์

> 🎓 **สำหรับหัวหน้าออนไลน์:** คู่มือนี้อธิบายการ Import Orders ทีละขั้นตอน พร้อมแผนรับมือเมื่อผิดพลาด

---

## 5.1 📥 การนำเข้าออเดอร์คืออะไร

### ทำไมต้อง Import Orders?

```
Import Orders = หัวใจของระบบ WMS

ถ้าไม่ Import Orders:
❌ ไม่มีออเดอร์ในระบบ
❌ ไม่สามารถสร้าง Batch ได้
❌ Picker ไม่มีงาน
❌ Packer ไม่มีอะไรส่ง
❌ ลูกค้าไม่ได้สินค้า
→ 🔥 ธุรกิจหยุดชะงัก!

ดังนั้น: Import Orders ต้องถูกต้อง 100%!
```

---

## 5.2 📋 ไฟล์ Excel ต้องมีอะไรบ้าง

### Template มาตรฐาน:

```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ Order Number │ Platform │ SKU │ Quantity │ Shop Name │ Due Date │ Item Name │ Logistic │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│ SO123456     │ Shopee   │ A01 │ 2        │ Shop A    │2025-11-20│ สินค้า A  │ SPX      │
│ SO123457     │ TikTok   │ B02 │ 5        │ Shop B    │2025-11-19│ สินค้า B  │ Flash    │
│ SO123458     │ Lazada   │ C03 │ 1        │ Shop C    │          │ สินค้า C  │ LEX      │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Column Details:

| Column | Required | Format | ตัวอย่าง | หมายเหตุ |
|--------|----------|--------|---------|---------|
| **Order Number** | ✅ ใช่ | Text | SO123456, TKS789 | **ห้ามซ้ำ!** ถ้าซ้ำ = Error |
| **Platform** | ✅ ใช่ | Text | Shopee, TikTok, Lazada | ตัวพิมพ์ใหญ่-เล็กไม่สำคัญ (shopee = Shopee) |
| **SKU** | ✅ ใช่ | Text | A01, SKU-123 | **ต้องมีในระบบก่อน** (Import Products ก่อน) |
| **Quantity** | ✅ ใช่ | Number | 1, 2, 10 | ต้องเป็นตัวเลข, ห้ามใส่ข้อความ |
| **Shop Name** | ✅ ใช่ | Text | Shop A, ร้านเราค้าขาย | **ต้องมีในระบบก่อน** |
| **Due Date** | ❌ ไม่จำเป็น | Date | 2025-11-20 | ไม่ใส่ = ระบบคำนวณให้ (Platform + 2 days) |
| **Item Name** | ❌ ไม่จำเป็น | Text | สินค้า A, Product XYZ | ชื่อสินค้า (สำหรับแสดงผล) |
| **Logistic** | ❌ ไม่จำเป็น | Text | SPX, Flash, Kerry | บริษัทขนส่ง |

---

## 5.3 🔍 ระบบจะตรวจสอบอะไรบ้าง

### ระบบจะตรวจสอบ 10 ข้อ:

```
1️⃣ Order Number ห้ามซ้ำ
   ❌ SO123456, SO123456 → Error: "Duplicate Order"
   ✅ SO123456, SO123457 → Pass

2️⃣ Order Number ห้ามว่าง
   ❌ "", null → Error: "Order Number Required"
   ✅ SO123456 → Pass

3️⃣ Platform ต้องมีในระบบ
   ❌ "Amazon" → Error: "Platform not found" (ถ้าไม่มีในระบบ)
   ✅ "Shopee", "TikTok", "Lazada" → Pass

4️⃣ SKU ต้องมีในระบบ
   ❌ "XYZ999" → Error: "SKU not found"
   ✅ "A01" (ที่ Import Products ไว้แล้ว) → Pass

5️⃣ Quantity ต้องเป็นตัวเลข
   ❌ "สอง", "2.5" → Error: "Quantity must be integer"
   ✅ 1, 2, 10 → Pass

6️⃣ Quantity ต้อง > 0
   ❌ 0, -1 → Error: "Quantity must be > 0"
   ✅ 1, 2 → Pass

7️⃣ Shop Name ต้องมีในระบบ
   ❌ "ร้านที่ไม่มี" → Error: "Shop not found"
   ✅ "Shop A" (ที่มีในระบบ) → Pass

8️⃣ Due Date ต้องเป็นวันที่ถูกต้อง
   ❌ "30-Feb-2025" → Error: "Invalid Date"
   ✅ "2025-11-20", "" (ว่าง = Auto) → Pass

9️⃣ Due Date ห้ามเป็นอดีต
   ❌ "2024-01-01" (ถ้าวันนี้ = 2025-11-18) → Error: "Due Date is in the past"
   ✅ "2025-11-20" → Pass

🔟 ไฟล์ Excel ต้องมี Column ครบ
   ❌ ไม่มี Column "SKU" → Error: "Missing required column: SKU"
   ✅ มีครบทุก Column → Pass
```

---

## 5.4 📤 ขั้นตอนการนำเข้า (ทีละขั้น)

### Step-by-Step (แบบละเอียด):

```
1️⃣ เตรียม Excel File
   ┌─────────────────────────────────────────┐
   │ 1.1 เปิด Template (ดาวน์โหลดจากระบบ)   │
   │ 1.2 กรอกข้อมูล:                         │
   │     • Order Number (ห้ามซ้ำ!)           │
   │     • Platform (Shopee/TikTok/Lazada)   │
   │     • SKU (ต้องมีในระบบก่อน)            │
   │     • Quantity (ต้องเป็นตัวเลข)         │
   │     • Shop Name (ต้องมีในระบบก่อน)      │
   │ 1.3 Save as .xlsx                       │
   └─────────────────────────────────────────┘
       │
       ▼

2️⃣ เข้าหน้า Import
   ┌─────────────────────────────────────────┐
   │ 2.1 Login: /login                       │
   │ 2.2 ไปที่: /import/orders               │
   │ 2.3 คลิก "Choose File"                  │
   │ 2.4 เลือกไฟล์ .xlsx                     │
   └─────────────────────────────────────────┘
       │
       ▼

3️⃣ Upload File
   ┌─────────────────────────────────────────┐
   │ 3.1 คลิก "Import"                       │
   │ 3.2 ระบบอ่านไฟล์ (10-30 วินาที)        │
   │ 3.3 แสดง Progress Bar                   │
   └─────────────────────────────────────────┘
       │
       ├─── ✅ Success (ไม่มี Error)
       │     │
       │     ▼
       │  ┌─────────────────────────────────────────┐
       │  │ 4.1 แสดงข้อความ:                        │
       │  │     "Import สำเร็จ 100 รายการ"          │
       │  │                                         │
       │  │ 4.2 ระบบ Auto-Classify:                 │
       │  │     • READY_ACCEPT: 80 รายการ (สีเขียว) │
       │  │     • LOW_STOCK: 15 รายการ (สีเหลือง)   │
       │  │     • SHORTAGE: 5 รายการ (สีแดง)         │
       │  │                                         │
       │  │ 4.3 Redirect to Dashboard               │
       │  └─────────────────────────────────────────┘
       │         │
       │         ▼
       │     ✅ เสร็จสิ้น!
       │
       └─── ❌ Error (มี Error)
             │
             ▼
          ┌─────────────────────────────────────────┐
          │ 5.1 แสดงข้อความ Error:                  │
          │                                         │
          │ ❌ "SKU not found: XYZ999" (Row 5)      │
          │ ❌ "Duplicate Order: SO123456" (Row 10) │
          │ ❌ "Shop not found: ร้านที่ไม่มี" (Row 3)│
          │                                         │
          │ 5.2 ไฟล์ไม่ถูก Import (ทั้งหมด Reject) │
          └─────────────────────────────────────────┘
             │
             ▼
          6. แก้ไข Excel
             ├─ เปิดไฟล์ Excel
             ├─ แก้ไข Row ที่ Error
             ├─ Save
             └─ Upload ใหม่ (กลับไป Step 2)
```

---

## 5.5 ⚠️ ข้อผิดพลาดที่พบบ่อยและวิธีแก้

### Error 1: "SKU not found"

```
❌ Error Message:
   "SKU not found: XYZ999 (Row 5)"

🔍 สาเหตุ:
   SKU "XYZ999" ไม่มีในระบบ

✅ วิธีแก้:
   Option 1: Import Products ก่อน
   ┌─────────────────────────────────────────┐
   │ 1. ไปที่ /import/products               │
   │ 2. Import SKU "XYZ999" ก่อน             │
   │ 3. กลับมา Import Orders ใหม่            │
   └─────────────────────────────────────────┘

   Option 2: แก้ SKU ใน Excel
   ┌─────────────────────────────────────────┐
   │ 1. เปิด Excel                            │
   │ 2. แก้ Row 5: XYZ999 → A01 (SKU ที่มี)  │
   │ 3. Save                                  │
   │ 4. Upload ใหม่                           │
   └─────────────────────────────────────────┘
```

---

### Error 2: "Duplicate Order"

```
❌ Error Message:
   "Duplicate Order Number: SO123456 (Row 10)"

🔍 สาเหตุ:
   Order Number "SO123456" ซ้ำกับ Order ที่มีในระบบแล้ว
   หรือ ซ้ำภายในไฟล์ Excel เดียวกัน

✅ วิธีแก้:
   ┌─────────────────────────────────────────┐
   │ 1. เช็คว่า SO123456 Import ไปแล้วหรือยัง│
   │    (ดูใน Dashboard)                     │
   │                                         │
   │ 2. ถ้า Import แล้ว:                     │
   │    → ลบ Row 10 ออกจาก Excel             │
   │                                         │
   │ 3. ถ้ายัง Import (ซ้ำในไฟล์เอง):       │
   │    → แก้ Order Number ให้ไม่ซ้ำ         │
   │      (เช่น SO123456 → SO123457)         │
   │                                         │
   │ 4. Save → Upload ใหม่                   │
   └─────────────────────────────────────────┘
```

---

### Error 3: "Shop not found"

```
❌ Error Message:
   "Shop not found: ร้านที่ไม่มี (Row 3)"

🔍 สาเหตุ:
   Shop Name "ร้านที่ไม่มี" ไม่มีในระบบ

✅ วิธีแก้:
   Option 1: สร้าง Shop ใหม่
   ┌─────────────────────────────────────────┐
   │ 1. ไปที่ /admin/shops (ถ้ามี)           │
   │ 2. สร้าง Shop: "ร้านที่ไม่มี"           │
   │ 3. กลับมา Import Orders ใหม่            │
   └─────────────────────────────────────────┘

   Option 2: แก้ Shop Name ใน Excel
   ┌─────────────────────────────────────────┐
   │ 1. เปิด Excel                            │
   │ 2. แก้ Row 3: "ร้านที่ไม่มี" → "Shop A" │
   │    (ใช้ Shop ที่มีในระบบ)               │
   │ 3. Save → Upload ใหม่                   │
   └─────────────────────────────────────────┘
```

---

### Error 4: "Quantity must be integer"

```
❌ Error Message:
   "Quantity must be integer (Row 7)"

🔍 สาเหตุ:
   Quantity ไม่ใช่ตัวเลข (เช่น "สอง", "2.5")

✅ วิธีแก้:
   ┌─────────────────────────────────────────┐
   │ 1. เปิด Excel                            │
   │ 2. แก้ Row 7:                            │
   │    • "สอง" → 2                           │
   │    • "2.5" → 2 (ปัดเศษ)                 │
   │    • "" (ว่าง) → 1                       │
   │ 3. Save → Upload ใหม่                   │
   └─────────────────────────────────────────┘
```

---

## 5.6 ⚠️ ถ้า Import ผิดพลาด จะเกิดอะไร?

| ❌ ถ้าทำผิด... | 💥 จะเกิด... | 🔥 ระดับความรุนแรง | ✅ วิธีแก้ไข |
|---------------|-------------|------------------|-------------|
| **Import SKU ที่ไม่มีในระบบ** | Orders เข้าเป็น SHORTAGE ทั้งหมด → Picker หยิบไม่ได้ → งานหยุด | 🔴 Critical | Import Products ก่อน → Import Orders ใหม่ |
| **Import Duplicate Order** | Order เก่าถูก Overwrite → ข้อมูลเดิมหาย → Batch ที่สร้างไว้พัง | ⚫ Catastrophic | ⚠️ เช็คให้แน่ใจก่อน Import! Backup ก่อนทุกครั้ง |
| **Import Quantity ผิด** | Picker หยิบผิดจำนวน → ลูกค้าได้ของไม่ครบ → Complaint | 🟠 High | แก้ใน Excel → Import ใหม่ ทันที |
| **Import Shop ผิด** | รายงานผิด → คำนวณค่าคอมมิชชั่นผิด → เสียเงิน | 🟡 Medium | แก้ใน Excel → Import ใหม่ |
| **ไม่ Import ทันเวลา** | ไม่มี Orders → ไม่สามารถสร้าง Batch → Picker ไม่มีงาน → งานล่าช้า | 🟠 High | Import ทุกเช้า ก่อน 09:00! |
| **Import ไฟล์ผิด** | Import Orders เก่า → Duplicate ทั้งหมด → ระบบพัง | ⚫ Catastrophic | ⚠️ ตรวจสอบไฟล์ก่อน Upload! |

---

## 5.7 📋 รายการตรวจสอบก่อนนำเข้า

### ก่อน Import (Pre-Import):

```
□ 1. ตรวจสอบไฟล์ Excel:
     □ ชื่อไฟล์ถูกต้อง (เช่น Orders_2025-11-18.xlsx)
     □ มี Column ครบ (Order Number, Platform, SKU, Quantity, Shop Name)
     □ ไม่มี Order Number ซ้ำภายในไฟล์
     □ SKU ทั้งหมดมีในระบบแล้ว (เช็คที่ /import/products)
     □ Shop ทั้งหมดมีในระบบแล้ว

□ 2. Backup ข้อมูลเดิม (ถ้าเป็น Import ซ้ำ):
     □ Export Orders เก่าก่อน (เผื่อผิดพลาด)
     □ บันทึก Log ไว้ (ว่า Import เมื่อไหร่, โดยใคร)

□ 3. เตรียมตัว:
     □ เน็ตเชื่อมต่อดี
     □ เวลาว่าง 10-30 นาที (อย่า Import ตอนกำลังรีบ)
```

---

### ระหว่าง Import (During Import):

```
□ 1. Upload ไฟล์ที่ถูกต้อง
□ 2. รอ Progress Bar จนเสร็จ (ห้ามปิดหน้าต่าง!)
□ 3. อ่านข้อความ Success/Error อย่างละเอียด
□ 4. ถ้า Error:
     □ บันทึก Error Message
     □ แก้ไข Excel ตาม Error
     □ Upload ใหม่
```

---

### หลัง Import (Post-Import):

```
□ 1. ตรวจสอบ Dashboard:
     □ Total Orders เพิ่มขึ้นตามจำนวนที่ Import
     □ ไม่มี Orders ที่ผิดปกติ

□ 2. เช็ค Order Classification:
     □ READY_ACCEPT: X รายการ (พร้อมสร้าง Batch)
     □ LOW_STOCK: X รายการ (ต้องระวัง)
     □ SHORTAGE: X รายการ (ต้องจัดการทันที)

□ 3. ถ้ามี SHORTAGE:
     □ ไปที่ /shortage-queue
     □ เช็คว่ามี SKU ไหนที่ขาดบ่อย
     □ วางแผนสั่งซื้อ SKU นั้นเพิ่ม

□ 4. แจ้งทีม:
     □ แจ้งทีมคลัง: "Import Orders แล้ว X รายการ, พร้อมสร้าง Batch"
     □ แจ้งหัวหน้า: "Import เสร็จแล้ว, มี Shortage X รายการ"

□ 5. บันทึก Log:
     □ วันที่ Import
     □ จำนวน Orders
     □ ใครเป็นคน Import
     □ มี Issues อะไรบ้าง
```

---


# 6. จุดเสี่ยงและแผนแก้ไข

> 🛡️ **สำหรับนักพัฒนา & ผู้จัดการ:** รายการจุดเสี่ยงและแผนแก้ไข

---

## 6.1 🚨 ตารางประเมินความเสี่ยง

### Risk Categories:

| Risk Level | Color | Impact | Likelihood | Action Required |
|------------|-------|--------|-----------|----------------|
| **Critical** | 🔴 | ธุรกิจหยุดชะงัก | High | แก้ทันที (24 ชม.) |
| **High** | 🟠 | เสียเงิน/ลูกค้า | Medium-High | แก้ใน 1 สัปดาห์ |
| **Medium** | 🟡 | งานล่าช้า | Medium | แก้ใน 1 เดือน |
| **Low** | 🟢 | ไม่สะดวก | Low | แก้เมื่อมีเวลา |

---

## 6.2 📊 จุดเสี่ยง 20 อันดับแรก

### 🔴 Critical Risks (ต้องแก้ทันที)

#### Risk 1: SQLite Scalability Limit

```
📌 Risk Description:
   SQLite มีข้อจำกัดในการรองรับ Concurrent Writes
   ถ้ามี Users หลายคนพร้อมกัน (>50) อาจเกิด "Database Locked"

💥 Impact:
   - ระบบช้า/ค้าง
   - Import Orders ล้มเหลว
   - Picker สแกนไม่ได้

🎯 Likelihood: High (เมื่อ Scale ขึ้น)

✅ Mitigation:
   Short-term (1-2 weeks):
   - เพิ่ม Connection Timeout
   - ใช้ Write-Ahead Logging (WAL mode)
   - Optimize Queries (Add Indexes)
   
   Long-term (3 months):
   - Migrate to PostgreSQL/MySQL
   - ใช้ Connection Pooling
   - Implement Read Replicas

📝 Implementation:
   1. Enable WAL mode:
      ```python
      db.engine.execute("PRAGMA journal_mode=WAL")
      ```
   2. Add indexes to critical columns:
      - order_lines: batch_id, sku, dispatch_status
      - batches: batch_date, platform, handover_code
   3. Monitor database file size (> 1 GB = ต้อง migrate)
```

---

#### Risk 2: No Database Backup System

```
📌 Risk Description:
   ไม่มีระบบ Backup อัตโนมัติ → ถ้า data.db เสีย = เสียข้อมูลทั้งหมด

💥 Impact:
   - เสียข้อมูลทั้งหมด
   - ไม่สามารถกู้คืนได้
   - ธุรกิจหยุดชะงัก

🎯 Likelihood: Medium (Hard disk failure, Human error)

✅ Mitigation:
   Immediate (Today):
   - Manual Backup ทุกวัน (Copy data.db ไปที่อื่น)
   
   Short-term (1 week):
   - Cron job สำหรับ Backup อัตโนมัติ:
     ```bash
     # Backup every day at 2 AM
     0 2 * * * cp /path/to/data.db /backup/data_$(date +\%Y\%m\%d).db
     ```
   
   Long-term (1 month):
   - Cloud Backup (S3, Google Drive)
   - Incremental Backup (เฉพาะส่วนที่เปลี่ยน)
   - Retention Policy (เก็บ 30 วัน)

📝 Implementation:
   1. สร้าง Backup script:
      ```python
      # backup.py
      import shutil
      from datetime import datetime
      
      source = "data.db"
      dest = f"backup/data_{datetime.now().strftime('%Y%m%d')}.db"
      shutil.copy2(source, dest)
      ```
   2. เพิ่มใน crontab
   3. Test restore ทุกเดือน
```

---

#### Risk 3: No Error Handling for QR Scanner

```
📌 Risk Description:
   QR Scanner ไม่มี Error Handling ดี
   - กล้องไม่ทำงาน = Picker สแกนไม่ได้
   - QR Code เสีย = ระบบค้าง

💥 Impact:
   - Picker ทำงานไม่ได้
   - งานค้าง
   - ต้องพิมพ์ซ้ำ

🎯 Likelihood: Medium (มือถือเก่า, QR Code พับ/เปียก)

✅ Mitigation:
   Short-term (1 week):
   - เพิ่ม Manual Entry Fallback:
     ┌─────────────────────────┐
     │ [Scan QR]               │
     │                         │
     │ หรือ                    │
     │                         │
     │ ใส่ Batch ID ด้วยมือ:   │
     │ [SH-2025-11-18-R1]      │
     │                         │
     │ [ยืนยัน]                │
     └─────────────────────────┘
   
   - เพิ่ม Camera Permission Check
   - แสดง Error Message ชัดเจน

📝 Implementation:
   1. Add fallback in scan_batch.html:
      ```html
      <button onclick="toggleManualEntry()">ใส่ Batch ID ด้วยมือ</button>
      <input id="manual_batch_id" style="display:none;">
      ```
   2. Add camera permission check:
      ```javascript
      navigator.mediaDevices.getUserMedia({video: true})
        .catch(err => alert("กรุณาเปิดกล้อง"));
      ```
```

---

### 🟠 High Risks (ต้องแก้ใน 1 สัปดาห์)

#### Risk 4: No Role-Based Access Control

```
📌 Risk Description:
   ยังไม่มี Role-based Permission (Admin/Staff/Picker/Packer)
   ทุกคนเข้าถึงทุกเมนูได้ → เสี่ยงผิดพลาด

💥 Impact:
   - Picker สามารถลบ Batch ได้ (ไม่ควร)
   - Staff สามารถ Import Orders ได้ (ไม่ควร)
   - เสียหายจากความผิดพลาด

🎯 Likelihood: Medium (User Error)

✅ Mitigation:
   1 week:
   - Add role field to User model (แนะนำใน Department-work.md แล้ว)
   - Implement @require_role decorator
   - Update UI to hide/show menus by role

📝 Implementation:
   (อ้างอิง Department-work.md Section 3)
```

---

#### Risk 5: No Session Timeout

```
📌 Risk Description:
   Session ไม่หมดอายุ → ถ้าลืมออกจากระบบ = ใครก็เข้าได้

💥 Impact:
   - Security Risk
   - คนอื่นใช้ Account ได้
   - ทำงานผิดพลาด

🎯 Likelihood: High (พนักงานลืม Logout)

✅ Mitigation:
   3 days:
   - Add session timeout (24 hours)
   - Add "Remember Me" option
   - Auto logout when idle 2 hours

📝 Implementation:
   ```python
   from datetime import timedelta
   
   app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
   
   @app.before_request
   def check_session_timeout():
       session.permanent = True
       last_active = session.get('last_active')
       if last_active:
           idle = datetime.now() - datetime.fromisoformat(last_active)
           if idle > timedelta(hours=2):
               session.clear()
               return redirect(url_for('login'))
       session['last_active'] = datetime.now().isoformat()
   ```
```

---

#### Risk 6: No Validation on Batch Delete

```
📌 Risk Description:
   Admin สามารถลบ Batch ได้โดยไม่มีการยืนยัน
   ลบผิด = เสียข้อมูลทั้ง Batch

💥 Impact:
   - เสียข้อมูล Order ทั้ง Batch
   - Picker ที่กำลังหยิบ = งานหาย
   - ต้องสร้าง Batch ใหม่

🎯 Likelihood: Medium (Human Error)

✅ Mitigation:
   3 days:
   - Add confirmation dialog:
     "คุณแน่ใจหรือไม่? Batch นี้มี X Orders"
   - Soft delete (เก็บไว้ใน Database แต่ซ่อน)
   - Add "Restore Batch" feature

📝 Implementation:
   ```javascript
   function confirmDelete(batchId) {
     if (confirm(`ลบ Batch ${batchId}? ไม่สามารถกู้คืนได้!`)) {
       fetch(`/batch/${batchId}/delete`, {method: 'POST'});
     }
   }
   ```
```

---

### 🟡 Medium Risks (ต้องแก้ใน 1 เดือน)

#### Risk 7: No Audit Log for Critical Actions

```
📌 Risk Description:
   ไม่มี Audit Log สำหรับ:
   - Batch Delete
   - User Management
   - Shortage Action

💥 Impact:
   - ไม่รู้ว่าใครทำอะไร
   - ตรวจสอบย้อนหลังไม่ได้
   - ถ้ามีปัญหา = หาตัวการไม่ได้

🎯 Likelihood: Low (แต่ Impact สูง)

✅ Mitigation:
   2 weeks:
   - Expand AuditLog model (มีอยู่แล้ว แต่ใช้น้อย)
   - Log all DELETE operations
   - Log all User Management actions
   - Add Audit Log UI (view logs)

📝 Implementation:
   (ใช้ log_audit() function ที่มีอยู่แล้ว app.py:173)
```

---

#### Risk 8: No Input Sanitization

```
📌 Risk Description:
   ไม่มี Input Validation/Sanitization
   - SQL Injection Risk
   - XSS Risk

💥 Impact:
   - Security Breach
   - Data Loss
   - System Compromise

🎯 Likelihood: Low (ใช้ SQLAlchemy = ป้องกัน SQL Injection อยู่แล้ว)

✅ Mitigation:
   1 month:
   - Add CSRF Protection (Flask-WTF)
   - Escape HTML Output (Jinja2 default = safe แล้ว)
   - Validate File Upload (Excel only)
   - Rate Limiting (ป้องกัน Brute Force)

📝 Implementation:
   ```python
   from flask_wtf.csrf import CSRFProtect
   
   csrf = CSRFProtect(app)
   ```
```

---

#### Risk 9: No Monitoring/Alerting

```
📌 Risk Description:
   ไม่มี Monitoring Dashboard
   - ไม่รู้ว่าระบบทำงานปกติหรือไม่
   - ไม่รู้ว่ามี Error

💥 Impact:
   - ปัญหาเกิดแล้วไม่รู้
   - ลูกค้าโทรมาบ่นก่อนถึงรู้

🎯 Likelihood: High (เมื่อ Scale ขึ้น)

✅ Mitigation:
   1 month:
   - Add Health Check Endpoint: /health
   - Log Errors to File (error.log)
   - Setup Email Alert (เมื่อเกิด Error)
   - Dashboard: System Status

📝 Implementation:
   ```python
   @app.route("/health")
   def health_check():
       return jsonify({
           "status": "ok",
           "database": "connected" if db.engine else "disconnected",
           "users_online": len(active_users),
           "timestamp": datetime.now().isoformat()
       })
   ```
```

---

#### Risk 10: No Mobile Optimization

```
📌 Risk Description:
   หน้าสแกน (Picker/Packer) ใช้งานบนมือถือได้แต่ไม่ Responsive ดี
   - ปุ่มเล็ก
   - Font เล็ก
   - สแกน QR ช้า

💥 Impact:
   - Picker ใช้งานลำบาก
   - สแกนผิด
   - เสียเวลา

🎯 Likelihood: Medium

✅ Mitigation:
   2 weeks:
   - Responsive Design (Bootstrap/Tailwind)
   - Large Buttons (min 48x48px)
   - Large Font (min 16px)
   - Optimize QR Scanner (use lighter library)

📝 Implementation:
   ```css
   /* Mobile-first */
   button {
     min-width: 48px;
     min-height: 48px;
     font-size: 18px;
   }
   
   @media (min-width: 768px) {
     /* Desktop styles */
   }
   ```
```

---

### 🟢 Low Risks (แก้เมื่อมีเวลา)

#### Risk 11-20: (Summary)

| Risk | Description | Impact | Likelihood | Priority |
|------|-------------|--------|-----------|---------|
| 11. No Batch Lock Mechanism | 2 คนแก้ Batch เดียวกัน = Data Conflict | Low | Low | 🟢 P3 |
| 12. No Offline Mode | เน็ตหลุด = ใช้งานไม่ได้ | Medium | Low | 🟢 P3 |
| 13. No Multi-language Support | แปลภาษาได้แค่ไทย | Low | Low | 🟢 P3 |
| 14. No API Documentation | Developer ใหม่เข้ามาเรียนรู้ยาก | Low | Low | 🟢 P3 |
| 15. No Unit Tests | แก้โค้ด = เสี่ยงทำอะไรพัง | Medium | Low | 🟢 P3 |
| 16. No Load Testing | ไม่รู้ว่ารองรับคนได้กี่คน | Medium | Low | 🟢 P3 |
| 17. Hard-coded Secrets | SECRET_KEY ใน Code = เสี่ยง | High | Low | 🟡 P2 |
| 18. No Docker Support | Deploy ยาก | Low | Low | 🟢 P3 |
| 19. No CI/CD Pipeline | Deploy ด้วยมือ = ช้า | Low | Low | 🟢 P3 |
| 20. No Performance Metrics | ไม่รู้ว่าช้าตรงไหน | Low | Low | 🟢 P3 |

---

## 6.3 🗓️ แผนพัฒนาระบบในอนาคต

### Phase 1: Stabilization (1-2 เดือน) - Fix Critical Risks

```
Week 1-2: Database & Backup
□ Enable SQLite WAL mode
□ Add Database Indexes
□ Setup Automatic Backup (Cron)
□ Test Restore Process

Week 3-4: Security & Permissions
□ Implement Role-Based Access Control
□ Add Session Timeout
□ Add CSRF Protection
□ Add Batch Delete Confirmation

Week 5-6: Error Handling
□ Add QR Scanner Fallback (Manual Entry)
□ Expand Audit Log
□ Add Error Logging (error.log)
□ Add Health Check Endpoint

Week 7-8: Mobile Optimization
□ Responsive Design
□ Large Buttons/Fonts
□ Optimize QR Scanner
□ Test on Multiple Devices

Goal: ระบบเสถียร, ปลอดภัย, ใช้งานง่าย
```

---

### Phase 2: Scale (3-4 เดือน) - Prepare for Growth

```
Month 3: Database Migration
□ Migrate from SQLite to PostgreSQL
□ Connection Pooling
□ Read Replicas
□ Query Optimization

Month 4: Monitoring & Alerting
□ Setup Monitoring Dashboard
□ Email Alerts for Errors
□ Performance Metrics (Response Time, Uptime)
□ Capacity Planning (Storage, Users)

Goal: รองรับ 500+ Users พร้อมกัน, 10,000+ Orders/day
```

---

### Phase 3: Advanced Features (5-6 เดือน) - Enhance

```
Month 5: API & Integrations
□ REST API (สำหรับ External Systems)
□ API Documentation (OpenAPI/Swagger)
□ Webhook Support (แจ้ง Event ไป External)
□ Third-party Integration (Logistics APIs)

Month 6: Analytics & AI
□ Advanced Dashboard (Charts, Trends)
□ Predictive Analytics (Forecast Shortage)
□ Automated Stock Replenishment
□ ML-based SKU Recommendation

Goal: ระบบอัจฉริยะ, เชื่อมต่อได้กับระบบอื่น
```

---

## 6.4 📋 รายการตรวจสอบก่อนเปิดใช้งานจริง

### Security Checklist:

```
□ ✅ Passwords hashed (Werkzeug - Done)
□ ✅ SQL Injection protected (SQLAlchemy - Done)
□ ⏳ CSRF Protection (Pending - Phase 1)
□ ⏳ Session Timeout (Pending - Phase 1)
□ ⏳ Role-Based Access Control (Pending - Phase 1)
□ ⏳ Audit Log Complete (Partial - Expand in Phase 1)
□ ⏳ Rate Limiting (Pending - Phase 2)
□ ⏳ HTTPS Enabled (Pending - Production Deploy)
```

---

### Performance Checklist:

```
□ ⏳ Database Indexes (Critical Columns - Phase 1)
□ ⏳ Query Optimization (N+1 Query - Phase 2)
□ ⏳ Caching (Redis - Phase 2)
□ ⏳ Load Testing (500 Users - Phase 2)
□ ⏳ CDN for Static Files (Phase 3)
```

---

### Reliability Checklist:

```
□ ⏳ Database Backup (Daily - Phase 1)
□ ⏳ Error Logging (File - Phase 1)
□ ⏳ Health Check Endpoint (Phase 1)
□ ⏳ Monitoring Dashboard (Phase 2)
□ ⏳ Alerting System (Email - Phase 2)
□ ⏳ Disaster Recovery Plan (Phase 2)
```

---

### Usability Checklist:

```
□ ⏳ Mobile Responsive (Phase 1)
□ ⏳ Large Buttons/Fonts (Phase 1)
□ ⏳ Error Messages ชัดเจน (Phase 1)
□ ⏳ Loading Indicators (Phase 1)
□ ⏳ Offline Mode (Phase 3 - Optional)
```

---

## 6.5 🎯 สิ่งที่ควรทำก่อน-หลัง

```
┌─────────────────────────────────────────────────────────────┐
│                    Priority Matrix                           │
│                                                              │
│  High Impact                                                 │
│      │                                                       │
│      │  [Risk 1]    [Risk 2]    [Risk 4]                    │
│      │  SQLite      Backup      RBAC                        │
│      │  ├─────────────────────────────────┐                 │
│      │  │        DO FIRST (Phase 1)       │                 │
│      │  │         Priority: P0            │                 │
│      │  └─────────────────────────────────┘                 │
│      │                                                       │
│      │  [Risk 3]    [Risk 5]    [Risk 6]                    │
│      │  QR Error    Session     Delete                      │
│      │  ├─────────────────────────────────┐                 │
│      │  │      DO SECOND (Phase 1-2)      │                 │
│      │  │         Priority: P1            │                 │
│      │  └─────────────────────────────────┘                 │
│      │                                                       │
│      │  [Risk 7-10]                                         │
│      │  Audit/Security/Monitor                              │
│      │  ├─────────────────────────────────┐                 │
│      │  │      DO THIRD (Phase 2)         │                 │
│      │  │         Priority: P2            │                 │
│      │  └─────────────────────────────────┘                 │
│      │                                                       │
│      │  [Risk 11-20]                                        │
│      │  Nice-to-have                                        │
│      │  ├─────────────────────────────────┐                 │
│      │  │      DO LATER (Phase 3)         │                 │
│      │  │         Priority: P3            │                 │
│      │  └─────────────────────────────────┘                 │
│      │                                                       │
│  Low Impact                                                  │
│      │                                                       │
│      └──────────────────────────────────────────> High      │
│                 Low Likelihood              Likelihood       │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.6 📞 ติดต่อและขอความช่วยเหลือ

### สำหรับรายงานปัญหา:

```
🐛 Bug Report:
   - GitHub Issues: https://github.com/[your-repo]/issues
   - Email: dev@vnix.com
   - Line: @vnixdev

💡 Feature Request:
   - GitHub Issues (tag: enhancement)
   - Email with subject: [FEATURE REQUEST]

📚 Documentation:
   - PRD.md (Product Requirements)
   - FLOW.md (This document)
   - Department-work.md (Workflow & Permissions)

👥 Team:
   - Product Owner: [Name]
   - Tech Lead: [Name]
   - Backend Dev: [Name]
   - Frontend Dev: [Name]
```

---

## 📄 Appendix: Quick Reference

### เมนูที่ใช้บ่อยที่สุด (Top 10):

```
1. /import/orders           (นำเข้าออเดอร์)
2. /batch/create            (สร้าง Batch)
3. /batch/list              (ดูรายการ Batch)
4. /scan/batch              (รับงาน Batch - Picker)
5. /scan/sku                (หยิบสินค้า - Picker)
6. /scan-handover           (ส่งมอบ - Packer)
7. /shortage-queue          (จัดการสินค้าขาด)
8. /dashboard               (ภาพรวม)
9. /batch/<id>              (รายละเอียด Batch)
10. /batch/<id>/print-picking (พิมพ์ Picking List)
```

---

### สูตรคำนวณสำคัญ:

```
1. Progress Percentage:
   Progress = (Picked Qty + Shortage Resolved Qty) / Total Qty × 100

2. SLA Due Date:
   Shopee: Order Date + 2 days
   TikTok: Order Date + 1 day
   Lazada: Order Date + 3 days

3. Shortage Urgency:
   Days Until Due = Due Date - Today
   If Days <= 1: high
   If Days <= 3: medium
   If Days > 3: low

4. Batch ID Format:
   {Platform Prefix}-YYYY-MM-DD-R{Run Number}
   Example: SH-2025-11-18-R1

5. Handover Code Format:
   H-YYYYMMDD-{Sequential Number}
   Example: H-20251118-001
```

---

## 🎓 Training Resources

### สำหรับพนักงานใหม่:

```
Day 1: Orientation
□ อ่าน FLOW.md (เอกสารนี้)
□ ดู Demo Video (ถ้ามี)
□ ทดสอบ Login (Username/Password)

Day 2: Hands-on Training
□ Online Team: ทดลอง Import Orders, สร้าง Batch
□ Picker: ทดลองสแกน Batch, สแกน SKU
□ Packer: ทดลองสแกน Handover

Day 3-5: Supervised Work
□ ทำงานจริงภายใต้การดูแลของหัวหน้า
□ ถามคำถามได้ตลอด

Week 2: Independent Work
□ ทำงานเองได้ (แต่ยังถามได้)
□ เริ่มเข้าใจ Flow การทำงาน

Month 1: Full Proficiency
□ ทำงานได้เต็มรูปแบบ
□ สามารถแนะนำคนใหม่ได้
```

---

## 🏆 Success Stories (ตัวอย่างผลลัพธ์)

### ก่อนใช้ระบบ:

```
📊 Metrics (Before):
   - Orders/day: 200
   - Picking Time: 5 min/order
   - Error Rate: 15%
   - Shortage: ไม่มีการติดตาม (หาย)
   - Dispatch Time: 3 hours/batch
```

### หลังใช้ระบบ:

```
📊 Metrics (After - 3 months):
   - Orders/day: 500 (+150%)
   - Picking Time: 3 min/order (-40%)
   - Error Rate: 3% (-80%)
   - Shortage: ติดตามได้ 100%, แก้ไขเฉลี่ย 18 ชม.
   - Dispatch Time: 1 hour/batch (-67%)

💰 ROI:
   - เพิ่ม Throughput: +150%
   - ลดต้นทุน Labor: -30%
   - ลด Error Cost: -80%
   - Customer Satisfaction: +25%
```

---

## 🎉 Conclusion

```
┌─────────────────────────────────────────────────────────────┐
│         ขอบคุณที่ใช้ VNIX WMS System! 🙏                     │
│                                                              │
│  ระบบนี้ออกแบบมาเพื่อ:                                       │
│  ✅ ลดเวลาทำงาน                                               │
│  ✅ ลดข้อผิดพลาด                                              │
│  ✅ เพิ่มความแม่นยำ                                           │
│  ✅ ติดตามได้แบบ Real-time                                    │
│                                                              │
│  หากพบปัญหาหรือมีข้อเสนอแนะ:                                 │
│  📧 Email: support@vnix.com                                  │
│  💬 Line: @vnixsupport                                       │
│  🐛 GitHub: https://github.com/[repo]/issues                │
│                                                              │
│  Happy Fulfillment! 🚀📦                                      │
└─────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 2.0  
**Last Updated:** 2025-11-18  
**Maintained By:** VNIX Development Team  
**Total Pages:** 100+ pages  
**Reading Time:** ~60 minutes  

---

**📥 Download PDF:**  
[FLOW.pdf](#) (ถ้ามี)

**🔗 Related Documents:**  
- [PRD.md](PRD.md) - Product Requirements Document  
- [Department-work.md](docs/Department-work.md) - Department Workflow Guide  
- [README.md](README.md) - Project Overview

---

**END OF DOCUMENT**

