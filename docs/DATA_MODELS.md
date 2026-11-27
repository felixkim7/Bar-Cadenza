# Data models and contracts

All schemas below are design contracts to implement and version in T010/T011. Example JSON under content/examples is illustrative, not a production catalogue. Validate IDs, references, enum values, bounds and unknown fields before using external data.

Implemented in T010:
- **`domain/catalogue.py`:**
  - authored records: IngredientDefinition, GlassDefinition, RecipeDefinition and CharacterProfile;
  - the versioned content-file shape;
  - the supported Method/Technique sets and the Flavor vocabulary;
  - `build_catalogue`, which checks references across files.
- **`domain/encounter.py`:**
  - Order and PreparationEvent;
  - PreparedDrink, which is `encounter.Drink`: its state plus observed events.

## Common rules
Use stable ASCII snake_case IDs. Display strings never act as primary keys. Use locale keys `ko` and `en`. Store time durations in milliseconds. Store money as integer minor units after currency O009 is decided. Use nonnegative integer microliters for measured liquid quantities (1 ml = 1,000 µl), rendering ml to the player; continuous pours accumulate subunit remainder rather than losing it each frame. ABV is a fraction in [0,1]. Keep authored targets separate from observed actions.

## Core records
| Record | Fields and invariant |
|---|---|
| IngredientDefinition | ingredient_id, localized name, category, abv_fraction, flavor_tags, asset_id, provenance; no gameplay state |
| GlassDefinition | glass_id, localized name, capacity_ul, asset_id, provenance; a recipe's volume must fit its glass |
| RecipeDefinition | recipe_id, localized name, ingredient quantities, steps, method, glass_id, ice/garnish, unlock requirements, variant_of (the house recipe it varies)/source; every reference resolves |
| Order | order_id, encounter_id, named/recommendation, recipe_id if named, revealed preferences, explicit adjustments; unavailable orders rejected or negotiated |
| PreparedDrink | drink_id, ingredient additions, vessel_id, action events, ice, dilution estimate, garnish, served_at; append observations, never copy recipe targets as actuals |
| PreparationEvent | event_id, action_type, start/end times, observed amount/rotation/intensity metrics; no negative durations or quantities |
| CharacterProfile | character_id, localized display name, adult age, appearance, personality, voice, stable facts, private facts, tastes, portrait references, provenance |
| CharacterState | save_id, character_id, current situation, relationship, recent events, revealed facts, visit count |
| Encounter | encounter_id, save_id, character_id, order_ids, drink_ids, dialogue state, arrival/departure and outcome |
| DialogueTurn | turn_id, encounter_id, role, text, locale, revision, timestamps; keep raw user text separate from instructions |
| MemoryFact | fact_id, subject_id, text, source_turn_ids, visibility, confidence/status; only evidenced facts enter confirmed memory |
| Evaluation | evaluation_id, encounter_id, drink components, rapport, evidence turn/event IDs, rubric_version, provisional/final status |
| Progress | save_id, XP, level, unlocked IDs, stock, money ledger, relationship references |
| SaveMetadata | save_id, selected_language, schema_version, content_version, timestamps |

## AI request envelope
`request_id`, `encounter_id`, `conversation_revision`, `kind`, `language`, `context`, `output_contract_version`. Context includes stable identity, private facts as private, known/revealed facts, relevant memory, recent turns, and a bounded game snapshot. Server/provider errors never masquerade as dialogue text.

## Dialogue response contract
`utterance` (nonempty bounded text), `expression_id` (allowlisted), `intent` (chat/order/finish_visit), `order_proposal` (nullable), `new_revelations` (bounded suggestions). Strictly reject unknown expression/action IDs and fabricated recipe IDs. Revealing an existing private fact is allowed; changing identity is not. Application rules decide whether to close the visit or accept an order.

## Evaluation response contract
Rapport dimensions, bounded scores, evidence turn IDs, and explanation in selected language. No money/XP fields. If evidence is missing or evaluator fails, mark assessment pending or unavailable and use documented fallback; do not silently manufacture a precise score.

## Database proposal
Tables: saves, character_profiles, character_states, encounters, dialogue_turns, memory_facts, prepared_drinks, evaluations, progression, inventory, ledger_entries, schema_migrations. Use foreign keys and transactions. Profile snapshots must stay available for saved visits even if authored content changes. Store structured event payloads as versioned JSON where useful; avoid dozens of tables for transient animation state.

## Save boundaries
Save at shift boundaries and safe encounter checkpoints. Do not serialize threads, sockets, pending futures or API keys. Persist an interrupted request marker and restart safely without double charging game currency or replaying actions. Completing a visit and paying rewards must be one atomic, idempotent transaction keyed by encounter_id.

## Catalogue import
Normalize units, retain source/variant, validate duplicates, missing ingredients and supported methods. Emit an import report; no silent acceptance of broken rows. Keep the input source outside production content until reviewed. One supported recipe can have multiple authored variants; choose the house version explicitly.
