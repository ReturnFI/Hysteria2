import json
import subprocess
import sys
from init_paths import *
from paths import *


def is_masquerade_enabled():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return "masquerade" in config
    except Exception as e:
        print(f"Error reading config: {e}")
        return False

def enable_masquerade(domain: str):
    if is_masquerade_enabled():
        print("Masquerade is already enabled.")
        sys.exit(0)

    url = f"https://{domain}"
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        config["masquerade"] = {
            "type": "proxy",
            "proxy": {
                "url": url,
                "rewriteHost": True
            },
            "listenHTTP": ":80",
            "listenHTTPS": ":443",
            "forceHTTPS": True
        }

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"Masquerade enabled with URL: {url}")
        subprocess.run(["python3", CLI_PATH, "restart-hysteria2"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception as e:
        print(f"Failed to enable masquerade: {e}")
        sys.exit(1)

def remove_masquerade():
    if not is_masquerade_enabled():
        print("Masquerade is not enabled.")
        sys.exit(0)

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        config.pop("masquerade", None)

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        print("Masquerade removed from config.json")
        subprocess.run(["python3", CLI_PATH, "restart-hysteria2"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception as e:
        print(f"Failed to remove masquerade: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 masquerade.py {1|2} [domain]")
        print("1: Enable Masquerade [domain]")
        print("2: Remove Masquerade")
        sys.exit(1)

    action = sys.argv[1]

    if action == "1":
        if len(sys.argv) < 3:
            print("Error: Missing domain argument for enabling masquerade.")
            sys.exit(1)
        domain = sys.argv[2]
        print(f"Enabling 'masquerade' with URL: {domain}...")
        enable_masquerade(domain)
    elif action == "2":
        print("Removing 'masquerade' from config.json...")
        remove_masquerade()
    else:
        print("Invalid option. Use 1 to enable or 2 to disable masquerade.")
        sys.exit(1)

if __name__ == "__main__":
    main()
