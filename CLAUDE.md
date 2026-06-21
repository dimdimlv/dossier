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

M1 in progress. Python project initialized: `src/` layout, packaged application via `uv`, Python 3.13, dev tooling (pytest, ruff, mypy); layout rationale in [ADR-003](docs/adr/ADR-003-python-project-layout.md). Next: inventory schema and first inventory entries. Roadmap in [`README.md`](README.md). Detailed, changing task state lives in issues, not here.
