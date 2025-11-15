# Design Document

## Overview

การปรับปรุง UX ของระบบ Batch Management จะเน้นการลดขั้นตอนการทำงาน เพิ่มความสะดวกในการค้นหาและจัดการ Batch และแก้ไขปัญหาที่พบในระบบปัจจุบัน โดยจะแบ่งการพัฒนาออกเป็น 3 ส่วนหลัก:

1. **Backend API Development** - สร้าง API endpoints ใหม่สำหรับ Quick Create และ Batch filtering
2. **Frontend Enhancement** - ปรับปรุง UI/UX ของหน้า Batch List, Batch Create, และ Batch Detail
3. **Performance & Error Handling** - เพิ่มประสิทธิภาพและปรับปรุงการจัดการข้อผิดพลาด

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Batch List   │  │ Batch Create │  │ Batch Detail │      │
│  │   (HTML/JS)  │  │   (HTML/JS)  │  │   (HTML/JS)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          │   AJAX Calls     │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Flask Routes (app.py)                               │   │
│  │  • /batch/list                                       │   │
│  │  • /batch/next-run/<platform>        [NEW]          │   │
│  │  • /batch/quick-create/<platform>    [NEW]          │   │
│  │  • /batch/create                                     │   │
│  │  • /batch/<batch_id>                                 │   │
│  │  • /batch/<batch_id>/summary                         │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Batch Management Functions                          │   │
│  │  • generate_batch_id()                               │   │
│  │  • compute_batch_summary()                           │   │
│  │  • create_batch_from_pending()                       │   │
│  │  • get_next_run_number()             [NEW]          │   │
│  └──────────────────┬───────────────────────────────────┘   │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer (SQLAlchemy)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Batch      │  │  OrderLine   │  │    Shop      │      │
│  │   Model      │  │    Model     │  │    Model     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend**: Flask (Python), SQLAlchemy ORM
- **Frontend**: Bootstrap 5.3.2, jQuery 3.7.1, DataTables 1.13.8
- **Database**: SQLite
- **AJAX**: jQuery AJAX for asynchronous operations

## Components and Interfaces

### 1. Backend API Components

#### 1.1 New API Endpoints

**Endpoint: `/batch/next-run/<platform>`**
- **Method**: GET
- **Purpose**: Get next available run number and preview data for quick create
- **Parameters**: 
  - `platform` (path): Platform name (Shopee, Lazada, TikTok)
- **Response**:
```json
{
  "platform": "Shopee",
  "next_run": 2,
  "batch_id_preview": "SH-2024-11-13-R2",
  "pending_count": 45,
  "summary": {
    "total_orders": 45,
    "carrier_summary": {
      "SPX": 30,
      "Flash": 10,
      "LEX": 3,
      "J&T": 2
    },
    "shop_summary": {
      "Shop A": 25,
      "Shop B": 20
    }
  }
}
```

**Endpoint: `/batch/quick-create/<platform>`**
- **Method**: POST
- **Purpose**: Create batch with next available run number automatically
- **Parameters**: 
  - `platform` (path): Platform name
- **Response**:
```json
{
  "success": true,
  "message": "สร้าง Batch SH-2024-11-13-R2 สำเร็จ",
  "batch_id": "SH-2024-11-13-R2",
  "redirect_url": "/batch/SH-2024-11-13-R2"
}
```

#### 1.2 Helper Functions

**Function: `get_next_run_number(platform: str, batch_date: date) -> int`**
- **Purpose**: Calculate next available run number for a platform on a specific date
- **Logic**:
  1. Query existing batches for the platform and date
  2. Find maximum run_no
  3. Return max_run + 1 (or 1 if no batches exist)
- **Returns**: Integer (1, 2, 3, ...)

**Function: `get_pending_orders_count(platform: str) -> int`**
- **Purpose**: Count pending orders for a platform
- **Logic**: Query OrderLine with batch_status='pending_batch' and platform
- **Returns**: Integer count

### 2. Frontend Components

#### 2.1 Batch List Page Enhancements

**Component: Quick Create Modal**
- **Location**: `templates/batch_list.html`
- **Features**:
  - Display batch preview with carrier and shop summary
  - Show loading spinner while fetching data
  - Confirm button with loading state
  - Auto-redirect to batch detail on success
- **JavaScript Functions**:
  - `loadQuickCreateData(platform)`: Fetch preview data via AJAX
  - `confirmQuickCreate()`: Submit quick create request

**Component: Filter Panel**
- **Location**: New section in `templates/batch_list.html`
- **Features**:
  - Search box for Batch ID
  - Platform dropdown filter
  - Status dropdown filter (All, Locked, Unlocked)
  - Date range picker
  - Clear filters button
- **Implementation**: Use DataTables built-in filtering API

