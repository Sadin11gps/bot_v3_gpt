from telebot import types

def button1_handler(bot, message):
    bot.reply_to(message, "তুমি Button 1 এ ক্লিক করেছো! 😎")
