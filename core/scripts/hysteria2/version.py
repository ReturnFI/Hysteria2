#!/usr/bin/env python3

import os
import sys
import requests
from pathlib import Path
from init_paths import *
from paths import *

def version_greater_equal(version1, version2):
    version1_parts = [int(part) for part in version1.strip().split('.')]
    version2_parts = [int(part) for part in version2.strip().split('.')]
    
    max_length = max(len(version1_parts), len(version2_parts))
    version1_parts.extend([0] * (max_length - len(version1_parts)))
    version2_parts.extend([0] * (max_length - len(version2_parts)))
    
    for i in range(max_length):
        if version1_parts[i] > version2_parts[i]:
            return True
        elif version1_parts[i] < version2_parts[i]:
            return False
    
    # If we get here, they're equal
    return True

def check_version():
    try:
        with open(LOCALVERSION, 'r') as f:
            local_version = f.read().strip()
        
        latest_version = requests.get(LATESTVERSION).text.strip()
        latest_changelog = requests.get(LASTESTCHANGE).text
        
        print(f"Panel Version: {local_version}")
        
        if not version_greater_equal(local_version, latest_version):
            print(f"Latest Version: {latest_version}")
            print(f"{latest_version} Version Change Log:")
            print(latest_changelog)
    except Exception as e:
        print(f"Error checking version: {e}", file=sys.stderr)
        sys.exit(1)

def show_version():
    try:
        with open(LOCALVERSION, 'r') as f:
            local_version = f.read().strip()
        
        print(f"Panel Version: {local_version}")
    except Exception as e:
        print(f"Error showing version: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} [check-version|show-version]", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check-version":
        check_version()
    elif command == "show-version":
        show_version()
    else:
        print(f"Usage: {sys.argv[0]} [check-version|show-version]", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()