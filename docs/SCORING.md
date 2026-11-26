# Evaluation and feedback

Confirmed: conversation contributes alongside preparation. Baseline: separate craft, preference fit and rapport. Weights, visibility, tips and thresholds remain tunable proposals, not approved values.

## Deterministic drink evaluation
Craft uses recorded quantities and preparation events against the selected house recipe, including explicit requested adjustments. Normalize unit conversion, compare with configurable tolerances, and explain consequential errors. A recipe calling for less sweetness must not be penalized for deviating from the unadjusted syrup target. Recommendation mode accepts multiple suitable recipes.

Preference fit uses only actionable information revealed to the player: dislikes, strengths, desired flavors, restrictions. Private character preferences may affect natural dialogue, but cannot create an unexplained deduction for information the player had no opportunity to learn. Clearly prohibited ingredients receive explicit feedback; no real-world clinical claims from the simulation.

Timing/intensity/dilution are gameplay approximations. Define and calibrate tolerances; do not claim physically exact taste simulation. Frame-rate independence is required.

## Rapport rubric proposal
| Dimension | Positive evidence | Avoid rewarding |
|---|---|---|
| Attention | References a specific detail accurately | Generic long sympathy paragraphs |
| Relevance | Follow-up connects to the customer's topic | Asking unrelated questions to extend chat |
| Boundaries | Respects refusal and asks before advice where useful | Extracting secrets or forcing a confession |
| Continuity | Remembers an established preference/event | Claiming unseen/private facts |
| Respect | Constructive, non-dismissive response | Automatic agreement with every claim |

Use evidence turn IDs. Accept multiple reasonable responses; no required sentiment or life decision. Do not grade the player's grammar, Korean/English choice, typing speed, or delayed response during active preparation. Do not score by number of messages.

## Feedback and rewards
End-of-visit response connects outcomes to specific actions. End-of-shift summary may show component scores and learning points; exact presentation O009 remains open. Keep AI wording separate from authoritative numeric reward calculation. No AI-generated money/XP updates. Rewards are applied once per encounter transaction.

Evaluator failure must be explicit in development logs and handled without a fake failure score. Decide provisional reward behavior before T029; do not repeatedly award rewards on reevaluation. Calibration set includes respectful disagreement, venting without advice, busy-action delay, ignored explicit preference, and prompt-injection attempts.
