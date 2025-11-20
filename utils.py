
# utils.py
from __future__ import annotations

import re
from datetime import datetime, date, time, timedelta
from typing import Optional, Iterable, Set, Dict, Tuple

import pytz

# ===================== Timezone =====================
TH_TZ = pytz.timezone("Asia/Bangkok")

# ===================== Platform priority / cutoffs (legacy) =====================
PLATFORM_PRIORITY: Dict[str, int] = {"Shopee": 1, "TikTok": 2, "Lazada": 3, "อื่นๆ": 4}

# คงไว้เพื่อ backward-compatible กับฟังก์ชันเก่า (ไม่ใช้ในคำนวณ SLA แบบวันทำการ)
CUTOFFS: Dict[str, time] = {
    "Lazada": time(11, 0, 0),
    "Shopee": time(12, 0, 0),
    "TikTok": time(12, 0, 0),
    "อื่นๆ": time(12, 0, 0),
}

# ===================== Platform normalize =====================
def normalize_platform(p: Optional[str]) -> Optional[str]:
    if not p:
        return None
    p = p.strip()
    aliases = {
        "shopee": "Shopee", "shoppee": "Shopee", "spx": "Shopee",
        "tiktok": "TikTok", "tiktokshop": "TikTok", "tikt0k": "TikTok", "tik tok": "TikTok",
        "lazada": "Lazada", "lz": "Lazada",
        "other": "อื่นๆ", "others": "อื่นๆ", "อื่นๆ": "อื่นๆ",
    }
    key = re.sub(r"[^a-zA-Zก-๙]", "", p).lower()
    return aliases.get(key, p)

# ===================== Logistic Type Cleaner =====================
def clean_logistic(logistic: Optional[str]) -> str:
    """
    ตัดข้อความยาวๆ ของ logistic type ให้สั้นลงและอ่านง่ายขึ้น

    Examples:
        "Standard Delivery - ส่งธรรมดาในประเทศ-Flash Express" → "Flash Express"
        "Standard Delivery - ส่งธรรมดาในประเทศ-" → ""
        "J&T Express" → "J&T Express"
    """
    if not logistic:
        return ""

    # ตัดข้อความ "Standard Delivery - ส่งธรรมดาในประเทศ-" ออก
    cleaned = logistic.replace("Standard Delivery - ส่งธรรมดาในประเทศ-", "").strip()

    # ถ้าเหลือแค่ว่างเปล่า ให้คืนค่า "Standard"
    return cleaned if cleaned else "Standard"

# ===================== Now/Format helpers =====================
def now_thai() -> datetime:
    return datetime.now(TH_TZ)

def current_be_year() -> int:
    return now_thai().year + 543

def format_sla_thai(order_time_str: Optional[str]) -> str:
    """
    แปลง order_time เป็นข้อความภาษาไทยแบบสัมพัทธ์

    Examples:
        - "2025-01-19 18:00" (วันนี้) → "วันนี้ 18:00"
        - "2025-01-20 12:00" (พรุ่งนี้) → "พรุ่งนี้ 12:00"
        - "2025-01-21 10:00" (มะรืน) → "มะรืน 10:00"
        - "2025-01-22 14:00" (อื่นๆ) → "22 ม.ค. 14:00"
    """
    if not order_time_str:
        return ""

    try:
        # Parse order_time (assume format: "YYYY-MM-DD HH:MM" or similar)
        if isinstance(order_time_str, str):
            order_dt = datetime.strptime(order_time_str.strip(), "%Y-%m-%d %H:%M")
        elif isinstance(order_time_str, datetime):
            order_dt = order_time_str
        else:
            return order_time_str

        # Get current date (Thai timezone)
        now = now_thai()
        today = now.date()
        order_date = order_dt.date()
        time_str = order_dt.strftime("%H:%M")

        # คำนวณความต่าง
        delta = (order_date - today).days

        if delta == 0:
            return f"วันนี้ {time_str}"
        elif delta == 1:
            return f"พรุ่งนี้ {time_str}"
        elif delta == 2:
            return f"มะรืน {time_str}"
        else:
            # แสดงวันที่แบบสั้น (เช่น "19 ม.ค. 18:00")
            month_names_short = [
                "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
            ]
            day = order_dt.day
            month = month_names_short[order_dt.month - 1]
            return f"{day} {month} {time_str}"

    except Exception as e:
        # ถ้า parse ไม่ได้ ให้คืนค่าเดิม
        return order_time_str

