"""T005 packaging probe: entry point of the experimental Windows build (not the game).

Writes what it found (bundled font/locales via resource_root) to the per-user data dir,
opens the T003 text window, then appends whether the window closed cleanly.
Source run: uv run python -m bar_cadenza.app.package_probe [--seconds S]
Build:      uv run pyinstaller --noconfirm --clean tools/package_probe.spec
"""

import argparse
import datetime
import os
import sys

from bar_cadenza.app.paths import resource_root, user_data_dir
from bar_cadenza.ui import text_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=None, help="auto-quit after S seconds")
    args = parser.parse_args()
    root = resource_root()
    report = user_data_dir() / "package_probe.txt"
    report.write_text(
        "\n".join(
            [
                f"started={datetime.datetime.now().isoformat(timespec='seconds')}",
                f"frozen={getattr(sys, 'frozen', False)}",
                f"executable={sys.executable}",
                f"cwd={os.getcwd()}",
                f"resource_root={root}",
                f"font_ok={(root / 'assets/fonts/NanumGothic-Regular.ttf').is_file()}",
                f"font_license_ok={(root / 'assets/fonts/NanumGothic-OFL.txt').is_file()}",
                f"locales={sorted(p.name for p in (root / 'content/locales').glob('*.json'))}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    sent = text_experiment.run(args.seconds)
    with report.open("a", encoding="utf-8") as f:
        f.write(f"closed_cleanly=True sent={sent!r}\n")


if __name__ == "__main__":
    main()
