# Asset production specification

## Visual gate before batch production
T009 assembles one scene, one patron, a bottle, jigger, shaker and dialogue/recipe panels at normal gameplay size. Confirm readability, hierarchy, perspective, contour weight and lighting before producing the catalogue. Baseline layout is 1280×720 logical pixels. Export sizes, scaling and DPI follow "Visual baseline" below (B012). The user approved the baseline, prop scale and light direction on 2026-11-28 (D024).

## Visual baseline (T009, B012; approved 2026-11-28, D024)

### Canvas and scaling
- Every scene draws on a 1280×720 logical canvas.
- The game is per-monitor DPI-aware. SDL scales the canvas once, fractionally and smoothly, to fill the window, with bars only on the axis whose ratio differs.
- The window opens at 80% of the desktop.
- The inverse pointer mapping was verified on real windows. Measured on a 2880×1800 display at 150%.
- **Limitation:** text and art are upscaled from the canvas, so they are soft rather than pixel-sharp at high DPI. Native-resolution rendering is the upgrade path (T043).

### Camera
- The view is the bartender's, across a two-tier bar. The user's counter art, 2026-11-27, set it.
- The guest stands behind the raised customer rail, whose top is at logical y 459.
- Tools stand on the lower work surface, y 513–584.
- The cabinets below, y 599–720, sit under the typing field.

### Layout
- **Guest:** in the middle; the art is placed bottom-centre at (640, 600), and the rail hides about the bottom 28%.
- **Conversation transcript:** left, (16, 44, 340×548).
- **Recipe card:** right, (924, 44, 340×352), on Champagne paper. Actions sit below it.
- **Typing field:** across the bottom, (16, 604, 1248×108).
- **Room:** drawn at about 78% brightness, so the guest and tools read first.
- **No overlap:** panels, buttons and the field never overlap a tool (tested).

### Export sizes
Supply each image at no less than 2× its logical display size; larger is fine. Keep the aspect within 1%, or the loader warns about stretching. The loader scales each image once, at load. The 2× source also serves later native-resolution rendering.

| Asset kind | Display (logical px) | Example export | Notes |
|---|---|---|---|
| Room background | 1280×720 | 2560×1440 | Opaque. |
| Counter | 1280 wide, height from the art | 2560 wide | Transparent above the rail. |
| Character | 400×500 | 800×1000 | Common canvas across all expressions. |
| Bottle | 70×210 | 140×420 or larger, 1:3 | |
| Shaker | 64×160 | 128×320 or larger, 2:5 | |
| Jigger | 38×70 | 6:11 | |

### Anchors
- **Room:** top-left (0, 0).
- **Counter:** bottom-centre at (640, 720).
- **Characters:** bottom-centre. Keep the waist line consistent across expressions.
- **Props:** bottom-centre on the base contact point, so bases rest on the work surface at y ≈ 574–580. If an export has empty space below the base, the manifest anchor's y fraction points at the base instead (the shaker uses 0.936).
- **Hit regions:** measured from the visible art, not the whole image box, so empty margins never catch the pointer.

### Prop scale
Props share about 7 logical px per cm, so a bottle, shaker and jigger agree with each other (approved, D024).

### Light direction (D024)
All new art follows this. The current images are temporary drafts and are not relit; the patron in particular stays as it is until the user supplies new art.

- **Key:** a warm amber key from above and slightly in front, from pendant lamps over the bar. Heads, shoulders, bottle shoulders and the bar top catch it, and shadows fall straight down.
- **Rim:** a restrained amber rim from the wall sconces behind the guest, on both edges.
- **Fill:** cool navy only from the windows in the room.
- **Props:** take the key highlight on top and the near (viewer-facing) side.

### Code-drawn states (not assets)
- The hover and selection outline in Whiskey Sour, with the tool name.
- The held-shaker hop, until a `shaker_active` sprite exists.
- The missing-asset placeholder.

## Naming and manifest
Use stable IDs and paths such as character_violinist_neutral, prop_jigger_idle and bg_bar_midground. Manifest records: asset_id, relative file, kind, canvas dimensions, display dimensions, anchor, draw layer, optional pivot/hit region, state/expression, source/license and approval status. Avoid localized words in filenames.

## Layers
Separate distant room, midground architecture, customer, counter/occluders, manipulable props, effects, and UI. The exact draw ordering depends on the camera; test hands and glasses behind/in front of the counter. Background shelf bottles may be painted decoration; usable bottles must be separate sprites. Never make a background object clickable merely because it resembles a bottle.

## Export rules
PNG RGBA for sprites needing transparency; avoid matte fringes. Keep common canvas/anchor across a character's expressions. Maintain source files separately from export assets, with provenance. Background format can be optimized after visual comparison; no automatic lossy conversion of small text/tool states. UI text remains rendered and localizable.

## Character set baseline
Neutral, speaking, listening/thoughtful, pleased, concerned and disappointed expressions are proposed starting coverage, not six required personalities. Use pose changes selectively. Blink/mouth overlays or small frame sequences are optional; do not require skeletal animation. Check hand position and counter alignment. Generated art needs the same review as authored art.

## Props
Bottle selection/highlight, measuring level, pour stream, shaker idle/active, spoon rotation, vessel liquid/ice state, glass and garnish states. Hit regions may be slightly larger than visual silhouette for usability but must not overlap ambiguously. Material read comes from few deliberate highlights, not photorealistic reflections.

## Selective animation
Allow subtle lamp/rain effects, blink, breathing or small gestures only if they preserve focus and performance. Cache loaded/scaled assets; no disk read or image generation per frame. Reduce ambient motion via settings when implemented.

## Approval checklist
Readable at normal scale; palette roles respected; same contour family; coherent perspective; matching light direction; clean transparency; correct anchor; working interaction state; no UI or localized text baked into sprites (bottle labels and brands are fine, D026); documented source/license (ChatGPT unless the user says otherwise, D025). Do not claim production approval because an image looks attractive in isolation.
