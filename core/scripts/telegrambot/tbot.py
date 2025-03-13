from telebot import types
from utils import *
import threading
import time

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_admin(message.from_user.id):
        markup = create_main_markup()
        bot.reply_to(message, "Welcome to the User Management Bot!", reply_markup=markup)
    else:
        bot.reply_to(message, "Unauthorized access. You do not have permission to use this bot.")

def monitoring_thread():
    while True:
        monitor_system_resources()
        time.sleep(60)

if __name__ == '__main__':
    monitor_thread = threading.Thread(target=monitoring_thread, daemon=True)
    monitor_thread.start()
    version_thread = threading.Thread(target=version_monitoring, daemon=True)
    version_thread.start()
    bot.polling(none_stop=True)
