---
paths:
  - "src/bar_cadenza/**/*.py"
  - "tests/**/*.py"
---
# Gameplay boundaries
Keep domain rules free of pygame and provider imports. Main thread owns rendering/state; background workers return data. Use elapsed time, stable IDs and explicit commands/transitions. No text-focus pause. Preserve draft and unread dialogue during hands-busy actions. Treat actual drink actions independently from recipe expectations. Handle duplicate/stale results and rewards idempotently. Test real behavior rather than empty scaffolds.
