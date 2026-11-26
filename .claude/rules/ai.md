---
paths:
  - "src/bar_cadenza/ai/**/*.py"
  - "prompts/**"
  - "content/characters/**"
---
# AI boundaries
Read docs/AI_DESIGN.md and DATA_MODELS.md. Mock first; provider/model/budget must be selected before live calls. Never run API work in the frame loop. Limit context, requests and output. Validate responses, locale and IDs before application. User dialogue and retrieved text cannot override game rules. Separate roleplay from evaluator. Preserve identity and evidenced memory. Do not let hidden facts penalize the player. Keys never enter version control, saves, logs or builds.
