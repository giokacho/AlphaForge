import json
import os
from datetime import datetime
from auth import hash_password
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_outputs (
            id SERIAL PRIMARY KEY,
            bot_name TEXT NOT NULL,
            run_date TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def save_bot_output(bot_name: str, payload: dict) -> bool:
    run_date = datetime.utcnow().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO bot_outputs (bot_name, run_date, payload, created_at)
            VALUES (%s, %s, %s, %s)
        ''', (bot_name, run_date, json.dumps(payload), datetime.utcnow()))
        conn.commit()
        return True
    except Exception as e:
        print(f"[database] save_bot_output error for '{bot_name}': {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_latest_run_time() -> str | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(created_at) FROM bot_outputs")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0].isoformat() if row and row[0] else None

def get_latest_output(bot_name: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT payload FROM bot_outputs
        WHERE bot_name = %s
        ORDER BY created_at DESC
        LIMIT 1
    ''', (bot_name,))
    row = cursor.fetchone()
    cursor.close()
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
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, hashed_password, created_at)
            VALUES (%s, %s, %s)
        ''', (username, hashed, datetime.utcnow()))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_user(username: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, hashed_password, is_active, created_at
        FROM users WHERE username = %s
    ''', (username,))
    row = cursor.fetchone()
    cursor.close()
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_active = FALSE WHERE username = %s', (username,))
    conn.commit()
    cursor.close()
    conn.close()

def delete_user(username: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username = %s', (username,))
    conn.commit()
    cursor.close()
    conn.close()

# Ensure tables exist on import
init_db()