def to_thai_be(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    dt = dt.astimezone(TH_TZ)
    y = dt.year + 543
    return dt.strftime(f"%d/%m/{y:04d} %H:%M")

def to_be_date_str(d: Optional[date]) -> str:
    if not d:
        return ""
    y = d.year + 543
    return d.strftime(f"%d/%m/{y:04d}")

# ===================== Robust datetime parsing (PATCHED) =====================
def parse_datetime_guess(s):
    """แปลงเป็น datetime(TH) แบบทนทาน: รองรับรูปแบบตัวอักษร, Excel serial, Unix ts; ปฏิเสธเลขเล็ก ๆ"""
    if s is None:
        return None
    if isinstance(s, datetime):
        return s.astimezone(TH_TZ) if s.tzinfo else TH_TZ.localize(s)

    # --- ตัวเลข ---
    if isinstance(s, (int, float)):
        x = float(s)
        # กรองเลขเล็ก ๆ (เช่น 0,1,2,3...) ที่ไม่ใช่เวลาแน่ ๆ
        if x < 10:
            return None
        # Excel serial date (Excel นับตั้งแต่ 1899-12-30)
        if 25569 <= x <= 60000:  # ประมาณปี 1970–2064
            try:
                dt = datetime(1899, 12, 30) + timedelta(days=x)
                return TH_TZ.localize(dt)
            except Exception:
                return None
        # Unix timestamp วินาที
        if x >= 1_000_000_000:
            try:
                return datetime.fromtimestamp(x, tz=TH_TZ)
            except Exception:
                pass
        # ไม่ใช่รูปแบบที่รองรับ
        return None

    # --- สตริง ---
    txt = str(s).strip()
    if not txt:
        return None
    txt = txt.replace("T", " ").replace("  ", " ").strip()

    patterns = [
        "%d %b %Y %H:%M:%S", "%d %b %Y %H:%M",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M",
        "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
        "%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y %H:%M", "%m/%d/%Y",
    ]
    for p in patterns:
        try:
            dt = datetime.strptime(txt, p)
            return TH_TZ.localize(dt)
        except Exception:
            pass

    # รูปแบบไทย BE: dd/mm/yyyy (อาจมีเวลา)
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})\s*(\d{1,2}:\d{2}(:\d{2})?)?$", txt)
    if m:
        d, mn, y, tm, _ = m.groups()
        y = int(y)
        if y > 2400:  # BE -> CE
            y -= 543
        if tm:
            fmt = "%d/%m/%Y %H:%M:%S" if len(tm.split(":")) == 3 else "%d/%m/%Y %H:%M"
            dt = datetime.strptime(f"{int(d):02d}/{int(mn):02d}/{y:04d} {tm}", fmt)
        else:
            dt = datetime.strptime(f"{int(d):02d}/{int(mn):02d}/{y:04d}", "%d/%m/%Y")
        return TH_TZ.localize(dt)

    return None

# =====================================================================
# ===================== Business-day aware SLA ========================
# =====================================================================

# === วันหยุดไทย (แก้ไข/เติมเองได้) : ใช้ ค.ศ. ===
TH_HOLIDAYS: Set[date] = set()
# ตัวอย่าง:
# TH_HOLIDAYS.update({
#     date(2025, 1, 1),   # New Year
#     date(2025, 4, 6),   # Chakri Day (ถ้าชนเสาร์/อาทิตย์ให้เพิ่มชดเชยเอง)
# })

