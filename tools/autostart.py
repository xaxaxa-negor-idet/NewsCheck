# -*- coding: utf-8 -*-
# Autostart via Startup folder (no admin rights needed)
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STARTUP = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
BAT = STARTUP / "NewsCheckDaemon.bat"

BAT_CONTENT = f'''@echo off
cd /d "{ROOT}"
start "NewsCheck" /min "{sys.executable}" -X utf8 "tools\\supervisor.py"
'''

def install() -> bool:
    try:
        STARTUP.mkdir(parents=True, exist_ok=True)
        BAT.write_text(BAT_CONTENT, encoding="utf-8")
        return True
    except Exception:
        return False

def uninstall() -> bool:
    try:
        if BAT.exists():
            BAT.unlink()
        return True
    except Exception:
        return False

def status() -> str:
    return "INSTALLED" if BAT.exists() else "NOT_INSTALLED"

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "install":
        print("installed" if install() else "failed")
    elif action == "uninstall":
        print("uninstalled" if uninstall() else "failed")
    else:
        print(status())
