# ADR-010: Containerization — uv multi-stage Docker image + docker-compose for CLI invocation

## Status

Accepted — 2026-06-25

## Context

Milestone M6 is containerization (README roadmap). The goal is a reproducible, portable runtime
for the `dossier` CLI so it runs identically on any machine without a local `uv`/Python setup, and
to lay groundwork for M7 (CI) and M8 (VPS deployment + monitoring).

Dossier is a **CLI, not a server**: commands such as `dossier generate cv <jd>` or
`dossier track followups` run to completion and exit. The container therefore exists for
**on-demand invocation**, not as a persistent service.

Two existing facts constrain the design:

1. **Personal data is external** (ADR-001). The app reads the inventory and writes generated
   documents and the tracker database under `DOSSIER_DATA_PATH`. At runtime that directory must be
   a **bind-mounted volume**, and secrets (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, …) must be
   injected from the environment — never baked into an image layer.

2. **Migrations resolve paths relative to the source tree.** `src/dossier/migrations_support.py`
   computes `PROJECT_ROOT = Path(__file__).resolve().parents[2]` to locate `alembic.ini` and
   `migrations/`. This only holds while the package lives at `<root>/src/dossier/…`. The
   conventional "smallest image" uv pattern installs the project `--no-editable` and copies only
   the virtual environment to the final stage — relocating the package into `site-packages` and
   **breaking `dossier db upgrade`**.

The stack is Python 3.13 managed with `uv` (ADR-003). The project values modern, transferable
practice and cautious choices.

## Considered alternatives

### Image build strategy

**A. uv multi-stage, slim base, *editable* install with the project tree in the final image,
non-root (chosen).** A builder stage installs dependencies in a cached layer from `uv.lock`
(`--no-install-project --no-dev`), then installs the project editable; the runtime stage copies
the whole `/app` (venv + `src/` + `alembic.ini` + `migrations/`) and runs as an unprivileged user.
Demonstrates current uv + Docker practice, keeps the dependency layer cacheable, and **preserves
the Alembic path resolution**. Cost: the final image carries the source tree (small for this
project). *Chosen.*

**B. uv multi-stage `--no-editable`, venv-only final image.** The canonical smallest-image
pattern. *Rejected* — it relocates the package to `site-packages` and breaks `dossier db upgrade`;
adopting it would force a code change to `migrations_support.py` for negligible size benefit.

**C. Single-stage, install as root.** Fewer moving parts and easier to read. *Rejected* — larger
image, no dependency-layer caching discipline, runs as root, weaker as a learning artifact.

**D. Distroless final stage.** Minimal attack surface. *Rejected* — harder to debug, and the
editable-install + source-tree requirement fits a normal slim base far more naturally than
distroless, for marginal gain on a single-user CLI.

### Invocation model

**A. `docker compose run --rm dossier <args>` — ephemeral CLI (chosen).** Compose encodes the
`.env` injection and the data bind-mount once; each command is a throwaway container. Matches the
tool's run-to-exit nature. *Chosen.*

**B. Long-running service (compose `up`).** *Rejected* — there is nothing to serve.

**C. Bare `docker run` documented in the README only.** *Rejected* — every invocation would have
to re-specify `--env-file` and `-v`; compose captures that wiring declaratively.

### Data and secrets wiring

The chosen approach: `env_file: .env` injects API keys and `DOSSIER_*` settings; the private
`dossier-data` checkout is bind-mounted to `/data`; `DOSSIER_DATA_PATH` is **overridden to `/data`
inside the container**, while its host value (read from `.env` via compose interpolation) selects
the mount source. *Rejected alternatives:* baking data into the image (violates ADR-001) or
passing secrets as build args (they would persist in image history).

## Decision

Containerize the CLI with a **multi-stage Dockerfile** on `python:3.13-slim` using the official
`uv` binary (pinned to 0.9.7), and a **`docker-compose.yml`** for on-demand invocation.

Specifics:

- **Builder stage**: `COPY --from=ghcr.io/astral-sh/uv:0.9.7`; `UV_PYTHON_DOWNLOADS=0`,
  `UV_LINK_MODE=copy`, `UV_COMPILE_BYTECODE=1`. A cached dependency layer
  (`uv sync --locked --no-install-project --no-dev` with bind-mounted `uv.lock`/`pyproject.toml`),
  then `COPY . /app` + `uv sync --locked --no-dev` (default **editable** install).
- **Runtime stage**: fresh `python:3.13-slim`, a system non-root `dossier` user,
  `COPY --from=builder --chown=dossier:dossier /app /app`, `PATH=/app/.venv/bin:$PATH`,
  `ENTRYPOINT ["dossier"]`, `CMD ["--help"]`.
- **`.dockerignore`** keeps the context to what the build needs (`src/`, `pyproject.toml`,
  `uv.lock`, `alembic.ini`, `migrations/`) and excludes secrets, the host `.venv`, caches, tests,
  and docs.
- **`docker-compose.yml`** defines one `dossier` service: `build: .`, `env_file: [.env]`,
  `environment: DOSSIER_DATA_PATH=/data`, and a bind-mount
  `${DOSSIER_DATA_PATH}:/data`.
- No application code changes are required.

## Consequences

### Positive

- Reproducible, portable runtime; `docker compose run --rm dossier …` works anywhere Docker does.
- Cacheable dependency layer keeps rebuilds fast when only source changes.
- Runs as non-root; secrets and personal data stay out of image layers (ADR-001 upheld).
- `dossier db upgrade` works in-container because the source tree (and thus `alembic.ini` +
  `migrations/`) ships in the image.

### Negative

- The final image carries the source tree and an editable install rather than the most minimal
  venv-only layout — a deliberate trade for working migrations.
- On Linux hosts, bind-mounted writes use the host UID; the fixed non-root container UID may
  mismatch and cause permission errors. Mitigation: override at runtime (e.g. compose
  `user: "${UID}:${GID}"`). On the author's macOS Docker Desktop this is handled transparently.

### Neutral / future options

- A scheduled `dossier track followups` reminder service is intentionally deferred to M8
  (deployment/scheduling), not bundled into M6.
- Image publishing to a registry and build automation arrive with M7 (CI/CD).

## References

- ADR-001 — Public/private repository separation.
- ADR-003 — Python project layout (`uv`, `src/` layout).
- ADR-005 — Tracker persistence (Alembic path resolution via `migrations_support.py`).
- uv Docker integration guide — https://docs.astral.sh/uv/guides/integration/docker/
