import sqlite3
import json
import os
from datetime import datetime
from auth import hash_password

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "users.db"))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_outputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_name TEXT NOT NULL,
            run_date TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_bot_output(bot_name: str, payload: dict) -> bool:
    run_date = datetime.utcnow().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO bot_outputs (bot_name, run_date, payload, created_at)
            VALUES (?, ?, ?, ?)
        ''', (bot_name, run_date, json.dumps(payload), datetime.utcnow()))
        conn.commit()
        return True
    except Exception as e:
        print(f"[database] save_bot_output error for '{bot_name}': {e}")
        return False
    finally:
        conn.close()

def get_latest_run_time() -> str | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT MAX(created_at) FROM bot_outputs").fetchone()
    conn.close()
    return row[0] if row and row[0] else None

def get_latest_output(bot_name: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT payload FROM bot_outputs
        WHERE bot_name = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (bot_name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            return None
    return None

def create_user(username: str, password: str) -> bool:
    password = password[:72]
    hashed = hash_password(password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, hashed_password, created_at)
            VALUES (?, ?, ?)
        ''', (username, hashed, datetime.utcnow()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, hashed_password, is_active, created_at
        FROM users WHERE username = ?
    ''', (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "username": row[1],
            "hashed_password": row[2],
            "is_active": bool(row[3]),
            "created_at": row[4]
        }
    return None

def deactivate_user(username: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_active = 0 WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def delete_user(username: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()

# Ensure DB exists on import
init_db()
