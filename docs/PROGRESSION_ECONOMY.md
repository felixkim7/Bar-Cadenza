# Progression and economy

Confirmed: levels expand drink possibilities, ingredients, conversation opportunities, and earning potential. Exact level counts, thresholds, currency, prices, and final content counts are open.

## Three tracks (baseline)
1. Bartender experience: techniques and increasingly complex orders.
2. Bar development: inventory, equipment, menu variety and earning opportunities.
3. Individual relationships: remembered preferences, new story stages and trust.

Long conversations depend on encounter design and relationship readiness, not a forced minimum word count. Short visits remain available at high levels. A customer does not reveal something personal simply because the global level increased.

## Unlock semantics
A drink is makeable only when recipe/technique requirements, required tools and stock are satisfied. Unlocking one ingredient can enable many recipes. UI explains why an option is unavailable. Keep unlock definitions in data, validate missing/cyclic prerequisite IDs, and test boundaries.

## Stock and money
Use one ledger for purchases/sales/tips/refunds; record idempotency keys. Choose whether stock is measured consumables or simplified availability in O009 before final economy implementation. Until then, fixtures explicitly label the simplification. Discards/remakes cost stock consistently. Net earnings distinguish revenue from ingredient costs. Never equate more serious disclosures with larger tips.

## Illustrative stages
Opening nights → wider basic techniques → neighborhood reputation → advanced menu and deeper returning stories. These are design labels, not approved numeric levels. Tune progression after repeated full-shift playtests. Store balance values in versioned configuration rather than scattered constants.

## Completion
A save spans multiple shifts, gains XP, unlocks an ingredient and resulting recipes, updates a relationship, survives reload, and does not duplicate rewards. Locked or out-of-stock recipes never become valid just because the AI names them.
