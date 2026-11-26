# Bar Cadenza — Claude Code Starter

Version 1.0 / 2026-11-26. A development handoff for the complete narrative bartending game, with staged playable milestones.

**This pack contains instructions, specifications, tasks, references, and a minimal Python package scaffold. It does not contain a playable game or finished production assets.** No implementation task is marked done.

## Start here
1. Extract this whole folder, including `.claude/`, to a new local Windows project folder (for example `C:\Projects\BarCadenza`).
2. Read [START_HERE.md](START_HERE.md).
3. Open the folder in VS Code and start Claude Code from this project root.
4. Paste the first-session prompt from [docs/CLAUDE_WORKFLOW.md](docs/CLAUDE_WORKFLOW.md).
5. Begin T001; follow [the task index](docs/tasks/INDEX.md).

## What is included
- `CLAUDE.md` and focused `.claude/rules/` instructions.
- Game design, requirements, architecture, data models, AI, localization, scoring, economy, art and asset specifications.
- Task files with dependencies, checks, and evidence fields; a machine-readable task catalogue and a readable index.
- Three supplied visual references, copied without image modification and clearly marked reference-only.
- Python project configuration and a diagnostic entry point. Dependency resolution belongs to T001; no fabricated lockfile is included.
- A standard-library pack checker for task links, dependency order, requirement coverage, example records, and localized string keys.

## Confirmed direction
Windows; pygame-ce; Korean/English chosen for a new game; free typing; continuous time; a large data-driven cocktail catalogue; a broad cast; conversations before/during/after preparation; conversation-sensitive results; progression and unlocks; one AI provider initially; personal/course use first.

## What remains open
Submission requirements (deadline is 2026-12-01, D020), first AI provider/model/budget, final content counts, historical accuracy policy, detailed score/economy tuning, runtime portrait generation commitment, and final asset dimensions/colors. See [DECISIONS.md](docs/DECISIONS.md). These do not block offline foundational work.

## Map
| Area | Location |
|---|---|
| Product and implementation documents | `docs/` |
| Ordered tasks | `docs/tasks/` |
| Game source scaffold | `src/bar_cadenza/` |
| Authored content and example contracts | `content/` |
| AI prompt specifications | `prompts/` |
| Production-asset slots | `assets/` |
| Supplied reference images | `references/art/` |
| Validation and development utilities | `tools/` |
| Future meaningful tests | `tests/` |

## Validation boundary
See `PACK_VALIDATION.md` for checks performed on this starter. The included checker verifies handoff integrity, not game correctness. Windows GUI, IME, audio, real APIs, and packaging must be verified during development.
