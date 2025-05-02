#!/usr/bin/env python3

import zipfile
from pathlib import Path
from datetime import datetime

backup_dir = Path("/opt/hysbackup")
backup_file = backup_dir / f"hysteria_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

files_to_backup = [
    Path("/etc/hysteria/ca.key"),
    Path("/etc/hysteria/ca.crt"),
    Path("/etc/hysteria/users.json"),
    Path("/etc/hysteria/config.json"),
    Path("/etc/hysteria/.configs.env"),
]

backup_dir.mkdir(parents=True, exist_ok=True)

try:
    with zipfile.ZipFile(backup_file, 'w') as zipf:
        for file_path in files_to_backup:
            if file_path.exists():
                zipf.write(file_path, arcname=file_path.name)
    print("Backup successfully created")
except Exception as e:
    print("Backup failed!", str(e))
