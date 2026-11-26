# Windows setup

## Baseline
Windows is the acceptance platform. Python 3.14 is the user-selected baseline (D019). Use one native Windows project environment. WSL/Linux can assist development but cannot certify Windows IME, audio, paths or executable behavior. Never share a .venv between operating systems.

Official references: https://www.python.org/downloads/windows/ ; https://docs.astral.sh/uv/getting-started/installation/ ; https://git-scm.com/downloads ; https://code.claude.com/docs/en/setup . Follow current official install instructions rather than outdated copied installation commands.

## T001 commands (PowerShell, project root)
```powershell
py -3.14 --version
uv --version
git --version
claude --version
py -3.14 tools/check_starter.py
uv lock
uv sync --locked
uv run python -m bar_cadenza
uv run python -c "import pygame; print(pygame.version.ver); print(getattr(pygame, 'IS_CE', False))"
```
Expected now: the entry point opens the game shell window (main menu → language → placeholder pre-shift/bar/results); add `--seconds 3` to auto-quit. The pygame check should identify pygame-ce. Do not install the original pygame alongside pygame-ce in the same environment.

The archive intentionally omits uv.lock because dependency resolution was not claimed. Generate it in T001, commit it after successful resolution, and use `uv sync --locked` thereafter. Initial bounded ranges are compatibility proposals, not a tested release environment. Update a range only for an observed issue and record the reason.

## Local configuration
Copy .env.example to .env when configuration loading is implemented. The example names describe the planned config contract; the diagnostic entry point does not consume them. Keep mock mode until a provider/model/budget is chosen. Never commit .env or keys. Do not put credentials in settings shown in screenshots.

## Git
If this is a new folder, initialize Git after checking no repository already exists. Review `.gitignore`, then stage intended files. Local commits are useful checkpoints; creating a remote or pushing is a separate user action. Do not commit saves, logs, caches, generated transcripts, .venv, or build outputs. No license grant is assumed for project distribution.

## Development workflow
```powershell
uv run python -m bar_cadenza
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
Pytest is meaningful only once tests have been added; an empty suite is not a passing game test. Run the built game with a working directory different from the repository during release verification.

## Windows checks
Test 100/125/150% DPI where available, resize/fullscreen if supported, Korean IME candidate positioning and Enter composition, audio device failure, Unicode save paths, and package startup without a development Python install. Build Windows executables on Windows.

## Packaging (selected in T005)
Tool: PyInstaller 6.22.3 (dev dependency, `pyinstaller>=6.16,<7` in pyproject.toml, locked in uv.lock). One-folder build, windowed (no console). pygame-ce ships its own PyInstaller hook for the SDL DLLs.
```powershell
uv sync --locked
uv run pyinstaller --noconfirm --clean tools/package_probe.spec
.\dist\BarCadenzaProbe\BarCadenzaProbe.exe --seconds 4
Get-Content "$env:LOCALAPPDATA\BarCadenza\package_probe.txt"
```
- Output: `dist/BarCadenzaProbe/` (≈39 MB; `build/` and `dist/` are gitignored). Ship the whole folder, not just the .exe.
- Resources: code finds bundled files with `bar_cadenza.app.paths.resource_root()` (the bundle's `_internal/` when frozen, else the repo root; never the cwd). Only folders listed in the spec's `datas` are bundled; add new asset/content folders there.
- User data: `bar_cadenza.app.paths.user_data_dir()` → `%LOCALAPPDATA%\BarCadenza` (via platformdirs).
- The probe is a feasibility build (the T003 text window), not the game. The final game spec replaces it in T046.
