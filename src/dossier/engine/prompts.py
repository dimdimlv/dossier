"""Prompt templates for the engine (versioned in the public repo, per CLAUDE.md).

Keep these stable and explicit; the model identifier is configured separately via
``ANTHROPIC_MODEL``. Bump ``PROMPT_VERSION`` when a prompt changes meaningfully so
it can be recorded as provenance alongside generated artifacts later.
"""

from __future__ import annotations

PROMPT_VERSION = "2026-06-21"

JD_EXTRACTION_SYSTEM = """\
You extract structured requirements from a job description (which may be in any \
language). Return only what the description actually states or clearly implies — do \
not invent requirements.

- Detect the job description's primary language and report it as an ISO 639-1 code \
  in the `language` field.
- Classify each skill as importance "required" (must-have) or "preferred" \
  (nice-to-have). Use the wording of the JD to decide.
- `skills` are concrete competencies/technologies/methods. `keywords` are the raw \
  ATS-style terms a screener might grep for (may overlap with skills).
- `responsibilities` are the main duties of the role, each a short phrase.
- Leave optional fields null when the JD does not state them. Do not guess salary, \
  company, or seniority if absent.
"""

GAP_ASSESSMENT_SYSTEM = """\
You compare a candidate's experience inventory against specific job requirements \
that were NOT matched by exact name. For each requirement, decide whether the \
inventory covers it:

- "covered": the inventory clearly demonstrates this (e.g. a synonym or a more \
  specific/general form — "k8s" vs "Kubernetes", "RDBMS" vs "PostgreSQL").
- "partial": related or adjacent experience exists but is not a full match.
- "gap": nothing in the inventory supports this requirement.

Cite concrete inventory items in `evidence` (skill names, roles, or achievements). \
Never fabricate experience the inventory does not contain. In `suggestions`, list \
existing inventory items that are most relevant to the gaps — items the candidate \
could legitimately emphasise — without inventing anything.
"""
