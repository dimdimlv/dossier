# CLAUDE.md

Project memory for Claude Code. Keep this file short and high-signal. Deeper detail lives in `README.md` and `docs/adr/` — reference those rather than duplicating them here.

## What this is

Dossier is a personal job-search system: a structured inventory of professional experience that generates tailored CVs and cover letters and tracks applications. Full overview in [`README.md`](README.md). It is both a working tool and a deliberate learning project in modern software practices.

## Architecture at a glance

- Two repositories: **`dossier`** (this one, public — code) and **`dossier-data`** (private — personal data). They are physically independent and linked at runtime via the `DOSSIER_DATA_PATH` environment variable. Rationale: [ADR-001](docs/adr/ADR-001-public-private-data-separation.md).
- Three layers, built incrementally (walking skeleton): **inventory** (structured data) → **engine** (JD analysis + generation via Anthropic API) → **tracker** (application log + reminders).
- License: MIT — [ADR-002](docs/adr/ADR-002-mit-license.md).

## Tooling

- **Python** environment and packages via **`uv`** — not pip/venv directly. Dependencies in `pyproject.toml` + `uv.lock` (both committed).
- **VS Code** as editor.
- Config via environment variables (Twelve-Factor). The model identifier lives in `.env` as `ANTHROPIC_MODEL`, not hard-coded.

## Conventions

- **Conventional Commits** for all commit messages (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`).
- **ADRs** for significant architectural decisions: Nygard format + explicit "Considered alternatives", stored in `docs/adr/`, indexed in `docs/adr/README.md`. ADRs are immutable once accepted — supersede, never edit.
- All documentation and code comments in **English**.
- Generated documents default to English; target language is a parameter (no separate translation step).

## Rules

- **Never** place real personal data, secrets, or generated CVs/letters in this public repo. They belong in `dossier-data`. When writing output files, target the path from `DOSSIER_DATA_PATH`.
- **Never** hard-code absolute paths, real names, or credentials in code — read them from the environment.
- Before adding a dependency or making an architectural choice, prefer explaining the trade-offs and alternatives over deciding unilaterally.
- Keep secrets out of commits; a pre-commit `detect-secrets` hook is active.

## Status

Project initialized (`src/` layout, packaged via `uv`, Python 3.13, pytest/ruff/mypy — [ADR-003](docs/adr/ADR-003-python-project-layout.md)). **M1 inventory schema** done: Pydantic models + loader + `dossier inventory validate` ([ADR-004](docs/adr/ADR-004-inventory-schema.md), [schema](docs/inventory-schema.md)). **M5 application tracker** done: SQLite + SQLAlchemy 2.0 + Alembic, `dossier track`/`dossier db` CLI, immutable hashed document storage, plus the reminder layer — `dossier track remind` (snooze/reschedule/clear a follow-up) and a `dossier track followups` digest (overdue vs due-today, `--exit-code` for schedulers) ([ADR-005](docs/adr/ADR-005-application-tracker-persistence.md), [schema](docs/tracker-schema.md)). **M2 engine** done: `dossier analyze` parses a JD via the Anthropic API (`messages.parse`) and runs hybrid (deterministic + LLM) gap analysis against the inventory ([ADR-006](docs/adr/ADR-006-engine-jd-analysis.md), [engine](docs/engine.md)); model read from `ANTHROPIC_MODEL`; unit tests use a fake LLM client (no network). The provider is pluggable — Anthropic (default) or OpenAI via `DOSSIER_LLM_PROVIDER`/`--provider` ([ADR-007](docs/adr/ADR-007-multi-provider-llm.md)). **M3 CV generator** done: `dossier generate cv` runs JD analysis, deterministically selects relevant inventory content, has the LLM tailor phrasing only (never selection), and renders a single Jinja2 Markdown template; drafts save under `$DOSSIER_DATA_PATH/generated/` ([ADR-008](docs/adr/ADR-008-cv-generation.md)). **M4 cover letter generator** done: `dossier generate cover-letter` reuses the same selector/render pipeline but the LLM composes prose (salutation + body paragraphs + signoff) with optional `--to`/`--notes`; anti-fabrication is best-effort (prompt + source-limited input + human review), not structural like the CV's ([ADR-009](docs/adr/ADR-009-cover-letter-generation.md)). **M6 containerization** done: multi-stage `uv` Dockerfile on `python:3.13-slim` (non-root, editable install so `dossier db upgrade` can still locate `alembic.ini`/`migrations/`) plus a `docker-compose.yml` for on-demand CLI use (`docker compose run --rm dossier …`); `.env` injects secrets, `dossier-data` bind-mounts to `/data` ([ADR-010](docs/adr/ADR-010-containerization.md)). **M7 CI** done: `.github/workflows/ci.yml` runs three parallel jobs on every push to `main` and every PR — `quality` (`uv sync --locked` → ruff check → mypy → pytest), `pre-commit` (`detect-secrets` + hygiene hooks), and `docker` (builds the M6 image, no push); hermetic (no secrets needed) ([ADR-011](docs/adr/ADR-011-ci-pipeline.md)). Next: M8 (deployment + monitoring). Roadmap in [`README.md`](README.md). Detailed task state lives in issues, not here.
