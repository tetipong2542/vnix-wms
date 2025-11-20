# 📋 Shortage Management Workflow (Option 3: Hybrid Flow)
## คู่มือการจัดการสินค้าขาด - Hybrid Flow

**Version:** 2.0
**Last Updated:** 2025-01-19
**Implemented:** Option 3 (Hybrid Flow with Auto-Resolution)

---

## 🎯 ภาพรวม

ระบบ Shortage Management ถูกออกแบบให้มีความยืดหยุ่นสูงสุด โดยอนุญาตให้:
- **Picker** สามารถหยิบของต่อได้เสมอ (ไม่ต้องรอ Admin)
- **Admin** สามารถเปลี่ยนสถานะได้โดยตรง
- **ระบบ** ตรวจจับและอัปเดทสถานะอัตโนมัติ

---

## 📊 Shortage Status Lifecycle

```
┌─────────────┐
│   pending   │ ← Picker บันทึก Shortage (สต็อกหมด/ไม่พอ)
└──────┬──────┘
       │
       ├───────────────────┬────────────────┬──────────────┐
       │                   │                │              │
       ▼                   ▼                ▼              ▼
┌──────────────┐   ┌──────────────┐   ┌─────────┐   ┌──────────┐
│ waiting_stock│   │ ready_to_pick│   │cancelled│   │ resolved │
│ (รอสต็อกเข้า)│   │ (พร้อมหยิบ)  │   │(ยกเลิก) │   │(จัดการแล้ว)│
└──────┬───────┘   └──────┬───────┘   └─────────┘   └──────────┘
       │                   │
       │ ✅ Import Stock   │ ✅ Picker หยิบครบ
       │                   │
       ▼                   ▼
┌──────────────┐   ┌──────────────┐
│ ready_to_pick│   │   resolved   │
│ (Auto-detect)│   │ (Auto-resolve)│
└──────────────┘   └──────────────┘
```

---

## 🔄 สถานะทั้งหมด

| Status | ความหมาย | ใครเปลี่ยน | Action ต่อไป |
|--------|----------|-----------|--------------|
| `pending` | รอ Admin จัดการ | System (Picker บันทึก) | Admin เลือก Action |
| `waiting_stock` | รอสต็อกเข้า | Admin | รอ Import Stock → Auto เปลี่ยนเป็น `ready_to_pick` |
| `ready_to_pick` | ✅ สต็อกพร้อมแล้ว | System (Auto) หรือ Admin | Picker สแกนหยิบได้เลย |
| `cancelled` | ยกเลิกแล้ว | Admin | ไม่ต้องหยิบ (Refund ลูกค้า) |
| `replaced` | แทน SKU แล้ว | Admin | Picker หยิบ SKU ใหม่ |
| `resolved` | จัดการเรียบร้อย | System (Auto) หรือ Admin (Force) | เสร็จสิ้น |

---

## 👤 Workflow สำหรับ Picker

### Scenario 1: สต็อกหมดเลย (0 ชิ้น)

```
[Picker] สแกน SKU
   ↓
[System] แสดงข้อมูล:
   - สต็อกคงเหลือ: 0 ชิ้น ❌
   - ต้องการ: 2 ชิ้น
   - ปุ่ม: "บันทึก Shortage (สต็อกหมด)"
   ↓
[Picker] เลือกเหตุผล: "สต็อกหมด"
   ↓
[Picker] กดปุ่ม "บันทึก Shortage (สต็อกหมด)"
   ↓
[System] สร้าง Shortage Record → status = "pending"
   ↓
[Admin] ไปที่ /shortage-queue → เปลี่ยนสถานะเป็น "รอสต็อกเข้า"
   ↓
[Warehouse] Import Stock ใหม่ (0 → 5 ชิ้น)
   ↓
[System] ✅ Auto-detect: เปลี่ยนสถานะเป็น "พร้อมหยิบ"
   ↓
[System] แสดง Flash Message: "SKU-001: สต็อกเพิ่มจาก 0 → 5 ชิ้น"
   ↓
[Picker] สแกน SKU อีกครั้ง → หยิบครบ 2 ชิ้น
   ↓
[System] ✅ Auto-resolve: Shortage Record → status = "resolved"
```

### Scenario 2: สต็อกมีบ้าง แต่ไม่พอ (เช่น มี 1 ต้องการ 2)

