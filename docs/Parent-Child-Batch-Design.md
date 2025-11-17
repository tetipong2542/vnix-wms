# 🏗️ Parent-Child Batch System Design
## ระบบ Batch แม่-ลูก สำหรับจัดการ Shortage แบบไม่ Block งาน

---

## 🎯 ความต้องการจากผู้บริหาร

### ✅ **Requirements:**

1. **Shortage ไม่ Block งาน**
   - 1 SKU ขาดไม่ทำให้ทั้ง Batch ค้าง
   - สินค้าที่มีพร้อมส่งได้เลย

2. **Partial Dispatch**
   - ส่งของที่พร้อมได้ทันที
   - ไม่ต้องรอของที่ขาด

3. **Sub-Batch System**
   - แยกสินค้าที่ขาดเป็น Child Batch (R1, R2, R3...)
   - อยู่ภายใต้ Parent Batch เดิม
   - จำกัดสูงสุด 5 Sub-Batch ต่อ 1 Parent

4. **Handover Code แยกกัน**
   - แต่ละ Sub-Batch มี Handover Code ของตัวเอง
   - ส่งได้อิสระ ไม่ต้องรอกัน

---

## 🏗️ Architecture Design

### **Batch Naming Convention:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Batch ID Structure                            │
└─────────────────────────────────────────────────────────────────┘

Parent Batch (Original):
SH-2025-11-17-R1
│   │    │    │  └── Run Number (รอบการสร้าง Batch ในวันนั้น)
│   │    │    └───── วันที่
│   │    └────────── เดือน-ปี
│   └─────────────── แพลตฟอร์ม
└─────────────────── Batch ID

Child Batch (Sub-Batch):
SH-2025-11-17-R1.1  ← Child ลำดับที่ 1
SH-2025-11-17-R1.2  ← Child ลำดับที่ 2
SH-2025-11-17-R1.3  ← Child ลำดับที่ 3
                │
                └── Sub-Batch Number (1-5)

ตัวอย่าง Workflow:
SH-2025-11-17-R1      → Batch แม่ (เดิม)
SH-2025-11-17-R1.1    → Shortage Round 1
SH-2025-11-17-R1.2    → Shortage Round 2
```

---

## 📊 Database Schema Changes

### 1️⃣ **แก้ไข Batch Model**

```python
# models.py

class Batch(db.Model):
    __tablename__ = "batches"

    # Existing fields...
    batch_id = db.Column(db.String(64), primary_key=True)
    platform = db.Column(db.String(20), nullable=False)
    batch_date = db.Column(db.Date, nullable=False)
    run_no = db.Column(db.Integer, default=1)

    # ✨ NEW: Parent-Child Relationship
    parent_batch_id = db.Column(db.String(64), db.ForeignKey("batches.batch_id"), nullable=True)
    sub_batch_number = db.Column(db.Integer, default=0)  # 0 = Parent, 1-5 = Child

    # ✨ NEW: Batch Type
    batch_type = db.Column(db.String(20), default='original')
    # 'original' = Batch แม่
    # 'shortage' = Batch ลูก (แยกจาก Shortage)

    # ✨ NEW: Shortage Info (สำหรับ Child Batch)
    shortage_reason = db.Column(db.Text)  # เหตุผลที่แยก Batch

    # Relationships
    children = db.relationship('Batch', backref=db.backref('parent', remote_side=[batch_id]))

    # Existing fields...
    total_orders = db.Column(db.Integer, default=0)
    handover_code = db.Column(db.String(20), unique=True)
    handover_confirmed = db.Column(db.Boolean, default=False)
    # ...
```

### 2️⃣ **Migration SQL**

```sql
-- migrations/add_parent_child_batch.sql

-- เพิ่ม columns ใหม่
ALTER TABLE batches ADD COLUMN parent_batch_id VARCHAR(64);
ALTER TABLE batches ADD COLUMN sub_batch_number INTEGER DEFAULT 0;
ALTER TABLE batches ADD COLUMN batch_type VARCHAR(20) DEFAULT 'original';
ALTER TABLE batches ADD COLUMN shortage_reason TEXT;

