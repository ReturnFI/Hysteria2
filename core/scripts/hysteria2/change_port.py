#!/usr/bin/env python3

import json
import sys
import re
import subprocess
from init_paths import *
from paths import *

def update_port(port):
    """
    Update the port in the configuration file and restart the service.
    
    Args:
        port (str): The port number to set
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not re.match(r'^[0-9]+$', port) or int(port) < 1 or int(port) > 65535:
            print("Invalid port number. Please enter a number between 1 and 65535.")
            return False
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"Error: Config file {CONFIG_FILE} not found.")
            return False
        
        config['listen'] = f":{port}"
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        subprocess.run(["python3", CLI_PATH, "restart-hysteria2"],)
        
        print(f"Port changed successfully to {port}.")
        return True
    
    except Exception as e:
        print(f"Error updating port: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_port.py <port_number>")
        sys.exit(1)
    
    success = update_port(sys.argv[1])
    sys.exit(0 if success else 1)