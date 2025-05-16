#!/usr/bin/env python3

import os
import subprocess
import sys

SERVICES = [
    "hysteria-server.service",
    "hysteria-webpanel.service",
    "hysteria-caddy.service",
    "hysteria-telegram-bot.service",
    "hysteria-normal-sub.service",
    "hysteria-singbox.service",
    "hysteria-ip-limit.service",
    "hysteria-scheduler.service",
]

def run_command(command, error_message):
    """Runs a command and prints an error message if it fails."""
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 0
    except subprocess.CalledProcessError:
        print(error_message)
        return 1
    except FileNotFoundError:
        print(f"Error: Command not found: {command[0]}")
        return 1

def uninstall_hysteria():
    """Uninstalls Hysteria2."""
    print("Uninstalling Hysteria2...")

    print("Running uninstallation script...")
    run_command(["bash", "-c", "curl -fsSL https://get.hy2.sh/ | bash -- --remove"], "Error running the official uninstallation script.")

    print("Removing WARP")
    cli_path = "/etc/hysteria/core/cli.py"
    if os.path.exists(cli_path):
        run_command([sys.executable, cli_path, "uninstall-warp"], "Error during WARP removal.")
    else:
        print("Skipping WARP removal (CLI path not found)")

    print("Removing Hysteria folder...")
    run_command(["rm", "-rf", "/etc/hysteria"], "Error removing the Hysteria folder.")

    print("Deleting hysteria user...")
    run_command(["userdel", "-r", "hysteria"], "Error deleting the hysteria user.")

    print("Stop/Disabling Hysteria Services...")
    for service in SERVICES + ["hysteria-server@*.service"]:
        print(f"Stopping and disabling {service}...")
        run_command(["systemctl", "stop", service], f"Error stopping {service}.")
        run_command(["systemctl", "disable", service], f"Error disabling {service}.")

    print("Removing systemd service files...")
    for service in SERVICES + ["hysteria-server@*.service"]:
        print(f"Removing service file: {service}")
        run_command(["rm", "-f", f"/etc/systemd/system/{service}", f"/etc/systemd/system/multi-user.target.wants/{service}"], f"Error removing service files for {service}.")

    print("Reloading systemd daemon...")
    run_command(["systemctl", "daemon-reload"], "Error reloading systemd daemon.")

    print("Removing cron jobs...")
    try:
        crontab_list = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
        if "hysteria" in crontab_list.stdout:
            new_crontab = "\n".join(line for line in crontab_list.stdout.splitlines() if "hysteria" not in line)
            process = subprocess.run(["crontab", "-"], input=new_crontab.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("Warning: crontab command not found.")
    except subprocess.CalledProcessError:
        print("Warning: Could not access crontab.")

    print("Removing alias 'hys2' from .bashrc...")
    bashrc_path = os.path.expanduser("~/.bashrc")
    if os.path.exists(bashrc_path):
        try:
            with open(bashrc_path, 'r') as f:
                lines = f.readlines()
            with open(bashrc_path, 'w') as f:
                for line in lines:
                    if 'alias hys2=' not in line:
                        f.write(line)
        except IOError:
            print(f"Warning: Could not access or modify {bashrc_path}.")
    else:
        print(f"Warning: {bashrc_path} not found.")

    print("Hysteria2 uninstalled!")
    print("Rebooting server...")
    run_command(["reboot"], "Error initiating reboot.")

if __name__ == "__main__":
    uninstall_hysteria()