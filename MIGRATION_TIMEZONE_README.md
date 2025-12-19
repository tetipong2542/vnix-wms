# 🔧 คู่มือ Migration: ImportLog Timezone (UTC → GMT+7)

## 📋 สรุปการแก้ไข

การแก้ไขนี้เปลี่ยน timezone ของ `ImportLog.created_at` จาก **UTC** เป็น **Thai Timezone (GMT+7)** เพื่อให้ข้อมูลเวลาแสดงผลถูกต้องตามเวลาประเทศไทย

---

## ⚠️ สิ่งที่ต้องทำก่อน Migration

### 1. Backup Database ก่อน!
```bash
# สำหรับ SQLite
cp oms.db oms.db.backup

# สำหรับ PostgreSQL
pg_dump -U username dbname > backup.sql

# สำหรับ MySQL
mysqldump -u username -p dbname > backup.sql
```

### 2. หยุดการทำงานของ Application
```bash
# หยุด web server
# ถ้าใช้ systemd
sudo systemctl stop oms-app

# หรือถ้าใช้ process manager
pkill -f "python app.py"
```

---

## 🚀 วิธีการ Migrate

### ขั้นตอนที่ 1: รัน Migration Script

```bash
# เข้าไปที่ directory ของโปรเจค
cd /Users/pond-dev/Documents/backup/oms-production/V.5.52\ 2/

# รัน migration script
python migrate_import_log_timezone.py
```

### ขั้นตอนที่ 2: ตรวจสอบผลลัพธ์

Script จะแสดงข้อความดังนี้:
```
================================================================================
🔧 Migration Script: ImportLog Timezone Conversion (UTC → GMT+7)
================================================================================

📊 พบข้อมูลทั้งหมด: XX records
⚠️  Script นี้จะบวกเวลา +7 ชั่วโมงให้กับคอลัมน์ created_at ทั้งหมด

❓ ต้องการดำเนินการต่อหรือไม่? (yes/no):
```

พิมพ์ **yes** เพื่อยืนยัน

### ขั้นตอนที่ 3: ตรวจสอบข้อมูลหลัง Migration

Script จะแสดงตัวอย่างข้อมูล 5 records ล่าสุด:
```
✅ อัพเดตสำเร็จ: XX records
✅ Migration เสร็จสมบูรณ์!

📋 ตัวอย่างข้อมูลหลัง migrate (5 records ล่าสุด):
ID | Filename | Created At
--------------------------------------------------------------------------------
1  | Excel File | 2025-01-15 14:30:00
2  | Google Sheet | 2025-01-15 15:45:00
...
```

### ขั้นตอนที่ 4: เริ่มการทำงานของ Application อีกครั้ง

```bash
# เริ่ม web server
sudo systemctl start oms-app

# หรือ
python app.py
```

---

## 🧪 ทดสอบหลัง Migration

1. เปิดหน้า `/import/bill_empty`
2. ตรวจสอบคอลัมน์ "เวลา" ในตาราง "ประวัติการ Import"
3. เวลาที่แสดงควรเป็น **เวลาไทย (GMT+7)** แล้ว

### ตัวอย่างการทดสอบ

**ก่อน Migration:**
- Created At: `2025-01-15 07:30:00` (UTC)
- แสดงในหน้าเว็บ: `07:30`

**หลัง Migration:**
- Created At: `2025-01-15 14:30:00` (GMT+7)
- แสดงในหน้าเว็บ: `14:30`

---

## 📝 การเปลี่ยนแปลงในโค้ด

### 1. ImportLog Model (app.py:174)
```python
# ก่อน
created_at = db.Column(db.DateTime, default=datetime.utcnow)

# หลัง
created_at = db.Column(db.DateTime, default=lambda: datetime.now(TH_TZ))
```

### 2. Template (import_bill_empty.html:313)
```jinja
<!-- ก่อน -->
{{ log.created_at.strftime('%H:%M') if log.created_at else '-' }}

<!-- หลัง -->
{{ log.created_at.strftime('%d/%m/%Y %H:%M') if log.created_at else '-' }}
```

### 3. ปุ่มล้างประวัติ (import_bill_empty.html:279-281)
```html
<button type="button" class="btn btn-outline-danger btn-sm" onclick="openClearModal()">
  <i class="bi bi-trash-fill"></i> ล้างประวัติ
</button>
```

### 4. API Endpoint (app.py:9717-9757)
```python
@app.route("/import/bill_empty/clear_logs", methods=["POST"])
@login_required
def clear_bill_empty_logs():
    # ลบ logs ตามช่วงวันที่ หรือทั้งหมด
    ...
```

---

## 🔄 Rollback (กรณีเกิดปัญหา)

### ถ้าต้องการ Rollback ให้ทำดังนี้:

1. **Restore Database จาก Backup**
   ```bash
   # SQLite
   cp oms.db.backup oms.db

   # PostgreSQL
   psql -U username dbname < backup.sql

   # MySQL
   mysql -u username -p dbname < backup.sql
   ```

2. **Revert โค้ดกลับไปเวอร์ชันเดิม**
   ```bash
   git checkout HEAD -- app.py templates/import_bill_empty.html
   ```

---

## ✅ Checklist หลัง Migration

- [ ] Backup database เรียบร้อย
- [ ] รัน migration script สำเร็จ
- [ ] ตรวจสอบเวลาในหน้า `/import/bill_empty` ถูกต้อง
- [ ] ทดสอบ import ใหม่ และตรวจสอบว่า created_at บันทึกเป็น GMT+7
- [ ] ทดสอบปุ่ม "ล้างประวัติ" ทำงานได้ปกติ
- [ ] ลบ backup file (ถ้าแน่ใจว่าทุกอย่างทำงานถูกต้อง)

---

## 📞 ติดต่อ/รายงานปัญหา

หากพบปัญหาหรือต้องการความช่วยเหลือ:
- ตรวจสอบ log file ของ application
- ตรวจสอบ browser console (F12)
- สร้าง issue ใน GitHub repository

---

## 📚 เอกสารอ้างอิง

- [Python datetime timezone](https://docs.python.org/3/library/datetime.html#timezone-objects)
- [SQLAlchemy DateTime](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.DateTime)
- [Flask SQLAlchemy Models](https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/models/)
