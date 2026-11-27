# Project status

Updated: 2026-11-28

## Actual state
Windows dev environment locked and verified: Python 3.14.7 (D019), uv 0.13.10, uv.lock with 16 packages, pygame-ce 2.5.8. Entry point `uv run python -m bar_cadenza` launches the T006 game shell: bilingual main menu, explicit ko/en new-game choice, and placeholder pre-shift/bar/results loop. The placeholder bar is the T007 test bench: chat field, hold-to-stir tool, serve, separate encounter/drink/conversation/input states, and the D022 pause menu (Esc, focus loss or minimize). T008 asset loader (app/assets.py) reads assets/manifest.json and draws layered scenes with hit-testing and missing-asset placeholders. Its test window is `uv run python -m bar_cadenza.app.asset_experiment`. Since T009 the game's bar is drawn from the manifest's `bar` scene, using the user's temporary draft art (not for release). T002 window/frame-loop experiment exists (`uv run python -m bar_cadenza.app.window_experiment`), verified by automated real-window runs and the user's manual Windows check. T003 text/IME experiment exists (`uv run python -m bar_cadenza.ui.text_experiment`) with bundled Nanum Gothic font, verified with the user's real Korean IME (D021 Enter/Shift+Enter behavior). T004 background job runner exists (ai/jobs.py) with a fake-provider experiment (`uv run python -m bar_cadenza.ai.latency_experiment`), verified in real-window runs. T005 PyInstaller build (`uv run pyinstaller --noconfirm --clean tools/package_probe.spec`) runs from a copied folder with no Python on PATH, reads bundled resources and writes to %LOCALAPPDATA%/BarCadenza. No gameplay system is implemented. No real provider or model selected. No paid API usage. No audio test performed yet; no clean-machine package test yet (T046).

## Current task
T009 — Visual integration gate (branch `feat/t009-visual-gate`).
- **Done:**
  - the bar is composed from the manifest with conversation and recipe panels, using the user's draft art;
  - the window is DPI-aware with fractional fill scaling (B012);
  - the user approved the composition, readability, prop scale and light direction (D024).
- **Waiting for:** the user to re-check the Add ingredient button. It showed no feedback; that is fixed and verified in a real window.

## Blockers
No blocker to offline work. Deadline is 2026-12-01 (D020); submission requirements O001 still open; provider/model/budget O002 blocks paid live integration only. See DECISIONS.md for later gates.

## Last completed implementation task
T008 — Asset loader and layered scene manifest (2026-11-27; user manual check passed). Evidence in docs/tasks/T008.md.

## Handoff
- Current task/status: T001–T008 done. T009 in progress (waiting for the user's re-check of the Add button). Evidence is in T001.md–T009.md.
- What actually changed: T002 added app/clock.py, app/window_experiment.py, tests/test_clock.py. T003 added ui/text_input.py (TextField + wrapping), ui/text_experiment.py, Nanum Gothic font + OFL, tests/test_text_input.py. T004 added ai/jobs.py (JobRunner), ai/latency_experiment.py, tests/test_jobs.py. T005 added PyInstaller (dev), app/paths.py, app/package_probe.py, tools/package_probe.spec, tests/test_paths.py. T006 added app/main.py (startup checks, loop, routing), scenes/shell.py, ui/buttons.py, ui/palette.py, domain/session.py and tests/test_app_shell.py. T007 added domain/encounter.py (separate state tracks), ui/input_router.py, the bar test bench and pause menu (D022), tests/test_encounter.py and tests/test_input_routing.py. T008 added app/assets.py (manifest, AssetStore), app/asset_experiment.py, assets/manifest.json and tests/test_assets.py. Details in T002.md–T008.md.
- Commands and results: pytest 71 passed at T008, 53 at T007, 24 at T005; T008 real-window pointer mapping 6/6 (includes replay of the user's real IME log; job tests repeated 10× with 0 failures); T004 45 s real-window run: max frame 18.5 ms, all paths incl. 3 timeouts, clean shutdown 0.8 ms; T005 built exe exits 0 from a copied folder with stripped PATH; T003 real-window screenshot reviewed; ruff clean; real-window runs at 30/60/uncapped fps and a 6 s stress run all exit 0, sim time tracks real time, max frame ≤ 35 ms at 30 fps.
- Manual Windows checks: T002 user check passed (maximize, sustained input, close); window drag freezes the loop (SDL2 on Windows). T003 real Korean IME check passed in two rounds (second after D021). T006 and T007 user checks passed: shell loop in both languages, IME typing while stirring, release outside the tool, pause on alt-tab, minimize and Esc, window drag, Tab/keyboard buttons. T008 user check passed: layered test art, and hover/click outlines under the cursor in a maximized window.
- Known defects/remaining evidence:
  - SCALED enforces a 1280×720 minimum window size (revisit at T043).
  - A window drag or resize adds no game time, and focus loss or minimize pauses (D022). Holding the title bar still without moving can still lose up to 1 s.
  - Since T009 the game is DPI-aware and fills the window with one smooth resample (B012). Text and art are still upscaled from the 1280×720 canvas, so they look soft at high DPI. Native-resolution rendering is the T043 option.
- Decisions needed: O001 submission requirements (not blocking until T046). O008 settled as D022 (2026-11-26).
- Next eligible task: finish T009 (Add re-check), then T010 typed contracts.
- Git checkpoint (only if actually created): T006 merged to main as 0f676a9, T007 as d13219d, T008 as 863da37. T009 is uncommitted on `feat/t009-visual-gate`.
