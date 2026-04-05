"""Detect Desktop path (handles OneDrive on Windows) and create output subdirectory."""

import sys
from pathlib import Path
import os


def detect_desktop(subdir: str) -> Path:
    home = Path.home()
    candidates = [
        Path(os.environ.get("OneDriveConsumer", "")) / "Desktop",
        Path(os.environ.get("OneDrive", "")) / "Desktop",
        home / "OneDrive" / "Desktop",
        home / "OneDrive - Personal" / "Desktop",
        home / "Desktop",
    ]
    desktop = next((p for p in candidates if p.exists()), home / "Desktop")
    out = desktop / subdir
    out.mkdir(parents=True, exist_ok=True)
    return out


if __name__ == "__main__":
    subdir = sys.argv[1] if len(sys.argv) > 1 else "bible-buddy"
    print(detect_desktop(subdir))
