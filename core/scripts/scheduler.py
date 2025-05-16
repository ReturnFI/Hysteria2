#!/usr/bin/env python3
import os
import sys
import time
import schedule
import logging
import subprocess
import fcntl
import datetime
from pathlib import Path
from paths import *

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/hysteria_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HysteriaScheduler")

# Constants
BASE_DIR = Path("/etc/hysteria")
VENV_ACTIVATE = BASE_DIR / "hysteria2_venv/bin/activate"
# CLI_PATH = BASE_DIR / "core/cli.py"
LOCK_FILE = "/tmp/hysteria_scheduler.lock"

def acquire_lock():
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd
    except IOError:
        logger.warning("Another process is already running and has the lock")
        return None

def release_lock(lock_fd):
    if lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()

def run_command(command, log_success=False):

    activate_cmd = f"source {VENV_ACTIVATE}"
    full_cmd = f"{activate_cmd} && {command}"
    
    try:
        result = subprocess.run(
            full_cmd, 
            shell=True, 
            executable="/bin/bash",
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Command failed: {full_cmd}")
            logger.error(f"Error: {result.stderr}")
        elif log_success:
            logger.info(f"Command executed successfully: {full_cmd}")
            
        return result.returncode == 0
    except Exception as e:
        logger.exception(f"Exception running command: {full_cmd}")
        return False

def check_traffic_status():
    lock_fd = acquire_lock()
    if not lock_fd:
        return
        
    try:
        success = run_command(f"python3 {CLI_PATH} traffic-status --no-gui", log_success=False)
        if not success:
            pass
    finally:
        release_lock(lock_fd)

def backup_hysteria():
    lock_fd = acquire_lock()
    if not lock_fd:
        logger.warning("Skipping backup due to lock")
        return
        
    try:
        run_command(f"python3 {CLI_PATH} backup-hysteria", log_success=True)
    finally:
        release_lock(lock_fd)

def main():
    logger.info("Starting Hysteria Scheduler")
    
    schedule.every(1).minutes.do(check_traffic_status)
    schedule.every(6).hours.do(backup_hysteria)
    
    backup_hysteria()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down scheduler")
            break
        except Exception as e:
            logger.exception("Error in main loop")
            time.sleep(60)

if __name__ == "__main__":
    main()