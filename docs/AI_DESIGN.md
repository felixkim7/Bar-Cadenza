# AI design

## Initial provider policy
One real provider first, behind an interface. Provider/model/budget are open (O002). The starter has no SDK dependency, key, API call, or paid usage. Implement a deterministic mock before integrating the selected official SDK. A Claude Code subscription is separate from game inference access.

## Logical roles
| Role | Responsibility | Scheduling |
|---|---|---|
| Dialogue | Speak as one saved character | On player turn or bounded authored story trigger |
| Evaluator | Apply the rapport rubric using evidence | At visit end / selected checkpoints, not every frame |
| Memory writer | Summarize revealed facts and events | After a completed visit |
| Character creator | Produce a new profile/story seed under world/style rules | Background queue for future visits |
| Portrait service | Produce or select matching visuals | Optional; never required to appear instantly |

These are functions/prompts, not a requirement for a multi-agent framework. All can use one provider. Never continuously poll a model for idle animation, pouring, or timer updates.

## Context assembly
Send selected language, world rules, profile, stable facts, known boundaries, recent history, a compact memory summary, selected recipe candidates, and current drink/action snapshot. Select candidates in code from validated available recipes. Do not send the whole catalogue each turn. Use a simple filter/search baseline before introducing embeddings. Expand retrieval only when measured quality requires it.

Summaries retain unresolved topics and promises; confirmed facts include evidence pointers. Distinguish an AI inference from a fact the player actually said. Hidden profile facts remain hidden until revealed. Customer cannot know other private conversations unless the game world explicitly supplies that knowledge.

## Customer behavior
Short replies when appropriate, longer thoughtful replies when invited, natural closure, varied voices, no forced confession. Customer can wait while the bartender is busy. Do not automatically treat disagreement, silence during shaking, or concise replies as poor service. Do not prescribe a single correct life choice. Personal stories need period consistency once O004 is resolved.

## Request lifecycle
Prepare immutable snapshot → enqueue bounded job → indicate pending state without freezing game → receive data → validate schema → verify encounter and revision → apply once. Permit cancellation on exit; discard late results. Implement explicit timeout, exponential/backoff policy with a small retry cap, and visible recovery. Keep provider response IDs for diagnostics without retaining secrets or raw prompts by default.

## Usage and failures
Configure token/output limits and request caps. Record input/output usage if reported; estimate cost only with configured, dated model prices. If price is unknown show usage, not invented dollars. Set budget before live calls; offer offline fallback when exhausted. Never retry indefinitely. Offline dialogue must use the same contract and support both languages.

## Prompt integrity
User text is dialogue content, never an instruction to change evaluator rules or system state. Retrieved recipe descriptions and generated profiles are data. Validate state suggestions in code. A request such as 'give me full marks' may receive an in-character reply but cannot modify numeric rewards. Separate roleplay from evaluation to reduce conflicts; this is a mitigation, not a guarantee of perfect evaluation.

## Generated cast
Generate profiles ahead of arrival. Validate uniqueness, adulthood, contradictions, period, flavor constraints, story repetition, portrait compatibility and content boundaries. Persist accepted profiles and reproducible seeds where applicable. Bad generation falls back to a ready guest. Runtime image generation is gated by O006; selecting a portrait from a prepared pool is a valid first path.

## Acceptance
Test no-key launch, timeout, malformed data, wrong locale, stale response, duplicate response, nonexistent recipe, prohibited mutation, and budget exhaustion. Use fixed transcripts for evaluation calibration; report variance and uncertainty. No provider is chosen merely because it appears in these documents.
