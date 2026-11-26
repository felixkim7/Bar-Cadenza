# Release and submission

The user targets the whole game by the deadline, 2026-12-01 (D020). Submission requirements remain open (O001). Preserve playable checkpoints throughout. Partial submission is a fallback, not an excuse to reduce the goal.

## Personal/course build
Windows source plus a runnable packaged build if required by the course. Include launch instructions, controls, Korean/English selection, known limitations and an offline scenario. Real AI requires explicitly configured access; offline demo must not masquerade as live generation. Keep a reproducible lockfile and build recipe.

## Submission scenario
Start a new save, choose language, meet guest, talk, prepare/serve, continue after service, close shift, review results, unlock something, save/reload, and demonstrate return memory. Prepare both live and offline variants. Record a backup video only if useful/required; it does not replace testing the actual executable.

## Packaging checks
Resources resolve outside repository cwd; fonts/license files included; application writes only to user-data folder; missing device/network handled; no credentials/logs/saves included; Windows target architecture documented. Test the package on a machine/user account without the development environment where feasible.

## Later wider distribution
Keep provider and persistence adapters replaceable. Before public/Steam release, decide hosted AI versus user-supplied credentials, usage costs, account access, cloud saves, generated-content policy, licenses and distribution requirements using then-current official guidance. These are future decisions, not functionality promised by this starter. Do not add Steam SDK, payments or cloud infrastructure just for hypothetical readiness.
