# UI Design System Documentation
# เอกสารระบบออกแบบ UI

**VNIX Order Management System (WMS)**
**Last Updated:** 2025-11-19

---

## Table of Contents | สารบัญ

- [Overview | ภาพรวม](#overview--ภาพรวม)
- [Color Palette | โทนสี](#color-palette--โทนสี)
- [Typography | การตั้งค่าฟอนต์](#typography--การตั้งค่าฟอนต์)
- [Buttons | ปุ่ม](#buttons--ปุ่ม)
- [Cards | การ์ด](#cards--การ์ด)
- [Tables | ตาราง](#tables--ตาราง)
- [Forms | ฟอร์ม](#forms--ฟอร์ม)
- [Badges | ป้ายสถานะ](#badges--ป้ายสถานะ)
- [Alerts | การแจ้งเตือน](#alerts--การแจ้งเตือน)
- [Modals | หน้าต่างป๊อปอัพ](#modals--หน้าต่างป๊อปอัพ)
- [Icons | ไอคอน](#icons--ไอคอน)
- [Confirmation Dialogs | ป๊อปอัพยืนยัน](#confirmation-dialogs--ป๊อปอัพยืนยัน)
- [Spacing & Layout | ระยะห่างและการจัดวาง](#spacing--layout--ระยะห่างและการจัดวาง)

---

## Overview | ภาพรวม

The VNIX WMS uses a **minimalist, modern design system** inspired by Tailwind CSS and Bootstrap 5, with a focus on:

ระบบ VNIX WMS ใช้**ระบบออกแบบที่เรียบง่ายและทันสมัย** โดยได้แรงบันดาลใจจาก Tailwind CSS และ Bootstrap 5 โดยเน้น:

- **Clean and Professional Look** | **รูปลักษณ์ที่สะอาดและเป็นมืออาชีพ**
- **High Readability** | **อ่านง่าย**
- **Consistent UI Components** | **ส่วนประกอบ UI ที่สม่ำเสมอ**
- **Responsive Design** | **ออกแบบให้รองรับทุกหน้าจอ**
- **Blue-based Color Theme** | **โทนสีหลักเป็นสีน้ำเงิน**

**Key Technologies:**
- **Bootstrap 5.3.2** - Base CSS framework
- **IBM Plex Sans Thai** - Primary font (supports Thai language beautifully)
- **Lucide Icons** - Modern icon library
- **DataTables** - Enhanced table functionality
- **Custom CSS** (`theme.css`) - Design system variables and components

---

## Color Palette | โทนสี

### Primary Colors (Blue Theme) | สีหลัก (โทนสีน้ำเงิน)

Our primary color scheme is based on a blue palette that conveys trust, professionalism, and clarity.

โทนสีหลักของเราใช้สีน้ำเงินที่แสดงถึงความน่าเชื่อถือ ความเป็นมืออาชีพ และความชัดเจน

| Color | Hex Code | CSS Variable | Usage |
|-------|----------|--------------|-------|
| Primary 50 | `#eff6ff` | `var(--primary-50)` | Light backgrounds, hover states |
| Primary 100 | `#dbeafe` | `var(--primary-100)` | Focus rings, subtle backgrounds |
| Primary 200 | `#bfdbfe` | `var(--primary-200)` | Borders, dividers |
| Primary 300 | `#93c5fd` | `var(--primary-300)` | Disabled states |
| Primary 400 | `#60a5fa` | `var(--primary-400)` | Secondary buttons |
| Primary 500 | `#3b82f6` | `var(--primary-500)` | Links, active states |
| **Primary 600** | **`#2563eb`** | **`var(--primary-600)`** | **Main brand color, primary buttons** |
| Primary 700 | `#1d4ed8` | `var(--primary-700)` | Hover states, dark mode |
| Primary 800 | `#1e40af` | `var(--primary-800)` | Text on light backgrounds |
| Primary 900 | `#1e3a8a` | `var(--primary-900)` | Headings, emphasis |

### Semantic Colors | สีตามความหมาย

| Purpose | Color Name | Hex Code | CSS Variable | Usage Example |
|---------|------------|----------|--------------|---------------|
| Success | Green | `#16a34a` | `var(--success-color)` | Completed orders, success messages |
| Warning | Orange | `#f59e0b` | `var(--warning-color)` | Pending actions, warnings |
| Danger | Red | `#dc2626` | `var(--danger-color)` | Errors, shortage alerts |
| Info | Sky Blue | `#0ea5e9` | `var(--info-color)` | Information messages, progress |

**ตัวอย่างการใช้งาน:**
- **Success (เขียว):** สถานะสำเร็จ, ออเดอร์ที่เสร็จสมบูรณ์
- **Warning (ส้ม):** รอดำเนินการ, สถานะที่ต้องแจ้งเตือน
- **Danger (แดง):** ข้อผิดพลาด, สินค้าขาด (Shortage)
- **Info (ฟ้า):** ข้อมูลเพิ่มเติม, ความคืบหน้า

### Gray Scale | โทนสีเทา

| Shade | Hex Code | CSS Variable | Usage |
|-------|----------|--------------|-------|
| Gray 50 | `#f9fafb` | `var(--gray-50)` | Page background, light surfaces |
| Gray 100 | `#f3f4f6` | `var(--gray-100)` | Table headers, light badges |
| Gray 200 | `#e5e7eb` | `var(--gray-200)` | Borders, dividers |
| Gray 300 | `#d1d5db` | `var(--gray-300)` | Input borders, subtle dividers |
| Gray 400 | `#9ca3af` | `var(--gray-400)` | Placeholders, disabled text |
| Gray 500 | `#6b7280` | `var(--gray-500)` | Secondary text, muted elements |
| Gray 600 | `#4b5563` | `var(--gray-600)` | Body text, badges |
| Gray 700 | `#374151` | `var(--gray-700)` | Headings, labels |
| Gray 800 | `#1f2937` | `var(--gray-800)` | Dark navbar, emphasis text |
| Gray 900 | `#111827` | `var(--gray-900)` | Main text color, headings |

### Carrier Colors | สีตามขนส่ง

Different logistics carriers have distinct badge colors for easy visual identification.

ขนส่งแต่ละประเภทมีสีเฉพาะเพื่อให้จำแนกได้ง่าย:

| Carrier | Badge Class | Color | Example |
|---------|-------------|-------|---------|
| **SPX** | `bg-danger` | Red (`#dc2626`) | `<span class="badge bg-danger">SPX</span>` |
| **Flash** | `bg-warning text-dark` | Orange (`#f59e0b`) | `<span class="badge bg-warning text-dark">Flash</span>` |
| **LEX** | `bg-primary` | Blue (`#2563eb`) | `<span class="badge bg-primary">LEX</span>` |
| **J&T** | `bg-success` | Green (`#16a34a`) | `<span class="badge bg-success">J&T</span>` |
| **Other** | `bg-secondary` | Gray (`#4b5563`) | `<span class="badge bg-secondary">Other</span>` |

### Platform Colors | สีตามแพลตฟอร์ม

| Platform | Badge Class | Color | Example |
|----------|-------------|-------|---------|
| **Shopee** | `bg-danger` | Red | `<span class="badge bg-danger fs-6">Shopee</span>` |
| **Lazada** | `bg-primary` | Blue | `<span class="badge bg-primary fs-6">Lazada</span>` |
| **TikTok** | `bg-dark` | Black | `<span class="badge bg-dark fs-6">TikTok</span>` |

---

## Typography | การตั้งค่าฟอนต์

### Font Family | แบบอักษร

**Primary Font:** IBM Plex Sans Thai
**Monospace Font:** SF Mono, Monaco, Cascadia Code, Courier New

```css
--font-sans: 'IBM Plex Sans Thai', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'SF Mono', 'Monaco', 'Cascadia Code', 'Courier New', monospace;
```

**Why IBM Plex Sans Thai?**
- Excellent Thai language support with beautiful letterforms
- Professional and modern appearance
- Great readability on screens
- Supports multiple weights (300, 400, 500, 600, 700)

**เหตุผลที่เลือก IBM Plex Sans Thai:**
- รองรับภาษาไทยได้ดีเยี่ยมด้วยรูปแบบตัวอักษรที่สวยงาม
- มีความเป็นมืออาชีพและทันสมัย
- อ่านง่ายบนหน้าจอ
- รองรับหลายระดับความหนา

### Font Sizes | ขนาดตัวอักษร

| Element | Size | Usage |
|---------|------|-------|
| Small text | `0.8125rem` (13px) | Captions, metadata |
| Body text | `0.875rem` (14px) | Main content, form inputs |
| Medium | `1rem` (16px) | Emphasis text |
| Large | `1.25rem` (20px) | Section headings |
| Display | `2rem - 3rem` | Page titles, KPIs |

### Font Weights | น้ำหนักตัวอักษร

| Weight | CSS | Usage |
|--------|-----|-------|
| Light | `300` | Subtle text, secondary info |
| Regular | `400` | Body text |
| Medium | `500` | Labels, form fields |
| Semi-bold | `600` | Headings, emphasis |
| Bold | `700` | Main headings, brand name |

---

## Buttons | ปุ่ม

### Button Styles | รูปแบบปุ่ม

All buttons feature:
- Smooth hover transitions (200ms)
- Slight upward translation on hover (`translateY(-1px)`)
- Shadow effects for depth
- Icon + text combination support
- Rounded corners (`8px`)

ปุ่มทั้งหมดมีคุณสมบัติ:
- การเปลี่ยนแปลงที่นุ่มนวลเมื่อเลื่อนเมาส์ผ่าน
- เคลื่อนตัวขึ้นเล็กน้อยเมื่อ hover
- เงาเพิ่มความลึก
- รองรับการใส่ไอคอนร่วมกับข้อความ
- มุมโค้งมน

### Primary Buttons | ปุ่มหลัก

```html
<button class="btn btn-primary">
  <i data-lucide="plus-circle"></i> สร้าง Batch ใหม่
</button>
```

**Style:**
- Background: `#2563eb` (Primary 600)
- Hover: `#1d4ed8` (Primary 700)
- Text: White
- Shadow: Subtle → Medium on hover

**Usage:** Main actions, primary CTAs
**การใช้งาน:** การดำเนินการหลัก เช่น สร้าง, ยืนยัน, บันทึก

### Success Buttons | ปุ่มสำเร็จ

```html
<button class="btn btn-success">
  <i data-lucide="check-circle"></i> ยืนยันส่งมอบ
</button>
```

**Style:**
- Background: `#16a34a` (Green)
- Hover: `#15803d`
- Text: White

**Usage:** Confirmation actions, completion
**การใช้งาน:** ยืนยันการดำเนินการ, การสำเร็จ

### Warning Buttons | ปุ่มเตือน

```html
<button class="btn btn-warning">
  <i data-lucide="alert-triangle"></i> แยก Batch
</button>
```

**Style:**
- Background: `#f59e0b` (Orange)
- Hover: `#d97706`
- Text: White

**Usage:** Cautionary actions, warnings
**การใช้งาน:** การดำเนินการที่ต้องระวัง, การแจ้งเตือน

### Danger Buttons | ปุ่มอันตราย

```html
<button class="btn btn-danger">
  <i data-lucide="trash-2"></i> ลบข้อมูล
</button>
```

**Style:**
- Background: `#dc2626` (Red)
- Hover: `#b91c1c`
- Text: White

**Usage:** Destructive actions, deletions
**การใช้งาน:** การลบ, การดำเนินการที่อันตราย

### Info Buttons | ปุ่มข้อมูล

```html
<button class="btn btn-info">
  <i data-lucide="eye"></i> รายละเอียด
</button>
```

**Style:**
- Background: `#0ea5e9` (Sky Blue)
- Hover: `#0284c7`
- Text: White

**Usage:** View details, information
**การใช้งาน:** ดูรายละเอียด, ข้อมูลเพิ่มเติม

### Secondary Buttons | ปุ่มรอง

```html
<button class="btn btn-secondary">
  <i data-lucide="x"></i> ยกเลิก
</button>
```

**Style:**
- Background: `#4b5563` (Gray 600)
- Text: White

**Usage:** Cancel, back actions
**การใช้งาน:** ยกเลิก, กลับ

### Outline Buttons | ปุ่มกรอบ

```html
<button class="btn btn-outline-primary">
  <i data-lucide="filter"></i> กรองข้อมูล
</button>
```

**Style:**
- Border: 1.5px solid (color matches variant)
- Background: White → Tinted on hover
- Text: Color matches variant

**Usage:** Secondary actions, less emphasis
**การใช้งาน:** การดำเนินการรอง ไม่ต้องการเน้นมาก

### Button Sizes | ขนาดปุ่ม

```html
<!-- Small -->
<button class="btn btn-sm btn-primary">Small Button</button>

<!-- Normal (default) -->
<button class="btn btn-primary">Normal Button</button>

<!-- Large -->
<button class="btn btn-lg btn-primary">Large Button</button>
```

| Size | Class | Padding | Font Size |
|------|-------|---------|-----------|
| Small | `btn-sm` | `0.375rem 0.875rem` | `0.8125rem` (13px) |
| Normal | - | `0.625rem 1.25rem` | `0.875rem` (14px) |
| Large | `btn-lg` | `0.875rem 1.75rem` | `1rem` (16px) |

---

## Cards | การ์ด

Cards are the primary container component in our system, used for grouping related content.

การ์ดเป็นส่วนประกอบหลักในระบบของเรา ใช้สำหรับจัดกลุ่มเนื้อหาที่เกี่ยวข้อง

### Basic Card | การ์ดพื้นฐาน

```html
<div class="card">
  <div class="card-header bg-primary text-white">
    <h5 class="mb-0">Card Title</h5>
  </div>
  <div class="card-body">
    Card content goes here
  </div>
</div>
```

**Style Features:**
- Border radius: `12px` (rounded-lg)
- Border: `1px solid #e5e7eb`
- Shadow: Subtle (`var(--shadow-sm)`)
- Hover effect: Elevated shadow
- Background: White

### Card Header Colors | สีหัวการ์ด

```html
<!-- Primary (Blue) -->
<div class="card-header bg-primary text-white">

<!-- Success (Green) -->
<div class="card-header bg-success text-white">

<!-- Warning (Orange) -->
<div class="card-header bg-warning text-white">

<!-- Danger (Red) -->
<div class="card-header bg-danger text-white">

<!-- Info (Sky Blue) -->
<div class="card-header bg-info text-white">

<!-- Dark (Gray) -->
<div class="card-header bg-dark text-white">

<!-- Secondary (Gray) -->
<div class="card-header bg-secondary text-white">

<!-- Light (for white/light backgrounds) -->
<div class="card-header bg-light">
```

### Card Borders | ขอบการ์ด

```html
<!-- Warning border -->
<div class="card border-warning border-3">

<!-- Success border -->
<div class="card border-success border-3">

<!-- Danger border -->
<div class="card border-danger border-3">
```

**Border widths:**
- Default: `1px`
- `border-2`: `2px`
- `border-3`: `3px`

### Stats Card Example | ตัวอย่างการ์ดสถิติ

```html
<div class="col-md-3">
  <div class="card bg-primary text-white h-100">
    <div class="card-body text-center">
      <div class="display-3 fw-bold">
        <i data-lucide="package" style="width: 64px; height: 64px;"></i>
      </div>
      <h1 class="display-3 fw-bold mb-2">{{ batch.total_orders }}</h1>
      <p class="mb-0 fs-6">จำนวนออเดอร์ทั้งหมด</p>
    </div>
  </div>
</div>
```

---

## Tables | ตาราง

### Basic Table | ตารางพื้นฐาน

```html
<table class="table table-hover table-bordered">
  <thead class="table-dark">
    <tr>
      <th>Column 1</th>
      <th>Column 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Data 1</td>
      <td>Data 2</td>
    </tr>
  </tbody>
</table>
```

**Style Features:**
- **Header:**
  - Background: `#f9fafb` (Gray 50) or dark variant
  - Font weight: 600
  - Text transform: Uppercase
  - Letter spacing: Increased
  - Font size: `0.8125rem` (13px)

- **Body:**
  - Font size: `0.875rem` (14px)
  - Border: `1px solid #e5e7eb`
  - Hover: Light gray background (`#f9fafb`)

### Table Variants | รูปแบบตาราง

```html
<!-- Hover effect -->
<table class="table table-hover">

<!-- Bordered -->
<table class="table table-bordered">

<!-- Striped rows -->
<table class="table table-striped">

<!-- Small/compact -->
<table class="table table-sm">

<!-- Dark header -->
<table class="table">
  <thead class="table-dark">
    ...
  </thead>
</table>

<!-- Light header -->
<table class="table">
  <thead class="table-light">
    ...
  </thead>
</table>
```

### Row Colors | สีแถว

```html
<!-- Success row (green background) -->
<tr class="table-success">

<!-- Warning row (yellow background) -->
<tr class="table-warning">

<!-- Danger row (red background) -->
<tr class="table-danger">

<!-- Info row (blue background) -->
<tr class="table-info">
```

**การใช้งาน:**
- `table-success`: แถวที่เสร็จสมบูรณ์
- `table-warning`: แถวที่กำลังดำเนินการ
- `table-danger`: แถวที่มีปัญหาหรือขาด (shortage)

### DataTables Integration | การใช้งาน DataTables

```javascript
$('#myTable').DataTable({
  pageLength: 25,
  order: [[0, 'asc']],
  language: {
    url: '//cdn.datatables.net/plug-ins/1.13.8/i18n/th.json'
  }
});
```

**Features enabled:**
- Pagination (25 items per page)
- Sorting
- Search/filter
- Thai language support

---

## Forms | ฟอร์ม

### Form Controls | ส่วนควบคุมฟอร์ม

```html
<div class="mb-3">
  <label class="form-label">ชื่อฟิลด์</label>
  <input type="text" class="form-control" placeholder="กรอกข้อมูล">
</div>

<div class="mb-3">
  <label class="form-label">เลือกตัวเลือก</label>
  <select class="form-select">
    <option>ตัวเลือก 1</option>
    <option>ตัวเลือก 2</option>
  </select>
</div>
```

**Style Features:**
- Border radius: `8px`
- Border: `1.5px solid #d1d5db` (Gray 300)
- Padding: `0.625rem 0.875rem`
- Font size: `0.875rem` (14px)
- Focus state:
  - Border color: `#2563eb` (Primary 600)
  - Box shadow: `0 0 0 3px rgba(37, 99, 235, 0.1)`

### Form Layout | การจัดวางฟอร์ม

```html
<form class="row g-3">
  <div class="col-md-4">
    <label class="form-label">Platform</label>
    <select class="form-select" name="platform">
      <option value="">ทั้งหมด</option>
      <option value="Shopee">Shopee</option>
      <option value="Lazada">Lazada</option>
    </select>
  </div>

  <div class="col-md-4">
    <label class="form-label">วันที่</label>
    <input type="date" class="form-control" name="date">
  </div>

  <div class="col-md-4 d-flex align-items-end">
    <button type="submit" class="btn btn-primary w-100">
      <i data-lucide="search"></i> ค้นหา
    </button>
  </div>
</form>
```

---

## Badges | ป้ายสถานะ

### Badge Styles | รูปแบบป้าย

```html
<!-- Primary -->
<span class="badge bg-primary">Primary</span>

<!-- Success -->
<span class="badge bg-success">Success</span>

<!-- Warning -->
<span class="badge bg-warning text-dark">Warning</span>

<!-- Danger -->
<span class="badge bg-danger">Danger</span>

<!-- Info -->
<span class="badge bg-info">Info</span>

<!-- Secondary -->
<span class="badge bg-secondary">Secondary</span>

<!-- Light -->
<span class="badge bg-light text-dark">Light</span>

<!-- Dark -->
<span class="badge bg-dark">Dark</span>
```

### Badge Sizes | ขนาดป้าย

```html
<!-- Default -->
<span class="badge bg-primary">Default</span>

<!-- Large (fs-6 = 1rem) -->
<span class="badge bg-primary fs-6">Large</span>

<!-- Small (custom) -->
<span class="badge bg-primary" style="font-size: 0.7rem;">Small</span>
```

### Badge with Icons | ป้ายพร้อมไอคอน

```html
<span class="badge bg-success fs-6">
  <i data-lucide="check-circle" style="width: 14px; height: 14px;"></i>
  ส่งมอบแล้ว
</span>

<span class="badge bg-warning text-dark fs-6">
  <i data-lucide="clock" style="width: 14px; height: 14px;"></i>
  รอยืนยัน
</span>
```

**Common Badge Uses in WMS:**
- Lock status: `<span class="badge bg-success"><i data-lucide="lock"></i> Locked</span>`
- Platform: `<span class="badge bg-danger fs-6">Shopee</span>`
- Carrier: `<span class="badge bg-danger">SPX: 15</span>`
- Handover status: `<span class="badge bg-success">ส่งแล้ว</span>`

---

## Alerts | การแจ้งเตือน

### Alert Types | ประเภทการแจ้งเตือน

```html
<!-- Info Alert -->
<div class="alert alert-info" role="alert">
  <i data-lucide="info"></i>
  This is an informational message
</div>

<!-- Success Alert -->
<div class="alert alert-success" role="alert">
  <i data-lucide="check-circle"></i>
  Operation completed successfully
</div>

<!-- Warning Alert -->
<div class="alert alert-warning" role="alert">
  <i data-lucide="alert-triangle"></i>
  Please review this warning
</div>

<!-- Danger Alert -->
<div class="alert alert-danger" role="alert">
  <i data-lucide="alert-circle"></i>
  An error occurred
</div>
```

**Style Features:**
- Border radius: `12px`
- Left border: `4px solid` (color matches variant)
- Padding: `1rem 1.25rem`
- No top/right/bottom borders
- Subtle shadow

### Dismissible Alerts | แจ้งเตือนที่ปิดได้

```html
<div class="alert alert-success alert-dismissible fade show" role="alert">
  {{ message }}
  <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
```

**Used for:**
- Flash messages from Flask
- Success confirmations
- Error notifications
- Warning messages

---

## Modals | หน้าต่างป๊อปอัพ

### Basic Modal Structure | โครงสร้างพื้นฐาน

```html
<div class="modal fade" id="myModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header bg-warning">
        <h5 class="modal-title">Modal Title</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <!-- Content -->
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
          ยกเลิก
        </button>
        <button type="button" class="btn btn-primary">
          ยืนยัน
        </button>
      </div>
    </div>
  </div>
</div>
```

### Modal Sizes | ขนาด Modal

```html
<!-- Small -->
<div class="modal-dialog modal-sm">

<!-- Default -->
<div class="modal-dialog">

<!-- Large -->
<div class="modal-dialog modal-lg">

<!-- Extra Large -->
<div class="modal-dialog modal-xl">

<!-- Full Width -->
<div class="modal-dialog modal-fullscreen">
```

### Opening Modal with JavaScript

```javascript
const modal = new bootstrap.Modal(document.getElementById('myModal'));
modal.show();
```

---

## Icons | ไอคอน

### Lucide Icons Integration

We use **Lucide Icons** - a beautiful, consistent icon set with 1000+ icons.

เราใช้ **Lucide Icons** - ชุดไอคอนที่สวยงามและสม่ำเสมอ มีมากกว่า 1000 ไอคอน

### Basic Usage | การใช้งานพื้นฐาน

```html
<i data-lucide="package"></i>
<i data-lucide="check-circle"></i>
<i data-lucide="alert-triangle"></i>
<i data-lucide="user"></i>
<i data-lucide="settings"></i>
```

### Icon Sizes | ขนาดไอคอน

```html
<!-- Inline with text (16x16) -->
<i data-lucide="package" style="width: 16px; height: 16px;"></i>

<!-- Medium (24x24) -->
<i data-lucide="package" style="width: 24px; height: 24px;"></i>

<!-- Large (64x64) -->
<i data-lucide="package" style="width: 64px; height: 64px;"></i>
```

### Common Icons Used in WMS

| Icon Name | Usage | Example |
|-----------|-------|---------|
| `package` | Batches, orders | `<i data-lucide="package"></i>` |
| `shopping-cart` | Orders | `<i data-lucide="shopping-cart"></i>` |
| `check-circle` | Success, completion | `<i data-lucide="check-circle"></i>` |
| `alert-triangle` | Warnings, shortage | `<i data-lucide="alert-triangle"></i>` |
| `eye` | View details | `<i data-lucide="eye"></i>` |
| `printer` | Print functions | `<i data-lucide="printer"></i>` |
| `qr-code` | QR codes | `<i data-lucide="qr-code"></i>` |
| `scan` | Scanning | `<i data-lucide="scan"></i>` |
| `user` | Users | `<i data-lucide="user"></i>` |
| `lock` / `unlock` | Lock status | `<i data-lucide="lock"></i>` |
| `upload` | Import | `<i data-lucide="upload"></i>` |
| `download` | Export | `<i data-lucide="download"></i>` |
| `trash-2` | Delete | `<i data-lucide="trash-2"></i>` |
| `plus-circle` | Add/Create | `<i data-lucide="plus-circle"></i>` |
| `filter` | Filter | `<i data-lucide="filter"></i>` |

### Icon Initialization

Icons are automatically initialized on page load and after dynamic content updates:

```javascript
// Auto-initialized in base.html
lucide.createIcons();

// Manual refresh if needed
if (window.refreshIcons) {
  window.refreshIcons();
}
```

---

## Confirmation Dialogs | ป๊อปอัพยืนยัน

### Standard JavaScript `confirm()`

We use the native browser confirmation dialog with informative messages:

เราใช้ป๊อปอัพยืนยันของเบราว์เซอร์พร้อมข้อความที่ให้ข้อมูล:

```javascript
// Simple confirmation
if (confirm('คุณต้องการลบข้อมูลนี้หรือไม่?')) {
  // Proceed with deletion
}

// Detailed confirmation with explanation
if (confirm(
  'คุณต้องการสร้างรหัสส่งมอบสำหรับ Batch นี้หรือไม่?\n\n' +
  'รหัสนี้จะใช้สำหรับยืนยันการส่งมอบพัสดุให้ขนส่ง'
)) {
  // Generate handover code
}

// Multi-line informative confirmation
if (confirm(
  'คุณต้องการแยก Batch นี้หรือไม่?\n\n' +
  'ระบบจะแยกเป็น 2 Batch:\n' +
  '✅ Batch แม่ (เดิม) → Orders ที่หยิบครบแล้ว (ส่งได้ทันที)\n' +
  '⏳ Batch ลูก (ใหม่) → Orders ที่มี Shortage (รอสต็อกเข้า)\n\n' +
  'ดำเนินการต่อไหม?'
)) {
  // Split batch
}
```

### `prompt()` for User Input

```javascript
const notes = prompt(
  'ยกเลิก Shortage สำหรับ SKU: ' + sku + '\n\nกรุณาระบุหมายเหตุ:',
  ''
);

if (notes === null) {
  return; // User cancelled
}

// Proceed with notes
```

### Best Practices | แนวทางปฏิบัติที่ดี

**✅ DO:**
- Use clear, concise Thai language
- Explain what will happen
- Use emojis for visual clarity (✅, ⏳, ❌)
- Provide context and consequences
- Check for `null` return (user cancelled)

**❌ DON'T:**
- Use generic "Are you sure?" messages
- Assume the user knows what will happen
- Use English for user-facing messages (Thai preferred)
- Skip confirmation for destructive actions

---

## Spacing & Layout | ระยะห่างและการจัดวาง

### Spacing Variables | ตัวแปรระยะห่าง

```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */
--spacing-2xl: 3rem;     /* 48px */
```

### Bootstrap Spacing Utilities

```html
<!-- Margin -->
<div class="m-0">No margin</div>
<div class="mt-3">Margin top 1rem</div>
<div class="mb-4">Margin bottom 1.5rem</div>
<div class="mx-auto">Horizontal center</div>

<!-- Padding -->
<div class="p-3">Padding 1rem</div>
<div class="py-4">Vertical padding 1.5rem</div>
<div class="px-5">Horizontal padding 3rem</div>

<!-- Gap (for flexbox/grid) -->
<div class="d-flex gap-2">
  <button>Button 1</button>
  <button>Button 2</button>
</div>
```

### Border Radius | มุมโค้ง

```css
--radius-sm: 6px;    /* Small components */
--radius-md: 8px;    /* Buttons, inputs */
--radius-lg: 12px;   /* Cards */
--radius-xl: 16px;   /* Large cards */
--radius-full: 9999px; /* Pills, circles */
```

### Shadows | เงา

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.05);
--shadow-xl: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
```

**Usage:**
```html
<div class="shadow-sm">Subtle shadow</div>
<div class="shadow-md">Medium shadow</div>
<div class="shadow-lg">Large shadow</div>
```

### Grid Layout | การจัดวางแบบตาราง

```html
<div class="row g-3">
  <div class="col-md-4">Column 1</div>
  <div class="col-md-4">Column 2</div>
  <div class="col-md-4">Column 3</div>
</div>
```

**Responsive Columns:**
- `col-12`: Full width on mobile
- `col-md-6`: Half width on tablets+
- `col-lg-4`: 1/3 width on desktops+

---

## Progress Bars | แถบความคืบหน้า

### Basic Progress Bar

```html
<div class="progress" style="height: 24px;">
  <div class="progress-bar bg-success fw-bold"
       role="progressbar"
       style="width: 75%"
       aria-valuenow="75"
       aria-valuemin="0"
       aria-valuemax="100">
    75%
  </div>
</div>
```

### Colored Progress Bars

```html
<!-- Success (Green) - 100% completed -->
<div class="progress-bar bg-success">100%</div>

<!-- Info (Blue) - 50-99% -->
<div class="progress-bar bg-info">75%</div>

<!-- Warning (Yellow) - Below 50% -->
<div class="progress-bar bg-warning">35%</div>
```

**Typical Usage in WMS:**
```html
{% if progress.percent == 100 %}
  <div class="progress-bar bg-success fw-bold">100%</div>
{% elif progress.percent >= 50 %}
  <div class="progress-bar bg-info fw-bold">{{ progress.percent }}%</div>
{% else %}
  <div class="progress-bar bg-warning fw-bold">{{ progress.percent }}%</div>
{% endif %}
```

---

## Responsive Design | การออกแบบที่รองรับหลายหน้าจอ

### Breakpoints | จุดหยุด

| Breakpoint | Screen Width | Class Prefix |
|------------|--------------|--------------|
| Extra Small | < 576px | `col-` |
| Small | ≥ 576px | `col-sm-` |
| Medium | ≥ 768px | `col-md-` |
| Large | ≥ 992px | `col-lg-` |
| Extra Large | ≥ 1200px | `col-xl-` |
| XXL | ≥ 1400px | `col-xxl-` |

### Responsive Utilities

```html
<!-- Hide on mobile, show on desktop -->
<div class="d-none d-md-block">Desktop only</div>

<!-- Show on mobile, hide on desktop -->
<div class="d-block d-md-none">Mobile only</div>

<!-- Hide on large screens -->
<td class="d-none d-lg-table-cell">Desktop Table Cell</td>
```

---

## Print Styles | การพิมพ์

```html
<!-- Print Button -->
<button class="btn btn-primary" onclick="window.print()">
  <i data-lucide="printer"></i> พิมพ์
</button>
```

**Print-specific CSS:**
```css
@media print {
  body {
    background: white;
  }

  .d-print-none {
    display: none !important;
  }

  .card {
    box-shadow: none;
    border: 1px solid #d1d5db;
  }
}
```

---

## Component Examples | ตัวอย่างส่วนประกอบ

### Quick Action Button Group

```html
<div class="btn-group" role="group">
  <a href="#" class="btn btn-sm btn-info">
    <i data-lucide="eye"></i> รายละเอียด
  </a>
  <a href="#" class="btn btn-sm btn-secondary">
    <i data-lucide="file-code"></i> JSON
  </a>
</div>
```

### Stat Cards Grid

```html
<div class="row mb-4">
  <!-- Total Orders -->
  <div class="col-md-3 col-6 mb-3">
    <div class="card bg-primary text-white h-100">
      <div class="card-body text-center">
        <h1 class="display-3 fw-bold mb-2">{{ total_orders }}</h1>
        <p class="mb-0 fs-6">จำนวนออเดอร์ทั้งหมด</p>
      </div>
    </div>
  </div>

  <!-- Lock Status -->
  <div class="col-md-3 col-6 mb-3">
    <div class="card bg-success text-white h-100">
      <div class="card-body text-center">
        <h1 class="display-3 mb-2">
          <i data-lucide="lock" style="width: 64px; height: 64px;"></i>
        </h1>
        <p class="mb-0 fs-5 fw-bold">Locked</p>
      </div>
    </div>
  </div>
</div>
```

### Information Alert with Icon

```html
<div class="alert alert-info mb-3">
  <h6 class="alert-heading">
    <i data-lucide="info"></i> วิธีใช้งาน:
  </h6>
  <ol class="mb-0 small">
    <li>พนักงานคลังสแกน QR Code นี้</li>
    <li>ระบบจะบันทึกว่ารับงานแล้ว</li>
    <li>เริ่มหยิบสินค้าตาม SKU</li>
  </ol>
</div>
```

---

## Accessibility | การเข้าถึง

### ARIA Labels

```html
<button class="btn btn-primary" aria-label="สร้าง Batch ใหม่">
  <i data-lucide="plus-circle"></i>
</button>

<div class="spinner-border" role="status">
  <span class="visually-hidden">กำลังโหลด...</span>
</div>
```

### Focus States

All interactive elements have clear focus indicators:
- Buttons: Blue ring on focus
- Inputs: Blue border + shadow on focus
- Links: Underline + color change

---

## Animation & Transitions | การเคลื่อนไหวและการเปลี่ยนผ่าน

### Transition Variables

```css
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
```

### Common Animations

**Button Hover:**
```css
.btn:hover {
  transform: translateY(-1px);
  transition: all 200ms;
}
```

**Card Hover:**
```css
.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
```

**Loading Spinner:**
```html
<div class="spinner-border text-primary" role="status">
  <span class="visually-hidden">กำลังโหลด...</span>
</div>
```

---

## Best Practices Summary | สรุปแนวทางปฏิบัติที่ดี

### ✅ DO:

1. **Use semantic colors** - Success = Green, Danger = Red, etc.
2. **Maintain consistent spacing** - Use Bootstrap spacing utilities
3. **Add icons to buttons** - Improves visual recognition
4. **Use clear labels** - Both Thai and English when appropriate
5. **Provide feedback** - Loading states, success messages, errors
6. **Test responsiveness** - Works on mobile, tablet, desktop
7. **Use confirmation dialogs** - For destructive actions
8. **Follow the established color palette** - Don't introduce random colors

### ❌ DON'T:

1. **Don't mix different design patterns** - Stick to the system
2. **Don't use inline styles excessively** - Use CSS classes
3. **Don't skip hover/focus states** - Important for UX
4. **Don't ignore accessibility** - Add ARIA labels where needed
5. **Don't use too many colors** - Stick to the palette
6. **Don't create new button styles** - Use existing variants
7. **Don't forget loading states** - Show spinners for async actions
8. **Don't use small font sizes** - Minimum 13px for readability

---

## File Structure | โครงสร้างไฟล์

```
vnix-wms-main/
├── templates/
│   ├── base.html              # Base template with navbar, footer
│   ├── batch_list.html        # Example: Cards, tables, badges
│   ├── batch_detail.html      # Example: Stats cards, progress bars
│   └── ...
├── static/
│   ├── theme.css              # Main design system CSS
│   ├── style.css              # Additional styles
│   └── main.js                # JavaScript utilities
└── docs/
    └── UI.md                  # This documentation
```

---

## Color Reference Quick Copy | คัดลอกสีด่วน

### Primary Blue Scale
```
#eff6ff  --primary-50
#dbeafe  --primary-100
#bfdbfe  --primary-200
#93c5fd  --primary-300
#60a5fa  --primary-400
#3b82f6  --primary-500
#2563eb  --primary-600  ⭐ Main Brand
#1d4ed8  --primary-700
#1e40af  --primary-800
#1e3a8a  --primary-900
```

### Semantic Colors
```
#16a34a  Success (Green)
#f59e0b  Warning (Orange)
#dc2626  Danger (Red)
#0ea5e9  Info (Sky Blue)
```

### Grays
```
#f9fafb  Gray 50 (Background)
#e5e7eb  Gray 200 (Borders)
#6b7280  Gray 500 (Secondary Text)
#111827  Gray 900 (Main Text)
```

---

## Support | การสนับสนุน

For questions or suggestions about the UI design system:

สำหรับคำถามหรือข้อเสนอแนะเกี่ยวกับระบบออกแบบ UI:

- **GitHub Issues:** https://github.com/tetipong2542/vnix-wms/issues
- **Documentation:** `/docs/UI.md`
- **Design Reference:** `static/theme.css`

---

**Last Updated:** 2025-11-19
**Version:** 1.0
**Maintained by:** VNIX Group Development Team
