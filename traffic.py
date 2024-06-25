#!/usr/bin/env python3
import subprocess
import json
import os

def traffic_status():
    green = '\033[0;32m'
    cyan = '\033[0;36m'
    NC = '\033[0m'

    try:
        secret = subprocess.check_output(['jq', '-r', '.trafficStats.secret', '/etc/hysteria/config.json']).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to read secret from config.json. Details: {e}")
        return

    if not secret:
        print("Error: Secret not found in config.json")
        return

    try:
        response = subprocess.check_output(['curl', '-s', '-H', f'Authorization: {secret}', 'http://127.0.0.1:25413/traffic?clear=1']).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to fetch traffic data. Details: {e}")
        return

    if not response or response == "{}":
        print("No traffic data available.")
        return

    try:
        online_response = subprocess.check_output(['curl', '-s', '-H', f'Authorization: {secret}', 'http://127.0.0.1:25413/online']).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to fetch online status data. Details: {e}")
        return

    if not online_response:
        print("No online data available.")
        return

    response_dict = json.loads(response)
    online_dict = json.loads(online_response)

    traffic_data = {}

    for user in response_dict.keys():
        tx_bytes = response_dict[user].get('tx', 0)
        rx_bytes = response_dict[user].get('rx', 0)
        online = online_dict.get(user, 0)

        traffic_data[user] = {
            "upload_bytes": tx_bytes,
            "download_bytes": rx_bytes,
            "status": "Online" if online == 1 else "Offline"
        }

    existing_data = {}
    if os.path.exists('/etc/hysteria/traffic_data.json'):
        try:
            with open('/etc/hysteria/traffic_data.json', 'r') as json_file:
                existing_data = json.load(json_file)
        except json.JSONDecodeError:
            print("Error: Failed to parse existing traffic data JSON file.")
            return

    for user, data in traffic_data.items():
        if user in existing_data:
            existing_data[user]["upload_bytes"] += data["upload_bytes"]
            existing_data[user]["download_bytes"] += data["download_bytes"]
            existing_data[user]["status"] = data["status"]
        else:
            existing_data[user] = data

    with open('/etc/hysteria/traffic_data.json', 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

    display_traffic_data(existing_data, green, cyan, NC)

def display_traffic_data(data, green, cyan, NC):
    if not data:
        print("No traffic data to display.")
        return

    print("Traffic Data:")
    print("-------------------------------------------------")
    print(f"{'User':<15} {'Upload (TX)':<15} {'Download (RX)':<15} {'Status':<10}")
    print("-------------------------------------------------")

    for user, entry in data.items():
        upload_bytes = entry["upload_bytes"]
        download_bytes = entry["download_bytes"]
        status = entry["status"]

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

traffic_status()
