#!/usr/bin/env python3

import json
import sys
import os
import getopt
from init_paths import *
from paths import *

def get_user_info(username):
    """
    Retrieves and prints information for a specific user from the USERS_FILE.

    Args:
        username (str): The username to look up.

    Returns:
        int: 0 on success, 1 on failure.
    """
    if not os.path.isfile(USERS_FILE):
        print(f"users.json file not found at {USERS_FILE}!")
        return 1

    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {USERS_FILE} contains invalid JSON.")
        return 1

    if username in users_data:
        user_info = users_data[username]
        print(json.dumps(user_info, indent=4))  # Print with indentation for readability
        # upload_bytes = user_info.get('upload_bytes', "No upload data available")
        # download_bytes = user_info.get('download_bytes', "No download data available")
        # status = user_info.get('status', "Status unavailable")
        # You can choose to print these individually as well, if needed
        # print(f"Upload Bytes: {upload_bytes}")
        # print(f"Download Bytes: {download_bytes}")
        # print(f"Status: {status}")
        return 0
    else:
        print(f"User '{username}' not found in {USERS_FILE}.")
        return 1

if __name__ == "__main__":
    username = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:", ["username="])
    except getopt.GetoptError as err:
        print(str(err))
        print(f"Usage: {sys.argv[0]} -u <username>")
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-u", "--username"):
            username = arg

    if not username:
        print(f"Usage: {sys.argv[0]} -u <username>")
        sys.exit(1)

    exit_code = get_user_info(username)
    sys.exit(exit_code)