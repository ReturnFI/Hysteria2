#!/usr/bin/env python3

import sys
import json
from hysteria2_api import Hysteria2Client
import time
from init_paths import *
from paths import *


def get_secret() -> str:
    if not CONFIG_FILE.exists():
        print("Error: config.json file not found!", file=sys.stderr)
        sys.exit(1)

    with CONFIG_FILE.open() as f:
        data = json.load(f)

    secret = data.get("trafficStats", {}).get("secret")
    if not secret:
        print("Error: secret not found in config.json!", file=sys.stderr)
        sys.exit(1)

    return secret


def convert_bytes(bytes_val: int) -> str:
    units = [("TB", 1 << 40), ("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)]
    for unit, factor in units:
        if bytes_val >= factor:
            return f"{bytes_val / factor:.2f} {unit}"
    return f"{bytes_val} B"


def get_cpu_usage(interval: float = 0.1) -> float:
    def read_cpu_times():
        with open("/proc/stat") as f:
            line = f.readline()
        fields = list(map(int, line.strip().split()[1:]))
        idle, total = fields[3], sum(fields)
        return idle, total

    idle1, total1 = read_cpu_times()
    time.sleep(interval)
    idle2, total2 = read_cpu_times()

    idle_delta = idle2 - idle1
    total_delta = total2 - total1
    cpu_usage = 100.0 * (1 - idle_delta / total_delta) if total_delta else 0.0
    return round(cpu_usage, 1)



def get_memory_usage() -> tuple[int, int]:
    mem_info = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(':')
                    if parts[1].isdigit():
                        mem_info[key] = int(parts[1])
    except FileNotFoundError:
        print("Error: /proc/meminfo not found.", file=sys.stderr)
        return 0, 0
    except Exception as e:
        print(f"Error reading /proc/meminfo: {e}", file=sys.stderr)
        return 0, 0

    mem_total_kb = mem_info.get("MemTotal", 0)
    mem_free_kb = mem_info.get("MemFree", 0)
    buffers_kb = mem_info.get("Buffers", 0)
    cached_kb = mem_info.get("Cached", 0)
    sreclaimable_kb = mem_info.get("SReclaimable", 0)

    used_kb = mem_total_kb - mem_free_kb - buffers_kb - cached_kb - sreclaimable_kb
    
    if used_kb < 0:
        used_kb = mem_total_kb - mem_info.get("MemAvailable", mem_total_kb)
        used_kb = max(0, used_kb)


    total_mb = mem_total_kb // 1024
    used_mb = used_kb // 1024
    
    return total_mb, used_mb



def get_online_user_count(secret: str) -> int:
    try:
        client = Hysteria2Client(
            base_url=API_BASE_URL,
            secret=secret
        )
        online_users = client.get_online_clients()
        return sum(1 for user in online_users.values() if user.is_online)
    except Exception as e:
        print(f"Error getting online users: {e}", file=sys.stderr)
        return 0


def get_total_traffic() -> tuple[int, int]:
    if not USERS_FILE.exists():
        return 0, 0

    try:
        with USERS_FILE.open() as f:
            users = json.load(f)

        total_upload = 0
        total_download = 0

        for user_data in users.values():
            total_upload += int(user_data.get("upload_bytes", 0) or 0)
            total_download += int(user_data.get("download_bytes", 0) or 0)

        return total_upload, total_download
    except Exception as e:
        print(f"Error parsing traffic data: {e}", file=sys.stderr)
        return 0, 0



def main():
    secret = get_secret()

    cpu_usage = get_cpu_usage()
    mem_total, mem_used = get_memory_usage()
    online_users = get_online_user_count(secret)

    print(f"📈 CPU Usage: {cpu_usage}")
    print(f"📋 Total RAM: {mem_total}MB")
    print(f"💻 Used RAM: {mem_used}MB")
    print(f"👥 Online Users: {online_users}")
    print()

    total_upload, total_download = get_total_traffic()

    print(f"🔼 Uploaded Traffic: {convert_bytes(total_upload)}")
    print(f"🔽 Downloaded Traffic: {convert_bytes(total_download)}")
    print(f"📊 Total Traffic: {convert_bytes(total_upload + total_download)}")


if __name__ == "__main__":
    main()
