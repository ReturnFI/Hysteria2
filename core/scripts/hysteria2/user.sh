#!/bin/bash

ADDR="$1"
AUTH="$2"
TX="$3"

# Source the path.sh script to load variables
source /etc/hysteria/core/scripts/path.sh

# Extract username and password from AUTH
IFS=':' read -r USERNAME PASSWORD <<< "$AUTH"

# Retrieve stored user data
STORED_PASSWORD=$(jq -r --arg user "$USERNAME" '.[$user].password' "$USERS_FILE")
MAX_DOWNLOAD_BYTES=$(jq -r --arg user "$USERNAME" '.[$user].max_download_bytes' "$USERS_FILE")
EXPIRATION_DAYS=$(jq -r --arg user "$USERNAME" '.[$user].expiration_days' "$USERS_FILE")
ACCOUNT_CREATION_DATE=$(jq -r --arg user "$USERNAME" '.[$user].account_creation_date' "$USERS_FILE")
BLOCKED=$(jq -r --arg user "$USERNAME" '.[$user].blocked' "$USERS_FILE")

# Check if the user is blocked
if [ "$BLOCKED" == "true" ]; then
  exit 1
fi

# Check if the provided password matches the stored password
if [ "$STORED_PASSWORD" != "$PASSWORD" ]; then
  exit 1
fi

# Check if the user's account has expired
CURRENT_DATE=$(date +%s)
EXPIRATION_DATE=$(date -d "$ACCOUNT_CREATION_DATE + $EXPIRATION_DAYS days" +%s)

if [ "$CURRENT_DATE" -ge "$EXPIRATION_DATE" ]; then
  jq --arg user "$USERNAME" '.[$user].blocked = true' "$USERS_FILE" > temp.json && mv temp.json "$USERS_FILE"
  exit 1
fi

# Check if the user's download limit has been exceeded
CURRENT_DOWNLOAD_BYTES=$(jq -r --arg user "$USERNAME" '.[$user].download_bytes' "$TRAFFIC_FILE")

if [ "$CURRENT_DOWNLOAD_BYTES" -ge "$MAX_DOWNLOAD_BYTES" ]; then
  SECRET=$(jq -r '.trafficStats.secret' "$CONFIG_FILE")
  KICK_ENDPOINT="http://127.0.0.1:25413/kick"
  curl -s -H "Authorization: $SECRET" -X POST -d "[\"$USERNAME\"]" "$KICK_ENDPOINT"

  jq --arg user "$USERNAME" '.[$user].blocked = true' "$USERS_FILE" > temp.json && mv temp.json "$USERS_FILE"
  exit 1
fi

# If all checks pass, print the username and exit successfully
echo "$USERNAME"
exit 0
