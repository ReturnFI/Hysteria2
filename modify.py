import json
import os
import subprocess
from datetime import datetime

users_file_path = '/etc/hysteria/users/users.json'

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
    for i, user in enumerate(users.keys(), start=1):
        print(f"{i}. {user}")

def edit_user(users):
    list_users(users)
    try:
        choice = int(input("Enter the number of the user to edit: "))
        username = list(users.keys())[choice - 1]
    except (ValueError, IndexError):
        print("Invalid choice.")
        return
    
    print(f"Editing user: {username}")

    change_password = input(f"Change password? (current: {users[username]['password']}) [y/N]: ").lower() == 'y'
    if change_password:
        new_password = generate_password()
        users[username]['password'] = new_password
        print(f"New password: {new_password}")
    
    while True:
        max_download_gb = input(f"Enter new max download bytes in GB (current: {users[username]['max_download_bytes'] // (1024 ** 3)} GB): ")
        if max_download_gb.isdigit():
            users[username]['max_download_bytes'] = int(max_download_gb) * (1024 ** 3)
            break
        else:
            print("Invalid input. Please enter a valid number.")

    while True:
        expiration_days = input(f"Enter new expiration days (current: {users[username]['expiration_days']}): ")
        if expiration_days.isdigit():
            users[username]['expiration_days'] = int(expiration_days)
            break
        else:
            print("Invalid input. Please enter a valid number.")
    
    blocked = input(f"Blocked? (current: {users[username]['blocked']}) [true/false]: ").lower()
    if blocked:
        users[username]['blocked'] = blocked == 'true'

    change_date = input(f"Change account creation date to today? (current: {users[username]['account_creation_date']}) [y/N]: ").lower() == 'y'
    if change_date:
        users[username]['account_creation_date'] = datetime.today().strftime('%Y-%m-%d')

def main():
    if not os.path.exists(users_file_path):
        print(f"File {users_file_path} does not exist.")
        return

    users = load_users()
    
    while True:
        print("1. Edit user")
        print("2. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            edit_user(users)
            save_users(users)
        elif choice == "2":
            return
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
