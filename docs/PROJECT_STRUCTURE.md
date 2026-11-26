# Project structure and technical baseline

| Path | Role |
|---|---|
| CLAUDE.md | Always-read concise project contract |
| .claude/rules/ | Scoped instructions, no custom plugins required |
| docs/ | Authoritative human-readable specifications |
| docs/tasks/ | Individual implementation tasks |
| src/bar_cadenza/app/ | Entry wiring, config and loop |
| src/bar_cadenza/scenes/ | Scene controllers |
| src/bar_cadenza/ui/ | Reusable GUI components |
| src/bar_cadenza/domain/ | Pure records and rules |
| src/bar_cadenza/systems/ | Gameplay coordination |
| src/bar_cadenza/ai/ | Provider adapter and jobs |
| src/bar_cadenza/persistence/ | Saves, SQLite, migrations |
| content/examples/ | Illustrative data contracts; not production data |
| content/locales/ | ko/en UI strings, shared key set |
| content/catalog/ | Future validated authored catalogue |
| content/characters/ | Future approved character definitions |
| prompts/ | Provider-independent prompt specifications |
| assets/ | Runtime asset slots |
| references/art/ | Unmodified supplied reference images |
| tests/ | Pure-logic, integration and fixture tests as implemented |
| tools/ | Import/validation/build utilities |

Folders contain README markers where implementation is intentionally absent. Do not mistake these markers for completed components. Avoid creating a universal ECS, plugin platform, or generic workflow engine without a concrete need.

## Baseline stack
Python 3.14 (D019); pygame-ce for rendering/input/audio; Pydantic v2 for data boundaries; SQLite via the standard library; platformdirs for writable locations; python-dotenv for local development configuration; pytest and Ruff for quality checks. A provider SDK is added only after O002. pyproject.toml uses bounded dependency ranges; T001 generates uv.lock and verifies actual compatibility.

## Skills the developer will exercise
Event loops and delta-time simulation; state machines; coordinate transforms and hit-testing; text editing/IME; 2D asset composition; structured data validation; request concurrency and queues; prompt/context management; SQL transactions/migrations; test fixtures; Windows builds; iterative playtesting.

Separate reusable logic from presentation. Prefer clear Python classes/dataclasses and small functions over additional frameworks. UI toolkit choice may be made in T003 if it demonstrably improves IME and scrolling support.