def is_weekend(d: date) -> bool:
    return d.weekday() >= 5  # 5=Sat, 6=Sun

def is_holiday(d: date) -> bool:
    return d in TH_HOLIDAYS

def is_business_day(d: date) -> bool:
    return (not is_weekend(d)) and (not is_holiday(d))

def add_business_days(d: date, n: int) -> date:
    step = 1 if n >= 0 else -1
    cur = d
    cnt = 0
    while cnt != n:
        cur = cur + timedelta(days=step)
        if is_business_day(cur):
            cnt += step
    return cur

def diff_business_days(d1: date, d2: date) -> int:
    """จำนวนวันทำการ (d2 - d1) ใช้บวก/ลบทีละวันโดยข้ามวันหยุด/เสาร์อาทิตย์"""
    if d1 == d2:
        return 0
    step = 1 if d2 >= d1 else -1
    cur = d1
    cnt = 0
    while cur != d2:
        cur = cur + timedelta(days=step)
        if is_business_day(cur):
            cnt += step
    return cnt

def _platform_cutoff_hour(platform: str) -> int:
    platform = normalize_platform(platform) or "อื่นๆ"
    return 11 if platform == "Lazada" else 12  # Shopee/TikTok/อื่นๆ = 12:00

def compute_due_date(platform: str, order_dt: datetime) -> date:
    """
    กำหนดส่งแบบ 'วันทำการ':
    - ถ้าออเดอร์ 'ก่อน cutoff' => due = 'วันเดียวกัน' (ถ้าวันนั้นไม่ใช่วันทำการ ให้เลื่อนไปวันทำการถัดไป)
    - ถ้า 'หลัง cutoff'     => due = 'วันทำการถัดไป'
    - เสาร์/อาทิตย์/วันหยุด ไม่นับเป็นวันส่ง
    """
    if order_dt.tzinfo is None:
        order_dt = TH_TZ.localize(order_dt)
    else:
        order_dt = order_dt.astimezone(TH_TZ)

    cutoff_hour = _platform_cutoff_hour(platform)
    cutoff = datetime(order_dt.year, order_dt.month, order_dt.day, cutoff_hour, 0, 0, tzinfo=TH_TZ)

    base = order_dt.date()
    due = base if order_dt <= cutoff else add_business_days(base, 1)

    while not is_business_day(due):
        due = add_business_days(due, 1)

    return due

def sla_text(platform: str, order_dt: datetime, today_dt: Optional[datetime] = None) -> str:
    """
    คืนข้อความ SLA:
      - 'เลยกำหนด (X วัน)'
      - 'วันนี้'
      - 'พรุ่งนี้'
      - 'อีก N วัน'
    โดยนับเฉพาะ 'วันทำการ' และอ้างอิง cutoff ของแพลตฟอร์ม
    """
    if not order_dt:
        return ""
    if today_dt is None:
        today_dt = now_thai()

    due = compute_due_date(platform, order_dt)
    today0 = today_dt.date()
    diff = diff_business_days(due, today0)  # today0 - due

    if diff > 0:
        return f"เลยกำหนด ({diff} วัน)"
    if diff == 0:
        return "วันนี้"
    if diff == -1:
        return "พรุ่งนี้"
    return f"อีก {-diff} วัน"

# =====================================================================
# ========== Backward-compatible wrappers (สำหรับโค้ดเดิม) ============
# =====================================================================
def due_date_for(platform: str, order_time: datetime) -> date:
    """ฟังก์ชันเดิม: ชี้ไปที่ compute_due_date (แบบวันทำการ)"""
    return compute_due_date(platform, order_time)

def sla_status(platform: str, order_time: datetime, ref_now: Optional[datetime] = None) -> Tuple[str, date]:
    """
    ฟังก์ชันเดิม: คืน (ข้อความSLA, due_date).
    - ถ้า PACKED ควรจัดการเว้นว่างจากฝั่งผู้เรียก
    """
    txt = sla_text(platform, order_time, ref_now)
    return txt, compute_due_date(platform, order_time)