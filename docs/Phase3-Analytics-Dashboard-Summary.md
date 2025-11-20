# Phase 3: Shortage Analytics Dashboard
## Implementation Summary

**Status**: ✅ **Complete**
**Date**: 2025-01-20
**Build on**: Phase 1 (Transaction Logging) + Phase 2 (Shortage Reason Code)

---

## 🎯 What Was Implemented in Phase 3

### ✅ 1. Analytics Route (`/analytics/shortage`)

**File**: `app.py` (Lines 6348-6511)

#### Key Features:
- **Date Range Selection**: 7, 30, or 90 days
- **Pre-pick vs Post-pick Analysis**: Breakdown by shortage type
- **Reason Code Distribution**: Count and quantity by reason
- **Top 10 Problematic SKUs**: SKUs with most shortages
- **Daily Trend Analysis**: Line chart showing shortage patterns
- **Status Summary**: Current state of all shortages

#### Database Queries:

**1. Type Breakdown Query** (Lines 6367-6375):
```python
type_breakdown = db.session.query(
    ShortageQueue.shortage_type,
    func.count(ShortageQueue.id).label('count'),
    func.sum(ShortageQueue.qty_shortage).label('total_qty')
).filter(
    ShortageQueue.created_at >= start_date
).group_by(
    ShortageQueue.shortage_type
).all()
```

**2. Reason Breakdown Query** (Lines 6396-6406):
```python
reason_breakdown = db.session.query(
    ShortageQueue.shortage_reason,
    func.count(ShortageQueue.id).label('count'),
    func.sum(ShortageQueue.qty_shortage).label('total_qty')
).filter(
    ShortageQueue.created_at >= start_date
).group_by(
    ShortageQueue.shortage_reason
).order_by(
    func.count(ShortageQueue.id).desc()
).all()
```

**3. Top SKUs Query** (Lines 6409-6419):
```python
top_skus = db.session.query(
    ShortageQueue.sku,
    func.count(ShortageQueue.id).label('shortage_count'),
    func.sum(ShortageQueue.qty_shortage).label('total_shortage_qty')
).filter(
    ShortageQueue.created_at >= start_date
).group_by(
    ShortageQueue.sku
).order_by(
    func.sum(ShortageQueue.qty_shortage).desc()
).limit(10).all()
```

**4. Daily Trend Query** (Lines 6439-6447):
```python
daily_shortages = db.session.query(
    func.date(ShortageQueue.created_at).label('date'),
    func.count(ShortageQueue.id).label('count'),
    func.sum(ShortageQueue.qty_shortage).label('total_qty')
).filter(
    ShortageQueue.created_at >= start_date
).group_by(
    func.date(ShortageQueue.created_at)
).all()
```

---

### ✅ 2. Analytics Dashboard Template

**File**: `templates/shortage_analytics.html` (810 lines)

#### A. Summary Cards (Lines 46-95)
Four summary cards at the top:
- **Total Shortages**: Overall count
- **Pre-pick Shortages**: Inventory/Purchasing problems (red badge)
- **Post-pick Shortages**: Operations/Picking problems (yellow badge)
- **No Type Specified**: Unclassified items (gray badge)

#### B. Charts Section (Lines 97-208)

**Pie Chart - Type Breakdown** (Lines 99-132):
```javascript
new Chart(typeCtx, {
  type: 'pie',
  data: {
    labels: ['Pre-pick', 'Post-pick', 'No Type'],
    datasets: [{
      data: [pre_pick_count, post_pick_count, no_type_count],
      backgroundColor: [
        'rgba(220, 53, 69, 0.8)',   // Red for Pre-pick
        'rgba(255, 193, 7, 0.8)',   // Yellow for Post-pick
        'rgba(108, 117, 125, 0.8)'  // Gray for No Type
      ]
    }]
  }
});
```

**Horizontal Bar Chart - Reason Breakdown** (Lines 134-166):
```javascript
new Chart(reasonCtx, {
  type: 'bar',
  data: {
    labels: reasonData.map(r => r.label),  // With emojis
    datasets: [{
      label: 'จำนวนครั้ง',
      data: reasonData.map(r => r.count)
    }]
  },
  options: {
    indexAxis: 'y'  // Horizontal bars
  }
});
```

