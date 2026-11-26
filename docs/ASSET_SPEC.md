# Asset production specification

## Visual gate before batch production
T009 assembles one scene, one patron, a bottle, jigger, shaker and dialogue/recipe panels at normal gameplay size. Confirm readability, hierarchy, perspective, contour weight and lighting before producing the catalogue. Baseline layout is 1280×720 logical pixels; final export resolution and high-DPI strategy remain O007.

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
Readable at normal scale; palette roles respected; same contour family; coherent perspective; matching light direction; clean transparency; correct anchor; working interaction state; no text baked into sprite; documented source/license. Do not claim production approval because an image looks attractive in isolation.
