# Example records

These records demonstrate field names and units. They are not final cast canon, approved recipes or production assets. Every file uses the T010 content-file shape: `schema_version`, `example_only`, and any of the lists `ingredients`, `glasses`, `recipes` and `characters`. `bar_cadenza.domain.catalogue.build_catalogue` validates them, but only with `allow_examples=True`. Files marked `example_only` are refused as game content. T012 creates reviewed working fixtures.

Ingredients, glasses and recipes use integer microliters. Asset IDs are planned identifiers without runtime images. Methods and techniques are the validated sets in `domain/catalogue.py`; T017 may extend them. Character private facts must not appear in the player journal or unexplained score deductions.
