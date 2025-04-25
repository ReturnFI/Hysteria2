import sys
from pathlib import Path

core_scripts_dir = Path(__file__).resolve().parents[1]

if str(core_scripts_dir) not in sys.path:
    sys.path.append(str(core_scripts_dir))
