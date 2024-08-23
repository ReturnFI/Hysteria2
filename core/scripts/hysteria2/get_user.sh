#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

while getopts ":u:" opt; do
  case ${opt} in
    u )
      USERNAME=$OPTARG
      ;;
    \? )
      echo "Usage: $0 -u <username>"
      exit 1
      ;;
  esac
done

if [ -z "$USERNAME" ]; then
  echo "Usage: $0 -u <username>"
  exit 1
fi

if [ ! -f "$USERS_FILE" ]; then
  echo "users.json file not found at $USERS_FILE!"
  exit 1
fi

USER_INFO=$(jq -r --arg username "$USERNAME" '.[$username] // empty' "$USERS_FILE")

if [ -z "$USER_INFO" ]; then
  echo "User '$USERNAME' not found in $USERS_FILE."
  exit 1
fi

echo "$USER_INFO" | jq .

UPLOAD_BYTES=$(echo "$USER_INFO" | jq -r '.upload_bytes // "No upload data available"')
DOWNLOAD_BYTES=$(echo "$USER_INFO" | jq -r '.download_bytes // "No download data available"')
STATUS=$(echo "$USER_INFO" | jq -r '.status // "Status unavailable"')

exit 0
