from utils import db

def handle(bot, message):
    # ইউজার ডাটাবেসে সেভ করা
    db.add_user(message.from_user.id, message.from_user.username)
    db.update_button(message.from_user.id, 'MENU🏠')

    bot.send_message(message.chat.id, 'MENU🏠 দেখানো হচ্ছে...')
