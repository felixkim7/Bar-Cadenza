# Phased development plan

Goal: complete the game by the deadline, 2026-12-01 (D020). Go as far as possible in dependency order; do not reduce the plan. The sequence is based on dependencies and risk, not a fixed two-week estimate. Development is accelerated with Claude Code but still needs Windows and playtest evidence.

| Phase | Tasks | Outcome |
|---|---|---|
| P0: technical feasibility | T001–T005 | Environment, window, IME, background calls, packaging proven |
| P1: reusable foundation | T006–T009 | Scenes, independent states, layers, first visual integration |
| P2: offline playable visit | T010–T013 | Contracts, saves, fixtures, complete visit (M1) |
| P3: general bartending | T014–T020 | Shared preparation methods and recipe evaluation |
| P4: integrated conversation | T021–T023 | Continuous-time free typing, long/post-service visits (M2) |
| P5: AI and memory | T024–T028 | Provider, resilience, returning customer (M3) |
| P6: progression and economy | T029–T033 | Rapport, feedback, earnings, unlocks, shifts (M4) |
| P7: characters and later chat features | T034–T038 | Decided generation/portrait path, varied cast, suggestions |
| P8: content and production | T039–T042 | Expanded catalogue/cast (M5), approved art, sound |
| P9: polish and submission | T043–T046 | Balance, regression, tested Windows build (M6) |

## Working order
Default to the numbered sequence, one task at a time. Dependencies are explicit in docs/tasks/catalog.json. Some content/art/audio work can proceed earlier once prerequisites are done, but do not start a parallel agent workflow by default. If a user decision blocks T025, for example, finish unrelated eligible content or offline work without pretending the live checkpoint passed.

## Milestones
M1: a full offline visit in Korean and English. M2: flexible mixing plus continuous-time chat. M3: live conversation and remembered return with offline fallback. M4: several shifts with economy and unlocks. M5: agreed full content target and the selected generation strategy. M6: tested Windows submission with final art/audio and known limitations documented.

Tag or otherwise preserve verified milestones in Git when authorized. An unfinished later feature must not break the earlier playable path. Use small test content to validate mechanisms, then expand; never keep fixture counts as the full-game design by accident.

## Art/content parallel track
T009 approves one composite early. Once approved, asset preparation can progress while core systems are built. Final integration T041 checks consistency in the actual game. Data-source review can begin before T039, but unvalidated bulk content does not enter the production catalogue.

## Decision gates
T001 deadline/submission facts; T009 final asset conventions; T024 AI content policy; T025 provider/model/budget; T031 economy policy; T034 generated cast and world population; T035 portrait strategy; T039 data sources/history/counts. Gates do not require repeated permission for routine reversible engineering.
