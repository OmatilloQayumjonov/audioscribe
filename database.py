# -*- coding: utf-8 -*-
"""
AudioScribe Database Layer
SQLite orqali foydalanuvchilar, obunalar, to'lovlar va bot sozlamalarini boshqarish.
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_bazasi.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        free_uses_left INTEGER DEFAULT 3,
        is_subscribed INTEGER DEFAULT 0,
        subscription_plan TEXT DEFAULT 'none',
        subscription_expires_at TEXT,
        joined_at TEXT,
        language TEXT DEFAULT 'uz'
    )
    """)
    
    # Migratsiya: language ustuni avvalgi bazada bo'lmasa qo'shish
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'uz'")
    except Exception:
        pass
    
    # Bot sozlamalari jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # To'lovlar tarixi jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT,
        amount TEXT,
        status TEXT,
        proof TEXT,
        created_at TEXT
    )
    """)
    
    # Standart sozlamalarni kiritish
    default_settings = {
        "free_limit": "3",
        "price_monthly": "25000",
        "price_yearly": "199000",
        "click_info": "8600 0000 0000 0000 (Click / Karta)",
        "admin_id": ""
    }
    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = get_db()
    cursor = conn.cursor()
    search_keys = [key]
    if key in ["click_info", "card_info"]:
        search_keys = ["click_info", "card_info"]
    
    for k in search_keys:
        cursor.execute("SELECT value FROM settings WHERE key = ?", (k,))
        row = cursor.fetchone()
        if row and row["value"]:
            conn.close()
            return row["value"]
            
    conn.close()
    return default

def set_setting(key, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    if key in ["click_info", "card_info"]:
        alt = "card_info" if key == "click_info" else "click_info"
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (alt, str(value)))
    conn.commit()
    conn.close()

def get_or_create_user(user_id, username="", full_name=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        free_limit = int(get_setting("free_limit", "3"))
        now = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO users (user_id, username, full_name, free_uses_left, is_subscribed, subscription_plan, joined_at, language)
        VALUES (?, ?, ?, ?, 0, 'none', ?, 'uz')
        """, (user_id, username, full_name, free_limit, now))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    else:
        # Ma'lumotlarni yangilash
        cursor.execute("UPDATE users SET username = ?, full_name = ? WHERE user_id = ?", (username, full_name, user_id))
        conn.commit()
        
    conn.close()
    return dict(user)

def get_user_language(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row["language"]:
        return row["language"]
    return "uz"

def set_user_language(user_id, lang):
    if lang not in ["uz", "ru", "en"]:
        lang = "uz"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def check_user_access(user_id):
    """
    Foydalanuvchining tahlil qilish huquqini tekshiradi:
    Qaytadi: (ruxsat_bormi: bool, sabab: str, qolgan_urinishlar: int)
    """
    admin_id = get_setting("admin_id")
    if admin_id:
        admin_list = [a.strip() for a in str(admin_id).split(",") if a.strip()]
        if str(user_id) in admin_list:
            return True, "admin", 999999
        
    user = get_or_create_user(user_id)
    
    # 1. Obuna borligini tekshirish
    if user.get("is_subscribed") == 1:
        exp_str = user.get("subscription_expires_at")
        if exp_str:
            try:
                exp_date = datetime.fromisoformat(exp_str)
                if exp_date > datetime.now():
                    return True, "subscribed", 999999
            except Exception:
                pass
        # Obuna muddati o'tgan bo'lsa
        conn = get_db()
        conn.cursor().execute("UPDATE users SET is_subscribed = 0, subscription_plan = 'none' WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    # 2. Bepul urinishlarni tekshirish
    free_left = user.get("free_uses_left", 0)
    if free_left > 0:
        return True, "free_trial", free_left
        
    return False, "limit_exceeded", 0

def use_free_trial(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET free_uses_left = MAX(0, free_uses_left - 1) WHERE user_id = ?", (user_id,))
    conn.commit()
    cursor.execute("SELECT free_uses_left FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["free_uses_left"] if row else 0

def activate_subscription(user_id, plan="monthly"):
    conn = get_db()
    cursor = conn.cursor()
    
    # Hozirgi tugash muddatini olish
    cursor.execute("SELECT subscription_expires_at, is_subscribed FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    start_date = datetime.now()
    if row and row["is_subscribed"] == 1 and row["subscription_expires_at"]:
        try:
            curr_exp = datetime.fromisoformat(row["subscription_expires_at"])
            if curr_exp > start_date:
                start_date = curr_exp
        except Exception:
            pass
            
    days = 30 if plan == "monthly" else 365
    new_expires_at = (start_date + timedelta(days=days)).isoformat()
    
    cursor.execute("""
    UPDATE users 
    SET is_subscribed = 1, subscription_plan = ?, subscription_expires_at = ?
    WHERE user_id = ?
    """, (plan, new_expires_at, user_id))
    conn.commit()
    conn.close()
    return new_expires_at

def add_free_uses(user_id, count=3):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET free_uses_left = free_uses_left + ? WHERE user_id = ?", (count, user_id))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total_users = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as subs FROM users WHERE is_subscribed = 1")
    active_subs = cursor.fetchone()["subs"]
    
    cursor.execute("SELECT COUNT(*) as free FROM users WHERE is_subscribed = 0 AND free_uses_left > 0")
    active_free = cursor.fetchone()["free"]
    
    conn.close()
    return {
        "total_users": total_users,
        "active_subs": active_subs,
        "active_free": active_free
    }

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r["user_id"] for r in rows]

def record_payment(user_id, plan="pending", amount="pending", proof="", status="pending"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO payments (user_id, plan, amount, status, proof, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, plan, amount, status, proof, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_pending_payments():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments WHERE status = 'pending' ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Bazani ishga tushirish
init_db()
