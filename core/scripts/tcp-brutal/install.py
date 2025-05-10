#!/usr/bin/env python3

import os
import subprocess

def main():
    print("Installing TCP Brutal...")
    
    subprocess.run("bash -c \"$(curl -fsSL https://tcp.hy2.sh/)\"", shell=True)
    os.system('clear')
    
    print("TCP Brutal installation complete.")

if __name__ == "__main__":
    main()