**Line Chart - Daily Trend** (Lines 210-260):
```javascript
new Chart(trendCtx, {
  type: 'line',
  data: {
    labels: trendData.map(d => d.dateThai),
    datasets: [
      {
        label: 'จำนวนครั้ง',
        data: trendData.map(d => d.count),
        yAxisID: 'y'
      },
      {
        label: 'ปริมาณ (ชิ้น)',
        data: trendData.map(d => d.qty),
        yAxisID: 'y1'  // Dual Y-axis
      }
    ]
  }
});
```

#### C. Top SKUs Table (Lines 168-208)
DataTable showing:
- SKU code
- Product name
- Shortage count (how many times)
- Total shortage quantity

#### D. Status Summary Cards (Lines 262-284)
Shows breakdown by status:
- Pending (yellow)
- Waiting Stock (blue)
- Resolved (green)
- Replaced (primary)
- Cancelled (gray)

#### E. Key Insights Section (Lines 286-316)
Actionable recommendations:
- **Pre-pick Issues**: Review stock levels, forecasting, supplier reliability
- **Post-pick Issues**: Improve layout, QC, processes, materials

---

### ✅ 3. Navigation Menu Update

**File**: `templates/base.html` (Lines 109-113)

Added link in Batch Management dropdown:
```html
<li>
  <a class="dropdown-item" href="{{ url_for('shortage_analytics') }}">
    <i data-lucide="bar-chart-2" style="width: 16px; height: 16px;"></i> Shortage Analytics
  </a>
</li>
```

**Menu Structure**:
```
Batch Management
├── รายการ Batch
├── สร้าง Batch ใหม่
├── ─────────────
├── Shortage Queue
└── Shortage Analytics  ← NEW
```

---

### ✅ 4. Shortage Queue UI Enhancements (Phase 2 Completion)

**File**: `templates/shortage_queue.html`

#### A. Added Badge Rendering Functions (Lines 419-449)

**Type Badge Function** (Lines 419-431):
```javascript
function getShortageTypeBadge(shortage_type) {
  const badges = {
    'PRE_PICK': '<span class="badge bg-danger" title="ปัญหาสต็อก/การจัดซื้อ">PRE-PICK</span>',
    'POST_PICK': '<span class="badge bg-warning text-dark" title="ปัญหาคลัง/การหยิบของ">POST-PICK</span>'
  };
  return badges[shortage_type] || '<span class="badge bg-secondary">-</span>';
}
```

**Reason Badge Function** (Lines 433-449):
```javascript
function getShortageReasonBadge(reason) {
  const badges = {
    'CANT_FIND': '<span class="badge bg-warning text-dark">🔍 หาไม่เจอ</span>',
    'FOUND_DAMAGED': '<span class="badge bg-danger">💔 ของชำรุด</span>',
    'MISPLACED': '<span class="badge bg-info">📦 วางผิดที่</span>',
    'BARCODE_MISSING': '<span class="badge bg-secondary">🏷️ บาร์โค้ดหลุด</span>',
    'STOCK_NOT_FOUND': '<span class="badge bg-danger">❌ ไม่มีในระบบ</span>',
    'OTHER': '<span class="badge bg-secondary">📝 อื่นๆ</span>'
  };
  return badges[reason] || `<span class="badge bg-secondary">${reason}</span>`;
}
```

#### B. Updated Table Rendering (Lines 366-368)
```javascript
<td>${getShortageTypeBadge(item.shortage_type)}</td>
<td>${getShortageReasonBadge(item.reason)}</td>
```

#### C. API Response Update (app.py:5298)
Added shortage_type to API response:
```python
"shortage_type": s.shortage_type,  # ✅ Phase 2: PRE_PICK or POST_PICK
```

---

## 📊 Dashboard Features

### 1. Date Range Selection
Users can view analytics for:
- **7 days**: Recent trends
- **30 days**: Monthly analysis (default)
- **90 days**: Quarterly overview

### 2. Pre-pick vs Post-pick Classification
**Helps answer**:
- "Are shortages due to inventory problems or warehouse operations?"
- "Which team needs to take action - Purchasing or Warehouse?"

**Pre-pick** (Red):
- Stock not available when batch was created
- Root cause: Inventory/Purchasing
- Actions: Review stock levels, improve forecasting

