# Application tracker

The **tracker** records every job application, its evolving status, and the exact CV / cover
letter / job description sent with it — frozen for future analysis. It is a SQLite database
accessed through SQLAlchemy 2.0, with Alembic migrations. Rationale:
[ADR-005](adr/ADR-005-application-tracker-persistence.md).

> The database and the frozen documents are **personal data** and live in the private
> **`dossier-data`** repo, located at runtime via `DOSSIER_DATA_PATH` (ADR-001). The public repo
> holds only code, migrations, and synthetic fixtures.

## On-disk layout (in `dossier-data/`)

```
applications/
├── applications.db                 # SQLite database (committed)
└── <application_id>/               # frozen, immutable record of what was sent
    ├── cv-<timestamp>.md
    ├── cover_letter-<timestamp>.md
    └── job_description-<timestamp>.md

generated/
├── <slug>-<timestamp>.md               # mutable CV drafts from `dossier generate cv --save`
└── <slug>-cover-letter-<timestamp>.md  # mutable cover letter drafts from `dossier generate cover-letter --save`
```

`generated/` holds mutable CV and cover letter drafts written by `dossier generate`;
`applications/<id>/` holds the frozen copy of what was actually sent (taken at attach time, never
mutated). `<slug>` is derived from the candidate's name. Review a draft, then run
`dossier track attach` (with `--kind cover_letter` for letters) to copy and hash the chosen version
into the frozen record (ADR-008, ADR-009).

## Tables

### `applications`
`id`, `company`, `role`, `status`, `source`, `location`, `work_mode` (onsite/hybrid/remote),
`compensation`, `url`, `applied_on`, `follow_up_on`, `notes`, `created_at`, `updated_at`.

### `application_events` — status history
`id`, `application_id`, `from_status`, `to_status`, `occurred_at`, `note`. One row per status
change (the first is `None → <initial>`), enabling funnel/time-in-stage analysis.

### `documents` — sent artifacts with provenance
`id`, `application_id`, `kind` (`cv` | `cover_letter` | `job_description`), `path` (relative to
the `dossier-data` root), `sha256` (integrity/immutability), and provenance: `model`, `language`,
`inventory_commit` (the `dossier-data` git commit when the document was captured), `generated_at`,
`created_at`.

## Status lifecycle

`draft → applied → screening → interview → technical → offer → accepted`, with
`rejected`, `withdrawn`, and `ghosted` as the other terminal outcomes. Transitions are recorded
freely (any → any); the terminal statuses (`accepted`, `rejected`, `withdrawn`, `ghosted`) clear
the follow-up date. A follow-up is set to `applied_on + DOSSIER_FOLLOWUP_DAYS` (default 10) on
non-terminal statuses.

## CLI

```bash
# Create / upgrade the database (runs Alembic migrations):
uv run dossier db upgrade

# Add an application:
uv run dossier track add --company Acme --role "Staff Engineer" \
    --status applied --applied-on 2026-06-21 [--source --url --location --work-mode --comp --notes]

# Attach the exact document sent (copied + hashed):
uv run dossier track attach 1 --kind cv --file path/to/cv.md [--model --language]

# Move it through the pipeline (records an event):
uv run dossier track status 1 interview --note "phone screen passed"

# Inspect:
uv run dossier track list [--status interview]
uv run dossier track show 1            # details + timeline + documents
uv run dossier track followups [--as-of 2026-07-01]
```

## Migrations

Schema changes are versioned with Alembic (`migrations/`). After editing the models in
`src/dossier/tracker/models.py`:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run dossier db upgrade        # or: uv run alembic upgrade head
```

`migrations/env.py` resolves the database URL from configuration
(`DOSSIER_DATABASE_URL`, else derived from `DOSSIER_DATA_PATH`); no path is hard-coded.
