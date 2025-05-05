#!/usr/bin/env python3

import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import datetime
from pathlib import Path
from init_paths import *
from paths import *

def run_command(command, capture_output=True, check=False):
    """Run a shell command and return its output"""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=capture_output,
        text=True,
        check=check
    )
    if capture_output:
        return result.returncode, result.stdout.strip()
    return result.returncode, None

def main():
    if len(sys.argv) < 2:
        print("Error: Backup file path is required.")
        return 1

    backup_zip_file = sys.argv[1]

    if not os.path.isfile(backup_zip_file):
        print(f"Error: Backup file not found: {backup_zip_file}")
        return 1

    if not backup_zip_file.lower().endswith('.zip'):
        print("Error: Backup file must be a .zip file.")
        return 1

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    restore_dir = f"/tmp/hysteria_restore_{timestamp}"
    target_dir = "/etc/hysteria"

    try:
        os.makedirs(restore_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(backup_zip_file) as zf:
                zf.testzip()
                zf.extractall(restore_dir)
        except zipfile.BadZipFile:
            print("Error: Invalid ZIP file.")
            return 1
        except Exception as e:
            print(f"Error: Could not extract the ZIP file: {e}")
            return 1
            
        expected_files = [
            "ca.key",
            "ca.crt",
            "users.json",
            "config.json",
            ".configs.env"
        ]
        
        for file in expected_files:
            file_path = os.path.join(restore_dir, file)
            if not os.path.isfile(file_path):
                print(f"Error: Required file '{file}' is missing from the backup.")
                return 1
        
        existing_backup_dir = f"/opt/hysbackup/restore_pre_backup_{timestamp}"
        os.makedirs(existing_backup_dir, exist_ok=True)
        
        for file in expected_files:
            source_file = os.path.join(target_dir, file)
            dest_file = os.path.join(existing_backup_dir, file)
            
            if os.path.isfile(source_file):
                try:
                    shutil.copy2(source_file, dest_file)
                except Exception as e:
                    print(f"Error creating backup file before restore from '{source_file}': {e}")
                    return 1
        
        for file in expected_files:
            source_file = os.path.join(restore_dir, file)
            dest_file = os.path.join(target_dir, file)
            
            try:
                shutil.copy2(source_file, dest_file)
            except Exception as e:
                print(f"Error: replace Configuration Files '{file}': {e}")
                shutil.rmtree(existing_backup_dir, ignore_errors=True)
                return 1
        
        config_file = os.path.join(target_dir, "config.json")
        
        if os.path.isfile(config_file):
            print("Checking and adjusting config.json based on system state...")
            
            ret_code, networkdef = run_command("ip route | grep '^default' | awk '{print $5}'")
            networkdef = networkdef.strip()
            
            if networkdef:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                for outbound in config.get('outbounds', []):
                    if outbound.get('name') == 'v4' and 'direct' in outbound:
                        current_v4_device = outbound['direct'].get('bindDevice', '')
                        
                        if current_v4_device != networkdef:
                            print(f"Updating v4 outbound bindDevice from '{current_v4_device}' to '{networkdef}'...")
                            outbound['direct']['bindDevice'] = networkdef
                            
                            with open(config_file, 'w') as f:
                                json.dump(config, f, indent=2)
            
            ret_code, _ = run_command("systemctl is-active --quiet wg-quick@wgcf.service", capture_output=False)
            
            if ret_code != 0:
                print("wgcf service is NOT active. Removing warps outbound and any ACL rules...")
                
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                config['outbounds'] = [outbound for outbound in config.get('outbounds', []) 
                                      if outbound.get('name') != 'warps']
                
                if 'acl' in config and 'inline' in config['acl']:
                    config['acl']['inline'] = [rule for rule in config['acl']['inline'] 
                                             if not rule.startswith('warps(')]
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
        
        run_command("chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt", 
                   capture_output=False)
        run_command("chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt", 
                   capture_output=False)
        
        ret_code, _ = run_command(f"python3 {CLI_PATH} restart-hysteria2", capture_output=False)
        
        if ret_code != 0:
            print("Error: Restart service failed.")
            return 1
        
        print("Hysteria configuration restored and updated successfully.")
        return 0
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1
    finally:
        shutil.rmtree(restore_dir, ignore_errors=True)
        if 'existing_backup_dir' in locals():
            shutil.rmtree(existing_backup_dir, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(main())