import psutil
import time
from utils.command import *


def get_system_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_usage = ram.percent
    return cpu_usage, ram_usage

def format_alert_message(cpu_usage, ram_usage):
    return (
        "🚨ALERT🚨\n"
        "High CPU and RAM usage detected ⚠️\n\n"
        f"📈 CPU: {cpu_usage:.1f}%\n"
        f"📋 RAM: {ram_usage:.1f}%"
    )

def monitor_system_resources():
    # Thresholds
    CPU_THRESHOLD = 90.0
    RAM_THRESHOLD = 90.0
    CONFIRMATION_DELAY = 60  # seconds
    
    try:
        cpu_usage, ram_usage = get_system_usage()
        
        if cpu_usage > CPU_THRESHOLD and ram_usage > RAM_THRESHOLD:
            time.sleep(CONFIRMATION_DELAY)
            cpu_usage, ram_usage = get_system_usage()
            
            if cpu_usage > CPU_THRESHOLD and ram_usage > RAM_THRESHOLD:
                alert_message = format_alert_message(cpu_usage, ram_usage)
                
                for admin_id in ADMIN_USER_IDS:
                    try:
                        bot.send_message(admin_id, alert_message)
                    except Exception as e:
                        print(f"Failed to send alert to admin {admin_id}: {str(e)}")
                
                return True
    
    except Exception as e:
        print(f"Error monitoring system resources: {str(e)}")
    
    return False

@bot.message_handler(commands=['system'])
def check_system(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Unauthorized access. You do not have permission to use this command.")
        return

    try:
        cpu_usage, ram_usage = get_system_usage()
        response = (
            "📊 System Resource Usage 📊\n\n"
            f"📈 CPU Usage: {cpu_usage:.1f}%\n"
            f"📋 RAM Usage: {ram_usage:.1f}%"
        )
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Error checking system resources: {str(e)}")
