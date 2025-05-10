#!/usr/bin/env python3

import os
import sys
import json
import time
import fcntl
import shutil
import datetime
from concurrent.futures import ThreadPoolExecutor
from init_paths import *
from paths import *
from hysteria2_api import Hysteria2Client

import logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s: [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

LOCKFILE = "/tmp/kick.lock"
BACKUP_FILE = f"{USERS_FILE}.bak"
MAX_WORKERS = 8

def acquire_lock():
    try:
        lock_file = open(LOCKFILE, 'w')
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file
    except IOError:
        logger.warning("Another instance is already running. Exiting.")
        sys.exit(1)

def kick_users(usernames, secret):
    try:
        client = Hysteria2Client(
            base_url="http://127.0.0.1:25413",
            secret=secret
        )
        
        client.kick_clients(usernames)
        logger.info(f"Successfully kicked {len(usernames)} users: {', '.join(usernames)}")
        return True
    except Exception as e:
        logger.error(f"Error kicking users: {str(e)}")
        return False

def process_user(username, user_data, config_secret, users_data):
    blocked = user_data.get('blocked', False)
    
    if blocked:
        logger.info(f"Skipping {username} as they are already blocked.")
        return None
    
    max_download_bytes = user_data.get('max_download_bytes', 0)
    expiration_days = user_data.get('expiration_days', 0)
    account_creation_date = user_data.get('account_creation_date')
    current_download_bytes = user_data.get('download_bytes', 0)
    current_upload_bytes = user_data.get('upload_bytes', 0)
    
    total_bytes = current_download_bytes + current_upload_bytes
    
    if not account_creation_date:
        logger.info(f"Skipping {username} due to missing account creation date.")
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
                logger.info(f"Setting blocked=True for user {username}")
                users_data[username]['blocked'] = True
                return username
        else:
            logger.info(f"Skipping {username} due to invalid or missing data.")
            return None
            
    except Exception as e:
        logger.error(f"Error processing user {username}: {str(e)}")
        return None
    
    return None

def main():
    lock_file = acquire_lock()
    
    try:
        shutil.copy2(USERS_FILE, BACKUP_FILE)
        logger.info(f"Created backup of users file at {BACKUP_FILE}")
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                secret = config.get('trafficStats', {}).get('secret', '')
                if not secret:
                    logger.error("No secret found in config file")
                    sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load config file: {str(e)}")
            shutil.copy2(BACKUP_FILE, USERS_FILE)
            sys.exit(1)
            
        try:
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
                logger.info(f"Loaded data for {len(users_data)} users")
        except json.JSONDecodeError:
            logger.error("Invalid users.json. Restoring backup.")
            shutil.copy2(BACKUP_FILE, USERS_FILE)
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load users file: {str(e)}")
            shutil.copy2(BACKUP_FILE, USERS_FILE)
            sys.exit(1)
            
        users_to_kick = []
        logger.info(f"Processing {len(users_data)} users in parallel with {MAX_WORKERS} workers")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_user = {
                executor.submit(process_user, username, user_data, secret, users_data): username
                for username, user_data in users_data.items()
            }
            
            for future in future_to_user:
                username = future.result()
                if username:
                    users_to_kick.append(username)
                    logger.info(f"User {username} added to kick list")
        
        if users_to_kick:
            logger.info(f"Saving changes to users file for {len(users_to_kick)} blocked users")
            for retry in range(3):
                try:
                    with open(USERS_FILE, 'w') as f:
                        json.dump(users_data, f, indent=2)
                    break 
                except Exception as e:
                    logger.error(f"Failed to save users file (attempt {retry+1}): {str(e)}")
                    time.sleep(1)
                    if retry == 2: 
                        raise
        
        if users_to_kick:
            logger.info(f"Kicking {len(users_to_kick)} users")
            batch_size = 50 
            for i in range(0, len(users_to_kick), batch_size):
                batch = users_to_kick[i:i+batch_size]
                logger.info(f"Processing batch of {len(batch)} users")
                kick_users(batch, secret)
                for username in batch:
                    logger.info(f"Blocked and kicked user {username}")
        else:
            logger.info("No users to kick")
                        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.info("Restoring users file from backup")
        shutil.copy2(BACKUP_FILE, USERS_FILE)
        sys.exit(1)
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()
        logger.info("Script completed")


if __name__ == "__main__":
    main()