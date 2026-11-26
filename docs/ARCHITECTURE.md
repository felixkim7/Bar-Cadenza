# Architecture

## Modules and ownership
| Module | Owns | Must not own |
|---|---|---|
| app | startup, configuration, main loop, scene router, services | recipes or provider-specific dialogue logic |
| scenes | menu, pre-shift, bar, results composition | scoring formulas or persistence SQL |
| ui | input fields, chat, buttons, layout, recipe book views | authoritative money/state changes |
| domain | typed records, invariants, commands/events | pygame imports, network or filesystem I/O |
| systems | simulation, encounters, evaluation orchestration, progression | direct provider SDK calls in update/render |
| ai | provider interface, background jobs, validation adapters, offline implementation | direct mutations of world state |
| persistence | database transactions, migrations, saves, repositories | rendering |
| content | authored definitions and import provenance | mutable save progress |
| assets | runtime-ready visual/audio/font files | secret configuration |

## Main loop
Poll input → route intent to UI/controller → advance simulation using elapsed time → drain completed jobs within a bounded frame budget → validate/apply domain commands → render → cap frame rate. Main thread owns display, event handling, active state, and sprite mutation. Network worker returns plain validated data; it does not draw.

Separate real monotonic elapsed time, simulation time, action elapsed time, and conversation metrics. Clamp/handle extreme frame gaps consistently; pause, focus loss, minimize and window-drag stalls follow D022. Never substitute frame count for elapsed time. Text entry does not alter simulation speed.

## Independent states
- Encounter: arriving / ordering / visiting / departing / closed.
- Drink: empty / assembling / mixing / ready / served / discarded.
- Conversation: idle / awaiting_player / request_pending / response_available / closed.
- Input context: gameplay / text_entry / hands_busy / modal.

Do not encode these into one giant enum. A served drink can coexist with awaiting_player. A pending AI request can coexist with stirring. Command handlers validate allowed transitions. Each visit has a unique encounter_id; closing it invalidates late callbacks.

## Background jobs
A bounded worker pool and result queue are enough initially. Jobs carry request_id, encounter_id, conversation_revision, request_kind, and cancellation state. One in-flight dialogue turn per encounter. UI may accumulate text without sending duplicate turns. Apply each successful result once; discard stale/out-of-order results. Retry only under bounded policy; never allow a retry to repeat a served drink or wallet transaction.

## Content and state
Authored JSON is read-only at runtime. Stable IDs reference ingredients, recipes, characters, assets and localization keys. SQLite stores save-specific state with schema_version and content_version. Assets resolve relative to package/build resources, not current working directory. User data resolves to a per-user writable directory via platformdirs.

## Dependency direction
Views issue commands to systems; systems use domain records and interfaces; adapters implement persistence and AI services. Pure recipe, scoring, unlock, and amount calculations remain testable without an open window.

## Future deployment seam
Keep an AIProvider interface from the first mock. Later, a server-backed adapter may protect developer-owned API keys and enforce usage policies. Do not build an account service now. Never ship a developer key in an executable; future public release requires an explicit credential/service design.

## Failure behavior
Bad authored content: validation error naming record/path before starting a shift. Missing noncritical artwork: visible placeholder plus diagnostic, not a crash. Missing required font/localization: clear startup report. AI failure: retry option or localized offline continuation. Save failure: retain current state and report failure; do not claim saved. Unsupported future save schema: refuse unsafe downgrade.
