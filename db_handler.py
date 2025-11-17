import os
import psycopg2
import logging

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

# --- ২. ইউজারের ব্যালেন্স ফ্রেচ করা ---
def get_user_balance(user_id: int) -> float:
    conn = connect_db()
    if not conn:
        return 0.0
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return float(result[0]) if result else 0.0
    except Exception as e:
        logger.error(f"Error fetching balance for user {user_id}: {e}")
        return 0.0
    finally:
        conn.close()

# --- ৩. ব্যালেন্স আপডেট ফাংশন ---
def update_balance(user_id: int, amount: float) -> bool:
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating balance for user {user_id}: {e}")
        return False
    finally:
        conn.close()

# --- ৪. উইথড্র রিকোয়েস্ট রেকর্ড করা ---
def record_withdraw_request(user_id: int, amount: float, wallet_address: str) -> int:
    conn = connect_db()
    if not conn:
        return 0
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO withdraw_requests (user_id, amount, wallet_address, status) VALUES (%s, %s, %s, 'pending') RETURNING id",
            (user_id, amount, wallet_address)
        )
        request_id = cursor.fetchone()[0]
        conn.commit()
        return request_id
    except Exception as e:
        logger.error(f"Error recording withdraw request for user {user_id}: {e}")
        return 0
    finally:
        conn.close()

# --- ৫. pending withdraws ফ্রেচ করা (অ্যাডমিনের জন্য) ---
def get_pending_withdrawals():
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, user_id, amount, wallet_address FROM withdraw_requests WHERE status='pending'")
        results = cursor.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error fetching pending withdrawals: {e}")
        return []
    finally:
        conn.close()

# --- ৬. উইথড্র স্ট্যাটাস আপডেট করা ---
def update_withdraw_status(request_id: int, new_status: str):
    conn = connect_db()
    if not conn:
        return False, None
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM withdraw_requests WHERE id = %s AND status='pending'", (request_id,))
        row = cursor.fetchone()
        if not row:
            return False, None
        user_id = row[0]
        cursor.execute("UPDATE withdraw_requests SET status=%s WHERE id=%s", (new_status, request_id))
        conn.commit()
        return True, user_id
    except Exception as e:
        logger.error(f"Error updating withdraw status for request {request_id}: {e}")
        return False, None
    finally:
        conn.close()

# --- ৭. ইউজারের ডাটা ফ্রেচ করা (যেমন wallet_address) ---
def get_user_data(user_id: int):
    conn = connect_db()
    if not conn:
        return {}
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT wallet_address, balance, refer_balance FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if not row:
            return {}
        return {
            "wallet_address": row[0],
            "balance": float(row[1]),
            "refer_balance": float(row[2])
        }
    except Exception as e:
        logger.error(f"Error fetching data for user {user_id}: {e}")
        return {}
    finally:
        conn.close()
