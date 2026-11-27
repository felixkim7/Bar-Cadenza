# catalog

The game's authored catalogue: ingredients, glassware and recipes. Every `*.json` file here (and in content/characters) is loaded and validated at startup by `app.main.load_catalogue`. A new file is picked up without code or screen changes. Invalid content stops startup with a message naming the file, record and field.

T012 provides a small representative fixture set: 19 ingredients, 3 glasses, and 9 recipes covering shake, stir and build, plus one variant. These counts are fixtures, not final limits (D014). Recipes are provisional house specs. Only drinks and brands commonly dated before 1935 are used, so the set fits either history policy while O004 is open. Each record states its provenance.
