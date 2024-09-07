#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

kick_user() {
  local username=$1
  local secret=$2
  local kick_endpoint="http://127.0.0.1:25413/kick"
  curl -s -H "Authorization: $secret" -X POST -d "[\"$username\"]" "$kick_endpoint"
}

SECRET=$(jq -r '.trafficStats.secret' "$CONFIG_FILE")

for USERNAME in $(jq -r 'keys[]' "$USERS_FILE"); do
  MAX_DOWNLOAD_BYTES=$(jq -r --arg user "$USERNAME" '.[$user].max_download_bytes // 0' "$USERS_FILE")
  EXPIRATION_DAYS=$(jq -r --arg user "$USERNAME" '.[$user].expiration_days // 0' "$USERS_FILE")
  ACCOUNT_CREATION_DATE=$(jq -r --arg user "$USERNAME" '.[$user].account_creation_date' "$USERS_FILE")
  CURRENT_DOWNLOAD_BYTES=$(jq -r --arg user "$USERNAME" '.[$user].download_bytes // 0' "$USERS_FILE")
  BLOCKED=$(jq -r --arg user "$USERNAME" '.[$user].blocked // false' "$USERS_FILE")

  if [ -z "$ACCOUNT_CREATION_DATE" ]; then
    echo "Skipping $USERNAME due to missing account creation date."
    continue
  fi

  CURRENT_DATE=$(date +%s)
  EXPIRATION_DATE=$(date -d "$ACCOUNT_CREATION_DATE + $EXPIRATION_DAYS days" +%s)

  if [ "$MAX_DOWNLOAD_BYTES" -gt 0 ] && [ "$CURRENT_DOWNLOAD_BYTES" -ge 0 ] && [ "$EXPIRATION_DAYS" -gt 0 ]; then
    if [ "$CURRENT_DOWNLOAD_BYTES" -ge "$MAX_DOWNLOAD_BYTES" ] || [ "$CURRENT_DATE" -ge "$EXPIRATION_DATE" ]; then
      jq --arg user "$USERNAME" '.[$user].blocked = true' "$USERS_FILE" > temp.json && mv temp.json "$USERS_FILE"
      kick_user "$USERNAME" "$SECRET"
    fi
  else
    echo "Skipping $USERNAME due to invalid or missing data."
  fi
done
