# VNIX WMS - Complete System Workflow

> **Comprehensive Mermaid Flowchart Documentation**
> Version: 2.0
> Last Updated: 2025-01-20
> Author: Claude Code

---

## 🎯 System Overview

VNIX WMS เป็นระบบ Warehouse Management System ที่ออกแบบมาเพื่อจัดการสต็อกสินค้า การหยิบสินค้า และการส่งมอบให้ขนส่งอย่างมีประสิทธิภาพ โดยมีการบูรณาการกับระบบ SBS (Smart Business Solution) และรองรับหลาย Platform (Shopee, Lazada, TikTok, Website)

### Core Features:
- ✅ Multi-Platform Order Management
- ✅ SLA-Based Batch Creation (Priority Queue)
- ✅ PRE-PICK & POST-PICK Shortage Detection
- ✅ Parent-Child Batch System (Auto Split)
- ✅ Banking-Style Stock Transaction Ledger
- ✅ Handover Code System
- ✅ Real-time Stock Reservation
- ✅ Analytics Dashboard (Pre-pick vs Post-pick Problems)

### User Roles:
- **Admin**: Full access (User management, Import, Batch creation, Reports, Analytics)
- **Picker**: Limited access (Scanning, Picking, Shortage marking)
- **Supervisor/Online**: Shortage Queue management, Resolution actions

---

## 📊 Complete System Workflow

