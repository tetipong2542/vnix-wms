# 📋 TODO Checklist - VNIX WMS

**Last Updated:** 2025-11-19
**Current Phase:** Phase 2 - Enhancements

---

## ✅ เสร็จสมบูรณ์แล้ว (Completed)

### Option 4: Security & Data Integrity
- [x] 4.1 Database Backup Automation
  - [x] backup_database.sh script
  - [x] setup_cron.sh script
  - [x] 30-day retention policy
  - [x] SQLite integrity checks
  - [x] Documentation: backups/README.md
- [x] 4.2 Security Fixes
  - [x] SECRET_KEY required (no fallback)
  - [x] ADMIN_USERNAME configurable
  - [x] Auto-generate admin password
  - [x] python-dotenv integration
  - [x] .env.example with documentation
  - [x] SECURITY.md guide
- [x] 4.3 Race Condition Protection
  - [x] SELECT FOR UPDATE lock in get_next_run_number()
  - [x] Auto-generate run_no
  - [x] Retry logic with exponential backoff
  - [x] Update all routes to use retry wrapper
  - [x] Remove manual run_no input from UI
- [x] 4.4 Stock Reservation System
  - [x] reserved_qty column in Stock model
  - [x] available_qty property
  - [x] Stock reservation on batch creation
  - [x] Reset reservation on stock import
  - [x] Migration: add_stock_reserved_qty.sql
  - [x] Documentation: Stock-Reservation-System.md

**Status:** ✅ 100% Complete (16/16 items)

---

## ❌ ยังไม่ได้ทำ (Pending) - Phase 2

### 🔴 HIGH Priority

#### Option 5: Role-Based Access Control (RBAC)
**Estimate:** 2-3 hours
**Priority:** HIGH
**From PRD:** FR-UM-02, FR-UM-03

**Tasks:**
- [ ] 5.1 Database Schema Changes
  - [ ] เพิ่ม `role` column ใน User model
    - Values: 'admin', 'staff', 'picker', 'packer'
  - [ ] เพิ่ม `department` column ใน User model
    - Values: 'online', 'warehouse'
  - [ ] สร้าง migration script
  - [ ] Run migration

- [ ] 5.2 Backend - Permission System
  - [ ] สร้าง `@require_role()` decorator
  - [ ] สร้าง `@require_department()` decorator
  - [ ] สร้าง `@require_permission()` decorator (combined)
  - [ ] เพิ่ม permission check ใน routes:
    - [ ] `/import/*` - admin only
    - [ ] `/users/*` - admin only
    - [ ] `/batch/create` - online department only
    - [ ] `/batch/delete/*` - admin only
    - [ ] `/scan/batch` - picker only
    - [ ] `/scan/sku` - picker only
    - [ ] `/scan/handover` - packer only
    - [ ] `/scan/tracking` - packer only

- [ ] 5.3 Frontend - UI Changes
  - [ ] อัพเดต base.html: ซ่อน/แสดงเมนูตาม role
  - [ ] อัพเดต users.html: เพิ่ม role และ department dropdowns
  - [ ] เพิ่ม permission denied page (403.html)
  - [ ] แสดง current user role ใน navbar

- [ ] 5.4 User Management
  - [ ] อัพเดต create user form (role + department)
  - [ ] อัพเดต edit user form
  - [ ] ตั้งค่า default role สำหรับ bootstrap admin

- [ ] 5.5 Testing
  - [ ] ทดสอบ admin role (full access)
  - [ ] ทดสอบ staff role (no import/user management)
  - [ ] ทดสอบ picker role (scan only)
  - [ ] ทดสอบ packer role (handover only)
  - [ ] ทดสอบ permission denied scenarios

**Expected Deliverables:**
- Migration script: `migrations/add_user_role_department.sql`
- Permission decorators in `app.py`
- Updated templates with role-based visibility
- Documentation: `docs/RBAC-Implementation.md`

---

#### Testing Infrastructure
**Estimate:** 4-6 hours
**Priority:** HIGH

