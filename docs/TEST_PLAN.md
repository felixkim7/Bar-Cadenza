# Verification plan

## Layers
| Layer | Verify | Method |
|---|---|---|
| Starter integrity | IDs, dependency graph/order, links, locale keys, example references | python tools/check_starter.py |
| Domain | quantities, tolerances, preferences, unlocks, state transitions | pytest pure functions/records |
| Integration | content load, save round-trip, worker results, idempotency | temporary SQLite and fake providers |
| UI | hit regions, scrolling, layout, text focus, state feedback | Windows manual and selective automation |
| AI | prompt/context quality, schema failures, locale, memory, rubric | fixed fixtures; optional live tests with budget |
| Release | executable, assets/fonts, writable paths, offline demo | clean Windows environment |

## Required regression cases
- Pouring and stirring at different frame rates yield equivalent measurements within documented tolerance.
- No negative stock/volume, duplicate ingredient IDs, or nonexistent referenced IDs accepted.
- Named order adjustment changes scoring target deliberately; recommendation has multiple valid answers.
- Typing and pending API jobs never freeze the simulation.
- Late or duplicate AI result cannot mutate another visit or pay twice.
- Hidden customer facts cannot create unexplained penalties.
- Respectful disagreement and busy-action delay do not automatically lower rapport.
- Korean IME Enter sends the full text including the composing syllable exactly once; Shift+Enter breaks lines; draft survives input-mode change.
- en/ko key sets match; long strings wrap and remain readable.
- Save persists language, relationships, unlocks and accepted generated character identity.
- Save migration preserves prior data; unsupported future schema refuses unsafe writes.
- Missing API key, timeout, invalid JSON, rate limit and budget limit each have a usable localized path.
- Offline demo completes without a key, credentials, or network.
- Public-release package scan contains no developer keys or personal transcripts.

## Evidence
Record exact command, environment, result, tested behavior and limits in each task. A screenshot is useful for visual work but does not prove all input states. A Linux dummy-video run does not prove Windows IME or packaged audio. Test only relevant changes; don't add tests that merely assert implementation details or empty scaffolds.

## Milestone gates
M1 offline visit; M2 flexible preparation/chat; M3 live customer with saved return; M4 multi-shift progression; M5 expanded content/approved generation; M6 polished submission. Each gate requires the named demo scenario plus regressions for affected systems.
