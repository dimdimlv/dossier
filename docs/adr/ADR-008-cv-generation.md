# ADR-008: CV generation — Jinja2 templating, hybrid selection, draft/frozen separation

## Status

Accepted — 2026-06-23

## Context

Milestone M3 turns the inventory plus a job-description analysis (ADR-006) into a tailored CV. Three
coupled decisions are needed: how to render structured content into a document, how much of the
tailoring the LLM is trusted to do, and where generated output lives relative to the tracker's
immutable per-application records (ADR-005). Constraints already fixed: output is Markdown only for
this milestone (no PDF/LaTeX/Word); the engine's `LLMClient` protocol and `Analysis` output (ADR-006)
are the intended reuse seam; one CV template, no pluggable template system yet.

## Considered alternatives

### Templating

**A. Jinja2 with one Markdown template (chosen).** Handles loops/conditionals over a multi-section
document (experience roles, grouped skills, education) that the existing ad-hoc string-building in
`cli.py`'s `_analysis_to_markdown` cannot scale to cleanly. *Chosen.*

**B. Continue manual string-building.** Fine for the flat analysis report; would become unreadable for
a structured CV with repeated, nested sections. *Rejected.*

**C. A pluggable template-engine/template-selection abstraction.** Premature for one template and one
output format. *Rejected for M3 — can be added if/when multiple CV styles are needed.*

### Content selection vs. tailoring

**A. LLM selects and phrases everything in one call.** Best linguistic fluency, but non-deterministic
about *which* experience appears, harder to unit-test, and risks silently dropping or inventing
achievements. *Rejected.*

**B. Fully deterministic, no LLM involvement.** Fully testable and zero fabrication risk, but produces
generic, unphrased CVs and doesn't honour the explicit decision that generation should be
LLM-assisted. *Rejected as the sole method.*

**C. Hybrid — deterministic selection, LLM rephrases only (chosen).** `generator.selector` picks which
roles/achievements/skills to include, ranked by overlap with the JD's requirements and keywords
(falling back to "most recent + has metrics" without a JD) — pure, offline-testable Python, mirroring
ADR-006's deterministic/LLM split. A single `LLMClient.tailor_cv` call then rewrites only the summary
and the phrasing of the *already-selected* achievements, echoing back each achievement's `id` so
generation code can detect (and reject, raising `EngineError`) any dropped or invented item. *Chosen.*

### Where the new LLM schema/prompt/protocol method lives

**A. Inside `generator/` (the new package).** Would require `engine/client.py` to import from
`generator` to add `tailor_cv` to its `LLMClient` Protocol, inverting the existing one-directional
dependency (`generator` → `engine`). *Rejected.*

**B. Inside `engine/` alongside the JD-analysis schemas (chosen).** `engine/models.py` gains
`SelectedAchievement`/`TailoredAchievement`/`CVTailoring`, `engine/prompts.py` gains
`CV_TAILORING_SYSTEM`, and `engine/client.py` gains `tailor_cv` on the `LLMClient` Protocol — `engine`
remains the single owner of every `messages.parse` schema/prompt/provider concern, exactly as it
already owns `Analysis` even though that's conceptually an `analyzer.py`-level concept. `generator/`
depends only on `engine`, and owns selection (`selector.py`) and rendering (`render.py`). *Chosen.*

### Draft vs. frozen storage

**A. Write generated CVs directly into `applications/<id>/` via `attach_document`.** Conflates "a
candidate document was produced" with "this is what was actually sent" — exactly the distinction
ADR-005's immutable hashed-document design exists to preserve. *Rejected.*

**B. Write drafts to a separate, mutable `generated/` directory (chosen).** `config.get_generated_dir()`
mirrors `get_analysis_dir()`; `dossier generate cv --save` writes there. A human reviews/edits the
draft, then runs `dossier track attach` to copy and hash the chosen version into the frozen
per-application record — generation and tracking remain decoupled steps, as `docs/tracker-schema.md`
already anticipated. *Chosen.*

## Decision

`dossier generate cv --jd <file>` (JD always required — no untailored "general CV" mode in M3) loads
the inventory, runs the existing `engine.analyze_jd`, then `generator.generate_cv`: deterministic
selection of roles/achievements/skills (newest-first, ranked by relevance to the JD, skills grouped by
`SkillCategory` with relevant groups/skills first), one `LLMClient.tailor_cv` call to phrase the
summary and rephrase selected achievements (never inventing facts/metrics, never dropping/adding an
achievement), rendered to Markdown via a single Jinja2 template. `--save` writes the draft under
`$DOSSIER_DATA_PATH/generated/`; the CLI output explicitly points at `dossier track attach` as the next
step. New runtime dependency: `jinja2`.

## Consequences

### Positive

- CV quality benefits from LLM phrasing while remaining auditable: every achievement traces back to a
  real inventory item, never a fabricated one (enforced by the `id` round-trip, not just prompt wording).
- The selection logic (`generator/selector.py`) is fully unit-tested without any LLM client.
- Clean seam for M4 (cover letters): a second template plus a second narrow `LLMClient` method,
  following the same selection/tailoring/render shape.

### Negative

- One new runtime dependency (`jinja2`).
- CV quality is bounded by the deterministic selector's heuristics (skill-overlap + metrics presence);
  the LLM cannot rescue a poor selection — a future milestone could let it influence ranking.

### Neutral

- `engine/` continues to grow as the single home for all LLM-protocol schemas/prompts, even ones that
  exist "for" the generator layer — consistent with how it already houses `analyzer.py`/`Analysis`.

## References

- ADR-001 — Public/private repository separation (generated drafts are personal data).
- ADR-004 — Inventory schema (the selection input).
- ADR-005 — Application tracker persistence (the draft/frozen separation this ADR makes concrete on
  the generation side).
- ADR-006 — Engine JD analysis (the `LLMClient`/`Analysis` seam this milestone reuses).
- ADR-007 — Multi-provider LLM support (`tailor_cv` must work identically on both providers).
