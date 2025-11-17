import telebot
from buttons import menu, profile, task, premium, verify, refer, support, history, withdraw
from utils import db
from admin import view_users, delete_user, ADMIN_ID

TOKEN = '8571457538:AAHdD81WRpJa_QiB5Wd9qNafxoH7FbN8EO4'
bot = telebot.TeleBot(TOKEN)

# ডাটাবেস টেবিল তৈরি
db.create_table()

# মেনু কীবোর্ড
menu_keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2)
menu_keyboard.add(
    telebot.types.KeyboardButton('MENU🏠'),
    telebot.types.KeyboardButton('PROFILE 👤'),
    telebot.types.KeyboardButton('TASK 🏅'),
    telebot.types.KeyboardButton('PREMIUM ✨'),
    telebot.types.KeyboardButton('VERIFY 💎'),
    telebot.types.KeyboardButton('REFER 📢'),
    telebot.types.KeyboardButton('SUPPORT ☎️'),
    telebot.types.KeyboardButton('HISTORY 📃'),
    telebot.types.KeyboardButton('WITHDRAW 🏦')
)

# স্টার্ট কমান্ড
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'বট চালু হয়েছে!', reply_markup=menu_keyboard)

# বাটন হ্যান্ডলার
@bot.message_handler(func=lambda message: message.text == 'MENU🏠')
def menu_handler(message):
    menu.handle(bot, message)

@bot.message_handler(func=lambda message: message.text == 'PROFILE 👤')
def profile_handler(message):
    profile.handle(bot, message)

@bot.message_handler(func=lambda message: message.text == 'TASK 🏅')
def task_handler(message):
    task.handle(bot, message)

@bot.message_handler(func=lambda message: message.text == 'PREMIUM ✨')
def premium_handler(message):
    premium.handle(bot, message)

@bot.message_handler(func=lambda message: message.text == 'VERIFY 💎')
def verify_handler(message):
    verify.handle(bot, message)

@bot.message_handler(func=lambda message: message.text == 'REFER 📢')
def refer_handler(message):
    refer.handle(bot, message)

@bot.message_handler(func=lambda message: message.text == 'SUPPORT ☎️')
def support_handler(message):
    support.handle(bot, message)

@bot.message_handler(func=lambda message: message.text == 'HISTORY 📃')
def history_handler(message):
    history.handle(bot, message)

@bot.message_handler(func=lambda message: message.text == 'WITHDRAW 🏦')
def withdraw_handler(message):
    withdraw.handle(bot, message)

# =======================
# Admin কমান্ড: view users
# =======================
@bot.message_handler(commands=['view_users'])
def handle_view_users(message):
    view_users(bot, message)

# =======================
# Admin কমান্ড: delete user
# =======================
@bot.message_handler(commands=['delete_user'])
def handle_delete_user(message):
    if message.from_user.id == ADMIN_ID:
        try:
            telegram_id = int(message.text.split()[1])
            delete_user(bot, message, telegram_id)
        except:
            bot.send_message(message.chat.id, "Usage: /delete_user <telegram_id>")
    else:
        bot.send_message(message.chat.id, "You are not admin!")

# বট চালু রাখা
bot.polling(non_stop=True, interval=0, timeout=20)