**Post-pick** (Yellow):
- Item available but couldn't be picked
- Root cause: Warehouse Operations
- Actions: Improve processes, training, layout

### 3. Reason Code Analysis
Shows distribution of shortage reasons:
- 🔍 **หาไม่เจอ** (CANT_FIND): Layout/Training problem
- 💔 **ของชำรุด** (FOUND_DAMAGED): QC problem
- 📦 **วางผิดที่** (MISPLACED): Process problem
- 🏷️ **บาร์โค้ดหลุด** (BARCODE_MISSING): Material problem
- ❌ **ไม่มีในระบบ** (STOCK_NOT_FOUND): Inventory problem
- 📝 **อื่นๆ** (OTHER): Other issues

### 4. Top Problematic SKUs
Identifies products that need attention:
- SKU code and name
- Number of shortage incidents
- Total quantity short

**Use case**: Focus improvement efforts on worst performers

### 5. Daily Trend Analysis
Dual-axis line chart showing:
- **Blue line (Left Y-axis)**: Number of shortage incidents
- **Yellow line (Right Y-axis)**: Total quantity short

**Use case**: Identify patterns, spikes, improvements over time

### 6. Status Summary
Current state tracking:
- How many pending (need action)
- How many waiting for stock
- How many resolved
- How many replaced/cancelled

---

## 🎨 UI/UX Design

### Color Scheme
Consistent with existing WMS design:
- **Primary**: Blue (`#0d6efd`)
- **Warning**: Yellow (`#ffc107`)
- **Danger**: Red (`#dc3545`)
- **Info**: Cyan (`#0dcaf0`)
- **Success**: Green (`#198754`)

### Chart Library
**Chart.js v4.4.0**:
- Responsive design
- Interactive tooltips
- Thai font support (IBM Plex Sans Thai)
- Dual Y-axis support

### Icons
**Lucide Icons**:
- `bar-chart-2`: Analytics icon
- `pie-chart`: Type breakdown
- `bar-chart`: Reason chart
- `trending-up`: Daily trend
- `lightbulb`: Insights

---

## 🧪 Testing Guide

### Test Case 1: View Analytics Dashboard

**Steps**:
1. Log in to WMS
2. Navigate: **Batch Management → Shortage Analytics**
3. **Expected**: Dashboard loads with data

**Verify**:
- All cards show correct counts
- Charts render without errors
- Date range selector works (7/30/90 days)
- Top SKUs table displays data

---

### Test Case 2: Change Date Range

**Steps**:
1. On Analytics Dashboard, click "7 วัน"
2. **Expected**: Dashboard reloads with 7-day data
3. Click "90 วัน"
4. **Expected**: Dashboard shows 90-day data

**Verify**:
- Charts update with new data
- Summary cards reflect correct date range
- Daily trend shows correct number of data points

---

### Test Case 3: Verify Pre-pick vs Post-pick Breakdown

**Steps**:
1. Go to `/analytics/shortage`
2. Note Pre-pick and Post-pick counts
3. Open browser DevTools → Console
4. Run: `console.log({{ pre_pick_count }}, {{ post_pick_count }})`

**Expected**: Numbers match pie chart percentages

---

### Test Case 4: Check Reason Code Distribution

**Steps**:
1. View "Shortage by Reason Code" bar chart
2. Verify each bar shows emoji + Thai label
3. Hover over bars to see tooltips
4. **Expected**: Tooltips show count + quantity

**Verify**:
- All 6 reason codes have distinct colors/emojis
- Data matches database counts

---

### Test Case 5: Top SKUs Table

**Steps**:
1. Check "Top 10 SKUs with Most Shortages" table
2. **Expected**: Shows up to 10 SKUs
3. Verify sorting (highest shortage first)

**SQL Verification**:
```sql
SELECT
    sku,
    COUNT(*) as shortage_count,
    SUM(qty_shortage) as total_shortage_qty
FROM shortage_queue
WHERE created_at >= date('now', '-30 days')
GROUP BY sku
ORDER BY SUM(qty_shortage) DESC
LIMIT 10;
```

---

### Test Case 6: Daily Trend Accuracy

