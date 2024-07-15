#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import datetime

users_file_path = '/etc/hysteria/users/users.json'

def colors():
    green='\033[0;32m'
    cyan='\033[0;36m'
    red='\033[0;31m'
    NC='\033[0m' # No Color
    return green, cyan, red, NC

def load_users():
    with open(users_file_path, 'r') as file:
        return json.load(file)

def save_users(users):
    with open(users_file_path, 'w') as file:
        json.dump(users, file, indent=4)

def generate_password():
    result = subprocess.run(['pwgen', '-s', '32', '1'], capture_output=True, text=True)
    return result.stdout.strip()

def list_users(users):
    green, cyan, red, NC = colors()
    print(f"{green}List of Users{NC}\n")
    for i, user in enumerate(users.keys(), start=1):
        print(f"{cyan}{i}. {user}{NC}")

def edit_user(users):
    green, cyan, red, NC = colors()
    list_users(users)
    try:
        choice = int(input(f"{green}Enter the number of the user to edit:{NC} "))
        username = list(users.keys())[choice - 1]
    except (ValueError, IndexError):
        print(f"{green}Invalid choice.{NC}")
        return
    
    print(f"{green}Editing user: {cyan}{username}{NC}")

    change_password = input(f"Change password? (current: {users[username]['password']}) [y/N]: ").lower() == 'y'
    if change_password:
        new_password = generate_password()
        users[username]['password'] = new_password
        print(f"{green}New password: {cyan}{new_password}{NC}")
    
    while True:
        current_max_download_gb = users[username]['max_download_bytes'] // (1024 ** 3)
        max_download_gb = input(f"Enter new max download bytes in GB (current: {current_max_download_gb} GB, press Enter to keep current): ")
        if max_download_gb.strip() == '':
            break
        elif max_download_gb.isdigit():
            users[username]['max_download_bytes'] = int(max_download_gb) * (1024 ** 3)
            break
        else:
            print(f"{red}Invalid input. Please enter a valid number or press Enter to keep current.{NC}")

    while True:
        expiration_days = input(f"Enter new expiration days (current: {users[username]['expiration_days']}, press Enter to keep current): ")
        if expiration_days.strip() == '':
            break
        elif expiration_days.isdigit():
            users[username]['expiration_days'] = int(expiration_days)
            break
        else:
            print(f"{red}Invalid input. Please enter a valid number or press Enter to keep current.{NC}")
    
    blocked = input(f"Blocked? (current: {users[username]['blocked']}) [true/false]: ").lower()
    if blocked:
        users[username]['blocked'] = blocked == 'true'

    change_date = input(f"Change account creation date to today? (current: {users[username]['account_creation_date']}) [y/N]: ").lower() == 'y'
    if change_date:
        users[username]['account_creation_date'] = datetime.today().strftime('%Y-%m-%d')

def main():
    green, cyan, red, NC = colors()

    if not os.path.exists(users_file_path):
        print(f"{red}File {users_file_path} does not exist.{NC}")
        return

    users = load_users()
    
    while True:
        print(f"{green}1. Edit user{NC}")
        print(f"{red}2. Exit{NC}")
        choice = input(f"{NC}Enter your choice: {NC}")

        if choice == "1":
            edit_user(users)
            save_users(users)
        elif choice == "2":
            print(f"{red}Exiting...{NC}")
            break
        else:
            print(f"{NC}Invalid choice. Please try again.{NC}")

if __name__ == "__main__":
    main()

