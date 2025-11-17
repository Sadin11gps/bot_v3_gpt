import os
import psycopg2
import logging
from datetime import datetime, timedelta
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# --- ডেটাবেস সংযোগ ---
def connect_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# --- কনভার্সেশন স্টেটস ---
SELECT_METHOD, SUBMIT_TNX = range(2)

# কনস্ট্যান্ট
VERIFY_AMOUNT = 50.00
VERIFY_DAYS = 30
PAYMENT_NUMBER = "01338553254"

# --- হেল্পার ফাংশন ---
async def menu_home(message, bot):
    """Circular Import এড়াতে ডামি ফাংশন"""
    try:
        await bot.send_message(chat_id=message.chat.id, text="🔙 প্রধান মেনু")
    except Exception as e:
        logger.error(f"Error in menu_home: {e}")

def format_verify_status(user_id):
    """ইউজারের ভেরিফাই স্ট্যাটাস চেক করে মেসেজ ও বাটন তৈরি করে"""
    conn = connect_db()
    if not conn:
        return "❌ দুঃখিত! ডেটাবেস সংযোগে সমস্যা হচ্ছে।", None

    cursor = conn.cursor()
    message = ""
    reply_markup = None

    try:
        cursor.execute(
            "SELECT is_premium, expiry_date, verify_expiry FROM users WHERE user_id=%s", (user_id,)
        )
        status = cursor.fetchone()
        if status:
            is_premium, expiry_date, verify_expiry = status
            now = datetime.utcnow()

            if is_premium and expiry_date and expiry_date > now:
                days = (expiry_date - now).days
                message += f"✨ **PREMIUM USER** ✨\n**PREMIUM TIME** : **{days} দিন বাকি**\nআপনার অ্যাকাউন্ট ভেরিফাইড আছে।"
            elif verify_expiry and verify_expiry > now:
                days = (verify_expiry - now).days
                message += f"✅ **ভেরিফাইড ইউজার** ✅\nVerify Time: **{days} দিন বাকি**"
            else:
                message += "⚠️ **আপনার একাউন্টটি ভেরিফাই করা নেই!**\nভেরিফাই করুন।"
                keyboard = [[InlineKeyboardButton("✅ VERIFY", callback_data="verify_start")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"Error formatting verify status for user {user_id}: {e}")
        message = "ভেরিফাই স্ট্যাটাস আনতে সমস্যা হচ্ছে।"
    finally:
        if conn:
            conn.close()

    return message, reply_markup

# --- মূল হ্যান্ডলার --- #
async def verify_command(message, bot):
    """VERIFY মেসেজ হ্যান্ডলার"""
    user_id = message.from_user.id
    msg, markup = format_verify_status(user_id)
    await bot.send_message(chat_id=message.chat.id, text=msg, reply_markup=markup, parse_mode='Markdown')

async def start_verify_flow(callback_query, bot):
    """VERIFY বাটন চাপলে পেমেন্ট মেথড দেখায়"""
    await bot.answer_callback_query(callback_query.id)
    keyboard = [
        [InlineKeyboardButton(f"💸 Bkash - {PAYMENT_NUMBER}", callback_data="method_Bkash")],
        [InlineKeyboardButton(f"💰 Nagad - {PAYMENT_NUMBER}", callback_data="method_Nagad")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                text="**Method সিলেক্ট করুন**",
                                reply_markup=markup,
                                parse_mode='Markdown')
    return SELECT_METHOD

async def submit_tnx_form(callback_query, bot, user_data):
    """পেমেন্ট মেথড সিলেক্টের পর Tnx ID রিকোয়েস্ট"""
    await bot.answer_callback_query(callback_query.id)
    method = callback_query.data.split('_')[1]
    user_data['payment_method'] = method

    msg = (
        f"⛔ এই **{method}** Personal নাম্বারে **৳{VERIFY_AMOUNT:.2f}** টাকা পরিশোধ করুন এবং **trxID পূরণ** করুন।\n"
        "👇 trxID মেসেজে পাঠান।"
    )
    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                text=msg,
                                parse_mode='Markdown')
    return SUBMIT_TNX

async def handle_tnx_submission(message, bot, user_data):
    """Tnx ID গ্রহণ এবং DB-এ সেভ করা"""
    tnx_id = message.text.strip()
    method = user_data.get('payment_method')
    admin_id = os.environ.get("ADMIN_ID")

    if not method:
        await bot.send_message(chat_id=message.chat.id, text="❌ পেমেন্ট মেথড পাওয়া যায়নি।")
        return

    conn = connect_db()
    if not conn:
        await bot.send_message(chat_id=message.chat.id, text="❌ ডেটাবেস সংযোগে সমস্যা।")
        return

    cursor = conn.cursor()
    request_id = None
    try:
        cursor.execute(
            "INSERT INTO verify_requests(user_id, username, amount, method, tnx_id, status) VALUES (%s,%s,%s,%s,%s,'pending') RETURNING request_id",
            (message.from_user.id, message.from_user.username, VERIFY_AMOUNT, method, tnx_id)
        )
        request_id = cursor.fetchone()[0]
        conn.commit()

        # অ্যাডমিন মেসেজ
        if admin_id:
            kb = [[InlineKeyboardButton("✅ ACCEPT", callback_data=f"verify_accept_{request_id}_{message.from_user.id}"),
                   InlineKeyboardButton("❌ REJECT", callback_data=f"verify_reject_{request_id}_{message.from_user.id}")]]
            markup = InlineKeyboardMarkup(kb)
            admin_msg = f"🔔 নতুন ভেরিফাই রিকোয়েস্ট\n👤 {message.from_user.first_name}\n🆔 {message.from_user.id}\n💳 {method}\n💸 {VERIFY_AMOUNT:.2f}\nTnx ID: {tnx_id}"
            await bot.send_message(chat_id=admin_id, text=admin_msg, reply_markup=markup, parse_mode='Markdown')

        await bot.send_message(chat_id=message.chat.id, text="🎉 VERIFY রিকোয়েস্ট জমা হয়েছে।", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error saving verify request: {e}")
        await bot.send_message(chat_id=message.chat.id, text="❌ রিকোয়েস্ট সেভ করতে সমস্যা হয়েছে।")
    finally:
        if conn:
            conn.close()

async def cancel_conversation(message, bot):
    """কথোপকথন বাতিল হ্যান্ডলার"""
    await menu_home(message, bot)

async def admin_verify_callback(callback_query, bot):
    """অ্যাডমিন ACCEPT/REJECT হ্যান্ডলার"""
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data.split('_')
    action = data[1]
    request_id = int(data[2])
    target_user_id = int(data[3])
    admin_name = callback_query.from_user.first_name

    conn = connect_db()
    if not conn:
        await bot.send_message(chat_id=callback_query.message.chat.id, text="DB সংযোগ ব্যর্থ।")
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT status FROM verify_requests WHERE request_id=%s", (request_id,))
        current_status = cursor.fetchone()[0]

        if current_status != 'pending':
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        text=f"🚫 Already {current_status} by {admin_name}")
            return

        cursor.execute("UPDATE verify_requests SET status=%s WHERE request_id=%s", (action, request_id))
        conn.commit()

        if action == 'accept':
            new_expiry = datetime.utcnow() + timedelta(days=VERIFY_DAYS)
            cursor.execute("UPDATE users SET verify_expiry=%s WHERE user_id=%s", (new_expiry, target_user_id))
            conn.commit()
            user_msg = f"✅ VERIFY ACCEPTED! মেয়াদ: {VERIFY_DAYS} দিন।"
            admin_text = f"✅ Request ACCEPTED by {admin_name}"
        else:
            user_msg = "❌ VERIFY REJECTED! আবার চেষ্টা করুন।"
            admin_text = f"❌ Request REJECTED by {admin_name}"

        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=admin_text)
        await bot.send_message(chat_id=target_user_id, text=user_msg)
    except Exception as e:
        logger.error(f"Error processing admin verify callback: {e}")
        await bot.send_message(chat_id=callback_query.message.chat.id, text="Processing error!")
    finally:
        if conn:
            conn.close()
