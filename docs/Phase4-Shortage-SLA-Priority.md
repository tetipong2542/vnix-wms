# Phase 4: Shortage Management + SLA Priority

## 🎯 Objective
อัปเดต Shortage Queue UI ให้แสดง SLA และเรียงลำดับตาม SLA priority (เร็วสุดก่อน) เพื่อให้ทีมจัดการ shortage ที่เร่งด่วนก่อน

---

## 📋 Changes Summary

### 1. **API Enhancement** (`app.py:5019-5135`)

#### Added SLA Sorting:
```python
# ✅ Phase 4: SLA-based sorting
def get_sla_for_shortage(shortage):
    order_line = shortage.order_line
    if order_line and order_line.sla_date:
        return (False, order_line.sla_date, shortage.created_at)
    else:
        # No SLA = last
        return (True, datetime.max.date(), shortage.created_at)

shortages = sorted(shortages, key=get_sla_for_shortage)
```

**Sorting Logic**:
- Orders with SLA → sorted by `sla_date` (earliest first)
- Orders without SLA → moved to the end
- Ties broken by `created_at`

---

#### Added SLA Fields to Response:
```python
# ✅ Phase 4: Add SLA information
sla_date = str(order_line.sla_date) if order_line.sla_date else None
platform = order_line.platform

# Calculate SLA status
if order_line.sla_date:
    today = date.today()
    if order_line.sla_date < today:
        sla_status = "overdue"
        sla_text = f"เลยกำหนด {days_overdue} วัน"
    elif order_line.sla_date == today:
        sla_status = "today"
        sla_text = "วันนี้"
    elif order_line.sla_date == today + timedelta(days=1):
        sla_status = "tomorrow"
        sla_text = "พรุ่งนี้"
    else:
        sla_status = "upcoming"
        sla_text = f"อีก {days_left} วัน"
```

**New Response Fields**:
```json
{
  "id": 123,
  "order_id": "ABC123",
  "sku": "SKU-001",
  "platform": "Shopee",
  "sla_date": "2025-01-20",
  "sla_status": "today",
  "sla_text": "วันนี้",
  ...
}
```

---

### 2. **UI Updates** (`templates/shortage_queue.html`)

#### Added Columns:
- **Platform**: แสดง platform badge
- **SLA**: แสดง SLA badge พร้อม emoji และสี

```html
<th>Platform</th>
<th>SLA</th>
```

#### Updated Table Rows:
```javascript
<td>${item.platform ? `<span class="badge bg-secondary">${item.platform}</span>` : '-'}</td>
<td>${getSLABadge(item.sla_status, item.sla_text, item.sla_date)}</td>
```

---

### 3. **New JavaScript Function** (`templates/shortage_queue.html:402-415`)

```javascript
// ✅ Phase 4: Get SLA Badge with appropriate styling
function getSLABadge(sla_status, sla_text, sla_date) {
  if (!sla_status || !sla_text) {
    return '<span class="text-muted">-</span>';
  }

  const badges = {
    'overdue': `<span class="badge bg-danger" title="SLA: ${sla_date}">🚨 ${sla_text}</span>`,
    'today': `<span class="badge bg-warning text-dark" title="SLA: ${sla_date}">⚠️ ${sla_text}</span>`,
    'tomorrow': `<span class="badge bg-info" title="SLA: ${sla_date}">📅 ${sla_text}</span>`,
    'upcoming': `<span class="badge bg-secondary" title="SLA: ${sla_date}">${sla_text}</span>`
  };

  return badges[sla_status] || `<span class="text-muted">${sla_text}</span>`;
}
```

**Badge Colors**:
- 🚨 **Red (danger)**: เลยกำหนดแล้ว (overdue)
- ⚠️ **Yellow (warning)**: วันนี้ (today)
- 📅 **Blue (info)**: พรุ่งนี้ (tomorrow)
- **Gray (secondary)**: อีกหลายวัน (upcoming)

---

## 📊 Before vs After

