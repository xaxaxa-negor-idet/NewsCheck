# -*- coding: utf-8 -*-
"""Single-instance lock for daemon: prevents multiple processes."""
from __future__ import annotations

import os
from pathlib import Path

LOCK_FILE = Path(__file__).resolve().parent.parent / "daemon.lock"


def acquire_lock() -> bool:
    """Return True if we are the only daemon; False if another is running."""
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            # check if process is alive
            if os.name == "nt":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
                if handle:
                    kernel32.CloseHandle(handle)
                    return False
            else:
                os.kill(pid, 0)
                return False
        except (ValueError, OSError, Exception):
            pass  # stale lock file
    LOCK_FILE.write_text(str(os.getpid()))
    return True


def release_lock() -> None:
    try:
        if LOCK_FILE.exists() and LOCK_FILE.read_text().strip() == str(os.getpid()):
            LOCK_FILE.unlink()
    except OSError:
        pass
