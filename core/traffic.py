#!/usr/bin/env python3
import subprocess
import json
import os

# Define static variables for paths and URLs
CONFIG_FILE = '/etc/hysteria/config.json'
USERS_FILE = '/etc/hysteria/users.json'
TRAFFIC_API_URL = 'http://127.0.0.1:25413/traffic?clear=1'
ONLINE_API_URL = 'http://127.0.0.1:25413/online'

def traffic_status():
    green = '\033[0;32m'
    cyan = '\033[0;36m'
    NC = '\033[0m'

    try:
        secret = subprocess.check_output(['jq', '-r', '.trafficStats.secret', CONFIG_FILE]).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to read secret from {CONFIG_FILE}. Details: {e}")
        return

    if not secret:
        print("Error: Secret not found in config.json")
        return

    try:
        response = subprocess.check_output(['curl', '-s', '-H', f'Authorization: {secret}', TRAFFIC_API_URL]).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to fetch traffic data. Details: {e}")
        return

    if not response or response == "{}":
        print("No traffic data available.")
        return

    try:
        online_response = subprocess.check_output(['curl', '-s', '-H', f'Authorization: {secret}', ONLINE_API_URL]).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to fetch online status data. Details: {e}")
        return

    if not online_response:
        print("No online data available.")
        return

    response_dict = json.loads(response)
    online_dict = json.loads(online_response)

    # Load the current users.json data
    users_data = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as users_file:
                users_data = json.load(users_file)
        except json.JSONDecodeError:
            print("Error: Failed to parse existing users data JSON file.")
            return

    # Update users.json with traffic data
    for user, traffic_info in response_dict.items():
        tx_bytes = traffic_info.get('tx', 0)
        rx_bytes = traffic_info.get('rx', 0)
        online_status = online_dict.get(user, 0)

        if user in users_data:
            users_data[user]["upload_bytes"] = users_data[user].get("upload_bytes", 0) + tx_bytes
            users_data[user]["download_bytes"] = users_data[user].get("download_bytes", 0) + rx_bytes
            users_data[user]["status"] = "Online" if online_status == 1 else "Offline"
        else:
            users_data[user] = {
                "upload_bytes": tx_bytes,
                "download_bytes": rx_bytes,
                "status": "Online" if online_status == 1 else "Offline"
            }

    # Save the updated data back to users.json
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
