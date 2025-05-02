#!/usr/bin/env python3

import json
import sys
import os
import asyncio
from init_paths import *
from paths import *

def sync_remove_user(username):
    if not os.path.isfile(USERS_FILE):
        return 1, f"Error: Config file {USERS_FILE} not found."

    try:
        with open(USERS_FILE, 'r') as f:
            try:
                users_data = json.load(f)
            except json.JSONDecodeError:
                return 1, f"Error: {USERS_FILE} contains invalid JSON."

        if username in users_data:
            del users_data[username]
            with open(USERS_FILE, 'w') as f:
                json.dump(users_data, f, indent=4)
            return 0, f"User {username} removed successfully."
        else:
            return 1, f"Error: User {username} not found."

    except Exception as e:
        return 1, f"Error: {str(e)}"

async def remove_user(username):
    return await asyncio.to_thread(sync_remove_user, username)

async def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <username>")
        sys.exit(1)

    username = sys.argv[1]
    exit_code, message = await remove_user(username)
    print(message)
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
