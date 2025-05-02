#!/usr/bin/env python3

import json
import sys
import os
import subprocess
import re
from datetime import datetime
from init_paths import *
from paths import *

def add_user(username, traffic_gb, expiration_days, password=None, creation_date=None):
    """
    Adds a new user to the USERS_FILE.

    Args:
        username (str): The username to add.
        traffic_gb (str): The traffic limit in GB.
        expiration_days (str): The number of days until the account expires.
        password (str, optional): The user's password. If None, a random one is generated.
        creation_date (str, optional): The account creation date in YYYY-MM-DD format. If None, the current date is used.

    Returns:
        int: 0 on success, 1 on failure.
    """
    if not username or not traffic_gb or not expiration_days:
        print(f"Usage: {sys.argv[0]} <username> <traffic_limit_GB> <expiration_days> [password] [creation_date]")
        return 1

    try:
        traffic_bytes = int(float(traffic_gb) * 1073741824)
        expiration_days = int(expiration_days)
    except ValueError:
        print("Error: Traffic limit and expiration days must be numeric.")
        return 1

    username_lower = username.lower()

    if not password:
        try:
            password_process = subprocess.run(['pwgen', '-s', '32', '1'], capture_output=True, text=True, check=True)
            password = password_process.stdout.strip()
        except FileNotFoundError:
            try:
                password = subprocess.check_output(['cat', '/proc/sys/kernel/random/uuid'], text=True).strip()
            except Exception:
                print("Error: Failed to generate password. Please install 'pwgen' or ensure /proc access.")

    if not creation_date:
        creation_date = datetime.now().strftime("%Y-%m-%d")
    else:
        if not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", creation_date):
            print("Invalid date format. Expected YYYY-MM-DD.")
            return 1
        try:
            datetime.strptime(creation_date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date. Please provide a valid date in YYYY-MM-DD format.")
            return 1

    if not re.match(r"^[a-zA-Z0-9]+$", username):
        print("Error: Username can only contain letters and numbers.")
        return 1

    if not os.path.isfile(USERS_FILE):
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump({}, f)
        except IOError:
            print(f"Error: Could not create {USERS_FILE}.")
            return 1

    try:
        with open(USERS_FILE, 'r+') as f:
            try:
                users_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error: {USERS_FILE} contains invalid JSON.")
                return 1

            for existing_username in users_data:
                if existing_username.lower() == username_lower:
                    print("User already exists.")
                    return 1

            users_data[username_lower] = {
                "password": password,
                "max_download_bytes": traffic_bytes,
                "expiration_days": expiration_days,
                "account_creation_date": creation_date,
                "blocked": False
            }

            f.seek(0)
            json.dump(users_data, f, indent=4)
            f.truncate()

        print(f"User {username} added successfully.")
        return 0

    except IOError:
        print(f"Error: Could not write to {USERS_FILE}.")
        return 1

if __name__ == "__main__":
    if len(sys.argv) not in [4, 6]:
        print(f"Usage: {sys.argv[0]} <username> <traffic_limit_GB> <expiration_days> [password] [creation_date]")
        sys.exit(1)

    username = sys.argv[1]
    traffic_gb = sys.argv[2]
    expiration_days = sys.argv[3]
    password = sys.argv[4] if len(sys.argv) > 4 else None
    creation_date = sys.argv[5] if len(sys.argv) > 5 else None

    exit_code = add_user(username, traffic_gb, expiration_days, password, creation_date)
    sys.exit(exit_code)