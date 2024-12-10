import telebot
import subprocess
import qrcode
import io
import json
import os
import shlex
import re
from dotenv import load_dotenv
from telebot import types

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_USER_IDS = json.loads(os.getenv('ADMIN_USER_IDS'))
CLI_PATH = '/etc/hysteria/core/cli.py'
BACKUP_DIRECTORY = '/opt/hysbackup'
USER_DATA_FILE = 'user_data.json'

bot = telebot.TeleBot(API_TOKEN)

diagnose_mode = False

def run_cli_command(command):
    try:
        args = shlex.split(command)
        result = subprocess.check_output(args, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        return f'Error: {e.output.decode("utf-8")}'

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def create_main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Add User', 'Show User')
    markup.row('Delete User', 'Server Info')
    markup.row('Backup Server', 'Toggle Diagnose Mode')
    return markup

def create_user_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('View Available Items', 'My Configuration')
    return markup

def is_admin(user_id):
    return user_id in ADMIN_USER_IDS

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_admin(message.from_user.id):
        markup = create_main_markup()
        bot.reply_to(message, "Welcome to the User Management Bot!", reply_markup=markup)
    else:
        markup = create_user_markup()
        bot.reply_to(message, "Welcome! How can I assist you today?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'View Available Items')
def view_items(message):
    items = ["Basic Plan - 10GB - $5", "Premium Plan - 50GB - $15"]
    response = "Available Plans:\n" + "\n".join(items)
    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: message.text.startswith('Buy'))
def buy_item(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    selected_item = message.text[4:]

    if user_id not in user_data:
        user_data[user_id] = {"purchases": []}

    user_data[user_id]["purchases"].append(selected_item)
    save_user_data(user_data)

    bot.reply_to(message, f"Thank you for purchasing: {selected_item}")

@bot.message_handler(func=lambda message: message.text == 'My Configuration')
def my_config(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()

    if diagnose_mode or (user_id in user_data and user_data[user_id]["purchases"]):
        purchases = user_data[user_id]["purchases"] if not diagnose_mode else ["Temporary Diagnose Configuration"]
        response = "Your Purchases:\n" + "\n".join(purchases)
    else:
        response = "You have not purchased any plans yet."

    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.text == 'Toggle Diagnose Mode')
def toggle_diagnose_mode(message):
    global diagnose_mode
    diagnose_mode = not diagnose_mode
    status = "ON" if diagnose_mode else "OFF"
    bot.reply_to(message, f"Diagnose mode is now {status}.")

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.text == 'Add User')
def add_user(message):
    msg = bot.reply_to(message, "Enter username:")
    bot.register_next_step_handler(msg, process_add_user_step1)

# Remaining admin-specific handlers are unchanged

if __name__ == '__main__':
    bot.polling(none_stop=True)
