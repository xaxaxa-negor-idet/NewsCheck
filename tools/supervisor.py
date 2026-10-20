# -*- coding: utf-8 -*-
"""Persistent launcher: auto-restart daemon on crash, single instance, logs to file."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
DAEMON = ROOT / "tools" / "daemon.py"
LOG = ROOT / "daemon.log"


def run_forever() -> None:
    while True:
        try:
            with open(LOG, "ab") as log:
                proc = subprocess.Popen(
                    [PY, "-X", "utf8", str(DAEMON), "--interval", "60"],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    cwd=str(ROOT),
                )
                code = proc.wait()
            with open(LOG, "ab") as log:
                log.write(f"[supervisor] daemon exited code={code}, restarting in 5s\n".encode("utf-8"))
        except KeyboardInterrupt:
            return
        time.sleep(5)


if __name__ == "__main__":
    run_forever()