```mermaid
---
config:
  layout: elk
  theme: default
---
flowchart TB
    %% ========================================
    %% ACTORS & SYSTEM OVERVIEW
    %% ========================================

    CEO(("👨‍💼 ผู้บริหาร<br>(Boss/Pam)"))
    ADMIN{{"👤 Admin User<br>(Boo/Porn)"}}
    PICKER{{"👤 Picker<br>(Warehouse Staff)"}}
    ONLINE{{"👤 Online/Supervisor<br>(Customer Service)"}}
    SBS[("💾 SBS System<br>(Smart Business Solution)")]

    VISION@{ label: "🎯 เป้าหมายหลัก:<br>1. ส่งของตรงเวลา (SLA)<br>2. สต็อกแม่น 100%<br>3. รู้ปัญหาชัด: ระบบ vs คน<br>4. Trace ได้ทุกการเปลี่ยนแปลง" }

    %% ========================================
    %% LAYER 0: AUTHENTICATION & AUTHORIZATION
    %% ========================================

    subgraph AUTH["🔐 Layer 0: Authentication & User Management"]
        direction TB

        LOGIN["📱 /login<br>Login Page"]
        LOGIN_POST["🔑 POST /login<br>Verify credentials"]

        SESSION{"✅ Session Valid?"}

        ROLE_CHECK{"👤 User Role?"}
        ADMIN_ACCESS["✅ Admin Access<br>- All features<br>- User management<br>- System config"]
        PICKER_ACCESS["✅ Picker Access<br>- Scan pages<br>- Mark shortage<br>- Limited views"]
        USER_ACCESS["✅ User Access<br>- View batches<br>- Reports<br>- No edit"]

        USER_MGMT["👥 /admin/users<br>Create/Edit Users<br>Set Roles & Permissions"]
        LOGOUT["🚪 /logout<br>End Session"]
    end

    %% ========================================
    %% LAYER 1: DATA INPUT (INBOUND)
    %% ========================================

    subgraph INBOUND["📥 Layer 1: Data Input & Stock Receiving (Inbound)"]
        direction TB

        %% Physical Receiving Process
        subgraph PHYSICAL_RECEIVE["🚚 ส่วนที่ 1: การรับของเข้าคลังจริง (Physical Inbound - ฝั่ง SBS)"]
            direction LR

            GOODS_ARRIVE["🚚 ของเข้าคลัง<br>(Supplier/Transfer)"]
            COUNT_CHECK{"📦 นับจำนวน<br>สินค้า"}

            SMALL_QTY["< 10 ชิ้น<br>→ พี่บู (Boo)<br>ยิงบาร์โค้ดรับเข้า SBS"]
            LARGE_QTY["> 10 ชิ้น<br>→ พี่พร (Porn)<br>ยิงมือรับเข้า SBS"]

            SBS_UPDATE["✅ SBS อัปเดต<br>stock_real_sbs<br>(Real-time)"]
        end

        %% WMS Data Import
        subgraph WMS_IMPORT["💾 ส่วนที่ 2: การนำเข้าข้อมูลสู่ WMS"]
            direction TB

            %% Order Import
            ORDER_IMPORT["📦 /import/orders<br>นำเข้า Order จาก Platforms<br>(Excel/CSV)"]
            ORDER_PARSE["🔍 Parse Order Data:<br>- order_id, sku, qty<br>- platform, shop<br>- order_time, logistic_type<br>- carrier (SPX/Flash/LEX/J&T)"]
            ORDER_SLA["⏱ คำนวณ SLA Date:<br>order_time + platform_sla_days<br>→ sla_date per OrderLine"]
            ORDER_SAVE["💾 Save to order_lines table<br>status: pending_batch"]

            %% Product Import
            PRODUCT_IMPORT["📋 /import/products<br>นำเข้า Product Master<br>(SKU, Brand, Model)"]

            %% Stock Import
            STOCK_IMPORT["📊 /import/stock<br>นำเข้า Stock จาก SBS<br>(Excel: SKU, Qty)"]
            STOCK_PARSE["🔍 Parse Stock Data:<br>sku, qty (real stock from SBS)"]
            STOCK_UPDATE["💾 Update stocks table:<br>- stock.qty = new_qty<br>- stock.updated_at = now()"]
            STOCK_TX_RECEIVE["📘 Transaction Log:<br>type: RECEIVE<br>reason: IMPORT_FROM_SBS<br>qty: +amount<br>balance_after: new_qty"]

            %% Sales Import
            SALES_IMPORT["🧾 /import/sales<br>นำเข้า Sales Order<br>(PO tracking)"]
        end

        GOODS_ARRIVE --> COUNT_CHECK
        COUNT_CHECK -- "< 10 ชิ้น" --> SMALL_QTY
        COUNT_CHECK -- "> 10 ชิ้น" --> LARGE_QTY
        SMALL_QTY --> SBS_UPDATE
        LARGE_QTY --> SBS_UPDATE

        SBS_UPDATE -.->|"รอบเช้า/บ่าย<br>Export Stock File"| STOCK_IMPORT

        ORDER_IMPORT --> ORDER_PARSE --> ORDER_SLA --> ORDER_SAVE
        PRODUCT_IMPORT --> ORDER_SAVE
        STOCK_IMPORT --> STOCK_PARSE --> STOCK_UPDATE --> STOCK_TX_RECEIVE
        SALES_IMPORT --> ORDER_SAVE
    end

    %% ========================================
    %% LAYER 2: STOCK ALLOCATION & RESERVATION
    %% ========================================

    subgraph ALLOCATION["🎯 Layer 2: Stock Allocation & Reservation (SLA-Based Priority)"]
        direction TB

        DASHBOARD["📊 / (Dashboard)<br>แสดงภาพรวม:<br>- Orders pending_batch<br>- Stock levels<br>- SLA warnings<br>- Today's batches"]

        BATCH_LIST["📋 /batch/list<br>รายการ Batch ทั้งหมด<br>Filter by: platform, date, status"]

        BATCH_CREATE_PAGE["➕ /batch/create<br>สร้าง Batch ใหม่<br>เลือก Platform & Date"]

        BATCH_CREATE_LOGIC["🧮 Batch Creation Logic:<br>1️⃣ ดึง Orders ที่ batch_status='pending_batch'<br>2️⃣ คำนวณ available = stock_total - reserved<br>3️⃣ จัดลำดับตาม SLA (เร็วที่สุดก่อน)<br>4️⃣ ตรวจสอบสต็อกพอหรือไม่"]

        STOCK_CHECK{"💡 Stock Check<br>per SKU"}

        AVAILABLE["✅ สต็อกพอ<br>(available >= required)"]
        PRE_PICK_SHORTAGE["❌ สต็อกไม่พอ<br>(available < required)"]

        RESERVE_STOCK["🔒 Reserve Stock:<br>stock.reserved_qty += qty<br>orderline.batch_status = 'batched'<br>orderline.batch_id = batch_id"]

        RESERVE_TX["📘 Transaction Log:<br>type: RESERVE<br>reason: BATCH_RESERVE<br>qty: -amount<br>reference: batch_id"]

        CREATE_SHORTAGE_PRE["⚠️ สร้าง Shortage Record:<br>type: PRE_PICK<br>status: waiting_stock<br>reason: STOCK_NOT_AVAILABLE<br>qty_shortage = required - available"]

        SHORTAGE_TX_PRE["📘 Transaction Log:<br>type: RESERVE_FAILED<br>reason: BATCH_RESERVE_FAILED<br>reference: shortage_id"]

        READY_TO_PICK["✅ Order Status:<br>ready_to_pick<br>(มีสต็อก พร้อมหยิบ)"]

        WAITING_STOCK["⏳ Order Status:<br>waiting_stock<br>(ไม่มีสต็อก รอของเข้า)"]

        BATCH_CREATED{"🎉 Batch Created?"}

        BATCH_SUCCESS["✅ Batch สร้างสำเร็จ<br>batch_id: {platform}-{date}-R{run}<br>locked: true<br>total_orders, carrier_counts"]

        BATCH_FAIL@{ label: "❌ ไม่มี Order ที่ ready_to_pick<br>= ปัญหา PRE-PICK ทั้งหมด<br>ไม่สามารถสร้าง Batch ได้" }

        QUICK_CREATE["⚡ /batch/quick-create/{platform}<br>สร้าง Batch แบบเร็ว (API)"]

        DASHBOARD --> BATCH_LIST
        BATCH_LIST --> BATCH_CREATE_PAGE
        BATCH_CREATE_PAGE --> BATCH_CREATE_LOGIC
        QUICK_CREATE --> BATCH_CREATE_LOGIC

        BATCH_CREATE_LOGIC --> STOCK_CHECK

        STOCK_CHECK -- "พอ" --> AVAILABLE
        STOCK_CHECK -- "ไม่พอ" --> PRE_PICK_SHORTAGE

        AVAILABLE --> RESERVE_STOCK --> RESERVE_TX --> READY_TO_PICK
        PRE_PICK_SHORTAGE --> CREATE_SHORTAGE_PRE --> SHORTAGE_TX_PRE --> WAITING_STOCK

        READY_TO_PICK --> BATCH_CREATED
        WAITING_STOCK --> BATCH_CREATED

        BATCH_CREATED -- "มี Order พอ" --> BATCH_SUCCESS
        BATCH_CREATED -- "ไม่มีเลย" --> BATCH_FAIL
    end

    %% ========================================
    %% LAYER 3: BATCH MANAGEMENT & REPORTS
    %% ========================================

    subgraph BATCH_MGMT["📦 Layer 3: Batch Management & Printing"]
        direction TB

        BATCH_DETAIL["📄 /batch/{batch_id}<br>Batch Detail Page:<br>- Order list<br>- SKU summary<br>- Carrier breakdown<br>- Shop summary<br>- Print buttons"]

        BATCH_SUMMARY["📊 /batch/{batch_id}/summary<br>Batch Summary (Modal)<br>Quick stats view"]

        BATCH_FAMILY["🔗 /api/batch/{batch_id}/family<br>Get Parent-Child Batch Tree<br>(for Auto-Split batches)"]

        %% Printing & Reports
        subgraph PRINT_REPORTS["🖨️ Printing & Export"]
            direction LR

            PRINT_WAREHOUSE["📋 /batch/{batch_id}/print-warehouse<br>พิมพ์ใบสั่งงานคลัง<br>(Warehouse Job Sheet)<br>รายชื่อ Order ทั้งหมด"]

            PRINT_PICKING["📝 /batch/{batch_id}/print-picking<br>พิมพ์ใบหยิบสินค้า<br>(Picking List)<br>รายการ SKU + Qty"]

            PRINT_SKU_QR["📱 /batch/{batch_id}/print-sku-qr<br>พิมพ์ QR Code ทุก SKU<br>สำหรับสแกนหยิบของ"]

            PRINT_HANDOVER["🎫 /batch/{batch_id}/print-handover<br>พิมพ์ใบส่งมอบ Handover<br>Handover Code + Batch Info"]

            EXPORT_EXCEL["📊 /batch/{batch_id}/export.xlsx<br>Export Batch to Excel<br>รายละเอียดทุก Order"]
        end

        %% Handover Code System
        subgraph HANDOVER_SYSTEM["🎫 Handover Code System (Batch Completion)"]
            direction TB

            GEN_HANDOVER["🔢 /api/batch/{batch_id}/generate-handover-code<br>สร้าง Handover Code<br>Format: BH-{date}-{sequence}<br>เช่น BH-20251120-001"]

            HANDOVER_GENERATED["✅ Handover Code Generated:<br>- batch.handover_code<br>- batch.handover_code_generated_at<br>- batch.handover_code_generated_by"]

            SCAN_HANDOVER_PAGE["📱 /scan-handover<br>หน้าสแกน Handover Code<br>เพื่อยืนยันส่งมอบให้ขนส่ง"]

            VERIFY_HANDOVER["🔍 /api/handover/verify<br>ตรวจสอบ Handover Code<br>→ ดึงข้อมูล Batch + Family"]

            CONFIRM_HANDOVER["✅ /api/handover/confirm<br>ยืนยันส่งมอบ Handover:<br>- batch.handover_confirmed = true<br>- batch.handover_confirmed_at<br>- batch.handover_confirmed_by<br>- batch.handover_notes"]

            HANDOVER_COMPLETE["🎉 Handover สำเร็จ:<br>Batch พร้อมส่งมอบขนส่ง<br>ปล่อย Reserved Stock"]

            RELEASE_RESERVED["🔓 Release Reserved Stock:<br>stock.reserved_qty -= qty<br>(เมื่อส่งมอบเรียบร้อย)"]

            RELEASE_TX["📘 Transaction Log:<br>type: RELEASE<br>reason: HANDOVER_RELEASE<br>qty: +amount (คืนสต็อก)<br>reference: batch_id"]
        end

        %% Auto-Split for Shortage Batches
        AUTO_SPLIT["✂️ /api/batch/{batch_id}/auto-split<br>แยก Batch อัตโนมัติ:<br>- Parent Batch (completed items)<br>- Child Batch (shortage items)<br>sub_batch_number: 1-5"]

        BATCH_DETAIL --> BATCH_SUMMARY
        BATCH_DETAIL --> BATCH_FAMILY
        BATCH_DETAIL --> PRINT_WAREHOUSE
        BATCH_DETAIL --> PRINT_PICKING
        BATCH_DETAIL --> PRINT_SKU_QR
        BATCH_DETAIL --> PRINT_HANDOVER
        BATCH_DETAIL --> EXPORT_EXCEL
        BATCH_DETAIL --> GEN_HANDOVER
        BATCH_DETAIL --> AUTO_SPLIT

        GEN_HANDOVER --> HANDOVER_GENERATED
        HANDOVER_GENERATED --> SCAN_HANDOVER_PAGE
        SCAN_HANDOVER_PAGE --> VERIFY_HANDOVER
        VERIFY_HANDOVER --> CONFIRM_HANDOVER
        CONFIRM_HANDOVER --> HANDOVER_COMPLETE
        HANDOVER_COMPLETE --> RELEASE_RESERVED --> RELEASE_TX
    end

    %% ========================================
    %% LAYER 4: PICKING PROCESS
    %% ========================================

    subgraph PICKING["📦 Layer 4: Picking Process (Warehouse Operations)"]
        direction TB

        SCAN_BATCH_PAGE["📱 /scan/batch<br>สแกน Batch เพื่อเริ่มหยิบ"]

        SCAN_BATCH_API["🔍 /api/scan/batch<br>Verify Batch exists & locked<br>→ Redirect to /scan/sku"]

        SCAN_SKU_PAGE["📱 /scan/sku<br>หน้าหยิบสินค้าหลัก<br>แสดง SKU ที่ต้องหยิบ:<br>- SKU Code<br>- Product Name<br>- Required Qty<br>- Picked Qty<br>- Remaining"]

        SKU_LIST["📋 /api/quick-assign/skus<br>ดึงรายการ SKU ใน Batch<br>เรียงตาม Priority/ตำแหน่ง"]

        SCAN_SKU_API["📱 /api/scan/sku<br>สแกน SKU Barcode<br>เพื่อเริ่มหยิบ SKU นี้"]

        SKU_VERIFIED["✅ SKU Verified:<br>แสดงข้อมูล SKU<br>+ ปุ่มยืนยันหยิบ<br>+ ปุ่มแจ้ง Shortage"]

        PICK_DECISION{"🤔 Picker<br>หยิบของได้ไหม?"}

        %% Full Pick Path
        PICK_FULL["✅ หยิบครบ<br>กดปุ่ม 'ยืนยันการหยิบ'"]

        PICK_API["✅ /api/pick/sku<br>บันทึกการหยิบ:<br>- orderline.picked_qty = qty<br>- orderline.picked_at = now()<br>- orderline.picked_by_user<br>- orderline.dispatch_status = 'ready'"]

        PICK_TX["📘 Transaction Log:<br>type: PICK<br>reason: PICKING_COMPLETED<br>qty: -amount<br>reference: order_line_id"]

        PICK_SUCCESS["🎉 หยิบ SKU สำเร็จ<br>ไปหยิบ SKU ถัดไป"]

        %% Partial/No Pick Path (POST-PICK Shortage)
        MARK_SHORTAGE["⚠️ หยิบได้ไม่ครบ / หาไม่เจอ<br>กดปุ่ม 'สินค้าขาด'"]

        SHORTAGE_FORM["📝 กรอกข้อมูล Shortage:<br>- จำนวนที่หยิบได้จริง<br>- เหตุผล (Reason Code)<br>- หมายเหตุเพิ่มเติม"]

        REASON_CODES@{ label: "📋 Reason Codes (POST-PICK):<br>• CANT_FIND - หาไม่เจอในคลัง<br>• FOUND_DAMAGED - ของชำรุด/เสียหาย<br>• MISPLACED - วางผิดที่/หลงช่อง<br>• BARCODE_MISSING - บาร์โค้ดหลุด/ไม่มี<br>• STOCK_NOT_FOUND - ไม่มีในระบบ<br>• OTHER - อื่นๆ" }

        SHORTAGE_API["⚠️ /api/shortage/mark<br>บันทึก Shortage:<br>- Create shortage_queue record<br>- type: POST_PICK<br>- status: pending<br>- shortage_reason<br>- notes from picker<br>- orderline.shortage_qty"]

        SHORTAGE_TX_POST["📘 Transaction Log:<br>type: DAMAGE / ADJUST<br>reason: {reason_code}<br>qty: -shortage_qty<br>reference: shortage_id"]

        SHORTAGE_CREATED_POST["⚠️ Shortage Record สร้างแล้ว:<br>เข้าคิว Shortage Queue<br>รอ Online จัดการ"]

        BATCH_CHECK{"✅ ทุก SKU ใน Batch<br>หยิบเสร็จหรือยัง?"}

        CONTINUE_PICK["⏭️ ยังไม่เสร็จ<br>หยิบ SKU ถัดไป"]

        BATCH_COMPLETE["🎉 Batch หยิบเสร็จทั้งหมด<br>พร้อมสร้าง Handover Code"]

        SCAN_BATCH_PAGE --> SCAN_BATCH_API
        SCAN_BATCH_API --> SCAN_SKU_PAGE
        SCAN_SKU_PAGE --> SKU_LIST
        SCAN_SKU_PAGE --> SCAN_SKU_API
        SCAN_SKU_API --> SKU_VERIFIED
        SKU_VERIFIED --> PICK_DECISION

        PICK_DECISION -- "หยิบครบ" --> PICK_FULL
        PICK_FULL --> PICK_API --> PICK_TX --> PICK_SUCCESS

        PICK_DECISION -- "หยิบไม่ครบ/หาไม่เจอ" --> MARK_SHORTAGE
        MARK_SHORTAGE --> SHORTAGE_FORM
        SHORTAGE_FORM -.->|"อ้างอิง"| REASON_CODES
        SHORTAGE_FORM --> SHORTAGE_API
        SHORTAGE_API --> SHORTAGE_TX_POST --> SHORTAGE_CREATED_POST

        PICK_SUCCESS --> BATCH_CHECK
        SHORTAGE_CREATED_POST --> BATCH_CHECK

        BATCH_CHECK -- "ยังไม่เสร็จ" --> CONTINUE_PICK
        CONTINUE_PICK --> SCAN_SKU_PAGE

        BATCH_CHECK -- "เสร็จแล้ว" --> BATCH_COMPLETE
    end

    %% ========================================
    %% LAYER 5: SHORTAGE QUEUE MANAGEMENT
    %% ========================================

    subgraph SHORTAGE_MGMT["⚠️ Layer 5: Shortage Queue Management (Online/Supervisor)"]
        direction TB

        SHORTAGE_QUEUE_PAGE["📋 /shortage-queue<br>หน้า Shortage Queue<br>แสดงทุกเคส Shortage:<br>- PRE_PICK + POST_PICK<br>- Status, Reason, SLA<br>- Action buttons"]

        SHORTAGE_API_LIST["🔍 /api/shortage/queue<br>ดึงรายการ Shortage<br>Filter by: status, type, reason, sku, date"]

        SHORTAGE_DETAIL["📄 /api/shortage/order-details<br>ดึงข้อมูล Order ที่เกี่ยวข้อง<br>เพื่อตัดสินใจ"]

        SHORTAGE_ACTION_CHOOSE{"🤔 Online/Supervisor<br>จะจัดการ Shortage อย่างไร?"}

        %% Action 1: Wait Stock
        ACTION_WAIT["⏳ รอของเข้า (Wait Stock)<br>เมื่อรู้ว่าของจะเข้าเร็วๆ นี้"]

        ACTION_WAIT_API["🕒 /api/shortage/action<br>action: wait_stock<br>status → waiting_stock<br>ผูกกับ Import รอบถัดไป"]

        WAIT_RESULT["⏳ Shortage รอของเข้า:<br>จะตรวจสอบอีกครั้งเมื่อ<br>Stock Import รอบหน้า"]

        %% Action 2: Cancel Order
        ACTION_CANCEL["❌ ยกเลิก Order / ลดจำนวน<br>แจ้งลูกค้า ขอโทษ"]

        ACTION_CANCEL_API["❌ /api/shortage/action<br>action: cancel<br>status → cancelled<br>orderline.qty → ปรับลด"]

        CANCEL_TX["📘 Transaction Log:<br>type: ADJUST<br>reason: ORDER_CANCELLED<br>qty: -shortage_qty<br>reference: shortage_id"]

        CANCEL_RESULT["❌ Shortage ยกเลิกแล้ว:<br>ไม่ต้องส่งของนี้<br>แจ้งลูกค้าเรียบร้อย"]

        %% Action 3: Replace SKU
        ACTION_REPLACE["🔄 แทน SKU อื่น<br>ส่งสินค้าทดแทน"]

        ACTION_REPLACE_API["🔄 /api/shortage/action<br>action: replace_sku<br>replacement_sku = new_sku<br>status → replaced"]

        REPLACE_RESULT["🔄 Shortage แทนด้วย SKU ใหม่:<br>สร้าง Order ใหม่<br>หยิบ SKU ทดแทน"]

        %% Action 4: Contact Customer
        ACTION_CONTACT["📞 ติดต่อลูกค้า<br>เพื่อหาทางออก"]

        ACTION_CONTACT_API["📞 /api/shortage/action<br>action: contact_customer<br>resolution_notes = details"]

        %% Action 5: Partial Ship
        ACTION_PARTIAL["📦 ส่งบางส่วน<br>ส่งเท่าที่หยิบได้"]

        ACTION_PARTIAL_API["📦 /api/shortage/action<br>action: partial_ship<br>orderline.qty → ปรับเป็น picked_qty<br>status → resolved"]

        PARTIAL_TX["📘 Transaction Log:<br>type: ADJUST<br>reason: PARTIAL_SHIP<br>qty: -(required - picked)"]

        PARTIAL_RESULT["📦 ส่งบางส่วนแล้ว:<br>ลูกค้าได้รับเท่าที่มี<br>คืนเงินส่วนต่าง"]

        %% Action 6: Fix System/Operation Error
        ACTION_FIX["🔧 แก้ไขข้อมูล/ระบบ<br>เช่น Barcode ผิด, SKU mapping ผิด"]

        ACTION_FIX_API["🔧 /api/shortage/action<br>action: fix_error<br>แก้ไขข้อมูล + ลบ Shortage"]

        FIX_RESULT["✅ แก้ไขข้อมูลแล้ว:<br>ไม่ใช่ Shortage จริง<br>ปิดเคสไป"]

        %% Bulk Actions
        BULK_ACTION["⚡ /api/shortage/bulk-action<br>จัดการหลาย Shortage พร้อมกัน<br>(เลือกหลาย checkbox)"]

        QUICK_ACTION["⚡ /api/shortage/quick-action<br>Quick Action (1 คลิก)<br>สำหรับเคสที่ตัดสินใจง่าย"]

        UPDATE_SHORTAGE["✏️ /api/shortage/update<br>อัปเดตข้อมูล Shortage<br>(Notes, Resolution details)"]

        CHANGE_STATUS["🔄 /api/shortage/change-status<br>เปลี่ยนสถานะ Shortage<br>manually"]

        EXPORT_SHORTAGE["📊 /api/shortage/export-excel<br>Export Shortage Queue to Excel<br>สำหรับวิเคราะห์/รายงาน"]

        SHORTAGE_RESOLVED["✅ Shortage Resolved:<br>status → resolved<br>resolved_at, resolved_by"]

        SHORTAGE_QUEUE_PAGE --> SHORTAGE_API_LIST
        SHORTAGE_QUEUE_PAGE --> SHORTAGE_DETAIL
        SHORTAGE_QUEUE_PAGE --> SHORTAGE_ACTION_CHOOSE
        SHORTAGE_QUEUE_PAGE --> BULK_ACTION
        SHORTAGE_QUEUE_PAGE --> QUICK_ACTION
        SHORTAGE_QUEUE_PAGE --> UPDATE_SHORTAGE
        SHORTAGE_QUEUE_PAGE --> CHANGE_STATUS
        SHORTAGE_QUEUE_PAGE --> EXPORT_SHORTAGE

        SHORTAGE_ACTION_CHOOSE -- "รอของเข้า" --> ACTION_WAIT
        ACTION_WAIT --> ACTION_WAIT_API --> WAIT_RESULT

        SHORTAGE_ACTION_CHOOSE -- "ยกเลิก" --> ACTION_CANCEL
        ACTION_CANCEL --> ACTION_CANCEL_API --> CANCEL_TX --> CANCEL_RESULT

        SHORTAGE_ACTION_CHOOSE -- "แทน SKU" --> ACTION_REPLACE
        ACTION_REPLACE --> ACTION_REPLACE_API --> REPLACE_RESULT

        SHORTAGE_ACTION_CHOOSE -- "ติดต่อลูกค้า" --> ACTION_CONTACT
        ACTION_CONTACT --> ACTION_CONTACT_API

        SHORTAGE_ACTION_CHOOSE -- "ส่งบางส่วน" --> ACTION_PARTIAL
        ACTION_PARTIAL --> ACTION_PARTIAL_API --> PARTIAL_TX --> PARTIAL_RESULT

        SHORTAGE_ACTION_CHOOSE -- "แก้ไขระบบ" --> ACTION_FIX
        ACTION_FIX --> ACTION_FIX_API --> FIX_RESULT

        CANCEL_RESULT --> SHORTAGE_RESOLVED
        REPLACE_RESULT --> SHORTAGE_RESOLVED
        PARTIAL_RESULT --> SHORTAGE_RESOLVED
        FIX_RESULT --> SHORTAGE_RESOLVED
    end

    %% ========================================
    %% LAYER 6: DISPATCH (OUTBOUND)
    %% ========================================

    subgraph DISPATCH["🚚 Layer 6: Dispatch & Tracking (Outbound)"]
        direction TB

        SCAN_TRACKING_PAGE["📱 /scan/tracking<br>หน้าสแกน Tracking Number<br>เพื่อยืนยันการส่งมอบขนส่ง"]

        SCAN_TRACKING_API["📱 /api/scan/tracking<br>สแกน Tracking Number:<br>- ค้นหา Order จาก tracking<br>- แสดงรายละเอียด Order<br>- ยืนยันส่งมอบ"]

        CONFIRM_DISPATCH["✅ /api/confirm-dispatch<br>ยืนยันส่งมอบขนส่ง:<br>- orderline.dispatch_status = 'dispatched'<br>- orderline.dispatched_at = now()<br>- orderline.dispatched_by_user"]

        DISPATCH_COMPLETE["🎉 Dispatch สำเร็จ:<br>Order ส่งมอบขนส่งแล้ว<br>รอขนส่งมารับของ"]

        %% SBS Stock Deduction
        subgraph SBS_OUTBOUND["💾 การตัดสต็อกจาก SBS (Optional)"]
            direction LR

            SBS_NEEDED{"📋 ต้องยิง SBS<br>เพื่อตัดสต็อกจริงไหม?"}

            HAS_SN{"🔢 สินค้านี้มี<br>Serial Number (S/N)?"}

            SN_EXISTS["✅ มี S/N อยู่แล้ว<br>→ ยิง S/N ที่ติดมากับสินค้า"]

            SN_CREATE["🏷️ ยังไม่มี S/N<br>→ พี่พร (Porn) ติด S/N ให้<br>ก่อนยิงออก"]

            SN_SCAN["📱 ยิง S/N ใหม่ที่ติดแล้ว<br>ใน SBS"]

            SBS_DEDUCT["✅ SBS ตัดสต็อกแล้ว:<br>stock_real_sbs -= qty"]

            SBS_SKIP["⏭️ ไม่ต้องตัด SBS<br>(บางกรณีทดลอง/ไม่ผูก)"]
        end

        MOVEMENT_TX["📘 Transaction Log (Optional):<br>type: MOVEMENT_OUT_FROM_SBS<br>reason: DISPATCHED_TO_CUSTOMER<br>qty: -amount<br>เพื่อให้ WMS & SBS sync"]

        SCAN_TRACKING_PAGE --> SCAN_TRACKING_API
        SCAN_TRACKING_API --> CONFIRM_DISPATCH
        CONFIRM_DISPATCH --> DISPATCH_COMPLETE

        DISPATCH_COMPLETE --> SBS_NEEDED

        SBS_NEEDED -- "ใช่" --> HAS_SN
        SBS_NEEDED -- "ไม่" --> SBS_SKIP

        HAS_SN -- "มีแล้ว" --> SN_EXISTS
        HAS_SN -- "ยังไม่มี" --> SN_CREATE

        SN_EXISTS --> SBS_DEDUCT
        SN_CREATE --> SN_SCAN --> SBS_DEDUCT

        SBS_DEDUCT --> MOVEMENT_TX
        SBS_SKIP --> MOVEMENT_TX
    end

    %% ========================================
    %% LAYER 7: TRANSACTION LEDGER
    %% ========================================

    subgraph LEDGER["📘 Layer 7: Stock Transaction Ledger (Banking Style)"]
        direction TB

        LEDGER_CONCEPT@{ label: "💡 Banking-Style Transaction Log:<br>ทุกการเปลี่ยนแปลงสต็อกถูกบันทึกเป็น Transaction<br>เหมือนสมุดบัญชีธนาคาร (Immutable Ledger)<br>ตรวจสอบย้อนหลังได้ทุก Transaction" }

        TX_TYPES@{ label: "📋 Transaction Types:<br>• RECEIVE - รับของเข้าคลัง (+)<br>• RESERVE - จองสต็อกสำหรับ Batch (-)<br>• RELEASE - ปล่อยสต็อกคืน (+)<br>• PICK - หยิบสินค้า (-)<br>• DAMAGE - ของเสียหาย/หาย (-)<br>• ADJUST - ปรับปรุงสต็อก (+/-)<br>• MOVEMENT_OUT - ส่งของออก (-)" }

        TX_FIELDS@{ label: "📝 Transaction Fields:<br>• sku - รหัสสินค้า<br>• transaction_type - ประเภท<br>• quantity - จำนวน (+/-)<br>• balance_after - สต็อกคงเหลือหลัง TX<br>• reason_code - เหตุผล<br>• reference_type + reference_id - อ้างอิง<br>• created_by - ผู้ทำ Transaction<br>• created_at - เวลา<br>• notes - หมายเหตุ" }

        VIEW_LEDGER["📊 /stock/{sku}/ledger<br>ดูสมุดบัญชีสต็อกต่อ SKU:<br>- ทุก Transaction<br>- Balance progression<br>- Root cause analysis<br>- Drill-down to reference"]

        LEDGER_ANALYSIS["🔍 วิเคราะห์จาก Ledger:<br>- สต็อกหายที่ไหน?<br>- Shortage เกิดเพราะอะไร?<br>- ใครทำ Transaction นี้?<br>- เกิดเมื่อไหร่?"]

        LEDGER_CONCEPT --> TX_TYPES
        TX_TYPES --> TX_FIELDS
        TX_FIELDS --> VIEW_LEDGER
        VIEW_LEDGER --> LEDGER_ANALYSIS
    end

    %% ========================================
    %% LAYER 8: ANALYTICS & DASHBOARD
    %% ========================================

    subgraph ANALYTICS["📊 Layer 8: Analytics Dashboard (Executive View)"]
        direction TB

        SHORTAGE_ANALYTICS["📊 /analytics/shortage<br>Shortage Analytics Dashboard:<br>แยก PRE-PICK vs POST-PICK Problems"]

        subgraph PRE_PICK_ANALYSIS["🔴 PRE-PICK Problems (ก่อนเข้าคลัง)"]
            direction TB

            PRE_PICK_DEF@{ label: "❌ PRE-PICK Shortage:<br>• เกิดตอนสร้าง Batch<br>• สต็อกไม่พอจอง<br>• available < required<br>• status: waiting_stock" }

            PRE_PICK_ROOT@{ label: "🔍 Root Cause:<br>• จัดซื้อไม่ทัน<br>• Import จาก SBS ผิดพลาด<br>• Stock count ไม่แม่น<br>• Demand forecasting ผิด" }

            PRE_PICK_OWNER@{ label: "👤 ความรับผิดชอบ:<br>ฝ่ายจัดซื้อ / ฝ่าย SBS / Planning Team" }
        end

        subgraph POST_PICK_ANALYSIS["🟡 POST-PICK Problems (หลังเข้าคลัง)"]
            direction TB

            POST_PICK_DEF@{ label: "⚠️ POST-PICK Shortage:<br>• เกิดตอนหยิบของ<br>• สต็อกมีในระบบ แต่หาไม่เจอจริง<br>• Reason Code: CANT_FIND, DAMAGED, etc." }

            POST_PICK_ROOT@{ label: "🔍 Root Cause:<br>• Layout คลังไม่ดี<br>• วางของผิดที่<br>• ของเสียหายในคลัง<br>• Barcode หลุด/ผิด<br>• Picking error (คนผิดพลาด)" }

            POST_PICK_OWNER@{ label: "👤 ความรับผิดชอบ:<br>ฝ่ายคลัง / Warehouse Manager / QC Team" }
        end

        ANALYTICS_CHARTS["📈 Charts & Visualizations:<br>1. Type Breakdown (Pie): PRE vs POST<br>2. Reason Breakdown (Bar): Top Reasons<br>3. Daily Trend (Line): 30 days<br>4. Top 10 SKUs with Most Shortages<br>5. Status Summary: Pending/Resolved/etc.<br>6. Recent Shortage Logs (Table)"]

        ANALYTICS_INSIGHTS@{ label: "💡 Key Insights:<br>• ถ้า PRE-PICK สูง → ปัญหาอยู่ที่ระบบ/จัดซื้อ<br>• ถ้า POST-PICK สูง → ปัญหาอยู่ที่คลัง/คน<br>• Reason Code บอกว่าต้องแก้ตรงไหน<br>• SKU ที่ Shortage บ่อย → ต้องปรับ Process" }

        DECISION_MAKING@{ label: "🎯 ตัดสินใจเชิงกลยุทธ์:<br>• จะไปแก้ที่ฝ่ายไหนก่อน?<br>• จัดซื้อ (SBS) / ระบบ (WMS) / คลังสินค้า?<br>• ลงทุนปรับปรุงตรงไหน?<br>• Training ทีมไหน?" }

        SHORTAGE_ANALYTICS --> PRE_PICK_DEF
        SHORTAGE_ANALYTICS --> POST_PICK_DEF

        PRE_PICK_DEF --> PRE_PICK_ROOT --> PRE_PICK_OWNER
        POST_PICK_DEF --> POST_PICK_ROOT --> POST_PICK_OWNER

        SHORTAGE_ANALYTICS --> ANALYTICS_CHARTS
        ANALYTICS_CHARTS --> ANALYTICS_INSIGHTS
        ANALYTICS_INSIGHTS --> DECISION_MAKING
    end

    %% ========================================
    %% ADDITIONAL FEATURES
    %% ========================================

    subgraph ADDITIONAL["🔧 Additional Features"]
        direction LR

        QR_GEN["📱 /qr/{text}<br>Generate QR Code<br>สำหรับ SKU, Batch, Tracking"]

        WAREHOUSE_REPORT["📊 /report/warehouse<br>รายงานคลัง:<br>สรุป Stock, Batch, SLA"]

        PICKING_REPORT["📊 /report/picking<br>รายงานการหยิบ:<br>ประสิทธิภาพ Picker"]

        ADMIN_CLEAR["🗑️ /admin/clear<br>ล้างข้อมูลทดสอบ<br>(Admin only)"]

        ADMIN_PREVIEW["👁️ /api/admin/preview<br>ดูตัวอย่างข้อมูลก่อน Import"]

        STOCK_LIST["📋 /api/admin/stock-list<br>รายการสต็อกทั้งหมด<br>(Admin view)"]

        DELETE_MULTI["🗑️ /api/admin/delete-multiple<br>ลบหลาย Orders/Stocks<br>(Bulk delete)"]
    end

    %% ========================================
    %% CONNECTIONS (ระหว่าง Layers)
    %% ========================================

    %% CEO Vision
    CEO --> VISION
    VISION --> AUTH

    %% Authentication Flow
    LOGIN --> LOGIN_POST --> SESSION
    SESSION -- "Valid" --> ROLE_CHECK
    SESSION -- "Invalid" --> LOGIN

    ROLE_CHECK -- "Admin" --> ADMIN_ACCESS
    ROLE_CHECK -- "Picker" --> PICKER_ACCESS
    ROLE_CHECK -- "User" --> USER_ACCESS

    ADMIN_ACCESS --> USER_MGMT
    ADMIN_ACCESS --> INBOUND
    PICKER_ACCESS --> PICKING
    USER_ACCESS --> BATCH_LIST

    %% Inbound to Allocation
    STOCK_TX_RECEIVE --> ALLOCATION
    ORDER_SAVE --> ALLOCATION

    %% Allocation to Batch
    BATCH_SUCCESS --> BATCH_MGMT

    %% Batch to Picking
    BATCH_SUCCESS --> PICKING
    PRINT_PICKING --> SCAN_BATCH_PAGE
    PRINT_SKU_QR --> SCAN_SKU_PAGE

    %% Picking to Shortage
    SHORTAGE_CREATED_POST --> SHORTAGE_MGMT
    CREATE_SHORTAGE_PRE --> SHORTAGE_MGMT

    %% Batch Complete to Handover
    BATCH_COMPLETE --> GEN_HANDOVER

    %% Handover to Dispatch
    HANDOVER_COMPLETE --> DISPATCH

    %% All Transactions to Ledger
    STOCK_TX_RECEIVE --> LEDGER
    RESERVE_TX --> LEDGER
    SHORTAGE_TX_PRE --> LEDGER
    PICK_TX --> LEDGER
    SHORTAGE_TX_POST --> LEDGER
    RELEASE_TX --> LEDGER
    CANCEL_TX --> LEDGER
    PARTIAL_TX --> LEDGER
    MOVEMENT_TX --> LEDGER

    %% Ledger to Analytics
    LEDGER_ANALYSIS --> ANALYTICS

    %% Shortage to Analytics
    SHORTAGE_RESOLVED --> ANALYTICS

    %% Analytics to CEO
    DECISION_MAKING --> CEO

    %% Admin Users
    ADMIN --> USER_MGMT
    ADMIN --> INBOUND
    ADMIN --> BATCH_CREATE_PAGE
    ADMIN --> ANALYTICS

    %% Picker Users
    PICKER --> SCAN_BATCH_PAGE

    %% Online Users
    ONLINE --> SHORTAGE_QUEUE_PAGE

    %% SBS Integration
    SBS --> SBS_UPDATE
    SBS --> STOCK_IMPORT
    SBS_DEDUCT --> SBS

    %% Additional Features Links
    BATCH_DETAIL --> QR_GEN
    DASHBOARD --> WAREHOUSE_REPORT
    DASHBOARD --> PICKING_REPORT
    ADMIN_ACCESS --> ADMIN_CLEAR
    ADMIN_ACCESS --> STOCK_LIST

    %% Style Definitions
    classDef actorStyle fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    classDef systemStyle fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef successStyle fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef errorStyle fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef warningStyle fill:#ffe0b2,stroke:#e65100,stroke-width:2px
    classDef processStyle fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px
    classDef decisionStyle fill:#fff3e0,stroke:#ef6c00,stroke-width:2px

    class CEO,ADMIN,PICKER,ONLINE actorStyle
    class SBS,VISION systemStyle
    class BATCH_SUCCESS,PICK_SUCCESS,HANDOVER_COMPLETE,DISPATCH_COMPLETE,SHORTAGE_RESOLVED successStyle
    class BATCH_FAIL,PRE_PICK_SHORTAGE,CREATE_SHORTAGE_PRE,SHORTAGE_CREATED_POST errorStyle
    class MARK_SHORTAGE,ACTION_WAIT,WAITING_STOCK warningStyle
    class BATCH_CREATE_LOGIC,SCAN_SKU_API,PICK_API,SHORTAGE_API processStyle
    class SESSION,ROLE_CHECK,STOCK_CHECK,PICK_DECISION,SHORTAGE_ACTION_CHOOSE,BATCH_CHECK,BATCH_CREATED,SBS_NEEDED,HAS_SN decisionStyle
```

