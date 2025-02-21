#!/bin/bash
source /etc/hysteria/core/scripts/path.sh

# Usage: ./restore.sh <backup_zip_file>

set -e 

BACKUP_ZIP_FILE="$1"
RESTORE_DIR="/tmp/hysteria_restore_$(date +%Y%m%d_%H%M%S)"
TARGET_DIR="/etc/hysteria"

if [ -z "$BACKUP_ZIP_FILE" ]; then
  echo "Error: Backup file path is required."
  exit 1
fi

if [ ! -f "$BACKUP_ZIP_FILE" ]; then
  echo "Error: Backup file not found: $BACKUP_ZIP_FILE"
  exit 1
fi

if [[ "$BACKUP_ZIP_FILE" != *.zip ]]; then
  echo "Error: Backup file must be a .zip file."
  exit 1
fi

mkdir -p "$RESTORE_DIR"

unzip -l "$BACKUP_ZIP_FILE" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Invalid ZIP file."
    rm -rf "$RESTORE_DIR" 
    exit 1
fi

unzip -o "$BACKUP_ZIP_FILE" -d "$RESTORE_DIR" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Could not extract the ZIP file."
    rm -rf "$RESTORE_DIR"
    exit 1
fi

expected_files=(
    "ca.key"
    "ca.crt"
    "users.json"
    "config.json"
    ".configs.env"
)

for file in "${expected_files[@]}"; do
    if [ ! -f "$RESTORE_DIR/$file" ]; then
        echo "Error: Required file '$file' is missing from the backup."
        rm -rf "$RESTORE_DIR"
        exit 1
    fi
    if [ ! -f "$RESTORE_DIR/$file" ]; then
        echo "Error: '$file' in the backup is not a regular file."
        rm -rf "$RESTORE_DIR"
        exit 1
    fi
done


timestamp=$(date +%Y%m%d_%H%M%S)
existing_backup_dir="/opt/hysbackup/restore_pre_backup_$timestamp"
mkdir -p "$existing_backup_dir"
for file in "${expected_files[@]}"; do
  if [ -f "$TARGET_DIR/$file" ]; then
    cp -p "$TARGET_DIR/$file" "$existing_backup_dir/$file"
    if [ $? -ne 0 ]; then
      echo "Error creating backup file before restore from '$TARGET_DIR/$file'."
      exit 1
    fi
  fi
done

for file in "${expected_files[@]}"; do
    cp -p "$RESTORE_DIR/$file" "$TARGET_DIR/$file"
     if [ $? -ne 0 ]; then
      echo "Error: replace Configuration Files '$file'."
      rm -rf "$existing_backup_dir"
      rm -rf "$RESTORE_DIR"
      exit 1
    fi
done

rm -rf "$RESTORE_DIR"
echo "Hysteria configuration restored successfully."

chown hysteria:hysteria /etc/hysteria/ca.key /etc/hysteria/ca.crt
chmod 640 /etc/hysteria/ca.key /etc/hysteria/ca.crt
python3 "$CLI_PATH" restart-hysteria2 > /dev/null 2>&1
if [ $? -ne 0 ]; then
      echo "Error: Restart service failed'."
      rm -rf "$existing_backup_dir"
      exit 1
fi

if [[ "$existing_backup_dir" != "" ]]; then
    rm -rf "$existing_backup_dir"
fi

exit 0
