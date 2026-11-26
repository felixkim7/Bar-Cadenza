"""Where bundled resources and per-user data live, from source or a PyInstaller build."""

import sys
from pathlib import Path

from platformdirs import user_data_path

APP_NAME = "BarCadenza"


def resource_root() -> Path:
    """Read-only bundled files (assets/, content/): the PyInstaller bundle directory when
    frozen, otherwise the repository root. Never the current working directory."""
    bundle = getattr(sys, "_MEIPASS", None)
    return Path(bundle) if bundle else Path(__file__).resolve().parents[3]


def user_data_dir() -> Path:
    """Per-user writable directory for saves and logs (Windows: %LOCALAPPDATA%\\BarCadenza)."""
    path = user_data_path(APP_NAME, appauthor=False)
    path.mkdir(parents=True, exist_ok=True)
    return path