```
[Picker] สแกน SKU
   ↓
[System] แสดงข้อมูล:
   - สต็อกคงเหลือ: 1 ชิ้น ⚠️
   - ต้องการ: 2 ชิ้น
   - ปุ่ม 1: "ยืนยันการหยิบ (หยิบได้ 1 ชิ้น)"
   - ปุ่ม 2: "บันทึกหยิบ 1 + Shortage 1 ชิ้น" (Hybrid)
   ↓
[Picker] Option A: กดปุ่ม 1 (หยิบ 1 ก่อน) → แล้วกด "สินค้าขาด"
[Picker] Option B: กดปุ่ม 2 (หยิบ + Shortage พร้อมกัน) ← แนะนำ
   ↓
[System]
   - บันทึกการหยิบ: 1 ชิ้น
   - สร้าง Shortage Record: ขาด 1 ชิ้น → status = "pending"
   ↓
[Admin] เปลี่ยนสถานะเป็น "รอสต็อกเข้า"
   ↓
[Warehouse] Import Stock ใหม่ (1 → 5 ชิ้น)
   ↓
[System] ✅ Auto-detect: เปลี่ยนสถานะเป็น "พร้อมหยิบ"
   ↓
[Picker] สแกน SKU อีกครั้ง → หยิบเพิ่ม 1 ชิ้น (รวม 2 ชิ้น)
   ↓
[System] ✅ Auto-resolve: Shortage Record → status = "resolved"
```

### Scenario 3: สต็อกพอ (ปกติ)

```
[Picker] สแกน SKU
   ↓
[System] แสดงข้อมูล:
   - สต็อกคงเหลือ: 10 ชิ้น ✅
   - ต้องการ: 2 ชิ้น
   - ปุ่ม: "ยืนยันการหยิบ (หยิบครบ)"
   ↓
[Picker] กดปุ่ม "ยืนยันการหยิบ"
   ↓
[System] บันทึกการหยิบ: 2 ชิ้น → เสร็จสิ้น
```

---

## 👨‍💼 Workflow สำหรับ Admin

### 1. เปลี่ยนสถานะ Shortage Record

**ที่:** `/shortage-queue`

**วิธีใช้:**
1. เข้าหน้า Shortage Queue
2. เห็น Dropdown ในคอลัมน์ "สถานะ"
3. เลือกสถานะใหม่:
   - **รอจัดการ** (pending)
   - **รอสต็อกเข้า** (waiting_stock) ← แจ้งทีม Warehouse
   - **✅ พร้อมหยิบ** (ready_to_pick) ← เปลี่ยนเมื่อสต็อกพร้อม
   - **ยกเลิกแล้ว** (cancelled) ← Refund ลูกค้า
   - **แทน SKU แล้ว** (replaced) ← ใช้สินค้าอื่นแทน
   - **จัดการแล้ว** (resolved) ← จัดการเรียบร้อย
4. ระบบแสดง Confirmation Dialog
5. กด "ยืนยัน" → สถานะเปลี่ยน

**ตัวอย่าง:**

```
[Admin] เห็น Shortage Record:
   Order: ORD001
   SKU: SKU-001
   ขาด: 2 ชิ้น
   สถานะ: pending
   ↓
[Admin] เปลี่ยนสถานะเป็น "รอสต็อกเข้า"
   ↓
[System] ยืนยันเปลี่ยนสถานะ?
   "รอจัดการ → รอสต็อกเข้า"
   [ยกเลิก] [ยืนยัน]
   ↓
[Admin] กด "ยืนยัน"
   ↓
[System] เปลี่ยนสถานะสำเร็จ!
```

### 2. Force Resolve (บังคับจัดการ)

**เมื่อไหร่ใช้:** เมื่อ Admin ต้องการปิด Shortage แต่ Picker ยังหยิบไม่ครบ

**Scenario:**

```
[Admin] เปลี่ยนสถานะเป็น "จัดการเรียบร้อย" (resolved)
   ↓
[System] ตรวจสอบ: ยังหยิบไม่ครบ!
   - SKU: SKU-001
   - ต้องหยิบ: 2 ชิ้น
   - หยิบแล้ว: 1 ชิ้น
   - ขาดอีก: 1 ชิ้น
   ↓
[System] แสดง Warning Confirmation:
   "⚠️ ยังหยิบไม่ครบ! คุณต้องการบังคับเปลี่ยนสถานะหรือไม่?"
   [ยืนยัน (Force)] [ยกเลิก]
   ↓
[Admin] กด "ยืนยัน (Force)"
   ↓
[System] เปลี่ยนสถานะสำเร็จ (Force)!
```

---

## 🤖 Automatic Features (ระบบทำอัตโนมัติ)

### 1. Auto-detect Stock Increase

**เมื่อไหร่:** หลัง Import Stock

**ทำอะไร:**
- ตรวจสอบว่า SKU ใดที่สต็อกเพิ่มขึ้น (เช่น 0 → 5 ชิ้น)
- หา Shortage Records ที่ status = `pending` หรือ `waiting_stock`
- เปลี่ยนสถานะเป็น `ready_to_pick` อัตโนมัติ
- แสดง Flash Message แจ้ง Admin

**ตัวอย่าง:**

