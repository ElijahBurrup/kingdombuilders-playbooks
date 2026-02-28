"""
SetHut Launcher — Launches a Claude session to generate a new playbook.

Runs every 30 minutes via Windows Task Scheduler.
Launches Claude in a Git Bash (mintty) window with the full prompt chain:
  1. Read master prompt
  2. Read KingdomBuilders prompt
  3. Read playbook prompt
  4. Execute SetHut

Safeguards:
  - Won't launch if a SetHut session is already running
  - Won't launch if mintty process count exceeds MAX_MINTTY
  - --hold error: window auto-closes on success, stays open on crash

Scheduled: Windows Task Scheduler every 30 min
Manual:    python sethut_launcher.py
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# --- Config ---

MINTTY = r"C:\Program Files\Git\usr\bin\mintty.exe"
GIT_BASH_ICON = r"C:\Program Files\Git\git-bash.exe"
MAX_MINTTY = 4  # hard cap on mintty processes

WORK_DIR = "/c/Projects/KingdomBuilders.AI"
WINDOW_TITLE = "Claude Work: SetHut"

MASTER_PROMPT = r"S:\My Drive\masterprompt.md"
KB_PROMPT = r"S:\My Drive\1. Projects\KingdomBuilders.AI\Documentation\claude_prompt.md"
PLAYBOOK_PROMPT = r"C:\Users\elija\.claude\projects\C--Users-elija\memory\kingdombuilders-playbooks.md"

LOG_DIR = Path(r"S:\My Drive\1. Projects\Tools\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- Logging ---

_handlers = [logging.FileHandler(LOG_DIR / "sethut_launcher.log", encoding="utf-8")]
try:
    _stream = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)
    _handlers.append(logging.StreamHandler(_stream))
except (AttributeError, OSError, ValueError):
    pass  # pythonw.exe has no stdout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=_handlers,
)
log = logging.getLogger("sethut_launcher")


def count_mintty_processes():
    """Count running mintty.exe processes."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq mintty.exe", "/NH", "/FO", "CSV"],
            capture_output=True, text=True, timeout=10,
        )
        return sum(1 for line in result.stdout.strip().splitlines() if "mintty" in line.lower())
    except Exception as e:
        log.warning(f"Could not count mintty processes: {e}")
        return 0


def has_sethut_window():
    """Check if a SetHut Claude window is already running."""
    try:
        result = subprocess.run(
            ["tasklist", "/V", "/FI", "IMAGENAME eq mintty.exe", "/NH", "/FO", "CSV"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.strip().splitlines():
            if WINDOW_TITLE.lower() in line.lower():
                return True
        return False
    except Exception as e:
        log.warning(f"Could not check for SetHut window: {e}")
        return False


def launch_sethut():
    """Launch Claude in a Git Bash window with the SetHut prompt chain."""
    # Scrub CLAUDE* env vars for clean session
    env = os.environ.copy()
    for key in list(env.keys()):
        if "CLAUDE" in key.upper():
            env.pop(key)

    # Build the prompt: read all three prompt files, then SetHut
    prompt_parts = [
        f"read '{MASTER_PROMPT}'",
        f"then read '{KB_PROMPT}'",
        f"then read '{PLAYBOOK_PROMPT}'",
        "then SetHut",
    ]
    prompt = " ".join(prompt_parts)
    bash_cmd = f"cd '{WORK_DIR}' && claude \"{prompt}\""

    cmd = [
        MINTTY,
        "-o", "AppID=GitForWindows.Bash",
        "-o", "AppName=Git Bash",
        "-i", GIT_BASH_ICON,
        "-t", WINDOW_TITLE,
        "--hold", "error",
        "--",
        "/usr/bin/bash", "-lic", bash_cmd,
    ]

    log.info(f"Launching: {' '.join(cmd)}")
    subprocess.Popen(cmd, env=env)
    log.info(f"Launched: {WINDOW_TITLE}")
    return True


def main():
    log.info("=" * 60)
    log.info("SetHut Launcher starting")

    # Guard 1: Already running
    if has_sethut_window():
        log.info("SetHut session already active. Skipping.")
        return

    # Guard 2: Too many mintty processes
    mintty_count = count_mintty_processes()
    if mintty_count >= MAX_MINTTY:
        log.warning(f"Mintty count ({mintty_count}) >= limit ({MAX_MINTTY}). Skipping.")
        return

    # Launch
    launch_sethut()
    log.info("SetHut Launcher done")


if __name__ == "__main__":
    main()
