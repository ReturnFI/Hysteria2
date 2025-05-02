#!/usr/bin/env python3

import json
import sys
import os
import asyncio
from init_paths import *
from paths import *

async def remove_user(username):
    """
    Remove a user from the USERS_FILE asynchronously.

    Args:
        username (str): The username to remove

    Returns:
        int: 0 on success, 1 on failure
    """
    if not os.path.isfile(USERS_FILE):
        print(f"Error: Config file {USERS_FILE} not found.")
        return 1

    try:
        async with asyncio.to_thread(open, USERS_FILE, 'r') as f:
            try:
                users_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error: {USERS_FILE} contains invalid JSON.")
                return 1

        if username in users_data:
            del users_data[username]
            async with asyncio.to_thread(open, USERS_FILE, 'w') as f:
                json.dump(users_data, f, indent=4)
            print(f"User {username} removed successfully.")
        else:
            print(f"Error: User {username} not found.")
            return 1

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    return 0

async def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <username>")
        sys.exit(1)

    username = sys.argv[1]
    exit_code = await remove_user(username)
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())