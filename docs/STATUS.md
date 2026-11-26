# Project status

Updated: 2026-11-26

## Actual state
Windows dev environment locked and verified: Python 3.14.7 (D019), uv 0.13.10, uv.lock with 16 packages, pygame-ce 2.5.8. Entry point is still the scaffold diagnostic. T002 window/frame-loop experiment exists (`uv run python -m bar_cadenza.app.window_experiment`), verified by automated real-window runs and the user's manual Windows check. T003 text/IME experiment exists (`uv run python -m bar_cadenza.ui.text_experiment`) with bundled Nanum Gothic font, verified with the user's real Korean IME (D021 Enter/Shift+Enter behavior). No gameplay system is implemented. No real provider or model selected. No paid API usage. No audio/package test performed yet.

## Current task
None in progress. Next: T004 — Background job and latency experiment.

## Blockers
No blocker to offline work. Deadline is 2026-12-01 (D020); submission requirements O001 still open; provider/model/budget O002 blocks paid live integration only. See DECISIONS.md for later gates.

## Last completed implementation task
T003 — Bilingual text and Korean IME experiment (2026-11-26). Evidence in docs/tasks/T003.md.

## Handoff
- Current task/status: T001, T002 and T003 done.
- What actually changed: T002 added app/clock.py, app/window_experiment.py, tests/test_clock.py. T003 added ui/text_input.py (TextField + wrapping), ui/text_experiment.py, Nanum Gothic font + OFL, tests/test_text_input.py. Details in T002.md/T003.md.
- Commands and results: pytest 13 passed (includes replay of the user's real IME log); T003 real-window screenshot reviewed; ruff clean; real-window runs at 30/60/uncapped fps and a 6 s stress run all exit 0, sim time tracks real time, max frame ≤ 35 ms at 30 fps.
- Manual Windows checks: T002 user check passed (maximize, sustained input, close); window drag freezes the loop (SDL2 on Windows). T003 real Korean IME check passed in two rounds (second after D021).
- Known defects/remaining evidence: SCALED enforces a 1280×720 minimum window size (revisit T009/T043). Window-drag stall > 1 s drops sim time (decide under O008 at T007).
- Decisions needed: O001 submission requirements (not blocking until T046). O008 focus/suspend policy at T007.
- Next eligible task: T004 (T005 also eligible).
- Git checkpoint (only if actually created): none.
