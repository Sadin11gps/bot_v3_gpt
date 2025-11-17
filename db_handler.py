# db_handler.py
import os
import psycopg2
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# --- ১. ডেটাবেস সংযোগ ফাংশন ---
def connect_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# --- ২. ইউজারের ব্যালেন্স ফাংশন ---
def get_user_balance(user_id):
    conn = connect_db()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            return float(result[0])
        return 0.0
    except Exception as e:
        logger.error(f"Error fetching balance for user {user_id}: {e}")
        return None
    finally:
        conn.close()

def update_balance(user_id, amount):
    """
    ব্যালেন্স আপডেট করে। amount ধনাত্মক হলে যোগ, ঋণাত্মক হলে কেটে দেয়।
    """
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            new_balance = float(result[0]) + float(amount)
            cursor.execute("UPDATE users SET balance = %s WHERE user_id = %s", (new_balance, user_id))
            conn.commit()
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error updating balance for user {user_id}: {e}")
        return False
    finally:
        conn.close()

# --- ৩. ইউজার ডেটা ফাংশন ---
def get_user_data(user_id):
    conn = connect_db()
    if not conn:
        return {}
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT user_id, username, first_name, balance, wallet_address, referrer_id, refer_balance FROM users WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        if result:
            keys = ["user_id", "username", "first_name", "balance", "wallet_address", "referrer_id", "refer_balance"]
            return dict(zip(keys, result))
        return {}
    except Exception as e:
        logger.error(f"Error fetching user data for {user_id}: {e}")
        return {}
    finally:
        conn.close()

# --- ৪. উইথড্র রিকোয়েস্ট রেকর্ড --- 
def record_withdraw_request(user_id, amount, wallet_address):
    conn = connect_db()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO withdraw_requests (user_id, amount, wallet_address, status, created_at) VALUES (%s, %s, %s, %s, %s) RETURNING request_id",
            (user_id, amount, wallet_address, "pending", datetime.now(timezone.utc))
        )
        request_id = cursor.fetchone()[0]
        conn.commit()
        return request_id
    except Exception as e:
        logger.error(f"Error recording withdraw request for user {user_id}: {e}")
        return None
    finally:
        conn.close()

# --- ৫. উইথড্র স্ট্যাটাস আপডেট ---
def update_withdraw_status(request_id, new_status):
    conn = connect_db()
    if not conn:
        return False, None
    cursor = conn.cursor()
    try:
        # request এর ইউজার আইডি বের করা
        cursor.execute("SELECT user_id FROM withdraw_requests WHERE request_id = %s AND status = 'pending'", (request_id,))
        result = cursor.fetchone()
        if not result:
            return False, None
        user_id = result[0]
        cursor.execute("UPDATE withdraw_requests SET status = %s WHERE request_id = %s", (new_status, request_id))
        conn.commit()
        return True, user_id
    except Exception as e:
        logger.error(f"Error updating withdraw status for request {request_id}: {e}")
        return False, None
    finally:
        conn.close()
