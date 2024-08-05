import telebot
import subprocess
import qrcode
import io
import json
import os
from dotenv import load_dotenv
from telebot import types

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_USER_IDS = json.loads(os.getenv('ADMIN_USER_IDS'))
CLI_PATH = '/etc/hysteria/core/cli.py'
bot = telebot.TeleBot(API_TOKEN)

def run_cli_command(command):
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        return f'Error: {e.output.decode("utf-8")}'

def create_main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Show User', 'Add User')
    markup.row('Delete User', 'Server Info')
    return markup

def is_admin(user_id):
    return user_id in ADMIN_USER_IDS

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_admin(message):
        markup = create_main_markup()
        bot.reply_to(message, "Welcome to the User Management Bot!", reply_markup=markup)
    else:
        bot.reply_to(message, "Unauthorized access. You do not have permission to use this bot.")

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.text == 'Add User')
def add_user(message):
    msg = bot.reply_to(message, "Enter username:")
    bot.register_next_step_handler(msg, process_add_user_step1)

def process_add_user_step1(message):
    username = message.text.strip()
    msg = bot.reply_to(message, "Enter traffic limit (GB):")
    bot.register_next_step_handler(msg, process_add_user_step2, username)

def process_add_user_step2(message, username):
    try:
        traffic_limit = int(message.text.strip())
        msg = bot.reply_to(message, "Enter expiration days:")
        bot.register_next_step_handler(msg, process_add_user_step3, username, traffic_limit)
    except ValueError:
        bot.reply_to(message, "Invalid traffic limit. Please enter a number.")

def process_add_user_step3(message, username, traffic_limit):
    try:
        expiration_days = int(message.text.strip())
        command = f"python3 {CLI_PATH} add-user -u {username} -t {traffic_limit} -e {expiration_days}"
        result = run_cli_command(command)
        bot.reply_to(message, result)
    except ValueError:
        bot.reply_to(message, "Invalid expiration days. Please enter a number.")

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.text == 'Show User')
def show_user(message):
    msg = bot.reply_to(message, "Enter username:")
    bot.register_next_step_handler(msg, process_show_user)

def process_show_user(message):
    username = message.text.strip()
    command = f"python3 {CLI_PATH} get-user -u {username}"
    result = run_cli_command(command)

    if "Error" in result or "Invalid" in result:
        bot.reply_to(message, result)
    else:
        user_details = json.loads(result)
        formatted_details = (
            f"Name: {username}\n"
            f"Traffic limit: {user_details['max_download_bytes'] / (1024 ** 3):.2f} GB\n"
            f"Days: {user_details['expiration_days']}\n"
            f"Account Creation: {user_details['account_creation_date']}\n"
            f"Blocked: {user_details['blocked']}"
        )

        qr_command = f"bash /etc/hysteria/core/scripts/hysteria2/show_user_uri.sh {username}"
        qr_result = run_cli_command(qr_command)

        if "Error" in qr_result or "Invalid" in qr_result:
            bot.reply_to(message, qr_result)
            return

        uris = qr_result.split('\n')
        if len(uris) < 2:
            bot.reply_to(message, "Failed to retrieve URIs. Please check the username or try again later.")
            return

        uri_v4 = uris[0].strip()
        uri_v6 = uris[1].strip()

        qr_v4 = qrcode.make(uri_v4)
        bio_v4 = io.BytesIO()
        qr_v4.save(bio_v4, 'PNG')
        bio_v4.seek(0)

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("Edit Username", callback_data=f"edit_username:{username}"),
                   types.InlineKeyboardButton("Edit Traffic Limit", callback_data=f"edit_traffic:{username}"))
        markup.add(types.InlineKeyboardButton("Edit Expiration Days", callback_data=f"edit_expiration:{username}"),
                   types.InlineKeyboardButton("Renew Password", callback_data=f"renew_password:{username}"))
        markup.add(types.InlineKeyboardButton("Renew Creation Date", callback_data=f"renew_creation:{username}"),
                   types.InlineKeyboardButton("Block User", callback_data=f"block_user:{username}"))

        bot.send_photo(message.chat.id, bio_v4, caption=f"User Details:\n{formatted_details}\n\nIPv4 URI: {uri_v4}", reply_markup=markup)

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.text == 'Server Info')
def server_info(message):
    command = f"python3 {CLI_PATH} server-info"
    result = run_cli_command(command)
    bot.reply_to(message, result)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_') or call.data.startswith('renew_') or call.data.startswith('block_'))