- [ ] 6.1 Unit Tests
  - [ ] Test Stock Reservation System
  - [ ] Test Race Condition Protection
  - [ ] Test get_next_run_number()
  - [ ] Test create_batch_with_retry()
  - [ ] Test RBAC decorators

- [ ] 6.2 Integration Tests
  - [ ] Test full batch creation flow
  - [ ] Test stock reservation + import reset
  - [ ] Test concurrent batch creation
  - [ ] Test permission enforcement

- [ ] 6.3 E2E Tests (Optional)
  - [ ] Test complete user journey
  - [ ] Test scanner workflows

- [ ] 6.4 Test Coverage
  - [ ] Setup pytest + coverage.py
  - [ ] Generate coverage report
  - [ ] Aim for >80% coverage

**Expected Deliverables:**
- `tests/` folder with test files
- pytest configuration
- Coverage report
- CI/CD integration (optional)

---

### 🟡 MEDIUM Priority

#### Performance Optimization
**Estimate:** 3-4 hours
**Priority:** MEDIUM

- [ ] 7.1 Database Indexing
  - [ ] Analyze slow queries with EXPLAIN
  - [ ] Add indexes:
    - [ ] `order_lines(batch_status, platform)`
    - [ ] `order_lines(batch_id)`
    - [ ] `batches(platform, batch_date)`
    - [ ] `stocks(sku)` (if not exists)
  - [ ] Measure improvement

- [ ] 7.2 Query Optimization
  - [ ] Fix N+1 queries (use eager loading)
  - [ ] Use `joinedload()` for relationships
  - [ ] Optimize batch summary computation
  - [ ] Cache frequently accessed data

- [ ] 7.3 Connection Pooling
  - [ ] Configure SQLAlchemy pool size
  - [ ] Add pool_pre_ping for connection health
  - [ ] Monitor connection usage

- [ ] 7.4 Performance Monitoring
  - [ ] Add query timing logs
  - [ ] Setup Flask-DebugToolbar (dev only)
  - [ ] Profile slow endpoints

**Expected Deliverables:**
- Migration with new indexes
- Performance benchmarks (before/after)
- Monitoring dashboard (optional)

---

#### Mobile UI Optimization
**Estimate:** 2-3 hours
**Priority:** MEDIUM

- [ ] 8.1 Responsive Design
  - [ ] Audit scanning pages on mobile
  - [ ] Fix layout issues
  - [ ] Test on real devices:
    - [ ] iOS Safari
    - [ ] Android Chrome
    - [ ] Various screen sizes

- [ ] 8.2 Touch Optimization
  - [ ] Increase button sizes (min 44x44px)
  - [ ] Improve tap targets
  - [ ] Add haptic feedback (if supported)
  - [ ] Optimize for one-handed use

- [ ] 8.3 Scanner Improvements
  - [ ] Larger QR code input
  - [ ] Auto-focus on scan input
  - [ ] Better error feedback
  - [ ] Offline mode indicators

- [ ] 8.4 PWA Support (Optional)
  - [ ] Create manifest.json
  - [ ] Add service worker
  - [ ] Enable "Add to Home Screen"
  - [ ] Cache critical assets

**Expected Deliverables:**
- Updated mobile CSS
- PWA configuration (optional)
- Mobile testing report

---

#### Error Handling & Logging
**Estimate:** 2-3 hours
**Priority:** MEDIUM

- [ ] 9.1 Centralized Error Tracking
  - [ ] Integrate Sentry (or similar)
  - [ ] Configure error levels
  - [ ] Add context to errors
  - [ ] Setup alerts

- [ ] 9.2 User-Friendly Errors
  - [ ] Create custom error pages (404, 500, 403)
  - [ ] Improve error messages (Thai language)
  - [ ] Add actionable error hints
  - [ ] Log user actions before error

- [ ] 9.3 Error Recovery
  - [ ] Add retry mechanisms
  - [ ] Graceful degradation
  - [ ] Fallback modes
  - [ ] Data integrity checks

