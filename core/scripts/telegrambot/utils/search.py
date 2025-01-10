from telebot import types
from utils.command import *

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

    if query_text == "block":
        for username, details in users.items():
            if details.get('blocked', False):
                title = f"{username} (Blocked)"
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
    else:
        for username, details in users.items():
            if query_text in username.lower():
                title = f"{username}"
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

    bot.answer_inline_query(query.id, results, cache_time=0)