def handle_edit_callback(call):
    action, username = call.data.split(':')
    if action == 'edit_username':
        msg = bot.send_message(call.message.chat.id, f"Enter new username for {username}:")
        bot.register_next_step_handler(msg, process_edit_username, username)
    elif action == 'edit_traffic':
        msg = bot.send_message(call.message.chat.id, f"Enter new traffic limit (GB) for {username}:")
        bot.register_next_step_handler(msg, process_edit_traffic, username)
    elif action == 'edit_expiration':
        msg = bot.send_message(call.message.chat.id, f"Enter new expiration days for {username}:")
        bot.register_next_step_handler(msg, process_edit_expiration, username)
    elif action == 'renew_password':
        command = f"python3 {CLI_PATH} edit-user -u {username} -rp"
        result = run_cli_command(command)
        bot.send_message(call.message.chat.id, result)
    elif action == 'renew_creation':
        command = f"python3 {CLI_PATH} edit-user -u {username} -rc"
        result = run_cli_command(command)
        bot.send_message(call.message.chat.id, result)
    elif action == 'block_user':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("True", callback_data=f"confirm_block:{username}:true"),
                   types.InlineKeyboardButton("False", callback_data=f"confirm_block:{username}:false"))
        bot.send_message(call.message.chat.id, f"Set block status for {username}:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_block:'))
def handle_block_confirmation(call):
    _, username, block_status = call.data.split(':')
    command = f"python3 {CLI_PATH} edit-user -u {username} {'-b' if block_status == 'true' else ''}"
    result = run_cli_command(command)
    bot.send_message(call.message.chat.id, result)

def process_edit_username(message, username):
    new_username = message.text.strip()
    command = f"python3 {CLI_PATH} edit-user -u {username} -nu {new_username}"
    result = run_cli_command(command)
    bot.reply_to(message, result)

def process_edit_traffic(message, username):
    try:
        new_traffic_limit = int(message.text.strip())
        command = f"python3 {CLI_PATH} edit-user -u {username} -nt {new_traffic_limit}"
        result = run_cli_command(command)
        bot.reply_to(message, result)
    except ValueError:
        bot.reply_to(message, "Invalid traffic limit. Please enter a number.")

def process_edit_expiration(message, username):
    try:
        new_expiration_days = int(message.text.strip())
        command = f"python3 {CLI_PATH} edit-user -u {username} -ne {new_expiration_days}"
        result = run_cli_command(command)
        bot.reply_to(message, result)
    except ValueError:
        bot.reply_to(message, "Invalid expiration days. Please enter a number.")

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.text == 'Delete User')
def delete_user(message):
    msg = bot.reply_to(message, "Enter username:")
    bot.register_next_step_handler(msg, process_delete_user)

def process_delete_user(message):
    username = message.text.strip()
    command = f"python3 {CLI_PATH} delete-user -u {username}"
    result = run_cli_command(command)
    bot.reply_to(message, result)

@bot.inline_handler(lambda query: is_admin(query.from_user.id))
def handle_inline_query(query):
    command = f"python3 {CLI_PATH} list-users"
    result = run_cli_command(command)
    try:
        users = json.loads(result)
    except json.JSONDecodeError:
        bot.answer_inline_query(query.id, results=[], switch_pm_text="Error retrieving users.", switch_pm_user_id=query.from_user.id)
        return

    query_text = query.query.lower()
    results = []
    for username, details in users.items():
        if query_text in username.lower():
            title = f"Username: {username}"
            description = f"Traffic Limit: {details['max_download_bytes'] / (1024 ** 3):.2f} GB, Expiration Days: {details['expiration_days']}"
            results.append(types.InlineQueryResultArticle(
                id=username,
                title=title,
                description=description,
                input_message_content=types.InputTextMessageContent(
                    message_text=f"Name: {username}\n"
                                 f"Traffic limit: {details['max_download_bytes'] / (1024 ** 3):.2f} GB\n"
                                 f"Days: {details['expiration_days']}\n"
                                 f"Account Creation: {details['account_creation_date']}\n"
                                 f"Blocked: {details['blocked']}"
                )
            ))

    bot.answer_inline_query(query.id, results)

if __name__ == '__main__':
    bot.polling(none_stop=True)
