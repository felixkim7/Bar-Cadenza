# Implementation task index

All tasks start not_started. Follow dependency order; document any safe deferral. Checkpoint readiness requires actual evidence, not a checked box alone.

| Task | Phase | Title | Dependencies | Status |
|---|---|---|---|---|
| [T001](T001.md) | P0 | Windows environment and dependency lock | — | done |
| [T002](T002.md) | P0 | Window and frame-loop experiment | T001 | done |
| [T003](T003.md) | P0 | Bilingual text and Korean IME experiment | T002 | done |
| [T004](T004.md) | P0 | Background job and latency experiment | T002 | done |
| [T005](T005.md) | P0 | Windows packaging experiment | T002 | done |
| [T006](T006.md) | P1 | Application shell and scene routing | T003, T004, T005 | done |
| [T007](T007.md) | P1 | Input routing and independent state model | T006 | done |
| [T008](T008.md) | P1 | Asset loader and layered scene manifest | T006 | done |
| [T009](T009.md) | P1 | Visual integration gate | T007, T008 | done |
| [T010](T010.md) | P2 | Typed content and gameplay contracts | T007 | done |
| [T011](T011.md) | P2 | Save schema and repository foundation | T010 | in_progress |
| [T012](T012.md) | P2 | Representative catalogue and offline guest | T010 | not_started |
| [T013](T013.md) | P2 | Complete offline visit checkpoint | T006, T008, T011, T012 | not_started |
| [T014](T014.md) | P3 | Measured pouring and vessel transfer | T013 | not_started |
| [T015](T015.md) | P3 | Shaking interaction | T014 | not_started |
| [T016](T016.md) | P3 | Stirring interaction | T014 | not_started |
| [T017](T017.md) | P3 | Ice, strain, glass and garnish | T015, T016 | not_started |
| [T018](T018.md) | P3 | Bilingual searchable recipe book | T012, T017 | not_started |
| [T019](T019.md) | P3 | Deterministic craft and taste-fit evaluation | T017, T018 | not_started |
| [T020](T020.md) | P3 | Discard, remake and drink-state recovery | T019 | not_started |
| [T021](T021.md) | P4 | Continuous-time chat during busy actions | T020, T003 | not_started |
| [T022](T022.md) | P4 | Long visits and conversation after serving | T021 | not_started |
| [T023](T023.md) | P4 | Complete localization and journal UI | T022, T011 | not_started |
| [T024](T024.md) | P5 | AI interface, context assembly and prompt contracts | T023, T004 | not_started |
| [T025](T025.md) | P5 | Initial live provider integration | T024 | not_started |
| [T026](T026.md) | P5 | AI failures, usage limits and offline recovery | T025 | not_started |
| [T027](T027.md) | P5 | Evidenced memory and conversation summaries | T026, T011 | not_started |
| [T028](T028.md) | P5 | Returning customer encounter | T027 | not_started |
| [T029](T029.md) | P6 | Rapport evaluator and calibration fixtures | T028 | not_started |
| [T030](T030.md) | P6 | Visit feedback and idempotent results | T029, T019 | not_started |
| [T031](T031.md) | P6 | Inventory and economy ledger | T030 | not_started |
| [T032](T032.md) | P6 | Level and relationship progression | T031 | not_started |
| [T033](T033.md) | P6 | Complete multi-shift game loop | T032 | not_started |
| [T034](T034.md) | P7 | Character creation policy and profile generator | T033 | not_started |
| [T035](T035.md) | P7 | Portrait strategy and asset compatibility | T034, T009 | not_started |
| [T036](T036.md) | P7 | Background guest preparation and scheduling | T035 | not_started |
| [T037](T037.md) | P7 | Story variety and relationship pacing | T036 | not_started |
| [T038](T038.md) | P7 | Optional suggested replies | T037 | not_started |
| [T039](T039.md) | P8 | Catalogue import and validation pipeline | T033, T012 | not_started |
| [T040](T040.md) | P8 | Broad catalogue and content integration | T039, T037 | not_started |
| [T041](T041.md) | P8 | Production art and expression integration | T009, T035, T040 | not_started |
| [T042](T042.md) | P8 | Sound and music integration | T033 | not_started |
| [T043](T043.md) | P9 | Settings, readability and interaction polish | T041, T042, T038 | not_started |
| [T044](T044.md) | P9 | Playtest and balance full game | T043, T040 | not_started |
| [T045](T045.md) | P9 | Save migration and failure regression | T044 | not_started |
| [T046](T046.md) | P9 | Windows release and submission checkpoint | T045, T005 | not_started |
