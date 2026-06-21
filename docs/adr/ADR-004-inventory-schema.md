# ADR-004: Inventory schema — hybrid YAML + Markdown frontmatter, validated with Pydantic v2

## Status

Accepted — 2026-06-21

## Context

Milestone M1 requires the first real domain code: the **inventory**, the structured store of
professional experience from which the engine will later assemble tailored CVs and cover letters.
Before any data is authored, three coupled decisions are needed, all awkward to reverse once data
and code depend on them:

1. **On-disk format** — how inventory entries are represented as files.
2. **Validation technology** — how the shape of that data is enforced in code.
3. **Entity scope** — which parts of a professional profile the first schema models.

Constraints already fixed by earlier decisions: the inventory is **human-authored, version-
controlled files** in the private `dossier-data` repo, read at runtime via `DOSSIER_DATA_PATH`
(ADR-001); the public README describes the inventory as "Markdown files under version control";
the toolchain is Python 3.13 managed with `uv` (ADR-003). The project also values being a
learning artifact in modern practices, which favours conventional, well-supported tools.

The data is heterogeneous: skills and education are **list-like records**, while a work role is a
**prose narrative with structured metadata** (company, dates, the skills it exercised, and
quantified achievements).

## Considered alternatives

### On-disk format

**A. Pure YAML for everything.** Uniform and trivial to parse/validate. But multi-paragraph role
descriptions become awkward YAML block scalars, and the narrative — the most human part of the
inventory — reads poorly in a data file. *Rejected.*

**B. Markdown + frontmatter for everything**, including one file per skill. Uniform Markdown and
keeps the README's "Markdown" framing literally. But list-like data (skills, education) fragments
into many tiny files with mostly-empty bodies, which is heavier to author and read. *Rejected.*

**C. Hybrid (chosen).** YAML for list-like data (`profile.yaml`, `skills.yaml`,
`education.yaml`); Markdown + YAML frontmatter for narrative roles (`experience/*.md`, structured
fields in frontmatter, prose in the body). Best fit per entity type: queryable structure where
the data is structured, first-class prose where the data is narrative. Honours the "Markdown
under version control" intent where it matters. Cost: two formats and a frontmatter parser.
*Chosen.*

### Validation technology

**A. Pydantic v2 (chosen).** Declarative models, coercion, rich and locatable error messages,
JSON Schema export, fast Rust core; the de-facto standard for this in modern Python and good
learning value. Cost: one well-maintained runtime dependency. *Chosen.*

**B. Standard-library dataclasses + hand-written validation.** Zero dependencies, but reinvents
coercion, enum checking, nested validation and error reporting, growing in boilerplate and bugs
as the schema grows. *Rejected.*

**C. attrs / msgspec.** Lighter or faster, but less batteries-included (validation and JSON
Schema need extra wiring) and less ubiquitous than Pydantic. Speed is irrelevant at inventory
sizes. *Rejected.*

### Entity scope

**A. Minimal (Profile + Skills + Experience).** Fastest, but a generated CV would lack education
and quantified achievements. *Rejected as too thin.*

**B. Profile + Skills + Experience + Education, achievements embedded in each role (chosen).**
Enough to assemble a credible first CV, consistent with the walking-skeleton approach.
Achievements live where they have context — inside the role. *Chosen.*

**C. Broader (standalone, cross-referenced Achievements and Projects now).** Richer querying, but
more schema and design surface than a first cut warrants; premature before the engine exists to
exploit it. *Deferred to a later iteration.*

## Decision

Adopt a **hybrid on-disk format** (YAML for `profile`/`skills`/`education`; Markdown + YAML
frontmatter for `experience/*.md`), modelled and validated with **Pydantic v2**, scoped to
**Profile, Skill, Experience (with embedded Achievement) and Education**.

Specifics:

- Models in `src/dossier/inventory/models.py`; `extra="forbid"` so unknown fields fail loudly; a
  `YearMonth` type accepting `"YYYY"`/`"YYYY-MM"` (null `end` = present).
- A loader in `src/dossier/inventory/loader.py` reads the files (frontmatter via the
  `python-frontmatter` library) and wraps validation errors in an `InventoryError` that **names
  the offending file**. Unknown skill references produce a non-fatal warning.
- Path resolution in `src/dossier/config.py` reads `DOSSIER_DATA_PATH` (loading a local `.env`
  via `python-dotenv`).
- A `dossier inventory validate` CLI (argparse) validates an inventory and prints a summary.
- New runtime dependencies: `pydantic`, `pyyaml`, `python-frontmatter`, `python-dotenv`
  (all small, ubiquitous, well-maintained).
- Synthetic fixtures live in the public repo under `tests/fixtures/inventory/`; real data lives
  only in `dossier-data` (ADR-001).

## Consequences

### Positive

- Each entity is stored in the format that suits it; roles keep first-class prose.
- Strong, declarative validation with locatable, file-named errors — and a CLI to run it.
- A clean importable namespace (`dossier.inventory`) and a documented format
  ([`docs/inventory-schema.md`](../inventory-schema.md)) for future milestones to build on.

### Negative

- Two on-disk formats and a frontmatter parser to maintain.
- Four new runtime dependencies (accepted; all are standard and low-risk).

### Neutral

- The schema is intentionally a walking skeleton; standalone Achievements/Projects and richer
  cross-referencing are expected to follow in a later ADR rather than being designed up front.
- The README's "Markdown files" description is now made precise by this ADR and the schema doc.

## References

- ADR-001 — Public/private repository separation.
- ADR-003 — Python project layout (`uv`, `src/` layout).
- Pydantic v2 documentation — https://docs.pydantic.dev/latest/
- `python-frontmatter` — https://python-frontmatter.readthedocs.io/
