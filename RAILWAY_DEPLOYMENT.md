# Railway Deployment Guide - VNIX WMS

คู่มือการ deploy VNIX Warehouse Management System ไปยัง Railway.app

## ข้อกำหนดเบื้องต้น

- GitHub repository: `https://github.com/tetipong2542/vnix-wms`
- Railway account (สมัครที่ https://railway.app)
- Google Service Account credentials (สำหรับ Google Sheets integration)

## ขั้นตอนการ Deploy

### 1. สร้าง Project บน Railway

1. เข้าไปที่ https://railway.app และ Login
2. คลิก **"New Project"**
3. เลือก **"Deploy from GitHub repo"**
4. เลือก repository `tetipong2542/vnix-wms`
5. Railway จะเริ่มทำการ deploy โดยอัตโนมัติ

### 2. ตั้งค่า Environment Variables

ไปที่ **Variables** tab ของ project และเพิ่ม environment variables ต่อไปนี้:

#### 🔴 Variables ที่จำเป็น (Required)

```bash
# Railway Volume Mount Path - สำคัญมาก!
RAILWAY_VOLUME_MOUNT_PATH=/data

# Google Service Account Credentials
GOOGLE_PROJECT_ID=vnix-oms
GOOGLE_PRIVATE_KEY_ID=<your-private-key-id>
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n<your-private-key>\n-----END PRIVATE KEY-----\n"
GOOGLE_CLIENT_EMAIL=<your-service-account-email>
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GOOGLE_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GOOGLE_CLIENT_CERT_URL=<your-client-cert-url>
GOOGLE_UNIVERSE_DOMAIN=googleapis.com
```

#### 🟡 Variables แนะนำ (Recommended)

```bash
# Flask Secret Key - สำหรับ session security
SECRET_KEY=<generate-random-secret-key>

# Application Name (แสดงใน UI)
APP_NAME=VNIX Order Management
```

**หมายเหตุ:**
- ค่า `RAILWAY_VOLUME_MOUNT_PATH=/data` จำเป็นต้องตั้งค่าเพื่อให้ database persistent storage ทำงาน
- สร้าง `SECRET_KEY` ที่ปลอดภัยด้วย: `python -c "import secrets; print(secrets.token_hex(32))"`
- คัดลอก Google credentials จากไฟล์ `.env` ใน local

### 3. ตั้งค่า Volume Mount (Persistent Storage)

Railway จะอ่านการตั้งค่าจากไฟล์ `railway.toml` โดยอัตโนมัติ:

```toml
[[mounts]]
mountPath = "/data"
```

**การตรวจสอบ:**
1. ไปที่ **Settings** > **Volumes** ใน Railway dashboard
2. ตรวจสอบว่ามี volume ที่ mount ที่ path `/data` แล้ว
3. ถ้ายังไม่มี ให้สร้าง volume ใหม่ด้วย mount path `/data`

### 4. การทำงานของ Database

Application จะจัดการ database โดยอัตโนมัติ:

- ✅ **Auto-creation**: สร้าง database schema อัตโนมัติจาก `models.py` เมื่อเริ่มรันครั้งแรก
- ✅ **Auto-migration**: ตรวจสอบและอัปเดต schema โดยอัตโนมัติ
- ✅ **Persistent storage**: ข้อมูลจะถูกเก็บใน `/data/data.db` และไม่หายเมื่อ redeploy
- ⚠️  **ข้อมูลเดิมจาก local จะไม่ถูกย้าย**: ระบบจะเริ่มต้นด้วย database เปล่า

### 5. Deployment Configuration

ไฟล์ที่จำเป็นสำหรับ deployment (มีอยู่ใน repository แล้ว):

**Procfile:**
```
web: python app.py
```

**railway.toml:**
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python app.py"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 10

[[mounts]]
mountPath = "/data"
```

**requirements.txt:**
- ระบุ dependencies ทั้งหมดที่ต้องการ
- Railway จะติดตั้งโดยอัตโนมัติ

### 6. ตรวจสอบการ Deploy

1. ไปที่ **Deployments** tab
2. รอจนกระทั่ง deployment status เป็น **"Success"** (สีเขียว)
3. คลิกที่ **"View Logs"** เพื่อดู application logs
4. ตรวจสอบว่ามีข้อความ:
   ```
   Serving on http://0.0.0.0:8000
   ```

### 7. เข้าถึง Application

1. ไปที่ **Settings** > **Networking**
2. คลิก **"Generate Domain"** เพื่อสร้าง public URL
3. เข้าถึง application ผ่าน URL ที่สร้างขึ้น เช่น:
   ```
   https://vnix-wms-production.up.railway.app
   ```

### 8. ตรวจสอบ System Status

เข้าไปที่ `/system_status` ใน application เพื่อดูข้อมูล:
- Database location และขนาด
- Environment variables ที่ตั้งค่าไว้
- Server information
- การเชื่อมต่อ Google Sheets

## การแก้ไขปัญหา (Troubleshooting)

### ❌ Database ไม่ถูกสร้าง

**อาการ:** Application error หรือ "no such table" errors

**วิธีแก้:**
1. ตรวจสอบว่า `RAILWAY_VOLUME_MOUNT_PATH=/data` ถูกตั้งค่าแล้ว
2. ตรวจสอบว่ามี volume mount ที่ `/data` ใน Railway dashboard
3. Restart deployment: **Deployments** > **⋮** > **Redeploy**

### ❌ Session/Login ไม่ทำงาน

**อาการ:** ถูก logout บ่อยๆ หรือ session หาย

**วิธีแก้:**
1. ตั้งค่า `SECRET_KEY` environment variable
2. ใช้ secret key ที่ปลอดภัย (อย่างน้อย 32 characters)
3. อย่าใช้ default secret key ใน production

### ❌ Google Sheets Integration ไม่ทำงาน

**อาการ:** ไม่สามารถ import ข้อมูลจาก Google Sheets ได้

**วิธีแก้:**
1. ตรวจสอบว่าทุก `GOOGLE_*` variables ถูกตั้งค่าครบถ้วน
2. ตรวจสอบว่า `GOOGLE_PRIVATE_KEY` มี `\n` ที่ถูกต้อง
3. ตรวจสอบว่า Service Account มีสิทธิ์เข้าถึง Google Sheets ที่ต้องการ
4. ดู logs: **Deployments** > **View Logs** เพื่อหา error details

### ❌ Application Crash หรือ Restart Loop

**อาการ:** Application restart บ่อยๆ หรือไม่สามารถเริ่มต้นได้

**วิธีแก้:**
1. ดู logs: **Deployments** > **View Logs**
2. ตรวจสอบว่า dependencies ใน `requirements.txt` ติดตั้งสำเร็จ
3. ตรวจสอบว่ามี memory เพียงพอ (อาจต้อง upgrade plan)
4. ตรวจสอบว่าไม่มี syntax errors ใน code

### 📊 ตรวจสอบ Logs แบบ Real-time

```bash
# ถ้าติดตั้ง Railway CLI แล้ว
railway logs --follow
```

## การอัปเดต Application

เมื่อมีการอัปเดตโค้ด:

1. Push changes ไปที่ GitHub:
   ```bash
   git add .
   git commit -m "Update: description"
   git push origin main
   ```

2. Railway จะ auto-deploy โดยอัตโนมัติเมื่อมี push ไปที่ `main` branch

3. ✅ **ข้อมูลใน database จะไม่หาย** เพราะใช้ persistent volume

## การ Backup Database

### Manual Backup

1. เข้าถึง Railway Shell:
   - Railway Dashboard > **⋮** > **Shell**

2. ดาวน์โหลด database:
   ```bash
   # จาก shell
   cat /data/data.db > /tmp/backup.db
   ```

3. หรือใช้ Railway CLI:
   ```bash
   railway run cat /data/data.db > backup_$(date +%Y%m%d).db
   ```

### Automated Backup (แนะนำ)

พิจารณาใช้ Railway Cron Jobs หรือ external backup service เพื่อ backup database เป็นประจำ

## Security Checklist

- [ ] ตั้งค่า `SECRET_KEY` ที่ปลอดภัยและไม่เหมือนกับ default
- [ ] ตรวจสอบว่า `.env` และ `data.db` ถูก ignore ใน `.gitignore`
- [ ] ไม่ commit sensitive credentials ขึ้น GitHub
- [ ] ตั้งค่า environment variables บน Railway เท่านั้น
- [ ] Enable Railway's access restrictions ถ้าต้องการ
- [ ] Backup database เป็นประจำ

## ข้อมูลเพิ่มเติม

- Railway Documentation: https://docs.railway.app
- Flask Documentation: https://flask.palletsprojects.com
- SQLAlchemy Documentation: https://docs.sqlalchemy.org

---

**สร้างโดย:** Claude Code
**วันที่:** 2025-12-19
**Version:** 1.0