**Component: Enhanced Batch Table**
- **Features**:
  - Color-coded platform badges
  - Larger font for order counts
  - Carrier summary badges in table
  - Responsive column hiding for mobile
- **DataTables Configuration**:
```javascript
$('#batchTable').DataTable({
  order: [[3, 'desc']], // Sort by date
  pageLength: 25,
  responsive: true,
  language: { url: '//cdn.datatables.net/plug-ins/1.13.8/i18n/th.json' }
});
```

#### 2.2 Batch Create Page Improvements

**Component: Enhanced Preview Section**
- **Location**: `templates/batch_create.html`
- **Features**:
  - Larger, more prominent summary cards
  - Visual carrier distribution (progress bars or charts)
  - Shop distribution table with sorting
  - Real-time Batch ID preview
- **Styling**: Use Bootstrap cards with color-coded headers

**Component: Run Number Selector**
- **Features**:
  - Radio buttons instead of dropdown for better UX
  - Show suggested next run (highlighted)
  - Display existing batches for the day
- **JavaScript**: Auto-update Batch ID preview on selection

#### 2.3 Batch Detail Page Enhancements

**Component: Summary Dashboard**
- **Location**: `templates/batch_detail.html`
- **Features**:
  - Large KPI cards for key metrics
  - Visual carrier distribution (pie chart or bar chart)
  - Shop distribution cards
  - Export buttons (Excel, JSON, PDF)
- **Chart Library**: Consider using Chart.js for visualizations

**Component: Enhanced Order Table**
- **Features**:
  - DataTables with advanced filtering
  - Column visibility toggle
  - Export functionality
  - Responsive design
- **Performance**: Use server-side processing for large datasets

### 3. UI/UX Design Patterns

#### 3.1 Color Scheme

