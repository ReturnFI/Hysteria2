#!/bin/bash

source /etc/hysteria/core/scripts/path.sh

if [ -z "$1" ]; then
  echo "Usage: $0 <username>"
  exit 1
fi

USERNAME=$1

if [ ! -f "$USERS_FILE" ]; then
  echo "users.json file not found!"
  exit 1
fi

if [ ! -f "$TRAFFIC_FILE" ]; then
  echo "traffic_data.json file not found!"
  exit 1
fi

USER_INFO=$(jq -r --arg username "$USERNAME" '.[$username] // empty' $USERS_FILE)

if [ -z "$USER_INFO" ]; then
  echo "User '$USERNAME' not found."
  exit 1
fi

TRAFFIC_INFO=$(jq -r --arg username "$USERNAME" '.[$username] // empty' $TRAFFIC_FILE)

echo "User Information:"
echo "$USER_INFO" | jq .

echo "Traffic Information:"
if [ -z "$TRAFFIC_INFO" ]; then
  echo "No traffic data found for user '$USERNAME'."
else
  echo "$TRAFFIC_INFO" | jq .
fi

exit 0
