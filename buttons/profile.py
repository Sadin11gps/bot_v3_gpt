import logging
from datetime import datetime
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.db import connect_db

logger = logging.getLogger(__name__)

# Conversation State (যদি future এ ConversationHandler লাগবে)
PROFILE_STATE = 0

def handle(bot):
    """Main handler function for profile buttons"""
    
    @bot.message_handler(commands=['profile'])
    @bot.callback_query_handler(func=lambda call: call.data == 'profile')
    def profile_menu(message_or_call):
        """Show user profile"""
        if hasattr(message_or_call, 'from_user'):
            user_id = message_or_call.from_user.id
        else:
            user_id = message_or_call.from_user.id

        conn = connect_db()
        status = None
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        is_premium, expiry_date, premium_balance, free_income,
                        refer_balance, salary_balance, total_withdraw, wallet_address,
                        verify_expiry_date, referrer_id
                    FROM users
                    WHERE telegram_id = %s
                """, (user_id,))
                status = cursor.fetchone()
            except Exception as e:
                logger.error(f"Error fetching profile: {e}")
            finally:
                cursor.close()
                conn.close()

        if status and len(status) >= 10:
            is_premium, expiry_date, premium_balance, free_income, refer_balance, \
            salary_balance, total_withdraw, wallet_address, verify_expiry_date, referrer_id = status

            premium_status = "Active" if is_premium and expiry_date and expiry_date >= datetime.now().date() else "Inactive"
            expiry_text = expiry_date.strftime("%Y-%m-%d") if expiry_date else "N/A"
            verify_status = "Verified" if verify_expiry_date and verify_expiry_date >= datetime.now().date() else "Not Verified"

            text = (
                f"**Your Profile**\n"
                f"ID: `{user_id}`\n"
                f"Premium: {premium_status}\n"
                f"Expiry: {expiry_text}\n"
                f"Verification: {verify_status}\n\n"
                f"Premium Balance: {premium_balance:.2f}\n"
                f"Free Income: {free_income:.2f}\n"
                f"Refer Balance: {refer_balance:.2f}\n"
                f"Salary Balance: {salary_balance:.2f}\n"
                f"Total Withdraw: {total_withdraw:.2f}\n"
                f"Wallet: `{wallet_address or 'Not set'}`"
            )

            keyboard = [
                [InlineKeyboardButton("Set Wallet", callback_data='set_wallet')],
                [InlineKeyboardButton("Back to Menu", callback_data='menu_home')]
            ]
            markup = InlineKeyboardMarkup(keyboard)
        else:
            text = "Profile not found. Please /start first."
            markup = None

        # Message vs Callback
        if hasattr(message_or_call, 'message'):  # callback_query
            bot.edit_message_text(chat_id=message_or_call.message.chat.id,
                                  message_id=message_or_call.message.message_id,
                                  text=text,
                                  reply_markup=markup,
                                  parse_mode='Markdown')
        else:  # normal message
            bot.send_message(chat_id=message_or_call.chat.id,
                             text=text,
                             reply_markup=markup,
                             parse_mode='Markdown')
