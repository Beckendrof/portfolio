#!/usr/bin/env python3
"""Watch for resume.pdf changes and auto-run the build pipeline."""

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


def timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_step(description: str, cmd: list[str]) -> bool:
    print(f"[{timestamp()}] {description}...")
    try:
        subprocess.run(cmd, check=True)
        print(f"[{timestamp()}] {description} — done")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[{timestamp()}] Error: {description} failed (exit code {e.returncode})")
        return False


class ResumeHandler(FileSystemEventHandler):
    def __init__(self):
        self._last_triggered = 0

    def on_modified(self, event):
        if event.is_directory:
            return
        if Path(event.src_path).name != "resume.pdf":
            return

        # Debounce: ignore events within 2 seconds of last trigger
        now = time.time()
        if now - self._last_triggered < 2:
            return
        self._last_triggered = now

        print(f"\n[{timestamp()}] Detected change to resume.pdf")
        time.sleep(1)  # debounce wait

        if not run_step("Parsing resume", [sys.executable, "scripts/parse_resume.py"]):
            return

        if not run_step("Building HTML", [sys.executable, "scripts/build.py"]):
            return

        if not run_step("Staging files", ["git", "add", "data/resume.json", "dist/index.html", "resume.pdf"]):
            return

        commit_msg = f"auto: update portfolio from resume ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        if not run_step("Committing", ["git", "commit", "-m", commit_msg]):
            return

        run_step("Pushing", ["git", "push"])
        print(f"[{timestamp()}] Pipeline complete.\n")


def main():
    print(f"[{timestamp()}] Watching for resume.pdf changes. Drop a new PDF to auto-deploy.")
    observer = Observer()
    observer.schedule(ResumeHandler(), path=".", recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print(f"\n[{timestamp()}] Watcher stopped.")
    observer.join()


if __name__ == "__main__":
    main()
