# ADR-012: Deployment — image to GHCR, docker-compose on a VPS, scheduled job via Ofelia

## Status

Accepted — 2026-06-25

## Context

Milestone M8 puts Dossier on a server (README roadmap). M6 produced a container image and M7 a CI
pipeline, but nothing publishes the image or runs Dossier anywhere. Two things must be decided: how
the image is published and deployed, and how the one recurring workload is scheduled.

Dossier is a **CLI/batch tool, not a service** (ADR-010). The only thing that needs to run
unattended on a server is the **follow-up reminder digest** (`dossier track followups`), whose
reminder layer was built in M5 and whose scheduling was explicitly deferred to M8. Personal data
stays in the private `dossier-data` repo, mounted at runtime (ADR-001). The author runs a single
small VPS; the project values transferable, low-footprint practice.

The deployment target is the author's VPS, which is not reachable from the development environment,
so this milestone delivers **repo-side, locally-verifiable artifacts plus a runbook** the operator
applies on the host.

## Considered alternatives

### Image distribution

**A. Publish to GitHub Container Registry (GHCR) (chosen).** A GitHub Actions workflow builds the
M6 `Dockerfile` and pushes `ghcr.io/<owner>/dossier` on push to `main` and on `v*` tags, using the
built-in `GITHUB_TOKEN` (no extra secrets). Same ecosystem as the M7 CI, free for public images.
*Chosen.*

**B. Docker Hub.** Equivalent, but a separate account/secret for no benefit. *Rejected.*

**C. Build on the VPS from source.** No registry, but ties deploys to a full toolchain on the host
and loses the immutable, CI-built artifact. *Rejected.*

### How it runs on the VPS

**A. `docker compose` on the host + a runbook (chosen).** A `deploy/docker-compose.yml` defines the
scheduler and the monitoring stack (ADR-013); the operator pulls images and `compose up -d`,
following `docs/deployment.md`. Minimal, transparent, matches the project's scale. *Chosen.*

**B. Ansible playbook.** Reproducible host provisioning, but heavyweight for one small single-user
VPS and more to learn/maintain than the milestone needs. *Rejected for now* — a clean future step.

**C. Kubernetes / Nomad.** Vastly disproportionate to a single-user CLI. *Rejected.*

### Scheduling the follow-up digest

**A. Ofelia cron sidecar in compose (chosen).** `mcuadros/ofelia` runs `dossier track followups
--push-metrics` from the published image on a schedule (config in `deploy/ofelia.ini`, `job-run`).
The schedule lives in the repo with the rest of the stack and is portable across hosts. *Chosen.*

**B. Host `cron`.** Simple, but the schedule lives outside the repo on the host and invokes Docker
by hand — less self-documenting and less portable. *Rejected.*

**C. systemd timer.** Robust and host-native, but host-specific units outside the compose stack.
*Rejected* — same portability objection as cron.

## Decision

Publish the image to **GHCR** via `.github/workflows/publish.yml` (build-push on `main` + `v*`
tags, `docker/metadata-action` for `latest`/`sha-…`/tag tags, `packages: write`). Deploy on the VPS
with **`deploy/docker-compose.yml`** and the **`docs/deployment.md`** runbook. Schedule the digest
with an **Ofelia** `job-run` sidecar (`deploy/ofelia.ini`) that runs the published image's
`track followups --push-metrics` and pushes metrics to the Pushgateway (ADR-013).

## Consequences

### Positive

- Immutable, CI-built images in GHCR; deploys are a `pull` + `compose up`.
- The recurring reminder runs unattended, its schedule version-controlled with the code.
- No new secrets for publishing (built-in `GITHUB_TOKEN`); the digest job needs no LLM key.

### Negative / trade-offs

- Ofelia mounts the Docker socket (read-only) to spawn the job container — a privilege to be aware
  of; acceptable on a single-tenant VPS, and the socket is mounted `:ro`.
- `deploy/ofelia.ini` carries a placeholder host data path (`/srv/dossier-data`) and image owner the
  operator edits before deploy — it cannot be env-interpolated from inside Ofelia's INI.
- The live VPS apply is manual (documented), not automated CD; SSH-based auto-deploy was considered
  and deferred to keep secrets and host access out of scope for now.

### Neutral / future options

- An SSH or Ansible-based auto-deploy job can be added later without changing the image or stack.
- Tagged releases (`v*`) already publish versioned images, enabling pinned production deploys.

## References

- ADR-001 — Public/private repository separation (data mounted at runtime).
- ADR-010 — Containerization (the image this publishes/deploys).
- ADR-013 — Observability (the monitoring stack and the metrics the scheduled job pushes).
- Ofelia — https://github.com/mcuadros/ofelia
