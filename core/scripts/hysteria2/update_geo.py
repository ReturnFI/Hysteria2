#!/usr/bin/env python3
import os
import subprocess

GEOSITE_PATH = "/etc/hysteria/geosite.dat"
GEOIP_PATH = "/etc/hysteria/geoip.dat"
GEOSITE_URL = "https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geosite.dat"
GEOIP_URL = "https://raw.githubusercontent.com/Chocolate4U/Iran-v2ray-rules/release/geoip.dat"


def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Removed existing file: {file_path}")


def download_file(url, destination):
    try:
        subprocess.run(
            ["wget", "-O", destination, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        print(f"Downloaded {url} to {destination}")
    except subprocess.CalledProcessError:
        print(f"Failed to download {url}")


def update_geo_files():
    try:
        print("Starting geo files update...")

        remove_file(GEOSITE_PATH)
        remove_file(GEOIP_PATH)
        download_file(GEOSITE_URL, GEOSITE_PATH)
        download_file(GEOIP_URL, GEOIP_PATH)

        print("Geo files update completed successfully.")

    except Exception as e:
        print(f"An error occurred during the update process: {e}")


if __name__ == "__main__":
    update_geo_files()
