"""Print starter status using only the Python standard library."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
print("Bar Cadenza starter: specifications and scaffold, not a playable game.")
print(f"Python: {sys.version.split()[0]}")
print(f"Project: {root}")
print("Next task: T001 — Windows environment and dependency lock.")
print("No API provider is configured; no network call was made.")