-- เพิ่ม Foreign Key
ALTER TABLE batches ADD CONSTRAINT fk_parent_batch
    FOREIGN KEY (parent_batch_id) REFERENCES batches(batch_id);

-- เพิ่ม Index เพื่อความเร็ว
CREATE INDEX idx_parent_batch ON batches(parent_batch_id);
CREATE INDEX idx_batch_type ON batches(batch_type);

-- อัปเดต Batch ที่มีอยู่ให้เป็น 'original'
UPDATE batches SET batch_type = 'original', sub_batch_number = 0 WHERE batch_type IS NULL;
```

---

## 🔄 Workflow Design

### **สถานการณ์ตัวอย่าง:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      Scenario: Shortage นาน                      │
└─────────────────────────────────────────────────────────────────┘

Day 1: สร้าง Batch SH-2025-11-17-R1
├─ 10 Orders
├─ 5 SKU
└─ 50 ชิ้น

Day 1: Picker หยิบของ
├─ SKU A: 10/10 ✅
├─ SKU B: 15/15 ✅
├─ SKU C: 0/5 ❌ (Shortage - สต็อกหมด)
├─ SKU D: 12/12 ✅
└─ SKU E: 8/8 ✅

Progress = 45/50 = 90%

❓ ตอนนี้ทำยังไง?
```

---

### **🎯 Solution: Auto Split to Child Batch**

```
┌─────────────────────────────────────────────────────────────────┐
│              Step 1: ระบบตรวจจับ Shortage                        │
└─────────────────────────────────────────────────────────────────┘

ระบบตรวจสอบ:
├─ Progress = 90% (< 100%)
├─ มี Shortage: SKU C (5 ชิ้น)
└─> ✅ ต้องแยก Batch!


┌─────────────────────────────────────────────────────────────────┐
│              Step 2: แยก Orders เป็น 2 กลุ่ม                     │
└─────────────────────────────────────────────────────────────────┘

Group A: Orders ที่ครบแล้ว (9 Orders)
├─ ไม่มี SKU C
└─ หยิบครบ 100% แล้ว

Group B: Orders ที่มี Shortage (1 Order)
├─ มี SKU C
└─ ยังหยิบไม่ครบ (Shortage 5 ชิ้น)


┌─────────────────────────────────────────────────────────────────┐
│              Step 3: สร้าง Child Batch                           │
└─────────────────────────────────────────────────────────────────┘

1. Batch แม่ (SH-2025-11-17-R1):
   ├─ เก็บ 9 Orders (ที่ครบ)
   ├─ Progress = 100% ✅
   ├─ parent_batch_id = NULL
   ├─ sub_batch_number = 0
   └─> พร้อมส่ง!

2. Batch ลูก (SH-2025-11-17-R1.1):
   ├─ ย้าย 1 Order (ที่มี SKU C) มาที่นี่
   ├─ Progress = 0% (รอสต็อก)
   ├─ parent_batch_id = "SH-2025-11-17-R1"
   ├─ sub_batch_number = 1
   ├─ batch_type = "shortage"
   ├─ shortage_reason = "SKU C: สต็อกหมด (5 ชิ้น)"
   └─> รอสต็อกเข้า


┌─────────────────────────────────────────────────────────────────┐
│              Step 4: Packer ทำงาน                                │
└─────────────────────────────────────────────────────────────────┘

Day 1: Packer
├─> เห็น Batch SH-2025-11-17-R1 (Progress 100%)
├─> สร้าง Handover Code: BH-20251117-001 ✅
├─> แพ็คและส่งมอบ 9 Orders
└─> ✅ ลูกค้า 9 Orders ได้รับของทันเวลา!


┌─────────────────────────────────────────────────────────────────┐
│              Step 5: จัดการ Child Batch ทีหลัง                  │
└─────────────────────────────────────────────────────────────────┘

Day 3: สต็อก SKU C เข้า
├─> Picker หยิบ Batch SH-2025-11-17-R1.1
├─> SKU C: 5/5 ✅
├─> Progress = 100%
└─> Packer ส่งมอบ (Handover Code: BH-20251120-005)

✅ ลูกค้า 1 Order ที่เหลือได้รับสินค้า
```

