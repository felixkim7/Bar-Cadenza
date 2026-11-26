# Claude Code workflow

## First session
Paste this from the project root:

> Read CLAUDE.md, docs/DECISIONS.md, docs/STATUS.md and docs/tasks/INDEX.md. Start T001 only. Confirm the environment, run the starter checker, resolve and lock dependencies, and verify the package diagnostic. Record actual evidence. Do not implement later tasks or silently select an AI provider. Ask only for missing information that blocks this task.

## Next task
> Read current STATUS and the task index. Implement the next eligible task only. Show its requirements, dependencies and completion criteria first. Preserve user changes. Run relevant checks, record evidence and update STATUS/index before stopping.

## Authorized range
> Implement T006 through T008 in order, one task at a time. Complete checks and update status after each task. Continue without asking for routine confirmation. If a decision blocks one task, explain it and work only on independent authorized tasks.

## Resume after a break / new context
> Read CLAUDE.md and docs/STATUS.md. Inspect the working tree and last completed task evidence. Summarize what actually exists and resume the current task. Do not infer completion from filenames or the old conversation.

## Debug a problem
> Reproduce this issue first. Separate runtime/syntax failures from logic/output/style issues. Preserve the original structure where practical, fix the smallest responsible area, verify the behavior, and update the affected task evidence.

## Visual review
> Compare the running bar scene at normal size with docs/ART_DIRECTION.md and the supplied references. Check interactive object readability, expression, contour, palette, perspective, lighting and UI text. List observed mismatches before making scoped fixes. Do not switch styles.

## Task states and records
`not_started`, `in_progress`, `blocked`, `implemented_pending_verification`, `done`.
The JSON catalogue carries stable IDs/dependencies/coverage. INDEX.md carries current task status; each task's Evidence section records results. STATUS.md carries the next action and active blockers. Keep these synchronized. Requirement completion is tracked separately in REQUIREMENTS.md because one task may only partially cover a requirement.

A task with code but missing Windows manual evidence is pending verification, not done. If work proceeds while that check is pending, say why it is safe; do not label its milestone submission-ready.

## Commit policy
Use a focused commit after a verified task when local commits are authorized in the session. Suggested message: `T014: implement measured pouring`. Do not stage unrelated edits. Do not push without authorization. Record actual SHA only after commit exists.

## Instructions versus procedures
CLAUDE.md holds concise stable constraints. Path-scoped `.claude/rules/` hold detailed local conventions. This pack intentionally uses ordinary task documents and copy/paste prompts instead of custom skills, hooks or permission overrides. No plugin or parallel-agent setup is required. If instructions conflict with a new explicit user decision, update the decision register and affected docs.
