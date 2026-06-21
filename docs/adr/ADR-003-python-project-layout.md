# ADR-003: Python project layout — `src/` layout, packaged application via `uv`

## Status

Accepted — 2026-06-21

## Context

Milestone M1 introduces the first real Python code into the `dossier` repository. Before any
modules exist, two structural choices must be made, because both are awkward to reverse once
code and import statements depend on them:

1. **Source layout** — should the importable package live at the repository root (a *flat*
   layout, `dossier/dossier/...`) or under a dedicated `src/` directory (`src/dossier/...`)?
2. **Project type** — should the project be a *packaged* distributable (with a build backend,
   installable into the environment, exposing a console entry point) or a bare *application*
   (a non-installable collection of scripts run directly)?

The toolchain is already fixed by CLAUDE.md: Python environments and dependencies are managed
with **`uv`** (not pip/venv directly), with `pyproject.toml` and `uv.lock` committed. The
existing `.gitignore` already anticipates the Python ecosystem (`__pycache__`, `.venv/`,
`.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`) and explicitly keeps `uv.lock` under version
control.

Dossier is, by design, both a working tool and a learning project in modern software practices.
Its architecture is three layers built incrementally — **inventory → engine → tracker** — which
will become sibling subpackages (`dossier.inventory`, `dossier.engine`, `dossier.tracker`) under
a single top-level package, and it has a natural command-line front door ("analyze this job
description, generate a CV"). The layout choice should serve that shape.

## Considered alternatives

### A. Flat layout, non-packaged application

The default of a plain `uv init`: a package directory (or loose modules) at the repository root,
no `[build-system]`, not installable; everything is run via `uv run some_script.py`.

- **Pros:** the absolute minimum of structure and configuration; fine for a single throwaway
  script.
- **Cons:** no console entry point; cross-module imports in tests are awkward and depend on the
  current working directory; no versioned, installable artifact; no clean namespace to host the
  three architectural layers.
- **Verdict:** rejected. Too thin for a multi-module, multi-milestone application.

### B. Flat layout, packaged

A packaged project, but with the importable package living at the repository root
(`dossier/dossier/...`).

- **Pros:** packaged benefits (build backend, entry point, installable) with one fewer directory
  level than `src/`.
- **Cons:** tests and tooling import the **working-tree source** rather than the installed
  artifact, which hides "works-on-my-machine" packaging bugs (missing data files, an incorrect
  `__init__`, files left out of the wheel); a top-level package directory competes with the
  repo's other root entries (`docs/`, future `tests/`, config files) and with the repository
  name itself.
- **Verdict:** rejected. The import-shadowing failure mode undermines the project's goal of
  trustworthy, modern testing practice.

### C. `src/` layout, packaged application

Code lives under `src/dossier/`; the project is packaged with a build backend, installed
(editable) into the `uv`-managed environment, and exposes a `dossier` console entry point.
Produced by `uv init --package`.

- **Pros:** the package is importable **only after installation**, so the test suite exercises
  the same artifact a user would install — packaging errors surface immediately; clean separation
  of shippable code from repository tooling and configuration; a real `dossier` CLI command as
  the natural user interface; a single namespace to host `dossier.inventory` / `dossier.engine` /
  `dossier.tracker`; this is the current PyPA / `uv --package` recommended default.
- **Cons:** one extra directory level and a handful of extra `pyproject.toml` lines. Negligible.
- **Verdict:** chosen.

## Decision

Adopt the **`src/` layout** with a **packaged application**, scaffolded via
`uv init --package --name dossier --python 3.13 .`.

Concretely:

- Importable code lives under `src/dossier/`.
- The project is packaged. The build backend is **`uv_build`** (uv's own backend, the default
  emitted by `uv init` in this uv version), declared in `[build-system]`. No separate build
  backend (e.g. hatchling/setuptools) is introduced.
- A console entry point `dossier = "dossier:main"` is declared under `[project.scripts]`.
- The interpreter is pinned to **Python 3.13** via `.python-version`, and `requires-python`
  is set to `>=3.13`.
- Developer tooling — **pytest, ruff, mypy** — is added as a `dev` dependency group
  (`uv add --dev pytest ruff mypy`).
- `uv.lock` is committed (it pins exact, reproducible dependency versions); the `.venv/` is not
  committed and is rebuilt from `pyproject.toml` + `uv.lock` on any machine.

## Consequences

### Positive

- The test suite runs against the installed package, catching packaging mistakes early and
  keeping tests honest — a core aim of the project as a modern-practices exercise.
- A clean import namespace for the three architectural layers, and a real `dossier` CLI as the
  product's front door.
- The repository root stays uncluttered: shippable code is isolated under `src/`, separate from
  docs, ADRs, and project configuration.
- Reproducible environments via the committed `uv.lock`; consistent linting/typing/testing via a
  pinned dev dependency group.

### Negative

- One additional directory level (`src/`) and a small amount of packaging configuration.
  Accepted as trivial.

### Neutral

- The layout binds the project to the `uv` workflow and the `uv_build` backend — both already
  decided in CLAUDE.md, so this introduces no new lock-in beyond what was chosen. Should a
  different build backend ever be warranted, only `[build-system]` changes; the `src/` layout is
  backend-agnostic.

## References

- Python Packaging User Guide — *src layout vs flat layout* —
  https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
- `uv` documentation — *Creating projects* (`uv init`, `--package`, `--lib`) —
  https://docs.astral.sh/uv/concepts/projects/init/
- `uv` documentation — *Build backend* (`uv_build`) —
  https://docs.astral.sh/uv/concepts/build-backend/