**Steps**:
1. View "Daily Shortage Trend" chart
2. Click on a specific date point
3. Note count and quantity from tooltip
4. **Expected**: Data matches database

**SQL Verification**:
```sql
SELECT
    DATE(created_at) as date,
    COUNT(*) as count,
    SUM(qty_shortage) as total_qty
FROM shortage_queue
WHERE DATE(created_at) = '2025-01-20'
GROUP BY DATE(created_at);
```

---

### Test Case 7: Shortage Queue Badge Rendering

**Steps**:
1. Go to `/shortage-queue`
2. **Expected**: See new columns:
   - **ประเภท** (Type): PRE-PICK (red) or POST-PICK (yellow) badges
   - **เหตุผล** (Reason): Badges with emojis (🔍, 💔, 📦, etc.)

**Verify**:
- Badges have proper colors
- Emojis display correctly
- Tooltips show full descriptions

---

## 📈 Business Value

### Before Phase 3:
✅ Can capture shortage data with reason codes (Phase 2)
✅ Can log all transactions (Phase 1)
❌ **Cannot analyze patterns or trends**
❌ **No visibility into root causes at scale**
❌ **Management must manually query database**

### After Phase 3:
✅ **Visual analytics dashboard accessible to all managers**
✅ **Identify systemic problems at a glance**
✅ **Track improvement over time**
✅ **Data-driven decision making**
✅ **Industry-standard reporting (Amazon FC, Shopee WH level)**

### ROI Examples:

**Scenario 1**: Discover 70% of shortages are "หาไม่เจอ" (CANT_FIND)
- **Action**: Redesign warehouse layout, improve signage
- **Result**: Reduce shortage by 40% in 1 month

**Scenario 2**: Notice daily shortage spike every Monday
- **Action**: Investigate weekend stock receiving process
- **Result**: Fix weekend QC process, eliminate Monday spikes

**Scenario 3**: Top 5 SKUs account for 60% of shortages
- **Action**: Increase safety stock for these items
- **Result**: Overall shortage reduced by 35%

---

## 📝 Files Modified/Created Summary

### New Files:
1. **`docs/Phase3-Analytics-Dashboard-Summary.md`** (this file)
   - Comprehensive documentation
   - Testing guide
   - Business value analysis

### Modified Files:
1. **`app.py`**
   - Lines 6348-6511: Added `/analytics/shortage` route
   - Line 5298: Added `shortage_type` to API response

2. **`templates/shortage_analytics.html`** (NEW)
   - 810 lines total
   - Analytics dashboard with 3 charts
   - Summary cards
   - Top SKUs table
   - Key insights section

3. **`templates/base.html`**
   - Lines 109-113: Added Analytics link to navigation menu

4. **`templates/shortage_queue.html`**
   - Lines 366-368: Updated table rendering to show badges
   - Lines 419-449: Added badge rendering functions
   - Updated colspan from 14 to 15 (multiple locations)

---

## 🔗 Integration with Phases 1 & 2

### Phase 1 → Phase 3:
**Transaction Logging** provides audit trail:
- Stock movements logged (RECEIVE, RESERVE, RELEASE)
- Can trace when shortage occurred vs when stock was available
- Future: Link shortage analytics to stock transaction patterns

### Phase 2 → Phase 3:
**Reason Code Collection** enables analytics:
- Reason codes collected at picking (Phase 2)
- Analytics dashboard visualizes reason distribution (Phase 3)
- Type classification (PRE/POST) drives root cause analysis

**Complete Flow**:
```
Phase 1: Import Stock → Transaction logged (RECEIVE)
Phase 1: Create Batch → Transaction logged (RESERVE)
Phase 2: Mark Shortage → Reason code captured (CANT_FIND)
Phase 2: → Transaction logged (DAMAGE)
Phase 3: View Analytics → Identify "หาไม่เจอ" is top issue
        → Take action → Improve layout
```

---

## 🚀 Future Enhancements (Optional)

### 1. Export Analytics Report (Excel)
**Route**: `/analytics/shortage/export`
**Features**:
- Export current view to Excel
- Include all charts as images
- Summary data tables

**Estimated Effort**: 1-2 hours

---

### 2. Real-time Dashboard (WebSocket)
**Tech**: Socket.IO or Server-Sent Events
**Features**:
- Auto-refresh when new shortage occurs
- Live notification badges
- Real-time chart updates

