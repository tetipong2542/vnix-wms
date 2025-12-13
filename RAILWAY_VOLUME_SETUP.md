# Railway Volume Setup Guide

## ปัญหาที่แก้ไข
ข้อมูลในระบบหายหลัง deploy เพราะ Railway ใช้ ephemeral filesystem ทำให้ไฟล์ `data.db` ถูกลบทุกครั้งที่อัปเดตโค้ด

## วิธีแก้ไข: ใช้ Railway Volume
Railway Volume จะเก็บข้อมูลแบบถาวร ไม่หายหลัง deploy

---

## ขั้นตอนการตั้งค่า Railway Volume

### 1. เข้าสู่ Railway Dashboard
- ไปที่ https://railway.app/
- เลือก Project ของคุณ

### 2. สร้าง Volume
1. คลิกที่ Service ของคุณ (ที่รัน app.py)
2. ไปที่แท็บ **"Variables"** หรือ **"Settings"**
3. เลื่อนลงหา **"Volumes"** section
4. คลิก **"+ New Volume"**

### 3. กำหนดค่า Volume
กรอกข้อมูลดังนี้:

- **Volume Name**: `data-volume` (ตั้งชื่ออะไรก็ได้)
- **Mount Path**: `/data`

> หมายเหตุ: ต้องใช้ `/data` ตามที่กำหนดไว้ในโค้ด

4. คลิก **"Add"** หรือ **"Create"**

### 4. ตั้งค่า Environment Variable
1. ไปที่แท็บ **"Variables"**
2. เพิ่ม Environment Variable ใหม่:
   ```
   RAILWAY_VOLUME_MOUNT_PATH = /data
   ```
3. คลิก **"Save"** หรือ **"Deploy"**

### 5. Deploy ใหม่
- Railway จะ redeploy อัตโนมัติ
- หรือกด **"Deploy"** ใหม่เอง

---

## วิธีตรวจสอบว่าใช้งานได้

### ตรวจสอบ Logs
1. ไปที่แท็บ **"Logs"** ใน Railway
2. หาข้อความที่แสดงว่า database path ถูกต้อง:
   ```
   Database path: /data/data.db
   ```

### ทดสอบการทำงาน
1. เข้าใช้งานระบบ
2. ตั้งค่า Google Sheet URL
3. Import ข้อมูล
4. Push code อัปเดตใหม่ (เช่นแก้ไข README)
5. รอ Railway deploy เสร็จ
6. เข้าระบบอีกครั้ง → ข้อมูลควรยังอยู่!

---

## การแก้ปัญหา (Troubleshooting)

### ถ้าข้อมูลยังหาย
1. ตรวจสอบว่า Environment Variable `RAILWAY_VOLUME_MOUNT_PATH` ตั้งค่าถูกต้อง
2. ตรวจสอบ Mount Path ใน Volume ต้องเป็น `/data`
3. ดู Logs ว่ามี error เกี่ยวกับ permission หรือไม่

### ถ้า Railway ไม่มี Volume option
- Railway Volume อาจไม่รองรับใน Free tier บางภูมิภาค
- พิจารณาเปลี่ยนไปใช้ Option 2 (PostgreSQL) แทน

---

## ค่าใช้จ่าย
- Railway Volume: **$0.25/GB/month**
- ตัวอย่าง: database 10MB = ~$0.0025/month (ถูกมาก)

---

## สรุป
หลังจากตั้งค่าแล้ว:
- ข้อมูลจะไม่หายหลัง deploy
- ไม่ต้องตั้งค่า Google Sheet URL ใหม่
- ข้อมูล Import จะถูกเก็บไว้ถาวร

---

**สร้างโดย:** Claude Code
**วันที่:** 2025-12-13
