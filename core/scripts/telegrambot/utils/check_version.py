import telebot
import subprocess
import shlex
import time
import re
from utils.command import *

def check_version():
    command = f"python3 {CLI_PATH} check-version"
    try:
        args = shlex.split(command)
        result = subprocess.check_output(args, stderr=subprocess.STDOUT).decode("utf-8").strip()      
        panel_version = re.search(r'Panel Version: (\d+\.\d+\.\d+)', result)
        latest_version = re.search(r'Latest Version: (\d+\.\d+\.\d+)', result)
        
        if panel_version and latest_version and panel_version.group(1) != latest_version.group(1):
            notify_admins(f"🔔 New version available!\n\n{result}")
            
    except subprocess.CalledProcessError as e:
        error_message = f"Error checking version: {e.output.decode('utf-8')}"
        print(f"Error checking version: {e.output.decode('utf-8')}")
        notify_admins(error_message)

def notify_admins(message):
    for admin_id in ADMIN_USER_IDS:
        try:
            bot.send_message(admin_id, message)
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {str(e)}")

def version_monitoring():
    while True:
        check_version()
        time.sleep(86400)