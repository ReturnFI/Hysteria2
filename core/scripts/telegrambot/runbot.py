#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

core_scripts_dir = Path(__file__).resolve().parents[1]
if str(core_scripts_dir) not in sys.path:
    sys.path.append(str(core_scripts_dir))

from paths import TELEGRAM_ENV




def update_env_file(api_token, admin_user_ids):
    TELEGRAM_ENV.write_text(f"""API_TOKEN={api_token}
ADMIN_USER_IDS=[{admin_user_ids}]
""")

def create_service_file():
    Path("/etc/systemd/system/hysteria-telegram-bot.service").write_text("""[Unit]
Description=Hysteria Telegram Bot
After=network.target

[Service]
ExecStart=/bin/bash -c 'source /etc/hysteria/hysteria2_venv/bin/activate && /etc/hysteria/hysteria2_venv/bin/python /etc/hysteria/core/scripts/telegrambot/tbot.py'
WorkingDirectory=/etc/hysteria/core/scripts/telegrambot
Restart=always

[Install]
WantedBy=multi-user.target
""")

def start_service(api_token, admin_user_ids):
    if subprocess.run(["systemctl", "is-active", "--quiet", "hysteria-telegram-bot.service"]).returncode == 0:
        print("The hysteria-telegram-bot.service is already running.")
        return

    update_env_file(api_token, admin_user_ids)
    create_service_file()

    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl", "enable", "hysteria-telegram-bot.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["systemctl", "start", "hysteria-telegram-bot.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if subprocess.run(["systemctl", "is-active", "--quiet", "hysteria-telegram-bot.service"]).returncode == 0:
        print("Hysteria bot setup completed. The service is now running.\n")
    else:
        print("Hysteria bot setup completed. The service failed to start.")

def stop_service():
    subprocess.run(["systemctl", "stop", "hysteria-telegram-bot.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["systemctl", "disable", "hysteria-telegram-bot.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    TELEGRAM_ENV.unlink(missing_ok=True)
    print("\nHysteria bot service stopped and disabled. .env file removed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 runbot.py {start|stop} <API_TOKEN> <ADMIN_USER_IDS>")
        sys.exit(1)

    action = sys.argv[1]

    if action == "start":
        if len(sys.argv) != 4:
            print("Usage: python3 runbot.py start <API_TOKEN> <ADMIN_USER_IDS>")
            sys.exit(1)
        start_service(sys.argv[2], sys.argv[3])
    elif action == "stop":
        stop_service()
    else:
        print("Usage: python3 runbot.py {start|stop} <API_TOKEN> <ADMIN_USER_IDS>")
        sys.exit(1)