---

## 🛠️ API Implementation

### **1. API: Split Batch (แยก Batch อัตโนมัติ)**

```python
# app.py

@app.route("/api/batch/<batch_id>/auto-split", methods=["POST"])
@login_required
def api_auto_split_batch(batch_id):
    """
    แยก Batch อัตโนมัติเมื่อมี Shortage
    - Orders ที่ครบแล้วอยู่ใน Parent Batch
    - Orders ที่มี Shortage ย้ายไป Child Batch
    """
    batch = db.session.get(Batch, batch_id)

    if not batch:
        return jsonify({"success": False, "error": "ไม่พบ Batch"}), 404

    # ตรวจสอบว่าเป็น Parent Batch (ไม่ใช่ Child)
    if batch.parent_batch_id is not None:
        return jsonify({
            "success": False,
            "error": "ไม่สามารถแยก Child Batch ได้ กรุณาแยกจาก Parent Batch"
        }), 400

    # ตรวจสอบจำนวน Child Batch ที่มีอยู่แล้ว
    existing_children = Batch.query.filter_by(parent_batch_id=batch_id).count()
    if existing_children >= 5:
        return jsonify({
            "success": False,
            "error": "ถึงขอบเขตแล้ว: Batch นี้มี Child Batch ครบ 5 Batch แล้ว"
        }), 400

    # ดึง Orders ทั้งหมดใน Batch
    orders = OrderLine.query.filter_by(batch_id=batch_id).all()

    if not orders:
        return jsonify({"success": False, "error": "Batch ไม่มี Orders"}), 404

    # แยก Orders เป็น 2 กลุ่ม
    complete_orders = []  # Orders ที่หยิบครบ (ไม่มี Shortage)
    shortage_orders = []  # Orders ที่มี Shortage

    for order in orders:
        if order.shortage_qty > 0:
            shortage_orders.append(order)
        else:
            complete_orders.append(order)

    # ถ้าไม่มี Shortage → ไม่ต้องแยก
    if not shortage_orders:
        return jsonify({
            "success": False,
            "error": "Batch นี้ไม่มี Shortage ไม่จำเป็นต้องแยก"
        }), 400

    # ถ้าทุก Order มี Shortage → ไม่ต้องแยก (รอสต็อกเข้าทั้งหมด)
    if not complete_orders:
        return jsonify({
            "success": False,
            "error": "Batch นี้ทุก Order มี Shortage กรุณารอสต็อกเข้าแทน"
        }), 400

    # สร้าง Child Batch
    next_sub_number = existing_children + 1
    child_batch_id = f"{batch_id}.{next_sub_number}"

    # รวบรวม Shortage Info
    shortage_info = []
    for order in shortage_orders:
        shortage_info.append(f"Order {order.order_id}: SKU {order.sku} ขาด {order.shortage_qty} ชิ้น")
    shortage_reason = "\n".join(shortage_info)

    # สร้าง Child Batch
    child_batch = Batch(
        batch_id=child_batch_id,
        platform=batch.platform,
        batch_date=batch.batch_date,
        run_no=batch.run_no,
        parent_batch_id=batch_id,
        sub_batch_number=next_sub_number,
        batch_type='shortage',
        shortage_reason=shortage_reason,
        total_orders=len(shortage_orders),
        created_by_user_id=current_user().id,
        created_by_username=current_user().username,
        created_at=now_thai()
    )

    db.session.add(child_batch)

    # ย้าย Orders ที่มี Shortage ไป Child Batch
    for order in shortage_orders:
        order.batch_id = child_batch_id

    # อัปเดต Parent Batch
    batch.total_orders = len(complete_orders)

    db.session.commit()

    # Log Audit
    log_audit(
        action="batch_split",
        details={
            "parent_batch": batch_id,
            "child_batch": child_batch_id,
            "shortage_orders": len(shortage_orders),
            "complete_orders": len(complete_orders),
            "reason": shortage_reason
        }
    )

    return jsonify({
        "success": True,
        "message": f"แยก Batch สำเร็จ",
        "parent_batch": {
            "batch_id": batch_id,
            "total_orders": len(complete_orders),
            "progress": 100  # Parent Batch มีแต่ Orders ที่ครบแล้ว
        },
        "child_batch": {
            "batch_id": child_batch_id,
            "sub_batch_number": next_sub_number,
            "total_orders": len(shortage_orders),
            "shortage_reason": shortage_reason
        }
    })
```