---

## 🔑 Key Workflows Summary

### 1️⃣ **Order-to-Dispatch Flow** (Happy Path)
```
Import Orders → Calculate SLA → Reserve Stock → Create Batch →
Print Picking List → Scan & Pick → Generate Handover Code →
Confirm Handover → Scan Tracking → Dispatch
```

### 2️⃣ **PRE-PICK Shortage Flow** (Stock Issue Before Picking)
```
Import Orders → Try Reserve Stock → ❌ Stock Insufficient →
Create PRE-PICK Shortage → Add to Shortage Queue →
Online Decision (Wait/Cancel/Fix) → Resolve
```

### 3️⃣ **POST-PICK Shortage Flow** (Warehouse Issue During Picking)
```
Scan SKU → Try Pick → ❌ Can't Find/Damaged →
Mark Shortage (Reason Code) → Create POST-PICK Shortage →
Add to Shortage Queue → Online Decision → Resolve
```

### 4️⃣ **Stock Transaction Flow** (All Stock Changes)
```
Every Stock Change → Create Transaction Record →
Log: Type, Qty, Balance, Reason, Reference →
View in /stock/{sku}/ledger → Analyze Root Cause
```

### 5️⃣ **Parent-Child Batch Flow** (Auto-Split for Shortage)
```
Original Batch → Some Items Shortage → Auto-Split →
Parent Batch (Completed Items - ship now) +
Child Batch (Shortage Items - wait stock)
```

