# Engine — JD analysis and gap reporting

The **engine** is the layer that calls the Anthropic API. Its first capability (M2) takes a job
description in any language, extracts a structured set of requirements, and compares them against
your inventory to produce a **gap report**. Rationale and alternatives:
[ADR-006](adr/ADR-006-engine-jd-analysis.md).

> The model is read from `ANTHROPIC_MODEL` (default `claude-sonnet-4-6`); the key from
> `ANTHROPIC_API_KEY`. Both live in your local, gitignored `.env` (see `.env.example`). JD text and
> saved analyses are personal data and are written only under `DOSSIER_DATA_PATH` (ADR-001).

## Providers

The engine can use **Anthropic** (default) or **OpenAI**, selected by `DOSSIER_LLM_PROVIDER`
(`anthropic` | `openai`) or the `--provider` flag on `analyze`. Both use their official SDK with
structured outputs — there is no compatibility shim. Rationale: [ADR-007](adr/ADR-007-multi-provider-llm.md).

| Provider | Key | Model | Notes |
|---|---|---|---|
| `anthropic` (default) | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` (default `claude-sonnet-4-6`) | |
| `openai` | `OPENAI_API_KEY` | `OPENAI_MODEL` (**required**, no default) | pick a model that supports structured outputs |

```bash
# Use OpenAI for a single run (env vars must be set):
uv run dossier analyze --jd jd.txt --provider openai
# Or make it the default in .env:  DOSSIER_LLM_PROVIDER=openai
```

## How it works (hybrid analysis)

1. **Extract** — Claude parses the JD into structured `JobRequirements` (role, seniority, detected
   language, required vs preferred skills, responsibilities, ATS keywords) via the SDK's
   `messages.parse(output_format=...)` for validated output.
2. **Match (deterministic)** — required skills are matched against the inventory by name, alias, and
   the skills referenced in your experience. This pass is exact and runs offline.
3. **Assess (LLM)** — only the requirements that didn't match exactly are sent back to Claude, which
   judges semantic coverage (`covered` / `partial` / `gap`, e.g. "k8s" ≈ "Kubernetes") and suggests
   existing inventory items relevant to the gaps. Skipped entirely when everything matched, or with
   `--no-llm-gaps`.

The result is an `Analysis` = the extracted `JobRequirements` plus a `GapReport`
(per-requirement coverage, suggestions, and a one-line summary like "8 of 12 covered; 4 gaps").

## CLI

```bash
# Analyse a JD against your inventory (prints a markdown report):
uv run dossier analyze --jd path/to/jd.txt

# From stdin, an explicit inventory, JSON output, or save to dossier-data:
pbpaste | uv run dossier analyze --jd -
uv run dossier analyze --jd jd.txt --inventory tests/fixtures/inventory --json
uv run dossier analyze --jd jd.txt --save        # writes analysis/<slug>-<ts>.json and .md

# Deterministic matching only (no second API call):
uv run dossier analyze --jd jd.txt --no-llm-gaps
```

`--jd` accepts a file path or `-` for stdin. `--inventory` defaults to
`$DOSSIER_DATA_PATH/inventory`. `--language` overrides the analysis language (default
`DOSSIER_DEFAULT_LANGUAGE`, else `en`). Note: extraction always needs the API; `--no-llm-gaps` only
skips the second (gap-assessment) call.

## Testing

Unit tests inject a fake `LLMClient` and never hit the network. A single opt-in live test
(`tests/test_engine_live.py`) runs only when `ANTHROPIC_API_KEY` is set.
