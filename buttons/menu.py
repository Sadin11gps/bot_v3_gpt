from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

def handle(bot):
    """Menu button handler"""

    @bot.message_handler(commands=['menu'])
    @bot.callback_query_handler(func=lambda call: call.data == 'menu_home')
    def menu_handler(message_or_call):
        text = "Welcome to Main Menu. Choose an option:"
        keyboard = [
            [InlineKeyboardButton("Profile", callback_data='profile')],
            [InlineKeyboardButton("Tasks", callback_data='task')],
            [InlineKeyboardButton("Premium", callback_data='premium')],
            [InlineKeyboardButton("Refer", callback_data='refer')],
            [InlineKeyboardButton("Withdraw", callback_data='withdraw')],
            [InlineKeyboardButton("Support", callback_data='support')],
            [InlineKeyboardButton("History", callback_data='history')]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        if hasattr(message_or_call, 'message'):  # callback_query
            bot.edit_message_text(chat_id=message_or_call.message.chat.id,
                                  message_id=message_or_call.message.message_id,
                                  text=text,
                                  reply_markup=markup)
        else:  # normal message
            bot.send_message(chat_id=message_or_call.chat.id,
                             text=text,
                             reply_markup=markup)