---

### **2. API: Get Batch Family (ดู Parent + Children)**

```python
@app.route("/api/batch/<batch_id>/family", methods=["GET"])
@login_required
def api_get_batch_family(batch_id):
    """
    ดึงข้อมูล Batch Family (Parent + All Children)
    """
    # หา Batch
    batch = db.session.get(Batch, batch_id)
    if not batch:
        return jsonify({"success": False, "error": "ไม่พบ Batch"}), 404

    # ถ้าเป็น Child Batch → ไปหา Parent
    if batch.parent_batch_id:
        parent_batch = db.session.get(Batch, batch.parent_batch_id)
    else:
        parent_batch = batch

    # ดึง Children ทั้งหมด
    children = Batch.query.filter_by(parent_batch_id=parent_batch.batch_id).order_by(Batch.sub_batch_number).all()

    # คำนวณ Progress แต่ละ Batch
    def get_batch_info(b):
        progress = calculate_batch_progress(b.batch_id)
        return {
            "batch_id": b.batch_id,
            "sub_batch_number": b.sub_batch_number,
            "batch_type": b.batch_type,
            "total_orders": b.total_orders,
            "progress_percent": progress["progress_percent"],
            "total_qty": progress["total_qty"],
            "completed_qty": progress["completed_qty"],
            "handover_code": b.handover_code,
            "handover_confirmed": b.handover_confirmed,
            "shortage_reason": b.shortage_reason,
            "created_at": to_thai_be(b.created_at)
        }

    result = {
        "parent": get_batch_info(parent_batch),
        "children": [get_batch_info(child) for child in children],
        "total_children": len(children),
        "can_split_more": len(children) < 5
    }

    return jsonify({"success": True, "family": result})
```

---

### **3. แก้ไข Generate Handover Code (ไม่ต้องรอ 100%)**

```python
@app.route("/api/batch/<batch_id>/generate-handover-code", methods=["POST"])
@login_required
def api_generate_handover_code(batch_id):
    batch = db.session.get(Batch, batch_id)
    if not batch:
        return jsonify({"success": False, "error": "ไม่พบ Batch"}), 404

    progress_data = calculate_batch_progress(batch_id)

    # ✅ NEW: อนุญาตให้ส่งถ้า Progress = 100% หรือ Batch ถูก Split แล้ว
    # (Parent Batch ที่ Split แล้วจะมีแต่ Orders ที่ครบ = 100% อยู่แล้ว)

    if progress_data["progress_percent"] < 100:
        return jsonify({
            "success": False,
            "error": f"Batch ยังไม่เสร็จ (Progress: {progress_data['progress_percent']:.1f}%)\n"
                    f"หยิบได้: {progress_data['completed_qty']}/{progress_data['total_qty']} ชิ้น\n\n"
                    f"💡 หากมี Shortage กรุณาใช้ฟีเจอร์ 'แยก Batch' เพื่อส่งของที่มีพร้อมก่อน"
        }), 400

    # ตรวจสอบว่ามี Handover Code แล้วหรือยัง
    if batch.handover_code:
        return jsonify({
            "success": False,
            "error": f"Batch นี้มีรหัสส่งมอบแล้ว: {batch.handover_code}"
        }), 400

    # สร้าง Handover Code (โค้ดเดิม...)
    # ...

    return jsonify({
        "success": True,
        "handover_code": handover_code,
        "batch_id": batch_id
    })
```

---

## 🎨 UI Changes

### **Batch Detail Page - แสดง Parent & Children**