---

## 📋 Transaction Types Reference

| Type | Direction | Reason Code Examples | Trigger |
|------|-----------|---------------------|---------|
| **RECEIVE** | `+` | `IMPORT_FROM_SBS` | Stock Import |
| **RESERVE** | `-` | `BATCH_RESERVE` | Batch Creation (Success) |
| **RESERVE_FAILED** | `-` | `BATCH_RESERVE_FAILED` | Batch Creation (PRE-PICK Shortage) |
| **RELEASE** | `+` | `HANDOVER_RELEASE` | Handover Confirm (Release Reserved) |
| **PICK** | `-` | `PICKING_COMPLETED` | Successful Pick |
| **DAMAGE** | `-` | `FOUND_DAMAGED`, `CANT_FIND` | POST-PICK Shortage |
| **ADJUST** | `+/-` | `ORDER_CANCELLED`, `PARTIAL_SHIP`, `CYCLE_COUNT_ADJUST` | Manual Adjustment |
| **MOVEMENT_OUT** | `-` | `DISPATCHED_TO_CUSTOMER` | SBS Stock Deduction |

---

## 🎯 Decision Points for Management

### ❓ "ปัญหาอยู่ที่ระบบหรือคน?"

**ดูที่ Analytics Dashboard** → `/analytics/shortage`

