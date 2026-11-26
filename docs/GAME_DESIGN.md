# Game design

## Promise
A single-player narrative bartending game: listen to a person, choose and prepare a drink, and build a relationship through what you say and serve. Aim for a complete game, not a permanently constrained demo.

## Two order types
- Named order: use the house recipe and explicit adjustments. Distinguish legitimate requested variation from accidental error.
- Recommendation: infer preferences through conversation and choose among valid available recipes. More than one answer can fit. Mood is contextual information, not a deterministic cocktail lookup.

## Visit flow
Arrival and greeting → story/order discovery → preparation → serving → reaction and continued conversation → natural departure. Ordering, preparation, and dialogue are independent state tracks; the arrows describe a common visit, not an enforced one-way chat lock.

The player can ask about taste, discuss the customer's situation, or offer advice. Some guests want a solution, others distraction or company. Topics include work/career, colleagues, burnout, relationships, breakups, family, uncertainty, everyday frustration, hobbies, and celebrations. Characters have interests, contradictions, humor, and boundaries beyond a single problem.

## Time and attention
Simulation time continues through reading, typing, recipe browsing, actions, and pending AI requests. Do not pause on focus in the input field. Hands-busy steps can temporarily prevent submitting a reply; preserve the draft and queued customer text. Avoid measuring empathy by typing speed. Mechanical time (ice dilution, active pouring) and social response windows are distinct.

Baseline: no global reply timeout that fails a visit while a player is actively shaking. When the action ends, the customer can await a response naturally. Unread dialogue persists. AI latency does not count as player silence. Details are tuned during T021, without stopping the game clock.

## Bartending
Select an available bottle/ingredient, measure, transfer, choose preparation, add ice, strain if needed, choose glass/garnish, and serve. Record all meaningful inputs. A recipe requiring an unsupported technique is visible as locked/unavailable, never silently converted to a different technique.

Provide clear feedback for selected bottle, target vessel, quantity, active action, errors, and serving readiness. Allow discard/remake with consistent costs once the economy exists. Recipe book search/filter supports names in both languages, spirit, method, flavor, and makeable-now.

## Stories and memory
Regulars return with remembered preferences and previously revealed facts. Separate immutable identity, evolving situation, relationship, and what the bartender knows. Private backstory is not automatically shown in the journal or used to penalize the player.

A visit can end with an unresolved life problem. The game evaluates attentive behavior, not agreement, extracting secrets, or guaranteeing a happy outcome. Customers may disagree without invalidating a respectful response.

## Shift and growth
Before shift: review stock/unlocks. During shift: serve and converse. After shift: review results, net earnings, XP and relationships. Advance and save. Higher levels unlock techniques/ingredients/recipes and richer encounter opportunities; short visits remain possible throughout.

## End-to-end checkpoint
One patron asks for a drink, exchanges dialogue, is served, responds, departs, and returns later with consistent memory. Each later milestone preserves an earlier playable path and an offline demo.

## Scope boundaries
No fixed final count of six recipes/three patrons. Fixtures may use small counts. Voice, multiplayer, a 3D world, a Steam integration, and hosted payment/billing are future expansions, not tasks hidden in the current build. Runtime character generation is planned as a module pending scope decision; runtime image generation has an explicit decision gate.
