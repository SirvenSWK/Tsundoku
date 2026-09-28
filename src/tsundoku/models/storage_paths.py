from __future__ import annotations

import os
import tempfile
from pathlib import Path


def data_directory() -> Path:
    """Return Tsundoku's per-user data directory."""
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return root / "Tsundoku"


def migrate_legacy_file(old_path: Path, new_path: Path) -> None:
    """Copy an older in-project data file once, without replacing newer user data."""
    if new_path.exists() or not old_path.exists():
        return
    new_path.parent.mkdir(parents=True, exist_ok=True)
    temporaryPath = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb", dir=new_path.parent, prefix=f"{new_path.name}.",
            suffix=".tmp", delete=False,
        ) as file:
            temporaryPath = Path(file.name)
            file.write(old_path.read_bytes())
            file.flush()
            os.fsync(file.fileno())
        if not new_path.exists():
            os.replace(temporaryPath, new_path)
    finally:
        if temporaryPath is not None and temporaryPath.exists():
            temporaryPath.unlink()
