#!/usr/bin/env python3

import subprocess
import shutil
import os
import sys
from init_paths import *
from paths import *

CONFIG_BACKUP = "/etc/hysteria/config_backup.json"
SERVICE_FILE = "/etc/systemd/system/hysteria-server.service"
OLD_CONFIG_PATH = "/etc/hysteria/config.yaml"

def backup_config():
    print("📦 Backing up the current configuration...")
    try:
        shutil.copy(CONFIG_FILE, CONFIG_BACKUP)
        return True
    except Exception as e:
        print(f"❌ Error: Failed to back up configuration: {e}")
        return False

def restore_config():
    print("♻️ Restoring configuration from backup...")
    try:
        shutil.move(CONFIG_BACKUP, CONFIG_FILE)
        return True
    except Exception as e:
        print(f"❌ Error: Failed to restore configuration: {e}")
        return False

def install_latest_hysteria():
    print("⬇️ Downloading and installing the latest version of Hysteria2...")
    try:
        cmd = 'bash -c "$(curl -fsSL https://get.hy2.sh/)"'
        result = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error during installation: {e}")
        return False

def modify_systemd_service():
    print("⚙️ Modifying systemd service to use config.json...")
    try:
        with open(SERVICE_FILE, 'r') as f:
            service_data = f.read()

        new_data = service_data.replace(
            "Description=Hysteria Server Service (config.yaml)", 
            "Description=Hysteria Server Service (Blitz Panel)"
        )

        new_data = new_data.replace(str(OLD_CONFIG_PATH), str(CONFIG_FILE))

        with open(SERVICE_FILE, 'w') as f:
            f.write(new_data)

        return True
    except Exception as e:
        print(f"❌ Error: Failed to modify systemd service: {e}")
        return False

def restart_hysteria():
    print("🔄 Restarting Hysteria2 service...")
    try:
        subprocess.run(["systemctl", "daemon-reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["python3", CLI_PATH, "restart-hysteria2"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"❌ Error: Failed to restart Hysteria2: {e}")
        return False

def main():
    print("🚀 Starting the update process for Hysteria2...")

    if not backup_config():
        print("❌ Aborting update due to failed backup.")
        sys.exit(1)

    if not install_latest_hysteria():
        print("❌ Installation failed. Restoring previous config...")
        restore_config()
        restart_hysteria()
        sys.exit(1)

    if not restore_config():
        sys.exit(1)

    if not modify_systemd_service():
        sys.exit(1)

    try:
        if os.path.exists(OLD_CONFIG_PATH):
            os.remove(OLD_CONFIG_PATH)
    except Exception as e:
        print(f"⚠️ Failed to remove old YAML config: {e}")

    if not restart_hysteria():
        sys.exit(1)

    print("\n✅ Hysteria2 has been successfully updated.")
    sys.exit(0)

if __name__ == "__main__":
    main()
