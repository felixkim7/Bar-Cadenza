# PyInstaller spec for the T005 packaging probe (not the game).
# Build from the repo root:  uv run pyinstaller --noconfirm --clean tools/package_probe.spec
# Output: dist/BarCadenzaProbe/BarCadenzaProbe.exe (one-folder build; build/ and dist/ are gitignored)
# Only the listed resources are bundled: no .env, saves, logs, references or docs.
from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "src/bar_cadenza/app/package_probe.py")],
    pathex=[str(ROOT / "src")],
    datas=[
        (str(ROOT / "assets/fonts"), "assets/fonts"),  # font + OFL license + provenance
        (str(ROOT / "content/locales"), "content/locales"),
    ],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="BarCadenzaProbe", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="BarCadenzaProbe")