- **ถ้า PRE-PICK สูง (สีแดง 🔴)**:
  - ปัญหา: ระบบ, จัดซื้อ, Planning
  - แก้ไข: ปรับ Forecast, เร่งจัดซื้อ, ตรวจสอบ SBS Import
  - ผู้รับผิดชอบ: ฝ่ายจัดซื้อ, SBS Admin

- **ถ้า POST-PICK สูง (สีเหลือง 🟡)**:
  - ปัญหา: คลัง, Layout, Picking Error
  - แก้ไข: ปรับ Layout, Training Picker, QC ดีกว่า
  - ผู้รับผิดชอบ: Warehouse Manager, QC Team

- **ดู Reason Code**:
  - `CANT_FIND` สูง → Layout ไม่ดี, ต้องปรับจัดเก็บ
  - `FOUND_DAMAGED` สูง → QC ไม่ดี, ต้องเช็คตอนรับของ
  - `BARCODE_MISSING` สูง → ต้อง Re-label สินค้า

---

## 🚀 API Endpoints Summary

<details>
<summary><b>Click to expand complete API list</b></summary>

### Authentication
- `GET /login` - Login page
- `POST /login` - Login authentication
- `GET /logout` - Logout

### User Management
- `GET/POST /admin/users` - User management (Admin only)

