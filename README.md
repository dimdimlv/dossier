# Dossier

[![CI](https://github.com/dimdimlv/dossier/actions/workflows/ci.yml/badge.svg)](https://github.com/dimdimlv/dossier/actions/workflows/ci.yml)

A personal job-search system that turns a structured inventory of your professional self into tailored CVs and cover letters — and tracks the pipeline they feed.

---

## Why

Most job-search tooling treats the CV as a master document to be edited each time. Dossier inverts this: the source of truth is a structured **inventory** of your skills, projects, achievements, and metrics. Each application produces a fresh CV and cover letter, generated to fit the specific job description, drawing only the relevant pieces from the inventory.

This works particularly well for polymath profiles whose full experience never fits a single CV.

## What it does (v1 scope)

- Maintain a structured inventory of skills, projects, achievements, and quantified outcomes
- Parse a job description in any language and extract what it actually asks for
- Generate a tailored CV (English by default; target language on request) by assembling relevant inventory items
- Generate a matching cover letter in the same language
- Surface gaps between the JD and the inventory, and suggest existing inventory items that might cover them
- Log every application with status, dates, and automated follow-up reminders

## What it does NOT do

- Auto-apply to jobs
- Scrape job boards
- Prepare you for interviews
- Support multiple users
- Mobile app

These exclusions are deliberate. They may be revisited, but only after v1 has proven its core value.

## Repository layout

Dossier ships as **two separate repositories**:

| Repository | Visibility | Contents |
|---|---|---|
| `dossier` (this repo) | public | Code, schemas, tests, prompt templates, documentation, ADRs |
| `dossier-data` | private | Personal inventory, generated CVs, application log, secrets |

The two are decoupled at runtime via the `DOSSIER_DATA_PATH` environment variable. The code never contains a hard-coded path to personal data, and personal data never appears in the public git history.

Rationale: see [`docs/adr/ADR-001-public-private-data-separation.md`](docs/adr/ADR-001-public-private-data-separation.md).

## Architecture (high level)

Three layers, built incrementally:

1. **Inventory** — structured store of skills, experience, achievements, and education. YAML for list-like data and Markdown-with-frontmatter for narrative roles, all under version control. Format reference: [`docs/inventory-schema.md`](docs/inventory-schema.md).
2. **Engine** — the core pipeline: `JD → analysis → assembly → CV + cover letter + gap report`. Uses the Anthropic Claude API (or OpenAI — provider is configurable). JD parsing and gap analysis are implemented; reference: [`docs/engine.md`](docs/engine.md).
3. **Tracker** — application log, status transitions, follow-up reminders, and an immutable record of the CV/cover letter sent with each application. SQLite via SQLAlchemy + Alembic. Reference: [`docs/tracker-schema.md`](docs/tracker-schema.md).

The project follows a *walking-skeleton* approach: the simplest end-to-end version of all three layers ships first, then each layer is hardened in subsequent iterations.

## Status

Early development. No functioning code yet — currently in design and bootstrapping phase.

## Tech stack (tentative)

- Python — engine, tracker
- Markdown + Git — inventory format
- SQLite — application log
- Anthropic Claude API — JD analysis and generation
- Docker, GitHub Actions, Prometheus + Grafana — later layers

Choices are recorded as ADRs as they are made.

## Run in Docker

Dossier is a CLI, so the container is for on-demand invocation rather than a long-running service.
With Docker installed and a populated `.env` (a valid `DOSSIER_DATA_PATH` pointing at your local
`dossier-data` checkout, plus your API key):

```bash
docker compose build
docker compose run --rm dossier db upgrade          # create/upgrade the tracker DB
docker compose run --rm dossier inventory validate  # validate the mounted inventory
docker compose run --rm dossier generate cv <jd>    # generate against a job description
```

Compose loads secrets from `.env` and bind-mounts your `dossier-data` directory to `/data` inside
the container; the host `DOSSIER_DATA_PATH` selects the mount source. Rationale and trade-offs:
[ADR-010](docs/adr/ADR-010-containerization.md).

## Deployment & monitoring

For unattended use, the published image runs the **follow-up reminder digest** on a schedule (an
Ofelia cron sidecar) and pushes metrics to a Prometheus + Grafana stack with a Pushgateway — the
canonical way to observe a batch CLI that runs and exits. The image is published to GHCR by
`.github/workflows/publish.yml`; the stack and a VPS runbook live under [`deploy/`](deploy/) and
[`docs/deployment.md`](docs/deployment.md). Metrics catalogue: [`docs/monitoring.md`](docs/monitoring.md).
Rationale: [ADR-012](docs/adr/ADR-012-deployment.md), [ADR-013](docs/adr/ADR-013-observability.md).

## Roadmap

- [x] **M0** — Project bootstrapped (README, repo layout, first ADRs)
- [x] **M1** — Inventory schema (real entries pending)
- [x] **M2** — JD parser and gap analysis
- [x] **M3** — CV generator
- [x] **M4** — Cover letter generator
- [x] **M5** — Application tracker with reminders — *schema, status history, document versioning, follow-ups, and manual reminder control + a due-follow-up digest*
- [x] **M6** — Containerization (Docker, docker-compose) — *multi-stage `uv` image, non-root, `docker compose run` for CLI invocation*
- [x] **M7** — CI/CD pipeline (GitHub Actions) — *lint, type-check, tests, secret scan, and Docker build on every push/PR*
- [x] **M8** — Deployment to VPS, monitoring (Prometheus + Grafana) — *image published to GHCR, scheduled follow-up digest (Ofelia) pushing metrics to a Prometheus + Grafana stack*

Milestones are sequential by default but the boundary between them is permeable — small pieces of M6+ infrastructure may slip in earlier when they make further development materially easier.

## Goals

This project serves two intertwined goals, both first-class:

1. **A working tool** that meaningfully improves the author's job search.
2. **A learning project** covering modern software development practices end-to-end — from architecture decisions and lean documentation to CI/CD, observability, and secure handling of personal data.

Every significant decision is documented as an ADR, so the project itself is a record of how it was built.

## License

MIT — see [`LICENSE`](LICENSE). Rationale recorded in [ADR-002](docs/adr/ADR-002-mit-license.md).

## Author

Dmitry Polishchuk — [LinkedIn](https://www.linkedin.com/in/dmitry-polischuk-8a42773a/)
