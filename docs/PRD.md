# 📋 Product Requirements Document (PRD)
## VNIX Warehouse Management System (WMS)

---

## 📌 Document Information

| Field | Value |
|-------|-------|
| **Product Name** | VNIX Warehouse Management System (WMS) |
| **Version** | 2.0 |
| **Last Updated** | 2025-11-18 |
| **Author** | VNIX Development Team |
| **Status** | Active Development |
| **Document Type** | Product Requirements Document |

---

## 📑 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Overview](#product-overview)
3. [Goals & Objectives](#goals--objectives)
4. [Target Users](#target-users)
5. [User Stories & Use Cases](#user-stories--use-cases)
6. [Functional Requirements](#functional-requirements)
7. [Non-Functional Requirements](#non-functional-requirements)
8. [System Architecture](#system-architecture)
9. [Data Model](#data-model)
10. [User Interface Requirements](#user-interface-requirements)
11. [Security & Permissions](#security--permissions)
12. [Integration Requirements](#integration-requirements)
13. [Success Metrics](#success-metrics)
14. [Timeline & Milestones](#timeline--milestones)
15. [Risks & Mitigation](#risks--mitigation)
16. [Appendix](#appendix)

---

## 1. Executive Summary

### 1.1 Product Vision
VNIX WMS is a comprehensive warehouse management system designed to streamline e-commerce order fulfillment across multiple platforms (Shopee, TikTok, Lazada). The system bridges the gap between online order management and physical warehouse operations through an efficient batch-based picking and dispatching workflow.

### 1.2 Problem Statement
**Current Challenges:**
- Manual order processing is time-consuming and error-prone
- Lack of real-time stock visibility across multiple sales channels
- Inefficient warehouse picking workflow
- No systematic shortage management
- Limited tracking and accountability for warehouse staff
- Difficulty in managing SLA deadlines across platforms

### 1.3 Solution Overview
VNIX WMS provides:
- **Automated order allocation** based on stock availability
- **Batch-based picking system** for efficient warehouse operations
- **Real-time progress tracking** with QR code scanning
- **Multi-platform support** (Shopee, TikTok, Lazada)
- **Role-based access control** for different team functions
- **Comprehensive audit logging** for accountability
- **Shortage queue management** for out-of-stock scenarios

---

## 2. Product Overview

### 2.1 Core Features

#### 📊 Order Management
- Import orders from Excel (multi-platform support)
- Automatic order status classification (READY, LOW_STOCK, SHORTAGE)
- SLA tracking with due date computation
- Order allocation to available stock

#### 📦 Batch Processing
- Create picking batches by platform and date
- Automatic run number generation (R1, R2, R3...)
- QR code generation for batch and SKU tracking
- Progress tracking (percentage completion)
- Batch assignment to warehouse staff

#### 🏷️ SKU Management
- Product master data management
- Stock level tracking
- SKU QR code generation for scanning
- Multi-location support (shelves)

#### 🔍 Picking Workflow
- Batch acceptance via QR scanning
- SKU picking with quantity verification
- Partial picking support with shortage recording
- Real-time progress updates

#### 🚚 Dispatch Management
- Handover code generation
- Tracking number assignment
- Dispatch status tracking
- Handover slip printing

#### ⚠️ Shortage Management
- Automatic shortage queue population
- Status tracking (waiting_stock, cancelled, replaced, resolved)
- Reason categorization (out of stock, damaged goods)
- Priority management

#### 📈 Reporting & Analytics
- Dashboard with order status overview
- Batch progress monitoring
- Excel export for all major datasets
- Audit log for all critical actions

### 2.2 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.x, Flask |
| **Database** | SQLite (with SQLAlchemy ORM) |
| **Frontend** | HTML, CSS, JavaScript (vanilla) |
| **QR Code** | Python qrcode library |
| **Data Processing** | Pandas |
| **Authentication** | Flask sessions with password hashing |
| **Timezone** | Asia/Bangkok (TH_TZ) |
| **Calendar** | Buddhist Era (BE) support |

---

## 3. Goals & Objectives

### 3.1 Business Goals
1. **Increase operational efficiency** by 40% through batch processing
2. **Reduce picking errors** by 60% with QR code verification
3. **Improve order fulfillment time** to meet platform SLAs
4. **Enhance inventory accuracy** to 98%+ through real-time tracking
5. **Enable scalability** to support 10,000+ daily orders

### 3.2 User Goals

#### Online Team
- Quickly import and process orders
- Create efficient picking batches
- Monitor warehouse progress in real-time
- Manage shortage situations effectively

#### Warehouse Team
- Clear, easy-to-follow picking instructions
- Mobile-friendly scanning interface
- Quick batch assignment
- Accurate progress tracking

---

## 4. Target Users

### 4.1 User Personas

#### 👤 Persona 1: Online Admin
- **Role:** Online Team Manager
- **Responsibilities:** Full system oversight, data import, user management
- **Technical Skill:** High
- **Goals:** Ensure smooth order processing, maintain data integrity
- **Pain Points:** Manual data entry, lack of visibility

#### 👤 Persona 2: Online Staff
- **Role:** Order Coordinator
- **Responsibilities:** Create batches, monitor progress, handle customer queries
- **Technical Skill:** Medium
- **Goals:** Process orders quickly, minimize errors
- **Pain Points:** Confusion over stock availability, delayed updates

#### 👤 Persona 3: Warehouse Picker
- **Role:** Warehouse Operator
- **Responsibilities:** Pick items according to batch instructions
- **Technical Skill:** Low to Medium
- **Goals:** Clear picking instructions, quick task completion
- **Pain Points:** Paper-based lists, unclear product locations

#### 👤 Persona 4: Warehouse Packer
- **Role:** Dispatch Coordinator
- **Responsibilities:** Pack items, assign tracking, handover to logistics
- **Technical Skill:** Low to Medium
- **Goals:** Fast packing, accurate dispatch
- **Pain Points:** Manual tracking number entry, handover documentation

---

## 5. User Stories & Use Cases

### 5.1 Online Team User Stories

#### Story 1: Import Orders
**As an** Online Admin
**I want to** import orders from Excel
**So that** I can quickly process daily orders without manual entry

**Acceptance Criteria:**
- ✅ Support Excel file upload (.xlsx)
- ✅ Validate data format before import
- ✅ Display success/error messages
- ✅ Auto-classify orders by stock status
- ✅ Log import action in audit log

#### Story 2: Create Batch
**As an** Online Staff
**I want to** create a picking batch for specific platform and date
**So that** warehouse team can efficiently pick orders

**Acceptance Criteria:**
- ✅ Filter orders by platform (Shopee/TikTok/Lazada)
- ✅ Filter by date range
- ✅ Show only READY orders
- ✅ Auto-generate run number
- ✅ Create batch QR code
- ✅ Print picking list

#### Story 3: Monitor Progress
**As an** Online Staff
**I want to** see real-time batch progress
**So that** I can track order fulfillment status

**Acceptance Criteria:**
- ✅ Display batch list with progress percentage
- ✅ Show SKU-level completion
- ✅ Highlight shortages
- ✅ Update in real-time as warehouse scans

### 5.2 Warehouse Team User Stories

#### Story 4: Accept Batch
**As a** Picker
**I want to** scan a batch QR code to accept work
**So that** I know which orders to pick

**Acceptance Criteria:**
- ✅ Scan batch QR via mobile device
- ✅ Display batch details
- ✅ Record acceptance timestamp and user
- ✅ Show picking list

#### Story 5: Pick Items
**As a** Picker
**I want to** scan SKU QR codes and confirm quantities
**So that** I can accurately pick items

**Acceptance Criteria:**
- ✅ Scan SKU QR code
- ✅ Display required quantity
- ✅ Enter picked quantity
- ✅ Mark as complete or shortage
- ✅ Update progress immediately

#### Story 6: Handover to Logistics
**As a** Packer
**I want to** scan completed batches for handover
**So that** I can dispatch orders to logistics partners

**Acceptance Criteria:**
- ✅ View only completed batches (100% progress)
- ✅ Scan batch for handover
- ✅ Auto-generate handover code
- ✅ Print handover slip
- ✅ Mark batch as DISPATCHED

---

## 6. Functional Requirements

### 6.1 User Management

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-UM-01 | System shall support user registration with username/password | High | ✅ Done |
| FR-UM-02 | System shall support role-based access (admin, staff, picker, packer) | High | 🔄 Planned |
| FR-UM-03 | System shall support department assignment (online, warehouse) | High | 🔄 Planned |
| FR-UM-04 | System shall hash passwords securely | High | ✅ Done |
| FR-UM-05 | Admin shall be able to create/edit/delete users | High | ✅ Done |
| FR-UM-06 | System shall track user sessions | High | ✅ Done |

### 6.2 Product & Stock Management

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-PS-01 | System shall import products from Excel | High | ✅ Done |
| FR-PS-02 | System shall import stock levels from Excel | High | ✅ Done |
| FR-PS-03 | System shall track stock by SKU and shelf location | High | ✅ Done |
| FR-PS-04 | System shall support multi-shop inventory | Medium | ✅ Done |
| FR-PS-05 | System shall generate QR codes for each SKU | High | ✅ Done |
| FR-PS-06 | System shall update stock in real-time as orders are picked | High | ✅ Done |

### 6.3 Order Management

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-OM-01 | System shall import orders from Excel | High | ✅ Done |
| FR-OM-02 | System shall support multiple platforms (Shopee, TikTok, Lazada) | High | ✅ Done |
| FR-OM-03 | System shall classify orders as READY/LOW_STOCK/SHORTAGE | High | ✅ Done |
| FR-OM-04 | System shall compute SLA due dates by platform | High | ✅ Done |
| FR-OM-05 | System shall support order lines (multiple SKUs per order) | High | ✅ Done |
| FR-OM-06 | System shall track order status throughout workflow | High | ✅ Done |
| FR-OM-07 | System shall normalize platform names (case-insensitive) | Medium | ✅ Done |

### 6.4 Batch Management

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-BM-01 | System shall create batches filtered by platform and date | High | ✅ Done |
| FR-BM-02 | System shall auto-generate run numbers (R1, R2, R3...) | High | ✅ Done |
| FR-BM-03 | System shall generate unique batch QR codes | High | ✅ Done |
| FR-BM-04 | System shall track batch status (pending, in_progress, completed, dispatched) | High | ✅ Done |
| FR-BM-05 | System shall calculate batch progress percentage | High | ✅ Done |
| FR-BM-06 | System shall support batch acceptance by warehouse staff | High | ✅ Done |
| FR-BM-07 | System shall allow batch deletion (admin only) | Medium | ✅ Done |
| FR-BM-08 | System shall print picking lists | High | ✅ Done |
| FR-BM-09 | System shall track print counts and timestamps | Medium | ✅ Done |

### 6.5 Picking Workflow

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-PW-01 | System shall allow batch acceptance via QR scanning | High | ✅ Done |
| FR-PW-02 | System shall support Quick Assign for batch selection | Medium | ✅ Done |
| FR-PW-03 | System shall allow SKU scanning with quantity entry | High | ✅ Done |
| FR-PW-04 | System shall support partial picking (shortage recording) | High | ✅ Done |
| FR-PW-05 | System shall update order line status in real-time | High | ✅ Done |
| FR-PW-06 | System shall track picker name and timestamp | High | ✅ Done |
| FR-PW-07 | System shall prevent duplicate scanning | Medium | ✅ Done |
| FR-PW-08 | System shall validate picked quantity against required | High | ✅ Done |

### 6.6 Shortage Management

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-SM-01 | System shall auto-create shortage records during picking | High | ✅ Done |
| FR-SM-02 | System shall track shortage reasons (out_of_stock, damaged, etc.) | High | ✅ Done |
| FR-SM-03 | System shall support shortage status updates | High | ✅ Done |
| FR-SM-04 | System shall prioritize shortages by urgency | Medium | ✅ Done |
| FR-SM-05 | System shall allow shortage resolution actions | High | ✅ Done |
| FR-SM-06 | System shall display shortage queue to online team | High | ✅ Done |

### 6.7 Dispatch Management

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-DM-01 | System shall allow handover scanning for completed batches | High | ✅ Done |
| FR-DM-02 | System shall auto-generate handover codes (H-YYYYMMDD-NNN) | High | ✅ Done |
| FR-DM-03 | System shall track dispatch status | High | ✅ Done |
| FR-DM-04 | System shall support tracking number entry | High | ✅ Done |
| FR-DM-05 | System shall print handover slips | Medium | ✅ Done |
| FR-DM-06 | System shall record dispatch timestamp and user | High | ✅ Done |

### 6.8 Reporting & Analytics

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-RA-01 | System shall display dashboard with order statistics | High | ✅ Done |
| FR-RA-02 | System shall export dashboard data to Excel | High | ✅ Done |
| FR-RA-03 | System shall show batch progress in list view | High | ✅ Done |
| FR-RA-04 | System shall provide SKU-level progress detail | High | ✅ Done |
| FR-RA-05 | System shall export batch data to Excel | Medium | ✅ Done |
| FR-RA-06 | System shall track all critical actions in audit log | High | ✅ Done |
| FR-RA-07 | System shall support date-based filtering | Medium | ✅ Done |

---

## 7. Non-Functional Requirements

### 7.1 Performance

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-P-01 | Dashboard page load time | < 2 seconds | High |
| NFR-P-02 | QR scan response time | < 1 second | High |
| NFR-P-03 | Batch creation time | < 5 seconds | Medium |
| NFR-P-04 | Excel import processing | < 30 seconds for 1000 rows | Medium |
| NFR-P-05 | Concurrent user support | 50+ simultaneous users | Medium |

### 7.2 Reliability

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-R-01 | System uptime | 99.5% | High |
| NFR-R-02 | Data backup frequency | Daily | High |
| NFR-R-03 | Error recovery | Graceful degradation | High |
| NFR-R-04 | Database integrity | ACID compliance | High |

### 7.3 Usability

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| NFR-U-01 | Mobile responsiveness | Full functionality on smartphones | High |
| NFR-U-02 | Interface language | Thai language support (UTF-8) | High |
| NFR-U-03 | User training time | < 2 hours for new users | Medium |
| NFR-U-04 | Error messages | Clear, actionable messages in Thai | High |

### 7.4 Security

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| NFR-S-01 | Password security | Bcrypt hashing with salt | High |
| NFR-S-02 | Session management | Secure session tokens | High |
| NFR-S-03 | Role-based access control | Enforce permissions at backend | High |
| NFR-S-04 | Audit logging | Log all critical actions with user ID | High |
| NFR-S-05 | SQL injection prevention | Parameterized queries (SQLAlchemy) | High |

### 7.5 Maintainability

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| NFR-M-01 | Code documentation | Inline comments for complex logic | Medium |
| NFR-M-02 | Database migrations | Support schema versioning | Medium |
| NFR-M-03 | Error logging | Centralized error tracking | Medium |
| NFR-M-04 | Code modularity | Separate concerns (models, views, controllers) | High |

### 7.6 Scalability

| ID | Requirement | Description | Priority |
|----|-------------|-------------|----------|
| NFR-SC-01 | Database optimization | Indexed columns for fast queries | High |
| NFR-SC-02 | Horizontal scaling | Support load balancing | Low |
| NFR-SC-03 | Storage capacity | Support 1M+ order records | Medium |

---

## 8. System Architecture

### 8.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  (Browser - Desktop & Mobile)                                │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Flask Web Server                          │   │
│  │  ┌──────────┬──────────┬──────────┬─────────────┐  │   │
│  │  │  Routes  │  Views   │ Business │ Utilities   │  │   │
│  │  │ (app.py) │(templates)│  Logic   │ (utils.py)  │  │   │
│  │  └──────────┴──────────┴──────────┴─────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Access Layer                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SQLAlchemy ORM                          │   │
│  │  (models.py - User, Product, Stock, Order, Batch)   │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer                             │
│                SQLite (data.db)                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        VNIX WMS                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Import     │  │    Batch     │  │   Picking    │      │
│  │   Module     │  │   Module     │  │   Module     │      │
│  │ (importers.py)│ │(allocation.py)│ │ (scan_*.html)│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │               │
│         └────────┬────────┴──────────┬───────┘               │
│                  ▼                   ▼                       │
│         ┌────────────────────────────────────┐              │
│         │     Core Business Logic            │              │
│         │        (app.py)                    │              │
│         └────────────────┬───────────────────┘              │
│                          │                                   │
│         ┌────────────────▼───────────────────┐              │
│         │      Data Models                   │              │
│         │      (models.py)                   │              │
│         │  - User, Shop, Product, Stock      │              │
│         │  - Sales, OrderLine, Batch         │              │
│         │  - AuditLog, ShortageQueue         │              │
│         └────────────────┬───────────────────┘              │
│                          │                                   │
│         ┌────────────────▼───────────────────┐              │
│         │       SQLAlchemy ORM               │              │
│         └────────────────┬───────────────────┘              │
│                          │                                   │
│         ┌────────────────▼───────────────────┐              │
│         │       SQLite Database              │              │
│         └────────────────────────────────────┘              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 8.3 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Order Processing Workflow                  │
└─────────────────────────────────────────────────────────────┘

1. Import Orders
   ┌──────────────┐
   │ Excel Upload │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │Parse & Validate│
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Auto-Classify│
   │ (READY/LOW/  │
   │  SHORTAGE)   │
   └──────┬───────┘
          │
          ▼
2. Create Batch
   ┌──────────────┐
   │ Filter Orders│
   │ (Platform +  │
   │  Date)       │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Run Allocation│
   │ Algorithm    │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │Generate QR + │
   │ Run Number   │
   └──────┬───────┘
          │
          ▼
3. Pick Items
   ┌──────────────┐
   │ Scan Batch QR│
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Scan SKU QR  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Enter Qty    │
   │ (Full/Partial)│
   └──────┬───────┘
          │
          ├─────Yes──► Update Progress
          │
          └─────No───► Record Shortage
                       │
                       ▼
                    ┌──────────────┐
                    │ Add to Queue │
                    └──────────────┘
          │
          ▼
4. Dispatch
   ┌──────────────┐
   │Check Progress│
   │   = 100%     │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Scan Handover│
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │Generate Code │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Print Slip   │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  DISPATCHED  │
   └──────────────┘
```

---

## 9. Data Model

### 9.1 Entity Relationship Diagram (ERD)

```
┌──────────────┐          ┌──────────────┐
│     User     │          │     Shop     │
├──────────────┤          ├──────────────┤
│ id (PK)      │          │ id (PK)      │
│ username     │          │ name         │
│ password     │          │ platform     │
│ department   │◄─────┐   │ created_at   │
│ role         │      │   └──────────────┘
│ created_at   │      │
└──────────────┘      │   ┌──────────────┐
                      │   │   Product    │
┌──────────────┐      │   ├──────────────┤
│  AuditLog    │      │   │ id (PK)      │
├──────────────┤      │   │ sku          │
│ id (PK)      │      │   │ description  │
│ user_id (FK) │──────┘   │ platform     │
│ action       │          │ created_at   │
│ details      │          └──────┬───────┘
│ timestamp    │                 │
└──────────────┘                 │
                                 │
                      ┌──────────▼───────┐
                      │      Stock       │
                      ├──────────────────┤
                      │ id (PK)          │
                      │ product_id (FK)  │◄────┐
                      │ shop_id (FK)     │     │
                      │ shelf            │     │
                      │ quantity         │     │
                      │ updated_at       │     │
                      └──────────────────┘     │
                                               │
┌──────────────┐          ┌──────────────────┐ │
│    Batch     │          │   OrderLine      │ │
├──────────────┤          ├──────────────────┤ │
│ id (PK)      │          │ id (PK)          │ │
│ batch_id     │◄────┐    │ order_number     │ │
│ run_number   │     │    │ platform         │ │
│ status       │     │    │ product_id (FK)  │─┘
│ created_by   │     │    │ batch_id (FK)    │
│ created_at   │     └────│ due_date         │
│ accepted_by  │          │ status           │
│ accepted_at  │          │ allocated_qty    │
└──────────────┘          │ picked_qty       │
                          │ shortage_qty     │
┌──────────────┐          │ picked_at        │
│ShortageQueue │          │ picked_by_user_id│
├──────────────┤          │ dispatch_status  │
│ id (PK)      │          │ dispatched_at    │
│ orderline_id │◄─────────│ tracking_number  │
│ (FK)         │          └──────────────────┘
│ sku          │
│ shortage_qty │
│ reason       │
│ status       │
│ urgency      │
│ created_at   │
│ resolved_at  │
└──────────────┘
```

### 9.2 Database Schema

#### Table: users
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | User ID |
| username | VARCHAR(64) | UNIQUE, NOT NULL | Login username |
| password | VARCHAR(128) | NOT NULL | Hashed password |
| department | VARCHAR(20) | DEFAULT 'online' | 'online' or 'warehouse' |
| role | VARCHAR(20) | DEFAULT 'staff' | 'admin', 'staff', 'picker', 'packer' |
| created_at | DATETIME | NOT NULL | Account creation timestamp |

#### Table: shops
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Shop ID |
| name | VARCHAR(128) | NOT NULL | Shop name |
| platform | VARCHAR(32) | NOT NULL | 'shopee', 'tiktok', 'lazada' |
| created_at | DATETIME | NOT NULL | Shop creation timestamp |

#### Table: products
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Product ID |
| sku | VARCHAR(64) | UNIQUE, NOT NULL | Stock Keeping Unit |
| description | TEXT | | Product description |
| platform | VARCHAR(32) | | Associated platform |
| created_at | DATETIME | NOT NULL | Product creation timestamp |

#### Table: stock
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Stock record ID |
| product_id | INTEGER | FK → products.id | Product reference |
| shop_id | INTEGER | FK → shops.id | Shop reference |
| shelf | VARCHAR(32) | | Shelf location |
| quantity | INTEGER | DEFAULT 0 | Available quantity |
| updated_at | DATETIME | NOT NULL | Last update timestamp |

#### Table: batches
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Batch record ID |
| batch_id | VARCHAR(64) | UNIQUE, NOT NULL | Batch identifier (QR code) |
| run_number | VARCHAR(16) | | Run number (R1, R2...) |
| status | VARCHAR(32) | DEFAULT 'pending' | Batch status |
| created_by_user_id | INTEGER | FK → users.id | Creator |
| created_at | DATETIME | NOT NULL | Creation timestamp |
| accepted_by_user_id | INTEGER | FK → users.id | Picker who accepted |
| accepted_at | DATETIME | | Acceptance timestamp |

#### Table: order_lines
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Order line ID |
| order_number | VARCHAR(128) | NOT NULL | Order number |
| platform | VARCHAR(32) | NOT NULL | Platform name |
| product_id | INTEGER | FK → products.id | Product reference |
| batch_id | INTEGER | FK → batches.id | Assigned batch |
| due_date | DATE | | SLA due date |
| status | VARCHAR(32) | DEFAULT 'pending' | Order status |
| allocated_qty | INTEGER | DEFAULT 0 | Allocated quantity |
| picked_qty | INTEGER | DEFAULT 0 | Picked quantity |
| shortage_qty | INTEGER | DEFAULT 0 | Shortage quantity |
| picked_at | DATETIME | | Pick timestamp |
| picked_by_user_id | INTEGER | FK → users.id | Picker |
| picked_by_username | VARCHAR(64) | | Picker username |
| dispatch_status | VARCHAR(32) | DEFAULT 'pending' | Dispatch status |
| dispatched_at | DATETIME | | Dispatch timestamp |
| dispatched_by_user_id | INTEGER | FK → users.id | Dispatcher |
| tracking_number | VARCHAR(128) | | Tracking number |

#### Table: shortage_queue
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Queue record ID |
| orderline_id | INTEGER | FK → order_lines.id | Order line reference |
| sku | VARCHAR(64) | NOT NULL | Product SKU |
| shortage_qty | INTEGER | NOT NULL | Shortage quantity |
| reason | VARCHAR(64) | | Shortage reason |
| status | VARCHAR(32) | DEFAULT 'waiting_stock' | Resolution status |
| urgency | VARCHAR(16) | DEFAULT 'medium' | Priority level |
| created_at | DATETIME | NOT NULL | Creation timestamp |
| resolved_at | DATETIME | | Resolution timestamp |

#### Table: audit_log
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO_INCREMENT | Log ID |
| user_id | INTEGER | FK → users.id | User who performed action |
| action | VARCHAR(128) | NOT NULL | Action type |
| details | TEXT | | Action details (JSON) |
| timestamp | DATETIME | NOT NULL | Action timestamp |

---

## 10. User Interface Requirements

### 10.1 UI Principles
- **Mobile-first design:** Warehouse staff primarily use mobile devices
- **Minimal clicks:** Each task should require ≤3 clicks
- **Clear visual feedback:** Immediate confirmation for all actions
- **Thai language:** All labels and messages in Thai
- **Color-coded status:** Green (complete), Yellow (in-progress), Red (shortage)

### 10.2 Key Screens

#### 10.2.1 Dashboard
**Purpose:** Overview of order status
**Users:** Online Admin, Online Staff
**Key Elements:**
- Summary cards (Total Orders, Ready, Low Stock, Shortage)
- Filter by platform, date, status
- Export to Excel button
- Navigation to Batch Create

#### 10.2.2 Batch List
**Purpose:** View all batches and progress
**Users:** All users (filtered by role)
**Key Elements:**
- Batch ID, Run Number, Progress %, Status
- Filter by date, platform, status
- Click to view Batch Detail
- Color-coded progress bars

#### 10.2.3 Batch Detail
**Purpose:** SKU-level progress tracking
**Users:** All users
**Key Elements:**
- Batch header (ID, Run, Status, Progress)
- SKU list with quantities (Required, Picked, Shortage)
- Visual progress indicators
- Print buttons (Picking List, QR Codes)

#### 10.2.4 Scan Batch (Mobile)
**Purpose:** Accept batch for picking
**Users:** Picker
**Key Elements:**
- Large QR scanner button
- Manual Batch ID entry
- Quick Assign dropdown
- Confirmation message

#### 10.2.5 Scan SKU (Mobile)
**Purpose:** Pick items and record quantities
**Users:** Picker
**Key Elements:**
- Batch selector
- Large QR scanner button
- Quantity input (number pad)
- Shortage button
- Visual feedback (✓ or ✗)

#### 10.2.6 Scan Handover (Mobile)
**Purpose:** Dispatch completed batches
**Users:** Packer
**Key Elements:**
- Batch QR scanner
- Handover code display
- Print handover slip button
- Confirmation message

#### 10.2.7 Shortage Queue
**Purpose:** Manage out-of-stock items
**Users:** Online Admin, Online Staff (read-only)
**Key Elements:**
- List of shortages with SKU, Qty, Reason
- Status selector (waiting_stock, cancelled, replaced, resolved)
- Urgency indicator
- Filter by status

### 10.3 Responsive Design

| Screen Size | Layout | Priority Elements |
|-------------|--------|-------------------|
| Mobile (< 768px) | Single column, large buttons | Scanner, Qty input, Submit |
| Tablet (768-1024px) | Two columns | List + Detail view |
| Desktop (> 1024px) | Multi-column, sidebar nav | Full dashboard, filters |

---

## 11. Security & Permissions

### 11.1 Authentication
- **Method:** Session-based authentication with Flask sessions
- **Password Policy:**
  - Minimum 8 characters (recommended)
  - Hashed with Werkzeug's generate_password_hash (PBKDF2-SHA256)
- **Session Management:**
  - Secure session cookies
  - Timeout after 24 hours of inactivity

### 11.2 Role-Based Access Control (RBAC)

#### Role Definitions

| Role | Department | Full Access | Limited Access | No Access |
|------|-----------|-------------|----------------|-----------|
| **Online Admin** | Online | Import, User Mgmt, Batch CRUD, Reports, Audit Log | - | - |
| **Online Staff** | Online | Batch Create, View Dashboard, Export (own batches) | - | Import, User Mgmt, Audit Log |
| **Picker** | Warehouse | Scan Batch, Scan SKU, Mark Shortage | Batch List (own only) | Import, Batch Create, Export, Handover |
| **Packer** | Warehouse | Scan Handover, Scan Tracking, Print Handover | Batch List (100% only) | Import, Batch Create, Picking |

### 11.3 Permission Matrix

Refer to [Department-work.md](docs/Department-work.md) for detailed permission matrix.

### 11.4 Audit Logging

**Logged Actions:**
- User login/logout
- Import operations (orders, products, stock)
- Batch create/delete
- Batch acceptance
- SKU picking (with quantities)
- Shortage recording
- Dispatch/handover
- User management actions

**Log Format:**
```json
{
  "user_id": 1,
  "username": "picker1",
  "action": "PICK_SKU",
  "details": {
    "batch_id": "B-20251118-001",
    "sku": "SKU123",
    "qty_picked": 5,
    "qty_required": 5
  },
  "timestamp": "2025-11-18T14:32:15+07:00"
}
```

---

## 12. Integration Requirements

### 12.1 Data Import Formats

#### 12.1.1 Orders Excel Format
| Column | Type | Required | Example | Notes |
|--------|------|----------|---------|-------|
| Order Number | String | ✅ | SO123456 | Unique order ID |
| Platform | String | ✅ | Shopee | shopee/tiktok/lazada |
| SKU | String | ✅ | SKU-001 | Product identifier |
| Quantity | Integer | ✅ | 2 | Ordered quantity |
| Shop Name | String | ✅ | Shop A | Shop identifier |
| Due Date | Date | ❌ | 2025-11-20 | Auto-computed if missing |
| Logistic | String | ❌ | Kerry | Logistics provider |

#### 12.1.2 Products Excel Format
| Column | Type | Required | Example | Notes |
|--------|------|----------|---------|-------|
| SKU | String | ✅ | SKU-001 | Unique product ID |
| Description | String | ✅ | Product Name | Product name/description |
| Platform | String | ❌ | Shopee | Associated platform |

#### 12.1.3 Stock Excel Format
| Column | Type | Required | Example | Notes |
|--------|------|----------|---------|-------|
| SKU | String | ✅ | SKU-001 | Product identifier |
| Shop Name | String | ✅ | Shop A | Shop identifier |
| Shelf | String | ✅ | A-01 | Shelf location |
| Quantity | Integer | ✅ | 100 | Available stock |

### 12.2 Export Formats

#### 12.2.1 Dashboard Export
- **Format:** Excel (.xlsx)
- **Columns:** Order Number, Platform, SKU, Description, Status, Due Date, Allocated Qty

#### 12.2.2 Batch Export
- **Format:** Excel (.xlsx)
- **Columns:** Batch ID, Run Number, SKU, Required Qty, Picked Qty, Shortage Qty, Progress %

### 12.3 QR Code Format

#### Batch QR Code
- **Format:** Text string
- **Content:** `BATCH:{batch_id}`
- **Example:** `BATCH:B-20251118-001`

#### SKU QR Code
- **Format:** Text string
- **Content:** `SKU:{sku}`
- **Example:** `SKU:SKU-001`

#### Order QR Code
- **Format:** Text string
- **Content:** `ORDER:{order_number}`
- **Example:** `ORDER:SO123456`

---

## 13. Success Metrics

### 13.1 Key Performance Indicators (KPIs)

#### Operational Efficiency
| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|--------------------|
| Orders processed per day | 500 | 1,000+ | Daily order count |
| Average picking time per order | 5 min | 3 min | Time from batch accept to complete |
| Batch creation time | 15 min | 5 min | Time from filter to batch created |
| Shortage rate | 15% | <5% | (Shortage orders / Total orders) × 100 |

#### Quality Metrics
| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|--------------------|
| Picking accuracy | 90% | 98% | (Correct picks / Total picks) × 100 |
| On-time dispatch rate | 85% | 95% | (On-time dispatches / Total dispatches) × 100 |
| Stock accuracy | 80% | 95% | (Correct stock counts / Total counts) × 100 |

#### User Adoption
| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Daily active users | 80% of staff | Login records |
| Mobile scanner usage | 90%+ of picks | Scan vs manual entry ratio |
| User satisfaction | 4/5 stars | Post-training survey |

#### System Performance
| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Page load time | <2s | Server logs |
| System uptime | 99.5% | Monitoring tools |
| Error rate | <1% | Error logs |

### 13.2 Success Criteria

**Phase 1 (MVP - Completed):**
- ✅ Core workflows functional (Import → Batch → Pick → Dispatch)
- ✅ QR scanning operational
- ✅ Basic reporting available
- ✅ User authentication working

**Phase 2 (Enhancements - In Progress):**
- 🔄 Role-based permissions implemented
- 🔄 Mobile UI optimized
- 🔄 Performance tuning for 1000+ daily orders
- 🔄 Comprehensive audit logging

**Phase 3 (Scale):**
- ⏳ Multi-warehouse support
- ⏳ API for external integrations
- ⏳ Advanced analytics dashboard
- ⏳ Automated shortage resolution suggestions

---

## 14. Timeline & Milestones

### 14.1 Development Phases

#### Phase 1: MVP (Completed - Nov 2025)
**Duration:** 4 weeks
**Deliverables:**
- ✅ User authentication
- ✅ Import modules (Orders, Products, Stock)
- ✅ Batch creation and allocation
- ✅ Basic picking workflow
- ✅ QR code generation and scanning
- ✅ Dashboard and reporting

#### Phase 2: Enhancements (Current - Nov 2025)
**Duration:** 3 weeks
**Milestones:**
- **Week 1:** Role-based permissions
  - Add department/role fields to User model
  - Implement permission decorators
  - Update UI to show/hide menus by role
- **Week 2:** Mobile optimization
  - Responsive design for scanning pages
  - Large button/input elements
  - Touch-friendly UI
- **Week 3:** Performance & logging
  - Database indexing
  - Comprehensive audit logging
  - Error handling improvements

#### Phase 3: Scale & Integration (Planned - Dec 2025)
**Duration:** 4 weeks
**Planned Features:**
- Multi-warehouse support
- REST API for external systems
- Advanced analytics (charts, trends)
- Automated stock replenishment alerts
- Integration with logistics APIs

### 14.2 Release Schedule

| Version | Release Date | Key Features |
|---------|--------------|--------------|
| v1.0 | 2025-11-01 | MVP launch (core workflows) |
| v2.0 | 2025-11-18 | Role-based permissions, mobile optimization |
| v2.1 | 2025-12-01 | Performance improvements, audit logging |
| v3.0 | 2025-12-15 | Multi-warehouse, API, advanced analytics |

---

## 15. Risks & Mitigation

### 15.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Database corruption** | Low | High | Daily backups, transaction logging, periodic integrity checks |
| **SQLite scalability limits** | Medium | Medium | Monitor performance, plan migration to PostgreSQL if needed |
| **QR scanner compatibility** | Medium | High | Test on multiple devices, provide manual entry fallback |
| **Session timeout during long picks** | Medium | Low | Extend session timeout, auto-refresh tokens |
| **Concurrent edit conflicts** | Medium | Medium | Implement optimistic locking, show conflict warnings |

### 15.2 Operational Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **User training gaps** | High | High | Comprehensive training, video tutorials, quick reference guides |
| **Resistance to change** | Medium | Medium | Involve users early, demonstrate benefits, gradual rollout |
| **Network connectivity in warehouse** | Medium | High | Offline mode for critical actions, sync when online |
| **Printer failures** | High | Medium | Multiple printer stations, digital fallback (show on screen) |
| **Stock data inaccuracy** | High | High | Regular stock audits, highlight discrepancies, easy correction UI |

### 15.3 Business Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Peak season overload** | Medium | High | Load testing, horizontal scaling plan, priority queues |
| **Platform integration changes** | Medium | Medium | Flexible import format, version control for mappings |
| **Staff turnover** | Medium | Medium | Clear documentation, simple UI, buddy training system |

---

## 16. Appendix

### 16.1 Glossary

| Term | Definition |
|------|------------|
| **Batch** | A collection of orders grouped for efficient warehouse picking |
| **Run Number** | Sequential identifier for batches created on the same day (R1, R2, R3...) |
| **SKU** | Stock Keeping Unit - unique product identifier |
| **Allocation** | Process of assigning stock to orders based on availability |
| **Shortage** | Situation where ordered quantity exceeds available stock |
| **Picking** | Warehouse process of collecting items for orders |
| **Dispatch** | Final step of handing over packed orders to logistics |
| **Handover Code** | Unique identifier for dispatch transactions (H-YYYYMMDD-NNN) |
| **SLA** | Service Level Agreement - platform-specific delivery deadlines |
| **BE** | Buddhist Era - Thai calendar system (2568 = 2025 CE) |

### 16.2 Platform-Specific Rules

#### Shopee
- **SLA:** 2 days from order date
- **Platform Code:** "shopee" (case-insensitive)
- **Logistics:** Shopee Express, Kerry, Flash Express

#### TikTok
- **SLA:** 1 day from order date
- **Platform Code:** "tiktok" (case-insensitive)
- **Logistics:** TikTok Shop Logistics, Kerry

#### Lazada
- **SLA:** 3 days from order date
- **Platform Code:** "lazada" (case-insensitive)
- **Logistics:** Lazada Express, J&T, Best Express

### 16.3 Status Definitions

#### Order Status
- `READY_ACCEPT` - Stock available, ready for batch creation
- `LOW_STOCK` - Partial stock available (can partially fulfill)
- `SHORTAGE` - Insufficient or no stock available
- `ALLOCATED` - Assigned to batch
- `PICKING` - Currently being picked
- `PICKED` - Fully picked
- `PARTIAL` - Partially picked with shortage
- `DISPATCHED` - Handed over to logistics

#### Batch Status
- `pending` - Created but not yet accepted
- `in_progress` - Accepted and being picked
- `completed` - All items picked (100% progress)
- `dispatched` - Handed over to logistics

#### Shortage Status
- `waiting_stock` - Awaiting stock replenishment
- `cancelled` - Order cancelled, shortage resolved
- `replaced` - Replaced with alternative SKU
- `resolved` - Issue resolved (e.g., found misplaced stock)

#### Dispatch Status
- `pending` - Not yet dispatched
- `ready` - Ready for dispatch (100% picked)
- `dispatched` - Handed over to logistics

### 16.4 File Structure

```
vnix-wms-main/
├── app.py                    # Main application file
├── models.py                 # Database models (SQLAlchemy)
├── importers.py              # Import logic for Excel files
├── allocation.py             # Order allocation algorithm
├── utils.py                  # Utility functions (dates, SLA, etc.)
├── data.db                   # SQLite database
├── requirements.txt          # Python dependencies
├── PRD.md                    # This document
├── CLAUDE.md                 # Project instructions for AI
├── .gitignore                # Git ignore rules
├── docs/
│   └── Department-work.md    # Department workflow & permissions
├── templates/                # HTML templates (Jinja2)
│   ├── base.html             # Base layout
│   ├── login.html            # Login page
│   ├── dashboard.html        # Order overview
│   ├── batch_create.html     # Batch creation form
│   ├── batch_list.html       # Batch listing
│   ├── batch_detail.html     # Batch detail view
│   ├── scan_batch.html       # Batch scanning (mobile)
│   ├── scan_sku.html         # SKU scanning (mobile)
│   ├── scan_handover.html    # Handover scanning (mobile)
│   ├── scan_tracking.html    # Tracking number entry
│   ├── shortage_queue.html   # Shortage management
│   ├── users.html            # User management
│   ├── import_*.html         # Import pages
│   └── *_print.html          # Print templates
├── migrations/               # Database migration scripts
└── __pycache__/              # Python cache (ignored by git)
```

### 16.5 Key Dependencies

```
Flask==2.3.0              # Web framework
SQLAlchemy==2.0.0         # ORM
pandas==2.0.0             # Data processing
qrcode==7.4.2             # QR code generation
Pillow==10.0.0            # Image processing
Werkzeug==2.3.0           # Password hashing
openpyxl==3.1.0           # Excel file handling
pytz==2023.3              # Timezone support
```

### 16.6 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application display name | "VNIX Order Management" |
| `SECRET_KEY` | Flask session secret key | "vnix-secret" |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | "sqlite:///data.db" |

### 16.7 API Endpoints (Internal)

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/` | GET | Redirect to dashboard | No |
| `/login` | GET, POST | User login | No |
| `/logout` | GET | User logout | Yes |
| `/dashboard` | GET | Order overview | Yes |
| `/import/orders` | GET, POST | Import orders | Yes (Admin) |
| `/import/products` | GET, POST | Import products | Yes (Admin) |
| `/import/stock` | GET, POST | Import stock | Yes (Admin) |
| `/batch/create` | GET, POST | Create batch | Yes |
| `/batch/list` | GET | List batches | Yes |
| `/batch/<id>` | GET | Batch detail | Yes |
| `/batch/<id>/delete` | POST | Delete batch | Yes (Admin) |
| `/scan/batch` | GET, POST | Scan batch QR | Yes (Picker) |
| `/scan/sku` | GET, POST | Scan SKU QR | Yes (Picker) |
| `/scan/handover` | GET, POST | Scan handover | Yes (Packer) |
| `/scan/tracking` | GET, POST | Enter tracking | Yes (Packer) |
| `/shortage/queue` | GET | View shortages | Yes |
| `/users` | GET, POST | User management | Yes (Admin) |
| `/api/quick_assign` | GET | Quick assign data | Yes |

### 16.8 Testing Scenarios

#### 16.8.1 Import Testing
- ✅ Import valid orders/products/stock Excel
- ✅ Reject invalid file formats
- ✅ Handle missing required columns
- ✅ Handle duplicate SKUs/orders
- ✅ Validate data types (e.g., qty must be integer)

#### 16.8.2 Batch Creation Testing
- ✅ Create batch with READY orders
- ✅ Prevent batch creation with SHORTAGE orders
- ✅ Auto-generate sequential run numbers
- ✅ Filter by platform and date correctly
- ✅ Generate unique batch QR codes

#### 16.8.3 Picking Workflow Testing
- ✅ Accept batch via QR scan
- ✅ Accept batch via Quick Assign
- ✅ Pick full quantity (complete)
- ✅ Pick partial quantity (shortage)
- ✅ Prevent picking more than required
- ✅ Update progress in real-time
- ✅ Create shortage queue entries

#### 16.8.4 Dispatch Testing
- ✅ Filter batches with 100% progress
- ✅ Generate handover code
- ✅ Assign tracking numbers
- ✅ Print handover slip
- ✅ Mark batch as DISPATCHED

#### 16.8.5 Permission Testing
- ✅ Online Admin can access all pages
- ✅ Online Staff cannot import data
- ✅ Picker can scan batch/SKU
- ✅ Picker cannot create batches
- ✅ Packer can scan handover
- ✅ Packer cannot scan SKU

### 16.9 References

- [Department Workflow Guide](docs/Department-work.md)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [Pandas Documentation](https://pandas.pydata.org/)

### 16.10 Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-11-01 | Initial PRD for MVP | VNIX Team |
| 2.0 | 2025-11-18 | Updated with role-based permissions, expanded functional requirements | VNIX Team |

### 16.11 Document Approvals

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| QA Lead | | | |
| Operations Manager | | | |

---

## 📞 Contact & Support

**For questions about this PRD:**
- **Email:** support@vnix.com
- **Line:** @vnixsupport
- **GitHub:** https://github.com/tetipong2542/vnix-wms

**For feature requests:**
- Create an issue on GitHub
- Email product team with "[FEATURE REQUEST]" in subject

**For bug reports:**
- Create an issue on GitHub with detailed steps to reproduce
- Include screenshots and error messages

---

**Document Status:** ✅ Active
**Next Review Date:** 2025-12-01
**Maintained By:** VNIX Development Team

---

*This PRD is a living document and will be updated as the product evolves.*
