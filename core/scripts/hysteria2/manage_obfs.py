#!/usr/bin/env python3

import json
import sys
import subprocess
import string
import secrets
from init_paths import *
from paths import *

def restart_hysteria():
    try:
        subprocess.run(["python3", CLI_PATH, "restart-hysteria2"], 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Failed to restart Hysteria2: {e}")

def remove_obfs():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        if 'obfs' in config:
            del config['obfs']
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            print("Successfully removed 'obfs' from config.json.")
        else:
            print("'obfs' section not found in config.json.")

        restart_hysteria()

    except FileNotFoundError:
        print(f"❌ Config file not found: {CONFIG_FILE}")
    except Exception as e:
        print(f"❌ Error removing 'obfs': {e}")

def generate_obfs():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        if 'obfs' in config:
            print("'obfs' section already exists. Replacing it.")
            del config['obfs']

        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

        config['obfs'] = {
            "type": "salamander",
            "salamander": {
                "password": password
            }
        }

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"Successfully added 'obfs' to config.json with password: {password}")

        restart_hysteria()

    except FileNotFoundError:
        print(f"Config file not found: {CONFIG_FILE}")
    except Exception as e:
        print(f"Error generating 'obfs': {e}")

def check_obfs():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        if 'obfs' in config:
            print("OBFS is active.")
        else:
            print("OBFS is not active.")
            
    except FileNotFoundError:
        print(f"Config file not found: {CONFIG_FILE}")
    except Exception as e:
        print(f"Error checking 'obfs' status: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 obfs_manager.py --remove|-r | --generate|-g | --check|-c")
        sys.exit(1)

    option = sys.argv[1]
    if option in ("--remove", "-r"):
        # print("Removing 'obfs' from config.json...")
        remove_obfs()
    elif option in ("--generate", "-g"):
        # print("Generating 'obfs' in config.json...")
        generate_obfs()
    elif option in ("--check", "-c"):
        # print("Checking 'obfs' status in config.json...")
        check_obfs()
    else:
        print("Invalid option. Use --remove|-r, --generate|-g, or --check|-c")
        sys.exit(1)

if __name__ == "__main__":
    main()