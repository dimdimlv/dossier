# ADR-009: Cover letter generation — composed prose with best-effort anti-fabrication

## Status

Accepted — 2026-06-23

## Context

Milestone M4 generates a tailored cover letter from the inventory plus a job-description analysis. ADR-008 already pre-declared this as "a second template plus a second narrow `LLMClient` method, following the same selection/tailoring/render shape" as the CV generator, and the tracker already supports it (`DocumentKind.cover_letter`, the `generated/` draft area). So most of M4 is a straight application of the M3 pattern and needs no new decision.

One thing genuinely differs and is worth recording. The CV generator (ADR-008) gives a **structural** no-fabrication guarantee: the LLM only rephrases achievements that were deterministically selected and handed to it, echoing each back by `id`, so generation code can reject anything dropped or invented. A cover letter is **composed prose** — its whole value is narrative synthesis — so there is no 1:1 item mapping to enforce. The anti-fabrication property therefore cannot be structural; it must be best-effort.

## Considered alternatives

### Content model

**A. Structured paragraphs (chosen).** The LLM returns `salutation` + `body_paragraphs[]` + `signoff`; the candidate's name/contact and the date come from the `Profile` deterministically and are rendered by the Jinja2 template. Keeps the content/render decoupling of `CVDraft`, keeps the candidate's identity out of the LLM's output (less to fabricate), and makes rendering/tests assert on discrete fields. *Chosen.*

**B. Single prose body blob.** The LLM returns the whole letter as one string; the template just wraps it. Simpler schema, but layout is at the model's mercy and harder to assert on. *Rejected.*

**C. Fully deterministic template fill.** A cover letter is inherently generative narrative; a fixed template produces a robotic, generic letter. *Rejected* — contradicts the point of the feature.

### Anti-fabrication

**A. Structural guarantee via id echo-back (as in the CV).** Not applicable: prose composition is not a per-item rephrasing, so there is no id set to round-trip. *Not available.*

**B. Best-effort: explicit prompt constraint + source-limited input + human-in-the-loop (chosen).** The `COVER_LETTER_SYSTEM` prompt forbids inventing employers/titles/credentials/metrics; the model is fed *only* real selected achievements + profile summary as source material; and the existing draft → review → `dossier track attach` workflow keeps a person between generation and anything that gets sent. The residual risk (a model could still embellish) is accepted and mitigated by that review step. *Chosen.*

### Personalization inputs

**A. Optional `--notes` and `--to` (chosen).** A good cover letter often needs candidate motivation that isn't in the inventory (relocation, enthusiasm for the product) and an addressee. Both are optional free-text; `--to` defaults to a neutral "Dear Hiring Manager," salutation. *Chosen.*

**B. No personalization inputs.** Simpler, but letters read generic and the candidate can't steer them without hand-editing. *Rejected.*

## Decision

`dossier generate cover-letter --jd <file>` (JD required, mirroring `generate cv`) runs the existing `engine.analyze_jd`, deterministically selects a tight set of highlights via the shared `select_experiences` selector (capped tighter than the CV — a few roles, ~2 achievements each), and calls a new `LLMClient.draft_cover_letter` method that returns a `CoverLetter` (`salutation` + `body_paragraphs[]` + `signoff`). The result is wrapped in a `CoverLetterDraft` (adding profile, company/role, recipient, date) and rendered to Markdown via a dedicated `cover_letter.md.j2` template. `--to` and `--notes` personalize the letter; `--save` writes `{slug}-cover-letter-{timestamp}.md` under `$DOSSIER_DATA_PATH/generated/`, frozen later via `dossier track attach --kind cover_letter`. The new schema, prompt, and protocol method live in `engine/` (single owner of all `messages.parse` concerns, per ADR-008); no new runtime dependency.

## Consequences

### Positive

- Reuses the entire M3 pipeline (selector, shared Jinja2 env, `generate` CLI family, draft/frozen split); the only genuinely new code is one schema, one prompt, one client method, one template, and the orchestration/CLI glue.
- Personalized, JD-tailored letters with candidate motivation woven in.

### Negative

- No structural anti-fabrication guarantee for the prose — best-effort only, leaning on the prompt, source-limited input, and human review. A determined model could still embellish; the review step is the backstop.

### Neutral

- `engine/` keeps growing as the home for all LLM-protocol schemas/prompts, including ones conceptually owned by the generator layer — consistent with how `Analysis`/`CVTailoring` already live there.

## References

- ADR-001 — Public/private repository separation (generated drafts are personal data).
- ADR-004 — Inventory schema (the selection input).
- ADR-005 — Application tracker persistence (draft/frozen separation; `DocumentKind.cover_letter`).
- ADR-006 — Engine JD analysis (the `LLMClient`/`Analysis` seam reused).
- ADR-008 — CV generation (the pattern this milestone extends, and the structural guarantee this one cannot match).
