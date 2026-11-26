# Decision register

Status vocabulary: **confirmed** = user decision; **baseline** = reversible implementation proposal; **open** = not selected. Baselines may be refined with evidence; never silently override a confirmed choice.

## Confirmed
| ID | Decision |
|---|---|
| D001 | pygame-ce and other libraries are allowed. |
| D002 | Aim for the full game within the existing deadline; preserve playable phase checkpoints for submission if incomplete. |
| D003 | Windows is the first target. |
| D004 | Korean and English options; language chosen when a new game starts. |
| D005 | Primarily free typing; suggested replies later. |
| D006 | Time does not pause during chatting or busy preparation. Player can answer afterward. |
| D007 | Start with one AI provider and allow later expansion. |
| D008 | Personal/course demo first; leave architectural room for broader audiences and Steam. |
| D009 | Characters: flat-color Western cartoon, recognizable adults, varied silhouettes and expression. |
| D010 | Props: matching flat-color illustration; legible silhouettes/materials. |
| D011 | Background: classic 2D animation painting with limited Art Deco editorial influence. |
| D012 | Oxblood, burgundy, navy, charcoal; aged brass/amber accents; emerald sparingly. |
| D013 | 1920s–1930s speakeasy atmosphere; layered raster assets. |
| D014 | Vast recipe/ingredient collection rather than a six-drink cap. |
| D015 | More than three characters; each has a story; conversation is a major activity. |
| D016 | Short and long conversations, including during mixing and after service. |
| D017 | Chat behavior affects the result alongside the drink. |
| D018 | Levels unlock drink possibilities, ingredients, richer encounters, and earning potential. |
| D019 | Python 3.14 instead of the 3.12 baseline (user decision 2026-11-26; 3.14 is installed locally, 3.12 is not). |
| D020 | Deadline 2026-12-01. Go as far as possible in dependency order; do not reduce the dev plan or scope (user decision 2026-11-26). |
| D021 | Chat input: Enter sends at once, including a syllable still being composed; Shift+Enter inserts a line break; held Backspace/Delete/arrows repeat; no composition underline. Supersedes 'composition Enter must not submit' (user decision 2026-11-26, after the T003 IME test). |
| D022 | Game time measures physical actions (pour duration, shake/stir duration and intensity, ice/dilution) and lets bartending and conversation run at once; it is not a countdown on the whole evening (user statement 2026-11-26). Resulting O008 policy: typing, reading, recipe browsing, busy actions and pending AI never pause time; Esc opens a pause menu (Resume / Main menu) that stops time; losing window focus or minimizing opens the same menu and ends any held action; a window drag/resize stall adds no time; other gaps stay capped at 1 s. |

## Engineering baselines
| ID | Baseline | Revisit when |
|---|---|---|
| B001 | Python 3.14 (D019), uv, Pydantic, SQLite, pytest, Ruff | Compatibility experiment shows a concrete issue |
| B002 | One desktop process; network worker + bounded queue; main thread owns UI/state | Distribution requires a server |
| B003 | Authored JSON catalogue, SQLite runtime saves, stable IDs | Import scale justifies a different storage layer |
| B004 | One foreground customer at a time; background ambience only | User requests simultaneous service |
| B005 | Regulars plus expandable newcomers; generated text profiles as a planned later module | Cast policy finalized |
| B006 | Separate craft, preference-fit, and rapport results | Playtesting/calibration |
| B007 | 1280×720 logical layout, scalable window; final raster export sizes decided at visual gate | T009 visual test |
| B008 | Persist language per save; do not translate past transcripts on load | User chooses mid-save language switching |
| B009 | Busy-action-aware reply grace; no automatic pause; network delay never directly penalizes rapport | Timing playtest |
| B010 | Main-menu and explicit pause behavior left separate from the no-chat-pause rule; pause policy settled in D022 (T007) | Playtest shows the pause menu or focus pause misfires |
| B011 | PyInstaller one-folder windowed build; resources via app/paths.resource_root (bundle or repo root, never cwd); user data in %LOCALAPPDATA%/BarCadenza via platformdirs (T005) | A Windows build or distribution issue appears |

## Open decisions and latest responsible task
| ID | Decision | Needed by | Default approach until answered |
|---|---|---|---|
| O001 | Submission requirements (deliverable format); deadline is confirmed in D020 | T046 | Ask before T046; keep dependency order |
| O002 | First AI provider, model, key ownership and spending cap | T004 live branch / T025 | Mock provider; zero paid calls |
| O003 | Final catalogue source and target size | T039 | Curated fixtures and importer contract |
| O004 | Strict history vs period-inspired fiction; treatment of later cocktails/topics | T012 / T039 | Label examples provisional; avoid modern brands/technology in stories |
| O005 | Authored/generated cast balance and whether runtime story generation is mandatory for submission | T034 | Plan generation module without counting it as confirmed scope |
| O006 | Runtime image generation vs prepared/modular portraits | T035 | Prepared placeholder portrait pool |
| O007 | Final base resolution, asset sizes, and additional exact palette values | T009 | B007 and named palette roles; no invented approved colors |
| O009 | Currency/world location, progression thresholds, and score weights | T031 | Configurable illustrative values clearly labeled |
| O010 | Human-only or mixed species cast | T034 | Human fixtures only; no anthropomorphic cast assumed approved |
| O011 | Content boundaries and intended rating | T024 / T034 | Adult patrons and everyday issues; sensitive themes reviewed explicitly |
| O012 | Voice, multiple simultaneous guests, alternative controls | Future expansion | Out of initial committed implementation |

Do not turn every open decision into an upfront blocker. Ask at its dependency boundary; preserve work that can proceed. New user decisions supersede older proposals. Update this register and affected docs/tasks together.