```html
<!-- templates/batch_detail.html -->

{% if batch.parent_batch_id %}
  <!-- ถ้าเป็น Child Batch → แสดง Link ไป Parent -->
  <div class="alert alert-info">
    📦 Batch นี้เป็น Sub-Batch ของ
    <a href="{{ url_for('batch_detail', batch_id=batch.parent_batch_id) }}">
      {{ batch.parent_batch_id }}
    </a>
    <span class="badge bg-secondary">Round {{ batch.sub_batch_number }}</span>
  </div>
{% endif %}

{% if batch.batch_type == 'original' %}
  <!-- ถ้าเป็น Parent Batch → แสดง Children (ถ้ามี) -->
  {% set children = get_child_batches(batch.batch_id) %}

  {% if children %}
    <div class="card mt-3">
      <div class="card-header bg-warning">
        <h5>🔄 Sub-Batches (Shortage Rounds)</h5>
      </div>
      <div class="card-body">
        <div class="list-group">
          {% for child in children %}
            <a href="{{ url_for('batch_detail', batch_id=child.batch_id) }}"
               class="list-group-item list-group-item-action">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <h6 class="mb-1">{{ child.batch_id }}</h6>
                  <small class="text-muted">{{ child.shortage_reason }}</small>
                </div>
                <div>
                  <span class="badge bg-{{ 'success' if child.progress_percent == 100 else 'warning' }}">
                    {{ child.progress_percent }}%
                  </span>
                  {% if child.handover_code %}
                    <span class="badge bg-info">{{ child.handover_code }}</span>
                  {% endif %}
                </div>
              </div>
            </a>
          {% endfor %}
        </div>

        {% if children|length < 5 %}
          <div class="alert alert-light mt-3 mb-0">
            💡 สามารถแยก Sub-Batch ได้อีก {{ 5 - children|length }} Batch
          </div>
        {% else %}
          <div class="alert alert-warning mt-3 mb-0">
            ⚠️ ถึงขอบเขตแล้ว: แยก Sub-Batch ได้สูงสุด 5 Batch
          </div>
        {% endif %}
      </div>
    </div>
  {% endif %}

  <!-- ปุ่มแยก Batch -->
  {% if batch.progress_percent < 100 %}
    <button class="btn btn-warning mt-3" onclick="splitBatch('{{ batch.batch_id }}')">
      <i data-lucide="split"></i> แยก Batch (ส่งของที่มีก่อน)
    </button>
  {% endif %}
{% endif %}

<script>
function splitBatch(batchId) {
  if (!confirm('คุณต้องการแยก Batch นี้ใช่หรือไม่?\n\n' +
               'Orders ที่หยิบครบจะอยู่ใน Batch เดิม\n' +
               'Orders ที่มี Shortage จะถูกย้ายไป Sub-Batch ใหม่')) {
    return;
  }

  fetch(`/api/batch/${batchId}/auto-split`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'}
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('✅ แยก Batch สำเร็จ!\n\n' +
            `Parent Batch: ${data.parent_batch.batch_id} (${data.parent_batch.total_orders} Orders)\n` +
            `Child Batch: ${data.child_batch.batch_id} (${data.child_batch.total_orders} Orders)`);
      location.reload();
    } else {
      alert('❌ เกิดข้อผิดพลาด: ' + data.error);
    }
  })
  .catch(err => {
    alert('❌ เกิดข้อผิดพลาด: ' + err.message);
  });
}
</script>
```

---

## 📊 Batch List - แสดง Parent & Children

