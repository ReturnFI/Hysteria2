from telebot import types

def create_main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Add User', 'Show User')
    markup.row('Delete User', 'Server Info')
    markup.row('Backup Server')
    return markup
