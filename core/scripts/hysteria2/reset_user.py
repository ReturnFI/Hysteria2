#!/usr/bin/env python3

import json
import sys
import os
from datetime import date
from init_paths import *
from paths import *

def reset_user(username):
    """
    Resets the data usage, status, and creation date of a user in the USERS_FILE.

    Args:
        username (str): The username to reset.

    Returns:
        int: 0 on success, 1 on failure.
    """
    if not os.path.isfile(USERS_FILE):
        print(f"Error: File '{USERS_FILE}' not found.")
        return 1

    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {USERS_FILE} contains invalid JSON.")
        return 1

    if username not in users_data:
        print(f"Error: User '{username}' not found in '{USERS_FILE}'.")
        return 1

    today = date.today().strftime("%Y-%m-%d")
    users_data[username]['upload_bytes'] = 0
    users_data[username]['download_bytes'] = 0
    users_data[username]['status'] = "Offline"
    users_data[username]['account_creation_date'] = today
    users_data[username]['blocked'] = False

    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=4)
        print(f"User '{username}' has been reset successfully.")
        return 0
    except IOError:
        print(f"Error: Failed to reset user '{username}' in '{USERS_FILE}'.")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <username>")
        sys.exit(1)

    username_to_reset = sys.argv[1]
    exit_code = reset_user(username_to_reset)
    sys.exit(exit_code)