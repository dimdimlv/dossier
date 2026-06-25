# ADR-011: Continuous integration with GitHub Actions

## Status

Accepted — 2026-06-25

## Context

Milestone M7 is the CI/CD pipeline (README roadmap). Until now every quality gate — `ruff check`,
`mypy src`, `pytest`, the `detect-secrets` + hygiene pre-commit hooks, and (since M6) the Docker
image build — runs only manually on the author's machine. Nothing enforces them on push or in pull
requests, so a regression or a leaked secret could reach `main` unnoticed. The project values modern,
transferable practice and treats secret hygiene as layered defense (ADR-001).

Fixed constraints: the repository is hosted on GitHub; Python is pinned to **3.13** only
(`requires-python>=3.13`, `.python-version`); dependencies are managed with **`uv`** with a committed
`uv.lock`; and the test suite runs green **without any secrets or `DOSSIER_DATA_PATH`** (it uses
`tmp_path`/in-memory SQLite fixtures and a fake LLM client). This milestone is **CI only** — building
and deploying the image to a registry/VPS belongs to M8.

## Considered alternatives

### CI platform

**A. GitHub Actions (chosen).** The repo already lives on GitHub; first-party, no extra accounts,
generous free minutes, large action ecosystem. *Chosen.*

**B. GitLab CI / CircleCI / others.** Capable, but would add an external integration for a repo that
is already on GitHub. *Rejected* — no benefit here.

### Toolchain installation

**A. `astral-sh/setup-uv` with caching (chosen).** Installs the same `uv` used locally, restores
`uv`'s cache between runs, and sets the Python version — mirroring the local environment exactly via
`uv sync --locked`. *Chosen.*

**B. `actions/setup-python` + `pip`.** Works, but diverges from the project's `uv`-managed workflow
and the locked dependency set. *Rejected.*

### Job layout

**A. Parallel jobs (chosen).** Separate `quality`, `pre-commit`, and `docker` jobs run concurrently
for faster feedback and a clear signal about which gate failed. *Chosen.*

**B. One sequential job.** Simpler file, but slower and noisier to diagnose. *Rejected.*

### Docker in CI

**A. Build-only validation (chosen).** CI builds the M6 `Dockerfile` (with GitHub Actions layer
cache) but does not push. Catches image regressions without coupling CI to a registry. *Chosen.*

**B. Build and publish to a registry (e.g. GHCR).** Useful, but publishing is a deployment concern.
*Rejected for M7* — deferred to M8.

### Secret scanning in CI

**A. Re-run the pre-commit hooks in CI (chosen).** `uvx pre-commit run --all-files` executes
`detect-secrets` and the hygiene hooks server-side, so the ADR-001 secret barrier holds even if a
contributor never installed the local hook. *Chosen.*

**B. Trust local hooks only.** *Rejected* — local hooks are opt-in and bypassable; CI is the
enforcing layer.

### Formatting scope

**A. Lint-only `ruff check` (chosen).** `ruff check` is already green. `ruff format --check` would
currently flag 15 files; enforcing it now would mix a large reformatting diff into the CI milestone.
*Chosen* — format enforcement deferred to a separate `style:` change.

**B. Add `ruff format --check` now.** *Rejected for M7* — scope creep.

## Decision

Add a single workflow, `.github/workflows/ci.yml`, triggered on push to `main` and on
`pull_request`, with top-level `permissions: contents: read` and `cancel-in-progress` concurrency.
Three parallel `ubuntu-latest` jobs:

- **`quality`** — `astral-sh/setup-uv` (cache on, `version: 0.9.7`, `python-version: 3.13`) →
  `uv sync --locked` → `uv run ruff check .` → `uv run mypy src` → `uv run pytest`.
- **`pre-commit`** — `astral-sh/setup-uv` → `uvx pre-commit run --all-files` (detect-secrets + hygiene).
- **`docker`** — `docker/setup-buildx-action` → `docker/build-push-action` with `push: false` and
  GitHub Actions layer caching, building the M6 `Dockerfile`.

Actions are pinned by tag — major-version where a floating tag exists
(`actions/checkout@v4`, `docker/*@v3`/`@v6`), and the exact release `astral-sh/setup-uv@v8.2.0`
since setup-uv publishes no floating `v8` tag.

## Consequences

### Positive

- Every push and PR gets an automatic green-check contract across lint, types, tests, secret scan,
  and image build — regressions and accidental secrets are caught before merge.
- No secrets are configured in CI; the suite is hermetic by design.
- The pipeline mirrors the exact local commands, so "green locally" means "green in CI".

### Negative

- GitHub Actions minutes are consumed per push/PR (small for this project; mitigated by caching and
  concurrency cancellation).

### Neutral / future options

- `ruff format --check` enforcement and a one-time reformat are a clean follow-up `style:` change.
- Pinning actions by full commit SHA is a further supply-chain hardening step.
- Publishing the image to GHCR and deploying it arrive with M8.

## References

- ADR-001 — Public/private repository separation (layered secret defense).
- ADR-003 — Python project layout (`uv`, `src/` layout).
- ADR-010 — Containerization (the `Dockerfile` built by the `docker` job).
- uv GitHub Actions integration — https://docs.astral.sh/uv/guides/integration/github/
