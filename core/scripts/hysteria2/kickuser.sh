#!/bin/bash

USERNAME="$1"

if [ -z "$USERNAME" ]; then
  echo "Usage: kickuser.sh <username>"
  exit 1
fi

source /etc/hysteria/core/scripts/path.sh

SECRET=$(jq -r '.trafficStats.secret' "$CONFIG_FILE")
KICK_ENDPOINT="http://127.0.0.1:25413/kick"

if [ -z "$SECRET" ]; then
  echo "Error: Could not retrieve trafficStats secret from config.json"
  exit 1
fi

echo "Kicking user: $USERNAME"

curl -s -H "Authorization: $SECRET" -X POST -d "[\"$USERNAME\"]" "$KICK_ENDPOINT"

if [ $? -eq 0 ]; then
  echo "User '$USERNAME' kicked successfully."
else
  echo "Error kicking user '$USERNAME'."
  exit 1
fi

exit 0