**Expected Deliverables:**
- Sentry integration (optional)
- Custom error templates
- Error handling guide

---

#### Documentation
**Estimate:** 3-4 hours
**Priority:** MEDIUM

- [ ] 10.1 API Documentation (if needed)
  - [ ] Document all endpoints
  - [ ] Request/response examples
  - [ ] Error codes
  - [ ] Authentication

- [ ] 10.2 User Manual
  - [ ] Getting started guide
  - [ ] User roles and permissions
  - [ ] Common workflows
  - [ ] FAQ
  - [ ] Screenshots

- [ ] 10.3 Deployment Guide
  - [ ] Server requirements
  - [ ] Installation steps
  - [ ] Environment configuration
  - [ ] Database setup
  - [ ] Backup/restore procedures
  - [ ] Monitoring setup

- [ ] 10.4 Troubleshooting Guide
  - [ ] Common issues
  - [ ] Error messages
  - [ ] Debug steps
  - [ ] Contact information

**Expected Deliverables:**
- `docs/API.md` (if needed)
- `docs/User-Manual.md`
- `docs/Deployment.md`
- `docs/Troubleshooting.md`

---

## ⏳ แผนอนาคต (Future) - Phase 3

### 🟢 LOW Priority / Nice to Have

#### Multi-warehouse Support
- [ ] เพิ่ม Warehouse model
- [ ] Stock per warehouse
- [ ] Transfer between warehouses
- [ ] Warehouse selection UI
- [ ] Multi-warehouse reporting

#### REST API
- [ ] API endpoints สำหรับ external systems
- [ ] API authentication (JWT/OAuth)
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Rate limiting
- [ ] Webhooks

#### Advanced Analytics
- [ ] Charts และ graphs (Chart.js/D3.js)
- [ ] Trend analysis
- [ ] Performance metrics
- [ ] Custom reports
- [ ] Export to Excel/PDF

#### Other Ideas
- [ ] Barcode printing integration
- [ ] Email notifications
- [ ] SMS alerts
- [ ] Mobile app (React Native/Flutter)
- [ ] Real-time updates (WebSocket)
- [ ] Import from POS API (auto-sync)

---

## 📊 Summary Statistics

### Overall Progress
```
Total Items (Phase 2 + 3): 47
✅ Completed: 16 (34%)
❌ Pending (Phase 2): 26 (55%)
⏳ Future (Phase 3): 12 (26%)
```

### Phase 2 Progress
```
✅ Option 4: 16/16 (100%)
❌ Option 5: 0/6 (0%)
❌ Testing: 0/4 (0%)
❌ Performance: 0/4 (0%)
❌ Mobile UI: 0/4 (0%)
❌ Error Handling: 0/3 (0%)
❌ Documentation: 0/4 (0%)
```

---

## 🎯 Recommended Next Steps

1. **ทำทันที (This Week):**
   - ✅ Option 4: Security & Data Integrity (DONE!)
   - ❌ Option 5: RBAC (2-3 hours)
   - ❌ Basic Testing (2-3 hours)

2. **ทำในสัปดาห์หน้า:**
   - Performance Optimization
   - Mobile UI Improvements
   - Documentation Complete

3. **ทำเมื่อมีเวลา:**
   - Advanced Testing
   - Error Tracking Integration
   - Phase 3 Features

---

## 📝 Notes

- ✅ = เสร็จแล้ว
- ❌ = ยังไม่ได้ทำ (Priority)
- ⏳ = แผนอนาคต
- 🔴 = HIGH Priority
- 🟡 = MEDIUM Priority
- 🟢 = LOW Priority

**การอัพเดตเอกสารนี้:**
- อัพเดตทุกครั้งที่เสร็จงาน
- ทำ checkbox เมื่อเสร็จแต่ละ item
- เพิ่ม notes หากมีปัญหาหรือการเปลี่ยนแปลง

---

**Generated:** 2025-11-19
**By:** Claude Code
**Project:** VNIX WMS Phase 2
