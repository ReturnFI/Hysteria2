#!/bin/bash

source /etc/hysteria/core/scripts/path.sh


# Check if a username is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <username>"
  exit 1
fi

USERNAME=$1

# Check if users.json file exists
if [ ! -f "$USERS_FILE" ]; then
  echo "users.json file not found!"
  exit 1
fi

# Extract user info using jq
USER_INFO=$(jq -r --arg username "$USERNAME" '.[$username] // empty' $USERS_FILE)

# Check if user info is found
if [ -z "$USER_INFO" ]; then
  echo "User '$USERNAME' not found."
  exit 1
fi

# Print user info
echo "$USER_INFO" | jq .

exit 0
