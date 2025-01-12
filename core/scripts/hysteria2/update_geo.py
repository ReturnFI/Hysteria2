#!/usr/bin/env python3
import os
import subprocess
from enum import Enum
import sys
import requests


class GeoCountry(Enum):
    IRAN = {
        'geosite': 'https://github.com/chocolate4u/Iran-v2ray-rules/releases/latest/download/geosite.dat',
        'geoip': 'https://github.com/chocolate4u/Iran-v2ray-rules/releases/latest/download/geoip.dat'
    }
    CHINA = {
        'geosite': 'https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat',
        'geoip': 'https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat'
    }
    RUSSIA = {
        'geosite': 'https://github.com/runetfreedom/russia-v2ray-rules-dat/releases/latest/download/geosite.dat',
        'geoip': 'https://github.com/runetfreedom/russia-v2ray-rules-dat/releases/latest/download/geoip.dat'
    }

GEOSITE_PATH = "/etc/hysteria/geosite.dat"
GEOIP_PATH = "/etc/hysteria/geoip.dat"

def remove_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed existing file: {file_path}")
    except Exception as e:
        print(f"Error removing file {file_path}: {e}")

def download_file(url, destination, chunk_size=32768):
    try:
        destination_dir = os.path.dirname(destination)
        if destination_dir and not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(destination, "wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                file.write(chunk)

        print(f"File successfully downloaded to: {destination}")

    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to download the file from '{url}'.\n{e}")
    except IOError as e:
        print(f"Error: Failed to save the file to '{destination}'.\n{e}")

def update_geo_files(country='iran'):
    try:
        print(f"Starting geo files update for {country.upper()}...")
        country_enum = GeoCountry[country.upper()]
        remove_file(GEOSITE_PATH)
        remove_file(GEOIP_PATH)
        download_file(country_enum.value['geosite'], GEOSITE_PATH)
        download_file(country_enum.value['geoip'], GEOIP_PATH)
        print("Geo files update completed successfully.")
    except KeyError:
        print(f"Invalid country selection. Available options: {', '.join([c.name.lower() for c in GeoCountry])}")
    except Exception as e:
        print(f"An error occurred during the update process: {e}")

if __name__ == "__main__":
    country = sys.argv[1] if len(sys.argv) > 1 else 'iran'
    update_geo_files(country)
