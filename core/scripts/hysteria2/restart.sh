#!/bin/bash

python3 /etc/hysteria/core/cli.py traffic-status > /dev/null 2>&1
systemctl restart hysteria-server.service