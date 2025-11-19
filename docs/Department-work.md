# 🏢 Department Workflow & Permission Guide
## แนวทางการแบ่งแผนก และกำหนดสิทธิ์การเข้าถึงระบบ VNIX WMS

---

## 📋 สารบัญ

1. [ภาพรวมแผนก](#ภาพรวมแผนก)
2. [ทีมออนไลน์ (Online Team)](#ทีมออนไลน์-online-team)
3. [ทีมคลัง (Warehouse Team)](#ทีมคลัง-warehouse-team)
4. [Permission Matrix](#permission-matrix)
5. [Workflow แต่ละแผนก](#workflow-แต่ละแผนก)
6. [คำแนะนำการ Implementation](#คำแนะนำการ-implementation)

---

## 🎯 ภาพรวมแผนก

### แผนกภาพรวม

```
┌─────────────────────────────────────────────────────────────────┐
│                         VNIX WMS System                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
        ┌───────▼────────┐             ┌───────▼────────┐
        │  ทีมออนไลน์     │             │   ทีมคลัง      │
        │ (Online Team)  │             │(Warehouse Team)│
        └────────────────┘             └────────────────┘
                │                               │
        ┌───────┴────────┐             ┌───────┴────────┐
        │                │             │                │
    ┌───▼───┐      ┌────▼────┐   ┌───▼───┐      ┌────▼────┐
    │ Admin │      │  Staff  │   │Picker │      │Packer   │
    └───────┘      └─────────┘   └───────┘      └─────────┘
```

---

## 🛒 ทีมออนไลน์ (Online Team)

### หน้าที่รับผิดชอบ:
- 📥 นำเข้าข้อมูล (Import Orders, Products, Stock)
- 📊 สร้าง Batch สำหรับการหยิบของ
- 🔍 ติดตาม Dashboard และ Progress
- 📋 จัดการ Shortage Queue
- 📦 Export รายงาน Excel
- 🖨️ พิมพ์เอกสาร (Picking List, QR Code)

### บทบาท (Roles):

#### 1️⃣ **Online Admin** (ผู้ดูแลระบบ)
**ภาระงาน:** บริหารจัดการทั้งหมด

**สิทธิ์เข้าถึง:**
```
✅ Full Access ทุกเมนู
✅ นำเข้าข้อมูล (Import)
✅ สร้าง/ลบ Batch
✅ จัดการ Shortage Queue
✅ Export รายงาน
✅ ดู Audit Log
✅ จัดการผู้ใช้ (User Management)
✅ ปรับแก้ข้อมูล Stock/Product
```

#### 2️⃣ **Online Staff** (พนักงานทั่วไป)
**ภาระงาน:** ดูแลออเดอร์และสร้าง Batch

**สิทธิ์เข้าถึง:**
```
✅ Dashboard (View Only)
✅ สร้าง Batch
✅ ดู Batch List & Detail
✅ Export Excel (Batch ที่ตนเองสร้าง)
✅ พิมพ์ Picking List
✅ ดู Shortage Queue (Read Only)
❌ Import ข้อมูล
❌ ลบ Batch
❌ แก้ไข Stock
```

---

## 🏭 ทีมคลัง (Warehouse Team)

### หน้าที่รับผิดชอบ:
- 📦 รับงาน Batch (Scan Batch)
- 🔍 หยิบสินค้า (Scan SKU)
- ⚠️ บันทึก Shortage
- 🚚 สแกนส่งมอบให้ขนส่ง (Scan Handover/Tracking)
- 📋 ตรวจสอบ Progress

### บทบาท (Roles):

#### 3️⃣ **Warehouse Picker** (พนักงานหยิบของ)
**ภาระงาน:** หยิบสินค้าตาม Batch

**สิทธิ์เข้าถึง:**
```
✅ Scan Batch (รับงาน)
✅ Scan SKU (หยิบของ)
✅ บันทึก Shortage
✅ ดู Batch Detail (Batch ที่ตนเองรับ)
✅ Quick Assign
❌ สร้าง/ลบ Batch
❌ Export รายงาน
❌ Scan Handover/Tracking (ยังไม่ใช่งาน Dispatch)
❌ Dashboard (ไม่จำเป็น)
```

#### 4️⃣ **Warehouse Packer** (พนักงานแพ็คและส่งมอบ)
**ภาระงาน:** แพ็คและส่งมอบให้ขนส่ง

**สิทธิ์เข้าถึง:**
```
✅ ดู Batch List (เฉพาะ Batch ที่พร้อมส่ง)
✅ Scan Handover (สแกนส่งมอบ)
✅ Scan Tracking (บันทึก Tracking Number)
✅ พิมพ์ใบส่งมอบ
✅ ดู Batch Detail (Read Only)
❌ Scan Batch/SKU (ไม่ใช่หน้าที่หยิบ)
❌ สร้าง/ลบ Batch
❌ Export รายงาน
```

---

## 📊 Permission Matrix

### ตารางสิทธิ์การเข้าถึง

| เมนู/ฟีเจอร์ | Online Admin | Online Staff | Picker | Packer |
|-------------|:------------:|:------------:|:------:|:------:|
| **📊 Dashboard** | ✅ Full | ✅ View | ❌ | ❌ |
| **📥 Import (Orders/Products/Stock)** | ✅ | ❌ | ❌ | ❌ |
| **📦 Batch Create** | ✅ | ✅ | ❌ | ❌ |
| **📋 Batch List** | ✅ Full | ✅ View | ✅ View (Own) | ✅ View (Ready) |
| **🔍 Batch Detail** | ✅ Full | ✅ View | ✅ View (Own) | ✅ View |
| **🗑️ Batch Delete** | ✅ | ❌ | ❌ | ❌ |
| **📄 Picking List Print** | ✅ | ✅ | ✅ | ❌ |
| **🏷️ SKU QR Print** | ✅ | ✅ | ✅ | ❌ |
| **📦 Scan Batch (รับงาน)** | ✅ | ❌ | ✅ | ❌ |
| **🔍 Scan SKU (หยิบของ)** | ✅ | ❌ | ✅ | ❌ |
| **⚠️ Mark Shortage** | ✅ | ❌ | ✅ | ❌ |
| **📋 Shortage Queue** | ✅ Full | ✅ View | ✅ Own | ❌ |
| **🚚 Scan Handover** | ✅ | ❌ | ❌ | ✅ |
| **📝 Scan Tracking** | ✅ | ❌ | ❌ | ✅ |
| **🖨️ Handover Print** | ✅ | ❌ | ❌ | ✅ |
| **📊 Export Excel** | ✅ | ✅ (Limited) | ❌ | ❌ |
| **🔐 User Management** | ✅ | ❌ | ❌ | ❌ |
| **📜 Audit Log** | ✅ | ❌ | ❌ | ❌ |
| **✏️ Edit Stock/Product** | ✅ | ❌ | ❌ | ❌ |

**Legend:**
- ✅ Full = สิทธิ์เต็ม (Read + Write + Delete)
- ✅ View = ดูได้อย่างเดียว (Read Only)
- ✅ Own = เฉพาะของตนเอง
- ✅ Limited = จำกัดขอบเขต
- ❌ = ไม่มีสิทธิ์

---

## 🔄 Workflow แต่ละแผนก

### 📱 ทีมออนไลน์ - Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      ทีมออนไลน์ (Online Team)                     │
└─────────────────────────────────────────────────────────────────┘

1️⃣ Import ข้อมูล (Admin Only)
   │
   ├─> 📥 Import Orders (Excel)
   ├─> 📦 Import Products (Excel)
   └─> 📊 Import Stock (Excel)
   │
   ▼

2️⃣ ตรวจสอบ Dashboard
   │
   ├─> 🔍 ดู Orders ที่พร้อมรับ (READY_ACCEPT)
   ├─> ⚠️ ดู Orders ที่สินค้าน้อย (LOW_STOCK)
   └─> ❌ ดู Orders ที่ไม่มีสินค้า (SHORTAGE)
   │
   ▼

3️⃣ สร้าง Batch (Admin + Staff)
   │
   ├─> 📋 เลือก Platform (Shopee/TikTok/Lazada)
   ├─> 📅 เลือกวันที่
   ├─> ✅ เลือก Orders
   └─> 🎯 สร้าง Batch → Run Number (R1, R2, ...)
   │
   ▼

4️⃣ พิมพ์เอกสาร
   │
   ├─> 🖨️ Picking List (รายการหยิบของ)
   ├─> 🏷️ SKU QR Code (สติกเกอร์ SKU)
   └─> 📄 Batch QR Code (ใบงาน Batch)
   │
   ▼

5️⃣ ส่งต่อให้ทีมคลัง
   │
   └─> 📦 แจ้งทีม Picker ไปหยิบของตาม Batch
   │
   ▼

6️⃣ ติดตาม Progress
   │
   ├─> 📊 ดู Batch List (Progress %)
   ├─> 🔍 ดู Batch Detail (SKU Progress)
   └─> ⚠️ ดู Shortage Queue (รายการขาด)
   │
   ▼

7️⃣ จัดการ Shortage (Admin Only)
   │
   ├─> ⏳ รอสต็อกเข้า (waiting_stock)
   ├─> ❌ ยกเลิก (cancelled)
   ├─> 🔄 แทน SKU (replaced)
   └─> ✅ จัดการเรียบร้อย (resolved)
   │
   ▼

8️⃣ Export รายงาน
   │
   ├─> 📊 Export Dashboard (Excel)
   ├─> 📦 Export Batch Progress
   └─> ⚠️ Export Shortage Queue
```

---

### 🏭 ทีมคลัง - Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      ทีมคลัง (Warehouse Team)                    │
└─────────────────────────────────────────────────────────────────┘

🔹 ส่วนที่ 1: Picker (พนักงานหยิบของ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ รับงาน Batch
   │
   ├─> 📲 ไปหน้า /scan/batch
   ├─> 📷 สแกน QR Code บนใบงาน Batch
   │   └─> หรือ: เลือกจาก Quick Assign
   └─> ✅ รับงาน Batch สำเร็จ
   │
   ▼

2️⃣ หยิบสินค้า
   │
   ├─> 📲 ไปหน้า /scan/sku
   ├─> 🔍 เลือก Batch ที่รับไว้
   │   └─> หรือ: Quick Assign SKU
   ├─> 📷 สแกน SKU QR Code
   ├─> 🔢 ระบุจำนวนที่หยิบ
   │
   ├─> ✅ สินค้าพอ → บันทึกสำเร็จ
   │
   └─> ❌ สินค้าไม่พอ → บันทึก Shortage
       │
       ├─> 📝 ระบุจำนวนที่ขาด
       ├─> 📝 เลือกเหตุผล (สต็อกหมด/สินค้าเสียหาย)
       └─> ⚠️ บันทึกลง Shortage Queue
   │
   ▼

3️⃣ ตรวจสอบ Progress
   │
   ├─> 📊 ดู Batch Detail
   ├─> ✅ SKU ที่หยิบครบ (สีเขียว)
   ├─> ⏳ SKU ที่ยังหยิบไม่ครบ (สีเหลือง)
   └─> ❌ SKU ที่มี Shortage (สีแดง)
   │
   ▼

4️⃣ ทำงานจนครบ
   │
   └─> ✅ Progress 100% → ส่งต่อให้ Packer


🔹 ส่วนที่ 2: Packer (พนักงานแพ็คและส่งมอบ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5️⃣ ดู Batch ที่พร้อมส่ง
   │
   ├─> 📋 ไปหน้า /batch/list
   ├─> 🔍 กรอง: Progress 100%
   └─> 📦 เลือก Batch ที่จะส่งมอบ
   │
   ▼

6️⃣ แพ็คสินค้า
   │
   ├─> 📦 แพ็คสินค้าตาม Batch
   ├─> 🏷️ ติดสติกเกอร์/เลข Tracking
   └─> ✅ พร้อมส่งมอบ
   │
   ▼

7️⃣ สแกนส่งมอบให้ขนส่ง
   │
   ├─> 📲 ไปหน้า /scan/handover
   ├─> 📷 สแกน Batch QR Code
   ├─> 🔢 ระบุจำนวนกล่อง (ถ้ามี)
   └─> ✅ สร้าง Handover Code อัตโนมัติ
   │
   ▼

8️⃣ บันทึก Tracking Number (Optional)
   │
   ├─> 📲 ไปหน้า /scan/tracking
   ├─> 📷 สแกน Order QR Code
   ├─> 🔢 ระบุ Tracking Number
   └─> ✅ บันทึกสำเร็จ
   │
   ▼

9️⃣ พิมพ์ใบส่งมอบ
   │
   ├─> 🖨️ พิมพ์ใบส่งมอบ (Handover Slip)
   ├─> 📋 มี QR Code สำหรับสแกนรับ
   └─> 📦 แนบกับสินค้า
   │
   ▼

🎉 เสร็จสิ้น
   │
   └─> ✅ Batch Status = DISPATCHED
```

---

## 💡 คำแนะนำการ Implementation

### 1️⃣ Database: เพิ่ม Role/Department Field

**แก้ไข `models.py`:**

```python
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    # ✨ เพิ่ม Fields เหล่านี้
    department = db.Column(db.String(20), default='online')  # 'online' หรือ 'warehouse'
    role = db.Column(db.String(20), default='staff')         # 'admin', 'staff', 'picker', 'packer'

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ))
```

**Migration SQL:**

```sql
-- เพิ่ม department และ role columns
ALTER TABLE users ADD COLUMN department VARCHAR(20) DEFAULT 'online';
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'staff';

-- อัปเดต user ที่มีอยู่แล้วให้เป็น admin
UPDATE users SET role = 'admin', department = 'online' WHERE username = 'admin';
```

---

### 2️⃣ Permission Decorator

**สร้าง `permissions.py`:**

```python
from functools import wraps
from flask import flash, redirect, url_for

def current_user():
    """Get current logged in user"""
    from models import User
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

def require_department(*allowed_departments):
    """Decorator สำหรับตรวจสอบแผนก"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = current_user()
            if not user:
                flash("กรุณาเข้าสู่ระบบ", "danger")
                return redirect(url_for('login'))

            if user.department not in allowed_departments:
                flash(f"คุณไม่มีสิทธิ์เข้าถึงหน้านี้ (ต้องการแผนก: {', '.join(allowed_departments)})", "danger")
                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(*allowed_roles):
    """Decorator สำหรับตรวจสอบบทบาท"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = current_user()
            if not user:
                flash("กรุณาเข้าสู่ระบบ", "danger")
                return redirect(url_for('login'))

            if user.role not in allowed_roles:
                flash(f"คุณไม่มีสิทธิ์ทำงานนี้ (ต้องการบทบาท: {', '.join(allowed_roles)})", "danger")
                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

---

### 3️⃣ ตัวอย่างการใช้งาน Permission

**ใน `app.py`:**

```python
from permissions import require_department, require_role

# ✅ เฉพาะทีมออนไลน์
@app.route("/import/orders")
@login_required
@require_department('online')
@require_role('admin')
def import_orders_page():
    return render_template("import_orders.html")

# ✅ เฉพาะ Picker
@app.route("/scan/batch")
@login_required
@require_department('warehouse')
@require_role('picker', 'admin')
def scan_batch():
    return render_template("scan_batch.html")

# ✅ เฉพาะ Packer
@app.route("/scan/handover")
@login_required
@require_department('warehouse')
@require_role('packer', 'admin')
def scan_handover():
    return render_template("scan_handover.html")

# ✅ ทั้งสองทีม แต่ดูได้เฉพาะของตัวเอง
@app.route("/batch/list")
@login_required
def batch_list():
    user = current_user()

    if user.department == 'warehouse' and user.role == 'picker':
        # Picker เห็นเฉพาะ Batch ที่ตนเองรับ
        batches = Batch.query.filter_by(accepted_by_username=user.username).all()
    elif user.department == 'warehouse' and user.role == 'packer':
        # Packer เห็นเฉพาะ Batch ที่พร้อมส่ง (Progress 100%)
        batches = [b for b in Batch.query.all() if calculate_batch_progress(b.batch_id)['progress_percent'] >= 100]
    else:
        # Admin/Staff เห็นทั้งหมด
        batches = Batch.query.all()

    return render_template("batch_list.html", batches=batches)
```

---

### 4️⃣ UI: แสดง/ซ่อนเมนูตาม Role

**ใน `templates/base.html`:**

```html
<!-- Navigation Menu -->
<nav>
  <!-- ✅ ทุกคนเห็น -->
  <a href="{{ url_for('dashboard') }}">Dashboard</a>

  <!-- ✅ เฉพาะทีมออนไลน์ -->
  {% if current_user.department == 'online' %}
    {% if current_user.role == 'admin' %}
      <a href="{{ url_for('import_orders_page') }}">Import Orders</a>
      <a href="{{ url_for('import_products_page') }}">Import Products</a>
    {% endif %}

    <a href="{{ url_for('batch_create') }}">สร้าง Batch</a>
    <a href="{{ url_for('batch_list') }}">รายการ Batch</a>
    <a href="{{ url_for('shortage_queue') }}">Shortage Queue</a>
  {% endif %}

  <!-- ✅ เฉพาะทีมคลัง - Picker -->
  {% if current_user.department == 'warehouse' and current_user.role == 'picker' %}
    <a href="{{ url_for('scan_batch') }}">📦 Scan Batch</a>
    <a href="{{ url_for('scan_sku') }}">🔍 Scan SKU</a>
    <a href="{{ url_for('batch_list') }}">📋 Batch ของฉัน</a>
  {% endif %}

  <!-- ✅ เฉพาะทีมคลัง - Packer -->
  {% if current_user.department == 'warehouse' and current_user.role == 'packer' %}
    <a href="{{ url_for('batch_list') }}">📦 Batch พร้อมส่ง</a>
    <a href="{{ url_for('scan_handover') }}">🚚 Scan Handover</a>
    <a href="{{ url_for('scan_tracking') }}">📝 Scan Tracking</a>
  {% endif %}

  <!-- ✅ Admin เห็นทุกอย่าง -->
  {% if current_user.role == 'admin' %}
    <a href="{{ url_for('user_management') }}">👥 จัดการผู้ใช้</a>
    <a href="{{ url_for('audit_log') }}">📜 Audit Log</a>
  {% endif %}
</nav>
```

---

### 5️⃣ สร้างผู้ใช้ตัวอย่าง

**Script สำหรับสร้าง Users:**

```python
from models import User, db
from werkzeug.security import generate_password_hash

users = [
    # Online Team
    User(username='online_admin', password=generate_password_hash('password'), department='online', role='admin'),
    User(username='online_staff1', password=generate_password_hash('password'), department='online', role='staff'),
    User(username='online_staff2', password=generate_password_hash('password'), department='online', role='staff'),
    User(username='Online_staff3', password=generate_password_hash('password'), department='online', role='staff'),

    # Warehouse Team
    User(username='picker1', password=generate_password_hash('password'), department='warehouse', role='picker'),
    User(username='picker2', password=generate_password_hash('password'), department='warehouse', role='picker'),
    User(username='picker3', password=generate_password_hash('password'), department='warehouse', role='picker'),
    User(username='picker4', password=generate_password_hash('password'), department='warehouse', role='picker'),
    User(username='packer1', password=generate_password_hash('password'), department='warehouse', role='packer'),
    User(username='packer2', password=generate_password_hash('password'), department='warehouse', role='packer'),
    User(username='packer3', password=generate_password_hash('password'), department='warehouse', role='packer'),
    User(username='packer4', password=generate_password_hash('password'), department='warehouse', role='packer')
]

for user in users:
    db.session.add(user)

db.session.commit()
print("✅ สร้างผู้ใช้สำเร็จ!")
```

---

## 🎯 สรุป Best Practices

### ✅ DO's (ควรทำ):

1. **แบ่งแผนกชัดเจน** - Online vs Warehouse
2. **กำหนด Role ตามหน้าที่จริง** - Admin, Staff, Picker, Packer
3. **ใช้ Permission Decorator** - ป้องกันการเข้าถึงที่ไม่ได้รับอนุญาต
4. **ซ่อนเมนูที่ไม่เกี่ยวข้อง** - UI แสดงเฉพาะสิ่งที่ใช้ได้
5. **Audit Log ทุก Action** - บันทึกว่าใครทำอะไร เมื่อไร
6. **ทดสอบ Permission** - ตรวจสอบว่าแต่ละ Role เข้าถึงได้ถูกต้อง

### ❌ DON'Ts (ไม่ควรทำ):

1. **ให้สิทธิ์มากเกินไป** - Picker ไม่ควรลบ Batch ได้
2. **Hard-code Username** - ใช้ Role แทนการเช็ค username == 'admin'
3. **เปิดเมนูทุกอย่าง** - ทำให้งง ควรแสดงเฉพาะที่เกี่ยวข้อง
4. **ลืม Validate Backend** - Frontend ซ่อนเมนูได้ แต่ต้อง validate ที่ Backend ด้วย

---

## 📞 ติดต่อ & สนับสนุน

หากมีข้อสงสัยเกี่ยวกับการแบ่งแผนกหรือ Permission:
- 📧 Email: support@vnix.com
- 💬 Line: @vnixsupport
- 📚 Docs: https://github.com/tetipong2542/vnix-wms/docs

---

**อัปเดตล่าสุด:** 2025-11-17
**เวอร์ชัน:** 2.0
**ผู้เขียน:** VNIX Development Team

---

🎉 **หมายเหตุ:** เอกสารนี้เป็นแนวทางเบื้องต้น คุณสามารถปรับแต่งเพิ่มเติมตามความต้องการของทีมได้ครับ