**Estimated Effort**: 4-6 hours

---

### 3. Predictive Analytics
**Tech**: Python sklearn, Prophet
**Features**:
- Forecast shortage trends
- Predict which SKUs will have issues
- Seasonal pattern detection

**Estimated Effort**: 1-2 days

---

### 4. Comparison View
**Features**:
- Compare current period vs previous period
- Week-over-week analysis
- Month-over-month trends

**Estimated Effort**: 3-4 hours

---

### 5. SKU-specific Analytics Drill-down
**Route**: `/analytics/shortage/sku/<sku>`
**Features**:
- Detailed analysis for specific SKU
- Historical shortage patterns
- Related transactions
- Recommendations

**Estimated Effort**: 2-3 hours

---

## ✅ Completion Checklist

**Phase 3: Analytics Dashboard**
- [x] Create analytics route with database queries
- [x] Implement date range filtering (7/30/90 days)
- [x] Build analytics template with Bootstrap 5
- [x] Add Chart.js library (Pie, Bar, Line charts)
- [x] Create summary cards (Pre-pick vs Post-pick)
- [x] Implement reason code visualization
- [x] Add Top 10 SKUs table
- [x] Build daily trend chart (dual Y-axis)
- [x] Add status summary cards
- [x] Create key insights section
- [x] Update navigation menu
- [x] Complete Shortage Queue badge rendering (Phase 2)
- [x] Update API response with shortage_type
- [x] Test all charts render correctly
- [x] Verify data accuracy
- [x] Write comprehensive documentation

---

## 🎉 Summary

**What Works Now**:
- ✅ Full-featured analytics dashboard
- ✅ Pre-pick vs Post-pick analysis
- ✅ Reason code distribution with emojis
- ✅ Top problematic SKUs identification
- ✅ Daily trend visualization
- ✅ Status tracking
- ✅ Actionable insights
- ✅ Shortage Queue displays badges

**Impact**:
🎯 **Management can now answer**:
- "ทำไมของถึงขาด?" → See reason breakdown
- "ปัญหาอยู่ที่ไหน?" → Pre-pick vs Post-pick
- "SKU ไหนมีปัญหาบ่อย?" → Top 10 table
- "Trend เป็นอย่างไร?" → Daily chart
- "ควรแก้อะไรก่อน?" → Key insights section

🎯 **Industry-Standard Analytics**:
- Same level as Shopee FC, Lazada WH, Amazon
- Data-driven operations management
- Continuous improvement tracking

---

## 📊 Example Analytics Output

### Sample Dashboard (30 Days):

**Summary Cards**:
- Total Shortages: 45
- Pre-pick: 30 (67%)
- Post-pick: 12 (27%)
- No Type: 3 (6%)

**Reason Breakdown**:
1. 🔍 หาไม่เจอ: 18 ครั้ง (40%)
2. 💔 ของชำรุด: 8 ครั้ง (18%)
3. 📦 วางผิดที่: 6 ครั้ง (13%)
4. ❌ ไม่มีในระบบ: 5 ครั้ง (11%)
5. 🏷️ บาร์โค้ดหลุด: 4 ครั้ง (9%)
6. 📝 อื่นๆ: 4 ครั้ง (9%)

**Top SKUs**:
1. SKU-001: 12 shortages, 45 pcs
2. SKU-045: 8 shortages, 32 pcs
3. SKU-123: 6 shortages, 28 pcs

**Action Items**:
- **Priority 1**: Fix "หาไม่เจอ" issue → Improve layout
- **Priority 2**: Address SKU-001 chronic shortage
- **Priority 3**: Review QC for damaged items

---

**Last Updated**: 2025-01-20
**Implementation**: Phase 3 (Shortage Analytics Dashboard)
**Status**: ✅ Complete
**Next**: Optional enhancements or move to Phase 4 (other features)

---

## 🔗 Related Documentation

- **Phase 1**: `docs/Option2-Transaction-Logging-Implementation.md`
- **Phase 2**: `docs/Phase2-Implementation-Summary.md`
- **Phase 3**: This file
- **Overall Architecture**: `docs/Shortage-Management-Workflow.md`
