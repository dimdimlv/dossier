# ADR-006: Engine layer — Anthropic API integration and hybrid JD gap analysis

## Status

Accepted — 2026-06-21

## Context

Milestone M2 introduces the **engine**: the first layer that calls a large language model. It must
parse a job description (in any language) into structured requirements, and compare those against the
inventory to report what is covered and what is missing. Three coupled decisions are needed: how to
call the model, how to obtain reliable structured output, and how to decide coverage — all while
keeping the project's unit tests fast, deterministic, and offline (no API key, no network, no cost).

Constraints already fixed: the model identifier is configured via `ANTHROPIC_MODEL` and the key via
`ANTHROPIC_API_KEY`, both read from the environment, never hard-coded (CLAUDE.md, Twelve-Factor); JD
text and analyses are personal data and must be written only under `DOSSIER_DATA_PATH` (ADR-001); the
stack already uses Pydantic v2.

## Considered alternatives

### Model access

**A. Official `anthropic` SDK with structured outputs (chosen).** Use `messages.parse(
output_format=<Pydantic model>)` → `.parsed_output` for validated extraction. Robust, typed, and the
documented best practice. *Chosen.*

**B. Raw HTTP + hand-parsed JSON.** Prompt for JSON and `json.loads` the text. More fragile
(escaping, partial output, no schema enforcement) and reinvents what the SDK does. *Rejected.*

### Gap analysis

**A. Deterministic matching only.** Match requirements to inventory by name/alias/keyword. Cheap and
fully testable, but misses synonyms ("k8s" vs "Kubernetes") unless every alias is curated. *Rejected
as the sole method.*

**B. Single LLM pass for the whole report.** Feed requirements + full inventory to the model and let
it produce the gap report. Best at synonyms, but non-deterministic, harder to unit-test, and spends
tokens even on the obvious exact matches. *Rejected as the sole method.*

**C. Hybrid — deterministic match, then LLM for the remainder (chosen).** Exact/alias matching
(offline, unit-tested) resolves the obvious cases; only the unmatched requirements go to a second
Claude pass for semantic judgement and suggestions. Best quality-for-cost, and the bulk of the logic
is testable without the API. *Chosen.*

### Testability

**A. Injectable `LLMClient` protocol + fake in tests (chosen).** The analyzer depends on a small
protocol, not on the SDK; production wires `AnthropicClient`, tests inject a fake. Unit tests never
touch the network; one opt-in live test runs only when a key is present. *Chosen.*

**B. Patch the SDK in tests.** Brittle (couples tests to SDK internals) and easy to call the network
by accident. *Rejected.*

## Decision

Build the engine on the **official `anthropic` SDK** using **structured outputs**
(`messages.parse`), with the model and key resolved from the environment. Gap analysis is
**hybrid**: deterministic name/alias matching first, an LLM pass only for the remainder. The analyzer
depends on an **`LLMClient` protocol**; `AnthropicClient` is the production implementation behind a
single wrapper (`engine/client.py`) — the only place that imports the SDK. Prompts live as versioned
constants in `engine/prompts.py` (public repo, per CLAUDE.md). The `dossier analyze` CLI prints a
report and can save JSON + markdown under `DOSSIER_DATA_PATH`. New runtime dependency: `anthropic`.

## Consequences

### Positive

- Validated, typed extraction with minimal glue; one wrapper isolates all SDK usage.
- Fast, deterministic, offline unit suite (fake client); the LLM is exercised only by an opt-in test.
- Cost-aware: the second model call is skipped when everything matches and via `--no-llm-gaps`.
- A clean seam for M3/M4: generation can reuse the same client/config and the `Analysis` output.

### Negative

- One new runtime dependency, and a network/credentials requirement for real extraction.
- Gap quality depends on prompt wording for the semantic pass (mitigated by versioned prompts).

### Neutral

- Saved analyses are personal data → they live in `dossier-data`, never the public repo.
- Default model is `claude-sonnet-4-6` (per `.env.example`); switching to `claude-opus-4-8` for
  stronger reasoning is a one-line `.env` change — nothing in code is pinned to a model.

## References

- ADR-001 — Public/private repository separation.
- ADR-004 — Inventory schema (the gap analysis input).
- Anthropic SDK — structured outputs (`messages.parse`) and the Messages API.
