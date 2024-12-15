from telebot import types
from utils.common import create_main_markup
from utils.adduser import *
from utils.backup import *
from utils.command import *
from utils.deleteuser import *
from utils.edituser import *
from utils.search import *
from utils.serverinfo import *

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_admin(message.from_user.id):
        markup = create_main_markup()
        bot.reply_to(message, "Welcome to the User Management Bot!", reply_markup=markup)
    else:
        bot.reply_to(message, "Unauthorized access. You do not have permission to use this bot.")

if __name__ == '__main__':
    bot.polling(none_stop=True)
