import telebot
import subprocess
import qrcode
import io
import json
import os
import re
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
    markup.row('Add User', 'Show User')
    markup.row('Delete User', 'Server Info')
    return markup

def is_admin(user_id):
    return user_id in ADMIN_USER_IDS

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_admin(message.from_user.id):
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
    if username == "":
        bot.reply_to(message, "Username cannot be empty. Please enter a valid username.")
        return

    command = f"python3 {CLI_PATH} list-users"
    result = run_cli_command(command)
    
    try:
        users = json.loads(result)

        if username in users:
            bot.reply_to(message, f"Username '{username}' already exists. Please choose a different username.")
            return
    except json.JSONDecodeError:
        if "No such file or directory" in result or result.strip() == "":
            bot.reply_to(message, "User list file does not exist. Adding the first user.")
        else:
            bot.reply_to(message, "Error retrieving user list. Please try again later.")
            return

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
    user_result = run_cli_command(command)
    
    user_json_match = re.search(r'(\{.*?\})\n?(\{.*?\})?', user_result, re.DOTALL)
    
    if not user_json_match:
        bot.reply_to(message, "Failed to parse user details. The command output format may be incorrect.")
        return

    user_json = user_json_match.group(1)
    traffic_data_section = user_json_match.group(2)

    try:
        user_details = json.loads(user_json)
        
        if traffic_data_section:
            traffic_data = json.loads(traffic_data_section)
            traffic_message = (
                f"**Traffic Data:**\n"
                f"Upload: {traffic_data.get('upload_bytes', 0) / (1024 ** 2):.2f} MB\n"
                f"Download: {traffic_data.get('download_bytes', 0) / (1024 ** 2):.2f} MB\n"
                f"Status: {traffic_data.get('status', 'Unknown')}"
            )
        else:
            traffic_message = "**Traffic Data:**\nNo traffic data available. The user might not have connected yet."
    except json.JSONDecodeError:
        bot.reply_to(message, "Failed to parse JSON data. The command output may be malformed.")
        return

    formatted_details = (
        f"**User Details:**\n\n"
        f"Name: {username}\n"
        f"Traffic Limit: {user_details['max_download_bytes'] / (1024 ** 3):.2f} GB\n"
        f"Days: {user_details['expiration_days']}\n"
        f"Account Creation: {user_details['account_creation_date']}\n"
        f"Blocked: {user_details['blocked']}\n\n"
        f"{traffic_message}"
    )

    combined_command = f"python3 {CLI_PATH} show-user-uri -u {username} -ip 4 -s"
    combined_result = run_cli_command(combined_command)

    if "Error" in combined_result or "Invalid" in combined_result:
        bot.reply_to(message, combined_result)
        return

    result_lines = combined_result.split('\n')
    uri_v4 = result_lines[1].strip()

    singbox_sublink = result_lines[-1].strip() if "https://" in result_lines[-1] else None

    qr_v4 = qrcode.make(uri_v4)
    bio_v4 = io.BytesIO()
    qr_v4.save(bio_v4, 'PNG')
    bio_v4.seek(0)

    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("Reset User", callback_data=f"reset_user:{username}"),
               types.InlineKeyboardButton("IPv6-URI", callback_data=f"ipv6_uri:{username}"))
    markup.add(types.InlineKeyboardButton("Edit Username", callback_data=f"edit_username:{username}"),
               types.InlineKeyboardButton("Edit Traffic Limit", callback_data=f"edit_traffic:{username}"))
    markup.add(types.InlineKeyboardButton("Edit Expiration Days", callback_data=f"edit_expiration:{username}"),
               types.InlineKeyboardButton("Renew Password", callback_data=f"renew_password:{username}"))
    markup.add(types.InlineKeyboardButton("Renew Creation Date", callback_data=f"renew_creation:{username}"),
               types.InlineKeyboardButton("Block User", callback_data=f"block_user:{username}"))

    caption = f"{formatted_details}\n\n**IPv4 URI:**\n\n`{uri_v4}`"
    if singbox_sublink:
        caption += f"\n\n\n**SingBox SUB:**\n{singbox_sublink}"

    bot.send_photo(
        message.chat.id,
        bio_v4,
        caption=caption,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.text == 'Server Info')
def server_info(message):
    command = f"python3 {CLI_PATH} server-info"
    result = run_cli_command(command)
    bot.reply_to(message, result)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_') or call.data.startswith('renew_') or call.data.startswith('block_') or call.data.startswith('reset_') or call.data.startswith('ipv6_'))
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
    elif action == 'reset_user':
        command = f"python3 {CLI_PATH} reset-user -u {username}"
        result = run_cli_command(command)
        bot.send_message(call.message.chat.id, result)
    elif action == 'ipv6_uri':
        command = f"python3 {CLI_PATH} show-user-uri -u {username} -ip 6"
        result = run_cli_command(command)
        if "Error" in result or "Invalid" in result:
            bot.send_message(call.message.chat.id, result)
            return
        
        uri_v6 = result.split('\n')[-1].strip()
        qr_v6 = qrcode.make(uri_v6)
        bio_v6 = io.BytesIO()
        qr_v6.save(bio_v6, 'PNG')
        bio_v6.seek(0)
        
        bot.send_photo(
            call.message.chat.id,
            bio_v6,
            caption=f"**IPv6 URI for {username}:**\n\n`{uri_v6}`",
            parse_mode="Markdown"
        )

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
    command = f"python3 {CLI_PATH} remove-user -u {username}"
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
