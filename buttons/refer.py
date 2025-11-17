import os
import psycopg2
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# --- ডেটাবেস সংযোগ ফাংশন ---
def connect_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"Database connection error in refer_handler: {e}")
        return None

# --- রেফারাল কমান্ড হ্যান্ডলার ---
async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    conn = connect_db()
    if not conn:
        await update.message.reply_text("❌ দুঃখিত! ডেটাবেস সংযোগে সমস্যা হচ্ছে।")
        return

    cursor = conn.cursor()
    message = ""

    try:
        # ১. Joining Bonus & Premium Reward রিয়েল টাইমে ফেচ
        cursor.execute("SELECT referral_bonus_joining, premium_reward_percent FROM settings LIMIT 1")
        result = cursor.fetchone()
        REFERRAL_BONUS_JOINING = result[0] if result else 40.0
        PREMIUM_REWARD_PERCENT = result[1] if result else 25

        # ২. ইউজারের রেফারাল ব্যালেন্স
        cursor.execute("SELECT refer_balance FROM users WHERE user_id=%s", (user_id,))
        result = cursor.fetchone()
        refer_balance = result[0] if result else 0.0

        # ৩. মোট রেফারাল সংখ্যা
        cursor.execute("SELECT COUNT(user_id) FROM users WHERE referrer_id=%s", (user_id,))
        referral_count = cursor.fetchone()[0]

        # ৪. রেফারাল লিংক
        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"

        # ৫. মেসেজ তৈরি
        message = (
            "🚀 রেফার করে উপার্জন করুন এবং বোটের বৈশিষ্ট্য উপভোগ করুন 💰\n"
            "🔥 **REFER REWARDS** 🔥\n\n"
            f"1️⃣ **NEW MEMBER JOINING**:\n"
            f"   **REWARD**: **{REFERRAL_BONUS_JOINING:.2f} ৳**\n"
            f"2️⃣ PREMIUM SUBSCRIPTION\n"
            f"   **REWARD**: **{PREMIUM_REWARD_PERCENT}%**\n\n"
            f"🆕 **FREE MEMBERS**: **{referral_count}**\n"
            "👑 **PREMIUM MEMBERS**: **0**\n"
            f"📌 **TOTAL REFERRALS**: **{referral_count}**\n\n"
            f"💲 **YOUR REFER BALANCE**: **{refer_balance:.2f} ৳**\n\n"
            f"🔗 **YOUR REFER LINK** 🔗\n"
            f"`{referral_link}`\n\n"
            "👉 এই লিঙ্কটি বন্ধুদের সঙ্গে শেয়ার করুন"
        )

    except Exception as e:
        logger.error(f"Referral data fetch error: {e}")
        message = "❌ রেফারেল তথ্য দেখাতে সমস্যা হচ্ছে।"
    finally:
        if conn:
            conn.close()

    await update.message.reply_text(message, parse_mode='Markdown')

# --- হ্যান্ডলার রেজিস্ট্রেশন ---
def handle(bot):
    from telegram.ext import CommandHandler
    bot.add_handler(CommandHandler("refer", refer_command))
