# admin.py

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from db_handler import get_pending_withdrawals, update_withdraw_status, update_balance

ADMIN_ID = os.environ.get("ADMIN_ID")  # নিশ্চিত করো পরিবেশে আছে

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """অ্যাডমিন প্যানেল দেখাবে এবং Pending Withdraw Requests লিস্ট করবে"""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই প্যানেল দেখার অনুমোদিত নন।")
        return

    # Pending withdraw requests ফ্রেচ করা
    pending_requests = get_pending_withdrawals()
    if not pending_requests:
        await update.message.reply_text("বর্তমানে কোনো Pending Withdraw Requests নেই।")
        return

    for req in pending_requests:
        request_id = req['id']
        uid = req['user_id']
        amount = req['amount']
        wallet = req['wallet_address']

        keyboard = [
            [InlineKeyboardButton("✅ সম্পন্ন", callback_data=f"withdraw_accept_{request_id}_{amount}")],
            [InlineKeyboardButton("❌ বাতিল", callback_data=f"withdraw_reject_{request_id}_{amount}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"🚨 নতুন উত্তোলন অনুরোধ 🚨\n\n"
            f"Request ID: {request_id}\n"
            f"User ID: {uid}\n"
            f"Amount: {amount:.2f} টাকা\n"
            f"Wallet: {wallet}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=message, reply_markup=reply_markup)

# অ্যাডমিনের CallbackQueryHandler (এইটা main.py বা conversation handler এ যুক্ত করা যাবে)
async def admin_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    action = data[0]  # withdraw
    status = data[1]  # accept or reject
    request_id = int(data[2])
    amount = float(data[3])

    if str(query.from_user.id) != ADMIN_ID:
        await query.answer("❌ অনুমোদিত নন।")
        return

    new_status = 'completed' if status == 'accept' else 'rejected'
    success, user_id = update_withdraw_status(request_id, new_status)

    if success:
        if new_status == 'rejected':
            update_balance(user_id, amount)  # টাকা ফেরত
            user_message = f"❌ আপনার উত্তোলন অনুরোধ (ID: {request_id}) বাতিল করা হয়েছে।"
        else:
            user_message = f"✅ আপনার উত্তোলন অনুরোধ (ID: {request_id}) সম্পন্ন হয়েছে।"

        await context.bot.send_message(chat_id=user_id, text=user_message)
        await query.edit_message_text(f"✅ অনুরোধ (ID: {request_id}) '{new_status}' করা হয়েছে।")
    else:
        await query.edit_message_text(f"⚠️ অনুরোধ (ID: {request_id}) আগে থেকেই প্রক্রিয়াকৃত।")
