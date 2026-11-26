# Requirements and acceptance

All implementation requirements initially **not_verified**. R032/R033 include explicit decision gates; do not convert planned generation into a user commitment. Final quantities and numeric tuning are open.

| ID | Requirement | Acceptance | Implementing tasks | State |
|---|---|---|---|---|
| R001 | Windows application | Launch/quit cleanly on target Windows and report missing required resources. | T001, T002, T006, T046 | not_verified |
| R002 | Korean/English new game | Both choices create a save with persisted language; load restores it. | T003, T006, T011, T023 | not_verified |
| R003 | Free typing and IME | Korean composition, English editing and scrollback work; Enter sends the complete text (including a composing syllable) exactly once, Shift+Enter breaks lines (D021). | T003, T021, T023, T043 | not_verified |
| R004 | Continuous time | Reading, typing, busy actions and pending AI do not pause simulation. | T002, T007, T021 | not_verified |
| R005 | Independent encounter states | Dialogue continues during preparation and after serving until departure. | T007, T013, T021, T022 | not_verified |
| R006 | Data-driven catalogue | Recipes/ingredients load by IDs and validate without per-recipe screen code; no six-drink cap. | T010, T012, T039, T040 | not_verified |
| R007 | Named and recommended orders | Both modes respect available recipes and revealed preferences; invalid IDs are rejected. | T010, T012, T013, T019, T024, T040 | not_verified |
| R008 | Measured pouring | Actual quantity is recorded independently of target and consistently across frame rates. | T014, T020 | not_verified |
| R009 | Shaking | Track duration and intensity with clear start/end feedback and comparable results across frame rates. | T015 | not_verified |
| R010 | Stirring | Track rotations and duration, ignoring jitter/reverse artifacts according to documented rules. | T016 | not_verified |
| R011 | Finishing | Ice, straining, vessel, glass and garnish states affect allowed steps and evaluation. | T017, T020 | not_verified |
| R012 | Recipe book | Search/filter names, flavors and availability in both languages; explain locked recipes. | T018, T040 | not_verified |
| R013 | Drink results | Use actual actions and explicit order adjustments; offer specific preparation feedback. | T019, T020, T030, T044 | not_verified |
| R014 | Conversation results | Apply evidence-based rubric; no penalty merely for busy-action delay or respectful disagreement. | T029, T030, T044 | not_verified |
| R015 | Broad character system | More than three customers supported through content, each with identity/story/preferences. | T012, T028, T032, T034, T036, T037, T040 | not_verified |
| R016 | Variable stories | Short and long visits cover varied everyday themes, with natural closure and boundaries. | T022, T028, T034, T037, T044 | not_verified |
| R017 | Memory and return visits | Persist evidenced preferences/facts and resume a returning character consistently. | T027, T028, T037 | not_verified |
| R018 | One provider and extensibility | Mock and initial provider share an interface; changing provider does not change game rules. | T024, T025 | not_verified |
| R019 | Nonblocking AI | Window/actions remain responsive; stale/duplicate results cannot corrupt state. | T004, T024, T025, T026, T036, T045 | not_verified |
| R020 | Offline and failures | A complete localized offline demo runs without API key/network; recover from live failure. | T004, T013, T026, T045, T046 | not_verified |
| R021 | Progression unlocks | Level/technique/ingredient unlocks change makeable recipes and survive reload. | T032, T033, T044 | not_verified |
| R022 | Economy | Stock/cost/sales/tips are consistent and awarded once; figures are configurable. | T031, T033, T044 | not_verified |
| R023 | Multi-shift loop | Pre-shift, service, results, next shift and save/load form a playable loop. | T006, T013, T033, T046 | not_verified |
| R024 | Reliable saves | Atomic saves, schema versioning, migration and clear failure handling preserve progress. | T011, T027, T030, T031, T033, T045 | not_verified |
| R025 | Confirmed visual direction | Characters, props, backgrounds and UI match ART_DIRECTION at gameplay size. | T009, T035, T041 | not_verified |
| R026 | Layered readable assets | Manifest/anchors/layers/hit regions support movement, expressions and interaction. | T008, T009, T035, T041 | not_verified |
| R027 | Bilingual interface | All user-facing controls/errors and authored/live/offline dialogue follow save locale. | T003, T018, T023, T025, T038, T043, T046 | not_verified |
| R028 | Audio | Mixing feedback and room/music sound have independent volume control and device fallback. | T042 | not_verified |
| R029 | Settings/readability | Window scaling, text readability, keyboard focus and feedback work at tested Windows DPI. | T007, T009, T043 | not_verified |
| R030 | Credential/usage boundary | No keys in repository/build; bounded request usage with explicit budget before live calls. | T024, T025, T026, T045 | not_verified |
| R031 | Windows release | Build runs outside source cwd with resources and an offline demonstration. | T005, T046 | not_verified |
| R032 | Generated profiles — planned, decision-gated | If O005 accepted: validate, persist and schedule a new profile without blocking current play. | T034, T036 | not_verified |
| R033 | Portrait strategy — decision-gated | Select prepared/modular/runtime strategy; never require synchronous generation on arrival. | T035, T036 | not_verified |
| R034 | Suggested replies — later phase | Optional localized suggestions preserve free typing and remain player-editable/selectable. | T038 | not_verified |
| R035 | Content provenance | Import reports record sources/variants and reject invalid references; asset licenses tracked. | T008, T010, T012, T039, T040, T041, T042 | not_verified |
| R036 | Task-by-task development | Each completed task has acceptance evidence, status update and a reproducible checkpoint. | T001, T046 | not_verified |