**Platform Colors:**
- Shopee: `bg-danger` (Red #EE4D2D)
- Lazada: `bg-primary` (Blue #0F156D)
- TikTok: `bg-dark` (Black #000000)

**Carrier Colors:**
- SPX: `bg-danger` (Red)
- Flash: `bg-warning` (Yellow/Orange)
- LEX: `bg-primary` (Blue)
- J&T: `bg-success` (Green)
- Other: `bg-secondary` (Gray)

**Status Colors:**
- Locked: `bg-success` (Green)
- Unlocked: `bg-warning` (Yellow)

#### 3.2 Typography

- **Headers**: Bootstrap h2-h5 classes
- **Body**: Default Bootstrap font (system font stack)
- **Numbers**: Larger font size (fs-4, fs-3) for emphasis
- **Icons**: Emoji or Bootstrap Icons

#### 3.3 Spacing and Layout

- Use Bootstrap grid system (container-fluid, row, col)
- Consistent padding: `py-3`, `px-4`
- Card spacing: `mb-3`, `mb-4`
- Button spacing: `gap-2`, `gap-3`

#### 3.4 Responsive Breakpoints

- **Mobile** (< 576px): Stack cards vertically, hide less important columns
- **Tablet** (576px - 992px): 2-column layout for cards
- **Desktop** (> 992px): Full layout with all features

## Data Models

### Existing Models (No Changes)

**Batch Model:**
```python
class Batch(db.Model):
    batch_id = db.Column(db.String(64), primary_key=True)
    platform = db.Column(db.String(20), nullable=False)
    run_no = db.Column(db.Integer, nullable=False)
    batch_date = db.Column(db.Date, nullable=False)
    total_orders = db.Column(db.Integer, default=0)
    spx_count = db.Column(db.Integer, default=0)
    flash_count = db.Column(db.Integer, default=0)
    lex_count = db.Column(db.Integer, default=0)
    jt_count = db.Column(db.Integer, default=0)
    other_count = db.Column(db.Integer, default=0)
    shop_summary = db.Column(db.Text)  # JSON
    locked = db.Column(db.Boolean, default=True)
    created_by_user_id = db.Column(db.Integer)
    created_by_username = db.Column(db.String(64))
    created_at = db.Column(db.DateTime)
```

**OrderLine Model:**
```python
class OrderLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(20), nullable=False)
    shop_id = db.Column(db.Integer, nullable=False)
    order_id = db.Column(db.String(128), nullable=False)
    sku = db.Column(db.String(64), nullable=False)
    qty = db.Column(db.Integer, default=1)
    carrier = db.Column(db.String(64))
    batch_status = db.Column(db.String(20), default="pending_batch")
    batch_id = db.Column(db.String(64))
    # ... other fields
```

### Database Indexes (Performance Optimization)

**Recommended Indexes:**
```python
# In models.py or migration script
db.Index('idx_batch_platform_date', Batch.platform, Batch.batch_date)
db.Index('idx_batch_created_at', Batch.created_at)
db.Index('idx_orderline_batch_status', OrderLine.batch_status)
db.Index('idx_orderline_platform', OrderLine.platform)
db.Index('idx_orderline_batch_id', OrderLine.batch_id)
```

## Error Handling

### Backend Error Handling

**Error Types:**
1. **Validation Errors**: Invalid platform, missing data
2. **Business Logic Errors**: No pending orders, duplicate batch ID
3. **Database Errors**: Connection issues, constraint violations
4. **System Errors**: Unexpected exceptions

**Error Response Format:**
```json
{
  "success": false,
  "error": "error_code",
  "message": "User-friendly error message in Thai",
  "details": {} // Optional technical details
}
```

**Error Codes:**
- `NO_PENDING_ORDERS`: No orders available for batch creation
- `DUPLICATE_BATCH_ID`: Batch ID already exists
- `INVALID_PLATFORM`: Invalid platform name
- `DATABASE_ERROR`: Database operation failed
- `UNKNOWN_ERROR`: Unexpected error

### Frontend Error Handling

**Error Display:**
- Use Bootstrap alerts for error messages
- Show specific error messages from backend
- Provide actionable suggestions
- Auto-dismiss success messages after 5 seconds
- Keep error messages until user dismisses

**Loading States:**
- Show spinner during AJAX requests
- Disable buttons during processing
- Display progress indicators for long operations

**Validation:**
- Client-side validation before API calls
- Prevent duplicate submissions
- Validate required fields

## Testing Strategy

### Unit Tests

**Backend Tests:**
- Test `get_next_run_number()` function
- Test `create_batch_from_pending()` with various scenarios
- Test API endpoints with mock data
- Test error handling paths

**Test Cases:**
```python
def test_get_next_run_number_no_existing_batches():
    # Should return 1 when no batches exist
    
def test_get_next_run_number_with_existing_batches():
    # Should return max_run + 1
    
def test_quick_create_no_pending_orders():
    # Should return error
    
def test_quick_create_success():
    # Should create batch and return success
```

### Integration Tests

**API Tests:**
- Test complete quick create flow
- Test batch list filtering
- Test batch detail page loading
- Test error scenarios

### Manual Testing Checklist

**Batch List Page:**
- [ ] Quick create button works for each platform
- [ ] Modal displays correct preview data
- [ ] Filters work correctly
- [ ] Search finds batches
- [ ] Table sorts correctly
- [ ] Responsive design works on mobile

**Batch Create Page:**
- [ ] Platform selection works
- [ ] Preview data displays correctly
- [ ] Run number selection updates Batch ID
- [ ] Create button works
- [ ] Error messages display correctly
- [ ] Redirect to detail page works

**Batch Detail Page:**
- [ ] Summary cards display correctly
- [ ] Carrier distribution shows accurate data
- [ ] Shop distribution shows accurate data
- [ ] Order table loads and filters work
- [ ] Export buttons work

### Performance Testing

**Metrics to Measure:**
- Page load time (target: < 2 seconds)
- API response time (target: < 1 second)
- Batch creation time (target: < 3 seconds)
- DataTables rendering time (target: < 500ms)

**Load Testing:**
- Test with 100+ batches in list
- Test with 1000+ orders in batch detail
- Test concurrent batch creation

## Security Considerations

**Authentication:**
- All batch management routes require login
- Use `@login_required` decorator

**Authorization:**
- Only authenticated users can create batches
- Track user who created each batch
- Audit log for all batch operations

**Input Validation:**
- Validate platform names against whitelist
- Sanitize user inputs
- Prevent SQL injection (use SQLAlchemy ORM)
- Prevent XSS (escape HTML in templates)

**CSRF Protection:**
- Use Flask-WTF CSRF tokens for POST requests
- Validate tokens on all form submissions

## Deployment Considerations

**Database Migration:**
- No schema changes required
- Add indexes via migration script
- Test migration on staging first

**Static Assets:**
- Minify CSS and JavaScript for production
- Use CDN for Bootstrap and jQuery
- Cache static files with proper headers

**Configuration:**
- Use environment variables for sensitive data
- Configure logging for production
- Set up error monitoring (e.g., Sentry)

**Rollback Plan:**
- Keep backup of current code
- Document rollback procedure
- Test rollback in staging

## Future Enhancements

**Phase 2 Features:**
1. Batch editing (unlock and modify)
2. Batch merging (combine multiple batches)
3. Batch splitting (split large batches)
4. Advanced analytics dashboard
5. Batch templates for recurring patterns
6. Automated batch creation (scheduled)
7. Email notifications for batch events
8. Batch history and audit trail viewer
9. Batch comparison tool
10. Export to multiple formats (PDF, CSV)

**Technical Improvements:**
1. Migrate to PostgreSQL for better performance
2. Implement caching (Redis) for frequently accessed data
3. Add WebSocket for real-time updates
4. Implement GraphQL API for flexible queries
5. Add comprehensive API documentation (Swagger/OpenAPI)
