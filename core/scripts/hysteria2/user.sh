#!/bin/bash

ADDR="$1"
AUTH="$2"
TX="$3"

source /etc/hysteria/core/scripts/path.sh

IFS=':' read -r USERNAME PASSWORD <<< "$AUTH"

STORED_PASSWORD=$(jq -r --arg user "$USERNAME" '.[$user].password' "$USERS_FILE")
MAX_DOWNLOAD_BYTES=$(jq -r --arg user "$USERNAME" '.[$user].max_download_bytes' "$USERS_FILE")
EXPIRATION_DAYS=$(jq -r --arg user "$USERNAME" '.[$user].expiration_days' "$USERS_FILE")
ACCOUNT_CREATION_DATE=$(jq -r --arg user "$USERNAME" '.[$user].account_creation_date' "$USERS_FILE")
BLOCKED=$(jq -r --arg user "$USERNAME" '.[$user].blocked' "$USERS_FILE")
CURRENT_DOWNLOAD_BYTES=$(jq -r --arg user "$USERNAME" '.[$user].download_bytes' "$USERS_FILE")

if [ "$BLOCKED" == "true" ]; then
  sleep 20 
  exit 1
fi

if [ "$STORED_PASSWORD" != "$PASSWORD" ]; then
  sleep 20
  exit 1
fi

CURRENT_DATE=$(date +%s)
EXPIRATION_DATE=$(date -d "$ACCOUNT_CREATION_DATE + $EXPIRATION_DAYS days" +%s)

if [ "$CURRENT_DATE" -ge "$EXPIRATION_DATE" ]; then
  jq --arg user "$USERNAME" '.[$user].blocked = true' "$USERS_FILE" > temp.json && mv temp.json "$USERS_FILE"
  exit 1
fi

if [ "$CURRENT_DOWNLOAD_BYTES" -ge "$MAX_DOWNLOAD_BYTES" ]; then
  SECRET=$(jq -r '.trafficStats.secret' "$CONFIG_FILE")
  KICK_ENDPOINT="http://127.0.0.1:25413/kick"
  curl -s -H "Authorization: $SECRET" -X POST -d "[\"$USERNAME\"]" "$KICK_ENDPOINT"

  jq --arg user "$USERNAME" '.[$user].blocked = true' "$USERS_FILE" > temp.json && mv temp.json "$USERS_FILE"
  exit 1
fi

echo "$USERNAME"
exit 0
