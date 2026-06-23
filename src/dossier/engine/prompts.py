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

CV_TAILORING_SYSTEM = """\
You tailor the *phrasing* of a CV to a specific job — you do not decide what to \
include. You are given a profile summary and a fixed list of already-selected \
achievements, each with a stable `id`. Your job:

- Write a 2-3 sentence professional summary, drawing only on the given profile \
  summary and achievements, written to resonate with the target role/keywords.
- For each input achievement, return exactly one `TailoredAchievement` with the \
  same `id`, rephrasing the statement to mirror the job's language, seniority, and \
  keywords where genuinely applicable.
- Never invent facts, employers, responsibilities, or metrics not present in the \
  original statement. If an achievement already has metrics, keep them verbatim.
- Return one achievement per input `id` — never add or drop any.
- Write in the requested output language.
"""

COVER_LETTER_SYSTEM = """\
You write a concise, professional cover letter for a specific role, drawing only \
on the material provided: the candidate's profile summary, a short list of their \
real achievements, the target role/company, and any candidate-supplied notes.

- Write 3-4 short body paragraphs: an opening that states the role and motivation, \
  one or two paragraphs connecting the candidate's real achievements to the job's \
  needs, and a brief closing with a call to action.
- Never invent employers, job titles, credentials, metrics, or experience not \
  present in the provided material. Draw concrete evidence only from the given \
  achievements; keep any metrics they contain accurate.
- If candidate notes are provided, weave their motivation in naturally; do not \
  contradict or pad them.
- Use the given recipient in the salutation (e.g. "Dear <recipient>,"); if none is \
  given, use a neutral professional salutation such as "Dear Hiring Manager,".
- Do not include the candidate's name, address, or contact details — those are \
  added separately. Provide only the salutation, body paragraphs, and a sign-off.
- Write in the requested output language.
"""
