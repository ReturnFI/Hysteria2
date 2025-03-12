import telebot
import subprocess
import shlex
import time
from utils.command import *

def check_version():
    command = f"python3 {CLI_PATH} check-version"
    try:
        args = shlex.split(command)
        result = subprocess.check_output(args, stderr=subprocess.STDOUT).decode("utf-8").strip()
        notify_admins(result)
    except subprocess.CalledProcessError as e:
        print(f"Error checking version: {e.output.decode('utf-8')}")

def notify_admins(message):
    for admin_id in ADMIN_USER_IDS:
        bot.send_message(admin_id, message)

def version_monitoring():
    while True:
        check_version()
        time.sleep(86400)
