import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.db import connect_db  # আগে তুমি db.py তে connect_db তৈরি করেছো

logger = logging.getLogger(__name__)

async def handle(bot, update):
    user_id = update.effective_user.id
    conn = connect_db()
    status = None

    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT is_premium, expiry_date, premium_balance, free_income,
                       refer_balance, salary_balance, total_withdraw, verify_expiry_date
                FROM users
                WHERE telegram_id = %s
            """, (user_id,))
            status = cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
        finally:
            cursor.close()
            conn.close()

    if status:
        is_premium, expiry_date, premium_balance, free_income, refer_balance, salary_balance, total_withdraw, verify_expiry_date = status
        premium_status = "Active" if is_premium and expiry_date and expiry_date >= datetime.now().date() else "Inactive"
        expiry_date_text = expiry_date.strftime("%Y-%m-%d") if expiry_date else "N/A"
        verify_status = "Verified" if verify_expiry_date and verify_expiry_date >= datetime.now().date() else "Not Verified"

        message = (
            f"**Profile Info**\n"
            f"User ID: `{user_id}`\n"
            f"Premium Status: {premium_status}\n"
            f"Premium Expiry: {expiry_date_text}\n"
            f"Verify Status: {verify_status}\n\n"
            f"Premium Balance: {premium_balance:.2f}\n"
            f"Free Income: {free_income:.2f}\n"
            f"Refer Balance: {refer_balance:.2f}\n"
            f"Salary Balance: {salary_balance:.2f}\n"
            f"Total Withdraw: {total_withdraw:.2f}"
        )

        keyboard = [
            [InlineKeyboardButton("Back to Menu 🏠", callback_data='menu_home')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text("Profile not found. Start /start first.")