### Before Phase 4:
```
Shortage Queue Table:
| # | Order ID | SKU | Batch | ต้องการ | หยิบได้ | ขาด | ... |
|---|----------|-----|-------|---------|---------|-----|-----|
| 1 | 789 | SKU-C | B-003 | 5 | 3 | 2 | ... |  ← created last
| 2 | 456 | SKU-B | B-002 | 3 | 0 | 3 | ... |  ← created 2nd
| 3 | 123 | SKU-A | B-001 | 2 | 0 | 2 | ... |  ← created 1st

Sorting: By created_at DESC (newest first)
Problem: ไม่สะท้อนความเร่งด่วนจริง
```

### After Phase 4:
```
Shortage Queue Table:
| # | Order ID | SKU | Batch | Platform | SLA | ต้องการ | หยิบได้ | ขาด | ... |
|---|----------|-----|-------|----------|-----|---------|---------|-----|-----|
| 1 | 123 | SKU-A | B-001 | Shopee | 🚨 เลยกำหนด 2 วัน | 2 | 0 | 2 | ... |  ← SLA: 2025-01-18
| 2 | 456 | SKU-B | B-002 | Lazada | ⚠️ วันนี้ | 3 | 0 | 3 | ... |  ← SLA: 2025-01-20
| 3 | 789 | SKU-C | B-003 | TikTok | 📅 พรุ่งนี้ | 5 | 3 | 2 | ... |  ← SLA: 2025-01-21

Sorting: By SLA Date ASC (earliest/most urgent first)
Benefit: ทีมเห็นสินค้าที่เร่งด่วนก่อน
```

---

## 🎨 Visual Examples

### SLA Badge Examples:

**Overdue (เลยกำหนดแล้ว)**:
```html
<span class="badge bg-danger">🚨 เลยกำหนด 3 วัน</span>
```
→ สีแดง, emoji 🚨, แสดงจำนวนวันที่เลยมา

**Today (วันนี้)**:
```html
<span class="badge bg-warning text-dark">⚠️ วันนี้</span>
```
→ สีเหลือง, emoji ⚠️

**Tomorrow (พรุ่งนี้)**:
```html
<span class="badge bg-info">📅 พรุ่งนี้</span>
```
→ สีฟ้า, emoji 📅

**Upcoming (อีกหลายวัน)**:
```html
<span class="badge bg-secondary">อีก 5 วัน</span>
```
→ สีเทา, แสดงจำนวนวันที่เหลือ

**No SLA**:
```html
<span class="text-muted">-</span>
```
→ แสดง "-" เมื่อไม่มี SLA

---

## 🧪 Test Cases

### Test Case 1: SLA Sorting Verification

**Setup**:
```
Create 3 shortages:
- Shortage A: SLA = 2025-01-18 (เลยกำหนด 2 วัน)
- Shortage B: SLA = 2025-01-20 (วันนี้)
- Shortage C: SLA = 2025-01-22 (อีก 2 วัน)
```

**Steps**:
1. ไปที่ `/shortage-queue`
2. ตรวจสอบลำดับในตาราง

**Expected Result**:
```
Row 1: Shortage A (🚨 เลยกำหนด 2 วัน) ← SLA เร็วสุด
Row 2: Shortage B (⚠️ วันนี้)
Row 3: Shortage C (อีก 2 วัน) ← SLA ช้าสุด
```

---

### Test Case 2: SLA Badge Colors

**Setup**:
```
Create shortages with different SLA statuses:
- Order 1: SLA = Yesterday (overdue)
- Order 2: SLA = Today
- Order 3: SLA = Tomorrow
- Order 4: SLA = Next week
```

**Steps**:
1. ไปที่ `/shortage-queue`
2. ตรวจสอบ badge colors

**Expected Result**:
```
Order 1: 🚨 เลยกำหนด 1 วัน (Red badge)
Order 2: ⚠️ วันนี้ (Yellow badge)
Order 3: 📅 พรุ่งนี้ (Blue badge)
Order 4: อีก 7 วัน (Gray badge)
```

---

### Test Case 3: Orders Without SLA

**Setup**:
```
Create shortage for order without order_time (no SLA):
- Order X: order_time = NULL, sla_date = NULL
```

**Steps**:
1. ไปที่ `/shortage-queue`
2. ตรวจสอบตำแหน่งและการแสดงผล

**Expected Result**:
```
- Order X อยู่ท้ายสุดของตาราง (sorted last)
- SLA column แสดง: "-" (text-muted)
```

---

### Test Case 4: Filter + Sort Combination