### Dashboard & Reports
- `GET /` - Main dashboard
- `GET /report/warehouse` - Warehouse report
- `POST /report/warehouse/print` - Print warehouse report
- `GET /report/picking` - Picking report
- `POST /report/picking/print` - Print picking report

### Data Import
- `GET/POST /import/orders` - Import orders from platforms
- `GET/POST /import/products` - Import product master
- `GET/POST /import/stock` - Import stock from SBS
- `GET/POST /import/sales` - Import sales orders

### Stock Management
- `GET /stock/{sku}/ledger` - Stock transaction ledger per SKU
- `GET /api/admin/stock-list` - List all stocks (Admin)
- `GET /api/admin/export-stock-excel` - Export stock to Excel
- `POST /api/admin/delete-multiple` - Bulk delete stocks

### Batch Management
- `GET /batch/list` - List all batches
- `GET/POST /batch/create` - Create new batch
- `GET /batch/{batch_id}` - Batch detail page
- `GET /batch/{batch_id}/summary` - Batch summary modal
- `GET /batch/next-run/{platform}` - Get next run number
- `POST /batch/quick-create/{platform}` - Quick create batch (API)
- `GET /batch/{batch_id}/export.xlsx` - Export batch to Excel
- `GET /batch/{batch_id}/print-warehouse` - Print warehouse job sheet
- `GET /batch/{batch_id}/print-picking` - Print picking list
- `GET /batch/{batch_id}/print-sku-qr` - Print SKU QR codes
- `GET /batch/{batch_id}/print-handover` - Print handover sheet
- `POST /api/batch/{batch_id}/generate-handover-code` - Generate handover code
- `POST /api/batch/{batch_id}/auto-split` - Auto-split batch (Parent-Child)
- `GET /api/batch/{batch_id}/family` - Get batch family tree

