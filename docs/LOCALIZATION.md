# Korean and English

Confirmed: choose Korean or English when creating a new game. Persist `selected_language` per save. Loading resumes that language. Whether settings can change an existing save's language is open; do not translate saved transcript history automatically.

## Text sources
- UI: stable keys in content/locales/en.json and ko.json. Both files must have identical keys.
- Authored content: localized names/descriptions or localization keys.
- AI dialogue: request selected locale directly; validate obvious locale failures and retry/fallback under policy.
- Memory: stable facts independent of display strings; summaries retain their locale or are explicitly translated when required.
- Logs: stable event codes; user-facing errors localized.

## Input
Use TEXTEDITING for the composition preview and TEXTINPUT for committed text. Handle cursor movement, selection if supported, deletion, multiline wrapping, clipboard and scrollback. Enter sends at once, including a syllable still being composed, and Shift+Enter inserts a line break (D021); the sent text must include the composed syllable exactly once. Validate that behavior on a real Korean Windows IME, not only simulated events.

Disable gameplay shortcuts while editing text; do not disable the simulation clock. Busy action state may temporarily disable reply submission, preserving the draft and composition safely. Reset text-input state on scene change without losing an already committed draft unintentionally.

## Fonts and layout
Bundle a redistributable font covering Hangul and Latin after license review; keep the license. Do not rely solely on one installed system font. Measure rendered text, wrap, scroll and clip at tested DPI/window sizes. English and Korean have different line-break needs. Dialogue panels must support long replies without hiding actions. No UI text baked into scenery or tool sprites.

## Manual acceptance
New game in each language; save/load; Korean composition/backspace/Enter; mixed Latin/Korean cocktail names; long paragraphs; resize/DPI scaling; text focus while a timer continues; input draft survives a busy step; selected language persists in offline and live responses.
