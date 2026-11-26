# Bar Cadenza — project instructions

Build the full Windows narrative bartending game in playable phases. This is a starter specification and scaffold, NOT an implemented game.

## Read at session start
1. docs/DECISIONS.md — confirmed, provisional, and open choices.
2. docs/STATUS.md and docs/tasks/INDEX.md — current work and next eligible task.
3. The selected task, its requirement IDs in docs/REQUIREMENTS.md, and relevant specifications.
Read only relevant detail documents; do not load the whole pack every turn.

## Non-negotiable product constraints
- Python + pygame-ce; Windows first. Other libraries are allowed.
- Full-game target, with independently playable submission checkpoints. Do not silently reduce final scope to six drinks or three customers.
- New game offers Korean/English; persist the selected language per save. All UI and runtime dialogue support it.
- Free typing is primary. Suggested replies come in a later phase.
- Time continues while chatting, reading, waiting for AI, and mixing. Busy actions may delay the player's response. No automatic pause on text focus.
- Conversations may continue during preparation and after serving.
- Score conversation as well as drinks; precise rubric and weights are provisional until calibrated.
- Follow docs/ART_DIRECTION.md: Western flat-color cartoon people/props, painted animation backgrounds, limited Art Deco influence. Oxblood/burgundy/navy/charcoal; emerald sparingly.
- 1920s–1930s speakeasy mood is confirmed. Strict historical accuracy is an open choice.

## Work procedure
- Implement one task at a time in dependency order. No independent agent delegation unless the user requests it.
- For a request covering multiple tasks, finish/verify/update each before moving to the next; do not require repeated approval for routine authorized steps.
- State the task ID, dependency readiness, and expected changed files before editing.
- Preserve user edits. Never overwrite working code just because a template differs.
- Keep game rules independent of Pygame and provider APIs. Game state is authoritative; AI responses are validated suggestions.
- Use mock AI by default; network calls do not belong in the frame loop.
- Do not embed credentials in source, assets, logs, saves, or builds.
- Small representative content sets are test fixtures, not final content limits.
- Ask only when a material open decision blocks the current task. Continue independent work where possible. Do not invent a deadline, provider, or spending authorization.
- Verify acceptance criteria; record evidence. Code generation alone does not complete a task.
- Update task Evidence, docs/tasks/INDEX.md, and docs/STATUS.md. Update requirements only when their complete acceptance criteria pass.
- Keep commits task-sized. Do not push, publish, or alter remote access unless authorized. Never fabricate a commit or test result.

## Commands
- Starter integrity (no third-party packages): python tools/check_starter.py
- Bootstrap diagnostic (not a game): python tools/starter_info.py
- Initial dependency resolution on target machine: uv lock; uv sync
- After locking: uv sync --locked
- Application entry: uv run python -m bar_cadenza (game shell since T006; --seconds S auto-quits)
- Tests after actual tests exist: uv run pytest
- Style checks: uv run ruff check .; uv run ruff format --check .

## Completion report
Report task ID, behavior changed, files, actual checks/results, remaining limitations, and next eligible task. Distinguish Windows manual checks from automated checks on another OS.