### Order Acceptance
- `POST /accept/{order_line_id}` - Accept order line
- `POST /cancel_accept/{order_line_id}` - Cancel acceptance
- `POST /bulk_accept` - Bulk accept orders
- `POST /bulk_cancel` - Bulk cancel orders

### Handover System
- `GET /scan-handover` - Handover scanning page
- `POST /api/handover/verify` - Verify handover code
- `POST /api/handover/confirm` - Confirm handover

### Picking (Scanning)
- `GET /scan/batch` - Scan batch to start picking
- `POST /api/scan/batch` - Verify batch and redirect
- `GET /scan/sku` - Scan SKU to pick
- `GET /api/quick-assign/skus` - Get SKU list for batch
- `POST /api/scan/sku` - Verify scanned SKU
- `POST /api/pick/sku` - Confirm pick completion

### Shortage Management
- `GET /shortage-queue` - Shortage queue page
- `GET /api/shortage/queue` - Get shortage list (filtered)
- `POST /api/shortage/mark` - Mark shortage (POST-PICK)
- `POST /api/shortage/action` - Take action on shortage
- `POST /api/shortage/quick-action` - Quick action (1-click)
- `POST /api/shortage/bulk-action` - Bulk action on multiple shortages
- `GET /api/shortage/export-excel` - Export shortage queue to Excel
- `POST /api/shortage/update` - Update shortage details
- `GET /api/shortage/order-details` - Get order details for shortage
- `POST /api/shortage/change-status` - Change shortage status

