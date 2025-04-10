#!/usr/bin/env python3
import json
import os
import json
from hysteria2_api import Hysteria2Client

# Define static variables for paths and URLs
CONFIG_FILE = '/etc/hysteria/config.json'
USERS_FILE = '/etc/hysteria/users.json'
API_BASE_URL = 'http://127.0.0.1:25413'

def traffic_status():
    green = '\033[0;32m'
    cyan = '\033[0;36m'
    NC = '\033[0m'

    try:
        with open(CONFIG_FILE, 'r') as config_file:
            config = json.load(config_file)
            secret = config.get('trafficStats', {}).get('secret')
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: Failed to read secret from {CONFIG_FILE}. Details: {e}")
        return

    if not secret:
        print("Error: Secret not found in config.json")
        return

    client = Hysteria2Client(base_url=API_BASE_URL, secret=secret)

    try:
        traffic_stats = client.get_traffic_stats(clear=True)
        
        online_status = client.get_online_clients()
    except Exception as e:
        print(f"Error communicating with Hysteria2 API: {e}")
        return

    users_data = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as users_file:
                users_data = json.load(users_file)
        except json.JSONDecodeError:
            print("Error: Failed to parse existing users data JSON file.")
            return

    for user in users_data:
        users_data[user]["status"] = "Offline"

    for user_id, status in online_status.items():
        if user_id in users_data:
            users_data[user_id]["status"] = "Online" if status.is_online else "Offline"
        else:
            users_data[user_id] = {
                "upload_bytes": 0,
                "download_bytes": 0,
                "status": "Online" if status.is_online else "Offline"
            }

    for user_id, stats in traffic_stats.items():
        if user_id in users_data:
            users_data[user_id]["upload_bytes"] = users_data[user_id].get("upload_bytes", 0) + stats.upload_bytes
            users_data[user_id]["download_bytes"] = users_data[user_id].get("download_bytes", 0) + stats.download_bytes
        else:
            online = user_id in online_status and online_status[user_id].is_online
            users_data[user_id] = {
                "upload_bytes": stats.upload_bytes,
                "download_bytes": stats.download_bytes,
                "status": "Online" if online else "Offline"
            }

    with open(USERS_FILE, 'w') as users_file:
        json.dump(users_data, users_file, indent=4)

    display_traffic_data(users_data, green, cyan, NC)

def display_traffic_data(data, green, cyan, NC):
    if not data:
        print("No traffic data to display.")
        return

    print("Traffic Data:")
    print("-------------------------------------------------")
    print(f"{'User':<15} {'Upload (TX)':<15} {'Download (RX)':<15} {'Status':<10}")
    print("-------------------------------------------------")

    for user, entry in data.items():
        upload_bytes = entry.get("upload_bytes", 0)
        download_bytes = entry.get("download_bytes", 0)
        status = entry.get("status", "Offline")

        formatted_tx = format_bytes(upload_bytes)
        formatted_rx = format_bytes(download_bytes)

        print(f"{user:<15} {green}{formatted_tx:<15}{NC} {cyan}{formatted_rx:<15}{NC} {status:<10}")
        print("-------------------------------------------------")

def format_bytes(bytes):
    if bytes < 1024:
        return f"{bytes}B"
    elif bytes < 1048576:
        return f"{bytes / 1024:.2f}KB"
    elif bytes < 1073741824:
        return f"{bytes / 1048576:.2f}MB"
    elif bytes < 1099511627776:
        return f"{bytes / 1073741824:.2f}GB"
    else:
        return f"{bytes / 1099511627776:.2f}TB"

if __name__ == "__main__":
    traffic_status()
