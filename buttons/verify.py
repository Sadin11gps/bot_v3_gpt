from utils import db

def handle(bot, message):
    db.add_user(message.from_user.id, message.from_user.username)
    db.update_button(message.from_user.id, 'VERIFY 💎')
    bot.send_message(message.chat.id, 'VERIFY 💎 দেখানো হচ্ছে...')
