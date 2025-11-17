import os
from telebot import TeleBot
from buttons import menu, profile, task, premium, verify, refer, support, history, withdraw
from admin import admin_panel

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)

# --- বাটন হ্যান্ডলার কল --- #
menu.handle(bot)
profile.handle(bot)
task.handle(bot, message)
premium.handle(bot)
verify.handle(bot)
refer.handle(bot)
support.handle(bot)
history.handle(bot)
withdraw.handle(bot)

# --- এডমিন হ্যান্ডলার কল --- #
admin_panel.handle(bot)

# --- বট চালু --- #
if __name__ == "__main__":
    bot.infinity_polling()