**Setup**:
```
Create 5 shortages with different statuses and SLAs:
- S1: status=pending, SLA=Today
- S2: status=pending, SLA=Tomorrow
- S3: status=waiting_stock, SLA=Yesterday (overdue)
- S4: status=resolved, SLA=Today
- S5: status=pending, SLA=Next week
```

**Steps**:
1. Filter: status = "pending"
2. ตรวจสอบลำดับ

**Expected Result**:
```
Only S1, S2, S5 shown (pending only)
Order: S1 (Today) → S2 (Tomorrow) → S5 (Next week)
```

---

## 🔍 Key Implementation Details

### 1. **Why Python Sorting Instead of SQL?**

```python
# SLA is in OrderLine table, not ShortageQueue
# → Need to join or sort in Python

# Option A: SQL JOIN (complex)
query = ShortageQueue.query.join(OrderLine).order_by(OrderLine.sla_date)

# Option B: Python sort (simple, flexible) ✅
shortages = query.all()
shortages = sorted(shortages, key=get_sla_for_shortage)
```

**Chose Python** because:
- Simpler code
- More flexible (can handle NULL SLA)
- Small dataset (shortage queue typically < 100 items)

---

### 2. **SLA Status Calculation**

```python
from datetime import date, timedelta

today = date.today()

if sla_date < today:
    status = "overdue"
elif sla_date == today:
    status = "today"
elif sla_date == today + timedelta(days=1):
    status = "tomorrow"
else:
    status = "upcoming"
```

**Edge Cases Handled**:
- `sla_date = None` → status = None, badge = "-"
- `order_line = None` → No SLA data
- Same SLA → sorted by `created_at`

---

### 3. **Colspan Updates**

```javascript
// Before: 12 columns
tbody.innerHTML = `<td colspan="12">...</td>`;

// After: 14 columns (added Platform + SLA)
tbody.innerHTML = `<td colspan="14">...</td>`;
```

**All Locations Updated**:
- Loading spinner
- No data message
- Error message
- Batch header row

---

## 📝 Integration with Previous Phases

### Phase 1 ✅
- Uses `sla_date` field from OrderLine table

### Phase 2 ✅
- Shortage items sorted by SLA match batch creation priority

### Phase 3 ✅
- When stock reallocated, shortage queue shows updated SLA

### Phase 4 ✅ (Current)
- UI shows SLA visually
- Team can prioritize by SLA

---

## 🚀 Benefits

### 1. **Visual Priority**
- Red badge = ต้องจัดการด่วน
- Yellow badge = ต้องจัดการวันนี้
- Blue badge = เตรียมการล่วงหน้า

### 2. **Better Workflow**
- ทีมเห็น shortage ที่เร่งด่วนก่อน
- ไม่พลาดออเดอร์ที่เลย SLA

### 3. **Consistent Experience**
- SLA priority เหมือนกันทุกหน้า:
  - Batch Creation (Phase 2)
  - Stock Reallocation (Phase 3)
  - Shortage Queue (Phase 4)

---

## ✅ Phase 4 Completion Checklist

- [x] Add SLA sorting to API (`api_shortage_queue`)
- [x] Add SLA fields to API response
- [x] Add Platform column to template
- [x] Add SLA column to template
- [x] Create `getSLABadge()` function
- [x] Update all colspan values
- [x] Test syntax (Python + HTML)
- [x] Create Phase 4 documentation

**Status**: ✅ Phase 4 Complete - Ready for Testing!

---

## 📚 References

- **Phase 2 Doc**: [SLA-based Batch Creation](./Phase2-SLA-Based-Batch-Creation.md)
- **Phase 3 Doc**: [Stock Reallocation](./Phase3-Stock-Reallocation.md)
- **API Endpoint**: `/api/shortage/queue` in `app.py:5019`
- **Template**: `/templates/shortage_queue.html`
- **Function**: `getSLABadge()` in `shortage_queue.html:402`

---

## 🎉 All Phases Complete!

✅ **Phase 0**: Reserved Stock Release Fix
✅ **Phase 1**: SLA Fields Implementation
✅ **Phase 2**: SLA-based Batch Creation
✅ **Phase 3**: Stock Import + Reallocation
✅ **Phase 4**: Shortage Management + SLA Priority

**Next**: Integration Testing & User Acceptance Testing
