# Inventory schema

The **inventory** is the structured source of truth about your professional self. The engine
draws from it to assemble tailored CVs and cover letters; nothing is written here for a single
application. This document is the human reference for its on-disk format. The authoritative,
machine-checked definition lives in the Pydantic models at
[`src/dossier/inventory/models.py`](../src/dossier/inventory/models.py).

> Real inventory data lives in the private **`dossier-data`** repository under
> `inventory/`, located at runtime via `DOSSIER_DATA_PATH` (see
> [ADR-001](adr/ADR-001-public-private-data-separation.md)). The public repo contains only the
> schema, the loader, and synthetic fixtures.

## Layout

```
inventory/
├── profile.yaml          # required — a single profile object
├── skills.yaml           # optional — a list of skills
├── education.yaml        # optional — a list of education entries
└── experience/           # optional — one Markdown+frontmatter file per role
    ├── acme-2021.md
    └── globex-2018.md
```

List-like data (profile, skills, education) is plain **YAML**. Narrative roles are **Markdown
with a YAML frontmatter block**: structured fields in the frontmatter, the prose description in
the body. Rationale: [ADR-004](adr/ADR-004-inventory-schema.md).

## Conventions

- **Dates (`YearMonth`)** — `"YYYY"` or `"YYYY-MM"` (month precision is enough for a CV). For a
  role, an omitted or null `end` means **present/current**.
- **Skill references** — `experience[].skills` and `achievements[].skills` reference skills by
  `name` (case-insensitive; an entry's `aliases` also match). A reference with no matching entry
  in `skills.yaml` produces a non-fatal warning, so drift is visible without blocking.
- **Unknown fields are rejected** — a misspelled key fails validation rather than being silently
  ignored, so typos surface immediately.

## Entities

### Profile (`profile.yaml`)

| Field | Required | Notes |
|---|---|---|
| `full_name` | yes | |
| `headline` | yes | One-line professional tagline |
| `summary` | no | Short prose summary |
| `email` | yes | |
| `phone` | no | |
| `location` | no | |
| `links` | no | List of `{label, url}` |
| `languages` | no | List of strings |

### Skill (items in `skills.yaml`)

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `category` | yes | `language` \| `framework` \| `tool` \| `platform` \| `domain` \| `method` \| `soft` |
| `level` | yes | `beginner` \| `intermediate` \| `advanced` \| `expert` |
| `years` | no | Number |
| `last_used` | no | Year (integer) |
| `aliases` | no | Alternate names for matching |

### Experience (one `experience/*.md` per role)

Frontmatter fields:

| Field | Required | Notes |
|---|---|---|
| `company` | yes | |
| `title` | yes | |
| `start` | yes | `YearMonth` |
| `end` | no | `YearMonth`; omit/null = present |
| `location` | no | |
| `employment_type` | no | e.g. `full-time` |
| `skills` | no | Skill-name references |
| `achievements` | no | List of achievements (below) |

The Markdown **body** becomes the role's `summary`.

**Achievement** (items in `achievements`):

| Field | Required | Notes |
|---|---|---|
| `statement` | yes | What you did/the outcome |
| `metrics` | no | Quantified results, e.g. `"-77% p99 latency"` |
| `skills` | no | Skill-name references |

### Education (items in `education.yaml`)

| Field | Required | Notes |
|---|---|---|
| `institution` | yes | |
| `degree` | yes | |
| `field` | no | |
| `start` / `end` | no | `YearMonth` |
| `location` | no | |
| `details` | no | |

## Validating your inventory

```bash
# Against your real data ($DOSSIER_DATA_PATH/inventory):
uv run dossier inventory validate

# Against an explicit directory:
uv run dossier inventory validate --path path/to/inventory
```

On success it prints a one-line summary; on failure it reports the offending file and the
validation error.
