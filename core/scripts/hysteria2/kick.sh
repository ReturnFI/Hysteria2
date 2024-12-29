#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

LOCKFILE="/tmp/kick.lock"
exec 200>$LOCKFILE
flock -n 200 || exit 1

LOGFILE="/var/log/kick.log"
BACKUP_FILE="${USERS_FILE}.bak"

cp "$USERS_FILE" "$BACKUP_FILE"

kick_user() {
  local username=$1
  local secret=$2
  local kick_endpoint="http://127.0.0.1:25413/kick"
  curl -s -H "Authorization: $secret" -X POST -d "[\"$username\"]" "$kick_endpoint"
}

SECRET=$(jq -r '.trafficStats.secret' "$CONFIG_FILE")

if ! jq empty "$USERS_FILE"; then
  echo "$(date): [ERROR] Invalid users.json. Restoring backup." >> $LOGFILE
  cp "$BACKUP_FILE" "$USERS_FILE"
  exit 1
fi

handle_error() {
  echo "$(date): [ERROR] An error occurred. Restoring backup." >> $LOGFILE
  cp "$BACKUP_FILE" "$USERS_FILE"
  exit 1
}

trap handle_error ERR

for USERNAME in $(jq -r 'keys[]' "$USERS_FILE"); do
  BLOCKED=$(jq -r --arg user "$USERNAME" '.[$user].blocked // false' "$USERS_FILE")

  if [ "$BLOCKED" == "true" ]; then
    echo "$(date): [INFO] Skipping $USERNAME as they are already blocked." >> $LOGFILE
    continue
  fi

  MAX_DOWNLOAD_BYTES=$(jq -r --arg user "$USERNAME" '.[$user].max_download_bytes // 0' "$USERS_FILE")
  EXPIRATION_DAYS=$(jq -r --arg user "$USERNAME" '.[$user].expiration_days // 0' "$USERS_FILE")
  ACCOUNT_CREATION_DATE=$(jq -r --arg user "$USERNAME" '.[$user].account_creation_date' "$USERS_FILE")
  CURRENT_DOWNLOAD_BYTES=$(jq -r --arg user "$USERNAME" '.[$user].download_bytes // 0' "$USERS_FILE")

  if [ -z "$ACCOUNT_CREATION_DATE" ]; then
    echo "$(date): [INFO] Skipping $USERNAME due to missing account creation date." >> $LOGFILE
    continue
  fi

  CURRENT_DATE=$(date +%s)
  EXPIRATION_DATE=$(date -d "$ACCOUNT_CREATION_DATE + $EXPIRATION_DAYS days" +%s)

  if [ "$MAX_DOWNLOAD_BYTES" -gt 0 ] && [ "$CURRENT_DOWNLOAD_BYTES" -ge 0 ] && [ "$EXPIRATION_DAYS" -gt 0 ]; then
    if [ "$CURRENT_DOWNLOAD_BYTES" -ge "$MAX_DOWNLOAD_BYTES" ] || [ "$CURRENT_DATE" -ge "$EXPIRATION_DATE" ]; then
      for i in {1..3}; do
        jq --arg user "$USERNAME" '.[$user].blocked = true' "$USERS_FILE" > temp.json && mv temp.json "$USERS_FILE" && break
        sleep 1
      done
      kick_user "$USERNAME" "$SECRET"
      echo "$(date): [INFO] Blocked and kicked user $USERNAME." >> $LOGFILE
    fi
  else
    echo "$(date): [INFO] Skipping $USERNAME due to invalid or missing data." >> $LOGFILE
  fi
done

# echo "$(date): [INFO] Kick script completed successfully." >> $LOGFILE
# exit 0