### Analytics
- `GET /analytics/shortage` - Shortage analytics dashboard

### Dispatch (Tracking)
- `GET /scan/tracking` - Scan tracking number page
- `POST /api/scan/tracking` - Verify tracking number
- `POST /api/confirm-dispatch` - Confirm dispatch

### Utilities
- `GET /qr/{text}` - Generate QR code
- `GET /admin/clear` - Clear test data (Admin only)
- `POST /api/admin/preview` - Preview import data
- `GET /export.xlsx` - Export orders to Excel
- `GET /export_picking.xlsx` - Export picking list to Excel

</details>

---

## 📚 Related Documentation

- [Shortage Management User Guide (Thai)](./คู่มือการใช้งาน-Shortage-Management.md)
- [Database Schema](./database-schema.md) (if exists)
- [API Reference](./api-reference.md) (if exists)

---

## 📝 Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 2.0 | 2025-01-20 | Complete comprehensive workflow with all features, API endpoints, transaction types | Claude Code |
| 1.0 | 2025-01-19 | Initial workflow draft | User |

---

## 💡 Notes

- ใช้ Mermaid Live Editor (https://mermaid.live) เพื่อดู/แก้ไข Diagram
- รองรับ ELK Layout สำหรับ Complex Flowchart
- แนะนำให้ดูแบบ Fullscreen เพื่อความชัดเจน
- Diagram นี้ครอบคลุม 100% ของ System Features ในปัจจุบัน

---

**🎯 สรุป**: ระบบ VNIX WMS ออกแบบมาเพื่อ **ลดปัญหา Shortage** โดยแยกชัดเจนระหว่าง **PRE-PICK** (ปัญหาระบบ/จัดซื้อ) และ **POST-PICK** (ปัญหาคลัง/คน) พร้อม **Transaction Ledger** สำหรับ Audit Trail และ **Analytics Dashboard** สำหรับการตัดสินใจเชิงกลยุทธ์
