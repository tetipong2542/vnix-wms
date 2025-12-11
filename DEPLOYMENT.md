# VNIX WMS - Deployment Guide

## การติดตั้งบน Production (Railway)

### 1. ตั้งค่า Google Service Account Credentials

ระบบต้องการ Google Service Account เพื่อเชื่อมต่อกับ Google Sheets

#### วิธีที่ 1: ใช้ GOOGLE_CREDENTIALS_JSON (แนะนำ)

1. เปิดไฟล์ `credentials.json` ของคุณ
2. Copy เนื้อหาทั้งหมด (เป็น JSON string)
3. ไปที่ Railway Dashboard → เลือก Project → Variables
4. เพิ่ม Environment Variable:
   ```
   Key: GOOGLE_CREDENTIALS_JSON
   Value: {เนื้อหาทั้งหมดของไฟล์ credentials.json}
   ```

#### วิธีที่ 2: ใช้ Environment Variables แยก

ตั้งค่า Environment Variables ต่อไปนี้ใน Railway:

```bash
GOOGLE_PROJECT_ID=vnix-oms
GOOGLE_PRIVATE_KEY_ID=da922b3018874afa6e4ff8a28ebc550e6c8345b0
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
GOOGLE_CLIENT_EMAIL=vnix-sheet-importer@vnix-oms.iam.gserviceaccount.com
GOOGLE_CLIENT_ID=116721842382656499585
GOOGLE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GOOGLE_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GOOGLE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/vnix-sheet-importer%40vnix-oms.iam.gserviceaccount.com
GOOGLE_UNIVERSE_DOMAIN=googleapis.com
```

**หมายเหตุ:** สำหรับ `GOOGLE_PRIVATE_KEY` ให้ใส่ `\n` แทนการขึ้นบรรทัดใหม่

### 2. ตั้งค่า Environment Variables อื่นๆ (ถ้ามี)

```bash
APP_NAME=VNIX Order Management
DATABASE_URL=<Railway จะตั้งให้อัตโนมัติ>
```

---

## การติดตั้งบน Local Development

### 1. Clone Repository

```bash
git clone https://github.com/tetipong2542/vnix-wms.git
cd vnix-wms
```

### 2. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Google Credentials

**วิธีที่ 1:** วางไฟล์ `credentials.json` ในโฟลเดอร์โปรเจกต์

```bash
# วางไฟล์ credentials.json ที่ได้จาก Google Cloud Console
cp /path/to/your/credentials.json ./credentials.json
```

**วิธีที่ 2:** ใช้ไฟล์ `.env`

```bash
# Copy ไฟล์ตัวอย่าง
cp .env.example .env

# แก้ไขไฟล์ .env และใส่ค่าจริง
nano .env
```

### 4. รันโปรแกรม

```bash
# Windows
run_server.bat

# Linux/Mac
python app.py
```

---

## การตรวจสอบ Credentials

ระบบจะลองโหลด credentials ตามลำดับ:

1. ✅ ตัวแปร `GOOGLE_CREDENTIALS_JSON` (JSON string ทั้งก้อน)
2. ✅ ตัวแปรแยก (`GOOGLE_PRIVATE_KEY`, `GOOGLE_CLIENT_EMAIL`, ฯลฯ)
3. ✅ ไฟล์ `credentials.json` ในโฟลเดอร์โปรเจกต์

หากไม่พบวิธีใดเลย ระบบจะแสดง error message พร้อมคำแนะนำ

---

## วิธีดึง Google Service Account Credentials

1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. เลือก Project หรือสร้างใหม่
3. ไปที่ **APIs & Services** → **Credentials**
4. คลิก **Create Credentials** → **Service Account**
5. ตั้งชื่อและสร้าง Service Account
6. ไปที่ **Keys** → **Add Key** → **Create New Key** → เลือก **JSON**
7. ดาวน์โหลดไฟล์ JSON ที่ได้

### เปิดใช้งาน APIs

ต้องเปิด APIs ต่อไปนี้:
- Google Sheets API
- Google Drive API

---

## แชร์สิทธิ์ Google Sheets

อย่าลืมแชร์ Google Sheet ให้กับ Service Account Email:

```
vnix-sheet-importer@vnix-oms.iam.gserviceaccount.com
```

โดยให้สิทธิ์ **Viewer** หรือ **Editor** ตามความต้องการ

---

## การแก้ปัญหา

### ❌ "ไม่พบ Google Service Account Credentials"

**วิธีแก้:**
- ตรวจสอบว่าตั้งค่า Environment Variables ใน Railway ครบถ้วน
- ตรวจสอบว่าไฟล์ `credentials.json` มีอยู่ (สำหรับ Local)

### ❌ "GOOGLE_CREDENTIALS_JSON ไม่ถูกต้อง"

**วิธีแก้:**
- ตรวจสอบว่า JSON format ถูกต้อง (ไม่มี syntax error)
- ตรวจสอบว่าไม่มีการตัดข้อความ (copy ไม่ครบ)

### ❌ "Permission denied on Google Sheet"

**วิธีแก้:**
- แชร์ Google Sheet ให้กับ Service Account Email
- ตรวจสอบว่าให้สิทธิ์เป็น Viewer หรือ Editor

---

## ข้อมูลเพิ่มเติม

- **Repository:** https://github.com/tetipong2542/vnix-wms
- **Production:** https://vnix-wms-production.up.railway.app