```
[Warehouse] Import Stock:
   - SKU-001: 0 → 5 ชิ้น
   - SKU-002: 3 → 8 ชิ้น
   ↓
[System] ตรวจจับ Shortage Records:
   - SKU-001: 2 รายการ (status = waiting_stock)
   - SKU-002: 1 รายการ (status = pending)
   ↓
[System] เปลี่ยนสถานะ:
   - SKU-001: waiting_stock → ready_to_pick (2 รายการ)
   - SKU-002: pending → ready_to_pick (1 รายการ)
   ↓
[System] แสดง Flash Message:
   "✅ SKU-001: สต็อกเพิ่มจาก 0 → 5 ชิ้น | อัปเดต Shortage 2 รายการเป็น 'พร้อมหยิบ'"
   "✅ SKU-002: สต็อกเพิ่มจาก 3 → 8 ชิ้น | อัปเดต Shortage 1 รายการเป็น 'พร้อมหยิบ'"
```

### 2. Auto-resolve When Picked Completely

**เมื่อไหร่:** หลัง Picker หยิบครบ

**ทำอะไร:**
- ตรวจสอบว่า Order ใดที่หยิบครบแล้ว (picked_qty >= qty)
- หา Shortage Records ที่เกี่ยวข้อง (status = `pending`, `waiting_stock`, `ready_to_pick`)
- เปลี่ยนสถานะเป็น `resolved` อัตโนมัติ

**ตัวอย่าง:**

```
[Picker] สแกน SKU-001 → หยิบ 2 ชิ้น
   ↓
[System] ตรวจสอบ:
   - Order: ORD001
   - ต้องการ: 2 ชิ้น
   - หยิบแล้ว: 2 ชิ้น (ครบแล้ว!)
   ↓
[System] หา Shortage Records:
   - Order: ORD001, SKU: SKU-001, Status: ready_to_pick
   ↓
[System] เปลี่ยนสถานะ:
   - ready_to_pick → resolved
   - บันทึก: "Auto-resolved: หยิบครบแล้ว"
```

---

## 📱 UI Changes

### หน้า `/scan/sku` (Picker)

**เดิม:**
- ถ้าสต็อกไม่พอ → ซ่อนปุ่ม "ยืนยันการหยิบ"
- แสดงเฉพาะปุ่ม "บันทึก Shortage"

**ใหม่:**
- ✅ แสดงปุ่ม "ยืนยันการหยิบ" เสมอ (เปลี่ยนข้อความตามสต็อก)
- ✅ เพิ่มปุ่ม Hybrid: "บันทึกหยิบ X + Shortage Y ชิ้น"
- Picker สามารถเลือกได้ว่าจะทำทีเดียวหรือแยกทำ

### หน้า `/shortage-queue` (Admin)

**เดิม:**
- แสดง Status Badge แบบคงที่
- ต้องกดปุ่ม "แก้ไข" → เลือก Action

**ใหม่:**
- ✅ แสดง Status Dropdown ในตาราง → เปลี่ยนได้ทันที
- ✅ เพิ่มสถานะ `ready_to_pick` ในฟิลเตอร์และ Dropdown
- ✅ Confirmation Dialog เมื่อเปลี่ยนเป็น `resolved` แต่ยังหยิบไม่ครบ

---

## 🔧 Technical Changes

### 1. Database Schema

**ไม่ต้องเปลี่ยน Schema** (ใช้ TEXT column เดิม)

เพิ่มสถานะใหม่:
- `ready_to_pick` (พร้อมหยิบ)

### 2. API Endpoints

**ใหม่:**
- `POST /api/shortage/change-status` - เปลี่ยนสถานะ Shortage Record

**อัปเดต:**
- `POST /api/shortage/mark` - รองรับ Hybrid Flow (หยิบ + shortage พร้อมกัน)
- `POST /api/pick/sku` - Auto-resolve เมื่อหยิบครบ

### 3. Importers

**อัปเดต:** `importers.py` - `import_stock()`
- Auto-detect Stock Increase
- เปลี่ยนสถานะ Shortage Records เป็น `ready_to_pick`

---

## ✅ Benefits

1. **Picker ไม่ต้องรอ Admin** → ทำงานต่อได้เสมอ
2. **Admin ควบคุมได้** → เปลี่ยนสถานะได้ตามต้องการ
3. **ระบบช่วยอัตโนมัติ** → ลด Manual Work
4. **Real-time Sync** → ข้อมูลถูกต้องตลอดเวลา
5. **Flexible & Scalable** → รองรับ Workflow หลากหลาย

---

## 📞 Support

หากพบปัญหาหรือต้องการความช่วยเหลือ:
- **Technical Issue:** แจ้งทีม IT
- **Workflow Question:** ดูคู่มือ [teamwork-manual-wms.md](./teamwork-manual-wms.md)
- **Bug Report:** สร้าง Issue ใน GitHub

---

**© 2025 บริษัท วีนิก กรุ๊ป จำกัด - Internal Documentation**
