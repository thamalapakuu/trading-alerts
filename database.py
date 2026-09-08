import os
import sqlite3


DATA_DIR = "/app/data"
DB_NAME = f"{DATA_DIR}/trading_alerts_20260810.db"

def init_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        pushover_user_key TEXT,
        pushover_enabled INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

def get_connection():
    # Safe locally; on Railway, /app/data must be the mounted volume.
    os.makedirs(DATA_DIR, exist_ok=True)
    return sqlite3.connect(DB_NAME)


# ==========================
# CREATE DATABASE
# ==========================

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT,
            target_price REAL,
            direction TEXT DEFAULT 'ABOVE',
            status TEXT DEFAULT 'ACTIVE'
        )
    """)

    cursor.execute("PRAGMA table_info(alerts)")
    columns = [row[1] for row in cursor.fetchall()]

    if "direction" not in columns:
        cursor.execute("""
            ALTER TABLE alerts
            ADD COLUMN direction TEXT DEFAULT 'ABOVE'
        """)

    if "status" not in columns:
        cursor.execute("""
            ALTER TABLE alerts
            ADD COLUMN status TEXT DEFAULT 'ACTIVE'
        """)

    conn.commit()
    conn.close()
    
    # Create user notification settings table
    init_users()


# ==========================
# ADD ALERT
# ==========================

def add_alert(user_id, symbol, price, direction):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts (
            user_id,
            symbol,
            target_price,
            direction
        )
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        symbol,
        price,
        direction
    ))

    conn.commit()
    conn.close()


# ==========================
# GET USER ACTIVE ALERTS
# ==========================

def get_user_alerts(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM alerts
        WHERE user_id = ?
        AND status = 'ACTIVE'
        ORDER BY id DESC
    """, (user_id,))

    alerts = cursor.fetchall()
    conn.close()

    return alerts


# ==========================
# GET ALL ACTIVE ALERTS
# ==========================

def get_active_alerts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM alerts
        WHERE status = 'ACTIVE'
    """)

    alerts = cursor.fetchall()
    conn.close()

    return alerts


# ==========================
# REMOVE SINGLE ALERT
# ==========================

def remove_alert(alert_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alerts
        SET status = 'DONE'
        WHERE id = ?
    """, (alert_id,))

    conn.commit()
    conn.close()


# ==========================
# REMOVE MULTIPLE ALERTS
# ==========================

def remove_multiple_alerts(alert_ids):
    conn = get_connection()
    cursor = conn.cursor()

    for alert_id in alert_ids:
        cursor.execute("""
            UPDATE alerts
            SET status = 'DONE'
            WHERE id = ?
        """, (alert_id,))

    conn.commit()
    conn.close()


# ==========================
# DISABLE ALERT AFTER HIT
# ==========================

def disable_alert(alert_id):
    remove_alert(alert_id)


# ==========================
# PUSHOVER SETTINGS
# ==========================

def save_pushover_key(telegram_id, user_key):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO users
        (
            telegram_id,
            pushover_user_key,
            pushover_enabled
        )
        VALUES (?, ?, 1)
    """, (
        telegram_id,
        user_key
    ))

    conn.commit()
    conn.close()



def get_pushover_key(telegram_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pushover_user_key
        FROM users
        WHERE telegram_id = ?
        AND pushover_enabled = 1
    """, (telegram_id,))

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return None



# ==========================
# CHECK PUSHOVER STATUS
# ==========================

def get_pushover_status(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pushover_enabled
        FROM users
        WHERE telegram_id = ?
    """, (user_id,))

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return 0



# ==========================
# DISABLE PUSHOVER
# ==========================

def disable_pushover(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET pushover_enabled = 0
        WHERE telegram_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

# ==========================
# ENABLE PUSHOVER
# ==========================

def enable_pushover(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET pushover_enabled = 1
        WHERE telegram_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()





# ==========================
# GET PUSHOVER SETTINGS
# ==========================

def get_pushover_settings(user_id):

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            pushover_enabled,
            pushover_user_key
        FROM users
        WHERE telegram_id = ?
    """, (user_id,))


    result = cursor.fetchone()


    conn.close()


    if result:

        return result[0], result[1]


    return 0, None
