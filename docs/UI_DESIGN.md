# UI and interaction

## Scenes
Menu (new/continue/settings), new-game language selection, pre-shift preparation, bar encounter, shift results. Keep save/language selection explicit. No game play begins before selecting ko/en for a new save.

## Bar layout baseline
Customer in upper/middle focal region; work surface in lower area; recipe book side panel; conversation transcript/input in a dedicated area that does not cover active tools. This is a layout hypothesis, not a fixed artwork crop. Prototype with rectangles and representative sprites before final art.

## Input priorities
Text input owns typing shortcuts while focused. Pointer actions go to the topmost eligible control. A mouse release must finish/cancel its captured action even if the pointer leaves the original rectangle. A hands-busy action may block sending chat temporarily but must preserve typed text. Time continues in all these states.

## Feedback
Make selected ingredient, target vessel, current quantity, active technique and available actions clear. Disabled actions explain why. Distinguish an unavailable recipe from a poor taste match. AI pending indicator is unobtrusive; it does not obscure controls. Keep customer text in scrollback if the player is busy.

## Localized layout
Measure actual strings, wrap and scroll. Reserve room for both Korean and English. Do not shrink long text to unreadability. Window scaling uses logical coordinates with inverse pointer transforms; test letterboxing and DPI. Avoid color-only states; combine highlighting with labels/icons.

## Open items
Final camera, display dimensions, window/fullscreen settings, pause/focus policy, exact reply grace and score visualization are settled at their tasks. No auto-pause may be introduced by choosing a UI toolkit.
