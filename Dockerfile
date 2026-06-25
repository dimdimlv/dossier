# syntax=docker/dockerfile:1
#
# Dossier container image (ADR-010).
#
# Multi-stage build using the official `uv` binary on a slim Python base. The
# project is installed in *editable* mode and the source tree is kept in the
# final image on purpose: `dossier db upgrade` locates `alembic.ini` and
# `migrations/` relative to the package source (see
# `src/dossier/migrations_support.py`), so the package must stay at
# `/app/src/dossier/...`. A `--no-editable` venv-only image would relocate the
# package into site-packages and break migrations.

# ── Builder ──────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

# Pin uv to the version used locally (uv.lock is produced by it).
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

# Use the image's system Python; copy (not symlink) into the cache mount.
ENV UV_PYTHON_DOWNLOADS=0 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Dependency layer: cached unless uv.lock / pyproject.toml change. No project,
# no dev dependencies (mypy/pytest/ruff are not needed at runtime).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Project layer: editable install keeps alembic.ini/migrations discoverable at /app.
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ── Runtime ──────────────────────────────────────────────────────────────────
FROM python:3.13-slim

# Run as an unprivileged user.
RUN groupadd --system dossier \
    && useradd --system --gid dossier --create-home dossier

WORKDIR /app

# Bring the venv and the project tree (src/, alembic.ini, migrations/, ...).
# The editable link remains valid because the path `/app` is identical.
COPY --from=builder --chown=dossier:dossier /app /app

ENV PATH="/app/.venv/bin:$PATH"

USER dossier

ENTRYPOINT ["dossier"]
CMD ["--help"]
