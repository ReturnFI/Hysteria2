#!/usr/bin/env python3

import subprocess
import sys
import os
from init_paths import *
from paths import *

def restart_hysteria_server():
    """
    Restarts the Hysteria server service.

    Returns:
        int: 0 on success, 1 on failure.
    """
    try:
        subprocess.run([sys.executable, CLI_PATH, "traffic-status"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        subprocess.run(["systemctl", "restart", "hysteria-server.service"], check=True)
        print("Hysteria server restarted successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to restart the Hysteria server.")
        return 1
    except FileNotFoundError:
        print(f"Error: CLI script not found at {CLI_PATH}.")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    exit_code = restart_hysteria_server()
    sys.exit(exit_code)