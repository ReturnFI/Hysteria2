#!/usr/bin/env python3
import json
import os
import sys
import time
import fcntl
import shutil
import datetime
from concurrent.futures import ThreadPoolExecutor
from hysteria2_api import Hysteria2Client

CONFIG_FILE = '/etc/hysteria/config.json'
USERS_FILE = '/etc/hysteria/users.json'
API_BASE_URL = 'http://127.0.0.1:25413'
LOCKFILE = "/tmp/kick.lock"
BACKUP_FILE = f"{USERS_FILE}.bak"
MAX_WORKERS = 8

# import logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s: [%(levelname)s] %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )
# logger = logging.getLogger()
# null_handler = logging.NullHandler()
# logger.handlers = [null_handler]

def acquire_lock():
    """Acquires a lock file to prevent concurrent execution"""
    try:
        lock_file = open(LOCKFILE, 'w')
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file
    except IOError:
        sys.exit(1)

def traffic_status(no_gui=False):
    """Updates and retrieves traffic statistics for all users.
    
    Args:
        no_gui (bool): If True, suppresses output to console
        
    Returns:
        dict: User data including upload/download bytes and status
    """
    green = '\033[0;32m'
    cyan = '\033[0;36m'
    NC = '\033[0m'

    try:
        with open(CONFIG_FILE, 'r') as config_file:
            config = json.load(config_file)
            secret = config.get('trafficStats', {}).get('secret')
    except (json.JSONDecodeError, FileNotFoundError) as e:
        if not no_gui:
            print(f"Error: Failed to read secret from {CONFIG_FILE}. Details: {e}")
        return None

    if not secret:
        if not no_gui:
            print("Error: Secret not found in config.json")
        return None

    client = Hysteria2Client(base_url=API_BASE_URL, secret=secret)

    try:
        traffic_stats = client.get_traffic_stats(clear=True)
        online_status = client.get_online_clients()
    except Exception as e:
        if not no_gui:
            print(f"Error communicating with Hysteria2 API: {e}")
        return None

    users_data = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as users_file:
                users_data = json.load(users_file)
        except json.JSONDecodeError:
            if not no_gui:
                print("Error: Failed to parse existing users data JSON file.")
            return None

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

    if not no_gui:
        display_traffic_data(users_data, green, cyan, NC)
    
    return users_data

def display_traffic_data(data, green, cyan, NC):
    """Displays traffic data in a formatted table"""
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
    """Format bytes as human-readable string"""
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

def kick_users(usernames, secret):
    """Kicks specified users from the server"""
    try:
        client = Hysteria2Client(
            base_url=API_BASE_URL,
            secret=secret
        )
        
        client.kick_clients(usernames)
        return True
    except Exception:
        return False

def process_user(username, user_data, config_secret, users_data):
    """Process a single user to check if they should be kicked"""
    blocked = user_data.get('blocked', False)
    
    if blocked:
        return None
    
    max_download_bytes = user_data.get('max_download_bytes', 0)
    expiration_days = user_data.get('expiration_days', 0)
    account_creation_date = user_data.get('account_creation_date')
    current_download_bytes = user_data.get('download_bytes', 0)
    current_upload_bytes = user_data.get('upload_bytes', 0)
    
    total_bytes = current_download_bytes + current_upload_bytes
    
    if not account_creation_date:
        return None
    
    try:
        current_date = datetime.datetime.now().timestamp()
        creation_date = datetime.datetime.fromisoformat(account_creation_date.replace('Z', '+00:00'))
        expiration_date = (creation_date + datetime.timedelta(days=expiration_days)).timestamp()
        
        should_block = False
        
        if max_download_bytes > 0 and total_bytes >= 0 and expiration_days > 0:
            if total_bytes >= max_download_bytes or current_date >= expiration_date:
                should_block = True
                
            if should_block:
                users_data[username]['blocked'] = True
                return username
        
    except Exception:
        return None
    
    return None

def kick_expired_users():
    """Kicks users who have exceeded their data limits or whose accounts have expired"""
    lock_file = acquire_lock()
    
    try:
        shutil.copy2(USERS_FILE, BACKUP_FILE)
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                secret = config.get('trafficStats', {}).get('secret', '')
                if not secret:
                    sys.exit(1)
        except Exception:
            shutil.copy2(BACKUP_FILE, USERS_FILE)
            sys.exit(1)
            
        try:
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
        except json.JSONDecodeError:
            shutil.copy2(BACKUP_FILE, USERS_FILE)
            sys.exit(1)
        except Exception:
            shutil.copy2(BACKUP_FILE, USERS_FILE)
            sys.exit(1)
            
        users_to_kick = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_user = {
                executor.submit(process_user, username, user_data, secret, users_data): username
                for username, user_data in users_data.items()
            }
            
            for future in future_to_user:
                username = future.result()
                if username:
                    users_to_kick.append(username)
        
        if users_to_kick:
            for retry in range(3):
                try:
                    with open(USERS_FILE, 'w') as f:
                        json.dump(users_data, f, indent=2)
                    break 
                except Exception:
                    time.sleep(1)
                    if retry == 2: 
                        raise
        
        if users_to_kick:
            batch_size = 50 
            for i in range(0, len(users_to_kick), batch_size):
                batch = users_to_kick[i:i+batch_size]
                kick_users(batch, secret)
                        
    except Exception:
        shutil.copy2(BACKUP_FILE, USERS_FILE)
        sys.exit(1)
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "kick":
            kick_expired_users()
        elif sys.argv[1] == "--no-gui":
            traffic_status(no_gui=True)
            kick_expired_users()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Usage: python traffic.py [kick|--no-gui]")
    else:
        traffic_status(no_gui=False)