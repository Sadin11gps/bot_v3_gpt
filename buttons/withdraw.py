import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from db_handler import connect_db, update_balance, get_user_balance, record_withdraw_request, update_withdraw_status, get_user_data

logger = logging.getLogger(__name__)

# --- কনভার্সেশন স্টেটস ---
WITHDRAW_AMOUNT_INPUT, WITHDRAW_WALLET_INPUT = range(2)

# অ্যাডমিন আইডি
ADMIN_ID = os.environ.get("ADMIN_ID")  # নিশ্চিত করুন যে এটি সঠিক

# --- কমাণ্ড ফাংশন ---
async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    balance = get_user_balance(user_id)

    if balance is None or balance <= 0:
        await update.message.reply_text("আপনার অ্যাকাউন্টে কোনো ব্যালেন্স নেই।")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton("❌ বাতিল করুন", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"আপনি কত টাকা উত্তোলন করতে চান?\nআপনার বর্তমান ব্যালেন্স: {balance:.2f} টাকা।\n\n(সর্বনিম্ন উত্তোলন: 100 টাকা।)",
        reply_markup=reply_markup
    )
    return WITHDRAW_AMOUNT_INPUT

# --- হ্যান্ডলার ফাংশন ---
async def handle_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = float(update.message.text)
        user_id = update.effective_user.id
        balance = get_user_balance(user_id)

        if amount < 100:
            await update.message.reply_text("উত্তোলনের পরিমাণ সর্বনিম্ন 100 টাকা হতে হবে। আবার লিখুন:")
            return WITHDRAW_AMOUNT_INPUT
        if amount > balance:
            await update.message.reply_text(f"আপনার ব্যালেন্স যথেষ্ট নয় ({balance:.2f} টাকা)। আবার লিখুন:")
            return WITHDRAW_AMOUNT_INPUT

        context.user_data['withdraw_amount'] = amount

        user_data = get_user_data(user_id)
        current_wallet = user_data.get('wallet_address')

        if current_wallet:
            context.user_data['wallet_address'] = current_wallet
            keyboard = [
                [InlineKeyboardButton(f"✅ এটি ব্যবহার করুন ({current_wallet})", callback_data="wallet_confirm")],
                [InlineKeyboardButton("নতুন ঠিকানা লিখুন", callback_data="wallet_new")],
                [InlineKeyboardButton("❌ বাতিল করুন", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "এই ঠিকানায় কি টাকা তুলতে চান?",
                reply_markup=reply_markup
            )
            return WITHDRAW_WALLET_INPUT
        else:
            keyboard = [[InlineKeyboardButton("❌ বাতিল করুন", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "অনুগ্রহ করে আপনার বিকাশ/নগদ/রকেট নম্বর লিখুন:",
                reply_markup=reply_markup
            )
            return WITHDRAW_WALLET_INPUT

    except ValueError:
        await update.message.reply_text("পরিমাণটি সংখ্যায় লিখুন।")
        return WITHDRAW_AMOUNT_INPUT

async def handle_withdraw_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    amount = context.user_data.get('withdraw_amount')

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        choice = query.data

        if choice == "wallet_confirm":
            wallet_address = context.user_data.get('wallet_address')
        elif choice == "wallet_new":
            keyboard = [[InlineKeyboardButton("❌ বাতিল করুন", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("অনুগ্রহ করে নতুন ওয়ালেট ঠিকানা লিখুন:", reply_markup=reply_markup)
            return WITHDRAW_WALLET_INPUT
        else:
            return await cancel_withdraw_conversation(update, context)
    else:
        wallet_address = update.message.text.strip()

    request_id = record_withdraw_request(user_id, amount, wallet_address)
    update_balance(user_id, -amount)

    await update.effective_chat.send_message(
        f"✅ উত্তোলন অনুরোধ সফল!\nপরিমাণ: {amount:.2f} টাকা\nওয়ালেট: {wallet_address}\n\nঅ্যাডমিন প্রক্রিয়াকরণ করবেন।"
    )

    admin_message = f"🚨 নতুন উত্তোলন অনুরোধ (ID: {request_id}) 🚨\n\nইউজার ID: {user_id}\nপরিমাণ: {amount:.2f} টাকা\nওয়ালেট: {wallet_address}"
    keyboard = [
        [InlineKeyboardButton("✅ সম্পন্ন", callback_data=f"withdraw_accept_{request_id}_{amount}")],
        [InlineKeyboardButton("❌ বাতিল", callback_data=f"withdraw_reject_{request_id}_{amount}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if ADMIN_ID:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, reply_markup=reply_markup)

    return ConversationHandler.END

async def cancel_withdraw_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ উত্তোলন বাতিল করা হয়েছে।")
    else:
        await update.message.reply_text("❌ উত্তোলন বাতিল করা হয়েছে।")
    return ConversationHandler.END

async def withdraw_admin_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    action = data[0]
    status = data[1]
    request_id = int(data[2])
    amount = float(data[3])

    if str(query.from_user.id) != ADMIN_ID:
        await query.answer("আপনার অনুমতি নেই।")
        return

    new_status = 'completed' if status == 'accept' else 'rejected'
    success, user_id = update_withdraw_status(request_id, new_status)

    if success:
        if new_status == 'completed':
            user_message = f"✅ আপনার উত্তোলন অনুরোধ (ID: {request_id}) সম্পন্ন হয়েছে। {amount:.2f} টাকা।"
        else:
            user_message = f"❌ আপনার উত্তোলন অনুরোধ (ID: {request_id}) বাতিল হয়েছে। {amount:.2f} টাকা ফেরত।"
            update_balance(user_id, amount)

        try:
            await context.bot.send_message(chat_id=user_id, text=user_message)
        except Exception as e:
            logger.error(f"User message error {user_id}: {e}")

        await query.edit_message_text(f"✅ অনুরোধ (ID: {request_id}) '{new_status}' করা হয়েছে।")
    else:
        await query.edit_message_text(f"ত্রুটি: অনুরোধ (ID: {request_id}) আগে থেকেই প্রক্রিয়াকৃত।")

# --- ConversationHandler ---
withdraw_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("withdraw", withdraw_command)],
    states={
        WITHDRAW_AMOUNT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_amount)],
        WITHDRAW_WALLET_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw_wallet),
            CallbackQueryHandler(handle_withdraw_wallet, pattern="^(wallet_confirm|wallet_new)$")
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel_withdraw_conversation),
        CallbackQueryHandler(cancel_withdraw_conversation, pattern="^cancel")
    ]
)