```html
<!-- templates/batch_list.html -->

{% for batch in batches %}
  <tr>
    <td>
      {% if batch.parent_batch_id %}
        <!-- Child Batch → เยื้อง + แสดง Icon -->
        <span style="margin-left: 20px;">
          └─ <i data-lucide="corner-down-right"></i>
        </span>
      {% endif %}

      <a href="{{ url_for('batch_detail', batch_id=batch.batch_id) }}">
        {{ batch.batch_id }}
      </a>

      {% if batch.sub_batch_number > 0 %}
        <span class="badge bg-secondary">R{{ batch.sub_batch_number }}</span>
      {% endif %}
    </td>
    <td>{{ batch.platform }}</td>
    <td>{{ batch.total_orders }}</td>
    <td>
      <!-- Progress Badge -->
      <span class="badge bg-{{ 'success' if batch.progress_percent == 100 else 'warning' }}">
        {{ batch.progress_percent }}%
      </span>
    </td>
    <td>
      {% if batch.handover_code %}
        <span class="badge bg-info">{{ batch.handover_code }}</span>
      {% else %}
        <span class="text-muted">-</span>
      {% endif %}
    </td>
  </tr>
{% endfor %}
```

---

## 🎯 Workflow ฉบับสมบูรณ์

```
┌─────────────────────────────────────────────────────────────────┐
│          Complete Workflow: Parent-Child Batch System            │
└─────────────────────────────────────────────────────────────────┘

Day 1: สร้าง Batch
├─> SH-2025-11-17-R1 (Parent)
├─> 10 Orders, 50 ชิ้น
└─> batch_type = 'original'

Day 1: Picker หยิบของ
├─> Progress = 90% (45/50)
└─> SKU C: Shortage 5 ชิ้น

Day 1: ทีมออนไลน์ดู Progress
├─> เห็นว่า Progress = 90%
├─> คลิก "แยก Batch" ในหน้า Batch Detail
└─> ✅ ระบบแยก Batch อัตโนมัติ:
    ├─ Parent: SH-2025-11-17-R1 (9 Orders, Progress 100%)
    └─ Child:  SH-2025-11-17-R1.1 (1 Order, Progress 0%)

Day 1: Packer ทำงาน
├─> ดู Batch List
├─> เห็น SH-2025-11-17-R1 (Progress 100%)
├─> สร้าง Handover Code: BH-20251117-001
├─> แพ็คและส่งมอบ 9 Orders ✅
└─> ลูกค้า 9 Orders ได้รับของทันเวลา!

Day 3: สต็อก SKU C เข้า
├─> Picker หยิบ SH-2025-11-17-R1.1
├─> SKU C: 5/5 ✅
└─> Progress = 100%

Day 3: Packer ส่งมอบ Child Batch
├─> สร้าง Handover Code: BH-20251120-005
├─> แพ็คและส่งมอบ 1 Order ✅
└─> ลูกค้า 1 Order ที่เหลือได้รับสินค้า!

✅ ผลลัพธ์:
├─ ลูกค้า 90% ได้รับของทันเวลา (Day 1)
├─ ลูกค้า 10% ได้รับของภายหลัง (Day 3)
└─ ไม่มี Batch ค้าง!
```

---

## 📋 Summary

### ✅ **ตอบโจทย์ทุกข้อ:**

| ความต้องการ | Solution | Status |
|-------------|----------|--------|
| **Shortage ไม่ Block งาน** | แยกเป็น Child Batch | ✅ |
| **Partial Dispatch** | Parent Batch ส่งได้เลย | ✅ |
| **Sub-Batch Max 5** | จำกัดที่ sub_batch_number 1-5 | ✅ |
| **Handover Code แยกกัน** | แต่ละ Batch มี Code ของตัวเอง | ✅ |

### 🛠️ **Implementation Checklist:**

- [ ] 1. แก้ไข `models.py` - เพิ่ม Parent-Child fields
- [ ] 2. Run Migration SQL
- [ ] 3. เพิ่ม API `/api/batch/<id>/auto-split`
- [ ] 4. เพิ่ม API `/api/batch/<id>/family`
- [ ] 5. อัปเดต `batch_detail.html` - แสดง Children
- [ ] 6. อัปเดต `batch_list.html` - แสดง Parent-Child
- [ ] 7. เพิ่มปุ่ม "แยก Batch"
- [ ] 8. ทดสอบ Workflow
- [ ] 9. อบรมทีมงาน

---

**อัปเดตล่าสุด:** 2025-11-17
**เวอร์ชัน:** 1.0
**ผู้เขียน:** VNIX Development Team

---

พร้อม implement ไหมครับ? 🚀
