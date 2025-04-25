import subprocess
import concurrent.futures
import re
import json
import sys

from init_paths import *
from paths import *

DEFAULT_ARGS = ["-a", "-n", "-s"]

def run_show_uri(username):
    try:
        cmd = ["python3", CLI_PATH, "show-user-uri", "-u", username] + DEFAULT_ARGS
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout
        if "Invalid username" in output:
            return {"username": username, "error": "User not found"}
        return parse_output(username, output)
    except subprocess.CalledProcessError as e:
        return {"username": username, "error": e.stderr.strip()}

def parse_output(username, output):
    ipv4 = None
    ipv6 = None
    normal_sub = None

    # Match links
    ipv4_match = re.search(r"IPv4:\s*(hy2://[^\s]+)", output)
    ipv6_match = re.search(r"IPv6:\s*(hy2://[^\s]+)", output)
    normal_sub_match = re.search(r"Normal-SUB Sublink:\s*(https?://[^\s]+)", output)

    if ipv4_match:
        ipv4 = ipv4_match.group(1)
    if ipv6_match:
        ipv6 = ipv6_match.group(1)
    if normal_sub_match:
        normal_sub = normal_sub_match.group(1)

    return {
        "username": username,
        "ipv4": ipv4,
        "ipv6": ipv6,
        "normal_sub": normal_sub
    }

def batch_show_uri(usernames, max_workers=20):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(run_show_uri, usernames))
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 show_uri_json.py user1 user2 ...")
        sys.exit(1)

    usernames = sys.argv[1:]
    output_list = batch_show_uri(usernames)
    print(json.dumps(output_list, indent=2))