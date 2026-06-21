# ADR-007: Multi-provider LLM support — pluggable engine clients (Anthropic default, OpenAI optional)

## Status

Accepted — 2026-06-21

## Context

The engine (ADR-006) was built against an `LLMClient` protocol with a single implementation
(`AnthropicClient`) chosen by a `build_default_client()` factory, and provider-neutral prompt
constants. A second provider — **OpenAI** — is now wanted as a selectable option, both for the
author's flexibility and as a demonstration that the engine is not coupled to one vendor. The change
should be additive (Anthropic stays the default), keep the unit suite offline and deterministic, and
respect the project's Twelve-Factor configuration (model and keys from the environment).

Three questions: how a provider is selected, how OpenAI produces validated structured output, and
whether OpenAI gets a default model.

## Considered alternatives

### Provider selection

**A. Explicit `DOSSIER_LLM_PROVIDER` env var + `--provider` flag (chosen).** Twelve-Factor,
predictable, and consistent with the rest of `config.py`; the CLI flag allows a one-off override.
*Chosen.*

**B. Infer the provider from which key is set.** Convenient until both keys are present, then
ambiguous; surprising and order-dependent. *Rejected.*

### OpenAI integration

**A. Official `openai` SDK with structured outputs (chosen).** Use
`client.beta.chat.completions.parse(response_format=<Pydantic model>)` →
`choices[0].message.parsed`, mirroring Anthropic's `messages.parse`. Each provider keeps its own
official SDK behind the shared protocol. *Chosen.*

**B. One SDK against an OpenAI-compatible `base_url` shim.** Tempting for "one code path", but
couples behaviour to a lowest-common-denominator surface and breaks provider-specific features
(structured outputs, error types). *Rejected.*

### OpenAI default model

**A. Require `OPENAI_MODEL`, no hard-coded default (chosen).** Structured-output support varies by
model, and OpenAI's model IDs change; requiring the user to name one avoids pinning a possibly-stale
or unsupported model in code, and fails fast with a clear `ConfigError`. *Chosen.*

**B. Hard-code a default (e.g. `gpt-4o`).** Convenient but bakes a model ID into the codebase that
can drift. *Rejected* (the user can still set any model via `.env`).

## Decision

Support both providers behind the existing `LLMClient` protocol. Add `OpenAIClient` alongside
`AnthropicClient` in `engine/client.py` (a small `_ParsingClient` base holds the two public methods;
each subclass implements `__init__` + `_parse`). `build_default_client(provider=None)` dispatches on
`provider or config.get_provider()`. Selection is via **`DOSSIER_LLM_PROVIDER`** (default
`anthropic`) with a `--provider` override on `dossier analyze`. OpenAI uses the **official `openai`
SDK** with structured outputs; **`OPENAI_MODEL` is required** (no default). The SDK import inside
each client is lazy, so importing the engine doesn't load a provider you aren't using. New runtime
dependency: `openai`.

## Consequences

### Positive

- The engine is demonstrably provider-agnostic; switching is a one-line `.env` change or a flag.
- No behaviour change for existing Anthropic users (it remains the default).
- Unit tests stay offline: a fake SDK client exercises `OpenAIClient`; live tests are gated on keys.
- Each provider keeps full access to its own SDK features (structured outputs, typed errors).

### Negative

- A second runtime dependency (`openai`), installed even for Anthropic-only use (lazy-imported, so
  not loaded at runtime unless selected). Making it an optional extra is a noted future refinement.
- Two SDK surfaces to keep working as they evolve.

### Neutral

- Prompts are shared, unchanged, across providers (they were already provider-neutral).
- `OPENAI_MODEL` being required is intentional friction that prevents silently using an unsupported
  model.

## References

- ADR-006 — Engine layer and the `LLMClient` protocol this builds on.
- Anthropic SDK `messages.parse`; OpenAI SDK `beta.chat.completions.parse` (structured outputs).
